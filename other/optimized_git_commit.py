import os
import subprocess
from collections import defaultdict

def get_git_log(repo_path: str, file_path: str):
    """
    Fetch creation date, last commit date, and last content change date for a single file.
    """
    result = {
        "creation_date": None,
        "last_commit_date": None,
        "last_content_change_date": None,
    }
    try:
        # Convert file path to relative path
        relative_file = os.path.relpath(file_path, repo_path)

        # Fetch creation date (first commit where the file was added)
        creation_command = [
            "git", "log", "--pretty=format:%ad", "--date=iso", "--follow", "--diff-filter=A", "--", relative_file
        ]
        creation_date = subprocess.check_output(creation_command, cwd=repo_path, stderr=subprocess.DEVNULL).decode().splitlines()
        result["creation_date"] = creation_date[-1] if creation_date else "N/A"

        # Fetch last commit date (most recent commit where the file was changed)
        last_commit_command = [
            "git", "log", "-1", "--pretty=format:%ad", "--date=iso", "--", relative_file
        ]
        result["last_commit_date"] = subprocess.check_output(last_commit_command, cwd=repo_path, stderr=subprocess.DEVNULL).decode().strip()

        # Fetch last content change date (most recent commit affecting content)
        content_change_command = [
            "git", "log", "-1", "--pretty=format:%ad", "--date=iso", "-c", "--", relative_file
        ]
        result["last_content_change_date"] = subprocess.check_output(content_change_command, cwd=repo_path, stderr=subprocess.DEVNULL).decode().strip()

    except subprocess.CalledProcessError:
        print(f"Error processing file: {file_path}")
    return result

def get_git_metadata(repo_path: str, file_list: list):
    """
    Fetch Git metadata for each file in the list.
    """
    if not os.path.isdir(repo_path):
        raise ValueError("Invalid Git repository path.")

    print(f"Fetching Git metadata for {len(file_list)} files...")

    results = []
    for file_path in file_list:
        metadata = get_git_log(repo_path, file_path)
        results.append({
            "file_path": file_path,
            "creation_date": metadata["creation_date"],
            "last_commit_date": metadata["last_commit_date"],
            "last_content_change_date": metadata["last_content_change_date"],
        })
    return results

