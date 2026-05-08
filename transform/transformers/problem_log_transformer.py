# transform/transformers/problem_log_transformer.py

import pandas as pd
from typing import Optional, List
from loguru import logger

from transform.date_parser import parse_date, parse_time
from transform.speed_parser import parse_speed_event
from transform.country_mapper import map_location_to_country

# Column positions in problem log — these may shift between files
# The transformer tries multiple positions and uses the first that yields data
DATE_COLS     = [1, 2]
TIME_COLS     = [2, 3]
CAR_TYPE_COL  = 4
VIN_COL       = 5
SPEED_COL     = 6   # "speed 30 / speedometer 80" string
COUNTRY_COL   = 8
ROAD_TYPE_COL = 9
RESOLUTION_COL= 10

ROAD_TYPE_MAP = {
    "urban": "urban", "city": "urban", "市区": "urban",
    "inter": "interurban", "国道": "interurban", "provincial": "interurban",
    "highway": "highway", "motorway": "highway", "高速": "highway",
    "autobahn": "highway",
}


def transform_problem_log(df_raw: pd.DataFrame) -> pd.DataFrame:
    records = []

    for source_file, file_df in df_raw.groupby("source_file"):
        file_df = file_df.sort_values("source_row_index").reset_index(drop=True)
        meta = _extract_file_meta(file_df)

        for _, row in file_df.iterrows():
            # Skip header rows — identified by having non-numeric date cell
            raw_date = _first_valid(row, DATE_COLS)
            date_val, date_warn = parse_date(raw_date, source_hint=source_file)

            if date_val is None:
                continue  # header row or empty row

            raw_time = _first_valid(row, TIME_COLS)
            time_val, time_warn = parse_time(raw_time)

            raw_speed = _get(row, SPEED_COL)
            actual_spd, display_spd, speed_warn = parse_speed_event(raw_speed)

            raw_country = _get(row, COUNTRY_COL)
            country, country_warn = map_location_to_country(raw_country)

            raw_road = _get(row, ROAD_TYPE_COL)
            road_type = _map_road_type(raw_road)

            for w in [date_warn, time_warn, speed_warn, country_warn]:
                if w:
                    logger.warning(f"{source_file} row {getattr(row, 'source_row_index', '?')}: {w}")

            records.append({
                "source_file":        source_file,
                "vehicle_id":         meta.get("vehicle_id"),
                "driver_name":        meta.get("driver_name"),
                "event_date":         date_val,
                "event_time":         time_val,
                "car_type":           _get(row, CAR_TYPE_COL),
                "vin_partial":        _get(row, VIN_COL),
                "actual_speed_limit": actual_spd,
                "displayed_speed":    display_spd,
                "speed_delta":        (display_spd - actual_spd)
                                      if actual_spd and display_spd else None,
                "country":            country,
                "road_type":          road_type,
                "resolution_minutes": _to_float(_get(row, RESOLUTION_COL)),
                "description_raw":    str(raw_speed) if raw_speed else None,
            })

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)
    df["event_date"] = pd.to_datetime(df["event_date"]).dt.date
    return df


def _map_road_type(raw) -> str:
    if not raw:
        return "unknown"
    text = str(raw).lower()
    for key, val in ROAD_TYPE_MAP.items():
        if key in text:
            return val
    return "unknown"


def _first_valid(row, cols: List[int]):
    for c in cols:
        val = _get(row, c)
        if val is not None:
            return val
    return None


def _extract_file_meta(df: pd.DataFrame) -> dict:
    row = df.iloc[0]
    return {k: getattr(row, k, None) for k in ["vehicle_id", "driver_name", "phase", "ingested_at"]}


def _get(row, col_idx: int):
    col = f"raw_col_{col_idx}"
    try:
        val = row[col]
        return None if pd.isna(val) else val
    except (KeyError, TypeError):
        return None


def _to_float(val) -> Optional[float]:
    try:
        return float(str(val).strip())
    except (TypeError, ValueError):
        return None