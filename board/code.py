import shutil

# Define the source folder and ZIP file paths
source_folder = "/dbfs/tmp/destination-folder"  # Source folder in DBFS
zip_file_path = "/dbfs/tmp/destination-folder.zip"  # Path for the ZIP file (output)

# Compress the folder into a ZIP archive
shutil.make_archive(zip_file_path.replace('.zip', ''), 'zip', source_folder)

print(f"Folder compressed into ZIP file at: {zip_file_path}")
