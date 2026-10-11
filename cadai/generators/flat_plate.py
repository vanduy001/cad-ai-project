"""
cadai/generators/flat_plate.py
Tam phang (flat plate): hop chu nhat, tuy chon co cac lo goc.
"""
import cadquery as cq


def build(spec) -> str:
    d = spec.base_dimensions
    length = d["length"]
    width = d["width"]
    thickness = d["thickness"]
    hole_diameter = d.get("hole_diameter", 0)
    hole_margin = d.get("hole_margin", round(min(length, width) * 0.08, 1))

    lines = [
        f"result = cq.Workplane('XY').box({length}, {width}, {thickness})",
    ]
    if hole_diameter and hole_diameter > 0:
        lines += [
            f"_margin = {hole_margin}",
            f"_hx = {length}/2 - _margin",
            f"_hy = {width}/2 - _margin",
            f"result = result.faces('>Z').workplane().pushPoints([",
            f"    (_hx, _hy), (-_hx, _hy), (_hx, -_hy), (-_hx, -_hy)",
            f"]).hole({hole_diameter})",
        ]
    return "\n".join(lines)