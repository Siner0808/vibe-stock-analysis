"""
experiment_fundamentals.py
──────────────────────────────────────────────────────────────────────
Dữ liệu tài chính có dự báo được lợi nhuận không.

⚠️ GIỚI HẠN LỰC THỐNG KÊ — ĐỌC TRƯỚC KHI DIỄN GIẢI KẾT QUẢ
Gói cộng đồng vnstock chỉ trả 8 quý. Mô phỏng với 50 mã mỗi kỳ:

      IC thật    8 quý    20 quý    40 quý
        0,03       8%       13%       23%
        0,05      12%       31%       52%
        0,10      38%       80%       98%
        0,20      89%      100%      100%

Yếu tố giá trị / chất lượng trong tài liệu học thuật có IC ≈ 0,03–0,05.
Ở mức đó, 8 quý bỏ sót tín hiệu 9 lần trên 10.

Nghĩa là: kết quả "không có tín hiệu" từ script này KHÔNG phải bằng chứng
dữ liệu tài chính vô dụng. Nó chỉ có nghĩa 8 quý không đủ để thấy.
Chỉ kết quả DƯƠNG MẠNH mới mang thông tin — và ngay cả khi đó cũng phải
trừ hao ba thiên lệch bên dưới.

BA THIÊN LỆCH ĐỀU ĐẨY KẾT QUẢ ĐẸP LÊN
  1. Số liệu đã điều chỉnh hồi tố — vnstock trả trạng thái HIỆN TẠI, gồm
     cả sửa đổi sau kiểm toán mà nhà đầu tư lúc đó không thấy.
  2. Thiên lệch sống sót — rổ là ảnh chụp hôm nay; doanh nghiệp phá sản
     hoặc huỷ niêm yết không có mặt, mà đó đúng là nhóm chỉ số xấu lẽ ra
     phải cảnh báo.
  3. Cửa sổ 2024-Q3 → 2026-Q2 nằm trọn trong vùng đã tối ưu.

Điều script này CÓ kiểm soát được: độ trễ công bố. Báo cáo quý kết thúc
30/06 chỉ công bố cuối tháng 7; dùng nó để quyết định ngày 01/07 là nhìn
trộm. Mặc định cộng 45 ngày.

CHẠY
    python fetch_fundamentals.py          # tải trước
    python experiment_fundamentals.py
    python experiment_fundamentals.py --lag 60 --horizon 40
"""
from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from backtest import data as bt_data
from vn100_symbols import VN100_SYMBOLS

FUND = Path(__file__).parent / "backtest" / "fundamentals"

#: Trường lấy từ item_id THẬT của vnstock, đã kiểm tra độ phủ trên 20 mã.
#:
#: KHÔNG dùng `sales` / `gross_profit`: ngân hàng không có doanh thu bán hàng,
#: chỉ 13/20 mã có `gross_profit`. Đưa vào sẽ loại hết nhóm ngân hàng — mà
#: đó lại là nhóm chiếm tỷ trọng lớn nhất rổ VN30. Chỉ giữ trường phủ 20/20.
ROWS = {
    "profit": ["attributable_to_parent_company", "net_profit_loss_after_tax"],
    "eps":    ["eps_basic_vnd"],
    "equity": ["owners_equity", "owner_s_equity"],
    "assets": ["total_assets"],
}


def _find_row(df: pd.DataFrame, keys: list[str]) -> pd.Series | None:
    """Tìm dòng theo item_id hoặc item_en. Trả series theo cột quý."""
    qcols = [c for c in df.columns if isinstance(c, str) and "-Q" in c]
    if not qcols:
        return None
    for col in ("item_id", "item_en", "item"):
        if col not in df.columns:
            continue
        names = df[col].astype(str).str.lower().str.strip()
        for k in keys:
            hit = names[names == k.lower()]
            if len(hit):
                return df.loc[hit.index[0], qcols]
        for k in keys:                       # nới ra: khớp một phần
            hit = names[names.str.contains(k.lower(), regex=False, na=False)]
            if len(hit):
                return df.loc[hit.index[0], qcols]
    return None


def quarter_end(q: str) -> pd.Timestamp | None:
    """'2025-Q3' -> 2025-09-30."""
    try:
        y, qq = q.split("-Q")
        return pd.Timestamp(int(y), int(qq) * 3, 1) + pd.offsets.MonthEnd(0)
    except Exception:
        return None


def load_features(symbol: str) -> pd.DataFrame | None:
    """Bảng đặc trưng cơ bản theo quý cho một mã."""
    inc_p, bal_p = FUND / f"{symbol}_income.csv", FUND / f"{symbol}_balance.csv"
    if not inc_p.exists() or not bal_p.exists():
        return None
    inc, bal = pd.read_csv(inc_p), pd.read_csv(bal_p)

    series = {}
    for name, keys in ROWS.items():
        src = inc if name in ("profit", "eps") else bal
        s = _find_row(src, keys)
        if s is not None:
            series[name] = pd.to_numeric(s, errors="coerce")
    if "profit" not in series or "equity" not in series:
        return None

    q = sorted({c for s in series.values() for c in s.index},
               key=lambda c: (quarter_end(c) or pd.Timestamp.min))
    rows = []
    for i, qq in enumerate(q):
        g = lambda k: (float(series[k].get(qq, np.nan))
                       if k in series else np.nan)
        prof, eps = g("profit"), g("eps")
        eq, ast = g("equity"), g("assets")
        # Lợi nhuận quý nhân 4 để quy về năm — giữ được cả 8 kỳ. Dùng tổng
        # 4 quý gần nhất thì mượt hơn nhưng chỉ còn 5 kỳ, mà số kỳ mới là
        # thứ quyết định lực thống kê ở đây.
        prev = q[i - 4] if i >= 4 else None
        p4 = float(series["profit"].get(prev, np.nan)) if prev else np.nan
        rows.append({
            "symbol": symbol, "quarter": qq, "qend": quarter_end(qq),
            "roe": prof * 4 / eq if eq and eq > 0 else np.nan,
            "roa": prof * 4 / ast if ast and ast > 0 else np.nan,
            "leverage": ast / eq if eq and eq > 0 else np.nan,
            "eps_q": eps if eps == eps else np.nan,
            "growth_profit": (prof / p4 - 1) if p4 and p4 > 0 else np.nan,
        })
    return pd.DataFrame(rows)


def forward_return(df_px, from_date, horizon) -> float | None:
    t = df_px["time"].astype(str)
    idx = t.searchsorted(str(from_date)[:10])
    if idx >= len(df_px) - horizon:
        return None
    c = df_px["close"].astype(float).to_numpy()
    return (c[idx + horizon] / c[idx] - 1) * 100


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lag", type=int, default=45,
                    help="ngày trễ công bố sau khi quý kết thúc")
    ap.add_argument("--horizon", type=int, default=60,
                    help="số phiên nắm giữ để đo lợi nhuận")
    a = ap.parse_args()

    if not FUND.exists():
        print("❌ Chưa có cache. Chạy `python fetch_fundamentals.py` trước.")
        return 1

    feats, missing = [], []
    for s in VN100_SYMBOLS:
        f = load_features(s)
        (feats.append(f) if f is not None else missing.append(s))
    if not feats:
        print("❌ Không đọc được mã nào.")
        return 1
    F = pd.concat(feats, ignore_index=True)
    px = bt_data.load_all(VN100_SYMBOLS)

    print("=" * 86)
    print("DỮ LIỆU TÀI CHÍNH CÓ DỰ BÁO ĐƯỢC LỢI NHUẬN KHÔNG")
    print("=" * 86)
    print(f"Đọc được {F['symbol'].nunique()}/{len(VN100_SYMBOLS)} mã"
          + (f"  (thiếu: {', '.join(missing[:6])}...)" if missing else ""))
    print(f"Quý: {F['quarter'].min()} → {F['quarter'].max()}  "
          f"({F['quarter'].nunique()} kỳ)")
    print(f"Độ trễ công bố: {a.lag} ngày · nắm giữ {a.horizon} phiên\n")

    # ── Ghép với lợi nhuận tương lai tại NGÀY CÔNG BỐ ────────────────
    F["avail"] = F["qend"] + pd.Timedelta(days=a.lag)
    F["fwd"] = [forward_return(px[r.symbol], r.avail, a.horizon)
                if r.symbol in px else None for r in F.itertuples()]

    # Tỷ suất lợi nhuận trên giá (E/P) — yếu tố giá trị kinh điển. Cần giá
    # tại NGÀY CÔNG BỐ, không phải giá hôm nay.
    from data_quality import price_multiplier
    ep = []
    for r in F.itertuples():
        d = px.get(r.symbol)
        if d is None or r.eps_q != r.eps_q:
            ep.append(np.nan); continue
        t = d["time"].astype(str)
        i = t.searchsorted(str(r.avail)[:10])
        if i >= len(d):
            ep.append(np.nan); continue
        p = float(d["close"].iloc[i]) * price_multiplier(d)
        ep.append(r.eps_q * 4 / p if p > 0 else np.nan)
    F["earnings_yield"] = ep

    cols = ["roe", "roa", "leverage", "growth_profit", "earnings_yield"]
    print("Độ phủ từng chỉ số:")
    for c in cols:
        print(f"  {c:<16}{F[c].notna().sum():>5}/{len(F)} quan sát")

    F = F.dropna(subset=["fwd"])
    print(f"\nGhép được {len(F)} quan sát có lợi nhuận tương lai\n")

    # ── Fama-MacBeth: tương quan chéo từng kỳ, rồi lấy TB qua các kỳ ──
    # Không gộp chung tất cả quan sát: trong cùng một kỳ, mọi mã cùng chịu
    # biến động thị trường nên chúng không độc lập. Xếp hạng chéo trong
    # từng kỳ loại bỏ phần chung đó.
    print(f"{'Chỉ số':<16}{'IC TB':>9}{'KTC 95%':>22}{'số kỳ':>8}  kết luận")
    print("─" * 86)
    for c in cols:
        per = []
        for q, g in F.groupby("quarter"):
            g2 = g.dropna(subset=[c])
            if len(g2) < 15:
                continue
            rho = g2[c].rank().corr(g2["fwd"].rank())
            if pd.notna(rho):
                per.append(float(rho))
        if len(per) < 3:
            print(f"{c:<16}{'—':>9}{'không đủ kỳ':>22}{len(per):>8}")
            continue
        m = statistics.mean(per)
        se = statistics.stdev(per) / len(per) ** 0.5 if len(per) > 1 else 0
        tcrit = {3: 4.30, 4: 3.18, 5: 2.78, 6: 2.57, 7: 2.45, 8: 2.36}.get(
            len(per) - 1, 2.1)
        lo, hi = m - tcrit * se, m + tcrit * se
        verdict = ("CÓ tín hiệu dương" if lo > 0 else
                   "CÓ tín hiệu âm" if hi < 0 else "không phân biệt được với 0")
        print(f"{c:<16}{m:>+9.3f}   [{lo:>+7.3f}, {hi:>+7.3f}]{len(per):>8}  {verdict}")

    print("\n" + "=" * 86)
    print("CÁCH ĐỌC — quan trọng hơn chính các con số ở trên")
    print("=" * 86)
    print(f"Chỉ có {F['quarter'].nunique()} kỳ. Ở mức IC thực tế của yếu tố cơ bản")
    print("(0,03–0,05), thiết kế này phát hiện được với xác suất ~10%.")
    print("")
    print("→ Dòng 'không phân biệt được với 0' KHÔNG có nghĩa là chỉ số đó vô")
    print("  dụng. Nó có nghĩa là mẫu quá nhỏ để nói bất cứ điều gì.")
    print("→ Dòng 'CÓ tín hiệu' cũng phải nghi ngờ: số liệu đã điều chỉnh hồi")
    print("  tố, rổ chỉ gồm mã còn sống, và cửa sổ nằm trong vùng đã tối ưu —")
    print("  cả ba đều tạo tín hiệu giả theo chiều dương.")
    print("")
    print("Muốn có câu trả lời thật cần ≥40 quý. Đó là giới hạn gói dữ liệu,")
    print("không phải giới hạn của mã nguồn.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
