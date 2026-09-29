"""Ren ky hieu (vd M8, M10) -- CHUA cat ren that trong hinh 3D,
chi khoan lo voi duong kinh nguoi dung khai bao va ghi chu ky hieu ren
trong code de nguoi doc/CAM hieu day la lo can ta-ro."""


def apply(feat, spec, idx) -> str:
    p = feat.params
    designation = p.get("designation", "")
    diameter = p["diameter"]
    positions = p["positions"]
    depth = p.get("depth", "through")

    lines = [f"# Ren {designation} - lo khoan truoc khi ta-ro, chua cat ren that"]
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
