import os
import git
from typing import Dict, List, Optional
from datetime import datetime
from git.repo import Repo
from git.exc import GitCommandError
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import cpu_count

class GitMetadataExtractor:
    def __init__(self, repo_path: str, file_types: Optional[List[str]] = None, max_workers: Optional[int] = None):
        """
        Initialize extractor with Git repository path and optional file type filter.
        
        Parameters:
        repo_path (str): Path to Git repository root
        file_types (List[str], optional): List of file extensions to process (without dots)
        max_workers (int, optional): Maximum number of worker threads. Defaults to number of CPUs * 2
        """
        self.repo = Repo(repo_path)
        self.repo_root = repo_path
        self.file_types = {ext.lstrip('.').lower() for ext in file_types} if file_types else None
        self.max_workers = max_workers or cpu_count() * 2
        
    def _get_commit_date(self, rel_path: str) -> Optional[str]:
        """
        Get the latest commit date for a single file using GitPython.
        
        Parameters:
        rel_path (str): Relative path of the file from repository root
        
        Returns:
        Optional[str]: ISO formatted date string of the latest commit or None if not found
        """
        try:
            # Use git log to get the latest commit for the file
            commits = list(self.repo.iter_commits(paths=rel_path, max_count=1))
            if commits:
                return commits[0].committed_datetime.isoformat()
        except GitCommandError:
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

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks and store futures
            future_to_metadata = {
                executor.submit(process_single_file, metadata): metadata 
                for metadata in file_metadata_list
            }

            # Process completed futures as they finish
            for future in as_completed(future_to_metadata):
                metadata = future_to_metadata[future]
                try:
                    updated_metadata = future.result()
                except Exception as e:
                    print(f"Error processing {metadata['relative_path']}: {str(e)}")

    def process_files(self, file_paths: Optional[List[str]] = None, include_commit_dates: bool = True) -> List[Dict]:
        """
        Process files with optional commit date extraction.
        
        Parameters:
        file_paths (Optional[List[str]]): List of file paths to process. If None, processes all files
        include_commit_dates (bool): Whether to extract commit dates for files
        
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
                continue
        
        # Process commit dates in parallel if needed
        if include_commit_dates:
            self._process_commit_dates(metadata_list)
                
        return metadata_list

    def get_all_files(self) -> List[str]:
        """
        Get all valid files in the repository.
        
        Returns:
        List[str]: List of absolute file paths
        """
        valid_files = []
        for root, _, files in os.walk(self.repo_root):
            # Skip .git directory
            if '.git' in root.split(os.sep):
                continue
                
            for file in files:
                if self.file_types is None or os.path.splitext(file)[1].lower().lstrip('.') in self.file_types:
                    valid_files.append(os.path.join(root, file))
                    
        return valid_files

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
