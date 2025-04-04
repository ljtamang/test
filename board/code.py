from typing import List, Dict, Any, Optional
from pathlib import Path
import os
from datetime import datetime
import re

def normalize_filename(filename: str) -> str:
    """
    Normalizes filename for consistent checking:
    - Converts to lowercase
    - Removes file extension
    - Replaces special characters and spaces with underscore
    - Removes multiple underscores
    
    Args:
        filename: Original filename
        
    Returns:
        Normalized filename
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
    
    Args:
        file_path: Path to the file
        
    Returns:
        String content of file if successful, None if reading fails
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().lower()
    except:
        return None

def tag_as_research_findings(file_path: str) -> List[Dict[str, Any]]:
    """
    Tags files as research findings based on specific scoring criteria:
    - Minimum score of 4 needed for classification
    - -8 penalty for certain keywords
    - Priority keywords get additional points
    - Scores based on filename, content, and path matches
    
    Args:
        file_path: Path to the file
        
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
    priority_keywords = set(filename_keywords[:11])
    
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
    
    # 2. Check filename
    filename = normalize_filename(Path(file_path).name)
    
    # Check for penalty keywords first
    for keyword in penalty_keywords:
        if keyword in filename:
            score -= 8
            break  # Stop checking other penalty keywords once one is found
    
    # Check filename keywords
    # First check priority keywords
    for keyword in priority_keywords:
        if keyword in filename:
            score += 3  # +1 for match, +2 for priority
            break  # Stop after first match
    else:
        # Only check regular keywords if no priority keyword was found
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
        else:
            # Only check regular content keywords if no priority keyword was found
            for keyword in content_keywords[11:]:
                if keyword in content:
                    score += 1
                    break  # Stop after first match
    
    # 4. Check path keywords
    path_str = str(Path(file_path).parent).lower()
    path_matches = set(keyword for keyword in path_keywords if keyword in path_str)
    score += len(path_matches)  # +1 for each path match
    
    # 5. Return tag if score meets threshold
    if score >= 4:
        return [{
            'tag': 'research_findings',
            'score': score
        }]
    
    return []

def tag_as_research_plan(file_path: str) -> List[Dict[str, Any]]:
    """
    Tags files as research plans based on specific scoring criteria:
    - Minimum score of 4 needed for classification
    - -8 penalty for certain keywords
    - Priority keywords get additional points
    - Scores based on filename, content, and path matches
    
    Args:
        file_path: Path to the file
        
    Returns:
        List containing single tag dictionary with score if classified as research plan,
        empty list otherwise
    """
    score = 0
    
    # 1. Initialize keyword lists
    penalty_keywords = {'readme', 'guide', 'findings', 'finding', 'report', 'summary', 'research findings', 
                      'key findings', 'details of findings', 'conversation guide', 'moderator logistics', 
                      'emergency exit', 'intro -', 'warm-up questions', 'post-task interview'}
    
    filename_keywords = [
        # Priority keywords (first 11) - highly confident indicators of research plans
        'research-plan', 'research_plan', 'researchplan', 'research plan', 'uat-plan',
        'research_plan_', 'research-plan-', 'researchplan_', 'uat_plan', 'research-brief',
        'uat-research-plan',
        # Regular keywords - likely indicators of research plans, but less certain
        'research_plan_template', 'research_brief', 'uat_research_plan', 'researchplan-',
        'site-search-research-plan', 'wizard-research-plan', 'usability-research-plan',
        'discovery-research-plan', 'pre-integration-research-plan', 'user-research-plan',
        'pre-need-integration-research-plan'
    ]
    # Common filenames observed in research plans (additional exact matches)
    research_plan_exact_filenames = [
        'research-plan.md', 'research_plan.md', 'researchplan.md', 'research plan.md',
        'ResearchPlan.md', 'researchplan-unmoderated.md', 'researchplan-assistedtech.md',
        'Research-Plan.md', 'Research_Plan.md', 'Research Plan.md'
    ]
    
    # Additional significant boost if filename is an exact match
    if Path(file_path).name in research_plan_exact_filenames:
        score += 10  # Very strong indicator
    
    content_keywords = [
        # Priority keywords (first 11) - unique to research plans
        'research plan for', '# research plan', 'recruitment criteria', 'recruitment approach', 
        'primary criteria', 'timeline', 'availability', 'research sessions',
        'research goals and questions', 'method of research', 'hypothesis',
        # Regular keywords - may appear in other docs but still relevant
        'usability', 'research materials', 'methodology', 'participant recruiting', 
        'length of sessions', 'team roles', 'octo priorities', 'veteran journey', 
        'research questions', 'prepare', 'screener questions'
    ]
    priority_content_keywords = set(content_keywords[:11])
    
    path_keywords = {
        'research', 'study', 'usability', 'test', 'discovery',
        'design', 'user-research', 'uat', 'interview'
    }
    
    # 2. Check filename
    filename = normalize_filename(Path(file_path).name)
    
    # Check for penalty keywords first
    for keyword in penalty_keywords:
        if keyword in filename:
            score -= 8
            break  # Stop checking other penalty keywords once one is found
    
    # Special case: if the filename literally contains "research-plan" or "research_plan"
    if "research-plan" in filename or "research_plan" in filename or "researchplan" in filename:
        score += 5  # Strong indicator this is a research plan
    
    # Check for patterns that strongly indicate this IS a research plan
    if any(pattern in filename for pattern in filename_keywords[:11]):
        score += 8  # High confidence patterns get a significant boost
    elif any(pattern in filename for pattern in filename_keywords[11:]):
        score += 3  # Regular confidence patterns get a moderate boost
    
    # 3. Check content keywords
    content = read_file_content(file_path)
    if content is not None:
        # Check for section headers that are common in research plans
        plan_section_headers = [
            "## background", "## research goals", "## methodology", 
            "## recruitment", "## timeline", "## team roles",
            "# research plan", "# research plan for", "## research materials",
            "## recruitment criteria", "## availability", "## method",
            "## hypothesis", "## research goals and questions"
        ]
        
    # Content keyword patterns to avoid - terms strongly associated with non-plan documents
    content_patterns_to_penalize = [
        '# research findings', '# findings', '# conversation guide', 'research findings',
        'key findings', 'details of findings', 'participant comments', 
        'moderator logistics', 'emergency exit', 'warm-up questions',
        'post-task interview', 'thank-you and closing'
    ]
    
    # Penalize if findings or guide content patterns are found
    for pattern in content_patterns_to_penalize:
        if pattern.lower() in content.lower():
            score -= 5  # Strong indicator this is not a research plan
            break
                
        # Bonus for plan headers
        
        for header in plan_section_headers:
            if header in content:
                score += 2  # Strong indicator of a research plan
                break
                
        # Check if "conversation guide" is in the title or if the content has conversation guide indicators
        if "# conversation guide" in content.lower() or any(header.lower() in content.lower() for header in guide_section_headers):
            score -= 10  # Strong indicator this is a conversation guide, not a research plan
            
        # Check if specific content patterns distinctive to research plans are present
        if "research plan for" in content.lower():
            score += 5  # Very strong indicator of a research plan
            
        if "## outcome" in content.lower() and "## hypothesis" in content.lower():
            score += 3  # Strong combination unique to research plans
        
        # First check priority content keywords
        for keyword in priority_content_keywords:
            if keyword in content:
                score += 3  # +1 for match, +2 for priority
                break  # Stop after first match
        else:
            # Only check regular content keywords if no priority keyword was found
            for keyword in content_keywords[11:]:
                if keyword in content:
                    score += 1
                    break  # Stop after first match
    
    # 4. Check path keywords and patterns
    path_str = str(Path(file_path).parent).lower()
    path_matches = set(keyword for keyword in path_keywords if keyword in path_str)
    score += len(path_matches)  # +1 for each path match
    
    # Examine if the path has clear indicators that this is a research plan
    research_plan_path_patterns = [
        '/research-plan', '/research_plan', '/researchplan',
        '/research-design/', '/research-plan/', '/research_plan/'
    ]
    
    # Boost score for paths that contain research plan indicators
    for pattern in research_plan_path_patterns:
        if pattern in file_path:
            score += 4  # Good indicator based on path
            break
        
    # Check for path patterns that indicate findings or guide
    if any(pattern in file_path.lower() for pattern in ['/findings/', '/conversation-guide/', '/convo-guide/']):
        score -= 3
    
    # Check if the file looks like a markdown file based on extension
    is_markdown = Path(file_path).suffix.lower() in ['.md', '.markdown']
    if is_markdown:
        score += 1  # Add a point for markdown files as research plans are often in markdown
    
    # 5. Return tag if score meets threshold
    if score >= 4:
        return [{
            'tag': 'research_plan',
            'score': score
        }]
    
    return []

def keyword_based_tagging(file_path: str) -> List[Dict[str, Any]]:
    """
    Tags files by sequentially applying different tagging strategies.
    Tries to tag as research finding first, then research plan, then other types.
    
    Args:
        file_path: Path to the file to be tagged
        
    Returns:
        List of dictionaries containing tag information and scores
    """
    # First try to tag as research findings
    tags = tag_as_research_findings(file_path)
    if tags:
        return tags
    
    # If not a research finding, try to tag as research plan
    tags = tag_as_research_plan(file_path)
    if tags:
        return tags
    
    # If neither, mark as unclassified
    return [{
        'tag': 'unclassified',
        'score': 1
    }]

def ai_based_tagging(file_path: str) -> List[Dict[str, Any]]:
    """
    Placeholder for AI-based tagging implementation.
    """
    return []

def tag_files(file_paths: List[str]) -> List[Dict[str, Any]]:
    """
    Main function to process and tag multiple files.
    
    Args:
        file_paths: List of paths to files that need to be tagged
        
    Returns:
        List of dictionaries containing detailed tagging information for each file
    """
    tagged_files = []
    
    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"Warning: File not found - {file_path}")
            continue
            
        file_tags = {
            'file_path': file_path,
            'timestamp': datetime.now().isoformat(),
            'keyword_tags': keyword_based_tagging(file_path),
            'ai_tags': ai_based_tagging(file_path)
        }
        
        tagged_files.append(file_tags)
    
    return tagged_files

# Example usage
if __name__ == "__main__":
    # Sample file paths showing different scenarios
    files_to_tag = [
        "research/findings/experiment_results.txt",  # Should score high as research_findings
        "research/findings/project_plan.txt",  # Should get -8 penalty for research_findings
        "research/data_summary.txt",  # Should check non-priority keywords for research_findings
        "docs/misc_document.txt",  # Should not qualify for research_findings
        "products/health-care/checkin/research/remote-discovery/research-plan.md",  # Should score high as research_plan
        "products/virtual-agent/research/userfeedbackresearch/researchplan.md",  # Should score high as research_plan
        "products/decision-reviews/Supplemental-Claims/Research/researchplan.md",  # Should score high as research_plan
        "products/platform/research/roe-documentation/readme-prototypes/readme-research-plan.md"  # Should get penalty for research_plan
    ]
    
    # Tag all files
    results = tag_files(files_to_tag)
    
    # Display results
    print("\nTagging Results:")
    print("-" * 50)
    import json
    print(json.dumps(results, indent=2))
