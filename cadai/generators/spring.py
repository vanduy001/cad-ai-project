"""
cadai/generators/spring.py
Lo xo xoan (coil spring): xap xi bang cac dia tru xep chong, khong dung helix.
Khong chinh xac 100% nhung du de xuat STEP va xem trong CAD.
"""
import math


def build(spec) -> str:
    d = spec.base_dimensions
    coil_diameter = d["coil_diameter"]      # duong kinh vong xoan (tim den tim day)
    wire_diameter = d["wire_diameter"]      # duong kinh day lo xo
    num_coils = d["num_coils"]              # so vong
    free_length = d["free_length"]          # chieu dai tu do
    bore_diameter = d.get("bore_diameter", 0)  # lo giua (neu co)

    coil_r = coil_diameter / 2
    wire_r = wire_diameter / 2
    pitch = free_length / max(num_coils, 1)

    # Xap xi lo xo bang cac doan ong ngan nghieng
    # Moi vong xoan = 8 doan, moi doan la 1 hinh tru nghieng nho
    segs_per_coil = 12
    total_segs = int(num_coils * segs_per_coil)

    lines = [
        "import cadquery as cq",
        "import math",
        f"_coil_r = {coil_r}",
        f"_wire_r = {wire_r}",
        f"_pitch = {round(pitch, 4)}",
        f"_total_segs = {total_segs}",
        f"_segs_per_coil = {segs_per_coil}",
        f"_free_l = {free_length}",
        "",
        "# Tao tung doan nho cua lo xo roi union lai",
        "_result = None",
        "for _seg in range(_total_segs):",
        "    _frac0 = _seg / _total_segs",
        "    _frac1 = (_seg + 1) / _total_segs",
        "    _a0 = _frac0 * 2 * math.pi * _segs_per_coil / _segs_per_coil",
        "    _a1 = _frac1 * 2 * math.pi * _segs_per_coil / _segs_per_coil",
        "    _angle0 = _frac0 * 2 * math.pi * (_total_segs / _segs_per_coil)",
        "    _angle1 = _frac1 * 2 * math.pi * (_total_segs / _segs_per_coil)",
        "    _x0 = _coil_r * math.cos(_angle0)",
        "    _y0 = _coil_r * math.sin(_angle0)",
        "    _z0 = _frac0 * _free_l",
        "    _x1 = _coil_r * math.cos(_angle1)",
        "    _y1 = _coil_r * math.sin(_angle1)",
        "    _z1 = _frac1 * _free_l",
        "    _mid_x = (_x0 + _x1) / 2",
        "    _mid_y = (_y0 + _y1) / 2",
        "    _mid_z = (_z0 + _z1) / 2",
        "    _seg_len = math.sqrt((_x1-_x0)**2 + (_y1-_y0)**2 + (_z1-_z0)**2)",
        "    if _seg_len < 0.001: continue",
        "    _dx = (_x1-_x0)/_seg_len; _dy = (_y1-_y0)/_seg_len; _dz = (_z1-_z0)/_seg_len",
        "    _cyl = (",
        "        cq.Workplane(cq.Plane(origin=(_mid_x,_mid_y,_mid_z), normal=(_dx,_dy,_dz)))",
        "        .circle(_wire_r)",
        "        .extrude(_seg_len / 2, both=True)",
        "    )",
        "    _result = _cyl if _result is None else _result.union(_cyl)",
        "result = _result",
    ]
    return "\n".join(lines)