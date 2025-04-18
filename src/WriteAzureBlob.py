from azure.storage.blob import BlobServiceClient
import ssl
import io

BLOB_SERVICE_CLIENT = None

def get_blob_service_client():
    ssl_context = ssl._create_unverified_context()
    account_url = "https://computepocstorage.blob.core.windows.net"
    container_name = "raw"
    sas_token = "sp=racwdlme&st=2025-04-15T21:43:23Z&se=2025-05-01T05:43:23Z&sv=2024-11-04&sr=c&sig=kQbhUdq5ZEcmCDnBQjoLyCZHYn92wY4Cv0dJzAHGlaM%3D"
    blob_service_client = BlobServiceClient(account_url=account_url, credential=sas_token, connection_verify=False)
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