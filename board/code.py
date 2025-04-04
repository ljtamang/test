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

def tag_as_research_plan(file_path: str, min_threshold: int = 4) -> Dict[str, Any]:
    """
    Tags files as research plans based on specific scoring criteria:
    - Minimum score needed for classification (default: 4)
    - -8 penalty for certain keywords
    - Priority keywords get additional points
    - Scores based on filename, content, and path matches
    
    Args:
        file_path: Path to the file
        min_threshold: Minimum score needed for classification (default: 4)
        
    Returns:
        Dictionary with tag and score if classified as research plan,
        empty dictionary otherwise
    """
    score = 0
    
    # 1. Initialize keyword lists
    penalty_keywords = {'guide', 'findings', 'finding', 'report', 'summary', 'research findings', 
                      'key findings', 'details of findings', 'conversation', 'convo', 'interview'}
    
    filename_keywords = [
        # Priority keywords (first 13) - highly confident indicators of research plans
        'research-plan', 'research_plan', 'researchplan', 'research plan', 'uat-plan',
        'research_plan_', 'research-plan-', 'researchplan_', 'uat_plan', 'research-brief',
        'uat-research-plan', 'researchplan-', 'research_plan_template',
        # Regular keywords - likely indicators of research plans, but less certain
        'research_brief', 'uat_research_plan', 'site-search-research-plan', 'wizard-research-plan', 
        'usability-research-plan', 'discovery-research-plan', 'pre-integration-research-plan', 
        'user-research-plan'
    ]
    
    # Research plan exact filename patterns without considering file extension
    research_plan_exact_name_patterns = [
        'research-plan', 'research_plan', 'researchplan', 'research plan',
        'ResearchPlan', 'Research-Plan', 'Research_Plan', 'Research Plan'
    ]
    
    # Additional significant boost if the filename without extension is an exact match
    filename_without_ext = Path(file_path).stem
    if filename_without_ext in research_plan_exact_name_patterns:
        score += 12  # Very strong indicator (increased weight)
    
    content_keywords = [
        # Priority keywords (first 10) - unique to research plans
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
        'research', 'study', 'analysis', 'discovery',
        'usability', 'testing', 'uat'
    }
    
    # 2. Check filename
    filename = normalize_filename(Path(file_path).name)
    
    # Special case: files like "plan1.txt", "plan2.txt" that are research plans
    if filename.startswith('plan'):
        score += 5  # Give some points for having "plan" in the filename
    
    # Check for penalty keywords first
    for keyword in penalty_keywords:
        if keyword in filename:
            score -= 8
            break  # Stop checking other penalty keywords once one is found
    
    # Special case: if the filename literally contains "research-plan" or "research_plan"
    if "research-plan" in filename or "research_plan" in filename or "researchplan" in filename:
        score += 7  # Strong indicator this is a research plan (increased weight)
    
    # Check for patterns that strongly indicate this IS a research plan
    if any(pattern in filename for pattern in filename_keywords[:13]):
        score += 10  # High confidence patterns get a significant boost (increased weight)
    elif any(pattern in filename for pattern in filename_keywords[13:]):
        score += 4  # Regular confidence patterns get a moderate boost (increased weight)
    
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
        
        # Conversation guide section headers - not declared earlier, need to define
        guide_section_headers = [
            "# conversation guide", "## warm-up questions", "## interview questions",
            "## task completion", "## post-task interview", "## thank you and closing"
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
            if header.lower() in content.lower():
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
        
        # Check for other important plan indicators in content
        if ("# research plan" in content.lower() or "research plan for" in content.lower() or 
            ("background" in content.lower() and "methodology" in content.lower()) or
            ("research goals" in content.lower() and "recruitment" in content.lower())):
            score += 10  # Very strong content indicators
        
        # First check priority content keywords (with increased weight)
        for keyword in priority_content_keywords:
            if keyword.lower() in content.lower():
                score += 4  # +4 for priority content keyword (increased weight)
                break  # Stop after first match
        else:
            # Only check regular content keywords if no priority keyword was found
            for keyword in content_keywords[11:]:
                if keyword.lower() in content.lower():
                    score += 2  # +2 for regular content keyword (increased weight)
                    break  # Stop after first match
    
    # 4. Check path keywords with reduced weight
    path_str = normalize_filename(str(Path(file_path).parent))
    path_matches = set(keyword for keyword in path_keywords if keyword in path_str)
    # Add just +1 point if any path keyword matches, regardless of how many
    if path_matches:
        score += 1  # +1 total for any path match
    
    # Special case: check for research/plan in path
    if "research" in path_str and "plan" in path_str:
        score += 3  # Strong indicator this is a research plan
    
    # 5. Return tag if score meets threshold
    if score >= min_threshold:
        return {
            'tag': 'research_plan',
            'score': score
        }
    
    return {}  # Empty dictionary is returned when threshold isn't met

def tag_as_research_findings(file_path: str, min_threshold: int = 4) -> Dict[str, Any]:
    """
    Tags files as research findings based on specific scoring criteria:
    - Minimum score needed for classification (default: 4)
    - -8 penalty for certain keywords
    - Priority keywords get additional points
    - Scores based on filename, content, and path matches
    
    Args:
        file_path: Path to the file
        min_threshold: Minimum score needed for classification (default: 4)
        
    Returns:
        Dictionary with tag and score if classified as research finding,
        empty dictionary otherwise
    """
    score = 0
    
    # 1. Initialize keyword lists
    penalty_keywords = {'plan', 'guide', 'readme', 'conversation-guide', 'convo-guide', 'moderator'}
    
    filename_keywords = [
        # Priority keywords - highly confident indicators of research findings
        'research-findings', 'research_findings', 'researchfindings', 'research findings',
        'findings', 'result', 'results', 'observation', 'observations',
        'research-report', 'research_report', 'research report', 'research-readout',
        # Regular keywords - likely indicators of research findings, but less certain
        'analysis', 'evaluation', 'assessment', 'measurement', 'report',
        'outcome', 'data', 'summary', 'investigation', 'review', 'synthesis'
    ]
    priority_keywords = set(filename_keywords[:13])
    
    # Findings exact filename patterns without considering file extension
    findings_exact_name_patterns = [
        'research-findings', 'research_findings', 'researchfindings', 'research findings',
        'ResearchFindings', 'Research-Findings', 'Research_Findings', 'Research Findings',
        'findings', 'Findings', 'research-report', 'research-readout'
    ]
    
    content_keywords = [
        # Priority keywords for research findings
        'key findings', 'research findings', 'hypotheses and conclusions', 
        'recommendations', 'results', 'details of findings', 'participant comments',
        'observed', 'measured', 'evaluated', 'concluded', 'observation',
        # Regular keywords
        'data', 'research', 'study', 'experiment', 'investigation',
        'assessment', 'measurement', 'evaluation'
    ]
    priority_content_keywords = set(content_keywords[:12])
    
    path_keywords = {
        'research', 'findings', 'results', 'study', 'analysis',
        'experiments', 'observations', 'data'
    }
    
    # 2. Check filename
    filename = normalize_filename(Path(file_path).name)
    
    # Special case: If the filename is simply "findings1.txt" or similar
    if filename.startswith('findings'):
        score += 5  # Give some points for having "findings" in the filename
    
    # Check for penalty keywords first
    for keyword in penalty_keywords:
        if keyword in filename:
            score -= 8
            break  # Stop checking other penalty keywords once one is found
    
    # Check filename keywords (with increased weight)
    # First check priority keywords
    for keyword in priority_keywords:
        if keyword in filename:
            score += 10  # +10 for priority keyword in filename (increased weight)
            break  # Stop after first match
    else:
        # Only check regular keywords if no priority keyword was found
        for keyword in filename_keywords[13:]:
            if keyword in filename:
                score += 4  # +4 for regular keyword (increased weight)
                break  # Stop after first match
    
    # Additional significant boost if the filename without extension is an exact match
    filename_without_ext = Path(file_path).stem
    if filename_without_ext in findings_exact_name_patterns:
        score += 12  # Very strong indicator
    
    # 3. Check content keywords
    content = read_file_content(file_path)
    if content is not None:
        content_lower = content.lower()
        
        # Check for section headers that are common in findings
        findings_section_headers = [
            "# research findings", "## research findings", 
            "# key findings", "## key findings",
            "# findings", "## findings",
            "# recommendations", "## recommendations",
            "# results", "## results"
        ]
        
        # Content keyword patterns to avoid - terms strongly associated with non-findings documents
        content_patterns_to_penalize = [
            '# research plan', 'recruitment criteria', 'timeline',
            '# conversation guide', 'moderator logistics', 'warm-up questions'
        ]
        
        # Penalize if plan or guide content patterns are found
        for pattern in content_patterns_to_penalize:
            if pattern.lower() in content_lower:
                score -= 8  # Strong indicator this is not a findings document
                break
                
        # Bonus for findings headers
        for header in findings_section_headers:
            if header.lower() in content_lower:
                score += 8  # Strong indicator of a findings document
                break
                
        # Look for findings-specific structural patterns
        if (("key findings" in content_lower and "recommendations" in content_lower) or
            ("findings" in content_lower and "recommendations" in content_lower) or
            ("hypotheses and conclusions" in content_lower)):
            score += 6  # Strong structural indicator of findings
        
        # First check priority content keywords
        for keyword in priority_content_keywords:
            if keyword.lower() in content_lower:
                score += 4  # +4 for priority content keyword
                break  # Stop after first match
        else:
            # Only check regular content keywords if no priority keyword was found
            for keyword in content_keywords[12:]:
                if keyword.lower() in content_lower:
                    score += 2  # +2 for regular content keyword
                    break  # Stop after first match
    
    # 4. Check path keywords with reduced weight
    path_str = normalize_filename(str(Path(file_path).parent))
    path_matches = set(keyword for keyword in path_keywords if keyword in path_str)
    # Add just +1 point if any path keyword matches, regardless of how many
    if path_matches:
        score += 1  # +1 total for any path match
    
    # Special case: check for research-findings in path
    if ("research-findings" in file_path.lower() or 
        ("research" in path_str and "findings" in path_str)):
        score += 5  # Strong indicator this is research findings
    
    # 5. Return tag if score meets threshold
    if score >= min_threshold:
        return {
            'tag': 'research_findings',
            'score': score
        }
    
    return {}  # Empty dictionary is returned when threshold isn't met

def tag_as_guide(file_path: str, min_threshold: int = 4) -> Dict[str, Any]:
    """
    Tags files as conversation guides based on specific scoring criteria:
    - Minimum score needed for classification (default: 4)
    - -8 penalty for certain keywords
    - Priority keywords get additional points
    - Scores based on filename, content, and path matches
    
    Args:
        file_path: Path to the file
        min_threshold: Minimum score needed for classification (default: 4)
        
    Returns:
        Dictionary with tag and score if classified as conversation guide,
        empty dictionary otherwise
    """
    score = 0
    
    # 1. Initialize keyword lists
    penalty_keywords = {'plan', 'findings', 'finding', 'report', 'summary', 'research findings', 
                      'key findings', 'details of findings', 'researchplan'}
    
    filename_keywords = [
        # Priority keywords - highly confident indicators of conversation guides
        'conversation-guide', 'convo-guide', 'conversation_guide', 'convo_guide', 
        'conversationguide', 'convoguid', 'interview-guide', 'interview_guide',
        'moderator-guide', 'moderator_guide', 'discussion-guide', 'discussion_guide',
        'usability-test-guide', 'usability_test_guide',
        # Regular keywords - likely indicators of conversation guides, but less certain
        'interview', 'discussion', 'questions', 'script', 'moderator', 'protocol',
        'testing-guide', 'testing_guide', 'user-testing'
    ]
    
    # Guide exact filename patterns without considering file extension
    guide_exact_name_patterns = [
        'conversation-guide', 'conversation_guide', 'conversationguide', 
        'convo-guide', 'convo_guide', 'convoguid',
        'interview-guide', 'interview_guide',
        'discussion-guide', 'discussion_guide',
        'Conversation Guide', 'Conversation_Guide', 'ConversationGuide'
    ]
    
    # Additional significant boost if the filename without extension is an exact match
    filename_without_ext = Path(file_path).stem
    if filename_without_ext in guide_exact_name_patterns:
        score += 12  # Very strong indicator
    
    content_keywords = [
        # Priority keywords - unique to conversation guides
        'moderator logistics', 'warm-up questions', 'interview questions', 
        'post-task interview', 'task completion', 'emergency exit',
        'thank you and closing', 'introduction script', 'tasks',
        '# conversation guide', '## conversation guide',
        # Regular keywords - may appear in other docs but still relevant
        'usability', 'participant', 'introduction', 'research session', 
        'screener', 'recording', 'think aloud', 'protocol'
    ]
    priority_content_keywords = set(content_keywords[:11])
    
    path_keywords = {
        'research', 'usability', 'testing', 'interview', 'user-research',
        'discovery', 'sessions'
    }
    
    # 2. Check filename
    filename = normalize_filename(Path(file_path).name)
    
    # Special case: If the filename is simply "guide1.txt" or similar
    if filename.startswith('guide'):
        score += 5  # Give some points for having "guide" in the filename
    
    # Check for penalty keywords first
    for keyword in penalty_keywords:
        if keyword in filename:
            score -= 8
            break  # Stop checking other penalty keywords once one is found
    
    # Special case: if the filename literally contains guide indicators
    if any(term in filename for term in ["guide", "conversation", "convo", "interview"]):
        score += 7  # Strong indicator this is a conversation guide
    
    # Check for patterns that strongly indicate this IS a guide
    if any(pattern in filename for pattern in filename_keywords[:14]):
        score += 10  # High confidence patterns get a significant boost
    elif any(pattern in filename for pattern in filename_keywords[14:]):
        score += 4  # Regular confidence patterns get a moderate boost
    
    # 3. Check content keywords
    content = read_file_content(file_path)
    if content is not None:
        # Check for section headers that are common in guides
        guide_section_headers = [
            "# conversation guide", "## warm-up questions", "## interview questions",
            "## task completion", "## post-task interview", "## thank you and closing",
            "## moderator logistics", "## participant logistics", "## introduction",
            "## tasks", "## background questions", "## wrap-up"
        ]
        
        # Content keyword patterns to avoid - terms strongly associated with non-guide documents
        content_patterns_to_penalize = [
            '# research plan', '# research findings', 'recruitment criteria', 
            'research methodology', 'hypothesis', 'research goals', 'timeline',
            'key findings', 'results summary'
        ]
        
        # Penalize if findings or plan content patterns are found
        for pattern in content_patterns_to_penalize:
            if pattern.lower() in content.lower():
                score -= 5  # Strong indicator this is not a conversation guide
                break
                
        # Bonus for guide headers
        for header in guide_section_headers:
            if header.lower() in content.lower():
                score += 5  # Strong indicator of a conversation guide
                break
                
        # Check if specific content patterns distinctive to guides are present
        if "conversation guide" in content.lower() or "discussion guide" in content.lower():
            score += 7  # Very strong indicator of a guide
        
        # First check priority content keywords
        for keyword in priority_content_keywords:
            if keyword.lower() in content.lower():
                score += 4  # +4 for priority content keyword
                break  # Stop after first match
        else:
            # Only check regular content keywords if no priority keyword was found
            for keyword in content_keywords[11:]:
                if keyword.lower() in content.lower():
                    score += 2  # +2 for regular content keyword
                    break  # Stop after first match
    
    # 4. Check path keywords with reduced weight
    path_str = normalize_filename(str(Path(file_path).parent))
    path_matches = set(keyword for keyword in path_keywords if keyword in path_str)
    # Add just +1 point if any path keyword matches, regardless of how many
    if path_matches:
        score += 1  # +1 total for any path match
    
    # 5. Return tag if score meets threshold
    if score >= min_threshold:
        return {
            'tag': 'conversation_guide',
            'score': score
        }
    
    return {}  # Empty dictionary is returned when threshold isn't met

def keyword_based_tagging(file_path: str) -> List[Dict[str, Any]]:
    """
    Tags files by sequentially applying different tagging strategies.
    Tries to tag as research finding first, then research plan, then guide, then other types.
    
    Args:
        file_path: Path to the file to be tagged
        
    Returns:
        List of dictionaries containing tag information and scores
    """
    # First try to tag as research findings
    tag = tag_as_research_findings(file_path)
    if tag:  # If not empty dictionary
        return [tag]  # Return as list with single dictionary
    
    # If not a research finding, try to tag as research plan
    tag = tag_as_research_plan(file_path)
    if tag:  # If not empty dictionary
        return [tag]  # Return as list with single dictionary
    
    # If not a research plan, try to tag as conversation guide
    tag = tag_as_guide(file_path)
    if tag:  # If not empty dictionary
        return [tag]  # Return as list with single dictionary
    
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
