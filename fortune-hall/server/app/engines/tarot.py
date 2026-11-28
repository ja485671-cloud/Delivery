"""塔羅：使用者在畫面上親手選牌，選到的位置決定亂數種子，再交給 tarot 技能腳本抽牌。

同樣的問題、牌陣與選牌位置會得到同樣的結果（可重現），方便之後存紀錄或除錯。
"""
from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from .. import skills, tw
from ..common import ChartError

DECK_SIZE = 78


def spreads() -> list[dict[str, Any]]:
    mod = skills.load("tarot")
    result = []
    for key, (name, raw) in mod.SPREADS.items():
        positions = [item.split(",")[0] for item in raw.split("|")]
        result.append({"key": key, "name": name, "positions": positions})
    return tw.deep(result)


def draw(*, question: str, spread: str, picks: list[int], timezone: str = "Asia/Taipei") -> dict[str, Any]:
    mod = skills.load("tarot")
    if spread not in mod.SPREADS:
        raise ChartError(f"沒有這個牌陣：{spread}")
    need = len(mod.SPREADS[spread][1].split("|"))
    if len(picks) != need or len(set(picks)) != need or not all(0 <= p < DECK_SIZE for p in picks):
        raise ChartError(f"這個牌陣要從 {DECK_SIZE} 張牌裡選 {need} 張不重複的牌。")
    digest = hashlib.sha256(f"{question}|{spread}|{','.join(map(str, picks))}".encode()).hexdigest()
    seed = int(digest[:16], 16)
    hour = datetime.now(ZoneInfo(timezone)).hour
    out = mod.draw_cards(spread, question, seed=seed, time_factor=mod.get_time_factor(hour))
    out["picks"] = picks
    return tw.deep(out)
