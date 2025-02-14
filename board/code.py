from pyspark.sql.functions import current_timestamp, lit
from pyspark.sql import SparkSession, DataFrame
from datetime import datetime
from typing import Dict, List, Optional
import logging
import os

# Global configurations
spark = SparkSession.builder.appName("FileMetadataSync").getOrCreate()
FILE_METADATA_TABLE = "target_file_metadata"
logger = logging.getLogger(__name__)

def get_files_by_status(file_statuses: List[str]) -> List[str]:
    """
    Retrieve file paths from metadata table matching specified statuses
    
    Args:
        file_statuses: List of status values to filter by 
                      e.g. ['pending_upload', 'pending_update']
    
    Returns:
        List[str]: List of file_relative_paths matching any of the given statuses
    
    Example:
        >>> get_files_by_status(['pending_upload', 'pending_update'])
        ['path/to/file1.txt', 'path/to/file2.txt']
    """
    quoted_statuses = ", ".join(f"'{status}'" for status in file_statuses)
    status_condition = f"file_status IN ({quoted_statuses})"
    
    pending_files = (spark.table(FILE_METADATA_TABLE)
        .filter(status_condition)
        .select("file_relative_path")
        .collect())
    
    return [row.file_relative_path for row in pending_files]

def upload_to_azure(files_to_upload: List[str], local_repo_path: str) -> List[Dict]:
    """
    Upload files to Azure storage
    
    Args:
        files_to_upload: List of relative file paths to upload
        local_repo_path: Base directory path to construct full file paths
    
    Returns:
        List[Dict]: List of result dictionaries, one per file:
        For success case:
            {
                'success': True,
                'file_relative_path': str,
                'blob_path': str,
                'timestamp': datetime,
                'error': None
            }
        For failure case:
            {
                'success': False,
                'file_relative_path': str,
                'error': str
            }
    
    Example:
        >>> results = upload_to_azure(['file1.txt'], '/tmp/repo')
        >>> results[0]
        {
            'success': True,
            'file_relative_path': 'file1.txt',
            'blob_path': '/dbfs/mnt/dir/file1_057de.txt',
            'timestamp': datetime(2024, 2, 14, 10, 30),
            'error': None
        }
    """
    results = []
    for file_path in files_to_upload:
        try:
            full_path = os.path.join(local_repo_path, file_path)
            # Azure upload logic here using full_path
            
            results.append({
                'success': True,
                'file_relative_path': file_path,
                'blob_path': f"/dbfs/mnt/dir/{os.path.basename(file_path).split('.')[0]}_057de.txt",
                'timestamp': datetime.utcnow(),
                'error': None
            })
        except Exception as e:
            results.append({
                'success': False,
                'file_relative_path': file_path,
                'error': str(e)
            })
    
    return results

def delete_from_azure(files_to_delete: List[str], local_repo_path: str) -> List[Dict]:
    """
    Delete files from Azure storage
    
    Args:
        files_to_delete: List of relative file paths to delete
        local_repo_path: Base directory path to construct full file paths
    
    Returns:
        List[Dict]: List of result dictionaries, one per file:
        For success case:
            {
                'success': True,
                'file_relative_path': str,
                'error': None
            }
        For failure case:
            {
                'success': False,
                'file_relative_path': str,
                'error': str
            }
    
    Example:
        >>> results = delete_from_azure(['file1.txt'], '/tmp/repo')
        >>> results[0]
        {
            'success': True,
            'file_relative_path': 'file1.txt',
            'error': None
        }
    """
    results = []
    for file_path in files_to_delete:
        try:
            full_path = os.path.join(local_repo_path, file_path)
            # Azure delete logic here using full_path
            
            results.append({
                'success': True,
                'file_relative_path': file_path,
                'error': None
            })
        except Exception as e:
            results.append({
                'success': False,
                'file_relative_path': file_path,
                'error': str(e)
            })
    
    return results

def sync_metadata_after_upload(upload_results: List[Dict]) -> None:
    """
    Update metadata table after file upload operations
    
    Args:
        upload_results: List of upload operation results from upload_to_azure()
    
    Actions:
        For successful uploads:
        - Updates blob_path with new path
        - Updates last_upload_on with upload timestamp
        - Clears error_message
        - Updates etl_updated_at
        
        For failed uploads:
        - Updates error_message with failure reason
        - Updates etl_updated_at
        - Keeps existing blob_path and last_upload_on
    
    Example:
        >>> results = upload_to_azure(['file1.txt'], '/tmp/repo')
        >>> sync_metadata_after_upload(results)
        # Updates metadata table based on results
    """
    if not upload_results:
        return

    # Separate successful and failed uploads
    successful_uploads = [(
        result['file_relative_path'],
        result['blob_path'],
        result['timestamp'],
        None  # Clear error message for success
    ) for result in upload_results if result['success']]
    
    failed_uploads = [(
        result['file_relative_path'],
        result['error']
    ) for result in upload_results if not result['success']]
    
    # Log summary
    total_files = len(upload_results)
    success_count = len(successful_uploads)
    fail_count = len(failed_uploads)
    logger.info(f"Upload summary: {success_count} of {total_files} files processed successfully, {fail_count} failed")
    
    # Update successful uploads
    if successful_uploads:
        success_df = spark.createDataFrame(
            successful_uploads,
            ["file_relative_path", "blob_path", "upload_time", "error_message"]
        )
        
        (spark.table(FILE_METADATA_TABLE)
            .alias("target")
            .merge(
                success_df.alias("updates"),
                "target.file_relative_path = updates.file_relative_path"
            )
            .whenMatched()
            .updateExpr({
                "blob_path": "updates.blob_path",
                "last_upload_on": "updates.upload_time",
                "error_message": "updates.error_message",
                "etl_updated_at": "current_timestamp()"
            })
            .execute())
    
    # Update failed uploads
    if failed_uploads:
        failed_df = spark.createDataFrame(
            failed_uploads,
            ["file_relative_path", "error_message"]
        )
        
        (spark.table(FILE_METADATA_TABLE)
            .alias("target")
            .merge(
                failed_df.alias("updates"),
                "target.file_relative_path = updates.file_relative_path"
            )
            .whenMatched()
            .updateExpr({
                "error_message": "updates.error_message",
                "etl_updated_at": "current_timestamp()"
            })
            .execute())

def sync_metadata_after_deletion(delete_results: List[Dict]) -> None:
    """
    Update metadata table after file deletion operations
    
    Args:
        delete_results: List of deletion operation results from delete_from_azure()
    
    Actions:
        For successful deletions:
        - Removes the record from metadata table
        
        For failed deletions:
        - Updates error_message with failure reason
        - Updates etl_updated_at
        - Keeps existing record
    
    Example:
        >>> results = delete_from_azure(['file1.txt'], '/tmp/repo')
        >>> sync_metadata_after_deletion(results)
        # Updates metadata table based on results
    """
    if not delete_results:
        return

    # Separate successful and failed deletes
    successful_deletes = [
        result['file_relative_path']
        for result in delete_results if result['success']
    ]
    
    failed_deletes = [(
        result['file_relative_path'],
        result['error']
    ) for result in delete_results if not result['success']]
    
    # Log summary
    total_files = len(delete_results)
    success_count = len(successful_deletes)
    fail_count = len(failed_deletes)
    logger.info(f"Deletion summary: {success_count} of {total_files} files processed successfully, {fail_count} failed")
    
    # Process successful deletions
    if successful_deletes:
        deletes_df = spark.createDataFrame(
            [(path,) for path in successful_deletes],
            ["file_relative_path"]
        )
        
        (spark.table(FILE_METADATA_TABLE)
            .alias("target")
            .merge(
                deletes_df.alias("deletes"),
                "target.file_relative_path = deletes.file_relative_path"
            )
            .whenMatched()
            .delete()
            .execute())
    
    # Update failed deletions
    if failed_deletes:
        failed_df = spark.createDataFrame(
            failed_deletes,
            ["file_relative_path", "error_message"]
        )
        
        (spark.table(FILE_METADATA_TABLE)
            .alias("target")
            .merge(
                failed_df.alias("updates"),
                "target.file_relative_path = updates.file_relative_path"
            )
            .whenMatched()
            .updateExpr({
                "error_message": "updates.error_message",
                "etl_updated_at": "current_timestamp()"
            })
            .execute())

def process_pending_file_operations(local_repo_path: str) -> None:
    """
    Process all pending file operations and sync metadata table
    
    Args:
        local_repo_path: Base directory path used to construct full file paths
                        for Azure storage operations
    
    Actions:
        1. Gets files with pending upload/update status
        2. Gets files with pending delete status
        3. Processes uploads and updates metadata
        4. Processes deletions and updates metadata
    
    Example:
        >>> process_pending_file_operations('/tmp/repo')
        # Processes all pending operations and updates metadata table
    """
    # Get files for upload/update operations
    to_upload = get_files_by_status(['pending_upload', 'pending_update'])
    
    # Get files for deletion
    to_delete = get_files_by_status(['pending_delete'])

    # Process uploads
    if to_upload:
        upload_results = upload_to_azure(to_upload, local_repo_path)
        sync_metadata_after_upload(upload_results)

    # Process deletions
    if to_delete:
        delete_results = delete_from_azure(to_delete, local_repo_path)
        sync_metadata_after_deletion(delete_results)

# Example usage
def main():
    local_repo_path = "/tmp/vfs"
    process_pending_file_operations(local_repo_path)
