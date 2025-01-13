def get_file_metadata(file_path: str) -> Union[Dict[str, Union[str, int]], str]:
   """
   Extract file name, path, size and type from a given file path.
   
   Args:
       file_path (str): The full path to the file
       
   Returns:
       Union[Dict[str, Union[str, int]], str]: Dictionary containing file metadata or error message
   """
   try:
       path_obj = Path(file_path)
       metadata = {
           'file_name': path_obj.name,
           'file_path': str(path_obj),
           'file_size_in_bytes': path_obj.stat().st_size,
           'file_type': path_obj.suffix[1:] if path_obj.suffix else 'No extension'
       }
       return metadata
       
   except FileNotFoundError:
       return f"Error: File '{file_path}' not found"
   except Exception as e:
       return f"Error: {str(e)}"

def extract_metadata(file_paths: List[str]) -> List[Union[Dict[str, Union[str, int]], str]]:
   """
   Extract metadata for multiple files.
   
   Args:
       file_paths (List[str]): List of file paths
       
   Returns:
       List[Union[Dict[str, Union[str, int]], str]]: List of dictionaries containing metadata or error messages
   """
   all_metadata = []
   for file_path in file_paths:
       metadata = get_file_metadata(file_path)
       all_metadata.append(metadata)
   return all_metadata
