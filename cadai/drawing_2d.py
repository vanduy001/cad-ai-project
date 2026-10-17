"""Xuat ban ve ky thuat 2D (DXF) tu mo hinh CadQuery.

Noi dung ban ve:
- Khung ban ve A4 / A3 (nam ngang), le trai 20mm, cac le khac 5mm.
- Khung ten (ten chi tiet, vat lieu, ty le, kho giay, ngay ve...).
- Ba hinh chieu theo goc chieu thu nhat (TCVN/ISO): dung (nhin tu -Y),
  bang (nhin tu +Z, dat duoi hinh dung), canh (nhin tu trai -X, dat ben phai).
- Net thay (lien dam), net khuat (net dut), duong tam (net cham gach).
- Kich thuoc: bao ngoai, duong kinh (lo, truc bac), ban kinh bo goc, vi tri lo,
  duong tron chia lo (PCD), cac bac theo chieu dai.
- Yeu cau ky thuat: dung sai chung, dung sai tung kich thuoc, do nham be mat.

Ty le tu dong chon theo day chuan: 10:1, 5:1, 2:1, 1:1, 1:2, 1:5, 1:10, ...
"""
import datetime
import math
import textwrap
import unicodedata

import cadquery as cq
import ezdxf
from ezdxf import const
from ezdxf.enums import TextEntityAlignment
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.GeomAbs import GeomAbs_Cylinder, GeomAbs_Plane
from OCP.HLRAlgo import HLRAlgo_Projector
from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape
from OCP.TopAbs import TopAbs_IN
from OCP.gp import gp_Ax2, gp_Dir, gp_Pnt

SHEETS = {"A4": (297.0, 210.0), "A3": (420.0, 297.0)}
SCALES = [10, 5, 2, 1, 0.5, 0.2, 0.1, 0.05, 0.02, 0.01]

# Khung ban ve (mm tren to giay)
MARGIN_LEFT = 20.0
MARGIN_OTHER = 5.0
TB_W, TB_H = 180.0, 50.0          # khung ten
DIM_OFF = 9.0                     # khoang cach duong kich thuoc dau tien so voi hinh
DIM_SP = 8.0                      # khoang cach giua cac duong kich thuoc xep chong
DIM_TAIL = 5.0                    # cho de chu cua duong kich thuoc ngoai cung
BLOCK_PAD = 8.0                   # khoang trong giua cac hinh chieu

# huong nhin ra phia nguoi xem, huong truc x cua hinh chieu
_VIEWS = {
    "front": ((0, -1, 0), (1, 0, 0)),   # x = X, y = Z
    "top": ((0, 0, 1), (1, 0, 0)),      # x = X, y = Y
    "left": ((-1, 0, 0), (0, -1, 0)),   # x = -Y, y = Z
}
# truc cua tru -> hinh chieu nhin thay duong tron
_CIRCLE_VIEW = {2: "top", 1: "front", 0: "left"}

PART_NAMES = {
    "plate": "TAM PHANG", "flat_plate": "TAM PHANG", "bracket": "GIA DO",
    "flange": "MAT BICH", "shaft": "TRUC", "stepped_shaft": "TRUC BAC",
    "housing": "THAN HOP", "pillow_block": "GOI DO", "bolt": "BU LONG",
    "nut": "DAI OC", "washer": "VONG DEM", "pin": "CHOT",
    "countersunk_screw": "VIT CHIM", "spur_gear": "BANH RANG TRU",
    "pulley": "PULI", "cam": "CAM", "coupling": "KHOP NOI", "key": "THEN",
    "retaining_ring": "VONG HAM", "bushing": "BAC LOT", "end_cap": "NAP CHAN",
    "bevel_gear": "BANH RANG CON", "sprocket": "DIA XICH", "spring": "LO XO",
    "bearing_housing": "GOI DO O LAN", "rack": "THANH RANG", "worm": "TRUC VIT",
    "piston": "PISTON", "connecting_rod": "THANH TRUYEN",
}


# ----------------------------------------------------------------------------
# Tien ich
# ----------------------------------------------------------------------------
def _ascii(s):
    """Bo dau tieng Viet de moi trinh xem DXF deu hien thi duoc."""
    if s is None:
        return ""
    s = str(s).replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


# ----------------------------------------------------------------------------
# Che do tuong thich: chu, kich thuoc, net dut ve bang hinh hoc co ban
# (LINE / LWPOLYLINE / SOLID) de MOI trinh xem DXF deu hien thi duoc, ke ca cac
# trinh xem don gian khong ve TEXT, DIMENSION va kieu net.
# ----------------------------------------------------------------------------
# Phong chu net don, luoi 4 x 6 (rong x cao chu hoa), goc duoi-trai la (0, 0)
_GLYPHS = {
    "0": [[(0, 1), (0, 5), (1, 6), (3, 6), (4, 5), (4, 1), (3, 0), (1, 0), (0, 1)]],
    "1": [[(1, 5), (2, 6), (2, 0)], [(1, 0), (3, 0)]],
    "2": [[(0, 5), (1, 6), (3, 6), (4, 5), (4, 4), (0, 0), (4, 0)]],
    "3": [[(0, 5), (1, 6), (3, 6), (4, 5), (4, 4), (3, 3), (1, 3)],
          [(3, 3), (4, 2), (4, 1), (3, 0), (1, 0), (0, 1)]],
    "4": [[(3, 0), (3, 6), (0, 2), (4, 2)]],
    "5": [[(4, 6), (0, 6), (0, 3), (3, 3), (4, 2), (4, 1), (3, 0), (1, 0), (0, 1)]],
    "6": [[(4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)]],
    "7": [[(0, 6), (4, 6), (1, 0)]],
    "8": [[(1, 3), (0, 4), (0, 5), (1, 6), (3, 6), (4, 5), (4, 4), (3, 3), (1, 3),
           (0, 2), (0, 1), (1, 0), (3, 0), (4, 1), (4, 2), (3, 3)]],
    "9": [[(0, 1), (1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 4), (1, 3), (4, 3)]],
    "A": [[(0, 0), (2, 6), (4, 0)], [(1, 2), (3, 2)]],
    "B": [[(0, 0), (0, 6), (3, 6), (4, 5), (4, 4), (3, 3), (0, 3)],
          [(3, 3), (4, 2), (4, 1), (3, 0), (0, 0)]],
    "C": [[(4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0), (3, 0), (4, 1)]],
    "D": [[(0, 0), (0, 6), (2, 6), (4, 4), (4, 2), (2, 0), (0, 0)]],
    "E": [[(4, 6), (0, 6), (0, 0), (4, 0)], [(0, 3), (3, 3)]],
    "F": [[(4, 6), (0, 6), (0, 0)], [(0, 3), (3, 3)]],
    "G": [[(4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0), (3, 0), (4, 1), (4, 3), (2, 3)]],
    "H": [[(0, 0), (0, 6)], [(4, 0), (4, 6)], [(0, 3), (4, 3)]],
    "I": [[(1, 6), (3, 6)], [(2, 6), (2, 0)], [(1, 0), (3, 0)]],
    "J": [[(4, 6), (4, 1), (3, 0), (1, 0), (0, 1)]],
    "K": [[(0, 0), (0, 6)], [(4, 6), (0, 3), (4, 0)]],
    "L": [[(0, 6), (0, 0), (4, 0)]],
    "M": [[(0, 0), (0, 6), (2, 3), (4, 6), (4, 0)]],
    "N": [[(0, 0), (0, 6), (4, 0), (4, 6)]],
    "O": [[(1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5), (4, 1), (3, 0), (1, 0)]],
    "P": [[(0, 0), (0, 6), (3, 6), (4, 5), (4, 4), (3, 3), (0, 3)]],
    "Q": [[(1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5), (4, 1), (3, 0), (1, 0)], [(2, 2), (4, 0)]],
    "R": [[(0, 0), (0, 6), (3, 6), (4, 5), (4, 4), (3, 3), (0, 3)], [(2, 3), (4, 0)]],
    "S": [[(4, 5), (3, 6), (1, 6), (0, 5), (0, 4), (1, 3), (3, 3), (4, 2), (4, 1), (3, 0), (1, 0), (0, 1)]],
    "T": [[(0, 6), (4, 6)], [(2, 6), (2, 0)]],
    "U": [[(0, 6), (0, 1), (1, 0), (3, 0), (4, 1), (4, 6)]],
    "V": [[(0, 6), (2, 0), (4, 6)]],
    "W": [[(0, 6), (1, 0), (2, 3), (3, 0), (4, 6)]],
    "X": [[(0, 6), (4, 0)], [(0, 0), (4, 6)]],
    "Y": [[(0, 6), (2, 3), (4, 6)], [(2, 3), (2, 0)]],
    "Z": [[(0, 6), (4, 6), (0, 0), (4, 0)]],
    ".": [[(1.5, 0), (2.5, 0), (2.5, 0.8), (1.5, 0.8), (1.5, 0)]],
    ",": [[(2, 0.8), (2, 0), (1.4, -1)]],
    ":": [[(1.5, 1), (2.5, 1), (2.5, 1.8), (1.5, 1.8), (1.5, 1)],
          [(1.5, 4), (2.5, 4), (2.5, 4.8), (1.5, 4.8), (1.5, 4)]],
    "-": [[(0.5, 3), (3.5, 3)]],
    "+": [[(0.5, 3), (3.5, 3)], [(2, 1.5), (2, 4.5)]],
    "=": [[(0.5, 2), (3.5, 2)], [(0.5, 4), (3.5, 4)]],
    "/": [[(0, 0), (4, 6)]],
    "(": [[(3, 6), (1.5, 4.5), (1.5, 1.5), (3, 0)]],
    ")": [[(1, 6), (2.5, 4.5), (2.5, 1.5), (1, 0)]],
    "_": [[(0, -1), (4, -1)]],
    "±": [[(0.5, 4.5), (3.5, 4.5)], [(2, 3), (2, 6)], [(0.5, 1), (3.5, 1)]],
    "×": [[(0.5, 1.5), (3.5, 4.5)], [(0.5, 4.5), (3.5, 1.5)]],
    "Ø": [[(1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5), (4, 1), (3, 0), (1, 0)], [(0, 0), (4, 6)]],
    "°": [[(1, 5), (2, 6), (3, 5), (2, 4), (1, 5)]],
}
_ADV = {" ": 3.0, ".": 3.0, ",": 3.0, ":": 3.0, "(": 4.0, ")": 4.0}


def _text_width(txt, h):
    k = h / 6.0
    t = str(txt).upper()
    if not t:
        return 0.0
    return (sum(_ADV.get(c, 6.0) for c in t) - 2.0) * k


def _poly(msp, pts, layer, width=0.0):
    if len(pts) < 2:
        return
    if len(pts) == 2 and not width:
        msp.add_line(pts[0], pts[1], dxfattribs={"layer": layer})
        return
    attrs = {"layer": layer}
    if width:
        attrs["const_width"] = width
    msp.add_lwpolyline(pts, dxfattribs=attrs)


def _stroke_text(msp, txt, x, y, h, layer, align="left", angle=0.0):
    """Ve chu bang net don. (x, y) la goc duong chu; align: left | center | right."""
    t = str(txt).upper()
    k = h / 6.0
    w = _text_width(t, h)
    cx = {"left": 0.0, "center": -w / 2.0, "right": -w}[align]
    ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    for ch in t:
        for stroke in _GLYPHS.get(ch, []):
            pts = []
            for px, py in stroke:
                lx, ly = cx + px * k, py * k
                pts.append((x + lx * ca - ly * sa, y + lx * sa + ly * ca))
            _poly(msp, pts, layer)
        cx += _ADV.get(ch, 6.0) * k


def _dash(msp, pts, pattern, layer, width=0.0):
    """Cat duong thanh cac doan net dut that. pattern = (net, trong, net, trong, ...) mm giay."""
    i, rem = 0, pattern[0]
    cur = [pts[0]]
    for a, b in zip(pts[:-1], pts[1:]):
        seg = math.dist(a, b)
        if seg < 1e-9:
            continue
        ux, uy = (b[0] - a[0]) / seg, (b[1] - a[1]) / seg
        pos = 0.0
        while seg - pos > 1e-9:
            step = min(rem, seg - pos)
            pos += step
            rem -= step
            q = (a[0] + ux * pos, a[1] + uy * pos)
            if i % 2 == 0:
                cur.append(q)
            if rem <= 1e-9:
                if i % 2 == 0:
                    _poly(msp, cur, layer, width)
                    cur = []
                i = (i + 1) % len(pattern)
                rem = pattern[i]
                if i % 2 == 0:
                    cur = [q]
    if i % 2 == 0 and len(cur) >= 2:
        _poly(msp, cur, layer, width)


def _center_line(msp, a, b):
    n = math.dist(a, b)
    pat = (12.0, 2.0, 1.0, 2.0) if n >= 30 else (6.0, 1.5, 1.0, 1.5)
    _dash(msp, [a, b], pat, "CENTER")


def _circle_pts(c, r, step_deg=3.0):
    n = max(24, int(360.0 / step_deg))
    return [(c[0] + r * math.cos(2 * math.pi * i / n), c[1] + r * math.sin(2 * math.pi * i / n))
            for i in range(n + 1)]


def _fmt_num(v):
    t = f"{v:.2f}".rstrip("0").rstrip(".")
    return t or "0"


def _dim_text(template, value, prefix=""):
    return (template or "<>").replace("<>", prefix + _fmt_num(value))


def _arrow(msp, tip, u, layer="DIM", length=3.0, hw=0.6):
    """Mui ten: dinh o `tip`, huong u (don vi) la huong mui ten chi toi."""
    bx, by = tip[0] - u[0] * length, tip[1] - u[1] * length
    nx, ny = -u[1], u[0]
    p1 = (bx + nx * hw, by + ny * hw)
    p2 = (bx - nx * hw, by - ny * hw)
    msp.add_lwpolyline([tip, p1, p2], close=True, dxfattribs={"layer": layer})
    msp.add_solid([tip, p1, p2], dxfattribs={"layer": layer})


def _dim_lin(msp, p1, p2, side, base, text, h=3.5, layer="DIM"):
    horiz = side in ("top", "bottom")
    L = 3.0
    at = {"layer": layer}
    if horiz:
        y = base[1]
        sg = 1.0 if y > p1[1] else -1.0
        for q in (p1, p2):
            msp.add_line((q[0], q[1] + sg * 1.0), (q[0], y + sg * 1.5), dxfattribs=at)
        lo, hi = sorted((p1[0], p2[0]))

        def pt(t):
            return (t, y)
        d_lo, d_hi = (-1.0, 0.0), (1.0, 0.0)
    else:
        x = base[0]
        sg = 1.0 if x > p1[0] else -1.0
        for q in (p1, p2):
            msp.add_line((q[0] + sg * 1.0, q[1]), (x + sg * 1.5, q[1]), dxfattribs=at)
        lo, hi = sorted((p1[1], p2[1]))

        def pt(t):
            return (x, t)
        d_lo, d_hi = (0.0, -1.0), (0.0, 1.0)
    span = hi - lo
    mid = (lo + hi) / 2.0
    if span >= 2 * L + 1.0:
        msp.add_line(pt(lo), pt(hi), dxfattribs=at)
        _arrow(msp, pt(lo), d_lo, layer)
        _arrow(msp, pt(hi), d_hi, layer)
    else:   # kich thuoc nho: mui ten nam ngoai
        msp.add_line(pt(lo - L - 1.0), pt(hi + L + 1.0), dxfattribs=at)
        _arrow(msp, pt(lo), d_hi, layer)
        _arrow(msp, pt(hi), d_lo, layer)
    tw = _text_width(text, h)
    if tw <= max(span - 1.0, 0.0):
        if horiz:
            _stroke_text(msp, text, mid, y + 1.0, h, layer, "center")
        else:
            _stroke_text(msp, text, x - 1.0, mid, h, layer, "center", angle=90)
    else:       # chu dai hon khoang -> dat ra ngoai dau tren/phai
        if horiz:
            _stroke_text(msp, text, hi + L + 2.0, y - h / 2.0, h, layer, "left")
        else:
            _stroke_text(msp, text, x + h / 2.0, hi + L + 2.0, h, layer, "left", angle=90)


def _dim_leader(msp, c, r, angle_deg, text, loc, h=3.5, layer="DIM"):
    """Duong dan ghi duong kinh / ban kinh: mui ten tren cung tron, chu tren vai ngang."""
    a = math.radians(angle_deg)
    edge = (c[0] + r * math.cos(a), c[1] + r * math.sin(a))
    dx, dy = edge[0] - loc[0], edge[1] - loc[1]
    n = math.hypot(dx, dy) or 1.0
    u = (dx / n, dy / n)
    tw = _text_width(text, h)
    side = 1.0 if math.cos(a) >= 0 else -1.0
    at = {"layer": layer}
    msp.add_line(loc, edge, dxfattribs=at)
    msp.add_line(loc, (loc[0] + side * (tw + 2.0), loc[1]), dxfattribs=at)
    _arrow(msp, edge, u, layer)
    if side > 0:
        _stroke_text(msp, text, loc[0] + 1.0, loc[1] + 1.0, h, layer, "left")
    else:
        _stroke_text(msp, text, loc[0] - 1.0, loc[1] + 1.0, h, layer, "right")


def _scale_text(s):
    return f"{s:g}:1" if s >= 1 else f"1:{1 / s:g}"


def _to_shape(obj):
    if isinstance(obj, cq.Workplane):
        vals = obj.vals()
        if len(vals) == 1:
            return vals[0]
        return cq.Compound.makeCompound(vals)
    return obj


def _vxy(view, x, y, z):
    """Toa do 3D -> toa do hinh chieu."""
    if view == "front":
        return (x, z)
    if view == "top":
        return (x, y)
    return (-y, z)


# ----------------------------------------------------------------------------
# Hinh chieu (HLR)
# ----------------------------------------------------------------------------
def _project(shape, direction, xdir):
    hlr = HLRBRep_Algo()
    hlr.Add(shape.wrapped)
    ax = gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(*direction), gp_Dir(*xdir))
    hlr.Projector(HLRAlgo_Projector(ax))
    hlr.Update()
    hlr.Hide()
    conv = HLRBRep_HLRToShape(hlr)

    def edges_of(getter):
        try:
            comp = getter()
        except Exception:
            return []
        if comp is None or comp.IsNull():
            return []
        return cq.Shape.cast(comp).Edges()

    visible = edges_of(conv.VCompound) + edges_of(conv.OutLineVCompound)
    hidden = edges_of(conv.HCompound) + edges_of(conv.OutLineHCompound)
    return visible, hidden


def _edge_points(edge):
    n = 1 if edge.geomType() == "LINE" else 48
    pts = [edge.positionAt(i / n) for i in range(n + 1)]
    return [(p.x, p.y) for p in pts]


def _bbox_of(polys):
    xs = [p[0] for poly in polys for p in poly]
    ys = [p[1] for poly in polys for p in poly]
    if not xs:
        return (0.0, 0.0, 0.0, 0.0)
    return (min(xs), min(ys), max(xs), max(ys))


# ----------------------------------------------------------------------------
# Phan tich hinh hoc 3D: mat tru, mat phang
# ----------------------------------------------------------------------------
def _axis_index(d):
    comps = (d.X(), d.Y(), d.Z())
    for i in range(3):
        if abs(abs(comps[i]) - 1.0) < 1e-6:
            return i
    return None


def _uv_bounds(face):
    try:
        return face._uvBounds()
    except Exception:
        from OCP.BRepTools import BRepTools
        return BRepTools.UVBounds_s(face.wrapped)


def _merge_levels(vals, tol=0.01):
    out = []
    for v in sorted(vals):
        if not out or abs(v - out[-1]) > tol:
            out.append(v)
    return out


def _analyze(shape):
    bb = shape.BoundingBox()
    info = {
        "bb": (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax),
        "levels": [[], [], []],
        "cyl": [],
    }
    groups = {}
    classifier = BRepClass3d_SolidClassifier(shape.wrapped)

    for face in shape.Faces():
        ad = BRepAdaptor_Surface(face.wrapped)
        t = ad.GetType()
        if t == GeomAbs_Plane:
            pl = ad.Plane()
            i = _axis_index(pl.Axis().Direction())
            if i is not None:
                loc = pl.Location()
                info["levels"][i].append((loc.X(), loc.Y(), loc.Z())[i])
        elif t == GeomAbs_Cylinder:
            cyl = ad.Cylinder()
            ax = cyl.Axis()
            axis = _axis_index(ax.Direction())
            if axis is None:
                continue
            r = cyl.Radius()
            loc = ax.Location()
            lc = (loc.X(), loc.Y(), loc.Z())
            perp_idx = [i for i in range(3) if i != axis]
            perp = (lc[perp_idx[0]], lc[perp_idx[1]])
            u0, u1, v0, v1 = _uv_bounds(face)
            fb = face.BoundingBox()
            lo = (fb.xmin, fb.ymin, fb.zmin)[axis]
            hi = (fb.xmax, fb.ymax, fb.zmax)[axis]
            key = (axis, round(perp[0], 3), round(perp[1], 3), round(r, 3),
                   round(lo, 2), round(hi, 2))
            g = groups.get(key)
            if g is None:
                # xac dinh lo (long) hay tru (loi) bang diem thu cach be mat
                um, vm = (u0 + u1) / 2.0, (v0 + v1) / 2.0
                p = ad.Value(um, vm)
                pc = (p.X(), p.Y(), p.Z())
                a_pt = list(lc)
                a_pt[axis] = pc[axis]
                rad = [pc[k] - a_pt[k] for k in range(3)]
                ln = math.sqrt(sum(c * c for c in rad)) or 1.0
                eps = min(0.05 * r, 0.2)
                q = [pc[k] - rad[k] / ln * eps for k in range(3)]
                classifier.Perform(gp_Pnt(*q), 1e-6)
                convex = classifier.State() == TopAbs_IN
                g = {"axis": axis, "perp": perp, "r": r, "vr": (lo, hi),
                     "span": 0.0, "convex": convex, "mid": pc}
                groups[key] = g
            g["span"] += (u1 - u0)

    for g in groups.values():
        g["full"] = g["span"] >= 2 * math.pi - 0.02
        info["cyl"].append(g)
    info["levels"] = [_merge_levels(v) for v in info["levels"]]
    return info


def _cyl_center3(g):
    """Tam truc tru (x, y, z) - thanh phan doc truc lay o giua doan."""
    axis = g["axis"]
    perp_idx = [i for i in range(3) if i != axis]
    c = [0.0, 0.0, 0.0]
    c[perp_idx[0]], c[perp_idx[1]] = g["perp"]
    c[axis] = (g["vr"][0] + g["vr"][1]) / 2.0
    return tuple(c)


# ----------------------------------------------------------------------------
# Sinh danh sach kich thuoc / duong tam (toa do hinh chieu, don vi mo hinh)
# ----------------------------------------------------------------------------
def _build_annotations(info, vbb):
    xmin, xmax, ymin, ymax, zmin, zmax = info["bb"]
    W, D, H = xmax - xmin, ymax - ymin, zmax - zmin
    dims = []
    cls = []      # duong tam
    circles = []  # duong tron tam (PCD): (view, (cx,cy), r)

    def lin(view, side, p1, p2, text=None, prio=0):
        horizontal = side in ("top", "bottom")
        span = abs(p2[0] - p1[0]) if horizontal else abs(p2[1] - p1[1])
        if span < 0.3:
            return
        dims.append({"kind": "lin", "view": view, "side": side, "p1": p1,
                     "p2": p2, "text": text, "prio": prio, "span": span})

    cyls = info["cyl"]
    holes = [g for g in cyls if g["full"] and not g["convex"]]
    bosses = [g for g in cyls if g["full"] and g["convex"]]
    rounds = [g for g in cyls if not g["full"] and g["r"] > 0.2]

    def circle_center(g):
        c3 = _cyl_center3(g)
        return _vxy(_CIRCLE_VIEW[g["axis"]], *c3)

    # --- Duong tam ---
    seg = {}
    for g in holes + bosses:
        c3 = _cyl_center3(g)
        cv = _CIRCLE_VIEW[g["axis"]]
        cx, cy = _vxy(cv, *c3)
        cls.append((cv, "cross", (cx, cy), g["r"]))
        lo, hi = g["vr"]
        for view in ("front", "top", "left"):
            if view == cv:
                continue
            # truc cua tru nam trong mat phang hinh chieu nay
            if g["axis"] == 2:      # truc Z -> duong dung
                px, _ = _vxy(view, c3[0], c3[1], 0)
                orient, pos, a, b = "v", px, lo, hi
            elif g["axis"] == 1:    # truc Y: top -> duong dung, left -> duong ngang
                if view == "top":
                    orient, pos, a, b = "v", c3[0], lo, hi
                else:
                    orient, pos, a, b = "h", c3[2], -hi, -lo
            else:                   # truc X: front/top -> duong ngang
                if view == "front":
                    orient, pos, a, b = "h", c3[2], lo, hi
                else:
                    orient, pos, a, b = "h", c3[1], lo, hi
            k = (view, orient, round(pos, 3))
            if k in seg:
                seg[k][0] = min(seg[k][0], a)
                seg[k][1] = max(seg[k][1], b)
            else:
                seg[k] = [a, b]
    for (view, orient, pos), (a, b) in seg.items():
        if orient == "v":
            cls.append((view, "line", (pos, a), (pos, b)))
        else:
            cls.append((view, "line", (a, pos), (b, pos)))

    # --- Kich thuoc bao ngoai, danh dau duong kinh neu la tru ---
    def has_boss(axes, dia, tol=0.02):
        return any(g["axis"] in axes and abs(2 * g["r"] - dia) < tol for g in bosses)

    w_dia = has_boss((1, 2), W)
    d_dia = has_boss((0, 2), D)
    h_dia = has_boss((0, 1), H)
    skip_d = d_dia and has_boss((2,), D) and w_dia and abs(W - D) < 0.02
    skip_h = h_dia and has_boss((1,), H) and w_dia and abs(W - H) < 0.02
    fx0, fy0, fx1, fy1 = vbb["front"]
    tx0, ty0, tx1, ty1 = vbb["top"]
    lin("front", "top", (fx0, fy1), (fx1, fy1), "Ø<>" if w_dia else None, prio=2)
    if not skip_h:
        lin("front", "left", (fx0, fy0), (fx0, fy1), "Ø<>" if h_dia else None, prio=2)
    if not skip_d:
        lin("top", "right", (tx1, ty0), (tx1, ty1), "Ø<>" if d_dia else None, prio=2)

    # --- Truc bac / tru loi: duong kinh tren hinh chieu ben ---
    seen = set()
    for g in sorted(bosses, key=lambda g: (g["axis"], g["vr"][0])):
        dia = 2 * g["r"]
        ax = g["axis"]
        if (ax, round(g["r"], 3)) in seen:
            continue
        seen.add((ax, round(g["r"], 3)))
        if (ax in (1, 2) and abs(dia - W) < 0.02) or \
           (ax in (0, 2) and abs(dia - D) < 0.02) or \
           (ax in (0, 1) and abs(dia - H) < 0.02):
            continue  # da duoc ghi o kich thuoc bao ngoai
        c3 = _cyl_center3(g)
        r = g["r"]
        if ax == 2:
            lin("front", "top", (c3[0] - r, g["vr"][1]), (c3[0] + r, g["vr"][1]), "Ø<>", prio=1)
        elif ax == 1:
            lin("top", "bottom", (c3[0] - r, g["vr"][0]), (c3[0] + r, g["vr"][0]), "Ø<>", prio=1)
        else:
            lin("front", "left", (g["vr"][0], c3[2] - r), (g["vr"][0], c3[2] + r), "Ø<>", prio=1)

    # --- Lo: duong kinh tren hinh chieu thay duong tron + vi tri tam ---
    angles = [45, 135, 225, 315, 30, 150, 210, 330]
    angle_used = {"front": 0, "top": 0, "left": 0}
    hgroups = {}
    for g in holes:
        k = (g["axis"], round(g["r"], 3), round(g["vr"][0], 1), round(g["vr"][1], 1))
        hgroups.setdefault(k, []).append(g)

    centers_for_chain = {"front": [], "top": [], "left": []}
    for k, gl in sorted(hgroups.items(), key=lambda kv: -kv[0][1]):
        ax = k[0]
        cv = _CIRCLE_VIEW[ax]
        r = gl[0]["r"]
        pts = [circle_center(g) for g in gl]
        n = len(pts)
        ang = angles[angle_used[cv] % len(angles)]
        angle_used[cv] += 1
        # ezdxf tu them tien to "Ø" cho kich thuoc duong kinh
        dims.append({"kind": "dia", "view": cv, "center": pts[0], "r": r,
                     "angle": ang, "text": (f"{n}×<>" if n > 1 else "<>")})
        # chia lo tren duong tron (PCD)?
        pcd = False
        if n >= 3:
            mx = sum(p[0] for p in pts) / n
            my = sum(p[1] for p in pts) / n
            dists = [math.hypot(p[0] - mx, p[1] - my) for p in pts]
            angs = sorted(math.degrees(math.atan2(p[1] - my, p[0] - mx)) % 360 for p in pts)
            gaps = [((angs[(i + 1) % n] - angs[i]) % 360, angs[i]) for i in range(n)]
            # vong chia lo that su: cac lo cung ban kinh VA cach deu nhau theo goc
            # (4 lo o goc hinh chu nhat khong deu goc -> ghi theo khoang cach)
            even = max(g for g, _ in gaps) - min(g for g, _ in gaps) < 1.0
            if max(dists) - min(dists) < 0.02 and dists[0] > r + 0.1 and even:
                pcd = True
                R = sum(dists) / n
                circles.append((cv, (mx, my), R))
                gsz, gstart = max(gaps)
                a_mid = (gstart + gsz / 2.0) % 360
                dims.append({"kind": "dia", "view": cv, "center": (mx, my), "r": R,
                             "angle": a_mid, "text": "<>"})
        if not pcd:
            centers_for_chain[cv].extend(pts)

    # --- Chuoi vi tri tam lo (tinh tu mep hinh chieu) ---
    for cv, pts in centers_for_chain.items():
        if not pts:
            continue
        x0, y0, x1, y1 = vbb[cv]
        xm, ym = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        xs = _merge_levels([p[0] for p in pts])
        ys = _merge_levels([p[1] for p in pts])
        xs = [v for v in xs if abs(v - xm) > 0.01]
        ys = [v for v in ys if abs(v - ym) > 0.01]
        if 0 < len(xs) <= 8:
            prev = x0
            for v in xs:
                if v - prev > 0.3:
                    lin(cv, "bottom", (prev, y0), (v, y0), prio=0)
                prev = v
        if 0 < len(ys) <= 8:
            side = "right" if cv == "left" else "left"
            xe = x1 if cv == "left" else x0
            prev = y0
            for v in ys:
                if v - prev > 0.3:
                    lin(cv, side, (xe, prev), (xe, v), prio=0)
                prev = v

    # --- Ban kinh bo goc / luon ---
    rgroups = {}
    for g in rounds:
        rgroups.setdefault((g["axis"], round(g["r"], 3)), []).append(g)
    for (ax, r), gl in sorted(rgroups.items(), key=lambda kv: -kv[0][1]):
        cv = _CIRCLE_VIEW[ax]
        g = gl[0]
        c = circle_center(g)
        mp = _vxy(cv, *g["mid"])
        ang = math.degrees(math.atan2(mp[1] - c[1], mp[0] - c[0])) % 360
        n = len(gl)
        # ezdxf tu them tien to "R" cho kich thuoc ban kinh
        dims.append({"kind": "rad", "view": cv, "center": c, "r": g["r"], "angle": ang,
                     "text": (f"{n}×<>" if n > 1 else "<>")})

    # --- Chuoi chieu dai theo cac bac mat phang (X, Y, Z) ---
    lx, ly, lz = info["levels"]
    if 2 < len(lz) <= 10:
        for a, b in zip(lz[:-1], lz[1:]):
            lin("front", "left", (fx0, a), (fx0, b), prio=0)
    if 2 < len(lx) <= 10:
        for a, b in zip(lx[:-1], lx[1:]):
            lin("front", "top", (a, fy1), (b, fy1), prio=0)
    if 2 < len(ly) <= 10:
        for a, b in zip(ly[:-1], ly[1:]):
            lin("top", "left", (tx0, a), (tx0, b), prio=0)

    return dims, cls, circles


# ----------------------------------------------------------------------------
# Bo cuc
# ----------------------------------------------------------------------------
def _assign_levels(dims):
    """Gan tang (level) cho moi kich thuoc tuyen tinh: cac kich thuoc khong chong len
    nhau (vi du chuoi cac bac) nam chung 1 hang; kich thuoc bao ngoai o ngoai cung."""
    groups = {}
    for d in dims:
        if d["kind"] == "lin":
            groups.setdefault((d["view"], d["side"]), []).append(d)
    for lst in groups.values():
        lst.sort(key=lambda d: (d["prio"], d["span"]))
        i = 0 if lst[0]["side"] in ("top", "bottom") else 1
        levels = []
        for d in lst:
            if d["prio"] >= 2:
                continue
            lo, hi = sorted((d["p1"][i], d["p2"][i]))
            for li, ivs in enumerate(levels):
                if all(hi <= a + 1e-6 or lo >= b - 1e-6 for a, b in ivs):
                    ivs.append((lo, hi))
                    d["level"] = li
                    break
            else:
                levels.append([(lo, hi)])
                d["level"] = len(levels) - 1
        nxt = len(levels)
        for d in lst:
            if d["prio"] >= 2:
                d["level"] = nxt
                nxt += 1


def _margins(dims):
    cnt = {}
    for d in dims:
        if d["kind"] == "lin":
            k = (d["view"], d["side"])
            cnt[k] = max(cnt.get(k, 0), d["level"] + 1)

    def m(view, side):
        n = cnt.get((view, side), 0)
        return 0.0 if n == 0 else DIM_OFF + (n - 1) * DIM_SP + DIM_TAIL

    return m


def _layout(vbb, dims, s, sheet):
    """Tra ve vi tri goc duoi-trai cua tung hinh chieu tren to giay, hoac None neu khong vua."""
    sw, sh = SHEETS[sheet]
    m = _margins(dims)
    f, t, l = vbb["front"], vbb["top"], vbb["left"]
    fw, fh = (f[2] - f[0]) * s, (f[3] - f[1]) * s
    tw, th = (t[2] - t[0]) * s, (t[3] - t[1]) * s
    lw = (l[2] - l[0]) * s

    left_margin = max(m("front", "left"), m("top", "left"))
    top_margin = max(m("front", "top"), m("left", "top"))
    gap_h = m("front", "right") + m("left", "left") + BLOCK_PAD
    gap_v = m("front", "bottom") + m("top", "top") + BLOCK_PAD
    total_w = max(left_margin + fw + gap_h + lw + m("left", "right"),
                  left_margin + tw + m("top", "right"))
    total_h = top_margin + fh + gap_v + th + m("top", "bottom")

    area_x0 = MARGIN_LEFT + 6
    area_x1 = sw - MARGIN_OTHER - 6
    area_y0 = MARGIN_OTHER + TB_H + 6
    area_y1 = sh - MARGIN_OTHER - 6
    aw, ah = area_x1 - area_x0, area_y1 - area_y0
    if total_w > aw or total_h > ah:
        return None
    bx = area_x0 + (aw - total_w) / 2.0
    by = area_y0 + (ah - total_h) / 2.0
    fx = bx + left_margin
    fy = by + total_h - top_margin - fh
    return {
        "front": (fx, fy),
        "top": (bx + left_margin, by + m("top", "bottom")),
        "left": (fx + fw + gap_h, fy),
    }


def _choose(vbb, dims, sheet_req):
    sheets = ["A4", "A3"] if sheet_req == "auto" else [sheet_req]
    best = {}
    for sh in sheets:
        for s in SCALES:
            pos = _layout(vbb, dims, s, sh)
            if pos is not None:
                best[sh] = (s, pos)
                break
    if not best:
        # khong vua o ty le nho nhat: van ve (se tran khung) voi ty le nho nhat
        sh = sheets[-1]
        s = SCALES[-1]
        sw, shh = SHEETS[sh]
        pos = {"front": (MARGIN_LEFT + 6, shh / 2), "top": (MARGIN_LEFT + 6, MARGIN_OTHER + TB_H + 6),
               "left": (sw / 2, shh / 2)}
        return sh, s, pos
    if sheet_req != "auto":
        sh = sheet_req
        return sh, best[sh][0], best[sh][1]
    if "A4" in best and best["A4"][0] >= 1:
        return "A4", best["A4"][0], best["A4"][1]
    if "A3" in best:
        return "A3", best["A3"][0], best["A3"][1]
    return "A4", best["A4"][0], best["A4"][1]


# ----------------------------------------------------------------------------
# Khung ban ve, khung ten, yeu cau ky thuat
# ----------------------------------------------------------------------------
def _text(msp, txt, x, y, h, layer="TEXT", align=TextEntityAlignment.LEFT,
          compat=False, maxw=None):
    if compat:
        t = str(txt)
        if maxw:
            w = _text_width(t, h)
            if w > maxw:
                h = h * maxw / w
        _stroke_text(msp, t, x, y, h, layer, "left")
        return None
    t = msp.add_text(txt, height=h, dxfattribs={"layer": layer})
    t.set_placement((x, y), align=align)
    return t


def _rect(msp, x0, y0, x1, y1, layer, lw, compat=False):
    attrs = {"layer": layer, "lineweight": lw}
    if compat and lw >= 25:
        attrs["const_width"] = lw / 100.0   # net day hien thi duoc ca o trinh xem don gian
    msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs=attrs)


def _draw_frame_and_title(msp, sheet, scale_txt, title, material, author, date, qty=1,
                          compat=False):
    sw, sh = SHEETS[sheet]
    _rect(msp, 0, 0, sw, sh, "FRAME", 13, compat)
    ix0, iy0, ix1, iy1 = MARGIN_LEFT, MARGIN_OTHER, sw - MARGIN_OTHER, sh - MARGIN_OTHER
    _rect(msp, ix0, iy0, ix1, iy1, "FRAME", 50, compat)

    x0, y0 = ix1 - TB_W, iy0
    _rect(msp, x0, y0, ix1, iy0 + TB_H, "TITLE", 50, compat)

    def cell(cx, cy, w, h, label, value, vh=4.0):
        _rect(msp, x0 + cx, y0 + cy, x0 + cx + w, y0 + cy + h, "TITLE", 25, compat)
        _text(msp, _ascii(label), x0 + cx + 1.5, y0 + cy + h - 3.8, 2.0, "TITLE",
              compat=compat, maxw=w - 3)
        if value:
            _text(msp, _ascii(value), x0 + cx + 1.5, y0 + cy + 2.5, vh, "TITLE",
                  compat=compat, maxw=w - 3)

    cell(0, 35, 110, 15, "TEN CHI TIET", title, 6.0)
    cell(0, 20, 70, 15, "VAT LIEU", material or "", 4.5)
    cell(70, 20, 40, 15, "SO LUONG", str(qty), 4.5)
    cell(0, 0, 55, 20, "NGUOI VE", author, 4.5)
    cell(55, 0, 55, 20, "NGAY VE", date, 4.5)
    cell(110, 35, 35, 15, "TY LE", scale_txt, 6.0)
    cell(145, 35, 35, 15, "KHO GIAY", sheet, 6.0)
    cell(110, 20, 35, 15, "DON VI", "mm", 4.5)
    cell(145, 20, 35, 15, "GOC CHIEU", "Thu nhat", 4.0)
    cell(110, 0, 70, 20, "CAD-AI", "Ban ve tu dong", 4.5)
    return x0


def _draw_notes(msp, tb_x0, lines, compat=False):
    if not lines:
        return
    x = MARGIN_LEFT + 4
    y = MARGIN_OTHER + TB_H - 5
    hn, cw, dy = (2.2, 2.2, 3.8) if compat else (2.5, 1.75, 4.5)
    max_chars = max(20, int((tb_x0 - 4 - x) / cw))
    _text(msp, "YEU CAU KY THUAT:", x, y, 3.0, "TEXT", compat=compat)
    y -= 5.0
    rows = []
    for ln in lines:
        rows.extend(textwrap.wrap(_ascii(ln), max_chars, subsequent_indent="    ") or [""])
    for row in rows[:10]:
        _text(msp, row, x, y, hn, "TEXT", compat=compat)
        y -= dy


def _sheet_bbox(views, view, pos, s):
    bx0, by0, bx1, by1 = views[view]["bb"]
    px, py = pos[view]
    return (px, py, px + (bx1 - bx0) * s, py + (by1 - by0) * s)


# ----------------------------------------------------------------------------
# Ham chinh
# ----------------------------------------------------------------------------
def export_drawing(obj, path, sheet="auto", title=None, material=None,
                   part_type=None, tolerance=None, tolerances=None,
                   surface_finish=None, author="CAD-AI", date=None,
                   with_dimensions=True, params=None, compat=True):
    """Xuat ban ve 2D day du ra file DXF. Tra ve dict {path, sheet, scale}.

    compat=True (mac dinh): chu, kich thuoc, net dut ve bang hinh hoc co ban nen moi trinh
    xem deu hien thi. compat=False: dung TEXT/DIMENSION/kieu net goc cua CAD (sua duoc
    trong AutoCAD nhung mot so trinh xem don gian se khong hien thi).
    """
    sheet = str(sheet or "auto")
    sheet = "auto" if sheet.lower() == "auto" else sheet.upper()
    if sheet not in ("auto", "A4", "A3"):
        sheet = "auto"
    shape = _to_shape(obj)
    if title is None:
        title = PART_NAMES.get(part_type or "", (part_type or "CHI TIET").upper())
    date = date or datetime.date.today().strftime("%d/%m/%Y")

    # 1) Hinh chieu
    views = {}
    for name, (direction, xdir) in _VIEWS.items():
        vis, hid = _project(shape, direction, xdir)
        vp = [_edge_points(e) for e in vis]
        hp = [_edge_points(e) for e in hid]
        views[name] = {"vis": vp, "hid": hp, "bb": _bbox_of(vp + hp)}
    vbb = {k: v["bb"] for k, v in views.items()}

    # 2) Phan tich hinh hoc -> kich thuoc, duong tam
    info = _analyze(shape)
    dims, cls, circles = _build_annotations(info, vbb)
    if not with_dimensions:
        dims = []
    _assign_levels(dims)

    # 3) Chon kho giay, ty le, bo cuc
    sheet_name, s, pos = _choose(vbb, dims, sheet)

    # 4) Tao DXF
    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.MM
    msp = doc.modelspace()
    if not compat:
        doc.linetypes.add("CAD_HIDDEN", pattern=[5.0, 3.0, -2.0], description="Net dut")
        doc.linetypes.add("CAD_CENTER", pattern=[13.0, 8.0, -2.0, 1.0, -2.0], description="Net cham gach")
    lt_h = {} if compat else {"linetype": "CAD_HIDDEN"}
    lt_c = {} if compat else {"linetype": "CAD_CENTER"}
    doc.layers.add("VISIBLE", color=7, lineweight=35)
    doc.layers.add("HIDDEN", color=8, lineweight=18, **lt_h)
    doc.layers.add("CENTER", color=1, lineweight=13, **lt_c)
    doc.layers.add("DIM", color=3, lineweight=13)
    doc.layers.add("FRAME", color=7, lineweight=50)
    doc.layers.add("TITLE", color=7, lineweight=25)
    doc.layers.add("TEXT", color=7, lineweight=13)

    def to_sheet(view, x, y):
        bx0, by0 = views[view]["bb"][0], views[view]["bb"][1]
        px, py = pos[view]
        return (px + (x - bx0) * s, py + (y - by0) * s)

    # net khuat ve truoc, net thay ve sau
    for name, v in views.items():
        for poly in v["hid"]:
            pts = [to_sheet(name, *p) for p in poly]
            if compat:
                _dash(msp, pts, (3.0, 1.5), "HIDDEN")
            else:
                pl = msp.add_lwpolyline(pts, dxfattribs={"layer": "HIDDEN", "linetype": "CAD_HIDDEN"})
                pl.dxf.flags |= const.LWPOLYLINE_PLINEGEN
        for poly in v["vis"]:
            pts = [to_sheet(name, *p) for p in poly]
            if compat:
                _poly(msp, pts, "VISIBLE", width=0.5)    # net thay day 0.5 mm
            else:
                pl = msp.add_lwpolyline(pts, dxfattribs={"layer": "VISIBLE"})
                pl.dxf.flags |= const.LWPOLYLINE_PLINEGEN

    # duong tam
    def center_seg(view, p1, p2):
        a, b = to_sheet(view, *p1), to_sheet(view, *p2)
        if compat:
            _center_line(msp, a, b)
        else:
            msp.add_line(a, b, dxfattribs={"layer": "CENTER", "linetype": "CAD_CENTER"})

    ex = 3.0 / s
    for item in cls:
        view = item[0]
        if item[1] == "cross":
            (cx, cy), r = item[2], item[3]
            a = r + ex
            center_seg(view, (cx - a, cy), (cx + a, cy))
            center_seg(view, (cx, cy - a), (cx, cy + a))
        else:
            p1, p2 = item[2], item[3]
            if abs(p1[0] - p2[0]) < 1e-9:
                p1, p2 = (p1[0], p1[1] - ex), (p2[0], p2[1] + ex)
            else:
                p1, p2 = (p1[0] - ex, p1[1]), (p2[0] + ex, p2[1])
            center_seg(view, p1, p2)
    for view, (cx, cy), R in circles:
        c = to_sheet(view, cx, cy)
        if compat:
            _dash(msp, _circle_pts(c, R * s), (6.0, 1.5, 1.0, 1.5), "CENTER")
        else:
            msp.add_circle(c, R * s, dxfattribs={"layer": "CENTER", "linetype": "CAD_CENTER"})
        a = R + ex
        center_seg(view, (cx - a, cy), (cx + a, cy))
        center_seg(view, (cx, cy - a), (cx, cy + a))

    # kich thuoc (don vi to giay; dimlfac = 1/ty le de chu hien thi dung kich thuoc that)
    ov = {"dimtxt": 3.5, "dimasz": 3.0, "dimexe": 1.5, "dimexo": 1.0, "dimgap": 1.0,
          "dimdec": 2, "dimzin": 8, "dimlfac": 1.0 / s}
    for d in dims:
        if d["kind"] != "lin":
            continue
        view, side = d["view"], d["side"]
        vx0, vy0, vx1, vy1 = _sheet_bbox(views, view, pos, s)
        off = DIM_OFF + d["level"] * DIM_SP
        p1 = to_sheet(view, *d["p1"])
        p2 = to_sheet(view, *d["p2"])
        text = d["text"] or "<>"
        if side == "top":
            base, ang = (p1[0], vy1 + off), 0
        elif side == "bottom":
            base, ang = (p1[0], vy0 - off), 0
        elif side == "left":
            base, ang = (vx0 - off, p1[1]), 90
        else:
            base, ang = (vx1 + off, p1[1]), 90
        if compat:
            _dim_lin(msp, p1, p2, side, base, _dim_text(d["text"], d["span"]))
        else:
            msp.add_linear_dim(base=base, p1=p1, p2=p2, angle=ang, text=text,
                               override=ov, dxfattribs={"layer": "DIM"}).render()
    for d in dims:
        if d["kind"] == "lin":
            continue
        c = to_sheet(d["view"], *d["center"])
        r = d["r"] * s
        a = math.radians(d["angle"])
        loc = (c[0] + (r + 7.0) * math.cos(a), c[1] + (r + 7.0) * math.sin(a))
        if compat:
            if d["kind"] == "dia":
                txt = _dim_text(d["text"], 2 * d["r"], "Ø")
            else:
                txt = _dim_text(d["text"], d["r"], "R")
            _dim_leader(msp, c, r, d["angle"], txt, loc)
        elif d["kind"] == "dia":
            msp.add_diameter_dim(center=c, radius=r, angle=d["angle"], location=loc,
                                 text=d["text"], override=ov,
                                 dxfattribs={"layer": "DIM"}).render()
        else:
            msp.add_radius_dim(center=c, radius=r, angle=d["angle"], location=loc,
                               text=d["text"], override=ov,
                               dxfattribs={"layer": "DIM"}).render()

    # khung, khung ten, yeu cau ky thuat
    tb_x0 = _draw_frame_and_title(msp, sheet_name, _scale_text(s), title, material,
                                  author, date, compat=compat)
    notes = ["1. Kich thuoc ghi bang mm."]
    if tolerance:
        notes.append(f"{len(notes) + 1}. Dung sai chung: ±{tolerance:g} mm.")
    if surface_finish:
        dflt = surface_finish.get("default")
        if dflt:
            notes.append(f"{len(notes) + 1}. Do nham be mat chung: Ra {dflt:g} um.")
        for name, ra in surface_finish.items():
            if name != "default":
                notes.append(f"    Be mat {name}: Ra {ra:g} um.")
    if tolerances:
        notes.append(f"{len(notes) + 1}. Dung sai kich thuoc: "
                     + "; ".join(f"{k} {v}" for k, v in tolerances.items()))
    if params:
        items = [f"{k} = {v:g}" if isinstance(v, (int, float)) else f"{k} = {v}"
                 for k, v in params.items() if not isinstance(v, (list, dict))]
        if items:
            notes.append(f"{len(notes) + 1}. Thong so: " + ", ".join(items))
    notes.append(f"{len(notes) + 1}. Ve theo goc chieu thu nhat (TCVN/ISO).")
    _draw_notes(msp, tb_x0, notes, compat)

    doc.saveas(path)
    return {"path": path, "sheet": sheet_name, "scale": _scale_text(s)}


# tuong thich voi ban truoc
export_dxf = export_drawing