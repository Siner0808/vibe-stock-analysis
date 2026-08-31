"""CLI backtest.

    # Bước 1 — tải dữ liệu (cần mạng, chạy một lần)
    python3 backtest/run.py fetch --start 2024-01-01 --end 2026-08-01

    # Bước 2 — chạy backtest (offline, lặp lại được)
    python3 backtest/run.py test --stride 5
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backtest import data, engine, report   # noqa: E402

OUT_DIR = Path(__file__).parent / "results"


def cmd_fetch(args) -> int:
    symbols = args.symbols.split(",") if args.symbols else data.VN30_SNAPSHOT
    print(f"Tải {len(symbols)} mã: {args.start} → {args.end}\n")
    got = data.download(symbols, args.start, args.end, force=args.force)
    print(f"\nXong: {len(got)}/{len(symbols)} mã có dữ liệu "
          f"({sum(got.values()):,} phiên) → {data.CACHE_DIR}")
    if len(got) < len(symbols) * 0.8:
        print("⚠️ Thiếu quá nhiều mã — kết quả backtest sẽ không đại diện.")
        return 1
    return 0


def cmd_test(args) -> int:
    symbols = args.symbols.split(",") if args.symbols else None
    dataset = data.load_all(symbols)
    if not dataset:
        print("❌ Chưa có cache. Chạy `python3 backtest/run.py fetch` trước.")
        return 1

    horizons = tuple(int(h) for h in args.horizons.split(","))
    print(f"Replay {len(dataset)} mã · stride={args.stride} · "
          f"horizons={horizons}\n")
    obs = engine.run_universe(dataset, horizons=horizons,
                              min_history=args.min_history, stride=args.stride)
    if not obs:
        print("❌ Không có quan sát nào — dữ liệu quá ngắn so với min_history + horizon.")
        return 1

    df = engine.to_frame(obs, horizons)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUT_DIR / "observations.csv"
    df.to_csv(csv_path, index=False)

    text = report.summarize(df, horizons)
    print("\n" + text)
    (OUT_DIR / "report.txt").write_text(text, encoding="utf-8")
    print(f"\n📄 Chi tiết: {csv_path}\n📄 Báo cáo:  {OUT_DIR / 'report.txt'}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Backtest hệ thống chấm điểm Vn-Stock")
    sub = p.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch", help="Tải dữ liệu lịch sử về cache")
    f.add_argument("--start", default="2024-01-01")
    f.add_argument("--end", default="2026-08-01")
    f.add_argument("--symbols", help="Danh sách mã, phân tách bởi dấu phẩy")
    f.add_argument("--force", action="store_true", help="Tải lại dù đã có cache")
    f.set_defaults(func=cmd_fetch)

    t = sub.add_parser("test", help="Chạy backtest trên cache")
    t.add_argument("--stride", type=int, default=5,
                   help="Lấy mẫu mỗi N phiên (lớn hơn = ít chồng lấn hơn)")
    t.add_argument("--min-history", type=int, default=60, dest="min_history")
    t.add_argument("--horizons", default="20,60")
    t.add_argument("--symbols")
    t.set_defaults(func=cmd_test)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
