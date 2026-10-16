"""
Test nhanh ca 4 chi tiet giai doan 1.
Chay: python test_phase1.py
Ket qua: 4 file STEP trong thu muc hien tai.
"""
import cadquery as cq
import sys

tests = [
    {
        "name": "washer_M8",
        "code": """
result = cq.Workplane('XY').circle(16 / 2).extrude(1.6)
result = result.faces('>Z').workplane().hole(8.4)
""",
    },
    {
        "name": "pin_5x30",
        "code": """
result = cq.Workplane('XY').circle(5 / 2).extrude(30)
result = result.edges('<Z').chamfer(0.25)
result = result.edges('>Z').chamfer(0.25)
""",
    },
    {
        "name": "flat_plate_100x60",
        "code": """
result = cq.Workplane('XY').box(100, 60, 5)
_margin = 5.0
_hx = 100/2 - _margin
_hy = 60/2 - _margin
result = result.faces('>Z').workplane().pushPoints([
    (_hx, _hy), (-_hx, _hy), (_hx, -_hy), (-_hx, -_hy)
]).hole(6)
""",
    },
    {
        "name": "countersunk_screw_M6x30",
        "code": """
result = cq.Workplane('XY').circle(6 / 2).extrude(30)
result = result.edges('<Z').chamfer(0.3)
_r1 = 12.0 / 2
_r2 = 6 / 2
_hh = 3.6
_head = cq.Workplane('XY').workplane(offset=30).add(
    cq.Solid.makeCone(_r1, _r2, _hh)
)
result = result.union(_head)
""",
    },
]

ok = 0
fail = 0
for t in tests:
    try:
        exec(t["code"])
        fname = f"{t['name']}.step"
        cq.exporters.export(result, fname)
        print(f"[OK] {t['name']} -> {fname}")
        ok += 1
    except Exception as e:
        print(f"[FAIL] {t['name']}: {e}")
        fail += 1

print(f"\nKet qua: {ok} OK, {fail} FAIL")
if fail:
    sys.exit(1)