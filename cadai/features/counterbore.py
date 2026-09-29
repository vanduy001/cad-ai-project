"""Lo bac (counterbore)."""


def apply(feat, spec, idx) -> str:
    p = feat.params
    hole_d = p["diameter"]
    cbore_d = p["cbore_diameter"]
    cbore_depth = p["cbore_depth"]
    positions = p["positions"]
    lines = [
        f"pts_{idx} = {positions}",
        f"result = (result.faces('>Z').workplane()"
        f".pushPoints(pts_{idx})"
        f".cboreHole({hole_d}, {cbore_d}, {cbore_depth}))",
    ]
    return "\n".join(lines)
