"""
pipeline.py
=============
Ghép toàn bộ pipeline end-to-end:

    NL request
      -> LLM: nl_to_spec()              [bước 1]
      -> validate_spec() (cấu trúc)     [bước 2]
      -> cq_generator: sinh code         [bước 3]
      -> cq_executor: chạy code          [bước 4]
      -> validator: kiểm tra hình học    [bước 5]
      -> (nếu fail) LLM: repair_spec()  [bước 6, lặp lại bước 3-5 tối đa N lần]
      -> export STEP + báo cáo số liệu

Chạy thử ngay (không cần API key):
    python pipeline.py --demo

Chạy với LLM thật:
    export ANTHROPIC_API_KEY=sk-...
    pip install anthropic cadquery
    python pipeline.py --request "Thiết kế mặt bích thép, đường kính ngoài 80mm..."
"""

from __future__ import annotations
import argparse
import time
from dataclasses import dataclass, field

from spec_schema import PartSpec, validate_spec
from cq_generator import generate_cadquery_code, CodeGenError
from cq_executor import export_step
from validator import validate_design, ValidationReport
from llm_client import get_default_client, LLMClient


@dataclass
class PipelineRunLog:
    """Log đầy đủ 1 lần chạy pipeline — đây chính là dữ liệu thô để tổng hợp
    bảng tiêu chí đánh giá (Giai đoạn 4 trong đề cương): số vòng lặp hội tụ,
    tỷ lệ thành công, sai lệch kích thước cuối cùng...
    """
    nl_request: str
    success: bool = False
    n_iterations: int = 0
    final_spec: dict | None = None
    final_errors: list[str] = field(default_factory=list)
    final_metrics: dict = field(default_factory=dict)
    step_path: str | None = None
    elapsed_sec: float = 0.0
    history: list[dict] = field(default_factory=list)  # 1 entry / vòng lặp


def run_pipeline(
    nl_request: str,
    client: LLMClient,
    output_step_path: str = "output.step",
    max_iterations: int = 4,
) -> PipelineRunLog:
    t0 = time.time()
    log = PipelineRunLog(nl_request=nl_request)

    # --- Bước 1: NL -> Spec ---
    try:
        spec = client.nl_to_spec(nl_request)
    except Exception as e:
        log.final_errors = [f"Lỗi ở bước NL->Spec: {e}"]
        log.elapsed_sec = time.time() - t0
        return log

    for iteration in range(1, max_iterations + 1):
        log.n_iterations = iteration
        iter_log = {"iteration": iteration, "spec": spec.to_dict()}

        # --- Bước 2: validate cấu trúc spec ---
        struct_errors = validate_spec(spec)
        if struct_errors:
            iter_log["stage"] = "spec_validation"
            iter_log["errors"] = struct_errors
            log.history.append(iter_log)
            spec = _try_repair(client, nl_request, spec, struct_errors)
            continue

        # --- Bước 3: sinh code ---
        try:
            code = generate_cadquery_code(spec)
            iter_log["code"] = code
        except CodeGenError as e:
            iter_log["stage"] = "codegen"
            iter_log["errors"] = [str(e)]
            log.history.append(iter_log)
            spec = _try_repair(client, nl_request, spec, [str(e)])
            continue

        # --- Bước 4: chạy code + export STEP luôn (tiết kiệm 1 lần build) ---
        exec_result = export_step(code, output_step_path)

        # --- Bước 5: validate hình học ---
        report: ValidationReport = validate_design(spec, exec_result)
        iter_log["stage"] = "geometry_validation"
        iter_log["errors"] = report.errors
        iter_log["metrics"] = report.metrics
        log.history.append(iter_log)

        if report.is_valid:
            log.success = True
            log.final_spec = spec.to_dict()
            log.final_metrics = report.metrics
            log.step_path = output_step_path
            break

        # --- Bước 6: fail -> sửa spec rồi lặp lại ---
        spec = _try_repair(client, nl_request, spec, report.errors)
        log.final_errors = report.errors

    log.elapsed_sec = round(time.time() - t0, 3)
    return log


def _try_repair(client: LLMClient, nl_request: str, spec: PartSpec, errors: list[str]) -> PartSpec:
    try:
        return client.repair_spec(nl_request, spec, errors)
    except Exception:
        # Nếu repair lỗi (vd DemoLLMClient), trả nguyên spec cũ để vòng lặp
        # dừng lại theo max_iterations thay vì crash toàn bộ pipeline.
        return spec


def print_report(log: PipelineRunLog) -> None:
    print("=" * 70)
    print(f"YÊU CẦU: {log.nl_request}")
    print("=" * 70)
    print(f"Kết quả       : {'THÀNH CÔNG' if log.success else 'THẤT BẠI'}")
    print(f"Số vòng lặp   : {log.n_iterations}")
    print(f"Thời gian     : {log.elapsed_sec}s")
    if log.success:
        print(f"STEP xuất ra  : {log.step_path}")
        print(f"Sai lệch KT   : {log.final_metrics}")
    else:
        print(f"Lỗi cuối cùng :")
        for e in log.final_errors:
            print(f"  - {e}")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CAD-AI Pipeline: NL request -> STEP")
    parser.add_argument("--request", type=str, default=None, help="Yêu cầu thiết kế bằng ngôn ngữ tự nhiên")
    parser.add_argument("--demo", action="store_true", help="Chạy với câu yêu cầu mẫu, dùng DemoLLMClient")
    parser.add_argument("--output", type=str, default="output.step")
    parser.add_argument("--max-iter", type=int, default=4)
    args = parser.parse_args()

    if args.demo or not args.request:
        nl_request = (
            "Thiết kế tấm phẳng thép 100x60x5mm, có 4 lỗ bắt vít đường kính 6mm "
            "cách mỗi cạnh 10mm, bo tròn 4 góc bán kính 3mm"
        )
    else:
        nl_request = args.request

    client = get_default_client()
    run_log = run_pipeline(nl_request, client, output_step_path=args.output, max_iterations=args.max_iter)
    print_report(run_log)
