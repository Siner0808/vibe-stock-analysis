"""
intraday_data.py
──────────────────────────────────────────────────────────────────────
Nến nội phiên — tầng dữ liệu cho bot phản ứng theo giá trong phiên.

VÌ SAO CẦN MỘT TẦNG RIÊNG, KHÔNG GỌI THẲNG vnstock
──────────────────────────────────────────────────
Nguồn trả về một LƯỚI 24/7, không phải chuỗi phiên giao dịch. Đo trên ACB,
khung 30 phút, một năm (13/08/2026):

    nến thô     17.521      = 48 khung × 365 ngày, đủ cả thứ Bảy Chủ Nhật
    nến thật     2.242      = 9 nến × 250 phiên
    rác          87,2%      OHLC là NaN, volume = 0

Đưa thẳng 17.521 dòng đó vào một chỉ báo là hỏng: trung bình động sẽ tính
cả những khung 03:00 sáng Chủ Nhật. Tệ hơn, nếu ai đó `ffill()` cho "sạch"
thì giá đêm và cuối tuần trở thành dữ liệu trông rất hợp lệ.

Cái bẫy thứ hai: giá về theo NGHÌN ĐỒNG (22.20), y hệt dữ liệu ngày. So
thẳng với stop_loss theo VNĐ thì `low <= stop_loss` luôn đúng — đúng lỗi
đã ghi trong NGUYEN-TAC-DO-LUONG.md.

Module này là ĐIỂM VÀO DUY NHẤT cho nến nội phiên. Nó lọc rác, quy đơn vị,
và NỔ khi dữ liệu bất thường thay vì trả về thứ trông có vẻ dùng được.

PHIÊN GIAO DỊCH HOSE
────────────────────
    Sáng   09:00 – 11:30
    Chiều  13:00 – 14:45
Khung 30 phút thực tế: 09:00 09:30 10:00 10:30 11:00 · 13:00 13:30 14:00 14:30

Xem NGUYEN-TAC-DO-LUONG.md.
"""
from __future__ import annotations

from datetime import time as _time
from pathlib import Path

import pandas as pd

from data_quality import price_multiplier

KHUNG_HOP_LE = ("1m", "5m", "15m", "30m", "1H")

# Giờ mở/đóng hai phiên HOSE. Nến nằm ngoài khoảng này là rác của lưới 24/7.
PHIEN = ((_time(9, 0), _time(11, 30)), (_time(13, 0), _time(14, 45)))

THU_MUC_CACHE = Path(__file__).parent / "intraday_cache"

# Số nến thật mỗi phiên, dùng để phát hiện dữ liệu thủng.
NEN_MOI_PHIEN = {"1m": 255, "5m": 51, "15m": 17, "30m": 9, "1H": 5}


class IntradayError(RuntimeError):
    """Dữ liệu nội phiên bất thường — luôn ném ra, không bao giờ trả bừa."""


def _trong_phien(ts: pd.Series) -> pd.Series:
    """True cho nến nằm trong giờ giao dịch, thứ 2–6."""
    gio = ts.dt.time
    trong_gio = False
    for mo, dong in PHIEN:
        trong_gio = trong_gio | ((gio >= mo) & (gio <= dong))
    return trong_gio & (ts.dt.dayofweek < 5)


def loc_rac(df: pd.DataFrame) -> pd.DataFrame:
    """Bỏ ô rỗng của lưới 24/7. Giữ nguyên thứ tự thời gian.

    Ba điều kiện, cố ý dư một chút: OHLC phải có giá trị, volume phải
    dương, và thời điểm phải nằm trong phiên. Chỉ lọc theo NaN là chưa đủ
    — nguồn có lúc trả 0 thay vì NaN cho khung ngoài giờ.
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])

    d = df.copy()
    d["time"] = pd.to_datetime(d["time"])
    co_gia = d[["open", "high", "low", "close"]].notna().all(axis=1)
    co_kl = pd.to_numeric(d["volume"], errors="coerce").fillna(0) > 0
    return d[co_gia & co_kl & _trong_phien(d["time"])].sort_values("time").reset_index(drop=True)


def _quy_ve_vnd(df: pd.DataFrame) -> pd.DataFrame:
    """Nhân giá về VNĐ bằng đúng bộ dò dùng cho dữ liệu ngày."""
    if df.empty:
        return df
    he_so = price_multiplier(df)
    if he_so == 1.0:
        return df
    d = df.copy()
    for c in ("open", "high", "low", "close"):
        d[c] = d[c] * he_so
    return d


def kiem_tra(df: pd.DataFrame, khung: str) -> dict:
    """Chẩn đoán chất lượng — gọi trước khi tin vào dữ liệu.

    Trả dict, KHÔNG ném. Nơi gọi tự quyết định dừng hay chạy tiếp, nhưng
    phải nhìn thấy con số trước đã.
    """
    if df.empty:
        return {"dat": False, "ghi_chu": "không có nến nào sau khi lọc"}

    ngay = df["time"].dt.date
    so_phien = ngay.nunique()
    tb = len(df) / so_phien
    mong_doi = NEN_MOI_PHIEN.get(khung, 0)
    thieu = [str(d) for d, n in df.groupby(ngay).size().items()
             if mong_doi and n < mong_doi * 0.5]

    return {
        "dat": bool(so_phien >= 20 and (not mong_doi or tb >= mong_doi * 0.5)),
        "so_nen": len(df),
        "so_phien": so_phien,
        "nen_moi_phien": round(tb, 1),
        "mong_doi_moi_phien": mong_doi,
        "phien_thung": thieu[:5],
        "tu": str(df["time"].min()),
        "den": str(df["time"].max()),
        "ghi_chu": ("OK" if so_phien >= 20 else
                    f"chỉ có {so_phien} phiên — quá ít để kết luận"),
    }


def tai(symbol: str, start: str, end: str, khung: str = "30m",
        dung_cache: bool = True) -> pd.DataFrame:
    """Nến nội phiên đã lọc rác và quy về VNĐ.

    Ném IntradayError nếu khung không hợp lệ hoặc nguồn không trả gì. KHÔNG
    tự lấp chỗ trống: thiếu là thiếu, không đoán.
    """
    if khung not in KHUNG_HOP_LE:
        raise IntradayError(
            f"Khung {khung!r} không hợp lệ. Chọn một trong {KHUNG_HOP_LE}.")

    duong = THU_MUC_CACHE / f"{symbol.upper()}_{khung}.csv"
    if dung_cache and duong.exists():
        d = pd.read_csv(duong)
        d["time"] = pd.to_datetime(d["time"])
        trong_khoang = (d["time"] >= pd.Timestamp(start)) & \
                       (d["time"] <= pd.Timestamp(end) + pd.Timedelta(days=1))
        if trong_khoang.any():
            return d[trong_khoang].reset_index(drop=True)

    try:
        from vnstock_auth import ensure_api_key
        ensure_api_key()
        from vnstock.api.quote import Quote
        tho = Quote(symbol=symbol.upper(), source="VCI").history(
            start=start, end=end, interval=khung)
    except Exception as e:
        raise IntradayError(f"{symbol}: {type(e).__name__}: {str(e)[:140]}") from e

    if tho is None or tho.empty:
        raise IntradayError(f"{symbol}: nguồn trả bảng rỗng cho khung {khung}")

    sach = _quy_ve_vnd(loc_rac(tho))
    if sach.empty:
        raise IntradayError(
            f"{symbol}: {len(tho)} dòng thô nhưng KHÔNG có nến giao dịch nào "
            f"sau khi lọc. Nguồn chỉ trả lưới rỗng.")

    if dung_cache:
        THU_MUC_CACHE.mkdir(parents=True, exist_ok=True)
        sach.to_csv(duong, index=False)
    return sach


def gop_theo_phien(df: pd.DataFrame) -> pd.DataFrame:
    """Gộp nến nội phiên thành nến NGÀY.

    Dùng để đối chiếu với dữ liệu ngày: hai nguồn cùng mô tả một phiên thì
    open/high/low/close phải khớp. Lệch nghĩa là một trong hai sai, và cần
    biết ngay chứ không phải sau khi đã dựng chiến lược lên đó.
    """
    if df.empty:
        return df
    g = df.groupby(df["time"].dt.date)
    return pd.DataFrame({
        "time": [str(d) for d in g.groups],
        "open": g["open"].first().values,
        "high": g["high"].max().values,
        "low": g["low"].min().values,
        "close": g["close"].last().values,
        "volume": g["volume"].sum().values,
    })
