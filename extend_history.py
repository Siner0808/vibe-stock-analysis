"""
extend_history.py
──────────────────────────────────────────────────────────────────────
Nối dài cache dữ liệu VỀ QUÁ KHỨ cho toàn bộ rổ.

VÌ SAO CẦN
Toàn bộ việc tối ưu tham số cho tới nay đã chạy trên khoảng dữ liệu hiện
có. Muốn biết chiến lược có lợi thế thật hay không thì phải đo trên khoảng
CHƯA từng dùng để chọn tham số. Với dự án này, khoảng đó nằm ở QUÁ KHỨ —
không phải ở hiện tại, vì hiện tại đã bị hàng trăm vòng loop nhìn qua.

Hiện trạng (đo ngày 07/08/2026):
    13 mã có dữ liệu từ 2023-11
     9 mã từ 2025-01
    28 mã từ 2025-07     ← không đủ để kiểm định bất cứ điều gì

Script này kéo tất cả về cùng một mốc, mặc định 2022-01-01.

CHẠY
    python extend_history.py                 # về 2022-01-01
    python extend_history.py --start 2021-01-01
    python extend_history.py --check         # chỉ xem độ phủ, không tải

Cần kết nối mạng và API key vnstock (xem vnstock_auth.py).
Chạy lại nhiều lần an toàn: mã nào đã đủ lịch sử thì bỏ qua.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date

from backtest.data import coverage, extend_history
from vn100_symbols import VN100_SYMBOLS


def print_coverage(symbols: list[str]) -> None:
    cov = coverage(symbols)
    have = cov[cov["sessions"] > 0]
    print(f"\nĐỘ PHỦ DỮ LIỆU — {len(have)}/{len(symbols)} mã có cache")
    if have.empty:
        print("  (chưa có mã nào)")
        return

    buckets = have.groupby(have["from"].str[:7]).size().sort_index()
    print("\n  Bắt đầu từ:")
    for month, n in buckets.items():
        print(f"    {month}: {'█' * n} {n} mã")

    print(f"\n  Phiên ít nhất : {have['sessions'].min()}  ({have.loc[have['sessions'].idxmin(), 'symbol']})")
    print(f"  Phiên nhiều nhất: {have['sessions'].max()}  ({have.loc[have['sessions'].idxmax(), 'symbol']})")

    earliest_common = have["from"].max()
    print(f"\n  → Mốc chung sớm nhất của CẢ RỔ: {earliest_common}")
    print("    (mọi phân tích trên toàn rổ chỉ đáng tin từ mốc này trở đi)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2022-01-01",
                    help="mốc lịch sử cần có (mặc định 2022-01-01)")
    ap.add_argument("--end", default=date.today().isoformat())
    ap.add_argument("--check", action="store_true",
                    help="chỉ in độ phủ hiện tại, không tải gì")
    a = ap.parse_args()

    symbols = VN100_SYMBOLS
    print(f"Rổ: {len(symbols)} mã")

    try:
        from vnstock_auth import status_message
        print(status_message())
    except Exception as e:
        print(f"⚠️ Không kiểm tra được API key: {type(e).__name__}")

    print_coverage(symbols)

    if a.check:
        return 0

    print(f"\n{'=' * 66}")
    print(f"Nối dài lịch sử về {a.start}")
    print(f"{'=' * 66}\n")

    changed = extend_history(symbols, a.start, a.end)

    print(f"\n{'=' * 66}")
    print(f"Đã cập nhật {len(changed)}/{len(symbols)} mã")
    print_coverage(symbols)

    print("\nBước tiếp theo:  python walkforward_vn100.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
