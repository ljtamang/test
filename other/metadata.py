import os
import git
from typing import Dict, List, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import subprocess
from datetime import datetime

class GitMetadataExtractor:
    def __init__(self, repo_path: str, file_types: Optional[List[str]] = None):
        """
        Initialize extractor with Git repository path and optional file type filter.
        
        Parameters:
        repo_path (str): Path to Git repository root
        file_types (List[str], optional): List of file extensions to process (without dots)
        """
        self.repo = git.Repo(repo_path)
        self.repo_root = repo_path
        self.file_types = {ext.lstrip('.').lower() for ext in file_types} if file_types and len(file_types) > 0 else None
        
    def _batch_get_commit_dates(self, rel_paths: List[str], batch_size: int = 50) -> Dict[str, str]:
        """
        Get commit dates for multiple files in batch using git command directly.
        Uses batching and subprocess for better performance.
        """
        commit_dates = {}
        
        # Process files in batches to avoid command line length limitations
        for i in range(0, len(rel_paths), batch_size):
            batch = rel_paths[i:i + batch_size]
            
            try:
                # Use git log with custom format and parallel processing
                cmd = [
                    'git', '-C', self.repo_root,
                    'log', '--pretty=format:%H%x00%aI', '--name-only',
                    '--first-parent', '--no-merges',
                    '--', *batch
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                
                # Parse the output efficiently
                current_commit = None
                current_date = None
                
                for line in result.stdout.split('\n'):
                    if not line:
                        continue
                    if '\0' in line:  # This is a commit line
                        commit_hash, date = line.split('\0')
                        current_commit = commit_hash
                        current_date = date
                    else:  # This is a file path line
                        # Only update if we haven't seen this file before
                        if line not in commit_dates:
                            commit_dates[line] = current_date
                            
            except subprocess.SubprocessError:
                # Fall back to individual file processing if batch fails
                for path in batch:
                    try:
                        cmd = [
                            'git', '-C', self.repo_root,
                            'log', '-1', '--format=%aI',
                            '--', path
                        ]
                        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                        if result.stdout.strip():
                            commit_dates[path] = result.stdout.strip()
                    except:
                        continue
                        
        return commit_dates

    def process_files_batch(self, file_paths: Optional[List[str]] = None) -> List[Dict]:
        """Process all files with optimized batch processing."""
        # Get all files if not provided
        if file_paths is None:
            file_paths = self.get_all_files()
        
        # Prepare basic file metadata first
        metadata_dict = {}
        rel_paths = []
        
        for file_path in file_paths:
            try:
                file_name = os.path.basename(file_path)
                file_stats = os.stat(file_path)
                rel_path = os.path.relpath(file_path, self.repo_root)
                
                metadata_dict[rel_path] = {
                    'file_name': file_name,
                    'file_path': os.path.abspath(file_path),
                    'file_size': format_file_size(file_stats.st_size),
                    'file_type': os.path.splitext(file_name)[1].lower().lstrip('.'),
                    'relative_path': rel_path,
                    'latest_commit_date': None
                }
                rel_paths.append(rel_path)
            except:
                continue

        # Get commit dates in optimized batches
        commit_dates = self._batch_get_commit_dates(rel_paths)
        
        # Update metadata with commit dates
        for rel_path, metadata in metadata_dict.items():
            metadata['latest_commit_date'] = commit_dates.get(rel_path)

        return list(metadata_dict.values())

    def get_all_files(self) -> List[str]:
        """Get all valid files efficiently."""
        valid_files = []
        for root, _, files in os.walk(self.repo_root):
            if '.git' in root:
                continue
            for file in files:
                if self.file_types is None or os.path.splitext(file)[1].lower().lstrip('.') in self.file_types:
                    valid_files.append(os.path.join(root, file))
        return valid_files

def format_file_size(size_in_bytes: int) -> str:
    """Format file size to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} PB"
