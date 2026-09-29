"""
cq_generator.py
=================
Chuyen PartSpec -> chuoi code CadQuery (Python).
Logic sinh code cho tung part_type nam trong cadai/generators/,
logic sinh code cho tung feature nam trong cadai/features/.
File nay CHI ghep lai, khong chua logic sinh hinh hoc.
"""

from __future__ import annotations
from cadai.spec_schema import PartSpec
from cadai.generators import BUILDERS
from cadai.features import APPLIERS


class CodeGenError(ValueError):
    pass


def generate_cadquery_code(spec: PartSpec) -> str:
    if spec.part_type not in BUILDERS:
        raise CodeGenError(f"Chua ho tro sinh code cho part_type='{spec.part_type}'")

    lines = ["import cadquery as cq", "import math", "", BUILDERS[spec.part_type](spec)]

    for i, feat in enumerate(spec.features):
        if feat.type not in APPLIERS:
            raise CodeGenError(f"Chua ho tro sinh code cho feature type='{feat.type}'")
        lines.append(APPLIERS[feat.type](feat, spec, i))

    return "\n".join(lines)


if __name__ == "__main__":
    from cadai.spec_schema import example_plate_spec

    code = generate_cadquery_code(example_plate_spec())
    print(code)