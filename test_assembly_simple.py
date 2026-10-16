"""Test assembly don gian: 7 chi tiet trong ban ve tong the."""
import cadquery as cq
import traceback

try:
    # 1. Tam phang (de)
    plate = cq.Workplane('XY').box(560, 380, 15)

    # 2. Gia do (bracket) - 2 cai, dat 2 ben
    bracket = cq.Workplane('XY').box(125, 75, 475)
    b1 = bracket.translate((-190, 0, 475/2 + 15/2))
    b2 = bracket.translate(( 190, 0, 475/2 + 15/2))

    # 3. Mat bich (flange) - gan vao bracket
    flange = cq.Workplane('XY').circle(180).extrude(15)
    fl = flange.translate((0, 0, 475 + 15))

    # 4. Truc tron (shaft)
    shaft = cq.Workplane('YZ').circle(20).extrude(560)
    shaft = shaft.translate((-280, 0, 305 + 15))

    # 5. Truc bac (stepped shaft)
    s1 = cq.Workplane('YZ').circle(41).extrude(130)
    s2 = cq.Workplane('YZ').circle(30).extrude(150).translate((0,0,130))
    stepped = s1.union(s2).translate((-65, 0, 305 + 15))

    # 6. Mop rong (housing)
    housing = (cq.Workplane('XY')
               .box(200, 200, 65)
               .faces('>Z').workplane()
               .circle(60).cutBlind(-65))
    housing = housing.translate((0, 0, 475 + 15 + 65/2))

    # 7. Goi do truc (pillow block) - 2 cai
    pb_base = cq.Workplane('XY').box(100, 70, 15)
    pb_top  = cq.Workplane('XY').circle(30).extrude(50).translate((0,0,15+25))
    pb = pb_base.union(pb_top)
    p1 = pb.translate((-140, 0, 15))
    p2 = pb.translate(( 140, 0, 15))

    # Ghep tat ca
    assembly = plate
    for part in [b1, b2, fl, shaft, stepped, housing, p1, p2]:
        assembly = assembly.union(part)

    cq.exporters.export(assembly, 'assembly_test.step')
    print("[OK] Xuat thanh cong: assembly_test.step")
    print("     Mo file nay trong FreeCAD de kiem tra!")

except Exception as e:
    print(f"[FAIL] {e}")
    traceback.print_exc()