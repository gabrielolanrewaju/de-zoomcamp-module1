# NYC Taxi Data Pipeline

A Data Engineering Zoomcamp Module 1 project for practicing Python, Docker, PostgreSQL, and SQL.

The pipeline reads NYC yellow taxi trip data from a compressed CSV file and loads it into a PostgreSQL database. The data can then be explored with SQL or through pgAdmin in a browser.

## Data flow

```text
NYC taxi CSV.gz → Python and pandas → PostgreSQL → SQL / pgAdmin
```

The ingestion script reads the data in chunks, converts column types, and loads the rows into a table called `yellow_taxi_data`.

## Tools

| Tool | Role |
| --- | --- |
| Python | Runs the ingestion script |
| pandas | Reads and processes tabular data |
| PostgreSQL | Stores the taxi trips |
| SQLAlchemy and psycopg | Connect Python to PostgreSQL |
| Docker | Packages the scripts and their dependencies |
| Docker Compose | Runs the database, pgAdmin, and ingestion service together |
| uv | Installs Python dependencies using the lock file |
| pgAdmin | Provides a browser interface for the database |

## Project files

```text
.
├── pipeline.py          # Introductory exercise that saves sample data as Parquet
├── ingest_data.py       # Loads NYC yellow taxi data into PostgreSQL
├── main.py              # Starter Python greeting
├── Dockerfile           # Builds the Python image
├── docker-compose.yaml  # Configures the database, pgAdmin, and ingestion service
├── pyproject.toml       # Project metadata and dependencies
├── uv.lock              # Locked Python package versions
├── .python-version      # Python version for local development
├── .dockerignore        # Excludes local files from Docker builds
└── .gitignore           # Excludes generated files from Git
```

## Requirements

- Git
- Docker Desktop with Docker Compose
- An internet connection to download images, dependencies, and the dataset

Start Docker Desktop before running the commands below. Python and uv are included in the Docker image.

## Setup

Clone the repository and open the project directory.

```bash
git clone https://github.com/gabrielolanrewajuu/de-zoomcamp-module1.git
cd de-zoomcamp-module1
```

For an existing clone, download the latest changes from the project directory.

```bash
git switch main
git pull --ff-only
```

Run all following commands from the directory containing `docker-compose.yaml`.

## Run the pipeline

### 1. Start PostgreSQL and pgAdmin

```bash
docker compose up -d pgdatabase pgadmin
```

The `-d` flag runs the services in the background. PostgreSQL stores the data, and pgAdmin provides the browser interface.

### 2. Build the ingestion image

```bash
docker compose build ingest
```

Docker installs the dependencies and copies the Python scripts into the image.

### 3. Load January 2021 taxi data

```bash
docker compose run --rm ingest --pg-host pgdatabase --year 2021 --month 1
```

This runs `ingest_data.py` and loads the selected month into the `yellow_taxi_data` table in the `ny_taxi` database. The database hostname is `pgdatabase` inside the Docker network.

The script displays progress and a row count. Wait for the command to finish successfully. Loading a full month can take several minutes.

The `--rm` flag removes the ingestion container after the run. Database data is stored separately in a persistent Docker volume.

### 4. Check the loaded data

```bash
docker compose exec pgdatabase psql -U root -d ny_taxi -c 'SELECT count(*) FROM yellow_taxi_data;'
```

This query returns the number of rows in the table.

To inspect five trips, run the following command.

```bash
docker compose exec pgdatabase psql -U root -d ny_taxi -c 'SELECT * FROM yellow_taxi_data LIMIT 5;'
```

## Explore with pgAdmin

Open [pgAdmin](http://localhost:8080) while the services are running.

Sign in with the local development account.

| Field | Value |
| --- | --- |
| Email | `admin@admin.com` |
| Password | `root` |

Register the PostgreSQL server.

1. Right-click **Servers** and select **Register → Server**.
2. On the **General** tab, enter `NYC Taxi` as the name.
3. On the **Connection** tab, enter the settings below.
4. Save the connection.

| Connection setting | Value |
| --- | --- |
| Host name/address | `pgdatabase` |
| Port | `5432` |
| Maintenance database | `ny_taxi` |
| Username | `root` |
| Password | `root` |

Expand **Databases → ny_taxi → Schemas → public → Tables**. Right-click `yellow_taxi_data` and select **View/Edit Data → First 100 Rows**.

You can also open the Query Tool for `ny_taxi` and run SQL.

```sql
SELECT
    passenger_count,
    COUNT(*) AS trip_count
FROM yellow_taxi_data
GROUP BY passenger_count
ORDER BY passenger_count;
```

This counts trips for each passenger count.

## Load another month

Use `--year` and `--month` to select a month available in the course dataset.

Each run replaces the destination table. To keep months in separate tables, provide a different table name.

```bash
docker compose run --rm ingest \
  --pg-host pgdatabase \
  --year 2021 \
  --month 2 \
  --target-table yellow_taxi_2021_02
```

The script loads all chunks within one database transaction. If a database load fails, the transaction is rolled back. Repeating a successful load replaces the table instead of adding another copy of its rows.

### Ingestion options

| Option | Default | Purpose |
| --- | --- | --- |
| `--year` | `2021` | Dataset year |
| `--month` | `1` | Dataset month, from 1 to 12 |
| `--target-table` | `yellow_taxi_data` | Destination table |
| `--chunksize` | `100000` | Number of rows read per chunk |
| `--url` | Generated from year and month | Compatible yellow taxi CSV/CSV.gz source |
| `--pg-host` | `localhost` | Database host. Use `pgdatabase` inside Compose |
| `--pg-port` | `5432` | Database port |
| `--pg-db` | `ny_taxi` | Database name |
| `--pg-user` | `root` | Database username |
| `--pg-pass` | `root` | Database password, also accepted through `PGPASSWORD` |

View command-line help with the following command.

```bash
docker compose run --rm ingest --help
```

## Introductory Parquet exercise

`pipeline.py` is a small exercise in creating and saving a table. It creates two sample rows, adds a month supplied through the command line, and writes a Parquet file. Parquet is a format for storing tabular data.

Build the image and run the exercise for month 12.

```bash
mkdir -p data
docker build -t cosmic-pipeline:v1 .
docker run --rm \
  -v "$PWD/data:/data" \
  -w /data \
  --entrypoint /code/.venv/bin/python \
  cosmic-pipeline:v1 /code/pipeline.py 12
```

The output is saved to `data/output_12.parquet` on your computer. The volume mapping connects the local `data` folder to the container's `/data` folder.

## Stop and restart

Stop the services with the following command.

```bash
docker compose down
```

The named volumes keep the database and pgAdmin settings. Restart the services with the following command.

```bash
docker compose up -d pgdatabase pgadmin
```

To delete the stored database and pgAdmin settings as well, use `docker compose down -v`.

## Reproducing the setup

The Dockerfile specifies the Python and uv versions. `uv.lock` records exact Python dependency versions, and Docker Compose defines the services, network connections, and storage.

To repeat a run, use the same repository commit, input dataset, year, month, and table settings. Container tags may receive updates, and the remote dataset is not checked against a stored checksum.

## Troubleshooting

| Problem | What to check |
| --- | --- |
| Cannot connect to the Docker daemon | Open Docker Desktop and wait for the engine to start |
| Port is already allocated | Check whether another application uses port 5432 or 8080 |
| pgAdmin cannot connect | Use `pgdatabase` as the server host |
| Dataset download returns an HTTP error | Check that the selected year and month exist at the source |
| Table does not exist | Check the ingestion output for errors and rerun the load |

Check service status and database logs with these commands.

```bash
docker compose ps
docker compose logs pgdatabase
```

## Validation status

Python syntax, command-line help, and Docker Compose configuration checks have passed. A full Docker build and database ingestion run are pending verification.

## Course and dataset

- [Data Engineering Zoomcamp — Module 1](https://github.com/DataTalksClub/data-engineering-zoomcamp/tree/main/01-docker-terraform)
- [NYC taxi data used by the course](https://github.com/DataTalksClub/nyc-tlc-data)
