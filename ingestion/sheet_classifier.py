import re
from enum import Enum
from typing import Optional, List, Dict


class SheetType(Enum):
    VEHICLE_LOG = "vehicle_log"
    PROBLEM_LOG = "problem_log"
    DAILY_RECOGNITION = "daily_recognition"
    UNKNOWN = "unknown"


VEHICLE_LOG_NAMES = {"车辆信息统计", "vehicle log", "vehicle information", "车辆信息统计(vehicle data)", "车辆信息统计(Vehicle data)"}
PROBLEM_LOG_NAMES = {"问题记录", "problem record", "problems", "问题记录(problem description)", "问题记录(Problem Description)"}


def classify_sheet(sheet_name: str) -> SheetType:
    name = sheet_name.strip()
    lower_name = name.lower()

    if lower_name in {n.lower() for n in VEHICLE_LOG_NAMES}:
        return SheetType.VEHICLE_LOG

    if lower_name in {n.lower() for n in PROBLEM_LOG_NAMES}:
        return SheetType.PROBLEM_LOG

    if re.match(r'^\d{1,2}[.\-/]\d{2}$', name):
        return SheetType.DAILY_RECOGNITION

    return SheetType.UNKNOWN


def classify_all_sheets(sheet_names: List[str]) -> Dict[str, SheetType]:
    return {name: classify_sheet(name) for name in sheet_names}
