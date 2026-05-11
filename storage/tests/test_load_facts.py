import sys
from pathlib import Path
import datetime

import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from storage.loaders import load_facts as lf


def test_register_dataframe_via_arrow_with_string_dtype():
    """Test that DataFrames with pandas string dtypes can be registered via Arrow."""
    df = pd.DataFrame({
        "vehicle_id": pd.Series(["V001", "V002"], dtype="string"),
        "entry_date": pd.to_datetime(["2026-05-01", "2026-05-02"]),
    })
    conn = duckdb.connect(database=":memory:")

    lf._register_dataframe_via_arrow(conn, "test_df", df)

    result = conn.execute("SELECT vehicle_id, entry_date FROM test_df ORDER BY vehicle_id").fetchall()
    assert len(result) == 2
    assert result[0][0] == "V001"
    assert result[1][0] == "V002"


def test_register_dataframe_via_arrow_with_date_objects():
    """Test that DataFrames with datetime.date objects are handled correctly."""
    df = pd.DataFrame({
        "driver_name": pd.Series(["Alice", "Bob"], dtype="string"),
        "event_date": [datetime.date(2026, 5, 1), datetime.date(2026, 5, 2)],
    })
    conn = duckdb.connect(database=":memory:")

    lf._register_dataframe_via_arrow(conn, "test_df", df)

    result = conn.execute("SELECT driver_name FROM test_df ORDER BY driver_name").fetchall()
    assert result == [("Alice",), ("Bob",)]
