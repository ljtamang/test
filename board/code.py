from typing import List, Dict, Any, Optional
from pathlib import Path
import os
from datetime import datetime
import re
def normalize_filename(filename: str) -> str:
def read_file_content(file_path: str, max_chars: Optional[int] = None, read_from_end: bool = False) -> Optional[str]:
    """
    Normalizes filename for consistent checking:
    - Converts to lowercase
    - Removes file extension
    - Replaces special characters and spaces with underscore
    - Removes multiple underscores
    """
    # Remove extension and convert to lowercase
    filename = Path(filename).stem.lower()
    
    # Replace special characters and spaces with underscore
    filename = re.sub(r'[^a-z0-9]', '_', filename)
    
    # Remove multiple underscores
    filename = re.sub(r'_+', '_', filename)
    
    # Remove leading/trailing underscores
    filename = filename.strip('_')
    
    return filename
def read_file_content(file_path: str) -> Optional[str]:
    """
    Reads content of a file. Implementation depends on file type.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().lower()
    except:
        return None
def tag_as_research_findings(file_path: str, min_threshold: int = 4) -> List[Dict[str, Any]]:
    """
    Tags files as research findings based on scoring criteria.
    Returns empty list if score is below minimum threshold.
    Reads content of a file based on file type. Supports different file types and reading options.

    Args:
        file_path: Path to the file
        min_threshold: Minimum score required for research finding classification (default: 4)
        
    Returns:
        List containing single tag dictionary with score if classified as research finding,
        empty list otherwise
    """
    score = 0
    
    # 1. Initialize keyword lists
    penalty_keywords = {'plan', 'guide', 'readme'}
    
    filename_keywords = [
        # Priority keywords (first 11)
        'finding', 'result', 'observation', 'experiment', 'study',
        'analysis', 'evaluation', 'assessment', 'measurement', 'report',
        'outcome',
        # Regular keywords
        'data', 'summary', 'research', 'investigation', 'review',
        'examination', 'survey', 'overview'
    ]
    priority_filename_keywords = set(filename_keywords[:11])
    
    content_keywords = [
        # Priority keywords (first 11)
        'methodology', 'participant', 'statistical', 'significant', 'analysis',
        'results', 'findings', 'observed', 'measured', 'evaluated',
        'concluded',
        # Regular keywords
        'data', 'research', 'study', 'experiment', 'investigation',
        'assessment', 'measurement', 'evaluation'
    ]
    priority_content_keywords = set(content_keywords[:11])
    
    path_keywords = {
        'research', 'study', 'analysis', 'results', 'findings', 
        'experiments', 'observations', 'data'
    }
        max_chars: Maximum number of characters to read. If None, reads all content.
        read_from_end: If True, reads from end of file. If False, reads from start.
                      Only applies when max_chars is specified.

    # 2. Check filename
    filename = normalize_filename(Path(file_path).name)
    
    # Check for penalty keywords first
    for keyword in penalty_keywords:
        if keyword in filename:
            score -= 8
            break  # Stop checking other penalty keywords once one is found
    
    # Check filename keywords
    # First check priority keywords
    for keyword in priority_filename_keywords:
        if keyword in filename:
            score += 3  # +1 for match, +2 for priority
            break  # Stop after first match
    else:
        # Check regular keywords if no priority keyword was found
        for keyword in filename_keywords[11:]:
            if keyword in filename:
                score += 1
                break  # Stop after first match
    
    # 3. Check content keywords
    content = read_file_content(file_path)
    if content is not None:
        # First check priority content keywords
        for keyword in priority_content_keywords:
            if keyword in content:
                score += 3  # +1 for match, +2 for priority
                break  # Stop after first match
        else:  # This else belongs to the for loop (for-else construct)
            # Only check regular content keywords if no priority keyword was found
            for keyword in content_keywords[11:]:
                if keyword in content:
                    score += 1
                    break  # Stop after first match
    
    # 4. Check path keywords
    path_str = normalize_filename(str(Path(file_path).parent))
    for keyword in path_keywords:
        normalized_keyword = normalize_filename(keyword)
        if normalized_keyword in path_str:
            score += 1  # +1 for each path match
    
    # 5. Return tag if score meets threshold
    if score >= min_threshold:
        return [{
            'tag': 'research_findings',
            'score': score
        }]
    
    return []
def keyword_based_tagging(file_path: str) -> List[Dict[str, Any]]:
    """
    Tags files by sequentially applying different tagging strategies.
    Returns:
        String content of file if successful, None if reading fails
    """
    tags = tag_as_research_findings(file_path)
    if tags:
        return tags
    file_extension = Path(file_path).suffix.lower()

    return [{
        'tag': 'unclassified',
        'score': 1
    }]
def tag_files(file_paths: List[str]) -> List[Dict[str, Any]]:
    """
    Main function to process and tag multiple files.
    """
    tagged_files = []
    # Handle PDF files (placeholder)
    if file_extension == '.pdf':
        print(f"PDF reading not implemented yet for: {file_path}")
        return None

    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"Warning: File not found - {file_path}")
            continue
    # Handle other file types
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        file_tags = {
            'file_path': file_path,
            'timestamp': datetime.now().isoformat(),
            'keyword_tags': keyword_based_tagging(file_path),
            'ai_tags': []  # Placeholder for AI-based tagging
        }
        
        tagged_files.append(file_tags)
    
    return tagged_files
            # If no max_chars specified, return all content
            if max_chars is None:
                return content.lower()
            
            # Handle partial content reading
            if read_from_end:
                return content[-max_chars:].lower()
            else:
                return content[:max_chars].lower()
                
    except Exception as e:
        print(f"Error reading file {file_path}: {str(e)}")
        return None
