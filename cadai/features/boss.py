"""Go noi hinh tru."""


def apply(feat, spec, idx) -> str:
    p = feat.params
    diameter, height = p["diameter"], p["height"]
    x, y = p["position"]
    return (
        f"result = (result.faces('>Z').workplane()"
        f".center({x}, {y})"
        f".circle({diameter} / 2)"
        f".extrude({height}))"
    )
