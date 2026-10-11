"""
cadai/generators/sprocket.py
Dia xich (sprocket): rang dang tron, tinh theo buoc xich (pitch).
"""
import math


def build(spec) -> str:
    d = spec.base_dimensions
    num_teeth = int(d["num_teeth"])
    pitch = d["pitch"]          # buoc xich (mm), vd: 12.7 (1/2 inch), 15.875 (5/8 inch)
    thickness = d["thickness"]
    bore_diameter = d.get("bore_diameter", 0)
    roller_diameter = d.get("roller_diameter", round(pitch * 0.625, 2))  # ~ 5/8 * pitch

    # Tinh toan theo tieu chuan dia xich
    pitch_radius = pitch / (2 * math.sin(math.pi / num_teeth))
    outer_radius = pitch_radius + roller_diameter / 2
    root_radius = pitch_radius - roller_diameter / 2 - 0.5  # khe ho nho

    tooth_angle = 2 * math.pi / num_teeth
    half_tooth = math.pi / num_teeth

    # Profil rang dia xich: dinh tron (trang circular arc)
    pts = []
    for i in range(num_teeth):
        angle = i * tooth_angle

        # Day rang (cung lom theo duong kinh con lan)
        valley_steps = 4
        for j in range(valley_steps + 1):
            a = angle - half_tooth + tooth_angle * j / valley_steps
            pts.append((round(root_radius * math.cos(a), 4),
                        round(root_radius * math.sin(a), 4)))

        # Dinh rang (cung tron nho)
        tip_r = outer_radius
        tip_steps = 3
        tip_start = angle - half_tooth * 0.3
        tip_end = angle + half_tooth * 0.3
        for j in range(1, tip_steps):
            a = tip_start + (tip_end - tip_start) * j / tip_steps
            pts.append((round(tip_r * math.cos(a), 4),
                        round(tip_r * math.sin(a), 4)))

    # Loc diem trung
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