"""
llm_client.py
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
  "part_type": "plate"|"bracket"|"flange"|"shaft"|"housing"|"stepped_shaft"|"pillow_block"|"bolt"|"nut"|"washer"|"pin"|"flat_plate"|"countersunk_screw"|"spur_gear"|"pulley"|"cam"|"coupling",
  "base_dimensions": {...tuy part_type, don vi mm...},
  "features": [...],
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
  bolt:          {"diameter":..,"length":.., "head_width":.. (tuy chon), "head_height":.. (tuy chon)}
  nut:           {"diameter":..,"height":.., "width":.. (tuy chon)}
  washer:        {"outer_diameter":..,"inner_diameter":..,"thickness":..}
  pin:           {"diameter":..,"length":.., "chamfer":.. (tuy chon)}
  flat_plate:    {"length":..,"width":..,"thickness":.., "hole_diameter":.. (tuy chon), "hole_margin":.. (tuy chon)}
  countersunk_screw: {"diameter":..,"length":.., "head_diameter":.. (tuy chon), "head_height":.. (tuy chon)}
  spur_gear:     {"num_teeth":..,"module":..,"thickness":.., "bore_diameter":.. (tuy chon), "pressure_angle":.. (tuy chon, mac dinh 20)}
    (banh rang thang; module = duong kinh chia / so rang; vi du banh rang m2 z20: module=2, num_teeth=20;
     num_teeth phai >= 6; bore_diameter la duong kinh lo truc, mac dinh 20% duong kinh chia)
  pulley:        {"outer_diameter":..,"bore_diameter":..,"width":.., "groove_depth":.. (tuy chon), "groove_angle":.. (tuy chon, mac dinh 38)}
    (puly/banh dai: hinh tru co ranh chu V; bore_diameter phai nho hon outer_diameter)
  cam:           {"base_radius":..,"lift":..,"thickness":.., "bore_diameter":.. (tuy chon), "cam_type":.. (tuy chon: "eccentric"|"ellipse", mac dinh "eccentric")}
    (cam dia: lech tam (eccentric) hoac ellipse; lift la hanh trinh/do lech tam)
  coupling:      {"outer_diameter":..,"bore_diameter":..,"total_length":.., "flange_thickness":.. (tuy chon), "bolt_count":.. (tuy chon, mac dinh 4), "bolt_diameter":.. (tuy chon), "pcd":.. (tuy chon)}
    (khop noi truc: 2 mat bich + loi trum; bore_diameter phai nho hon outer_diameter)

Quy tac feature params:
  hole, fillet, chamfer, pocket, boss, slot, keyway, bolt_circle, radial_hole, counterbore, side_lugs, thread
  (giu nguyen nhu cu)

QUAN TRONG - Tu choi yeu cau khong phu hop:
Neu yeu cau KHONG the mo ta bang cac part_type tren, HOAC khong du thong tin,
HOAC khong phai chi tiet co khi, thi tra ve:
{"error": "<mo ta ngan gon bang tieng Viet ly do khong xu ly duoc>"}
"""


class LLMClient(ABC):
    @abstractmethod
    def nl_to_spec(self, nl_request: str) -> PartSpec: ...

    @abstractmethod
    def repair_spec(self, nl_request: str, current_spec: PartSpec, errors: list[str]) -> PartSpec: ...


class ClaudeLLMClient(LLMClient):
    def __init__(self, model: str = "claude-sonnet-4-6"):
        import anthropic
        self.client = anthropic.Anthropic()
        self.model = model

    def _call(self, user_prompt: str) -> dict:
        resp = self.client.messages.create(
            model=self.model, max_tokens=2000, system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = "".join(block.text for block in resp.content if block.type == "text")
        return json.loads(_strip_code_fence(text))

    def nl_to_spec(self, nl_request: str) -> PartSpec:
        data = self._call(f"Yeu cau thiet ke:\n{nl_request}")
        if "error" in data:
            raise ValueError(f"Khong the xu ly yeu cau: {data['error']}")
        return PartSpec.from_dict(data)

    def repair_spec(self, nl_request: str, current_spec: PartSpec, errors: list[str]) -> PartSpec:
        prompt = (
            f"Yeu cau thiet ke goc:\n{nl_request}\n\n"
            f"Spec hien tai:\n{current_spec.to_json()}\n\n"
            "Cac loi can sua:\n" + "\n".join(f"- {e}" for e in errors) +
            "\n\nHay sua lai spec, tra ve JSON day du, khong giai thich."
        )
        data = self._call(prompt)
        if "error" in data:
            raise ValueError(f"Khong the sua duoc: {data['error']}")
        return PartSpec.from_dict(data)


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    return text


class DemoLLMClient(LLMClient):
    def nl_to_spec(self, nl_request: str) -> PartSpec:
        from cadai.spec_schema import example_plate_spec
        if "tam" in nl_request.lower() or "plate" in nl_request.lower():
            return example_plate_spec()
        raise NotImplementedError("DemoLLMClient chi ho tro cau mau tam phang.")

    def repair_spec(self, nl_request: str, current_spec: PartSpec, errors: list[str]) -> PartSpec:
        return current_spec


def get_default_client() -> LLMClient:
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            return ClaudeLLMClient()
        except ImportError:
            print("[llm_client] Chua cai anthropic. Dung DemoLLMClient.")
    else:
        print("[llm_client] Chua set ANTHROPIC_API_KEY. Dung DemoLLMClient.")
    return DemoLLMClient()