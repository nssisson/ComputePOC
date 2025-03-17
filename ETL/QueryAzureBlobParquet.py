import azure.storage.blob as blob
import pandas as pd
import pyarrow.parquet as pq
import fnmatch
import ssl
import io
SERVICE_CLIENT = None
CONTAINER_CLIENT = None

def get_blob_service_client():
    global SERVICE_CLIENT
    ssl_context = ssl._create_unverified_context()
    account_url = "https://computepocstorage.blob.core.windows.net"
    container_name = "raw"
    sas_token = "sv=2022-11-02&ss=b&srt=co&sp=rwdlacyx&se=2025-04-01T05:14:44Z&st=2025-03-14T21:14:44Z&spr=https&sig=RjihXFoWHI%2FkfjJkitSONq7QWYWzhOpMynMqIE3AEPQ%3D"
    SERVICE_CLIENT = blob.BlobServiceClient(account_url=account_url, credential=sas_token, connection_verify=False)
    return SERVICE_CLIENT

def get_blobs(container_name, filepattern):
    global CONTAINER_CLIENT
    CONTAINER_CLIENT = get_blob_service_client().get_container_client(container_name)
    blob_list = CONTAINER_CLIENT.list_blobs(name_starts_with=filepattern)
    parquet_blobs = [blob.name for blob in blob_list if fnmatch.fnmatch(blob.name, "*.parquet")]
    return parquet_blobs


def get_dataframe(container_name, filepattern):
    dataframes = []
    parquet_blobs = get_blobs(container_name, filepattern)
    for blob_name in parquet_blobs:
        # Download blob content into memory
        blob_client = CONTAINER_CLIENT.get_blob_client(blob_name)
        stream = io.BytesIO()
        blob_client.download_blob().readinto(stream)
        stream.seek(0)  # Reset stream position

        # Read Parquet file into a DataFrame
        table = pq.read_table(stream)
        df = table.to_pandas()
        df['source_file'] = blob_name
        dataframes.append(df)
    combined_df = pd.concat(dataframes, ignore_index=True)
    return combined_df

def query(container_name, filepattern):
    return get_dataframe(container_name, filepattern)