#!/usr/bin/env python
# coding: utf-8

import click
import pandas as pd
from sqlalchemy import create_engine, URL, text
from tqdm.auto import tqdm

dtype = {
    "VendorID": "Int64",
    "passenger_count": "Int64",
    "trip_distance": "float64",
    "RatecodeID": "Int64",
    "store_and_fwd_flag": "string",
    "PULocationID": "Int64",
    "DOLocationID": "Int64",
    "payment_type": "Int64",
    "fare_amount": "float64",
    "extra": "float64",
    "mta_tax": "float64",
    "tip_amount": "float64",
    "tolls_amount": "float64",
    "improvement_surcharge": "float64",
    "total_amount": "float64",
    "congestion_surcharge": "float64"
}

parse_dates = [
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime"
]


@click.command()
@click.option('--pg-user', default='root', help='PostgreSQL user')
@click.option('--pg-pass', default='root', envvar='PGPASSWORD', help='PostgreSQL password')
@click.option('--pg-host', default='localhost', help='PostgreSQL host')
@click.option('--pg-port', default=5432, type=int, help='PostgreSQL port')
@click.option('--pg-db', default='ny_taxi', help='PostgreSQL database name')
@click.option('--url', default=None, help='Override source with a CSV or CSV.gz URL/path')
@click.option('--year', default=2021, type=int, help='Year of the data')
@click.option('--month', default=1, type=click.IntRange(1, 12), help='Month of the data')
@click.option('--target-table', default='yellow_taxi_data', help='Target table name')
@click.option('--chunksize', default=100000, type=click.IntRange(min=1), help='Chunk size for reading CSV')
def run(pg_user, pg_pass, pg_host, pg_port, pg_db, year, month, target_table, chunksize, url):
    """Ingest NYC taxi data into PostgreSQL database."""
    prefix = 'https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow'
    url = url or f'{prefix}/yellow_tripdata_{year}-{month:02d}.csv.gz'

    engine = create_engine(URL.create('postgresql+psycopg', username=pg_user, password=pg_pass, host=pg_host, port=pg_port, database=pg_db))

    df_iter = pd.read_csv(
        url,
        dtype=dtype,
        parse_dates=parse_dates,
        iterator=True,
        chunksize=chunksize,
    )

    # PostgreSQL rolls back the replacement and all chunks if any chunk fails.
    try:
        with engine.begin() as connection:
            connection.execute(
                text("SELECT pg_advisory_xact_lock(hashtext(:name))"),
                {"name": target_table},
            )
            first = True
            total = 0
            for chunk in tqdm(df_iter):
                chunk.to_sql(
                    target_table, connection,
                    if_exists="replace" if first else "append",
                    index=False, chunksize=1000,
                )
                first = False
                total += len(chunk)
            click.echo(f"Loaded {total:,} rows into {target_table}")
    finally:
        df_iter.close()
        engine.dispose()


if __name__ == '__main__':
    run()

