"""載入 repo 內 .claude/skills/ 的排盤腳本。

排盤一律交給技能腳本計算，這裡只負責把模組載進來；不在網站端重寫任何排盤邏輯。
技能目錄預設為 repo 根目錄的 .claude/skills，可用環境變數 SKILLS_DIR 覆寫（部署到雲端時用）。
"""
from __future__ import annotations

import importlib.util
import os
import sys
from functools import lru_cache
from pathlib import Path
from types import ModuleType

_DEFAULT_SKILLS_DIR = Path(__file__).resolve().parents[3] / ".claude" / "skills"

SCRIPT_PATHS = {
    "ziwei": "ziwei-doushu/scripts/ziwei_cli.py",
    "qimen": "qimen-dunjia/scripts/qimen_cli.py",
    "bazi": "bazi/scripts/pai_pan.py",
    "tarot": "tarot/scripts/draw.py",
}


def skills_dir() -> Path:
    return Path(os.environ.get("SKILLS_DIR") or _DEFAULT_SKILLS_DIR)


@lru_cache(maxsize=None)
def load(name: str) -> ModuleType:
    path = skills_dir() / SCRIPT_PATHS[name]
    if not path.is_file():
        raise RuntimeError(f"找不到排盤腳本：{path}")
    spec = importlib.util.spec_from_file_location(f"skill_{name}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module  # 腳本裡的 dataclass 需要在 sys.modules 找得到自己
    spec.loader.exec_module(module)
    return module
