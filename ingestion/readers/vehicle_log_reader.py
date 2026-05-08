import pandas as pd
from pathlib import Path
from typing import Any, Union, List, Dict


def read_vehicle_log(
    filepath: Union[str, Path],
    sheet_name: str,
    file_metadata: dict,
) -> List[Dict]:
    df = pd.read_excel(filepath, sheet_name=sheet_name, header=None)
    rows: List[Dict] = []

    for i in range(len(df)):
        row = df.iloc[i]
        raw = {
            "source_file": Path(filepath).name,
            "source_sheet": sheet_name,
            "source_row_index": int(i),
            "raw_col_0": _safe(row, 0),
            "raw_col_1": _safe(row, 1),
            "raw_col_2": _safe(row, 2),
            "raw_col_3": _safe(row, 3),
            "raw_col_4": _safe(row, 4),
            "raw_col_5": _safe(row, 5),
            "raw_col_6": _safe(row, 6),
            "raw_col_7": _safe(row, 7),
            **file_metadata,
        }
        rows.append(raw)

    return rows


def _safe(row: pd.Series, idx: int) -> Any:
    try:
        val = row.iloc[idx]
        return None if pd.isna(val) else str(val)
    except (IndexError, TypeError):
        return None
