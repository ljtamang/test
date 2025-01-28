SELECT
    -- Extract the second part of the file_relative_path as product_name
    SPLIT_PART(file_relative_path, '/', 2) AS product_name,
    file_relative_path,
    file_extension,
    category
FROM
    your_table_name
