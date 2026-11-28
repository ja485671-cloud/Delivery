"""AI 供應商。用環境變數 AI_PROVIDER 切換：mock（預設，不花錢）、openai。

要加別家（例如 Anthropic）時，在這裡新增一個 class，實作 generate() 就好，其他程式不用動。
"""
from __future__ import annotations

import json
import os
from typing import Any, Protocol


class Provider(Protocol):
    name: str

    def generate(self, *, system: str, user: str, schema: dict[str, Any]) -> dict[str, Any]: ...


class ProviderError(RuntimeError):
    pass


class OpenAIProvider:
    name = "openai"

    def __init__(self, client: Any = None, model: str | None = None) -> None:
        self.model = model or os.environ.get("OPENAI_MODEL")
        if not self.model:
            raise ProviderError("請在 server/.env 設定 OPENAI_MODEL（要用的模型名稱）")
        if client is None:
            if not os.environ.get("OPENAI_API_KEY"):
                raise ProviderError("請在 server/.env 設定 OPENAI_API_KEY")
            from openai import OpenAI
            client = OpenAI()
        self.client = client

    def generate(self, *, system: str, user: str, schema: dict[str, Any]) -> dict[str, Any]:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            response_format={"type": "json_schema",
                             "json_schema": {"name": "reading_script", "strict": True, "schema": schema}},
        )
        msg = resp.choices[0].message
        if getattr(msg, "refusal", None):
            raise ProviderError(f"AI 拒絕回答：{msg.refusal}")
        try:
            return json.loads(msg.content)
        except (TypeError, json.JSONDecodeError) as exc:
            raise ProviderError("AI 回傳的格式不正確") from exc


def current() -> str:
    return (os.environ.get("AI_PROVIDER") or "mock").strip().lower()


def get(name: str | None = None) -> Provider | None:
    """回傳 None 代表 mock 模式（由 mock.py 依盤面產生假台詞）。"""
    name = name or current()
    if name == "mock":
        return None
    if name == "openai":
        return OpenAIProvider()
    raise ProviderError(f"不認得的 AI_PROVIDER：{name}（可用：mock、openai）")
