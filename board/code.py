import re
import spacy

def remove_ssn(text):
    """
    Remove Social Security Numbers in various formats from text.
    Handles standard formats like XXX-XX-XXXX, XXXXXXXXX, XXX XX XXXX
    and also handles last 4 digits only (XXXX) when context indicates it's an SSN.
    
    Replaces only the SSN part with [SSN], not surrounding context.
    Case-insensitive matching for all context patterns.
    """
    # Load a spaCy model
    nlp = spacy.load("en_core_web_sm")
    
    # Process the text to analyze it
    doc = nlp(text)
    
    # Pattern for full SSN in different formats
    # SSN formats: XXX-XX-XXXX, XXX XX XXXX, XXXXXXXXX
    ssn_pattern = r'\b(\d{3}[-\s]?\d{2}[-\s]?\d{4})\b'
    
    # Get the indices of all SSN matches - capture only the SSN part in group 1
    ssn_matches = list(re.finditer(ssn_pattern, text))
    
    # Enhanced patterns for last 4 digits with common contexts - all case insensitive
    # The crucial part is to use capturing groups () only around the actual digits we want to replace
    last4_indicators = [
        # Common ways to reference SSN last 4
        r'(?:ssn|social security|ss#).*?(?:ending|last).*?(\d{4})\b',
        r'(?:ending|last).*?(?:ssn|social security|ss#).*?(\d{4})\b',
        r'(?:ssn|social security|ss#).*?[-:]\s*[Xx*]{5}[-\s]?(\d{4})\b',
        r'(?:ssn|social security|ss#).*?[-:]\s*(\d{4})\b',
        
        # Additional standard contexts
        r'last\s+four\s+(?:digits\s+)?(?:of\s+)?(?:your\s+)?(?:ssn|social security).*?(\d{4})\b',
        r'(?:ssn|social security).*?last\s+four\s+(?:digits)?.*?(\d{4})\b',
        r'(?:ssn|social security|ss)[\s#-]*\d{3}[\s-]*\d{2}[\s-]*(\d{4})',
        r'(?:ssn|social security|ss)\s*#*\s*[Xx*]{3}[\s-]*[Xx*]{2}[\s-]*(\d{4})',
        r'(?:ssn|social security)\s*(?:number)?\s*:?\s*[Xx*]{3}[\s-]*[Xx*]{2}[\s-]*(\d{4})',
        r'(?:ssn|ss#)[\s:-]*(\d{4})',
        r'(?:verify|verification|confirm).*?(?:ssn|social security).*?(\d{4})',
        r'(?:ssn|social security).*?(?:verify|verification|confirm).*?(\d{4})',
        r'(?:identification|id).*?(?:ssn|social security).*?(\d{4})',
        r'(?:ssn|social security).*?on\s+file.*?(\d{4})',
        r'on\s+file.*?(?:ssn|social security).*?(\d{4})',
        r'ssn\s*ending\s*in\s*(\d{4})',
        r'social\s+security\s*ending\s*in\s*(\d{4})',
        r'provide.*?last\s+four.*?(?:ssn|social).*?(\d{4})',
        r'enter.*?last\s+four.*?(?:ssn|social).*?(\d{4})'
    ]
    
    # Collect all matches and process them
    result = text
    
    # Process full SSN matches first
    for match in ssn_matches:
        full_match = match.group(0)  # The entire matched string
        ssn_only = match.group(1)    # Just the SSN part (captured in group 1)
        
        # Replace only the SSN part
        result = result.replace(ssn_only, "[SSN]")
    
    # Process last 4 digit matches
    for pattern in last4_indicators:
        for match in re.finditer(pattern, result, re.IGNORECASE):
            if match.groups():  # Ensure there's a capturing group
                last_four = match.group(1)  # The captured group (just the 4 digits)
                
                # Replace only those 4 digits, not the whole match
                result = result.replace(last_four, "[SSN]")
    
    return result

# Test the function
if __name__ == "__main__":
    # Test with different SSN formats, including problematic cases
    test_texts = [
        "My SSN is 123-45-6789",
        "ssn: 123 45 6789",
        "Social Security Number 123456789",
        "Ssn ending in 6789",
        "My SOCIAL SECURITY's last four digits are 6789",
        "social Security: XXX-XX-6789",
        "Please verify your sSn with the last four: 6789",
        "For identification, please provide your Ssn ending in 6789",
        "We have your ssn on file ending with 6789",
        "Enter the last four digits of your SOCIAL: 6789",
        "ssn: ***-**-6789",
        "For my SSN number is 456-78-4567. I work at James VA",  # The problematic case
        "Phone: 555-123-4567",  # Should not be redacted
        "DOB: 01-15-2000",      # Should not be redacted
        "ZIP: 12345",           # Should not be redacted
        "Account: 123456789"    # Ambiguous, should not be redacted without context
    ]
    
    for test in test_texts:
        redacted = remove_ssn(test)
        print(f"Original: {test}")
        print(f"Redacted: {redacted}")
        print("-" * 50)
