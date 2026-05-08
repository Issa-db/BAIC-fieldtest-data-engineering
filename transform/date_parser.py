# transform/date_parser.py

import re
from datetime import date, datetime
from typing import Optional, Tuple
from dateutil import parser as dateutil_parser

# If a date parses to a year outside this range, it is flagged as suspicious
VALID_YEAR_MIN = 2024
VALID_YEAR_MAX = 2027

# Year to assume when a date string has no year (e.g. "28.03")
DEFAULT_YEAR = 2026


def parse_date(raw: Optional[str], source_hint: str = "") -> Tuple[Optional[date], Optional[str]]:
    """
    Parse any of the date formats seen in the ISA source files.

    Returns (parsed_date, warning_message).
    warning_message is None if the date parsed cleanly.
    Returns (None, warning) if parsing fails entirely.
    """
    if raw is None:
        return None, None

    raw = str(raw).strip()

    if not raw or raw in {"/", "//", "-", "N/A", "na", ""}:
        return None, None

    # ── 1. Handle short formats with no year: "28.03" or "3.27"
    short_match = re.match(r'^(\d{1,2})[.\-/](\d{2})$', raw)
    if short_match:
        try:
            day = int(short_match.group(1))
            month = int(short_match.group(2))
            # Assume year 2026 for short dates
            parsed = date(DEFAULT_YEAR, month, day)
            if parsed.year < VALID_YEAR_MIN or parsed.year > VALID_YEAR_MAX:
                return parsed, f"suspicious year {parsed.year} in '{raw}' (expected {VALID_YEAR_MIN}-{VALID_YEAR_MAX})"
            return parsed, None
        except ValueError as e:
            return None, f"invalid short date '{raw}': {e}"

    # ── 2. Handle mixed separator: "04-01/2026"
    mixed = re.sub(r'[\-/.]', '-', raw)

    # ── 3. Try dateutil for everything else (handles most standard formats)
    try:
        d = dateutil_parser.parse(mixed, dayfirst=False).date()
        if d.year < VALID_YEAR_MIN or d.year > VALID_YEAR_MAX:
            warning = f"suspicious year {d.year} in '{raw}' (expected {VALID_YEAR_MIN}-{VALID_YEAR_MAX})"
            return d, warning
        return d, None

    except Exception as e:
        return None, f"cannot parse date '{raw}': {e}"


def parse_time(raw: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse a time string — handles both ':' and ';' as separators.
    Returns (HH:MM string, warning) or (None, warning).
    """
    if raw is None:
        return None, None
    raw = str(raw).strip()
    if not raw or raw in {"/", "//"}:
        return None, None

    # Replace semicolons used as time separators
    normalized = raw.replace(';', ':').replace('；', ':')

    match = re.match(r'^(\d{1,2}):(\d{2})(?::\d{2})?$', normalized)
    if match:
        h = int(match.group(1))
        m = int(match.group(2))
        if 0 <= h <= 23 and 0 <= m <= 59:
            return f"{h:02d}:{m:02d}", None
        else:
            return None, f"invalid time values h={h}, m={m} in '{raw}'"

    return None, f"cannot parse time '{raw}'"