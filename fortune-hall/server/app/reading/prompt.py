"""組合送給 AI 的提示詞：共同規則 + 老師人設 + 老師的 prompt.md + 技能知識 + 這次的盤與回答。"""
from __future__ import annotations

import json
from typing import Any

import yaml

from .. import content

LINE_COUNT = "15 到 25"


def _persona_brief(p: dict[str, Any]) -> str:
    brief = {
        "名字": p["name"],
        "主題": p["subject"],
        "人設": p["profile"],
        "解讀順序": p.get("reading", {}).get("order"),
    }
    return yaml.safe_dump(brief, allow_unicode=True, sort_keys=False)


def system_prompt(teacher: str) -> str:
    p = content.persona(teacher)
    return "\n\n".join([
        content.shared_rules().replace("{line_count}", LINE_COUNT),
        f"# 你扮演的老師\n\n```yaml\n{_persona_brief(p)}```",
        content.teacher_prompt(teacher),
        "# 命理知識（簡體，僅供依據）\n\n" + content.knowledge(teacher),
    ])


def user_prompt(*, chart: dict[str, Any], profile: dict[str, Any], answers: list[dict[str, Any]],
                codes: list[str], expressions: list[str], followup: str | None = None) -> str:
    parts = [
        "# 客人資料\n" + json.dumps(profile, ensure_ascii=False),
        "# 確認問題與客人的回答\n" + json.dumps(answers, ensure_ascii=False),
        "# 排盤結果\n" + json.dumps(chart, ensure_ascii=False),
        "# 可點亮代號（highlight 只能用這些）\n" + json.dumps(codes, ensure_ascii=False),
        "# 表情（expression 只能用這些）\n" + json.dumps(expressions, ensure_ascii=False),
    ]
    if followup:
        parts.append("# 客人追問\n" + followup
                     + "\n\n這是解盤後的追問：台詞約 4 到 10 句，直接回答這個問題；report_markdown 寫這題的完整回答。")
    else:
        parts.append("請開始解盤，輸出台詞腳本 JSON。")
    return "\n\n".join(parts)
