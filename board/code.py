'file_path': str(path_obj),
           'file_size_in_bytes': path_obj.stat().st_size,
           'file_type': path_obj.suffix[1:] if path_obj.suffix else 'No extension'  # Remove the dot from extension
