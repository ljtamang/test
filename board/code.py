import spacy

def redact_name_pii(text):
    """
    Redact only name-related PII (person names and organization names) from text.
    
    Args:
        text (str): The input text to redact
        
    Returns:
        str: Text with name PII replaced by entity type tags
    """
    # Load the English NLP model
    nlp = spacy.load("en_core_web_md")
    
    # Process the text
    doc = nlp(text)
    
    # Create a list of tokens to be joined later
    tokens = []
    
    # Define which entity types to redact (only names)
    name_entities = {
        "PERSON": "<PERSON>",
        "ORG": "<ORGANIZATION>"
    }
    
    # Track current entity to handle multi-token entities
    current_ent = None
    
    for token in doc:
        # Check if this token is part of a name entity we want to redact
        if token.ent_type_ in name_entities:
            # If this is the start of a new entity
            if current_ent != token.ent_:
                current_ent = token.ent_
                # Get the standardized tag for this entity type
                tag = name_entities[token.ent_type_]
                tokens.append(tag)
        else:
            # If we're not in a name entity or we've left one
            if current_ent and current_ent.label_ in name_entities:
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
    comment = "Lasang works for University of Memphis during the day and lives in Nashville."
    redacted = redact_name_pii(comment)
    print(redacted)  # Output: "<PERSON> works for <ORGANIZATION> during the day and lives in Nashville."
