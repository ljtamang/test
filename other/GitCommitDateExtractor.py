# file_helper.py

import re
from typing import List, Dict, Set
from pathlib import Path

def normalize_filename(filename: str) -> str:
    """
    Normalize filename for consistent matching
    
    Args:
        filename (str): Original filename
        
    Returns:
        str: Normalized filename
    """
    normalized = filename.lower()
    normalized = normalized.replace('-', ' ').replace('_', ' ')
    normalized = ' '.join(normalized.split())
    return normalized

def read_file_content(file_path: str, max_chars: int = 2000) -> str:
    """
    Reads content from both markdown and PDF files.
    
    Args:
        file_path (str): Path to the file
        max_chars (int): Maximum number of characters to read
        
    Returns:
        str: File content or empty string if reading fails
    """
    try:
        if file_path.lower().endswith('.pdf'):
            # Placeholder for PDF handling
            # TODO: Implement PDF reading functionality
            pass
        else:
            # For markdown and other text files
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read(max_chars)
                
    except Exception as e:
        print(f"Warning: Could not read file {file_path}: {str(e)}")
        return ""

def list_files_by_extensions(
    base_path: str,
    target_extensions: List[str],
    recursive: bool = True
) -> List[Dict[str, str]]:
    """
    Lists all files with specified extensions in the given directory.
    
    Args:
        base_path (str): Base directory path to start searching from
        target_extensions (List[str]): List of file extensions to search for (e.g., ['.md', '.txt'])
        recursive (bool): Whether to search recursively in subdirectories (default: True)
    
    Returns:
        List[Dict[str, str]]: List of dictionaries containing file information
    """
    # Normalize extensions
    target_extensions = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' 
                        for ext in target_extensions]
    
    found_files = []
    base_path = Path(base_path)
    
    try:
        pattern = '**/*' if recursive else '*'
        
        for file_path in base_path.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in target_extensions:
                found_files.append({
                    'file_name': file_path.name,
                    'file_path': str(file_path.absolute())
                })
                
        return found_files
    
    except Exception as e:
        print(f"Error while listing files: {str(e)}")
        return []

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
            # Core terms
            'research',
            'findings',
            'report',
            'summary',
            'synthesis',
            'discovery',
            
            # Specific combinations
            'research-findings',
            'research report',
            'research-report',
            'researchreport',
            'research summary',
            'research-summary',
            
            # Research types
            'user research',
            'userresearch',
            'pre-discovery',
            'design-discovery',
            
            # Finding variations
            'finding',
            'key-findings',
            'key findings',
            
            # Report variations
            'session-report',
            'readout',
            'research-readout',
            
            # Test related
            'test synthesis',
            'usability test',
            'beta test',
            
            # Round indicators
            'round',
            'r1',
            'round1',
            'round 1',
            
            # Additional patterns
            'heuristic',
            'prefill',
            'topline'
        ]
    
    if path_keywords is None:
        path_keywords = [
            'research',
            'studies',
            'findings',
            'analysis',
            'discovery',
            'user-research',
            'usability'
        ]
    
    if content_markers is None:
        content_markers = [
            'Research Findings',
            'Study Results',
            'Research Goals',
            'Key Findings',
            'Methodology',
            'Research Methods',
            'Participant Demographics',
            'Executive Summary',
            'Research Objectives',
            'Data Analysis',
            'Research Approach',
            'User Feedback',
            'Research Insights'
        ]

    research_files = []
    
    for file_info in files:
        score = 0
        file_path = file_info['file_path']
        normalized_filename = normalize_filename(file_info['file_name'])
        
        # Check filename keywords
        for keyword in filename_keywords:
            normalized_keyword = normalize_filename(keyword)
            if normalized_keyword in normalized_filename:
                score += 2
                # Bonus point for exact matches of important terms
                if normalized_keyword in ['research findings', 'research report', 
                                       'research summary', 'findings report']:
                    score += 1
                
        # Check path keywords
        normalized_path = normalize_filename(file_path)
        for keyword in path_keywords:
            normalized_keyword = normalize_filename(keyword)
            if normalized_keyword in normalized_path:
                score += 1
        
        # Check content markers only for non-PDF files for now
        if not file_path.lower().endswith('.pdf'):
            content = read_file_content(file_path)
            normalized_content = content.lower()
            for marker in content_markers:
                if marker.lower() in normalized_content:
                    score += 2
            
        # Add additional metadata to file_info
        file_info['research_score'] = score
        file_info['is_research'] = score >= min_score
        file_info['matched_criteria'] = []
        
        if score >= min_score:
            research_files.append(file_info)
    
    return research_files
