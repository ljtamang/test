from pyspark.sql.functions import col

def get_files_by_status(status_list, cols=None):
    """
    Retrieves files from target_file_metadata table based on file_status values.
    
    Args:
        status_list (list): List of file status values to filter on 
                           (e.g., ['pending_delete', 'pending_update'])
        cols (list or str, optional): Column(s) to select. 
                                    Defaults to ['file_relative_path']
    
    Returns:
        list: If single column requested, returns list of values
              e.g., ['file/path1.txt', 'file/path2.txt']
              
              If multiple columns requested, returns list of dictionaries
              e.g., [
                  {'file_relative_path': 'file/path1.txt', 'file_status': 'pending_delete'},
                  {'file_relative_path': 'file/path2.txt', 'file_status': 'pending_update'}
              ]
    
    Examples:
        # Get file paths for pending delete files
        paths = get_files_by_status(['pending_delete'])
        
        # Get specific column values
        blob_paths = get_files_by_status(['pending_delete'], cols=['blob_path'])
        
        # Get multiple columns for multiple statuses
        records = get_files_by_status(
            ['pending_delete', 'pending_update'],
            cols=['file_relative_path', 'file_status', 'blob_path']
        )
    """
    # Set default columns if not provided
    if cols is None:
        cols = ['file_relative_path']
    
    # Ensure cols is a list
    if isinstance(cols, str):
        cols = [cols]
    
    # Create DataFrame with filters
    df = (
        spark.table("vfs.target_file_metadata")
        .filter(col("file_status").isin(status_list))
        .select(cols)
    )
    
    # If single column requested, return simple list of values
    if len(cols) == 1:
        return [row[0] for row in df.collect()]
    
    # If multiple columns requested, return list of dictionaries
    return df.rdd.map(lambda row: row.asDict()).collect()
