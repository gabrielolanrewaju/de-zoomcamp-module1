Data Pipeline: From Local Script to Portable Container

This project demonstrates the transition of a Python data pipeline from a local, hardware-dependent environment to a fully containerized Docker solution, ensuring 100% reproducibility across any machine.

(Setting the Scene)
Before diving into infrastructure, we need a baseline. This project uses Python 3.13 and Pandas to process monthly data.

Environment: VS Code on macOS (M4 Apple Silicon).

Language: Python.

The Goal: Build a pipeline that takes a month argument and spits out a processed .parquet file.

The Problem 
Running code locally is "brittle." If I send you my script, it might fail because you have the wrong version of Pandas or a different OS.

In Data Engineering, "it works on my machine" is a failure. Manually installing dependencies (pip install ...) leads to "Version Drift," where the pipeline eventually breaks as libraries update.

Solution: Docker (The Portable Workshop)
Think of Docker not just as a virtual machine, but as a Construction Company for your code.

What: It builds an isolated, "Slim" Linux workshop (a Container) inside your computer.

Why: 
1. Safety: It keeps your main Mac OS clean (no global pip installs).
2. Reproducibility: It freezes the exact versions of the "tools" (Python, Pandas, PyArrow) inside the workshop so the code runs the same in 2026 as it does today.

The "How" (The Technical Roadmap)
To get this running, we follow a three-step workflow:

Step A: The Blueprint (Dockerfile)
We don't just "install" things manually. We write a Dockerfile—a recipe that tells Docker how to build the room.

We use the python:3.13.11-slim image for speed.

We use uv (a high-performance package manager) to lock our dependencies.

Step B: The Build (Baking the Image)
We turn the blueprint into a frozen image.

Bash
docker build -t cosmic-pipeline:v1 .

Step C: The Execution (Running the Container)
We walk into the workshop and run the pipeline for a specific month (e.g., Month 12).

Bash
docker run -it --rm cosmic-pipeline:v1 12


Data Persistence Problem; Using 'Volumes' to establish stateless data
## Complete NYC taxi ingestion

The next stage follows the [Module 1 guide](https://github.com/DataTalksClub/data-engineering-zoomcamp/tree/main/01-docker-terraform).
Python 3.13, uv, and Docker with Compose are required. Start Docker Desktop first.

### Run PostgreSQL and pgAdmin

```bash
docker compose up -d pgdatabase pgadmin
docker compose build ingest
docker compose run --rm ingest --pg-host pgdatabase --year 2021 --month 1
```

The default source is the course's January 2021 yellow taxi CSV.gz.
The loader reads 100,000 rows per chunk, parses pickup/dropoff timestamps,
and writes to `yellow_taxi_data` without an extra DataFrame index column.
Each run replaces the target table inside one transaction. Reruns do not
duplicate rows, and failures roll back the entire replacement. Use a distinct
`--target-table` per month to retain multiple months. Concurrent loads to the
same table are serialized.

### Run ingestion locally

```bash
uv sync --locked
uv run python ingest_data.py --year 2021 --month 1 --pg-host localhost
uv run python ingest_data.py --help
```

Options include `--pg-user`, `--pg-pass`, `--pg-port`, `--pg-db`,
`--target-table`, `--chunksize`, and `--url` for another compatible yellow
taxi CSV/CSV.gz URL or local file. The password can also come from `PGPASSWORD`.

### Query and inspect

```bash
docker compose exec pgdatabase psql -U root -d ny_taxi -c 'SELECT count(*) FROM yellow_taxi_data;'
docker compose exec pgdatabase psql -U root -d ny_taxi -c 'SELECT min(tpep_pickup_datetime), max(tpep_pickup_datetime) FROM yellow_taxi_data;'
```

Open http://localhost:8080 and sign in with `admin@admin.com` / `root`.
Register a server with host `pgdatabase`, port `5432`, database `ny_taxi`,
user `root`, and password `root`. These credentials are for the local course setup.

### Persist the original Parquet output

```bash
mkdir -p data
docker build -t cosmic-pipeline:v1 .
docker run --rm -v "$PWD/data:/data" -w /data --entrypoint /code/.venv/bin/python cosmic-pipeline:v1 /code/pipeline.py 12
```

This writes `data/output_12.parquet` on your machine.

### Stop services

```bash
docker compose down
```

Named volumes retain the database and pgAdmin settings. To intentionally erase
both, run `docker compose down -v`.
