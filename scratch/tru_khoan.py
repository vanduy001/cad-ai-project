import cadquery as cq

D = 100      # đường kính trụ (mm)
H = 200      # chiều cao trụ (mm)
r = D / 2

result = cq.Workplane("XY").circle(r).extrude(H)

# Lỗ khoan ngang: cao 100mm tính từ đáy, đường kính 20mm, xuyên qua thân
hole_horizontal_d = 20
hole_horizontal_r = hole_horizontal_d / 2
height_from_base = 100

horizontal_hole = (
    cq.Workplane("YZ")
    .move(0, height_from_base)
    .circle(hole_horizontal_r)
    .extrude(D + 20, both=True)
)
result = result.cut(horizontal_hole)

# Lỗ khoan ở tâm 2 mặt đáy, sâu 30mm (giả định đường kính = 20mm)
center_hole_d = 20
center_hole_r = center_hole_d / 2
depth = 30

bottom_hole = cq.Workplane("XY").circle(center_hole_r).extrude(depth)
result = result.cut(bottom_hole)

top_hole = cq.Workplane("XY").workplane(offset=H).circle(center_hole_r).extrude(-depth)
result = result.cut(top_hole)

result.val().exportStep("tru_khoan.step")