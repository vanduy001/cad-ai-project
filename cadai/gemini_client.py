"""
gemini_client.py
==================
Client goi Google Gemini API (dung SDK moi google-genai), thay the cho
ClaudeLLMClient. Interface giu nguyen nhu llm_client.LLMClient de
pipeline.py dung duoc khong can sua gi them.

Yeu cau: pip install google-genai
Bien moi truong:
  GEMINI_API_KEY   bat buoc
  GEMINI_MODEL     tuy chon, doi model chinh khong can sua code
  GEMINI_FALLBACK  tuy chon, danh sach model du phong cach nhau boi dau phay

LUU Y: key mien phi (free tier) bi gioi han uu tien xu ly thap hon key tra
phi, nen de bi bao 503 "qua tai" vao gio cao diem. Co nhieu model du phong
giam duoc tan suat loi nhung khong loai bo hoan toan.
"""

from __future__ import annotations
import os
import json
import time

from cadai.spec_schema import PartSpec
from cadai.llm_client import LLMClient, SYSTEM_PROMPT, _strip_code_fence

DEFAULT_MODEL = "gemini-3.8-flash"
# Thu tu du phong: tu moi nhat toi on dinh/nhe nhat. Model nhe (flash-lite,
# 1.5-flash) thuong co han muc free tier rong hon, it bi nghen gio cao diem.
DEFAULT_FALLBACKS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
]
RETRIES_PER_MODEL = 2
BASE_DELAY_SEC = 2  # tang dan: 2, 4 giay moi model truoc khi chuyen model ke tiep


class AllModelsOverloadedError(RuntimeError):
    """Tat ca model (chinh + du phong) deu qua tai. Day la loi tam thoi tu
    phia Google (thuong do gioi han key mien phi vao gio cao diem), KHONG
    phai loi code. Nguoi dung nen doi vai phut roi thu lai."""


class GeminiLLMClient(LLMClient):
    def __init__(self, model: str | None = None):
        from google import genai

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("Chua set bien moi truong GEMINI_API_KEY")

        self.client = genai.Client(api_key=api_key)

        primary = model or os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)
        fallback_env = os.environ.get("GEMINI_FALLBACK")
        fallbacks = [m.strip() for m in fallback_env.split(",")] if fallback_env else DEFAULT_FALLBACKS
        # danh sach model se thu, theo thu tu, bo trung neu primary trung fallback
        self.models = [primary] + [m for m in fallbacks if m != primary]

    def _call(self, user_prompt: str) -> dict:
        last_error = None
        tried_models = []
        for model in self.models:
            tried_models.append(model)
            for attempt in range(RETRIES_PER_MODEL):
                t0 = time.time()
                try:
                    resp = self.client.models.generate_content(
                        model=model,
                        contents=user_prompt,
                        config={"system_instruction": SYSTEM_PROMPT},
                    )
                    elapsed = round(time.time() - t0, 1)
                    print(f"[gemini_client] {model} thanh cong, mat {elapsed}s")
                    text = _strip_code_fence(resp.text)
                    return json.loads(text)
                except Exception as e:
                    elapsed = round(time.time() - t0, 1)
                    last_error = e
                    is_overload = "503" in str(e) or "UNAVAILABLE" in str(e) or "overloaded" in str(e).lower()
                    if is_overload and attempt < RETRIES_PER_MODEL - 1:
                        delay = BASE_DELAY_SEC * (2 ** attempt)
                        print(f"[gemini_client] {model} loi sau {elapsed}s ({e}). Cho {delay}s roi thu lai...")
                        time.sleep(delay)
                        continue
                    if is_overload:
                        print(f"[gemini_client] {model} van qua tai sau {elapsed}s, chuyen sang model du phong")
                        break  # sang model tiep theo trong self.models
                    print(f"[gemini_client] {model} loi khong the thu lai sau {elapsed}s: {e}")
                    raise

        # Het tat ca model trong danh sach ma van qua tai
        raise AllModelsOverloadedError(
            f"Da thu {len(tried_models)} model ({', '.join(tried_models)}) nhung tat ca deu "
            f"dang qua tai (Google free tier bi gioi han gio cao diem). Loi cuoi: {last_error}"
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


def get_gemini_client() -> GeminiLLMClient:
    return GeminiLLMClient()