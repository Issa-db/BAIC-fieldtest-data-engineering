import sys
from pathlib import Path

import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from storage.loaders import load_facts as lf


def test_normalize_string_dtype_for_duckdb():
    df = pd.DataFrame({
        "vehicle_id": pd.Series(["V001", "V002"], dtype="string"),
        "entry_date": [pd.Timestamp("2026-05-01"), pd.Timestamp("2026-05-02")],
    })

    normalized = lf._normalize_df_for_duckdb(df)

    assert normalized["vehicle_id"].dtype == object
    assert pd.api.types.is_datetime64_any_dtype(normalized["entry_date"].dtype)


def test_register_dataframe_falls_back_with_object_types():
    df = pd.DataFrame({
        "driver_name": pd.Series(["Alice", "Bob"], dtype="string"),
        "event_date": [pd.Timestamp("2026-05-01"), pd.Timestamp("2026-05-02")],
    })
    conn = duckdb.connect(database=":memory:")

    lf._register_dataframe(conn, "test_df", df)

    result = conn.execute("SELECT driver_name, event_date FROM test_df ORDER BY driver_name").fetchall()
    assert result == [("Alice", pd.Timestamp("2026-05-01")), ("Bob", pd.Timestamp("2026-05-02"))]
