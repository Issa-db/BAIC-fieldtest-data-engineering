# EV ADAS ISA Field Test — ETL Pipeline
## BAIC / Bethel Project 

> ETL pipeline for processing ISA (Intelligent Speed Assistance)
> field test data from BAIC electric vehicles tested across Europe.


```text
BICA - DATA/
├── .github/
│   └── workflows/
│       └── ci.yml
├── claude-agent/
├── data/
│   ├── raw/
│   │   └── processed/
│   ├── landing/
│   │   ├── vehicle_log/
│   │   ├── problem_log/
│   │   └── daily_recognition/
│   ├── cleaned/
│   └── quarantine/
├── docs/
│   └── phase2-cicd-runbook.md
├── img/
├── ingestion/
│   ├── __init__.py (optional)
│   ├── filename_parser.py
│   ├── sheet_classifier.py
│   ├── run_ingestion.py
│   ├── readers/
│   │   ├── vehicle_log_reader.py
│   │   ├── problem_log_reader.py
│   │   └── daily_recognition_reader.py
│   ├── tests/
│   │   └── test_filename_parser.py
├── logs/
├── transform/
│   ├── __init__.py
│   ├── date_parser.py
│   ├── speed_parser.py
│   ├── country_mapper.py
│   ├── run_transform.py
│   ├── tests/
│   │   └── test_run_transform.py
│   ├── transformers/
│   │   ├── vehicle_log_transformer.py
│   │   ├── problem_log_transformer.py
│   │   └── daily_recognition_transformer.py
├── requirements.txt
└── README.md
```

## Generated Files (After a Successful Run)

```text
BICA - DATA/
├── data/
│   ├── raw/
│   │   └── processed/
│   │       ├── <source-file-1>.xlsx
│   │       └── <source-file-2>.xlsx
│   ├── landing/
│   │   ├── vehicle_log/
│   │   │   └── <file_stem>__<YYYYMMDDTHHMMSS>.parquet
│   │   ├── problem_log/
│   │   │   └── <file_stem>__<YYYYMMDDTHHMMSS>.parquet
│   │   └── daily_recognition/
│   │       └── <file_stem>__<YYYYMMDDTHHMMSS>.parquet
│   ├── cleaned/
│   │   ├── vehicle_log.parquet
│   │   ├── problem_log.parquet
│   │   └── daily_recognition.parquet
│   └── quarantine/
│       └── <invalid-or-unparsed-file>.xlsx
└── logs/
    ├── ingestion.log
    └── transform.log
```

## Pipeline Flow

1. Put source Excel files in `data/raw/`
2. Run ingestion (`ingestion/run_ingestion.py`) to create parquet files in `data/landing/`
3. Run transform phase 2 (`python -m transform.run_transform`) to create cleaned outputs in `data/cleaned/`
4. Review logs in `logs/ingestion.log` and `logs/transform.log`
