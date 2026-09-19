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


_BASE_BUILDERS = {
    "plate": _build_plate_base,
    "bracket": _build_bracket_base,
    "flange": _build_flange_base,
    "shaft": _build_shaft_base,
    "stepped_shaft": _build_stepped_shaft_base,
    "housing": _build_housing_base,
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
    """Ranh then: cat 1 khoi hop chu nhat vao than truc, tinh theo mat ngoai."""
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
    """Vong lo bat vit bo tri deu quanh tam (dung cho flange)."""
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


_FEATURE_APPLIERS = {
    "hole": _apply_hole,
    "fillet": _apply_fillet,
    "chamfer": _apply_chamfer,
    "pocket": _apply_pocket,
    "boss": _apply_boss,
    "slot": _apply_slot,
    "keyway": _apply_keyway,
    "bolt_circle": _apply_bolt_circle,
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