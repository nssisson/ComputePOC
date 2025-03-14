import requests
import json
import time
import pandas as pd
import io
from azure.storage.blob import BlobServiceClient
import ssl

API_KEY = "0c34b5e00a2480151931f7c6fcc6fe5c"
BASE_URL = "https://api.stlouisfed.org/fred"

delay = 0.4 #FRED has a limit of 120 requests per minute

def get_releases():
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
    data = response.json()
    # The releases are found under the 'release' key in the 'releases' dict.
    return data.get("releases", {})

def get_series_for_release(release_id):
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
    print(response.json)
    data = response.json()
    # Series data is stored under 'series' inside the 'seriess' dictionary.
    return data.get("seriess", {})

def get_all_series(releases):
    release_series_dict = {}
    for release in releases:
        release_id = release.get("id")
        print(release_id)
        if release_id is not None:
            print(f"Fetching series for release ID {release_id}...")
            series = get_series_for_release(release_id)
            release_series_dict[release_id] = series
        time.sleep(delay)
    return release_series_dict

def get_blob_service_client():
    ssl_context = ssl._create_unverified_context()
    account_url = "https://computepocstorage.blob.core.windows.net"
    container_name = "raw"
    sas_token = "sv=2022-11-02&ss=b&srt=co&sp=rwdlacyx&se=2025-04-01T05:14:44Z&st=2025-03-14T21:14:44Z&spr=https&sig=RjihXFoWHI%2FkfjJkitSONq7QWYWzhOpMynMqIE3AEPQ%3D"
    blob_service_client = BlobServiceClient(account_url=account_url, credential=sas_token, connection_verify=False)
    return blob_service_client

def writeBlob(containerName, blobName, dataframe):
    blob_service_client = get_blob_service_client()
    blob_client = blob_service_client.get_blob_client(container=containerName, blob=blobName)
    buffer = io.BytesIO()
    dataframe.to_parquet(buffer, engine="pyarrow", compression="snappy")
    buffer.seek(0)
    print("Writing to Blob: ", blobName)
    blob_client.upload_blob(buffer.getvalue(), overwrite=True)
    print(blobName, " write complete")

def main():
    # This dictionary will store series data for each release keyed by release_id.
    releases = get_releases()
    series = get_all_series(releases)
    releases_df = pd.json_normalize(releases)
    series_df = pd.json_normalize(series)
    print(series_df)
    #writeBlob("raw","FRED_releases/FRED_releases.parquet",releases_df)

  

if __name__ == "__main__":
    main()
