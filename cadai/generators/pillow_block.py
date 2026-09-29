"""Goi do truc: khoi hop chu nhat, vat 2 ben, ranh cong dat truc o tren.
Toa do: X = length (ngang), Y = depth (sau, truc cua ranh cong), Z = height (cao, day tai Z=0)."""


def build(spec) -> str:
    d = spec.base_dimensions
    length = d["length"]
    depth = d["depth"]
    height = d["height"]
    base_height = d["base_height"]
    top_width = d["top_width"]
    seat_radius = d["seat_radius"]
    half_l = length / 2
    half_w = top_width / 2

    lines = [
        f"result = cq.Workplane('XY').rect({length}, {depth}).extrude({height})",
        f"_vat_l = (cq.Workplane('XZ')"
        f".moveTo({-half_l}, {base_height}).lineTo({-half_w}, {height}).lineTo({-half_l}, {height})"
        f".close().extrude({depth} + 20, both=True))",
        "result = result.cut(_vat_l)",
        f"_vat_r = (cq.Workplane('XZ')"
        f".moveTo({half_l}, {base_height}).lineTo({half_w}, {height}).lineTo({half_l}, {height})"
        f".close().extrude({depth} + 20, both=True))",
        "result = result.cut(_vat_r)",
        f"_seat = (cq.Workplane('XZ').center(0, {height}).circle({seat_radius})"
        f".extrude({depth} + 20, both=True))",
        "result = result.cut(_seat)",
    ]
    return "\n".join(lines)
