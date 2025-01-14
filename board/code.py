from pathlib import Path
from typing import Dict, List, Union
from datetime import datetime, timezone
import subprocess

def get_git_info(file_path: str) -> Dict[str, Union[str, None]]:
    """
    Get Git metadata for a file.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        Dict[str, Union[str, None]]: Dictionary with git metadata:
            - git_root: Root directory of git repository
            - git_relative_path: Path relative to git root
            - git_blob_hash: Hash of file content
            - git_last_commit: Hash of last commit that modified the file
            Returns None values if not in git repo or errors occur
    """
    try:
        # Get git root
        git_root = subprocess.check_output(
            ['git', 'rev-parse', '--show-toplevel'],
            cwd=str(Path(file_path).parent),
            universal_newlines=True
        ).strip()
        
        # Get path relative to git root
        git_relative_path = str(Path(file_path).resolve().relative_to(Path(git_root)))
        
        # Get file's blob hash
        git_blob_hash = subprocess.check_output(
            ['git', 'hash-object', file_path],
            universal_newlines=True
        ).strip()
        
        # Get last commit hash for this file
        git_last_commit = subprocess.check_output(
            ['git', 'rev-list', '-1', 'HEAD', git_relative_path],
            cwd=git_root,
            universal_newlines=True
        ).strip()
        
        return {
            'git_root': git_root,
            'git_relative_path': git_relative_path,
            'git_blob_hash': git_blob_hash,
            'git_last_commit': git_last_commit
        }
    except subprocess.CalledProcessError:
        return {
            'git_root': None,
            'git_relative_path': None,
            'git_blob_hash': None,
            'git_last_commit': None
        }

def get_file_metadata(
    file_path: str, 
    local_base_path: str = "", 
    blob_base_path: str = "",
    updated_at: float = None,
    git_info: Dict[str, str] = None
) -> Union[Dict[str, Union[str, int, float, dict]], None]:
    """
    Extract file metadata including storage paths from a given file path.
    
    Args:
        file_path (str): The full path to the file
        local_base_path (str): Base path for local storage
        blob_base_path (str): Base path for blob storage
        updated_at (float): Unix timestamp in UTC. If None, current UTC timestamp is used
        git_info (Dict[str, str]): Git metadata from get_git_info(). If None, git fields will be None
        
    Returns:
        Union[Dict[str, Union[str, int, float, dict]], None]: Dictionary containing metadata if successful, None if error
    """
    try:
        path_obj = Path(file_path)
        
        # Use provided timestamp or current UTC timestamp
        if updated_at is None:
            updated_at = datetime.now(timezone.utc).timestamp()
            
        # Calculate relative path based on local_base_path
        try:
            relative_path = str(path_obj.relative_to(local_base_path))
        except ValueError:
            relative_path = path_obj.name
            
        # Use provided git info or set to None
        git_info = git_info or {
            'git_root': None,
            'git_relative_path': None,
            'git_blob_hash': None,
            'git_last_commit': None
        }
            
        metadata = {
            'file_name': path_obj.name,
            'file_path': str(path_obj),
            'file_size_in_bytes': path_obj.stat().st_size,
            'file_type': path_obj.suffix[1:] if path_obj.suffix else 'No extension',
            'updated_at': updated_at,
            'relative_path': relative_path,
            'git_blob_hash': git_info['git_blob_hash'],
            'git_relative_path': git_info['git_relative_path'],
            'git_root': git_info['git_root'],
            'git_last_commit': git_info['git_last_commit'],
            'local': {
                'base_path': local_base_path,
                'full_path': str(path_obj)
            },
            'blob': {
                'base_path': blob_base_path,
                'full_path': str(Path(blob_base_path) / relative_path)
            }
        }
        return metadata
        
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found")
        return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def extract_metadata(
    file_paths: List[str], 
    local_base_path: str = "", 
    blob_base_path: str = ""
) -> List[Dict[str, Union[str, int, float, dict]]]:
    """
    Extract metadata for multiple files.
    
    Args:
        file_paths (List[str]): List of file paths
        local_base_path (str): Base path for local storage
        blob_base_path (str): Base path for blob storage
        
    Returns:
        List[Dict[str, Union[str, int, float, dict]]]: List of dictionaries containing metadata
    """
    # Get current UTC timestamp once for all files
    current_utc = datetime.now(timezone.utc).timestamp()
    
    all_metadata = []
    for file_path in file_paths:
        # Get git info for the file
        git_info = get_git_info(file_path)
        
        metadata = get_file_metadata(
            file_path, 
            local_base_path, 
            blob_base_path,
            updated_at=current_utc,
            git_info=git_info
        )
        if metadata:
            all_metadata.append(metadata)
    return all_metadata
