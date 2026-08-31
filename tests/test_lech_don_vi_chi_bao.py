"""Không được trộn chỉ báo GIÁ từ hai nguồn khác hệ đơn vị.

VÌ SAO CÓ FILE NÀY
──────────────────
`DataOrchestrator.collect_and_handoff()` lấy chỉ báo từ TradingView (đơn vị
VNĐ) rồi ghi đè bằng chỉ báo tự tính từ OHLCV của vnstock (thường là nghìn
đồng). Vòng ghi đè chỉ đụng tới những khoá local TÍNH ĐƯỢC — khoá nào local
trả None thì giá trị VNĐ nằm lại.

Đo được 21/08/2026 trên app đang chạy: `days_back = 180` (~124 phiên) nên
local không bao giờ tính nổi SMA200 (cần 200 phiên). Gói dữ liệu ra thế này:

    EMA20  =     69,44   (nghìn đồng, local)
    SMA50  =     69,63   (nghìn đồng, local)
    SMA200 = 82.942,00   (VNĐ, TradingView)

`TrendAnalysisAgent` so `sma50 > sma200` tức `69,63 > 82.942` — SAI với MỌI
mã, MỌI lần — rồi trừ 2,0 điểm và in "🔴 Xu hướng trung-dài hạn GIẢM (Bear
Market)". FPT bị gắn nhãn giảm trong khi chính TradingView chấm BUY.

HAI CHIỀU PHẢI ĐÚNG, không chỉ một:
  · chỉ báo mang ĐƠN VỊ GIÁ mà local không tính được  -> BỎ
  · chỉ báo KHÔNG mang đơn vị giá (RSI, ADX, CCI…)     -> GIỮ

Chỉ kiểm chiều thứ nhất thì một bản sửa thô bạo "xoá sạch chỉ báo
TradingView" cũng xanh, mà bản đó vứt mất RSI/ADX/CCI đang dùng được.

Chạy offline: hai agent thu thập đều bị thay bằng hàm giả, không gọi mạng.
"""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import data_collectors as dc


def _df(n: int) -> pd.DataFrame:
    """OHLCV giả, giá quanh 69 — tức đơn vị NGHÌN ĐỒNG như vnstock trả."""
    gia = [69.0 + (i % 7) * 0.1 for i in range(n)]
    return pd.DataFrame({
        "time": pd.bdate_range("2024-01-01", periods=n).strftime("%Y-%m-%d"),
        "open": gia, "high": [g + 0.3 for g in gia],
        "low": [g - 0.3 for g in gia], "close": gia,
        "volume": [1_000_000] * n,
    })


def _goi(so_phien: int):
    """Chạy collect_and_handoff với hai nguồn giả. Trả về packet."""
    o = dc.DataOrchestrator("FPT", "2024-01-01", "2026-08-21", "HOSE",
                            collect_news=False)

    o.vnstock_agent.collect = lambda *a, **k: {
        "df": _df(so_phien), "status": "OK", "note": "gia lap"}

    # TradingView trả VNĐ — chênh local đúng 1.000 lần.
    o.tv_agent.collect = lambda *a, **k: {
        "status": "OK",
        "summary": {}, "oscillators": "NEUTRAL", "moving_averages": "NEUTRAL",
        "recommendation": "BUY", "exchange_found": "HOSE", "note": "gia lap",
        "indicators": {
            "EMA20": 69_437.0, "SMA50": 69_628.0, "SMA200": 82_942.0,
            "BB_Upper": 72_000.0, "BB_Lower": 66_000.0,
            "ATR": 1_200.0, "Mom": 350.0,
            # KHÔNG mang đơn vị giá — phải sống sót:
            "ADX": 17.7, "CCI20": -45.3, "Williams_R": -62.1,
        },
    }
    return o.collect_and_handoff()


# ─────────────────────────────────────────────────────────────────────
# 1. Chỉ báo GIÁ mà local không tính được -> BỎ
# ─────────────────────────────────────────────────────────────────────

def test_thieu_sma200_thi_BO_chu_khong_de_lai_gia_tri_VND():
    """124 phiên: đủ cho EMA20/SMA50, KHÔNG đủ cho SMA200 (cần 200)."""
    p = _goi(124)
    tv = p.tv_indicators

    assert "SMA200" not in tv, (
        f"SMA200 = {tv.get('SMA200')} còn nằm lại — đây là giá trị VNĐ của "
        f"TradingView, trong khi SMA50 = {tv.get('SMA50')} là nghìn đồng. "
        f"So hai số này là so hai thang đo khác nhau.")

    # Hai khoá local TÍNH ĐƯỢC thì phải mang giá trị của local.
    assert tv["EMA20"] < 1_000, f"EMA20 = {tv['EMA20']} vẫn là đơn vị VNĐ"
    assert tv["SMA50"] < 1_000, f"SMA50 = {tv['SMA50']} vẫn là đơn vị VNĐ"
    print("PASS  thiếu SMA200 -> bỏ hẳn, không để lại giá trị khác đơn vị")


def test_moi_chi_bao_theo_gia_deu_cung_mot_thang_do():
    """Không có khoá giá nào sót lại ở thang VNĐ."""
    p = _goi(124)
    tv = p.tv_indicators
    lech = {k: v for k, v in tv.items()
            if k in dc.CHI_BAO_THEO_GIA and isinstance(v, (int, float))
            and abs(v) > 1_000}
    assert not lech, f"còn chỉ báo ở thang VNĐ lẫn vào: {lech}"
    print("PASS  mọi chỉ báo theo giá cùng một thang đo")


# ─────────────────────────────────────────────────────────────────────
# 2. Chỉ báo KHÔNG mang đơn vị giá -> GIỮ
# ─────────────────────────────────────────────────────────────────────

def test_chi_bao_khong_mang_don_vi_gia_van_duoc_giu():
    """Chiều ngược lại. Thiếu test này thì một bản sửa 'xoá sạch chỉ báo
    TradingView' cũng xanh — mà bản đó vứt mất ADX và CCI20.

    ADX và CCI20 là hai khoá local KHÔNG tự tính, nên chúng là phép thử
    thật: nếu bản sửa xoá bừa thì hai khoá này biến mất.

    `Williams_R` không dùng làm phép thử được — local CÓ tự tính nó, nên
    giá trị của TradingView bị ghi đè một cách hợp lệ. Nó không mang đơn vị
    giá nên lấy từ nguồn nào cũng so sánh được; điều cần kiểm chỉ là nó còn
    có mặt.
    """
    p = _goi(124)
    tv = p.tv_indicators

    for k, mong in (("ADX", 17.7), ("CCI20", -45.3)):
        assert k in tv, f"{k} bị bỏ oan — nó không mang đơn vị giá"
        assert abs(tv[k] - mong) < 1e-6, (
            f"{k} = {tv[k]}, đáng lẽ giữ nguyên {mong} của TradingView")

    assert "Williams_R" in tv, "Williams %R biến mất — nó không mang đơn vị giá"
    assert -100 <= tv["Williams_R"] <= 0, (
        f"Williams %R = {tv['Williams_R']} ngoài dải [-100, 0]")

    # Mom mang đơn vị giá và local không tính -> phải bị bỏ.
    assert "Mom" not in tv, f"Mom = {tv.get('Mom')} còn lại ở thang VNĐ"
    print("PASS  ADX/CCI20 giữ nguyên · Williams %R còn · Mom bị bỏ")


# ─────────────────────────────────────────────────────────────────────
# 3. Đủ lịch sử thì luật SMA200 sống lại, bằng đúng đơn vị
# ─────────────────────────────────────────────────────────────────────

def test_du_lich_su_thi_sma200_duoc_tinh_tai_cho():
    p = _goi(300)
    tv = p.tv_indicators
    assert "SMA200" in tv, "đủ 300 phiên mà SMA200 vẫn vắng"
    assert tv["SMA200"] < 1_000, (
        f"SMA200 = {tv['SMA200']} — vẫn là giá trị VNĐ của TradingView chứ "
        f"không phải giá trị tính tại chỗ")
    assert 60 < tv["SMA200"] < 80, f"SMA200 = {tv['SMA200']} ngoài dải giá giả"
    print("PASS  đủ lịch sử -> SMA200 tính tại chỗ, cùng đơn vị")


def test_ghi_chu_noi_ra_da_bo_nhung_gi():
    """Bỏ im lặng thì không phân biệt được với 'TradingView không trả về'."""
    p = _goi(124)
    ghi = " ".join(p.source_notes)
    assert "khác hệ đơn vị" in ghi, f"không ghi chú gì về việc bỏ: {ghi}"
    assert "SMA200" in ghi, f"không nêu tên chỉ báo bị bỏ: {ghi}"
    print("PASS  ghi chú nói ra đã bỏ chỉ báo nào và vì sao")


if __name__ == "__main__":
    for ten, ham in sorted(list(globals().items())):
        if ten.startswith("test_"):
            ham()
    print("\nTẤT CẢ ĐỀU QUA")
