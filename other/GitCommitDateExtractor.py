# file_helper.py (add these functions to existing file)

import re
from typing import List, Dict, Set

def identify_research_files(
    files: List[Dict[str, str]],
    filename_keywords: List[str] = None,
    path_keywords: List[str] = None,
    content_markers: List[str] = None,
    min_score: int = 2
) -> List[Dict[str, str]]:
    """
    Identifies research finding files based on multiple criteria.
    
    Args:
        files (List[Dict[str, str]]): List of file information dictionaries
        filename_keywords (List[str]): Keywords to look for in filenames
        path_keywords (List[str]): Keywords to look for in file paths
        content_markers (List[str]): Phrases to look for in file content
        min_score (int): Minimum score required to classify as research file
    
    Returns:
        List[Dict[str, str]]: List of files identified as research findings
    """
    # Default keywords if none provided
    if filename_keywords is None:
        filename_keywords = [
            'research', 'findings', 'study', 'survey', 'feedback',
            'analysis', 'results', 'insights', 'discovery'
        ]
    
    if path_keywords is None:
        path_keywords = [
            'research', 'studies', 'findings', 'analysis'
        ]
    
    if content_markers is None:
        content_markers = [
            '# Research Findings',
            '# Study Results',
            '## Research Goals',
            '## Key Findings',
            '## Methodology',
            '## Research Methods',
            '## Participant Demographics'
        ]

    research_files = []
    
    for file_info in files:
        score = 0
        file_path = file_info['file_path']
        file_name = file_info['file_name'].lower()
        
        # Check filename keywords
        for keyword in filename_keywords:
            if keyword.lower() in file_name:
                score += 2  # Filename matches are strong indicators
                
        # Check path keywords
        for keyword in path_keywords:
            if keyword.lower() in file_path.lower():
                score += 1  # Path matches are moderate indicators
        
        # Check content markers
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(2000)  # Read first 2000 characters
                for marker in content_markers:
                    if marker.lower() in content.lower():
                        score += 2  # Content matches are strong indicators
        except Exception as e:
            print(f"Warning: Could not read file {file_path}: {str(e)}")
            
        # Add additional metadata to file_info
        file_info['research_score'] = score
        file_info['is_research'] = score >= min_score
        
        if score >= min_score:
            research_files.append(file_info)
    
    return research_files
