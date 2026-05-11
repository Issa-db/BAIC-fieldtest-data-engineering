from pathlib import Path
from typing import Union

import duckdb

DB_PATH = Path("data/warehouse/isa_pipeline.duckdb")


def get_connection(read_only: bool = False) -> duckdb.DuckDBPyConnection:
    """
    Return a DuckDB connection to the warehouse file.
    Creates parent directories if they do not exist.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(DB_PATH), read_only=read_only)


def execute_sql_file(conn: duckdb.DuckDBPyConnection, path: Union[str, Path]) -> None:
    """Execute a .sql file against the provided connection."""
    sql = Path(path).read_text(encoding="utf-8")
    conn.execute(sql)

