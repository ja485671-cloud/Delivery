"""台詞腳本的格式：給 AI 的 JSON Schema，以及回來之後的檢查與清理。"""
from __future__ import annotations

from typing import Any


def json_schema(codes: list[str], expressions: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["lines", "report_markdown"],
        "properties": {
            "lines": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["say", "highlight", "expression"],
                    "properties": {
                        "say": {"type": "string"},
                        "highlight": {"type": "array", "items": {"type": "string", "enum": codes}},
                        "expression": {"type": "string", "enum": expressions},
                    },
                },
            },
            "report_markdown": {"type": "string"},
        },
    }


def clean(raw: dict[str, Any], codes: list[str], expressions: list[str]) -> dict[str, Any]:
    """不合法的點亮代號直接丟掉、不合法的表情改成 idle，確保前端不會壞。"""
    allowed = set(codes)
    default_expr = "idle" if "idle" in expressions else expressions[0]
    lines = []
    for line in raw.get("lines") or []:
        say = str(line.get("say") or "").strip()
        if not say:
            continue
        expr = line.get("expression")
        lines.append({
            "say": say,
            "highlight": [h for h in line.get("highlight") or [] if h in allowed],
            "expression": expr if expr in expressions else default_expr,
        })
    if not lines:
        raise ValueError("AI 沒有產生任何台詞")
    return {"lines": lines, "report_markdown": str(raw.get("report_markdown") or "").strip()}
