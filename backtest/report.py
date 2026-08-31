"""Chấm điểm hệ thống: có tốt hơn ngẫu nhiên và hơn mua-giữ không?

Ba câu hỏi phải trả lời, theo thứ tự khắt khe dần:
  Q1. Nhóm MUA có lợi nhuận cao hơn nhóm BÁN không?
  Q2. Chênh lệch đó có vượt được ngẫu nhiên không? (bootstrap)
  Q3. Sau khi trừ thị trường chung, còn lại gì không? (excess return)

Q3 là câu khó nhất. Trong thị trường tăng, MỌI tín hiệu mua đều có lãi —
điều đó không chứng minh hệ thống có kỹ năng.
"""
from __future__ import annotations

import random
import statistics

import pandas as pd

BULLISH = ("MUA MẠNH", "MUA")
BEARISH = ("BÁN MẠNH", "BÁN")
BUCKET_ORDER = ["MUA MẠNH", "MUA", "NẮM GIỮ", "BÁN", "BÁN MẠNH"]


def bootstrap_diff(a: list[float], b: list[float], iters: int = 5000,
                   seed: int = 0) -> dict:
    """Khoảng tin cậy 95% cho (trung bình a − trung bình b).

    Khoảng chứa 0 => CHƯA đủ bằng chứng kết luận khác nhau.
    """
    if len(a) < 5 or len(b) < 5:
        return {"diff": float("nan"), "ci": (float("nan"), float("nan")),
                "significant": False, "verdict": "không đủ mẫu"}
    rng = random.Random(seed)
    diffs = []
    for _ in range(iters):
        sa = [a[rng.randrange(len(a))] for _ in range(len(a))]
        sb = [b[rng.randrange(len(b))] for _ in range(len(b))]
        diffs.append(statistics.mean(sa) - statistics.mean(sb))
    diffs.sort()
    lo, hi = diffs[int(0.025 * iters)], diffs[int(0.975 * iters)]
    observed = statistics.mean(a) - statistics.mean(b)
    sig = not (lo <= 0 <= hi)
    return {
        "diff": observed,
        "ci": (lo, hi),
        "significant": sig,
        "verdict": ("có ý nghĩa thống kê" if sig
                    else "CHƯA đủ bằng chứng (khoảng tin cậy chứa 0)"),
    }


def _ranks(xs: list[float]) -> list[float]:
    """Thứ hạng trung bình (xử lý giá trị bằng nhau)."""
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def spearman(xs: list[float], ys: list[float]) -> float:
    """Tương quan hạng. Đo 'điểm cao có đi kèm lợi nhuận cao không'."""
    if len(xs) < 3:
        return float("nan")
    rx, ry = _ranks(xs), _ranks(ys)
    mx, my = statistics.mean(rx), statistics.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else float("nan")


def spearman_ci(xs: list[float], ys: list[float], iters: int = 2000,
                seed: int = 0) -> dict:
    """Bootstrap khoảng tin cậy cho tương quan hạng."""
    if len(xs) < 30:
        return {"rho": float("nan"), "ci": (float("nan"), float("nan")),
                "significant": False}
    rng = random.Random(seed)
    n = len(xs)
    vals = []
    for _ in range(iters):
        idx = [rng.randrange(n) for _ in range(n)]
        vals.append(spearman([xs[i] for i in idx], [ys[i] for i in idx]))
    vals = [v for v in vals if v == v]
    vals.sort()
    lo, hi = vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals))]
    return {"rho": spearman(xs, ys), "ci": (lo, hi),
            "significant": not (lo <= 0 <= hi)}


COMPONENT_LABELS = {
    "score": "ĐIỂM TỔNG",
    "trend_score": "Xu hướng",
    "momentum_score": "Động lượng",
    "volume_score": "Khối lượng",
    "sr_score": "Hỗ trợ/Kháng cự",
    "risk_score": "Rủi ro",
    "news_score": "Tin tức",
}


def component_table(df: pd.DataFrame, horizon: int, col: str = "excess") -> pd.DataFrame:
    """Sức dự báo của TỪNG thành phần, không chỉ điểm tổng.

    Điểm tổng cho một con số; nếu nó bằng 0 thì không biết vì sao. Bảng này
    chỉ ra thành phần nào mang tín hiệu và thành phần nào là nhiễu — đó mới
    là thứ hành động được (bỏ bớt, chứ không phải chỉnh trọng số mò).
    """
    field = f"{col}_{horizon}d"
    if field not in df.columns:
        return pd.DataFrame()

    rows = []
    for key, label in COMPONENT_LABELS.items():
        if key not in df.columns:
            continue
        sub = df[[key, field]].dropna()
        if len(sub) < 30:
            continue
        if sub[key].nunique() < 3:
            rows.append({"Thành phần": label, "rho": "—", "KTC 95%": "—",
                         "Kết luận": "không đủ biến thiên để đo"})
            continue
        sc = spearman_ci(sub[key].tolist(), sub[field].tolist())
        rows.append({
            "Thành phần": label,
            "rho": f"{sc['rho']:+.3f}",
            "KTC 95%": f"[{sc['ci'][0]:+.3f}, {sc['ci'][1]:+.3f}]",
            "Kết luận": "CÓ tín hiệu" if sc["significant"] else "không có bằng chứng",
        })
    return pd.DataFrame(rows)


def score_quantile_table(df: pd.DataFrame, horizon: int, col: str = "ret",
                         q: int = 5) -> pd.DataFrame:
    """Chia quan sát theo NGŨ PHÂN VỊ ĐIỂM, xem lợi nhuận từng nhóm.

    Cách đo này độc lập với ngưỡng 78/62/45/30 — nên vẫn dùng được khi
    các ngưỡng đó không bao giờ kích hoạt.
    """
    field = f"{col}_{horizon}d"
    sub = df[["score", field]].dropna()
    if len(sub) < q * 10 or sub["score"].nunique() < q:
        return pd.DataFrame()
    try:
        sub = sub.assign(q=pd.qcut(sub["score"], q, labels=False,
                                   duplicates="drop"))
    except ValueError:
        return pd.DataFrame()
    rows = []
    for qi in sorted(sub["q"].dropna().unique()):
        g = sub[sub["q"] == qi]
        rows.append({
            "Nhóm điểm": f"Q{int(qi) + 1}",
            "Khoảng điểm": f"{g['score'].min():.0f}–{g['score'].max():.0f}",
            "Số quan sát": len(g),
            "TB (%)": round(g[field].mean(), 2),
            "Trung vị (%)": round(g[field].median(), 2),
            "Tỷ lệ thắng": f"{(g[field] > 0).mean():.1%}",
        })
    return pd.DataFrame(rows)


def bucket_table(df: pd.DataFrame, horizon: int, col: str = "ret") -> pd.DataFrame:
    """Thống kê lợi nhuận theo từng nhóm khuyến nghị."""
    field = f"{col}_{horizon}d"
    rows = []
    for b in BUCKET_ORDER:
        sub = df[df["bucket"] == b][field].dropna()
        if len(sub) == 0:
            continue
        rows.append({
            "Nhóm": b,
            "Số quan sát": len(sub),
            "TB (%)": round(sub.mean(), 2),
            "Trung vị (%)": round(sub.median(), 2),
            "Tỷ lệ thắng": f"{(sub > 0).mean():.1%}",
            "Độ lệch chuẩn": round(sub.std(), 2),
        })
    return pd.DataFrame(rows)


def random_baseline(df: pd.DataFrame, horizon: int, col: str = "ret",
                    n_trials: int = 500, seed: int = 0) -> dict:
    """Đường cơ sở: gán nhãn MUA/BÁN NGẪU NHIÊN với cùng tỷ lệ như hệ thống.

    Nếu hệ thống không đánh bại được cái này, nó không có giá trị.
    """
    field = f"{col}_{horizon}d"
    sub = df[[field, "bucket"]].dropna()
    n_bull = int((sub["bucket"].isin(BULLISH)).sum())
    n_bear = int((sub["bucket"].isin(BEARISH)).sum())
    if n_bull < 5 or n_bear < 5:
        return {"mean_gap": float("nan"), "p_value": float("nan"),
                "note": "không đủ mẫu hai phía"}

    values = sub[field].tolist()
    rng = random.Random(seed)
    gaps = []
    for _ in range(n_trials):
        pool = values[:]
        rng.shuffle(pool)
        gaps.append(statistics.mean(pool[:n_bull])
                    - statistics.mean(pool[n_bull:n_bull + n_bear]))

    real_bull = sub[sub["bucket"].isin(BULLISH)][field]
    real_bear = sub[sub["bucket"].isin(BEARISH)][field]
    real_gap = real_bull.mean() - real_bear.mean()
    # p-value một phía: bao nhiêu lần ngẫu nhiên đạt được khoảng cách này?
    p = sum(1 for g in gaps if g >= real_gap) / len(gaps)
    return {
        "real_gap": real_gap,
        "random_gap_mean": statistics.mean(gaps),
        "random_gap_p95": sorted(gaps)[int(0.95 * len(gaps))],
        "p_value": p,
        "beats_random": p < 0.05,
    }


def summarize(df: pd.DataFrame, horizons: tuple[int, ...] = (20, 60)) -> str:
    out: list[str] = []
    add = out.append

    add("=" * 68)
    add("KẾT QUẢ BACKTEST")
    add("=" * 68)
    add(f"Tổng quan sát : {len(df):,}")
    add(f"Số mã         : {df['symbol'].nunique()}")
    add(f"Khoảng thời gian: {df['date'].min()} → {df['date'].max()}")
    add("")
    add("Phân bố khuyến nghị:")
    for b in BUCKET_ORDER:
        n = int((df["bucket"] == b).sum())
        if n:
            add(f"  {b:<10} {n:>6,}  ({n / len(df):>5.1%})")

    s = df["score"]
    add("")
    add(f"Phân bố điểm  : min={s.min():.0f}  Q1={s.quantile(.25):.0f}  "
        f"trung vị={s.median():.0f}  Q3={s.quantile(.75):.0f}  max={s.max():.0f}")

    # Cảnh báo khi một phía hoàn toàn vắng mặt — làm hỏng phép so MUA vs BÁN
    n_bull = int(df["bucket"].isin(BULLISH).sum())
    n_bear = int(df["bucket"].isin(BEARISH).sum())
    if n_bull < 5 or n_bear < 5:
        thieu = "MUA" if n_bull < 5 else "BÁN"
        add("")
        add("⚠️  CẢNH BÁO — KHÔNG THỂ SO SÁNH MUA vs BÁN")
        add(f"    Nhóm {thieu} gần như không xuất hiện "
            f"(MUA={n_bull}, BÁN={n_bear}).")
        add("    Nguyên nhân nhiều khả năng: backtest chạy với tv_bonus = 0")
        add("    (không có dữ liệu TradingView lịch sử), trong khi các ngưỡng")
        add("    78/62/45/30 được đặt khi CÓ tv_bonus ±8. Bỏ phần thưởng đó ra,")
        add("    thang điểm co lại quanh 50 và không bao giờ chạm ngưỡng MUA.")
        add("    → Dùng bảng NGŨ PHÂN VỊ ĐIỂM bên dưới thay thế: nó đo được")
        add("      sức mạnh dự báo của điểm số mà không phụ thuộc ngưỡng.")

    for h in horizons:
        for col, label in (("ret", "LỢI NHUẬN THÔ"),
                           ("excess", "LỢI NHUẬN VƯỢT THỊ TRƯỜNG")):
            field = f"{col}_{h}d"
            if field not in df.columns or df[field].dropna().empty:
                continue
            add("")
            add("─" * 68)
            add(f"{label} — sau {h} phiên")
            add("─" * 68)
            bt = bucket_table(df, h, col)
            if not bt.empty:
                add(bt.to_string(index=False))

            bull = df[df["bucket"].isin(BULLISH)][field].dropna().tolist()
            bear = df[df["bucket"].isin(BEARISH)][field].dropna().tolist()
            if len(bull) >= 5 and len(bear) >= 5:
                r = bootstrap_diff(bull, bear)
                add("")
                add(f"  MUA − BÁN = {r['diff']:+.2f}%  "
                    f"[KTC 95%: {r['ci'][0]:+.2f}%, {r['ci'][1]:+.2f}%]")
                add(f"     → {r['verdict']}")
                rb = random_baseline(df, h, col)
                if rb.get("p_value") == rb.get("p_value"):
                    add(f"  So với cơ sở ngẫu nhiên: p-value = {rb['p_value']:.3f}  "
                        f"{'ĐÁNH BẠI' if rb['beats_random'] else 'KHÔNG đánh bại'}")
            else:
                add("  (bỏ qua so sánh MUA vs BÁN — xem cảnh báo ở đầu báo cáo)")

            # ── Phép đo độc lập với ngưỡng: điểm có dự báo được không? ──
            qt = score_quantile_table(df, h, col)
            if not qt.empty:
                add("")
                add("  Theo NGŨ PHÂN VỊ ĐIỂM (Q1 = điểm thấp nhất, Q5 = cao nhất):")
                add("  " + qt.to_string(index=False).replace("\n", "\n  "))

            sub = df[["score", field]].dropna()
            if len(sub) >= 30:
                sc = spearman_ci(sub["score"].tolist(), sub[field].tolist())
                add("")
                add(f"  Tương quan hạng điểm↔lợi nhuận: rho = {sc['rho']:+.3f}  "
                    f"[KTC 95%: {sc['ci'][0]:+.3f}, {sc['ci'][1]:+.3f}]")
                add(f"     → {'CÓ quan hệ có ý nghĩa' if sc['significant'] else 'KHÔNG có bằng chứng điểm dự báo được lợi nhuận'}")

    # ── Phân rã theo thành phần ───────────────────────────────────────
    for h in horizons:
        ct = component_table(df, h, "excess")
        if ct.empty:
            continue
        add("")
        add("─" * 68)
        add(f"SỨC DỰ BÁO TỪNG THÀNH PHẦN — lợi nhuận vượt thị trường, {h} phiên")
        add("─" * 68)
        add(ct.to_string(index=False))
        signal = ct[ct["Kết luận"] == "CÓ tín hiệu"]["Thành phần"].tolist()
        add("")
        if signal:
            add(f"  → Có tín hiệu: {', '.join(signal)}")
            add("    Các thành phần còn lại chưa chứng minh được giá trị. Cân nhắc")
            add("    giảm trọng số hoặc bỏ, thay vì thêm chỉ báo mới.")
        else:
            add("  → KHÔNG thành phần nào có tín hiệu có ý nghĩa thống kê.")
            add("    Chỉnh trọng số sẽ không cứu được: vấn đề nằm ở bản thân các")
            add("    chỉ báo trên khung thời gian này, không phải ở cách tổng hợp.")

    add("")
    add("=" * 68)
    add("CÁCH ĐỌC")
    add("=" * 68)
    add("• 'Lợi nhuận thô' dương ở nhóm MUA KHÔNG chứng minh hệ thống tốt —")
    add("  trong thị trường tăng thì mọi tín hiệu mua đều có lãi.")
    add("• Chỉ 'lợi nhuận VƯỢT THỊ TRƯỜNG' mới nói lên kỹ năng chọn mã.")
    add("• Nếu khoảng tin cậy chứa 0 → chưa có bằng chứng, đừng tinh chỉnh")
    add("  trọng số dựa trên nó.")
    add("• Chưa trừ phí giao dịch, thuế, trượt giá. Kết quả thực tế sẽ thấp hơn.")
    return "\n".join(out)
