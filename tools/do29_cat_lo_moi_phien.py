"""ĐO 29 — đối chứng (iii), (iv) và số đếm của walk-forward xét cắt lỗ ở MỌI phiên.

Tiêu chí: `docs/TIEU-CHI-DOC-TRUOC.md` mục ĐO 29 (ký ở `c4d01ed`, TRƯỚC dụng cụ này).
Alpha và KTC đọc ở log walk-forward của hai lượt; ghép từng lệnh bằng
`tools/do20_ghep_tung_lenh.py`. Dụng cụ này trả lời phần còn lại:

- **(iii) ca thật:** ở lượt B, lệnh GIL tín hiệu 14/12/2022 ra ngày 21/12/2022 bằng
  `STOP_LOSS`, giá ≤ 13.590 (giá mở cửa phiên ấy, trước trượt) — ca BƯỚC 209 tìm ra.
- **(iv)** lượt A có 0 lệnh ra bằng `STOP_LOSS` ở phiên CHỈ-KHỚP, lượt B có > 0.
- **Số đếm:** lệnh B ra bằng cắt lỗ ở phiên chỉ-khớp; với lệnh chung khoá A ↔ B mà
  ngày ra khác: lợi nhuận (giá ra ÷ giá vào − 1) đổi trung bình bao nhiêu, và ra sớm
  hơn bao nhiêu phiên.

Lịch phiên chỉ-khớp dựng bằng ĐÚNG các hàm của máy đo — `walkforward.chia_vung`
(vùng OOS theo mốc dữ liệu sạch) rồi `walkforward.diem_ghe` — với `stride`,
`min_history`, `do_tre_khop` lấy từ mặc định của `walkforward.chay` (lượt
`do1 --mot-luot 2` không truyền gì), không gõ tay.

    ./.venv/Scripts/python.exe tools/do29_cat_lo_moi_phien.py \\
        --a <A/wf_oos.db> --b <B/wf_oos.db> --cache <thư mục CSV>

CHỈ ĐỌC: DB mở `mode=ro`. Mã thoát 0 = (iii) và (iv) đạt · 1 = một trong hai trượt ·
2 = chưa kiểm được (thiếu tệp, hoặc không dựng được lịch phiên chỉ-khớp nào).
"""
from __future__ import annotations

import argparse
import inspect
import statistics
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

import walkforward                                  # noqa: E402
from do20_ghep_tung_lenh import doc_so              # noqa: E402

#: Ca thật đã ký ở (iii): (mã, ngày tín hiệu), ngày ra phải là, giá ra tối đa (VNĐ).
CA_GIL = ("GIL", "2022-12-14")
NGAY_RA_GIL = "2022-12-21"
GIA_RA_GIL_TOI_DA = 13_590.0
CAT_LO = "STOP_LOSS"


def tham_so_luot() -> dict:
    """`stride`, `min_history`, `do_tre_khop` mà `walkforward.chay` dùng khi không ai
    truyền — đúng cấu hình của `do1 --mot-luot 2`."""
    ps = inspect.signature(walkforward.chay).parameters
    return {k: ps[k].default for k in ("stride", "min_history", "do_tre_khop")}


def lich_mot_ma(df, moc: str, stride: int, min_history: int,
                do_tre_khop) -> tuple[list[str], set[str]]:
    """(mọi NGÀY của vùng OOS theo thứ tự, tập ngày CHỈ-KHỚP) của một mã."""
    oos, _ = walkforward.chia_vung(df, moc)
    oos = oos.reset_index(drop=True)
    ngay = [str(x)[:10] for x in oos["time"]]
    ck = {ngay[t] for t, chi_khop in walkforward.diem_ghe(len(oos), min_history, stride,
                                                          do_tre_khop) if chi_khop}
    return ngay, ck


def nap_lich(cache: Path, cac_ma: list[str], ts: dict) -> tuple[dict, dict]:
    """({mã: ngày OOS}, {mã: ngày chỉ-khớp}) — đọc CSV bằng `backtest.data.load`."""
    import backtest.data as bd
    moc = walkforward.nap_moc_sach()
    cu = bd.CACHE_DIR
    bd.CACHE_DIR = Path(cache)
    try:
        ngay_cua, ck = {}, {}
        for ma in cac_ma:
            df = bd.load(ma)
            if df is None or ma not in moc:
                continue
            ngay_cua[ma], ck[ma] = lich_mot_ma(df, moc[ma], ts["stride"],
                                               ts["min_history"], ts["do_tre_khop"])
    finally:
        bd.CACHE_DIR = cu
    return ngay_cua, ck


def _ngay(x) -> str:
    return str(x or "")[:10]


def cat_lo_chi_khop(so: dict, ck: dict[str, set[str]]) -> list[tuple]:
    """Khoá (mã, ngày tín hiệu) của lệnh đã đóng bằng cắt lỗ ở một phiên CHỈ-KHỚP."""
    return sorted(k for k, d in so.items()
                  if d["status"] == "CLOSED" and d["exit_reason"] == CAT_LO
                  and _ngay(d["exit_date"]) in ck.get(d["symbol"], set()))


def doi_chung_iii(b: dict) -> tuple[bool, str]:
    """(đạt?, mô tả) cho ca GIL ở lượt B."""
    d = b.get(CA_GIL)
    if d is None:
        return False, "không có lệnh GIL tín hiệu 14/12/2022 ở B"
    dat = (d["status"] == "CLOSED" and d["exit_reason"] == CAT_LO
           and _ngay(d["exit_date"]) == NGAY_RA_GIL
           and d["exit_price"] is not None and float(d["exit_price"]) <= GIA_RA_GIL_TOI_DA)
    return dat, _dong(d)


def _loi(d: dict) -> float | None:
    try:
        return float(d["exit_price"]) / float(d["entry_price"]) - 1.0
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def doi_ngay_ra(a: dict, b: dict, ngay_cua: dict[str, list[str]]) -> list[dict]:
    """Lệnh chung khoá, cùng ngày vào, ngày ra KHÁC: Δ lợi nhuận và số phiên ra sớm."""
    ra = []
    for k in sorted(set(a) & set(b)):
        x, y = a[k], b[k]
        if x["status"] != "CLOSED" or y["status"] != "CLOSED":
            continue
        if _ngay(x["entry_date"]) != _ngay(y["entry_date"]) or \
                _ngay(x["exit_date"]) == _ngay(y["exit_date"]):
            continue
        la, lb = _loi(x), _loi(y)
        ds = ngay_cua.get(x["symbol"], [])
        som = (ds.index(_ngay(x["exit_date"])) - ds.index(_ngay(y["exit_date"]))
               if _ngay(x["exit_date"]) in ds and _ngay(y["exit_date"]) in ds else None)
        ra.append({"khoa": k, "delta": None if la is None or lb is None else lb - la,
                   "som_hon": som})
    return ra


def _dong(d: dict) -> str:
    return (f"vào {_ngay(d['entry_date']) or '-'} {d['entry_price']} · ra {_ngay(d['exit_date']) or '-'} "
            f"{d['exit_price']} {d['exit_reason']} · {d['status']}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--a", required=True, type=Path, help="wf_oos.db của lượt A (máy đo cũ)")
    ap.add_argument("--b", required=True, type=Path, help="wf_oos.db của lượt B (ĐO 29)")
    ap.add_argument("--cache", required=True, type=Path, help="thư mục CSV của lượt đo")
    a_ = ap.parse_args(argv)
    for p in (a_.a, a_.b):
        if not p.is_file():
            print(f"CHƯA KIỂM ĐƯỢC: không có {p}")
            return 2
    if not a_.cache.is_dir():
        print(f"CHƯA KIỂM ĐƯỢC: không có thư mục cache {a_.cache}")
        return 2

    a, b = doc_so(a_.a), doc_so(a_.b)
    ts = tham_so_luot()
    cac_ma = sorted({d["symbol"] for d in (*a.values(), *b.values())})
    ngay_cua, ck = nap_lich(a_.cache, cac_ma, ts)
    so_ck = sum(len(v) for v in ck.values())
    print(f"lệnh A: {len(a)} · lệnh B: {len(b)} · mã: {len(cac_ma)} · tham số lượt {ts}")
    print(f"phiên chỉ-khớp dựng được: {so_ck} trên {len(ck)} mã")
    if not so_ck:
        print("CHƯA KIỂM ĐƯỢC: không dựng được phiên chỉ-khớp nào — (iv) không thể ra dương.")
        return 2

    ca, cb = cat_lo_chi_khop(a, ck), cat_lo_chi_khop(b, ck)
    dat_iv = not ca and bool(cb)
    print(f"\n(iv) cắt lỗ ở phiên chỉ-khớp: A {len(ca)} · B {len(cb)} → "
          f"{'ĐẠT' if dat_iv else 'TRƯỢT'} (cần A = 0, B > 0)")
    for k in ca:
        print(f"  A {k[0]} tín hiệu {k[1]}: {_dong(a[k])}")
    for k in cb:
        print(f"  B {k[0]} tín hiệu {k[1]}: {_dong(b[k])}")
        print(f"      A: {_dong(a[k]) if k in a else '(không có)'}")

    dat_iii, mo_ta = doi_chung_iii(b)
    print(f"\n(iii) ca GIL tín hiệu 14/12/2022 ở B: {'ĐẠT' if dat_iii else 'TRƯỢT'} — {mo_ta}")
    print(f"      cần: ra {NGAY_RA_GIL} bằng {CAT_LO}, giá ≤ {GIA_RA_GIL_TOI_DA:,.0f}")
    if CA_GIL in a:
        print(f"      A: {_dong(a[CA_GIL])}")

    doi = doi_ngay_ra(a, b, ngay_cua)
    delta = [x["delta"] for x in doi if x["delta"] is not None]
    som = [x["som_hon"] for x in doi if x["som_hon"] is not None]
    print(f"\nlệnh chung khoá, cùng ngày vào, ngày ra khác: {len(doi)}")
    if delta:
        print(f"  Δ lợi nhuận (B − A), trước phí: trung bình {statistics.mean(delta) * 100:+.3f} điểm"
              f" · trung vị {statistics.median(delta) * 100:+.3f} · nhỏ nhất {min(delta) * 100:+.2f}"
              f" · lớn nhất {max(delta) * 100:+.2f}")
    if som:
        dem = {s: som.count(s) for s in sorted(set(som))}
        print(f"  B ra sớm hơn A (số phiên OOS): {dem}")
    for x in doi:
        k = x["khoa"]
        d_txt = "-" if x["delta"] is None else f"{x['delta'] * 100:+.2f}"
        print(f"  {k[0]} tín hiệu {k[1]}: Δ {d_txt}"
              f" · sớm {x['som_hon']} · A {_ngay(a[k]['exit_date'])} {a[k]['exit_reason']}"
              f" · B {_ngay(b[k]['exit_date'])} {b[k]['exit_reason']}")
    return 0 if (dat_iii and dat_iv) else 1


if __name__ == "__main__":
    sys.exit(main())
