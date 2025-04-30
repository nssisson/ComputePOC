import QueryAzureBlobParquet
import WriteAzureBlob
import duckdb
import time
import asyncio
from datetime import datetime
import os
import pyarrow.parquet as pq

#@profile
def main():
    total_start_time = time.time()

    step_start_time = time.time()
    releases = asyncio.run(QueryAzureBlobParquet.query("allraw", "FRED_releases"))
    releases_time = time.time() - step_start_time

    step_start_time = time.time()
    series = asyncio.run(QueryAzureBlobParquet.query("allraw", "FRED_series"))
    series_time = time.time() - step_start_time

    step_start_time = time.time()
    observations = asyncio.run(QueryAzureBlobParquet.query("allraw", "FRED_observations"))
    observation_time = time.time() - step_start_time
    
    step_start_time = time.time()
    series_derived = duckdb.sql("SELECT *, regexp_extract(source_file, '_(\d+)\.parquet', 1) as releases_id FROM series")
    observations_derived = duckdb.sql("SELECT *, regexp_extract(source_file, 'FRED_observations_(.*?)\.parquet', 1) as series_id FROM observations")
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
    INNER JOIN series_derived s ON r.id = s.releases_id
    INNER JOIN observations_derived o ON s.id = o.series_id
    '''
    outputPath = './FRED_BigTable.parquet'
    duckdb.query(query).write_parquet(outputPath)
    del releases
    del series
    del observations
    duckdb_time = time.time() - step_start_time

    step_start_time = time.time()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    WriteAzureBlob.writeParquetToBlob("staging", f"{timestamp}/FRED_BigTable/FRED_BigTable.parquet", outputPath)
    row_count = pq.ParquetFile(outputPath).metadata.num_rows
    #os.remove(outputPath)
    blobwrite_time = time.time() - step_start_time



    total_end_time = time.time() - total_start_time


    print(f"Releases Execution time: {releases_time} seconds")
    print(f"Series Execution time: {series_time} seconds")
    print(f"Observation Execution time: {observation_time} seconds")
    print(f"Duckdb Execution time: {duckdb_time} seconds")
    print(f"BlobWrite Execution time: {blobwrite_time} seconds")
    print(f"Total Execution time: {total_end_time} seconds")
    print(f"Total Records Written: {row_count} records written")


    output = {}
    output["status"] = 'success'
    output["output"] = {}
    output["output"]["executionDuration"] = total_end_time
    output["output"]["rowCount"] = row_count
    return output



if __name__ == "__main__":
    main()
