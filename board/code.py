import csv
import os
import requests
import uuid

# Define the base URL for the GitHub repository
base_url = "https://raw.githubusercontent.com/username/repository/main"  # Replace with your GitHub base URL

# Define the output folder
output_folder = r"C:\Users\YourUsername\output_folder"  # Replace with your desired output folder

# Ensure the output folder exists
os.makedirs(output_folder, exist_ok=True)

# Read the CSV file
csv_file_path = r"C:\Users\YourUsername\file_paths.csv"  # Replace with your CSV file path

# Initialize counters
total_files = 0
successful_downloads = 0
failed_downloads = 0

with open(csv_file_path, mode='r') as csv_file:
    csv_reader = csv.reader(csv_file)
    
    # Skip the header row
    next(csv_reader)
    
    # Iterate over each row in the CSV file
    for row in csv_reader:
        total_files += 1  # Increment total files counter
        file_relative_path = row[0]
        
        # Construct the full GitHub URL
        github_file_url = f"{base_url}/{file_relative_path}"
        
        # Generate a unique ID
        unique_id = str(uuid.uuid4().hex)[:8]  # Using the first 8 characters of a UUID
        
        # Get the file name and extension from the relative path
        file_name, file_extension = os.path.splitext(os.path.basename(file_relative_path))
        
        # Construct the new file name with the unique ID before the extension
        new_file_name = f"{file_name}_{unique_id}{file_extension}"
        
        # Construct the full destination path
        full_destination_path = os.path.join(output_folder, new_file_name)
        
        # Download the file from GitHub
        try:
            response = requests.get(github_file_url)
            response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
            
            # Save the file to the output folder
            with open(full_destination_path, 'wb') as file:
                file.write(response.content)
            
            successful_downloads += 1  # Increment successful downloads counter
            print(f"Downloaded and saved: {github_file_url} -> {full_destination_path}")
        except requests.exceptions.RequestException as e:
            failed_downloads += 1  # Increment failed downloads counter
            print(f"Failed to download {github_file_url}: {e}")

# Print final status
print("\n--- Download Status ---")
print(f"Total files processed: {total_files}")
print(f"Successful downloads: {successful_downloads}")
print(f"Failed downloads: {failed_downloads}")
