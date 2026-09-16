import cadquery as cq

d1 = 32
d2 = 20
d_hole = 8
l1 = 40
l2 = 40
l3 = 60
r_fillet = 1

# Đoạn 1 (trái): Ø32 × 40, từ Z=0 đến Z=40
seg1 = cq.Workplane("XY").circle(d1/2).extrude(l1)

# Đoạn 2 (giữa): Ø20 × 40, từ Z=40 đến Z=80
seg2 = cq.Workplane("XY").moveTo(0, 0).circle(d2/2).extrude(l2)
seg2 = seg2.translate((0, 0, l1))

# Đoạn 3 (phải): Ø32 × 60, từ Z=80 đến Z=140
seg3 = cq.Workplane("XY").circle(d1/2).extrude(l3)
seg3 = seg3.translate((0, 0, l1 + l2))

# Union tất cả
result = seg1.union(seg2).union(seg3)

# Bo tròn cạnh
result = result.edges().fillet(r_fillet)

# Cắt lỗ xuyên Ø8
hole = cq.Workplane("XY").circle(d_hole/2).extrude(l1 + l2 + l3)
result = result.cut(hole)

result.val().exportStep("truc_output.step")