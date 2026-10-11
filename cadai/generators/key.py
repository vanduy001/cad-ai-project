"""
cadai/generators/key.py
Then bang (parallel key): hinh hop chu nhat, 2 dau ban tron hoac vuong.
"""


def build(spec) -> str:
    d = spec.base_dimensions
    length = d["length"]
    width = d["width"]
    height = d["height"]
    key_type = d.get("key_type", "square")  # square | rounded

    lines = [
        "import cadquery as cq",
        f"_l = {length}",
        f"_w = {width}",
        f"_h = {height}",
    ]

    if key_type == "rounded":
        # Dau ban tron: extrude doc theo chieu dai, profil chu nhat, fillet 2 dau
        lines += [
            "result = cq.Workplane('XY').box(_l, _w, _h)",
            f"_r = min({width}, {height}) / 2 - 0.01",
            "result = result.edges('|Z').fillet(_r)",
        ]
    else:
        lines += [
            "result = cq.Workplane('XY').box(_l, _w, _h)",
        ]

    return "\n".join(lines)