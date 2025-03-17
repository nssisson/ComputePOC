import requests
import json
import time
import pandas as pd
import io
from azure.storage.blob import BlobServiceClient
import ssl

API_KEY = "0c34b5e00a2480151931f7c6fcc6fe5c"
BASE_URL = "https://api.stlouisfed.org/fred"
BLOB_SERVICE_CLIENT = None

delay = 0.4 #FRED has a limit of 120 requests per minute

def process_releases():
    """Fetches all releases from FRED."""
    url = f"{BASE_URL}/releases"
    params = {
        "api_key": API_KEY,
        "file_type": "json"
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print("Error fetching releases:", response.status_code)
        return []
    jsonData = response.json().get("releases", {})
    releases_df = pd.json_normalize(jsonData)
    writeDataframeToBlob("raw", "FRED_releases/FRED_releases.parquet", releases_df)
    process_all_series(jsonData)

def process_series_for_release(release_id):
    """Fetches series data for a given release."""
    url = f"{BASE_URL}/release/series"
    params = {
        "api_key": API_KEY,
        "file_type": "json",
        "release_id": release_id
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"Error fetching series for release {release_id}: {response.status_code}")
        return []
    jsonData = response.json().get("seriess", {})
    series_df = pd.json_normalize(jsonData)
    writeDataframeToBlob("raw", f"FRED_series/FRED_series_{release_id}.parquet""", series_df)
    process_all_observations(jsonData)

def process_all_series(releases):
    release_series_dict = {}
    #for release in releases:
    i=0
    while i < 50 and i < len(releases): 
        release_id = releases[i].get("id")
        if release_id is not None:
            print(f"Fetching series for release ID {release_id}...")
            series = process_series_for_release(release_id)
            release_series_dict[release_id] = series
        time.sleep(delay)
        i+=1
    return release_series_dict

def process_observations_for_series(series_id):
    url = f"{BASE_URL}/series/observations"
    params = {
        "api_key": API_KEY,
        "file_type": "json",
        "series_id": series_id
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"Error fetching series for series {series_id}: {response.status_code}")
        return []
    jsonData = response.json().get("observations", {})
    observation_df = pd.json_normalize(jsonData)
    writeDataframeToBlob("raw", f"FRED_observations/FRED_observations_{series_id}.parquet""", observation_df)

def process_all_observations(series):
    i=0
    while i < 50 and i < len(series): 
        series_id = series[i].get("id")
        if series_id is not None:
            print(f"Fetching observations for series ID {series_id}...")
            process_observations_for_series(series_id)
        time.sleep(delay)
        i+=1

def get_blob_service_client():
    ssl_context = ssl._create_unverified_context()
    account_url = "https://computepocstorage.blob.core.windows.net"
    container_name = "raw"
    sas_token = "sv=2022-11-02&ss=b&srt=co&sp=rwdlacyx&se=2025-04-01T05:14:44Z&st=2025-03-14T21:14:44Z&spr=https&sig=RjihXFoWHI%2FkfjJkitSONq7QWYWzhOpMynMqIE3AEPQ%3D"
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

def main():
    process_releases()


if __name__ == "__main__":
    main()
