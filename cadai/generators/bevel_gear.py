"""
cadai/generators/bevel_gear.py
Banh rang con (bevel gear): xap xi bang hinh non cat bot, profil rang polyline.
"""
import math


def build(spec) -> str:
    d = spec.base_dimensions
    num_teeth = int(d["num_teeth"])
    module = d["module"]
    thickness = d["thickness"]
    cone_angle = d.get("cone_angle", 45)  # do, goc non chia (pitch cone angle)
    bore_diameter = d.get("bore_diameter", round(module * num_teeth * 0.15, 1))

    pitch_radius = module * num_teeth / 2
    outer_radius = pitch_radius + module * math.cos(math.radians(cone_angle))
    root_radius = pitch_radius - 1.25 * module * math.cos(math.radians(cone_angle))
    tooth_angle = 2 * math.pi / num_teeth
    half_tooth = math.pi / num_teeth

    # Tinh profil rang (tuong tu spur_gear, thu nho lai theo cone_angle)
    pts = []
    for i in range(num_teeth):
        angle = i * tooth_angle
        a0 = angle - half_tooth * 0.45
        pts.append((round(root_radius * math.cos(a0), 4),
                    round(root_radius * math.sin(a0), 4)))
        for frac in (0.35, 0.7):
            r = root_radius + (outer_radius - root_radius) * frac
            a = angle - half_tooth * 0.35 * (1 - frac)
            pts.append((round(r * math.cos(a), 4), round(r * math.sin(a), 4)))
        pts.append((round(outer_radius * math.cos(angle), 4),
                    round(outer_radius * math.sin(angle), 4)))
        for frac in (0.7, 0.35):
            r = root_radius + (outer_radius - root_radius) * frac
            a = angle + half_tooth * 0.35 * (1 - frac)
            pts.append((round(r * math.cos(a), 4), round(r * math.sin(a), 4)))
        a1 = angle + half_tooth * 0.45
        pts.append((round(root_radius * math.cos(a1), 4),
                    round(root_radius * math.sin(a1), 4)))

    # Loc diem trung
    filtered = [pts[0]]
    for p in pts[1:]:
        prev = filtered[-1]
        if math.sqrt((p[0]-prev[0])**2 + (p[1]-prev[1])**2) > 0.001:
            filtered.append(p)

    # Tinh toa do hinh non
    cone_rad = math.radians(cone_angle)
    top_r = round(outer_radius * 0.4, 2)  # ban kinh dinh nho hon
    cone_height = round(outer_radius * math.tan(cone_rad) * 0.6, 2)

    pts_str = ",\n    ".join(f"({x}, {y})" for x, y in filtered)

    lines = [
        "import cadquery as cq",
        f"_thickness = {thickness}",
        f"_bore_d = {bore_diameter}",
        f"_top_r = {top_r}",
        f"_cone_h = {cone_height}",
        f"_outer_r = {round(outer_radius, 4)}",
        "_pts = [",
        f"    {pts_str}",
        "]",
        "# Mat rang (profil tuong tu spur gear)",
        "result = (",
        "    cq.Workplane('XY')",
        "    .polyline(_pts, includeCurrent=False)",
        "    .close()",
        "    .extrude(_thickness)",
        ")",
        "# Cat hinh non de tao dang banh rang con",
        "_cone = (",
        "    cq.Workplane('XZ')",
        "    .workplane(offset=0)",
        "    .polyline([",
        "        (0, 0),",
        "        (_outer_r + 2, 0),",
        "        (_top_r, _cone_h),",
        "        (0, _cone_h),",
        "    ]).close()",
        "    .revolve(360, [0,0,0], [0,1,0])",
        ")",
        "result = result.intersect(_cone)",
        "if _bore_d > 0:",
        "    result = result.faces('>Z').workplane().hole(_bore_d)",
    ]
    return "\n".join(lines)