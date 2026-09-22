"""
spec_schema.py
================
Dinh nghia Parametric Spec.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional, Any
import json

SUPPORTED_PART_TYPES = ("plate", "bracket", "flange", "shaft", "housing", "stepped_shaft", "pillow_block")
SUPPORTED_FEATURE_TYPES = (
    "hole", "fillet", "chamfer", "pocket", "boss", "slot",
    "keyway", "bolt_circle", "radial_hole", "counterbore", "side_lugs",
)


class SpecValidationError(ValueError):
    pass


@dataclass
class Feature:
    type: str
    params: dict[str, Any] = field(default_factory=dict)

    def validate(self, idx: int) -> list[str]:
        errs = []
        if self.type not in SUPPORTED_FEATURE_TYPES:
            errs.append(
                f"features[{idx}].type='{self.type}' khong duoc ho tro "
                f"(chi chap nhan {SUPPORTED_FEATURE_TYPES})"
            )
        if not isinstance(self.params, dict):
            errs.append(f"features[{idx}].params phai la dict")
        return errs


@dataclass
class Constraint:
    type: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class PartSpec:
    part_type: str
    base_dimensions: dict[str, Any]
    features: list[Feature] = field(default_factory=list)
    constraints: list[Constraint] = field(default_factory=list)
    material: Optional[str] = None
    tolerance: float = 0.1
    units: str = "mm"

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
    errors: list[str] = []

    if spec.part_type not in SUPPORTED_PART_TYPES:
        errors.append(
            f"part_type='{spec.part_type}' khong duoc ho tro "
            f"(chi chap nhan {SUPPORTED_PART_TYPES})"
        )

    required_dims = {
        "plate": ["length", "width", "thickness"],
        "bracket": ["length", "width", "thickness"],
        "flange": ["outer_diameter", "inner_diameter", "thickness"],
        "shaft": ["diameter", "length"],
        "housing": ["length", "width", "height", "wall_thickness"],
        "stepped_shaft": [],
        "pillow_block": ["length", "depth", "height", "base_height", "top_width", "seat_radius"],
    }
    needed = required_dims.get(spec.part_type, [])
    for dim in needed:
        if dim not in spec.base_dimensions:
            errors.append(f"base_dimensions thieu truong bat buoc '{dim}' cho part_type='{spec.part_type}'")
        elif not isinstance(spec.base_dimensions[dim], (int, float)) or spec.base_dimensions[dim] <= 0:
            errors.append(f"base_dimensions['{dim}'] phai la so duong")

    if spec.part_type == "stepped_shaft":
        segments = spec.base_dimensions.get("segments")
        if not isinstance(segments, list) or len(segments) == 0:
            errors.append("base_dimensions['segments'] phai la danh sach khong rong cho part_type='stepped_shaft'")
        else:
            for i, seg in enumerate(segments):
                if not isinstance(seg, dict):
                    errors.append(f"segments[{i}] phai la object")
                    continue
                for key in ("diameter", "length"):
                    if key not in seg:
                        errors.append(f"segments[{i}] thieu truong '{key}'")
                    elif not isinstance(seg[key], (int, float)) or seg[key] <= 0:
                        errors.append(f"segments[{i}]['{key}'] phai la so duong")

    if spec.part_type == "pillow_block":
        bh = spec.base_dimensions.get("base_height")
        h = spec.base_dimensions.get("height")
        if isinstance(bh, (int, float)) and isinstance(h, (int, float)) and bh >= h:
            errors.append("pillow_block: base_height phai nho hon height")
        tw = spec.base_dimensions.get("top_width")
        length = spec.base_dimensions.get("length")
        if isinstance(tw, (int, float)) and isinstance(length, (int, float)) and tw >= length:
            errors.append("pillow_block: top_width phai nho hon length")

    for i, feat in enumerate(spec.features):
        errors.extend(feat.validate(i))

    if spec.tolerance <= 0:
        errors.append("tolerance phai > 0")

    return errors


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
    print("\nValidation errors:", errs if errs else "KHONG CO - spec hop le")