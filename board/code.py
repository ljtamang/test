def deduplicate_by_blob_hash(files):
    # Create a dictionary to store the latest file for each blob hash
    unique_files = {}
    
    for file in files:
        blob_hash = file['git_blob_hash']
        
        # If we haven't seen this blob hash before, or if this file is more recent
        # than the one we've stored, update our dictionary
        if (blob_hash not in unique_files or 
            file['git_last_commit'] > unique_files[blob_hash]['git_last_commit']):
            unique_files[blob_hash] = file
    
    # Convert the dictionary values back to a list
    return list(unique_files.values())
