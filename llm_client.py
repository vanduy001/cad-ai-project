"""
llm_client.py
===============
Bọc lời gọi tới LLM (Claude API) cho 2 việc:
    1. nl_to_spec(text)               : NL request -> PartSpec (JSON có schema)
    2. repair_spec(spec, errors, nl)  : sửa spec dựa trên lỗi validator trả về

Yêu cầu: pip install anthropic, và biến môi trường ANTHROPIC_API_KEY.
Nếu chưa có API key, dùng DemoLLMClient (rule-based, chỉ khớp đúng câu
mẫu trong examples/) để chạy thử toàn bộ pipeline không cần mạng/API key.
"""

from __future__ import annotations
import os
import json
import re
from abc import ABC, abstractmethod
from spec_schema import PartSpec, validate_spec

SYSTEM_PROMPT = """Bạn là bộ chuyển đổi yêu cầu thiết kế cơ khí sang JSON đặc tả tham số.
Chỉ trả về DUY NHẤT một JSON object hợp lệ, không thêm lời giải thích, không dùng markdown code fence.

Schema JSON bắt buộc:
{
  "part_type": "plate" | "bracket" | "flange" | "shaft" | "housing",
  "base_dimensions": {...tuỳ part_type, đơn vị mm...},
  "features": [ {"type": "hole"|"fillet"|"chamfer"|"pocket"|"boss"|"slot", "params": {...}} ],
  "constraints": [ {"type": "symmetric"|"concentric"|"min_wall_thickness"|"min_edge_distance", "params": {...}} ],
  "material": "tên vật liệu hoặc null",
  "tolerance": 0.1
}

Quy tắc base_dimensions theo part_type:
  plate/bracket: {"length":..,"width":..,"thickness":..}
  flange:        {"outer_diameter":..,"inner_diameter":..,"thickness":..}
  shaft:         {"diameter":..,"length":..}
  housing:       {"length":..,"width":..,"height":..,"wall_thickness":..}

Quy tắc feature params:
  hole:    {"diameter":.., "depth":"through"|<số mm>, "positions":[[x,y],...]}
  fillet:  {"radius":.., "edges":"all"|"corners"|"top"|"bottom"}
  chamfer: {"distance":.., "edges":"all"|"top"|"bottom"}
  pocket:  {"length":..,"width":..,"depth":..,"position":[x,y]}
  boss:    {"diameter":..,"height":..,"position":[x,y]}
  slot:    {"length":..,"width":..,"depth":"through"|<số>, "position":[x,y], "angle":0}

positions/position tính theo hệ toạ độ tâm mặt phẳng đặt tại tâm hình học của base.
"""


class LLMClient(ABC):
    @abstractmethod
    def nl_to_spec(self, nl_request: str) -> PartSpec:
        ...

    @abstractmethod
    def repair_spec(self, nl_request: str, current_spec: PartSpec, errors: list[str]) -> PartSpec:
        ...


class ClaudeLLMClient(LLMClient):
    """Client thật, gọi Anthropic API. Cần: pip install anthropic
    và export ANTHROPIC_API_KEY=sk-...
    """

    def __init__(self, model: str = "claude-sonnet-4-6"):
        import anthropic  # import trễ để không bắt buộc cài nếu dùng DemoLLMClient

        self.client = anthropic.Anthropic()
        self.model = model

    def _call(self, user_prompt: str) -> dict:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = "".join(block.text for block in resp.content if block.type == "text")
        text = _strip_code_fence(text)
        return json.loads(text)

    def nl_to_spec(self, nl_request: str) -> PartSpec:
        data = self._call(f"Yêu cầu thiết kế:\n{nl_request}")
        return PartSpec.from_dict(data)

    def repair_spec(self, nl_request: str, current_spec: PartSpec, errors: list[str]) -> PartSpec:
        prompt = (
            f"Yêu cầu thiết kế gốc:\n{nl_request}\n\n"
            f"Spec hiện tại (đã sinh nhưng còn lỗi):\n{current_spec.to_json()}\n\n"
            f"Các lỗi cần sửa:\n" + "\n".join(f"- {e}" for e in errors) + "\n\n"
            "Hãy sửa lại spec để khắc phục các lỗi trên, giữ nguyên các phần đã đúng. "
            "Trả về JSON đầy đủ theo đúng schema, không giải thích."
        )
        data = self._call(prompt)
        return PartSpec.from_dict(data)


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    return text


class DemoLLMClient(LLMClient):
    """Client giả lập KHÔNG gọi API — dùng để chạy thử toàn bộ pipeline khi
    chưa có ANTHROPIC_API_KEY hoặc chưa có mạng. Chỉ nhận diện được câu mẫu
    trong examples/plate_4holes_request.txt bằng keyword-matching thô sơ.

    Mục đích: cho phép sinh viên/giảng viên chạy `python pipeline.py --demo`
    và thấy toàn bộ pipeline hoạt động end-to-end ngay lập tức.
    """

    def nl_to_spec(self, nl_request: str) -> PartSpec:
        from spec_schema import example_plate_spec

        text = nl_request.lower()
        if "tấm" in text or "plate" in text:
            return example_plate_spec()
        raise NotImplementedError(
            "DemoLLMClient chỉ hỗ trợ câu mẫu 'tấm phẳng...'. "
            "Dùng ClaudeLLMClient với API key thật cho câu yêu cầu tự do."
        )

    def repair_spec(self, nl_request: str, current_spec: PartSpec, errors: list[str]) -> PartSpec:
        # Demo mode không có khả năng tự sửa thông minh — trả nguyên spec.
        # Trong pipeline thật, đây là nơi ClaudeLLMClient.repair_spec phát huy tác dụng.
        return current_spec


def get_default_client() -> LLMClient:
    """Trả về ClaudeLLMClient nếu có API key + đã cài `anthropic`,
    ngược lại fallback về DemoLLMClient để không chặn việc chạy thử.
    """
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            return ClaudeLLMClient()
        except ImportError:
            print("[llm_client] Chưa cài `anthropic` (pip install anthropic). Dùng DemoLLMClient.")
    else:
        print("[llm_client] Chưa set ANTHROPIC_API_KEY. Dùng DemoLLMClient (chỉ chạy được câu mẫu).")
    return DemoLLMClient()
