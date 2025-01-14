from pathlib import Path
from typing import Dict, List, Union
from datetime import datetime

def get_file_metadata(file_path: str, local_base_path: str = "", blob_base_path: str = "") -> Union[Dict[str, Union[str, int, dict]], None]:
    """
    Extract file metadata including storage paths from a given file path.
    
    Args:
        file_path (str): The full path to the file
        local_base_path (str): Base path for local storage
        blob_base_path (str): Base path for blob storage
        
    Returns:
        Union[Dict[str, Union[str, int, dict]], None]: Dictionary containing file metadata if successful, None if error
    """
    try:
        path_obj = Path(file_path)
        
        # Calculate relative path based on local_base_path
        try:
            relative_path = str(path_obj.relative_to(local_base_path))
        except ValueError:
            relative_path = path_obj.name
            
        metadata = {
            'file_name': path_obj.name,
            'file_path': str(path_obj),
            'file_size_in_bytes': path_obj.stat().st_size,
            'file_type': path_obj.suffix[1:] if path_obj.suffix else 'No extension',
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'relative_path': relative_path,
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

def extract_metadata(file_paths: List[str], local_base_path: str = "", blob_base_path: str = "") -> List[Dict[str, Union[str, int, dict]]]:
    """
    Extract metadata for multiple files.
    
    Args:
        file_paths (List[str]): List of file paths
        local_base_path (str): Base path for local storage
        blob_base_path (str): Base path for blob storage
        
    Returns:
        List[Dict[str, Union[str, int, dict]]]: List of dictionaries containing metadata
    """
    all_metadata = []
    for file_path in file_paths:
        metadata = get_file_metadata(file_path, local_base_path, blob_base_path)
        if metadata:
            all_metadata.append(metadata)
    return all_metadata

# Example usage
if __name__ == "__main__":
    local_base = "C:/Users/Documents"
    blob_base = "container/data"
    
    files = [
        "C:/Users/Documents/report.pdf",
        "./nonexistent.csv",
        "../Pictures/image.jpg",
        "./config"
    ]
    
    all_files_metadata = extract_metadata(files, local_base, blob_base)
    
    print("\nMetadata for all files:")
    print("-" * 50)
    for idx, metadata in enumerate(all_files_metadata, 1):
        print(f"\nFile {idx}:")
        for key, value in metadata.items():
            if isinstance(value, dict):
                print(f"\n{key.replace('_', ' ').title()}:")
                for sub_key, sub_value in value.items():
                    print(f"  {sub_key.replace('_', ' ').title()}: {sub_value}")
            else:
                print(f"{key.replace('_', ' ').title()}: {value}")
