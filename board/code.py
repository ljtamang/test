missing_percentage = df.isna().mean() * 100
print(missing_percentage)

df_clean = df.dropna(subset=['trust'])

df_clean.fillna(df_clean.mean(), inplace=True)  # Mean imputation
# Or use median:
df_clean.fillna(df_clean.median(), inplace=True)


import pandas as pd
import numpy as np

# Example dataframe
data = {
    'know_what_to_expect': [5, 4, np.nan, 3, 2],
    'communicated_what_evidience_needed': [4, np.nan, 3, 2, 1],
    'trust': [5, 4, 3, np.nan, 1]
}
df = pd.DataFrame(data)

# Step 1: Drop rows where trust is missing (partial case analysis)
df_clean = df.dropna(subset=['trust'])

# Step 2: Impute missing values in predictors
df_clean.fillna(df_clean.mean(), inplace=True)  # Replace missing values with column mean

print("Cleaned Data:")
print(df_clean)
