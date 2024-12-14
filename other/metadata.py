import os
import git
from typing import Dict, List, Optional
from datetime import datetime
from git.repo import Repo
from git.exc import GitCommandError
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import cpu_count

class GitMetadataExtractor:
    def __init__(self, repo_path: str, file_types: Optional[List[str]] = None, max_workers: Optional[int] = None, trust_repo: bool = False):
        """
        Initialize extractor with Git repository path and optional file type filter.
        
        Parameters:
        repo_path (str): Path to Git repository root
        file_types (List[str], optional): List of file extensions to process (without dots)
        max_workers (int, optional): Maximum number of worker threads. Defaults to number of CPUs * 2
        trust_repo (bool): If True, adds the repository to Git's safe directories
        """
        self.repo_root = os.path.abspath(repo_path)
        
        try:
            self.repo = Repo(self.repo_root)
        except git.exc.GitCommandError as e:
            if "dubious ownership" in str(e).lower():
                if trust_repo:
                    # Add repository to safe directories
                    with git.Git().custom_environment(GIT_CONFIG_GLOBAL='/dev/null'):
                        git.Git().config("--global", "--add", "safe.directory", self.repo_root)
                    # Try initializing repository again
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
        
        self.file_types = {ext.lstrip('.').lower() for ext in file_types} if file_types else None
        self.max_workers = max_workers or cpu_count() * 2
        
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
            
            # Use -- to separate options from file paths
            commits = list(self.repo.iter_commits(paths=[normalized_path], max_count=1))
            if commits:
                return commits[0].committed_datetime.isoformat()
        except GitCommandError as e:
            # Handle special characters in filename by using shell-quoted paths
            try:
                from shlex import quote
                quoted_path = quote(normalized_path)
                commits = list(self.repo.iter_commits(f'--all -- {quoted_path}', max_count=1))
                if commits:
                    return commits[0].committed_datetime.isoformat()
            except (GitCommandError, Exception) as e2:
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

    def process_files(self, file_paths: Optional[List[str]] = None, include_commit_dates: bool = True, ignore_errors: bool = True) -> List[Dict]:
        """
        Process files with optional commit date extraction.
        
        Parameters:
        file_paths (Optional[List[str]]): List of file paths to process. If None, processes all files
        include_commit_dates (bool): Whether to extract commit dates for files
        ignore_errors (bool): Whether to continue processing when encountering errors with individual files
        
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

# Example Usage
if __name__ == "__main__":
    # Example 1: Handling dubious ownership
    try:
        extractor = GitMetadataExtractor(
            repo_path="path/to/repo",
            file_types=["md"],
            trust_repo=False  # Default safe behavior
        )
    except git.exc.GitCommandError as e:
        if "dubious ownership" in str(e).lower():
            print("Retrying with trust_repo=True")
            extractor = GitMetadataExtractor(
                repo_path="path/to/repo",
                file_types=["md"],
                trust_repo=True  # Automatically add to safe.directory
            )
    
    # Example 2: Basic usage with default settings
    extractor = GitMetadataExtractor(
        repo_path="path/to/your/repo",
        file_types=["py", "js", "ts"]  # Only process Python and JavaScript/TypeScript files
    )
    
    # Get metadata including commit dates
    metadata = extractor.process_files(include_commit_dates=True)
    
    # Print sample output
    print("\nExample 1: Basic usage output")
    print("-" * 50)
    for item in metadata[:2]:  # Show first 2 files
        print(f"File: {item['file_name']}")
        print(f"Path: {item['relative_path']}")
        print(f"Size: {item['file_size']}")
        print(f"Type: {item['file_type']}")
        print(f"Last Commit: {item['latest_commit_date']}")
        print()

    # Example 2: Fast metadata without commit dates
    extractor = GitMetadataExtractor(
        repo_path="path/to/your/repo",
        file_types=["py"]  # Only Python files
    )
    
    # Get metadata without commit dates for faster processing
    fast_metadata = extractor.process_files(include_commit_dates=False)
    
    print("\nExample 2: Fast metadata without commit dates")
    print("-" * 50)
    for item in fast_metadata[:2]:  # Show first 2 files
        print(f"File: {item['file_name']}")
        print(f"Size: {item['file_size']}")
        print()

    # Example 3: Custom thread count for large repositories
    extractor = GitMetadataExtractor(
        repo_path="path/to/your/repo",
        file_types=["py", "js", "ts", "jsx", "tsx"],
        max_workers=8  # Use 8 threads for commit date extraction
    )
    
    # Process specific files only
    specific_files = [
        "src/main.py",
        "src/utils/helpers.js",
        "tests/test_main.py"
    ]
    
    metadata = extractor.process_files(
        file_paths=[os.path.join("path/to/your/repo", f) for f in specific_files],
        include_commit_dates=True
    )
    
    print("\nExample 3: Processing specific files with custom thread count")
    print("-" * 50)
    for item in metadata:
        print(f"File: {item['file_name']}")
        print(f"Last Commit: {item['latest_commit_date']}")
        print()

# Sample Output:
"""
Example 1: Basic usage output
--------------------------------------------------
File: main.py
Path: src/main.py
Size: 1.25 KB
Type: py
Last Commit: 2024-12-14T10:30:45+00:00

File: utils.js
Path: src/utils/utils.js
Size: 2.80 KB
Type: js
Last Commit: 2024-12-13T15:45:22+00:00

Example 2: Fast metadata without commit dates
--------------------------------------------------
File: api.py
Size: 3.45 KB

File: models.py
Size: 5.12 KB

Example 3: Processing specific files with custom thread count
--------------------------------------------------
File: main.py
Last Commit: 2024-12-14T10:30:45+00:00

File: helpers.js
Last Commit: 2024-12-12T09:15:33+00:00

File: test_main.py
Last Commit: 2024-12-13T16:20:11+00:00
"""
