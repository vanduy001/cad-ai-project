"""Lo thang, xuyen hoac co do sau (khoan tu mat tren +Z).

params:
  diameter    (bat buoc) duong kinh lo, mm
  positions   (tuy chon) [[x, y], ...] so voi tam mat tren. Thieu -> [[0, 0]] (lo o tam,
              vi du lo khoan doc tam truc). Cung chap nhan "position": [x, y].
  depth       (tuy chon) "through" (mac dinh) hoac so mm.
"""


def apply(feat, spec, idx) -> str:
    p = feat.params
    diameter = None
    for n in ("diameter", "hole_diameter", "d"):
        v = p.get(n)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            diameter = v
            break
    if diameter is None:
        raise KeyError("diameter")

    positions = p.get("positions")
    if positions is None:
        positions = p.get("position")
    if positions is None:
        positions = [[0, 0]]
    # [x, y] don le -> [[x, y]]
    if (isinstance(positions, (list, tuple)) and len(positions) == 2
            and all(isinstance(v, (int, float)) for v in positions)):
        positions = [positions]

    depth = p.get("depth", "through")
    if isinstance(depth, bool) or not isinstance(depth, (int, float)):
        depth = "through"

    lines = [f"pts_{idx} = {positions}"]
    if depth == "through":
        lines.append(
            f"result = (result.faces('>Z').workplane()"
            f".pushPoints(pts_{idx}).hole({diameter}))"
        )
    else:
        lines.append(
            f"result = (result.faces('>Z').workplane()"
            f".pushPoints(pts_{idx}).hole({diameter}, depth={depth}))"
        )
    return "\n".join(lines)