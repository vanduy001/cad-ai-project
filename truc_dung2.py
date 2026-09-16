import cadquery as cq

d1 = 32
d2 = 20
d_hole = 8
l1 = 40
l2 = 40
l3 = 60
r1 = d1 / 2
r2 = d2 / 2
total_length = l1 + l2 + l3

# Vẽ biên dạng: trục X = bán kính, trục Y = chiều dài dọc trục
profile = (
    cq.Workplane("XY")
    .moveTo(0, 0)
    .lineTo(r1, 0)
    .lineTo(r1, l1)
    .lineTo(r2, l1)
    .lineTo(r2, l1 + l2)
    .lineTo(r1, l1 + l2)
    .lineTo(r1, total_length)
    .lineTo(0, total_length)
    .close()
)

# Revolve quanh trục Y (mặc định) -> tạo hình trụ bậc
result = profile.revolve()

# Cắt lỗ xuyên tâm Ø8 (dọc theo trục Y)
hole = cq.Workplane("XZ").circle(d_hole / 2).extrude(total_length)
result = result.cut(hole)

result.val().exportStep("truc_dung2.step")