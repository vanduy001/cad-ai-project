"""Ranh (slot)."""


def apply(feat, spec, idx) -> str:
    p = feat.params
    length, width, depth = p["length"], p["width"], p.get("depth", "through")
    x, y = p["position"]
    angle = p.get("angle", 0)
    setup = (
        f"result = (result.faces('>Z').workplane()"
        f".center({x}, {y})"
        f".transformed(rotate=(0, 0, {angle}))"
        f".slot2D({length}, {width})"
    )
    if depth == "through":
        return setup + ".cutThruAll())"
    return setup + f".cutBlind(-{depth}))"
