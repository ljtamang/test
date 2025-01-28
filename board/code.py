import os
import zipfile
from pyspark.dbutils import DBUtils

# Path to the source folder in DBFS
source_folder = "/dbfs/tmp/destination-folder"

# Create a temporary zip file
zip_path = "/dbfs/tmp/download_folder.zip"

# Create a zip file containing the folder contents
def zip_folder(folder_path, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)

# Zip the folder
zip_folder(source_folder, zip_path)

# Create a link to download the zip file
displayHTML(f"""<a href="/files{zip_path.replace('/dbfs', '')}" download>Download Folder as ZIP</a>""")

# Optional: Clean up the zip file after some time
# dbutils.fs.rm(zip_path)
