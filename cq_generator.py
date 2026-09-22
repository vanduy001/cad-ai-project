"""
cq_generator.py
=================
Chuyen PartSpec -> chuoi code CadQuery (Python). Template-based.
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
    return f"result = cq.Workplane('XY').box({d['length']}, {d['width']}, {d['thickness']})"


def _build_bracket_base(spec: PartSpec) -> str:
    d = spec.base_dimensions
    if "leg_height" in d and "leg_thickness" in d:
        length = d["length"]
        base_thickness = d["thickness"]
        leg_height = d["leg_height"]
        leg_thickness = d["leg_thickness"]
        width = d["width"]
        lines = [
            f"_profile = (cq.Workplane('XZ')",
            f"    .moveTo(0, 0)",
            f"    .lineTo({length}, 0)",
            f"    .lineTo({length}, {base_thickness})",
            f"    .lineTo({leg_thickness}, {base_thickness})",
            f"    .lineTo({leg_thickness}, {leg_height})",
            f"    .lineTo(0, {leg_height})",
            f"    .close())",
            f"result = _profile.extrude({width})",
        ]
        return "\n".join(lines)
    return f"result = cq.Workplane('XY').box({d['length']}, {d['width']}, {d['thickness']})"


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
    return f"result = cq.Workplane('XY').circle({d['diameter']} / 2).extrude({d['length']})"


def _build_stepped_shaft_base(spec: PartSpec) -> str:
    segments = spec.base_dimensions["segments"]
    lines = [
        f"_segments = {segments!r}",
        "result = None",
        "_z = 0",
        "for _seg in _segments:",
        "    _d = _seg['diameter']",
        "    _l = _seg['length']",
        "    _piece = cq.Workplane('XY').workplane(offset=_z).circle(_d / 2).extrude(_l)",
        "    result = _piece if result is None else result.union(_piece)",
        "    _z += _l",
    ]
    return "\n".join(lines)


def _build_housing_base(spec: PartSpec) -> str:
    d = spec.base_dimensions
    wt = d["wall_thickness"]
    return (
        f"result = (cq.Workplane('XY')"
        f".box({d['length']}, {d['width']}, {d['height']})"
        f".faces('>Z').shell(-{wt}))"
    )


def _build_pillow_block_base(spec: PartSpec) -> str:
    """Goi do truc: khoi hop chu nhat, vat 2 ben (nhin tu truoc), co ranh
    cong o tren de dat truc. Toa do: X = length (ngang), Y = depth (sau,
    truc cua ranh cong), Z = height (cao, day tai Z=0)."""
    d = spec.base_dimensions
    length = d["length"]
    depth = d["depth"]
    height = d["height"]
    base_height = d["base_height"]
    top_width = d["top_width"]
    seat_radius = d["seat_radius"]
    half_l = length / 2
    half_w = top_width / 2

    lines = [
        f"result = cq.Workplane('XY').rect({length}, {depth}).extrude({height})",
        f"_vat_l = (cq.Workplane('XZ')"
        f".moveTo({-half_l}, {base_height}).lineTo({-half_w}, {height}).lineTo({-half_l}, {height})"
        f".close().extrude({depth} + 20, both=True))",
        f"result = result.cut(_vat_l)",
        f"_vat_r = (cq.Workplane('XZ')"
        f".moveTo({half_l}, {base_height}).lineTo({half_w}, {height}).lineTo({half_l}, {height})"
        f".close().extrude({depth} + 20, both=True))",
        f"result = result.cut(_vat_r)",
        f"_seat = (cq.Workplane('XZ').center(0, {height}).circle({seat_radius})"
        f".extrude({depth} + 20, both=True))",
        f"result = result.cut(_seat)",
    ]
    return "\n".join(lines)


_BASE_BUILDERS = {
    "plate": _build_plate_base,
    "bracket": _build_bracket_base,
    "flange": _build_flange_base,
    "shaft": _build_shaft_base,
    "stepped_shaft": _build_stepped_shaft_base,
    "housing": _build_housing_base,
    "pillow_block": _build_pillow_block_base,
}


# ---------------------------------------------------------------------------
# Feature appliers
# ---------------------------------------------------------------------------

def _apply_hole(feat: Feature, spec: PartSpec, idx: int) -> str:
    p = feat.params
    diameter = p["diameter"]
    positions = p["positions"]
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
    selector_map = {"all": "'|Z'", "top": "'>Z'", "bottom": "'<Z'", "corners": "'|Z'"}
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


def _apply_keyway(feat: Feature, spec: PartSpec, idx: int) -> str:
    p = feat.params
    width = p["width"]
    depth = p["depth"]
    length = p["length"]
    z_start = p.get("z_start", 0)
    shaft_d = p["shaft_diameter"]
    r = shaft_d / 2
    lines = [
        f"_r_{idx} = {r}",
        f"_bottom_{idx} = _r_{idx} - {depth}",
        f"_top_{idx} = _r_{idx} + 5",
        f"_h_{idx} = _top_{idx} - _bottom_{idx}",
        f"_cy_{idx} = (_bottom_{idx} + _top_{idx}) / 2",
        f"_cz_{idx} = {z_start} + {length} / 2",
        f"_cutter_{idx} = cq.Workplane('XY').box({width}, _h_{idx}, {length})",
        f"_cutter_{idx} = _cutter_{idx}.translate((0, _cy_{idx}, _cz_{idx}))",
        f"result = result.cut(_cutter_{idx})",
    ]
    return "\n".join(lines)


def _apply_bolt_circle(feat: Feature, spec: PartSpec, idx: int) -> str:
    p = feat.params
    count = p["count"]
    hole_d = p["hole_diameter"]
    pcd = p["pcd"]
    lines = [
        f"_positions_{idx} = []",
        f"for _i in range({count}):",
        f"    _angle = 2 * math.pi * _i / {count}",
        f"    _x = ({pcd} / 2) * math.cos(_angle)",
        f"    _y = ({pcd} / 2) * math.sin(_angle)",
        f"    _positions_{idx}.append((_x, _y))",
        f"result = (result.faces('>Z').workplane().pushPoints(_positions_{idx}).hole({hole_d}))",
    ]
    return "\n".join(lines)


def _apply_radial_hole(feat: Feature, spec: PartSpec, idx: int) -> str:
    p = feat.params
    diameter = p["diameter"]
    height_from_base = p["height_from_base"]
    outer_extent = p.get("outer_extent", 200)
    lines = [
        f"_cutter_{idx} = (cq.Workplane('YZ')",
        f"    .move(0, {height_from_base})",
        f"    .circle({diameter} / 2)",
        f"    .extrude({outer_extent}, both=True))",
        f"result = result.cut(_cutter_{idx})",
    ]
    return "\n".join(lines)


def _apply_counterbore(feat: Feature, spec: PartSpec, idx: int) -> str:
    p = feat.params
    hole_d = p["diameter"]
    cbore_d = p["cbore_diameter"]
    cbore_depth = p["cbore_depth"]
    positions = p["positions"]
    lines = [
        f"pts_{idx} = {positions}",
        f"result = (result.faces('>Z').workplane()"
        f".pushPoints(pts_{idx})"
        f".cboreHole({hole_d}, {cbore_d}, {cbore_depth}))",
    ]
    return "\n".join(lines)


def _apply_side_lugs(feat: Feature, spec: PartSpec, idx: int) -> str:
    """Them 2 tai bat bu-long o 2 dau khoi (dung cho pillow_block)."""
    p = feat.params
    lug_length = p["lug_length"]
    lug_thickness = p.get("lug_thickness", spec.base_dimensions.get("base_height", 10))
    length = spec.base_dimensions["length"]
    depth = spec.base_dimensions["depth"]
    half_l = length / 2
    half_d = depth / 2
    lines = [
        f"_lug_r_{idx} = (cq.Workplane('XY')"
        f".moveTo({half_l}, {-half_d}).lineTo({half_l + lug_length}, {-half_d})"
        f".lineTo({half_l + lug_length}, {half_d}).lineTo({half_l}, {half_d})"
        f".close().extrude({lug_thickness}))",
        f"result = result.union(_lug_r_{idx})",
        f"_lug_l_{idx} = (cq.Workplane('XY')"
        f".moveTo({-half_l}, {-half_d}).lineTo({-half_l - lug_length}, {-half_d})"
        f".lineTo({-half_l - lug_length}, {half_d}).lineTo({-half_l}, {half_d})"
        f".close().extrude({lug_thickness}))",
        f"result = result.union(_lug_l_{idx})",
    ]
    return "\n".join(lines)


_FEATURE_APPLIERS = {
    "hole": _apply_hole,
    "fillet": _apply_fillet,
    "chamfer": _apply_chamfer,
    "pocket": _apply_pocket,
    "boss": _apply_boss,
    "slot": _apply_slot,
    "keyway": _apply_keyway,
    "bolt_circle": _apply_bolt_circle,
    "radial_hole": _apply_radial_hole,
    "counterbore": _apply_counterbore,
    "side_lugs": _apply_side_lugs,
}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def generate_cadquery_code(spec: PartSpec) -> str:
    if spec.part_type not in _BASE_BUILDERS:
        raise CodeGenError(f"Chua ho tro sinh code cho part_type='{spec.part_type}'")

    lines = ["import cadquery as cq", "import math", "", _BASE_BUILDERS[spec.part_type](spec)]

    for i, feat in enumerate(spec.features):
        if feat.type not in _FEATURE_APPLIERS:
            raise CodeGenError(f"Chua ho tro sinh code cho feature type='{feat.type}'")
        lines.append(_FEATURE_APPLIERS[feat.type](feat, spec, i))

    return "\n".join(lines)


if __name__ == "__main__":
    from spec_schema import example_plate_spec

    code = generate_cadquery_code(example_plate_spec())
    print(code)