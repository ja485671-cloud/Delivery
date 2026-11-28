# 圖片生成任務（給本機 Claude Code）

> 把下面「任務內容」整段貼給本機 Claude Code。它會幫你安裝、操作圖片生成工具（Claude 本身不會畫圖）。
> 決策紀錄：改用「固定影片」做法，每位老師只要 1 張「老師在房間裡」的圖，再用 AI 影片工具做成對口型的影片。

## 任務內容

請幫我用 AI 生成 7 張寫實風格的圖片，給我的命理網站使用。你自己不會畫圖，請幫我安裝並操作圖片生成工具。

### 第一步：檢查環境，建議方案
1. 檢查我的電腦：作業系統、有沒有 NVIDIA 顯示卡（顯示記憶體多大）、是不是 Apple M 系列晶片、記憶體大小。
2. 檢查環境變數裡有沒有圖片 API 金鑰（例如 REPLICATE_API_TOKEN、FAL_KEY、GEMINI_API_KEY），只確認有沒有，不要印出內容。
3. 依結果建議方案，等我同意再開始：
   - 方案 A：呼叫雲端圖片 API（優先考慮 Flux 系列，或 Google Imagen），寫一個 Python 腳本批次生成。
   - 方案 B：電腦夠力就在本機跑 Flux 或 SDXL（diffusers 或 ComfyUI）。
   請先查官方文件確認目前的模型名稱和用法，不要憑記憶，並告訴我大概要花多少錢或多少時間。
4. 需要 API 金鑰時，告訴我去哪裡申請、怎麼設定成環境變數。不要叫我把金鑰貼在對話裡，也不要把金鑰寫進任何會進 git 的檔案。

### 第二步：生成圖片
- 每張提示詞先生成 4 張候選圖（用不同的 seed），記下每張的 seed，方便之後重畫或微調。
- 比例：老師的 5 張用直式 2:3（例如 1024×1536）；入口用直式 2:3；大廳用橫式 3:2。
- 下面的提示詞是英文的，直接使用。模型支援負面提示詞的話，就加上「通用負面提示詞」。
- 存檔位置（在 repo 的 fortune-hall 資料夾裡）：
  - 候選圖：fortune-hall/art/candidates/<代號>/<代號>_seed<數字>.png
  - 生成腳本：fortune-hall/art/generate.py（提示詞也寫在腳本裡，之後可以重跑）
- 全部生成完，做一張預覽總表 fortune-hall/art/candidates/contact_sheet.png（每列一個代號、4 張候選並排、標上檔名），讓我一次挑選。

### 第三步：我選完之後
把我選的圖複製到 fortune-hall/content/teachers/<代號>/images/scene.png（入口、大廳放到 fortune-hall/content/scenes/entrance.png、lobby.png）。

### 這些圖之後的用途（請在構圖上配合）
老師的圖會拿去用 AI 影片工具做成「老師說話、對口型」的影片，所以：
- 老師要正面、看著鏡頭，臉清楚，頭和肩膀位在畫面中上方，臉部要夠大。
- 嘴巴一定要完整露出：鬍子不能遮住嘴唇，手和道具不能擋住臉。
- 嘴巴自然閉合、表情溫和，不要露齒大笑。
- 老師坐在桌子後面，上半身入鏡，房間的佈景要看得到，但不要搶走人物的焦點。

### 通用風格（加在每一張老師提示詞後面）
cinematic photorealistic film still, shot on 50mm lens, soft warm key light with gentle rim light, shallow depth of field, natural skin texture, rich fabric detail, authentic costume, looking directly at the camera, face fully visible, lips clearly visible and not covered by beard or hands, mouth gently closed, centered composition, upper body visible, sitting behind a table, vertical 2:3, no text, no watermark, no logo

### 通用負面提示詞
cosplay, costume party, plastic skin, waxy, cartoon, anime, 3d render, deformed hands, extra fingers, beard covering mouth, hand covering face, open mouth, teeth showing, text, watermark, logo, blurry face, cropped head

### 提示詞

#### ziwei（天璣老人，紫微斗數）——和藹可親的長輩
A kindly elderly East Asian man around 70 years old, a master of Zi Wei Dou Shu astrology, sitting behind a low dark wooden table inside an octagonal observatory loft at night. Round, full face with rosy cheeks and smile lines, warm bright wise eyes, a gentle closed-mouth smile, the kind of grandfather who makes you feel safe. White hair tied in a neat topknot with a simple wooden hairpin. Neatly trimmed white beard down to the chest, with a short sparse moustache so his lips are fully visible. Deep purple wide-sleeved Taoist robe embroidered with pale gold constellations and the Big Dipper, a string of wooden prayer beads on his wrist, hands resting calmly on the table. Behind him: a large round skylight showing a deep starry night sky, a bronze armillary sphere, faded antique star charts on the walls, thin wisps of incense smoke, warm candlelight.

#### bazi（沈墨蘭先生，八字）
An elegant, scholarly East Asian woman around 45 years old, a master of Bazi (Four Pillars) destiny reading, sitting behind a large sandalwood writing desk in a traditional study. Hair in a neat low bun held by a wooden hairpin, thin round wire-framed glasses, calm intelligent eyes, a gentle composed smile with lips closed. Dark green modern qipao with a sheer long outer robe. On the desk: a calligraphy brush resting on a brush stand, an inkstone, a sheet of rice paper, and a cup of tea. Behind her: floor-to-ceiling shelves of thread-bound ancient Chinese books, a lattice window showing bamboo in soft rain, soft diffused daylight.

#### qimen（司南先生，奇門遁甲）
A handsome East Asian man around 32 years old, a brilliant military strategist and master of Qimen Dunjia, sitting behind a heavy wooden table in a dim war room. Sharp, intelligent eyes, a confident slight smile with lips closed, clean-shaven. Long black hair tied up in a topknot. Black robe with gold-trimmed collar and sleeves, holding a white feather fan loosely at chest height (not covering his face), an antique bronze compass hanging at his belt. On the table in front of him: a large carved stone board divided into a three-by-three grid. Behind him: old maps on the walls, rolled bamboo scrolls of military texts, flickering candlelight and warm shadows.

#### tarot（露娜 Luna，塔羅）
A mysterious, gentle young woman around 28 years old with East Asian features, a tarot reader, sitting behind a round table in a bohemian fortune-teller's tent. Long wavy black hair, deep purple eye makeup, star and crescent moon earrings, layered delicate necklaces, dark red nails, a soft knowing smile with lips closed. Deep blue velvet hooded cloak with the hood down so her face is fully visible. On the table: purple velvet cloth, a glowing crystal ball, and a tarot deck face-down. Around her: hanging dried flowers, dreamcatchers, many lit candles, light incense haze, warm and dreamy atmosphere.

#### yinyuan（紅線婆婆，姻緣合盤）
A cheerful, warm-hearted East Asian grandmother around 65 years old, a matchmaker who reads love destinies, sitting at a round stone table in a temple courtyard at night. Round smiling face, rosy cheeks, happy squinting eyes with deep laugh lines, a big warm closed-mouth smile. Gray-black hair in a bun decorated with a red flower. Red traditional Tang-style jacket, a loop of red string wound around her wrist, a small fluffy white rabbit sitting on the table beside two cups of hot tea. Behind her: many glowing red lanterns, a large old banyan tree hung with countless red threads and small wooden wish plaques, soft moonlight.

#### entrance（命理館入口）——直式 2:3
A narrow old street in Taiwan at night, a mysterious traditional fortune-telling house with dark wooden doors left slightly ajar, warm golden light spilling from inside, red paper lanterns hanging by the door, a blank wooden signboard with no characters, stone steps, light mist on the ground, cinematic photorealistic, inviting yet mysterious, no people, no text, no watermark.

#### lobby（命理館大廳）——橫式 3:2
The interior hall of a grand traditional Chinese fortune-telling house, high wooden ceiling, thin incense smoke, warm lantern light. Along the back wall are five distinct doorways, each with its own atmosphere glowing from within: a deep purple doorway with starry light (astrology), a dark green doorway with scrolls and books (Bazi), a black-and-gold doorway with a bronze compass motif (strategy), a deep blue doorway with a crescent moon glow (tarot), and a red doorway with lanterns and red threads (love). Polished wooden floor, the center of the hall left open, cinematic photorealistic, no people, no text, no watermark.
