"""ĐO 33 — chốt sụt giảm của sổ: hai lượt walk-forward và phép tự nhất quán (iii) + đếm (iv).

Tiêu chí đọc đã khai và đã ký TRƯỚC mã và lượt chạy: `docs/TIEU-CHI-DOC-TRUOC.md`,
mục "ĐO 33" (BƯỚC 226). Đừng đọc alpha trước khi đọc mục ấy — bảng kết cục ở
trong ấy là thứ quyết định con số này dùng được hay không.

HAI LƯỢT, MỖI LƯỢT MỘT TIẾN TRÌNH — và một worktree, vì walkforward ghi sổ ở gốc repo
──────────────────────────────────────────────────────────────────────────────────
    A   CHOT_SUT_GIAM_NGUONG = 0      mặc định; phải tái lập lượt A của ĐO 31
    B   CHOT_SUT_GIAM_NGUONG = 0,15   giá trị DUY NHẤT ĐO 33 ghim

Cả hai là lượt 2 của `tools/do1_chi_phi_thuc_thi.py` (trượt giá BẬT · theo ngày).
Công cụ này chỉ đặt cờ TRONG tiến trình rồi giao cho `chay_mot_luot`.

PHÉP TỰ NHẤT QUÁN (iii) — dựng lại máy trạng thái TỪ sổ
───────────────────────────────────────────────────────
`--dem` lấy lệnh CLOSED của sổ và lịch phiên (`VNINDEX` của `backtest.data.CACHE_DIR`),
chạy CÙNG `chot_sut_giam.khoi_dong_bang` với ngưỡng 0,15, rồi đối chiếu với quyết định
mang lý do `paper_trading.LY_DO_CHOT_SUT_GIAM` và với ngày tín hiệu của lệnh. Sổ mở
trên BẢN CHÉP (mở `PaperTradingJournal` có thể ghi lược đồ).

CHẠY
────
    VIBE_CACHE_DIR=<bản chép cache> ./.venv/Scripts/python.exe tools/do33_chot_sut_giam.py --luot A
    VIBE_CACHE_DIR=<bản chép cache> ./.venv/Scripts/python.exe tools/do33_chot_sut_giam.py --dem <wf_oos.db>
"""
from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent

#: Giá trị DUY NHẤT ĐO 33 ghim cho lượt B. `tests/test_chot_sut_giam.py` đọc lại mục
#: ĐO 33 của `docs/TIEU-CHI-DOC-TRUOC.md` để hai chỗ không trôi khỏi nhau.
NGUONG_LUOT_B = 0.15
LUOT = {"A": 0, "B": NGUONG_LUOT_B}

#: Lượt của `tools/do1_chi_phi_thuc_thi.py` mà ĐO 33 đo lại: trượt giá BẬT · theo ngày.
LUOT_DO1 = 2


def doi_chieu(khoi: list[tuple[str, list[str]]], quyet_dinh: list[dict], lenh: list[dict],
              ly_do: str) -> dict:
    """Hàm THUẦN. Đối chiếu khối đóng băng dựng lại với sổ.

    Trả: số khối, số phiên bị chặn, số quyết định mang `ly_do`, số quyết định ấy NẰM NGOÀI
    khối (phải 0), số lệnh có ngày tín hiệu NẰM TRONG khối (sổ có cổng: phải 0)."""
    chan = {d for _, ds in khoi for d in ds}
    qd = [q for q in quyet_dinh if str(q["skip_reason"] or "").startswith(ly_do)]
    return {"so_khoi": len(khoi), "so_phien_chan": len(chan), "qd_ly_do": len(qd),
            "qd_ngoai_khoi": sum(str(q["signal_date"])[:10] not in chan for q in qd),
            "lenh_trong_khoi": sum(str(x["signal_date"])[:10] in chan for x in lenh
                                   if x["status"] == "CLOSED")}


def _doc(duong: str, sql: str) -> list[dict]:
    c = sqlite3.connect(f"file:{duong}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in c.execute(sql)]
    finally:
        c.close()


def chay_luot(ten: str) -> int:
    """Một lượt TRONG tiến trình này: đặt cờ, rồi giao cho `do1.chay_mot_luot`."""
    sys.path.insert(0, str(GOC))
    sys.path.insert(0, str(GOC / "tools"))
    import paper_trading
    import do1_chi_phi_thuc_thi as do1

    paper_trading.CHOT_SUT_GIAM_NGUONG = LUOT[ten]
    print(f"ĐO 33 · LƯỢT {ten} — paper_trading.CHOT_SUT_GIAM_NGUONG = {paper_trading.CHOT_SUT_GIAM_NGUONG}"
          f" · CHOT_SUT_GIAM_PHIEN = {paper_trading.CHOT_SUT_GIAM_PHIEN}", flush=True)
    return do1.chay_mot_luot(LUOT_DO1)


def main(argv: list[str] | None = None) -> int:
    for luong in (sys.stdout, sys.stderr):
        try:
            luong.reconfigure(encoding="utf-8", line_buffering=True)
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="ĐO 33 — chốt sụt giảm của sổ")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--luot", choices=sorted(LUOT), help="chạy một lượt walk-forward")
    g.add_argument("--dem", metavar="SO_DB", help="phép tự nhất quán (iii) + đếm (iv) trên một sổ")
    a = ap.parse_args(argv)
    if a.luot:
        return chay_luot(a.luot)
    sys.path.insert(0, str(GOC))
    import chot_sut_giam
    import paper_trading
    from backtest.data import CACHE_DIR

    with tempfile.TemporaryDirectory() as tam:
        ban = Path(tam) / "so.db"
        shutil.copy2(a.dem, ban)
        j = paper_trading.PaperTradingJournal(str(ban))
        try:
            he_so = chot_sut_giam.he_so_lenh(j.all_trades(paper_trading.Status.CLOSED))
        finally:
            j.db.close()
    phien = chot_sut_giam.lich_phien_mac_dinh()
    khoi = chot_sut_giam.khoi_dong_bang(phien, he_so, NGUONG_LUOT_B, paper_trading.CHOT_SUT_GIAM_PHIEN)
    lenh = _doc(a.dem, "SELECT id, symbol, signal_date, status FROM trades ORDER BY id")
    qd = _doc(a.dem, "SELECT signal_date, skip_reason FROM decisions ORDER BY seq")
    kq = doi_chieu(khoi, qd, lenh, paper_trading.LY_DO_CHOT_SUT_GIAM)
    print(f"sổ: {a.dem} · cache: {CACHE_DIR} · lệnh CLOSED: {len(he_so)} · phiên trong lịch: {len(phien)}")
    print(f"khối đóng băng dựng lại (ngưỡng {NGUONG_LUOT_B:g}, {paper_trading.CHOT_SUT_GIAM_PHIEN} phiên): "
          f"{kq['so_khoi']} · phiên bị chặn: {kq['so_phien_chan']}")
    for bd, ds in khoi[:8]:
        print(f"   bắt đầu {bd} · {len(ds)} phiên · tới {ds[-1]}")
    print(f"quyết định lý do chốt sụt giảm: {kq['qd_ly_do']} · nằm ngoài khối: {kq['qd_ngoai_khoi']}")
    print(f"lệnh CLOSED có ngày tín hiệu trong khối: {kq['lenh_trong_khoi']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
