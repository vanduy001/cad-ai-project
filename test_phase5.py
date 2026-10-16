"""Test nhanh 4 chi tiet Phase 5."""
import cadquery as cq
import sys, math, traceback

tests = [
    {
        "name": "rack_m2_z10",
        "code": """
import cadquery as cq, math
_module=2; _num_teeth=10; _thickness=20; _height=8; _width=15
_pitch=math.pi*_module; _addendum=_module; _dedendum=1.25*_module
_tooth_h=_addendum+_dedendum; _pa=math.radians(20)
_tth=_addendum*math.tan(_pa); _tbh=_dedendum*math.tan(_pa)
_total_l=_pitch*_num_teeth
_pts=[]
for _i in range(_num_teeth):
    _xb=_i*_pitch
    _pts.append((_xb+_tbh, 0))
    _pts.append((_xb+_pitch/2-_tth, _tooth_h))
    _pts.append((_xb+_pitch/2+_tth, _tooth_h))
    _pts.append((_xb+_pitch-_tbh, 0))
_all_pts=[(0,0)]+_pts+[(_total_l,0),(_total_l,-_height+_tooth_h),(0,-_height+_tooth_h)]
result=cq.Workplane('XY').polyline(_all_pts,includeCurrent=False).close().extrude(_width)
""",
    },
    {
        "name": "worm_d30_l60",
        "code": """
import cadquery as cq
_od=15; _rd=12; _l=60; _bore=9; _module=3
_tooth_w=9.42; _pa_offset=1.09
result=cq.Workplane('XY').circle(_od).extrude(_l)
result=result.faces('>Z').workplane().hole(_bore)
""",
    },
       {
        "name": "piston_d80_l100",
        "code": """
import cadquery as cq
_d=80; _l=100; _pin_d=22; _wt=8; _n_rings=2
_rw=4; _rd=2; _crown_h=10; _ring_start=14
result=cq.Workplane('XY').circle(_d/2).extrude(_l)
_inner_d=_d-2*_wt
result=result.faces('>Z').workplane().circle(_inner_d/2).cutBlind(-(_l-_crown_h))
for _ri in range(_n_rings):
    _rz=_ring_start+_ri*(_rw+_rw*1.5)
    _groove_pts=[(_d/2-_rd,_l-_rz),(_d/2+1,_l-_rz),(_d/2+1,_l-_rz-_rw),(_d/2-_rd,_l-_rz-_rw)]
    _groove=cq.Workplane('XZ').workplane(offset=0).polyline(_groove_pts).close().revolve(360,[0,0,0],[0,1,0])
    result=result.cut(_groove)
_pin_z=_l/2-_crown_h-(_n_rings+1)*_rw*3
result=(
    result
    .workplane(offset=_pin_z)
    .center(0,0)
    .moveTo(0,0)
    .circle(_pin_d/2)
    .cutThruAll()
)
""",
    },
    {
        "name": "connecting_rod",
        "code": """
import cadquery as cq
_l=150; _big_r=25; _small_r=15; _t=20; _big_bore=28; _small_bore=15; _bw=18
_big_end=cq.Workplane('XY').circle(_big_r).extrude(_t)
_big_end=_big_end.faces('>Z').workplane().hole(_big_bore)
_small_end=cq.Workplane('XY').workplane(offset=0).center(0,_l).circle(_small_r).extrude(_t)
_small_end=_small_end.faces('>Z').workplane().hole(_small_bore)
_beam_pts=[(-_bw/2,_big_r*0.8),(-_bw/2*0.6,_l-_small_r*0.8),(_bw/2*0.6,_l-_small_r*0.8),(_bw/2,_big_r*0.8)]
_beam=cq.Workplane('XY').polyline(_beam_pts,includeCurrent=False).close().extrude(_t)
result=_big_end.union(_small_end).union(_beam)
""",
    },
]

ok=0; fail=0
for t in tests:
    try:
        ns={}; exec(t["code"],ns)
        cq.exporters.export(ns["result"], f"{t['name']}.step")
        print(f"[OK] {t['name']}")
        ok+=1
    except Exception as e:
        print(f"[FAIL] {t['name']}: {e}")
        traceback.print_exc()
        fail+=1
print(f"\nKet qua: {ok} OK, {fail} FAIL")
if fail: sys.exit(1)