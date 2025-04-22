import re

def redact_ssn(text):
    """
    Identify and redact US Social Security Numbers in various formats.
    
    This function recognizes and redacts SSNs in the following formats:
    - XXX-XX-XXXX (standard hyphenated format)
    - XXXXXXXXX (9 continuous digits)
    - XXX XX XXXX (space-separated format)
    - XXX.XX.XXXX (period-separated format)
    - Last 4 digits only when prefixed with appropriate context
    
    Args:
        text (str): Text that may contain SSNs
        
    Returns:
        str: Text with SSNs redacted
    """
    # Copy the text for redaction
    redacted_text = text
    
    # Standard hyphenated SSN format (XXX-XX-XXXX)
    hyphenated_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
    
    # Continuous 9-digit SSN (XXXXXXXXX)
    # Only match if surrounded by word boundaries to avoid catching other 9-digit numbers
    continuous_pattern = r'\b\d{9}\b'
    
    # Space-separated SSN format (XXX XX XXXX)
    space_pattern = r'\b\d{3}\s\d{2}\s\d{4}\b'
    
    # Period-separated SSN format (XXX.XX.XXXX)
    period_pattern = r'\b\d{3}\.\d{2}\.\d{4}\b'
    
    # Last 4 digits with context pattern
    # Match phrases like "SSN ending in 1234" or "last four of SSN: 1234"
    last_four_pattern = r'(?:ssn|social\s+security|social\s+security\s+number)(?:[^0-9]+)(?:ending[\s:]+in|last[\s:]+four[\s:]+(?:digits[\s:]+)?(?:of)?|:|\#)\s*\d{4}\b'
    
    # Combined pattern for SSN validation (after initial match)
    # This helps filter out false positives by validating the number structure
    def is_valid_ssn(ssn_candidate):
        # Remove any non-digits
        digits_only = ''.join(c for c in ssn_candidate if c.isdigit())
        
        # SSN can't be all zeros in each group
        if digits_only[:3] == '000' or digits_only[3:5] == '00' or digits_only[5:] == '0000':
            return False
            
        # First 3 digits can't be 666 and can't be in range 900-999
        if digits_only[:3] == '666' or digits_only[:3] >= '900':
            return False
            
        # Valid SSN should have 9 digits
        if len(digits_only) != 9:
            return False
            
        return True
        
    # Find and redact standard hyphenated SSNs
    for match in re.finditer(hyphenated_pattern, redacted_text, re.IGNORECASE):
        if is_valid_ssn(match.group()):
            start, end = match.span()
            redacted_text = redacted_text[:start] + "[REDACTED-SSN]" + redacted_text[end:]
    
    # Find and redact continuous 9-digit SSNs
    for match in re.finditer(continuous_pattern, redacted_text, re.IGNORECASE):
        # Extra validation to avoid catching phone numbers, zip+4, etc.
        # Look for context that suggests this is an SSN
        start, end = match.span()
        context_before = redacted_text[max(0, start-30):start].lower()
        if is_valid_ssn(match.group()) and ('ssn' in context_before or 'social' in context_before or 'security' in context_before):
            redacted_text = redacted_text[:start] + "[REDACTED-SSN]" + redacted_text[end:]
    
    # Find and redact space-separated SSNs
    for match in re.finditer(space_pattern, redacted_text, re.IGNORECASE):
        if is_valid_ssn(match.group()):
            start, end = match.span()
            redacted_text = redacted_text[:start] + "[REDACTED-SSN]" + redacted_text[end:]
    
    # Find and redact period-separated SSNs
    for match in re.finditer(period_pattern, redacted_text, re.IGNORECASE):
        if is_valid_ssn(match.group()):
            start, end = match.span()
            redacted_text = redacted_text[:start] + "[REDACTED-SSN]" + redacted_text[end:]
    
    # Find and redact last 4 digits with context
    for match in re.finditer(last_four_pattern, redacted_text, re.IGNORECASE):
        start, end = match.span()
        redacted_text = redacted_text[:start] + "[REDACTED-SSN-REFERENCE]" + redacted_text[end:]
    
    return redacted_text

# Example usage
if __name__ == "__main__":
    sample_text = """
    Here are some examples of SSNs in different formats:
    Standard format: 413-61-5150
    Continuous digits: 413615150
    Space separated: 413 61 5150
    Period separated: 413.61.5150
    With context: My SSN is 413-61-5150
    Last four only: My SSN ending in 5150
    Social Security Number: 413-61-5150
    Invalid example that shouldn't match: 12345 (too short)
    Another invalid example: 000-00-0000 (all zeros)
    """
    
    redacted = redact_ssn(sample_text)
    print("Original Text:")
    print(sample_text)
    print("\nRedacted Text:")
    print(redacted)
