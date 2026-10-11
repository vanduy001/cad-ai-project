"""
cadai/generators/retaining_ring.py
Vong ham truc (circlip / retaining ring): vong C mo mot khe.
"""
import math


def build(spec) -> str:
    d = spec.base_dimensions
    outer_diameter = d["outer_diameter"]
    inner_diameter = d["inner_diameter"]
    thickness = d["thickness"]
    gap_angle = d.get("gap_angle", 30)  # do, do mo cua khe

    outer_r = outer_diameter / 2
    inner_r = inner_diameter / 2
    half_gap = gap_angle / 2  # do

    # Tinh cac diem profil vong C
    # Vong ngoai: tu (half_gap) den (360 - half_gap) tinh theo do
    steps = 48
    start_deg = half_gap
    end_deg = 360 - half_gap
    span = end_deg - start_deg

    outer_pts = []
    for i in range(steps + 1):
        deg = start_deg + span * i / steps
        rad = math.radians(deg)
        outer_pts.append((round(outer_r * math.cos(rad), 4),
                          round(outer_r * math.sin(rad), 4)))

    inner_pts = []
    for i in range(steps + 1):
        deg = end_deg - span * i / steps  # nguoc chieu
        rad = math.radians(deg)
        inner_pts.append((round(inner_r * math.cos(rad), 4),
                          round(inner_r * math.sin(rad), 4)))

    all_pts = outer_pts + inner_pts
    pts_str = ",\n    ".join(f"({x}, {y})" for x, y in all_pts)

    lines = [
        "import cadquery as cq",
        f"_thickness = {thickness}",
        "_pts = [",
        f"    {pts_str}",
        "]",
        "result = (",
        "    cq.Workplane('XY')",
        "    .polyline(_pts, includeCurrent=False)",
        "    .close()",
        "    .extrude(_thickness)",
        ")",
    ]
    return "\n".join(lines)