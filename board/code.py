from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType
from typing import List, Dict
from delta.tables import DeltaTable
from common_utils import get_standarized_timestamp

# Define constant for table name at the top
FILE_METADATA_TABLE = "vfs.target_file_metadata"

# Initialize Spark session outside the function
spark = SparkSession.builder.getOrCreate()

# Define schema for target_files DataFrame
TARGET_FILES_SCHEMA = StructType([
    StructField("file_relative_path", StringType(), False),
    StructField("git_blob_hash", StringType(), False)
])

def merge_target_file_metadata(target_files: List[Dict[str, str]]) -> bool:
    """
    Merge target files into the target_file_metadata Delta table using Delta Lake MERGE operation
    
    Args:
        target_files: List of dictionaries containing file_relative_path and git_blob_hash
        
    Returns:
        bool: True if merge operation successful, raises exception otherwise
        
    Conditions:
        1. New File (Insert):
           - When: file_relative_path in target_files but not in table
           - Action: Inserts new record with:
             - file_status = "active"
             - etl_created_at = current timestamp
             - etl_updated_at = current timestamp
             - All provided fields (file_relative_path, git_blob_hash)
        
        2. Removed File (Delete):
           - When: file_relative_path in table but not in target_files
           - Action: Deletes the record from the table
        
        3. Updated File (Update):
           - When: file_relative_path in both, but git_blob_hash differs
           - Action: Updates existing record with:
             - git_blob_hash = new git_blob_hash
             - file_status = "pending_update"
             - etl_updated_at = current timestamp
            
    Notes:
        - Prints counts of inserted, updated (pending_update), and deleted records
    """
    # Get current timestamp as ISO string
    current_time = get_standarized_timestamp()
    
    # Create DataFrame from target_files
    target_df = spark.createDataFrame(
        data=target_files,
        schema=TARGET_FILES_SCHEMA
    ).withColumn("current_time", lit(current_time))
    
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
            }
        ).whenNotMatchedInsert(
            values={
                "file_relative_path": "source.file_relative_path",
                "git_blob_hash": "source.git_blob_hash",
                "file_status": lit("active"),
                "etl_created_at": "source.current_time",
                "etl_updated_at": "source.current_time"
            }
        # Deletes records that exist in the target table (vfs.target_file_metadata) 
        # but are not present in the source (target_files), i.e., removed files
        ).whenNotMatchedBySourceDelete(
        )
        
        # Execute the merge and get operation metrics
        merge_operation.execute()
        
        # Get the latest operation metrics from Delta table history
        history = delta_table.history(1).collect()[0]
        num_inserted = history["operationMetrics"].get("numTargetRowsInserted", 0)
        num_updated = history["operationMetrics"].get("numTargetRowsUpdated", 0)
        num_deleted = history["operationMetrics"].get("numTargetRowsDeleted", 0)
        
        # Print the counts
        print(f"Merge operation completed:")
        print(f" - Files inserted (new): {num_inserted}")
        print(f" - Files updated (pending_update): {num_updated}")
        print(f" - Files deleted: {num_deleted}")
        
        return True
        
    except Exception as e:
        print(f"Error during merge operation: {str(e)}")
        raise

# Example usage
def main():
    # Sample target files
    target_files: List[Dict[str, str]] = [
        {'file_relative_path': 'path/to/file1.txt', 'git_blob_hash': 'abc123'},
        {'file_relative_path': 'path/to/file2.txt', 'git_blob_hash': 'def456'}
    ]
    
    # Execute merge
    success = merge_target_file_metadata(target_files)
    if success:
        print("Merge completed successfully")

if __name__ == "__main__":
    main()
