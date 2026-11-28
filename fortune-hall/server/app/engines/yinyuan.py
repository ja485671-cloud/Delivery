"""姻緣合盤：兩人各排八字（有時辰再加紫微），並列出兩盤之間的合、沖、刑、害。

yinyuan 技能本身沒有計算腳本，這裡的合沖表是標準干支關係，只產生「事實清單」，
好壞輕重交給 AI 依 yinyuan 技能的參考資料解讀。
"""
from __future__ import annotations

from datetime import date
from itertools import combinations
from typing import Any

from . import bazi, ziwei

ZODIAC = dict(zip("子丑寅卯辰巳午未申酉戌亥", "鼠牛虎兔龍蛇馬羊猴雞狗豬"))

GAN_HE = {frozenset(p): f"{p[0]}{p[1]}合" for p in ("甲己", "乙庚", "丙辛", "丁壬", "戊癸")}
GAN_CHONG = {frozenset(p): f"{p[0]}{p[1]}沖" for p in ("甲庚", "乙辛", "丙壬", "丁癸")}

ZHI_RULES: list[tuple[str, str, int, list[str]]] = [
    # (類別, 吉凶傾向, 分數權重, 配對)
    ("六合", "合", 2, ["子丑", "寅亥", "卯戌", "辰酉", "巳申", "午未"]),
    ("六沖", "沖", -2, ["子午", "丑未", "寅申", "卯酉", "辰戌", "巳亥"]),
    ("六害", "害", -1, ["子未", "丑午", "寅巳", "卯辰", "申亥", "酉戌"]),
    ("相刑", "刑", -1, ["寅巳", "巳申", "寅申", "丑戌", "戌未", "丑未", "子卯"]),
]
SANHE = {"申子辰": "水", "亥卯未": "木", "寅午戌": "火", "巳酉丑": "金"}

_ZHI_TABLE: dict[frozenset, list[tuple[str, str, int]]] = {}
for _cat, _tone, _w, _pairs in ZHI_RULES:
    for _p in _pairs:
        _ZHI_TABLE.setdefault(frozenset(_p), []).append((_cat, _tone, _w))
for _group, _wx in SANHE.items():
    for _a, _b in combinations(_group, 2):
        _ZHI_TABLE.setdefault(frozenset(_a + _b), []).append((f"半三合{_wx}局", "合", 1))


def _relations(a: dict[str, Any], b: dict[str, Any]) -> list[dict[str, Any]]:
    """比對兩人同一柱位（年對年、月對月、日對日、時對時）。"""
    rels = []
    for pa, pb in zip(a["pillars"], b["pillars"]):
        if pa["key"] == "hour" and (a["hour_unknown"] or b["hour_unknown"]):
            continue
        g = frozenset((pa["gan"], pb["gan"]))
        for table, tone, w in ((GAN_HE, "合", 2), (GAN_CHONG, "沖", -1)):
            if g in table:
                rels.append({"position": pa["label"], "kind": "天干" + table[g][-1],
                             "detail": table[g], "tone": tone, "weight": w})
        z = frozenset((pa["zhi"], pb["zhi"]))
        for cat, tone, w in _ZHI_TABLE.get(z, []):
            rels.append({"position": pa["label"], "kind": "地支" + cat,
                         "detail": f"{pa['zhi']}{pb['zhi']}{cat}", "tone": tone, "weight": w})
    # 日柱是夫妻宮，加倍
    for r in rels:
        if r["position"] == "日柱":
            r["weight"] *= 2
    return rels


def chart(*, a: dict[str, Any], b: dict[str, Any] | None) -> dict[str, Any]:
    """a、b 為各自的出生資料（同 bazi.chart 參數，外加 name）。b 為 None 表示單身，只看 a 的桃花。"""
    def one(p: dict[str, Any]) -> dict[str, Any]:
        args = {k: p[k] for k in ("calendar", "birth_date", "birth_time", "gender", "is_leap_month")}
        person: dict[str, Any] = {"name": p.get("name"), "bazi": bazi.chart(**args, place=p.get("place"))}
        if p.get("birth_time"):
            person["ziwei"] = ziwei.chart(**args, query_year=date.today().year)
        person["zodiac"] = ZODIAC[person["bazi"]["pillars"][0]["zhi"]]
        return person

    pa = one(a)
    if b is None:
        return {"mode": "single", "a": pa}
    pb = one(b)
    rels = _relations(pa["bazi"], pb["bazi"])
    score = sum(r["weight"] for r in rels)
    return {"mode": "couple", "a": pa, "b": pb, "relations": rels, "raw_score": score,
            # 同性伴侶一樣可以合盤；傳統「夫星／妻星」的說法交給 AI 調整
            "same_gender": pa["bazi"]["gender"] == pb["bazi"]["gender"]}

