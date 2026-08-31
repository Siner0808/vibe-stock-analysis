"""Test bất biến cho cổng chất lượng dữ liệu.

Bất biến quan trọng nhất của dự án:
    KHÔNG BAO GIỜ đưa ra khuyến nghị mua/bán từ dữ liệu không đáng tin.

Chạy offline, không cần mạng, không cần API key:
    python3 tests/test_data_quality_gate.py
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_collectors import MarketDataPacket, VNStockCollectorAgent
from master_agent import MasterConsensusAgent

# Các chuỗi biểu thị một lời khuyên hành động — không được xuất hiện
# khi dữ liệu không đáng tin.
ACTION_WORDS = ["MUA", "BÁN", "NẮM GIỮ"]


def _packet(quality: str) -> MarketDataPacket:
    return MarketDataPacket(symbol="FPT", exchange="HOSE", data_quality=quality)


def test_du_lieu_mo_phong_khong_ra_khuyen_nghi():
    """SYNTHETIC = random walk => tuyệt đối không được ra tín hiệu mua/bán."""
    result = MasterConsensusAgent().run(_packet("SYNTHETIC"))
    rec = result["recommendation"]
    assert "MÔ PHỎNG" in rec, f"phải nói rõ là dữ liệu mô phỏng, nhận: {rec!r}"
    for w in ACTION_WORDS:
        assert w not in rec, f"khuyến nghị {w!r} bị rò rỉ từ dữ liệu giả: {rec!r}"
    assert "NGẪU NHIÊN" in result["key_reasons"][0]
    print(f"PASS  SYNTHETIC bị chặn -> {rec!r}")


def test_du_lieu_that_bai_khong_ra_khuyen_nghi():
    result = MasterConsensusAgent().run(_packet("FAILED"))
    rec = result["recommendation"]
    assert "KHÔNG KHẢ DỤNG" in rec
    for w in ACTION_WORDS:
        assert w not in rec, f"khuyến nghị {w!r} bị rò rỉ: {rec!r}"
    print(f"PASS  FAILED bị chặn -> {rec!r}")


def test_fallback_generator_bao_dung_status():
    """Bộ sinh dữ liệu dự phòng phải tự khai báo là SYNTHETIC, không phải OK.

    Ép nhánh fallback bằng cách thay `vnstock` bằng module giả luôn trả rỗng
    — mô phỏng đúng tình huống nguồn dữ liệu chết. Không cần mạng.
    """
    import types

    import pandas as pd

    fake = types.ModuleType("vnstock")

    class _EmptyQuote:
        def __init__(self, *a, **kw): pass
        def history(self, *a, **kw): return pd.DataFrame()

    fake.Quote = _EmptyQuote
    saved = sys.modules.get("vnstock")
    sys.modules["vnstock"] = fake
    try:
        res = VNStockCollectorAgent().collect("FPT", "2026-01-01", "2026-03-01")
    finally:
        if saved is None:
            sys.modules.pop("vnstock", None)
        else:
            sys.modules["vnstock"] = saved

    assert res["status"] == "SYNTHETIC", (
        f"fallback phải báo SYNTHETIC, nhận {res['status']!r} — "
        "đây là lỗi khiến dữ liệu giả bị coi là thật")
    assert "MÔ PHỎNG" in res["note"]
    assert not res["df"].empty
    print(f"PASS  nguồn chết -> fallback tự khai báo status={res['status']!r}")


def test_nguon_chet_thi_toan_pipeline_tu_choi_khuyen_nghi():
    """Kiểm chứng đầu-cuối: nguồn giá chết => không có tín hiệu mua/bán nào thoát ra."""
    import types

    import pandas as pd

    fake = types.ModuleType("vnstock")

    class _EmptyQuote:
        def __init__(self, *a, **kw): pass
        def history(self, *a, **kw): return pd.DataFrame()

    fake.Quote = _EmptyQuote
    saved = sys.modules.get("vnstock")
    sys.modules["vnstock"] = fake
    try:
        from data_collectors import DataOrchestrator
        packet = DataOrchestrator("FPT", "2026-01-01", "2026-03-01",
                                  collect_news=False).collect_and_handoff()
        result = MasterConsensusAgent().run(packet)
    finally:
        if saved is None:
            sys.modules.pop("vnstock", None)
        else:
            sys.modules["vnstock"] = saved

    assert packet.data_quality == "SYNTHETIC", packet.data_quality
    for w in ACTION_WORDS:
        assert w not in result["recommendation"], (
            f"khuyến nghị {w!r} thoát ra từ dữ liệu ngẫu nhiên: "
            f"{result['recommendation']!r}")
    print(f"PASS  end-to-end: nguồn chết -> {result['recommendation']!r}")


def test_khong_con_key_hardcode_trong_ma_nguon():
    """Chống tái phạm: không được nhúng API key vào mã nguồn."""
    import chatbot_agent

    assert not hasattr(chatbot_agent, "DEFAULT_GEMINI_KEY"), \
        "DEFAULT_GEMINI_KEY đã quay lại — key không được nằm trong mã nguồn"
    assert hasattr(chatbot_agent, "load_system_api_key")

    # Bắt cả kiểu nhúng thẳng lẫn kiểu chẻ chuỗi rồi nối lại để né grep
    src = open(chatbot_agent.__file__, encoding="utf-8").read()
    assert "_K_PARTS" not in src, "kiểu chẻ chuỗi để giấu key đã quay lại"

    # Credential có entropy cao: dài, lẫn HOA/thường VÀ có chữ số.
    # Tên biến/khoá dict kiểu snake_case không thoả cả ba nên không báo nhầm.
    suspicious = [
        s for s in re.findall(r"""["']([A-Za-z0-9_\-.]{25,})["']""", src)
        if any(c.isupper() for c in s)
        and any(c.islower() for c in s)
        and any(c.isdigit() for c in s)
    ]
    assert not suspicious, f"chuỗi khả nghi giống credential: {suspicious[:2]}"

    # Không có key cấu hình => agent phải để api_key None, không tự bịa
    saved = {k: os.environ.pop(k, None) for k in ("GEMINI_API_KEY", "GOOGLE_API_KEY")}
    try:
        assert chatbot_agent.StockChatbotAgent().api_key is None
    finally:
        for k, v in saved.items():
            if v is not None:
                os.environ[k] = v
    print("PASS  không còn key hardcode, thiếu key thì để None")


def test_khong_tai_sinh_post_mortem_gia():
    """Chống tái phạm: tầng 'tự học' giả không được quay lại.

    Bản cũ tăng trọng số Bear sau mỗi lần thua gần đây — đó là học theo
    chế độ thị trường vừa qua, không phải học quy luật. Chỉ được bật lại
    khi đã có backtest và cơ chế phát hiện thị trường đảo chiều.
    """
    import debate_agents
    import master_agent as ma

    assert not hasattr(debate_agents, "PostMortemLearningAgent"), (
        "PostMortemLearningAgent đã quay lại — đọc ghi chú cuối debate_agents.py")
    assert not hasattr(ma.MasterConsensusAgent(), "post_mortem"), \
        "post_mortem được nối lại vào pipeline mà chưa có backtest"
    print("PASS  không có tầng tự-học giả trong pipeline")


def test_thieu_key_van_tra_loi_duoc_bang_engine_noi_bo():
    """Bỏ key hệ thống không được làm hỏng chatbot — phải rơi về fallback."""
    from chatbot_agent import StockChatbotAgent

    result = {
        "symbol": "FPT", "exchange": "HOSE", "final_score": 72,
        "recommendation": "MUA 📈", "data_quality": "OK",
        "score_breakdown": {"trend_score": 70}, "key_reasons": ["Xu hướng tăng"],
        "analyses": {},
    }
    saved = {k: os.environ.pop(k, None) for k in ("GEMINI_API_KEY", "GOOGLE_API_KEY")}
    try:
        answer = StockChatbotAgent(api_key=None).answer_question(
            "Tại sao lại khuyến nghị như vậy?", result)
    finally:
        for k, v in saved.items():
            if v is not None:
                os.environ[k] = v

    assert "FPT" in answer and len(answer) > 50
    assert "Internal Engine" in answer, "phải dùng engine nội bộ khi không có key"
    print("PASS  thiếu key vẫn trả lời được bằng engine nội bộ")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"\n===== {len(fns)}/{len(fns)} test PASS =====")
