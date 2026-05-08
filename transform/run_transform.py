# transform/run_transform.py

from pathlib import Path
import pandas as pd
from loguru import logger

from transform.transformers.vehicle_log_transformer import transform_vehicle_log
from transform.transformers.problem_log_transformer import transform_problem_log
from transform.transformers.daily_recognition_transformer import transform_daily_recognition

LANDING_DIR = Path("data/landing")
CLEANED_DIR = Path("data/cleaned")
LOG_FILE    = Path("logs/transform.log")

for d in [CLEANED_DIR, LOG_FILE.parent]:
    d.mkdir(parents=True, exist_ok=True)

logger.add(LOG_FILE, rotation="10 MB", level="INFO")


def load_landing(sheet_type: str) -> pd.DataFrame:
    folder = LANDING_DIR / sheet_type
    files  = list(folder.glob("*.parquet"))
    if not files:
        logger.warning(f"No parquet files in {folder}")
        return pd.DataFrame()
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)


def run():
    logger.info("Starting transform run")

    # ── Vehicle log ──────────────────────────────────────────────────────────
    df_raw = load_landing("vehicle_log")
    if not df_raw.empty:
        df_clean = transform_vehicle_log(df_raw)
        out = CLEANED_DIR / "vehicle_log.parquet"
        df_clean.to_parquet(out, index=False)
        logger.info(f"vehicle_log: {len(df_clean)} rows → {out}")
    else:
        logger.warning("vehicle_log: no raw data found")

    # ── Problem log ───────────────────────────────────────────────────────────
    df_raw = load_landing("problem_log")
    if not df_raw.empty:
        df_clean = transform_problem_log(df_raw)
        out = CLEANED_DIR / "problem_log.parquet"
        df_clean.to_parquet(out, index=False)
        logger.info(f"problem_log: {len(df_clean)} rows → {out}")

    # ── Daily recognition ─────────────────────────────────────────────────────
    df_raw = load_landing("daily_recognition")
    if not df_raw.empty:
        df_clean = transform_daily_recognition(df_raw)
        out = CLEANED_DIR / "daily_recognition.parquet"
        df_clean.to_parquet(out, index=False)
        logger.info(f"daily_recognition: {len(df_clean)} rows → {out}")

    logger.info("Transform run complete")


if __name__ == "__main__":
    run()