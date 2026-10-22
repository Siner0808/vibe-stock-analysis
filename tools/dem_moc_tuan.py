"""Đếm tiêu chí ra khỏi giai đoạn A của lộ trình — CHỈ ĐỌC `docs/STATE.md`.

VÌ SAO CÓ FILE NÀY (BƯỚC 218, 22/10/2026)
──────────────────────────────────────────
`docs/LO-TRINH.md`, giai đoạn A: *"Ra khỏi giai đoạn khi: ít nhất 2/3 số BƯỚC mỗi
tuần phục vụ một mốc sản phẩm"* (mốc sản phẩm = mọi mã trừ nhóm A và `quy-trinh`),
kèm câu *"chưa có công cụ đếm"*. Trước file này chỉ có hai lượt đếm bằng script nháp
của leader: 17/10 (`docs/STATE.md` BƯỚC 203: W41 10/15, W42 15/24 lúc tuần chưa hết)
và 22/10 (W41 đạt, W42 và W43 không). Hạn giai đoạn A là 25/10/2026; người dùng chọn
*"Vào B đúng lịch + dựng công cụ đếm (Recommended)"*.

Đọc bằng ĐÚNG bộ tách của gác Mốc (`tools/moc_lo_trinh.py`: `tach_muc_buoc`,
`tach_dau_ly_do`, `cac_ma`) — mã nhắc trong LÝ DO của dòng Mốc không được đếm.
Ngày lấy ở cuối tiêu đề `## BƯỚC n — … (dd/mm/yyyy)`; tiêu đề không có ngày thì
BƯỚC ấy được liệt kê riêng, không lặng lẽ rơi khỏi quần thể.

Máy KHÔNG đọc được mã khai có đúng với việc đã làm không — mã do chính BƯỚC tự
khai (cùng giới hạn đã ghi trong docstring của `tools/moc_lo_trinh.py`).
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import moc_lo_trinh as mlt  # noqa: E402

#: Tỷ lệ của LO-TRINH (giai đoạn A): ít nhất 2/3 — so bằng số nguyên, không float.
TU_SO, MAU_SO = 2, 3

SAN_PHAM = "san-pham"
NHOM_A = "nhom-A"
QUY_TRINH = mlt.QUY_TRINH
THIEU = "thieu-moc"

RE_NGAY_TIEU_DE = re.compile(r"\((\d{1,2})/(\d{1,2})/(\d{4})\)\s*$")


def loai_moc(noi: str | None) -> str:
    """Loại của MỘT dòng Mốc: san-pham · nhom-A · quy-trinh · thieu-moc. HÀM THUẦN."""
    if not noi:
        return THIEU
    dau, _ = mlt.tach_dau_ly_do(noi)
    if dau.strip().lower() == QUY_TRINH:
        return QUY_TRINH
    ma = [t for t in mlt.cac_ma(dau) if mlt.RE_MA.fullmatch(t)]
    if not ma:
        return THIEU
    return SAN_PHAM if any(not t.startswith("A") for t in ma) else NHOM_A


def doc_buoc(van_state: str, tu: int = mlt.TU_BUOC) -> tuple[list[dict], list[int]]:
    """([{n, ngay, loai, moc}], [n không đọc được ngày]). HÀM THUẦN."""
    muc = mlt.tach_muc_buoc(van_state, tu)
    tieu_de: dict[int, str] = {}
    for d in van_state.splitlines():
        m = mlt.RE_TIEU_DE_BUOC.match(d)
        if m and int(m.group(1)) in muc:
            tieu_de.setdefault(int(m.group(1)), d)
    ra, khong_ngay = [], []
    for n in sorted(muc):
        k = RE_NGAY_TIEU_DE.search(tieu_de[n].rstrip())
        if not k:
            khong_ngay.append(n)
            continue
        noi = next((m.group(1) for d in muc[n] if (m := mlt.RE_DONG_MOC.match(d))), None)
        ra.append({"n": n, "ngay": date(int(k.group(3)), int(k.group(2)), int(k.group(1))),
                   "loai": loai_moc(noi), "moc": noi or ""})
    return ra, khong_ngay


def dem_theo_tuan(buoc: list[dict], hom_nay: date) -> list[dict]:
    """Một dòng mỗi tuần ISO: số BƯỚC, số phục vụ sản phẩm, đạt ≥ 2/3 không, tuần đã hết chưa."""
    tuan: dict[tuple[int, int], list[dict]] = defaultdict(list)
    for b in buoc:
        nam, so, _ = b["ngay"].isocalendar()
        tuan[(nam, so)].append(b)
    nay = hom_nay.isocalendar()[:2]
    ra = []
    for (nam, so), ds in sorted(tuan.items()):
        sp = sum(1 for b in ds if b["loai"] == SAN_PHAM)
        ra.append({"tuan": f"{nam}-W{so:02d}", "so_buoc": len(ds), "san_pham": sp,
                   "dat": MAU_SO * sp >= TU_SO * len(ds),
                   "da_het": (nam, so) < nay, "buoc": ds})
    return ra


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--tu", type=int, default=mlt.TU_BUOC, help="BƯỚC đầu tiên được đếm")
    ap.add_argument("--tho", action="store_true", help="in thêm từng BƯỚC dưới bảng")
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    buoc, khong_ngay = doc_buoc(mlt.doc_van_state(), a.tu)
    print(f"Tiêu chí ra khỏi giai đoạn A: ≥ {TU_SO}/{MAU_SO} số BƯỚC mỗi tuần phục vụ mốc "
          f"sản phẩm (mọi mã trừ nhóm A và quy-trinh). Mã do BƯỚC tự khai.")
    print("Tuần ISO | BƯỚC | sản phẩm | tỷ lệ | đạt?  | tuần")
    for t in dem_theo_tuan(buoc, date.today()):
        print(f"{t['tuan']} | {t['so_buoc']:4d} | {t['san_pham']:8d} | "
              f"{t['san_pham'] / t['so_buoc']:5.0%} | {'ĐẠT ' if t['dat'] else 'không'} | "
              f"{'đã hết' if t['da_het'] else 'CHƯA HẾT'}")
        if a.tho:
            for b in t["buoc"]:
                print(f"    BƯỚC {b['n']} {b['ngay'].isoformat()} {b['loai']:9s} | {b['moc'][:70]}")
    if khong_ngay:
        print(f"Không đọc được ngày ở tiêu đề (KHÔNG đếm): BƯỚC {khong_ngay}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
