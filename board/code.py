from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

df['sentiment'] = df['comment'].apply(lambda x: SentimentIntensityAnalyzer().polarity_scores(x)['compound'])
