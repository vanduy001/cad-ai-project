"""Bu-long don gian: dau luc giac + than tru, vat canh o dau mut than.
Than KHONG co duong ren xoan 3D thuc -- day la mo hinh don gian hoa, giong
cach lam voi tinh nang 'thread' (chi danh dau ky hieu, chua cat ren that)."""


def build(spec) -> str:
    d = spec.base_dimensions
    diameter = d["diameter"]
    length = d["length"]
    # head_width/head_height/chamfer la tuy chon, co gia tri mac dinh xap xi
    # theo ty le thuong gap cua bu-long luc giac (khong phai bang ISO chinh xac)
    head_width = d.get("head_width", round(1.5 * diameter + 6, 1))
    head_height = d.get("head_height", round(0.7 * diameter, 1))
    chamfer = d.get("chamfer", round(diameter * 0.1, 2))

    lines = [
        f"result = cq.Workplane('XY').circle({diameter} / 2).extrude({length})",
        f"result = result.edges('<Z').chamfer({chamfer})",
        f"_head = cq.Workplane('XY').workplane(offset={length}).polygon(6, {head_width}).extrude({head_height})",
        "result = result.union(_head)",
    ]
    return "\n".join(lines)