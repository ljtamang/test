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
    
    # List of common street suffixes
    street_suffixes = [
        'Street', 'St', 'Avenue', 'Ave', 'Boulevard', 'Blvd', 'Drive', 'Dr',
        'Lane', 'Ln', 'Road', 'Rd', 'Court', 'Ct', 'Way', 'Place', 'Pl',
        'Circle', 'Cir', 'Terrace', 'Ter', 'Highway', 'Hwy', 'Parkway', 'Pkwy', 
        'Alley', 'Route', 'Rt'
    ]
    
    # Join suffixes with word boundaries for pattern matching
    suffix_pattern = r'\b(?:' + '|'.join(street_suffixes) + r')\b'
    
    # More precise patterns that require clear indicators of address content
    # Street pattern requires a number followed by words and then a street suffix
    street_pattern = r'\b\d+\s+[A-Za-z\s]+\s+(?:' + '|'.join(street_suffixes) + r')\b'
    
    # ZIP code pattern (5 digit or 9 digit format)
    zip_code_pattern = r'\b\d{5}(?:-\d{4})?\b'
    
    # Apartment/suite pattern requires clear apartment indicators
    apt_pattern = r'\b(?:apt|apartment|suite|unit|#)\s*[\w-]+\b'
    
    # PO Box pattern
    po_box_pattern = r'\b(?:p\.?o\.?\s*box|post\s*office\s*box)\s*[\w-]+\b'
    
    # Find all GPE (geopolitical entities) to preserve cities, states, and countries
    gpe_spans = [ent for ent in doc.ents if ent.label_ == "GPE"]
    gpe_spans_ranges = [(ent.start_char, ent.end_char) for ent in gpe_spans]
    
    # Function to check if a match is in a GPE span
    def is_in_gpe(match_start, match_end):
        for start, end in gpe_spans_ranges:
            if (match_start < end and match_end > start):
                return True
        return False
    
    # Find and redact complete street addresses (e.g. "123 Main Street")
    for match in re.finditer(street_pattern, redacted_text, re.IGNORECASE):
        if not is_in_gpe(match.start(), match.end()):
            start, end = match.span()
            # Split the match to handle street number and name separately
            parts = match.group().split(' ', 1)
            street_num = parts[0]
            street_name = parts[1]
            
            # Replace just the street number with [REDACTED-NUM]
            redacted_text = redacted_text[:start] + "[REDACTED-NUM] " + street_name + redacted_text[end:]
            
            # Adjust match length after first replacement
            end_adjust = len("[REDACTED-NUM] ") - len(street_num + " ")
            
            # Now find the street suffix within the street name
            for suffix in street_suffixes:
                if re.search(r'\b' + suffix + r'\b', street_name, re.IGNORECASE):
                    # Replace the street name with [REDACTED-STREET]
                    updated_start = start + len("[REDACTED-NUM] ")
                    updated_end = end + end_adjust
                    redacted_text = redacted_text[:updated_start] + "[REDACTED-STREET]" + redacted_text[updated_end:]
                    break
    
    # Redact ZIP codes
    for match in re.finditer(zip_code_pattern, redacted_text):
        if not is_in_gpe(match.start(), match.end()):
            # Check if this looks like an actual ZIP code by looking at context
            context_before = redacted_text[max(0, match.start()-20):match.start()].lower()
            context_after = redacted_text[match.end():min(len(redacted_text), match.end()+20)].lower()
            
            # Only redact if it appears in an address context
            address_indicators = ['address', 'street', 'ave', 'blvd', 'drive', 'lane', 'road', 'court', 'city', 'state', 'zip']
            
            has_address_context = any(indicator in context_before or indicator in context_after for indicator in address_indicators)
            
            if has_address_context:
                start, end = match.span()
                redacted_text = redacted_text[:start] + "[REDACTED-ZIP]" + redacted_text[end:]
    
    # Redact apartment/building numbers
    for match in re.finditer(apt_pattern, redacted_text, re.IGNORECASE):
        if not is_in_gpe(match.start(), match.end()):
            start, end = match.span()
            redacted_text = redacted_text[:start] + "[REDACTED-APT]" + redacted_text[end:]
    
    # Redact PO Boxes
    for match in re.finditer(po_box_pattern, redacted_text, re.IGNORECASE):
        if not is_in_gpe(match.start(), match.end()):
            start, end = match.span()
            redacted_text = redacted_text[:start] + "[REDACTED-PO-BOX]" + redacted_text[end:]
    
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
