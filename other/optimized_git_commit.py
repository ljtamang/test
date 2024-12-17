import os
import subprocess
from collections import defaultdict

def get_git_log_batch(repo_path: str, file_list: list):
    """
    Batch processing: Fetch creation date, last commit date, and last content change date
    for all files in a single git log command.
    """
    result = defaultdict(lambda: {"creation_date": None, "last_commit_date": None, "last_content_change_date": None})
    try:
        # Prepare the list of relative file paths
        relative_files = [os.path.relpath(file, repo_path) for file in file_list]

        # Construct the git log command
        git_command = [
            "git", "log", "--pretty=format:%H %ad", "--name-status", "--date=iso", "--follow", "--diff-filter=ACDMR"
        ] + relative_files

        output = subprocess.check_output(git_command, cwd=repo_path, stderr=subprocess.DEVNULL).decode()

        current_commit = None
        current_date = None

        file_first_commit = defaultdict(list)  # Tracks first commit for creation date
        file_last_commit = defaultdict(lambda: {"last_commit_date": None, "last_content_change_date": None})

        for line in output.splitlines():
            if line and not line.startswith(("A", "D", "M", "R")):  # Commit hash and date
                parts = line.split(" ", 1)
                current_commit, current_date = parts[0], parts[1]
            elif line.startswith(("A", "C", "M", "R")):  # File status
                status, file_path = line.split("\t", 1)
                if file_path in relative_files:
                    if status == "A":  # Added file (Creation Date)
                        file_first_commit[file_path].append(current_date)
                    # Update last commit and content change date
                    file_last_commit[file_path]["last_commit_date"] = current_date
                    file_last_commit[file_path]["last_content_change_date"] = current_date

        # Assign parsed data to result dictionary
        for file in relative_files:
            result[file]["creation_date"] = file_first_commit[file][-1] if file_first_commit[file] else "N/A"
            result[file]["last_commit_date"] = file_last_commit[file]["last_commit_date"] or "N/A"
            result[file]["last_content_change_date"] = file_last_commit[file]["last_content_change_date"] or "N/A"

    except subprocess.CalledProcessError as e:
        print(f"Error running git log: {e}")
    return result

def update_metadata_batch(repo_path: str, file_dicts: list):
    """
    Update a list of dictionaries with metadata for their file paths using batch processing.
    """
    file_list = [os.path.relpath(file_dict['file_path'], repo_path) for file_dict in file_dicts]
    metadata = get_git_log_batch(repo_path, file_list)

    # Update dictionaries with fetched metadata
    for file_dict in file_dicts:
        rel_file = os.path.relpath(file_dict['file_path'], repo_path)
        file_dict["creation_date"] = metadata[rel_file]["creation_date"]
        file_dict["last_commit_date"] = metadata[rel_file]["last_commit_date"]
        file_dict["last_content_change_date"] = metadata[rel_file]["last_content_change_date"]

def main(repo_path: str, file_dicts: list):
    """
    Main function to process and update metadata using batch processing.
    """
    if not os.path.isdir(repo_path):
        print("Error: Invalid Git repository path.")
        return

    print(f"Processing {len(file_dicts)} files using batch processing...")
    update_metadata_batch(repo_path, file_dicts)

    # Output results
    print("\nResults:")
    for file_dict in file_dicts:
        print(f"File: {file_dict['file_path']}")
        print(f"  Creation Date: {file_dict['creation_date']}")
        print(f"  Last Commit Date: {file_dict['last_commit_date']}")
        print(f"  Last Content Change Date: {file_dict['last_content_change_date']}")
        print("-" * 40)

if __name__ == "__main__":
    # Path to the Git repository
    REPO_PATH = "/path/to/your/repo"

    # List of file dictionaries to process
    FILE_DICTS = [
        {"file_path": "/path/to/your/repo/src/file1.py"},
        {"file_path": "/path/to/your/repo/src/file2.js"},
        {"file_path": "/path/to/your/repo/docs/readme.md"},
        # Add more file dictionaries here
    ]

    main(REPO_PATH, FILE_DICTS)
