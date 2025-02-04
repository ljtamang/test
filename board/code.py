from typing import List
from pyspark.sql import SparkSession

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
    
    df = spark.table("vfs.target_file_metadata") \
        .filter(df.upload_status == lit(status)) \
        .select("file_relative_path")
    
    target_file_paths = [row.file_relative_path for row in df.collect()]
    
    return target_file_paths

# Example usage:
# pending_target_files = get_target_files_by_status('pending upload')
# uploaded_target_files = get_target_files_by_status('uploaded')
