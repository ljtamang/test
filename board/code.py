import pandas as pd
import numpy as np
from keybert import KeyBERT
import matplotlib.pyplot as plt
import seaborn as sns
import nltk
from nltk.corpus import stopwords
import re

# Download required NLTK data
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)

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
    # Filter for low trust (1-2) AND negative sentiment
    filtered_df = df[
        (df['trust'].isin([1, 2])) &
        (df['sentiment'] == 'Negative')
    ].copy()

    # Clean the comments
    filtered_df['cleaned_comment'] = filtered_df['free_text_comment'].apply(clean_text)

    # Remove empty comments
    filtered_df = filtered_df[filtered_df['cleaned_comment'].str.len() > 0]

    return filtered_df

def extract_keyphrases(texts, top_n=20):
    """Extract keyphrases using KeyBERT."""
    # Initialize KeyBERT
    kw_model = KeyBERT()

    # Combine all texts into one
    combined_text = ' '.join(texts)

    # Extract keyphrases
    keyphrases = kw_model.extract_keywords(
        combined_text,
        keyphrase_ngram_range=(2, 3),  # Extract 2-3 word phrases
        stop_words='english',
        use_maxsum=True,
        nr_candidates=20,
        top_n=top_n
    )

    return keyphrases

def plot_keyphrases(keyphrases, n=15, title="Top Negative Keyphrases in Low Trust Comments"):
    """Plot top keyphrases as a horizontal bar chart."""
    plt.figure(figsize=(12, 6))

    phrases = [phrase for phrase, score in keyphrases[:n]]
    scores = [score for phrase, score in keyphrases[:n]]

    plt.barh(phrases, scores, color='salmon')
    plt.xlabel("Relevance Score")
    plt.title(title)
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.show()

def plot_keyphrase_heatmap(keyphrases, n=20):
    """Create a heatmap visualization of keyphrase relevance."""
    plt.figure(figsize=(12, 8))

    # Prepare data for heatmap
    phrases = [phrase for phrase, _ in keyphrases[:n]]
    scores = [score for _, score in keyphrases[:n]]

    # Reshape data for heatmap (4x5 matrix)
    matrix = np.array(scores[:20]).reshape(4, 5)

    # Plot heatmap
    sns.heatmap(matrix,
                annot=True,
                fmt='.3f',
                cmap='Reds',
                xticklabels=range(1, 6),
                yticklabels=range(1, 5))

    plt.title("Keyphrase Relevance Heatmap")
    plt.tight_layout()
    plt.show()

def analyze_by_trust_score(df, keyphrases):
    """Analyze keyphrase occurrence by trust score (1 vs 2)."""
    def contains_phrase(text, phrase):
        return 1 if phrase in text else 0

    top_phrases = [phrase for phrase, _ in keyphrases[:10]]

    analysis_df = pd.DataFrame()
    for phrase in top_phrases:
        df[f'contains_{phrase}'] = df['cleaned_comment'].apply(
            lambda x: contains_phrase(x, phrase)
        )
        trust_counts = df.groupby('trust')[f'contains_{phrase}'].sum()
        analysis_df[phrase] = trust_counts

    return analysis_df

def plot_trust_analysis(trust_analysis):
    """Plot phrase distribution across trust scores."""
    plt.figure(figsize=(12, 6))
    trust_analysis.plot(kind='bar')
    plt.title("Negative Keyphrase Distribution by Trust Score")
    plt.xlabel("Trust Score")
    plt.ylabel("Frequency")
    plt.xticks(rotation=0)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
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
        print("\nTop 10 negative keyphrases:")
        for phrase, score in keyphrases[:10]:
            print(f"{phrase}: {score:.4f}")

        # 3. Create visualizations
        print("\nStep 3: Creating visualizations...")
        plot_keyphrases(keyphrases)
        plot_keyphrase_heatmap(keyphrases)

        # 4. Analyze by trust score
        print("\nStep 4: Analyzing keyphrases by trust score...")
        trust_analysis = analyze_by_trust_score(filtered_df, keyphrases)
        plot_trust_analysis(trust_analysis)

        return filtered_df, keyphrases, trust_analysis

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None, None, None

# Main execution
def main():
    try:
        # Run the analysis
        filtered_df, keyphrases, trust_analysis = analyze_negative_comments(df_comments)

        if filtered_df is not None:
            print("\nAnalysis completed successfully!")
            print("\nKey Insights:")
            print(f"- Most relevant negative keyphrases found in {len(filtered_df)} comments")
            print(f"- Trust score distribution: {filtered_df['trust'].value_counts().to_dict()}")

    except Exception as e:
        print(f"Error in main execution: {str(e)}")

if __name__ == "__main__":
    main()
