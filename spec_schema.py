"""
spec_schema.py
================
Định nghĩa Parametric Spec — định dạng trung gian giữa "yêu cầu ngôn ngữ
tự nhiên" và "code CadQuery". Đây là phần XƯƠNG SỐNG của pipeline:

    NL request --(LLM)--> PartSpec (JSON) --(generator)--> CadQuery code

Thiết kế không dùng pydantic để tránh phụ thuộc ngoài lúc cài đặt ban đầu
(có thể nâng cấp sang pydantic sau khi môi trường ổn định). Validate thủ
công bằng hàm validate_spec().

Mọi đơn vị chiều dài mặc định là milimét (mm).
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional, Literal, Any
import json

# ---------------------------------------------------------------------------
# Các loại part_type và feature_type được pipeline hỗ trợ ở giai đoạn 1.
# Mở rộng dần khi bộ test case yêu cầu thêm.
# ---------------------------------------------------------------------------
SUPPORTED_PART_TYPES = ("plate", "bracket", "flange", "shaft", "housing")
SUPPORTED_FEATURE_TYPES = ("hole", "fillet", "chamfer", "pocket", "boss", "slot")


class SpecValidationError(ValueError):
    """Raised khi PartSpec không hợp lệ (thiếu trường, sai kiểu, sai giá trị)."""


@dataclass
class Feature:
    """Một feature (đặc trưng hình học) áp lên khối cơ sở.

    type: "hole" | "fillet" | "chamfer" | "pocket" | "boss" | "slot"
    params: dict tham số riêng cho từng loại feature, ví dụ:
        hole:    {"diameter": 6, "depth": "through", "positions": [[10,10],[90,10]]}
        fillet:  {"radius": 3, "edges": "all" | "corners" | "top" | "bottom"}
        chamfer: {"distance": 1, "edges": "top"}
        pocket:  {"length": 20, "width": 10, "depth": 3, "position": [50, 30]}
        boss:    {"diameter": 12, "height": 5, "position": [50, 30]}
        slot:    {"length": 20, "width": 5, "depth": "through", "position": [50,30], "angle": 0}
    """
    type: str
    params: dict[str, Any] = field(default_factory=dict)

    def validate(self, idx: int) -> list[str]:
        errs = []
        if self.type not in SUPPORTED_FEATURE_TYPES:
            errs.append(
                f"features[{idx}].type='{self.type}' không được hỗ trợ "
                f"(chỉ chấp nhận {SUPPORTED_FEATURE_TYPES})"
            )
        if not isinstance(self.params, dict):
            errs.append(f"features[{idx}].params phải là dict")
        return errs


@dataclass
class Constraint:
    """Ràng buộc thiết kế cấp cao, dùng cho constraint checker ở validator.py.

    type: "symmetric" | "concentric" | "min_wall_thickness" | "min_edge_distance"
    params: tham số riêng, ví dụ:
        symmetric: {"axis": "x" | "y" | "both"}
        min_wall_thickness: {"value": 2.0}
        min_edge_distance: {"value": 5.0}
        concentric: {"feature_a": 0, "feature_b": 1}
    """
    type: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class PartSpec:
    part_type: str
    base_dimensions: dict[str, float]      # vd: {"length":100,"width":60,"thickness":5}
    features: list[Feature] = field(default_factory=list)
    constraints: list[Constraint] = field(default_factory=list)
    material: Optional[str] = None
    tolerance: float = 0.1                  # mm, sai lệch cho phép khi validate
    units: str = "mm"

    # ---- (de)serialization -------------------------------------------------
    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @staticmethod
    def from_dict(d: dict) -> "PartSpec":
        features = [Feature(**f) for f in d.get("features", [])]
        constraints = [Constraint(**c) for c in d.get("constraints", [])]
        return PartSpec(
            part_type=d["part_type"],
            base_dimensions=d["base_dimensions"],
            features=features,
            constraints=constraints,
            material=d.get("material"),
            tolerance=d.get("tolerance", 0.1),
            units=d.get("units", "mm"),
        )

    @staticmethod
    def from_json(s: str) -> "PartSpec":
        return PartSpec.from_dict(json.loads(s))


def validate_spec(spec: PartSpec) -> list[str]:
    """Kiểm tra spec có hợp lệ về mặt CẤU TRÚC (không phải hình học thật).
    Kiểm tra hình học thật (chạy CadQuery xong) nằm ở validator.py.

    Trả về danh sách lỗi (rỗng nếu hợp lệ). Dùng list rỗng thay vì bool để
    feedback loop có thể đưa thẳng lỗi này cho LLM sửa.
    """
    errors: list[str] = []

    if spec.part_type not in SUPPORTED_PART_TYPES:
        errors.append(
            f"part_type='{spec.part_type}' không được hỗ trợ "
            f"(chỉ chấp nhận {SUPPORTED_PART_TYPES})"
        )

    required_dims = {
        "plate": ["length", "width", "thickness"],
        "bracket": ["length", "width", "thickness"],
        "flange": ["outer_diameter", "inner_diameter", "thickness"],
        "shaft": ["diameter", "length"],
        "housing": ["length", "width", "height", "wall_thickness"],
    }
    needed = required_dims.get(spec.part_type, [])
    for dim in needed:
        if dim not in spec.base_dimensions:
            errors.append(f"base_dimensions thiếu trường bắt buộc '{dim}' cho part_type='{spec.part_type}'")
        elif not isinstance(spec.base_dimensions[dim], (int, float)) or spec.base_dimensions[dim] <= 0:
            errors.append(f"base_dimensions['{dim}'] phải là số dương")

    for i, feat in enumerate(spec.features):
        errors.extend(feat.validate(i))

    if spec.tolerance <= 0:
        errors.append("tolerance phải > 0")

    return errors


# ---------------------------------------------------------------------------
# Ví dụ spec mẫu — dùng cho demo / test, khớp với ví dụ trong README.
# NL request tương ứng:
#   "Thiết kế tấm phẳng thép 100x60x5mm, có 4 lỗ bắt vít đường kính 6mm
#    cách mỗi cạnh 10mm, bo tròn 4 góc bán kính 3mm"
# ---------------------------------------------------------------------------
def example_plate_spec() -> PartSpec:
    return PartSpec(
        part_type="plate",
        base_dimensions={"length": 100, "width": 60, "thickness": 5},
        features=[
            Feature(
                type="hole",
                params={
                    "diameter": 6,
                    "depth": "through",
                    "positions": [[10, 10], [90, 10], [10, 50], [90, 50]],
                },
            ),
            Feature(type="fillet", params={"radius": 3, "edges": "corners"}),
        ],
        constraints=[Constraint(type="symmetric", params={"axis": "both"})],
        material="Steel",
        tolerance=0.1,
    )


if __name__ == "__main__":
    spec = example_plate_spec()
    print(spec.to_json())
    errs = validate_spec(spec)
    print("\nValidation errors:", errs if errs else "KHÔNG CÓ — spec hợp lệ")
