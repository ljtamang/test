
# Combined Workflow Code

## Code Snippet

```python
import os
import shutil
import subprocess
import pandas as pd

# Define repository and storage paths
repo_url = "https://github.com/department-of-veterans-affairs/va.gov-team"
local_dir = "/tmp/va.gov-team"
products_dir = os.path.join(local_dir, "products")
blob_storage_path = "/dbfs/mnt/blob/raw"
metadata_path = os.path.join(blob_storage_path, "metadata.parquet")

# Delete and clone repository
if os.path.exists(local_dir):
    shutil.rmtree(local_dir)
subprocess.run(["git", "clone", repo_url, local_dir], check=True)

# Load historical metadata
try:
    historical_metadata = pd.read_parquet(metadata_path)
except FileNotFoundError:
    historical_metadata = pd.DataFrame(columns=["file_name", "commit_hash"])

# List and filter `.md` files
md_files = [os.path.join(root, file) for root, _, files in os.walk(products_dir) for file in files if file.endswith(".md")]

# Extract current metadata
def get_file_metadata(file_path):
    # Use `git log` for metadata
    result = subprocess.run(
        ["git", "log", "-1", "--pretty=format:%H,%ci", "--", file_path],
        cwd=local_dir,
        capture_output=True,
        text=True
    )
    commit_hash, commit_date = result.stdout.split(',')
    file_size = os.path.getsize(file_path)
    return {
        "file_name": os.path.relpath(file_path, products_dir),
        "file_path": file_path,
        "file_size": file_size,
        "file_type": "md",
        "commit_hash": commit_hash,
        "commit_date": commit_date.strip(),
    }

current_metadata = [get_file_metadata(file) for file in md_files]

# Compare metadata
historical_files = set(historical_metadata["file_name"])
new_or_updated_files = []

for metadata in current_metadata:
    file_name = metadata["file_name"]
    if file_name not in historical_files:
        metadata["is_new"] = True
        metadata["is_updated"] = False
    else:
        historical_commit = historical_metadata.loc[historical_metadata["file_name"] == file_name, "commit_hash"].iloc[0]
        if metadata["commit_hash"] != historical_commit:
            metadata["is_new"] = False
            metadata["is_updated"] = True
        else:
            metadata["is_new"] = False
            metadata["is_updated"] = False
    new_or_updated_files.append(metadata)

# Save new or updated files
for metadata in new_or_updated_files:
    if metadata["is_new"] or metadata["is_updated"]:
        dest_path = os.path.join(blob_storage_path, os.path.basename(metadata["file_path"]))
        shutil.copy(metadata["file_path"], dest_path)

# Update metadata
updated_metadata = pd.DataFrame(new_or_updated_files)
updated_metadata.to_parquet(metadata_path, index=False)
```
