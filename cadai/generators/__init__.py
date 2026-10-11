"""
cadai/generators/__init__.py
Gom ham build() cua tung part_type thanh 1 dict BUILDERS.
"""
from . import plate, bracket, flange, shaft, stepped_shaft, housing, pillow_block, bolt, nut
from . import washer, pin, flat_plate, countersunk_screw

BUILDERS = {
    "plate": plate.build,
    "bracket": bracket.build,
    "flange": flange.build,
    "shaft": shaft.build,
    "stepped_shaft": stepped_shaft.build,
    "housing": housing.build,
    "pillow_block": pillow_block.build,
    "bolt": bolt.build,
    "nut": nut.build,
    "washer": washer.build,
    "pin": pin.build,
    "flat_plate": flat_plate.build,
    "countersunk_screw": countersunk_screw.build,
}