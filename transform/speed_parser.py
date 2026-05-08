# transform/speed_parser.py

import re
from typing import Optional, Tuple


def parse_speed_event(raw: Optional[str]) -> Tuple[Optional[int], Optional[int], Optional[str]]:
    """
    Parse a speed mismatch string into (actual_limit, displayed_speed, warning).

    Returns:
        actual_speed_limit  — what the road sign actually says
        displayed_speed     — what the car's ISA system showed
        warning             — set if parsing was ambiguous
    """
    if raw is None:
        return None, None, None

    raw = str(raw).strip()

    if not raw or raw in {"/", "//", "N/A", ""}:
        return None, None, None

    # Remove common Chinese labels
    cleaned = re.sub(r'(限速|speed|实际|actual)', '', raw, flags=re.IGNORECASE)
    cleaned = re.sub(r'(显示|speedometer|仪表)', '/', cleaned, flags=re.IGNORECASE)

    # Find all numbers in order
    numbers = re.findall(r'\d+', cleaned)

    if len(numbers) >= 2:
        try:
            actual = int(numbers[0])
            displayed = int(numbers[1])
            warning = None
            if len(numbers) > 2:
                warning = f"found {len(numbers)} numbers in '{raw}', using first two"
            return actual, displayed, warning
        except ValueError as e:
            return None, None, f"speed parse error '{raw}': {e}"

    if len(numbers) == 1:
        return int(numbers[0]), None, f"only one speed value found in '{raw}'"

    return None, None, f"no numbers found in speed string '{raw}'"