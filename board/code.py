from typing import List, Dict, Any

def deduplicate_metadata(files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
   """
   Deduplicate file metadata entries by keeping only the most recent version of files with the same git blob hash.
   
   Args:
       files: List of dictionaries containing file metadata with the following structure:
           {
               'updated_at': float,        # File update timestamp
               'git_root': str,            # Git repository root path
               'git_relative_path': str,   # File path relative to git root
               'git_blob_hash': str,       # Git blob hash
               'git_last_commit': float    # Timestamp of last git commit
           }
   
   Returns:
       List[Dict[str, Any]]: Deduplicated list of file metadata where:
           - Duplicate files (same git_blob_hash) are removed
           - For duplicates, keeps the entry with the most recent git_last_commit
           - Original metadata structure is preserved
   """
   unique_files = {}
   
   for file in files:
       blob_hash = file['git_blob_hash']
       
       # Keep the file with most recent git commit date for each blob hash
       if (blob_hash not in unique_files or 
           file['git_last_commit'] > unique_files[blob_hash]['git_last_commit']):
           unique_files[blob_hash] = file
   
   return list(unique_files.values())
