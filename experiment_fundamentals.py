"""
experiment_fundamentals.py
──────────────────────────────────────────────────────────────────────
Dữ liệu tài chính có dự báo được lợi nhuận không.

⚠️ GIỚI HẠN LỰC THỐNG KÊ — ĐỌC TRƯỚC KHI DIỄN GIẢI KẾT QUẢ
Mô phỏng với 50 mã mỗi kỳ:

      IC thật    8 quý    20 quý    40 quý
        0,03       8%       13%       23%
        0,05      12%       31%       52%
        0,10      38%       80%       98%
        0,20      89%      100%      100%

Yếu tố giá trị / chất lượng trong tài liệu học thuật có IC ≈ 0,03–0,05.

SỐ KỲ THẬT SỰ DÙNG ĐƯỢC KHÔNG PHẢI SỐ KỲ TẢI VỀ. Từ 23/08/2026 cache BCTC
có 34 kỳ (2018-Q1 → 2026-Q2, hạng silver), nhưng cache GIÁ chỉ lùi tới
2021-10 / 2022-01. Quý nào không có giá tương ứng thì bị loại — còn **19
kỳ**. Ở 19 kỳ, lực phát hiện với IC = 0,05 vào khoảng 30%.

Nghĩa là: kết quả "không có tín hiệu" từ script này KHÔNG phải bằng chứng
dữ liệu tài chính vô dụng. Nó chỉ có nghĩa mẫu chưa đủ để thấy.
Chỉ kết quả DƯƠNG MẠNH mới mang thông tin — và ngay cả khi đó cũng phải
trừ hao ba thiên lệch bên dưới.

NĂM CHỈ SỐ ĐƯỢC KIỂM CÙNG LÚC. Xác suất ít nhất một chỉ số vượt ngưỡng 95%
do MAY là 1 − 0,95⁵ = 23%. Cột "kết luận" bên dưới KHÔNG sửa cho việc đó —
một dòng "CÓ tín hiệu" đơn lẻ chưa đủ. Sửa theo Bonferroni (α = 0,01) đo
ngày 23/08/2026: **không chỉ số nào còn loại được số 0.**

BA THIÊN LỆCH ĐỀU ĐẨY KẾT QUẢ ĐẸP LÊN
  1. Số liệu đã điều chỉnh hồi tố — vnstock trả trạng thái HIỆN TẠI, gồm
     cả sửa đổi sau kiểm toán mà nhà đầu tư lúc đó không thấy.
  2. Thiên lệch sống sót — rổ là ảnh chụp hôm nay; doanh nghiệp phá sản
     hoặc huỷ niêm yết không có mặt, mà đó đúng là nhóm chỉ số xấu lẽ ra
     phải cảnh báo. Thiên lệch này cắn MẠNH NHẤT vào `leverage`: doanh
     nghiệp vay nhiều mà chết thì không có trong rổ, nên đòn bẩy trông
     giống một điều tốt.
  3. Cửa sổ dùng được (2021-Q4 → 2026-Q1) nằm trọn trong vùng đã tối ưu.

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

# Console Windows mặc định cp1258, không mã hoá nổi tiếng Việt. Thiếu dòng
# này thì script chết ngay ở dòng tiêu đề, TRƯỚC khi kịp đo bất cứ thứ gì —
# cùng quy ước với run_daily.py, fetch_fundamentals.py và các script khác.
sys.stdout.reconfigure(encoding="utf-8")

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


#: t hai phía, mức 95%, tra theo BẬC TỰ DO (df = n − 1). Khoá là df, không
#: phải n — bản trước tra bằng `n - 1` trên một bảng mà khoá là `n`, nên
#: luôn dùng t của df = n − 2.
_T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447,
        7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179,
        13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101,
        19: 2.093, 20: 2.086, 21: 2.080, 22: 2.074, 23: 2.069, 24: 2.064,
        25: 2.060, 26: 2.056, 27: 2.052, 28: 2.048, 29: 2.045, 30: 2.042,
        40: 2.021, 60: 2.000, 120: 1.980}


def t_crit_95(n: int) -> float:
    """t hai phía 95% cho n quan sát.

    Ngoài bảng thì lấy mốc df LỚN NHẤT còn ≤ df thật, tức luôn nghiêng về
    phía t LỚN hơn — khoảng tin cậy rộng hơn, khó tuyên bố "có tín hiệu"
    hơn. Hằng số 2,1 của bản trước đi ngược hướng đó: với n = 10 (df = 9)
    t thật là 2,262, dùng 2,1 làm khoảng hẹp lại 7%.
    """
    df = max(int(n) - 1, 1)
    if df in _T95:
        return _T95[df]
    moc = [k for k in _T95 if k <= df]
    return _T95[max(moc)] if moc else _T95[1]


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


def truoc_khi_co_gia(df_px, from_date) -> bool:
    """Ngày hỏi nằm TRƯỚC phiên đầu tiên có trong cache giá.

    `searchsorted` trả 0 cho mọi ngày sớm hơn dữ liệu, nên không có phép
    kiểm này thì một quý 2018 nhận đúng lợi nhuận 60 phiên đầu tiên của
    cache — và MỌI quý trước ngày đó nhận CÙNG một con số.

    Đo trên FPT (cache bắt đầu 2021-10-14) ngày 23/08/2026:

        2018-05-15 -> −5,478%
        2019-08-14 -> −5,478%     ← cùng một con số
        2021-06-01 -> −5,478%     ← cùng một con số

    Lỗi này ngủ yên khi cache BCTC chỉ lùi tới 2024-Q3. Làm mới lên 34 kỳ
    (2018-Q1) là đánh thức nó: 14/33 kỳ trong phép đo thành bản sao của
    một cửa sổ giá duy nhất, ghép với số liệu tài chính của bốn năm trước.
    """
    return str(from_date)[:10] < str(df_px["time"].iloc[0])[:10]


def forward_return(df_px, from_date, horizon) -> float | None:
    if truoc_khi_co_gia(df_px, from_date):
        return None
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
        # Cùng cái bẫy `searchsorted` như `forward_return`: không có phép
        # kiểm này thì EPS quý 2018 chia cho giá của phiên đầu năm 2022.
        if truoc_khi_co_gia(d, r.avail):
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
        tcrit = t_crit_95(len(per))
        lo, hi = m - tcrit * se, m + tcrit * se
        verdict = ("CÓ tín hiệu dương" if lo > 0 else
                   "CÓ tín hiệu âm" if hi < 0 else "không phân biệt được với 0")
        print(f"{c:<16}{m:>+9.3f}   [{lo:>+7.3f}, {hi:>+7.3f}]{len(per):>8}  {verdict}")

    print("\n" + "=" * 86)
    print("CÁCH ĐỌC — quan trọng hơn chính các con số ở trên")
    print("=" * 86)
    # Lực phát hiện phải suy từ SỐ KỲ THẬT SỰ ĐỌC ĐƯỢC, không in một hằng
    # số. Trước 22/08/2026 gói cộng đồng khoá ở 8 kỳ nên "~10%" luôn đúng;
    # gói tài trợ mở lên ~34 kỳ và con số cứng đó lập tức thành lời nói dối.
    _n = F["quarter"].nunique()
    _luc = {8: "~12%", 20: "~31%", 40: "~52%"}
    _gan = min(_luc, key=lambda k: abs(k - _n))
    print(f"Có {_n} kỳ. Ở mức IC thực tế của yếu tố cơ bản (0,03–0,05),")
    print(f"thiết kế này phát hiện được với xác suất khoảng {_luc[_gan]} "
          f"(nội suy từ mốc {_gan} kỳ).")
    print("")
    print("→ Dòng 'không phân biệt được với 0' KHÔNG có nghĩa là chỉ số đó vô")
    print("  dụng. Nó có nghĩa là mẫu quá nhỏ để nói bất cứ điều gì.")
    print("→ Dòng 'CÓ tín hiệu' cũng phải nghi ngờ: số liệu đã điều chỉnh hồi")
    print("  tố, rổ chỉ gồm mã còn sống, và cửa sổ nằm trong vùng đã tối ưu —")
    print("  cả ba đều tạo tín hiệu giả theo chiều dương.")
    print("")
    if _n < 20:
        print("Muốn có câu trả lời thật cần ≥40 quý. Số kỳ ít thế này nghĩa là")
        print("gói tài trợ CHƯA có hiệu lực ở môi trường đang chạy — kiểm bằng")
        print("`python -c \"import vnstock_goi; print(vnstock_goi.kiem_goi().dong_log())\"`")
    else:
        print("Số kỳ đã đủ để phép đo có nghĩa. Nhưng ba thiên lệch ở đầu file")
        print("vẫn nguyên, nên một kết quả DƯƠNG MẠNH vẫn phải nghi ngờ trước.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
