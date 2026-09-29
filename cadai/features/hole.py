"""Lo thang, xuyen hoac co do sau."""


def apply(feat, spec, idx) -> str:
    p = feat.params
    diameter = p["diameter"]
    positions = p["positions"]
    depth = p.get("depth", "through")

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
