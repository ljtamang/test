SELECT 
    SPLIT_PART(file_relative_path, '/', 2) AS product_name,
    file_relative_path,
    file_extension,
    category,
    CONCAT('https://github.com/department-of-veterans-affairs/va.gov-team/blob/main/', file_relative_path) AS github_link
FROM 
    your_table_name 
ORDER BY 
    LOWER(SPLIT_PART(file_relative_path, '/', 2)) ASC;
