"""Lo bac (counterbore).

params:
  diameter        (bat buoc) duong kinh lo nho, mm
  cbore_diameter  (bat buoc) duong kinh phan loe (bac to), mm
  cbore_depth     (bat buoc) do sau phan loe, mm
  positions       (tuy chon) [[x, y], ...] so voi tam mat. Thieu -> [[0, 0]] (lo o tam truc).
                  Cung chap nhan "position": [x, y].
  depth           (tuy chon) "through" (mac dinh) hoac so mm = TONG do sau lo tinh tu mat (gom ca bac loe).
  end             (tuy chon) "end" (mac dinh, mat +Z) hoac "start" (mat dau z = 0 cua truc).
"""


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _total_length(spec):
    d = spec.base_dimensions
    segs = d.get("segments")
    if isinstance(segs, list) and segs:
        return sum(float(s["length"]) for s in segs)
    for k in ("length", "total_length", "height", "thickness"):
        if _num(d.get(k)):
            return float(d[k])
    return None


def apply(feat, spec, idx) -> str:
    p = feat.params
    hole_d = p.get("diameter", p.get("hole_diameter"))
    if not _num(hole_d):
        raise KeyError("diameter")
    cbore_d = p["cbore_diameter"]
    cbore_depth = p["cbore_depth"]

    positions = p.get("positions")
    if positions is None:
        positions = p.get("position")
    if positions is None:
        positions = [[0, 0]]
    if (isinstance(positions, (list, tuple)) and len(positions) == 2
            and all(_num(v) for v in positions)):
        positions = [positions]

    depth = p.get("depth", "through")
    if not _num(depth):
        depth = "through"

    from_start = str(p.get("end", "end")).lower() in ("start", "z0", "bottom")

    lines = [f"pts_{idx} = {positions}"]
    if not from_start:
        if depth == "through":
            lines.append(
                f"result = (result.faces('>Z').workplane()"
                f".pushPoints(pts_{idx})"
                f".cboreHole({hole_d}, {cbore_d}, {cbore_depth}))"
            )
        else:
            lines.append(
                f"result = (result.faces('>Z').workplane()"
                f".pushPoints(pts_{idx})"
                f".cboreHole({hole_d}, {cbore_d}, {cbore_depth}, {depth}))"
            )
    else:
        # khoan tu mat z = 0 vao +Z; bat dau tu z = -1 de cat sach mat dau
        if depth == "through":
            total = _total_length(spec)
            hole_len = (total if total is not None else 1000)
        else:
            hole_len = depth
        lines.append(
            f"_cb_{idx} = (cq.Workplane('XY').workplane(offset=-1)"
            f".pushPoints(pts_{idx}).circle({cbore_d} / 2).extrude({cbore_depth} + 1))"
        )
        lines.append(
            f"_hl_{idx} = (cq.Workplane('XY').workplane(offset=-1)"
            f".pushPoints(pts_{idx}).circle({hole_d} / 2).extrude({hole_len} + 1))"
        )
        lines.append(f"result = result.cut(_cb_{idx}).cut(_hl_{idx})")
    return "\n".join(lines)