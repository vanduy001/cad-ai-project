"""
web/app.py
============
Backend FastAPI cho website AI CAD.
Chay: python run_server.py   (hoac: uvicorn web.app:app --reload)
"""

import re
import sys
import uuid
import pathlib
import time
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from cadai.pipeline import run_pipeline
from cadai.gemini_client import get_gemini_client

app = FastAPI()

_request_log: dict[str, list[float]] = defaultdict(list)
MAX_REQUESTS_PER_WINDOW = 30
WINDOW_SECONDS = 3600  # 1 gio

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent / "generated"
OUTPUT_DIR.mkdir(exist_ok=True)
INDEX_HTML = pathlib.Path(__file__).resolve().parent / "index.html"

OVERLOAD_MESSAGE = (
    "He thong AI dang qua tai (dang dung key Gemini mien phi, bi gioi han uu "
    "tien xu ly vao gio cao diem). Day la gioi han tu phia Google, khong phai "
    "loi cua he thong. Vui long doi 1-2 phut roi bam Tao ban ve lai, hoac thu "
    "vao gio khac it nguoi dung hon."
)


class GenerateRequest(BaseModel):
    request: str


def _is_overload_error(errors: list[str]) -> bool:
    text = " ".join(errors).lower()
    return any(kw in text for kw in ("qua tai", "overload", "503", "unavailable"))


def _build_pipeline_info(log) -> dict:
    """Gom du lieu tung buoc de trang web hien thi:
    NL -> yeu cau ky thuat -> JSON spec -> code CadQuery -> kiem tra -> STEP.
    """
    last = log.history[-1] if log.history else {}

    # Spec va code cua vong cuoi cung (neu co)
    spec = log.final_spec or last.get("spec")
    code = None
    for entry in reversed(log.history):
        if entry.get("code"):
            code = entry["code"]
            break

    requirements = None
    if spec:
        requirements = {
            "part_type": spec.get("part_type"),
            "base_dimensions": spec.get("base_dimensions"),
            "features": spec.get("features", []),
            "material": spec.get("material"),
            "tolerance": spec.get("tolerance"),
        }

    # Tom tat tung vong lap (khong gui lai code de nhe response)
    iterations = [
        {
            "iteration": h.get("iteration"),
            "stage": h.get("stage"),
            "errors": h.get("errors", []),
            "metrics": h.get("metrics", {}),
        }
        for h in log.history
    ]

    # Buoc nao da chay xong / dung o dau
    if not log.history:
        failed_at = "nl_to_spec"
    elif log.success:
        failed_at = None
    else:
        failed_at = last.get("stage")

    return {
        "nl_request": log.nl_request,
        "requirements": requirements,
        "spec": spec,
        "code": code,
        "validation": {
            "is_valid": log.success,
            "errors": log.final_errors,
            "metrics": log.final_metrics,
        },
        "n_iterations": log.n_iterations,
        "elapsed_sec": log.elapsed_sec,
        "failed_at": failed_at,
        "iterations": iterations,
    }


@app.get("/", response_class=HTMLResponse)
def index():
    return INDEX_HTML.read_text(encoding="utf-8")


@app.post("/generate")
def generate(request: Request, body: GenerateRequest):
    client_ip = request.client.host
    now = time.time()
    _request_log[client_ip] = [t for t in _request_log[client_ip] if now - t < WINDOW_SECONDS]

    if len(_request_log[client_ip]) >= MAX_REQUESTS_PER_WINDOW:
        return {
            "success": False,
            "message": f"Ban da vuot qua gioi han {MAX_REQUESTS_PER_WINDOW} lan tao/gio. Vui long thu lai sau.",
        }
    _request_log[client_ip].append(now)

    file_id = uuid.uuid4().hex[:8]
    output_path = OUTPUT_DIR / f"{file_id}.step"

    try:
        client = get_gemini_client()
    except Exception as e:
        return {"success": False, "message": f"Loi cau hinh Gemini API key: {e}"}

    log = run_pipeline(body.request, client, output_step_path=str(output_path))
    info = _build_pipeline_info(log)

    if log.success:
        return {
            "success": True,
            "message": "Da tao mo hinh 3D thanh cong.",
            "download_url": f"/download/{file_id}",
            "metrics": log.final_metrics,
            "pipeline": info,
        }

    if _is_overload_error(log.final_errors):
        return {
            "success": False,
            "message": OVERLOAD_MESSAGE,
            "pipeline": info,
        }

    return {
        "success": False,
        "message": "Khong the tao mo hinh. Loi: " + "; ".join(log.final_errors),
        "pipeline": info,
    }


@app.get("/download/{file_id}")
def download(file_id: str):
    if not re.fullmatch(r"[0-9a-f]{8}", file_id):
        return {"error": "File khong hop le"}
    path = OUTPUT_DIR / f"{file_id}.step"
    if not path.exists():
        return {"error": "File khong ton tai"}
    return FileResponse(path, filename=f"{file_id}.step", media_type="application/step")