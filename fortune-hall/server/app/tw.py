"""技能腳本輸出是簡體中文，送到前端前一律轉成台灣繁體。"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

import opencc

# OpenCC 轉完後，命理用語再依台灣習慣修正
_FIXES = {
    "天衝": "天沖",
    "聖盃": "聖杯",
}


@lru_cache(maxsize=1)
def _converter() -> opencc.OpenCC:
    return opencc.OpenCC("s2tw")


def text(s: str) -> str:
    out = _converter().convert(s)
    for a, b in _FIXES.items():
        out = out.replace(a, b)
    return out


def deep(obj: Any) -> Any:
    """遞迴轉換 dict / list 裡所有字串（含 key）。"""
    if isinstance(obj, str):
        return text(obj)
    if isinstance(obj, dict):
        return {deep(k) if isinstance(k, str) else k: deep(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [deep(v) for v in obj]
    return obj
