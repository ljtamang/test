# Copy folder from mount point to a temporary local path
dbutils.fs.cp("/mnt/your-mount-point/folder-name", "dbfs:/tmp/folder-name", recursive=True)
print("Folder copied to temporary path in DBFS.")


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
