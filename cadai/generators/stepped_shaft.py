"""Truc nhieu bac, moi doan 1 duong kinh, KHONG bat buoc doi xung."""


def build(spec) -> str:
    segments = spec.base_dimensions["segments"]
    lines = [
        f"_segments = {segments!r}",
        "result = None",
        "_z = 0",
        "for _seg in _segments:",
        "    _d = _seg['diameter']",
        "    _l = _seg['length']",
        "    _piece = cq.Workplane('XY').workplane(offset=_z).circle(_d / 2).extrude(_l)",
        "    result = _piece if result is None else result.union(_piece)",
        "    _z += _l",
    ]
    return "\n".join(lines)
