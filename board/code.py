import matplotlib.pyplot as plt

# Plot stacked bar chart
sentiment_counts_by_trust.plot(kind='bar', stacked=True, figsize=(10, 6), colormap='viridis')

plt.title("Sentiment Distribution by Trust Score")
plt.xlabel("Trust Score")
plt.ylabel("Count of Sentiments")
plt.legend(title="Sentiment Category")
plt.xticks(rotation=45)
plt.show()

sentiment_counts_by_trust.plot(kind='bar', figsize=(10, 6), colormap='Set2')

plt.title("Sentiment Distribution by Trust Score")
plt.xlabel("Trust Score")
plt.ylabel("Count of Sentiments")
plt.legend(title="Sentiment Category")
plt.xticks(rotation=45)
plt.show()
