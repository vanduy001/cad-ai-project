"""Ranh thoat dao (undercut): ranh tron quanh truc, cat sau vao be mat ngoai.

params:
  width       (bat buoc) be rong ranh doc truc, mm
  depth       (bat buoc) do sau ranh theo ban kinh, mm
  z           (bat buoc) vi tri bat dau ranh doc truc, tinh tu dau truc (z = 0), mm
              (cung chap nhan "z_start", "position", "height_from_base")
  from_end    (tuy chon) true -> z tinh tu dau CUOI truc (ranh nam cach dau cuoi z mm)
  diameter    (tuy chon) duong kinh truc tai cho cat; thieu thi tu lay theo doan truc tai vi tri do
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


def _radius_at(spec, z):
    d = spec.base_dimensions
    segs = d.get("segments")
    if isinstance(segs, list) and segs:
        z0 = 0.0
        for s in segs:
            z1 = z0 + float(s["length"])
            if z0 <= z <= z1:
                d0 = float(s["diameter"])
                d1 = float(s.get("end_diameter", d0)) if s.get("shape") == "taper" else d0
                t = (z - z0) / (z1 - z0) if z1 > z0 else 0.0
                return (d0 + (d1 - d0) * t) / 2
            z0 = z1
        return float(segs[-1]["diameter"]) / 2
    v = d.get("diameter")
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return float(v) / 2
    return None


def apply(feat, spec, idx) -> str:
    p = feat.params
    width = _first(p, ("width", "length"))
    if width is None:
        raise KeyError("width")
    depth = _first(p, ("depth",))
    if depth is None:
        raise KeyError("depth")
    z = _first(p, ("z", "z_start", "position", "height_from_base"))
    if z is None:
        raise KeyError("z")

    if p.get("from_end"):
        total = _total_length(spec)
        if total is None:
            raise KeyError("z")
        z = total - z - width
    if z < 0:
        z = 0

    dia = _first(p, ("diameter", "shaft_diameter"))
    radius = dia / 2 if dia is not None else _radius_at(spec, z + width / 2)
    if radius is None:
        raise KeyError("diameter")
    if depth >= radius:
        raise ValueError("undercut: depth phai nho hon ban kinh truc")

    r_in = round(radius - depth, 4)
    r_out = round(radius + 5, 4)
    lines = [
        f"_ring_{idx} = (cq.Workplane('XY').workplane(offset={z})",
        f"    .circle({r_out}).circle({r_in})",
        f"    .extrude({width}))",
        f"result = result.cut(_ring_{idx})",
    ]
    return "\n".join(lines)