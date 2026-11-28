# 命理館

互動式 AI 算命網站：走進命理館、挑一位老師、用對話被算命。

- 規格書：[`docs/SPEC.md`](docs/SPEC.md)
- 出圖提示詞：[`docs/art-prompts.md`](docs/art-prompts.md)
- 老師設定（改台詞就改這裡）：`content/teachers/<老師>/persona.yaml`
- 老師圖片（換圖就換這裡）：`content/teachers/<老師>/images/`

## 目錄

```
fortune-hall/
├─ docs/              規格書、出圖提示詞
├─ content/teachers/  五位老師的人設、台詞、圖片
└─ server/            後端（Python）：排盤 API，之後加 AI 解讀與語音
```

排盤計算使用 repo 根目錄 `.claude/skills/` 裡的技能腳本。

## 在自己電腦啟動後端

需要 Python 3.10 以上。

```bash
cd fortune-hall/server
python3 -m venv .venv
source .venv/bin/activate          # Windows：.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

打開 http://127.0.0.1:8000/docs ，可以直接在網頁上試每個排盤 API。

執行測試：

```bash
python -m pytest -q tests
```
