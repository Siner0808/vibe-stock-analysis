"""ĐO 31 — lọc IMOM nhóm thấp: hai lượt walk-forward và phép đếm (iv).

Tiêu chí đọc đã khai và đã ký TRƯỚC mã và lượt chạy: `docs/TIEU-CHI-DOC-TRUOC.md`,
mục "ĐO 31" (BƯỚC 223). Đừng đọc alpha trước khi đọc mục ấy — bảng kết cục ở
trong ấy là thứ quyết định con số này dùng được hay không.

HAI LƯỢT, MỖI LƯỢT MỘT TIẾN TRÌNH — và một worktree, vì walkforward ghi sổ ở gốc repo
──────────────────────────────────────────────────────────────────────────────────
    A   LOC_IMOM_PHAN_VI = 0      mặc định; phải tái lập lượt A của ĐO 30
    B   LOC_IMOM_PHAN_VI = 0,20   giá trị DUY NHẤT ĐO 31 ghim

Cả hai là lượt 2 của `tools/do1_chi_phi_thuc_thi.py` (trượt giá BẬT · theo
ngày). Công cụ này chỉ đặt cờ TRONG tiến trình rồi giao cho `chay_mot_luot` —
không chép đường chạy, không sửa nguồn giữa hai lượt.

PHÉP ĐẾM (iv) — cùng định nghĩa với cổng `paper_trading.phan_vi_imom_bi_loc`
──────────────────────────────────────────────────────────────────────────
Một lệnh CLOSED của sổ là "lẽ ra bị lọc" khi phân vị IMOM của mã tại ngày tín
hiệu (`imom.BangIMOM` trên thư mục cache `backtest.data.CACHE_DIR`, tức
`VIBE_CACHE_DIR` nếu đặt) ≤ 0,20. Ở A phải ra đúng số đã khai, ở B phải ra 0.

CHẠY
────
    VIBE_CACHE_DIR=<bản chép cache> ./.venv/Scripts/python.exe tools/do31_loc_imom.py --luot A
    VIBE_CACHE_DIR=<bản chép cache> ./.venv/Scripts/python.exe tools/do31_loc_imom.py --luot B
    VIBE_CACHE_DIR=<bản chép cache> ./.venv/Scripts/python.exe tools/do31_loc_imom.py --dem <wf_oos.db>
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent

#: Giá trị DUY NHẤT ĐO 31 ghim cho lượt B. `tests/test_loc_imom.py` đọc lại mục
#: ĐO 31 của `docs/TIEU-CHI-DOC-TRUOC.md` để hai chỗ không trôi khỏi nhau.
PHAN_VI_LUOT_B = 0.20
LUOT = {"A": 0, "B": PHAN_VI_LUOT_B}

#: Lượt của `tools/do1_chi_phi_thuc_thi.py` mà ĐO 31 đo lại: trượt giá BẬT · theo ngày.
LUOT_DO1 = 2


def lenh_bi_loc(lenh: list[dict], phan_vi, nguong: float) -> list[dict]:
    """Các lệnh CLOSED mà cổng lọc IMOM LẼ RA chặn. Cùng định nghĩa cổng.

    `phan_vi(ma, ngay)` trả phân vị hoặc None (thiếu IMOM → không chặn).
    """
    ra = []
    for x in lenh:
        if x["status"] != "CLOSED" or not x["signal_date"]:
            continue
        pv = phan_vi(x["symbol"], str(x["signal_date"])[:10])
        if pv is not None and pv <= nguong:
            ra.append({**x, "phan_vi": pv})
    return ra


def doc_so(duong: str) -> list[dict]:
    """Mọi lệnh của một sổ walk-forward, CHỈ ĐỌC."""
    c = sqlite3.connect(f"file:{duong}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in c.execute(
            "SELECT id, symbol, signal_date, status FROM trades ORDER BY id")]
    finally:
        c.close()


def chay_luot(ten: str) -> int:
    """Một lượt TRONG tiến trình này: đặt cờ, rồi giao cho `do1.chay_mot_luot`."""
    sys.path.insert(0, str(GOC))
    sys.path.insert(0, str(GOC / "tools"))
    import paper_trading
    import do1_chi_phi_thuc_thi as do1

    paper_trading.LOC_IMOM_PHAN_VI = LUOT[ten]
    print(f"ĐO 31 · LƯỢT {ten} — paper_trading.LOC_IMOM_PHAN_VI = "
          f"{paper_trading.LOC_IMOM_PHAN_VI}", flush=True)
    return do1.chay_mot_luot(LUOT_DO1)


def main(argv: list[str] | None = None) -> int:
    for luong in (sys.stdout, sys.stderr):
        try:
            luong.reconfigure(encoding="utf-8", line_buffering=True)
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="ĐO 31 — lọc IMOM nhóm thấp")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--luot", choices=sorted(LUOT), help="chạy một lượt walk-forward")
    g.add_argument("--dem", metavar="SO_DB", help="phép đếm (iv) trên một sổ, chỉ đọc")
    a = ap.parse_args(argv)
    if a.luot:
        return chay_luot(a.luot)
    sys.path.insert(0, str(GOC))
    import imom
    from backtest.data import CACHE_DIR

    bang = imom.bang_cho(str(CACHE_DIR))
    lenh = doc_so(a.dem)
    dong = [x for x in lenh if x["status"] == "CLOSED"]
    loc = lenh_bi_loc(lenh, bang.phan_vi, PHAN_VI_LUOT_B)
    thieu = sum(bang.phan_vi(x["symbol"], str(x["signal_date"])[:10]) is None for x in dong)
    print(f"sổ: {a.dem} · cache: {CACHE_DIR} · lệnh CLOSED: {len(dong)} · thiếu IMOM: {thieu}")
    print(f"lệnh CLOSED có phân vị IMOM ≤ {PHAN_VI_LUOT_B:g} tại ngày tín hiệu: {len(loc)}")
    for x in sorted(loc, key=lambda x: (str(x["signal_date"]), x["symbol"]))[:5]:
        print(f"   {x['symbol']} · tín hiệu {str(x['signal_date'])[:10]} · id {x['id']} · "
              f"phân vị {x['phan_vi']:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
