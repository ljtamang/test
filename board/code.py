from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import StructType, StructField, StringType, TimestampType
from pyspark.sql.functions import (
    to_timestamp, 
    lit, 
    from_utc_timestamp, 
    current_timestamp
)
from typing import List, Dict

def get_standardized_timestamp(timezone: str = "UTC"):
    """
    Returns a standardized current timestamp column in the specified timezone.
    
    Parameters:
        timezone (str): Timezone to convert to. Default is "UTC".
                       Example values: "UTC", "America/New_York"
    
    Returns:
        Column: A Spark SQL column containing the current timestamp in specified timezone
    """
    return from_utc_timestamp(current_timestamp(), timezone)

def convert_to_standard_timestamp(column_name: str, input_format: str = "yyyy-MM-dd'T'HH:mm:ssXXX", timezone: str = "UTC"):
    """
    Converts a timestamp string column to a standardized timestamp in the specified timezone.
    
    Parameters:
        column_name (str): Name of the column to convert
        input_format (str): Format of the input timestamp string. 
        timezone (str): Timezone to convert to. Default is "UTC".
    
    Returns:
        Column: A Spark SQL column containing the converted timestamp in specified timezone
    """
    return from_utc_timestamp(to_timestamp(column_name, input_format), timezone)

def first_time_load_file_metadata_to_table(metadata_list: List[Dict], timezone: str = "America/New_York") -> None:
    """
    Load file metadata into vfs_raw.file_metadata Delta table using overwrite mode.
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
    
    processed_df = initial_df \
        .withColumn("git_last_commit_date", convert_to_standard_timestamp("git_last_commit_date", timezone=timezone)) \
        .withColumn("upload_on", convert_to_standard_timestamp("upload_on", timezone=timezone)) \
        .withColumn("etl_created_at", get_standardized_timestamp(timezone)) \
        .withColumn("etl_updated_at", get_standardized_timestamp(timezone))
    
    processed_df.write.format("delta") \
        .mode("overwrite") \
        .saveAsTable("vfs_raw.file_metadata")
    
    print("First-time load of metadata into Delta table completed successfully.")

# Example usage:
if __name__ == "__main__":
    # Example metadata
    initial_metadata = [
        {
            "file_name": "example.csv",
            "file_relative_path": "data/example.csv",
            "file_extension": "csv",
            "category": "raw_data",
            "git_last_commit_date": "2024-01-26T10:00:00Z",
            "git_blob_hash": "abc123",
            "upload_status": "pending",
            "upload_on": None,
            "blob_url": None,
            "error_message": None
        }
    ]
    
    # Load with EST timezone
    first_time_load_file_metadata_to_table(initial_metadata, timezone="America/New_York")
