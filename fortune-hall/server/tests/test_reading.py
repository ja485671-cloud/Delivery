"""AI 解讀模組測試：確認問題、提示詞組裝、mock 模式、OpenAI 供應商（用假 client，不花錢）。"""
import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app import content
from app.main import app
from app.reading import highlights, prompt, providers, schema, service

client = TestClient(app)
ME = {"name": "測試", "birth_date": "1998-08-19", "birth_time": "15:44", "gender": "男", "place": "台北市"}

CHART_REQUESTS = {
    "ziwei": ("/api/chart/ziwei", {**ME, "query_year": 2026}),
    "bazi": ("/api/chart/bazi", ME),
    "qimen": ("/api/chart/qimen", {"question": "該不該離職", "at": "2026-11-21T13:36:00", "city": "新北"}),
    "tarot": ("/api/chart/tarot", {"question": "感情", "spread": "three", "picks": [3, 50, 77]}),
    "yinyuan": ("/api/chart/yinyuan", {"a": ME, "b": {"birth_date": "1999-03-10", "gender": "女"}}),
}


@pytest.fixture(scope="module")
def charts():
    return {t: client.post(url, json=body).json() for t, (url, body) in CHART_REQUESTS.items()}


@pytest.fixture(autouse=True)
def _mock_mode(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "mock")


def test_teachers_list_and_detail():
    lst = client.get("/api/teachers").json()
    assert [t["id"] for t in lst] == list(content.TEACHERS)
    d = client.get("/api/teachers/ziwei").json()
    assert d["name"] == "天璣老人" and "knowledge" not in d["reading"]
    assert client.get("/api/teachers/nobody").status_code == 404


@pytest.mark.parametrize("teacher", content.TEACHERS)
def test_every_knowledge_ref_resolves(teacher):
    # persona.yaml 寫錯檔名或標題時，這裡會抓到
    text = content.knowledge(teacher)
    assert len(text) > 1000
    sp = prompt.system_prompt(teacher)
    assert content.persona(teacher)["name"] in sp and "{line_count}" not in sp


def test_ziwei_questions_auto_event(charts):
    qs = client.post("/api/reading/ziwei/questions", json={"chart": charts["ziwei"], "name": "小明"}).json()
    assert len(qs) == 3
    assert "{auto" not in json.dumps(qs, ensure_ascii=False)
    assert "歲那段時間" in qs[1]["ask"] and "purpose" not in qs[1]


def test_bazi_questions_auto_year(charts):
    qs = client.post("/api/reading/bazi/questions", json={"chart": charts["bazi"]}).json()
    assert "年這幾年" in qs[0]["ask"]


def test_yinyuan_questions_follow_mode(charts):
    qs = client.post("/api/reading/yinyuan/questions", json={"chart": charts["yinyuan"]}).json()
    assert qs[0]["id"] == "status"


@pytest.mark.parametrize("teacher", content.TEACHERS)
def test_mock_reading_highlights_are_valid(teacher, charts):
    body = {"chart": charts[teacher], "profile": {"name": "小明"},
            "answers": [{"id": "focus", "question": "最想問？", "answer": "事業"}]}
    r = client.post(f"/api/reading/{teacher}", json=body).json()
    assert r["source"] == "mock" and len(r["lines"]) >= 2
    codes = set(highlights.codes(teacher, charts[teacher]))
    exprs = content.persona(teacher)["profile"]["expressions"]
    assert any(line["highlight"] for line in r["lines"])
    for line in r["lines"]:
        assert set(line["highlight"]) <= codes and line["expression"] in exprs


def test_followup_mock(charts):
    r = client.post("/api/reading/tarot", json={"chart": charts["tarot"], "followup": "那他會回來嗎？"}).json()
    assert "那他會回來嗎" in r["lines"][0]["say"]


def test_clean_drops_bad_values():
    raw = {"lines": [{"say": "嗨", "highlight": ["palace:命宮", "palace:亂寫"], "expression": "dance"},
                     {"say": "  ", "highlight": [], "expression": "idle"}],
           "report_markdown": "x"}
    out = schema.clean(raw, ["palace:命宮"], ["idle", "smile"])
    assert out["lines"] == [{"say": "嗨", "highlight": ["palace:命宮"], "expression": "idle"}]
    with pytest.raises(ValueError):
        schema.clean({"lines": []}, [], ["idle"])


class FakeOpenAI:
    """模擬 OpenAI SDK：記下送出的參數，回傳固定的 JSON。"""

    def __init__(self, payload):
        self.payload, self.sent = payload, None
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.sent = kwargs
        msg = SimpleNamespace(content=json.dumps(self.payload, ensure_ascii=False), refusal=None)
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)])


def test_openai_provider_sends_strict_schema(charts):
    fake = FakeOpenAI({"lines": [{"say": "老夫看見了。", "highlight": ["palace:命宮"], "expression": "gaze"}],
                       "report_markdown": "## 命宮"})
    prov = providers.OpenAIProvider(client=fake, model="test-model")
    r = service.read("ziwei", chart=charts["ziwei"], profile={"name": "小明"}, answers=[], provider=prov)
    assert r["source"] == "openai" and r["lines"][0]["highlight"] == ["palace:命宮"]
    rf = fake.sent["response_format"]
    assert fake.sent["model"] == "test-model" and rf["json_schema"]["strict"] is True
    item = rf["json_schema"]["schema"]["properties"]["lines"]["items"]
    assert "palace:命宮" in item["properties"]["highlight"]["items"]["enum"]
    assert "台灣繁體中文" in fake.sent["messages"][0]["content"]
    assert "小明" in fake.sent["messages"][1]["content"]


def test_openai_requires_config(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    r = client.post("/api/reading/tarot", json={"chart": {"cards": [], "spread_name": "x"}})
    assert r.status_code == 503 and "OPENAI_MODEL" in r.json()["error"]
