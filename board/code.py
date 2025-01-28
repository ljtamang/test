# Define source and destination paths
source_path = "/mnt/your-mount-point/folder-name"
destination_path = "dbfs:/tmp/folder-name"

# List all files in the source path
files = dbutils.fs.ls(source_path)

# Iterate through files and copy them one by one
for file in files:
    if file.isDir():
        # Handle subdirectories recursively (if needed)
        print(f"Skipping subdirectory: {file.path}")
    else:
        # Copy individual files
        destination_file_path = destination_path + "/" + file.name
        dbutils.fs.cp(file.path, destination_file_path)
        print(f"Copied {file.path} to {destination_file_path}")

print("All files copied.")



import shutil

# Define paths
source_path = "/dbfs/tmp/folder-name"  # DBFS path
zip_path = "/dbfs/tmp/folder-name.zip"  # Path for the ZIP file

# Create a ZIP archive
shutil.make_archive(source_path, 'zip', source_path)
print(f"Folder archived to {zip_path}")


 Display the download link
displayHTML(f"""
    <a href="files/tmp/folder-name.zip" download>Click here to download the ZIP file</a>
""")
