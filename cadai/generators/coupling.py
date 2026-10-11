"""
cadai/generators/coupling.py
Khop noi truc (shaft coupling): 2 mat bich tru noi nhau qua bu-long.
"""


def build(spec) -> str:
    d = spec.base_dimensions
    outer_diameter = d["outer_diameter"]
    bore_diameter = d["bore_diameter"]
    total_length = d["total_length"]
    flange_thickness = d.get("flange_thickness", round(outer_diameter * 0.15, 1))
    bolt_count = int(d.get("bolt_count", 4))
    bolt_diameter = d.get("bolt_diameter", round(outer_diameter * 0.08, 1))
    pcd = d.get("pcd", round(outer_diameter * 0.7, 1))  # pitch circle diameter

    hub_length = (total_length - 2 * flange_thickness) / 2
    hub_diameter = round(bore_diameter * 1.8, 1)

    lines = [
        "import cadquery as cq",
        f"_od = {outer_diameter}",
        f"_bore = {bore_diameter}",
        f"_total_l = {total_length}",
        f"_ft = {flange_thickness}",
        f"_bolt_n = {bolt_count}",
        f"_bolt_d = {bolt_diameter}",
        f"_pcd = {pcd}",
        f"_hub_l = {round(hub_length, 2)}",
        f"_hub_d = {hub_diameter}",
        "",
        "# Mat bich trai",
        "result = cq.Workplane('XY').circle(_od / 2).extrude(_ft)",
        "",
        "# Loi trum trai",
        "_hub_left = cq.Workplane('XY').workplane(offset=_ft).circle(_hub_d/2).extrude(_hub_l)",
        "result = result.union(_hub_left)",
        "",
        "# Loi trum phai",
        "_hub_right = cq.Workplane('XY').workplane(offset=_ft + _hub_l).circle(_hub_d/2).extrude(_hub_l)",
        "result = result.union(_hub_right)",
        "",
        "# Mat bich phai",
        "_flange_right = cq.Workplane('XY').workplane(offset=_total_l - _ft).circle(_od/2).extrude(_ft)",
        "result = result.union(_flange_right)",
        "",
        "# Lo truc xuyen suot",
        "result = result.faces('>Z').workplane().hole(_bore)",
        "",
        "# Lo bu-long tren mat bich",
        "result = (",
        "    result.faces('>Z').workplane()",
        "    .polarArray(_pcd/2, 0, 360, _bolt_n)",
        "    .hole(_bolt_d)",
        ")",
    ]
    return "\n".join(lines)