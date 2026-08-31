"""Test bất biến cho tầng Safety Harness.

Bất biến: Safety Harness phải NẰM TRÊN đường thực thi, không chỉ tồn tại
trong sơ đồ kiến trúc. Ba quy tắc bất biến của nó:

  R1. Stop-loss > 10%  -> ép giảm tỷ trọng vốn
  R2. Position size > 25%  -> hạ về 20%
  R3. Xu hướng DOWNTREND nhưng điểm > 60  -> phạt 10 điểm (chống bull trap)

Chạy offline:  python3 tests/test_safety_harness.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd

from data_collectors import MarketDataPacket
from debate_agents import SafetyHarnessGuardrails
from master_agent import MasterConsensusAgent


# ─────────────────────────────────────────────────────────────────────
# Dựng dữ liệu giá tất định (không random) để test lặp lại được
# ─────────────────────────────────────────────────────────────────────
def make_df(direction: str, n: int = 120, start_price: float = 100_000.0):
    """Chuỗi giá đi lên hoặc đi xuống đều đặn, không nhiễu."""
    step = {"up": 1.004, "down": 0.996}[direction]
    close = start_price * np.power(step, np.arange(n))
    return pd.DataFrame({
        "time": pd.date_range("2026-01-01", periods=n, freq="B").strftime("%Y-%m-%d"),
        "open": close * 0.999,
        "high": close * 1.005,
        "low": close * 0.995,
        "close": close,
        "volume": np.full(n, 3_000_000),
    })


def make_packet(direction: str, tv: str = "NEUTRAL") -> MarketDataPacket:
    return MarketDataPacket(
        symbol="TEST", exchange="HOSE", ohlcv_df=make_df(direction),
        tv_recommendation=tv, data_quality="OK",
    )


# ─────────────────────────────────────────────────────────────────────
# Tầng 1 — Harness đúng logic khi gọi trực tiếp
# ─────────────────────────────────────────────────────────────────────
def test_harness_phat_diem_khi_downtrend_ma_diem_cao():
    """R3: điểm MUA cao trong DOWNTREND phải bị trừ 10 điểm."""
    h = SafetyHarnessGuardrails()
    out = h.evaluate_safety({"trend": {"trend": "DOWNTREND MẠNH"}}, initial_verdict_score=80.0)
    assert out["adjusted_score"] == 70.0, out
    assert not out["is_safe"]
    assert any("Bull Trap" in v for v in out["safety_violations"])
    print(f"PASS  R3 downtrend+điểm cao: 80 -> {out['adjusted_score']}")


def test_harness_khong_phat_khi_uptrend():
    h = SafetyHarnessGuardrails()
    out = h.evaluate_safety({"trend": {"trend": "UPTREND MẠNH"}}, initial_verdict_score=80.0)
    assert out["adjusted_score"] == 80.0 and out["is_safe"]
    print("PASS  uptrend điểm cao không bị phạt")


def test_harness_chan_stop_loss_va_position_size():
    """R1 + R2: chặn stop-loss quá rộng và tỷ trọng vốn quá lớn."""
    h = SafetyHarnessGuardrails()
    out = h.evaluate_safety(
        {"risk": {"recommendations": {"stop_loss_pct": 15.0,
                                      "suggested_position_size_pct": 40.0}}},
        initial_verdict_score=70.0)
    assert out["safe_position_size"] <= 10.0, out   # R1 ép xuống 10%
    assert not out["is_safe"]
    print(f"PASS  R1 SL 15% -> ép vốn còn {out['safe_position_size']}%")

    out2 = h.evaluate_safety(
        {"risk": {"recommendations": {"stop_loss_pct": 7.0,
                                      "suggested_position_size_pct": 40.0}}},
        initial_verdict_score=70.0)
    assert out2["safe_position_size"] == 20.0, out2  # R2 hạ về 20%
    print(f"PASS  R2 vốn 40% -> hạ còn {out2['safe_position_size']}%")


# ─────────────────────────────────────────────────────────────────────
# Tầng 2 — Harness THỰC SỰ được nối vào pipeline (đây là phần từng thiếu)
# ─────────────────────────────────────────────────────────────────────
def test_pipeline_co_bao_cao_ket_qua_harness():
    """Kết quả trả về phải có mục `safety` — bằng chứng harness đã chạy."""
    result = MasterConsensusAgent().run(make_packet("up"))
    assert "safety" in result, (
        "Thiếu khóa 'safety' — Safety Harness chưa được gọi trong pipeline")
    s = result["safety"]
    for k in ("is_safe", "safe_position_size", "safety_violations"):
        assert k in s, f"thiếu trường {k} trong result['safety']"
    print(f"PASS  pipeline có báo cáo harness: is_safe={s['is_safe']}")


def test_ket_qua_harness_thuc_su_quyet_dinh_diem_cuoi():
    """Test phân biệt: điểm cuối phải LẤY TỪ harness, không phải bỏ qua nó.

    Thay harness bằng bản giả trả điểm cố định. Nếu pipeline vẫn cho ra
    điểm khác => harness bị bỏ qua (đúng lỗi cũ). Test này fail trước khi
    nối harness và pass sau khi nối, nên nó chống tái phạm thật sự.
    """
    class StubHarness:
        NAME = "stub"
        def evaluate_safety(self, analyses, initial_verdict_score):
            self.seen_score = initial_verdict_score
            return {"is_safe": False, "adjusted_score": 12.0,
                    "safe_position_size": 3.0,
                    "safety_violations": ["🧪 Dấu vết từ harness giả"]}

    agent = MasterConsensusAgent()
    stub = StubHarness()
    agent.harness = stub
    result = agent.run(make_packet("up", tv="STRONG_BUY"))

    assert result["final_score"] == 12, (
        f"final_score={result['final_score']} — harness bị bỏ qua, "
        "điểm không đi qua evaluate_safety()")
    assert "BÁN MẠNH" in result["recommendation"], result["recommendation"]
    assert any("harness giả" in r for r in result["key_reasons"]), \
        "vi phạm an toàn không được hiển thị cho người dùng"
    assert "Vốn tối đa (sau Harness): 3.0%" in " ".join(result["key_reasons"])
    assert hasattr(stub, "seen_score"), "harness chưa từng được gọi"
    print(f"PASS  điểm cuối lấy từ harness: {result['final_score']} "
          f"-> {result['recommendation']!r}")


def test_pipeline_downtrend_khong_bao_gio_ra_mua_manh():
    """Bất biến quan trọng nhất: xu hướng giảm không được ra MUA MẠNH.

    Ép điều kiện thuận lợi nhất cho phe mua (TradingView STRONG_BUY)
    trên một chuỗi giá giảm đều — harness phải kéo điểm xuống.
    """
    result = MasterConsensusAgent().run(make_packet("down", tv="STRONG_BUY"))
    rec = result["recommendation"]
    assert "MUA MẠNH" not in rec, (
        f"DOWNTREND vẫn ra {rec!r} (điểm {result['final_score']}) — "
        "harness không chặn được bull trap")
    print(f"PASS  downtrend + TV STRONG_BUY -> {rec!r} ({result['final_score']} điểm)")


def test_diem_luon_trong_khoang_hop_le():
    for direction in ("up", "down"):
        for tv in ("STRONG_BUY", "STRONG_SELL", "NEUTRAL"):
            r = MasterConsensusAgent().run(make_packet(direction, tv=tv))
            assert 5 <= r["final_score"] <= 95, (direction, tv, r["final_score"])
    print("PASS  điểm luôn nằm trong [5, 95] qua 6 tổ hợp")


def test_harness_khong_pha_ket_qua_binh_thuong():
    """Uptrend sạch vẫn phải ra được tín hiệu tích cực — harness không quá tay."""
    result = MasterConsensusAgent().run(make_packet("up", tv="STRONG_BUY"))
    assert result["safety"]["is_safe"], result["safety"]["safety_violations"]
    assert "BÁN" not in result["recommendation"], result["recommendation"]
    print(f"PASS  uptrend sạch -> {result['recommendation']!r} "
          f"({result['final_score']} điểm), không bị phạt oan")


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
