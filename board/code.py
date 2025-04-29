
from pyspark.sql import SparkSession
import os
import uuid

# Part 1: Upload file and print file path
def upload_csv_file():
    """
    Upload a CSV file and return the full file path in DBFS.
    This function creates a widget for file upload and saves the file to DBFS.
    
    Returns:
        str: Full DBFS path to the uploaded file
    """
    # Create file input widget for CSV upload
    display(dbutils.widgets.fileupload("csv_upload", ""))
    
    # Get the uploaded file info
    uploaded_file = dbutils.widgets.get("csv_upload")
    
    if not uploaded_file:
        print("Please upload a CSV file using the widget above")
        return None
    
    # Create a temporary directory to save the file
    temp_dir = f"/tmp/csv_upload_{uuid.uuid4().hex}"
    dbutils.fs.mkdirs(temp_dir)
    
    # Path for the uploaded file
    temp_file_path = f"{temp_dir}/uploaded.csv"
    
    # Save widget content to the temp file
    try:
        with open(temp_file_path, "w") as f:
            f.write(uploaded_file)
        
        # Convert local path to DBFS path
        dbfs_path = f"dbfs:{temp_file_path}"
        
        print(f"✅ File successfully uploaded to: {dbfs_path}")
        print(f"Local file path: {temp_file_path}")
        
        # Preview first few lines of the file
        print("\nFile preview (first 5 lines):")
        with open(temp_file_path, "r") as f:
            for i, line in enumerate(f):
                if i < 5:
                    print(line.strip())
                else:
                    break
        
        return dbfs_path
    
    except Exception as e:
        print(f"❌ Error uploading file: {str(e)}")
        # Clean up if there's an error
        dbutils.fs.rm(temp_dir, True)
        return None


# Part 2: Write the uploaded file to a table
def write_csv_to_table(file_path, table_name, infer_schema=True, header=True, delimiter=",", multiline=False):
    """
    Write a CSV file to a Databricks Delta table
    
    Args:
        file_path (str): DBFS path to the CSV file
        table_name (str): Name of the table to write data to
        infer_schema (bool): Whether to infer schema from data
        header (bool): Whether CSV has a header row
        delimiter (str): CSV delimiter character
        multiline (bool): Whether rows can span multiple lines
    """
    if not file_path:
        print("No file path provided. Please upload a file first.")
        return
    
    try:
        # Read the CSV file
        df = spark.read.format("csv") \
            .option("header", header) \
            .option("inferSchema", infer_schema) \
            .option("delimiter", delimiter) \
            .option("multiLine", multiline) \
            .load(file_path)
        
        # Show preview of the data
        print(f"Preview of data from CSV file:")
        df.show(5)
        
        # Get column information
        print("\nColumn information:")
        df.printSchema()
        
        # Get row count
        row_count = df.count()
        print(f"\nTotal rows: {row_count}")
        
        # Write to the specified table
        df.write.format("delta") \
            .mode("overwrite") \
            .option("overwriteSchema", "true") \
            .saveAsTable(table_name)
        
        print(f"✅ Successfully wrote data to table: {table_name}")
        
        # Print SQL code for querying the data
        print("\nSQL to query the table:")
        print(f"SELECT * FROM {table_name} LIMIT 100;")
        
    except Exception as e:
        print(f"❌ Error writing to table: {str(e)}")
        print("\nTroubleshooting tips:")
        print("- Check if your CSV format is correct")
        print("- Verify the delimiter is properly specified")
        print("- If your CSV has quotes or special characters, try setting multiline=True")
        print("- Make sure the table name includes a database if needed (e.g., 'my_database.my_table')")


# Example usage:
# 1. First upload the file:
# file_path = upload_csv_file()
#
# 2. Then write to table (after file is uploaded):
# if file_path:
#     write_csv_to_table(file_path, "my_database.my_table")
