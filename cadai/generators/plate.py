"""Tam phang."""


def build(spec) -> str:
    d = spec.base_dimensions
    return f"result = cq.Workplane('XY').box({d['length']}, {d['width']}, {d['thickness']})"
