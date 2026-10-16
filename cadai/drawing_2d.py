"""Xuat ban ve 2D (DXF) tu mo hinh CadQuery.

Ba hinh chieu theo goc chieu thu nhat (TCVN/ISO):
- Hinh chieu dung (nhin tu phia -Y)   : dat o tren ben trai
- Hinh chieu bang  (nhin tu tren +Z)  : dat ngay duoi hinh dung
- Hinh chieu canh  (nhin tu trai -X)  : dat ben phai hinh dung

Net thay: lop VISIBLE (net lien). Net khuat: lop HIDDEN (net dut).
Kich thuoc bao ngoai (dai, rong, cao): lop DIM.
"""
import cadquery as cq
import ezdxf
from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape
from OCP.HLRAlgo import HLRAlgo_Projector
from OCP.gp import gp_Ax2, gp_Pnt, gp_Dir

# (huong nhin ra phia nguoi xem, huong truc x cua hinh chieu)
_VIEWS = {
    "front": ((0, -1, 0), (1, 0, 0)),   # x = X, y = Z
    "top": ((0, 0, 1), (1, 0, 0)),      # x = X, y = Y
    "left": ((-1, 0, 0), (0, -1, 0)),   # x = -Y, y = Z
}


def _to_shape(obj):
    if isinstance(obj, cq.Workplane):
        vals = obj.vals()
        if len(vals) == 1:
            return vals[0]
        return cq.Compound.makeCompound(vals)
    return obj


def _project(shape, direction, xdir):
    """Tra ve (danh_sach_canh_thay, danh_sach_canh_khuat) trong toa do hinh chieu."""
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
    """Roi rac mot canh thanh danh sach diem (x, y)."""
    if edge.geomType() == "LINE":
        n = 1
    else:
        n = 48
    pts = [edge.positionAt(i / n) for i in range(n + 1)]
    return [(p.x, p.y) for p in pts]


def _bbox(edges):
    xs, ys = [], []
    for e in edges:
        for x, y in _edge_points(e):
            xs.append(x)
            ys.append(y)
    if not xs:
        return 0.0, 0.0, 0.0, 0.0
    return min(xs), min(ys), max(xs), max(ys)


def export_dxf(obj, path, with_dimensions=True, gap=None):
    """Xuat 3 hinh chieu cua `obj` (Workplane hoac Shape) ra file DXF."""
    shape = _to_shape(obj)

    views = {}
    for name, (direction, xdir) in _VIEWS.items():
        vis, hid = _project(shape, direction, xdir)
        views[name] = {"vis": vis, "hid": hid, "bb": _bbox(vis + hid)}

    fx0, fy0, fx1, fy1 = views["front"]["bb"]
    tx0, ty0, tx1, ty1 = views["top"]["bb"]
    lx0, ly0, lx1, ly1 = views["left"]["bb"]
    W, H = fx1 - fx0, fy1 - fy0
    D = ty1 - ty0
    size = max(W, H, D, 1.0)
    if gap is None:
        gap = size * 0.35  # chua cho de ghi kich thuoc

    # Tinh do dich de dat: front goc (0,0); top ben duoi; left ben phai.
    offsets = {
        "front": (-fx0, -fy0),
        "top": (-tx0, -gap - (ty1 - ty0) - ty0),
        "left": (W + gap - lx0, -ly0),
    }

    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.MM
    msp = doc.modelspace()
    doc.layers.add("VISIBLE", color=7)
    doc.layers.add("HIDDEN", color=8, linetype="DASHED")
    doc.layers.add("DIM", color=3)

    for name, v in views.items():
        dx, dy = offsets[name]
        # Ve net khuat truoc, net thay sau de net lien nam tren cung
        for e in v["hid"]:
            pts = [(x + dx, y + dy) for x, y in _edge_points(e)]
            msp.add_lwpolyline(pts, dxfattribs={"layer": "HIDDEN", "linetype": "DASHED"})
        for e in v["vis"]:
            pts = [(x + dx, y + dy) for x, y in _edge_points(e)]
            msp.add_lwpolyline(pts, dxfattribs={"layer": "VISIBLE"})

    if with_dimensions:
        off = size * 0.12
        ov = {
            "dimtxt": size * 0.04,
            "dimasz": size * 0.03,
            "dimexe": size * 0.015,
            "dimexo": size * 0.01,
            "dimdec": 1,
            "dimlfac": 1.0,  # kieu mac dinh cua ezdxf nhan 100, phai dat lai
            "dimzin": 8,     # bo so 0 thua: 80 thay vi 80.0
        }
        top_dy = offsets["top"][1]
        top_y0 = ty0 + top_dy
        top_y1 = ty1 + top_dy
        attrs = {"layer": "DIM"}
        # Chieu dai (X) tren hinh dung
        msp.add_linear_dim(
            base=(0, H + off), p1=(0, H), p2=(W, H),
            dimstyle="EZDXF", override=ov, dxfattribs=attrs,
        ).render()
        # Chieu cao (Z) ben trai hinh dung
        msp.add_linear_dim(
            base=(-off, 0), p1=(0, 0), p2=(0, H), angle=90,
            dimstyle="EZDXF", override=ov, dxfattribs=attrs,
        ).render()
        # Chieu rong (Y) ben phai hinh bang
        msp.add_linear_dim(
            base=(W + off, 0), p1=(W, top_y0), p2=(W, top_y1), angle=90,
            dimstyle="EZDXF", override=ov, dxfattribs=attrs,
        ).render()

    doc.saveas(path)
    return path