"""Kéo chuỗi khối ngoại cho cả rổ về `backtest/cache_khoi_ngoai/`.

ĐO 14 (`docs/STATE.md` BƯỚC 112) đo được đường này dùng được: 2.923 phiên
từ 2015-01-05, 71/71 mã, 0 phiên có giá mà thiếu khối ngoại. Script này
biến nó thành cache trên đĩa để phép đo tái lập được mà không cần mạng —
đúng cặp `fetch_fundamentals.py` / `experiment_fundamentals.py`.

CACHE NẰM Ở `backtest/cache_khoi_ngoai/`, KHÔNG PHẢI CHỖ KHÁC
`.gitignore` có mẫu `backtest/cache*/` và lời khai của nó nói rõ vì sao:
*"để một cache mới không bao giờ lọt vào commit"*. Đặt tên theo mẫu ấy là
cách rẻ nhất để không phải nhớ.

KHÔNG CẮT NGÀY Ở ĐÂY
Kéo TOÀN BỘ chuỗi nguồn phục vụ. Cắt theo cửa sổ là việc của phép đo, và
một cache đã bị cắt thì không ai biết nó bị cắt — đúng cái bẫy `download()`
trong `NGUYEN-TAC-DO-LUONG.md`: mã tải lần đầu với 13 tháng sẽ mãi mãi 13
tháng.

CHẠY
    ./.venv/Scripts/python.exe fetch_khoi_ngoai.py
    ./.venv/Scripts/python.exe fetch_khoi_ngoai.py --lam-lai
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))

RA = GOC / "backtest" / "cache_khoi_ngoai"

#: Xin đủ sớm để chạm trần THẬT của nguồn, không phải trần của câu hỏi.
XIN_TU = "2015-01-01"

#: Cột bắt buộc. Thiếu một cột là hỏng ngầm, không phải thiếu một tiện ích.
COT_BAT_BUOC = ("time", "buy_vol", "buy_val", "sell_vol", "sell_val",
                "net_vol", "net_val")


def _hom_nay() -> str:
    return time.strftime("%Y-%m-%d")


def keo_mot_ma(mkt, ma: str):
    """Bảng khối ngoại của một mã, hoặc None. KHÔNG nuốt lỗi thành bảng rỗng."""
    import pandas as pd

    try:
        df = mkt.equity(ma).foreign_flow(start=XIN_TU, end=_hom_nay())
    except Exception as e:  # noqa: BLE001
        print(f"  {ma:<5} LOI {type(e).__name__}: {str(e)[:70]}")
        return None
    if not isinstance(df, pd.DataFrame) or df.empty:
        print(f"  {ma:<5} rong")
        return None
    thieu = [c for c in COT_BAT_BUOC if c not in df.columns]
    if thieu:
        print(f"  {ma:<5} THIEU COT {thieu} — bo, khong doan")
        return None
    return df


def main(tham_so: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Keo chuoi khoi ngoai ca ro")
    ap.add_argument("--lam-lai", action="store_true",
                    help="keo lai ca nhung ma da co file")
    ap.add_argument("--nghi", type=float, default=0.2)
    ap.add_argument("--so-ma", type=int, default=0)
    a = ap.parse_args(tham_so)

    try:
        import vnstock_data as vd
    except Exception as e:  # noqa: BLE001
        print(f"CHUA KIEM DUOC — import vnstock_data no: {type(e).__name__}: {e}")
        return 2

    from vn100_symbols import VN100_SYMBOLS

    RA.mkdir(parents=True, exist_ok=True)
    mkt = vd.Market()
    ma_list = VN100_SYMBOLS[:a.so_ma] if a.so_ma else list(VN100_SYMBOLS)

    co, bo, sot = 0, 0, 0
    for i, ma in enumerate(ma_list, 1):
        f = RA / f"{ma}.csv"
        if f.exists() and not a.lam_lai:
            sot += 1
            continue
        df = keo_mot_ma(mkt, ma)
        if df is None:
            bo += 1
        else:
            df.to_csv(f, index=False, encoding="utf-8")
            co += 1
            if i % 10 == 0:
                print(f"  {i:>3}/{len(ma_list)}  {ma} {len(df)} dong")
        time.sleep(a.nghi)

    print(f"\nKEO: {co} ma · BO QUA (da co): {sot} · HONG: {bo}"
          f" · tong {len(ma_list)}")
    print(f"noi ghi: {RA}")
    return 0 if bo == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
