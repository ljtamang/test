   # Apply sentiment analysis and add a new column
    df['sentiment_score'] = df[text_column].apply(lambda text: TextBlob(text).sentiment.polarity)
