import QueryAzureBlobParquet
import WriteAzureBlob
import duckdb
import time
import asyncio
from datetime import datetime

def main():
    total_start_time = time.time()

    step_start_time = time.time()
    releases = asyncio.run(QueryAzureBlobParquet.query("allraw", "FRED_releases"))
    releases_time = time.time() - step_start_time

    step_start_time = time.time()
    series = asyncio.run(QueryAzureBlobParquet.query("allraw", "FRED_series"))
    series = series.to_pandas(use_threads=True, split_blocks=True, self_destruct=True)
    series["releases_id"] = series['source_file'].str.extract(r'_(\d+)\.parquet').astype(int)
    series_time = time.time() - step_start_time

    step_start_time = time.time()
    observations = asyncio.run(QueryAzureBlobParquet.query("allraw", "FRED_observations"))
    observations = observations.to_pandas(use_threads=True, split_blocks=True, self_destruct=True)
    observations["series_id"] = observations['source_file'].str.extract(r'FRED_observations_(.*?)\.parquet')
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
    FROM releases r
    INNER JOIN series s ON r.id = s.releases_id
    INNER JOIN observations o ON s.id = o.series_id
    '''
    step_start_time = time.time()
    outputPath = './FRED_BigTable.parquet'
    duckdb.query(query).write_parquet(outputPath)
    del releases
    del series
    del observations
    duckdb_time = time.time() - step_start_time

    step_start_time = time.time()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    WriteAzureBlob.writeParquetToBlob("staging", f"{timestamp}/FRED_BigTable/FRED_BigTable_ALL.parquet", outputPath)
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
    output["output"]["executionDuration"] = total_end_time
    return output



if __name__ == "__main__":
    main()
