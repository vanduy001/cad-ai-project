"""
cq_executor.py
================
Chạy (execute) chuỗi code CadQuery đã sinh ra từ cq_generator.py, trong
một namespace cô lập, bắt lỗi rõ ràng để phục vụ feedback loop.

QUAN TRỌNG: đây là bước exec() code Python, nên trong pipeline thật cần
chạy trong subprocess/container riêng có giới hạn thời gian & tài nguyên,
KHÔNG exec() trực tiếp trong tiến trình chính nếu code đến từ LLM không
qua kiểm soát. File này minh hoạ 2 chế độ:
    - run_inprocess(): đơn giản, dùng khi demo/debug cục bộ.
    - run_subprocess(): an toàn hơn, dùng khi build sản phẩm thật.
"""

from __future__ import annotations
import subprocess
import sys
import tempfile
import os
import json
from dataclasses import dataclass
from typing import Optional


class ExecutionError(RuntimeError):
    """Lỗi khi chạy code CadQuery — message sẽ được đưa ngược cho LLM sửa."""


@dataclass
class ExecutionResult:
    success: bool
    step_path: Optional[str] = None
    error_message: Optional[str] = None
    # Các số liệu hình học cơ bản lấy được ngay sau khi build, dùng cho
    # validator.py mà không cần load lại STEP.
    bounding_box: Optional[dict] = None
    volume: Optional[float] = None


def run_inprocess(code: str, timeout_note: str = "") -> ExecutionResult:
    """Chạy code CadQuery ngay trong tiến trình hiện tại bằng exec().

    Dùng cho giai đoạn phát triển/debug. Không dùng trong sản phẩm thật
    với code không tin cậy (không có sandbox thời gian/bộ nhớ).
    """
    namespace: dict = {}
    try:
        exec(code, namespace)  # noqa: S102 - có kiểm soát, dùng cho dev/demo
    except Exception as e:  # bắt mọi lỗi để đưa message rõ ràng ra ngoài
        return ExecutionResult(success=False, error_message=f"{type(e).__name__}: {e}")

    result = namespace.get("result")
    if result is None:
        return ExecutionResult(
            success=False,
            error_message="Code không tạo ra biến 'result' (biến chứa solid cuối cùng).",
        )

    try:
        bb = result.val().BoundingBox()
        bounding_box = {
            "xlen": round(bb.xlen, 4),
            "ylen": round(bb.ylen, 4),
            "zlen": round(bb.zlen, 4),
        }
        volume = round(result.val().Volume(), 4)
    except Exception as e:
        return ExecutionResult(
            success=False,
            error_message=f"Build ra solid nhưng không đọc được thuộc tính hình học: {e}",
        )

    return ExecutionResult(success=True, bounding_box=bounding_box, volume=volume)


def export_step(code: str, output_path: str) -> ExecutionResult:
    """Chạy code và export STEP ra output_path. Trả về ExecutionResult kèm
    step_path nếu thành công."""
    namespace: dict = {}
    try:
        exec(code, namespace)  # noqa: S102
        result = namespace.get("result")
        if result is None:
            raise ExecutionError("Code không tạo ra biến 'result'.")
        result.val().exportStep(output_path)
    except Exception as e:
        return ExecutionResult(success=False, error_message=f"{type(e).__name__}: {e}")

    exec_result = run_inprocess(code)
    exec_result.step_path = output_path
    return exec_result


def run_subprocess(code: str, timeout_sec: int = 30) -> ExecutionResult:
    """Chạy code CadQuery trong tiến trình con riêng (an toàn hơn), có
    timeout. Dùng khi tích hợp thật với LLM-generated code chưa qua kiểm
    duyệt kỹ. Giao tiếp qua file JSON tạm để lấy kết quả bounding box/volume.
    """
    with tempfile.TemporaryDirectory() as tmp:
        script_path = os.path.join(tmp, "run.py")
        result_path = os.path.join(tmp, "result.json")

        wrapper = f"""
{code}

import json
bb = result.val().BoundingBox()
with open({result_path!r}, "w") as f:
    json.dump({{
        "bounding_box": {{"xlen": bb.xlen, "ylen": bb.ylen, "zlen": bb.zlen}},
        "volume": result.val().Volume(),
    }}, f)
"""
        with open(script_path, "w") as f:
            f.write(wrapper)

        try:
            proc = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=timeout_sec,
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(success=False, error_message=f"Timeout sau {timeout_sec}s")

        if proc.returncode != 0:
            return ExecutionResult(success=False, error_message=proc.stderr.strip()[-2000:])

        if not os.path.exists(result_path):
            return ExecutionResult(success=False, error_message="Không sinh được result.json")

        with open(result_path) as f:
            data = json.load(f)

        return ExecutionResult(
            success=True,
            bounding_box={k: round(v, 4) for k, v in data["bounding_box"].items()},
            volume=round(data["volume"], 4),
        )


if __name__ == "__main__":
    from spec_schema import example_plate_spec
    from cq_generator import generate_cadquery_code

    code = generate_cadquery_code(example_plate_spec())
    print("--- Code sinh ra ---")
    print(code)
    print("\n--- Kết quả chạy (cần cài cadquery để thực sự chạy được) ---")
    res = run_inprocess(code)
    print(res)
