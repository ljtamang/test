from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, BooleanType

DELETE_SCHEMA = StructType([
    StructField("file_relative_path", StringType(), False),
    StructField("success", BooleanType(), False),
    StructField("error_message", StringType(), True)
])

FILE_METADATA = target_file_metadata_table

def update_metadata_after_deletion(deletion_results):
    """
    Updates the target_file_metadata Delta table based on file deletion results.
    
    Args:
        deletion_results (list): List of dictionaries containing deletion operation results
    """
    # Create DataFrame from deletion results
    deletion_df = spark.createDataFrame(deletion_results, DELETE_SCHEMA)
    
    # Get current timestamp
    current_time = common_utils.get_standardized_timestamp()
    
    # Split into successful and failed deletions
    successful_deletions = deletion_df.filter(F.col("success") == True) \
        .select("file_relative_path")
    
    failed_deletions = deletion_df.filter(F.col("success") == False) \
        .select("file_relative_path", "error_message")
    
    # Handle successful deletions - delete records
    if successful_deletions.count() > 0:
        FILE_METADATA.alias("target") \
            .merge(
                successful_deletions.alias("source"),
                "target.file_relative_path = source.file_relative_path"
            ) \
            .whenMatchedDelete() \
            .execute()
    
    # Handle failed deletions - update records
    if failed_deletions.count() > 0:
        FILE_METADATA.alias("target") \
            .merge(
                failed_deletions.alias("source"),
                "target.file_relative_path = source.file_relative_path"
            ) \
            .whenMatchedUpdate(
                set = {
                    "etl_updated_at": current_time,
                    "error_message": F.col("source.error_message")
                }
            ) \
            .execute()

# Example usage:
# update_metadata_after_deletion(deletion_results)
