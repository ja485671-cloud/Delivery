"""奇門遁甲：呼叫 qimen-dunjia 技能腳本起局。"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from .. import skills, tw
from ..common import ChartError


def chart(*, question: str, question_type: str, at: datetime | None, city: str,
          timezone: str = "Asia/Taipei", country: str = "台灣") -> dict[str, Any]:
    if not question.strip():
        raise ChartError("奇門要先知道你想問什麼事。")
    when = at or datetime.now(ZoneInfo(timezone))
    payload = {
        "question_type": question_type,
        "question_goal": question,
        "time_input": when.strftime("%Y-%m-%d %H:%M"),
        "calendar_type": "solar",
        "location": {"country": country, "city": city, "timezone": timezone},
        "ruleset": "mainline-cn-v1",
    }
    try:
        out = skills.load("qimen").build_output(payload)
    except ValueError as exc:
        raise ChartError(tw.text(str(exc))) from exc
    return tw.deep(out)
