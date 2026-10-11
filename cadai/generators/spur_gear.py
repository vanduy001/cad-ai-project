"""
cadai/generators/spur_gear.py
Banh rang thang (spur gear): xap xi profil bang polyline, loc diem trung.
"""
import math


def build(spec) -> str:
    d = spec.base_dimensions
    num_teeth = int(d["num_teeth"])
    module = d["module"]
    thickness = d["thickness"]
    bore_diameter = d.get("bore_diameter", round(module * num_teeth * 0.2, 1))

    pitch_radius = module * num_teeth / 2
    outer_radius = pitch_radius + module
    root_radius = pitch_radius - 1.25 * module
    tooth_angle = 2 * math.pi / num_teeth
    half_tooth = math.pi / num_teeth

    # Tinh toan toan bo diem trong Python (luc build)
    pts = []
    for i in range(num_teeth):
        angle = i * tooth_angle

        # Chan rang trai
        a0 = angle - half_tooth * 0.45
        pts.append((round(root_radius * math.cos(a0), 4),
                    round(root_radius * math.sin(a0), 4)))

        # Suon trai (2 diem trung gian)
        for frac in (0.35, 0.7):
            r = root_radius + (outer_radius - root_radius) * frac
            a = angle - half_tooth * 0.35 * (1 - frac)
            pts.append((round(r * math.cos(a), 4), round(r * math.sin(a), 4)))

        # Dinh rang
        pts.append((round(outer_radius * math.cos(angle), 4),
                    round(outer_radius * math.sin(angle), 4)))

        # Suon phai (2 diem trung gian)
        for frac in (0.7, 0.35):
            r = root_radius + (outer_radius - root_radius) * frac
            a = angle + half_tooth * 0.35 * (1 - frac)
            pts.append((round(r * math.cos(a), 4), round(r * math.sin(a), 4)))

        # Chan rang phai
        a1 = angle + half_tooth * 0.45
        pts.append((round(root_radius * math.cos(a1), 4),
                    round(root_radius * math.sin(a1), 4)))

    # Loc bo diem trung (tranh loi BRep_API)
    filtered = [pts[0]]
    for p in pts[1:]:
        prev = filtered[-1]
        if math.sqrt((p[0]-prev[0])**2 + (p[1]-prev[1])**2) > 0.001:
            filtered.append(p)

    pts_str = ",\n    ".join(f"({x}, {y})" for x, y in filtered)

    lines = [
        "import cadquery as cq",
        f"_thickness = {thickness}",
        f"_bore_d = {bore_diameter}",
        "_pts = [",
        f"    {pts_str}",
        "]",
        "result = (",
        "    cq.Workplane('XY')",
        "    .polyline(_pts, includeCurrent=False)",
        "    .close()",
        "    .extrude(_thickness)",
        ")",
        "if _bore_d > 0:",
        "    result = result.faces('>Z').workplane().hole(_bore_d)",
    ]
    return "\n".join(lines)