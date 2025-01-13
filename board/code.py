from pathlib import Path
from typing import Dict, List, Union, Optional
from datetime import datetime, timezone

def get_file_metadata(file_path: str, metadata_timestamp: Optional[float] = None) -> Union[Dict[str, Union[str, int, float]], None]:
    """
    Extract file metadata with timestamp.
    
    Args:
        file_path (str): The full path to the file
        metadata_timestamp (float, optional): UTC timestamp to use for metadata_updated_at
            If None, current UTC timestamp will be used
        
    Returns:
        Union[Dict[str, Union[str, int, float]], None]: Dictionary containing file metadata if successful, None if error
    """
    try:
        path_obj = Path(file_path)
        
        # Use provided timestamp or current UTC timestamp
        timestamp = metadata_timestamp if metadata_timestamp is not None else datetime.now(timezone.utc).timestamp()
        
        metadata = {
            'file_name': path_obj.name,
            'file_path': str(path_obj),
            'file_size_in_bytes': path_obj.stat().st_size,
            'file_type': path_obj.suffix[1:] if path_obj.suffix else 'No extension',
            'metadata_updated_at': timestamp
        }
        return metadata
        
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found")
        return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def extract_metadata(file_paths: List[str], metadata_timestamp: Optional[float] = None) -> List[Dict[str, Union[str, int, float]]]:
    """
    Extract metadata for multiple files.
    
    Args:
        file_paths (List[str]): List of file paths
        metadata_timestamp (float, optional): UTC timestamp to use for all files
            If None, current UTC timestamp will be used
        
    Returns:
        List[Dict[str, Union[str, int, float]]]: List of dictionaries containing metadata
    """
    # Use provided timestamp or create new one for batch
    batch_timestamp = metadata_timestamp if metadata_timestamp is not None else datetime.now(timezone.utc).timestamp()
    
    all_metadata = []
    for file_path in file_paths:
        metadata = get_file_metadata(file_path, metadata_timestamp=batch_timestamp)
        if metadata:
            all_metadata.append(metadata)
    return all_metadata

# Example usage:
if __name__ == "__main__":
    # Use current timestamp
    metadata_list1 = extract_metadata(["file1.txt", "file2.pdf"])
    
    # Use specific timestamp
    custom_timestamp = datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp()
    metadata_list2 = extract_metadata(["file1.txt", "file2.pdf"], metadata_timestamp=custom_timestamp)
