from datetime import date, timedelta

import pandas as pd
from loguru import logger


def populate_dim_date(conn) -> None:
    """Generate a date dimension from 2000-01-01 to 2100-12-31."""
    conn.execute("DELETE FROM dim_date")

    dates = []
    current = date(2000, 1, 1)
    end = date(2100, 12, 31)
    while current <= end:
        dates.append(
            {
                "date_key": current,
                "year": current.year,
                "month": current.month,
                "week": current.isocalendar()[1],
                "day_of_week": current.weekday(),
                "month_name": current.strftime("%B"),
                "quarter": (current.month - 1) // 3 + 1,
                "is_weekend": current.weekday() >= 5,
            }
        )
        current += timedelta(days=1)

    df = pd.DataFrame(dates)
    conn.register("dim_date_df", df)
    conn.execute("INSERT INTO dim_date SELECT * FROM dim_date_df")
    conn.unregister("dim_date_df")
    logger.info(f"dim_date populated with {len(df)} rows")


def upsert_dim_vehicle(conn, df: pd.DataFrame) -> None:
    if "vehicle_id" not in df.columns:
        return
    vehicles = df[["vehicle_id"]].drop_duplicates().dropna()
    for _, row in vehicles.iterrows():
        conn.execute(
            """
            INSERT OR IGNORE INTO dim_vehicle (vehicle_id) VALUES (?)
            """,
            [row.vehicle_id],
        )


def upsert_dim_driver(conn, df: pd.DataFrame) -> None:
    if "driver_name" not in df.columns:
        return
    phase_col = "phase" if "phase" in df.columns else None
    cols = ["driver_name"] + ([phase_col] if phase_col else [])
    drivers = df[cols].drop_duplicates().dropna(subset=["driver_name"])
    for _, row in drivers.iterrows():
        conn.execute(
            """
            INSERT OR IGNORE INTO dim_driver (driver_id, driver_name, phase)
            VALUES (?, ?, ?)
            """,
            [row.driver_name, row.driver_name, row.get("phase")],
        )


def upsert_dim_country(conn, df: pd.DataFrame) -> None:
    if "country" not in df.columns:
        return
    countries = df[["country"]].drop_duplicates().dropna()
    for _, row in countries.iterrows():
        country = str(row.country).strip()
        if not country:
            continue
        conn.execute(
            """
            INSERT OR IGNORE INTO dim_country (country_key, country, region)
            VALUES (?, ?, 'Europe')
            """,
            [country, country],
        )

