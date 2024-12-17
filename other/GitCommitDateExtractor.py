import multiprocessing
import psutil
from typing import List, Dict, Tuple, Optional, Union
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class GitCommitDateExtractor:
    @staticmethod
    def _calculate_optimal_threads():
        """Calculate optimal number of threads based on system resources"""
        cpu_count = multiprocessing.cpu_count()
        memory_gb = psutil.virtual_memory().total / (1024**3)
        optimal_threads = min(cpu_count, int(memory_gb * 2))
        return max(2, min(optimal_threads, 32))

    def __init__(self, repo_path: str, temp_dir: str = "/tmp/git_repos", threads_per_worker: Optional[int] = None):
        """
        Initialize the GitCommitDateExtractor.
        
        Args:
            repo_path: Path to the git repository
            temp_dir: Directory for temporary files (default: /tmp/git_repos)
            threads_per_worker: Number of threads per worker (default: auto-calculated)
        """
        self.repo_path = repo_path
        self.temp_dir = Path(temp_dir)
        self.local_hostname = socket.gethostname()
        logger.info(f"Initializing GitCommitDateExtractor on host {self.local_hostname}")
        
        self.threads_per_worker = threads_per_worker or self._calculate_optimal_threads()
        logger.info(f"Using {self.threads_per_worker} threads per worker")
        
        os.makedirs(self.temp_dir, exist_ok=True)
        self.spark = SparkSession.builder.getOrCreate()
        self._broadcast_paths()

    def _broadcast_paths(self):
        """Broadcast paths and configuration to all workers"""
        self.broadcast_repo_path = self.spark.sparkContext.broadcast(str(self.repo_path))
        self.broadcast_temp_dir = self.spark.sparkContext.broadcast(str(self.temp_dir))
        self.broadcast_threads = self.spark.sparkContext.broadcast(self.threads_per_worker)
        self.broadcast_local_hostname = self.spark.sparkContext.broadcast(self.local_hostname)

    def _create_repo_archive(self) -> str:
        """Create compressed archive of repository with detailed logging"""
        logger.info(f"Starting repository compression from {self.repo_path}")
        compression_start = time.time()
        
        temp_archive = tempfile.NamedTemporaryFile(delete=False, suffix='.tar.gz')
        logger.info(f"Created temporary archive at {temp_archive.name}")
        
        try:
            subprocess.run([
                "tar", "czf", temp_archive.name,
                "-C", str(Path(self.repo_path).parent),
                Path(self.repo_path).name
            ], check=True, capture_output=True)
            
            archive_size = os.path.getsize(temp_archive.name)
            compression_time = time.time() - compression_start
            logger.info(f"Compression completed in {compression_time:.2f} seconds")
            logger.info(f"Compressed archive size: {archive_size / 1024 / 1024:.2f} MB")
            
            with open(temp_archive.name, 'rb') as f:
                encoded = base64.b64encode(f.read()).decode('utf-8')
            
            logger.info("Archive encoded to base64 for distribution")
            return encoded
        finally:
            os.unlink(temp_archive.name)
            logger.info(f"Temporary archive deleted from main node: {temp_archive.name}")

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
                        if existing_dir.is_dir():
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

    def _normalize_extensions(self, extensions: List[str]) -> List[str]:
        """Normalize file extensions"""
        return [f'.{ext.lower().lstrip(".")}' for ext in extensions]

    def _should_process_file(self, file_path: str, file_types: List[str] = [], exclude_folders: List[str] = []) -> bool:
        """Check if file should be processed"""
        path = Path(file_path)
        
        for folder in exclude_folders:
            folder = folder.strip('/')
            if folder in str(path.parent).split('/'):
                return False
                
        if not file_types:
            return True
            
        return path.suffix.lower() in self._normalize_extensions(file_types)

    def get_all_files(self, file_types: List[str] = [], exclude_folders: List[str] = []) -> List[str]:
        """
        Get filtered list of files from repository.
        
        Args:
            file_types: List of file extensions to include (e.g., ['py', 'java'])
            exclude_folders: List of folders to exclude (e.g., ['tests', '.git'])
            
        Returns:
            List of file paths matching the criteria
        """
        cmd = ["git", "--git-dir", f"{self.repo_path}/.git", "ls-files"]
        output = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
        
        all_files = output.splitlines()
        return [f for f in all_files if self._should_process_file(f, file_types, exclude_folders)]

    @staticmethod
    def _get_file_dates(repo_path: str, file_path: str, get_created: bool = False, 
                     get_content_change: bool = False) -> Dict[str, datetime]:
        """Get various dates for a file"""
        dates = {}
        
        try:
            # Get latest modification date
            result = subprocess.run([
                "git", "--git-dir", f"{repo_path}/.git",
                "log", "-1", "--format=%cd",
                "--date=iso-strict", "--follow",
                "--", file_path
            ], capture_output=True, text=True, check=True)
            
            date_str = result.stdout.strip()
            if date_str:
                dates['latest'] = datetime.fromisoformat(date_str)
            
            # Get creation date if requested
            if get_created:
                result = subprocess.run([
                    "git", "--git-dir", f"{repo_path}/.git",
                    "log", "--reverse", "-1", "--format=%cd",
                    "--date=iso-strict", "--follow",
                    "--", file_path
                ], capture_output=True, text=True, check=True)
                
                date_str = result.stdout.strip()
                if date_str:
                    dates['created'] = datetime.fromisoformat(date_str)
            
            # Get content change date if requested
            if get_content_change:
                result = subprocess.run([
                    "git", "--git-dir", f"{repo_path}/.git",
                    "log", "-1", "--format=%cd",
                    "--date=iso-strict", "--follow",
                    "--diff-filter=M",
                    "--", file_path
                ], capture_output=True, text=True, check=True)
                
                date_str = result.stdout.strip()
                if date_str:
                    dates['content_change'] = datetime.fromisoformat(date_str)
            
            return dates
        except subprocess.CalledProcessError:
            return {}

    def get_commit_dates_distributed(self, files: List[str], get_created: bool = False,
                                   get_content_change: bool = False,
                                   num_partitions: Optional[int] = None) -> Dict[str, Dict[str, datetime]]:
        """
        Get commit dates using distributed processing.
        
        Args:
            files: List of files to process
            get_created: Whether to get file creation dates
            get_content_change: Whether to get last content change dates
            num_partitions: Number of partitions for processing (default: auto-calculated)
            
        Returns:
            Dictionary mapping file paths to their dates
        """
        if not files:
            return {}
        
        total_start_time = time.time()
        logger.info(f"Starting distributed processing of {len(files)} files")
        
        if num_partitions is None:
            suggested_partitions = max(
                len(files) // 1000,
                self.spark.sparkContext.defaultParallelism
            )
            num_partitions = min(suggested_partitions, len(files))
        
        logger.info(f"Using {num_partitions} partitions across cluster")
        
        # Create and broadcast repository archive
        logger.info("Starting repository archive creation and broadcasting")
        compressed_repo = self._create_repo_archive()
        broadcast_repo = self.spark.sparkContext.broadcast(compressed_repo)
        broadcast_temp_dir = self.spark.sparkContext.broadcast(str(self.temp_dir))
        broadcast_threads = self.spark.sparkContext.broadcast(self.threads_per_worker)
        broadcast_local_hostname = self.spark.sparkContext.broadcast(self.local_hostname)
        broadcast_options = self.spark.sparkContext.broadcast({
            'get_created': get_created,
            'get_content_change': get_content_change
        })
        logger.info("Repository and configuration broadcast completed")
        
        def process_partition(iterator):
            """Process files in partition with detailed logging"""
            current_hostname = socket.gethostname()
            partition_start = time.time()
            logger.info(f"Starting partition processing on {current_hostname}")
            
            worker_repo_path = GitCommitDateExtractor._setup_worker_repo(
                broadcast_repo.value,
                broadcast_temp_dir.value,
                broadcast_local_hostname.value
            )
            
            try:
                files_list = list(iterator)
                results = []
                logger.info(f"Processing {len(files_list)} files on {current_hostname}")
                
                processed_count = 0
                
                def process_file(file_path):
                    nonlocal processed_count
                    dates = GitCommitDateExtractor._get_file_dates(
                        worker_repo_path,
                        file_path,
                        broadcast_options.value['get_created'],
                        broadcast_options.value['get_content_change']
                    )
                    processed_count += 1
                    if processed_count % 100 == 0:
                        logger.info(f"Processed {processed_count}/{len(files_list)} files on {current_hostname}")
                    if dates:
                        return file_path, dates
                    return None
                
                batch_size = max(1, len(files_list) // broadcast_threads.value)
                logger.info(f"Using batch size of {batch_size} on {current_hostname}")
                
                with ThreadPoolExecutor(max_workers=broadcast_threads.value) as executor:
                    for i in range(0, len(files_list), batch_size):
                        batch = files_list[i:i + batch_size]
                        thread_results = list(executor.map(process_file, batch))
                        results.extend([r for r in thread_results if r is not None])
                
                partition_time = time.time() - partition_start
                logger.info(f"Partition processing completed on {current_hostname} in {partition_time:.2f} seconds")
                return results
            finally:
                if current_hostname != broadcast_local_hostname.value:
                    logger.info(f"Cleaning up worker repository on {current_hostname}")
                    shutil.rmtree(worker_repo_path, ignore_errors=True)
                    logger.info(f"Worker repository cleanup completed on {current_hostname}")
        
        files_rdd = self.spark.sparkContext.parallelize(files, num_partitions)
        logger.info("Starting RDD processing")
        results = files_rdd.mapPartitions(process_partition).collect()
        
        # Cleanup broadcasts
        logger.info("Cleaning up broadcast variables")
        broadcast_repo.unpersist()
        broadcast_temp_dir.unpersist()
        broadcast_threads.unpersist()
        broadcast_local_hostname.unpersist()
        broadcast_options.unpersist()
        logger.info("Broadcast cleanup completed")
        
        total_time = time.time() - total_start_time
        logger.info(f"Total processing completed in {total_time:.2f} seconds")
        
        return dict(results)


# Example Usage

# Example 1: Get only latest commit dates
"""
from git_commit_extractor import GitCommitDateExtractor

# Initialize the extractor
extractor = GitCommitDateExtractor("/path/to/repo")

# Get all Python files
files = extractor.get_all_files(file_types=['py'])

# Get only latest commit dates
latest_dates = extractor.get_commit_dates_distributed(files)

# Get only latest commit date, modified data and last content change
latest_dates = extractor.get_commit_dates_distributed(
    files,
    get_created=True,
    get_content_change=True
    )

# Print results
for file_path, dates in latest_dates.items():
    print(f"{file_path}: Last modified {dates['latest']}")
"""
