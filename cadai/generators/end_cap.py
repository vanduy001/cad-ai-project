"""
cadai/generators/end_cap.py
Nap dau truc (end cap / shaft cover): mat bich tru co lo truc, co the co ro-ven.
"""


def build(spec) -> str:
    d = spec.base_dimensions
    outer_diameter = d["outer_diameter"]
    bore_diameter = d["bore_diameter"]
    thickness = d["thickness"]
    flange_thickness = d.get("flange_thickness", round(thickness * 0.4, 1))
    hub_diameter = d.get("hub_diameter", round(outer_diameter * 0.55, 1))
    hub_length = d.get("hub_length", round(thickness * 0.6, 1))
    bolt_count = int(d.get("bolt_count", 4))
    bolt_diameter = d.get("bolt_diameter", round(outer_diameter * 0.07, 1))
    pcd = d.get("pcd", round(outer_diameter * 0.75, 1))
    has_seal_groove = d.get("has_seal_groove", False)
    seal_width = d.get("seal_width", 5)
    seal_depth = d.get("seal_depth", 2)

    lines = [
        "import cadquery as cq",
        f"_od = {outer_diameter}",
        f"_bore = {bore_diameter}",
        f"_t = {thickness}",
        f"_ft = {flange_thickness}",
        f"_hub_d = {hub_diameter}",
        f"_hub_l = {hub_length}",
        f"_bolt_n = {bolt_count}",
        f"_bolt_d = {bolt_diameter}",
        f"_pcd = {pcd}",
        "",
        "# Mat bich chinh",
        "result = cq.Workplane('XY').circle(_od / 2).extrude(_ft)",
        "",
        "# Loi trum (hub)",
        "_hub = cq.Workplane('XY').workplane(offset=_ft).circle(_hub_d / 2).extrude(_hub_l)",
        "result = result.union(_hub)",
        "",
        "# Lo truc xuyen suot",
        "result = result.faces('>Z').workplane().hole(_bore)",
        "",
        "# Lo bu-long tren mat bich",
        "result = (",
        "    result.faces('<Z').workplane()",
        "    .polarArray(_pcd / 2, 0, 360, _bolt_n)",
        "    .hole(_bolt_d)",
        ")",
    ]

    if has_seal_groove:
        lines += [
            "",
            "# Ranh ro-ven (seal groove) o mat trong lo truc",
            f"_sw = {seal_width}",
            f"_sd = {seal_depth}",
            "_seal_r_in = _bore / 2",
            "_seal_r_out = _seal_r_in + _sd",
            "_seal_z = _ft / 2 - _sw / 2",
            "_seal_pts = [",
            "    (_seal_r_in,  _seal_z),",
            "    (_seal_r_out, _seal_z),",
            "    (_seal_r_out, _seal_z + _sw),",
            "    (_seal_r_in,  _seal_z + _sw),",
            "]",
            "_groove = (",
            "    cq.Workplane('XZ')",
            "    .workplane(offset=0)",
            "    .polyline(_seal_pts).close()",
            "    .revolve(360, [0,0,0], [0,1,0])",
            ")",
            "result = result.cut(_groove)",
        ]

    return "\n".join(lines)