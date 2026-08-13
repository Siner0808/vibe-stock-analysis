"""Test biểu đồ xem lại quyết định của agent.

Điểm cốt lõi: biểu đồ phải TÁCH ĐƯỢC vùng agent đã biết khỏi vùng tương lai.
Nhìn cả biểu đồ liền mạch thì quyết định nào cũng trông hiển nhiên — thiên
lệch nhận thức muộn. Che phần tương lai đi mới đánh giá được chất lượng
quyết định, tách khỏi việc nó lãi hay lỗ.

Chạy offline:  python3 tests/test_trade_review.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd

import market_filter
import trade_review as tr
from paper_trading import PaperTradingJournal, Status

# Ghim bộ lọc VN-INDEX mở: consider_entry() hỏi market_filter, và bộ lọc đó
# đọc cache VNINDEX thật nên kết quả test phụ thuộc hướng thị trường vào
# ngày hardcode — test tự đỏ/xanh theo thị trường mà không ai đụng vào mã.
# File này kiểm thử BIỂU ĐỒ XEM LẠI, không kiểm thử bộ lọc.
market_filter.is_vni_bullish = lambda _signal_date: True


def df_nghin_dong(n: int = 140) -> pd.DataFrame:
    """Giá theo NGHÌN ĐỒNG, đúng như vnstock trả về."""
    c = 71.2 * np.power(1.002, np.arange(n))
    return pd.DataFrame({
        "time": pd.bdate_range("2026-01-01", periods=n).strftime("%Y-%m-%d"),
        "open": c * 0.998, "high": c * 1.006, "low": c * 0.994,
        "close": c, "volume": np.full(n, 2_000_000)})


def make_result(score: int = 75, sl: float = 66_000.0,
                tp: float = 82_000.0, entry: float = 72_000.0) -> dict:
    # `entry_price` là bắt buộc từ khi cỡ lệnh tính theo khoảng cách cắt lỗ
    # (rủi ro cố định 1%/lệnh). Thiếu nó, consider_entry() ném KeyError và
    # cả 7 test ở file này đỏ — cùng nguyên nhân với test_paper_trading.py.
    return {
        "final_score": score, "recommendation": "MUA 📈", "data_quality": "OK",
        "score_breakdown": {"trend_score": 72.0, "momentum_score": 66.0},
        "key_reasons": ["Xu hướng tăng", "Khối lượng tích cực"],
        "safety": {"safe_position_size": 10.0},
        "analyses": {"risk": {"recommendations": {
            "entry_price": entry,
            "stop_loss_price": sl, "take_profit_price": tp,
            "suggested_position_size_pct": 10.0}}}}


def _one_closed_trade():
    """Dựng một lệnh đã đóng trong sổ, giá quy về VNĐ như runner vẫn làm."""
    df = df_nghin_dong()
    j = PaperTradingJournal(":memory:")
    j.consider_entry("FPT", df["time"].iloc[80], make_result())
    j.fill_pending("FPT", df["time"].iloc[81], float(df["open"].iloc[81]) * 1000)
    # Đóng lệnh bằng CẮT LỖ. Trước đây helper này đẩy high lên 90.000 để
    # chạm take_profit 82.000 — chốt lời cứng đã bị gỡ có chủ ý (Fat-Tail,
    # thay bằng trailing stop 7%) nên cách đó không còn đóng lệnh, khiến cả
    # 7 test ở đây đỏ. Cắt lỗ là lệnh chờ đặt sẵn nên khớp ngay trong phiên.
    j.evaluate_open("FPT", df["time"].iloc[95], {
        "open": float(df["open"].iloc[95]) * 1000, "high": 90_000.0,
        "low": 65_000.0,
        "close": float(df["close"].iloc[95]) * 1000})
    return df, j, j.all_trades(Status.CLOSED)[0]


def test_cat_dung_doan_quanh_lenh():
    df, _, t = _one_closed_trade()
    w = tr.slice_around(df, t.signal_date, t.exit_date, before=60, after=20)
    assert not w.empty
    assert t.signal_date in set(w["time"].astype(str))
    assert t.exit_date in set(w["time"].astype(str))
    print(f"PASS  cắt {len(w)} phiên quanh lệnh, chứa cả ngày vào và ra")


def test_bieu_do_quy_gia_ve_vnd():
    """Biểu đồ phải cùng đơn vị với SL/TP, nếu không đường ngưỡng lệch hẳn."""
    df, _, t = _one_closed_trade()
    fig = tr.build_figure(df, t)
    candle = fig.data[0]
    assert candle.type == "candlestick"
    median = float(np.median(candle.close))
    assert 10_000 < median < 500_000, f"giá {median} chưa quy về VNĐ"
    print(f"PASS  biểu đồ nến theo VNĐ (trung vị {median:,.0f})")


def test_co_vung_mo_tach_phan_agent_chua_biet():
    """Đây là điểm quan trọng nhất của biểu đồ này."""
    df, _, t = _one_closed_trade()
    fig = tr.build_figure(df, t)
    rects = [s for s in (fig.layout.shapes or ())
             if getattr(s, "type", None) == "rect"]
    assert rects, "thiếu vùng mờ đánh dấu phần agent chưa biết"
    anns = " ".join(a.text or "" for a in (fig.layout.annotations or ()))
    assert "chưa biết" in anns
    print(f"PASS  có vùng mờ tách phần tương lai ({len(rects)} vùng)")


def test_co_moc_vao_ra_va_nguong():
    df, _, t = _one_closed_trade()
    fig = tr.build_figure(df, t)
    names = [d.name for d in fig.data]
    assert "Vào lệnh" in names and "Đóng lệnh" in names
    anns = " ".join(a.text or "" for a in (fig.layout.annotations or ()))
    assert "Cắt lỗ" in anns and "Chốt lời" in anns
    print("PASS  có mốc vào/ra và ngưỡng cắt lỗ/chốt lời")


def test_boi_canh_lay_nguyen_trang_tu_so():
    """Đọc từ sổ, KHÔNG tính lại.

    Tính lại bằng code hôm nay sẽ cho con số khác nếu logic đã đổi — và
    như vậy thì không còn kiểm tra được quyết định GỐC nữa.
    """
    _, j, t = _one_closed_trade()
    ctx = tr.decision_context(j, t)
    assert ctx["score"] == 75
    assert ctx["components"]["trend_score"] == 72.0
    assert "Xu hướng tăng" in ctx["reasons"]
    print(f"PASS  bối cảnh nguyên trạng từ sổ (điểm {ctx['score']}, "
          f"{len(ctx['reasons'])} lý do)")


def test_thieu_du_lieu_khong_vo():
    _, _, t = _one_closed_trade()
    empty = pd.DataFrame({"time": [], "open": [], "high": [],
                          "low": [], "close": []})
    fig = tr.build_figure(empty, t)
    assert fig.layout.annotations, "phải báo rõ khi không có dữ liệu"
    print("PASS  thiếu dữ liệu giá -> báo rõ, không vỡ")


def test_ket_cuc_noi_ro_la_ket_qua_khong_phai_danh_gia():
    _, _, t = _one_closed_trade()
    s = tr.outcome_summary(t)
    assert "%" in s and ("chốt lời" in s or "cắt lỗ" in s or "hết hạn" in s)
    print(f"PASS  tóm tắt kết cục: {s}")


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
