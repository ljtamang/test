# Import required functions
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import StructType, StructField, StringType, TimestampType
from pyspark.sql.functions import to_timestamp, lit
from typing import List, Dict
from datetime import datetime
import pytz

def get_timestamp(use_est: bool = True) -> str:
    utc_time = datetime.now(pytz.UTC)
    if use_est:
        est_timezone = pytz.timezone('US/Eastern')
        est_time = utc_time.astimezone(est_timezone)
        return est_time.isoformat()
    return utc_time.isoformat()

def first_time_load_file_metadata_to_table(metadata_list: List[Dict]) -> None:
    """
    Load file metadata into vfs_raw.file_metadata Delta table using overwrite mode.
    
    Parameters:
        metadata_list (List[Dict]): List of dictionaries containing file metadata.
                                  Required keys: file_name, file_relative_path, file_extension,
                                  category, git_last_commit_date, git_blob_hash, upload_status
                                  Optional keys: upload_on, blob_url, error_message
    
    Returns:
        None
    
    Raises:
        ValueError: If required metadata fields are missing
        PySparkException: If Delta table operations fail
    """
    spark = SparkSession.builder.appName("FirstTimeLoadMetadata").getOrCreate()
    
    schema = StructType([
        StructField("file_name", StringType(), nullable=False),
        StructField("file_relative_path", StringType(), nullable=False),
        StructField("file_extension", StringType(), nullable=False),
        StructField("category", StringType(), nullable=False),
        StructField("git_last_commit_date", StringType(), nullable=False),
        StructField("git_blob_hash", StringType(), nullable=False),
        StructField("upload_status", StringType(), nullable=False),
        StructField("upload_on", StringType(), nullable=True),
        StructField("blob_url", StringType(), nullable=True),
        StructField("error_message", StringType(), nullable=True)
    ])
    
    initial_df = spark.createDataFrame(metadata_list, schema=schema)
    
    current_time = get_timestamp()
    
    initial_df = initial_df \
        .withColumn("git_last_commit_date", to_timestamp("git_last_commit_date", "yyyy-MM-dd'T'HH:mm:ssXXX")) \
        .withColumn("upload_on", to_timestamp("upload_on", "yyyy-MM-dd'T'HH:mm:ssXXX")) \
        .withColumn("etl_created_at", to_timestamp(lit(current_time))) \
        .withColumn("etl_updated_at", to_timestamp(lit(current_time)))
    
    initial_df.write.format("delta") \
        .mode("overwrite") \
        .saveAsTable("vfs_raw.file_metadata")
    
    print("First-time load of metadata into Delta table completed successfully.")

# Example usage
if __name__ == "__main__":
    # Sample metadata list
    metadata = [
        {
            "file_name": "research_data.txt",
            "file_relative_path": "research/2024/research_data.txt",
            "file_extension": "txt",
            "category": "research_findings",
            "git_last_commit_date": "2024-01-26T14:30:00-05:00",
            "git_blob_hash": "a1b2c3d4e5f6",
            "upload_status": "pending",
            "upload_on": "2024-01-26T14:35:00-05:00",
            "blob_url": None,
            "error_message": None
        },
        {
            "file_name": "analysis.pdf",
            "file_relative_path": "reports/analysis.pdf",
            "file_extension": "pdf",
            "category": "reports",
            "git_last_commit_date": "2024-01-26T15:00:00-05:00",
            "git_blob_hash": "f6e5d4c3b2a1",
            "upload_status": "uploaded",
            "upload_on": "2024-01-26T15:05:00-05:00",
            "blob_url": "https://storage.azure.com/reports/analysis.pdf",
            "error_message": None
        }
    ]
    
    # Call the function
    first_time_load_file_metadata_to_table(metadata)
