from pathlib import Path
from datetime import datetime
import hashlib
import subprocess
from typing import Dict, Any, Tuple

def get_metadata(file_info: Dict[str, str], git_root_path: str = "/path/to/tmp/va.gov-team", 
                blob_base_path: str = "https://myblob.blob.core.windows.net/container") -> Dict[str, Any]:
    """
    Generate metadata for a file including git information and blob storage details.
    
    Args:
        file_info (Dict[str, str]): Dictionary containing file_path and file_category
        git_root_path (str): Base path of the git repository
        blob_base_path (str): Base URL for blob storage
        
    Returns:
        Dict[str, Any]: Dictionary containing all metadata fields
    """
    file_path = Path(file_info["file_path"])
    file_category = file_info["file_category"]
    git_root_path = Path(git_root_path)
    
    # Extract file information
    file_name = file_path.name
    file_relative_path = str(file_path.relative_to(git_root_path))
    file_size = file_path.stat().st_size
    file_type = file_path.suffix.lstrip('.')
    
    # Get git information
    git_blob_hash, git_last_commit_date = get_git_info(file_path, git_root_path)
    
    # Get file timestamps
    current_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    file_stats = os.stat(file_path)
    created_timestamp = datetime.utcfromtimestamp(file_stats.st_ctime).strftime("%Y-%m-%dT%H:%M:%SZ")
    last_modified_timestamp = datetime.utcfromtimestamp(file_stats.st_mtime).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    metadata = {
        "file_name": file_name,
        "file_relative_path": file_relative_path,
        "git_root_path": git_root_path,
        "blob_base_path": blob_base_path,
        "file_size": file_size,
        "file_type": file_type,
        "file_category": file_category,
        "git_blob_hash": git_blob_hash,
        "created_timestamp": created_timestamp,
        "last_modified_timestamp": last_modified_timestamp,
        "git_last_commit_date": git_last_commit_date,
        "last_blob_update": current_time,
        "last_indexed_timestamp": None,
        "index_action": "Add",
        "index_status": "Pending"
    }
    
    return metadata

def get_git_info(file_path: Path) -> dict[str, str | None]:
    """
    Get git blob hash and last commit date for a file.
    Determines git root path from the file path.
    
    Args:
        file_path (Path): Path to the file
        
    Returns:
        dict: Dictionary with git_blob_hash and git_last_commit_date (None if commands fail)
    """
    try:
        # Get git root path
        git_root = subprocess.check_output(
            ['git', 'rev-parse', '--show-toplevel'],
            cwd=str(file_path.parent),
            universal_newlines=True
        ).strip()
        git_root_path = Path(git_root)
        
        rel_path = file_path.relative_to(git_root_path)
        
        git_blob_hash = subprocess.check_output(
            ['git', 'hash-object', str(file_path)],
            cwd=str(git_root_path),
            universal_newlines=True
        ).strip()
        
        git_last_commit_date = subprocess.check_output(
            ['git', 'log', '-1', '--format=%aI', '--', str(rel_path)],
            cwd=str(git_root_path),
            universal_newlines=True
        ).strip()
        
        return {
            "git_blob_hash": git_blob_hash,
            "git_last_commit_date": git_last_commit_date,
            "git_root_path": str(git_root_path)
        }
        
    except (subprocess.SubprocessError, ValueError):
        return {
            "git_blob_hash": None,
            "git_last_commit_date": None,
            "git_root_path": None
        }

# Example usage:
def process_files(file_list):
    """
    Process a list of files and generate metadata for each.
    
    Args:
        file_list (List[Dict]): List of dictionaries containing file information
        
    Returns:
        List[Dict]: List of metadata dictionaries for each file
    """
    metadata_list = []
    
    for file_info in file_list:
        try:
            metadata = get_metadata(file_info)
            metadata_list.append(metadata)
        except Exception as e:
            print(f"Error processing file {file_info['file_path']}: {str(e)}")
            
    return metadata_list

# Example of how to use the functions:
if __name__ == "__main__":
    files = [
        {
            "file_path": "file/full/path/filename.txt",
            "file_category": "research-finding"
        },
        {
            "file_path": "file/full/path/filename2.txt",
            "file_category": "research-finding"
        }
    ]
    
    results = process_files(files)
    for metadata in results:
        print(metadata)
