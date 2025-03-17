import QueryAzureBlobParquet
import duckdb
import time
import asyncio

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
COPY (
SELECT *
FROM releases_df r
INNER JOIN series_df s ON r.id = s.releases_id
INNER JOIN observation_df o ON s.id = o.series_id
)
    TO 'FREDBIGTABLE.parquet'
    (FORMAT PARQUET, COMPRESSION SNAPPY)
'''
step_start_time = time.time()
merged = duckdb.sql(query)
duckdb_time = time.time() - step_start_time

total_end_time = time.time() - total_start_time


print(f"Releases Execution time: {releases_time} seconds")
print(f"Series Execution time: {series_time} seconds")
print(f"Observation Execution time: {observation_time} seconds")
print(f"Duckdb Execution time: {duckdb_time} seconds")
print(f"Total Execution time: {total_end_time} seconds")
