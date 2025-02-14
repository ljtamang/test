import pytz
from datetime import datetime
from typing import Dict, List
import logging
import os
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType
from delta.tables import DeltaTable

# Global configurations
spark = SparkSession.builder \
    .appName("FileMetadataSync") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

FILE_METADATA_TABLE = "target_file_metadata"
logger = logging.getLogger(__name__)

# Define schemas at module level
UPLOAD_SUCCESS_SCHEMA = StructType([
    StructField("source_file_relative_path", StringType(), False),
    StructField("blob_path", StringType(), True),
    StructField("timestamp", StringType(), True)
])

FAILED_OPERATION_SCHEMA = StructType([
    StructField("source_file_relative_path", StringType(), False),
    StructField("error_message", StringType(), True)
])

DELETE_PATH_SCHEMA = StructType([
    StructField("source_file_relative_path", StringType(), False)
])

def get_standard_time() -> str:
    """Returns current time in ISO format with UTC timezone"""
    return datetime.now(pytz.UTC).isoformat()

def get_files_by_status(file_statuses: List[str]) -> List[str]:
    """Retrieve file paths from metadata table matching specified statuses"""
    if not file_statuses:
        return []
        
    quoted_statuses = ", ".join(f"'{status}'" for status in file_statuses)
    status_condition = f"file_status IN ({quoted_statuses})"
    
    # Use DeltaTable to read the table
    delta_table = DeltaTable.forName(spark, FILE_METADATA_TABLE)
    pending_files = (delta_table.toDF()
        .filter(status_condition)
        .select("source_file_relative_path")
        .collect())
    
    return [row.source_file_relative_path for row in pending_files]

def upload_to_azure(files_to_upload: List[str], local_repo_path: str) -> List[Dict]:
    """Upload files to Azure storage"""
    results = []
    for file_path in files_to_upload:
        try:
            if not file_path:  # Skip empty paths
                continue
                
            full_path = os.path.join(local_repo_path, file_path)
            # Azure upload logic here using full_path
            
            results.append({
                'success': True,
                'source_file_relative_path': file_path,
                'blob_path': f"/dbfs/mnt/dir/{os.path.basename(file_path).split('.')[0]}_057de.txt",
                'timestamp': get_standard_time()
            })
        except Exception as e:
            logger.error(f"Failed to upload {file_path}: {str(e)}")
            results.append({
                'success': False,
                'source_file_relative_path': file_path,
                'error_message': str(e)
            })
    
    return results

def delete_from_azure(files_to_delete: List[str], local_repo_path: str) -> List[Dict]:
    """Delete files from Azure storage"""
    results = []
    for file_path in files_to_delete:
        try:
            if not file_path:  # Skip empty paths
                continue
                
            full_path = os.path.join(local_repo_path, file_path)
            # Azure delete logic here using full_path
            
            results.append({
                'success': True,
                'source_file_relative_path': file_path
            })
        except Exception as e:
            logger.error(f"Failed to delete {file_path}: {str(e)}")
            results.append({
                'success': False,
                'source_file_relative_path': file_path,
                'error_message': str(e)
            })
    
    return results

def sync_metadata_after_upload(upload_results: List[Dict]) -> None:
    """Update metadata table after file upload operations using explicit DeltaTable"""
    if not upload_results:
        return

    # Get DeltaTable instance
    delta_table = DeltaTable.forName(spark, FILE_METADATA_TABLE)

    # Separate successful and failed uploads
    successful_uploads = [(
        result['source_file_relative_path'],
        result['blob_path'],
        result['timestamp']
    ) for result in upload_results if result['success']]
    
    failed_uploads = [(
        result['source_file_relative_path'],
        result['error_message']
    ) for result in upload_results if not result['success']]
    
    # Log summary
    total_files = len(upload_results)
    success_count = len(successful_uploads)
    fail_count = len(failed_uploads)
    logger.info(f"Upload summary: {success_count} of {total_files} files processed successfully, {fail_count} failed")
    
    # Update successful uploads
    if successful_uploads:
        try:
            success_df = spark.createDataFrame(
                successful_uploads,
                schema=UPLOAD_SUCCESS_SCHEMA
            )
            
            delta_table.alias("target") \
                .merge(
                    success_df.alias("updates"),
                    "target.source_file_relative_path = updates.source_file_relative_path"
                ) \
                .whenMatchedUpdate(set={
                    "blob_path": "updates.blob_path",
                    "last_upload_on": "to_timestamp(updates.timestamp)",
                    "error_message": "NULL",
                    "etl_updated_at": f"to_timestamp('{get_standard_time()}')"
                }) \
                .execute()
        except Exception as e:
            logger.error(f"Failed to update metadata for successful uploads: {str(e)}")
            print(f"Full error details: {str(e)}")
    
    # Update failed uploads
    if failed_uploads:
        try:
            failed_df = spark.createDataFrame(
                failed_uploads,
                schema=FAILED_OPERATION_SCHEMA
            )
            
            delta_table.alias("target") \
                .merge(
                    failed_df.alias("updates"),
                    "target.source_file_relative_path = updates.source_file_relative_path"
                ) \
                .whenMatchedUpdate(set={
                    "error_message": "updates.error_message",
                    "etl_updated_at": f"to_timestamp('{get_standard_time()}')"
                }) \
                .execute()
        except Exception as e:
            logger.error(f"Failed to update metadata for failed uploads: {str(e)}")
            print(f"Full error details: {str(e)}")

def sync_metadata_after_deletion(delete_results: List[Dict]) -> None:
    """Update metadata table after file deletion operations using explicit DeltaTable"""
    if not delete_results:
        return

    # Get DeltaTable instance
    delta_table = DeltaTable.forName(spark, FILE_METADATA_TABLE)

    # Separate successful and failed deletes
    successful_deletes = [
        (result['source_file_relative_path'],)
        for result in delete_results if result['success']
    ]
    
    failed_deletes = [(
        result['source_file_relative_path'],
        result['error_message']
    ) for result in delete_results if not result['success']]
    
    # Log summary
    total_files = len(delete_results)
    success_count = len(successful_deletes)
    fail_count = len(failed_deletes)
    logger.info(f"Deletion summary: {success_count} of {total_files} files processed successfully, {fail_count} failed")
    
    # Process successful deletions
    if successful_deletes:
        try:
            deletes_df = spark.createDataFrame(
                successful_deletes,
                schema=DELETE_PATH_SCHEMA
            )
            
            delta_table.alias("target") \
                .merge(
                    deletes_df.alias("deletes"),
                    "target.source_file_relative_path = deletes.source_file_relative_path"
                ) \
                .whenMatchedDelete() \
                .execute()
        except Exception as e:
            logger.error(f"Failed to update metadata for successful deletions: {str(e)}")
            print(f"Full error details: {str(e)}")
    
    # Update failed deletions
    if failed_deletes:
        try:
            failed_df = spark.createDataFrame(
                failed_deletes,
                schema=FAILED_OPERATION_SCHEMA
            )
            
            delta_table.alias("target") \
                .merge(
                    failed_df.alias("updates"),
                    "target.source_file_relative_path = updates.source_file_relative_path"
                ) \
                .whenMatchedUpdate(set={
                    "error_message": "updates.error_message",
                    "etl_updated_at": f"to_timestamp('{get_standard_time()}')"
                }) \
                .execute()
        except Exception as e:
            logger.error(f"Failed to update metadata for failed deletions: {str(e)}")
            print(f"Full error details: {str(e)}")

def process_pending_file_operations(local_repo_path: str) -> None:
    """Process all pending file operations and sync metadata table"""
    try:
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
            
    except Exception as e:
        logger.error(f"Failed to process pending file operations: {str(e)}")
        raise

def main() -> None:
    """Main entry point for the file metadata sync process"""
    try:
        # Add verification of Delta Lake setup
        print("Checking Delta Lake configuration...")
        print("Spark Version:", spark.version)
        print("SQL Extensions:", spark.conf.get("spark.sql.extensions", "Not configured"))
        print("SQL Catalog:", spark.conf.get("spark.sql.catalog.spark_catalog", "Not configured"))
        
        # Verify table is Delta format
        table_format = spark.sql(f"DESCRIBE DETAIL {FILE_METADATA_TABLE}").select("format").first()[0]
        print("Table format:", table_format)
        
        # Continue with main process
        local_repo_path = "/tmp/vfs"
        process_pending_file_operations(local_repo_path)
    except Exception as e:
        logger.error(f"File metadata sync process failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
