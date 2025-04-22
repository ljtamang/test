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
    nlp = spacy.load("en_core_web_lg")  # Use the large model for better NER
    
    # Process the text
    doc = nlp(text)
    
    # Create a copy of the text that we'll modify
    redacted_text = text
    
    # Track offsets as we modify the text
    offset = 0
    
    # Regular expressions for address components
    street_number_pattern = r'\b\d+\s'  # Street numbers
    zip_code_pattern = r'\b\d{5}(?:-\d{4})?\b'  # ZIP codes (5 digit or 9 digit format)
    apt_pattern = r'\b(?:apt|apartment|suite|unit|#)\s*[\w-]+\b'  # Apartment/suite numbers
    po_box_pattern = r'\b(?:p\.?o\.?\s*box|post\s*office\s*box)\s*[\w-]+\b'  # PO Boxes
    
    # Find all GPE (geopolitical entities) to preserve cities, states, and countries
    gpe_spans = [ent for ent in doc.ents if ent.label_ == "GPE"]
    gpe_spans_ranges = [(ent.start_char, ent.end_char) for ent in gpe_spans]
    
    # Find all address entities
    for ent in doc.ents:
        if ent.label_ == "LOC" or ent.label_ == "FAC":
            # Check if this entity overlaps with any GPE (cities, states, countries)
            is_protected = False
            for start, end in gpe_spans_ranges:
                if (ent.start_char < end and ent.end_char > start):
                    is_protected = True
                    break
            
            if not is_protected:
                # This is likely a street name or other address component we want to redact
                # Redact the entire span
                original = text[ent.start_char:ent.end_char]
                replacement = "[REDACTED-STREET]"
                redacted_text = redacted_text[:ent.start_char + offset] + replacement + redacted_text[ent.end_char + offset:]
                offset += len(replacement) - len(original)
    
    # Use regex to find and redact street numbers, ZIP codes, and apartment numbers
    # Redact street numbers
    redacted_text = re.sub(street_number_pattern, "[REDACTED-NUM] ", redacted_text, flags=re.IGNORECASE)
    
    # Redact ZIP codes (but make sure they're not inside GPE spans)
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
    # Sample text with addresses
    sample_text = """
    John lives at 123 Main Street, Apt 4B, New York, NY 10001, USA.
    The company headquarters is at 456 Business Avenue, Suite 200, Chicago, IL 60601.
    Send your mail to P.O. Box 789, Los Angeles, CA 90001.
    We're opening a new store in Seattle, Washington next month.
    """
    
    redacted = redact_address_components(sample_text)
    print("Original Text:")
    print(sample_text)
    print("\nRedacted Text:")
    print(redacted)
