
# Incremental Workflow

This workflow processes only new or updated files by comparing the current repository state with the historical metadata.

## Steps

1. **Delete Existing Repo and Clone Fresh**:
   - Delete `/tmp/va.gov-team` if it exists.
   - Clone the repository to `/tmp/va.gov-team`.

2. **Load Historical Metadata**:
   - Read the metadata from Azure Blob Storage.

3. **List `.md` Files**:
   - Traverse the `products` folder and list all `.md` files.

4. **Compare with Historical Metadata**:
   - For each file:
     - If the file doesn’t exist in historical metadata, it’s **new** (`is_new=True`).
     - If the `commit_hash` differs from historical metadata, it’s **updated** (`is_updated=True`).

5. **Process New or Updated Files**:
   - Copy new or updated files to Azure Blob Storage.
   - Append or update their metadata.

6. **Save Updated Metadata**:
   - Write the updated metadata back to Azure Blob Storage.

---

## Metadata Example

| file_name                   | file_path                             | file_size | file_type | commit_hash      | commit_date         | is_new | is_updated |
|-----------------------------|---------------------------------------|-----------|-----------|------------------|---------------------|--------|------------|
| research-summary.md         | /tmp/va.gov-team/products/research-summary.md | 2048      | md        | abc1234567890def | 2025-01-01T12:00:00 | False  | False      |
| findings-overview.md        | /tmp/va.gov-team/products/findings-overview.md | 1024      | md        | xyz1234567890abc | 2025-01-02T14:00:00 | False  | True       |
| additional-findings.md      | /tmp/va.gov-team/products/additional-findings.md | 4096      | md        | lmn1234567890opq | 2025-01-02T14:05:00 | True   | False      |
