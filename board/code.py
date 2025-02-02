# Filter rows where 'trust' and 'comments' columns are not empty
df_comments = df[(df['trust'].notna()) & (df['comments'].notna())].copy()
