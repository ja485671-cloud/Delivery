"""每位老師的「可點亮代號」。AI 只能從這份清單挑，前端盤面元件依同樣的代號點亮。

代號格式見 docs/SPEC.md 第 4 節。
"""
from __future__ import annotations

from typing import Any


def _ziwei(chart: dict[str, Any], prefix: str = "") -> list[str]:
    codes: list[str] = []
    for p in chart["chart"]["palaces"]:
        codes.append(f"{prefix}palace:{p['name']}")
        for group in ("major_stars", "minor_stars", "adjective_stars"):
            # 主星、輔星是 {"name": ...}；乙級星（adjective_stars）是純字串
            codes += [f"{prefix}star:{s['name'] if isinstance(s, dict) else s}" for s in p.get(group, [])]
    codes += [f"{prefix}sihua:{t}" for t in ("化祿", "化權", "化科", "化忌")]
    return codes


def _bazi(chart: dict[str, Any], prefix: str = "") -> list[str]:
    codes = [f"{prefix}pillar:{p['key']}" for p in chart["pillars"]]
    codes += [f"{prefix}dayun:{d['ganzhi']}" for d in chart["dayun"]]
    codes += [f"{prefix}shensha:{s['name']}" for s in chart["shensha"]]
    return codes


def _qimen(chart: dict[str, Any]) -> list[str]:
    codes: list[str] = []
    for p in chart["chart"]["palaces"]:
        codes.append(f"palace:{p['palace']}")
        for key in ("door", "star", "god"):
            if p.get(key):
                codes.append(f"{key}:{p[key]}")
    return codes


def _tarot(chart: dict[str, Any]) -> list[str]:
    return [f"card:{i}" for i in range(len(chart["cards"]))]


def _yinyuan(chart: dict[str, Any]) -> list[str]:
    people = ["a"] + (["b"] if chart["mode"] == "couple" else [])
    codes: list[str] = []
    for who in people:
        codes.append(f"person:{who}")
        codes += _bazi(chart[who]["bazi"], f"{who}.")
        if "ziwei" in chart[who]:
            codes += [f"{who}.palace:{p['name']}" for p in chart[who]["ziwei"]["chart"]["palaces"]]
    codes += [f"relation:{i}" for i in range(len(chart.get("relations", [])))]
    return codes


_BUILDERS = {"ziwei": _ziwei, "bazi": _bazi, "qimen": _qimen, "tarot": _tarot, "yinyuan": _yinyuan}


def codes(teacher: str, chart: dict[str, Any]) -> list[str]:
    return list(dict.fromkeys(_BUILDERS[teacher](chart)))  # 去重、保留順序
