"""
cadai/generators/rack.py
Thanh rang thang (rack): an khop voi spur gear, rang hinh thang.
"""
import math


def build(spec) -> str:
    d = spec.base_dimensions
    module = d["module"]
    num_teeth = int(d["num_teeth"])
    thickness = d["thickness"]
    height = d.get("height", round(module * 3, 1))      # chieu cao thanh (tu day den dinh rang)
    width = d.get("width", round(module * 2.5, 1))      # chieu rong (chieu sau)
    pressure_angle = d.get("pressure_angle", 20)

    pitch = math.pi * module                            # buoc rang
    addendum = module
    dedendum = 1.25 * module
    tooth_height = addendum + dedendum

    pa_rad = math.radians(pressure_angle)
    tooth_top_half = addendum * math.tan(pa_rad)       # do thu lai o dinh rang
    tooth_bot_half = dedendum * math.tan(pa_rad)       # do thu lai o day rang

    # Tinh toa do toan bo profil rang
    pts = []
    total_length = pitch * num_teeth

    for i in range(num_teeth):
        x_base = i * pitch
        # Day rang trai
        x0 = x_base
        # Suon trai (tu day len dinh)
        pts.append((round(x0 + tooth_bot_half, 4), 0))
        pts.append((round(x0 + pitch/2 - tooth_top_half, 4), tooth_height))
        # Dinh rang
        pts.append((round(x0 + pitch/2 + tooth_top_half, 4), tooth_height))
        # Suon phai (tu dinh xuong day)
        pts.append((round(x0 + pitch - tooth_bot_half, 4), 0))

    # Dong profil: them 4 goc hop
    all_pts = [(0, 0)] + pts + [
        (total_length, 0),
        (total_length, -height + tooth_height),
        (0, -height + tooth_height),
    ]

    pts_str = ",\n    ".join(f"({x}, {y})" for x, y in all_pts)

    lines = [
        "import cadquery as cq",
        f"_w = {width}",
        f"_thickness = {thickness}",
        "_pts = [",
        f"    {pts_str}",
        "]",
        "result = (",
        "    cq.Workplane('XY')",
        "    .polyline(_pts, includeCurrent=False)",
        "    .close()",
        "    .extrude(_w)",
        ")",
    ]
    return "\n".join(lines)