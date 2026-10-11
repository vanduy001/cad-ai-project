"""
cadai/generators/washer.py
Vong dem (washer): hinh tru phang co lo o giua.
"""
import cadquery as cq


def build(spec) -> str:
    d = spec.base_dimensions
    outer_diameter = d["outer_diameter"]
    inner_diameter = d["inner_diameter"]
    thickness = d["thickness"]

    lines = [
        f"result = cq.Workplane('XY').circle({outer_diameter} / 2).extrude({thickness})",
        f"result = result.faces('>Z').workplane().hole({inner_diameter})",
    ]
    return "\n".join(lines)