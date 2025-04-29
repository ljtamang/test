# Databricks CSV File Upload and Table Creation
# This notebook provides two methods for loading CSV files to tables in Databricks

# Method 1: Using the Databricks UI to upload files
# ------------------------------------------------
# Instructions for UI method:
# 1. In the Databricks sidebar, click on "Data"
# 2. Click "Add Data" or "Create Table"
# 3. Upload your CSV file(s) using the UI
# 4. Configure options like header, delimiter, etc.
# 5. Create the table

# Method 2: Using code to upload files from DBFS
# ----------------------------------------------
# This method requires you to first upload the CSV to DBFS using the Databricks UI
# or by mounting external storage

# STEP 1: First check if your file exists in DBFS
# Replace with your file path (example: /FileStore/tables/your_file.csv)
file_path = "/FileStore/tables/your_file.csv"

# Display the first few lines of the file
def preview_csv_file(file_path):
    """
    Preview the contents of a CSV file in DBFS
    """
    print(f"Previewing file: {file_path}")
    try:
        # Read the file to see if it exists
        file_exists = dbutils.fs.ls(file_path)
        print(f"✅ File exists at: {file_path}")
        
        # Preview the first few lines
        print("\nFile preview (first 5 lines):")
        
        # Use dbutils.fs.head to read the first few lines
        file_content = dbutils.fs.head(file_path, 1024)  # Read first 1KB
        
        # Print lines (up to 5)
        lines = file_content.split("\n")
        for i, line in enumerate(lines[:5]):
            print(f"Line {i+1}: {line}")
            
        return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\nTroubleshooting tips:")
        print("- Check if the file path is correct")
        print("- Verify that you've uploaded the file to DBFS")
        print("- Common locations are '/FileStore/tables/' or your mounted storage")
        print("\nTo upload a file to DBFS:")
        print("1. In Databricks sidebar, click on 'Data'")
        print("2. Click 'Add Data' and follow the upload wizard")
        print("3. After upload, you'll see the path to use in your code")
        return False


# STEP 2: Write the CSV file to a table
def write_csv_to_table(file_path, table_name, infer_schema=True, header=True, delimiter=",", multiline=False):
    """
    Write a CSV file from DBFS to a Databricks Delta table
    
    Args:
        file_path (str): DBFS path to the CSV file
        table_name (str): Name of the table to write data to
        infer_schema (bool): Whether to infer schema from data
        header (bool): Whether CSV has a header row
        delimiter (str): CSV delimiter character
        multiline (bool): Whether rows can span multiple lines
    """
    if not file_path:
        print("No file path provided. Please specify a DBFS file path.")
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


# STEP 3: Example usage - uncomment and modify as needed

# Preview the file first
# preview_csv_file("/FileStore/tables/your_file.csv")

# Then write to table (after confirming file exists)
# write_csv_to_table(
#     file_path="/FileStore/tables/your_file.csv", 
#     table_name="my_database.my_table", 
#     header=True,               # Set to True if first row contains headers
#     delimiter=",",             # Change if using a different delimiter
#     infer_schema=True,         # Try to detect column types
#     multiline=False            # Set to True if CSV has line breaks in values
# )

# Alternative example for reading from cloud storage
# If you have mounted storage, you can read directly from it:
# write_csv_to_table(
#     file_path="/mnt/your-mount-point/path/to/file.csv",
#     table_name="your_table"
# )
