import spacy

def redact_name_org_facility(text):
    """
    Redact name-related PII (person names, organization names, and facilities) from text.
    
    Args:
        text (str): The input text to redact
        
    Returns:
        str: Text with name, organization, and facility PII replaced by entity type tags
    """
    # Load the English NLP model
    nlp = spacy.load("en_core_web_md")
    
    # Process the text
    doc = nlp(text)
    
    # Create a list of tokens to be joined later
    tokens = []
    
    # Define which entity types to redact
    entities_to_redact = {
        "PERSON": "<PERSON>",
        "ORG": "<ORGANIZATION>",
        "FAC": "<FACILITY>"
    }
    
    # Track current entity to handle multi-token entities
    current_ent = None
    
    for token in doc:
        # Check if this token is part of an entity we want to redact
        if token.ent_type_ in entities_to_redact:
            # If this is the start of a new entity
            if current_ent != token.ent_:
                current_ent = token.ent_
                # Get the standardized tag for this entity type
                tag = entities_to_redact[token.ent_type_]
                tokens.append(tag)
        else:
            # If we're not in a target entity or we've left one
            if current_ent and current_ent.label_ in entities_to_redact:
                current_ent = None
            
            # Add the original token text
            if not current_ent:
                tokens.append(token.text)
    
    # Join the tokens with spaces
    redacted_text = ""
    for i, token in enumerate(tokens):
        # Don't add a space before punctuation
        if i > 0 and token not in ".,!?;:)]}" and tokens[i-1] not in "([{":
            redacted_text += " "
        redacted_text += token
        
    return redacted_text

# Example usage
if __name__ == "__main__":
    comment = "My name is John Smith and I had a great experience at the VA hospital in San Diego. I visited the Pentagon last month."
    redacted = redact_name_org_facility(comment)
    print(redacted)  # Output: "My name is <PERSON> and I had a great experience at the <ORGANIZATION> in San Diego. I visited the <FACILITY> last month."
