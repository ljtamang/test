def extract_keyphrases_rake(texts, top_n=50):
    """Extract keyphrases using RAKE and remove duplicates."""
    # Initialize RAKE
    rake = Rake()

    # Combine all texts into one
    combined_text = ' '.join(texts)

    # Extract keyphrases
    rake.extract_keywords_from_text(combined_text)

    # Get ranked phrases with scores
    ranked_phrases = rake.get_ranked_phrases_with_scores()

    # Remove duplicates by normalizing phrases (convert to lowercase)
    unique_phrases = {}
    for score, phrase in ranked_phrases:
        normalized_phrase = phrase.lower()  # Normalize to lowercase
        if normalized_phrase not in unique_phrases:
            unique_phrases[normalized_phrase] = score

    # Sort the unique phrases by score in descending order
    sorted_phrases = sorted(unique_phrases.items(), key=lambda x: x[1], reverse=True)

    # Return the top N phrases
    return sorted_phrases[:top_n]
