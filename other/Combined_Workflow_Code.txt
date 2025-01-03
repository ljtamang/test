# main.py or your notebook

from file_helper import list_files_by_extensions, identify_research_files

# First get all markdown files (for now)
products_path = "/tmp/va.gov-team/products"
all_files = list_files_by_extensions(
    base_path=products_path,
    target_extensions=['.md']  # Only handling markdown files for now
)

# Custom content markers specific to your domain
custom_content_markers = [
    'Research Findings',
    'Key Findings',
    'Methodology',
    'Executive Summary',
    'Research Objectives',
    'Data Analysis',
    'Survey Results',
    'User Research',
    'Research Goals',
    'Participant Feedback'
]

# Identify research files
research_files = identify_research_files(
    files=all_files,
    content_markers=custom_content_markers,
    min_score=2
)

# Display results
print(f"\nFound {len(research_files)} research files:")
for file_info in research_files:
    print(f"\nFile: {file_info['file_name']}")
    print(f"Path: {file_info['file_path']}")
    print(f"Research Score: {file_info['research_score']}")
    print(f"Is Research: {file_info['is_research']}")
    print("-" * 50)

# Optional: Save results to a file
import json
with open('research_files_analysis.json', 'w') as f:
    json.dump(research_files, f, indent=2)
