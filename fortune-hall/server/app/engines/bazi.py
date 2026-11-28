"""八字：呼叫 bazi 技能腳本的 compute()，整理成 JSON。"""
from __future__ import annotations

import re
from datetime import date
from typing import Any

from lunar_python import Lunar, Solar

from .. import skills, tw
from ..common import ChartError, dst_warning

_POSITIONS = (("year", "年柱"), ("month", "月柱"), ("day", "日柱"), ("hour", "時柱"))


def _lunar_text(d: date, birth_time: str | None) -> str:
    # 技能腳本的農曆顯示有誤（會把 1998 年六月印成閏六月），改用 lunar_python 產生
    h, m = (int(x) for x in birth_time.split(":")) if birth_time else (12, 0)
    lunar = Solar.fromYmdHms(d.year, d.month, d.day, h, m, 0).getLunar()
    return f"{lunar.getYearInGanZhi()}年{lunar.getMonthInChinese()}月{lunar.getDayInChinese()}"


def chart(*, calendar: str, birth_date: date, birth_time: str | None, gender: str,
          is_leap_month: bool = False, place: str | None = None) -> dict[str, Any]:
    mod = skills.load("bazi")
    solar_date = birth_date
    if calendar == "lunar":
        # 不用技能腳本的 lunar_to_solar：它的閏月判斷有誤（例如把 1998 年閏五月當成閏六月），
        # 改用 lunar_python（紫微、奇門腳本也是用它）
        try:
            month = -birth_date.month if is_leap_month else birth_date.month
            s = Lunar.fromYmd(birth_date.year, month, birth_date.day).getSolar()
        except Exception as exc:
            raise ChartError("這個農曆日期不存在，請再確認一次（是不是閏月？）") from exc
        solar_date = date(s.getYear(), s.getMonth(), s.getDay())

    hour = minute = None
    if birth_time:
        hour, minute = (int(x) for x in birth_time.split(":"))
    try:
        r = mod.compute(solar_date=solar_date, hour=hour, minute=minute, sex=gender, place=place)
    except ValueError as exc:
        raise ChartError(tw.text(str(exc))) from exc

    pillars = []
    for key, label in _POSITIONS:
        gan, zhi, shishen, canggan = r["pillars"][key]
        pillars.append({"key": key, "label": label, "gan": gan, "zhi": zhi,
                        "shishen": shishen, "canggan": canggan.split("、")})

    dayun = [{"step": step, "ages": ages, "ganzhi": gz} for step, ages, gz in r["dayun_rows"]]

    shensha = []
    for line in r["shensha_lines"]:
        parts = [p.strip() for p in re.sub(r"^-\s*", "", line).split("—")]
        if len(parts) >= 2:
            shensha.append({"name": parts[0], "where": parts[1].removeprefix("见于")})

    warnings = list(r["warnings"])
    if calendar == "solar" and (w := dst_warning(birth_date)):
        warnings.append(w)

    out = {
        "solar": r["solar_text"],
        "lunar": _lunar_text(solar_date, birth_time),
        "shichen": r["shichen_text"],
        "hour_unknown": r["hour_unknown"],
        "gender": gender,
        "place": place,
        "jieqi": r["jie_name"],
        "day_master": pillars[2]["gan"],
        "pillars": pillars,
        "dayun_forward": r["forward"],
        "qiyun": r["qiyun_text"],
        "dayun": dayun,
        "current_year": {"year": r["current_year"], "ganzhi": r["current_gz"]},
        "shensha": shensha,
        "warnings": warnings,
    }
    return tw.deep(out)
