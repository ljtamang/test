import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Union

def delete_azure_mounted_file(file_info: Dict[str, str]) -> Dict[str, Union[str, bool]]:
    """
    Delete a single file from Azure mounted storage.
    
    Args:
        file_info (Dict[str, str]): Dictionary containing:
            - file_relative_path: relative path of the file
            - blob_path: full path in the mounted storage
            
    Returns:
        Dict: Deletion result containing:
            - file_relative_path: relative path of the file
            - success: boolean indicating if deletion was successful
            - error_message: string containing error message if deletion failed (optional)
    """
    result = {
        'file_relative_path': file_info['file_relative_path'],
        'success': False
    }
    
    try:
        # Check if file exists
        if not os.path.exists(file_info['blob_path']):
            raise FileNotFoundError(f"File not found: {file_info['blob_path']}")
        
        # Delete the file
        os.remove(file_info['blob_path'])
        result['success'] = True
        
    except FileNotFoundError as e:
        result['error_message'] = str(e)
    except PermissionError as e:
        result['error_message'] = f"Permission denied: {str(e)}"
    except Exception as e:
        result['error_message'] = f"Unexpected error: {str(e)}"
    
    return result

def batch_delete_azure_mounted_files(
    files_to_delete: List[Dict[str, str]], 
    max_workers: int = 5
) -> List[Dict[str, Union[str, bool]]]:
    """
    Delete multiple files from Azure mounted storage using multithreading.
    
    Args:
        files_to_delete (List[Dict[str, str]]): List of dictionaries containing:
            - file_relative_path: relative path of the file
            - blob_path: full path in the mounted storage
        max_workers (int, optional): Maximum number of concurrent deletion threads.
            Defaults to 5.
            
    Returns:
        List[Dict]: List of dictionaries containing deletion results.
        Each dict contains:
            - file_relative_path: relative path of the file
            - success: boolean indicating if deletion was successful
            - error_message: string containing error message if deletion failed (optional)
    """
    deletion_results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all deletion tasks
        future_to_file = {
            executor.submit(delete_azure_mounted_file, file_info): file_info
            for file_info in files_to_delete
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_file):
            result = future.result()
            deletion_results.append(result)
    
    return deletion_results

# Example execution with both success and failure cases
if __name__ == "__main__":
    # Example data with both existing and non-existing files
    files_to_delete = [
        {
            'file_relative_path': 'base/path/to/existing_file1.txt',
            'blob_path': '/dbfs/mnt/vac20vddmsn/path/to/existing_file1.txt',
        },
        {
            'file_relative_path': 'base/path/to/nonexistent_file.txt',
            'blob_path': '/dbfs/mnt/vac20vddmsn/path/to/nonexistent_file.txt',
        },
        {
            'file_relative_path': 'base/path/to/existing_file2.txt',
            'blob_path': '/dbfs/mnt/vac20vddmsn/path/to/existing_file2.txt',
        }
    ]

    print("1. Single File Deletion Examples:")
    print("\na) Attempting to delete an existing file:")
    result = delete_azure_mounted_file(files_to_delete[0])
    print(f"""
    File: {result['file_relative_path']}
    Success: {result['success']}
    {'Error: ' + result['error_message'] if not result['success'] else 'Status: File successfully deleted'}
    """)

    print("\nb) Attempting to delete a non-existent file:")
    result = delete_azure_mounted_file(files_to_delete[1])
    print(f"""
    File: {result['file_relative_path']}
    Success: {result['success']}
    {'Error: ' + result['error_message'] if not result['success'] else 'Status: File successfully deleted'}
    """)

    print("\n2. Batch Deletion Example:")
    print("\nAttempting to delete multiple files:")
    batch_results = batch_delete_azure_mounted_files(files_to_delete, max_workers=5)
    
    for result in batch_results:
        print(f"""
    File: {result['file_relative_path']}
    Success: {result['success']}
    {'Error: ' + result['error_message'] if not result['success'] else 'Status: File successfully deleted'}
    """)

# Example output would look like:
"""
1. Single File Deletion Examples:

a) Attempting to delete an existing file:

    File: base/path/to/existing_file1.txt
    Success: True
    Status: File successfully deleted
    

b) Attempting to delete a non-existent file:

    File: base/path/to/nonexistent_file.txt
    Success: False
    Error: File not found: /dbfs/mnt/vac20vddmsn/path/to/nonexistent_file.txt
    

2. Batch Deletion Example:

Attempting to delete multiple files:

    File: base/path/to/existing_file1.txt
    Success: True
    Status: File successfully deleted
    

    File: base/path/to/nonexistent_file.txt
    Success: False
    Error: File not found: /dbfs/mnt/vac20vddmsn/path/to/nonexistent_file.txt
    

    File: base/path/to/existing_file2.txt
    Success: True
    Status: File successfully deleted
"""
