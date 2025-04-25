from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
import ssl
import io
import json

BLOB_SERVICE_CLIENT = None

def get_blob_service_client():
    account_url = "https://computepocstorage.blob.core.windows.net"
    blob_service_client = BlobServiceClient(
        account_url=account_url,
        credential = DefaultAzureCredential()
        #,connection_verify=False  #uncomment to run locally with certificate issue
    )
    return blob_service_client

def writeDataframeToBlob(containerName, blobName, dataframe):
    global BLOB_SERVICE_CLIENT
    if BLOB_SERVICE_CLIENT is None:
        print("Retrieving")
        BLOB_SERVICE_CLIENT = get_blob_service_client()
    blob_client = BLOB_SERVICE_CLIENT.get_blob_client(container=containerName, blob=blobName)
    buffer = io.BytesIO()
    dataframe.to_parquet(buffer, engine="pyarrow", compression="snappy")
    buffer.seek(0)
    blob_client.upload_blob(buffer.getvalue(), overwrite=True)
    print("Written to Blob: ", blobName)

def writeJsonToBlob(containerName, blobName, contents):
    global BLOB_SERVICE_CLIENT
    if BLOB_SERVICE_CLIENT is None:
        print("Retrieving")
        BLOB_SERVICE_CLIENT = get_blob_service_client()
    blob_client = BLOB_SERVICE_CLIENT.get_blob_client(container=containerName, blob=blobName)
    blob = json.dumps(contents)
    blob_client.upload_blob(blob, overwrite=True)
    print("Written to Blob: ", blobName)