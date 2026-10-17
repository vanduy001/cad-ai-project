"""Ranh then tren truc: cat tu mat ngoai ve phia +Y, doc theo truc Z.

params:
  length          (bat buoc) chieu dai ranh, mm
  width, depth    (tuy chon) neu thieu -> lay theo DIN 6885 tu duong kinh truc
  z_start         (tuy chon, mac dinh 0) vi tri bat dau, tinh tu dau truc (z = 0)
  shaft_diameter  (tuy chon) neu thieu -> lay tu spec (truc bac: doan truc tai vi tri ranh)
"""

# (duong kinh truc toi da, b = chieu rong then, t1 = chieu sau ranh tren truc) theo DIN 6885
_DIN6885 = [
    (8, 2, 1.2), (10, 3, 1.8), (12, 4, 2.5), (17, 5, 3.0), (22, 6, 3.5),
    (30, 8, 4.0), (38, 10, 5.0), (44, 12, 5.0), (50, 14, 5.5), (58, 16, 6.0),
    (65, 18, 7.0), (75, 20, 7.5), (85, 22, 9.0), (95, 25, 9.0), (110, 28, 10.0),
]


def _first(p, names, default=None):
    """Lay gia tri SO dau tien co trong params theo danh sach ten (chap nhan ten goi khac)."""
    for n in names:
        v = p.get(n)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return v
    return default


def _din6885(d):
    for dmax, b, t1 in _DIN6885:
        if d <= dmax:
            return b, t1
    return _DIN6885[-1][1], _DIN6885[-1][2]


def _shaft_diameter(spec, z_mid):
    d = spec.base_dimensions
    segs = d.get("segments")
    if isinstance(segs, list) and segs:
        z = 0.0
        for s in segs:
            z2 = z + float(s["length"])
            if z <= z_mid <= z2:
                return float(s["diameter"])
            z = z2
        return max(float(s["diameter"]) for s in segs)
    for k in ("diameter", "outer_diameter"):
        if isinstance(d.get(k), (int, float)):
            return float(d[k])
    return None


def apply(feat, spec, idx) -> str:
    p = feat.params
    length = _first(p, ("length", "key_length"))
    if length is None:
        raise KeyError("length")
    z_start = _first(p, ("z_start", "start", "offset", "position", "z"), 0)
    shaft_d = _first(p, ("shaft_diameter", "shaft_d", "diameter"))
    if shaft_d is None:
        shaft_d = _shaft_diameter(spec, z_start + length / 2.0)
    if shaft_d is None:
        raise KeyError("shaft_diameter")
    b_std, t1_std = _din6885(shaft_d)
    width = _first(p, ("width", "b"), b_std)
    depth = _first(p, ("depth", "t1"), t1_std)
    r = shaft_d / 2
    lines = [
        f"_r_{idx} = {r}",
        f"_bottom_{idx} = _r_{idx} - {depth}",
        f"_top_{idx} = _r_{idx} + 5",
        f"_h_{idx} = _top_{idx} - _bottom_{idx}",
        f"_cy_{idx} = (_bottom_{idx} + _top_{idx}) / 2",
        f"_cz_{idx} = {z_start} + {length} / 2",
        f"_cutter_{idx} = cq.Workplane('XY').box({width}, _h_{idx}, {length})",
        f"_cutter_{idx} = _cutter_{idx}.translate((0, _cy_{idx}, _cz_{idx}))",
        f"result = result.cut(_cutter_{idx})",
    ]
    return "\n".join(lines)