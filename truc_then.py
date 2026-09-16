import cadquery as cq

d1 = 25      # Ø25 f7 - đoạn trục lớn
d2 = 18      # Ø18 h7 - đoạn trục nhỏ
l1 = 60      # chiều dài đoạn Ø25 (giả định)
l2 = 40      # chiều dài đoạn Ø18 (giả định)
r1 = d1 / 2
r2 = d2 / 2
r_fillet = 1

seg1 = cq.Workplane("XY").circle(r1).extrude(l1)
seg2 = cq.Workplane("XY").workplane(offset=l1).circle(r2).extrude(l2)

result = seg1.union(seg2)
result = result.edges().fillet(r_fillet)

# Rãnh then: rộng 8mm, sâu 4mm (tính từ bề mặt trục), dài 40mm
b = 8
t1 = 4
L = 40
keyway_start = 10

keyway_bottom_y = r1 - t1
safety_top = r1 + 5
cutter_height = safety_top - keyway_bottom_y
center_y = (keyway_bottom_y + safety_top) / 2
center_z = keyway_start + L / 2

cutter = cq.Workplane("XY").box(b, cutter_height, L)
cutter = cutter.translate((0, center_y, center_z))
result = result.cut(cutter)

result.val().exportStep("truc_then.step")