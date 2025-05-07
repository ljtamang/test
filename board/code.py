import spacy
import re

def redact_person_names(text):
    """
    Function to identify and redact person names in text.
    Replaces identified person names with <PERSON> tag.
    
    Args:
        text (str): Input text to process
        
    Returns:
        str: Text with person names redacted
    """
    # Load spaCy English model with NER capability
    nlp = spacy.load("en_core_web_lg")
    
    # Process the text
    doc = nlp(text)
    
    # Create a list to store the spans that need to be redacted
    spans_to_redact = []
    
    # Find person entities using spaCy's NER
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            spans_to_redact.append((ent.start_char, ent.end_char))
    
    # Additional patterns to catch names that might be missed by spaCy
    
    # Pattern for titles followed by names
    title_pattern = r'\b(Dr\.|Mr\.|Mrs\.|Ms\.|Miss|Sgt\.|Col\.|Gen\.|Prof\.|Lieutenant|Captain|Major)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
    for match in re.finditer(title_pattern, text):
        name_start = match.start(2)  # Start of the name after the title
        name_end = match.end(2)
        spans_to_redact.append((name_start, name_end))
    
    # Pattern for names with apostrophes or hyphens
    special_name_pattern = r'\b[A-Z][a-z]+(?:[-\']\w+)+\b'
    for match in re.finditer(special_name_pattern, text):
        spans_to_redact.append((match.start(), match.end()))
    
    # Sort spans in reverse order to avoid messing up character positions when replacing
    spans_to_redact.sort(key=lambda x: x[0], reverse=True)
    
    # Replace each span with <PERSON>
    result = text
    for start, end in spans_to_redact:
        result = result[:start] + "<PERSON>" + result[end:]
    
    return result

# Function to demonstrate redaction on the sample comments
def demonstrate_redaction(examples):
    print("Original Text -> Redacted Text")
    
    for example in examples:
        redacted = redact_person_names(example)
        print(f"Original: {example}")
        print(f"Redacted: {redacted}")
        print("-" * 50)

# Sample comments
sample_comments = [
    "Dr. Smith at the VA clinic in Phoenix was very helpful with my medication issues.",
    "I waited 3 hours before John Williams finally called me back about my benefits claim.",
    "The nurse practitioner Mary Jane Johnson took time to explain everything clearly.",
    "My experience with Sgt. Rodriguez during my transition assistance was outstanding.",
    "I was disappointed that Ms. Sarah O'Malley-Smith didn't follow up as promised.",
    "When I called about my appointment, Robert told me I needed to bring different paperwork.",
    "The physical therapist (David Lee, I think) showed me exercises that really helped my back pain.",
    "I would like to thank Nguyen from the front desk for going above and beyond.",
    "My VSO J.R. Thompson helped me navigate the claims process efficiently.",
    "I'm grateful to both Dr. Li and Nurse Washington for their exceptional care."
]

# Demonstrate the redaction
demonstrate_redaction(sample_comments)
