"""ĐO 28 — đối chứng (iii) và số đếm của mô hình khớp ở phiên KỊCH TRẦN/SÀN MỘT GIÁ.

Tiêu chí: `docs/TIEU-CHI-DOC-TRUOC.md` mục ĐO 28 (ký ở `059e456`, TRƯỚC dụng cụ này).
Alpha và KTC đọc ở log walk-forward của hai lượt; ghép từng lệnh bằng
`tools/do20_ghep_tung_lenh.py`. Dụng cụ này trả lời phần còn lại:

- **(iii)** mọi lệnh OOS của lượt A (mô hình cũ) VÀO ở phiên KỊCH TRẦN hoặc RA ở
  phiên KỊCH SÀN phải KHÁC ở lượt B (mô hình mới): biến mất, hoặc ngày vào/ra
  khác. Giống hệt nghĩa là mã sửa không chạy trên đường walk-forward.
- **Số đếm của B:** lệnh `HUY` vì kịch trần (`paper_trading.LY_DO_KICH_TRAN`);
  lệnh ra NGAY SAU một chuỗi phiên kịch sàn, và chuỗi dài nhất.

Phiên khoá dùng ĐÚNG `vong_doi_lenh.khoa_bien`, biên độ của sàn tra theo mã
(`san_giao_dich.san_cua`, `data_quality.EXCHANGE_LIMITS`) — một định nghĩa, không
bản sao thứ hai. Tham chiếu = giá đóng cửa phiên trước, như `paper_runner`.

    ./.venv/Scripts/python.exe tools/do28_khoa_bien.py \\
        --a <A/wf_oos.db> --b <B/wf_oos.db> --cache <thư mục CSV>

CHỈ ĐỌC: DB mở `mode=ro`. Mã thoát 0 = (iii) đạt · 1 = (iii) trượt · 2 = chưa
kiểm được (thiếu tệp, hoặc quần thể (iii) RỖNG — khi ấy không có ca nào chứng minh
mã sửa đã chạy, và "đạt" sẽ là một kết quả âm không có khả năng ra dương).
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
for _p in (GOC, GOC / "tools"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

for _luong in (sys.stdout, sys.stderr):   # stderr: BƯỚC 129
    try:
        _luong.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from data_quality import EXCHANGE_LIMITS            # noqa: E402
from do20_ghep_tung_lenh import doc_so              # noqa: E402
from san_giao_dich import san_cua                   # noqa: E402
from vong_doi_lenh import KICH_SAN, KICH_TRAN, khoa_bien  # noqa: E402


def nap_khoa(cache: Path, ma: str) -> tuple[list[str], dict[str, str]]:
    """(các NGÀY của mã theo thứ tự, {ngày: KICH_TRAN|KICH_SAN}). Thiếu tệp hoặc sàn
    không có biên độ thì ([], {}): không phân được, không đoán."""
    p = Path(cache) / f"{ma}.csv"
    bien = EXCHANGE_LIMITS.get(str(san_cua(ma)).upper())
    if not p.is_file() or bien is None:
        return [], {}
    dong = []
    with open(p, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            try:
                dong.append((str(r["time"])[:10], float(r["high"]), float(r["low"]),
                             float(r["close"])))
            except (KeyError, TypeError, ValueError):
                continue
    dong.sort()
    khoa: dict[str, str] = {}
    for i in range(1, len(dong)):
        ngay, cao, thap, _ = dong[i]
        k = khoa_bien({"high": cao, "low": thap, "tham_chieu": dong[i - 1][3]}, bien)
        if k:
            khoa[ngay] = k
    return [d[0] for d in dong], khoa


def _ngay(x) -> str:
    return str(x or "")[:10]


def ca_dinh_khoa(a: dict, khoa: dict[str, dict[str, str]]) -> list[tuple]:
    """Khoá (mã, ngày tín hiệu) của lệnh A đã có giá vào mà VÀO ở phiên KỊCH TRẦN hoặc
    RA ở phiên KỊCH SÀN — quần thể của đối chứng (iii)."""
    ra = []
    for k, d in sorted(a.items()):
        if d["entry_price"] is None:
            continue
        km = khoa.get(d["symbol"], {})
        if km.get(_ngay(d["entry_date"])) == KICH_TRAN or \
                km.get(_ngay(d["exit_date"])) == KICH_SAN:
            ra.append(k)
    return ra


def doi_chung_iii(a: dict, b: dict, ca: list[tuple]) -> list[tuple[tuple, str]]:
    """[(khoá, 'biến mất' | 'khác' | 'GIỐNG')] — 'GIỐNG' là trượt."""
    ra = []
    for k in ca:
        if k not in b:
            ra.append((k, "biến mất"))
            continue
        x, y = a[k], b[k]
        giong = (_ngay(x["entry_date"]) == _ngay(y["entry_date"])
                 and _ngay(x["exit_date"]) == _ngay(y["exit_date"])
                 and x["status"] == y["status"])
        ra.append((k, "GIỐNG" if giong else "khác"))
    return ra


def dem_b(b: dict, ngay_cua: dict[str, list[str]], khoa: dict[str, dict[str, str]],
          ly_do_kich_tran: str) -> dict:
    """Số đếm của lượt B: `HUY` vì kịch trần; lệnh đã đóng có chuỗi phiên KỊCH SÀN
    NGAY TRƯỚC ngày ra (độ dài chuỗi = số phiên bán bị dời nếu lệnh đã chạm lệnh dừng)."""
    huy = sorted(k for k, d in b.items()
                 if d["status"] == "HUY" and d["exit_reason"] == ly_do_kich_tran)
    chuoi: dict[tuple, int] = {}
    for k, d in b.items():
        if d["status"] != "CLOSED" or d["entry_price"] is None:
            continue
        ds, km = ngay_cua.get(d["symbol"], []), khoa.get(d["symbol"], {})
        ra = _ngay(d["exit_date"])
        if ra not in ds:
            continue
        i, n = ds.index(ra) - 1, 0
        while i >= 0 and ds[i] > _ngay(d["entry_date"]) and km.get(ds[i]) == KICH_SAN:
            n, i = n + 1, i - 1
        if n:
            chuoi[k] = n
    return {"huy_kich_tran": huy, "ra_sau_chuoi_kich_san": chuoi,
            "chuoi_dai_nhat": max(chuoi.values(), default=0)}


def _dong(d: dict) -> str:
    return (f"vào {_ngay(d['entry_date']) or '-'} {d['entry_price']} · ra {_ngay(d['exit_date']) or '-'} "
            f"{d['exit_price']} {d['exit_reason']} · {d['status']}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--a", required=True, type=Path, help="wf_oos.db của lượt A (mô hình cũ)")
    ap.add_argument("--b", required=True, type=Path, help="wf_oos.db của lượt B (mô hình mới)")
    ap.add_argument("--cache", required=True, type=Path, help="thư mục CSV của lượt đo")
    a_ = ap.parse_args(argv)
    for p in (a_.a, a_.b):
        if not p.is_file():
            print(f"CHƯA KIỂM ĐƯỢC: không có {p}")
            return 2
    if not a_.cache.is_dir():
        print(f"CHƯA KIỂM ĐƯỢC: không có thư mục cache {a_.cache}")
        return 2
    import paper_trading

    a, b = doc_so(a_.a), doc_so(a_.b)
    ma = sorted({d["symbol"] for d in (*a.values(), *b.values())})
    ngay_cua, khoa = {}, {}
    for m in ma:
        ngay_cua[m], khoa[m] = nap_khoa(a_.cache, m)
    so_khoa = sum(len(v) for v in khoa.values())
    print(f"lệnh A: {len(a)} · lệnh B: {len(b)} · mã: {len(ma)} · phiên khoá biên của các mã ấy: "
          f"{so_khoa} (trần {sum(1 for v in khoa.values() for x in v.values() if x == KICH_TRAN)}, "
          f"sàn {sum(1 for v in khoa.values() for x in v.values() if x == KICH_SAN)})")

    ca = ca_dinh_khoa(a, khoa)
    kq = doi_chung_iii(a, b, ca)
    print(f"\n(iii) lệnh A vào ở KỊCH TRẦN hoặc ra ở KỊCH SÀN: {len(ca)}")
    for k, nhan in kq:
        print(f"  {nhan:<8} {k[0]} tín hiệu {k[1]}")
        print(f"           A: {_dong(a[k])}")
        print(f"           B: {_dong(b[k]) if k in b else '(không có)'}")

    d = dem_b(b, ngay_cua, khoa, paper_trading.LY_DO_KICH_TRAN)
    print(f"\nB — HUY vì kịch trần: {len(d['huy_kich_tran'])} {d['huy_kich_tran']}")
    print(f"B — lệnh ra ngay sau chuỗi phiên kịch sàn: {len(d['ra_sau_chuoi_kich_san'])} · "
          f"chuỗi dài nhất {d['chuoi_dai_nhat']} phiên")
    for k, n in sorted(d["ra_sau_chuoi_kich_san"].items()):
        print(f"  {k[0]} tín hiệu {k[1]}: {n} phiên · B: {_dong(b[k])}")

    if not ca:
        print("\n(iii) CHƯA KIỂM ĐƯỢC: quần thể rỗng — không có ca nào chứng minh mã sửa đã chạy.")
        return 2
    truot = [k for k, nhan in kq if nhan == "GIỐNG"]
    print(f"\n(iii) {'TRƯỢT' if truot else 'ĐẠT'}: {len(ca) - len(truot)}/{len(ca)} lệnh khác ở B")
    return 1 if truot else 0


if __name__ == "__main__":
    sys.exit(main())
