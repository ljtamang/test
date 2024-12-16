import os
import shutil
import concurrent.futures
from pathlib import Path
from typing import List, Optional
import psutil
import time
import json

##############
# Save Metadata

import json
import os

def save_metadata_to_json(metadata: list, filepath: str, pretty_format: bool = False, overwrite: bool = True) -> None:
    """
    Save a list of dictionaries as a JSON file.
    
    Args:
        metadata (list): List of dictionaries containing metadata
        filepath (str): Path where the JSON file should be saved
        pretty_format (bool): If True, formats JSON with indentation for better readability
        overwrite (bool): If False, raises an error when file exists. If True, overwrites existing file
    
    Returns:
        None
    
    Raises:
        TypeError: If metadata is not a list
        FileExistsError: If file exists and overwrite is False
        IOError: If there's an error writing to the file
    """
    if not isinstance(metadata, list):
        raise TypeError("metadata must be a list of dictionaries")
    
    # Check if file exists and overwrite is False
    if not overwrite and os.path.exists(filepath):
        raise FileExistsError(f"File {filepath} already exists and overwrite is set to False")
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            if pretty_format:
                json.dump(metadata, f, indent=4, ensure_ascii=False)
            else:
                json.dump(metadata, f, ensure_ascii=False)
    except IOError as e:
        raise IOError(f"Error writing to file {filepath}: {str(e)}")


"""
EXample Usage
# This will raise FileExistsError if the file exists
save_metadata_to_json(metadata, "output.json", overwrite=False)

# This will overwrite any existing file
save_metadata_to_json(metadata, "output.json", overwrite=True)
"""

##########
def get_optimal_workers(total_files: int) -> int:
    """
    Determine optimal number of workers based on system resources and workload.
    
    Args:
        total_files (int): Total number of files to be copied
        
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
    
    # Set reasonable bounds
    return max(2, min(optimal_workers, 32))  # Between 2 and 32 workers

def delete_item(path: Path):
    """Delete a single file or empty directory"""
    try:
        if path.is_file():
            path.unlink()
        elif path.is_dir() and not any(path.iterdir()):  # Only delete if empty
            path.rmdir()
    except Exception as e:
        print(f"Error deleting {path}: {str(e)}")

def parallel_delete(path: Path, max_workers: int = None):
    """Delete directory contents in parallel"""
    if not path.exists():
        return

    if path.is_file():
        path.unlink()
        return

    # Collect all files and directories
    all_paths = []
    for root, dirs, files in os.walk(path, topdown=False):
        root_path = Path(root)
        # Add files first
        all_paths.extend(root_path / file for file in files)
        # Add directories
        all_paths.extend(root_path / dir for dir in dirs)
    # Add the root directory itself
    all_paths.append(path)

    # Use ThreadPoolExecutor for parallel deletion
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Delete files and empty directories in parallel
        list(executor.map(delete_item, all_paths))

def copy_files(
    source_path: str,
    destination_path: str,
    file_types: Optional[List[str]] = None,
    exclude_folders: Optional[List[str]] = None,
    max_workers: Optional[int] = None
) -> None:
    """
    Copy files from source to destination with automatic worker optimization.
    
    Args:
        source_path (str): Source directory path
        destination_path (str): Destination directory path
        file_types (List[str], optional): List of file extensions to copy
        exclude_folders (List[str], optional): List of folder names to exclude
        max_workers (int, optional): Maximum number of worker threads. If None, automatically determined
    """
    start_time = time.time()
    
    # Convert paths to Path objects
    source = Path(source_path)
    destination = Path(destination_path)
    
    # Delete destination if it exists using parallel deletion
    if destination.exists():
        print("Deleting existing destination...")
        delete_start = time.time()
        parallel_delete(destination, max_workers)
        print(f"Deletion completed in {time.time() - delete_start:.2f} seconds")
    
    # Create destination directory
    destination.mkdir(parents=True, exist_ok=True)
    
    def normalize_file_types(types: List[str]) -> List[str]:
        """Normalize file extensions to handle both with and without dots"""
        if types is None:
            return None
        return [ext.lower().strip('.') for ext in types]
    
    def should_copy_file(file_path: Path) -> bool:
        """Check if file should be copied based on its extension"""
        if file_types is None:
            return True
        normalized_types = normalize_file_types(file_types)
        return file_path.suffix.lower().strip('.') in normalized_types
    
    def is_excluded_folder(folder_path: Path) -> bool:
        """Check if folder should be excluded"""
        if not exclude_folders:
            return False
        return any(part in exclude_folders for part in folder_path.parts)
    
    def copy_file(src_file: Path, dest_file: Path):
        """Copy single file and create parent directories if needed"""
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dest_file)
    
    # Collect all files to copy
    files_to_copy = []
    total_size = 0
    
    for root, dirs, files in os.walk(source):
        root_path = Path(root)
        
        if exclude_folders:
            dirs[:] = [d for d in dirs if not is_excluded_folder(root_path / d)]
        
        for file in files:
            src_file = root_path / file
            if should_copy_file(src_file):
                total_size += src_file.stat().st_size
                rel_path = src_file.relative_to(source)
                dest_file = destination / rel_path
                files_to_copy.append((src_file, dest_file))
    
    # Determine optimal number of workers if not specified
    if max_workers is None:
        max_workers = get_optimal_workers(len(files_to_copy))
    
    print(f"Starting copy operation with {max_workers} workers")
    print(f"Total files to copy: {len(files_to_copy)}")
    print(f"Total size: {total_size / (1024*1024):.2f} MB")
    
    # Use ThreadPoolExecutor for parallel copying
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(copy_file, src, dst)
            for src, dst in files_to_copy
        ]
        
        # Wait for all copying tasks to complete
        completed = 0
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
                completed += 1
                if completed % 100 == 0:  # Progress update every 100 files
                    print(f"Copied {completed}/{len(files_to_copy)} files...")
            except Exception as e:
                print(f"Error during copy: {str(e)}")
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\nCopy operation completed:")
    print(f"Time taken: {duration:.2f} seconds")
    print(f"Average speed: {(total_size / (1024*1024)) / duration:.2f} MB/s")

# Example usage:
if __name__ == "__main__":
    # Example 1: Copy all files
    copy_files(
        source_path="/tmp/source",
        destination_path="/mnt/destination"
    )
    
    # Example 2: Copy specific file types with excluded folders
    copy_files(
        source_path="/tmp/source",
        destination_path="/mnt/destination",
        file_types=["md", "pdf", "py"],  # will match .md, .pdf, .py files
        exclude_folders=["venv", "node_modules"]
    )
    
    # Example 3: Copy with manual worker specification
    copy_files(
        source_path="/tmp/source",
        destination_path="/mnt/destination",
        max_workers=8  # manually specify worker count
    )
