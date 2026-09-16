"""
gemini_client.py
==================
Client goi Google Gemini API (dung SDK moi google-genai), thay the cho
ClaudeLLMClient. Interface giu nguyen nhu llm_client.LLMClient de
pipeline.py dung duoc khong can sua gi them.

Yeu cau: pip install google-genai
Bien moi truong: GEMINI_API_KEY=...
"""

from __future__ import annotations
import os
import json
import time

from spec_schema import PartSpec
from llm_client import LLMClient, SYSTEM_PROMPT, _strip_code_fence


class GeminiLLMClient(LLMClient):
    def __init__(self, model: str = "gemini-3.6-flash"):
        from google import genai

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("Chua set bien moi truong GEMINI_API_KEY")

        self.client = genai.Client(api_key=api_key)
        self.model = model

    def _call(self, user_prompt: str) -> dict:
        last_error = None
        for attempt in range(3):
            try:
                resp = self.client.models.generate_content(
                    model=self.model,
                    contents=user_prompt,
                    config={"system_instruction": SYSTEM_PROMPT},
                )
                text = _strip_code_fence(resp.text)
                return json.loads(text)
            except Exception as e:
                last_error = e
                if "503" in str(e) or "UNAVAILABLE" in str(e):
                    time.sleep(3)
                    continue
                raise
        raise last_error

    def nl_to_spec(self, nl_request: str) -> PartSpec:
        data = self._call(f"Yeu cau thiet ke:\n{nl_request}")
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
        return PartSpec.from_dict(data)


def get_gemini_client() -> GeminiLLMClient:
    return GeminiLLMClient()