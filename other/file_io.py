import os
import shutil
import concurrent.futures
from pathlib import Path
from typing import List, Optional

def copy_files(
    source_path: str,
    destination_path: str,
    file_types: Optional[List[str]] = None,
    exclude_folders: Optional[List[str]] = None,
    max_workers: int = None
) -> None:
    """
    Copy files from source to destination with support for file type filtering and folder exclusion.
    Uses multithreading for faster copying. If destination exists, it will be removed first.
    
    Args:
        source_path (str): Source directory path
        destination_path (str): Destination directory path
        file_types (List[str], optional): List of file extensions to copy (e.g., ['md', 'pdf'])
                                        Can be with or without dots
        exclude_folders (List[str], optional): List of folder names to exclude
        max_workers (int, optional): Maximum number of worker threads
    """
    # Convert paths to Path objects
    source = Path(source_path)
    destination = Path(destination_path)
    
    # Delete destination if it exists
    if destination.exists():
        if destination.is_file():
            destination.unlink()
        else:
            shutil.rmtree(destination)
    
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
    for root, dirs, files in os.walk(source):
        root_path = Path(root)
        
        # Skip excluded folders if any are specified
        if exclude_folders:
            dirs[:] = [d for d in dirs if not is_excluded_folder(root_path / d)]
        
        for file in files:
            src_file = root_path / file
            if should_copy_file(src_file):
                # Calculate relative path to maintain directory structure
                rel_path = src_file.relative_to(source)
                dest_file = destination / rel_path
                files_to_copy.append((src_file, dest_file))
    
    # Use ThreadPoolExecutor for parallel copying
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(copy_file, src, dst)
            for src, dst in files_to_copy
        ]
        
        # Wait for all copying tasks to complete
        concurrent.futures.wait(futures)
        
        # Check for any errors
        for future in futures:
            try:
                future.result()
            except Exception as e:
                print(f"Error during copy: {str(e)}")

# Example usage:
if __name__ == "__main__":
    # Copy all files (no filtering)
    copy_files(
        source_path="/tmp/your-files",
        destination_path="/mnt/path/to/persistent/storage/your-files"
    )
    
    # Copy only markdown and PDF files
    copy_files(
        source_path="/tmp/your-files",
        destination_path="/mnt/path/to/persistent/storage/your-files",
        file_types=["md", ".pdf", "MD", ".MD"],  # handles various formats
        exclude_folders=["node_modules", "venv"]  # optional folder exclusions
    )
