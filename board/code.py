import os
from pathlib import Path

def get_file_metadata(file_path):
    """
    Extract file name, path and size from a given file path.
    
    Args:
        file_path (str): The full path to the file
        
    Returns:
        dict: Dictionary containing file name, path and size
    """
    try:
        path_obj = Path(file_path)
        file_stats = os.stat(file_path)
        
        metadata = {
            'file_name': path_obj.name,
            'file_path': str(path_obj.absolute()),
            'file_size_in_bytes': file_stats.st_size
        }
        
        return metadata
        
    except FileNotFoundError:
        return f"Error: File '{file_path}' not found"
    except Exception as e:
        return f"Error: {str(e)}"

def extract_metadata(file_paths):
    """
    Extract metadata for multiple files.
    
    Args:
        file_paths (list): List of file paths
        
    Returns:
        list: List of dictionaries containing metadata for each file
    """
    all_metadata = []
    
    for file_path in file_paths:
        metadata = get_file_metadata(file_path)
        all_metadata.append(metadata)
    
    return all_metadata

# Example usage
if __name__ == "__main__":
    # List of example file paths
    files = [
        "C:/Users/Documents/report.pdf",
        "C:/Users/Documents/data.csv",
        "C:/Users/Pictures/image.jpg"
    ]
    
    # Get metadata for all files
    all_files_metadata = extract_metadata(files)
    
    # Print metadata for each file
    print("\nMetadata for all files:")
    print("-" * 50)
    for idx, metadata in enumerate(all_files_metadata, 1):
        print(f"\nFile {idx}:")
        if isinstance(metadata, dict):
            for key, value in metadata.items():
                print(f"{key.replace('_', ' ').title()}: {value}")
        else:
            print(metadata)  # Print error message if any
