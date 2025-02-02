# Count sentiment categories grouped by trust score
sentiment_counts_by_trust = df.groupby('trust')['sentiment_category'].value_counts().unstack(fill_value=0)

# Display the result
print(sentiment_counts_by_trust)
