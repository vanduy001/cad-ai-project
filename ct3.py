import cadquery as cq

d_bore = 20
d_hub = 35
d_flange = 50
l_hub = 20
l_flange = 15
l_total = 45
l_end = l_total - l_hub - l_flange   # = 10mm, phần giả định

r_bore = d_bore / 2
r_hub = d_hub / 2
r_flange = d_flange / 2

seg1 = cq.Workplane("XY").circle(r_hub).extrude(l_hub)
seg2 = cq.Workplane("XY").workplane(offset=l_hub).circle(r_flange).extrude(l_flange)
seg3 = cq.Workplane("XY").workplane(offset=l_hub + l_flange).circle(r_hub).extrude(l_end)

result = seg1.union(seg2).union(seg3)

hole = cq.Workplane("XY").circle(r_bore).extrude(l_total)
result = result.cut(hole)

keyway_width = 5
keyway_depth = 8
key_height = 4

key_box = cq.Workplane("XY").box(keyway_width, key_height, keyway_depth)
key_box = key_box.translate((0, r_bore + key_height/2, l_total - keyway_depth/2))
result = result.cut(key_box)

result.val().exportStep("ct3_output.step")