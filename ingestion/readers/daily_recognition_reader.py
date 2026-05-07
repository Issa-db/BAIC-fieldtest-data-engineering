import pandas as pd
from pathlib import Path
from typing import Union


def read_daily_recognition(
    filepath: Union[str, Path],
    sheet_name: str,
    file_metadata: dict,
) -> list[dict]:
    df = pd.read_excel(filepath, sheet_name=sheet_name, header=None)

    if df.empty:
        return []

    rows: list[dict] = []
    for i, row in df.iterrows():
        raw = {
            "source_file": Path(filepath).name,
            "source_sheet": sheet_name,
            "source_row_index": int(i),
            "sheet_date_raw": sheet_name,
            **file_metadata,
        }
        for j in range(len(row)):
            val = row.iloc[j]
            raw[f"raw_col_{j}"] = None if pd.isna(val) else val
        rows.append(raw)

    return rows
