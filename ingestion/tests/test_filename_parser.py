import pytest
from ingestion.filename_parser import parse_filename
from ingestion.sheet_classifier import classify_sheet, SheetType


def test_parses_n50_file():
    meta = parse_filename("测试队N50ISA-Driver_One-p2.xlsx")
    assert meta.vehicle_id == "N50"
    assert meta.driver_name == "Driver_One"
    assert meta.phase == "p2"


def test_parses_double_underscore_driver():
    meta = parse_filename("北汽ISA-Driver__Three-p1_.xlsx")
    assert meta.driver_name == "Driver_Three"
    assert meta.phase == "p1"


def test_unknown_file_has_warnings():
    meta = parse_filename("random_file_no_info.xlsx")
    assert meta.vehicle_id is None
    assert meta.parse_warning is not None


def test_sheet_classifier():
    assert classify_sheet("车辆信息统计") == SheetType.VEHICLE_LOG
    assert classify_sheet("问题记录") == SheetType.PROBLEM_LOG
    assert classify_sheet("03.27") == SheetType.DAILY_RECOGNITION
    assert classify_sheet("Summary") == SheetType.UNKNOWN
