# Using Databricks SQL
from pyspark.sql import SparkSession

# Get or create Spark session
spark = SparkSession.builder.getOrCreate()

# Query the table
query = """
SELECT file_relative_path 
FROM vfs.target_file_metadata 
WHERE upload_status = 'pending upload'
"""

# Execute query and collect results
df = spark.sql(query)
file_paths = [row.file_relative_path for row in df.collect()]

# Now file_paths is a Python list containing all the matching file paths
# You can print it to verify
print(file_paths)
