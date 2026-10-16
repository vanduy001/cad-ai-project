"""
openrouter_client.py
======================
Client goi OpenRouter API (OpenAI-compatible qua HTTP, dung `requests`).
Interface giu nguyen nhu llm_client.LLMClient de pipeline.py dung duoc
khong can sua gi them.

Yeu cau: pip install requests
Bien moi truong:
  OPENROUTER_API_KEY   bat buoc
  OPENROUTER_MODEL     tuy chon, doi model chinh khong can sua code
  OPENROUTER_FALLBACK  tuy chon, danh sach model du phong cach nhau boi dau phay

Lay API key mien phi tai: https://openrouter.ai/keys
"""

from __future__ import annotations
import os
import json
import time
import requests

from cadai.spec_schema import PartSpec
from cadai.llm_client import LLMClient, SYSTEM_PROMPT, _strip_code_fence

API_URL = "https://openrouter.ai/api/v1/chat/completions"

DEFAULT_MODEL = "google/gemma-4-31b-it:free"
DEFAULT_FALLBACKS = [
    "nvidia/nemotron-3-super-120b-a12b:free",
    "google/gemma-4-26b-a4b-it:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "cohere/north-mini-code:free",
    "openrouter/free",
]
RETRIES_PER_MODEL = 2
BASE_DELAY_SEC = 2
TIMEOUT_SEC = 60


class AllModelsOverloadedError(RuntimeError):
    """Tat ca model (chinh + du phong) deu bi gioi han rate limit/qua tai.
    Nguoi dung nen doi vai chuc giay roi thu lai."""


class OpenRouterLLMClient(LLMClient):
    def __init__(self, model: str | None = None):
        api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("Chua set bien moi truong OPENROUTER_API_KEY")
        self.api_key = api_key

        primary = (model or os.environ.get("OPENROUTER_MODEL", DEFAULT_MODEL)).strip()
        fallback_env = os.environ.get("OPENROUTER_FALLBACK")
        fallbacks = [m.strip() for m in fallback_env.split(",")] if fallback_env else DEFAULT_FALLBACKS
        self.models = [primary] + [m for m in fallbacks if m != primary]

    def _call(self, user_prompt: str) -> dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://cad-ai-project.onrender.com",
            "X-Title": "CAD-AI",
        }

        last_error = None
        tried_models = []
        for model in self.models:
            tried_models.append(model)
            for attempt in range(RETRIES_PER_MODEL):
                t0 = time.time()
                try:
                    payload = {
                        "model": model,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt},
                        ],
                        "response_format": {"type": "json_object"},
                        "temperature": 0.2,
                    }
                    r = requests.post(API_URL, headers=headers, json=payload, timeout=TIMEOUT_SEC)
                    if r.status_code != 200:
                        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")
                    data = r.json()
                    if "error" in data:
                        raise RuntimeError(f"API error: {data['error']}")
                    content = data["choices"][0]["message"]["content"]
                    elapsed = round(time.time() - t0, 1)
                    print(f"[openrouter_client] {model} thanh cong, mat {elapsed}s")
                    text = _strip_code_fence(content)
                    return json.loads(text)
                except Exception as e:
                    elapsed = round(time.time() - t0, 1)
                    last_error = e
                    msg = str(e).lower()
                    is_overload = any(kw in msg for kw in ("429", "rate", "503", "overloaded", "402"))
                    is_model_gone = any(kw in msg for kw in ("404", "not_found", "not found", "does not exist"))
                    if is_model_gone:
                        print(f"[openrouter_client] {model} loi (model khong ton tai): {e}")
                        break
                    if is_overload and attempt < RETRIES_PER_MODEL - 1:
                        delay = BASE_DELAY_SEC * (2 ** attempt)
                        print(f"[openrouter_client] {model} loi sau {elapsed}s ({e}). Cho {delay}s roi thu lai...")
                        time.sleep(delay)
                        continue
                    if is_overload:
                        print(f"[openrouter_client] {model} van bi gioi han sau {elapsed}s: {e}")
                        break
                    print(f"[openrouter_client] {model} loi khong the thu lai sau {elapsed}s: {e}")
                    raise

        raise AllModelsOverloadedError(
            f"Da thu {len(tried_models)} model ({', '.join(tried_models)}) nhung tat ca deu "
            f"dang bi gioi han/qua tai. Loi cuoi: {last_error}"
        )

    def nl_to_spec(self, nl_request: str) -> PartSpec:
        data = self._call(f"Yeu cau thiet ke:\n{nl_request}")
        if "error" in data:
            raise ValueError(f"Khong the xu ly yeu cau: {data['error']}")
        return PartSpec.from_dict(data)

    def repair_spec(self, nl_request: str, current_spec: PartSpec, errors: list[str]) -> PartSpec:
        prompt = (
            f"Yeu cau thiet ke goc:\n{nl_request}\n\n"
            f"Spec hien tai (da sinh nhung con loi):\n{current_spec.to_json()}\n\n"
            "Cac loi can sua:\n" + "\n".join(f"- {e}" for e in errors) + "\n\n"
            "Hay sua lai spec de khac phuc cac loi tren, giu nguyen cac phan da dung. "
            "Tra ve JSON day du theo dung schema, khong giai thich."
        )
        data = self._call(prompt)
        if "error" in data:
            raise ValueError(f"Khong the sua duoc yeu cau: {data['error']}")
        return PartSpec.from_dict(data)


def get_openrouter_client() -> OpenRouterLLMClient:
    return OpenRouterLLMClient()