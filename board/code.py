# Add sentiment classification column using a lambda function
df_comments['sentiment'] = df_comments['sentiment_score'].apply(
    lambda score: "Positive" if score > 0 else ("Negative" if score < 0 else "Neutral")
)
