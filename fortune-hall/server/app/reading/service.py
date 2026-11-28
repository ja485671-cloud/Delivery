"""AI 解讀的進入點：組提示詞 → 呼叫供應商（或 mock）→ 檢查清理 → 回傳台詞腳本。"""
from __future__ import annotations

from typing import Any

from .. import content
from . import highlights, mock, prompt, providers, schema


def read(teacher: str, *, chart: dict[str, Any], profile: dict[str, Any],
         answers: list[dict[str, Any]], followup: str | None = None,
         provider: providers.Provider | None = None, use_mock: bool | None = None) -> dict[str, Any]:
    if use_mock is None:
        use_mock = provider is None and providers.current() == "mock"
    if not use_mock:
        provider = provider or providers.get()  # 先檢查設定，設定有誤就不必往下算

    codes = highlights.codes(teacher, chart)
    exprs = content.persona(teacher)["profile"]["expressions"]

    if use_mock:
        raw = mock.build(teacher, chart, profile, followup)
        source = "mock"
    else:
        assert provider is not None
        raw = provider.generate(
            system=prompt.system_prompt(teacher),
            user=prompt.user_prompt(chart=chart, profile=profile, answers=answers,
                                    codes=codes, expressions=exprs, followup=followup),
            schema=schema.json_schema(codes, exprs),
        )
        source = provider.name
    return {**schema.clean(raw, codes, exprs), "source": source}
