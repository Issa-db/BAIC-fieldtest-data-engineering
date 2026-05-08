# transform/transformers/daily_recognition_transformer.py

import re
import pandas as pd
from typing import Optional
from loguru import logger

from transform.date_parser import parse_date

# Each segment block in the daily sheet spans 8 rows.
# Row structure within each block:
#   0: block header ("TOTAL" or "Segment N")
#   1: D Total row
#   2: D Urban row
#   3: D Interurban row
#   4: D Highway row
#   5–7: (dark / night versions of above, or empty)
BLOCK_SIZE = 8
DAYLIGHT_COLS = {"total_km": 2, "correct_km": 3}
DARK_COLS     = {"total_km": 5, "correct_km": 6}

ROAD_TYPE_PATTERNS = {
    "total":       r'(total|合计|总)',
    "urban":       r'(urban|city|市区)',
    "interurban":  r'(inter|national|国道|省道)',
    "highway":     r'(highway|motorway|高速|autobahn)',
}


def transform_daily_recognition(df_raw: pd.DataFrame) -> pd.DataFrame:
    records = []

    for source_file, file_df in df_raw.groupby("source_file"):
        file_df = file_df.sort_values("source_row_index").reset_index(drop=True)
        meta = _extract_file_meta(file_df)

        for sheet_date_raw, sheet_df in file_df.groupby("sheet_date_raw"):
            sheet_df = sheet_df.reset_index(drop=True)
            entry_date, date_warn = parse_date(
                f"{sheet_date_raw}.2026",
                source_hint=f"{source_file}!{sheet_date_raw}"
            )
            if date_warn:
                logger.warning(date_warn)

            # Walk through the sheet in 8-row blocks
            segment_counter = 0
            i = 0
            while i < len(sheet_df):
                block_rows = sheet_df.iloc[i: i + BLOCK_SIZE]
                if block_rows.empty:
                    break

                header_cell = _get(block_rows.iloc[0], 0) or ""
                is_total    = bool(re.search(r'total|合计|总计', str(header_cell), re.I))
                is_segment  = bool(re.search(r'segment|段|第.段', str(header_cell), re.I))

                if not is_total and not is_segment:
                    i += 1
                    continue

                block_type = "TOTAL" if is_total else "SEGMENT"
                segment_counter = 0 if is_total else segment_counter + 1

                # Parse each road type row within the block
                for j, brow in block_rows.iterrows():
                    road_type = _identify_road_type(_get(brow, 1))
                    if road_type is None:
                        continue

                    day_total   = _to_float(_get(brow, DAYLIGHT_COLS["total_km"]))
                    day_correct = _to_float(_get(brow, DAYLIGHT_COLS["correct_km"]))
                    drk_total   = _to_float(_get(brow, DARK_COLS["total_km"]))
                    drk_correct = _to_float(_get(brow, DARK_COLS["correct_km"]))

                    records.append({
                        "source_file":              source_file,
                        "vehicle_id":               meta.get("vehicle_id"),
                        "driver_name":              meta.get("driver_name"),
                        "entry_date":               entry_date,
                        "segment_no":               segment_counter,
                        "block_type":               block_type,
                        "road_type":                road_type,
                        "daylight_total_km":        day_total,
                        "daylight_correct_km":      day_correct,
                        "dark_total_km":            drk_total,
                        "dark_correct_km":          drk_correct,
                        "recognition_rate_daylight":_safe_rate(day_correct, day_total),
                        "recognition_rate_dark":    _safe_rate(drk_correct, drk_total),
                    })

                i += BLOCK_SIZE

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)
    if "entry_date" in df.columns:
        df["entry_date"] = pd.to_datetime(df["entry_date"]).dt.date
    return df


def _identify_road_type(cell_val) -> Optional[str]:
    if not cell_val:
        return None
    text = str(cell_val).lower()
    for rtype, pattern in ROAD_TYPE_PATTERNS.items():
        if re.search(pattern, text, re.I):
            return rtype
    return None


def _safe_rate(correct, total) -> Optional[float]:
    if correct is None or total is None or total == 0:
        return None
    rate = correct / total
    return round(rate, 4)


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
        return float(str(val).replace(",", ".").strip())
    except (TypeError, ValueError):
        return None