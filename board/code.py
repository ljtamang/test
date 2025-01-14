def get_git_info(file_path: str) -> Dict[str, Union[str, None]]:
    """ Get Git metadata for a file. """
    try:
        # Get git root
        git_root = subprocess.check_output(
            ['git', 'rev-parse', '--show-toplevel'], 
            cwd=str(Path(file_path).parent), 
            universal_newlines=True
        ).strip()
        
        # Get path relative to git root
        git_relative_path = str(Path(file_path).resolve().relative_to(Path(git_root)))
        
        # Get file's blob hash
        git_blob_hash = subprocess.check_output(
            ['git', 'hash-object', file_path], 
            universal_newlines=True
        ).strip()
        
        # Get last commit date for this file (Unix timestamp)
        git_last_commit = subprocess.check_output(
            ['git', 'log', '-1', '--format=%at', git_relative_path], 
            cwd=git_root, 
            universal_newlines=True
        ).strip()
        
        # Convert timestamp to float if it exists
        git_last_commit = float(git_last_commit) if git_last_commit else None
        
        # Return a dictionary with the collected Git metadata
        return {
            'git_root': git_root,
            'relative_path': git_relative_path,
            'blob_hash': git_blob_hash,
            'last_commit_timestamp': git_last_commit
        }
    except Exception as e:
        # Handle potential errors (this part was also missing in the original snippet)
        return {
            'git_root': None,
            'relative_path': None,
            'blob_hash': None,
            'last_commit_timestamp': None
        }
