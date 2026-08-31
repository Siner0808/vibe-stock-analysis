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


def _tre_phien(ngay_cuoi: str, moc: str, lich=None) -> int:
    """Số PHIÊN từ sau `ngay_cuoi` tới hết `moc`.

    ĐẾM BẰNG GÌ — VÀ VÌ SAO CÂU ĐÓ QUAN TRỌNG
    ──────────────────────────────────────────
    Bản trước đếm bằng `pd.bdate_range`, tức ngày làm việc T2–T6. Ngày làm
    việc KHÁC phiên giao dịch: thị trường Việt Nam nghỉ lễ. Đo ngày
    31/08/2026, với nến cuối là thứ Sáu 28/08 và kỳ nghỉ Quốc khánh 31/08
    → 02/09:

        31/08 → 1     01/09 → 2     02/09 → 3     03/09 → **4**

    Sáng thứ Năm 03/09 — phiên đầu tiên mở lại — bộ đếm cũ báo trễ 4 phiên
    trong khi dữ liệu chỉ cũ MỘT phiên theo lịch thị trường. Tết còn nặng
    hơn: cùng phép đo cho 8–9. Một ngưỡng đúng đơn vị không cứu được một
    phép đo sai đơn vị.

    LỊCH LẤY TỪ ĐÂU
    ───────────────
    Không có API lịch giao dịch trong `vnstock`. Nhưng chuỗi giá CHÍNH LÀ
    bản ghi phiên: thị trường có phiên thì có nến. `lich` là tập ngày phiên
    quan sát được — `run_daily` nạp nó từ rổ đang quét bằng
    `ghi_nhan_lich_phien()`.

    CÁI BẪY, VÀ CHỐT CHẶN CHO NÓ
    ────────────────────────────
    Nếu chính `lich` cũng cũ hơn `moc` thì phép đếm ra 0 và ô C1 tắt lặng
    lẽ — đúng thứ nó sinh ra để bắt. Nên lịch chỉ được dùng khi nó PHỦ TỚI
    `moc`; không phủ thì lùi về đếm ngày làm việc, và `status()` nói rõ đó
    là ước tính.
    """
    ngay_cuoi, moc = str(ngay_cuoi)[:10], str(moc)[:10]
    if moc <= ngay_cuoi:
        return 0
    lich = _LICH_PHIEN if lich is None else tuple(
        sorted({str(d)[:10] for d in lich}))
    if lich and max(lich) >= moc:
        return sum(1 for d in lich if ngay_cuoi < d <= moc)
    return len(pd.bdate_range(
        start=pd.Timestamp(ngay_cuoi) + pd.Timedelta(days=1),
        end=pd.Timestamp(moc)))


def _lich_phu_toi(moc: str, lich=None) -> bool:
    """Lịch phiên có phủ tới `moc` không — tức phép đếm có CHẮC không."""
    lich = _LICH_PHIEN if lich is None else lich
    return bool(lich) and max(str(d)[:10] for d in lich) >= str(moc)[:10]


#: Lịch phiên THẬT quan sát được trong lượt chạy này, nạp từ rổ đang quét.
#: Rỗng thì `_tre_phien` lùi về đếm ngày làm việc — hành vi của bản trước.
_LICH_PHIEN: tuple[str, ...] = ()


def ghi_nhan_lich_phien(ngay) -> int:
    """Nạp lịch phiên thật. Trả số ngày đã nạp.

    Gọi MỘT lần đầu lượt quét, từ chuỗi giá vừa tải. Không đọc file, không
    gọi mạng, và không tích luỹ qua lượt — nạp lại là ghi đè, nên cùng một
    gói dữ liệu vẫn cho cùng một kết quả (bất biến 2).
    """
    global _LICH_PHIEN
    _LICH_PHIEN = tuple(sorted({str(d)[:10] for d in ngay}))
    return len(_LICH_PHIEN)


def quen_lich_phien() -> None:
    """Xoá lịch — cho test, và cho bất kỳ ai muốn về hành vi lùi."""
    global _LICH_PHIEN
    _LICH_PHIEN = ()


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


def status(hom_nay: str | None = None, lich=None) -> dict:
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
    tre = _tre_phien(cuoi, moc, lich)
    st["ngay_cuoi"] = cuoi
    st["tuoi_phien"] = tre
    # Đếm chắc (có lịch phiên phủ tới mốc) khác hẳn đếm ước tính (ngày làm
    # việc). Không nói ra thì một con số nghỉ lễ trông y hệt một con số
    # cache chết.
    st["uoc_tinh"] = not _lich_phu_toi(moc, lich)
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


# ── VN-INDEX cho THANH TIÊU ĐỀ (khác đường dùng của bộ lọc) ──────────
#
# Ô "VN-Index" trên topbar viết cứng dấu gạch "—" từ đầu: nó không đọc gì,
# nên không bao giờ có số. Nay nó đọc thật.
#
# VÌ SAO KHÔNG DÙNG LẠI `get_vni_df()`
# Hàm đó phục vụ bộ lọc: nó ưu tiên cache trên đĩa và chỉ ra mạng khi cache
# RỖNG — cache cũ vẫn được coi là dùng được. Đúng cho backtest (phải tất
# định), sai cho thanh tiêu đề (phải là phiên gần nhất). Đo 22/08/2026:
# cache dừng ở 20/08 với 1.734,24 trong khi phiên 21/08 đóng 1.768,12 —
# lệch 1,96%. Một con số cũ trông y hệt một con số mới.
#
# Nên đường này ưu tiên MẠNG, chỉ lùi về cache khi mạng hỏng, và LUÔN trả
# về ngày của phiên để giao diện hiện ngày cạnh con số. Số không kèm ngày
# là số không kiểm được.
SO_PHIEN_TOPBAR = 12


def chi_so_moi_nhat(so_phien: int = SO_PHIEN_TOPBAR) -> dict:
    """Phiên VN-INDEX gần nhất: {dong_cua, thay_doi, phan_tram, ngay, nguon, loi}.

    Luôn trả dict, không bao giờ ném. Không lấy được thì mọi con số là None
    và `loi` nói vì sao.
    """
    trong = {"dong_cua": None, "thay_doi": None, "phan_tram": None,
             "ngay": None, "nguon": None, "loi": None}
    df, nguon, loi = None, None, None

    try:
        from datetime import timedelta
        hom_nay = date.today()
        # Xin dư ngày lịch để chắc chắn có ít nhất hai phiên kể cả khi rơi
        # vào kỳ nghỉ dài.
        df = _btd.fetch_one("VNINDEX",
                            (hom_nay - timedelta(days=so_phien * 3)).isoformat(),
                            hom_nay.isoformat())
        if df is not None and not df.empty:
            nguon = "mạng"
    except Exception as e:
        loi = f"mạng: {type(e).__name__}"
        df = None

    if df is None or df.empty:
        try:
            df = _btd.load("VNINDEX")
            if df is not None and not df.empty:
                nguon = "cache trên đĩa"
        except Exception as e:
            loi = f"{loi or ''} cache: {type(e).__name__}".strip()
            df = None

    if df is None or df.empty:
        return {**trong, "loi": loi or "không lấy được VN-INDEX"}

    try:
        d = df.copy()
        d["time"] = d["time"].astype(str)
        d = d.sort_values("time").reset_index(drop=True)
        if len(d) < 2:
            return {**trong, "nguon": nguon,
                    "loi": "chỉ có một phiên, không tính được thay đổi"}
        dong = float(d["close"].iloc[-1])
        truoc = float(d["close"].iloc[-2])
        return {"dong_cua": dong,
                "thay_doi": dong - truoc,
                "phan_tram": (dong - truoc) / truoc * 100.0 if truoc else None,
                "ngay": str(d["time"].iloc[-1])[:10],
                "nguon": nguon,
                "loi": None}
    except Exception as e:
        return {**trong, "nguon": nguon,
                "loi": f"{type(e).__name__}: {str(e)[:80]}"}
