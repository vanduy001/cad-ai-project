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


def _safe_call(fn, args, what: str) -> str:
    """Goi ham sinh code; moi loi do spec thieu/sai tham so deu doi thanh CodeGenError
    (pipeline se dua thong bao nay cho LLM sua lai thay vi bi sap)."""
    try:
        return fn(*args)
    except CodeGenError:
        raise
    except KeyError as e:
        raise CodeGenError(f"{what}: thieu tham so bat buoc {e}. Hay bo sung dung ten tham so.") from e
    except (TypeError, ValueError, IndexError, AttributeError, ZeroDivisionError) as e:
        raise CodeGenError(f"{what}: tham so khong hop le ({type(e).__name__}: {e}).") from e


def generate_cadquery_code(spec: PartSpec) -> str:
    if spec.part_type not in BUILDERS:
        raise CodeGenError(f"Chua ho tro sinh code cho part_type='{spec.part_type}'")

    lines = [
        "import cadquery as cq", "import math", "",
        _safe_call(BUILDERS[spec.part_type], (spec,),
                   f"part_type='{spec.part_type}' base_dimensions={spec.base_dimensions}"),
    ]

    for i, feat in enumerate(spec.features):
        if feat.type not in APPLIERS:
            raise CodeGenError(f"Chua ho tro sinh code cho feature type='{feat.type}'")
        lines.append(_safe_call(APPLIERS[feat.type], (feat, spec, i),
                                f"features[{i}] type='{feat.type}' params={feat.params}"))

    return "\n".join(lines)


if __name__ == "__main__":
    from cadai.spec_schema import example_plate_spec

    code = generate_cadquery_code(example_plate_spec())
    print(code)