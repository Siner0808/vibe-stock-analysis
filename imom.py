"""imom.py — momentum đặc thù (IMOM) 12 tháng, bản rút gọn, cho ĐO 31 (BƯỚC 223).

ĐỊNH NGHĨA ĐÃ GHIM TRƯỚC — `docs/TIEU-CHI-DOC-TRUOC.md`, mục "ĐO 31". Đổi một
hằng số ở đây là đổi phép đo sau khi đã ký (bất biến 7); đọc mục ấy trước.

    r_i, r_m   lợi nhuận ngày từ giá đóng cửa liên tiếp của mã và của VNINDEX
    W          các phiên có ngày trong [t − 12 tháng ; t − 1 tháng)
    β          hệ số góc OLS (có hệ số chặn) của r_i theo r_m trên W
    e          r_i − β·r_m        ← KHÔNG trừ hệ số chặn
    IMOM       trung bình(e) / độ lệch chuẩn(e, ddof=1); cần ≥ 200 phiên trong W

VÌ SAO KHÔNG TRỪ HỆ SỐ CHẶN — cửa sổ ước lượng trùng cửa sổ hình thành. Trừ nó
thì trung bình phần dư OLS bằng 0 theo cấu tạo và IMOM ≡ 0 với MỌI mã; bộ lọc
khi ấy chặn theo nhiễu làm tròn. Bài gốc (Hoàng Văn Hải và cộng sự, 2022) ước
lượng trên 36 tháng nên không gặp bẫy này; bản rút gọn thì gặp.

Phân vị tại ngày t: xếp hạng IMOM của mọi mã trong thư mục cache (trừ VNINDEX)
có IMOM, hạng trung bình khi bằng nhau, chia cho N; N < 20 thì không xếp. Bảng
tính trên cache ĐẦY ĐỦ nhưng chỉ dùng giá trước t − 1 tháng — không nhìn tương lai.

Đường giao dịch KHÔNG nhập module này trừ khi `paper_trading.LOC_IMOM_PHAN_VI` > 0.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

CUA_SO_THANG = 12
BO_THANG_GAN = 1
PHIEN_TOI_THIEU = 200
N_XEP_HANG_TOI_THIEU = 20
MA_CHI_SO = "VNINDEX"


def loi_nhuan_ngay(duong: Path) -> pd.Series:
    """Lợi nhuận ngày từ cột `close` của một tệp cache, chỉ mục là ngày."""
    d = pd.read_csv(duong, usecols=["time", "close"])
    d["time"] = pd.to_datetime(d["time"].astype(str).str[:10])
    d = d.drop_duplicates("time").sort_values("time").set_index("time")["close"]
    return d.pct_change().dropna()


def imom(r_ma: pd.Series, r_tt: pd.Series, t: pd.Timestamp) -> float:
    """IMOM của một mã tại ngày tín hiệu `t`; NaN nếu W có dưới `PHIEN_TOI_THIEU` phiên."""
    dau = t - pd.DateOffset(months=CUA_SO_THANG)
    cuoi = t - pd.DateOffset(months=BO_THANG_GAN)
    x = pd.concat([r_ma[(r_ma.index >= dau) & (r_ma.index < cuoi)], r_tt],
                  axis=1, join="inner").dropna()
    if len(x) < PHIEN_TOI_THIEU:
        return float("nan")
    ri, rm = x.iloc[:, 0].to_numpy(), x.iloc[:, 1].to_numpy()
    beta = np.cov(ri, rm, ddof=1)[0, 1] / np.var(rm, ddof=1)
    e = ri - beta * rm
    return float(e.mean() / e.std(ddof=1))


def phan_vi(bang_ln: dict[str, pd.Series], r_tt: pd.Series, t: pd.Timestamp) -> pd.Series | None:
    """Phân vị IMOM (hạng tăng / N) của mọi mã có IMOM tại `t`; None nếu N < ngưỡng."""
    v = pd.Series({ma: imom(r, r_tt, t) for ma, r in bang_ln.items()}).dropna()
    if len(v) < N_XEP_HANG_TOI_THIEU:
        return None
    return v.rank(method="average") / len(v)


class BangIMOM:
    """Lợi nhuận ngày của mọi mã trong MỘT thư mục cache, nạp một lần; phân vị nhớ theo ngày."""

    def __init__(self, thu_muc: Path):
        thu_muc = Path(thu_muc)
        self.r_tt = loi_nhuan_ngay(thu_muc / f"{MA_CHI_SO}.csv")
        self.bang_ln = {f.stem: loi_nhuan_ngay(f) for f in sorted(thu_muc.glob("*.csv"))
                        if f.stem != MA_CHI_SO}
        self._theo_ngay: dict[str, pd.Series | None] = {}

    def phan_vi(self, ma: str, ngay: str) -> float | None:
        """Phân vị của `ma` tại `ngay` (YYYY-MM-DD); None nếu thiếu IMOM hoặc không xếp được."""
        ngay = str(ngay)[:10]
        if ngay not in self._theo_ngay:
            self._theo_ngay[ngay] = phan_vi(self.bang_ln, self.r_tt, pd.Timestamp(ngay))
        pv = self._theo_ngay[ngay]
        if pv is None or ma not in pv.index:
            return None
        return float(pv[ma])


@lru_cache(maxsize=4)
def bang_cho(thu_muc: str) -> BangIMOM:
    """Một `BangIMOM` cho mỗi thư mục cache (nạp lần đầu, dùng lại suốt lượt chạy)."""
    return BangIMOM(Path(thu_muc))


def phan_vi_mac_dinh(ma: str, ngay: str) -> float | None:
    """Phân vị trên thư mục cache mà backtest đang dùng (`backtest.data.CACHE_DIR`)."""
    from backtest.data import CACHE_DIR
    return bang_cho(str(CACHE_DIR)).phan_vi(ma, ngay)
