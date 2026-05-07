import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd
from loguru import logger

from ingestion.filename_parser import parse_filename
from ingestion.sheet_classifier import classify_sheet, SheetType
from ingestion.readers.vehicle_log_reader import read_vehicle_log
from ingestion.readers.problem_log_reader import read_problem_log
from ingestion.readers.daily_recognition_reader import read_daily_recognition

RAW_DIR = Path("data/raw")
LANDING_DIR = Path("data/landing")
QUARANTINE_DIR = Path("data/quarantine")
PROCESSED_DIR = RAW_DIR / "processed"
LOG_FILE = Path("logs/ingestion.log")

for d in [
    RAW_DIR,
    LANDING_DIR / "vehicle_log",
    LANDING_DIR / "problem_log",
    LANDING_DIR / "daily_recognition",
    QUARANTINE_DIR,
    PROCESSED_DIR,
    LOG_FILE.parent,
]:
    d.mkdir(parents=True, exist_ok=True)

logger.add(LOG_FILE, rotation="10 MB", retention="30 days", level="INFO")


def run():
    xlsx_files = list(RAW_DIR.glob("*.xlsx"))
    logger.info(f"Found {len(xlsx_files)} file(s) in {RAW_DIR}")

    results = {
        "processed": [],
        "quarantined": [],
        "skipped": [],
    }

    for filepath in xlsx_files:
        logger.info(f"Processing: {filepath.name}")

        meta = parse_filename(filepath)
        if meta.parse_warning:
            logger.warning(f"{filepath.name} | filename warning: {meta.parse_warning}")

        if meta.vehicle_id is None and meta.driver_name is None:
            logger.error(f"{filepath.name} | cannot parse vehicle_id or driver — quarantining")
            shutil.copy(filepath, QUARANTINE_DIR / filepath.name)
            results["quarantined"].append(filepath.name)
            continue

        file_metadata = {
            "vehicle_id": meta.vehicle_id,
            "driver_name": meta.driver_name,
            "phase": meta.phase,
            "fleet": meta.fleet,
            "ingested_at": datetime.utcnow().isoformat(),
            "source_file": filepath.name,
        }

        try:
            import openpyxl  # noqa: F401
            wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
        except Exception as e:
            logger.error(f"{filepath.name} | cannot open workbook: {e} — quarantining")
            shutil.copy(filepath, QUARANTINE_DIR / filepath.name)
            results["quarantined"].append(filepath.name)
            continue

        sheet_types = {name: classify_sheet(name) for name in wb.sheetnames}
        logger.info(f"{filepath.name} | sheets: {sheet_types}")
        wb.close()

        unknown_sheets = [n for n, t in sheet_types.items() if t == SheetType.UNKNOWN]
        if unknown_sheets:
            logger.warning(f"{filepath.name} | unknown sheets (will skip): {unknown_sheets}")

        all_rows = {
            "vehicle_log": [],
            "problem_log": [],
            "daily_recognition": [],
        }

        for sheet_name, sheet_type in sheet_types.items():
            if sheet_type == SheetType.UNKNOWN:
                continue
            try:
                if sheet_type == SheetType.VEHICLE_LOG:
                    rows = read_vehicle_log(filepath, sheet_name, file_metadata)
                    all_rows["vehicle_log"].extend(rows)
                elif sheet_type == SheetType.PROBLEM_LOG:
                    rows = read_problem_log(filepath, sheet_name, file_metadata)
                    all_rows["problem_log"].extend(rows)
                elif sheet_type == SheetType.DAILY_RECOGNITION:
                    rows = read_daily_recognition(filepath, sheet_name, file_metadata)
                    all_rows["daily_recognition"].extend(rows)
            except Exception as e:
                logger.error(f"{filepath.name} | sheet '{sheet_name}' failed: {e}")

        run_ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        file_stem = filepath.stem.replace(" ", "_")

        for sheet_type_key, rows in all_rows.items():
            if not rows:
                continue
            df = pd.DataFrame(rows)
            out_path = LANDING_DIR / sheet_type_key / f"{file_stem}__{run_ts}.parquet"
            df.to_parquet(out_path, index=False)
            logger.info(f"  wrote {len(df)} rows → {out_path}")

        shutil.move(str(filepath), PROCESSED_DIR / filepath.name)
        logger.info(f"{filepath.name} | moved to processed/")
        results["processed"].append(filepath.name)

    logger.info("─── Ingestion run complete ───")
    logger.info(f"  processed:   {len(results['processed'])}")
    logger.info(f"  quarantined: {len(results['quarantined'])}")
    logger.info(f"  skipped:     {len(results['skipped'])}")
    return results


if __name__ == "__main__":
    run()
