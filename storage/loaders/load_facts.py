from pathlib import Path
import datetime

import pandas as pd
from loguru import logger

from storage.loaders.load_dimensions import (
    upsert_dim_country,
    upsert_dim_driver,
    upsert_dim_vehicle,
)


def _normalize_df_for_duckdb(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    for col in normalized.columns:
        series = normalized[col]
        dtype_name = series.dtype.name

        if pd.api.types.is_categorical_dtype(series.dtype):
            normalized[col] = series.astype("string").astype(object)
            continue

        if dtype_name.startswith("string"):
            normalized[col] = series.astype(object)
            continue

        if pd.api.types.is_object_dtype(series.dtype):
            non_null = series.dropna()
            if not non_null.empty and non_null.map(
                lambda value: isinstance(value, (datetime.date, datetime.datetime))
            ).all():
                normalized[col] = pd.to_datetime(series, errors="coerce")

    return normalized


def _register_dataframe(conn, name: str, df: pd.DataFrame) -> None:
    try:
        conn.register(name, df)
    except Exception:
        conn.register(name, _normalize_df_for_duckdb(df))


def load_vehicle_log(conn, cleaned_dir: Path) -> None:
    path = cleaned_dir / "vehicle_log.parquet"
    if not path.exists():
        logger.warning(f"Not found: {path}")
        return

    df = pd.read_parquet(path)
    upsert_dim_vehicle(conn, df)
    upsert_dim_driver(conn, df)
    upsert_dim_country(conn, df)

    _register_dataframe(conn, "vehicle_log_df", df)
    conn.execute("DELETE FROM fact_vehicle_log")
    conn.execute(
        """
        INSERT INTO fact_vehicle_log
        SELECT
            gen_random_uuid(),
            source_file,
            vehicle_id,
            driver_name AS driver_id,
            entry_date,
            COALESCE(country, 'unknown') AS country_key,
            location_raw,
            daily_mileage_km,
            issues_today,
            cumulative_issues,
            remark,
            NOW()
        FROM vehicle_log_df
        WHERE entry_date IS NOT NULL
    """
    )
    conn.unregister("vehicle_log_df")
    n = conn.execute("SELECT COUNT(*) FROM fact_vehicle_log").fetchone()[0]
    logger.info(f"fact_vehicle_log: {n} rows loaded")


def load_problem_log(conn, cleaned_dir: Path) -> None:
    path = cleaned_dir / "problem_log.parquet"
    if not path.exists():
        logger.warning(f"Not found: {path}")
        return

    df = pd.read_parquet(path)
    upsert_dim_vehicle(conn, df)
    upsert_dim_driver(conn, df)
    upsert_dim_country(conn, df)

    _register_dataframe(conn, "problem_log_df", df)
    conn.execute("DELETE FROM fact_problem_log")
    conn.execute(
        """
        INSERT INTO fact_problem_log
        SELECT
            gen_random_uuid(),
            source_file,
            vehicle_id,
            driver_name AS driver_id,
            event_date,
            event_time,
            car_type,
            vin_partial,
            actual_speed_limit,
            displayed_speed,
            speed_delta,
            COALESCE(country, 'unknown') AS country_key,
            road_type,
            resolution_minutes,
            description_raw,
            NOW()
        FROM problem_log_df
        WHERE event_date IS NOT NULL
    """
    )
    conn.unregister("problem_log_df")
    n = conn.execute("SELECT COUNT(*) FROM fact_problem_log").fetchone()[0]
    logger.info(f"fact_problem_log: {n} rows loaded")


def load_daily_recognition(conn, cleaned_dir: Path) -> None:
    path = cleaned_dir / "daily_recognition.parquet"
    if not path.exists():
        logger.warning(f"Not found: {path}")
        return

    df = pd.read_parquet(path)
    upsert_dim_vehicle(conn, df)
    upsert_dim_driver(conn, df)

    # The recognition sheet has no explicit country column in the cleaned output.
    # We infer country by vehicle_id from loaded vehicle facts where possible.
    if "country" not in df.columns:
        df = df.assign(country=None)
    upsert_dim_country(conn, df)

    _register_dataframe(conn, "daily_recognition_df", df)
    conn.execute("DELETE FROM fact_daily_recognition")
    conn.execute(
        """
        INSERT INTO fact_daily_recognition
        SELECT
            gen_random_uuid(),
            r.source_file,
            r.vehicle_id,
            r.driver_name AS driver_id,
            r.entry_date,
            COALESCE(r.country, vc.country_key, pc.country_key, 'unknown') AS country_key,
            r.segment_no,
            r.block_type,
            r.road_type,
            r.daylight_total_km,
            r.daylight_correct_km,
            r.dark_total_km,
            r.dark_correct_km,
            r.recognition_rate_daylight,
            r.recognition_rate_dark,
            NOW()
        FROM daily_recognition_df r
        LEFT JOIN (
            SELECT vehicle_id, any_value(country_key) AS country_key
            FROM fact_vehicle_log
            GROUP BY 1
        ) vc ON r.vehicle_id = vc.vehicle_id
        LEFT JOIN (
            SELECT vehicle_id, any_value(country_key) AS country_key
            FROM fact_problem_log
            GROUP BY 1
        ) pc ON r.vehicle_id = pc.vehicle_id
        WHERE r.entry_date IS NOT NULL
    """
    )
    conn.unregister("daily_recognition_df")
    n = conn.execute("SELECT COUNT(*) FROM fact_daily_recognition").fetchone()[0]
    logger.info(f"fact_daily_recognition: {n} rows loaded")

