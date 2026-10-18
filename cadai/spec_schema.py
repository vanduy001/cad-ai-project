"""
spec_schema.py
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional, Any
import json
import re

SUPPORTED_PART_TYPES = (
    "plate", "bracket", "flange", "shaft", "housing", "stepped_shaft", "pillow_block",
    "bolt", "nut",
    "washer", "pin", "flat_plate", "countersunk_screw",
    "spur_gear", "pulley", "cam", "coupling",
    "key", "retaining_ring", "bushing", "end_cap",
    "bevel_gear", "sprocket", "spring", "bearing_housing",
    "rack", "worm", "piston", "connecting_rod",
)
SUPPORTED_FEATURE_TYPES = (
    "hole", "fillet", "chamfer", "pocket", "boss", "slot",
    "keyway", "bolt_circle", "radial_hole", "counterbore", "side_lugs", "thread",
    "undercut",
)
# Hinh dang cac doan cua stepped_shaft
SEGMENT_SHAPES = ("cylinder", "taper", "spline", "eccentric")

# ---- Dung sai (tolerances) va do nham (surface_finish) ----
# Cap dung sai ISO: chu hoa = lo (H7, K7), chu thuong = truc (g6, h6, k6); so = cap chinh xac IT1..IT18
_ISO_FIT_RE = re.compile(r"^([A-Za-z]{1,2})(\d{1,2})$")
_SYMMETRIC_RE = re.compile(r"^(?:±|\+/-|\+-)\s*(\d+(?:\.\d+)?)$")
_ASYMMETRIC_RE = re.compile(r"^([+-]\s*\d+(?:\.\d+)?)\s*/\s*([+-]\s*\d+(?:\.\d+)?)$")
_STEPPED_KEY_RE = re.compile(r"^segments\[(\d+)\]\.(diameter|length)$")
# Do nham Ra thuong dung (um): 0.4, 0.8, 1.6, 3.2, 6.3, 12.5, 25 ... (chi canh bao khoang hop le, khong ep dung day so)
MAX_RA = 100.0


class SpecValidationError(ValueError):
    pass


def _is_num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


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
    # Dung sai theo tung kich thuoc: {"diameter": "g6", "length": "±0.1", "width": "+0.02/-0.01"}
    tolerances: dict[str, str] = field(default_factory=dict)
    # Do nham be mat Ra (um): {"default": 3.2, "bore": 1.6, "outer": 0.8}
    surface_finish: dict[str, float] = field(default_factory=dict)

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
            tolerances=d.get("tolerances") or {},
            surface_finish=d.get("surface_finish") or {},
        )

    @staticmethod
    def from_json(s: str) -> "PartSpec":
        return PartSpec.from_dict(json.loads(s))


def _check_tolerance_value(key: str, val: Any) -> list[str]:
    """Kiem tra 1 gia tri dung sai: cap ISO (H7, g6), doi xung (±0.1) hoac khong doi xung (+0.02/-0.01)."""
    if not isinstance(val, str) or not val.strip():
        return [f"tolerances['{key}'] phai la chuoi khong rong (vi du 'H7', '±0.1', '+0.02/-0.01')"]
    s = val.strip()

    m = _SYMMETRIC_RE.match(s)
    if m:
        if float(m.group(1)) <= 0:
            return [f"tolerances['{key}']='{val}': gia tri sai lech phai > 0"]
        return []

    m = _ASYMMETRIC_RE.match(s)
    if m:
        upper = float(m.group(1).replace(" ", ""))
        lower = float(m.group(2).replace(" ", ""))
        if upper < lower:
            return [f"tolerances['{key}']='{val}': sai lech tren phai >= sai lech duoi"]
        return []

    m = _ISO_FIT_RE.match(s)
    if m:
        letters, grade = m.group(1), int(m.group(2))
        if not (1 <= grade <= 18):
            return [f"tolerances['{key}']='{val}': cap chinh xac IT phai tu 1 den 18"]
        # 1 hoac 2 chu cai cung kieu (cung hoa hoac cung thuong), tru JS/js, CD/cd, EF/ef, FG/fg
        if not (letters.isupper() or letters.islower()):
            return [f"tolerances['{key}']='{val}': chu cai phai viet hoa het (lo) hoac viet thuong het (truc)"]
        return []

    return [
        f"tolerances['{key}']='{val}' khong hop le "
        f"(chap nhan: cap ISO nhu 'H7', 'g6'; doi xung '±0.1'; khong doi xung '+0.02/-0.01')"
    ]


def _validate_tolerances_and_finish(spec: PartSpec) -> list[str]:
    errs: list[str] = []

    # ---- dung sai ----
    if not isinstance(spec.tolerances, dict):
        errs.append("tolerances phai la object (ten kich thuoc -> gia tri dung sai)")
    else:
        for key, val in spec.tolerances.items():
            sm = _STEPPED_KEY_RE.match(key)
            if sm:
                if spec.part_type != "stepped_shaft":
                    errs.append(f"tolerances['{key}'] chi dung cho stepped_shaft")
                else:
                    segs = spec.base_dimensions.get("segments")
                    idx = int(sm.group(1))
                    if not isinstance(segs, list) or idx >= len(segs):
                        errs.append(f"tolerances['{key}']: khong co segments[{idx}]")
            elif key not in spec.base_dimensions:
                errs.append(
                    f"tolerances['{key}']: khong co kich thuoc nay trong base_dimensions "
                    f"({list(spec.base_dimensions.keys())})"
                )
            errs.extend(_check_tolerance_value(key, val))

    # ---- do nham ----
    if not isinstance(spec.surface_finish, dict):
        errs.append("surface_finish phai la object (ten be mat -> Ra tinh bang um)")
    else:
        for name, ra in spec.surface_finish.items():
            if not isinstance(name, str) or not name.strip():
                errs.append("surface_finish: ten be mat phai la chuoi khong rong")
            if isinstance(ra, bool) or not isinstance(ra, (int, float)) or ra <= 0 or ra > MAX_RA:
                errs.append(f"surface_finish['{name}']={ra!r} phai la so Ra > 0 va <= {MAX_RA:g} (um)")

    return errs


def _validate_segment_shape(i: int, seg: dict) -> list[str]:
    """Kiem tra hinh dang rieng cua tung doan stepped_shaft (taper / spline / eccentric)."""
    errs: list[str] = []
    shape = seg.get("shape", "cylinder")
    if shape not in SEGMENT_SHAPES:
        return [f"segments[{i}].shape='{shape}' khong hop le (chi chap nhan {SEGMENT_SHAPES})"]

    d = seg.get("diameter")

    if shape == "taper":
        ed = seg.get("end_diameter")
        if not _is_num(ed) or ed <= 0:
            errs.append(f"segments[{i}] (taper) can 'end_diameter' la so duong")

    elif shape == "eccentric":
        off = seg.get("offset")
        if not _is_num(off) or off <= 0:
            errs.append(f"segments[{i}] (eccentric) can 'offset' la so duong (do lech tam, mm)")

    elif shape == "spline":
        if "spline_count" in seg:
            n = seg["spline_count"]
            if not _is_num(n) or int(n) != n or n < 2:
                errs.append(f"segments[{i}]['spline_count'] phai la so nguyen >= 2")
        for key in ("spline_width", "spline_depth"):
            if key in seg and (not _is_num(seg[key]) or seg[key] <= 0):
                errs.append(f"segments[{i}]['{key}'] phai la so duong")
        sd = seg.get("spline_depth")
        if _is_num(sd) and _is_num(d) and sd >= d / 2:
            errs.append(f"segments[{i}]: spline_depth phai nho hon ban kinh doan (diameter/2)")

    return errs


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
        "bolt": ["diameter", "length"],
        "nut": ["diameter", "height"],
        "washer": ["outer_diameter", "inner_diameter", "thickness"],
        "pin": ["diameter", "length"],
        "flat_plate": ["length", "width", "thickness"],
        "countersunk_screw": ["diameter", "length"],
        "spur_gear": ["num_teeth", "module", "thickness"],
        "pulley": ["outer_diameter", "bore_diameter", "width"],
        "cam": ["base_radius", "lift", "thickness"],
        "coupling": ["outer_diameter", "bore_diameter", "total_length"],
        "key": ["length", "width", "height"],
        "retaining_ring": ["outer_diameter", "inner_diameter", "thickness"],
        "bushing": ["outer_diameter", "inner_diameter", "length"],
        "end_cap": ["outer_diameter", "bore_diameter", "thickness"],
        "bevel_gear": ["num_teeth", "module", "thickness"],
        "sprocket": ["num_teeth", "pitch", "thickness"],
        "spring": ["coil_diameter", "wire_diameter", "num_coils", "free_length"],
        "bearing_housing": ["outer_diameter", "bearing_diameter", "length"],
        "rack": ["module", "num_teeth", "thickness"],
        "worm": ["diameter", "length"],
        "piston": ["diameter", "length"],
        "connecting_rod": ["length", "big_end_diameter", "small_end_diameter", "thickness"],
    }
    needed = required_dims.get(spec.part_type, [])
    for dim in needed:
        if dim not in spec.base_dimensions:
            errors.append(f"base_dimensions thieu truong bat buoc '{dim}' cho part_type='{spec.part_type}'")
        elif spec.part_type not in ("spur_gear", "bevel_gear") and (
            not isinstance(spec.base_dimensions[dim], (int, float)) or spec.base_dimensions[dim] <= 0
        ):
            errors.append(f"base_dimensions['{dim}'] phai la so duong")

    if spec.part_type == "spur_gear":
        nt = spec.base_dimensions.get("num_teeth")
        if not isinstance(nt, (int, float)) or nt < 6:
            errors.append("spur_gear: num_teeth phai >= 6")
        m = spec.base_dimensions.get("module")
        if not isinstance(m, (int, float)) or m <= 0:
            errors.append("spur_gear: module phai la so duong")

    if spec.part_type == "bevel_gear":
        nt = spec.base_dimensions.get("num_teeth")
        if not isinstance(nt, (int, float)) or nt < 6:
            errors.append("bevel_gear: num_teeth phai >= 6")
        m = spec.base_dimensions.get("module")
        if not isinstance(m, (int, float)) or m <= 0:
            errors.append("bevel_gear: module phai la so duong")

    if spec.part_type == "rack":
        nt = spec.base_dimensions.get("num_teeth")
        if not isinstance(nt, (int, float)) or nt < 2:
            errors.append("rack: num_teeth phai >= 2")
        m = spec.base_dimensions.get("module")
        if not isinstance(m, (int, float)) or m <= 0:
            errors.append("rack: module phai la so duong")

    if spec.part_type == "sprocket":
        nt = spec.base_dimensions.get("num_teeth")
        if not isinstance(nt, (int, float)) or nt < 6:
            errors.append("sprocket: num_teeth phai >= 6")

    if spec.part_type == "spring":
        cd = spec.base_dimensions.get("coil_diameter")
        wd = spec.base_dimensions.get("wire_diameter")
        if isinstance(cd, (int, float)) and isinstance(wd, (int, float)) and wd >= cd / 2:
            errors.append("spring: wire_diameter phai nho hon ban kinh vong xoan (coil_diameter/2)")

    if spec.part_type == "bearing_housing":
        od = spec.base_dimensions.get("outer_diameter")
        bd = spec.base_dimensions.get("bearing_diameter")
        if isinstance(od, (int, float)) and isinstance(bd, (int, float)) and bd >= od:
            errors.append("bearing_housing: bearing_diameter phai nho hon outer_diameter")

    if spec.part_type == "connecting_rod":
        bed = spec.base_dimensions.get("big_end_diameter")
        sed = spec.base_dimensions.get("small_end_diameter")
        ln = spec.base_dimensions.get("length")
        if isinstance(bed, (int, float)) and isinstance(ln, (int, float)) and bed >= ln:
            errors.append("connecting_rod: big_end_diameter phai nho hon length")
        if isinstance(sed, (int, float)) and isinstance(bed, (int, float)) and sed >= bed:
            errors.append("connecting_rod: small_end_diameter phai nho hon big_end_diameter")

    if spec.part_type == "stepped_shaft":
        segments = spec.base_dimensions.get("segments")
        if not isinstance(segments, list) or len(segments) == 0:
            errors.append("base_dimensions['segments'] phai la danh sach khong rong")
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
                errors.extend(_validate_segment_shape(i, seg))

    if spec.part_type == "pillow_block":
        bh = spec.base_dimensions.get("base_height")
        h = spec.base_dimensions.get("height")
        if isinstance(bh, (int, float)) and isinstance(h, (int, float)) and bh >= h:
            errors.append("pillow_block: base_height phai nho hon height")

    if spec.part_type == "nut":
        dia = spec.base_dimensions.get("diameter")
        width = spec.base_dimensions.get("width")
        if isinstance(dia, (int, float)) and isinstance(width, (int, float)) and width <= dia:
            errors.append("nut: width phai lon hon diameter")

    if spec.part_type == "washer":
        od = spec.base_dimensions.get("outer_diameter")
        id_ = spec.base_dimensions.get("inner_diameter")
        if isinstance(od, (int, float)) and isinstance(id_, (int, float)) and id_ >= od:
            errors.append("washer: inner_diameter phai nho hon outer_diameter")

    if spec.part_type == "countersunk_screw":
        dia = spec.base_dimensions.get("diameter")
        hd = spec.base_dimensions.get("head_diameter")
        if isinstance(dia, (int, float)) and isinstance(hd, (int, float)) and hd <= dia:
            errors.append("countersunk_screw: head_diameter phai lon hon diameter")

    if spec.part_type == "pulley":
        od = spec.base_dimensions.get("outer_diameter")
        bd = spec.base_dimensions.get("bore_diameter")
        if isinstance(od, (int, float)) and isinstance(bd, (int, float)) and bd >= od:
            errors.append("pulley: bore_diameter phai nho hon outer_diameter")

    if spec.part_type == "coupling":
        od = spec.base_dimensions.get("outer_diameter")
        bd = spec.base_dimensions.get("bore_diameter")
        if isinstance(od, (int, float)) and isinstance(bd, (int, float)) and bd >= od:
            errors.append("coupling: bore_diameter phai nho hon outer_diameter")

    if spec.part_type == "retaining_ring":
        od = spec.base_dimensions.get("outer_diameter")
        id_ = spec.base_dimensions.get("inner_diameter")
        if isinstance(od, (int, float)) and isinstance(id_, (int, float)) and id_ >= od:
            errors.append("retaining_ring: inner_diameter phai nho hon outer_diameter")

    if spec.part_type == "bushing":
        od = spec.base_dimensions.get("outer_diameter")
        id_ = spec.base_dimensions.get("inner_diameter")
        if isinstance(od, (int, float)) and isinstance(id_, (int, float)) and id_ >= od:
            errors.append("bushing: inner_diameter phai nho hon outer_diameter")

    if spec.part_type == "end_cap":
        od = spec.base_dimensions.get("outer_diameter")
        bd = spec.base_dimensions.get("bore_diameter")
        if isinstance(od, (int, float)) and isinstance(bd, (int, float)) and bd >= od:
            errors.append("end_cap: bore_diameter phai nho hon outer_diameter")

    for i, feat in enumerate(spec.features):
        errors.extend(feat.validate(i))

    errors.extend(_validate_tolerances_and_finish(spec))

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
                params={"diameter": 6, "depth": "through", "positions": [[10, 10], [90, 10], [10, 50], [90, 50]]},
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