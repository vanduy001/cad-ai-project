"""
cadai/generators/connecting_rod.py
Thanh truyen (connecting rod): dau to + than + dau nho.
"""
import math


def build(spec) -> str:
    d = spec.base_dimensions
    length = d["length"]                     # khoang cach tam 2 dau
    big_end_diameter = d["big_end_diameter"]  # duong kinh dau to (goi truc khuyu)
    small_end_diameter = d["small_end_diameter"]  # duong kinh dau nho (goi chot piston)
    thickness = d["thickness"]               # chieu day thanh truyen
    big_bore = d.get("big_bore", round(big_end_diameter * 0.55, 1))
    small_bore = d.get("small_bore", round(small_end_diameter * 0.5, 1))
    beam_width = d.get("beam_width", round(big_end_diameter * 0.35, 1))

    big_r = big_end_diameter / 2
    small_r = small_end_diameter / 2

    lines = [
        "import cadquery as cq",
        "import math",
        f"_l = {length}",
        f"_big_r = {big_r}",
        f"_small_r = {small_r}",
        f"_t = {thickness}",
        f"_big_bore = {big_bore}",
        f"_small_bore = {small_bore}",
        f"_bw = {beam_width}",
        "",
        "# Dau to (big end) - hinh tru dep",
        "_big_end = cq.Workplane('XY').circle(_big_r).extrude(_t)",
        "_big_end = _big_end.faces('>Z').workplane().hole(_big_bore)",
        "",
        "# Dau nho (small end) - dich chuyen theo truc Y",
        "_small_end = (",
        "    cq.Workplane('XY')",
        "    .workplane(offset=0)",
        "    .center(0, _l)",
        "    .circle(_small_r)",
        "    .extrude(_t)",
        ")",
        "_small_end = _small_end.faces('>Z').workplane().hole(_small_bore)",
        "",
        "# Than thanh truyen (hinh thang noi 2 dau)",
        "_beam_pts = [",
        "    (-_bw/2,          _big_r * 0.8),",
        "    (-_bw/2 * 0.6,    _l - _small_r * 0.8),",
        "    ( _bw/2 * 0.6,    _l - _small_r * 0.8),",
        "    ( _bw/2,          _big_r * 0.8),",
        "]",
        "_beam = (",
        "    cq.Workplane('XY')",
        "    .polyline(_beam_pts, includeCurrent=False)",
        "    .close()",
        "    .extrude(_t)",
        ")",
        "",
        "# Ghep lai",
        "result = _big_end.union(_small_end).union(_beam)",
    ]
    return "\n".join(lines)