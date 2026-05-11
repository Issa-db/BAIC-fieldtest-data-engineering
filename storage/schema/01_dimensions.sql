-- 01_dimensions.sql
-- Dimension tables for the ISA analytics star schema

CREATE TABLE IF NOT EXISTS dim_vehicle (
    vehicle_id   VARCHAR PRIMARY KEY,
    fleet        VARCHAR,
    vehicle_type VARCHAR DEFAULT 'EV'
);

CREATE TABLE IF NOT EXISTS dim_driver (
    driver_id   VARCHAR PRIMARY KEY,
    driver_name VARCHAR NOT NULL,
    phase       VARCHAR
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_key     DATE PRIMARY KEY,
    year         INTEGER NOT NULL,
    month        INTEGER NOT NULL,
    week         INTEGER NOT NULL,
    day_of_week  INTEGER NOT NULL,
    month_name   VARCHAR NOT NULL,
    quarter      INTEGER NOT NULL,
    is_weekend   BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_country (
    country_key VARCHAR PRIMARY KEY,
    country     VARCHAR NOT NULL,
    region      VARCHAR DEFAULT 'Europe'
);

-- Seed known countries
INSERT OR IGNORE INTO dim_country VALUES
    ('Germany',     'Germany',     'Europe'),
    ('France',      'France',      'Europe'),
    ('Italy',       'Italy',       'Europe'),
    ('Switzerland', 'Switzerland', 'Europe'),
    ('Austria',     'Austria',     'Europe'),
    ('Netherlands', 'Netherlands', 'Europe'),
    ('Belgium',     'Belgium',     'Europe'),
    ('unknown',     'Unknown',     'Unknown');

