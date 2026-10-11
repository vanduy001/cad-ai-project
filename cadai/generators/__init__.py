"""
cadai/generators/__init__.py
"""
from . import plate, bracket, flange, shaft, stepped_shaft, housing, pillow_block, bolt, nut
from . import washer, pin, flat_plate, countersunk_screw
from . import spur_gear, pulley, cam, coupling
from . import key, retaining_ring, bushing, end_cap

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
    "spur_gear": spur_gear.build,
    "pulley": pulley.build,
    "cam": cam.build,
    "coupling": coupling.build,
    "key": key.build,
    "retaining_ring": retaining_ring.build,
    "bushing": bushing.build,
    "end_cap": end_cap.build,
}