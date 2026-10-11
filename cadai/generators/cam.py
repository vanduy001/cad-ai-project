"""
cadai/generators/cam.py
Cam (cam): dia tru lech tam, profil ellipse hoac tron lech.
"""
import math


def build(spec) -> str:
    d = spec.base_dimensions
    base_radius = d["base_radius"]
    lift = d["lift"]              # hanh trinh cam (do lech tam)
    thickness = d["thickness"]
    bore_diameter = d.get("bore_diameter", round(base_radius * 0.4, 1))
    cam_type = d.get("cam_type", "eccentric")  # eccentric | ellipse

    if cam_type == "ellipse":
        r_major = base_radius + lift
        r_minor = base_radius
        lines = [
            "import cadquery as cq",
            f"_r_major = {r_major}",
            f"_r_minor = {r_minor}",
            f"_thickness = {thickness}",
            f"_bore = {bore_diameter}",
            "",
            "# Ellipse: xap xi bang spline 12 diem",
            "import math",
            "_pts = [(_r_major * math.cos(a * math.pi/6), _r_minor * math.sin(a * math.pi/6))",
            "        for a in range(12)]",
            "result = cq.Workplane('XY').spline(_pts, periodic=True).close().extrude(_thickness)",
            "if _bore > 0:",
            "    result = result.faces('>Z').workplane().hole(_bore)",
        ]
    else:
        # Eccentric: hinh tron lech tam
        eccentricity = lift / 2
        outer_radius = base_radius + eccentricity
        lines = [
            "import cadquery as cq",
            f"_r = {outer_radius}",
            f"_ecc = {eccentricity}",
            f"_thickness = {thickness}",
            f"_bore = {bore_diameter}",
            "",
            "# Cam lech tam: hinh tron dich chuyen theo truc X",
            "result = (",
            "    cq.Workplane('XY')",
            "    .center(_ecc, 0)",
            "    .circle(_r)",
            "    .extrude(_thickness)",
            ")",
            "# Lo truc o tam goc (khong phai tam hinh tron)",
            "result = result.faces('>Z').workplane().hole(_bore)",
        ]
    return "\n".join(lines)