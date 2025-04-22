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
    street_number_pattern = r'\b\d+\s'  # Street numbers
    zip_code_pattern = r'\b\d{5}(?:-\d{4})?\b'  # ZIP codes (5 digit or 9 digit format)
    apt_pattern = r'\b(?:apt|apartment|suite|unit|#)\s*[\w-]+\b'  # Apartment/suite numbers
    po_box_pattern = r'\b(?:p\.?o\.?\s*box|post\s*office\s*box)\s*[\w-]+\b'  # PO Boxes
    
    # More comprehensive street name pattern - matches common street suffixes
    street_name_pattern = r'\b[A-Za-z\'\s]+(?:Street|St|Avenue|Ave|Boulevard|Blvd|Drive|Dr|Lane|Ln|Road|Rd|Court|Ct|Way|Place|Pl|Circle|Cir|Terrace|Ter|Highway|Hwy|Parkway|Pkwy|Alley|Route|Rt)\b'
    
    # Find all GPE (geopolitical entities) to preserve cities, states, and countries
    gpe_spans = [ent for ent in doc.ents if ent.label_ == "GPE"]
    gpe_spans_ranges = [(ent.start_char, ent.end_char) for ent in gpe_spans]
    
    # Redact street numbers
    redacted_text = re.sub(street_number_pattern, "[REDACTED-NUM] ", redacted_text, flags=re.IGNORECASE)
    
    # Redact street names using the comprehensive pattern
    for match in re.finditer(street_name_pattern, redacted_text, re.IGNORECASE):
        is_in_gpe = False
        # Check if this street name is part of a GPE (city, state, country)
        for start, end in gpe_spans_ranges:
            if (match.start() < end and match.end() > start):
                is_in_gpe = True
                break
        
        if not is_in_gpe:
            # This is a street name not part of a GPE
            original = match.group()
            replacement = "[REDACTED-STREET]"
            start, end = match.span()
            redacted_text = redacted_text[:start] + replacement + redacted_text[end:]
    
    # Redact ZIP codes
    for match in re.finditer(zip_code_pattern, redacted_text):
        is_in_gpe = False
        for start, end in gpe_spans_ranges:
            if (match.start() < end and match.end() > start):
                is_in_gpe = True
                break
        
        if not is_in_gpe:
            original = match.group()
            replacement = "[REDACTED-ZIP]"
            start, end = match.span()
            redacted_text = redacted_text[:start] + replacement + redacted_text[end:]
    
    # Redact apartment/building numbers
    redacted_text = re.sub(apt_pattern, "[REDACTED-APT]", redacted_text, flags=re.IGNORECASE)
    
    # Redact PO Boxes
    redacted_text = re.sub(po_box_pattern, "[REDACTED-PO-BOX]", redacted_text, flags=re.IGNORECASE)
    
    return redacted_text

# Example usage
if __name__ == "__main__":
    # Sample text with addresses, including your example
    sample_text = """
    John lives at 123 Main Street, Apt 4B, New York, NY 10001, USA.
    The company headquarters is at 456 Business Avenue, Suite 200, Chicago, IL 60601.
    Send your mail to P.O. Box 789, Los Angeles, CA 90001.
    I live at 178 Willow Drive, Apt 3, Memphis, TN, 38124.
    We're opening a new store in Seattle, Washington next month.
    """
    
    redacted = redact_address_components(sample_text)
    print("Original Text:")
    print(sample_text)
    print("\nRedacted Text:")
    print(redacted)
