import cadquery as cq
import math

d_outer = 60
d_center = 15
d_bolt = 10
pcd = 45
thickness = 20
n_holes = 6

r_outer = d_outer / 2
r_center = d_center / 2
r_bolt = d_bolt / 2
r_pcd = pcd / 2

result = (
    cq.Workplane("XY")
    .circle(r_outer)
    .circle(r_center)
    .extrude(thickness)
)

positions = []
for i in range(n_holes):
    angle = 2 * math.pi * i / n_holes
    x = r_pcd * math.cos(angle)
    y = r_pcd * math.sin(angle)
    positions.append((x, y))

result = (
    result.faces(">Z").workplane()
    .pushPoints(positions)
    .hole(d_bolt)
)

result.val().exportStep("ct2_output.step")