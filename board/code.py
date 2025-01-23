from azure.storage.blob import BlobServiceClient
import json

def load_json_from_blob(
    storage_account_name: str,
    storage_account_key: str,
    container_name: str,
    blob_name: str
) -> dict:
    """
    Loads a JSON file from Azure Blob Storage and returns it as a Python dictionary.

    Parameters:
        storage_account_name (str): The name of the Azure Storage account.
        storage_account_key (str): The access key for the Azure Storage account.
        container_name (str): The name of the container in the Azure Blob Storage.
        blob_name (str): The name of the JSON file (blob) in the container.

    Returns:
        dict: A Python dictionary containing the JSON data.
    """
    # Create a BlobServiceClient
    blob_service_client = BlobServiceClient(
        account_url=f"https://{storage_account_name}.blob.core.windows.net",
        credential=storage_account_key
    )

    # Get the blob client
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

    # Download the blob data
    blob_data = blob_client.download_blob().readall()

    # Decode the blob data to a string and parse it as JSON
    json_data = json.loads(blob_data.decode('utf-8'))

    return json_data

# Example usage
if __name__ == "__main__":
    # Define parameters
    storage_account_name = "mystorageaccount"  # Replace with your storage account name
    storage_account_key = "myaccesskey"       # Replace with your storage account key
    container_name = "mycontainer"            # Replace with your container name
    blob_name = "myfile.json"                 # Replace with your JSON file name

    # Load JSON data
    json_data = load_json_from_blob(storage_account_name, storage_account_key, container_name, blob_name)

    # Print the JSON data
    print(json_data)
