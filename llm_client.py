"""
llm_client.py
===============
Boc loi goi toi LLM (Claude API) cho 2 viec:
    1. nl_to_spec(text)               : NL request -> PartSpec (JSON co schema)
    2. repair_spec(spec, errors, nl)  : sua spec dua tren loi validator tra ve

Yeu cau: pip install anthropic, va bien moi truong ANTHROPIC_API_KEY.
Neu chua co API key, dung DemoLLMClient (rule-based, chi khop dung cau
mau trong examples/) de chay thu toan bo pipeline khong can mang/API key.
"""

from __future__ import annotations
import os
import json
import re
from abc import ABC, abstractmethod
from spec_schema import PartSpec, validate_spec

SYSTEM_PROMPT = """Ban la bo chuyen doi yeu cau thiet ke co khi sang JSON dac ta tham so.
Chi tra ve DUY NHAT mot JSON object hop le, khong them loi giai thich, khong dung markdown code fence.

Schema JSON bat buoc:
{
  "part_type": "plate" | "bracket" | "flange" | "shaft" | "housing" | "stepped_shaft",
  "base_dimensions": {...tuy part_type, don vi mm...},
  "features": [ {"type": "hole"|"fillet"|"chamfer"|"pocket"|"boss"|"slot"|"keyway"|"bolt_circle"|"radial_hole"|"counterbore", "params": {...}} ],
  "constraints": [],
  "material": "ten vat lieu hoac null",
  "tolerance": 0.1
}

Quy tac base_dimensions theo part_type:
  plate:         {"length":..,"width":..,"thickness":..}
  bracket:       {"length":..,"width":..,"thickness":.., "leg_height":.., "leg_thickness":..}  (leg_height/leg_thickness dung khi can gia do hinh chu L that, bo trong neu chi can khoi hop don gian)
  flange:        {"outer_diameter":..,"inner_diameter":..,"thickness":..}
  shaft:         {"diameter":..,"length":..}
  stepped_shaft: {"segments":[{"diameter":..,"length":..}, ...]}  (dung khi truc co tu 2 doan duong kinh khac nhau tro len)
  housing:       {"length":..,"width":..,"height":..,"wall_thickness":..}

Quy tac feature params:
  hole:        {"diameter":.., "depth":"through"|<so mm>, "positions":[[x,y],...]}
  fillet:      {"radius":.., "edges":"all"|"corners"|"top"|"bottom"}
  chamfer:     {"distance":.., "edges":"all"|"top"|"bottom"}
  pocket:      {"length":..,"width":..,"depth":..,"position":[x,y]}
  boss:        {"diameter":..,"height":..,"position":[x,y]}
  slot:        {"length":..,"width":..,"depth":"through"|<so>, "position":[x,y], "angle":0}
  keyway:      {"width":.., "depth":.., "length":.., "z_start":.., "shaft_diameter":..}  (ranh then, dung cho shaft/stepped_shaft)
  bolt_circle: {"count":.., "hole_diameter":.., "pcd":..}  (vong lo bat vit bo tri deu quanh tam, dung cho flange)
  radial_hole: {"diameter":.., "height_from_base":..}  (lo khoan ngang xuyen qua truc, vuong goc truc chinh, dung cho shaft/stepped_shaft; height_from_base tinh tu day Z=0)
  counterbore: {"diameter":.., "cbore_diameter":.., "cbore_depth":.., "positions":[[x,y],...]}  (lo bac/lo chim dau vit: lo nho xuyen suot + lo to nong o mat tren de chim dau bu long)

positions/position tinh theo he toa do tam mat phang dat tai tam hinh hoc cua base.

QUAN TRONG - Tu choi yeu cau khong phu hop:
Neu yeu cau cua nguoi dung KHONG the mo ta bang cac part_type va feature_type o tren
(vi du: co ren, banh rang, bien dang tu do phuc tap, lap ghep nhieu bo phan,
mat cat bac phuc tap nhieu tang khong doi xung...),
HOAC khong du thong tin de xac dinh kich thuoc co ban,
HOAC khong phai la mo ta 1 chi tiet co khi (cau vo nghia, cau hoi khac, chao hoi...),
thi KHONG duoc co gang ep vao 1 part_type bat ky de tra loi cho co.
Thay vao do, PHAI tra ve DUY NHAT JSON dang:
{"error": "<mo ta ngan gon bang tieng Viet ly do khong xu ly duoc>"}
"""


class LLMClient(ABC):
    @abstractmethod
    def nl_to_spec(self, nl_request: str) -> PartSpec:
        ...

    @abstractmethod
    def repair_spec(self, nl_request: str, current_spec: PartSpec, errors: list[str]) -> PartSpec:
        ...


class ClaudeLLMClient(LLMClient):
    """Client that, goi Anthropic API. Can: pip install anthropic
    va export ANTHROPIC_API_KEY=sk-...
    """

    def __init__(self, model: str = "claude-sonnet-4-6"):
        import anthropic

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
        data = self._call(f"Yeu cau thiet ke:\n{nl_request}")
        if "error" in data:
            raise ValueError(f"Khong the xu ly yeu cau: {data['error']}")
        return PartSpec.from_dict(data)

    def repair_spec(self, nl_request: str, current_spec: PartSpec, errors: list[str]) -> PartSpec:
        prompt = (
            f"Yeu cau thiet ke goc:\n{nl_request}\n\n"
            f"Spec hien tai (da sinh nhung con loi):\n{current_spec.to_json()}\n\n"
            f"Cac loi can sua:\n" + "\n".join(f"- {e}" for e in errors) + "\n\n"
            "Hay sua lai spec de khac phuc cac loi tren, giu nguyen cac phan da dung. "
            "Tra ve JSON day du theo dung schema, khong giai thich."
        )
        data = self._call(prompt)
        if "error" in data:
            raise ValueError(f"Khong the sua duoc yeu cau: {data['error']}")
        return PartSpec.from_dict(data)


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    return text


class DemoLLMClient(LLMClient):
    """Client gia lap KHONG goi API - dung de chay thu toan bo pipeline khi
    chua co ANTHROPIC_API_KEY hoac chua co mang. Chi nhan dien duoc cau mau
    trong examples/plate_4holes_request.txt bang keyword-matching tho so.
    """

    def nl_to_spec(self, nl_request: str) -> PartSpec:
        from spec_schema import example_plate_spec

        text = nl_request.lower()
        if "tam" in text or "plate" in text:
            return example_plate_spec()
        raise NotImplementedError(
            "DemoLLMClient chi ho tro cau mau 'tam phang...'. "
            "Dung ClaudeLLMClient voi API key that cho cau yeu cau tu do."
        )

    def repair_spec(self, nl_request: str, current_spec: PartSpec, errors: list[str]) -> PartSpec:
        return current_spec


def get_default_client() -> LLMClient:
    """Tra ve ClaudeLLMClient neu co API key + da cai `anthropic`,
    nguoc lai fallback ve DemoLLMClient de khong chan viec chay thu.
    """
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            return ClaudeLLMClient()
        except ImportError:
            print("[llm_client] Chua cai `anthropic` (pip install anthropic). Dung DemoLLMClient.")
    else:
        print("[llm_client] Chua set ANTHROPIC_API_KEY. Dung DemoLLMClient (chi chay duoc cau mau).")
    return DemoLLMClient()