"""2 tai bat bu-long o 2 dau (dung cho pillow_block)."""


def apply(feat, spec, idx) -> str:
    p = feat.params
    lug_length = p["lug_length"]
    lug_thickness = p.get("lug_thickness", spec.base_dimensions.get("base_height", 10))
    length = spec.base_dimensions["length"]
    depth = spec.base_dimensions["depth"]
    half_l = length / 2
    half_d = depth / 2
    lines = [
        f"_lug_r_{idx} = (cq.Workplane('XY')"
        f".moveTo({half_l}, {-half_d}).lineTo({half_l + lug_length}, {-half_d})"
        f".lineTo({half_l + lug_length}, {half_d}).lineTo({half_l}, {half_d})"
        f".close().extrude({lug_thickness}))",
        f"result = result.union(_lug_r_{idx})",
        f"_lug_l_{idx} = (cq.Workplane('XY')"
        f".moveTo({-half_l}, {-half_d}).lineTo({-half_l - lug_length}, {-half_d})"
        f".lineTo({-half_l - lug_length}, {half_d}).lineTo({-half_l}, {half_d})"
        f".close().extrude({lug_thickness}))",
        f"result = result.union(_lug_l_{idx})",
    ]
    return "\n".join(lines)
