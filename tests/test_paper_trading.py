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

import market_filter
import paper_metrics as pm
import paper_trading as pt
from paper_trading import ExitReason, PaperTradingJournal, Status

# ─────────────────────────────────────────────────────────────────────
# CÁCH LY BỘ LỌC VN-INDEX
#
# consider_entry() hỏi market_filter.is_vni_bullish(signal_date). Bộ lọc đó
# đọc cache VNINDEX thật, nên kết quả test phụ thuộc vào việc thị trường
# nằm trên hay dưới MA50 vào đúng ngày được hardcode trong test.
#
# Hậu quả đã xảy ra: VN-INDEX xuống dưới MA50 ngày 2026-08-05 làm 11 test
# đỏ mà không ai đụng vào mã. Nguy hiểm hơn là chiều ngược lại — chúng sẽ
# tự xanh trở lại khi thị trường đổi chiều, che mất hồi quy thật.
#
# File này kiểm thử SỔ LỆNH, không kiểm thử bộ lọc. Ghim bộ lọc mở để test
# tái lập được và không cần cache VNINDEX.
market_filter.is_vni_bullish = lambda _signal_date: True

# ─────────────────────────────────────────────────────────────────────
# Ô C5 — NGƯỠNG MUA ĐỂ TRỐNG
#
# `paper_trading.CHO_PHEP_MO_LENH_MOI` mặc định TẮT: hệ thống chạy thật
# không mở vị thế mới cho tới khi Phase 5D sinh ra một ngưỡng chọn bằng
# walk-forward hợp lệ. File này kiểm thử chính logic vào lệnh, nên phải
# bật công tắc — nếu không mọi test vào lệnh đều đo nhầm cái công tắc.
pt.CHO_PHEP_MO_LENH_MOI = True


def make_result(score: int, sl: float = 90.0, tp: float = 120.0,
                quality: str = "OK", size: float = 10.0,
                entry: float = 100.0) -> dict:
    # `entry_price` là bắt buộc: từ khi cỡ lệnh tính theo khoảng cách cắt lỗ
    # (rủi ro cố định 1%/lệnh), consider_entry() cần giá vào để suy ra
    # sl_pct_dist. Fixture thiếu khoá này làm 15 test đỏ âm thầm.
    return {
        "final_score": score,
        "recommendation": "MUA 📈" if score >= 62 else "NẮM GIỮ 👀",
        "data_quality": quality,
        "score_breakdown": {"trend_score": 70.0, "momentum_score": 65.0},
        "key_reasons": ["Xu hướng tăng"],
        "safety": {"safe_position_size": size},
        "analyses": {"risk": {"recommendations": {
            "entry_price": entry,
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


def test_cham_muc_tp_khong_con_dong_lenh_ma_nang_trailing_stop():
    """Chốt lời cứng ĐÃ BỊ GỠ có chủ ý (paper_trading.py, 'Fat-Tail
    Exploitation'): giá chạm mức take_profit không còn đóng lệnh nữa, chỉ
    trailing stop 7% mới đóng.

    Test cũ ở đây khoá hành vi ngược lại và đã đỏ âm thầm. Giữ lại test này
    để (a) ghi nhận luật hiện hành, (b) bắt được nếu Hard TP bị đưa trở lại
    mà không ai bàn.
    """
    j = new_journal()
    j.consider_entry("FPT", "2026-08-05", make_result(70, sl=90, tp=120))
    j.fill_pending("FPT", "2026-08-06", 100.0)

    # high 122 vượt mức TP 120 — trước đây đóng ở 120, nay KHÔNG đóng.
    closed = j.evaluate_open("FPT", "2026-08-07", bar(105, 122, 104, 121))
    assert closed == [], f"chạm mức TP không được đóng lệnh nữa, nhận {closed}"

    t = j.open_position("FPT")
    assert t is not None and t.status == Status.OPEN

    # Đổi lại, stop phải được nâng: hoà vốn (>= +5%) rồi trailing 7% từ giá
    # đóng cửa 121 -> 112.53, và trailing cao hơn nên thắng.
    assert abs(t.stop_loss - 121 * 0.93) < 1e-9, (
        f"trailing stop phải nâng lên {121 * 0.93:.2f}, đang là {t.stop_loss}")
    print(f"PASS  chạm mức TP không đóng lệnh, trailing stop nâng lên "
          f"{t.stop_loss:.2f}")


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
    # Đóng lệnh bằng tín hiệu đảo chiều rồi khớp ở giá mở cửa phiên sau.
    # Trước đây test này đóng bằng chốt lời cứng — cơ chế đó đã bị gỡ, nhưng
    # bất biến cần khoá (lợi nhuận phải trừ phí) thì không đổi.
    j = new_journal()
    j.consider_entry("FPT", "2026-08-05", make_result(70, sl=90, tp=110))
    j.fill_pending("FPT", "2026-08-06", 100.0)
    j.evaluate_open("FPT", "2026-08-07", bar(100, 105, 98, 99),
                    current_score=40)
    assert j.fill_closing("FPT", "2026-08-10", 110.0) == 1

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
    j.consider_entry("FPT", "2026-08-05", make_result(70, sl=90.0, tp=120.0))
    j.fill_pending("FPT", "2026-08-06", 100.0)
    j.evaluate_open("FPT", "2026-08-07", bar(100, 100.5, 98.0, 99.0),
                    current_score=40)
    assert j.fill_closing("FPT", "2026-08-10", 100.0) == 1
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


def _overlapping_trades(n: int, size_pct: float) -> list:
    """n lệnh mở CÙNG LÚC, mỗi lệnh chiếm size_pct vốn."""
    return [pt.Trade(
        id=i, symbol=f"S{i}", signal_date="2026-01-01",
        entry_date="2026-01-02", entry_price=100.0,
        exit_date="2026-02-02", exit_price=105.0,
        exit_reason=ExitReason.MAX_HOLD, stop_loss=90.0, take_profit=120.0,
        size_pct=size_pct, entry_score=70, status=Status.CLOSED)
        for i in range(n)]


def test_von_trien_khai_phat_hien_don_bay_an():
    """Đường vốn nhân dồn từng lệnh vào TOÀN BỘ vốn, lần lượt. Phép nhân đó
    chỉ đúng khi mỗi thời điểm có một lệnh mở.

    Sự cố 12/08/2026: báo cáo 20 vòng công bố +636,11% ở ngưỡng 50,0. Con
    số tái lập được, nhưng bộ lệnh đó giữ trung bình 224% vốn (đỉnh 1.160%)
    — lợi nhuận của một tài khoản dùng đòn bẩy 2,2 lần, không phải tài
    khoản thật. Không có phép đo nào bắt được điều đó, nên nó thành 'kết
    quả' và được nạp đè vào sổ lệnh thật.
    """
    perf = pm.compute(_overlapping_trades(12, 30.0))
    assert perf is not None
    assert abs(perf.avg_capital_deployed_pct - 360.0) < 1e-6, (
        f"12 lệnh × 30% mở cùng lúc = 360% vốn, "
        f"đo được {perf.avg_capital_deployed_pct}")
    assert abs(perf.peak_capital_deployed_pct - 360.0) < 1e-6
    print(f"PASS  bắt được đòn bẩy ẩn: "
          f"{perf.avg_capital_deployed_pct:.0f}% vốn trung bình")


def test_von_trien_khai_khong_bao_dong_gia_khi_lenh_noi_tiep():
    """Lệnh nối tiếp nhau, không chồng lấn -> vốn triển khai đúng bằng
    tỷ trọng một lệnh. Không được báo động giả."""
    trades = [pt.Trade(
        id=i, symbol="X", signal_date="2026-01-01",
        entry_date=f"2026-0{i + 1}-01", entry_price=100.0,
        exit_date=f"2026-0{i + 2}-01", exit_price=105.0,
        exit_reason=ExitReason.MAX_HOLD, stop_loss=90.0, take_profit=120.0,
        size_pct=25.0, entry_score=70, status=Status.CLOSED)
        for i in range(3)]
    perf = pm.compute(trades)
    assert abs(perf.peak_capital_deployed_pct - 25.0) < 1e-6, (
        f"không chồng lấn thì đỉnh phải là 25%, "
        f"đo được {perf.peak_capital_deployed_pct}")
    print(f"PASS  lệnh nối tiếp -> {perf.peak_capital_deployed_pct:.0f}% vốn, "
          f"không báo động giả")


def test_bao_cao_canh_bao_khi_von_vuot_100():
    text = pm.report(_overlapping_trades(12, 30.0))
    assert "đòn bẩy" in text.lower(), "báo cáo phải nói rõ đây là đòn bẩy"
    assert "360" in text
    print("PASS  báo cáo cảnh báo khi vốn triển khai vượt 100%")


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


def test_vs_benchmark_bao_ro_so_lenh_bi_bo_vi_thieu_cap_ngay():
    """Gate 5B — một phép đo im lặng bỏ mẫu là phép đo hỏng.

    Đây là cơ chế thật, không phải giả định: `backtest/cache/` có HAI định
    dạng cột `time` trong cùng một thư mục — 40/125 file dạng
    `2025-02-10 07:00:00`, 85/125 dạng `2021-10-14` — trong khi 113/113
    lệnh trong sổ đều dùng `YYYY-MM-DD` sạch. Khoá đối chiếu là chuỗi
    nguyên vẹn, nên rổ dựng từ nhóm file có hậu tố giờ KHÔNG khớp một lệnh
    nào, và `vs_benchmark` `continue` im lặng qua từng lệnh một.

    Hậu quả không phải là báo lỗi mà là một câu vô hại: "mới 0 lệnh có đối
    chiếu, chưa đủ" — đọc như thiếu dữ liệu, thật ra là lỗi định dạng.
    """
    trades = _closed_trades([5.0] * 12)

    # Rổ chuẩn dựng từ file cache CÓ hậu tố giờ: không khớp lệnh nào.
    ro_hong = {("2026-01-02 07:00:00", "2026-02-02 07:00:00"): 3.0}
    r = pm.vs_benchmark(trades, ro_hong)
    assert r["n"] == 0
    assert r.get("bo_qua") == 12, (
        f"bỏ 12/12 lệnh mà không nói ra: bo_qua={r.get('bo_qua')!r}")

    # Rổ đúng định dạng: khớp hết, không bỏ lệnh nào.
    ro_dung = {("2026-01-02", "2026-02-02"): 3.0}
    r2 = pm.vs_benchmark(trades, ro_dung)
    assert r2["n"] == 12 and r2.get("bo_qua") == 0

    # Và báo cáo phải NÓI RA con số đó, không giấu trong dict.
    text = pm.report(trades, ro_hong)
    assert "12" in text and "bỏ" in text.lower(), (
        "báo cáo không nhắc tới số lệnh bị bỏ:" + chr(10) + text)
    print("PASS  vs_benchmark nói ra 12/12 lệnh bị bỏ vì lệch định dạng ngày")


def test_ro_chuan_chuan_hoa_ngay_o_CA_HAI_phia():
    """Gate 5B — lệch định dạng ngày phải được vá ở ĐIỂM DÙNG.

    `backtest/cache/` có 40/125 file mang hậu tố ' 07:00:00'. Sửa 125 file
    dữ liệu là một việc; dựng rổ chuẩn sao cho không quan tâm hậu tố là
    việc khác, rẻ hơn và không đụng vào dữ liệu gốc.
    """
    trades = _closed_trades([5.0] * 3)          # vào 2026-01-02, ra 2026-02-02

    # Chuỗi giá mang hậu tố giờ — đúng dạng 40/125 file cache đang có.
    gia = {"2026-01-02 07:00:00": 100.0, "2026-02-02 07:00:00": 110.0}
    ro = pm.ro_chuan_tu_chuoi_gia(trades, gia)

    assert ("2026-01-02", "2026-02-02") in ro, f"khoá chưa chuẩn hoá: {list(ro)}"
    assert abs(ro[("2026-01-02", "2026-02-02")] - 10.0) < 1e-9

    # Và rổ đó phải khớp thật khi đem đi đo, không bỏ lệnh nào.
    r = pm.vs_benchmark(trades, ro)
    assert r["bo_qua"] == 0, f"vẫn bỏ {r['bo_qua']} lệnh"

    # Thiếu ngày trong chuỗi giá -> KHÔNG dựng khoá, để vs_benchmark đếm.
    ro_thieu = pm.ro_chuan_tu_chuoi_gia(trades, {"2026-01-02": 100.0})
    assert ro_thieu == {}
    assert pm.vs_benchmark(trades, ro_thieu)["bo_qua"] == 3
    print("PASS  rổ chuẩn chuẩn hoá ngày hai phía, thiếu ngày thì đếm chứ không đoán")


def test_C5_khong_mo_lenh_moi_khi_nguong_chua_chon():
    """Ô C5: quét tiếp, ghi quyết định tiếp, nhưng KHÔNG mở vị thế mới.

    Đây là chốt chặn cho đúng cạm bẫy mà docs/HANDOFF.md cảnh báo: giây
    phút Phase 2 gỡ cổng VN-INDEX, `consider_entry()` sẽ chạy tới dòng so
    ngưỡng và mở lệnh ở lượt quét kế tiếp, bằng ngưỡng 50,0 — con số mà
    NGUYEN-TAC-DO-LUONG.md mục 7 đã tuyên bố vô hiệu.

    Đo được trong phiên 20/08: win rate cả dải ngưỡng 48–59 chỉ trải
    28,2%–30,7%, tương quan ngưỡng↔số lệnh −0,999 và số lệnh↔vốn đỉnh
    +0,990. Ngưỡng không cải thiện chất lượng chọn mã; nó chỉ điều khiển
    đòn bẩy.

    Quan trọng: quyết định VẪN được ghi sổ, kèm lý do. Im lặng không mở
    lệnh thì không phân biệt được với "không có tín hiệu nào".
    """

    import tempfile
    with tempfile.TemporaryDirectory() as d:
        j = PaperTradingJournal(os.path.join(d, "so.db"))
        cu = pt.CHO_PHEP_MO_LENH_MOI
        try:  # noqa: đóng sổ ở cuối, xem finally phía dưới
            pt.CHO_PHEP_MO_LENH_MOI = False
            tid = j.consider_entry("FPT", "2026-08-05", make_result(95),
                                   buy_threshold=50.0)
        finally:
            pt.CHO_PHEP_MO_LENH_MOI = cu

        assert tid is None, "điểm 95 vẫn mở lệnh dù công tắc C5 đang TẮT"

        dong = j.db.execute(
            "select skip_reason, score, acted from decisions "
            "where symbol='FPT'").fetchall()
        assert dong, "không mở lệnh mà cũng KHÔNG ghi quyết định — mất dấu vết"
        ly_do, diem, acted = dong[0]
        assert acted == 0
        assert int(diem) == 95, f"điểm thật không được ghi: {diem}"
        assert "C5" in (ly_do or ""), f"lý do không nhắc ô C5: {ly_do!r}"
        j.db.close()
    print("PASS  C5: không mở lệnh mới, nhưng vẫn ghi quyết định kèm lý do")



def test_C5_backtest_duoc_mo_cong_tac_va_luon_tra_lai():
    """Ngoại lệ hẹp của C5: backtest tồn tại ĐỂ ĐO logic vào lệnh.

    Chạy backtest với công tắc tắt thì mọi sổ đều rỗng, và mọi kết luận
    kiểu "không có giá trị X trong sổ" đều đúng một cách vô nghĩa. Nhưng
    ngoại lệ phải TRẢ LẠI trạng thái cũ, kể cả khi có lỗi ở giữa.
    """
    import paper_runner as pr

    cu = pt.CHO_PHEP_MO_LENH_MOI
    try:
        pt.CHO_PHEP_MO_LENH_MOI = False
        with pr._cho_phep_mo_lenh():
            assert pt.CHO_PHEP_MO_LENH_MOI is True, "backtest không được mở công tắc"
        assert pt.CHO_PHEP_MO_LENH_MOI is False, "không trả lại trạng thái cũ"

        try:
            with pr._cho_phep_mo_lenh():
                raise RuntimeError("lỗi giữa chừng")
        except RuntimeError:
            pass
        assert pt.CHO_PHEP_MO_LENH_MOI is False, (
            "lỗi giữa chừng làm công tắc kẹt ở BẬT — hệ thống chạy thật sẽ "
            "mở lệnh mà không ai biết")
    finally:
        pt.CHO_PHEP_MO_LENH_MOI = cu
    print("PASS  backtest mở công tắc rồi trả lại, kể cả khi có lỗi")



def test_drawdown_va_profit_factor():
    perf = pm.compute(_closed_trades([10, -5, 8, -12, 6]))
    assert perf.n_trades == 5
    assert 0 < perf.win_rate < 1
    assert perf.max_drawdown_pct > 0
    assert perf.profit_factor > 0
    print(f"PASS  {perf.summary()}")


def _trade(sym, entry_date, exit_date, gross_pct, tid=0, size=100.0):
    return pt.Trade(
        id=tid, symbol=sym, signal_date=entry_date, entry_date=entry_date,
        entry_price=100.0, exit_date=exit_date,
        exit_price=100.0 * (1 + gross_pct / 100),
        exit_reason=ExitReason.MAX_HOLD, stop_loss=90.0, take_profit=120.0,
        size_pct=size, entry_score=70, status=Status.CLOSED)


def test_duong_von_khong_phu_thuoc_thu_tu_ban_ghi():
    """Sổ trả lệnh theo id (hết mã A rồi tới mã B), không theo thời gian.

    Dựng đường vốn theo thứ tự đó cho ra một chuỗi lãi/lỗ chưa từng tồn tại.
    Đảo thứ tự chèn mà kết quả đổi thì chỉ số đang đo thứ tự lưu trữ, không
    đo hiệu quả giao dịch.
    """
    # Theo id  : -10, -10, +30  -> hai lỗ liền nhau, đáy 19% dưới đỉnh
    # Theo ngày: -10, +30, -10  -> hai lỗ bị cái lãi tách ra, đáy chỉ ~10%
    a = [_trade("AAA", "2026-01-05", "2026-01-10", -10, 1),
         _trade("AAA", "2026-03-05", "2026-03-10", -10, 2),
         _trade("BBB", "2026-02-05", "2026-02-10", +30, 3)]
    b = [a[2], a[1], a[0]]                     # cùng tập lệnh, khác thứ tự chèn

    pa, pb = pm.compute(a), pm.compute(b)
    assert abs(pa.max_drawdown_pct - pb.max_drawdown_pct) < 1e-9, (
        f"MaxDD đổi theo thứ tự chèn: {pa.max_drawdown_pct:.2f} "
        f"vs {pb.max_drawdown_pct:.2f}")
    assert abs(pa.total_net_pct - pb.total_net_pct) < 1e-9
    # Và phải ra con số của thứ tự THỜI GIAN, không phải của thứ tự chèn
    assert pa.max_drawdown_pct < 12.0, (
        f"MaxDD {pa.max_drawdown_pct:.2f}% là của thứ tự chèn (~19%), "
        "không phải thứ tự thời gian (~10%)")
    print(f"PASS  đảo thứ tự chèn không đổi MaxDD ({pa.max_drawdown_pct:.2f}%)")


def test_drawdown_dung_bang_muc_sut_giam_thuc():
    """Chuỗi có drawdown biết trước: +20% rồi -30% -> đáy sâu 30% dưới đỉnh."""
    trades = [_trade("AAA", "2026-01-05", "2026-01-10", +20, 1),
              _trade("BBB", "2026-02-05", "2026-02-10", -30, 2)]
    perf = pm.compute(trades)
    # phí hai chiều làm lệch nhẹ so với 30% lý thuyết
    assert 30.0 <= perf.max_drawdown_pct <= 31.0, perf.max_drawdown_pct
    print(f"PASS  drawdown thực {perf.max_drawdown_pct:.2f}% (lý thuyết ~30%)")


# ─────────────────────────────────────────────────────────────────────
# 5b. Dời stop về hoà vốn — không được chọn kết cục có lợi
# ─────────────────────────────────────────────────────────────────────
def test_doi_stop_hoa_von_khong_co_hieu_luc_trong_chinh_phien_do():
    """Nến vừa chạm +5% vừa thủng cắt lỗ: phải khớp ở SL GỐC.

    Nến ngày không cho biết đỉnh hay đáy tới trước. Dời stop rồi xét ngay
    trong chính cây nến đó là giả định đỉnh luôn tới trước — chọn kết cục
    có lợi, đúng thứ bất biến "giả định bất lợi" của sổ này cấm.
    """
    j = new_journal()
    j.consider_entry("FPT", "2026-08-05", make_result(70, sl=95.0, tp=130.0))
    j.fill_pending("FPT", "2026-08-06", 100.0)

    # high 106 (>= +5%), low 94 (thủng SL gốc 95)
    closed = j.evaluate_open("FPT", "2026-08-07", bar(100, 106, 94, 96))
    assert len(closed) == 1
    assert closed[0]["exit_price"] == 95.0, (
        f"khớp ở {closed[0]['exit_price']} thay vì SL gốc 95.0 — "
        "stop hoà vốn đã bảo vệ ngược lại chính cây nến tạo ra nó")
    print("PASS  nến vừa chạm +5% vừa thủng SL -> khớp ở SL gốc, không phải hoà vốn")


def test_doi_stop_hoa_von_co_hieu_luc_tu_phien_sau():
    """Nhưng quy tắc vẫn phải hoạt động — chỉ là chậm một phiên."""
    j = new_journal()
    j.consider_entry("FPT", "2026-08-05", make_result(70, sl=95.0, tp=130.0))
    j.fill_pending("FPT", "2026-08-06", 100.0)

    # Phiên 1: chạm +5%, không thủng SL -> stop được nâng lên 100
    assert j.evaluate_open("FPT", "2026-08-07", bar(100, 106, 99, 105)) == []
    assert j.open_position("FPT").stop_loss == 100.0

    # Phiên 2: giá lùi về 99 -> khớp ở mức hoà vốn 100
    closed = j.evaluate_open("FPT", "2026-08-10", bar(104, 105, 99, 99))
    assert len(closed) == 1 and closed[0]["exit_price"] == 100.0
    print("PASS  stop hoà vốn có hiệu lực từ phiên sau (khớp ở 100.0)")



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



# ─────────────────────────────────────────────────────────────────────
# 7. ĐƠN VỊ GIÁ — lỗi này làm hỏng toàn bộ sổ mà không ai thấy
# ─────────────────────────────────────────────────────────────────────
def test_gia_nghin_dong_khong_lam_hong_so_lenh():
    """Nguồn vnstock trả nghìn đồng (FPT = 71.2); SL/TP tính bằng VNĐ (66.000).

    So thẳng hai đơn vị đó thì `low <= stop_loss` LUÔN đúng — mọi lệnh đóng
    ngay phiên sau với lợi nhuận hàng chục nghìn phần trăm. Dữ liệu test
    tổng hợp ở mức 50.000 nên đơn vị trùng nhau và lỗi hoàn toàn vô hình.
    Test này dùng đúng thang nghìn đồng như dữ liệu thật.
    """
    import numpy as np
    import pandas as pd

    import paper_runner as pr

    n = 120
    close_k = 71.2 * np.power(1.002, np.arange(n))     # nghìn đồng
    df = pd.DataFrame({
        "time": pd.bdate_range("2026-01-01", periods=n).strftime("%Y-%m-%d"),
        "open": close_k * 0.998, "high": close_k * 1.006,
        "low": close_k * 0.994, "close": close_k,
        "volume": np.full(n, 2_000_000),
    })

    # SL/TP do RiskManagementAgent trả về: đơn vị VNĐ
    pr._analyze = lambda sym, hist, exch="HOSE": make_result(
        75,
        sl=float(hist["close"].iloc[-1]) * 1000 * 0.93,
        tp=float(hist["close"].iloc[-1]) * 1000 * 1.15)

    j = new_journal()
    for t in range(60, n):
        row = df.iloc[t]
        pr.run_session(j, "T", df.iloc[: t + 1],
                       {"open": float(row["open"]), "high": float(row["high"]),
                        "low": float(row["low"]), "close": float(row["close"])},
                       str(row["time"]))

    closed = j.all_trades(Status.CLOSED)
    opened = [t for t in j.all_trades() if t.entry_price is not None]
    assert opened, "không có lệnh nào khớp"

    for t in opened:
        assert 10_000 < t.entry_price < 500_000, (
            f"giá vào {t.entry_price} không phải VNĐ — đơn vị chưa quy đổi")
    for t in closed:
        g = t.gross_return_pct()
        assert -60 < g < 60, (
            f"lợi nhuận {g:,.0f}% vô lý — dấu hiệu lẫn đơn vị nghìn đồng/VNĐ")
    print(f"PASS  giá nghìn đồng quy đúng về VNĐ ({opened[0].entry_price:,.0f}), "
          f"{len(closed)} lệnh đóng với lợi nhuận hợp lý")



def test_run_session_tra_ve_diem_that_khong_phai_hang_so():
    """run_session() phải trả ĐIỂM THẬT ra ngoài cho bên dựng báo cáo.

    Bối cảnh: run_daily.py dựng báo cáo phiên bằng `s.get("score", 50.0)`,
    trong khi run_session() không hề đặt khoá đó — điểm thật được tính bên
    trong rồi bị vứt đi. Hệ quả đo được: 210/210 điểm cổ phiếu và 336/336
    điểm ngành trong 21 file reports/ đều bằng 50.0, không một giá trị nào
    khác trong 6 ngày. Ba mục dẫn xuất ("71/71 mã đạt ngưỡng", "TOP 10 tín
    hiệu", "Mã dẫn đầu ngành") vì thế là số bịa.

    Test kiểm HAI điều, vì mỗi điều một mình đều lọt được:
      - khoá tồn tại và mang đúng điểm của mã đó (không phải một số bất kỳ);
      - hai mã điểm khác nhau thì giá trị trả về phải khác nhau (không phải
        một hằng số dùng chung).
    """
    import numpy as np
    import pandas as pd

    import paper_runner as pr

    n = 80
    close = 50_000 * np.power(1.002, np.arange(n))
    df = pd.DataFrame({
        "time": pd.bdate_range("2026-01-01", periods=n).strftime("%Y-%m-%d"),
        "open": close * 0.999, "high": close * 1.006,
        "low": close * 0.994, "close": close,
        "volume": np.full(n, 2_000_000),
    })

    diem = {"AA": 73, "BB": 41}
    pr._analyze = lambda sym, hist, exch="HOSE": make_result(
        diem[sym], sl=float(hist["close"].iloc[-1]) * 0.9,
        tp=float(hist["close"].iloc[-1]) * 1.5)

    j = new_journal()
    row = df.iloc[-1]
    b = {"open": float(row["open"]), "high": float(row["high"]),
         "low": float(row["low"]), "close": float(row["close"])}
    ra = {sym: pr.run_session(j, sym, df, b, str(row["time"]))
          for sym in ("AA", "BB")}

    for sym in ("AA", "BB"):
        assert "final_score" in ra[sym], (
            f"run_session() không trả điểm ra ngoài (mã {sym}) — bên dựng báo "
            f"cáo buộc phải bịa một con số. Khoá có: {sorted(ra[sym])}")
        assert ra[sym]["final_score"] == float(diem[sym]), (
            f"mã {sym}: trả {ra[sym]['final_score']}, đáng lẽ {float(diem[sym])}")

    assert ra["AA"]["final_score"] != ra["BB"]["final_score"], (
        "hai mã điểm khác nhau nhưng trả về cùng một giá trị — vẫn là hằng số")
    print(f"PASS  run_session trả điểm thật: AA={ra['AA']['final_score']}, "
          f"BB={ra['BB']['final_score']}")



# ─────────────────────────────────────────────────────────────────────
# 5. ĐÓNG ĐƯỜNG GHI VÀO SỔ THẬT  (Phase 3A, 3D)
# ─────────────────────────────────────────────────────────────────────
def test_mo_so_that_phai_khai_bao_ro():
    """Mở `paper_trades.db` mà không khai báo thì NỔ.

    Bản cũ: guard_not_real_ledger() chỉ được gọi ở 3/7 script tối ưu, và
    mỗi lần đều truyền HẰNG SỐ tên file scratch — tức nó không bao giờ có
    thể kích hoạt. Nó là lời tự khai, không phải cái cửa.

    KHÔNG gọi ở: optimize_20loops_custom71_18m.py (script sinh ra
    +636,11%), optimize_custom_71stocks_18m.py, optimize_vn100_18m.py,
    walkforward_vn100.py, run_oos_test.py, run_vn100_18m_test.py,
    PaperTradingJournal.__init__, paper_runner.cmd_seed.

    Nay gác nằm TRONG __init__: mọi đường ghi đều phải đi qua, kể cả
    script viết sau này.
    """
    import os
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        duong_dan = os.path.join(d, "paper_trades.db")
        try:
            PaperTradingJournal(duong_dan)
        except pt.ProtectedLedgerError as e:
            assert "paper_trades.db" in str(e)
        else:
            raise AssertionError(
                "mở sổ thật KHÔNG bị chặn — script tối ưu vẫn ghi đè được")

        # Khai báo rõ thì cho qua: người gọi đã nói ra ý định.
        j = PaperTradingJournal(duong_dan, cho_phep_so_that=True)
        j.db.close()
    print("PASS  mở sổ thật phải khai báo cho_phep_so_that=True")


def test_cmd_seed_khong_ghi_duoc_vao_so_that():
    """`paper_runner.py seed` mặc định trỏ vào paper_trades.db.

    Đúng đường đã đi ngày 12/08/2026: ba script tối ưu kết thúc bằng
    os.remove("paper_trades.db") rồi seed lại bằng vòng lãi cao nhất
    trong 20 vòng chạy trên cùng dữ liệu — 96/113 lệnh thật biến mất.
    """
    import argparse
    import os
    import tempfile

    import paper_runner as pr

    with tempfile.TemporaryDirectory() as d:
        args = argparse.Namespace(
            db=os.path.join(d, "paper_trades.db"), symbols="FPT",
            min_history=30, stride=5, buy_threshold=None, no_summary=True)
        try:
            pr.cmd_seed(args)
        except pt.ProtectedLedgerError:
            pass
        else:
            raise AssertionError("cmd_seed ghi thẳng vào sổ thật, không gặp gác")
    print("PASS  cmd_seed bị chặn khi trỏ vào sổ thật")


def test_nang_stop_duoc_ghi_ngay_khong_cho_lenh_dong():
    """Nâng stop phải commit ngay, không chờ có lệnh đóng.

    Bản cũ: `UPDATE trades SET stop_loss=?` chạy, nhưng `commit()` chỉ xảy
    ra khi danh sách `closed` không rỗng. Đóng kết nối là mất. Nặng hơn:
    run_daily.py gọi push() TRƯỚC journal.db.close(), nên Sheets nhận stop
    mới còn DB local rollback về stop cũ — và pull() từ chối ghi đè sổ
    không rỗng, nên hai kho lệch nhau vĩnh viễn.
    """
    import os
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        duong_dan = os.path.join(d, "so_tam.db")
        j = PaperTradingJournal(duong_dan)
        tid = j.consider_entry("T", "2026-01-05", make_result(75), "HOSE")
        j.fill_pending("T", "2026-01-06", 100.0)
        # Giá chạm mốc dời stop, KHÔNG có lệnh nào đóng trong phiên này
        j.evaluate_open("T", "2026-01-07", bar(o=112, h=118, l=111, c=117),
                        current_score=75)
        sl_trong_phien = j.db.execute(
            "SELECT stop_loss FROM trades WHERE id=?", (tid,)).fetchone()[0]
        j.db.close()

        j2 = PaperTradingJournal(duong_dan)
        sl_sau_khi_dong = j2.db.execute(
            "SELECT stop_loss FROM trades WHERE id=?", (tid,)).fetchone()[0]
        j2.db.close()

    assert sl_sau_khi_dong == sl_trong_phien, (
        f"stop trong phiên {sl_trong_phien} nhưng sau khi đóng kết nối còn "
        f"{sl_sau_khi_dong} — lần nâng stop bị rollback")
    print(f"PASS  stop nâng lên {sl_trong_phien:,.1f} sống sót qua đóng kết nối")


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
