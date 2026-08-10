"""
fetch_fundamentals.py
──────────────────────────────────────────────────────────────────────
Tải báo cáo tài chính THEO QUÝ và ghi cache, để đo xem dữ liệu cơ bản có
tín hiệu dự báo hay không.

VÌ SAO PHẢI THEO QUÝ, KHÔNG PHẢI THEO NĂM
`financial_collector.py` dùng `period="year"`. Dữ liệu năm cho 4-5 điểm
quan sát mỗi mã trong toàn bộ lịch sử — không đủ để đo bất cứ điều gì.
Theo quý cho ~18 điểm mỗi mã trên 4,5 năm.

BA CÁI BẪY CỦA DỮ LIỆU CƠ BẢN — đọc trước khi tin kết quả

1. ĐỘ TRỄ CÔNG BỐ. Báo cáo quý 2 kết thúc 30/06 nhưng chỉ công bố cuối
   tháng 7. Dùng số liệu quý 2 để ra quyết định ngày 01/07 là nhìn trộm
   tương lai — và đây là lỗi phổ biến nhất khi backtest dữ liệu cơ bản.
   Script đo sẽ cộng độ trễ; ở đây chỉ tải và giữ nguyên ngày kết thúc quý.

2. SỐ LIỆU ĐÃ ĐIỀU CHỈNH LẠI. vnstock trả về báo cáo ở trạng thái HIỆN
   TẠI, gồm cả những lần điều chỉnh hồi tố sau kiểm toán. Nhà đầu tư năm
   2022 không thấy con số đó. KHÔNG có cách nào sửa từ nguồn này — phải
   ghi nhận đây là giới hạn và hiểu rằng kết quả sẽ lạc quan hơn thực tế.

3. THIÊN LỆCH SỐNG SÓT. Rổ là ảnh chụp hiện tại. Doanh nghiệp phá sản
   hoặc bị huỷ niêm yết không có mặt — mà đó chính là nhóm mà chỉ số cơ
   bản xấu lẽ ra phải cảnh báo.

Hai cái sau không khắc phục được bằng nguồn dữ liệu miễn phí. Nếu kết quả
ra rho ≈ 0 thì kết luận vẫn vững (thiên lệch chỉ làm ĐẸP lên, nên đo được
số 0 ở đây là bằng chứng mạnh). Nếu ra rho > 0 thì phải nghi ngờ.

CHẠY
    python fetch_fundamentals.py            # cả rổ
    python fetch_fundamentals.py --schema   # in cấu trúc dữ liệu rồi dừng
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd

from vn100_symbols import VN100_SYMBOLS

OUT = Path(__file__).parent / "backtest" / "fundamentals"


def fetch_symbol(symbol: str) -> dict[str, pd.DataFrame]:
    """Tải các bảng theo quý. Trả dict rỗng nếu không lấy được."""
    from vnstock import Finance

    fin = Finance(source="VCI", symbol=symbol, period="quarter", show_log=False)
    out = {}
    for name, fn in (("ratio", lambda: fin.ratio(lang="en", dropna=False)),
                     ("income", lambda: fin.income_statement(lang="en", dropna=False)),
                     ("balance", lambda: fin.balance_sheet(lang="en", dropna=False))):
        try:
            df = fn()
            if df is not None and not df.empty:
                out[name] = df
        except Exception as e:
            print(f"    {name}: ❌ {type(e).__name__}: {str(e)[:70]}")
    return out


def describe(df: pd.DataFrame, name: str) -> None:
    print(f"\n  ── {name}: {df.shape[0]} dòng × {df.shape[1]} cột")
    cols = list(df.columns)
    flat = [c if not isinstance(c, tuple) else " | ".join(str(x) for x in c)
            for c in cols]
    print(f"     8 cột đầu: {flat[:8]}")
    if len(flat) > 8:
        print(f"     8 cột cuối: {flat[-8:]}")
    print(f"     2 dòng đầu:")
    with pd.option_context("display.max_columns", 6, "display.width", 200):
        print("       " + df.head(2).to_string().replace("\n", "\n       ")[:600])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", type=int, default=0,
                    help="giới hạn số mã (0 = cả rổ)")
    ap.add_argument("--schema", action="store_true",
                    help="chỉ tải 1 mã và in cấu trúc, không ghi cache")
    a = ap.parse_args()

    try:
        from vnstock_auth import status_message
        print(status_message())
    except Exception:
        pass

    syms = VN100_SYMBOLS[:a.symbols] if a.symbols else VN100_SYMBOLS

    if a.schema:
        sym = syms[0]
        print(f"\nCẤU TRÚC DỮ LIỆU THEO QUÝ — {sym}")
        print("=" * 70)
        tables = fetch_symbol(sym)
        if not tables:
            print("❌ Không tải được bảng nào.")
            return 1
        for name, df in tables.items():
            describe(df, name)
        print("\n→ Dán phần trên vào cuộc trò chuyện để viết phần đọc dữ liệu.")
        return 0

    OUT.mkdir(parents=True, exist_ok=True)
    ok = skipped = 0
    for i, sym in enumerate(syms, 1):
        paths = {n: OUT / f"{sym}_{n}.csv" for n in ("ratio", "income", "balance")}
        if all(p.exists() for p in paths.values()):
            print(f"[{i}/{len(syms)}] {sym}: đã có cache — bỏ qua")
            skipped += 1
            continue
        tables = fetch_symbol(sym)
        if not tables:
            print(f"[{i}/{len(syms)}] {sym}: ❌ không tải được")
            continue
        for name, df in tables.items():
            df.to_csv(paths[name], index=False)
        ok += 1
        print(f"[{i}/{len(syms)}] {sym}: ✅ "
              + " · ".join(f"{n} {d.shape[0]}×{d.shape[1]}"
                           for n, d in tables.items()))
        time.sleep(0.5)

    print(f"\nTải mới {ok} mã, bỏ qua {skipped} mã đã có.")
    print(f"Cache: {OUT}")
    print("\nBước tiếp theo: chạy `python fetch_fundamentals.py --schema` "
          "rồi dán kết quả để viết phần đo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
