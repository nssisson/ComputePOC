import requests
import json
import time

API_KEY = "0c34b5e00a2480151931f7c6fcc6fe5c"
BASE_URL = "https://api.stlouisfed.org/fred"

delay = 0.5 #FRED has a limit of 120 requests per minute

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
    data = response.json()
    # Series data is stored under 'series' inside the 'seriess' dictionary.
    return data.get("seriess", {})
def main():
    # This dictionary will store series data for each release keyed by release_id.
    release_series_dict = {}
    
    releases = get_releases()
    #print(json.dumps(releases, indent=2))
    
    
    for release in releases:
        release_id = release.get("id")
        print(release_id)
        if release_id is not None:
            print(f"Fetching series for release ID {release_id}...")
            series = get_series_for_release(release_id)
            release_series_dict[release_id] = series
        time.sleep(delay)
    print(len(release_series_dict))
    # Output the resulting dictionary in a pretty-printed JSON format.
    #print(json.dumps(release_series_dict, indent=2))'
  

if __name__ == "__main__":
    main()
