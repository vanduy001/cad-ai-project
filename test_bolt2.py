from cadai.spec_schema import PartSpec
from cadai.cq_generator import generate_cadquery_code

spec = PartSpec(part_type="bolt", base_dimensions={"diameter": 8, "length": 30, "real_thread": True})
print(generate_cadquery_code(spec))