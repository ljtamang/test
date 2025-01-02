
# First-Time Workflow

This workflow initializes the repository processing and generates metadata for all eligible files.

## Steps

1. **Delete Existing Repo and Clone Fresh**:
   - Delete `/tmp/va.gov-team` if it exists.
   - Clone the repository to `/tmp/va.gov-team`.

2. **List `.md` Files**:
   - Traverse the `products` folder and list all `.md` files.

3. **Filter Research Findings**:
   - Use predefined rules to identify research finding files.

4. **Extract Metadata**:
   - For each file, extract metadata:
     - `file_name`, `file_path`, `file_size`, `file_type`, `commit_hash`, `commit_date`, `is_new`, `is_updated`.

5. **Save Files and Metadata**:
   - Save the raw files and metadata to Azure Blob Storage.

---

## Metadata Example

| file_name                   | file_path                             | file_size | file_type | commit_hash      | commit_date         | is_new | is_updated |
|-----------------------------|---------------------------------------|-----------|-----------|------------------|---------------------|--------|------------|
| research-summary.md         | /tmp/va.gov-team/products/research-summary.md | 2048      | md        | abc1234567890def | 2025-01-01T12:00:00 | True   | False      |
| findings-overview.md        | /tmp/va.gov-team/products/findings-overview.md | 1024      | md        | def4567890abc123 | 2025-01-01T12:05:00 | True   | False      |
| new-research-data.md        | /tmp/va.gov-team/products/new-research-data.md | 3072      | md        | ghi7890abc123456 | 2025-01-01T12:10:00 | True   | False      |
