from typing import List, Dict, Tuple, Optional
from datetime import datetime
import os
import subprocess
from pathlib import Path
import tempfile
import time
import base64
import tarfile
import shutil
from pyspark.sql import SparkSession

class GitCommitDateExtractor:
    def __init__(self, repo_path: str, temp_dir: str = "/tmp/git_repos"):
        """
        Initialize the extractor with repository path and temporary directory
        
        Args:
            repo_path: Path to the original git repository
            temp_dir: Base directory for temporary worker copies
        """
        self.repo_path = repo_path
        self.temp_dir = Path(temp_dir)
        
        # Create temp directory if it doesn't exist
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Get Spark session without storing it as instance variable
        self.spark = SparkSession.builder.getOrCreate()
        
        # Broadcast paths as strings
        self._broadcast_paths()

    def _broadcast_paths(self):
        """Broadcast repository and temp directory paths to all workers"""
        self.broadcast_repo_path = self.spark.sparkContext.broadcast(str(self.repo_path))
        self.broadcast_temp_dir = self.spark.sparkContext.broadcast(str(self.temp_dir))

    def _normalize_extensions(self, extensions: List[str]) -> List[str]:
        """Normalize file extensions for consistent comparison"""
        return [f'.{ext.lower().lstrip(".")}' for ext in extensions]

    def _should_process_file(self, file_path: str, file_types: List[str] = [], exclude_folders: List[str] = []) -> bool:
        """Check if a file should be processed based on its type and location"""
        path = Path(file_path)
        
        # Check excluded folders
        for folder in exclude_folders:
            folder = folder.strip('/')
            if folder in str(path.parent).split('/'):
                return False
                
        # If no file types specified, process all files
        if not file_types:
            return True
            
        return path.suffix.lower() in self._normalize_extensions(file_types)

    def _create_repo_archive(self) -> str:
        """Create a base64 encoded archive of the repository"""
        temp_archive = tempfile.NamedTemporaryFile(delete=False, suffix='.tar.gz')
        
        try:
            # Create archive using tar
            subprocess.run([
                "tar", "czf", temp_archive.name,
                "-C", str(Path(self.repo_path).parent),
                Path(self.repo_path).name
            ], check=True, capture_output=True)
            
            # Read and encode archive
            with open(temp_archive.name, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        finally:
            os.unlink(temp_archive.name)

    @staticmethod
    def _setup_worker_repo(compressed_repo: str, temp_dir: str) -> str:
        """Set up repository on worker node and return its path"""
        worker_dir = Path(temp_dir) / f"worker_{time.time_ns()}"
        worker_dir.mkdir(parents=True)
        
        # Create temporary file for archive
        temp_archive = tempfile.NamedTemporaryFile(delete=False, suffix='.tar.gz')
        
        try:
            # Write and extract archive
            with open(temp_archive.name, 'wb') as f:
                f.write(base64.b64decode(compressed_repo))
            
            subprocess.run([
                "tar", "xzf", temp_archive.name,
                "-C", str(worker_dir)
            ], check=True, capture_output=True)
            
            return str(worker_dir)
        finally:
            os.unlink(temp_archive.name)

    @staticmethod
    def _get_commit_date(repo_path: str, file_path: str) -> Optional[datetime]:
        """Get the latest commit date for a file"""
        try:
            result = subprocess.run([
                "git",
                "--git-dir", f"{repo_path}/.git",
                "log",
                "-1",
                "--format=%cd",
                "--date=iso-strict",
                "--",
                file_path
            ], capture_output=True, text=True, check=True)
            
            date_str = result.stdout.strip()
            return datetime.fromisoformat(date_str) if date_str else None
        except (subprocess.CalledProcessError, ValueError):
            return None

    def get_all_files(self, file_types: List[str] = [], exclude_folders: List[str] = []) -> List[str]:
        """Get filtered list of files from repository"""
        cmd = ["git", "--git-dir", f"{self.repo_path}/.git", "ls-files"]
        output = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
        
        all_files = output.splitlines()
        return [
            f for f in all_files 
            if self._should_process_file(f, file_types, exclude_folders)
        ]

    def get_commit_dates_distributed(self, files: List[str], num_partitions: Optional[int] = None) -> Dict[str, datetime]:
        """Get commit dates using distributed processing"""
        if not files:
            return {}
            
        if num_partitions is None:
            num_partitions = self.spark.sparkContext.defaultParallelism
        
        # Create and broadcast repository archive
        compressed_repo = self._create_repo_archive()
        broadcast_repo = self.spark.sparkContext.broadcast(compressed_repo)
        broadcast_temp_dir = self.spark.sparkContext.broadcast(str(self.temp_dir))
        
        def process_partition(iterator):
            """Process a partition of files"""
            # Set up repository for this partition
            worker_repo_path = GitCommitDateExtractor._setup_worker_repo(
                broadcast_repo.value,
                broadcast_temp_dir.value
            )
            
            try:
                results = []
                for file_path in iterator:
                    commit_date = GitCommitDateExtractor._get_commit_date(worker_repo_path, file_path)
                    if commit_date:
                        results.append((file_path, commit_date))
                return results
            finally:
                # Clean up worker repository
                shutil.rmtree(worker_repo_path, ignore_errors=True)
        
        # Create RDD and process files
        files_rdd = self.spark.sparkContext.parallelize(files, num_partitions)
        results = files_rdd.mapPartitions(process_partition).collect()
        
        # Clean up broadcast variables
        broadcast_repo.unpersist()
        broadcast_temp_dir.unpersist()
        
        return dict(results)
 """
# Example usage

# Initialize with your repository path
repo_path = "/tmp/va.gov-team"
extractor = GitCommitDateExtractor(repo_path)

# Get only markdown files, excluding .git folder
files = extractor.get_all_files(
    file_types=['md'],
    exclude_folders=['.git']
)
print(f"Found {len(files)} markdown files")

# Get commit dates using distributed processing
commit_dates = extractor.get_commit_dates_distributed(files)

# Print results
for file_path, commit_date in commit_dates.items():
    print(f"{file_path}: {commit_date}")
"""
