"""
Unit test cho phần KHÔNG phụ thuộc cadquery: spec_schema.py, cq_generator.py,
validator.py (dùng ExecutionResult giả lập).

Chạy: python -m pytest tests/ -v
(hoặc python tests/test_schema_and_generator.py nếu chưa cài pytest)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from spec_schema import PartSpec, Feature, Constraint, validate_spec, example_plate_spec
from cq_generator import generate_cadquery_code, CodeGenError
from cq_executor import ExecutionResult
from validator import validate_design


def test_example_spec_is_valid():
    spec = example_plate_spec()
    assert validate_spec(spec) == []


def test_missing_base_dimension_is_caught():
    spec = PartSpec(part_type="plate", base_dimensions={"length": 100, "width": 60})
    errors = validate_spec(spec)
    assert any("thickness" in e for e in errors)


def test_invalid_part_type_is_caught():
    spec = PartSpec(part_type="rocket", base_dimensions={})
    errors = validate_spec(spec)
    assert any("part_type" in e for e in errors)


def test_negative_dimension_is_caught():
    spec = PartSpec(part_type="plate", base_dimensions={"length": -10, "width": 60, "thickness": 5})
    errors = validate_spec(spec)
    assert any("length" in e for e in errors)


def test_generator_produces_result_variable():
    spec = example_plate_spec()
    code = generate_cadquery_code(spec)
    assert "result = cq.Workplane" in code
    assert "hole(6)" in code
    assert "fillet(3)" in code


def test_generator_rejects_unsupported_part_type():
    spec = PartSpec(part_type="rocket", base_dimensions={})
    try:
        generate_cadquery_code(spec)
        assert False, "Phải raise CodeGenError"
    except CodeGenError:
        pass


def test_generator_flange():
    spec = PartSpec(
        part_type="flange",
        base_dimensions={"outer_diameter": 80, "inner_diameter": 40, "thickness": 8},
    )
    code = generate_cadquery_code(spec)
    assert "circle(80 / 2)" in code
    assert "circle(40 / 2)" in code


def test_validator_catches_dimension_mismatch():
    spec = example_plate_spec()
    bad_exec = ExecutionResult(
        success=True,
        bounding_box={"xlen": 105.0, "ylen": 60.0, "zlen": 5.0},  # lệch 5mm
        volume=100 * 60 * 5,
    )
    report = validate_design(spec, bad_exec)
    assert report.is_valid is False
    assert any("xlen" in e for e in report.errors)


def test_validator_passes_within_tolerance():
    spec = example_plate_spec()
    good_exec = ExecutionResult(
        success=True,
        bounding_box={"xlen": 100.05, "ylen": 60.0, "zlen": 5.0},  # trong tolerance 0.1mm
        volume=100 * 60 * 5 - 4 * 3.14159 * 3 * 3 * 5,
    )
    report = validate_design(spec, good_exec)
    assert report.is_valid is True


def test_validator_catches_missing_holes():
    spec = example_plate_spec()
    no_holes_exec = ExecutionResult(
        success=True,
        bounding_box={"xlen": 100.0, "ylen": 60.0, "zlen": 5.0},
        volume=100 * 60 * 5,  # không trừ lỗ nào
    )
    report = validate_design(spec, no_holes_exec)
    assert report.is_valid is False
    assert any("lỗ" in e for e in report.errors)


def test_validator_catches_build_failure():
    spec = example_plate_spec()
    failed_exec = ExecutionResult(success=False, error_message="Something broke")
    report = validate_design(spec, failed_exec)
    assert report.is_valid is False
    assert "Build thất bại" in report.errors[0]


if __name__ == "__main__":
    # Chạy được cả khi chưa cài pytest.
    import inspect

    current_module = sys.modules[__name__]
    test_funcs = [
        obj for name, obj in inspect.getmembers(current_module)
        if name.startswith("test_") and inspect.isfunction(obj)
    ]

    passed, failed = 0, 0
    for fn in test_funcs:
        try:
            fn()
            print(f"PASS  {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL  {fn.__name__}: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
