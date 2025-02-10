import os
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import hashlib
import shutil

def generate_unique_filename(file_path: str) -> str:
    """
    Generate a unique filename with hash suffix for RAG pipeline.
    """
    path_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
    original_name, file_extension = os.path.splitext(os.path.basename(file_path))
    return f"{original_name}_{path_hash}{file_extension}"

def upload_file_to_azure_storage(
    file_path: str,
    local_repo_path: str,
    mount_point: str,
    destination_folder: str
) -> Dict:
    """
    Copy a single file to Azure Storage mount point.
    Args:
        file_path: Path to the file to copy
        local_repo_path: Base path of the local repository for relative path calculation
        mount_point: Azure Storage mount point base path
        destination_folder: Folder path within the mount point
    """
    try:
        unique_filename = generate_unique_filename(file_path)
        relative_path = os.path.relpath(file_path, local_repo_path)
        dest_path = os.path.join(mount_point, destination_folder, unique_filename)
        
        # Create destination directory if it doesn't exist
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        # Copy the file
        shutil.copy2(file_path, dest_path)
        
        return {
            "original_file_name": os.path.basename(file_path),
            "source_file_relative_path": relative_path,
            "storage_file_name": unique_filename,
            "storage_path": dest_path,
            "upload_status": "success",
            "error_message": None,
            "upload_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except FileNotFoundError as e:
        return {
            "original_file_name": os.path.basename(file_path),
            "source_file_relative_path": None,
            "storage_file_name": None,
            "storage_path": None,
            "upload_status": "fail",
            "error_message": f"Source file not found: {str(e)}",
            "upload_timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "original_file_name": os.path.basename(file_path),
            "source_file_relative_path": relative_path,
            "storage_file_name": unique_filename,
            "storage_path": dest_path,
            "upload_status": "fail",
            "error_message": str(e),
            "upload_timestamp": datetime.now(timezone.utc).isoformat()
        }

def bulk_upload_to_azure_storage(
    source_files: List[str],
    local_repo_path: str,
    mount_point: str,
    destination_folder: str,
    max_workers: int = 4
) -> List[Dict]:
    """
    Perform bulk copy to Azure Storage mount point with metadata tracking.
    Args:
        source_files: List of file paths to copy
        local_repo_path: Base path of the local repository for relative path calculation
        mount_point: Azure Storage mount point base path
        destination_folder: Folder path within the mount point
        max_workers: Maximum number of concurrent copies
    Returns:
        List of dictionaries containing copy results for each file
    """
    upload_results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(
                upload_file_to_azure_storage,
                file_path,
                local_repo_path,
                mount_point,
                destination_folder
            ): file_path for file_path in source_files
        }
        
        for future in as_completed(future_to_file):
            try:
                result = future.result()
                upload_results.append(result)
            except Exception as e:
                file_path = future_to_file[future]
                upload_results.append({
                    "original_file_name": os.path.basename(file_path),
                    "source_file_relative_path": None,
                    "storage_file_name": None,
                    "storage_path": None,
                    "upload_status": "fail",
                    "error_message": f"Thread execution error: {str(e)}",
                    "upload_timestamp": datetime.now(timezone.utc).isoformat()
                })
    
    return upload_results

# Example usage
if __name__ == "__main__":
    source_files = [
        "/path/to/repo/documents/report1.pdf",
        "/path/to/repo/documents/report2.pdf",
        "/path/to/repo/documents/subfolder/report3.pdf"
    ]
    
    results = bulk_upload_to_azure_storage(
        source_files=source_files,
        local_repo_path="/path/to/repo",
        mount_point="/mnt/azure-storage",
        destination_folder="reports",
        max_workers=4
    )
