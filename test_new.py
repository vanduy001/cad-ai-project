from cq_generator import generate_cadquery_code
from spec_schema import example_plate_spec

code = generate_cadquery_code(example_plate_spec())
print(code)
print("\n---OK, khong loi---")