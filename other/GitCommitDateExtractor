from typing import List, Dict, Tuple, Optional
import os
import shutil
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
from pyspark.sql import SparkSession
from datetime import datetime
import subprocess
from pathlib import Path
import tempfile
import time
import math
import tarfile
import io
import base64

class GitCommitDateExtractor:
    def __init__(self, repo_path: str, temp_dir: str = "/tmp/git_repos"):
        """
        Initialize the extractor with repository path and temporary directory for worker copies
        
        Args:
            repo_path: Path to the original git repository
            temp_dir: Base directory for temporary worker copies
        """
        self.repo_path = repo_path
        self.temp_dir = Path(temp_dir)
        self.spark = SparkSession.builder.getOrCreate()
        
        # Ensure temp directory exists on driver
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Broadcast paths to all workers
        self.broadcast_repo_path = self.spark.sparkContext.broadcast(str(repo_path))
        self.broadcast_temp_dir = self.spark.sparkContext.broadcast(str(temp_dir))

    def _normalize_extensions(self, extensions: List[str]) -> List[str]:
        """
        Normalize file extensions for consistent comparison
        
        Args:
            extensions: List of file extensions (with or without dots)
            
        Returns:
            List of normalized extensions (lowercase, with dots)
        """
        normalized = []
        for ext in extensions:
            # Remove leading dot if present and convert to lowercase
            ext = ext.lower().lstrip('.')
            normalized.append(f'.{ext}')
        return normalized

    def _should_process_file(self, file_path: str, file_types: List[str] = [], exclude_folders: List[str] = []) -> bool:
        """
        Check if a file should be processed based on its type and location
        
        Args:
            file_path: Path to the file
            file_types: List of file extensions to include
            exclude_folders: List of folders to exclude
            
        Returns:
            Boolean indicating whether to process the file
        """
        path = Path(file_path)
        
        # Check excluded folders
        for folder in exclude_folders:
            # Normalize folder path
            folder = folder.strip('/')
            if folder in str(path.parent).split('/'):
                return False
        
        # If no file types specified, process all files
        if not file_types:
            return True
            
        # Check file extension
        return path.suffix.lower() in self._normalize_extensions(file_types)

    def _create_repo_archive(self) -> Tuple[str, str]:
        """
        Create a compressed archive of the git repository from worker node
        
        Returns:
            Tuple of (base64 encoded compressed repository, temp file path)
        """
        print("Creating compressed repository archive from worker node...")
        
        # Create a temporary file for the archive
        temp_archive = tempfile.NamedTemporaryFile(delete=False, suffix='.tar.gz')
        temp_archive_path = temp_archive.name
        
        # Create bare repository archive using tar directly
        try:
            subprocess.run([
                "tar", "czf", temp_archive_path,
                "-C", str(Path(self.repo_path).parent),
                Path(self.repo_path).name
            ], check=True, capture_output=True)
            
            # Read and encode the archive
            with open(temp_archive_path, 'rb') as f:
                archive_data = base64.b64encode(f.read()).decode('utf-8')
            
            print(f"Compressed archive size: {os.path.getsize(temp_archive_path) / 1024 / 1024:.2f} MB")
            return archive_data, temp_archive_path
        except Exception as e:
            if os.path.exists(temp_archive_path):
                os.unlink(temp_archive_path)
            raise e

    def _efficient_worker_cleanup(self) -> None:
        """
        Efficiently clean up repositories on all worker nodes
        """
        def cleanup_worker(_):
            worker_temp_dir = Path(self.broadcast_temp_dir.value)
            
            # Find all git repositories in temp directory
            repo_dirs = list(worker_temp_dir.glob("worker_*"))
            
            for repo_dir in repo_dirs:
                try:
                    # Create a temporary directory for atomic move
                    tmp_dir = Path(tempfile.mkdtemp(dir=worker_temp_dir))
                    
                    # Move existing directory to temp (faster than recursive delete)
                    repo_dir.rename(tmp_dir / "to_delete")
                    
                    # Delete in background
                    subprocess.Popen(
                        ["rm", "-rf", str(tmp_dir)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                except Exception as e:
                    # Fallback to synchronous delete
                    print(f"Cleanup error for {repo_dir}: {e}")
                    shutil.rmtree(repo_dir, ignore_errors=True)
            
            return True

        # Execute cleanup on each executor
        num_executors = len(self.spark.sparkContext._jsc.sc().statusTracker().getExecutorInfos()) - 1
        cleanup_rdd = self.spark.sparkContext.parallelize(range(num_executors), num_executors)
        cleanup_rdd.map(cleanup_worker).collect()

    def _distribute_repo_to_workers(self) -> None:
        """
        Distribute repository from worker node to all cluster nodes.
        Ensures cleanup of temporary files after distribution.
        """
        # First, clean up any existing repositories
        self._efficient_worker_cleanup()
        
        # Create and broadcast compressed repository
        print("Creating archive from worker node repository...")
        compressed_repo, temp_archive_path = self._create_repo_archive()
        
        try:
            # Broadcast the compressed data
            broadcast_repo = self.spark.sparkContext.broadcast(compressed_repo)
            
            def setup_worker_repo(_):
                """Setup repository on each cluster node"""
                try:
                    worker_temp_dir = Path(self.broadcast_temp_dir.value)
                    worker_temp_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Create temporary directory for archive
                    temp_zip_dir = worker_temp_dir / "temp_zip"
                    temp_zip_dir.mkdir(exist_ok=True)
                    temp_zip_path = temp_zip_dir / "repo.tar.gz"
                    
                    # Write compressed data to temporary file
                    archive_data = base64.b64decode(broadcast_repo.value)
                    with open(temp_zip_path, 'wb') as f:
                        f.write(archive_data)
                    
                    # Create a unique directory for this worker
                    worker_dir = worker_temp_dir / f"worker_{time.time_ns()}"
                    worker_dir.mkdir(parents=True)
                    
                    # Extract repository using tar
                    subprocess.run([
                        "tar", "xzf", str(temp_zip_path),
                        "-C", str(worker_dir)
                    ], check=True, capture_output=True)
                    
                    # Clean up the temporary zip file
                    temp_zip_path.unlink()
                    temp_zip_dir.rmdir()
                    
                    return True
                except Exception as e:
                    print(f"Error setting up worker repository: {e}")
                    return False
            
            # Create an RDD with one partition per executor
            num_executors = len(self.spark.sparkContext._jsc.sc().statusTracker().getExecutorInfos()) - 1
            dummy_rdd = self.spark.sparkContext.parallelize(range(num_executors), num_executors)
            
            # Execute repository setup on each executor
            setup_success = dummy_rdd.map(setup_worker_repo).collect()
            
            if not all(setup_success):
                raise RuntimeError("Failed to set up repository on all workers")
            
            # Unpersist the broadcast variable
            broadcast_repo.unpersist()
            
        finally:
            # Clean up the original temporary archive
            if os.path.exists(temp_archive_path):
                os.unlink(temp_archive_path)
                print("Cleaned up temporary archive on driver node")

    def _get_file_commit_date_distributed(self, file_info: Tuple[int, str]) -> Tuple[str, datetime]:
        """
        Get commit date for a file in distributed mode
        
        Args:
            file_info: Tuple of (partition_id, file_path)
            
        Returns:
            Tuple of (file_path, commit_date)
        """
        partition_id, file_path = file_info
        worker_temp_dir = Path(self.broadcast_temp_dir.value)
        
        # Find the repository in worker's temp directory
        worker_repos = list(worker_temp_dir.glob("worker_*"))
        if not worker_repos:
            raise RuntimeError(f"No repository found in {worker_temp_dir}")
        
        repo_path = str(worker_repos[0])
        
        cmd = [
            "git",
            "--git-dir", repo_path,
            "log",
            "-1",
            "--format=%cd",
            "--date=iso-strict",
            "--",
            file_path
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            date_str = result.stdout.strip()
            commit_date = datetime.fromisoformat(date_str) if date_str else None
            return file_path, commit_date
        except (subprocess.CalledProcessError, ValueError):
            return file_path, None

    def get_all_files(self, file_types: List[str] = [], exclude_folders: List[str] = []) -> List[str]:
        """
        Get list of all files in the repository, filtered by type and excluded folders.
        By default, processes all files in all folders if no filters are specified.
        
        Args:
            file_types: Optional list of file extensions to filter by (e.g., ['md', 'pdf'])
                       If empty, processes all file types
            exclude_folders: Optional list of folders to exclude (e.g., ['.git', 'node_modules'])
                           Paths are relative to repository root
            
        Returns:
            List of relative file paths
        """
        cmd = ["git", "ls-files"]
        output = subprocess.run(
            cmd,
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True
        ).stdout
        
        all_files = output.splitlines()
        
        # Filter files based on type and excluded folders
        return [
            f for f in all_files 
            if self._should_process_file(f, file_types, exclude_folders)
        ]

    def get_commit_dates_distributed(self, files: List[str], num_partitions: int = None) -> Dict[str, datetime]:
        """
        Get commit dates using distributed processing across cluster nodes
        
        Args:
            files: List of files to process
            num_partitions: Number of partitions for parallel processing
            
        Returns:
            Dictionary mapping file paths to their latest commit dates
        """
        if num_partitions is None:
            num_partitions = self.spark.sparkContext.defaultParallelism
        
        # First, distribute repository to all workers
        self._distribute_repo_to_workers()
        
        # Create RDD with partition IDs
        files_with_partition = [(i % num_partitions, f) for i, f in enumerate(files)]
        files_rdd = self.spark.sparkContext.parallelize(files_with_partition, num_partitions)
        
        # Process files
        results_rdd = files_rdd.map(self._get_file_commit_date_distributed)
        
        # Collect results
        results = results_rdd.collect()
        
        # Clean up after processing
        self._efficient_worker_cleanup()
        
        return {file_path: commit_date for file_path, commit_date in results if commit_date is not None}

"""
# Initialize with repository path (usually mounted in DBFS in Databricks)
repo_path = "/dbfs/mnt/your-mount-point/your-repo"
extractor = GitCommitDateExtractor(repo_path)

# Example 1: Process all files in all folders (default behavior)
all_files = extractor.get_all_files()
print(f"Found {len(all_files)} total files in repository")

# Example 2: Process only markdown and PDF files
md_pdf_files = extractor.get_all_files(file_types=['md', 'pdf'])
print(f"Found {len(md_pdf_files)} markdown and PDF files")

# Example 3: Process all files except those in specific folders
filtered_files = extractor.get_all_files(exclude_folders=['.git', 'node_modules', 'test'])
print(f"Found {len(filtered_files)} files (excluding specified folders)")

# Example 4: Process specific file types and exclude certain folders
specific_files = extractor.get_all_files(
    file_types=['md', 'pdf'],
    exclude_folders=['.git', 'node_modules']
)
print(f"Found {len(specific_files)} markdown and PDF files (excluding specified folders)")

# Get commit dates for the filtered files
commit_dates = extractor.get_commit_dates_distributed(specific_files)
"""
