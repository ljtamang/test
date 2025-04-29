# Write DataFrame to a table in Databricks with overwrite mode
df.write.format("delta").mode("overwrite").saveAsTable("your_table_name")
