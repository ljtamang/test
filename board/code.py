# Define source directory and destination directory
source_dir = "/mnt/your-mount-point/source-folder"  # Replace with your actual source directory
destination_dir = "dbfs:/tmp/destination-folder"  # Destination path in DBFS

# Ensure the destination directory exists
dbutils.fs.mkdirs(destination_dir)

# List files in the source directory
files = dbutils.fs.ls(source_dir)

# Iterate over all files and copy them to the destination directory
for file in files:
    if file.isDir():  # If it's a subdirectory, you can handle it recursively if needed
        print(f"Skipping directory: {file.path}")
    else:
        destination_file = f"{destination_dir}/{file.name}"
        dbutils.fs.cp(file.path, destination_file)
        print(f"Copied {file.path} to {destination_file}")

print("All files copied to /tmp.")




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
