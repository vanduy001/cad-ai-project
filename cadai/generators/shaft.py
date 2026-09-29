"""Truc tron 1 bac."""


def build(spec) -> str:
    d = spec.base_dimensions
    return f"result = cq.Workplane('XY').circle({d['diameter']} / 2).extrude({d['length']})"
