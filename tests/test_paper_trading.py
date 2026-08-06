"""Test sổ lệnh giấy.

Bốn bất biến, mỗi cái đều có thể âm thầm làm hỏng toàn bộ bằng chứng:
  1. Không nhìn trộm — vào lệnh ở giá MỞ CỬA phiên sau, không phải đóng cửa
     phiên có tín hiệu.
  2. Giả định bất lợi — SL và TP cùng chạm trong một phiên thì lấy SL.
  3. Có phí — lợi nhuận báo cáo phải đã trừ phí hai chiều và thuế bán.
  4. Ghi đủ — cả quyết định KHÔNG vào lệnh cũng phải có trong sổ.

Chạy offline:  python3 tests/test_paper_trading.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import paper_metrics as pm
import paper_trading as pt
from paper_trading import ExitReason, PaperTradingJournal, Status


def make_result(score: int, sl: float = 90.0, tp: float = 120.0,
                quality: str = "OK", size: float = 10.0) -> dict:
    return {
        "final_score": score,
        "recommendation": "MUA 📈" if score >= 62 else "NẮM GIỮ 👀",
        "data_quality": quality,
        "score_breakdown": {"trend_score": 70.0, "momentum_score": 65.0},
        "key_reasons": ["Xu hướng tăng"],
        "safety": {"safe_position_size": size},
        "analyses": {"risk": {"recommendations": {
            "stop_loss_price": sl, "take_profit_price": tp,
            "suggested_position_size_pct": size}}},
    }


def bar(o=None, h=None, l=None, c=None):
    return {"open": o, "high": h, "low": l, "close": c}


def new_journal() -> PaperTradingJournal:
    return PaperTradingJournal(":memory:")


# ─────────────────────────────────────────────────────────────────────
# 1. KHÔNG NHÌN TRỘM — bất biến quan trọng nhất
# ─────────────────────────────────────────────────────────────────────
def test_khong_vao_lenh_o_gia_dong_cua_phien_tin_hieu():
    """Tín hiệu sinh sau phiên T thì phải vào ở giá MỞ CỬA T+1.

    Vào ở giá đóng cửa T là nhìn trộm: lúc tín hiệu được tính, phiên T đã
    kết thúc. Sai lầm này khiến sổ đẹp lên một cách có hệ thống.
    """
    j = new_journal()
    tid = j.consider_entry("FPT", "2026-08-05", make_result(70))
    assert tid is not None

    t = j.open_position("FPT")
    assert t.status == Status.PENDING and t.entry_price is None

    # Cùng ngày tín hiệu -> KHÔNG được khớp
    assert j.fill_pending("FPT", "2026-08-05", 100.0) == 0
    assert j.open_position("FPT").status == Status.PENDING

    # Phiên sau -> khớp ở giá mở cửa
    assert j.fill_pending("FPT", "2026-08-06", 101.5) == 1
    t = j.open_position("FPT")
    assert t.status == Status.OPEN and t.entry_price == 101.5
    assert t.entry_date == "2026-08-06"
    print("PASS  vào lệnh ở giá mở cửa phiên sau, không phải đóng cửa phiên tín hiệu")


def test_khong_dong_lenh_ngay_trong_phien_vao():
    j = new_journal()
    j.consider_entry("FPT", "2026-08-05", make_result(70, sl=90, tp=120))
    j.fill_pending("FPT", "2026-08-06", 100.0)
    # Ngay phiên vào, giá quét cả SL lẫn TP -> vẫn không đóng
    closed = j.evaluate_open("FPT", "2026-08-06", bar(100, 125, 85, 110))
    assert closed == []
    assert j.open_position("FPT").status == Status.OPEN
    print("PASS  không đóng lệnh ngay trong phiên vừa vào")


# ─────────────────────────────────────────────────────────────────────
# 2. GIẢ ĐỊNH BẤT LỢI khi không phân biệt được thứ tự
# ─────────────────────────────────────────────────────────────────────
def test_sl_va_tp_cung_cham_thi_lay_sl():
    """Nến ngày không cho biết cái nào chạm trước. Chọn giả định bất lợi.

    Giả định có lợi (lấy TP) sẽ thổi phồng kết quả một cách có hệ thống —
    và lỗi đó không nhìn ra được từ báo cáo cuối.
    """
    j = new_journal()
    j.consider_entry("FPT", "2026-08-05", make_result(70, sl=90, tp=120))
    j.fill_pending("FPT", "2026-08-06", 100.0)
    closed = j.evaluate_open("FPT", "2026-08-07", bar(100, 125, 85, 110))
    assert len(closed) == 1
    assert closed[0]["reason"] == ExitReason.STOP_LOSS
    assert closed[0]["exit_price"] == 90.0
    print("PASS  SL và TP cùng chạm -> lấy SL (giả định bất lợi)")


def test_cham_tp_thi_dong_o_tp():
    j = new_journal()
    j.consider_entry("FPT", "2026-08-05", make_result(70, sl=90, tp=120))
    j.fill_pending("FPT", "2026-08-06", 100.0)
    closed = j.evaluate_open("FPT", "2026-08-07", bar(105, 122, 104, 121))
    assert closed[0]["reason"] == ExitReason.TAKE_PROFIT
    assert closed[0]["exit_price"] == 120.0
    print("PASS  chạm chốt lời -> đóng đúng ở giá TP")


def test_dong_theo_nguyen_tac_khi_tin_hieu_dao_chieu():
    j = new_journal()
    j.consider_entry("FPT", "2026-08-05", make_result(70, sl=90, tp=120))
    j.fill_pending("FPT", "2026-08-06", 100.0)
    # Giá chưa chạm SL/TP nhưng agent hạ điểm xuống dưới ngưỡng
    closed = j.evaluate_open("FPT", "2026-08-07", bar(100, 105, 98, 99),
                             current_score=40)
    assert closed[0]["reason"] == ExitReason.SIGNAL_REVERSED
    # Chưa khớp ngay: tín hiệu chỉ biết sau khi đóng cửa -> chờ mở cửa phiên sau
    assert closed[0]["exit_price"] is None and closed[0]["pending"] is True
    assert j.open_position("FPT").status == Status.CLOSING

    assert j.fill_closing("FPT", "2026-08-10", 97.5) == 1
    t = j.all_trades(Status.CLOSED)[0]
    assert t.exit_price == 97.5 and t.exit_date == "2026-08-10"
    print("PASS  đảo chiều -> chờ khớp giá mở cửa phiên sau, không bán ở giá đóng cửa")


def test_dong_khi_het_han_nam_giu():
    j = new_journal()
    j.consider_entry("FPT", "2026-01-05", make_result(70, sl=90, tp=120))
    j.fill_pending("FPT", "2026-01-06", 100.0)
    closed = j.evaluate_open("FPT", "2026-05-06", bar(100, 105, 98, 103))
    assert closed[0]["reason"] == ExitReason.MAX_HOLD
    assert closed[0]["pending"] is True
    assert j.fill_closing("FPT", "2026-05-07", 102.0) == 1
    assert j.all_trades(Status.CLOSED)[0].exit_price == 102.0
    print("PASS  hết hạn nắm giữ -> cũng khớp ở giá mở cửa phiên sau")


# ─────────────────────────────────────────────────────────────────────
# 3. PHÍ — bỏ qua thì mọi con số lạc quan giả
# ─────────────────────────────────────────────────────────────────────
def test_loi_nhuan_da_tru_phi():
    j = new_journal()
    j.consider_entry("FPT", "2026-08-05", make_result(70, sl=90, tp=110))
    j.fill_pending("FPT", "2026-08-06", 100.0)
    j.evaluate_open("FPT", "2026-08-07", bar(105, 112, 104, 111))

    t = j.all_trades(Status.CLOSED)[0]
    assert t.gross_return_pct() == 10.0            # 100 -> 110
    expected_cost = (pt.BROKER_FEE_PCT * 2 + pt.SELL_TAX_PCT) * 100
    assert abs(t.net_return_pct() - (10.0 - expected_cost)) < 1e-9
    assert t.net_return_pct() < t.gross_return_pct()
    print(f"PASS  lợi nhuận thô 10.00% -> sau phí {t.net_return_pct():.2f}% "
          f"(phí {expected_cost:.2f}%)")


def test_lenh_hoa_von_thuc_ra_lo_vi_phi():
    """Vào 100 ra 100 là LỖ, vì phí. Đây là chỗ dễ tự lừa nhất."""
    j = new_journal()
    j.consider_entry("FPT", "2026-08-05", make_result(70, sl=99.9, tp=100.0))
    j.fill_pending("FPT", "2026-08-06", 100.0)
    j.evaluate_open("FPT", "2026-08-07", bar(100, 100.5, 100.0, 100.0))
    t = j.all_trades(Status.CLOSED)[0]
    assert t.gross_return_pct() == 0.0
    assert t.net_return_pct() < 0
    print(f"PASS  lệnh hoà vốn thực ra lỗ {t.net_return_pct():.2f}% do phí")


# ─────────────────────────────────────────────────────────────────────
# 4. GHI ĐỦ — kể cả quyết định không vào lệnh
# ─────────────────────────────────────────────────────────────────────
def test_ghi_ca_quyet_dinh_khong_vao_lenh():
    """Chỉ ghi lệnh đã mở thì chính sổ đã có thiên lệch chọn mẫu."""
    j = new_journal()
    assert j.consider_entry("AAA", "2026-08-05", make_result(40)) is None
    assert j.consider_entry("BBB", "2026-08-05",
                            make_result(70, quality="SYNTHETIC")) is None
    assert j.consider_entry("CCC", "2026-08-05", make_result(70)) is not None

    all_d = j.decisions()
    assert len(all_d) == 3
    skipped = j.decisions(acted=False)
    assert len(skipped) == 2
    reasons = " ".join(d["skip_reason"] for d in skipped)
    assert "dưới ngưỡng" in reasons and "SYNTHETIC" in reasons
    print(f"PASS  ghi cả 3 quyết định, 2 không vào lệnh: {[d['skip_reason'][:28] for d in skipped]}")


def test_khong_mo_hai_lenh_cung_ma():
    j = new_journal()
    assert j.consider_entry("FPT", "2026-08-05", make_result(70)) is not None
    assert j.consider_entry("FPT", "2026-08-06", make_result(80)) is None
    assert "đã có vị thế" in j.decisions(acted=False)[0]["skip_reason"]
    print("PASS  không mở trùng vị thế trên cùng mã")


def test_chan_du_lieu_khong_dang_tin():
    j = new_journal()
    for q in ("SYNTHETIC", "FAILED", "PARTIAL"):
        assert j.consider_entry(f"X{q}", "2026-08-05",
                                make_result(90, quality=q)) is None
    assert len(j.all_trades()) == 0
    print("PASS  không vào lệnh khi dữ liệu không đáng tin")


# ─────────────────────────────────────────────────────────────────────
# 5. Chỉ số hiệu quả không tự lừa mình
# ─────────────────────────────────────────────────────────────────────
def _closed_trades(returns_pct: list[float]) -> list:
    """Dựng danh sách lệnh đã đóng với lợi nhuận THÔ cho trước."""
    trades = []
    for i, g in enumerate(returns_pct):
        trades.append(pt.Trade(
            id=i, symbol="X", signal_date="2026-01-01",
            entry_date="2026-01-02", entry_price=100.0,
            exit_date="2026-02-02", exit_price=100.0 * (1 + g / 100),
            exit_reason=ExitReason.MAX_HOLD, stop_loss=90.0, take_profit=120.0,
            size_pct=10.0, entry_score=70, status=Status.CLOSED))
    return trades


def test_it_lenh_thi_khong_ket_luan():
    r = pm.expectancy_significant(_closed_trades([5, -2, 3]))
    assert not r["significant"] and "chưa đủ" in r["verdict"]
    print(f"PASS  3 lệnh -> {r['verdict']}")


def test_ky_vong_duong_nhung_nhieu_thi_khong_ket_luan():
    import random
    rng = random.Random(1)
    noisy = [rng.gauss(0.5, 8) for _ in range(60)]
    r = pm.expectancy_significant(_closed_trades(noisy))
    assert not r["significant"], r
    print(f"PASS  60 lệnh nhiễu -> {r['verdict']}")


def test_ky_vong_duong_ro_rang_thi_ket_luan_duoc():
    import random
    rng = random.Random(2)
    strong = [rng.gauss(6, 3) for _ in range(120)]
    r = pm.expectancy_significant(_closed_trades(strong))
    assert r["significant"] and r["expectancy"] > 3
    print(f"PASS  120 lệnh lãi rõ -> {r['verdict']}")


def test_bao_cao_canh_bao_khi_thieu_doi_chieu_chuan():
    text = pm.report(_closed_trades([5, -3, 8, -2, 6, 1, -4, 9, 2, -1, 3, 7]))
    assert "Chưa có đối chiếu chuẩn" in text
    assert "phí" in text
    print("PASS  báo cáo cảnh báo rõ khi thiếu đối chiếu chỉ số")


def test_so_voi_chi_so_bat_duoc_thua_thi_truong():
    """Lãi 8% khi chỉ số tăng 12% là THUA — phép đo phải nói được điều đó."""
    trades = _closed_trades([8.0] * 40)
    bench = {("2026-01-02", "2026-02-02"): 12.0}
    r = pm.vs_benchmark(trades, bench)
    assert r["alpha"] < 0 and r["significant"]
    assert "THUA chuẩn" in r["verdict"]
    print(f"PASS  lãi 8% khi chỉ số +12% -> {r['verdict']} ({r['alpha']:+.2f}%)")


def test_drawdown_va_profit_factor():
    perf = pm.compute(_closed_trades([10, -5, 8, -12, 6]))
    assert perf.n_trades == 5
    assert 0 < perf.win_rate < 1
    assert perf.max_drawdown_pct > 0
    assert perf.profit_factor > 0
    print(f"PASS  {perf.summary()}")



# ─────────────────────────────────────────────────────────────────────
# 6. Vòng chạy một phiên — thứ tự thao tác quyết định tính đúng
# ─────────────────────────────────────────────────────────────────────
def test_tin_hieu_hom_nay_khong_khop_trong_hom_nay():
    """Bất biến của runner: tín hiệu phiên T không được khớp ở phiên T.

    Nếu run_session gọi consider_entry TRƯỚC fill_pending thì lệnh sẽ khớp
    ngay trong phiên có tín hiệu — nhìn trộm, và sổ đẹp lên có hệ thống.
    """
    import numpy as np
    import pandas as pd

    import paper_runner as pr

    n = 120
    close = 50_000 * np.power(1.003, np.arange(n))
    df = pd.DataFrame({
        "time": pd.bdate_range("2026-01-01", periods=n).strftime("%Y-%m-%d"),
        "open": close * 0.999, "high": close * 1.006,
        "low": close * 0.994, "close": close,
        "volume": np.full(n, 2_000_000),
    })

    j = new_journal()
    # Thay hệ chấm điểm bằng stub: test này kiểm tra THỨ TỰ THAO TÁC của
    # runner, không phải chất lượng tín hiệu. Trộn hai thứ vào một test thì
    # khi fail sẽ không biết cái nào hỏng.
    pr._analyze = lambda sym, hist, exch="HOSE": make_result(
        75, sl=float(hist["close"].iloc[-1]) * 0.9,
        tp=float(hist["close"].iloc[-1]) * 1.5)

    seen_entry_dates = []
    for t in range(60, n):
        row = df.iloc[t]
        pr.run_session(j, "T", df.iloc[: t + 1],
                       {"open": float(row["open"]), "high": float(row["high"]),
                        "low": float(row["low"]), "close": float(row["close"])},
                       str(row["time"]))
        pos = j.open_position("T")
        if pos and pos.entry_date:
            seen_entry_dates.append((pos.signal_date, pos.entry_date))

    assert seen_entry_dates, "không có lệnh nào được khớp"
    for signal_date, entry_date in seen_entry_dates:
        assert entry_date > signal_date, (
            f"khớp ngày {entry_date} cho tín hiệu ngày {signal_date} — nhìn trộm")
    print(f"PASS  {len(set(seen_entry_dates))} lệnh, mọi ngày khớp đều SAU ngày tín hiệu")


def test_gia_vao_dung_bang_gia_mo_cua_phien_khop():
    import numpy as np
    import pandas as pd

    import paper_runner as pr

    n = 100
    close = np.linspace(50_000, 70_000, n)
    df = pd.DataFrame({
        "time": pd.bdate_range("2026-01-01", periods=n).strftime("%Y-%m-%d"),
        "open": close * 0.99, "high": close * 1.01,
        "low": close * 0.98, "close": close,
        "volume": np.full(n, 2_000_000),
    })

    j = new_journal()
    pr._analyze = lambda sym, hist, exch="HOSE": make_result(
        75, sl=float(hist["close"].iloc[-1]) * 0.5,
        tp=float(hist["close"].iloc[-1]) * 5.0)

    for t in range(60, n):
        row = df.iloc[t]
        pr.run_session(j, "T", df.iloc[: t + 1],
                       {"open": float(row["open"]), "high": float(row["high"]),
                        "low": float(row["low"]), "close": float(row["close"])},
                       str(row["time"]))

    opened = [t for t in j.all_trades() if t.entry_price is not None]
    assert opened, "không có lệnh nào khớp"
    for t in opened:
        idx = list(df["time"]).index(t.entry_date)
        assert abs(t.entry_price - float(df["open"].iloc[idx])) < 1e-6, (
            f"giá vào {t.entry_price} khác giá mở cửa {df['open'].iloc[idx]}")
    print(f"PASS  {len(opened)} lệnh, giá vào đúng bằng giá mở cửa phiên khớp")


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
