# Using Spark SQL to query the table and create a DataFrame
df = spark.sql("""
    SELECT file_relative_path, file_status, blob_path
    FROM vfs.target_file_metadata
    WHERE file_status = 'pending_delete'
""")

# Display the DataFrame
display(df)
