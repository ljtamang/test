from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import StructType, StructField, StringType, TimestampType
from pyspark.sql.functions import to_timestamp, lit, col, when
from datetime import datetime
import pytz
from typing import List, Dict, Union, Optional

def get_standardized_timestamp(
    timezone: str = "UTC",
    format_string: str = None
) -> Union[datetime, str]:
    """
    Get current timestamp in specified timezone.
    
    Args:
        timezone (str): Target timezone (e.g., "UTC", "America/New_York"). 
                       Defaults to "UTC".
        format_string (str, optional): If provided, returns formatted string.
                                     If None, returns datetime object.
                                     Example: "%Y-%m-%d %H:%M:%S"
    
    Returns:
        Union[datetime, str]: Current timestamp as datetime object or formatted string
                             if format_string is provided.
    """
    try:
        tz = pytz.timezone(timezone)
        utc_now = datetime.now(pytz.UTC)
        local_time = utc_now.astimezone(tz)
        
        if format_string:
            return local_time.strftime(format_string)
        return local_time
        
    except pytz.exceptions.PytzError as e:
        raise ValueError(f"Invalid timezone: {timezone}. Error: {str(e)}")
    except ValueError as e:
        raise ValueError(f"Invalid format string: {format_string}. Error: {str(e)}")

def convert_to_standard_timestamp(
    timestamp_str: Optional[str],
    timezone: str = "UTC",
    input_format: str = None,
    output_format: str = None
) -> Union[datetime, str, None]:
    """
    Convert timestamp string to standardized timestamp in specified timezone.
    
    Args:
        timestamp_str (str, optional): Input timestamp string. 
                                     If None, returns None.
        timezone (str): Target timezone (e.g., "UTC", "America/New_York").
                       Defaults to "UTC".
        input_format (str, optional): Format of input timestamp.
                                    If None, assumes ISO format.
                                    Example: "%Y-%m-%d %H:%M:%S"
        output_format (str, optional): If provided, returns formatted string.
                                     If None, returns datetime object.
                                     Example: "%Y-%m-%d %H:%M:%S"
    """
    if timestamp_str is None:
        return None
        
    try:
        # Parse timestamp string based on input format
        if input_format:
            dt = datetime.strptime(timestamp_str, input_format)
            if dt.tzinfo is None:
                dt = pytz.UTC.localize(dt)
        else:
            # Handle ISO format with Z or +00:00
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1] + '+00:00'
            dt = datetime.fromisoformat(timestamp_str)
            if dt.tzinfo is None:
                dt = pytz.UTC.localize(dt)
        
        # Convert to target timezone
        target_tz = pytz.timezone(timezone)
        converted_dt = dt.astimezone(target_tz)
        
        # Return formatted string if output_format provided
        if output_format:
            return converted_dt.strftime(output_format)
        return converted_dt
        
    except ValueError as e:
        raise ValueError(f"Error parsing timestamp '{timestamp_str}' with format '{input_format}'. Error: {str(e)}")
    except pytz.exceptions.PytzError as e:
        raise ValueError(f"Invalid timezone: {timezone}. Error: {str(e)}")

def first_time_load_file_metadata_to_table(
    metadata_list: List[Dict],
    timezone: str = "America/New_York"
) -> None:
    """
    Load file metadata into vfs_raw.file_metadata Delta table using overwrite mode.
    
    Args:
        metadata_list (List[Dict]): List of dictionaries containing file metadata
        timezone (str): Timezone for timestamps. Defaults to "America/New_York"
    """
    spark = SparkSession.builder.appName("FirstTimeLoadMetadata").getOrCreate()
    
    schema = StructType([
        StructField("file_name", StringType(), nullable=False),
        StructField("file_relative_path", StringType(), nullable=False),
        StructField("file_extension", StringType(), nullable=False),
        StructField("category", StringType(), nullable=False),
        StructField("git_blob_hash", StringType(), nullable=False),
        StructField("upload_status", StringType(), nullable=False),
        StructField("upload_on", StringType(), nullable=True),
        StructField("blob_url", StringType(), nullable=True),
        StructField("error_message", StringType(), nullable=True)
    ])
    
    initial_df = spark.createDataFrame(metadata_list, schema=schema)
    
    # Get current timestamp
    current_time = get_standardized_timestamp(timezone)
    
    processed_df = initial_df \
        .withColumn("upload_on", 
                   when(col("upload_on").isNotNull(),
                        lit(convert_to_standard_timestamp(
                            col("upload_on"), 
                            timezone=timezone).isoformat()))
                   .otherwise(None)) \
        .withColumn("etl_created_at", lit(current_time.isoformat())) \
        .withColumn("etl_updated_at", lit(current_time.isoformat()))
    
    processed_df.write.format("delta") \
        .mode("overwrite") \
        .saveAsTable("vfs_raw.file_metadata")
    
    print("First-time load of metadata into Delta table completed successfully.")

def update_file_metadata(
    metadata_list: List[Dict],
    timezone: str = "America/New_York"
) -> None:
    """
    Update existing records in the file_metadata Delta table.
    
    Args:
        metadata_list (List[Dict]): List of dictionaries containing file metadata updates
        timezone (str): Timezone for timestamps. Defaults to "America/New_York"
    """
    spark = SparkSession.builder.appName("UpdateFileMetadata").getOrCreate()
    
    update_schema = StructType([
        StructField("file_name", StringType(), True),
        StructField("file_relative_path", StringType(), False),
        StructField("file_extension", StringType(), True),
        StructField("category", StringType(), True),
        StructField("git_blob_hash", StringType(), True),
        StructField("upload_status", StringType(), True),
        StructField("upload_on", StringType(), True),
        StructField("blob_url", StringType(), True),
        StructField("error_message", StringType(), True)
    ])
    
    update_df = spark.createDataFrame(metadata_list, schema=update_schema)
    
    # Get current timestamp
    current_time = get_standardized_timestamp(timezone)
    
    processed_update_df = update_df \
        .withColumn("upload_on", 
                   when(col("upload_on").isNotNull(),
                        lit(convert_to_standard_timestamp(
                            col("upload_on"), 
                            timezone=timezone).isoformat()))
                   .otherwise(None)) \
        .withColumn("etl_updated_at", lit(current_time.isoformat()))
    
    existing_table = spark.read.format("delta").table("vfs_raw.file_metadata")
    
    existing_table.alias("existing").merge(
        processed_update_df.alias("updates"),
        "existing.file_relative_path = updates.file_relative_path"
    ).whenMatchedUpdate(set={
        "file_name": "updates.file_name",
        "file_extension": "updates.file_extension",
        "category": "updates.category",
        "git_blob_hash": "updates.git_blob_hash",
        "upload_status": "updates.upload_status",
        "upload_on": "updates.upload_on",
        "blob_url": "updates.blob_url",
        "error_message": "updates.error_message",
        "etl_updated_at": "updates.etl_updated_at"
    }).execute()
    
    print("Metadata updates completed successfully.")

# Example usage:
if __name__ == "__main__":
    # Example metadata for first-time load
    initial_metadata = [
        {
            "file_name": "example.csv",
            "file_relative_path": "data/example.csv",
            "file_extension": "csv",
            "category": "raw_data",
            "git_blob_hash": "abc123",
            "upload_status": "pending",
            "upload_on": None,
            "blob_url": None,
            "error_message": None
        }
    ]
    
    first_time_load_file_metadata_to_table(initial_metadata)
