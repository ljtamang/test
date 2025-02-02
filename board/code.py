# Define custom colors
custom_colors = {'negative': '#FF4C4C', 'positive': '#4CAF50', 'neutral': '#B0B0B0'}

# Plot grouped bar chart with custom colors
ax = sentiment_counts_by_trust.plot(kind='bar', figsize=(10, 6), color=[custom_colors[col] for col in sentiment_counts_by_trust.columns])

# Customize the chart
plt.title("Sentiment Distribution by Trust Score")
plt.xlabel("Trust Score")
plt.ylabel("Count of Sentiments")
plt.legend(title="Sentiment Category")
plt.xticks(rotation=45)
plt.grid(axis='y', linestyle='--', alpha=0.7)

# Show the plot
plt.show()
