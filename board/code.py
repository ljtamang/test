SELECT 
    SPLIT_PART(file_relative_path, '/', 2) AS product_name,
    CONCAT('=HYPERLINK("https://github.com/department-of-veterans-affairs/va.gov-team/blob/master/', 
           file_relative_path,
           '","',
           file_relative_path,
           '")') AS file_path
FROM 
    your_table_name 
ORDER BY 
    LOWER(SPLIT_PART(file_relative_path, '/', 2)) ASC;
