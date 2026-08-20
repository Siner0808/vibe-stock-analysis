"""
market_filter.py
──────────────────────────────────────────────────────────────────────
Bộ lọc xu hướng thị trường chung: VN-INDEX dưới MA50 thì không mở lệnh mới.

BẢN TRƯỚC HỎNG ÂM THẦM
Không có cache VNINDEX thì `get_vni_df()` gọi thẳng ra mạng; hỏng mạng thì
trả None, và `is_vni_bullish()` trả True cho mọi ngày. Tức là bộ lọc TẮT
hoàn toàn mà không ai biết — mọi báo cáo vẫn ghi "đã lọc theo xu hướng thị
trường" trong khi thực tế không lọc gì.

Ba thay đổi:
  • Tải được thì GHI RA CACHE, để lần sau không phụ thuộc mạng nữa.
  • `status()` cho biết bộ lọc đang bật hay tắt, để báo cáo nói đúng sự thật.
  • Không còn ngày kết thúc cứng trong code (bản trước ghi "2026-08-06",
    sẽ cũ dần rồi lọc sai mà không báo).

Vẫn giữ nguyên tắc hỏng-thì-cho-qua: bộ lọc này chỉ CHẶN lệnh, nên khi
không có dữ liệu, cho qua là lựa chọn ít gây hại hơn. Nhưng nó phải LỘ RA.
"""
from __future__ import annotations

import functools
from datetime import date

import pandas as pd

from backtest import data as _btd

MA_WINDOW = 50
#: Ô C1 — cache VN-INDEX trễ quá bao nhiêu phiên thì coi là KHÔNG CÓ dữ liệu.
#: Trễ trong ngưỡng là bình thường (cuối tuần, nghỉ lễ, chưa chạy phiên thu).
TRE_TOI_DA_PHIEN = 3


class CacheQuaHanError(RuntimeError):
    """Cache VN-INDEX quá cũ để phán quyết về ngày đang chấm.

    Ô C1 đã chọn: quá hạn thì DỪNG PHIÊN QUÉT, không âm thầm cho qua và
    cũng không âm thầm chặn hết.

    Vì sao không trả về False: bản cũ làm đúng thế, và kết quả là 14 ngày
    liền không mở được lệnh nào trong khi `status()` vẫn báo `active: True`.
    Chỗ nguy hiểm không phải *mất* dữ liệu — mất thì fail-open còn nhìn
    thấy được. Nguy hiểm là **dữ liệu cũ trông giống dữ liệu mới**.
    """


def _tre_phien(ngay_cuoi: str, moc: str) -> int:
    """Số phiên (ngày làm việc) từ sau `ngay_cuoi` tới hết `moc`."""
    ngay_cuoi, moc = str(ngay_cuoi)[:10], str(moc)[:10]
    if moc <= ngay_cuoi:
        return 0
    return len(pd.bdate_range(
        start=pd.Timestamp(ngay_cuoi) + pd.Timedelta(days=1),
        end=pd.Timestamp(moc)))


_STATUS = {"active": False, "note": "chưa nạp", "rows": 0}


@functools.lru_cache(maxsize=1)
def get_vni_df():
    """Nạp VN-INDEX kèm MA50. Tải từ mạng đúng một lần rồi ghi ra cache."""
    global _STATUS
    try:
        df = _btd.load("VNINDEX")
        source = "cache"

        if df is None or df.empty:
            df = _btd.fetch_one("VNINDEX", "2020-01-01", date.today().isoformat())
            source = "mạng"
            if df is not None and not df.empty:
                try:
                    _btd.CACHE_DIR.mkdir(parents=True, exist_ok=True)
                    df.to_csv(_btd.cache_path("VNINDEX"), index=False)
                    source = "mạng (đã ghi cache)"
                except Exception:
                    pass

        if df is None or df.empty:
            _STATUS = {"active": False, "rows": 0,
                       "note": "KHÔNG có dữ liệu VN-INDEX — bộ lọc TẮT, "
                               "mọi lệnh đều qua được"}
            return None

        df = df.copy()
        df["time"] = df["time"].astype(str)
        df = df.sort_values("time").reset_index(drop=True)
        df["vni_ma50"] = df["close"].rolling(MA_WINDOW).mean()
        _STATUS = {"active": True, "rows": len(df),
                   "note": f"VN-INDEX {df['time'].iloc[0]} → {df['time'].iloc[-1]} "
                           f"({len(df)} phiên, nguồn: {source})"}
        return df
    except Exception as e:
        _STATUS = {"active": False, "rows": 0,
                   "note": f"lỗi nạp VN-INDEX ({type(e).__name__}) — bộ lọc TẮT"}
        return None


def status(hom_nay: str | None = None) -> dict:
    """Bộ lọc có thật sự đang hoạt động không.

    Báo cáo nào nói "đã lọc theo xu hướng thị trường" đều phải gọi hàm này
    trước, nếu không nó đang khẳng định một điều có thể không đúng.

    Bản cũ chỉ trả lời "df có nạp được không" — nên nó báo `active: True`
    suốt 14 ngày trong khi cổng đóng cứng cho mọi ngày tương lai. Nay nó
    trả về cả TUỔI của dữ liệu, và `active` là False khi dữ liệu quá hạn.
    Một cổng dùng dữ liệu 13 ngày trước không phải cổng đang hoạt động.
    """
    df = get_vni_df()
    st = dict(_STATUS)
    if df is None or len(df) == 0:
        return st

    moc = str(hom_nay or date.today().isoformat())[:10]
    cuoi = str(df["time"].iloc[-1])[:10]
    tre = _tre_phien(cuoi, moc)
    st["ngay_cuoi"] = cuoi
    st["tuoi_phien"] = tre
    if tre > TRE_TOI_DA_PHIEN:
        st["active"] = False
        st["note"] = (f"VN-INDEX QUÁ HẠN: dữ liệu tới {cuoi}, trễ {tre} phiên "
                      f"so với {moc} (ngưỡng {TRE_TOI_DA_PHIEN}). Bộ lọc KHÔNG "
                      f"dùng được — xem ô C1 trong docs/STATE.md.")
    return st


def is_vni_bullish(signal_date: str) -> bool:
    """VN-INDEX tại `signal_date` có nằm trên MA50 không.

    Chỉ dùng dữ liệu tới hết `signal_date` — không nhìn trộm phiên sau.
    """
    vni_df = get_vni_df()
    if vni_df is None or vni_df.empty:
        # MẤT dữ liệu -> cho qua. Bộ lọc này chỉ CHẶN, nên khi không có dữ
        # liệu, cho qua là lựa chọn ít gây hại hơn — và `status()` nói ra.
        # Khác hẳn với dữ liệu CŨ, xử lý ngay bên dưới.
        return True

    # Độ cũ đo so với NGÀY ĐANG CHẤM, không so với hôm nay: cache chạy tới
    # 2026 mà chấm phiên 2024 thì không hề quá hạn. Đo sai chiều là mọi
    # backtest nổ oan.
    cuoi = str(vni_df["time"].iloc[-1])[:10]
    tre = _tre_phien(cuoi, signal_date)
    if tre > TRE_TOI_DA_PHIEN:
        raise CacheQuaHanError(
            f"VN-INDEX chỉ có dữ liệu tới {cuoi}, trễ {tre} phiên so với "
            f"{str(signal_date)[:10]} (ngưỡng {TRE_TOI_DA_PHIEN}). Không đủ "
            f"căn cứ để phán quyết về ngày này. Ô C1: dừng phiên quét. "
            f"Cập nhật bằng `extend_history.py`, KHÔNG phải `download()` — "
            f"download() bỏ qua mọi mã đã có cache.")

    sub = vni_df[vni_df["time"] <= signal_date]
    if sub.empty:
        return True

    latest = sub.iloc[-1]
    if pd.notna(latest.get("vni_ma50")):
        return float(latest["close"]) >= float(latest["vni_ma50"])
    return True
