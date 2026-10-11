"""
cadai/generators/pin.py
Chot tru (cylindrical pin / dowel pin): hinh tru thang.
"""
import cadquery as cq


def build(spec) -> str:
    d = spec.base_dimensions
    diameter = d["diameter"]
    length = d["length"]
    chamfer = d.get("chamfer", round(diameter * 0.05, 2))

    lines = [
        f"result = cq.Workplane('XY').circle({diameter} / 2).extrude({length})",
        f"result = result.edges('<Z').chamfer({chamfer})",
        f"result = result.edges('>Z').chamfer({chamfer})",
    ]
    return "\n".join(lines)