"""ĐO 20 — ghép TỪNG LỆNH giữa sổ OOS của hai luồng (đối chứng · đã sửa).

Tiêu chí: `docs/TIEU-CHI-DOC-TRUOC.md` mục ĐO 20. Alpha và KTC đọc ở log của
walkforward; dụng cụ này trả lời câu mà alpha không trả lời được — Δ đến từ
ĐÂU: lệnh nào chỉ có ở một bên, lệnh nào cùng khoá mà khác giá, và lệnh chỉ
có ở bên đã sửa có đúng là lệnh khớp ở phiên mở cửa lệch > 7% không.

    ./.venv/Scripts/python.exe tools/do20_ghep_tung_lenh.py \
        --doi-chung <wf_oos.db> --sua <wf_oos.db> [--cache <thư mục CSV>]

CHỈ ĐỌC: mở hai DB ở chế độ `mode=ro`. Mã thoát 0 đọc được · 2 chưa kiểm
được (thiếu file). Khoá ghép là (mã, NGÀY tín hiệu 10 ký tự) — cùng khoá
ĐO 18 dùng.
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

for _luong in (sys.stdout, sys.stderr):   # stderr: BƯỚC 129
    try:
        _luong.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

COT = ("symbol", "signal_date", "entry_date", "entry_price", "exit_date",
       "exit_price", "exit_reason", "status", "size_pct")


def doc_so(duong: Path) -> dict:
    """{(mã, ngày tín hiệu): dòng} — nổ nếu một khoá xuất hiện hai lần."""
    db = sqlite3.connect(f"file:{duong}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    ra: dict = {}
    for r in db.execute(f"SELECT {', '.join(COT)} FROM trades ORDER BY id"):
        k = (r["symbol"], str(r["signal_date"])[:10])
        if k in ra:
            raise ValueError(f"{duong.name}: khoá {k} xuất hiện hai lần")
        ra[k] = dict(r)
    db.close()
    return ra


def _gia(d: dict) -> tuple:
    return (str(d["entry_date"] or "")[:10], d["entry_price"],
            str(d["exit_date"] or "")[:10], d["exit_price"], d["exit_reason"])


def ghep(a: dict, b: dict) -> dict:
    """Hàm THUẦN: phân loại khoá của hai sổ. `a` đối chứng, `b` đã sửa."""
    chung = sorted(set(a) & set(b))
    return {
        "giong_het": [k for k in chung if _gia(a[k]) == _gia(b[k])
                      and a[k]["status"] == b[k]["status"]],
        "khac": [k for k in chung if _gia(a[k]) != _gia(b[k])
                 or a[k]["status"] != b[k]["status"]],
        "chi_doi_chung": sorted(set(a) - set(b)),
        "chi_sua": sorted(set(b) - set(a)),
    }


def lech_mo_cua(cache: Path | None, ma: str, ngay: str) -> float | None:
    """(mở cửa ngày ấy / đóng cửa phiên trước) − 1, từ cache CSV. None nếu thiếu."""
    if cache is None or not ngay:
        return None
    f = cache / f"{ma}.csv"
    if not f.exists():
        return None
    import pandas as pd
    d = pd.read_csv(f)
    d["d"] = d["time"].astype(str).str[:10]
    i = d.index[d["d"] == ngay]
    if len(i) == 0 or i[0] == 0:
        return None
    return float(d.loc[i[0], "open"]) / float(d.loc[i[0] - 1, "close"]) - 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--doi-chung", required=True, type=Path)
    ap.add_argument("--sua", required=True, type=Path)
    ap.add_argument("--cache", type=Path, default=None)
    a = ap.parse_args()
    for p in (a.doi_chung, a.sua):
        if not p.exists():
            print(f"CHUA KIEM DUOC — thiếu {p}", file=sys.stderr)
            return 2

    dc, sua = doc_so(a.doi_chung), doc_so(a.sua)
    for ten, so in (("doi chung", dc), ("da sua", sua)):
        tt: dict = {}
        for d in so.values():
            tt[d["status"]] = tt.get(d["status"], 0) + 1
        print(f"{ten:10} {len(so):4d} dong · theo trang thai {tt}")

    g = ghep(dc, sua)
    print(f"\ncung khoa, GIONG HET : {len(g['giong_het'])}")
    print(f"cung khoa, KHAC      : {len(g['khac'])}")
    print(f"chi o DOI CHUNG      : {len(g['chi_doi_chung'])}")
    print(f"chi o DA SUA         : {len(g['chi_sua'])}")

    def _in(nhan, khoa, so):
        print(f"\n{nhan}:")
        for k in khoa:
            d = so[k]
            lech = lech_mo_cua(a.cache, k[0], str(d["entry_date"] or "")[:10])
            s_lech = "   -   " if lech is None else f"{lech:+.4f}"
            print(f"  {k[0]:5} tin hieu {k[1]} · vao {str(d['entry_date'] or '-')[:10]}"
                  f" mo cua lech {s_lech} · {d['status']:6} · {d['exit_reason']}")

    _in("CHI O DA SUA (dong du lieu tho)", g["chi_sua"], sua)
    _in("CHI O DOI CHUNG (dong du lieu tho)", g["chi_doi_chung"], dc)
    _in("CUNG KHOA, KHAC — ben DA SUA", g["khac"], sua)
    huy = sorted(k for k, d in sua.items() if d["status"] == "HUY")
    _in("HUY o ben DA SUA", huy, sua)

    if a.cache is not None:
        vao = [k for k in g["chi_sua"] if sua[k]["entry_date"]]
        lech = [lech_mo_cua(a.cache, k[0], str(sua[k]["entry_date"])[:10])
                for k in vao]
        tren7 = sum(1 for x in lech if x is not None and abs(x) > 0.07)
        print(f"\nlenh CHI o DA SUA co khop: {len(vao)} · trong do mo cua "
              f"lech > 7%: {tren7}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
