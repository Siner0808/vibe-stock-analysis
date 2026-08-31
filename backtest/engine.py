"""Engine replay lịch sử — chạy đúng pipeline thật, không look-ahead.

BẤT BIẾN QUAN TRỌNG NHẤT
────────────────────────
Tại ngày T, pipeline CHỈ được nhìn thấy dữ liệu đến hết ngày T.
Cách bảo đảm: cắt DataFrame `df.iloc[:t+1]` TRƯỚC khi đưa vào packet.
Nếu cắt sau (hoặc lọc sau khi tính), backtest sẽ đẹp một cách vô nghĩa.
Xem tests/test_backtest.py::test_khong_co_look_ahead để kiểm chứng.

HẠN CHẾ ĐÃ BIẾT (phải đọc trước khi tin kết quả)
────────────────────────────────────────────────
1. TradingView: không có dữ liệu lịch sử → mọi phiên đều NEUTRAL (tv_bonus=0).
   Backtest này KHÔNG đo được đóng góp của TradingView.
2. Tin tức: không tái dựng được tin cũ → news_packet=None.
   Backtest này đo phần LÕI KỸ THUẬT: trend, momentum, volume, S/R, risk,
   debate council và safety harness.
3. Survivorship bias: chạy trên rổ VN30 hiện tại → lạc quan hơn thực tế.
4. Chi phí giao dịch, trượt giá, thuế: chưa tính.
5. Mẫu chồng lấn: các ngày gần nhau có lợi nhuận tương quan. Dùng `stride`
   để giảm, nhưng không loại bỏ hoàn toàn.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data_collectors import MarketDataPacket   # noqa: E402
from master_agent import MasterConsensusAgent  # noqa: E402

# Nhóm khuyến nghị -> hướng kỳ vọng, dùng để chấm điểm hệ thống
BULLISH = ("MUA MẠNH", "MUA")
BEARISH = ("BÁN MẠNH", "BÁN")


# Điểm thành phần cần theo dõi riêng. Đo cả hệ thống chỉ cho MỘT con số —
# nếu nó bằng 0 thì không biết vì sao. Đo từng thành phần mới biết cái nào
# có tín hiệu, cái nào là nhiễu, và đó mới là thứ hành động được.
COMPONENTS = ("trend_score", "momentum_score", "volume_score",
              "sr_score", "risk_score", "news_score")


@dataclass
class Observation:
    """Một quan sát: hệ thống nói gì tại ngày T, và sau đó giá đi thế nào."""
    symbol: str
    date: str
    score: int
    recommendation: str
    bucket: str                       # MUA MẠNH / MUA / NẮM GIỮ / BÁN / BÁN MẠNH
    components: dict[str, float] = field(default_factory=dict)
    fwd_return: dict[int, float] = field(default_factory=dict)   # horizon -> %
    excess_return: dict[int, float] = field(default_factory=dict)


def _bucket(recommendation: str) -> str:
    for name in ("MUA MẠNH", "BÁN MẠNH", "MUA", "BÁN", "NẮM GIỮ"):
        if name in recommendation:
            return name
    return "KHÁC"


def run_symbol(symbol: str, df: pd.DataFrame, *,
               horizons: tuple[int, ...] = (20, 60),
               min_history: int = 60,
               stride: int = 5,
               agent: MasterConsensusAgent | None = None) -> list[Observation]:
    """Replay một mã. Trả về danh sách quan sát."""
    agent = agent or MasterConsensusAgent()
    max_h = max(horizons)
    close = df["close"].to_numpy(dtype=float)
    obs: list[Observation] = []

    # t chạy từ sau warmup đến khi vẫn còn đủ tương lai để đo
    for t in range(min_history, len(df) - max_h, stride):
        # ── CẮT TRƯỚC KHI TÍNH: đây là dòng chống look-ahead ──────────
        history = df.iloc[: t + 1].reset_index(drop=True)

        packet = MarketDataPacket(
            symbol=symbol, exchange="HOSE", ohlcv_df=history,
            tv_recommendation="NEUTRAL",   # không có TV lịch sử — xem hạn chế (1)
            news_packet=None,              # không có tin cũ — xem hạn chế (2)
            data_quality="OK",
        )
        try:
            result = agent.run(packet)
        except Exception:
            continue

        breakdown = result.get("score_breakdown", {}) or {}
        o = Observation(
            symbol=symbol,
            date=str(df["time"].iloc[t]),
            score=int(result["final_score"]),
            recommendation=result["recommendation"],
            bucket=_bucket(result["recommendation"]),
            components={k: float(breakdown[k]) for k in COMPONENTS
                        if isinstance(breakdown.get(k), (int, float))},
        )
        p0 = close[t]
        if p0 <= 0:
            continue
        for h in horizons:
            o.fwd_return[h] = (close[t + h] - p0) / p0 * 100.0
        obs.append(o)
    return obs


def run_universe(data: dict[str, pd.DataFrame], *,
                 horizons: tuple[int, ...] = (20, 60),
                 min_history: int = 60,
                 stride: int = 5,
                 progress: bool = True) -> list[Observation]:
    """Replay toàn rổ, rồi tính lợi nhuận VƯỢT THỊ TRƯỜNG.

    Lợi nhuận vượt thị trường = lợi nhuận mã đó − lợi nhuận trung bình
    của toàn rổ CÙNG NGÀY. Đây là phần quan trọng: nó tách "hệ thống chọn
    đúng mã" khỏi "thị trường chung đi lên".
    """
    agent = MasterConsensusAgent()
    all_obs: list[Observation] = []
    for i, (sym, df) in enumerate(sorted(data.items()), 1):
        obs = run_symbol(sym, df, horizons=horizons, min_history=min_history,
                         stride=stride, agent=agent)
        all_obs.extend(obs)
        if progress:
            print(f"  [{i}/{len(data)}] {sym}: {len(obs)} quan sát")

    # Trung bình thị trường theo từng ngày, cho từng horizon
    for h in horizons:
        by_date: dict[str, list[float]] = {}
        for o in all_obs:
            if h in o.fwd_return:
                by_date.setdefault(o.date, []).append(o.fwd_return[h])
        market = {d: float(np.mean(v)) for d, v in by_date.items()}
        for o in all_obs:
            if h in o.fwd_return:
                o.excess_return[h] = o.fwd_return[h] - market[o.date]
    return all_obs


def to_frame(obs: list[Observation], horizons: tuple[int, ...] = (20, 60)) -> pd.DataFrame:
    rows = []
    for o in obs:
        row = {"symbol": o.symbol, "date": o.date, "score": o.score,
               "bucket": o.bucket, "recommendation": o.recommendation}
        row.update(o.components)
        for h in horizons:
            row[f"ret_{h}d"] = o.fwd_return.get(h)
            row[f"excess_{h}d"] = o.excess_return.get(h)
        rows.append(row)
    return pd.DataFrame(rows)
