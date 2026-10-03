"""
cadai/generators/__init__.py
================================
Gom ham build() cua tung part_type thanh 1 dict BUILDERS.
"""
from . import plate, bracket, flange, shaft, stepped_shaft, housing, pillow_block, bolt

BUILDERS = {
    "plate": plate.build,
    "bracket": bracket.build,
    "flange": flange.build,
    "shaft": shaft.build,
    "stepped_shaft": stepped_shaft.build,
    "housing": housing.build,
    "pillow_block": pillow_block.build,
    "bolt": bolt.build,
}