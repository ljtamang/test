import os
import subprocess
from collections import defaultdict

def get_git_log_batch(repo_path: str, file_list: list):
    """
    Batch processing: Fetch creation date, last commit date, and last content change date
    for all files in a single git log command.
    """
    # Results initialized with default values
    result = defaultdict(lambda: {
        "creation_date": None, 
        "last_commit_date": None, 
        "last_content_change_date": None
    })
    
    try:
        # Convert file paths to relative paths
        relative_files = [os.path.relpath(file, repo_path) for file in file_list]

        # Single git log command to process all files at once
        git_command = [
            "git", "log", "--pretty=format:%H %ad", "--name-status", "--date=iso", "--follow", "--diff-filter=ACDMR"
        ] + relative_files

        # Run the git log command and decode output
        output = subprocess.check_output(git_command, cwd=repo_path, stderr=subprocess.DEVNULL).decode()

        current_commit = None
        current_date = None

        file_creation_commits = defaultdict(list)  # Tracks first commit date for each file
        file_last_commit_data = defaultdict(lambda: {"last_commit_date": None, "last_content_change_date": None})

        # Parse git log output
        for line in output.splitlines():
            if line and not line.startswith(("A", "D", "M", "R")):  # Commit hash and date
                parts = line.split(" ", 1)
                current_commit, current_date = parts[0], parts[1]
            elif line.startswith(("A", "C", "M", "R")):  # File changes
                status, file_path = line.split("\t", 1)
                if file_path in relative_files:
                    if status == "A":  # File added - Creation Date
                        file_creation_commits[file_path].append(current_date)
                    # Update last commit and content change dates
                    file_last_commit_data[file_path]["last_commit_date"] = current_date
                    file_last_commit_data[file_path]["last_content_change_date"] = current_date

        # Populate the final result
        for file in relative_files:
            result[file]["creation_date"] = file_creation_commits[file][-1] if file_creation_commits[file] else "N/A"
            result[file]["last_commit_date"] = file_last_commit_data[file]["last_commit_date"] or "N/A"
            result[file]["last_content_change_date"] = file_last_commit_data[file]["last_content_change_date"] or "N/A"

    except subprocess.CalledProcessError as e:
        print(f"Error running git log: {e}")
    return result

def get_git_metadata(repo_path: str, file_list: list):
    """
    API function to fetch Git metadata (creation date, last commit date, and last content change date)
    for a list of files in a repository.

    Args:
        repo_path (str): Path to the Git repository.
        file_list (list): List of absolute file paths to process.

    Returns:
        list: A list of dictionaries containing metadata for each file.
    """
    if not os.path.isdir(repo_path):
        raise ValueError("Invalid Git repository path.")

    print(f"Fetching Git metadata for {len(file_list)} files...")

    # Fetch metadata in batch
    metadata = get_git_log_batch(repo_path, file_list)

    # Construct final result list
    results = []
    for file in file_list:
        rel_file = os.path.relpath(file, repo_path)
        file_data = metadata[rel_file]
        results.append({
            "file_path": file,
            "creation_date": file_data["creation_date"],
            "last_commit_date": file_data["last_commit_date"],
            "last_content_change_date": file_data["last_content_change_date"]
        })
    return results

"""
EXAMPLE USAGE

# Example usage for direct execution
REPO_PATH = "/path/to/your/repo"
FILE_LIST = [
    "/path/to/your/repo/src/file1.py",
    "/path/to/your/repo/src/file2.js",
    "/path/to/your/repo/docs/readme.md",
    # Add more file paths as needed
]

try:
    metadata = get_git_metadata(REPO_PATH, FILE_LIST)
    for item in metadata:
        print(f"File: {item['file_path']}")
        print(f"  Creation Date: {item['creation_date']}")
        print(f"  Last Commit Date: {item['last_commit_date']}")
        print(f"  Last Content Change Date: {item['last_content_change_date']}")
        print("-" * 40)
except ValueError as e:
    print(e)

"""
