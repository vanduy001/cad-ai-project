"""
cadai/generators/piston.py
Piston: hinh tru co ranh xec-mang, lo chot piston.
"""


def build(spec) -> str:
    d = spec.base_dimensions
    diameter = d["diameter"]
    length = d["length"]
    pin_diameter = d.get("pin_diameter", round(diameter * 0.28, 1))
    wall_thickness = d.get("wall_thickness", round(diameter * 0.1, 1))
    num_rings = int(d.get("num_rings", 2))          # so ranh xec-mang
    ring_width = d.get("ring_width", round(diameter * 0.05, 1))
    ring_depth = d.get("ring_depth", round(diameter * 0.025, 1))
    crown_height = d.get("crown_height", round(diameter * 0.12, 1))  # chieu cao dinh piston
    skirt_length = d.get("skirt_length", round(length * 0.55, 1))    # chieu dai chan piston

    ring_start = round(crown_height + ring_width * 0.5, 1)   # vi tri ranh dau tien

    lines = [
        "import cadquery as cq",
        f"_d = {diameter}",
        f"_l = {length}",
        f"_pin_d = {pin_diameter}",
        f"_wt = {wall_thickness}",
        f"_n_rings = {num_rings}",
        f"_rw = {ring_width}",
        f"_rd = {ring_depth}",
        f"_crown_h = {crown_height}",
        f"_skirt_l = {skirt_length}",
        f"_ring_start = {ring_start}",
        "",
        "# Than piston chinh (hinh tru dac)",
        "result = cq.Workplane('XY').circle(_d / 2).extrude(_l)",
        "",
        "# Khoet rong ben trong (tao thanh vo mong)",
        "_inner_d = _d - 2 * _wt",
        "result = result.faces('>Z').workplane().circle(_inner_d / 2).cutBlind(-(_l - _crown_h))",
        "",
        "# Cac ranh xec-mang (ring grooves)",
        "for _ri in range(_n_rings):",
        "    _rz = _ring_start + _ri * (_rw + _rw * 1.5)",
        "    _groove_pts = [",
        "        (_d/2 - _rd, _l - _rz),",
        "        (_d/2 + 1,   _l - _rz),",
        "        (_d/2 + 1,   _l - _rz - _rw),",
        "        (_d/2 - _rd, _l - _rz - _rw),",
        "    ]",
        "    _groove = (",
        "        cq.Workplane('XZ').workplane(offset=0)",
        "        .polyline(_groove_pts).close()",
        "        .revolve(360, [0,0,0], [0,1,0])",
        "    )",
        "    result = result.cut(_groove)",
        "",
        "# Lo chot piston (xuyen ngang)",
        "result = (",
        "    result",
        "    .faces('>X')",
        "    .workplane(centerOption='CenterOfBoundBox')",
        "    .center(0, -(_l/2 - _crown_h - (_n_rings+1)*_rw*3))",
        "    .hole(_pin_d)",
        ")",
    ]
    return "\n".join(lines)