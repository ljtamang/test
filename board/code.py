import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk
from nltk.corpus import stopwords
import re
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Download required NLTK data
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)

def clean_text(text):
    """Clean and preprocess text data."""
    if isinstance(text, str):
        text = text.lower()
        text = re.sub(r'[^a-zA-Z\s]', '', text)  # Remove special characters and digits
        text = ' '.join(text.split())  # Remove extra whitespace
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

    # Add analysis metadata
    filtered_df['comment_length'] = filtered_df['cleaned_comment'].str.len()

    return filtered_df

def extract_phrases_tfidf(texts, max_features=50):
    """Extract phrases using TF-IDF."""
    tfidf = TfidfVectorizer(
        ngram_range=(2, 3),  # Extract bigrams and trigrams
        max_features=max_features,
        stop_words='english'
    )
    tfidf_matrix = tfidf.fit_transform(texts)
    feature_names = tfidf.get_feature_names_out()
    scores = tfidf_matrix.sum(axis=0).A1
    phrase_scores = dict(zip(feature_names, scores))
    sorted_phrases = sorted(phrase_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_phrases

def plot_top_phrases(phrases, n=15, title="Top Negative Phrases in Low Trust Comments"):
    """Plot top phrases as a horizontal bar chart."""
    plt.figure(figsize=(12, 6))
    labels, values = zip(*phrases[:n])
    plt.barh(labels, values, color='salmon')  # Changed color to reflect negative sentiment
    plt.xlabel("TF-IDF Score")
    plt.title(title)
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.show()

def create_wordcloud(phrases):
    """Create and display word cloud of phrases."""
    word_freq = dict(phrases)
    wordcloud = WordCloud(
        width=800,
        height=400,
        background_color='white',
        colormap='Reds',  # Changed colormap to reflect negative sentiment
        max_words=50
    ).generate_from_frequencies(word_freq)

    plt.figure(figsize=(15, 8))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title("Word Cloud of Common Negative Phrases in Low Trust Comments")
    plt.show()

def analyze_by_trust_score(df, phrases):
    """Analyze phrase occurrence by trust score (1 vs 2)."""
    def contains_phrase(text, phrase):
        return 1 if phrase in text else 0

    top_phrases = [phrase[0] for phrase in phrases[:10]]

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
    plt.title("Negative Phrase Distribution by Trust Score")
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

        # Get data summary
        print(f"Total negative comments with low trust: {len(filtered_df)}")
        print(f"Trust Score Distribution:\n{filtered_df['trust'].value_counts()}")

        # 2. Extract phrases
        print("\nStep 2: Extracting common negative phrases...")
        phrases = extract_phrases_tfidf(filtered_df['cleaned_comment'])
        print("\nTop 10 negative phrases:")
        for phrase, score in phrases[:10]:
            print(f"{phrase}: {score:.4f}")

        # 3. Create visualizations
        print("\nStep 3: Creating visualizations...")
        plot_top_phrases(phrases)
        create_wordcloud(phrases)

        # 4. Analyze by trust score
        print("\nStep 4: Analyzing phrases by trust score...")
        trust_analysis = analyze_by_trust_score(filtered_df, phrases)
        plot_trust_analysis(trust_analysis)

        return filtered_df, phrases, trust_analysis

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None, None, None
