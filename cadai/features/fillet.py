"""Bo tron canh.

Voi chi tiet KHONG phai truc nhieu bac (tam, ke, mat bich...): giu nguyen cach cu,
chon canh song song truc Z va bo tron.

Voi TRUC NHIEU BAC (base_dimensions co "segments"): bo goc LOM (goc trong) tai cac vai truc,
la cac duong tron noi giua 2 doan co duong kinh khac nhau (dung chuan thiet ke truc).
Khong dung selector '|Z' cho truc vi tren mat tru no chon trung duong noi (seam) cua mat tru,
bo tron duong do se bao loi StdFail_NotDone: BRep_API: command not done.

params:
  radius   (bat buoc) ban kinh bo, mm
  edges    (tuy chon) "all" (mac dinh) | "top" | "bottom" | "corners"
           Voi truc, "top"/"bottom" van la bo canh tron o dau truc; cac gia tri con lai
           = bo goc lom tai moi vai truc.
"""


def _shaft_junctions(segs, radius):
    """Tra ve danh sach (z, ban_kinh_canh_lom, ban_kinh_bo) tai moi cho doi duong kinh."""
    junctions = []
    z = 0.0
    for i in range(len(segs) - 1):
        a, b = segs[i], segs[i + 1]
        z += float(a["length"])
        if a.get("shape") == "eccentric" or b.get("shape") == "eccentric":
            continue
        if a.get("shape") == "taper":
            d_left = float(a.get("end_diameter", a["diameter"]))
        else:
            d_left = float(a["diameter"])
        d_right = float(b["diameter"])
        step = abs(d_left - d_right) / 2.0
        if step < 0.01:
            continue
        r_edge = min(d_left, d_right) / 2.0
        # ban kinh bo khong duoc lon hon ~90% chieu cao bac, neu khong se tran ra canh ngoai
        r_eff = min(float(radius), 0.9 * step)
        junctions.append((round(z, 4), round(r_edge, 4), round(r_eff, 4)))
    return junctions


def apply(feat, spec, idx) -> str:
    p = feat.params
    radius = p["radius"]
    edges = p.get("edges", "all")

    segs = spec.base_dimensions.get("segments")
    is_shaft = isinstance(segs, list) and len(segs) > 0

    if is_shaft and edges not in ("top", "bottom"):
        junctions = _shaft_junctions(segs, radius)
        if not junctions:
            return "# fillet: khong co vai truc nao can bo"
        lines = [
            f"_junc_{idx} = {junctions!r}",
            f"for _z, _r, _f in _junc_{idx}:",
            "    _es = [e for e in result.edges().vals()",
            "           if e.geomType() == 'CIRCLE'",
            "           and abs(e.Center().z - _z) < 0.01",
            "           and abs(e.BoundingBox().xlen / 2.0 - _r) < 0.05]",
            "    if not _es:",
            "        continue",
            "    for _k in (1.0, 0.9, 0.8, 0.7, 0.5):",
            "        try:",
            "            result = result.newObject(_es).fillet(round(_f * _k, 3))",
            "            if _k < 1.0:",
            "                print('[fillet] z=%s: dung R=%s (nho hon R yeu cau vi gan ranh/lo)' % (_z, round(_f * _k, 3)))",
            "            break",
            "        except Exception:",
            "            pass",
            "    else:",
            "        print('[fillet] bo qua vai truc tai z=%s: khong bo duoc' % _z)",
        ]
        return "\n".join(lines)

    selector_map = {"all": "'|Z'", "top": "'>Z'", "bottom": "'<Z'", "corners": "'|Z'"}
    selector = selector_map.get(edges, "'|Z'")
    return f"result = result.edges({selector}).fillet({radius})"