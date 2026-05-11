from pathlib import Path

from loguru import logger

from storage.db import execute_sql_file, get_connection
from storage.loaders.load_dimensions import populate_dim_date
from storage.loaders.load_facts import (
    load_daily_recognition,
    load_problem_log,
    load_vehicle_log,
)
from storage.loaders.load_marts import rebuild_marts

CLEANED_DIR = Path("data/cleaned")
SCHEMA_DIR = Path("storage/schema")
LOG_FILE = Path("logs/storage.log")

LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
logger.add(LOG_FILE, rotation="10 MB", level="INFO")

SCHEMA_FILES = [
    "01_dimensions.sql",
    "02_facts.sql",
]


def run() -> None:
    conn = get_connection()
    logger.info("Connected to DuckDB warehouse")

    # 1. Run schema migrations (dimensions/facts/views first).
    for sql_file in SCHEMA_FILES:
        path = SCHEMA_DIR / sql_file
        execute_sql_file(conn, path)
        logger.info(f"Executed schema file: {sql_file}")

    # Reset facts before rebuilding dimensions to satisfy FK constraints.
    conn.execute("DELETE FROM fact_daily_recognition")
    conn.execute("DELETE FROM fact_problem_log")
    conn.execute("DELETE FROM fact_vehicle_log")

    # 2. Populate date dimension.
    populate_dim_date(conn)

    # 3. Load cleaned Parquet files into fact tables.
    load_vehicle_log(conn, CLEANED_DIR)
    load_problem_log(conn, CLEANED_DIR)
    load_daily_recognition(conn, CLEANED_DIR)

    # 4. Rebuild mart tables from fresh facts.
    rebuild_marts(conn, SCHEMA_DIR)

    # 5. Rebuild views after marts are refreshed.
    execute_sql_file(conn, SCHEMA_DIR / "04_views.sql")
    logger.info("Executed schema file: 04_views.sql")

    conn.close()
    logger.info("Storage run complete")


if __name__ == "__main__":
    run()

