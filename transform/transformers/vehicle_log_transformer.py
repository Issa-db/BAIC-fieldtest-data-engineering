# transform/transformers/vehicle_log_transformer.py

import pandas as pd
from pathlib import Path
from typing import Optional, Dict
from loguru import logger

from transform.date_parser import parse_date
from transform.country_mapper import map_location_to_country


# Column positions in the vehicle log sheet (0-indexed)
# Based on audit of the 3 source files — may need adjustment if new files differ
COL_SEQ      = 0
COL_DATE     = 1
COL_LOCATION = 2
COL_MILEAGE  = 3
COL_ISSUES_TODAY = 4
COL_CUM_ISSUES   = 5
COL_REMARK       = 6


def transform_vehicle_log(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Transform raw vehicle_log landing rows into a clean flat table.
    Input: raw rows from landing zone (all columns named raw_col_N)
    Output: clean DataFrame matching the vehicle_log schema
    """
    records = []

    # Group rows by source file to process each file's block structure
    for source_file, file_df in df_raw.groupby("source_file"):
        file_df = file_df.sort_values("source_row_index").reset_index(drop=True)
        meta = _extract_file_meta(file_df)

        # Walk through rows looking for date-like cells to anchor day blocks
        i = 0
        while i < len(file_df):
            row = file_df.iloc[i]
            raw_date = _get(row, COL_DATE)

            date_val, date_warn = parse_date(raw_date, source_hint=source_file)

            if date_val is not None:
                # This row is a date row — extract the full day block
                location_raw = _get(row, COL_LOCATION)
                mileage_raw  = _get(row, COL_MILEAGE)
                issues_today = _get(row, COL_ISSUES_TODAY)
                cum_issues   = _get(row, COL_CUM_ISSUES)
                remark       = _get(row, COL_REMARK)

                country, country_warn = map_location_to_country(location_raw)

                if date_warn:
                    logger.warning(f"{source_file} row {row.source_row_index}: {date_warn}")
                if country_warn:
                    logger.warning(f"{source_file} row {row.source_row_index}: {country_warn}")

                records.append({
                    "source_file":      source_file,
                    "vehicle_id":       meta.get("vehicle_id"),
                    "driver_name":      meta.get("driver_name"),
                    "phase":            meta.get("phase"),
                    "entry_date":       date_val,
                    "country":          country,
                    "location_raw":     location_raw,
                    "daily_mileage_km": _to_float(mileage_raw),
                    "issues_today":     _to_int(issues_today),
                    "cumulative_issues": _to_int(cum_issues),
                    "remark":           remark,
                    "ingested_at":      meta.get("ingested_at"),
                })
            i += 1

    if not records:
        logger.warning("vehicle_log transform produced zero records")
        return pd.DataFrame()

    df = pd.DataFrame(records)
    df["entry_date"] = pd.to_datetime(df["entry_date"]).dt.date
    return df


def _extract_file_meta(df: pd.DataFrame) -> dict:
    row = df.iloc[0]
    return {
        "vehicle_id":  getattr(row, "vehicle_id", None),
        "driver_name": getattr(row, "driver_name", None),
        "phase":       getattr(row, "phase", None),
        "ingested_at": getattr(row, "ingested_at", None),
    }


def _get(row, col_idx: int):
    col = f"raw_col_{col_idx}"
    val = getattr(row, col, None)
    return None if pd.isna(val) else val


def _to_float(val) -> Optional[float]:
    try:
        f = float(str(val).replace(",", ".").strip())
        return f if f >= 0 else None
    except (TypeError, ValueError):
        return None


def _to_int(val) -> Optional[int]:
    f = _to_float(val)
    return int(f) if f is not None else None