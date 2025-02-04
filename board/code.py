from pathlib import Path
import subprocess
from typing import Optional, Union

def get_git_blob_hash(file_path: Union[str, Path]) -> Optional[str]:
    """
    Get git blob hash for a file in git repository
    
    Args:
        file_path (Union[str, Path]): Full path or path relative to git repository root
        
    Returns:
        Optional[str]: Git blob hash of the file if successful, None otherwise
    """
    try:
        repo_root = Path(subprocess.check_output(
            ['git', 'rev-parse', '--show-toplevel'],
            stderr=subprocess.STDOUT,
            text=True
        ).strip())
        
        relative_path = Path(file_path).resolve().relative_to(repo_root)
        
        result = subprocess.check_output(
            ['git', 'hash-object', str(relative_path)], 
            stderr=subprocess.STDOUT,
            text=True,
            cwd=repo_root
        )
        return result.strip()
        
    except Exception:
        return None
