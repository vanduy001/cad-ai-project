"""Vong lo bu-long quanh tam."""


def apply(feat, spec, idx) -> str:
    p = feat.params
    count = p["count"]
    hole_d = p["hole_diameter"]
    pcd = p["pcd"]
    lines = [
        f"_positions_{idx} = []",
        f"for _i in range({count}):",
        f"    _angle = 2 * math.pi * _i / {count}",
        f"    _x = ({pcd} / 2) * math.cos(_angle)",
        f"    _y = ({pcd} / 2) * math.sin(_angle)",
        f"    _positions_{idx}.append((_x, _y))",
        f"result = (result.faces('>Z').workplane().pushPoints(_positions_{idx}).hole({hole_d}))",
    ]
    return "\n".join(lines)
