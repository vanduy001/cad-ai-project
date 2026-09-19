"""
web/app.py
============
Backend FastAPI cho website AI CAD.
Chay: uvicorn web.app:app --reload
"""

import sys
import uuid
import pathlib
import time
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from pipeline import run_pipeline
from gemini_client import get_gemini_client

app = FastAPI()

_request_log: dict[str, list[float]] = defaultdict(list)
MAX_REQUESTS_PER_WINDOW = 5
WINDOW_SECONDS = 3600  # 1 gio

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent / "generated"
OUTPUT_DIR.mkdir(exist_ok=True)
INDEX_HTML = pathlib.Path(__file__).resolve().parent / "index.html"


class GenerateRequest(BaseModel):
    request: str


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

    if log.success:
        return {
            "success": True,
            "message": "Da tao mo hinh 3D thanh cong.",
            "download_url": f"/download/{file_id}",
            "metrics": log.final_metrics,
        }
    return {
        "success": False,
        "message": "Khong the tao mo hinh. Loi: " + "; ".join(log.final_errors),
    }


@app.get("/download/{file_id}")
def download(file_id: str):
    path = OUTPUT_DIR / f"{file_id}.step"
    if not path.exists():
        return {"error": "File khong ton tai"}
    return FileResponse(path, filename=f"{file_id}.step", media_type="application/step")