from pathlib import Path

import pandas as pd

from transform import run_transform as rt


def test_run_transform_writes_all_phase2_outputs(tmp_path, monkeypatch):
    landing_dir = tmp_path / "landing"
    cleaned_dir = tmp_path / "cleaned"
    log_file = tmp_path / "logs" / "transform.log"

    for folder in ["vehicle_log", "problem_log", "daily_recognition"]:
        (landing_dir / folder).mkdir(parents=True, exist_ok=True)
    cleaned_dir.mkdir(parents=True, exist_ok=True)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(rt, "LANDING_DIR", landing_dir)
    monkeypatch.setattr(rt, "CLEANED_DIR", cleaned_dir)
    monkeypatch.setattr(rt, "LOG_FILE", log_file)

    common = {
        "source_file": "unit_sample.xlsx",
        "vehicle_id": "V001",
        "driver_name": "Tester",
        "phase": "phase2",
        "ingested_at": "2026-05-08T10:00:00",
    }

    pd.DataFrame(
        [
            {
                **common,
                "source_row_index": 1,
                "raw_col_1": "03/28/2026",
                "raw_col_2": "Berlin",
                "raw_col_3": "120",
                "raw_col_4": "2",
                "raw_col_5": "10",
                "raw_col_6": "normal",
            }
        ]
    ).to_parquet(landing_dir / "vehicle_log" / "unit_sample.parquet", index=False)

    pd.DataFrame(
        [
            {
                **common,
                "source_row_index": 1,
                "raw_col_1": "03/28/2026",
                "raw_col_2": "08:30",
                "raw_col_4": "SUV",
                "raw_col_5": "VIN123",
                "raw_col_6": "speed 30 / speedometer 50",
                "raw_col_8": "Berlin",
                "raw_col_9": "urban",
                "raw_col_10": "5",
            }
        ]
    ).to_parquet(landing_dir / "problem_log" / "unit_sample.parquet", index=False)

    daily_rows = [
        {**common, "sheet_date_raw": "28.03", "source_row_index": 1, "raw_col_0": "TOTAL", "raw_col_1": None},
        {**common, "sheet_date_raw": "28.03", "source_row_index": 2, "raw_col_1": "Total", "raw_col_2": 100, "raw_col_3": 95, "raw_col_5": 50, "raw_col_6": 45},
        {**common, "sheet_date_raw": "28.03", "source_row_index": 3, "raw_col_1": "Urban", "raw_col_2": 30, "raw_col_3": 29, "raw_col_5": 10, "raw_col_6": 9},
        {**common, "sheet_date_raw": "28.03", "source_row_index": 4, "raw_col_1": "Inter", "raw_col_2": 20, "raw_col_3": 18, "raw_col_5": 5, "raw_col_6": 4},
        {**common, "sheet_date_raw": "28.03", "source_row_index": 5, "raw_col_1": "Highway", "raw_col_2": 50, "raw_col_3": 48, "raw_col_5": 35, "raw_col_6": 32},
        {**common, "sheet_date_raw": "28.03", "source_row_index": 6},
        {**common, "sheet_date_raw": "28.03", "source_row_index": 7},
        {**common, "sheet_date_raw": "28.03", "source_row_index": 8},
    ]
    pd.DataFrame(daily_rows).to_parquet(landing_dir / "daily_recognition" / "unit_sample.parquet", index=False)

    rt.run()

    vehicle_out = cleaned_dir / "vehicle_log.parquet"
    problem_out = cleaned_dir / "problem_log.parquet"
    daily_out = cleaned_dir / "daily_recognition.parquet"

    assert vehicle_out.exists()
    assert problem_out.exists()
    assert daily_out.exists()

    assert len(pd.read_parquet(vehicle_out)) == 1
    assert len(pd.read_parquet(problem_out)) == 1
    assert len(pd.read_parquet(daily_out)) >= 4
