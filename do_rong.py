"""do_rong.py — độ rộng thị trường (tỉ lệ mã trên MA50 của chính nó) cho ĐO 32 (BƯỚC 224).

ĐỊNH NGHĨA ĐÃ GHIM TRƯỚC — `docs/TIEU-CHI-DOC-TRUOC.md`, mục "ĐO 32". Đổi một
hằng số ở đây là đổi phép đo sau khi đã ký (bất biến 7); đọc mục ấy trước.

    MA50      trung bình 50 giá đóng cửa liên tiếp của CHÍNH mã, tới hết dòng ấy
              (cùng cách `market_filter.get_vni_df` tính `vni_ma50`)
    N(t)      số mã của cache (trừ VNINDEX) có ≥ 50 dòng với ngày ≤ t
    "trên"    giá đóng cửa ≥ MA50 ở dòng cuối có ngày ≤ t (phép so `>=` của cổng VN-INDEX)
    độ rộng   số mã "trên" / N(t); N(t) < 20 thì THIẾU

VÌ SAO PHẢI LOẠI MÃ CHƯA ĐỦ 50 DÒNG KHỎI N — trong pandas `gia >= NaN` là False,
nên một bản ngây thơ đếm mã mới niêm yết (MA còn NaN) là "dưới MA" và kéo độ rộng
xuống: 37 mã của cache chỉ có giá từ 2025, đúng vùng IS.

Bảng tính trên cache ĐẦY ĐỦ (không chia vùng theo mốc sạch) nhưng chỉ dùng giá tới
hết t — như cổng VN-INDEX; lệnh vẫn khớp ở giá mở cửa phiên sau.

Đường giao dịch KHÔNG nhập module này trừ khi `paper_trading.DO_RONG_NGUONG` > 0.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

MA_PHIEN = 50
N_TOI_THIEU = 20
MA_CHI_SO = "VNINDEX"


def gia_dong_cua(duong: Path) -> pd.Series:
    """Cột `close` của một tệp cache, chỉ mục là ngày."""
    d = pd.read_csv(duong, usecols=["time", "close"]).dropna()
    d["time"] = pd.to_datetime(d["time"].astype(str).str[:10])
    return d.drop_duplicates("time").sort_values("time").set_index("time")["close"]


def co_tren_ma(gia: pd.Series) -> pd.Series:
    """Theo từng dòng của chính mã: 1.0 nếu đóng cửa ≥ MA50, 0.0 nếu dưới, NaN khi MA chưa đủ."""
    ma = gia.rolling(MA_PHIEN).mean()
    return (gia >= ma).astype(float).where(ma.notna())


def do_rong(bang_co: dict[str, pd.Series], t: pd.Timestamp) -> float | None:
    """Độ rộng tại `t` trên các chuỗi cờ của `co_tren_ma`; None nếu N(t) < `N_TOI_THIEU`."""
    tren = n = 0
    for co in bang_co.values():
        i = co.index.searchsorted(t, side="right") - 1      # dòng cuối có ngày ≤ t
        if i < 0 or pd.isna(co.iloc[i]):
            continue
        n += 1
        tren += int(co.iloc[i])
    return tren / n if n >= N_TOI_THIEU else None


class BangDoRong:
    """Cờ "trên MA50" của mọi mã trong MỘT thư mục cache, nạp một lần; độ rộng nhớ theo ngày."""

    def __init__(self, thu_muc: Path):
        thu_muc = Path(thu_muc)
        self.bang_co = {f.stem: co_tren_ma(gia_dong_cua(f)) for f in sorted(thu_muc.glob("*.csv"))
                        if f.stem != MA_CHI_SO}
        self._theo_ngay: dict[str, float | None] = {}

    def do_rong(self, ngay: str) -> float | None:
        """Độ rộng tại `ngay` (YYYY-MM-DD); None nếu N < ngưỡng."""
        ngay = str(ngay)[:10]
        if ngay not in self._theo_ngay:
            self._theo_ngay[ngay] = do_rong(self.bang_co, pd.Timestamp(ngay))
        return self._theo_ngay[ngay]


@lru_cache(maxsize=4)
def bang_cho(thu_muc: str) -> BangDoRong:
    """Một `BangDoRong` cho mỗi thư mục cache (nạp lần đầu, dùng lại suốt lượt chạy)."""
    return BangDoRong(Path(thu_muc))


def do_rong_mac_dinh(ngay: str) -> float | None:
    """Độ rộng trên thư mục cache mà backtest đang dùng (`backtest.data.CACHE_DIR`)."""
    from backtest.data import CACHE_DIR
    return bang_cho(str(CACHE_DIR)).do_rong(ngay)
