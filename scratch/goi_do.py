import cadquery as cq

# ---- Thông số theo bản vẽ (một số là giả định hợp lý, sẽ ghi chú) ----
base_width = 120
total_length = 144
depth = 78
body_height = 42
wall_height = 17
top_flat_half = 35        # giả định: nửa rộng mặt trên trước khi vát
tab_width = 15
tab_height = 8             # giả định: bản vẽ không ghi chiều cao gờ
seat_radius = 29
bore_big = 64
bore_small = 38
cbore_depth = 8            # giả định: chiều sâu lỗ khoét bậc

half_base = base_width / 2
lug_len = (total_length - base_width) / 2   # tai mỗi bên = 12mm

# ---- Mặt cắt ngang thân chính (mặt XY, extrude theo Z = chiều sâu) ----
profile = (
    cq.Workplane("XY")
    .moveTo(-half_base, 0)
    .lineTo(half_base, 0)
    .lineTo(half_base, wall_height)
    .lineTo(top_flat_half, body_height)
    .lineTo(tab_width / 2, body_height)
    .lineTo(tab_width / 2, body_height + tab_height)
    .lineTo(-tab_width / 2, body_height + tab_height)
    .lineTo(-tab_width / 2, body_height)
    .lineTo(-top_flat_half, body_height)
    .lineTo(-half_base, wall_height)
    .close()
)
result = profile.extrude(depth)

# ---- Cắt rãnh cong đặt trục (bán kính 29), tâm ở đỉnh khối ----
seat_cutter = cq.Workplane("XY").center(0, body_height).circle(seat_radius).extrude(depth)
result = result.cut(seat_cutter)

# ---- Thêm 2 tai bắt bu-lông ở 2 đầu ----
lug_right = (
    cq.Workplane("XY")
    .moveTo(half_base, 0).lineTo(half_base + lug_len, 0)
    .lineTo(half_base + lug_len, wall_height).lineTo(half_base, wall_height)
    .close().extrude(depth)
)
lug_left = (
    cq.Workplane("XY")
    .moveTo(-half_base, 0).lineTo(-half_base - lug_len, 0)
    .lineTo(-half_base - lug_len, wall_height).lineTo(-half_base, wall_height)
    .close().extrude(depth)
)
result = result.union(lug_right).union(lug_left)

# ---- Khoan lỗ bậc ở tâm (đường kính lớn 64, đường kính nhỏ xuyên 38) ----
bore_plane = cq.Workplane("XZ").workplane(offset=wall_height)
cbore_cutter = bore_plane.center(0, depth / 2).circle(bore_big / 2).extrude(-cbore_depth)
through_cutter = bore_plane.center(0, depth / 2).circle(bore_small / 2).extrude(-wall_height)
result = result.cut(cbore_cutter).cut(through_cutter)

result.val().exportStep("goi_do_truc.step")