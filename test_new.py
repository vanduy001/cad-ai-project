from spec_schema import PartSpec, Feature, validate_spec
from cq_generator import generate_cadquery_code

spec = PartSpec(
    part_type="pillow_block",
    base_dimensions={
        "length": 120, "depth": 78, "height": 42,
        "base_height": 17, "top_width": 50, "seat_radius": 29,
    },
    features=[Feature(type="side_lugs", params={"lug_length": 12})],
)

print("Loi validate:", validate_spec(spec) or "khong co")
print(generate_cadquery_code(spec))