"""Test nhanh 4 chi tiet giai doan 2."""
import cadquery as cq
import sys, math

tests = [
       {
        "name": "spur_gear_m2_z20",
        "code": """
import cadquery as cq, math
_num_teeth=20; _module=2; _thickness=15; _bore_d=8
_pitch_r=_module*_num_teeth/2; _outer_r=_pitch_r+_module; _root_r=_pitch_r-1.25*_module
_tooth_angle=2*math.pi/_num_teeth; _half_tooth=math.pi/_num_teeth
_pts=[]
for _i in range(_num_teeth):
    _angle=_i*_tooth_angle
    _a0=_angle-_half_tooth*0.45
    _pts.append((round(_root_r*math.cos(_a0),4),round(_root_r*math.sin(_a0),4)))
    for _frac in (0.35,0.7):
        _r=_root_r+(_outer_r-_root_r)*_frac; _a=_angle-_half_tooth*0.35*(1-_frac)
        _pts.append((round(_r*math.cos(_a),4),round(_r*math.sin(_a),4)))
    _pts.append((round(_outer_r*math.cos(_angle),4),round(_outer_r*math.sin(_angle),4)))
    for _frac in (0.7,0.35):
        _r=_root_r+(_outer_r-_root_r)*_frac; _a=_angle+_half_tooth*0.35*(1-_frac)
        _pts.append((round(_r*math.cos(_a),4),round(_r*math.sin(_a),4)))
    _a1=_angle+_half_tooth*0.45
    _pts.append((round(_root_r*math.cos(_a1),4),round(_root_r*math.sin(_a1),4)))
_filtered=[_pts[0]]
for _p in _pts[1:]:
    _prev=_filtered[-1]
    if math.sqrt((_p[0]-_prev[0])**2+(_p[1]-_prev[1])**2)>0.001: _filtered.append(_p)
result=cq.Workplane('XY').polyline(_filtered,includeCurrent=False).close().extrude(_thickness)
if _bore_d>0: result=result.faces('>Z').workplane().hole(_bore_d)
""",
    },
    {
        "name": "pulley_100x20",
        "code": """
import cadquery as cq, math
_od=100; _bore=20; _w=40; _gd=8; _ga=math.radians(38)
_hub_d=40; _hub_l=24
result=cq.Workplane('XY').circle(_od/2).extrude(_w)
_groove_top_r=_od/2; _groove_bot_r=_groove_top_r-_gd
_groove_half_w=_gd*math.tan(_ga); _mid=_w/2
_pts=[(_groove_top_r,_mid-_groove_half_w),(_groove_bot_r,_mid),
      (_groove_top_r,_mid+_groove_half_w),(_groove_top_r+2,_mid+_groove_half_w),
      (_groove_top_r+2,_mid-_groove_half_w)]
_groove_wire=cq.Workplane('XZ').workplane(offset=0).polyline(_pts).close().revolve(360,[0,0,0],[0,1,0])
result=result.cut(_groove_wire)
_hub=cq.Workplane('XY').workplane(offset=-(_hub_l-_w)/2).circle(_hub_d/2).extrude(_hub_l)
result=result.union(_hub)
result=result.faces('>Z').workplane().hole(_bore)
""",
    },
    {
        "name": "cam_eccentric",
        "code": """
import cadquery as cq
_r=25; _ecc=5; _thickness=20; _bore=10
result=cq.Workplane('XY').center(_ecc,0).circle(_r).extrude(_thickness)
result=result.faces('>Z').workplane().hole(_bore)
""",
    },
    {
        "name": "coupling_50x20x80",
        "code": """
import cadquery as cq
_od=50; _bore=20; _total_l=80; _ft=8
_hub_l=(_total_l-2*_ft)/2; _hub_d=36
_bolt_n=4; _bolt_d=6; _pcd=38
result=cq.Workplane('XY').circle(_od/2).extrude(_ft)
_hub_left=cq.Workplane('XY').workplane(offset=_ft).circle(_hub_d/2).extrude(_hub_l)
result=result.union(_hub_left)
_hub_right=cq.Workplane('XY').workplane(offset=_ft+_hub_l).circle(_hub_d/2).extrude(_hub_l)
result=result.union(_hub_right)
_flange_right=cq.Workplane('XY').workplane(offset=_total_l-_ft).circle(_od/2).extrude(_ft)
result=result.union(_flange_right)
result=result.faces('>Z').workplane().hole(_bore)
result=result.faces('>Z').workplane().polarArray(_pcd/2,0,360,_bolt_n).hole(_bolt_d)
""",
    },
]

ok=0; fail=0
for t in tests:
    try:
        ns={}; exec(t["code"],ns); result=ns["result"]
        cq.exporters.export(result, f"{t['name']}.step")
        print(f"[OK] {t['name']}")
        ok+=1
    except Exception as e:
        print(f"[FAIL] {t['name']}: {e}")
        fail+=1
print(f"\nKet qua: {ok} OK, {fail} FAIL")
if fail: sys.exit(1)