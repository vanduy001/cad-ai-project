"""Hop rong thanh mong, day kin."""


def build(spec) -> str:
    d = spec.base_dimensions
    wt = d["wall_thickness"]
    return (
        f"result = (cq.Workplane('XY')"
        f".box({d['length']}, {d['width']}, {d['height']})"
        f".faces('>Z').shell(-{wt}))"
    )
