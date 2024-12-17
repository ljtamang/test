import multiprocessing
import psutil
from typing import List, Dict, Tuple, Optional, Union, Set
from datetime import datetime
import os
import subprocess
from pathlib import Path
import tempfile
import time
import base64
import shutil
import socket
import logging
from concurrent.futures import ThreadPoolExecutor
from pyspark.sql import SparkSession
import hashlib
import json
from functools import lru_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class GitCommitDateExtractor:
    BATCH_SIZE = 1000  # Number of files to process in one batch
    CACHE_DIR = Path("/tmp/git_cache")
    
    @staticmethod
    def _calculate_optimal_threads():
        """Calculate optimal number of threads based on system resources"""
        cpu_count = multiprocessing.cpu_count()
        memory_gb = psutil.virtual_memory().total / (1024**3)
        optimal_threads = min(cpu_count, int(memory_gb * 2))
        return max(2, min(optimal_threads, 32))

    def __init__(self, repo_path: str, temp_dir: str = "/tmp/git_repos", 
                 threads_per_worker: Optional[int] = None,
                 file_types: Optional[List[str]] = None):
        """
        Initialize the GitCommitDateExtractor with enhanced caching and batch processing.
        
        Args:
            repo_path: Path to the git repository
            temp_dir: Directory for temporary files
            threads_per_worker: Number of threads per worker
            file_types: List of file extensions to process (e.g., ['py', 'java'])
        """
        self.repo_path = repo_path
        self.temp_dir = Path(temp_dir)
        self.file_types = self._normalize_extensions(file_types) if file_types else None
        self.local_hostname = socket.gethostname()
        
        # Create cache directory
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
        self.threads_per_worker = threads_per_worker or self._calculate_optimal_threads()
        logger.info(f"Using {self.threads_per_worker} threads per worker")
        
        os.makedirs(self.temp_dir, exist_ok=True)
        self.spark = SparkSession.builder.getOrCreate()
        self._broadcast_paths()
        
        # Initialize cache
        self._init_cache()

    def _normalize_extensions(self, extensions: Optional[List[str]]) -> Optional[List[str]]:
        """Normalize file extensions"""
        if extensions is None:
            return None
        return [f'.{ext.lower().lstrip(".")}' for ext in extensions]

    def _init_cache(self):
        """Initialize the cache system"""
        self.cache_file = self.CACHE_DIR / f"repo_{self._get_repo_hash()}.json"
        self.cache = self._load_cache()

    def _get_repo_hash(self) -> str:
        """Generate a unique hash for the repository state"""
        try:
            head_commit = subprocess.run(
                ["git", "--git-dir", f"{self.repo_path}/.git", "rev-parse", "HEAD"],
                capture_output=True, text=True, check=True
            ).stdout.strip()
            return hashlib.sha256(head_commit.encode()).hexdigest()
        except subprocess.CalledProcessError:
            return hashlib.sha256(str(time.time()).encode()).hexdigest()

    def _load_cache(self) -> Dict:
        """Load the cache from disk"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def _save_cache(self):
        """Save the cache to disk"""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f)

    def _should_process_file(self, file_path: str, exclude_folders: List[str] = []) -> bool:
        """Check if file should be processed"""
        path = Path(file_path)
        
        # Check excluded folders
        for folder in exclude_folders:
            folder = folder.strip('/')
            if folder in str(path.parent).split('/'):
                return False
        
        # Check file type if specified
        if self.file_types:
            return path.suffix.lower() in self.file_types
            
        return True

    def _broadcast_paths(self):
        """Broadcast paths and configuration to all workers"""
        self.broadcast_repo_path = self.spark.sparkContext.broadcast(str(self.repo_path))
        self.broadcast_temp_dir = self.spark.sparkContext.broadcast(str(self.temp_dir))
        self.broadcast_threads = self.spark.sparkContext.broadcast(self.threads_per_worker)
        self.broadcast_local_hostname = self.spark.sparkContext.broadcast(self.local_hostname)
        self.broadcast_file_types = self.spark.sparkContext.broadcast(self.file_types)

    def _create_selective_archive(self) -> str:
        """Create compressed archive of repository with only selected file types"""
        logger.info(f"Starting selective repository compression from {self.repo_path}")
        compression_start = time.time()
        
        temp_archive = tempfile.NamedTemporaryFile(delete=False, suffix='.tar.gz')
        temp_file_list = tempfile.NamedTemporaryFile(delete=False, mode='w')
        
        try:
            # Always include .git directory
            git_files = subprocess.run(
                ["find", f"{self.repo_path}/.git", "-type", "f"],
                capture_output=True, text=True, check=True
            ).stdout.splitlines()
            
            # Get list of files matching specified extensions
            if self.file_types:
                file_list = []
                for ext in self.file_types:
                    result = subprocess.run(
                        ["find", self.repo_path, "-type", "f", "-name", f"*{ext}"],
                        capture_output=True, text=True, check=True
                    )
                    file_list.extend(result.stdout.splitlines())
            else:
                file_list = subprocess.run(
                    ["find", self.repo_path, "-type", "f"],
                    capture_output=True, text=True, check=True
                ).stdout.splitlines()
            
            # Combine git files and filtered repository files
            all_files = git_files + file_list
            
            # Write file list for tar
            for file_path in all_files:
                relative_path = os.path.relpath(file_path, os.path.dirname(self.repo_path))
                temp_file_list.write(relative_path + '\n')
            temp_file_list.flush()
            
            # Create tar archive with only selected files
            subprocess.run([
                "tar", "czf", temp_archive.name,
                "-C", str(Path(self.repo_path).parent),
                "-T", temp_file_list.name
            ], check=True, capture_output=True)
            
            archive_size = os.path.getsize(temp_archive.name)
            compression_time = time.time() - compression_start
            logger.info(f"Selective compression completed in {compression_time:.2f} seconds")
            logger.info(f"Compressed archive size: {archive_size / 1024 / 1024:.2f} MB")
            
            with open(temp_archive.name, 'rb') as f:
                encoded = base64.b64encode(f.read()).decode('utf-8')
            
            return encoded
        finally:
            os.unlink(temp_archive.name)
            os.unlink(temp_file_list.name)

    @staticmethod
    def _setup_worker_repo(compressed_repo: str, temp_dir: str, local_hostname: str) -> str:
        """Setup repository on worker node with detailed logging"""
        current_hostname = socket.gethostname()
        worker_dir = Path(temp_dir) / f"worker_{time.time_ns()}"
        
        logger.info(f"Setting up worker repository on host {current_hostname}")
        
        # Clean up existing repos only on non-local worker nodes
        if current_hostname != local_hostname:
            parent_temp_dir = Path(temp_dir)
            if parent_temp_dir.exists():
                logger.info(f"Cleaning up existing repos on worker node {current_hostname}")
                cleanup_count = 0
                for existing_dir in parent_temp_dir.glob("worker_*"):
                    try:
                        if existing_dir.is_dir() and existing_dir != worker_dir:
                            shutil.rmtree(existing_dir)
                            cleanup_count += 1
                    except Exception as e:
                        logger.error(f"Failed to remove directory {existing_dir}: {e}")
                logger.info(f"Cleaned up {cleanup_count} existing repositories")
        
        worker_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created worker directory: {worker_dir}")
        
        extraction_start = time.time()
        temp_archive = tempfile.NamedTemporaryFile(delete=False, suffix='.tar.gz')
        try:
            logger.info(f"Decoding and writing compressed repo on {current_hostname}")
            with open(temp_archive.name, 'wb') as f:
                f.write(base64.b64decode(compressed_repo))
            
            logger.info(f"Extracting repository on {current_hostname}")
            subprocess.run([
                "tar", "xzf", temp_archive.name,
                "-C", str(worker_dir)
            ], check=True, capture_output=True)
            
            extraction_time = time.time() - extraction_start
            logger.info(f"Repository extraction completed in {extraction_time:.2f} seconds on {current_hostname}")
            
            return str(worker_dir)
        finally:
            os.unlink(temp_archive.name)
            logger.info(f"Temporary archive deleted from worker node {current_hostname}")

    @staticmethod
    def _get_file_dates(repo_path: str, file_path: str, get_created: bool = False, 
                       get_content_change: bool = False) -> Dict[str, datetime]:
        """Get various dates for a file with optimized git commands"""
        dates = {}
        git_dir = Path(repo_path) / '.git'
        
        try:
            # Batch git commands for better performance
            commands = []
            
            # Latest modification date
            commands.append([
                "git", f"--git-dir={git_dir}",
                "log", "-1", "--format=%cd",
                "--date=iso-strict", "--follow",
                "--", file_path
            ])
            
            # Creation date
            if get_created:
                commands.append([
                    "git", f"--git-dir={git_dir}",
                    "log", "--reverse", "-1", "--format=%cd",
                    "--date=iso-strict", "--follow",
                    "--", file_path
                ])
            
            # Content change date
            if get_content_change:
                commands.append([
                    "git", f"--git-dir={git_dir}",
                    "log", "-1", "--format=%cd",
                    "--date=iso-strict", "--follow",
                    "--diff-filter=M",
                    "--", file_path
                ])
            
            # Execute commands and process results
            for i, cmd in enumerate(commands):
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                date_str = result.stdout.strip()
                
                if date_str:
                    if i == 0:
                        dates['latest'] = datetime.fromisoformat(date_str)
                    elif i == 1 and get_created:
                        dates['created'] = datetime.fromisoformat(date_str)
                    elif get_content_change:
                        dates['content_change'] = datetime.fromisoformat(date_str)
            
            return dates
        except subprocess.CalledProcessError:
            return {}

    @staticmethod
    @lru_cache(maxsize=1024)
    def _get_file_dates_cached(repo_path: str, file_path: str, get_created: bool,
                             get_content_change: bool) -> Dict[str, str]:
        """Cached version of get_file_dates"""
        return GitCommitDateExtractor._get_file_dates(
            repo_path, file_path, get_created, get_content_change
        )

    def process_batch(self, batch: List[str], worker_repo_path: str,
                     get_created: bool, get_content_change: bool) -> List[Tuple[str, Dict]]:
        """Process a batch of files with caching"""
        results = []
        cache_key = f"{get_created}_{get_content_change}"
        
        for file_path in batch:
            # Check cache first
            cache_entry = self.cache.get(file_path, {}).get(cache_key)
            if cache_entry:
                results.append((file_path, cache_entry))
                continue
            
            # If not in cache, process the file
            dates = self._get_file_dates_cached(
                worker_repo_path,
                file_path,
                get_created,
                get_content_change
            )
            
            if dates:
                # Update cache
                if file_path not in self.cache:
                    self.cache[file_path] = {}
                self.cache[file_path][cache_key] = dates
                results.append((file_path, dates))
        
        return results

    def get_all_files(self, exclude_folders: List[str] = []) -> List[str]:
        """
        Get filtered list of files from repository.
        
        Args:
            exclude_folders: List of folders to exclude (e.g., ['tests', '.git'])
            
        Returns:
            List of file paths matching the criteria
        """
        cmd = ["git", "--git-dir", f"{self.repo_path}/.git", "ls-files"]
        output = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
        
        all_files = output.splitlines()
        return [f for f in all_files if self._should_process_file(f, exclude_folders)]

    def get_commit_dates_distributed(self, files: List[str], get_created: bool = False,
                                   get_content_change: bool = False,
                                   num_partitions: Optional[int] = None) -> Dict[str, Dict[str, datetime]]:
        """
        Get commit dates using distributed processing with batching and caching.
        """
        if not files:
            return {}
        
        total_start_time = time.time()
        logger.info(f"Starting distributed processing of {len(files)} files")
        
        # Calculate optimal number of partitions
        if num_partitions is None:
            suggested_partitions = max(
                len(files) // self.BATCH_SIZE,
                self.spark.sparkContext.defaultParallelism
            )
            num_partitions = min(suggested_partitions, len(files))
        
        logger.info(f"Using {num_partitions} partitions across cluster")
        
        # Create and broadcast repository archive
        compressed_repo = self._create_selective_archive()
        broadcast_repo = self.spark.sparkContext.broadcast(compressed_repo)
        broadcast_config = self.spark.sparkContext.broadcast({
            'temp_dir': str(self.temp_dir),
            'threads': self.threads_per_worker,
            'local_hostname': self.local_hostname,
            'get_created': get_created,
            'get_content_change': get_content_change,
            'batch_size': self.BATCH_SIZE
        })
        
        def process_partition(iterator):
            """Process files in partition with batching"""
            config = broadcast_config.value
            current_hostname = socket.gethostname()
            
            worker_repo_path = self._setup_worker_repo(
                broadcast_repo.value,
                config['temp_dir'],
                config['local_hostname']
            )
            
            try:
                files_list = list(iterator)
                results = []
                
                # Process files in batches
                for i in range(0, len(files_list), config['batch_size']):
                    batch = files_list[i:i + config['batch_size']]
                    batch_results = self.process_batch(
                        batch,
                        worker_repo_path,
                        config['get_created'],
                        config['get_content_change']
                    )
                    results.extend(batch_results)
                    
                    logger.info(f"Processed batch {i//config['batch_size'] + 1} on {current_hostname}")
                
                return results
            finally:
                if current_hostname != config['local_hostname']:
                    shutil.rmtree(worker_repo_path, ignore_errors=True)
        
        # Process files using Spark
        files_rdd = self.spark.sparkContext.parallelize(files, num_partitions)
        results = files_rdd.mapPartitions(process_partition).collect()
        
        # Cleanup broadcasts
        broadcast_repo.unpersist()
        broadcast_config.unpersist()
        
        # Save updated cache
        self._save_cache()
        
        total_time = time.time() - total_start_time
        logger.info(f"Total processing completed in {total_time:.2f} seconds")
        
        return dict(results)

    def cleanup(self):
        """Cleanup resources and temporary files"""
        try:
            # Cleanup broadcast variables
            if hasattr(self, 'broadcast_repo_path'):
                self.broadcast_repo_path.unpersist()
            if hasattr(self, 'broadcast_temp_dir'):
                self.broadcast_temp_dir.unpersist()
            if hasattr(self, 'broadcast_threads'):
                self.broadcast_threads.unpersist()
            if hasattr(self, 'broadcast_local_hostname'):
                self.broadcast_local_hostname.unpersist()
            if hasattr(self, 'broadcast_file_types'):
                self.broadcast_file_types.unpersist()
            
            # Save cache before cleanup
            self._save_cache()
            
            # Cleanup temporary directories on local machine
            if self.local_hostname == socket.gethostname():
                for temp_dir in Path(self.temp_dir).glob("worker_*"):
                    try:
                        if temp_dir.is_dir():
                            shutil.rmtree(temp_dir)
                    except Exception as e:
                        logger.error(f"Failed to cleanup directory {temp_dir}: {e}")
            
            logger.info("Cleanup completed successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()
