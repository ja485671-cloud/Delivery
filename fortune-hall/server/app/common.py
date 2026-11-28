from __future__ import annotations

from datetime import date

# 台灣實施日光節約時間的年份（出生時間要減 1 小時才是標準時間）
# 資料來源：中央氣象署公告。實際起訖日每年不同，這裡只用月份粗略提醒，交給老師追問確認。
TAIWAN_DST_YEARS = {1945, 1946, 1947, 1948, 1949, 1950, 1951, 1952, 1953, 1954,
                    1955, 1956, 1957, 1958, 1959, 1960, 1961, 1974, 1975, 1979}


def dst_warning(d: date) -> str | None:
    if d.year in TAIWAN_DST_YEARS and 4 <= d.month <= 10:
        return (f"{d.year} 年台灣曾實施日光節約時間，若出生於實施期間，"
                "出生證明上的時間要減 1 小時才是標準時間，請向使用者確認。")
    return None


class ChartError(ValueError):
    """使用者輸入有問題，需要老師追問。訊息會直接顯示給使用者。"""
