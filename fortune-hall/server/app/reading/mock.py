"""假資料模式：不呼叫 AI，依盤面資料套用固定句型產生台詞腳本。

用途是開發前端與動畫時不花錢；內容只求「格式正確、點亮位置正確」，不代表真正的解讀。
"""
from __future__ import annotations

from typing import Any

from .. import content

TAG = "（示範模式）"


def _stars(p: dict[str, Any]) -> list[str]:
    return [s["name"] for s in p.get("major_stars", [])]


def _ziwei(chart: dict[str, Any], name: str) -> list[tuple[str, list[str], int]]:
    palaces = {p["name"]: p for p in chart["chart"]["palaces"]}
    ming = palaces["命宮"]
    stars = _stars(ming) or ["空宮"]
    lines = [
        (f"{name}，你的命宮在{ming['ganzhi']}，坐的是{'、'.join(stars)}。",
         ["palace:命宮"] + [f"star:{s}" for s in _stars(ming)], 2),
    ]
    shen = next(p for p in chart["chart"]["palaces"] if p["is_shen_gong"])
    lines.append((f"身宮落在{shen['name']}，後天的重心，在這裡。", [f"palace:{shen['name']}"], 1))
    for sh in chart["chart"]["year_sihua"]:
        lines.append((f"生年{sh['type']}，落在{sh['palace']}宮的{sh['star']}。",
                      [f"palace:{sh['palace']}", f"star:{sh['star']}", f"sihua:{sh['type']}"], 3))
    if hz := chart.get("horoscope"):
        y = hz["yearly"]
        lines.append((f"今年{y['ganzhi']}年，流年命宮走到你的{y['ming_on_natal_palace']}宮。",
                      [f"palace:{y['ming_on_natal_palace']}"], 4))
    return lines


def _bazi(chart: dict[str, Any], name: str) -> list[tuple[str, list[str], int]]:
    p = chart["pillars"]
    lines = [(f"{name}，你的八字是{'、'.join(x['gan'] + x['zhi'] for x in p)}。",
              [f"pillar:{x['key']}" for x in p], 3)]
    lines.append((f"日主是{chart['day_master']}，這就是你自己。", ["pillar:day"], 1))
    for s in chart["shensha"][:2]:
        lines.append((f"命帶{s['name']}，見於{s['where']}。", [f"shensha:{s['name']}"], 2))
    for d in chart["dayun"][1:4]:
        lines.append((f"{d['ages']}，走{d['ganzhi']}大運。", [f"dayun:{d['ganzhi']}"], 4))
    return lines


def _qimen(chart: dict[str, Any], name: str) -> list[tuple[str, list[str], int]]:
    c = chart["chart"]
    lines = [(f"{c['dun_type']}{c['ju_number']}局。這局，我看到了。", [], 1),
             (f"值符{c['zhifu']['star']}落{c['zhifu']['palace']}宮。", [f"palace:{c['zhifu']['palace']}"], 3),
             (f"值使{c['zhishi']['door']}落{c['zhishi']['palace']}宮。",
              [f"palace:{c['zhishi']['palace']}", f"door:{c['zhishi']['door']}"], 3)]
    for p in c["palaces"]:
        if p.get("door") in ("開門", "生門", "休門"):
            lines.append((f"{p['name']}有{p['door']}，方向在{p['direction']}。",
                          [f"palace:{p['palace']}", f"door:{p['door']}"], 2))
    return lines


def _tarot(chart: dict[str, Any], name: str) -> list[tuple[str, list[str], int]]:
    lines = [(f"親愛的{name}，你抽到的是{chart['spread_name']}。", [], 1)]
    for i, c in enumerate(chart["cards"]):
        lines.append((f"{c['position']}的位置，是{c['card']}，{c['orientation']}。", [f"card:{i}"], 2 + i % 3))
    return lines


def _yinyuan(chart: dict[str, Any], name: str) -> list[tuple[str, list[str], int]]:
    a = chart["a"]
    if chart["mode"] == "single":
        return [(f"{name}，你屬{a['zodiac']}，日主是{a['bazi']['day_master']}。",
                 ["person:a", "a.pillar:day"], 0)]
    b = chart["b"]
    lines = [(f"哎唷，一個屬{a['zodiac']}、一個屬{b['zodiac']}！", ["person:a", "person:b"], 1)]
    for i, r in enumerate(chart["relations"][:5]):
        lines.append((f"{r['position']}有{r['detail']}。", [f"relation:{i}"], 2 if r["tone"] == "合" else 3))
    return lines


_BUILDERS = {"ziwei": _ziwei, "bazi": _bazi, "qimen": _qimen, "tarot": _tarot, "yinyuan": _yinyuan}


def build(teacher: str, chart: dict[str, Any], profile: dict[str, Any],
          followup: str | None = None) -> dict[str, Any]:
    p = content.persona(teacher)
    exprs = p["profile"]["expressions"]
    name = profile.get("name") or "你"
    if followup:
        body = [(f"你問的是：{followup.rstrip('？?。! ')}。這是示範模式，接上 AI 後我才會真正回答。", [], 1)]
    else:
        body = _BUILDERS[teacher](chart, name)
    closing = p["profile"]["catchphrases"][0]
    lines = [{"say": TAG + say if i == 0 else say, "highlight": hl, "expression": exprs[e % len(exprs)]}
             for i, (say, hl, e) in enumerate(body)]
    lines.append({"say": closing, "highlight": [], "expression": exprs[0]})
    report = "\n".join([f"# {p['name']}的解讀{TAG}", ""] + [f"- {line['say']}" for line in lines])
    return {"lines": lines, "report_markdown": report}
