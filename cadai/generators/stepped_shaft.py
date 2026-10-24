"""Truc nhieu bac, moi doan 1 duong kinh, KHONG bat buoc doi xung.

Moi doan co the co khoa "shape":
  cylinder  (mac dinh) : hinh tru, dung "diameter"
  taper                : hinh non, "diameter" la dk dau doan, "end_diameter" la dk cuoi doan
  spline               : hinh tru co N ranh chu nhat doc truc
                         (tuy chon: spline_count mac dinh 6, spline_width, spline_depth)
  eccentric            : hinh tru lech tam, "offset" la do lech tam (mm) theo truc X
  square               : doan vuong/chu nhat; "diameter" la CANH vuong (mm),
                         tuy chon "width_y" la canh con lai (mac dinh = diameter)
  hexagon              : doan luc giac deu; "diameter" la BE RONG DOI DIEN (mm),
                         tuc khoang cach giua hai mat phang song song
"""


def build(spec) -> str:
    segments = spec.base_dimensions["segments"]
    lines = [
        f"_segments = {segments!r}",
        "result = None",
        "_z = 0",
        "for _seg in _segments:",
        "    _d = _seg['diameter']",
        "    _l = _seg['length']",
        "    _shape = _seg.get('shape', 'cylinder')",
        "    if _shape == 'taper':",
        "        _ed = _seg.get('end_diameter', _d)",
        "        _piece = cq.Workplane('XY').newObject([cq.Solid.makeCone(_d / 2, _ed / 2, _l, cq.Vector(0, 0, _z), cq.Vector(0, 0, 1))])",
        "    elif _shape == 'eccentric':",
        "        _off = _seg.get('offset', 0)",
        "        _piece = cq.Workplane('XY').workplane(offset=_z).center(_off, 0).circle(_d / 2).extrude(_l)",
        "    elif _shape == 'square':",
        "        _wy = _seg.get('width_y', _d)",
        "        _piece = cq.Workplane('XY').workplane(offset=_z).rect(_d, _wy).extrude(_l)",
        "    elif _shape == 'hexagon':",
        "        _piece = cq.Workplane('XY').workplane(offset=_z).polygon(6, _d * 1.1547005383792515).extrude(_l)",
        "    else:",
        "        _piece = cq.Workplane('XY').workplane(offset=_z).circle(_d / 2).extrude(_l)",
        "        if _shape == 'spline':",
        "            _n = int(_seg.get('spline_count', 6))",
        "            _w = _seg.get('spline_width', 3.1416 * _d / (2 * _n))",
        "            _t = _seg.get('spline_depth', 0.08 * _d)",
        "            for _i in range(_n):",
        "                _cut = (cq.Workplane('XY').workplane(offset=_z)",
        "                        .center(_d / 2 - _t / 2 + 0.5, 0).rect(_t + 1, _w).extrude(_l)",
        "                        .rotate((0, 0, 0), (0, 0, 1), 360.0 * _i / _n))",
        "                _piece = _piece.cut(_cut)",
        "    result = _piece if result is None else result.union(_piece)",
        "    _z += _l",
    ]
    return "\n".join(lines)