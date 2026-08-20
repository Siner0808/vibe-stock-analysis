"""Cổng chất lượng dữ liệu phải THẬT SỰ được cắm — Gate 2 điều kiện 4.

Đo ngày 20/08/2026: `decisions.data_quality` = 'OK' cho **12.984/12.984**
dòng, không một giá trị nào khác trong toàn sổ. Khi soi sổ, cột đó trông
đúng như bằng chứng dữ liệu đã sạch.

Nguồn: `MarketDataPacket.data_quality: str = "OK"` là mặc định ngay trong
dataclass, và `paper_runner._analyze()` dựng packet với `data_quality="OK"`
cứng. Nhánh `elif quality != "OK"` trong `consider_entry()` vì thế là CODE
CHẾT — không bao giờ đúng.

Cạm bẫy khi cắm: `validate_ohlcv` đo độ cũ so với HÔM NAY. Backtest replay
phiên 2024 thì mọi lát cắt đều "cũ 2 năm" và bị BLOCK sạch. Đây đúng cùng
một lỗi khái niệm với cổng VN-INDEX: độ cũ phải đo so với NGÀY ĐANG CHẤM.
"""
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import pandas as pd

from data_quality import Severity, validate_ohlcv


def _chuoi(den: str, n: int = 80) -> pd.DataFrame:
    ngay = pd.bdate_range(end=den, periods=n).strftime("%Y-%m-%d")
    return pd.DataFrame({
        "time": ngay, "open": [10.0] * n, "high": [10.4] * n,
        "low": [9.7] * n, "close": [10.1] * n, "volume": [1_000_000] * n})


def test_do_cu_do_so_voi_NGAY_DANG_CHAM_khong_phai_hom_nay():
    """Lát cắt backtest năm 2024 KHÔNG được coi là cũ 2 năm."""
    df = _chuoi("2024-03-01")
    r = validate_ohlcv(df, "TST", as_of="2024-03-01")
    assert not any(i.code == "STALE" for i in r.issues), (
        f"lát cắt tự nó là mới nhất mà vẫn bị STALE: {r.summary()}")
    print("PASS  chấm phiên 2024 với as_of=2024 -> không STALE")


def test_du_lieu_cu_that_thi_van_bi_bat():
    """Quá hạn khác với backtest. Cũ thật thì phải chặn."""
    df = _chuoi("2026-07-01")
    r = validate_ohlcv(df, "TST", as_of="2026-08-20")
    assert any(i.code == "STALE" for i in r.issues)
    assert r.level >= Severity.BLOCK, f"cũ 7 tuần mà chỉ {r.level.name}"
    print("PASS  dữ liệu cũ thật -> vẫn BLOCK")


def test_khong_truyen_as_of_thi_van_do_so_voi_hom_nay():
    """Giữ nguyên hành vi cũ khi không ai truyền gì."""
    r = validate_ohlcv(_chuoi("2020-01-01"), "TST")
    assert any(i.code == "STALE" for i in r.issues)
    print("PASS  không truyền as_of -> vẫn so với hôm nay")


def test_analyze_ghi_muc_chat_luong_THAT_khong_phai_hang_OK():
    """Gate 2 điều kiện 4: packet phải mang mức thật, không phải 'OK' cứng."""
    import paper_runner as pr

    cu = pr._ANALYZE_CACHE
    try:
        pr._ANALYZE_CACHE = {}
        # Lát cắt dừng 2026-07-01 nhưng đang chấm phiên 2026-08-20 -> cũ thật.
        kq = pr._analyze("TST", _chuoi("2026-07-01", n=140),
                         session_date="2026-08-20")
    finally:
        pr._ANALYZE_CACHE = cu

    assert kq.get("data_quality") != "OK", (
        f"lát cắt cũ 7 tuần mà packet vẫn ghi {kq.get('data_quality')!r} — "
        f"cổng chất lượng vẫn là code chết")
    print(f"PASS  _analyze ghi mức thật: {kq.get('data_quality')!r}")


def test_consider_entry_chan_theo_BLOCK_chu_khong_chan_ca_WARN():
    """WARN là cảnh báo, BLOCK là chặn. Gộp hai thứ là mất thông tin."""
    import os
    import tempfile

    import market_filter
    import paper_trading as pt
    market_filter.is_vni_bullish = lambda _d: True
    pt.CHO_PHEP_MO_LENH_MOI = True

    def _kq(muc):
        return {"final_score": 95, "recommendation": "MUA 📈",
                "data_quality": muc, "score_breakdown": {},
                "key_reasons": [], "safety": {"safe_position_size": 10.0},
                "analyses": {"risk": {"recommendations": {
                    "entry_price": 100.0, "stop_loss_price": 90.0,
                    "take_profit_price": 120.0,
                    "suggested_position_size_pct": 10.0}}}}

    with tempfile.TemporaryDirectory() as d:
        j = pt.PaperTradingJournal(os.path.join(d, "s.db"))
        id_warn = j.consider_entry("AAA", "2026-08-05", _kq("WARN"),
                                   buy_threshold=50.0)
        id_block = j.consider_entry("BBB", "2026-08-05", _kq("BLOCK"),
                                    buy_threshold=50.0)
        muc = dict(j.db.execute(
            "select symbol, data_quality from decisions").fetchall())
        j.db.close()

    assert id_block is None, "mức BLOCK mà vẫn mở lệnh"
    assert id_warn is not None, "mức WARN bị chặn như BLOCK — mất phân biệt"
    assert muc.get("AAA") == "WARN" and muc.get("BBB") == "BLOCK", (
        f"sổ không ghi đúng mức: {muc}")
    print("PASS  BLOCK chặn, WARN chỉ cảnh báo, sổ ghi đúng mức")


if __name__ == "__main__":
    for f in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        f()
