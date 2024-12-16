Complete Git Metadata Extractor with All Features

import os
import git
import psutil
from typing import Dict, List, Optional
from datetime import datetime
from git.repo import Repo
from git.exc import GitCommandError
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_optimal_workers(total_files: int) -> int:
    """
    Determine optimal number of workers based on system resources and workload.
    
    Args:
        total_files (int): Total number of files to be processed
        
    Returns:
        int: Recommended number of worker threads
    """
    # Get CPU and memory information
    cpu_count = psutil.cpu_count(logical=False)  # Physical CPU cores
    memory = psutil.virtual_memory()
    
    # Base calculations
    # Use physical CPU count as a base
    base_workers = cpu_count if cpu_count else 4  # Default to 4 if CPU count cannot be determined
    
    # Adjust based on memory availability
    memory_factor = 1.0
    if memory.percent > 80:  # High memory usage
        memory_factor = 0.5
    elif memory.percent < 40:  # Low memory usage
        memory_factor = 1.5
        
    # Adjust based on number of files
    if total_files < 100:
        file_factor = 0.5
    elif total_files > 1000:
        file_factor = 1.5
    else:
        file_factor = 1.0
        
    # Calculate final worker count
    optimal_workers = int(base_workers * memory_factor * file_factor)
    
    # Ensure at least 1 worker and no more than 2x CPU count
    return max(1, min(optimal_workers, cpu_count * 2 if cpu_count else 8))

def format_file_size(size_in_bytes: int) -> str:
    """
    Format file size to human readable format.
    
    Parameters:
    size_in_bytes (int): File size in bytes
    
    Returns:
    str: Formatted file size string with appropriate unit
    """
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    size = float(size_in_bytes)
    unit_index = 0
    
    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1
        
    return f"{size:.2f} {units[unit_index]}"

class GitMetadataExtractor:
    def __init__(self, repo_path: str, file_types: Optional[List[str]] = None, 
                 exclude_dirs: Optional[List[str]] = None, trust_repo: bool = False):
        """
        Initialize extractor with Git repository path and optional filters.
        
        Parameters:
        repo_path (str): Path to Git repository root
        file_types (List[str], optional): List of file extensions to process (without dots)
        exclude_dirs (List[str], optional): List of directory paths relative to repo_path to exclude
        trust_repo (bool): If True, adds the repository to Git's safe directories
        """
        self.repo_root = os.path.abspath(repo_path)
        self.file_types = {ext.lstrip('.').lower() for ext in file_types} if file_types else None
        
        # Normalize exclude_dirs paths relative to repo_root
        if exclude_dirs:
            self.exclude_dirs = set()
            for dir_path in exclude_dirs:
                # Remove leading/trailing slashes and normalize path separators
                normalized_path = dir_path.strip('/\\').replace('\\', '/')
                # Add the normalized path to the set
                if normalized_path:
                    self.exclude_dirs.add(normalized_path)
        else:
            self.exclude_dirs = {'.git'}
            
        # Verify that all exclude_dirs actually exist in the repository
        for dir_path in self.exclude_dirs:
            abs_dir_path = os.path.join(self.repo_root, dir_path)
            if not os.path.isdir(abs_dir_path):
                print(f"Warning: Excluded directory '{dir_path}' not found in repository")
        
        try:
            self.repo = Repo(self.repo_root)
        except git.exc.GitCommandError as e:
            if "dubious ownership" in str(e).lower():
                if trust_repo:
                    with git.Git().custom_environment(GIT_CONFIG_GLOBAL='/dev/null'):
                        git.Git().config("--global", "--add", "safe.directory", self.repo_root)
                    self.repo = Repo(self.repo_root)
                else:
                    raise git.exc.GitCommandError(
                        "Repository has dubious ownership. "
                        "To proceed, either:\n"
                        "1. Pass trust_repo=True to automatically add to safe.directory\n"
                        "2. Manually run: git config --global --add safe.directory '<path>'\n"
                        "3. Fix the ownership of the repository\n"
                        f"Repository path: {self.repo_root}",
                        -1
                    )
            else:
                raise

    def should_exclude_path(self, path: str) -> bool:
        """
        Check if a path should be excluded based on exclude_dirs.
        
        Parameters:
        path (str): Path to check (relative to repository root)
        
        Returns:
        bool: True if path should be excluded, False otherwise
        """
        # Normalize the path for comparison
        norm_path = path.strip('/\\').replace('\\', '/')
        
        # Check if the path or any of its parent directories should be excluded
        path_parts = norm_path.split('/')
        current_path = ''
        
        for part in path_parts:
            current_path = f"{current_path}/{part}" if current_path else part
            if current_path in self.exclude_dirs:
                return True
            
        return False

    def _get_commit_date(self, rel_path: str) -> Optional[str]:
        """
        Get the latest commit date for a single file using GitPython.
        Handles special characters in file paths.
        
        Parameters:
        rel_path (str): Relative path of the file from repository root
        
        Returns:
        Optional[str]: ISO formatted date string of the latest commit or None if not found
        """
        try:
            # Normalize path for Git (replace backslashes with forward slashes)
            normalized_path = rel_path.replace(os.sep, '/')
            
            commits = list(self.repo.iter_commits(paths=[normalized_path], max_count=1))
            if commits:
                return commits[0].committed_datetime.isoformat()
        except GitCommandError:
            try:
                from shlex import quote
                quoted_path = quote(normalized_path)
                commits = list(self.repo.iter_commits(f'--all -- {quoted_path}', max_count=1))
                if commits:
                    return commits[0].committed_datetime.isoformat()
            except Exception:
                pass
        except Exception:
            pass
        return None

    def _process_commit_dates(self, file_metadata_list: List[Dict]) -> None:
        """
        Process commit dates for multiple files in parallel using ThreadPoolExecutor.
        
        Parameters:
        file_metadata_list (List[Dict]): List of file metadata dictionaries to update with commit dates
        """
        def process_single_file(metadata: Dict) -> Dict:
            metadata['latest_commit_date'] = self._get_commit_date(metadata['relative_path'])
            return metadata

        # Calculate optimal number of workers based on file count
        optimal_workers = get_optimal_workers(len(file_metadata_list))
        
        with ThreadPoolExecutor(max_workers=optimal_workers) as executor:
            future_to_metadata = {
                executor.submit(process_single_file, metadata): metadata 
                for metadata in file_metadata_list
            }

            for future in as_completed(future_to_metadata):
                metadata = future_to_metadata[future]
                try:
                    updated_metadata = future.result()
                except Exception as e:
                    print(f"Error processing {metadata['relative_path']}: {str(e)}")

    def process_files(self, file_paths: Optional[List[str]] = None, 
                     include_commit_dates: bool = True, 
                     ignore_errors: bool = True) -> List[Dict]:
        """
        Process files with optional commit date extraction.
        
        Parameters:
        file_paths (Optional[List[str]]): List of file paths to process. If None, processes all files
        include_commit_dates (bool): Whether to extract commit dates for files
        ignore_errors (bool): Whether to continue processing when encountering errors
        
        Returns:
        List[Dict]: List of dictionaries containing file metadata
        """
        # Get all files if not provided
        if file_paths is None:
            file_paths = self.get_all_files()
        
        # Process basic metadata first
        metadata_list = []
        
        for file_path in file_paths:
            try:
                file_name = os.path.basename(file_path)
                file_stats = os.stat(file_path)
                rel_path = os.path.relpath(file_path, self.repo_root)
                
                # Skip if path should be excluded
                if self.should_exclude_path(rel_path):
                    continue
                
                metadata = {
                    'file_name': file_name,
                    'file_path': os.path.abspath(file_path),
                    'file_size': format_file_size(file_stats.st_size),
                    'file_type': os.path.splitext(file_name)[1].lower().lstrip('.'),
                    'relative_path': rel_path,
                    'latest_commit_date': None
                }
                metadata_list.append(metadata)
            except (OSError, ValueError) as e:
                if not ignore_errors:
                    raise
                continue
        
        # Process commit dates in parallel if needed
        if include_commit_dates:
            self._process_commit_dates(metadata_list)
                
        return metadata_list

    def get_all_files(self) -> List[str]:
        """
        Get all valid files in the repository, excluding specified directories.
        
        Returns:
        List[str]: List of absolute file paths
        """
        valid_files = []
        for root, _, files in os.walk(self.repo_root):
            # Get path relative to repo root for exclusion check
            rel_root = os.path.relpath(root, self.repo_root)
            
            # Skip excluded directories
            if self.should_exclude_path(rel_root):
                continue
                
            for file in files:
                if self.file_types is None or os.path.splitext(file)[1].lower().lstrip('.') in self.file_types:
                    valid_files.append(os.path.join(root, file))
                    
        return valid_files

# Example usage
if __name__ == "__main__":
    # Initialize extractor with excluded directories
    extractor = GitMetadataExtractor(
        repo_path="/path/to/repo",
        file_types=["py", "txt", "md"],  # Optional: filter by file types
        exclude_dirs=[
            "node_modules",           # Excludes /path/to/repo/node_modules
            "products/print-styles"   # Excludes /path/to/repo/products/print-styles
        ],
        trust_repo=True
    )
    
    # Process files and get metadata
    metadata = extractor.process_files()
