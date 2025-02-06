import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import hashlib

def generate_unique_filename(file_path: str) -> str:
    """
    Generate a unique filename with hash suffix for RAG pipeline.
    """
    path_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
    original_name, file_extension = os.path.splitext(os.path.basename(file_path))
    return f"{original_name}_{path_hash}{file_extension}"

def upload_file_to_azure_storage(
    file_path: str,
    mount_point: str,
    destination_folder: str
) -> Dict:
    """
    Upload a single file to Azure Storage with metadata for database tracking.
    """
    try:
        unique_filename = generate_unique_filename(file_path)
        relative_path = os.path.relpath(file_path, os.path.dirname(file_path))
        blob_path = os.path.join(mount_point, destination_folder, unique_filename)
        
        # Attempt the upload
        os.makedirs(os.path.dirname(blob_path), exist_ok=True)
        dbutils.fs.cp(file_path, blob_path)
        
        return {
            "original_file_name": os.path.basename(file_path),
            "source_file_relative_path": relative_path,
            "storage_file_name": unique_filename,
            "storage_blob_path": blob_path,
            "upload_status": "success",
            "error_message": None,
            "upload_timestamp": datetime.utcnow().isoformat()
        }
        
    except FileNotFoundError as e:
        return {
            "original_file_name": os.path.basename(file_path),
            "source_file_relative_path": None,
            "storage_file_name": None,
            "storage_blob_path": None,
            "upload_status": "fail",
            "error_message": f"Source file not found: {str(e)}",
            "upload_timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "original_file_name": os.path.basename(file_path),
            "source_file_relative_path": relative_path,
            "storage_file_name": unique_filename,
            "storage_blob_path": blob_path,
            "upload_status": "fail",
            "error_message": str(e),
            "upload_timestamp": datetime.utcnow().isoformat()
        }

def bulk_upload_to_azure_storage(
    source_files: List[str],
    mount_point: str,
    destination_folder: str,
    max_workers: int = 4
) -> List[Dict]:
    """
    Perform bulk upload to Azure Storage with metadata tracking.
    Args:
        source_files: List of file paths to upload
        mount_point: Azure Storage mount point
        destination_folder: Folder in container for uploads
        max_workers: Maximum number of concurrent uploads
    Returns:
        List of dictionaries containing upload results for each file
    """
    upload_results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(
                upload_file_to_azure_storage,
                file_path,
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
                    "storage_blob_path": None,
                    "upload_status": "fail",
                    "error_message": f"Thread execution error: {str(e)}",
                    "upload_timestamp": datetime.utcnow().isoformat()
                })
    
    return upload_results

# Example usage
if __name__ == "__main__":
    source_files = [
        "/path/to/documents/report1.pdf",
        "/path/to/documents/report2.pdf",
        "/path/to/documents/subfolder/report3.pdf"
    ]
    
    results = bulk_upload_to_azure_storage(
        source_files=source_files,
        mount_point="/dbfs/mnt/documents",
        destination_folder="reports",
        max_workers=4
    )
