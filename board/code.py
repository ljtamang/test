import csv
import os
import shutil
import uuid

# Define the base path and the output folder
base_path = "/path/to/base"  # Replace with your base path
output_folder = "/path/to/output_folder"  # Replace with your desired output folder

# Ensure the output folder exists
os.makedirs(output_folder, exist_ok=True)

# Read the CSV file
csv_file_path = "file_paths.csv"  # Replace with your CSV file path

with open(csv_file_path, mode='r') as csv_file:
    csv_reader = csv.reader(csv_file)
    
    # Skip the header row
    next(csv_reader)
    
    # Iterate over each row in the CSV file
    for row in csv_reader:
        file_relative_path = row[0]
        
        # Construct the full source path
        full_source_path = os.path.join(base_path, file_relative_path)
        
        # Generate a unique ID
        unique_id = str(uuid.uuid4().hex)[:8]  # Using the first 8 characters of a UUID
        
        # Get the file name from the relative path
        file_name = os.path.basename(file_relative_path)
        
        # Construct the new file name with the unique ID
        new_file_name = f"{unique_id}_{file_name}"
        
        # Construct the full destination path
        full_destination_path = os.path.join(output_folder, new_file_name)
        
        # Copy the file to the output folder with the new name
        shutil.copy(full_source_path, full_destination_path)
        
        print(f"Copied: {full_source_path} -> {full_destination_path}")

print("All files have been copied successfully.")
