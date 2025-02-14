from pyspark.sql.functions import current_timestamp, lit
from datetime import datetime
from typing import Dict, List
import logging
from pyspark.sql import SparkSession

# Global configurations
spark = SparkSession.builder.appName("FileMetadataSync").getOrCreate()
FILE_METADATA_TABLE = "target_file_metadata"
logger = logging.getLogger(__name__)

def upload_to_azure(files_to_upload: List[str], local_repo_path: str) -> List[Dict]:
    """
    Placeholder for Azure upload function
    Args:
        files_to_upload: List of relative file paths
        local_repo_path: Base path to create full file paths
    Returns: 
        List of results, one per file:
        [
            {
                'success': True,
                'file_relative_path': 'folder/file1.txt',
                'blob_path': '/dbfs/mnt/dir/file1_057de.txt',
                'timestamp': datetime object,
                'error': None
            },
            {
                'success': False,
                'file_relative_path': 'folder/file2.txt',
                'error': 'Failed to upload file'
            }
        ]
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
    Placeholder for Azure delete function
    Args:
        files_to_delete: List of relative file paths
        local_repo_path: Base path to create full file paths
    Returns:
        List of results, one per file:
        [
            {
                'success': True,
                'file_relative_path': 'folder/file1.txt',
                'error': None
            },
            {
                'success': False,
                'file_relative_path': 'folder/file2.txt',
                'error': 'Failed to delete file'
            }
        ]
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

def get_files_by_status(file_statuses: List[str]) -> List[str]:
    """
    Get list of file paths that have the specified status(es)
    
    Args:
        file_statuses: List of file statuses to filter by (e.g. ['pending_upload', 'pending_update'])
    
    Returns:
        List of file relative paths matching the given status(es)
    """
    status_condition = f"file_status IN ({','.join([f"'{status}'" for status in file_statuses])})"
    
    pending_files = (spark.table(FILE_METADATA_TABLE)
        .filter(status_condition)
        .select("file_relative_path")
        .collect())
    
    return [row.file_relative_path for row in pending_files]

def sync_metadata_after_upload(upload_results: List[Dict]) -> None:
    """
    Synchronize metadata table after Azure storage upload operations.
    - For successful uploads: Updates blob_path, last_upload_on, clears error_message
    - For failed uploads: Only updates error_message
    - Always updates etl_updated_at for any operation attempt
    """
    if not upload_results:
        return

    # Separate successful and failed uploads
    successful_uploads = [(
        result['file_relative_path'],
        result['blob_path'],
        result['timestamp'],
        None  # Clear error message for successful uploads
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
    
    # Handle successful uploads
    if successful_uploads:
        success_df = spark.createDataFrame(
            successful_uploads,
            ["file_relative_path", "blob_path", "upload_time", "error_message"]
        )
        
        # Update successful uploads with new blob_path, timestamp, and clear error
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
    
    # Handle failed uploads
    if failed_uploads:
        failed_df = spark.createDataFrame(
            failed_uploads,
            ["file_relative_path", "error_message"]
        )
        
        # Update only error message for failed uploads
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
    Synchronize metadata table after Azure storage deletion operations
    Removes records for successful deletions and updates error messages for failed ones
    """
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
    
    # Handle successful deletions
    if successful_deletes:
        deletes_df = spark.createDataFrame(
            [(path,) for path in successful_deletes],
            ["file_relative_path"]
        )
        
        # Delete successful records
        (spark.table(FILE_METADATA_TABLE)
            .alias("target")
            .merge(
                deletes_df.alias("deletes"),
                "target.file_relative_path = deletes.file_relative_path"
            )
            .whenMatched()
            .delete()
            .execute())
    
    # Handle failed deletions
    if failed_deletes:
        failed_df = spark.createDataFrame(
            failed_deletes,
            ["file_relative_path", "error_message"]
        )
        
        # Update error messages for failed deletes
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
    Process all pending file operations (uploads, updates, deletions) and 
    synchronize metadata table with Azure storage state
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

# Example usage:
def main():
    local_repo_path = "/tmp/vfs"
    process_pending_file_operations(local_repo_path)

if __name__ == "__main__":
    main()
