"""ĐO 30 — nghỉ sau lệnh LỖ: hai lượt walk-forward và phép đếm (iv).

Tiêu chí đọc đã khai và đã ký TRƯỚC mã và lượt chạy: `docs/TIEU-CHI-DOC-TRUOC.md`,
mục "ĐO 30" (BƯỚC 221). Đừng đọc alpha trước khi đọc mục ấy — bảng kết cục ở
trong ấy là thứ quyết định con số này dùng được hay không.

HAI LƯỢT, MỖI LƯỢT MỘT TIẾN TRÌNH — và một worktree, vì walkforward ghi sổ ở gốc repo
──────────────────────────────────────────────────────────────────────────────────
    A   NGHI_SAU_LO_NGAY = 0   mặc định; phải tái lập lượt B của ĐO 29
    B   NGHI_SAU_LO_NGAY = 7   giá trị DUY NHẤT ĐO 30 ghim
    A50 như A, dải ngưỡng IS ghim [50]   chẩn đoán ĐO 30b (BƯỚC 227), khai SAU kết quả

Cả hai là lượt 2 của `tools/do1_chi_phi_thuc_thi.py` (trượt giá BẬT · theo
ngày). Công cụ này chỉ đặt cờ TRONG tiến trình rồi giao cho `chay_mot_luot` —
không chép đường chạy, không sửa nguồn giữa hai lượt.

PHÉP ĐẾM (iv) — cùng định nghĩa với cổng `PaperTradingJournal.ngay_ra_lo_gan`
──────────────────────────────────────────────────────────────────────────────
Một lệnh trong sổ là "tín hiệu lẽ ra bị chặn" khi CÙNG mã có một lệnh CLOSED
khác, giá ra < giá vào, mà ngày ra nằm trong [ngày tín hiệu − N ; ngày tín
hiệu] (ngày lịch). Ở A phải ra đúng số đã khai, ở B phải ra 0.
Kèm đếm quyết định mang lý do `paper_trading.LY_DO_NGHI_SAU_LO` (ĐO 30b (iii): phải ra 0).

CHẠY
────
    ./.venv/Scripts/python.exe tools/do30_nghi_sau_lo.py --luot A
    ./.venv/Scripts/python.exe tools/do30_nghi_sau_lo.py --luot B
    ./.venv/Scripts/python.exe tools/do30_nghi_sau_lo.py --dem <wf_oos.db>
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import date
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent

#: Giá trị DUY NHẤT ĐO 30 ghim cho lượt B. `tests/test_nghi_sau_lo.py` đọc lại
#: mục ĐO 30 của `docs/TIEU-CHI-DOC-TRUOC.md` để hai chỗ không trôi khỏi nhau.
NGAY_NGHI_LUOT_B = 7
LUOT = {"A": 0, "B": NGAY_NGHI_LUOT_B}

#: Chẩn đoán ĐO 30b (BƯỚC 227, khai sau kết quả ĐO 30): cấu hình lượt A, dải ngưỡng dò IS
#: chỉ còn MỘT giá trị — đặt `walkforward.DAI_NGUONG` TRONG tiến trình, không sửa nguồn.
NGUONG_GHIM_A50 = 50.0
CHAN_DOAN = {"A50": (LUOT["A"], NGUONG_GHIM_A50)}

#: Lượt của `tools/do1_chi_phi_thuc_thi.py` mà ĐO 30 đo lại: trượt giá BẬT · theo ngày.
LUOT_DO1 = 2


def tin_hieu_bi_chan(lenh: list[dict], ngay_nghi: int) -> list[dict]:
    """Các lệnh mà cổng nghỉ-sau-lỗ LẼ RA chặn. HÀM THUẦN — cùng định nghĩa cổng.

    `lenh`: mọi lệnh của sổ, mỗi lệnh có `id`, `symbol`, `signal_date`,
    `exit_date`, `entry_price`, `exit_price`, `status`.
    """
    lo: dict[str, list[date]] = {}
    for x in lenh:
        if (x["status"] == "CLOSED" and x["exit_date"] and x["entry_price"] is not None
                and x["exit_price"] is not None and x["exit_price"] < x["entry_price"]):
            lo.setdefault(x["symbol"], []).append(date.fromisoformat(str(x["exit_date"])[:10]))
    ra = []
    for x in lenh:
        if not x["signal_date"]:
            continue
        s = date.fromisoformat(str(x["signal_date"])[:10])
        if any(0 <= (s - e).days <= ngay_nghi for e in lo.get(x["symbol"], [])):
            ra.append(x)
    return ra


def doc_so(duong: str) -> list[dict]:
    """Mọi lệnh của một sổ walk-forward, CHỈ ĐỌC."""
    c = sqlite3.connect(f"file:{duong}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in c.execute(
            "SELECT id, symbol, signal_date, exit_date, entry_price, exit_price, status "
            "FROM trades ORDER BY id")]
    finally:
        c.close()


def doc_ly_do(duong: str) -> list:
    """Lý do của mọi quyết định, CHỈ ĐỌC. Sổ không có bảng `decisions` thì NỔ — đối chứng
    đếm 0 trên một bảng vắng là đối chứng giả."""
    c = sqlite3.connect(f"file:{duong}?mode=ro", uri=True)
    try:
        return [r[0] for r in c.execute("SELECT skip_reason FROM decisions ORDER BY seq")]
    finally:
        c.close()


def chay_luot(ten: str) -> int:
    """Một lượt TRONG tiến trình này: đặt cờ, rồi giao cho `do1.chay_mot_luot`."""
    sys.path.insert(0, str(GOC))
    sys.path.insert(0, str(GOC / "tools"))
    import paper_trading
    import do1_chi_phi_thuc_thi as do1

    if ten in CHAN_DOAN:
        import walkforward
        ngay, nguong = CHAN_DOAN[ten]
        walkforward.DAI_NGUONG = [nguong]
        print(f"ĐO 30b · dải ngưỡng IS ghim: walkforward.DAI_NGUONG = {walkforward.DAI_NGUONG}", flush=True)
    else:
        ngay = LUOT[ten]
    paper_trading.NGHI_SAU_LO_NGAY = ngay
    print(f"ĐO 30 · LƯỢT {ten} — paper_trading.NGHI_SAU_LO_NGAY = "
          f"{paper_trading.NGHI_SAU_LO_NGAY}", flush=True)
    return do1.chay_mot_luot(LUOT_DO1)


def main(argv: list[str] | None = None) -> int:
    for luong in (sys.stdout, sys.stderr):
        try:
            luong.reconfigure(encoding="utf-8", line_buffering=True)
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="ĐO 30 — nghỉ sau lệnh lỗ")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--luot", choices=sorted(LUOT) + sorted(CHAN_DOAN), help="chạy một lượt walk-forward")
    g.add_argument("--dem", metavar="SO_DB", help="phép đếm (iv) trên một sổ, chỉ đọc")
    a = ap.parse_args(argv)
    if a.luot:
        return chay_luot(a.luot)
    lenh = doc_so(a.dem)
    chan = tin_hieu_bi_chan(lenh, NGAY_NGHI_LUOT_B)
    print(f"sổ: {a.dem} · lệnh: {len(lenh)}")
    print(f"tín hiệu cùng mã trong 0–{NGAY_NGHI_LUOT_B} ngày lịch sau một lệnh lỗ: {len(chan)}")
    for x in sorted(chan, key=lambda x: (str(x["signal_date"]), x["symbol"]))[:5]:
        print(f"   {x['symbol']} · tín hiệu {str(x['signal_date'])[:10]} · id {x['id']}")
    sys.path.insert(0, str(GOC))
    import paper_trading
    nghi = [r for r in doc_ly_do(a.dem) if str(r or "").startswith(paper_trading.LY_DO_NGHI_SAU_LO)]
    print(f"quyết định lý do {paper_trading.LY_DO_NGHI_SAU_LO}: {len(nghi)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
