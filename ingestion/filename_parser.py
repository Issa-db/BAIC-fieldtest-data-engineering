import re
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Union


@dataclass
class FileMetadata:
    raw_filename: str
    vehicle_id: Optional[str]
    driver_name: Optional[str]
    phase: Optional[str]
    fleet: Optional[str]
    parse_warning: Optional[str]


def parse_filename(path: Union[str, Path]) -> FileMetadata:
    """
    Extract structured metadata from an ISA test Excel filename.
    Never raises — always returns a FileMetadata, with parse_warning set if needed.
    """
    stem = Path(path).stem

    vehicle_id = None
    driver_name = None
    phase = None
    fleet = None
    warnings: list[str] = []

    vehicle_match = re.search(r'(N\d{2,3})(?!\d)', stem)
    if vehicle_match:
        vehicle_id = vehicle_match.group(1)
    else:
        warnings.append("vehicle_id not found in filename")

    driver_match = re.search(r'-([^\-]+?)(?:-p[12]|$)', stem, re.IGNORECASE)
    if driver_match:
        raw_driver = driver_match.group(1)
        driver_name = re.sub(r'[\s_]+', '_', raw_driver).strip('_')
        if not driver_name:
            driver_name = None
            warnings.append("driver_name found but empty after normalization")
    else:
        warnings.append("driver_name not found in filename")

    phase_match = re.search(r'-(p[12])_?', stem, re.IGNORECASE)
    if phase_match:
        phase = phase_match.group(1).lower()
    else:
        warnings.append("phase not found in filename — defaulting to unknown")
        phase = "unknown"

    fleet_match = re.match(r'^([\u4e00-\u9fff]+)', stem)
    if fleet_match:
        fleet = fleet_match.group(1)

    return FileMetadata(
        raw_filename=Path(path).name,
        vehicle_id=vehicle_id,
        driver_name=driver_name,
        phase=phase,
        fleet=fleet,
        parse_warning="; ".join(warnings) if warnings else None,
    )


if __name__ == "__main__":
    cases = [
        "测试队N50ISA-Driver_One-p2.xlsx",
        "测试队N51ISA-Driver_Two-p2.xlsx",
        "北汽ISA-Driver__Three-p1_.xlsx",
        "unknown_file_no_vehicle.xlsx",
    ]
    for c in cases:
        result = parse_filename(c)
        print(result)
