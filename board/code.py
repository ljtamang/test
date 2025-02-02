import pandas as pd
from rake_nltk import Rake
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import nltk
import re

# Download required NLTK data
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

def clean_text(text):
    """Clean and preprocess text data."""
    if isinstance(text, str):
        text = text.lower()
        text = re.sub(r'[^a-zA-Z\s]', '', text)  # Remove non-alphabetic characters
        text = ' '.join(text.split())  # Remove extra spaces
        return text
    return ''

def prepare_data(df, sentiment, trust_scores):
    """
    Prepare and clean the dataframe.
    Filter for specific trust scores and sentiment.
    """
    # Filter for the specified trust scores and sentiment
    filtered_df = df[
        (df['trust'].isin(trust_scores)) &
        (df['sentiment'] == sentiment)
    ].copy()

    # Clean the comments
    filtered_df['cleaned_comment'] = filtered_df['free_text_comment'].apply(clean_text)

    # Remove empty comments
    filtered_df = filtered_df[filtered_df['cleaned_comment'].str.len() > 0]

    return filtered_df

def extract_keyphrases_rake(texts, top_n=50):
    """Extract keyphrases using RAKE."""
    # Initialize RAKE
    rake = Rake()

    # Combine all texts into one
    combined_text = ' '.join(texts)

    # Extract keyphrases
    rake.extract_keywords_from_text(combined_text)

    # Get ranked phrases with scores
    ranked_phrases = rake.get_ranked_phrases_with_scores()

    # Sort and return the top N phrases
    return ranked_phrases[:top_n]

def generate_wordcloud(keyphrases, title="WordCloud of Key Phrases"):
    """Generate a WordCloud from keyphrases."""
    if not keyphrases:
        print("No keyphrases to visualize")
        return

    # Convert keyphrases to a dictionary with scores
    phrase_dict = {phrase: score for score, phrase in keyphrases}

    # Generate the WordCloud
    wordcloud = WordCloud(
        background_color='white',
        colormap='Greens' if 'Positive' in title else 'Reds',  # Use different colors for positive/negative
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

def analyze_comments(df_comments, sentiment, trust_scores, title_prefix):
    """Analyze comments for a specific sentiment and trust score range."""
    try:
        # 1. Prepare and clean data
        print(f"Step 1: Preparing and cleaning data for {sentiment} comments...")
        filtered_df = prepare_data(df_comments, sentiment, trust_scores)

        print(f"\nTotal {sentiment.lower()} comments with trust scores {trust_scores}: {len(filtered_df)}")
        print(f"\nTrust Score Distribution:\n{filtered_df['trust'].value_counts()}")

        # 2. Extract keyphrases using RAKE
        print(f"\nStep 2: Extracting common {sentiment.lower()} keyphrases...")
        keyphrases = extract_keyphrases_rake(filtered_df['cleaned_comment'].tolist())

        if keyphrases:
            print(f"\nTop 10 {sentiment.lower()} keyphrases:")
            for score, phrase in keyphrases[:10]:
                print(f"{phrase}: {score:.4f}")

            # 3. Create WordCloud visualization
            print(f"\nStep 3: Creating WordCloud visualization for {sentiment.lower()} comments...")
            generate_wordcloud(keyphrases, title=f"{title_prefix} WordCloud of {sentiment} Comments")
        else:
            print(f"No keyphrases were extracted for {sentiment.lower()} comments.")

        return filtered_df, keyphrases

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None, None

# Main execution
def main():
    try:
        # Example dataframe (replace this with your actual dataframe)
        data = {
            'trust': [1, 2, 3, 4, 5, 1, 2, 3, 4, 5],
            'free_text_comment': [
                "The product quality is terrible and the service is bad.",
                "I am very disappointed with the delayed delivery.",
                "The experience was amazing, and the staff was very helpful.",
                "Great product! Excellent quality and fast delivery.",
                "Fantastic service and very friendly staff.",
                "Horrible customer service and rude staff.",
                "The product broke after one use. Very poor quality.",
                "I love the design and the ease of use.",
                "The team was very responsive and helpful.",
                "The best experience I've had with any company!"
            ],
            'sentiment': ['Negative', 'Negative', 'Positive', 'Positive', 'Positive', 'Negative', 'Negative', 'Positive', 'Positive', 'Positive']
        }
        df_comments = pd.DataFrame(data)

        # Analyze negative comments (trust scores 1-2)
        print("\nAnalyzing Negative Comments...")
        analyze_comments(df_comments, sentiment='Negative', trust_scores=[1, 2], title_prefix="Negative")

        # Analyze positive comments (trust scores 3 and above)
        print("\nAnalyzing Positive Comments...")
        analyze_comments(df_comments, sentiment='Positive', trust_scores=[3, 4, 5], title_prefix="Positive")

    except Exception as e:
        print(f"Error in main execution: {str(e)}")

if __name__ == "__main__":
    main()
