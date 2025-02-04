from typing import List
from pyspark.sql import SparkSession
from pyspark.sql.functions import lit

def get_target_files_by_status(status: str) -> List[str]:
    """
    Queries target_file_metadata table and returns file_relative_path values 
    based on their upload_status.
    
    Args:
        status (str): The upload_status to filter by (e.g., 'pending upload', 'uploaded', 'pending delete')
        
    Returns:
        List[str]: List of target file paths matching the specified status
    """
    spark = SparkSession.builder.getOrCreate()
    
    # Create DataFrame and filter - corrected version
    df = spark.table("vfs.target_file_metadata") \
        .filter("upload_status = '{}'".format(status)) \
        .select("file_relative_path")
    
    target_file_paths = [row.file_relative_path for row in df.collect()]
    
    return target_file_paths
