from pathlib import Path
from typing import Dict, List, Union

def get_file_metadata(file_path: str) -> Union[Dict[str, Union[str, int]], None]:
    """
    Extract file name, path, size and type from a given file path.
    
    Args:
        file_path (str): The full path to the file
        
    Returns:
        Union[Dict[str, Union[str, int]], None]: Dictionary containing file metadata if successful, None if error
    """
    try:
        path_obj = Path(file_path)
        metadata = {
            'file_name': path_obj.name,
            'file_path': str(path_obj),
            'file_size_in_bytes': path_obj.stat().st_size,
            'file_type': path_obj.suffix[1:] if path_obj.suffix else 'No extension'
        }
        return metadata
        
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found")
        return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def extract_metadata(file_paths: List[str]) -> List[Dict[str, Union[str, int]]]:
    """
    Extract metadata for multiple files.
    
    Args:
        file_paths (List[str]): List of file paths
        
    Returns:
        List[Dict[str, Union[str, int]]]: List of dictionaries containing metadata
    """
    all_metadata = []
    for file_path in file_paths:
        metadata = get_file_metadata(file_path)
        if metadata:
            all_metadata.append(metadata)
    return all_metadata

# Example usage
if __name__ == "__main__":
    files = [
        "C:/Users/Documents/report.pdf",
        "./nonexistent.csv",
        "../Pictures/image.jpg",
        "./config"
    ]
    
    all_files_metadata = extract_metadata(files)
    
    print("\nMetadata for all files:")
    print("-" * 50)
    for idx, metadata in enumerate(all_files_metadata, 1):
        print(f"\nFile {idx}:")
        for key, value in metadata.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
