def check_for_zee(names):
    """
    Check if the word 'zee' exists in the list of names.
    Returns True if found, False otherwise.
    Case-insensitive search.
    """
    return any('zee' in name.lower() for name in names)

# Example usage
def main():
    # Sample list of names
    names = ['John', 'Zee Smith', 'Alice', 'Zeeland', 'Bob']
    
    result = check_for_zee(names)
    if result:
        print("The word 'zee' was found in the list")
    else:
        print("The word 'zee' was not found in the list")

# Test the function
if __name__ == "__main__":
    main()
