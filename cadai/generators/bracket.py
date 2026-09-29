"""Gia do: khoi hop hoac dang chu L neu co leg_height/leg_thickness."""


def build(spec) -> str:
    d = spec.base_dimensions
    if "leg_height" in d and "leg_thickness" in d:
        length = d["length"]
        base_thickness = d["thickness"]
        leg_height = d["leg_height"]
        leg_thickness = d["leg_thickness"]
        width = d["width"]
        lines = [
            "_profile = (cq.Workplane('XZ')",
            "    .moveTo(0, 0)",
            f"    .lineTo({length}, 0)",
            f"    .lineTo({length}, {base_thickness})",
            f"    .lineTo({leg_thickness}, {base_thickness})",
            f"    .lineTo({leg_thickness}, {leg_height})",
            f"    .lineTo(0, {leg_height})",
            "    .close())",
            f"result = _profile.extrude({width})",
        ]
        return "\n".join(lines)
    return f"result = cq.Workplane('XY').box({d['length']}, {d['width']}, {d['thickness']})"
