-- 03_marts.sql
-- Wide mart tables - pre-joined for BI tools and non-SQL users

CREATE TABLE IF NOT EXISTS mart_recognition_daily AS
WITH recognition_base AS (
    SELECT
        r.*,
        MAX(CASE WHEN r.block_type = 'SEGMENT' THEN 1 ELSE 0 END) OVER (
            PARTITION BY r.source_file, r.vehicle_id, r.entry_date
        ) AS has_segment
    FROM fact_daily_recognition r
)
SELECT
    r.entry_date,
    v.vehicle_id,
    d.driver_name,
    d.phase,
    c.country,
    r.road_type,
    SUM(r.daylight_total_km)         AS total_km_daylight,
    SUM(r.daylight_correct_km)       AS correct_km_daylight,
    SUM(r.dark_total_km)             AS total_km_dark,
    SUM(r.dark_correct_km)           AS correct_km_dark,
    CASE
        WHEN SUM(r.daylight_total_km) > 0
        THEN ROUND(SUM(r.daylight_correct_km) / SUM(r.daylight_total_km), 4)
    END AS recognition_rate_daylight,
    CASE
        WHEN SUM(r.dark_total_km) > 0
        THEN ROUND(SUM(r.dark_correct_km) / SUM(r.dark_total_km), 4)
    END AS recognition_rate_dark,
    COUNT(*)                         AS segment_count
FROM recognition_base r
LEFT JOIN dim_vehicle  v ON r.vehicle_id  = v.vehicle_id
LEFT JOIN dim_driver   d ON r.driver_id   = d.driver_id
LEFT JOIN dim_country  c ON r.country_key = c.country_key
WHERE r.block_type = 'SEGMENT'
   OR (r.block_type = 'TOTAL' AND r.has_segment = 0)
GROUP BY 1, 2, 3, 4, 5, 6;


CREATE TABLE IF NOT EXISTS mart_problems AS
SELECT
    p.event_date,
    v.vehicle_id,
    d.driver_name,
    d.phase,
    c.country,
    p.road_type,
    p.actual_speed_limit,
    p.displayed_speed,
    p.speed_delta,
    p.resolution_minutes,
    p.description_raw,
    dt.month_name,
    dt.week
FROM fact_problem_log p
LEFT JOIN dim_vehicle  v  ON p.vehicle_id  = v.vehicle_id
LEFT JOIN dim_driver   d  ON p.driver_id   = d.driver_id
LEFT JOIN dim_country  c  ON p.country_key = c.country_key
LEFT JOIN dim_date     dt ON p.event_date  = dt.date_key;


CREATE TABLE IF NOT EXISTS mart_vehicle_daily AS
SELECT
    vl.entry_date,
    v.vehicle_id,
    d.driver_name,
    d.phase,
    c.country,
    vl.daily_mileage_km,
    vl.issues_today,
    vl.cumulative_issues,
    vl.remark
FROM fact_vehicle_log vl
LEFT JOIN dim_vehicle v ON vl.vehicle_id  = v.vehicle_id
LEFT JOIN dim_driver  d ON vl.driver_id   = d.driver_id
LEFT JOIN dim_country c ON vl.country_key = c.country_key;

