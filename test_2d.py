"""Chay thu xuat ban ve 2D (DXF) doc lap, khong can web.

Cach chay (trong terminal co (cadai)):
    python test_2d.py
Ket qua: file test_2d.dxf, mo bang FreeCAD hoac LibreCAD de xem.
"""
import cadquery as cq
from cadai.drawing_2d import export_dxf

# Chi tiet mau: tam day co lo xuyen o giua va 4 lo nho o goc
result = (
    cq.Workplane("XY")
    .box(80, 50, 15)
    .faces(">Z").workplane()
    .hole(20)
    .faces(">Z").workplane()
    .rect(60, 30, forConstruction=True)
    .vertices()
    .hole(6)
)

export_dxf(result, "test_2d.dxf")
print("OK - da tao test_2d.dxf")