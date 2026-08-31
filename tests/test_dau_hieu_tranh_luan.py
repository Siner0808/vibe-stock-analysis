"""Quy ước DẤU của Debate Council — và một nhánh không thể chạm tới.

`run_debate` cộng `bull_total*0.4 + bear_total*0.4 + devil_adj*0.2`. Phép
cộng đó chỉ đúng nghĩa "hai phe triệt tiêu nhau" khi Bull luôn dương và
Bear luôn âm. Không chỗ nào trong `debate_agents.py` phát biểu quy ước đó
thành lời, nên nó có thể bị phá bởi một lần sửa vô tình — và khi bị phá,
kết quả vẫn TRÔNG hợp lý: điểm vẫn nằm trong ±8, không ai nổ.

Hệ quả đã đo được: dòng `if bull_total < 0: key_risks.append(...)` ở
`run_debate` KHÔNG THỂ chạy. Bull cộng vô điều kiện +0,5 ở vòng 2 và
+1,0 ở vòng 3, còn mọi nhánh khác của nó chỉ có `impact +=`. Sàn cấu
trúc của `bull_total` là +1,5. Đo 262 lượt tranh luận thật trên 40 mã
ngày 28/08/2026: `bull_score` thấp nhất = +1,50, không lượt nào âm.

Dòng chết đó đã được gỡ. Test này giữ cho lý do gỡ nó còn đúng.
"""
import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from debate_agents import (BearAdvocateAgent, BullAdvocateAgent,
                           DevilsAdvocateAgent)

SAN_BULL = 1.5   # +0,5 (vòng 2) + 1,0 (vòng 3), cộng vô điều kiện


def _luoi():
    """Mọi tổ hợp bật/tắt của các nhánh mà Bull và Bear đọc."""
    for (t, ms, vs, pos, rs, ns, vr, rsi) in itertools.product(
            ("STRONG_UPTREND", "DOWNTREND", "SIDEWAYS"),
            ("STRONG_BUY", "SELL", ""),
            ("CONFIRM", "STRONG", ""),
            ("Gần vùng HỖ TRỢ", ""),
            (10, 80),
            ("POSITIVE", "NEGATIVE", ""),
            (0.4, 1.6),
            (25.0, 80.0)):
        yield {
            "trend": {"trend": t, "trend_strength": "MẠNH"},
            "momentum": {"momentum_signal": ms,
                         "indicators_summary": {"RSI": rsi}},
            "volume": {"volume_signal": vs,
                       "stats": {"vol_ratio_vs_ma20": vr}},
            "support_resistance": {"position": pos,
                                   "levels": {"support_1": 20000.0}},
            "risk": {"risk_score": rs,
                     "metrics": {"max_drawdown": 30.0, "sharpe_ratio": 1.2,
                                 "volatility_annual": 40.0},
                     "recommendations": {}},
            "news": {"overall_sentiment": ns},
        }


def _ba_vong(agent, a, doi_thu):
    """Tổng ba vòng của một phe, dùng đúng lịch sử mà `run_debate` dựng."""
    lich_su = []
    tong = 0.0
    for vong in (1, 2, 3):
        r = (agent.argue(a, round_num=vong, bear_prev=doi_thu)
             if isinstance(agent, BullAdvocateAgent)
             else agent.argue(a, round_num=vong, bull_prev=doi_thu))
        lich_su.append(r)
        tong += r.score_impact
    return tong


def test_bull_khong_bao_gio_am():
    """Bull chỉ được phép lập luận theo chiều DƯƠNG."""
    bull, bear = BullAdvocateAgent(), BearAdvocateAgent()
    thap_nhat = None
    for a in _luoi():
        doi_thu = [bear.argue(a, round_num=1, bull_prev=[])]
        tong = _ba_vong(bull, a, doi_thu)
        thap_nhat = tong if thap_nhat is None else min(thap_nhat, tong)
    assert thap_nhat is not None
    assert thap_nhat >= SAN_BULL, (
        f"bull_total chạm {thap_nhat:+.2f}, thấp hơn sàn {SAN_BULL:+.2f}. "
        f"Quy ước dấu đã bị phá: phép cộng trong run_debate không còn "
        f"nghĩa 'hai phe triệt tiêu nhau'.")


def test_bear_khong_bao_gio_duong():
    """Bear chỉ được phép lập luận theo chiều ÂM."""
    bull, bear = BullAdvocateAgent(), BearAdvocateAgent()
    cao_nhat = None
    for a in _luoi():
        doi_thu = [bull.argue(a, round_num=1, bear_prev=[])]
        tong = _ba_vong(bear, a, doi_thu)
        cao_nhat = tong if cao_nhat is None else max(cao_nhat, tong)
    assert cao_nhat is not None
    assert cao_nhat <= 0.0, (
        f"bear_total chạm {cao_nhat:+.2f}. Bear đang cộng điểm dương — "
        f"cộng nó vào bull_total sẽ khuếch đại thay vì triệt tiêu.")


def test_devil_khong_bao_gio_duong():
    """Devil's Advocate là phía phản biện: chỉ trừ, không cộng."""
    bull, bear, devil = (BullAdvocateAgent(), BearAdvocateAgent(),
                         DevilsAdvocateAgent())
    cao_nhat = None
    for a in _luoi():
        b = [bull.argue(a, round_num=1, bear_prev=[])]
        r = [bear.argue(a, round_num=1, bull_prev=[])]
        d = devil.challenge(a, b, r).score_impact
        cao_nhat = d if cao_nhat is None else max(cao_nhat, d)
    assert cao_nhat is not None
    assert cao_nhat <= 0.0, f"devil_adj chạm {cao_nhat:+.2f} — phải luôn ≤ 0."


def test_nhanh_bull_am_khong_duoc_quay_lai():
    """Dòng `if bull_total < 0` đã bị gỡ vì không thể chạm tới.

    Nếu nó quay lại mà quy ước dấu vẫn như cũ thì đó lại là một cảnh báo
    không bao giờ nổ — đúng thứ dự án này gọi là 'silent pass'.
    """
    import ast
    import pathlib

    src = (pathlib.Path(__file__).resolve().parent.parent
           / "debate_agents.py").read_text(encoding="utf-8")
    for n in ast.walk(ast.parse(src)):
        if not isinstance(n, ast.Compare):
            continue
        trai = n.left
        if isinstance(trai, ast.Name) and trai.id == "bull_total":
            for op, phai in zip(n.ops, n.comparators):
                if (isinstance(op, (ast.Lt, ast.LtE))
                        and isinstance(phai, ast.Constant)
                        and isinstance(phai.value, (int, float))
                        and phai.value <= SAN_BULL):
                    raise AssertionError(
                        f"debate_agents.py dòng {n.lineno}: so bull_total "
                        f"với {phai.value} — sàn của nó là +{SAN_BULL}, "
                        f"nhánh này không bao giờ chạy.")
