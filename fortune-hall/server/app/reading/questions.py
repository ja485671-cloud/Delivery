"""確認問題：讀 persona.yaml 的 confirm，把需要看盤才能產生的問題（{auto_...}）填好。

這一步用規則產生，不呼叫 AI：快、免費、結果穩定。
"""
from __future__ import annotations

import re
from datetime import date
from typing import Any

from .. import content


def _ziwei_event_question(chart: dict[str, Any]) -> str:
    """找出 18 歲所在的大限，問那十年有沒有離家或大轉折（用來驗證時辰）。"""
    birth_year = int(chart["normalized_input"]["civil_solar_datetime"][:4])
    for p in chart["chart"]["palaces"]:
        d = p["decadal"]
        if d["start_age"] <= 18 <= d["end_age"]:
            y1, y2 = birth_year + d["start_age"] - 1, birth_year + d["end_age"] - 1  # 大限是虛歲
            return (f"{d['start_age']} 到 {d['end_age']} 歲那段時間，大約是 {y1} 到 {y2} 年，"
                    "你是不是離開了家，或人生有一次大轉折？")
    return "十八歲前後，你是不是離開了家，或人生有一次大轉折？"


def _bazi_year_question(chart: dict[str, Any]) -> str:
    """挑「上一步大運」（已經走完、記憶最清楚），問那十年順不順，用來判定喜用神。"""
    birth_year = int(chart["solar"][:4])
    age_now = date.today().year - birth_year
    rows = [r for r in chart["dayun"] if re.match(r"^\d+-\d+", r["ages"])]
    spans = [(r, *map(int, re.match(r"^(\d+)-(\d+)", r["ages"]).groups())) for r in rows]
    current = next((i for i, (_, a, b) in enumerate(spans) if a <= age_now <= b), None)
    pick = spans[current - 1] if current else spans[0]
    _, a, b = pick
    y1, y2 = birth_year + a, min(birth_year + b, date.today().year - 1)
    return f"回想一下，{y1} 到 {y2} 年這幾年，你整體過得順，還是比較辛苦？"


_AUTO = {
    "auto_event_question": _ziwei_event_question,
    "auto_year_question": _bazi_year_question,
}


def confirm_questions(teacher: str, chart: dict[str, Any], *, name: str | None = None,
                      mode: str | None = None) -> list[dict[str, Any]]:
    confirm = content.persona(teacher)["script"]["confirm"]
    if isinstance(confirm, dict):  # 姻緣：依 couple / single 分流
        confirm = confirm[mode or chart.get("mode", "couple")]
    out = []
    for q in confirm:
        q = dict(q)
        ask = q["ask"]
        for key, fn in _AUTO.items():
            if "{" + key + "}" in ask:
                ask = ask.replace("{" + key + "}", fn(chart))
        if name:
            ask = ask.replace("{name}", name)
        q["ask"] = ask
        q.pop("purpose", None)  # 內部說明，不送前端
        out.append(q)
    return out[:3]
