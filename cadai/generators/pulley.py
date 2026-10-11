"""
cadai/generators/pulley.py
Puly / banh dai (pulley): hinh tru co ranh chu V o giua.
"""


def build(spec) -> str:
    d = spec.base_dimensions
    outer_diameter = d["outer_diameter"]
    bore_diameter = d["bore_diameter"]
    width = d["width"]
    groove_depth = d.get("groove_depth", round(outer_diameter * 0.08, 1))
    groove_angle = d.get("groove_angle", 38)  # do, goc mo ranh V
    hub_diameter = d.get("hub_diameter", round(bore_diameter * 2.0, 1))
    hub_length = d.get("hub_length", round(width * 0.6, 1))

    lines = [
        "import cadquery as cq",
        "import math",
        f"_od = {outer_diameter}",
        f"_bore = {bore_diameter}",
        f"_w = {width}",
        f"_gd = {groove_depth}",
        f"_ga = math.radians({groove_angle})",
        f"_hub_d = {hub_diameter}",
        f"_hub_l = {hub_length}",
        "",
        "# Than puly chinh (hinh tru)",
        "result = cq.Workplane('XY').circle(_od / 2).extrude(_w)",
        "",
        "# Cat ranh V o giua",
        "_groove_top_r = _od / 2",
        "_groove_bot_r = _groove_top_r - _gd",
        "_groove_half_w = _gd * math.tan(_ga)",
        "_mid = _w / 2",
        "_pts = [",
        "    (_groove_top_r, _mid - _groove_half_w),",
        "    (_groove_bot_r, _mid),",
        "    (_groove_top_r, _mid + _groove_half_w),",
        "    (_groove_top_r + 2, _mid + _groove_half_w),",
        "    (_groove_top_r + 2, _mid - _groove_half_w),",
        "]",
        "_groove_wire = (",
        "    cq.Workplane('XZ')",
        "    .workplane(offset=0)",
        "    .polyline(_pts).close()",
        "    .revolve(360, [0,0,0], [0,1,0])",
        ")",
        "result = result.cut(_groove_wire)",
        "",
        "# Loi trum (hub)",
        "_hub = cq.Workplane('XY').workplane(offset=-(_hub_l - _w)/2).circle(_hub_d/2).extrude(_hub_l)",
        "result = result.union(_hub)",
        "",
        "# Lo truc",
        "result = result.faces('>Z').workplane().hole(_bore)",
    ]
    return "\n".join(lines)