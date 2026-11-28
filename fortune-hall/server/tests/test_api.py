"""排盤 API 測試。用張展嘉的資料（已和紙本盤、前次分析核對過）當基準。"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
ME = {"name": "測試", "birth_date": "1998-08-19", "birth_time": "15:44", "gender": "男", "place": "台北市"}


def test_health():
    assert client.get("/api/health").json() == {"ok": True}


def test_ziwei_matches_verified_chart():
    d = client.post("/api/chart/ziwei", json={**ME, "query_year": 2026}).json()
    ming = d["chart"]["palaces"][0]
    assert ming["name"] == "命宮" and ming["ganzhi"] == "癸亥"
    assert [s["name"] for s in ming["major_stars"]] == ["武曲", "破軍"]
    assert d["horoscope"]["yearly"]["ganzhi"] == "丙午"
    assert "简" not in str(d) and "宫" not in str(d)  # 已轉繁體


def test_ziwei_requires_time():
    r = client.post("/api/chart/ziwei", json={**ME, "birth_time": None})
    assert r.status_code == 422 and "時辰" in r.json()["error"]


def test_bazi_pillars_and_lunar_fix():
    d = client.post("/api/chart/bazi", json=ME).json()
    assert [p["gan"] + p["zhi"] for p in d["pillars"]] == ["戊寅", "庚申", "戊戌", "庚申"]
    assert d["day_master"] == "戊"
    assert d["lunar"] == "戊寅年六月廿八"  # 腳本原本會誤印閏六月
    assert any(s["name"] == "驛馬" for s in d["shensha"])
    assert [r["ganzhi"] for r in d["dayun"]][1:4] == ["辛酉", "壬戌", "癸亥"]


def test_bazi_unknown_hour():
    d = client.post("/api/chart/bazi", json={**ME, "birth_time": None}).json()
    assert d["hour_unknown"] is True


def test_bazi_lunar_input():
    d = client.post("/api/chart/bazi", json={**ME, "calendar": "lunar", "birth_date": "1998-06-28"}).json()
    assert [p["gan"] + p["zhi"] for p in d["pillars"]] == ["戊寅", "庚申", "戊戌", "庚申"]


def test_dst_warning():
    d = client.post("/api/chart/bazi", json={**ME, "birth_date": "1975-07-01"}).json()
    assert any("日光節約" in w for w in d["warnings"])


def test_qimen_matches_previous_reading():
    d = client.post("/api/chart/qimen", json={"question": "該不該離職", "question_type": "事業",
                                              "at": "2026-11-21T13:36:00", "city": "新北"}).json()
    c = d["chart"]
    assert c["dun_type"] == "陰遁" and c["ju_number"] == 9
    assert len(c["palaces"]) == 9


def test_qimen_needs_question():
    assert client.post("/api/chart/qimen", json={"question": " "}).status_code == 422


def test_tarot_reproducible_and_validated():
    body = {"question": "感情", "spread": "three", "picks": [3, 50, 77]}
    a = client.post("/api/chart/tarot", json=body).json()
    b = client.post("/api/chart/tarot", json=body).json()
    assert [c["card"] for c in a["cards"]] == [c["card"] for c in b["cards"]]
    assert len(a["cards"]) == 3 and a["spread_name"] == "三牌陣"
    bad = client.post("/api/chart/tarot", json={**body, "picks": [1, 1, 2]})
    assert bad.status_code == 422
    spreads = client.get("/api/tarot/spreads").json()
    assert {s["key"] for s in spreads} >= {"single", "three", "celtic"}


def test_yinyuan_couple_and_single():
    partner = {"birth_date": "1999-03-10", "birth_time": None, "gender": "女"}
    d = client.post("/api/chart/yinyuan", json={"a": ME, "b": partner}).json()
    assert d["mode"] == "couple" and d["a"]["zodiac"] == "虎" and d["b"]["zodiac"] == "兔"
    assert "ziwei" in d["a"] and "ziwei" not in d["b"]
    assert all(r["position"] != "時柱" for r in d["relations"])
    s = client.post("/api/chart/yinyuan", json={"a": ME}).json()
    assert s["mode"] == "single"


def test_bazi_lunar_leap_month():
    # 1998 年閏五月：閏五月初一 = 國曆 1998-06-24
    d = client.post("/api/chart/bazi", json={**ME, "calendar": "lunar", "birth_date": "1998-05-01",
                                             "is_leap_month": True}).json()
    assert d["solar"].startswith("1998-06-24")
    bad = client.post("/api/chart/bazi", json={**ME, "calendar": "lunar", "birth_date": "1998-06-01",
                                               "is_leap_month": True})
    assert bad.status_code == 422
