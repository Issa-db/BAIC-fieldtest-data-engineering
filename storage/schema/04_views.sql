-- 04_views.sql
-- Analytical views used by the Streamlit dashboard (Phase 04)

-- Overall recognition rate by country
CREATE OR REPLACE VIEW vw_rate_by_country AS
SELECT
    country,
    road_type,
    ROUND(AVG(recognition_rate_daylight), 4) AS avg_rate_daylight,
    ROUND(AVG(recognition_rate_dark), 4)     AS avg_rate_dark,
    SUM(total_km_daylight)                   AS total_km,
    COUNT(*)                                 AS day_count
FROM mart_recognition_daily
WHERE country IS NOT NULL
GROUP BY 1, 2
ORDER BY avg_rate_daylight ASC;


-- Weekly recognition rate trend per vehicle
CREATE OR REPLACE VIEW vw_weekly_trend AS
SELECT
    dt.year,
    dt.week,
    r.vehicle_id,
    r.country,
    ROUND(
        SUM(r.correct_km_daylight) / NULLIF(SUM(r.total_km_daylight), 0), 4
    ) AS recognition_rate,
    SUM(r.total_km_daylight) AS km_driven
FROM mart_recognition_daily r
LEFT JOIN dim_date dt ON r.entry_date = dt.date_key
GROUP BY 1, 2, 3, 4
ORDER BY 1, 2;


-- Problem frequency by speed limit value
CREATE OR REPLACE VIEW vw_problems_by_speed_limit AS
SELECT
    actual_speed_limit,
    country,
    road_type,
    COUNT(*)                          AS event_count,
    ROUND(AVG(speed_delta), 1)        AS avg_speed_delta,
    ROUND(AVG(resolution_minutes), 1) AS avg_resolution_min
FROM mart_problems
WHERE actual_speed_limit IS NOT NULL
GROUP BY 1, 2, 3
ORDER BY event_count DESC;


-- Daily mileage and cumulative issues trend
CREATE OR REPLACE VIEW vw_daily_progress AS
SELECT
    entry_date,
    vehicle_id,
    country,
    daily_mileage_km,
    cumulative_issues,
    SUM(daily_mileage_km) OVER (
        PARTITION BY vehicle_id ORDER BY entry_date
    ) AS total_km_to_date
FROM mart_vehicle_daily
ORDER BY vehicle_id, entry_date;

