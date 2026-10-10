"""Bu-long: dau luc giac + than tru.
Than luon TRON TRON (khong ren xoan 3D that) -- da thu nghiem cat ren that
bang sweep() theo duong xoan oc nhung bi treo/loi OCCT voi so vong ren lon,
khong on dinh du de dung san xuat. "real_thread" van duoc chap nhan trong
spec (de khong vo pipeline neu AI dat co) nhung hien khong lam thay doi
hinh hoc -- chi la placeholder cho huong giai quyet khac sau nay."""


def build(spec) -> str:
    d = spec.base_dimensions
    diameter = d["diameter"]
    length = d["length"]
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