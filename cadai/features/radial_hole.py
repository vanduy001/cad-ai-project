"""Lo ngang xuyen truc (khoan vuong goc voi truc, theo huong X).

params:
  diameter           (bat buoc) duong kinh lo, mm
  height_from_base   (tuy chon) vi tri doc truc, tinh tu dau truc (z = 0), mm.
                     Neu thieu -> khoan o giua chieu dai truc.
"""


def _first(p, names, default=None):
    for n in names:
        v = p.get(n)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return v
    return default


def _total_length(spec):
    d = spec.base_dimensions
    segs = d.get("segments")
    if isinstance(segs, list) and segs:
        return sum(float(s["length"]) for s in segs)
    for k in ("length", "total_length", "height"):
        if isinstance(d.get(k), (int, float)):
            return float(d[k])
    return None


def apply(feat, spec, idx) -> str:
    p = feat.params
    diameter = _first(p, ("diameter", "hole_diameter", "d"))
    if diameter is None:
        raise KeyError("diameter")
    height_from_base = _first(p, (
        "height_from_base", "position", "z", "z_position", "height",
        "distance", "offset", "from_base", "z_start",
    ))
    if height_from_base is None:
        total = _total_length(spec)
        if total is None:
            raise KeyError("height_from_base")
        height_from_base = total / 2
    outer_extent = _first(p, ("outer_extent",), 200)
    lines = [
        f"_cutter_{idx} = (cq.Workplane('YZ')",
        f"    .move(0, {height_from_base})",
        f"    .circle({diameter} / 2)",
        f"    .extrude({outer_extent}, both=True))",
        f"result = result.cut(_cutter_{idx})",
    ]
    return "\n".join(lines)