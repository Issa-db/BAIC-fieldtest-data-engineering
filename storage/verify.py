from storage.db import get_connection


def verify() -> None:
    conn = get_connection(read_only=True)

    tables = [
        "dim_vehicle",
        "dim_driver",
        "dim_date",
        "dim_country",
        "fact_vehicle_log",
        "fact_problem_log",
        "fact_daily_recognition",
        "mart_recognition_daily",
        "mart_problems",
        "mart_vehicle_daily",
    ]

    print("\n-- Row counts ----------------------------")
    for t in tables:
        n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        status = "OK" if n > 0 else "EMPTY"
        print(f"  {status:<5} {t:<35} {n:>6} rows")

    print("\n-- Top 5 countries by recognition rate --")
    rows = conn.execute(
        """
        SELECT country, road_type,
               ROUND(avg_rate_daylight * 100, 1) AS rate_pct,
               total_km
        FROM vw_rate_by_country
        ORDER BY rate_pct ASC
        LIMIT 5
    """
    ).fetchall()
    for r in rows:
        country = r[0] or "Unknown"
        road_type = r[1] or "unknown"
        rate = "n/a" if r[2] is None else f"{r[2]}%"
        total_km = 0 if r[3] is None else round(r[3], 0)
        print(f"  {country:<15} {road_type:<15} {rate:<6} ({total_km:.0f} km)")
        
    print("\n-- Total KM total_km in all countries --")
    total = conn.execute("SELECT SUM(total_km) FROM vw_rate_by_country").fetchone()[0]
    total_km = 0 if total is None else round(total, 0)
    print(f"  {total_km:.0f} km")

    conn.close()

if __name__ == "__main__":
    verify()

