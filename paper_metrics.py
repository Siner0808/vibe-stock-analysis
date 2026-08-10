"""
paper_metrics.py
──────────────────────────────────────────────────────────────────────
Chấm điểm sổ lệnh giấy.

Câu hỏi phải trả lời, theo thứ tự khắt khe dần:
  1. Kỳ vọng mỗi lệnh có dương không? (sau phí)
  2. Con số đó có vượt được ngẫu nhiên không?
  3. Có hơn việc chỉ cầm đều cả rổ không?

Câu 3 là câu quyết định. Lãi 8% khi VN-INDEX tăng 12% là THUA — và đây
đúng là cái bẫy đã gặp ở backtest: thị trường tăng làm mọi thứ trông đẹp.
"""
from __future__ import annotations

import random
import statistics
from dataclasses import dataclass

from paper_trading import BROKER_FEE_PCT, SELL_TAX_PCT, ExitReason, Trade

ROUND_TRIP_COST_PCT = (BROKER_FEE_PCT * 2 + SELL_TAX_PCT) * 100


@dataclass
class Performance:
    n_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    expectancy: float          # kỳ vọng mỗi lệnh, sau phí (%)
    profit_factor: float
    total_net_pct: float       # tổng lợi nhuận cộng dồn theo tỷ trọng
    max_drawdown_pct: float
    by_exit_reason: dict[str, int]

    def summary(self) -> str:
        return (f"{self.n_trades} lệnh · thắng {self.win_rate:.0%} · "
                f"kỳ vọng {self.expectancy:+.2f}%/lệnh · "
                f"PF {self.profit_factor:.2f} · DD tối đa {self.max_drawdown_pct:.1f}%")


def _returns(trades: list[Trade]) -> list[float]:
    return [t.net_return_pct() for t in trades
            if t.status == "CLOSED" and t.net_return_pct() is not None]


def compute(trades: list[Trade]) -> Performance | None:
    rets = _returns(trades)
    if not rets:
        return None

    wins = [r for r in rets if r > 0]
    losses = [r for r in rets if r <= 0]
    gross_win = sum(wins)
    gross_loss = abs(sum(losses))

    # Đường vốn: mỗi lệnh đóng góp theo tỷ trọng vốn của nó.
    #
    # PHẢI sắp theo NGÀY ĐÓNG LỆNH. Danh sách lấy từ sổ mặc định xếp theo id,
    # tức thứ tự chèn: hết toàn bộ lệnh của mã A rồi mới tới mã B. Dựng đường
    # vốn theo thứ tự đó cho ra một chuỗi lãi/lỗ chưa từng tồn tại, và
    # drawdown tính từ nó không phải mức sụt giảm tài khoản thật sự chịu.
    # Đo trên rổ 50 mã: 23,0% theo id so với 30,7% theo thời gian.
    closed = [t for t in trades if t.status == "CLOSED"
              and t.net_return_pct() is not None]
    
    # Sắp xếp lệnh theo thời điểm ĐÓNG LỆNH để tính chính xác MaxDD theo thời gian
    closed.sort(key=lambda x: x.exit_date or "")
    
    equity, peak, max_dd = 100.0, 100.0, 0.0
    for t in closed:
        equity *= 1 + (t.net_return_pct() / 100) * (t.size_pct / 100)
        peak = max(peak, equity)
        max_dd = max(max_dd, (peak - equity) / peak * 100)

    reasons: dict[str, int] = {}
    for t in closed:
        reasons[t.exit_reason or "?"] = reasons.get(t.exit_reason or "?", 0) + 1

    return Performance(
        n_trades=len(rets),
        win_rate=len(wins) / len(rets),
        avg_win=statistics.mean(wins) if wins else 0.0,
        avg_loss=statistics.mean(losses) if losses else 0.0,
        expectancy=statistics.mean(rets),
        profit_factor=(gross_win / gross_loss) if gross_loss else float("inf"),
        total_net_pct=equity - 100.0,
        max_drawdown_pct=max_dd,
        by_exit_reason=reasons,
    )


def expectancy_significant(trades: list[Trade], iters: int = 5000,
                           seed: int = 0) -> dict:
    """Kỳ vọng dương có phải may rủi không? Bootstrap khoảng tin cậy.

    Khoảng chứa 0 => chưa đủ bằng chứng. Với 20-30 lệnh thì gần như chắc
    chắn sẽ chứa 0 — đó là lý do cần vài trăm lệnh trước khi kết luận.
    """
    rets = _returns(trades)
    if len(rets) < 10:
        return {"expectancy": None, "ci": (None, None), "significant": False,
                "verdict": f"mới {len(rets)} lệnh, chưa đủ để kết luận"}
    rng = random.Random(seed)
    means = []
    for _ in range(iters):
        sample = [rets[rng.randrange(len(rets))] for _ in range(len(rets))]
        means.append(statistics.mean(sample))
    means.sort()
    lo, hi = means[int(0.025 * iters)], means[int(0.975 * iters)]
    sig = lo > 0
    return {
        "expectancy": statistics.mean(rets),
        "ci": (lo, hi),
        "significant": sig,
        "verdict": ("kỳ vọng dương có ý nghĩa thống kê" if sig else
                    "CHƯA đủ bằng chứng kỳ vọng dương (khoảng tin cậy chứa 0)"),
    }


def vs_benchmark(trades: list[Trade],
                 benchmark_return_by_period: dict[tuple[str, str], float]) -> dict:
    """So từng lệnh với việc cầm CHUẨN trong CÙNG khoảng thời gian.

    benchmark_return_by_period: {(ngày_vào, ngày_ra): % thay đổi của chuẩn}

    Đây là phép đo quyết định. Không có nó, một thị trường tăng sẽ khiến
    mọi hệ thống trông như thiên tài.
    """
    diffs = []
    for t in trades:
        if t.status != "CLOSED" or t.net_return_pct() is None:
            continue
        key = (t.entry_date or "", t.exit_date or "")
        bench = benchmark_return_by_period.get(key)
        if bench is None:
            continue
        diffs.append(t.net_return_pct() - bench)

    if len(diffs) < 10:
        return {"n": len(diffs), "alpha": None,
                "verdict": f"mới {len(diffs)} lệnh có đối chiếu, chưa đủ"}

    rng = random.Random(0)
    means = []
    for _ in range(5000):
        s = [diffs[rng.randrange(len(diffs))] for _ in range(len(diffs))]
        means.append(statistics.mean(s))
    means.sort()
    lo, hi = means[125], means[4874]
    return {
        "n": len(diffs),
        "alpha": statistics.mean(diffs),
        "ci": (lo, hi),
        "significant": not (lo <= 0 <= hi),
        "verdict": ("VƯỢT chuẩn có ý nghĩa" if lo > 0 else
                    "THUA chuẩn có ý nghĩa" if hi < 0 else
                    "không khác chuẩn một cách có ý nghĩa"),
    }


def report(trades: list[Trade],
           benchmark: dict[tuple[str, str], float] | None = None) -> str:
    out: list[str] = []
    add = out.append
    add("=" * 64)
    add("SỔ LỆNH GIẤY CỦA AGENT")
    add("=" * 64)

    perf = compute(trades)
    n_open = sum(1 for t in trades if t.status in ("OPEN", "PENDING"))
    if perf is None:
        add(f"Chưa có lệnh nào đóng. Đang mở/chờ: {n_open}")
        return "\n".join(out)

    add(f"Đã đóng   : {perf.n_trades} lệnh   |  Đang mở/chờ: {n_open}")
    add(f"Tỷ lệ thắng: {perf.win_rate:.1%}")
    add(f"Lãi TB    : {perf.avg_win:+.2f}%   |  Lỗ TB: {perf.avg_loss:+.2f}%")
    add(f"Kỳ vọng   : {perf.expectancy:+.2f}% mỗi lệnh (đã trừ "
        f"{ROUND_TRIP_COST_PCT:.2f}% phí)")
    add(f"Profit factor: {perf.profit_factor:.2f}")
    add(f"Lợi nhuận cộng dồn: {perf.total_net_pct:+.2f}%")
    add(f"Sụt giảm tối đa   : {perf.max_drawdown_pct:.1f}%")
    add("")
    add("Lý do đóng lệnh:")
    labels = {ExitReason.STOP_LOSS: "Chạm cắt lỗ",
              ExitReason.TAKE_PROFIT: "Chạm chốt lời",
              ExitReason.SIGNAL_REVERSED: "Tín hiệu đảo chiều",
              ExitReason.MAX_HOLD: "Hết hạn nắm giữ"}
    for k, v in sorted(perf.by_exit_reason.items(), key=lambda x: -x[1]):
        add(f"  {labels.get(k, k):<22} {v:>4}  ({v / perf.n_trades:.0%})")

    add("")
    sig = expectancy_significant(trades)
    add("─" * 64)
    if sig["expectancy"] is not None:
        add(f"Kỳ vọng {sig['expectancy']:+.2f}%  "
            f"[KTC 95%: {sig['ci'][0]:+.2f}%, {sig['ci'][1]:+.2f}%]")
    add(f"  → {sig['verdict']}")

    if benchmark:
        b = vs_benchmark(trades, benchmark)
        add("")
        if b.get("alpha") is not None:
            add(f"So với cầm đều cả rổ cùng kỳ: {b['alpha']:+.2f}%/lệnh  "
                f"[{b['ci'][0]:+.2f}%, {b['ci'][1]:+.2f}%]")
        add(f"  → {b['verdict']}")
    else:
        add("")
        add("⚠️ Chưa có đối chiếu chuẩn. Con số ở trên KHÔNG nói lên được gì")
        add("   cho tới khi biết thị trường chung đi thế nào trong cùng kỳ.")

    add("")
    add("=" * 64)
    add("CÁCH ĐỌC")
    add("=" * 64)
    add("• Dưới ~100 lệnh, mọi kết luận đều mong manh. Kiên nhẫn.")
    add("• Kỳ vọng dương mà khoảng tin cậy chứa 0 = chưa biết gì.")
    add("• Chỉ so với chuẩn mới tách được kỹ năng chọn mã khỏi xu hướng chung.")
    add("• Sổ này chỉ đo TÍN HIỆU. Giao dịch thật còn có trượt giá, khớp")
    add("  một phần và tâm lý — kết quả thực tế sẽ thấp hơn.")
    return "\n".join(out)
