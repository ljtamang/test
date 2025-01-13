from pathlib import Path
from typing import Dict, List, Union, Optional
from datetime import datetime, timezone

def get_file_metadata(file_path: str, metadata_extracted_at: Optional[float] = None) -> Union[Dict[str, Union[str, int, float]], None]:
    """
    Extract file metadata with extraction timestamp.
    
    Args:
        file_path (str): The full path to the file
        metadata_extracted_at (float, optional): UTC timestamp when metadata was extracted
            If None, current UTC timestamp will be used
        
    Returns:
        Union[Dict[str, Union[str, int, float]], None]: Dictionary containing file metadata if successful, None if error
    """
    try:
        path_obj = Path(file_path)
        
        # Use provided timestamp or current UTC timestamp
        timestamp = metadata_extracted_at if metadata_extracted_at is not None else datetime.now(timezone.utc).timestamp()
        
        metadata = {
            'file_name': path_obj.name,
            'file_path': str(path_obj),
            'file_size_in_bytes': path_obj.stat().st_size,
            'file_type': path_obj.suffix[1:] if path_obj.suffix else 'No extension',
            'metadata_extracted_at': timestamp
        }
        return metadata
        
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found")
        return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def extract_metadata(file_paths: List[str]) -> List[Dict[str, Union[str, int, float]]]:
    """
    Extract metadata for multiple files using current timestamp.
    
    Args:
        file_paths (List[str]): List of file paths
        
    Returns:
        List[Dict[str, Union[str, int, float]]]: List of dictionaries containing metadata
    """
    batch_timestamp = datetime.now(timezone.utc).timestamp()
    
    all_metadata = []
    for file_path in file_paths:
        metadata = get_file_metadata(file_path, metadata_extracted_at=batch_timestamp)
        if metadata:
            all_metadata.append(metadata)
    return all_metadata
