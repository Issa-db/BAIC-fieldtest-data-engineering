-- 02_facts.sql
-- Fact tables - one per source sheet type

CREATE TABLE IF NOT EXISTS fact_vehicle_log (
    fact_id             VARCHAR DEFAULT gen_random_uuid(),
    source_file         VARCHAR NOT NULL,
    vehicle_id          VARCHAR REFERENCES dim_vehicle(vehicle_id),
    driver_id           VARCHAR REFERENCES dim_driver(driver_id),
    entry_date          DATE REFERENCES dim_date(date_key),
    country_key         VARCHAR REFERENCES dim_country(country_key),
    location_raw        VARCHAR,
    daily_mileage_km    DOUBLE,
    issues_today        INTEGER,
    cumulative_issues   INTEGER,
    remark              VARCHAR,
    ingested_at         TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fact_problem_log (
    fact_id             VARCHAR DEFAULT gen_random_uuid(),
    source_file         VARCHAR NOT NULL,
    vehicle_id          VARCHAR REFERENCES dim_vehicle(vehicle_id),
    driver_id           VARCHAR REFERENCES dim_driver(driver_id),
    event_date          DATE REFERENCES dim_date(date_key),
    event_time          VARCHAR,
    car_type            VARCHAR,
    vin_partial         VARCHAR,
    actual_speed_limit  INTEGER,
    displayed_speed     INTEGER,
    speed_delta         INTEGER,
    country_key         VARCHAR REFERENCES dim_country(country_key),
    road_type           VARCHAR,
    resolution_minutes  DOUBLE,
    description_raw     VARCHAR,
    ingested_at         TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fact_daily_recognition (
    fact_id                   VARCHAR DEFAULT gen_random_uuid(),
    source_file               VARCHAR NOT NULL,
    vehicle_id                VARCHAR REFERENCES dim_vehicle(vehicle_id),
    driver_id                 VARCHAR REFERENCES dim_driver(driver_id),
    entry_date                DATE REFERENCES dim_date(date_key),
    country_key               VARCHAR REFERENCES dim_country(country_key),
    segment_no                INTEGER,
    block_type                VARCHAR,
    road_type                 VARCHAR,
    daylight_total_km         DOUBLE,
    daylight_correct_km       DOUBLE,
    dark_total_km             DOUBLE,
    dark_correct_km           DOUBLE,
    recognition_rate_daylight DOUBLE,
    recognition_rate_dark     DOUBLE,
    ingested_at               TIMESTAMP
);

