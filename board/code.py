from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, TimestampType
from pyspark.sql.functions import col, lit
from typing import List, Dict
from delta.tables import DeltaTable
from pathlib import Path
import common_utils  # For get_standarized_timestamp
import git_utils    # For get_file_git_info

# Define constant for table name at the top
FILE_METADATA_TABLE = "vfs.target_file_metadata"

# Initialize Spark session outside the function
spark = SparkSession.builder.getOrCreate()

# Define schema for enriched target_files DataFrame
TARGET_FILES_SCHEMA = StructType([
    StructField("file_relative_path", StringType(), False),  # Derived
    StructField("git_blob_hash", StringType(), False),       # Derived
    StructField("file_category", StringType(), False),       # Required (maps to category on insert)
    StructField("file_name", StringType(), True),            # Derived
    StructField("file_extension", StringType(), True)        # Derived
])

def enrich_file_info(target_files: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Enrich target_files with file_relative_path, git_blob_hash, file_name, and file_extension.
    
    Args:
        target_files: List of dictionaries containing file_path and file_category
        
    Returns:
        List of enriched dictionaries with file_relative_path, git_blob_hash, file_name, 
        file_extension, and file_category
    """
    enriched_files = []
    for file_info in target_files:
        file_path = file_info["file_path"]
        git_info = git_utils.get_file_git_info(file_path)  # Returns {'git_root_path': ..., 'git_blob_hash': ...}
        
        file_relative_path = str(Path(file_path).relative_to(git_info["git_root_path"]))
        git_blob_hash = git_info["git_blob_hash"]
        
        enriched_dict = {
            "file_relative_path": file_relative_path,
            "git_blob_hash": git_blob_hash,
            "file_category": file_info["file_category"],  # Required field
            "file_name": Path(file_relative_path).name,
            "file_extension": Path(file_relative_path).suffix.lstrip(".")
        }
        enriched_files.append(enriched_dict)
    
    return enriched_files

def merge_target_file_metadata(target_files: List[Dict[str, str]]) -> bool:
    """
    Merge target files into the target_file_metadata Delta table using Delta Lake MERGE operation
    
    Args:
        target_files: List of dictionaries containing file_path and file_category
        
    Returns:
        bool: True if merge operation successful, raises exception otherwise
        
    Conditions:
        1. New File (Insert):
           - When: file_relative_path in target_files but not in table
           - Action: Inserts new record with:
             - file_status = "pending_upload"
             - etl_created_at = current timestamp from common_utils.get_standarized_timestamp()
             - etl_updated_at = same current timestamp as etl_created_at
             - file_relative_path derived from file_path relative to git_root_path
             - git_blob_hash derived from git_utils.get_file_git_info(file_path)
             - category from file_category
             - file_name derived from file_relative_path (e.g., "file1.txt")
             - file_extension derived from file_relative_path (e.g., "txt")
             - Other fields (error_message, blob_path, last_upload_at, etc.) set to NULL
        
        2. Removed File (Update to Pending Delete):
           - When: file_relative_path in table but not in target_files
           - Action: Updates record with:
             - file_status = "pending_delete"
             - etl_updated_at = current timestamp
        
        3. Updated File (Update):
           - When: file_relative_path in both, but git_blob_hash differs
           - Action: Updates existing record with:
             - git_blob_hash = new git_blob_hash
             - file_status = "pending_update"
             - etl_updated_at = current timestamp
             - category, file_name, file_extension remain unchanged
             
    Notes:
        - Prints counts of inserted, updated (pending_update), and deleted records
        - Records marked 'pending_delete' are updated, not physically deleted
    """
    # Get current timestamp as ISO string
    current_time = common_utils.get_standarized_timestamp()
    
    # Enrich target_files
    enriched_target_files = enrich_file_info(target_files)
    
    # Create DataFrame from enriched target_files
    target_df = spark.createDataFrame(
        data=enriched_target_files,
        schema=TARGET_FILES_SCHEMA
    ).withColumn("current_time", col(lit(current_time)).cast(TimestampType()))
    
    # Get Delta table using constant
    delta_table = DeltaTable.forName(spark, FILE_METADATA_TABLE)
    
    try:
        # Single MERGE operation handling all three conditions
        merge_operation = delta_table.alias("target").merge(
            source=target_df.alias("source"),
            condition="target.file_relative_path = source.file_relative_path"
        ).whenMatchedUpdate(
            condition="target.git_blob_hash != source.git_blob_hash",
            set={
                "git_blob_hash": "source.git_blob_hash",
                "file_status": lit("pending_update"),
                "etl_updated_at": "source.current_time"
                # category, file_name, file_extension are intentionally not updated here
            }
        ).whenNotMatchedInsert(
            values={
                "file_relative_path": "source.file_relative_path",
                "git_blob_hash": "source.git_blob_hash",
                "file_status": lit("pending_upload"),
                "etl_created_at": "source.current_time",  # Set to current timestamp
                "etl_updated_at": "source.current_time",  # Same as etl_created_at
                "category": "source.file_category",       # Set category from file_category on insert
                "file_name": "source.file_name",          # Derived from file_relative_path
                "file_extension": "source.file_extension"  # Derived from file_relative_path
                # error_message, blob_path, last_upload_at, id are left as NULL by default
            }
        # Updates records that exist in the target table (vfs.target_file_metadata) 
        # but are not present in the source (target_files) to 'pending_delete'
        ).whenNotMatchedBySourceUpdate(
            set={
                "file_status": lit("pending_delete"),
                "etl_updated_at": "source.current_time"
            }
        )
        
        # Execute the merge and get operation metrics
        merge_operation.execute()
        
        # Get the latest operation metrics from Delta table history
        history = delta_table.history(1).collect()[0]
        num_inserted = history["operationMetrics"].get("numTargetRowsInserted", 0)
        num_updated = history["operationMetrics"].get("numTargetRowsUpdated", 0)
        num_deleted = history["operationMetrics"].get("numTargetRowsDeleted", 0)
        
        # Print the counts
        # Note: 'pending_delete' and 'pending_update' are counted as updates
        print(f"Merge operation completed:")
        print(f" - Files inserted (new with pending_upload): {num_inserted}")
        print(f" - Files updated (pending_update or pending_delete): {num_updated}")
        print(f" - Files deleted: {num_deleted}")
        
        return True
        
    except Exception as e:
        print(f"Error during merge operation: {str(e)}")
        raise

# Example usage
def main():
    # Sample target files with file_path and mandatory file_category
    target_files: List[Dict[str, str]] = [
        {'file_path': '/repo_root/path/to/file1.txt', 'file_category': 'docs'},
        {'file_path': '/repo_root/path/to/file2.py', 'file_category': 'scripts'}
    ]
    
    # Execute merge
    success = merge_target_file_metadata(target_files)
    if success:
        print("Merge completed successfully")

if __name__ == "__main__":
    main()
