"""Test nhanh 4 chi tiet Phase 4."""
import cadquery as cq
import sys, math, traceback

tests = [
    {
        "name": "bevel_gear_m2_z20",
        "code": """
import cadquery as cq, math
_num_teeth=20; _module=2; _thickness=15; _bore_d=8; _cone_angle=45
_pitch_r=_module*_num_teeth/2
_ca=math.cos(math.radians(_cone_angle))
_outer_r=_pitch_r+_module*_ca; _root_r=_pitch_r-1.25*_module*_ca
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
_top_r=round(_outer_r*0.4,2); _cone_h=round(_outer_r*math.tan(math.radians(_cone_angle))*0.6,2)
_cone=cq.Workplane('XZ').workplane(offset=0).polyline([(0,0),(_outer_r+2,0),(_top_r,_cone_h),(0,_cone_h)]).close().revolve(360,[0,0,0],[0,1,0])
result=result.intersect(_cone)
if _bore_d>0: result=result.faces('>Z').workplane().hole(_bore_d)
""",
    },
    {
        "name": "sprocket_z16_p12.7",
        "code": """
import cadquery as cq, math
_num_teeth=16; _pitch=12.7; _thickness=8; _bore_d=15
_roller_d=_pitch*0.625
_pitch_r=_pitch/(2*math.sin(math.pi/_num_teeth))
_outer_r=_pitch_r+_roller_d/2; _root_r=_pitch_r-_roller_d/2-0.5
_tooth_angle=2*math.pi/_num_teeth; _half_tooth=math.pi/_num_teeth
_pts=[]
for _i in range(_num_teeth):
    _angle=_i*_tooth_angle
    _valley_steps=4
    for _j in range(_valley_steps+1):
        _a=_angle-_half_tooth+_tooth_angle*_j/_valley_steps
        _pts.append((round(_root_r*math.cos(_a),4),round(_root_r*math.sin(_a),4)))
    _tip_steps=3
    _tip_start=_angle-_half_tooth*0.3; _tip_end=_angle+_half_tooth*0.3
    for _j in range(1,_tip_steps):
        _a=_tip_start+(_tip_end-_tip_start)*_j/_tip_steps
        _pts.append((round(_outer_r*math.cos(_a),4),round(_outer_r*math.sin(_a),4)))
_filtered=[_pts[0]]
for _p in _pts[1:]:
    _prev=_filtered[-1]
    if math.sqrt((_p[0]-_prev[0])**2+(_p[1]-_prev[1])**2)>0.001: _filtered.append(_p)
result=cq.Workplane('XY').polyline(_filtered,includeCurrent=False).close().extrude(_thickness)
if _bore_d>0: result=result.faces('>Z').workplane().hole(_bore_d)
""",
    },
    {
        "name": "spring_d30_w3_n6",
        "code": """
import cadquery as cq, math
_coil_r=15; _wire_r=1.5; _pitch=10; _free_l=60
_total_segs=72; _segs_per_coil=12
_result=None
for _seg in range(_total_segs):
    _frac0=_seg/_total_segs; _frac1=(_seg+1)/_total_segs
    _angle0=_frac0*2*math.pi*(_total_segs/_segs_per_coil)
    _angle1=_frac1*2*math.pi*(_total_segs/_segs_per_coil)
    _x0=_coil_r*math.cos(_angle0); _y0=_coil_r*math.sin(_angle0); _z0=_frac0*_free_l
    _x1=_coil_r*math.cos(_angle1); _y1=_coil_r*math.sin(_angle1); _z1=_frac1*_free_l
    _mx=(_x0+_x1)/2; _my=(_y0+_y1)/2; _mz=(_z0+_z1)/2
    _sl=math.sqrt((_x1-_x0)**2+(_y1-_y0)**2+(_z1-_z0)**2)
    if _sl<0.001: continue
    _dx=(_x1-_x0)/_sl; _dy=(_y1-_y0)/_sl; _dz=(_z1-_z0)/_sl
    _cyl=cq.Workplane(cq.Plane(origin=(_mx,_my,_mz),normal=(_dx,_dy,_dz))).circle(_wire_r).extrude(_sl/2,both=True)
    _result=_cyl if _result is None else _result.union(_cyl)
result=_result
""",
    },
    {
        "name": "bearing_housing_od60_bd40",
        "code": """
import cadquery as cq
_od=60; _bd=40; _l=50; _fd=90; _ft=11; _bolt_n=4; _bolt_d=6; _pcd=68
result=cq.Workplane('XY').circle(_od/2).extrude(_l)
result=result.faces('>Z').workplane().hole(_bd)
_flange=cq.Workplane('XY').workplane(offset=-_ft).circle(_fd/2).extrude(_ft)
result=result.union(_flange)
result=result.faces('<Z').workplane().hole(_bd)
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
        print(f"[FAIL] {t['name']}: {e}")
        traceback.print_exc()
        fail+=1
print(f"\nKet qua: {ok} OK, {fail} FAIL")
if fail: sys.exit(1)