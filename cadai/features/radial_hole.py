"""Lo ngang xuyen truc."""


def apply(feat, spec, idx) -> str:
    p = feat.params
    diameter = p["diameter"]
    height_from_base = p["height_from_base"]
    outer_extent = p.get("outer_extent", 200)
    lines = [
        f"_cutter_{idx} = (cq.Workplane('YZ')",
        f"    .move(0, {height_from_base})",
        f"    .circle({diameter} / 2)",
        f"    .extrude({outer_extent}, both=True))",
        f"result = result.cut(_cutter_{idx})",
    ]
    return "\n".join(lines)
