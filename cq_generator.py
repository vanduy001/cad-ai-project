"""
cq_generator.py
=================
Chuyển PartSpec -> chuỗi code CadQuery (Python).

Chiến lược: TEMPLATE-BASED, không để LLM tự sinh code CadQuery tự do.
Mỗi part_type có 1 hàm "builder" riêng, mỗi feature có 1 hàm "apply" riêng.
Lý do (đã thống nhất trong đề cương):
    - Độ tin cậy cao hơn nhiều so với để LLM sinh code trực tiếp.
    - Dễ viết validation vì biết chính xác cấu trúc code sinh ra.
    - LLM chỉ chịu trách nhiệm ở bước NL -> Spec (đã đủ khó rồi).

Nếu muốn thử hướng (b) "LLM sinh code trực tiếp" để so sánh, viết thêm
llm_code_generator.py riêng, KHÔNG sửa file này.
"""

from __future__ import annotations
from spec_schema import PartSpec, Feature


class CodeGenError(ValueError):
    pass


# ---------------------------------------------------------------------------
# Base builders theo part_type
# ---------------------------------------------------------------------------

def _build_plate_base(spec: PartSpec) -> str:
    d = spec.base_dimensions
    return (
        f"result = cq.Workplane('XY').box({d['length']}, {d['width']}, {d['thickness']})"
    )


def _build_bracket_base(spec: PartSpec) -> str:
    # Bracket đơn giản: hiện tại dựng như 1 block chữ nhật (bản mở rộng sau
    # có thể thêm profile chữ L qua polyline + extrude).
    d = spec.base_dimensions
    return (
        f"result = cq.Workplane('XY').box({d['length']}, {d['width']}, {d['thickness']})"
    )


def _build_flange_base(spec: PartSpec) -> str:
    d = spec.base_dimensions
    return (
        f"result = (cq.Workplane('XY')"
        f".circle({d['outer_diameter']} / 2)"
        f".circle({d['inner_diameter']} / 2)"
        f".extrude({d['thickness']}))"
    )


def _build_shaft_base(spec: PartSpec) -> str:
    d = spec.base_dimensions
    return (
        f"result = cq.Workplane('XY').circle({d['diameter']} / 2).extrude({d['length']})"
    )


def _build_housing_base(spec: PartSpec) -> str:
    d = spec.base_dimensions
    wt = d["wall_thickness"]
    return (
        f"result = (cq.Workplane('XY')"
        f".box({d['length']}, {d['width']}, {d['height']})"
        f".faces('>Z').shell(-{wt}))"
    )


_BASE_BUILDERS = {
    "plate": _build_plate_base,
    "bracket": _build_bracket_base,
    "flange": _build_flange_base,
    "shaft": _build_shaft_base,
    "housing": _build_housing_base,
}


# ---------------------------------------------------------------------------
# Feature appliers
# ---------------------------------------------------------------------------

def _apply_hole(feat: Feature, spec: PartSpec, idx: int) -> str:
    p = feat.params
    diameter = p["diameter"]
    positions = p["positions"]  # list [x, y] tính từ tâm mặt phẳng XY
    depth = p.get("depth", "through")

    lines = [f"pts_{idx} = {positions}"]
    if depth == "through":
        lines.append(
            f"result = (result.faces('>Z').workplane()"
            f".pushPoints(pts_{idx}).hole({diameter}))"
        )
    else:
        lines.append(
            f"result = (result.faces('>Z').workplane()"
            f".pushPoints(pts_{idx}).hole({diameter}, depth={depth}))"
        )
    return "\n".join(lines)


def _apply_fillet(feat: Feature, spec: PartSpec, idx: int) -> str:
    p = feat.params
    radius = p["radius"]
    edges = p.get("edges", "all")

    selector_map = {
        "all": "'|Z'",
        "top": "'>Z'",
        "bottom": "'<Z'",
        "corners": "'|Z'",  # dùng chung selector cạnh đứng; đủ cho block đơn giản
    }
    selector = selector_map.get(edges, "'|Z'")
    return f"result = result.edges({selector}).fillet({radius})"


def _apply_chamfer(feat: Feature, spec: PartSpec, idx: int) -> str:
    p = feat.params
    distance = p["distance"]
    edges = p.get("edges", "all")
    selector_map = {"all": "'|Z'", "top": "'>Z'", "bottom": "'<Z'"}
    selector = selector_map.get(edges, "'|Z'")
    return f"result = result.edges({selector}).chamfer({distance})"


def _apply_pocket(feat: Feature, spec: PartSpec, idx: int) -> str:
    p = feat.params
    length, width, depth = p["length"], p["width"], p["depth"]
    x, y = p["position"]
    return (
        f"result = (result.faces('>Z').workplane()"
        f".center({x}, {y})"
        f".rect({length}, {width})"
        f".cutBlind(-{depth}))"
    )


def _apply_boss(feat: Feature, spec: PartSpec, idx: int) -> str:
    p = feat.params
    diameter, height = p["diameter"], p["height"]
    x, y = p["position"]
    return (
        f"result = (result.faces('>Z').workplane()"
        f".center({x}, {y})"
        f".circle({diameter} / 2)"
        f".extrude({height}))"
    )


def _apply_slot(feat: Feature, spec: PartSpec, idx: int) -> str:
    p = feat.params
    length, width, depth = p["length"], p["width"], p.get("depth", "through")
    x, y = p["position"]
    angle = p.get("angle", 0)

    setup = (
        f"result = (result.faces('>Z').workplane()"
        f".center({x}, {y})"
        f".transformed(rotate=(0, 0, {angle}))"
        f".slot2D({length}, {width})"
    )
    if depth == "through":
        return setup + ".cutThruAll())"
    return setup + f".cutBlind(-{depth}))"


_FEATURE_APPLIERS = {
    "hole": _apply_hole,
    "fillet": _apply_fillet,
    "chamfer": _apply_chamfer,
    "pocket": _apply_pocket,
    "boss": _apply_boss,
    "slot": _apply_slot,
}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def generate_cadquery_code(spec: PartSpec) -> str:
    """Sinh code CadQuery hoàn chỉnh (dạng chuỗi) từ PartSpec.

    Code sinh ra luôn gán solid cuối cùng vào biến `result`, để executor
    có thể exec() rồi lấy `result` ra export STEP / kiểm tra hình học.
    """
    if spec.part_type not in _BASE_BUILDERS:
        raise CodeGenError(f"Chưa hỗ trợ sinh code cho part_type='{spec.part_type}'")

    lines = ["import cadquery as cq", "", _BASE_BUILDERS[spec.part_type](spec)]

    for i, feat in enumerate(spec.features):
        if feat.type not in _FEATURE_APPLIERS:
            raise CodeGenError(f"Chưa hỗ trợ sinh code cho feature type='{feat.type}'")
        lines.append(_FEATURE_APPLIERS[feat.type](feat, spec, i))

    return "\n".join(lines)


if __name__ == "__main__":
    from spec_schema import example_plate_spec

    code = generate_cadquery_code(example_plate_spec())
    print(code)
