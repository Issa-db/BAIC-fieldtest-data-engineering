import pandas as pd
from loguru import logger


def populate_dim_date(conn) -> None:
    """Generate a date dimension from 2000-01-01 to 2100-12-31."""
    conn.execute("DELETE FROM dim_date")
    conn.execute(
        """
        INSERT INTO dim_date
        SELECT
            d AS date_key,
            EXTRACT(YEAR FROM d)::INTEGER AS year,
            EXTRACT(MONTH FROM d)::INTEGER AS month,
            STRFTIME(d, '%V')::INTEGER AS week,
            (STRFTIME(d, '%u')::INTEGER - 1) AS day_of_week,
            STRFTIME(d, '%B') AS month_name,
            EXTRACT(QUARTER FROM d)::INTEGER AS quarter,
            (STRFTIME(d, '%u')::INTEGER IN (6, 7)) AS is_weekend
        FROM generate_series(
            DATE '2000-01-01',
            DATE '2100-12-31',
            INTERVAL 1 DAY
        ) AS t(d)
        """
    )
    n = conn.execute("SELECT COUNT(*) FROM dim_date").fetchone()[0]
    logger.info(f"dim_date populated with {n} rows")


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

