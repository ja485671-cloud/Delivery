# 命理館 —— 規格書

> 這份文件是專案的「唯一依據」。之後每次改動都先改這裡，再改程式。
> 最後更新：2026-11-28

## 1. 產品概念

使用者用第一人稱「走進命理館」，挑一位老師，用對話的方式被算命：

```
進站 →【動畫】走進命理館
     → 大廳：五位老師，各有一句介紹與標籤
     → 點選老師 →【動畫】走進老師的房間
     → 老師開場白（有聲音、有口型）
     → 對話式收資料（名字、生辰……）
     → 老師確認問題（最多 3 題）
     →【動畫】排盤（等待 AI 時老師在沉思）
     → 老師逐句講解，講到哪裡、盤面哪裡就亮
     → 完整文字報告
     → 追問（之後再決定是否收費）
```

| 老師 | 主題 | 需要的資料 | 設定檔 |
|---|---|---|---|
| 天璣老人 | 紫微斗數 | 姓名、性別、生日、時辰（必填） | `content/teachers/ziwei/persona.yaml` |
| 沈墨蘭先生 | 八字 | 姓名、性別、生日、時辰（可不知道）、出生地 | `content/teachers/bazi/persona.yaml` |
| 司南先生 | 奇門遁甲 | 姓名、問題、問題類別、所在城市（起局時間＝提問當下） | `content/teachers/qimen/persona.yaml` |
| 露娜 Luna | 塔羅 | 暱稱、問題、星座（選填）；使用者親手選牌 | `content/teachers/tarot/persona.yaml` |
| 紅線婆婆 | 姻緣合盤 | 先分流「有對象／單身」；有對象就收兩人資料 | `content/teachers/yinyuan/persona.yaml` |

## 2. 已確定的決策

| 項目 | 決定 | 備註 |
|---|---|---|
| 裝置 | 手機、電腦都要 | 手機直式優先設計，電腦版置中加寬 |
| 口型 | 方案 A：2D 立繪 + 嘴型切換，加程式做的呼吸、眨眼、微晃 | 角色層設計成可替換，之後可升級 Live2D |
| 聲音 | 要有。先用 edge-tts（免費），之後可換 Azure 語音（有嘴型時間點） | 嘴型：edge-tts 用音量驅動；Azure 用 viseme |
| AI | 先用 OpenAI API；程式可切換供應商（`AI_PROVIDER`） | 開發期用 `mock` 假資料模式，不花錢 |
| 執行環境 | 先在自己電腦跑 | 之後後端上 Railway 或 Google Cloud Run，前端上 Vercel／Cloudflare Pages |
| 維護方式 | 使用者只需改文字（YAML、Markdown）和換圖 | |
| 收費、會員、紀錄 | 之後再設計 | 架構先預留 |
| 美術風格 | 待定：先比較國風水墨、日系動漫、暗黑奇幻寫實 | 見 `docs/art-prompts.md` |

## 3. 系統架構與模組

```
┌──────────── 前端（瀏覽器）────────────┐      ┌──────── 後端（Python）────────┐
│ ① 場景動畫  ② 角色（立繪/嘴型/表情）    │      │ ⑤ 排盤引擎 ← .claude/skills 腳本 │
│ ③ 對話互動（流程狀態機）                │ ───▶ │ ⑥ AI 解讀  ← Claude API + 人設   │
│ ④ 盤面視覺（可點亮）  ⑦ 語音播放        │ ◀─── │ ⑦ 語音合成（TTS）                │
└───────────────────────────────────────┘      │ ⑧ 營運（金流/會員）—— 之後        │
                                               └──────────────────────────────┘
```

| # | 模組 | 位置 | 狀態 |
|---|---|---|---|
| ⑤ | 排盤引擎 API | `server/app/engines/` | ✅ 完成 |
| ⑥ | AI 解讀 | `server/app/reading/`、`content/teachers/*/prompt.md` | ✅ 完成（mock＋OpenAI；30 項測試通過） |
| ③ | 對話互動 | `web/src/dialogue/` | ⬜ 下一步 |
| ④ | 盤面視覺 | `web/src/charts/` | ⬜ 先做紫微 |
| ② | 角色系統 | `web/src/character/` | ⬜ 先用暫代圖 |
| ⑦ | 語音 | `server/app/tts/`、`web/src/voice/` | ⬜ |
| ① | 場景動畫 | `web/src/scenes/` | ⬜ 等美術定稿 |
| ⑧ | 營運 | — | ⬜ 之後 |

**開發順序**：先把「紫微」一位老師整條流程跑通（⑤→⑥→③→④→②→⑦→①），確認體驗後再複製到其他四位。

**前端技術**（預定）：Vite + React + TypeScript；動畫用 GSAP；盤面用 SVG（容易點亮與縮放）。

## 4. 核心設計：台詞腳本

AI 不直接輸出一大段文字，而是輸出「台詞腳本」。前端依序播放：老師說一句（語音＋口型），盤面亮對應的地方，同時換表情。

```json
{
  "lines": [
    { "say": "你的命宮坐的是武曲、破軍……", "highlight": ["palace:命宮", "star:武曲", "star:破軍"], "expression": "gaze" },
    { "say": "再看官祿宮，紫微貪狼同宮，而且化祿。", "highlight": ["palace:官祿", "sihua:化祿"], "expression": "smile" }
  ],
  "report_markdown": "## 一、命宮與性格\n……"
}
```

- `highlight` 的代號由各盤面元件定義，例如紫微：`palace:<宮名>`、`star:<星名>`、`sihua:<化祿/化權/化科/化忌>`；八字：`pillar:<year/month/day/hour>`、`dayun:<干支>`；奇門：`palace:<1-9>`、`door:<門名>`；塔羅：`card:<位置序號>`；姻緣：`relation:<序號>`。
- `expression` 只能用該老師 `persona.yaml` 裡 `expressions` 列出的值。
- 後端會檢查格式，不合法的 `highlight` 直接忽略，不讓前端出錯。

## 5. 排盤 API（模組 ⑤，已完成）

啟動方式見 `fortune-hall/README.md`。完整互動文件：啟動後打開 `http://127.0.0.1:8000/docs`。

| 方法 | 路徑 | 說明 |
|---|---|---|
| GET | `/api/health` | 健康檢查 |
| POST | `/api/chart/ziwei` | 紫微命盤（需要時辰），含流年 |
| POST | `/api/chart/bazi` | 八字四柱、大運、神煞（時辰可空） |
| POST | `/api/chart/qimen` | 奇門起局（時間留空＝現在） |
| GET | `/api/tarot/spreads` | 牌陣清單 |
| POST | `/api/chart/tarot` | 依使用者選的牌位抽牌（同輸入同結果） |
| POST | `/api/chart/yinyuan` | 兩人八字（有時辰加紫微）＋同柱合沖刑害；單身只看自己 |

規則：
- 排盤一律由 `.claude/skills/` 的腳本計算，後端只做轉接，不自己重寫排盤邏輯。
- 所有輸出轉成台灣繁體（OpenCC `s2tw`，再修正「天沖」「聖杯」等用語）。
- 輸入有問題時回 `422 {"error": "中文訊息"}`，前端讓老師把這句話「問」出來。
- 1945–1961、1974、1975、1979 年 4–10 月出生，會加上台灣日光節約時間的提醒。

| GET | `/api/teachers` | 大廳用：五位老師的名字、介紹、標籤、主題色 |
| GET | `/api/teachers/{id}` | 房間用：完整人設與台詞 |
| POST | `/api/reading/{id}/questions` | 排盤後的確認問題（最多 3 題，依盤面自動產生，不花 AI 費用） |
| POST | `/api/reading/{id}` | AI 解盤，回傳台詞腳本；帶 `followup` 就是追問 |

已知問題與處理：
- 八字腳本的農曆換算會把 1998 年閏五月當成閏六月，所以「農曆顯示」和「農曆輸入換算」都改用 lunar_python（紫微、奇門腳本本來就用它）。四柱本身不受影響。

## 6. AI 解讀（模組 ⑥）

送給 AI 的提示詞由四塊組成（`server/app/reading/prompt.py`）：

| 順序 | 內容 | 來源（要改就改這裡） |
|---|---|---|
| 1 | 共同規則：繁中台灣用語、不改盤、分寸、輸出格式 | `content/shared/reading-rules.md` |
| 2 | 老師人設摘要 | `content/teachers/<id>/persona.yaml` 的 `profile`、`reading.order` |
| 3 | 老師的口吻與解讀順序 | `content/teachers/<id>/prompt.md` |
| 4 | 命理知識（技能裡挑選的章節） | `persona.yaml` 的 `reading.knowledge` |

之後再接上這次的盤、客人資料、確認問題的回答、可點亮代號清單、表情清單。

- OpenAI 使用 Structured Outputs（strict JSON Schema），點亮代號和表情都用 enum 限制；回來後仍會再檢查一次。
- 提示詞固定部分約 3 千（塔羅）到 1.9 萬字（姻緣），再加上盤面資料。
- 確認問題用規則產生：紫微問「18 歲所在大限」那十年是否離家（驗證時辰）；八字問「上一步大運」那幾年順不順（判定喜用神）。
- 送給 AI 的資料包含客人的名字與生辰，上線前的個資說明要寫到這點。

## 7. 尚未決定／待確認

- [ ] 美術風格（三選一或混搭）
- [ ] 確認問題的最終內容（目前寫在各 `persona.yaml` 的 `confirm`）
- [ ] 追問的次數與收費
- [ ] **授權**：bazi、tarot 技能是 MIT 授權，可商用；ziwei-doushu、qimen-dunjia、yinyuan 目錄裡沒有授權檔，**正式收費前要確認來源與授權**。
- [ ] 免責聲明文字（「僅供參考、娛樂」）與個資說明（生辰屬個人資料）
