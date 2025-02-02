import pandas as pd
import numpy as np

def clean_and_drop_missing(my_df):
    """
    Clean the data by converting 'Not Applicable (N/A)' to NaN and drop rows with missing values.
    Uses complete case analysis (drops rows with any missing values).

    Parameters:
    my_df (pandas.DataFrame): Input dataframe

    Returns:
    pandas.DataFrame: Cleaned dataframe with no missing values
    dict: Summary of cleaning operations
    """
    # Make a copy of the original dataframe
    df_clean = my_df.copy()

    # List of Likert scale columns
    likert_columns = [
        'know_what_to_expect',
        'communicated_what_evidience_needed',
        'medical_exam_process_was_easy',
        'gave_useful_status_update',
        'processing_time',
        'explain_reason',
        'fair_rating',
        'beleive_evidence_fully_reviewed',
        'understand_additional_option',
        'trust'
    ]

    # Store initial state
    summary = {
        'original_rows': len(df_clean),
        'na_counts_before': df_clean[likert_columns].isna().sum().to_dict()
    }

    # Convert 'Not Applicable (N/A)' to NaN for all Likert columns
    for col in likert_columns:
        df_clean[col] = df_clean[col].replace({'Not Applicable (N/A)': np.nan})
        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')

    # Store NA counts after conversion
    summary['na_counts_after'] = df_clean[likert_columns].isna().sum().to_dict()

    # Drop rows with any missing values (complete case analysis)
    df_clean = df_clean.dropna(subset=likert_columns)

    # Update summary
    summary['rows_after_cleaning'] = len(df_clean)
    summary['rows_removed'] = summary['original_rows'] - summary['rows_after_cleaning']
    summary['missing_percentage'] = (my_df[likert_columns].isna().sum() / len(my_df) * 100).to_dict()

    # Print summary
    print("\nData Cleaning Summary:")
    print(f"Original rows: {summary['original_rows']}")
    print(f"Rows after cleaning: {summary['rows_after_cleaning']}")
    print(f"Rows removed: {summary['rows_removed']}")

    print("\nMissing values percentage in original data:")
    for col, pct in summary['missing_percentage'].items():
        print(f"{col}: {pct:.2f}%")

    return df_clean, summary

# Example usage:
# cleaned_df, summary = clean_and_drop_missing(my_df)

def analyze_relationships(df):
    """
    Analyze relationships between predictors and trust
    """
    correlations = df.corr(method='spearman')['trust'].sort_values(ascending=False)

    print("\nCorrelations with trust (Spearman):")
    print(correlations)

    return correlations

# Run the complete analysis
cleaned_df, summary = clean_and_drop_missing(my_df)
correlations = analyze_relationships(cleaned_df)
