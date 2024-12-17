import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

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

        # Fetch creation date
        creation_command = [
            "git", "log", "--pretty=format:%ad", "--date=iso", "--follow", "--diff-filter=A", "--", relative_file
        ]
        creation_date = subprocess.check_output(creation_command, cwd=repo_path, stderr=subprocess.DEVNULL).decode().splitlines()
        result["creation_date"] = creation_date[-1] if creation_date else "N/A"

        # Fetch last commit date
        last_commit_command = [
            "git", "log", "-1", "--pretty=format:%ad", "--date=iso", "--", relative_file
        ]
        result["last_commit_date"] = subprocess.check_output(last_commit_command, cwd=repo_path, stderr=subprocess.DEVNULL).decode().strip()

        # Fetch last content change date
        content_change_command = [
            "git", "log", "-1", "--pretty=format:%ad", "--date=iso", "-c", "--", relative_file
        ]
        content_change_date = subprocess.check_output(content_change_command, cwd=repo_path, stderr=subprocess.DEVNULL).decode().splitlines()
        result["last_content_change_date"] = content_change_date[0] if content_change_date else "N/A"

    except subprocess.CalledProcessError:
        print(f"Error processing file: {file_path}")
    return {"file_path": file_path, **result}

def get_optimal_threads():
    """
    Dynamically calculate the optimal number of threads for the environment.
    """
    cpu_count = os.cpu_count() or 1  # Fallback to 1 if CPU count is unavailable
    optimal_threads = cpu_count * 2  # Multiplier of 2 for I/O-bound tasks
    print(f"Detected {cpu_count} CPUs. Setting max_threads to {optimal_threads} for I/O-bound tasks.")
    return optimal_threads

def get_git_metadata(repo_path: str, file_list: list):
    """
    Fetch Git metadata for each file in the list using dynamically calculated multithreading.
    """
    if not os.path.isdir(repo_path):
        raise ValueError("Invalid Git repository path.")

    max_threads = get_optimal_threads()

    print(f"Fetching Git metadata for {len(file_list)} files using {max_threads} threads...")

    results = []
    with ThreadPoolExecutor(max_threads) as executor:
        # Submit tasks for each file
        future_to_file = {executor.submit(get_git_log, repo_path, file_path): file_path for file_path in file_list}
        for future in as_completed(future_to_file):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"Error processing file {future_to_file[future]}: {e}")
    return results
