import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def upload_file_to_azure_storage(
    file_path: str,
    destination_folder: str,
    mount_point: str
) -> Dict:
    """
    Upload a single file to Azure Storage via Databricks mount point.
    
    Args:
        file_path (str): Local path to the file
        destination_folder (str): Destination folder in the container
        mount_point (str): Databricks mount point path
        
    Returns:
        Dict: Upload status and details
    """
    try:
        # Get the relative path of the file for storage path construction
        file_relative_path = os.path.basename(file_path)
        
        # Construct the destination path
        blob_path = os.path.join(mount_point, destination_folder, file_relative_path)
        
        # Ensure the destination directory exists
        os.makedirs(os.path.dirname(blob_path), exist_ok=True)
        
        # Copy the file to the mounted location
        dbutils.fs.cp(file_path, blob_path)
        
        # Construct the Azure storage URL
        blob_url = f"https://<storage-account>.blob.core.windows.net/<container>/{destination_folder}/{file_relative_path}"
        
        return {
            "file_path": file_path,
            "file_relative_path": file_relative_path,
            "upload_status": "success",
            "blob_path": blob_path,
            "blob_url": blob_url,
            "error_message": None,
            "upload_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "file_path": file_path,
            "file_relative_path": file_relative_path,
            "upload_status": "fail",
            "blob_path": None,
            "blob_url": None,
            "error_message": str(e),
            "upload_timestamp": datetime.utcnow().isoformat()
        }

def bulk_upload_to_azure_storage(
    source_files: List[str],
    destination_folder: str,
    mount_point: str,
    max_workers: int = 4
) -> List[Dict]:
    """
    Perform bulk upload of files to Azure Storage using concurrent processing.
    
    Args:
        source_files (List[str]): List of file paths to upload
        destination_folder (str): Destination folder in the container
        mount_point (str): Databricks mount point path
        max_workers (int): Maximum number of concurrent uploads
        
    Returns:
        List[Dict]: List of upload results for each file
    """
    upload_results = []
    total_files = len(source_files)
    completed_count = 0
    
    print(f"Starting upload of {total_files} files...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(
                upload_file_to_azure_storage,
                file_path,
                destination_folder,
                mount_point
            ): file_path for file_path in source_files
        }
        
        for future in as_completed(future_to_file):
            try:
                result = future.result()
                upload_results.append(result)
                completed_count += 1
                
                # Simple progress update
                if completed_count == total_files:
                    success_count = sum(1 for r in upload_results if r["upload_status"] == "success")
                    print(f"Upload complete. Successfully uploaded {success_count} of {total_files} files.")
                    
            except Exception as e:
                print(f"Error in upload task: {str(e)}")
    
    return upload_results

# Example usage:
if __name__ == "__main__":
    source_files = [
        "/path/to/your/files/document1.pdf",
        "/path/to/your/files/image1.jpg"
    ]
    destination_folder = "uploaded_files"
    mount_point = "/dbfs/mnt/your-container"
    
    results = bulk_upload_to_azure_storage(
        source_files=source_files,
        destination_folder=destination_folder,
        mount_point=mount_point
    )
