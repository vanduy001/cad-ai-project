"""Test nhanh 4 chi tiet Phase 3."""
import cadquery as cq
import sys, math

tests = [
    {
        "name": "key_square",
        "code": """
import cadquery as cq
_l=50; _w=10; _h=8
result=cq.Workplane('XY').box(_l,_w,_h)
""",
    },
    {
        "name": "key_rounded",
        "code": """
import cadquery as cq
_l=50; _w=10; _h=8
result=cq.Workplane('XY').box(_l,_w,_h)
_r=min(_w,_h)/2-0.01
result=result.edges('|Z').fillet(_r)
""",
    },
    {
        "name": "retaining_ring",
        "code": """
import cadquery as cq, math
_od=40; _id=34; _t=1.5; _gap=30
_or=_od/2; _ir=_id/2; _hg=_gap/2
_steps=48; _start=_hg; _end=360-_hg; _span=_end-_start
_outer=[( round(_or*math.cos(math.radians(_start+_span*i/_steps)),4),
          round(_or*math.sin(math.radians(_start+_span*i/_steps)),4) ) for i in range(_steps+1)]
_inner=[( round(_ir*math.cos(math.radians(_end-_span*i/_steps)),4),
          round(_ir*math.sin(math.radians(_end-_span*i/_steps)),4) ) for i in range(_steps+1)]
_pts=_outer+_inner
result=cq.Workplane('XY').polyline(_pts,includeCurrent=False).close().extrude(_t)
""",
    },
    {
        "name": "bushing",
        "code": """
import cadquery as cq
_od=30; _id=20; _l=40
result=cq.Workplane('XY').circle(_od/2).extrude(_l)
result=result.faces('>Z').workplane().hole(_id)
""",
    },
    {
        "name": "end_cap",
        "code": """
import cadquery as cq
_od=80; _bore=25; _t=15; _ft=6; _hub_d=44; _hub_l=9
_bolt_n=4; _bolt_d=6; _pcd=60
result=cq.Workplane('XY').circle(_od/2).extrude(_ft)
_hub=cq.Workplane('XY').workplane(offset=_ft).circle(_hub_d/2).extrude(_hub_l)
result=result.union(_hub)
result=result.faces('>Z').workplane().hole(_bore)
result=result.faces('<Z').workplane().polarArray(_pcd/2,0,360,_bolt_n).hole(_bolt_d)
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
        import traceback
        print(f"[FAIL] {t['name']}: {e}")
        traceback.print_exc()
        fail+=1
print(f"\nKet qua: {ok} OK, {fail} FAIL")
if fail: sys.exit(1)