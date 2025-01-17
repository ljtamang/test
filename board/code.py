from typing import Dict, List, Optional, Set, TypedDict
import subprocess
import json

def get_relative_path(full_path: str, git_root_path: str = "/tmp/va.gov-team") -> str:
    """
    Extract relative path from full path.

    Args:
        full_path (str): Full path of the file
        git_root_path (str): Git repository root path

    Returns:
        str: Relative path extracted from full path
    """
    if full_path.startswith(git_root_path):
        return full_path[len(git_root_path):].lstrip('/')
    return full_path.lstrip('/')

def get_git_blob_hash(file_path: str) -> Optional[str]:
    """
    Get git blob hash for a file using git command.

    Args:
        file_path (str): Path to the file

    Returns:
        Optional[str]: Git blob hash if successful, None if failed
    """
    try:
        cmd = ["git", "hash-object", file_path]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error getting git hash for {file_path}: {e}")
        return None

def compare_files_with_metadata(
    file_list: List[Dict[str, str]],
    metadata: List[Dict[str, str]]
) -> Dict[str, List[Dict[str, str]]]:
    """
    Compare file list with metadata to determine required changes.
    Only gets git_blob_hash for files that need modification check.

    Args:
        file_list: List of dictionaries containing:
            - file__path (str): Full path of the file
            - file_category (str): Category of the file
        
        metadata: List of dictionaries containing:
            - file_relative_path (str): Relative path of the file
            - file_category (str): Category of the file
            - git_blob_hash (str): Git blob hash of the file
            - Other metadata fields (not used in comparison)

    Returns:
        Dict with three keys: 'add', 'modify', 'delete'
        Each key contains a list of dictionaries with:
            - relative_path (str): Relative path of the file
            - file_category (str): Category of the file
    """
    changes: Dict[str, List[Dict[str, str]]] = {
        "add": [],
        "modify": [],
        "delete": []
    }
    
    # Create metadata lookup dictionary
    metadata_dict: Dict[str, Dict[str, str]] = {
        meta["file_relative_path"]: meta
        for meta in metadata
    }
    
    # Track files found in file_list
    existing_files: Set[str] = set()
    
    # Step 1: First check for files to add
    for file_info in file_list:
        relative_path = get_relative_path(file_info["file__path"])
        existing_files.add(relative_path)
        
        if relative_path not in metadata_dict:
            # File needs to be added
            changes["add"].append({
                "relative_path": relative_path,
                "file_category": file_info["file_category"]
            })
            continue
        
        # Step 2: For existing files, check if they need modification
        # Only get git_blob_hash for files that exist in metadata
        current_hash = get_git_blob_hash(file_info["file__path"])
        if current_hash and current_hash != metadata_dict[relative_path].get("git_blob_hash"):
            changes["modify"].append({
                "relative_path": relative_path,
                "file_category": file_info["file_category"]
            })
    
    # Step 3: Check for files to delete
    # Files in metadata but not in file_list
    for relative_path, meta_info in metadata_dict.items():
        if relative_path not in existing_files:
            changes["delete"].append({
                "relative_path": relative_path,
                "file_category": meta_info["file_category"]
            })
    
    return changes

# Example usage
if __name__ == "__main__":
    # Sample input data
    sample_file_list = [
        {
            "file__path": "/tmp/va.gov-team/products/health-care/research/health-research-2024.md",
            "file_category": "research_findings"
        },
        {
            "file__path": "/tmp/va.gov-team/products/health-care/research/veteran-interview-2024.md",
            "file_category": "research_findings"
        },
        {
            "file__path": "/tmp/va.gov-team/products/health-care/research/health-research-2025.md",
            "file_category": "research_findings"
        }
    ]

    sample_metadata = [
        {
            "file_name": "health-research-2024.md",
            "file_relative_path": "products/health-care/research/health-research-2024.md",
            "git_root_path": "/tmp/va.gov-team",
            "file_category": "research_findings",
            "git_blob_hash": "a29f8d5c67f12b3459231b4d2611184a",
            "index_action": "Add",
            "index_status": "Pending"
        },
        {
            "file_name": "user-interview-transcript.docx",
            "file_relative_path": "products/disability/research/interviews/user-interview-transcript.docx",
            "git_root_path": "/tmp/va.gov-team",
            "file_category": "research_findings",
            "git_blob_hash": "b45e2d8f91a23c4567890d123f456789",
            "index_action": "Add",
            "index_status": "Pending"
        }
    ]
    
    print("Input file_list:")
    print(json.dumps(sample_file_list, indent=2))
    print("\nInput metadata:")
    print(json.dumps(sample_metadata, indent=2))
    
    result = compare_files_with_metadata(sample_file_list, sample_metadata)
    print("\nOutput changes:")
    print(json.dumps(result, indent=2))

"""
Expected output:
{
  "add": [
    {
      "relative_path": "products/health-care/research/health-research-2025.md",
      "file_category": "research_findings"
    },
    {
      "relative_path": "products/health-care/research/veteran-interview-2024.md",
      "file_category": "research_findings"
    }
  ],
  "modify": [
    {
      "relative_path": "products/health-care/research/health-research-2024.md",
      "file_category": "research_findings"
    }
  ],
  "delete": [
    {
      "relative_path": "products/disability/research/interviews/user-interview-transcript.docx",
      "file_category": "research_findings"
    }
  ]
}
"""
