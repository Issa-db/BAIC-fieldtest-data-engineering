# transform/transformers/daily_recognition_transformer.py

import re
import pandas as pd
from typing import Optional, List
from loguru import logger

from transform.date_parser import parse_date

RAW_COLS = [f"raw_col_{i}" for i in range(12)]

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

            segment_counter = 0
            current_block_type = None
            current_segment_no = 0

            for _, row in sheet_df.iterrows():
                header_text = _header_text(row)
                block_type = _identify_block_type(header_text)
                if block_type:
                    current_block_type = block_type
                    if block_type == "TOTAL":
                        current_segment_no = 0
                    else:
                        parsed_no = _extract_segment_number(header_text)
                        if parsed_no is not None:
                            current_segment_no = parsed_no
                            segment_counter = max(segment_counter, parsed_no)
                        else:
                            segment_counter += 1
                            current_segment_no = segment_counter

                if current_block_type is None:
                    continue

                road_type = _identify_road_type(_row_text(row))
                if road_type is None:
                    continue

                metrics = _extract_numeric_metrics(row)
                day_total, day_correct, drk_total, drk_correct = _normalize_metrics(metrics)
                if all(v is None for v in [day_total, day_correct, drk_total, drk_correct]):
                    continue

                records.append(
                    {
                        "source_file": source_file,
                        "vehicle_id": meta.get("vehicle_id"),
                        "driver_name": meta.get("driver_name"),
                        "entry_date": entry_date,
                        "segment_no": current_segment_no,
                        "block_type": current_block_type,
                        "road_type": road_type,
                        "daylight_total_km": day_total,
                        "daylight_correct_km": day_correct,
                        "dark_total_km": drk_total,
                        "dark_correct_km": drk_correct,
                        "recognition_rate_daylight": _safe_rate(day_correct, day_total),
                        "recognition_rate_dark": _safe_rate(drk_correct, drk_total),
                    }
                )

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


def _identify_block_type(text: str) -> Optional[str]:
    if not text:
        return None
    lowered = text.lower()
    if re.search(r"\bsegment\b|第.{0,2}段|段", lowered, re.I):
        return "SEGMENT"
    if re.search(r"\btotal\b|合计|总计", lowered, re.I):
        return "TOTAL"
    return None


def _extract_segment_number(text: str) -> Optional[int]:
    if not text:
        return None
    m = re.search(r"segment\s*(\d+)", text, re.I)
    if m:
        return int(m.group(1))
    return None


def _row_text(row) -> str:
    values: List[str] = []
    for col in RAW_COLS:
        val = row.get(col) if isinstance(row, pd.Series) else getattr(row, col, None)
        if val is None or pd.isna(val):
            continue
        values.append(str(val))
    return " ".join(values)


def _header_text(row) -> str:
    # Headers are usually present in left-side columns or the "raw_col_2" lane.
    candidates = [_get(row, 0), _get(row, 1), _get(row, 2)]
    return " ".join(str(v) for v in candidates if v is not None)


def _extract_numeric_metrics(row) -> List[float]:
    metrics = []
    for col in RAW_COLS:
        v = row.get(col) if isinstance(row, pd.Series) else getattr(row, col, None)
        num = _to_float(v)
        if num is not None:
            metrics.append(num)
    return metrics


def _normalize_metrics(metrics: List[float]):
    # Supports multiple sheet layouts:
    # - [day_total, day_correct, dark_total, dark_correct]
    # - [day_total, day_correct]
    # - [day_total]
    if not metrics:
        return None, None, None, None
    if len(metrics) >= 4:
        return metrics[0], metrics[1], metrics[2], metrics[3]
    if len(metrics) == 3:
        return metrics[0], metrics[1], metrics[2], None
    if len(metrics) == 2:
        return metrics[0], metrics[1], None, None
    return metrics[0], None, None, None


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