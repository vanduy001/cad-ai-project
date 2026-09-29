"""
cadai/generators/__init__.py
================================
Gom ham build() cua tung part_type thanh 1 dict BUILDERS.

THEM PART_TYPE MOI:
  1. Tao file moi trong thu muc nay, vd ban_rang.py, co ham build(spec) -> str
  2. Import file do o duoi day va them vao dict BUILDERS
  3. Khai bao part_type moi trong cadai/spec_schema.py (SUPPORTED_PART_TYPES + required_dims)
  4. Cap nhat SYSTEM_PROMPT trong cadai/llm_client.py
"""
from . import plate, bracket, flange, shaft, stepped_shaft, housing, pillow_block

BUILDERS = {
    "plate": plate.build,
    "bracket": bracket.build,
    "flange": flange.build,
    "shaft": shaft.build,
    "stepped_shaft": stepped_shaft.build,
    "housing": housing.build,
    "pillow_block": pillow_block.build,
}
