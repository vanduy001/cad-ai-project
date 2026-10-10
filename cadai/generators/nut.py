"""Dai oc (nut): khoi luc giac co lo xuyen giua.
Lo chi la lo tron don gian (khong ren that, giong logic cua bolt.py) --
on dinh, nhanh, khong dung sweep/helix nen khong gap van de hieu nang/OCCT."""


def build(spec) -> str:
    d = spec.base_dimensions
    diameter = d["diameter"]  # duong kinh lo (= duong kinh danh nghia bu-long, vd M8 -> 8)
    height = d["height"]
    width = d.get("width", round(1.5 * diameter + 6, 1))

    lines = [
        f"result = cq.Workplane('XY').polygon(6, {width}).extrude({height})",
        f"result = result.faces('>Z').workplane().hole({diameter})",
    ]
    return "\n".join(lines)