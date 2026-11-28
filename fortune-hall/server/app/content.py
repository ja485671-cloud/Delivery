"""讀取 content/ 底下的老師設定（persona.yaml、prompt.md）與共同規則。"""
from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from . import skills

TEACHERS = ("ziwei", "bazi", "qimen", "tarot", "yinyuan")
_DEFAULT_CONTENT_DIR = Path(__file__).resolve().parents[2] / "content"


def content_dir() -> Path:
    return Path(os.environ.get("CONTENT_DIR") or _DEFAULT_CONTENT_DIR)


def check_teacher(teacher: str) -> None:
    if teacher not in TEACHERS:
        raise KeyError(teacher)


# 開發時改了 YAML 想立刻生效，就不要快取；正式環境檔案不會變，讀檔成本也很低
def persona(teacher: str) -> dict[str, Any]:
    check_teacher(teacher)
    return yaml.safe_load((content_dir() / "teachers" / teacher / "persona.yaml").read_text(encoding="utf-8"))


def teacher_prompt(teacher: str) -> str:
    check_teacher(teacher)
    return (content_dir() / "teachers" / teacher / "prompt.md").read_text(encoding="utf-8")


def shared_rules() -> str:
    return (content_dir() / "shared" / "reading-rules.md").read_text(encoding="utf-8")


_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")


def _section(md: str, heading: str) -> str | None:
    """取出 Markdown 中某個標題到下一個同級或更高級標題之間的內容。"""
    lines = md.splitlines()
    for i, line in enumerate(lines):
        m = _HEADING.match(line)
        if m and m.group(2) == heading:
            level = len(m.group(1))
            out = [line]
            for nxt in lines[i + 1:]:
                n = _HEADING.match(nxt)
                if n and len(n.group(1)) <= level:
                    break
                out.append(nxt)
            return "\n".join(out).strip()
    return None


@lru_cache(maxsize=None)
def knowledge_item(ref: str) -> str:
    """ref 形如 'ziwei-doushu/references/stars.md' 或 'ziwei-doushu/SKILL.md#核心规则'。"""
    path, _, heading = ref.partition("#")
    md = (skills.skills_dir() / path).read_text(encoding="utf-8")
    if not heading:
        return md.strip()
    sec = _section(md, heading)
    if sec is None:
        raise ValueError(f"在 {path} 找不到標題「{heading}」")
    return sec


def knowledge(teacher: str) -> str:
    refs = persona(teacher).get("reading", {}).get("knowledge", [])
    return "\n\n---\n\n".join(f"<!-- 來源：{r} -->\n{knowledge_item(r)}" for r in refs)
