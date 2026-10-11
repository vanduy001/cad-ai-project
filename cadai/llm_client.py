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
from cadai.spec_schema import PartSpec, validate_spec

SYSTEM_PROMPT = """Ban la bo chuyen doi yeu cau thiet ke co khi sang JSON dac ta tham so.
Chi tra ve DUY NHAT mot JSON object hop le, khong them loi giai thich, khong dung markdown code fence.

Schema JSON bat buoc:
{
  "part_type": "plate" | "bracket" | "flange" | "shaft" | "housing" | "stepped_shaft" | "pillow_block" | "bolt" | "nut" | "washer" | "pin" | "flat_plate" | "countersunk_screw",
  "base_dimensions": {...tuy part_type, don vi mm...},
  "features": [ {"type": "hole"|"fillet"|"chamfer"|"pocket"|"boss"|"slot"|"keyway"|"bolt_circle"|"radial_hole"|"counterbore"|"side_lugs"|"thread", "params": {...}} ],
  "constraints": [],
  "material": "ten vat lieu hoac null",
  "tolerance": 0.1
}

Quy tac base_dimensions theo part_type:
  plate:         {"length":..,"width":..,"thickness":..}
  bracket:       {"length":..,"width":..,"thickness":.., "leg_height":.., "leg_thickness":..}
  flange:        {"outer_diameter":..,"inner_diameter":..,"thickness":..}
  shaft:         {"diameter":..,"length":..}
  stepped_shaft: {"segments":[{"diameter":..,"length":..}, ...]}
  housing:       {"length":..,"width":..,"height":..,"wall_thickness":..}
  pillow_block:  {"length":..,"depth":..,"height":..,"base_height":..,"top_width":..,"seat_radius":..}
  bolt:          {"diameter":..,"length":.., "head_width":.. (tuy chon), "head_height":.. (tuy chon), "chamfer":.. (tuy chon)}
    (bu-long don gian: dau luc giac + than tru, khong co ren xoan 3D thuc)
  nut:           {"diameter":..,"height":.., "width":.. (tuy chon)}
    (dai oc luc giac co lo xuyen giua; diameter la duong kinh lo)
  washer:        {"outer_diameter":..,"inner_diameter":..,"thickness":..}
    (vong dem: hinh tru phang co lo o giua; outer_diameter phai lon hon inner_diameter;
     vd vong dem M8: inner_diameter=8.4, outer_diameter=16, thickness=1.6)
  pin:           {"diameter":..,"length":.., "chamfer":.. (tuy chon)}
    (chot tru / chot dinh vi: hinh tru thang, vat can 2 dau; chamfer mac dinh ~5% diameter)
  flat_plate:    {"length":..,"width":..,"thickness":.., "hole_diameter":.. (tuy chon), "hole_margin":.. (tuy chon)}
    (tam phang chu nhat; neu co hole_diameter se tu dong tao 4 lo goc cach mep hole_margin mm;
     hole_margin mac dinh ~8% chieu nho nhat cua tam)
  countersunk_screw: {"diameter":..,"length":.., "head_diameter":.. (tuy chon), "head_height":.. (tuy chon), "chamfer":.. (tuy chon)}
    (vit dau chim: than tru + dau hinh non; diameter la duong kinh than;
     head_diameter mac dinh ~2x diameter, head_height mac dinh ~0.6x diameter)

Quy tac feature params:
  hole:        {"diameter":.., "depth":"through"|<so mm>, "positions":[[x,y],...]}
  fillet:      {"radius":.., "edges":"all"|"corners"|"top"|"bottom"}
  chamfer:     {"distance":.., "edges":"all"|"top"|"bottom"}
  pocket:      {"length":..,"width":..,"depth":..,"position":[x,y]}
  boss:        {"diameter":..,"height":..,"position":[x,y]}
  slot:        {"length":..,"width":..,"depth":"through"|<so>, "position":[x,y], "angle":0}
  keyway:      {"width":.., "depth":.., "length":.., "z_start":.., "shaft_diameter":..}
  bolt_circle: {"count":.., "hole_diameter":.., "pcd":..}
  radial_hole: {"diameter":.., "height_from_base":..}
  counterbore: {"diameter":.., "cbore_diameter":.., "cbore_depth":.., "positions":[[x,y],...]}
  side_lugs:   {"lug_length":.., "lug_thickness":..}
  thread:      {"designation":"M8", "diameter":.., "depth":"through"|<so mm>, "positions":[[x,y],...]}

positions/position tinh theo he toa do tam mat phang dat tai tam hinh hoc cua base.

QUAN TRONG - Tu choi yeu cau khong phu hop:
Neu yeu cau KHONG the mo ta bang cac part_type va feature_type o tren
(vi du: banh rang, bien dang tu do phuc tap, lap ghep nhieu bo phan,
bu-long/dai oc co ren xoan 3D thuc chi tiet,
vit dau chim co ren xoan 3D thuc chi tiet...),
HOAC khong du thong tin de xac dinh kich thuoc co ban,
HOAC khong phai la mo ta 1 chi tiet co khi,
thi PHAI tra ve DUY NHAT JSON dang:
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
    """Client that, goi Anthropic API."""

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
    """Client gia lap KHONG goi API."""

    def nl_to_spec(self, nl_request: str) -> PartSpec:
        from cadai.spec_schema import example_plate_spec
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
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            return ClaudeLLMClient()
        except ImportError:
            print("[llm_client] Chua cai `anthropic`. Dung DemoLLMClient.")
    else:
        print("[llm_client] Chua set ANTHROPIC_API_KEY. Dung DemoLLMClient.")
    return DemoLLMClient()