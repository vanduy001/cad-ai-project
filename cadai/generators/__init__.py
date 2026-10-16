"""
cadai/generators/__init__.py
"""
from . import plate, bracket, flange, shaft, stepped_shaft, housing, pillow_block, bolt, nut
from . import washer, pin, flat_plate, countersunk_screw
from . import spur_gear, pulley, cam, coupling
from . import key, retaining_ring, bushing, end_cap
from . import bevel_gear, sprocket, spring, bearing_housing
from . import rack, worm, piston, connecting_rod

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
    "bevel_gear": bevel_gear.build,
    "sprocket": sprocket.build,
    "spring": spring.build,
    "bearing_housing": bearing_housing.build,
    "rack": rack.build,
    "worm": worm.build,
    "piston": piston.build,
    "connecting_rod": connecting_rod.build,
}