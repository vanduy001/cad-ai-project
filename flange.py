import cadquery as cq
import math

outer_diameter = 120
inner_diameter = 40
thickness = 20
n_holes = 6
hole_diameter = 8
pcd = 90

result = (
    cq.Workplane("XY")
    .circle(outer_diameter / 2)
    .circle(inner_diameter / 2)
    .extrude(thickness)
)

positions = []
for i in range(n_holes):
    angle = 2 * math.pi * i / n_holes
    x = (pcd / 2) * math.cos(angle)
    y = (pcd / 2) * math.sin(angle)
    positions.append((x, y))

result = (
    result.faces(">Z").workplane()
    .pushPoints(positions)
    .hole(hole_diameter)
)

result.val().exportStep("flange_output.step")