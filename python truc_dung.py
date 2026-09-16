import cadquery as cq

# Thông số
d1 = 32        # Ø đoạn 1, 3
d2 = 20        # Ø đoạn 2
d_hole = 8     # Ø lỗ xuyên
l1 = 40        # chiều dài đoạn 1
l2 = 40        # chiều dài đoạn 2
l3 = 60        # chiều dài đoạn 3
r1 = d1 / 2    # bán kính đoạn 1, 3
r2 = d2 / 2    # bán kính đoạn 2

# Vẽ biên dạng mặt cắt ngang (từ tâm ra ngoài, dọc theo Z)
# Bắt đầu từ (0, 0)
profile = (
    cq.Workplane("YZ")
    .moveTo(0, 0)
    .lineTo(r1, 0)                    # Ø32 tại Z=0
    .lineTo(r1, l1)                   # kéo xuống Z=40
    .lineTo(r2, l1)                   # chuyển từ Ø32 sang Ø20 (mặt xiên)
    .lineTo(r2, l1 + l2)              # kéo xuống Z=80
    .lineTo(r1, l1 + l2)              # chuyển từ Ø20 sang Ø32
    .lineTo(r1, l1 + l2 + l3)         # kéo xuống Z=140
    .lineTo(0, l1 + l2 + l3)          # về tâm
    .close()
)

# Revolve quanh trục Z để tạo trục 3D
result = profile.revolve(axisEnd=(0, 0, l1 + l2 + l3), axisStart=(0, 0, 0))

# Cắt lỗ xuyên Ø8
hole = cq.Workplane("XY").circle(d_hole/2).extrude(l1 + l2 + l3)
result = result.cut(hole)

# Xuất file
result.val().exportStep("truc_dung.step")