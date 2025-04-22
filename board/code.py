import spacy
import re

def redact_address_components(text):
    """
    Redact specific components of addresses while preserving city, state, and country names.
    
    Args:
        text (str): Input text containing addresses
        
    Returns:
        str: Text with specific address components redacted
    """
    # Load spaCy model
    nlp = spacy.load("en_core_web_lg")
    
    # Process the text
    doc = nlp(text)
    
    # Create a copy of the text that we'll modify
    redacted_text = text
    
    # Regular expressions for address components
    street_number_pattern = r'\b\d+\s+(?=[A-Za-z\s]+(?:Street|St|Avenue|Ave|Boulevard|Blvd|Drive|Dr|Lane|Ln|Road|Rd|Court|Ct|Way|Place|Pl|Circle|Cir|Terrace|Ter|Highway|Hwy|Parkway|Pkwy|Alley|Route|Rt)\b)'  # Street numbers followed by street name
    zip_code_pattern = r'\b\d{5}(?:-\d{4})?\b'  # ZIP codes (5 digit or 9 digit format)
    apt_pattern = r'\b(?:apt|apartment|suite|unit|#)\s*[\w-]+\b'  # Apartment/suite numbers
    po_box_pattern = r'\b(?:p\.?o\.?\s*box|post\s*office\s*box)\s*[\w-]+\b'  # PO Boxes
    
    # More comprehensive street name pattern with negative lookbehind to avoid matching abbreviations
    # The negative lookbehind (?<!&) ensures we don't match terms with ampersands like VR&E
    street_name_pattern = r'(?<!&)\b[A-Za-z\s]+\s(?:Street|St|Avenue|Ave|Boulevard|Blvd|Drive|Dr|Lane|Ln|Road|Rd|Court|Ct|Way|Place|Pl|Circle|Cir|Terrace|Ter|Highway|Hwy|Parkway|Pkwy|Alley|Route|Rt)\b'
    
    # Maintain a list of non-address terms that might be falsely identified
    non_address_terms = [
        r'\bVR&E\b',      # Veterans Readiness and Employment
        r'\bR&D\b',       # Research & Development
        r'\bB&B\b',       # Bed & Breakfast (unless used as actual address)
        r'\bP&L\b',       # Profit & Loss
        r'\bM&A\b',       # Mergers & Acquisitions
        r'\bD&D\b',       # Dungeons & Dragons
        r'\bH&R\b'        # H&R Block (unless used as actual address)
    ]
    
    # Find all GPE (geopolitical entities) to preserve cities, states, and countries
    gpe_spans = [ent for ent in doc.ents if ent.label_ == "GPE"]
    gpe_spans_ranges = [(ent.start_char, ent.end_char) for ent in gpe_spans]
    
    # Create a protection mask for terms that shouldn't be redacted
    protected_spans = []
    for pattern in non_address_terms:
        for match in re.finditer(pattern, redacted_text):
            protected_spans.append((match.start(), match.end()))
    
    # Add GPE spans to protected spans
    protected_spans.extend(gpe_spans_ranges)
    
    # Function to check if a match is in a protected span
    def is_protected(match_start, match_end):
        for start, end in protected_spans:
            if (match_start < end and match_end > start):
                return True
        return False
    
    # Redact street numbers with improved pattern
    for match in re.finditer(street_number_pattern, redacted_text, re.IGNORECASE):
        if not is_protected(match.start(), match.end()):
            original = match.group()
            replacement = "[REDACTED-NUM] "
            start, end = match.span()
            redacted_text = redacted_text[:start] + replacement + redacted_text[end:]
    
    # Redact street names using the improved pattern
    for match in re.finditer(street_name_pattern, redacted_text, re.IGNORECASE):
        if not is_protected(match.start(), match.end()):
            original = match.group()
            replacement = "[REDACTED-STREET]"
            start, end = match.span()
            redacted_text = redacted_text[:start] + replacement + redacted_text[end:]
    
    # Redact ZIP codes
    for match in re.finditer(zip_code_pattern, redacted_text):
        if not is_protected(match.start(), match.end()):
            original = match.group()
            replacement = "[REDACTED-ZIP]"
            start, end = match.span()
            redacted_text = redacted_text[:start] + replacement + redacted_text[end:]
    
    # Redact apartment/building numbers
    for match in re.finditer(apt_pattern, redacted_text, re.IGNORECASE):
        if not is_protected(match.start(), match.end()):
            original = match.group()
            replacement = "[REDACTED-APT]"
            start, end = match.span()
            redacted_text = redacted_text[:start] + replacement + redacted_text[end:]
    
    # Redact PO Boxes
    for match in re.finditer(po_box_pattern, redacted_text, re.IGNORECASE):
        if not is_protected(match.start(), match.end()):
            original = match.group()
            replacement = "[REDACTED-PO-BOX]"
            start, end = match.span()
            redacted_text = redacted_text[:start] + replacement + redacted_text[end:]
    
    return redacted_text

# Example usage
if __name__ == "__main__":
    # Sample text with addresses, including example with VR&E
    sample_text = """
    John lives at 123 Main Street, Apt 4B, New York, NY 10001, USA.
    The company headquarters is at 456 Business Avenue, Suite 200, Chicago, IL 60601.
    Send your mail to P.O. Box 789, Los Angeles, CA 90001.
    I live at 178 Willow Drive, Apt 3, Memphis, TN, 38124.
    I have used VR&E prior for education.
    We're opening a new store in Seattle, Washington next month.
    """
    
    redacted = redact_address_components(sample_text)
    print("Original Text:")
    print(sample_text)
    print("\nRedacted Text:")
    print(redacted)
