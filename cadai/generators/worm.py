"""
cadai/generators/worm.py
Truc vit (worm): hinh tru co rang xoan don gian hoa bang cac rang doc truc.
"""
import math


def build(spec) -> str:
    d = spec.base_dimensions
    diameter = d["diameter"]
    length = d["length"]
    num_threads = int(d.get("num_threads", 1))   # so dau moi (1, 2, 4)
    module = d.get("module", round(diameter * 0.1, 1))
    bore_diameter = d.get("bore_diameter", round(diameter * 0.3, 1))

    pitch_r = diameter / 2
    addendum = module
    dedendum = 1.25 * module
    outer_r = pitch_r + addendum
    root_r = pitch_r - dedendum

    # Xap xi rang xoan bang cac rang thang xep nghieng
    # Moi rang la 1 khe cat theo chieu doc + xoay
    thread_angle = 2 * math.pi / num_threads
    tooth_width = math.pi * module        # buoc rang
    lead_angle = math.degrees(math.atan(num_threads * module / diameter))

    # Sinh profil rang: polyline tren mat phang doc truc
    # Xap xi: cat cac ranh hinh thang doc theo truc, xoay quanh truc
    num_grooves = max(int(length / tooth_width), 2)
    groove_pts_left = []
    groove_pts_right = []

    for i in range(num_grooves + 1):
        z = i * tooth_width - tooth_width / 2
        if z < 0 or z > length:
            continue
        groove_pts_left.append((root_r, round(z, 4)))
        groove_pts_right.append((outer_r, round(z + tooth_width * 0.4, 4)))

    # Sinh code: than tru + cat rang xoan
    # Don gian hoa: cat cac ranh hinh thang xoay deu quanh truc
    groove_width = tooth_width * 0.5
    pa_offset = round(module * math.tan(math.radians(20)), 4)

    # Tao profil 1 ranh (mat cat doc truc, xoay 360/num_threads)
    lines = [
        "import cadquery as cq",
        "import math",
        f"_od = {outer_r}",
        f"_rd = {root_r}",
        f"_l = {length}",
        f"_bore = {bore_diameter}",
        f"_module = {module}",
        f"_num_threads = {num_threads}",
        f"_tooth_w = {round(tooth_width, 4)}",
        f"_pa_offset = {pa_offset}",
        "",
        "# Than tru chinh",
        "result = cq.Workplane('XY').circle(_od).extrude(_l)",
        "",
        "# Cat cac ranh rang xap xi (hinh thang xoay quanh truc)",
        "_num_grooves = max(int(_l / _tooth_w), 2)",
        "for _gi in range(_num_grooves):",
        "    for _ti in range(_num_threads):",
        "        _z0 = _gi * _tooth_w",
        "        _z1 = _z0 + _tooth_w * 0.5",
        "        if _z1 > _l: break",
        "        _rot = 360 * _ti / _num_threads + _gi * 360 / _num_threads / _num_grooves",
        "        _groove_pts = [",
        "            (_rd, _z0 + _pa_offset),",
        "            (_od + 1, _z0),",
        "            (_od + 1, _z1),",
        "            (_rd, _z1 - _pa_offset),",
        "        ]",
        "        _groove = (",
        "            cq.Workplane('XZ').workplane(offset=0)",
        "            .polyline(_groove_pts).close()",
        "            .revolve(_rot + 360/_num_threads, [0,0,0], [0,1,0])",
        "        )",
        "        result = result.cut(_groove)",
        "",
        "# Lo truc",
        "result = result.faces('>Z').workplane().hole(_bore)",
    ]
    return "\n".join(lines)