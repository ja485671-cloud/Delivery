"""命理館後端 API。

目前只負責「排盤」（固定計算，不經過 AI）。AI 解讀、語音之後會是獨立模組。
啟動：uvicorn app.main:app --reload（在 fortune-hall/server 目錄下）
API 文件：啟動後打開 http://127.0.0.1:8000/docs
"""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")  # 金鑰等設定放 server/.env（不進 git）

from fastapi import FastAPI, HTTPException, Request  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from . import content  # noqa: E402
from .common import ChartError  # noqa: E402
from .engines import bazi, qimen, tarot, yinyuan, ziwei  # noqa: E402
from .reading import providers, questions, service  # noqa: E402

app = FastAPI(title="命理館 API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # 前端開發伺服器
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ChartError)
async def _chart_error(_: Request, exc: ChartError) -> JSONResponse:
    # 422 + 中文訊息：前端讓老師把這句話「問」出來
    return JSONResponse(status_code=422, content={"error": str(exc)})


@app.exception_handler(providers.ProviderError)
async def _provider_error(_: Request, exc: providers.ProviderError) -> JSONResponse:
    return JSONResponse(status_code=503, content={"error": str(exc)})


class Birth(BaseModel):
    name: str | None = Field(None, max_length=40, examples=["張三"])
    calendar: Literal["solar", "lunar"] = "solar"
    birth_date: date = Field(examples=["1990-05-15"])
    birth_time: str | None = Field(None, description="HH:MM；不知道時辰就留空", examples=["14:30"])
    is_leap_month: bool = False
    gender: Literal["男", "女"]
    place: str | None = Field(None, max_length=40, examples=["台北市"])

    @field_validator("birth_time")
    @classmethod
    def _check_time(cls, v: str | None) -> str | None:
        if v in (None, ""):
            return None
        try:
            datetime.strptime(v, "%H:%M")
        except ValueError as exc:
            raise ValueError("出生時間格式要是 HH:MM，例如 14:30") from exc
        return v

    def args(self) -> dict:
        return {"calendar": self.calendar, "birth_date": self.birth_date, "birth_time": self.birth_time,
                "gender": self.gender, "is_leap_month": self.is_leap_month}


class ZiweiReq(Birth):
    query_year: int | None = Field(None, description="要看流年的年份，預設今年")


class QimenReq(BaseModel):
    question: str = Field(max_length=200, examples=["該不該從現在的公司離職？"])
    question_type: str = Field("綜合", max_length=20, examples=["事業"])
    at: datetime | None = Field(None, description="起局時間；留空 = 現在")
    city: str = Field("台北", max_length=40)
    timezone: str = "Asia/Taipei"


class TarotReq(BaseModel):
    question: str = Field("", max_length=200)
    spread: str = Field("three", examples=["three"])
    picks: list[int] = Field(description="使用者在 78 張牌中選的位置（0–77）", examples=[[5, 40, 71]])


class YinyuanReq(BaseModel):
    a: Birth
    b: Birth | None = Field(None, description="對象；單身只看桃花就留空")


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "ai_provider": providers.current()}


# ---------- 老師 ----------

def _teacher_or_404(teacher: str) -> None:
    try:
        content.check_teacher(teacher)
    except KeyError:
        raise HTTPException(404, "沒有這位老師") from None


@app.get("/api/teachers")
def teachers() -> list:
    """大廳用：五位老師的名字、介紹、標籤、主題色。"""
    out = []
    for t in content.TEACHERS:
        p = content.persona(t)
        out.append({k: p.get(k) for k in ("id", "name", "subject", "hall_intro", "hall_tags", "theme_color")})
    return out


@app.get("/api/teachers/{teacher}")
def teacher_detail(teacher: str) -> dict:
    """房間用：完整人設與台詞（不含給 AI 的知識清單）。"""
    _teacher_or_404(teacher)
    p = content.persona(teacher)
    p.get("reading", {}).pop("knowledge", None)
    return p


@app.post("/api/chart/ziwei")
def chart_ziwei(req: ZiweiReq) -> dict:
    return ziwei.chart(**req.args(), query_year=req.query_year or date.today().year)


@app.post("/api/chart/bazi")
def chart_bazi(req: Birth) -> dict:
    return bazi.chart(**req.args(), place=req.place)


@app.post("/api/chart/qimen")
def chart_qimen(req: QimenReq) -> dict:
    return qimen.chart(question=req.question, question_type=req.question_type, at=req.at,
                       city=req.city, timezone=req.timezone)


@app.get("/api/tarot/spreads")
def tarot_spreads() -> list:
    return tarot.spreads()


@app.post("/api/chart/tarot")
def chart_tarot(req: TarotReq) -> dict:
    return tarot.draw(question=req.question, spread=req.spread, picks=req.picks)


@app.post("/api/chart/yinyuan")
def chart_yinyuan(req: YinyuanReq) -> dict:
    a = {**req.a.args(), "name": req.a.name, "place": req.a.place}
    b = {**req.b.args(), "name": req.b.name, "place": req.b.place} if req.b else None
    return yinyuan.chart(a=a, b=b)


# ---------- AI 解讀 ----------

class QuestionsReq(BaseModel):
    chart: dict[str, Any] = Field(description="排盤 API 的回傳結果，原封不動傳回來")
    name: str | None = Field(None, max_length=40)


class Answer(BaseModel):
    id: str = Field(max_length=40)
    question: str = Field(max_length=300)
    answer: str = Field(max_length=500)


class ReadingReq(BaseModel):
    chart: dict[str, Any] = Field(description="排盤 API 的回傳結果，原封不動傳回來")
    profile: dict[str, Any] = Field(default_factory=dict, description="姓名等基本資料")
    answers: list[Answer] = Field(default_factory=list, max_length=3)
    followup: str | None = Field(None, max_length=300, description="追問；留空 = 第一次解盤")


@app.post("/api/reading/{teacher}/questions")
def reading_questions(teacher: str, req: QuestionsReq) -> list:
    """排完盤後，老師要問的確認問題（最多 3 題）。"""
    _teacher_or_404(teacher)
    try:
        return questions.confirm_questions(teacher, req.chart, name=req.name)
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(422, f"盤面資料不完整：{exc}") from exc


@app.post("/api/reading/{teacher}")
def reading(teacher: str, req: ReadingReq) -> dict:
    """AI 解盤，回傳台詞腳本：{lines: [{say, highlight, expression}], report_markdown, source}。"""
    _teacher_or_404(teacher)
    try:
        return service.read(teacher, chart=req.chart, profile=req.profile,
                            answers=[a.model_dump() for a in req.answers], followup=req.followup)
    except (KeyError, TypeError) as exc:
        raise HTTPException(422, f"盤面資料不完整：{exc}") from exc
