import cadquery as cq

d1, l1 = 50, 20    # cổ 1
d2, l2 = 40, 10    # cổ 2
d3, l3 = 10, 10    # cổ 3
r1, r2, r3 = d1/2, d2/2, d3/2

seg1 = cq.Workplane("XY").circle(r1).extrude(l1)
seg2 = cq.Workplane("XY").workplane(offset=l1).circle(r2).extrude(l2)
seg3 = cq.Workplane("XY").workplane(offset=l1 + l2).circle(r3).extrude(l3)

result = seg1.union(seg2).union(seg3)

# Lỗ khoan ở đầu cổ Ø50 (mặt Z=0), sâu 15mm, đường kính 3mm
hole_d = 3
hole_r = hole_d / 2
hole_depth = 15

hole = cq.Workplane("XY").circle(hole_r).extrude(hole_depth)
result = result.cut(hole)

result.val().exportStep("truc_3co.step")