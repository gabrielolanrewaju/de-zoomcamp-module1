# NYC taxi pipeline

A data pipeline is a program that reads data, does some processing, and writes the result somewhere useful.

There are two exercises here.

- `pipeline.py` creates two example rows, adds a month, and saves a Parquet file.
- `ingest_data.py` reads real NYC yellow taxi trips from a compressed CSV file and loads them into PostgreSQL.

PostgreSQL stores tables that you can ask questions about using SQL. pgAdmin is a browser interface for viewing that database. GitHub stores the source code. You run the programs on your computer using Docker.

## What existed and what was added

Originally, the repository had the two-row Parquet exercise, a Dockerfile, Python dependency files, a starter `main.py`, and an introductory README.

The completed ingestion stage adds `ingest_data.py`, `docker-compose.yaml`, and `.dockerignore`. The Dockerfile and dependency files were updated to support ingestion. The original `pipeline.py` remains the introductory exercise. `main.py` only prints a greeting and is unused by the Docker workflows.

The implemented scope is the local Docker/PostgreSQL ingestion stage. Terraform cloud infrastructure and taxi-zone lookup joins are further course topics.

## Start here on your Mac

Install Git and Docker Desktop if needed. Open Docker Desktop and wait until its engine is running. Docker includes Compose. For the Docker instructions below, Python and uv are installed inside the image.

Open Terminal. These commands download the project into a new folder and enter that folder.

```bash
git clone https://github.com/gabrielolanrewajuu/de-zoomcamp-module1.git
cd de-zoomcamp-module1
```

If you already have a clone, open Terminal in that existing folder and update it.

```bash
git switch main
git pull --ff-only
```

Run the remaining commands from the folder containing `docker-compose.yaml`.

### 1. Start the database and browser interface

```bash
docker compose up -d pgdatabase pgadmin
```

`docker compose` reads the YAML configuration. `up` creates and starts the named services. `-d` keeps them running in the background. The first run downloads their images.

An image is a packaged filesystem and program configuration. A container is a running instance of an image.

### 2. Build the Python program's image

```bash
docker compose build ingest
```

This follows the Dockerfile to install Python dependencies and copy the scripts into an image. You should see a successful build before continuing.

### 3. Load one month of taxi trips

```bash
docker compose run --rm ingest --pg-host pgdatabase --year 2021 --month 1
```

`run` starts a one-off container for the ingest service. `--rm` removes that container after it exits. The remaining options are passed to the Python script.

`--pg-host pgdatabase` identifies the database service on Compose's internal network. `--year 2021 --month 1` selects January 2021. The script reads the course's yellow taxi CSV.gz source and writes a table called `yellow_taxi_data` in the `ny_taxi` database.

Successful completion prints `Loaded ... rows into yellow_taxi_data`. The row count depends on the input file. Downloading and inserting the full month may take several minutes.

Every run replaces the target table. To keep another month alongside January, choose a different table.

```bash
docker compose run --rm ingest --pg-host pgdatabase --year 2021 --month 2 --target-table yellow_taxi_2021_02
```

### 4. Check your result

```bash
docker compose exec pgdatabase psql -U root -d ny_taxi -c 'SELECT count(*) FROM yellow_taxi_data;'
```

`exec` runs a command in the existing database container. `psql` is PostgreSQL's terminal client. `-U root` chooses the user, `-d ny_taxi` chooses the database, and `-c` supplies SQL.

`SELECT count(*) FROM yellow_taxi_data;` asks how many rows the table contains.

### 5. View the data in your browser

Open http://localhost:8080 while the services are running.

1. Sign in with email `admin@admin.com` and password `root`.
2. Right-click Servers and choose Register → Server.
3. In General, give it a name such as Local taxi database.
4. In Connection, set Host to `pgdatabase`, Port to `5432`, Maintenance database to `ny_taxi`, Username to `root`, and Password to `root`.
5. Save. Expand Databases → ny_taxi → Schemas → public → Tables.
6. Right-click `yellow_taxi_data` and choose View/Edit Data → First 100 Rows.

The browser connects to pgAdmin on your Mac through port 8080. pgAdmin connects to PostgreSQL through the internal service name `pgdatabase`. The credentials above are the local learning defaults in the Compose file.

### 6. Stop the services

```bash
docker compose down
```

The database is stored in a named Docker volume, so it survives this shutdown. Start the services again to access it.

`docker compose down -v` intentionally deletes the named volumes and their saved database/settings.

## Your original Python exercise, line by line

Python runs statements from top to bottom. Indentation groups statements, much as braces do in C++. Variables do not require a written type declaration.

```python
import sys
```

Load Python's built-in system module so the program can read command-line arguments.

```python
# print("arguments", sys.argv)
```

A line starting with `#` is a comment. Removing `#` would print the arguments for debugging.

```python
month = int(sys.argv[1])
```

`sys.argv` is a list of command-line strings. Index 0 holds the script name. Index 1 holds the first supplied argument, such as `"12"`. `int` converts that string into the integer 12. Omitting the argument or supplying a non-integer causes an error in this introductory script.

```python
print(f"Running pipeline for month {month}")
```

`print` displays text. The `f` prefix allows expressions inside braces to be inserted into a string.

```python
import pandas as pd
```

Load pandas, a library for working with tables. `pd` is the short alias used in this file.

```python
df = pd.DataFrame({'day': [1, 2], 'num_passenger': [14, 7]})
```

A dictionary maps column names to lists of values. A DataFrame turns those columns into a table. Row one has day 1 and 14 passengers. Row two has day 2 and 7 passengers. These are invented example values.

```python
df['month'] = month
```

Add a column called month and give every row the selected month.

```python
print(df.head())
```

Display the first five rows, or all rows when there are fewer than five.

```python
df.to_parquet(f'output_{month}.parquet')
```

Write the table to a Parquet file in the current working directory. Parquet is a binary table format designed for efficient storage and analytical reading.

### Run the exercise and keep its output

```bash
mkdir -p data
docker build -t cosmic-pipeline:v1 .
docker run --rm -v "$PWD/data:/data" -w /data --entrypoint /code/.venv/bin/python cosmic-pipeline:v1 /code/pipeline.py 12
```

`mkdir -p data` creates an output directory. `docker build` builds the image, `-t` names it, and `.` supplies the current directory as build input.

The run command attaches your local data directory to `/data` inside the container. `$PWD` means your current terminal directory. `-w /data` makes that the working directory. `--entrypoint` selects the installed Python executable, followed by the script path and its month argument.

The resulting file is `data/output_12.parquet` on your Mac.

## The real ingestion script, statement by statement

Open [ingest_data.py](ingest_data.py) alongside this section.

- `#!/usr/bin/env python` tells a Unix system which interpreter to use when launching an executable script directly.
- `# coding: utf-8` declares the text encoding.
- `import click` loads a library that turns terminal options into function arguments.
- `import pandas as pd` loads the table-processing library.
- `from sqlalchemy import create_engine, URL, text` imports connection creation, safe connection URL construction, and SQL statement wrapping.
- `from tqdm.auto import tqdm` imports a progress display for the loop.

### Column types

`dtype = {...}` creates a dictionary of expected column types. Each line maps a CSV header to a type.

| Columns | Type | Meaning |
| --- | --- | --- |
| VendorID, RatecodeID, PULocationID, DOLocationID, payment_type | Int64 | Integer identifiers/codes with missing values allowed |
| passenger_count | Int64 | Integer passenger count with missing values allowed |
| trip_distance | float64 | Decimal distance |
| store_and_fwd_flag | string | Text flag |
| fare_amount, extra, mta_tax, tip_amount, tolls_amount, improvement_surcharge, total_amount, congestion_surcharge | float64 | Decimal money amounts |

`parse_dates = [...]` is a list of the pickup and dropoff column names. pandas is asked to parse those text fields as date/time values.

### Terminal options and the function

`@click.command()` makes the following function a command-line command. Each `@click.option(...)` defines an accepted named option. These lines are decorators, which configure the function defined below them.

| Option | Default | Purpose |
| --- | --- | --- |
| --pg-user | root | Database username |
| --pg-pass | root | Database password, also read from PGPASSWORD |
| --pg-host | localhost | Database hostname |
| --pg-port | 5432 | Database connection port |
| --pg-db | ny_taxi | Database name |
| --url | None | Optional compatible CSV/CSV.gz URL or file path |
| --year | 2021 | Source year |
| --month | 1 | Source month, validated from 1 through 12 |
| --target-table | yellow_taxi_data | Destination table |
| --chunksize | 100000 | Rows per pandas chunk, validated as positive |

`None` means no value was supplied. `default=` supplies a fallback, `help=` supplies help text, and `type=` selects conversion or validation.

`def run(...):` defines a function. Its parameters receive the values selected by Click. The indented lines belong to that function. The triple-quoted sentence is its documentation string.

`prefix = ...` stores the course data's base URL.

`url = url or f'...'` uses an explicitly supplied URL when present, otherwise constructs one from the year and month. `{month:02d}` formats an integer with at least two digits, so January becomes `01`.

`engine = create_engine(URL.create(...))` prepares a database connection manager. `postgresql+psycopg` selects PostgreSQL and its Python driver. Named arguments supply the connection details. Building the URL this way handles special characters in passwords.

`df_iter = pd.read_csv(...)` prepares CSV reading with the specified column types, date fields, and chunk size. `iterator=True` allows the loop to request successive chunks. Chunking limits the table rows processed at once, although URL downloading may buffer data depending on the reader.

### Loading and cleanup

`try:` begins a block whose cleanup is handled by `finally`.

`with engine.begin() as connection:` opens a database transaction. Successful exit commits the changes. An exception rolls them back. A transaction groups writes so a failed load does not leave a half-replaced table.

`connection.execute(text(...), {"name": target_table})` requests a PostgreSQL advisory lock associated with the target name. Other runs of this loader using the same name wait for it. The `:name` SQL parameter receives a value separately from the SQL text. PostgreSQL releases this transaction lock when the transaction ends.

`first = True` remembers that no chunk has been written. `total = 0` initializes the row counter.

`for chunk in tqdm(df_iter):` reads successive DataFrames and displays progress. A Python `for` loop assigns each next item to the variable `chunk`.

`chunk.to_sql(...)` writes that DataFrame using the active database connection.

- `target_table` supplies the destination name.
- `if_exists="replace" if first else "append"` replaces the table for the first chunk, then adds subsequent chunks.
- `index=False` excludes pandas' row index from the database.
- `chunksize=1000` batches database inserts separately from the 100,000-row CSV reading chunks.

`first = False` makes later iterations append.

`total += len(chunk)` adds the current chunk's row count to the total. This is equivalent to `total = total + len(chunk)`.

`click.echo(f"Loaded {total:,} rows into {target_table}")` prints the count with thousands separators. It executes just before the transaction block exits and commits. A later commit error still means the run failed.

`finally:` runs cleanup even if loading raised an error. `df_iter.close()` closes the CSV reader. `engine.dispose()` releases pooled database connections.

`if __name__ == '__main__':` checks whether Python is running this file directly. `run()` then starts the Click command. Importing this file from another script does not automatically execute the loader.

## The Dockerfile, line by line

| Statement | Meaning |
| --- | --- |
| FROM python:3.13.11-slim | Start from an image containing Python 3.13.11 and a compact Linux environment |
| COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /bin/ | Copy the uv dependency manager from its versioned image |
| WORKDIR /code | Set the container's working directory |
| ENV PATH="/code/.venv/bin:$PATH" | Make commands find the project's installed Python environment first |
| COPY pyproject.toml .python-version uv.lock ./ | Copy dependency declarations, Python preference, and locked versions |
| RUN uv sync --locked --no-dev | Install the locked application dependencies and fail if the project and lock disagree |
| COPY pipeline.py ingest_data.py ./ | Copy both scripts into the image |
| ENTRYPOINT ["python", "pipeline.py"] | Run the introductory script by default |

Compose overrides that final entrypoint for the ingest service, so its command runs `ingest_data.py`.

## The Compose file, line by line

YAML uses indentation to group settings. Open [docker-compose.yaml](docker-compose.yaml) alongside this explanation.

- `services:` begins the programs Compose manages.
- `pgdatabase:` names the PostgreSQL service and its network hostname.
- `image: postgres:17` selects a PostgreSQL image.
- Its `environment:` block provides the initial username, password, and database name.
- `ports:` with `127.0.0.1:5432:5432` connects port 5432 on your Mac's loopback interface to port 5432 inside the container.
- Its `volumes:` entry stores PostgreSQL data in `postgres_data` at the image's expected data directory.
- `healthcheck:` describes how to check readiness.
- `test: ["CMD-SHELL", "pg_isready -U root -d ny_taxi"]` runs PostgreSQL's readiness command.
- `interval: 5s` repeats the check every five seconds. `timeout: 5s` limits each check. `retries: 20` sets the failed-check threshold.
- `pgadmin:` names the browser administration service.
- `image: dpage/pgadmin4:9` selects its image.
- Its environment variables set the initial browser login.
- `127.0.0.1:8080:80` connects your browser's port 8080 to pgAdmin's container port 80.
- `pgadmin_data:/var/lib/pgadmin` persists its settings.
- `ingest:` names the Python loading service.
- `build: .` builds its image from the current directory's Dockerfile.
- `profiles: ["ingest"]` keeps it out of a normal service startup unless selected. The explicit `run ingest` command selects it.
- `entrypoint: ["python", "ingest_data.py"]` selects the real data loader.
- `PGPASSWORD: root` passes the database password to that loader.
- `command: ["--pg-host", "pgdatabase"]` supplies default script arguments. Arguments after `run ingest` replace this list, which is why the examples repeat the hostname.
- `depends_on:` with `condition: service_healthy` waits for database readiness before starting ingestion.
- The final top-level `volumes:` block declares the two persistent volumes.

## Other project files

| File | Purpose |
| --- | --- |
| pyproject.toml | Project metadata, supported Python range, and direct library requirements |
| uv.lock | Exact resolved Python package versions, download locations, and hashes |
| .python-version | Python version preference for local uv commands |
| .dockerignore | Files excluded from Docker's build input |
| .gitignore | Files Git should ignore when adding new files |
| main.py | Starter greeting function, followed by a direct-execution check and function call |
| .DS_Store | macOS folder metadata, unused by the pipeline |

## How reproducible is it?

Another person can clone the same commit, build the image, start the same service configuration, and invoke the same script with the same source month.

The lock file fixes Python dependency versions. The Dockerfile specifies Python and uv versions. Compose records service names, ports, storage, and startup dependencies. The README records the commands.

This supports repeatable setup. Exact identical results also depend on identical input data and the execution environment. Container tags can change, PostgreSQL and pgAdmin tags allow updates, and the remote CSV is not verified against a saved checksum. The previous README's claim of 100% reproducibility across any machine was too strong.

## Verification status and troubleshooting

Python compilation, command-line help, and Compose configuration checks passed during implementation. A full Docker image build and real PostgreSQL ingestion have not yet been verified because the Docker daemon was stopped.

- If Docker says it cannot connect to the daemon, open Docker Desktop and wait for readiness.
- If a port is already allocated, stop the other service using it or change the host-side port in Compose.
- If pgAdmin cannot reach PostgreSQL, use host `pgdatabase` in its connection settings.
- If you see an HTTP error, confirm the selected year/month exists at the course source.
- If a table does not exist, inspect the ingestion output for a failure and rerun the load.
- To inspect service status, run `docker compose ps`.
- To inspect database logs, run `docker compose logs pgdatabase`.

For an optional local Python workflow, install Python 3.13 and uv, start the database with Compose, then run `uv sync --locked` and `uv run python ingest_data.py --pg-host localhost --year 2021 --month 1`.
