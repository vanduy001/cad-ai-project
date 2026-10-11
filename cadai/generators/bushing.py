"""
cadai/generators/bushing.py
Bac lot truc (bushing / sleeve bearing): hinh tru rong, co the co ranh dau.
"""


def build(spec) -> str:
    d = spec.base_dimensions
    outer_diameter = d["outer_diameter"]
    inner_diameter = d["inner_diameter"]
    length = d["length"]
    has_oil_groove = d.get("has_oil_groove", False)
    flange_diameter = d.get("flange_diameter", 0)
    flange_thickness = d.get("flange_thickness", round(outer_diameter * 0.15, 1))

    lines = [
        "import cadquery as cq",
        f"_od = {outer_diameter}",
        f"_id = {inner_diameter}",
        f"_l = {length}",
        f"_flange_d = {flange_diameter}",
        f"_flange_t = {flange_thickness}",
        "",
        "# Than bac (hinh tru rong)",
        "result = cq.Workplane('XY').circle(_od / 2).extrude(_l)",
        "result = result.faces('>Z').workplane().hole(_id)",
    ]

    if flange_diameter and flange_diameter > outer_diameter:
        lines += [
            "",
            "# Mat bich (flange)",
            "_flange = cq.Workplane('XY').workplane(offset=-_flange_t).circle(_flange_d / 2).extrude(_flange_t)",
            "result = result.union(_flange)",
            "result = result.faces('<Z').workplane().hole(_id)",
        ]

    if has_oil_groove:
        lines += [
            "",
            "# Ranh dau (oil groove) giua than",
            "_groove_d = _od + 2",
            "_groove_w = 3",
            "_groove_depth = 1.5",
            "_mid = _l / 2",
            "_groove = (",
            "    cq.Workplane('XZ')",
            "    .workplane(offset=0)",
            "    .polyline([",
            "        (_od/2 - _groove_depth, _mid - _groove_w/2),",
            "        (_od/2 + 1,             _mid - _groove_w/2),",
            "        (_od/2 + 1,             _mid + _groove_w/2),",
            "        (_od/2 - _groove_depth, _mid + _groove_w/2),",
            "    ]).close()",
            "    .revolve(360, [0,0,0], [0,1,0])",
            ")",
            "result = result.cut(_groove)",
        ]

    return "\n".join(lines)