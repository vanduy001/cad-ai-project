"""
validator.py
==============
Lớp kiểm tra & hiệu chỉnh thiết kế — TRỌNG TÂM NGHIÊN CỨU của đề tài.

Ba nhóm kiểm tra:
    1. Geometric validity  : solid có hợp lệ không (volume>0, không lỗi topology)
    2. Dimensional accuracy: kích thước bao (bounding box) có khớp spec không
    3. Feature presence    : số lượng feature (lỗ, fillet...) có đúng như spec không
                              (kiểm tra gián tiếp qua số mặt trụ / volume chênh lệch)

Mọi hàm trả về ValidationReport — có is_valid (bool) và errors (list[str]).
Danh sách errors được thiết kế để ĐƯA THẲNG vào prompt sửa lỗi cho LLM
(feedback loop), nên viết rõ ràng, có số liệu cụ thể, không mơ hồ.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from spec_schema import PartSpec
from cq_executor import ExecutionResult


@dataclass
class ValidationReport:
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)  # số liệu dùng để chấm điểm sau này

    def summary_for_llm(self) -> str:
        """Định dạng lỗi thành đoạn text ngắn gọn để đưa vào prompt sửa lỗi."""
        if self.is_valid:
            return "Thiết kế hợp lệ, không có lỗi."
        lines = ["Thiết kế CHƯA đạt yêu cầu, các lỗi cụ thể:"]
        for i, e in enumerate(self.errors, 1):
            lines.append(f"{i}. {e}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Kích thước bao kỳ vọng theo part_type — dùng để so khớp bounding box
# ---------------------------------------------------------------------------

def _expected_bounding_box(spec: PartSpec) -> dict:
    d = spec.base_dimensions
    if spec.part_type in ("plate", "bracket"):
        return {"xlen": d["length"], "ylen": d["width"], "zlen": d["thickness"]}
    if spec.part_type == "flange":
        od = d["outer_diameter"]
        return {"xlen": od, "ylen": od, "zlen": d["thickness"]}
    if spec.part_type == "shaft":
        dia = d["diameter"]
        return {"xlen": dia, "ylen": dia, "zlen": d["length"]}
    if spec.part_type == "housing":
        return {"xlen": d["length"], "ylen": d["width"], "zlen": d["height"]}
    return {}


def check_geometric_validity(exec_result: ExecutionResult) -> tuple[bool, list[str]]:
    """Nhóm 1: solid có build thành công và có thể tích dương không."""
    errors = []
    if not exec_result.success:
        errors.append(f"Build thất bại: {exec_result.error_message}")
        return False, errors
    if exec_result.volume is None or exec_result.volume <= 0:
        errors.append(f"Volume không hợp lệ: {exec_result.volume} (phải > 0)")
        return False, errors
    return True, errors


def check_dimensional_accuracy(spec: PartSpec, exec_result: ExecutionResult) -> tuple[bool, list[str], dict]:
    """Nhóm 2: so bounding box thực tế với bounding box kỳ vọng từ spec.
    Sai lệch cho phép = spec.tolerance (mm).
    """
    errors: list[str] = []
    metrics: dict = {}

    expected = _expected_bounding_box(spec)
    actual = exec_result.bounding_box or {}

    for axis in ("xlen", "ylen", "zlen"):
        if axis not in expected:
            continue
        exp_val = expected[axis]
        act_val = actual.get(axis)
        if act_val is None:
            errors.append(f"Không đọc được kích thước '{axis}' của mô hình để so sánh.")
            continue
        diff = abs(act_val - exp_val)
        diff_pct = (diff / exp_val * 100) if exp_val else 0.0
        metrics[f"{axis}_error_mm"] = round(diff, 4)
        metrics[f"{axis}_error_pct"] = round(diff_pct, 2)
        if diff > spec.tolerance:
            errors.append(
                f"Kích thước '{axis}' lệch {diff:.3f}mm ({diff_pct:.1f}%): "
                f"kỳ vọng {exp_val}mm, thực tế {act_val}mm "
                f"(vượt sai số cho phép {spec.tolerance}mm)"
            )

    return (len(errors) == 0), errors, metrics


def check_feature_count(spec: PartSpec, exec_result: ExecutionResult) -> tuple[bool, list[str]]:
    """Nhóm 3 (kiểm tra thô): ước lượng thể tích bị trừ đi bởi các feature dạng
    cắt (hole, pocket, slot) và so với thể tích lý thuyết dự kiến bị trừ.
    Đây là kiểm tra GIÁN TIẾP, không thay thế việc soi từng feature bằng
    cách duyệt topology (nên làm ở bản mở rộng, dùng result.val().Faces()
    để đếm số mặt trụ có đường kính khớp spec).
    """
    errors: list[str] = []
    expected = _expected_bounding_box(spec)
    if not expected:
        return True, errors

    # Thể tích khối đặc lý thuyết (chưa trừ feature) để ước lượng % vật liệu bị cắt
    if spec.part_type in ("plate", "bracket", "housing"):
        solid_volume = expected["xlen"] * expected["ylen"] * expected["zlen"]
    else:
        solid_volume = None

    n_holes = sum(1 for f in spec.features if f.type == "hole")
    n_pockets = sum(1 for f in spec.features if f.type == "pocket")

    if exec_result.volume is not None and solid_volume:
        if (n_holes > 0 or n_pockets > 0) and exec_result.volume >= solid_volume * 0.999:
            errors.append(
                f"Spec yêu cầu {n_holes} lỗ / {n_pockets} pocket nhưng volume mô hình "
                f"({exec_result.volume}mm³) gần bằng khối đặc lý thuyết "
                f"({solid_volume}mm³) — có khả năng feature cắt vật liệu KHÔNG được áp dụng."
            )

    return (len(errors) == 0), errors


def validate_design(spec: PartSpec, exec_result: ExecutionResult) -> ValidationReport:
    """Hàm tổng hợp — gọi cả 3 nhóm kiểm tra, gộp kết quả."""
    all_errors: list[str] = []
    all_warnings: list[str] = []
    metrics: dict = {}

    ok_geo, err_geo = check_geometric_validity(exec_result)
    all_errors.extend(err_geo)

    if ok_geo:
        ok_dim, err_dim, dim_metrics = check_dimensional_accuracy(spec, exec_result)
        all_errors.extend(err_dim)
        metrics.update(dim_metrics)

        ok_feat, err_feat = check_feature_count(spec, exec_result)
        all_errors.extend(err_feat)

    is_valid = len(all_errors) == 0
    return ValidationReport(
        is_valid=is_valid,
        errors=all_errors,
        warnings=all_warnings,
        metrics=metrics,
    )


if __name__ == "__main__":
    from spec_schema import example_plate_spec
    from cq_executor import ExecutionResult

    spec = example_plate_spec()

    # Case 1: mô phỏng build đúng
    good = ExecutionResult(
        success=True,
        bounding_box={"xlen": 100.0, "ylen": 60.0, "zlen": 5.0},
        volume=100 * 60 * 5 - 4 * (3.14159 * 3 * 3 * 5) * 0.95,  # gần đúng, có trừ lỗ
    )
    report = validate_design(spec, good)
    print("=== Case build đúng ===")
    print(report.summary_for_llm())
    print("Metrics:", report.metrics)

    # Case 2: mô phỏng build sai kích thước (quên fillet, sai chiều dài)
    bad = ExecutionResult(
        success=True,
        bounding_box={"xlen": 100.0, "ylen": 60.0, "zlen": 5.0},
        volume=100 * 60 * 5,  # không trừ lỗ nào -> feature check sẽ bắt lỗi
    )
    report2 = validate_design(spec, bad)
    print("\n=== Case thiếu feature (quên khoét lỗ) ===")
    print(report2.summary_for_llm())
