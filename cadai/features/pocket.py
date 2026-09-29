"""Tui (khoet hinh chu nhat)."""


def apply(feat, spec, idx) -> str:
    p = feat.params
    length, width, depth = p["length"], p["width"], p["depth"]
    x, y = p["position"]
    return (
        f"result = (result.faces('>Z').workplane()"
        f".center({x}, {y})"
        f".rect({length}, {width})"
        f".cutBlind(-{depth}))"
    )
