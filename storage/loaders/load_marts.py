from pathlib import Path

from loguru import logger

from storage.db import execute_sql_file


def rebuild_marts(conn, schema_dir: Path) -> None:
    """Drop and recreate mart tables from live fact data."""
    for mart in ["mart_recognition_daily", "mart_problems", "mart_vehicle_daily"]:
        conn.execute(f"DROP TABLE IF EXISTS {mart}")
    execute_sql_file(conn, schema_dir / "03_marts.sql")
    logger.info("Mart tables rebuilt")

