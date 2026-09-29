"""Mat bich: vong tron ngoai tru vong tron trong."""


def build(spec) -> str:
    d = spec.base_dimensions
    return (
        f"result = (cq.Workplane('XY')"
        f".circle({d['outer_diameter']} / 2)"
        f".circle({d['inner_diameter']} / 2)"
        f".extrude({d['thickness']}))"
    )
