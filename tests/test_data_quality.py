"""Test tầng kiểm định dữ liệu.

Mỗi luật kiểm định có hai ca: một ca dữ liệu HỎNG phải bị bắt, và ca dữ
liệu SẠCH không được báo nhầm. Thiếu ca thứ hai thì không biết luật có
quá nhạy hay không — và một tầng kiểm định báo động liên tục sẽ bị bỏ qua.

Chạy offline:  python3 tests/test_data_quality.py
"""
import os
import sys
from datetime import timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd

from data_quality import (Severity, detect_unit_multiplier, normalize_ohlcv,
                          now_vn, price_multiplier, today_vn, validate_ohlcv)


def clean_df(n: int = 120, start_price: float = 50_000.0,
             end_offset: int = 0) -> pd.DataFrame:
    """Bảng OHLCV hợp lệ, phiên gần nhất cách hôm nay `end_offset` ngày."""
    last = today_vn() - timedelta(days=end_offset)
    dates = pd.bdate_range(end=last, periods=n)
    close = start_price * np.power(1.001, np.arange(n))
    return pd.DataFrame({
        "time": dates.strftime("%Y-%m-%d"),
        "open": close * 0.998,
        "high": close * 1.006,
        "low": close * 0.994,
        "close": close,
        "volume": np.full(n, 1_500_000),
    })


def codes(rep) -> set:
    return {i.code for i in rep.issues}


# ─────────────────────────────────────────────────────────────────────
# 0. Ca sạch — không được báo nhầm
# ─────────────────────────────────────────────────────────────────────
def test_du_lieu_sach_khong_bi_bao_nham():
    rep = validate_ohlcv(clean_df(), "FPT", "HOSE")
    assert not rep.blocked, rep.summary()
    assert rep.level == Severity.OK, [i.message for i in rep.issues]
    assert rep.rows == 120
    print(f"PASS  dữ liệu sạch -> {rep.summary()}")


# ─────────────────────────────────────────────────────────────────────
# 1. Múi giờ
# ─────────────────────────────────────────────────────────────────────
def test_gio_viet_nam_khong_phai_gio_server():
    from datetime import datetime, timezone
    vn = now_vn()
    utc = datetime.now(timezone.utc)
    offset_hours = vn.utcoffset().total_seconds() / 3600
    assert offset_hours == 7, f"lệch múi giờ {offset_hours}h, phải là +7"
    # cùng thời điểm tuyệt đối, khác cách hiển thị
    assert abs((vn - utc).total_seconds()) < 5
    assert vn.hour == (utc.hour + 7) % 24
    print(f"PASS  giờ VN = UTC+7 ({vn:%H:%M} vs UTC {utc:%H:%M})")


# ─────────────────────────────────────────────────────────────────────
# 2. Quy đổi đơn vị — điểm giòn của bản cũ
# ─────────────────────────────────────────────────────────────────────
def test_don_vi_quyet_dinh_tu_trung_vi_khong_phai_gia_cuoi():
    """Chuỗi quanh mốc 1.000: giá cuối lúc dưới lúc trên, hệ số không được nhảy.

    Bản cũ dùng `1000 if close.iloc[-1] < 1000 else 1` nên hai phiên liền kề
    có thể cho hệ số lệch nhau 1000 lần.
    """
    base = np.linspace(980, 1020, 60)          # trung vị = 1000
    df_a = clean_df(60); df_a["close"] = base            # kết thúc ở 1020
    df_b = clean_df(60); df_b["close"] = base[::-1]      # kết thúc ở 980

    m_a, m_b = price_multiplier(df_a), price_multiplier(df_b)
    assert m_a == m_b, (
        f"hệ số nhảy theo giá cuối: {m_a} vs {m_b} — đây chính là lỗi cũ")
    print(f"PASS  hệ số ổn định bất kể giá cuối ({m_a})")


def test_nhan_dien_dung_nghin_dong_va_dong():
    df_k = clean_df(60, start_price=71.2)       # nghìn đồng
    df_d = clean_df(60, start_price=71_200.0)   # đồng
    assert price_multiplier(df_k) == 1000.0
    assert price_multiplier(df_d) == 1.0
    print("PASS  phân biệt đúng nghìn đồng (×1000) và đồng (×1)")


def test_canh_bao_khi_don_vi_khong_nhat_quan():
    """Nửa chuỗi theo nghìn đồng, nửa theo đồng -> phải cảnh báo."""
    mixed = pd.Series([70.0] * 30 + [70_000.0] * 30)
    mult, warn = detect_unit_multiplier(mixed)
    assert warn is not None and "không nhất quán" in warn
    print(f"PASS  bắt được đơn vị lẫn lộn: {warn[:50]}...")


# ─────────────────────────────────────────────────────────────────────
# 3. Tính hợp lệ của OHLCV
# ─────────────────────────────────────────────────────────────────────
def test_chan_gia_am_va_high_nho_hon_low():
    df = clean_df()
    df.loc[10, "close"] = -5
    rep = validate_ohlcv(df, "X", "HOSE")
    assert rep.blocked and "NON_POSITIVE" in codes(rep)

    df2 = clean_df()
    df2.loc[20, "high"] = df2.loc[20, "low"] - 100
    rep2 = validate_ohlcv(df2, "X", "HOSE")
    assert rep2.blocked and "HIGH_LT_LOW" in codes(rep2)
    print("PASS  chặn giá âm và high < low")


def test_chan_ngay_trung_va_thieu_cot():
    df = clean_df()
    df.loc[5, "time"] = df.loc[4, "time"]
    rep = validate_ohlcv(df, "X", "HOSE")
    assert rep.blocked and "DUPLICATE_DATES" in codes(rep)

    rep2 = validate_ohlcv(clean_df().drop(columns=["volume"]), "X", "HOSE")
    assert rep2.blocked and "MISSING_COLS" in codes(rep2)
    print("PASS  chặn ngày trùng và thiếu cột")


def test_chan_du_lieu_qua_ngan_va_rong():
    assert validate_ohlcv(clean_df(10), "X").blocked
    assert validate_ohlcv(pd.DataFrame(), "X").blocked
    assert validate_ohlcv(None, "X").blocked
    print("PASS  chặn dữ liệu rỗng và quá ngắn")


def test_gia_dong_cua_ngoai_khoang_cao_thap():
    df = clean_df()
    df.loc[30:40, "close"] = df.loc[30:40, "high"] * 2   # 11 phiên -> >2%
    rep = validate_ohlcv(df, "X", "HOSE")
    assert "OHLC_INCONSISTENT" in codes(rep) and rep.blocked
    print("PASS  chặn khi nhiều phiên có giá ngoài khoảng cao-thấp")


# ─────────────────────────────────────────────────────────────────────
# 4. Độ mới của dữ liệu
# ─────────────────────────────────────────────────────────────────────
def test_phat_hien_du_lieu_cu():
    rep_ok = validate_ohlcv(clean_df(end_offset=1), "X", "HOSE")
    assert "STALE" not in codes(rep_ok), rep_ok.summary()

    rep_warn = validate_ohlcv(clean_df(end_offset=5), "X", "HOSE")
    assert "STALE" in codes(rep_warn) and not rep_warn.blocked

    rep_block = validate_ohlcv(clean_df(end_offset=20), "X", "HOSE")
    assert "STALE" in codes(rep_block) and rep_block.blocked
    print("PASS  dữ liệu cũ: 1 ngày OK · 5 ngày cảnh báo · 20 ngày chặn")


# ─────────────────────────────────────────────────────────────────────
# 5. Biên độ dao động (nghi chia tách chưa điều chỉnh)
# ─────────────────────────────────────────────────────────────────────
def test_canh_bao_bien_dong_vuot_bien_do():
    df = clean_df()
    df.loc[60:, "close"] = df.loc[60:, "close"] / 2      # chia tách 1:2
    df.loc[60:, ["open", "high", "low"]] = df.loc[60:, ["open", "high", "low"]] / 2
    rep = validate_ohlcv(df, "X", "HOSE")
    assert "PRICE_JUMP" in codes(rep), rep.summary()
    assert not rep.blocked, "chia tách là cảnh báo, không phải lỗi chặn"
    print("PASS  cảnh báo (không chặn) khi nghi chia tách chưa điều chỉnh giá")


def test_bien_do_theo_san():
    """UPCOM biên độ rộng hơn HOSE nên cùng dữ liệu phải ít cảnh báo hơn."""
    df = clean_df()
    rng = np.random.default_rng(0)
    df["close"] = df["close"] * (1 + rng.choice([-0.10, 0.10], len(df)))
    df["high"] = df[["open", "close"]].max(axis=1) * 1.001
    df["low"] = df[["open", "close"]].min(axis=1) * 0.999
    hose = validate_ohlcv(df, "X", "HOSE")
    upcom = validate_ohlcv(df, "X", "UPCOM")
    assert "PRICE_JUMP" in codes(hose)
    assert "PRICE_JUMP" not in codes(upcom)
    print("PASS  biên độ áp theo sàn (HOSE 7% cảnh báo, UPCOM 15% không)")


# ─────────────────────────────────────────────────────────────────────
# 6. Chuẩn hoá
# ─────────────────────────────────────────────────────────────────────
def test_normalize_bo_trung_va_sap_xep():
    df = clean_df(50)
    dup = pd.concat([df, df.iloc[[10]]], ignore_index=True)
    shuffled = dup.sample(frac=1, random_state=1).reset_index(drop=True)
    out = normalize_ohlcv(shuffled)
    assert len(out) == 50
    t = pd.to_datetime(out["time"])
    assert t.is_monotonic_increasing and not t.duplicated().any()
    print("PASS  chuẩn hoá bỏ ngày trùng và sắp xếp tăng dần")


def test_normalize_khong_bia_du_lieu():
    """Chuẩn hoá không được lấp giá trị thiếu — lấp là tạo số không có thật."""
    df = clean_df(50)
    df.loc[10, "close"] = np.nan
    out = normalize_ohlcv(df)
    assert pd.isna(out.loc[10, "close"]), "giá trị thiếu bị lấp — không được"
    print("PASS  chuẩn hoá giữ nguyên ô thiếu, không tự lấp")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
        except Exception as e:
            failed += 1
            print(f"FAIL  {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n===== {len(fns) - failed}/{len(fns)} test PASS =====")
    sys.exit(1 if failed else 0)
