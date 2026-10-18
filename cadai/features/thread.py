"""Ren ky hieu (vd M8, M10) -- CHUA cat ren that trong hinh 3D.

REN TRONG (mac dinh): khoan lo voi duong kinh nguoi dung khai bao va ghi chu ky hieu ren
trong code de nguoi doc/CAM hieu day la lo can ta-ro.
  params: designation, diameter (bat buoc), positions (bat buoc), depth ("through"|so mm)

REN NGOAI ("kind": "external"): CHI GHI CHU ky hieu, KHONG thay doi hinh 3D (truc van la
hinh tru tron theo duong kinh danh nghia).
  params: designation, z_start (tuy chon), length (tuy chon) = doan truc co ren
"""


def _clean(s) -> str:
    return str(s).replace("\n", " ").replace("\r", " ")


def apply(feat, spec, idx) -> str:
    p = feat.params
    designation = p.get("designation", "")

    kind = str(p.get("kind", "")).lower()
    if kind == "external" or p.get("external") is True:
        z_start = p.get("z_start", 0)
        length = p.get("length")
        where = f"z={_clean(z_start)}"
        if length is not None:
            where += f", dai {_clean(length)}"
        return f"# Ren ngoai {_clean(designation)} ({where}) - chi ky hieu, chua cat ren that"

    diameter = p["diameter"]
    positions = p["positions"]
    depth = p.get("depth", "through")

    lines = [f"# Ren {_clean(designation)} - lo khoan truoc khi ta-ro, chua cat ren that"]
    lines.append(f"pts_{idx} = {positions}")
    if depth == "through":
        lines.append(
            f"result = (result.faces('>Z').workplane()"
            f".pushPoints(pts_{idx}).hole({diameter}))"
        )
    else:
        lines.append(
            f"result = (result.faces('>Z').workplane()"
            f".pushPoints(pts_{idx}).hole({diameter}, depth={depth}))"
        )
    return "\n".join(lines)