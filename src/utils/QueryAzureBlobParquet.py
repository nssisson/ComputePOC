import azure.storage.blob as blob
import pandas as pd
import fnmatch
import ssl
import io
import asyncio

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


async def read_blob_async(blob_client, loop):
    """Read a single blob asynchronously and return the raw data"""
    # Run the blocking IO operations in a thread pool
    blob_data = await loop.run_in_executor(None, blob_client.download_blob)
    
    # Using stream download to avoid loading entire blob into memory at once
    stream = io.BytesIO()
    await loop.run_in_executor(None, lambda: blob_data.readinto(stream))
    stream.seek(0)
    return stream, blob_client.blob_name

async def download_all_blobs(blob_names, max_concurrency=20):
    """Download all blobs in parallel using asyncio with semaphore"""
    # Initialize the blob service client
    # Create a list of blob clients
    blob_clients = [CONTAINER_CLIENT.get_blob_client(blob) for blob in blob_names]
    
    # Get the event loop
    loop = asyncio.get_event_loop()
    # Create semaphore to limit concurrency
    sem = asyncio.Semaphore(max_concurrency)
    results = []
    async def download_with_semaphore(client):
        async with sem:
            return await read_blob_async(client, loop)
    
    # Create tasks for all blobs
    tasks = [download_with_semaphore(client) for client in blob_clients]
    # Process as they complete
    for completed_task in asyncio.as_completed(tasks):
        try:
            result = await completed_task
            results.append(result)
            print(f"Successfully downloaded {result[1]}")
        except Exception as e:
            print(f"Error downloading blob: {e}")
    
    return results

def process_results(results):
    """Process downloaded results into dataframes synchronously"""
    dfs = []
    for stream, blob_name in results:
        try:
            df = pd.read_parquet(stream)
            df['source_file'] = blob_name
            dfs.append(df)
        except Exception as e:
            print(f"Error processing {blob_name}: {e}")
    
    # Combine all dataframes
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    else:
        return pd.DataFrame()

async def query(container_name, filepattern):
    enumerate_blobs = get_blobs(container_name, filepattern)
    all_blobs = await download_all_blobs(enumerate_blobs)
    df_all = process_results(all_blobs)
    return df_all