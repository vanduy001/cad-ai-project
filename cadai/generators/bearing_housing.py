"""
cadai/generators/bearing_housing.py
Goi do vong bi (bearing housing): than tru rong de lap vong bi, co mat bich.
"""


def build(spec) -> str:
    d = spec.base_dimensions
    outer_diameter = d["outer_diameter"]      # duong kinh ngoai than
    bearing_diameter = d["bearing_diameter"]  # duong kinh lo lap vong bi
    length = d["length"]                      # chieu dai than
    flange_diameter = d.get("flange_diameter", round(outer_diameter * 1.5, 1))
    flange_thickness = d.get("flange_thickness", round(outer_diameter * 0.18, 1))
    bolt_count = int(d.get("bolt_count", 4))
    bolt_diameter = d.get("bolt_diameter", round(outer_diameter * 0.1, 1))
    pcd = d.get("pcd", round(flange_diameter * 0.75, 1))
    has_snap_ring_groove = d.get("has_snap_ring_groove", False)
    groove_width = d.get("groove_width", 3)
    groove_depth = d.get("groove_depth", 1.5)

    lines = [
        "import cadquery as cq",
        f"_od = {outer_diameter}",
        f"_bd = {bearing_diameter}",
        f"_l = {length}",
        f"_fd = {flange_diameter}",
        f"_ft = {flange_thickness}",
        f"_bolt_n = {bolt_count}",
        f"_bolt_d = {bolt_diameter}",
        f"_pcd = {pcd}",
        "",
        "# Than chinh (hinh tru)",
        "result = cq.Workplane('XY').circle(_od / 2).extrude(_l)",
        "",
        "# Lo lap vong bi xuyen suot",
        "result = result.faces('>Z').workplane().hole(_bd)",
        "",
        "# Mat bich",
        "_flange = cq.Workplane('XY').workplane(offset=-_ft).circle(_fd / 2).extrude(_ft)",
        "result = result.union(_flange)",
        "result = result.faces('<Z').workplane().hole(_bd)",
        "",
        "# Lo bu-long tren mat bich",
        "result = (",
        "    result.faces('<Z').workplane()",
        "    .polarArray(_pcd / 2, 0, 360, _bolt_n)",
        "    .hole(_bolt_d)",
        ")",
    ]

    if has_snap_ring_groove:
        lines += [
            "",
            "# Ranh vong ham (snap ring groove) sat mat bich",
            f"_gw = {groove_width}",
            f"_gd = {groove_depth}",
            "_gz = _l - _gw - 3",
            "_groove_pts = [",
            "    (_bd/2,      _gz),",
            "    (_bd/2 - _gd, _gz),",
            "    (_bd/2 - _gd, _gz + _gw),",
            "    (_bd/2,      _gz + _gw),",
            "]",
            "_groove = (",
            "    cq.Workplane('XZ')",
            "    .workplane(offset=0)",
            "    .polyline(_groove_pts).close()",
            "    .revolve(360, [0,0,0], [0,1,0])",
            ")",
            "result = result.cut(_groove)",
        ]

    return "\n".join(lines)