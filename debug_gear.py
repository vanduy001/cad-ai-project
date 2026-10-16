import cadquery as cq
import math
import traceback

_num_teeth = 20
_module = 2
_thickness = 15
_bore_d = 8

_pitch_r = _module * _num_teeth / 2
_outer_r = _pitch_r + _module
_root_r = _pitch_r - 1.25 * _module
_tooth_angle = 2 * math.pi / _num_teeth
_half_tooth = math.pi / _num_teeth

_pts = []
for _i in range(_num_teeth):
    _angle = _i * _tooth_angle

    # Chan rang trai
    _a0 = _angle - _half_tooth * 0.45
    _pts.append((round(_root_r * math.cos(_a0), 4), round(_root_r * math.sin(_a0), 4)))

    # Suon trai (chi 2 diem trung gian, KHONG them frac=1.0 vi se trung dinh rang)
    for _frac in (0.35, 0.7):
        _r = _root_r + (_outer_r - _root_r) * _frac
        _a = _angle - _half_tooth * 0.35 * (1 - _frac)
        _pts.append((round(_r * math.cos(_a), 4), round(_r * math.sin(_a), 4)))

    # Dinh rang
    _pts.append((round(_outer_r * math.cos(_angle), 4), round(_outer_r * math.sin(_angle), 4)))

    # Suon phai (chi 2 diem trung gian)
    for _frac in (0.7, 0.35):
        _r = _root_r + (_outer_r - _root_r) * _frac
        _a = _angle + _half_tooth * 0.35 * (1 - _frac)
        _pts.append((round(_r * math.cos(_a), 4), round(_r * math.sin(_a), 4)))

    # Chan rang phai
    _a1 = _angle + _half_tooth * 0.45
    _pts.append((round(_root_r * math.cos(_a1), 4), round(_root_r * math.sin(_a1), 4)))

print("So diem:", len(_pts))

# Loc bo diem trung
_filtered = [_pts[0]]
for _p in _pts[1:]:
    _prev = _filtered[-1]
    _dist = math.sqrt((_p[0]-_prev[0])**2 + (_p[1]-_prev[1])**2)
    if _dist > 0.001:
        _filtered.append(_p)

print("Sau khi loc:", len(_filtered))

try:
    result = cq.Workplane('XY').polyline(_filtered, includeCurrent=False).close().extrude(_thickness)
    print("extrude OK")
    if _bore_d > 0:
        result = result.faces('>Z').workplane().hole(_bore_d)
    print("ALL OK")
    cq.exporters.export(result, "test_gear.step")
    print("Xuat STEP OK")
except Exception as e:
    traceback.print_exc()