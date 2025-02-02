import pandas as pd
from keybert import KeyBERT
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import nltk
import re
from sentence_transformers import SentenceTransformer

# Download required NLTK data
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

def clean_text(text):
    """Clean and preprocess text data."""
    if isinstance(text, str):
        text = text.lower()
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        text = ' '.join(text.split())
        return text
    return ''

def prepare_data(df):
    """
    Prepare and clean the dataframe.
    Filter for trust scores 1-2 AND negative sentiment only.
    """
    filtered_df = df[
        (df['trust'].isin([1, 2])) &
        (df['sentiment'] == 'Negative')
    ].copy()

    filtered_df['cleaned_comment'] = filtered_df['free_text_comment'].apply(clean_text)
    filtered_df = filtered_df[filtered_df['cleaned_comment'].str.len() > 0]

    return filtered_df

def extract_keyphrases(texts, top_n=50):
    """Extract keyphrases using KeyBERT with specific model."""
    try:
        # Initialize specific sentence transformer model
        model = SentenceTransformer('all-MiniLM-L6-v2')
        kw_model = KeyBERT(model=model)

        # Combine all texts into one
        combined_text = ' '.join(texts)

        # Extract keyphrases
        keyphrases = kw_model.extract_keywords(
            combined_text,
            keyphrase_ngram_range=(2, 3),
            stop_words='english',
            use_maxsum=True,
            nr_candidates=20,
            top_n=top_n
        )

        return keyphrases
    except Exception as e:
        print(f"Error in keyphrase extraction: {str(e)}")
        return []

def generate_wordcloud(keyphrases, title="WordCloud of Key Phrases"):
    """Generate a WordCloud from keyphrases."""
    if not keyphrases:
        print("No keyphrases to visualize")
        return

    # Convert keyphrases to a dictionary with scores
    phrase_dict = {phrase: score for phrase, score in keyphrases}

    # Generate the WordCloud
    wordcloud = WordCloud(
        background_color='white',
        colormap='Reds',
        width=1200,
        height=800,
        prefer_horizontal=0.7,
        max_words=50,
        min_font_size=10,
        max_font_size=50
    ).generate_from_frequencies(phrase_dict)

    # Plot the WordCloud
    plt.figure(figsize=(15, 8))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title(title, fontsize=16, pad=20)
    plt.tight_layout(pad=0)
    plt.show()

def analyze_negative_comments(df_comments):
    """Main analysis function for negative comments with low trust scores."""
    try:
        # 1. Prepare and clean data
        print("Step 1: Preparing and cleaning data...")
        filtered_df = prepare_data(df_comments)

        print(f"\nTotal negative comments with low trust: {len(filtered_df)}")
        print(f"\nTrust Score Distribution:\n{filtered_df['trust'].value_counts()}")

        # 2. Extract keyphrases
        print("\nStep 2: Extracting common negative keyphrases...")
        keyphrases = extract_keyphrases(filtered_df['cleaned_comment'].tolist())

        if keyphrases:
            print("\nTop 10 negative keyphrases:")
            for phrase, score in keyphrases[:10]:
                print(f"{phrase}: {score:.4f}")

            # 3. Create WordCloud visualization
            print("\nStep 3: Creating WordCloud visualization...")
            generate_wordcloud(keyphrases)
        else:
            print("No keyphrases were extracted.")

        return filtered_df, keyphrases

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None, None

# Main execution
def main():
    try:
        # Run the analysis with your df_comments
        filtered_df, keyphrases = analyze_negative_comments(df_comments)

        if filtered_df is not None:
            print("\nAnalysis completed successfully!")
            print("\nKey Insights:")
            print(f"- Most relevant negative keyphrases found in {len(filtered_df)} comments")
            print(f"- Trust score distribution: {filtered_df['trust'].value_counts().to_dict()}")

    except Exception as e:
        print(f"Error in main execution: {str(e)}")

if __name__ == "__main__":
    main()
