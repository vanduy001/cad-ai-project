import cadquery as cq

total_length = 86
total_height = 58
total_depth = 72
base_height = 22
top_height = total_height - base_height
mid_width = 40
seat_radius = 30
half_length = total_length / 2
half_mid_width = mid_width / 2

result = cq.Workplane("XY").box(total_length, total_depth, total_height)

cutter1 = cq.Workplane("YZ").center(0, total_height - seat_radius).circle(seat_radius).extrude(total_depth)
result = result.cut(cutter1)

cutter2 = cq.Workplane("XY").moveTo(-half_length, 0).lineTo(-half_mid_width, top_height).lineTo(-half_length, top_height).close().extrude(total_depth)
result = result.cut(cutter2)

cutter3 = cq.Workplane("XY").moveTo(half_length, 0).lineTo(half_mid_width, top_height).lineTo(half_length, top_height).close().extrude(total_depth)
result = result.cut(cutter3)

result.val().exportStep("h4a_output.step")