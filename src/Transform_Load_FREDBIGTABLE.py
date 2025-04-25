import QueryAzureBlobParquet
import WriteAzureBlob
import duckdb
import time
import asyncio

def main():
    total_start_time = time.time()

    step_start_time = time.time()
    releases_df = asyncio.run(QueryAzureBlobParquet.query("raw", "FRED_releases"))
    releases_time = time.time() - step_start_time

    step_start_time = time.time()
    series_df = asyncio.run(QueryAzureBlobParquet.query("raw", "FRED_series"))
    series_df["releases_id"] = series_df['source_file'].str.extract(r'_(\d+)\.parquet').astype(int)
    series_time = time.time() - step_start_time

    step_start_time = time.time()
    observation_df = asyncio.run(QueryAzureBlobParquet.query("raw", "FRED_observations"))
    observation_df["series_id"] = observation_df['source_file'].str.extract(r'FRED_observations_(.*?)\.parquet')
    observation_time = time.time() - step_start_time

    query = '''
    SELECT 
        r.id AS ReleaseId,
        r.name AS ReleaseName,
        r.link AS ReleaseLink,
        r.notes AS ReleaseNotes,
        s.id AS SeriesId,
        s.title AS SeriesTitle,
        s.observation_start AS SeriesStart,
        s.observation_end AS SeriesEnd,
        s.frequency AS SeriesFrequency,
        s.units AS SeriesUnits,
        s.seasonal_adjustment AS SeriesSeasonalAdjustment,
        s.last_updated AS SeriesLastUpdated,
        s.popularity AS SeriesPopularity,
        s.group_popularity AS SeriesGroupPopularity,
        s.notes AS SeriesNotes,
        o.date AS ObservationDate,
        o.value AS ObservationValue
    FROM releases_df r
    INNER JOIN series_df s ON r.id = s.releases_id
    INNER JOIN observation_df o ON s.id = o.series_id
    '''
    step_start_time = time.time()
    merged = duckdb.query(query).to_df()
    duckdb_time = time.time() - step_start_time

    step_start_time = time.time()
    WriteAzureBlob.writeDataframeToBlob("raw", "FRED_BigTable/FRED_BigTable.parquet", merged)
    blobwrite_time = time.time() - step_start_time



    total_end_time = time.time() - total_start_time


    print(f"Releases Execution time: {releases_time} seconds")
    print(f"Series Execution time: {series_time} seconds")
    print(f"Observation Execution time: {observation_time} seconds")
    print(f"Duckdb Execution time: {duckdb_time} seconds")
    print(f"BlobWrite Execution time: {blobwrite_time} seconds")
    print(f"Total Execution time: {total_end_time} seconds")

    output = {}
    output["status"] = 'success'
    output["output"] = {}
    output["output"]["rowsWritten"] = len(merged)
    output["output"]["executionDuration"] = total_end_time
    return output




if __name__ == "__main__":
    main()
