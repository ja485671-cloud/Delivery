"""紫微斗數：呼叫 ziwei-doushu 技能腳本排盤。"""
from __future__ import annotations

from datetime import date
from typing import Any

from .. import skills, tw
from ..common import ChartError, dst_warning


def chart(*, calendar: str, birth_date: date, birth_time: str | None, gender: str,
          is_leap_month: bool = False, query_year: int | None = None) -> dict[str, Any]:
    if not birth_time:
        raise ChartError("紫微斗數需要出生時辰才能排盤。")
    payload: dict[str, Any] = {
        "calendar_type": calendar,
        "birth_time": f"{birth_date.isoformat()} {birth_time}",
        "is_leap_month": is_leap_month,
        "gender": gender,
    }
    if query_year:
        payload["query_year"] = query_year
    try:
        out = skills.load("ziwei").build_output(payload)
    except ValueError as exc:
        raise ChartError(tw.text(str(exc))) from exc
    if calendar == "solar" and (w := dst_warning(birth_date)):
        out.setdefault("warnings", []).append(w)
    return tw.deep(out)
