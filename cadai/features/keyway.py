"""Ranh then tren truc."""


def apply(feat, spec, idx) -> str:
    p = feat.params
    width = p["width"]
    depth = p["depth"]
    length = p["length"]
    z_start = p.get("z_start", 0)
    shaft_d = p["shaft_diameter"]
    r = shaft_d / 2
    lines = [
        f"_r_{idx} = {r}",
        f"_bottom_{idx} = _r_{idx} - {depth}",
        f"_top_{idx} = _r_{idx} + 5",
        f"_h_{idx} = _top_{idx} - _bottom_{idx}",
        f"_cy_{idx} = (_bottom_{idx} + _top_{idx}) / 2",
        f"_cz_{idx} = {z_start} + {length} / 2",
        f"_cutter_{idx} = cq.Workplane('XY').box({width}, _h_{idx}, {length})",
        f"_cutter_{idx} = _cutter_{idx}.translate((0, _cy_{idx}, _cz_{idx}))",
        f"result = result.cut(_cutter_{idx})",
    ]
    return "\n".join(lines)
