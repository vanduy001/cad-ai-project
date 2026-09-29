"""
cadai/features/__init__.py
==============================
Gom ham apply() cua tung feature_type thanh 1 dict APPLIERS.

THEM FEATURE MOI:
  1. Tao file moi trong thu muc nay, co ham apply(feat, spec, idx) -> str
  2. Import file do o duoi day va them vao dict APPLIERS
  3. Them ten feature vao SUPPORTED_FEATURE_TYPES trong cadai/spec_schema.py
  4. Cap nhat SYSTEM_PROMPT trong cadai/llm_client.py
"""
from . import (
    hole, fillet, chamfer, pocket, boss, slot, keyway,
    bolt_circle, radial_hole, counterbore, side_lugs, thread,
)

APPLIERS = {
    "hole": hole.apply,
    "fillet": fillet.apply,
    "chamfer": chamfer.apply,
    "pocket": pocket.apply,
    "boss": boss.apply,
    "slot": slot.apply,
    "keyway": keyway.apply,
    "bolt_circle": bolt_circle.apply,
    "radial_hole": radial_hole.apply,
    "counterbore": counterbore.apply,
    "side_lugs": side_lugs.apply,
    "thread": thread.apply,
}
