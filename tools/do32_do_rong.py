"""ĐO 32 — độ rộng thị trường thay cổng VN-INDEX: ba lượt walk-forward và phép đếm (iv).

Tiêu chí đọc đã khai và đã ký TRƯỚC mã và lượt chạy: `docs/TIEU-CHI-DOC-TRUOC.md`,
mục "ĐO 32" (BƯỚC 224). Đừng đọc alpha trước khi đọc mục ấy — bảng kết cục ở
trong ấy là thứ quyết định con số này dùng được hay không.

BA LƯỢT, MỖI LƯỢT MỘT TIẾN TRÌNH — và một worktree, vì walkforward ghi sổ ở gốc repo
──────────────────────────────────────────────────────────────────────────────────
    A   CONG_VNI_BAT True,  DO_RONG_NGUONG 0      mặc định; phải tái lập lượt A của ĐO 31
    B   CONG_VNI_BAT False, DO_RONG_NGUONG 0,50   giá trị DUY NHẤT ĐO 32 ghim
    C   CONG_VNI_BAT False, DO_RONG_NGUONG 0      chẩn đoán: không cổng thị trường nào

Cả ba là lượt 2 của `tools/do1_chi_phi_thuc_thi.py` (trượt giá BẬT · theo
ngày). Công cụ này chỉ đặt cờ TRONG tiến trình rồi giao cho `chay_mot_luot` —
không chép đường chạy, không sửa nguồn giữa các lượt.

PHÉP ĐẾM (iv) — cùng định nghĩa với cổng `paper_trading.do_rong_bi_chan`
──────────────────────────────────────────────────────────────────────
Một lệnh CLOSED là "lẽ ra bị chặn" khi độ rộng tại ngày tín hiệu (`do_rong.BangDoRong`
trên thư mục cache `backtest.data.CACHE_DIR`, tức `VIBE_CACHE_DIR` nếu đặt) < 0,50.
Kèm đếm quyết định theo lý do: `paper_trading.LY_DO_VNI` và `paper_trading.LY_DO_DO_RONG`.

CHẠY
────
    VIBE_CACHE_DIR=<bản chép cache> ./.venv/Scripts/python.exe tools/do32_do_rong.py --luot A
    VIBE_CACHE_DIR=<bản chép cache> ./.venv/Scripts/python.exe tools/do32_do_rong.py --dem <wf_oos.db>
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent

#: Giá trị DUY NHẤT ĐO 32 ghim cho lượt B. `tests/test_do_rong.py` đọc lại mục
#: ĐO 32 của `docs/TIEU-CHI-DOC-TRUOC.md` để hai chỗ không trôi khỏi nhau.
NGUONG_LUOT_B = 0.50
#: (CONG_VNI_BAT, DO_RONG_NGUONG) của từng lượt.
LUOT = {"A": (True, 0), "B": (False, NGUONG_LUOT_B), "C": (False, 0)}

#: Lượt của `tools/do1_chi_phi_thuc_thi.py` mà ĐO 32 đo lại: trượt giá BẬT · theo ngày.
LUOT_DO1 = 2


def lenh_bi_chan(lenh: list[dict], do_rong, nguong: float) -> list[dict]:
    """Các lệnh CLOSED mà cổng độ rộng LẼ RA chặn. Cùng định nghĩa cổng.

    `do_rong(ngay)` trả độ rộng hoặc None (thiếu → không chặn).
    """
    ra = []
    for x in lenh:
        if x["status"] != "CLOSED" or not x["signal_date"]:
            continue
        dr = do_rong(str(x["signal_date"])[:10])
        if dr is not None and dr < nguong:
            ra.append({**x, "do_rong": dr})
    return ra


def _doc(duong: str, sql: str) -> list[dict]:
    c = sqlite3.connect(f"file:{duong}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in c.execute(sql)]
    finally:
        c.close()


def doc_so(duong: str) -> list[dict]:
    """Mọi lệnh của một sổ walk-forward, CHỈ ĐỌC."""
    return _doc(duong, "SELECT id, symbol, signal_date, status FROM trades ORDER BY id")


def doc_quyet_dinh(duong: str) -> list[dict]:
    """Ngày tín hiệu và lý do của mọi quyết định, CHỈ ĐỌC."""
    return _doc(duong, "SELECT signal_date, skip_reason FROM decisions ORDER BY seq")


def chay_luot(ten: str) -> int:
    """Một lượt TRONG tiến trình này: đặt cờ, rồi giao cho `do1.chay_mot_luot`."""
    sys.path.insert(0, str(GOC))
    sys.path.insert(0, str(GOC / "tools"))
    import paper_trading
    import do1_chi_phi_thuc_thi as do1

    paper_trading.CONG_VNI_BAT, paper_trading.DO_RONG_NGUONG = LUOT[ten]
    print(f"ĐO 32 · LƯỢT {ten} — paper_trading.CONG_VNI_BAT = {paper_trading.CONG_VNI_BAT} · "
          f"DO_RONG_NGUONG = {paper_trading.DO_RONG_NGUONG}", flush=True)
    return do1.chay_mot_luot(LUOT_DO1)


def main(argv: list[str] | None = None) -> int:
    for luong in (sys.stdout, sys.stderr):
        try:
            luong.reconfigure(encoding="utf-8", line_buffering=True)
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="ĐO 32 — độ rộng thị trường thay cổng VN-INDEX")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--luot", choices=sorted(LUOT), help="chạy một lượt walk-forward")
    g.add_argument("--dem", metavar="SO_DB", help="phép đếm (iv) trên một sổ, chỉ đọc")
    a = ap.parse_args(argv)
    if a.luot:
        return chay_luot(a.luot)
    sys.path.insert(0, str(GOC))
    import do_rong
    import paper_trading
    from backtest.data import CACHE_DIR

    bang = do_rong.bang_cho(str(CACHE_DIR))
    lenh = doc_so(a.dem)
    dong = [x for x in lenh if x["status"] == "CLOSED"]
    chan = lenh_bi_chan(lenh, bang.do_rong, NGUONG_LUOT_B)
    thieu = sum(bang.do_rong(str(x["signal_date"])[:10]) is None for x in dong)
    print(f"sổ: {a.dem} · cache: {CACHE_DIR} · lệnh CLOSED: {len(dong)} · thiếu độ rộng: {thieu}")
    print(f"lệnh CLOSED có độ rộng < {NGUONG_LUOT_B:g} tại ngày tín hiệu: {len(chan)}")
    for x in sorted(chan, key=lambda x: (str(x["signal_date"]), x["symbol"]))[:5]:
        print(f"   {x['symbol']} · tín hiệu {str(x['signal_date'])[:10]} · id {x['id']} · "
              f"độ rộng {x['do_rong']:.3f}")
    qd = doc_quyet_dinh(a.dem)
    vni = [q for q in qd if q["skip_reason"] == paper_trading.LY_DO_VNI]
    dr = [q for q in qd if str(q["skip_reason"] or "").startswith(paper_trading.LY_DO_DO_RONG)]
    ngay_dr = {str(q["signal_date"])[:10] for q in dr}
    lech = [q for q in dr if str(q["signal_date"])[:10] in
            {d for d in ngay_dr if bang.do_rong(d) is None or bang.do_rong(d) >= NGUONG_LUOT_B}]
    print(f"quyết định lý do VN-INDEX: {len(vni)} · lý do độ rộng: {len(dr)} "
          f"(rơi vào ngày độ rộng ≥ {NGUONG_LUOT_B:g} hoặc thiếu: {len(lech)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
