"""
cadai/generators/countersunk_screw.py
Vit dau chim (countersunk screw): than tru + dau hinh non.
"""
import cadquery as cq
import math


def build(spec) -> str:
    d = spec.base_dimensions
    diameter = d["diameter"]
    length = d["length"]
    head_diameter = d.get("head_diameter", round(2.0 * diameter, 1))
    head_height = d.get("head_height", round(0.6 * diameter, 1))
    chamfer = d.get("chamfer", round(diameter * 0.05, 2))

    lines = [
        # Than tru
        f"result = cq.Workplane('XY').circle({diameter} / 2).extrude({length})",
        f"result = result.edges('<Z').chamfer({chamfer})",
        # Dau non (frustum): cat khoi tru lon bang hinh non nguoc
        f"_r1 = {head_diameter} / 2",
        f"_r2 = {diameter} / 2",
        f"_hh = {head_height}",
        f"_head = cq.Workplane('XY').workplane(offset={length}).add(",
        f"    cq.Solid.makeCone(_r1, _r2, _hh)",
        f")",
        f"result = result.union(_head)",
    ]
    return "\n".join(lines)