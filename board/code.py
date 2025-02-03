import pandas as pd

# Calculate the median for the specified columns
median_scores = my_df[['explain_reason', 'beleive_evidence_fully_reviewed']].median()

# Print the results
print("\nMedian Scores (1-5 scale):")
print(f"Explain Reason: {median_scores['explain_reason']}")
print(f"Believe Evidence Fully Reviewed: {median_scores['beleive_evidence_fully_reviewed']}")
