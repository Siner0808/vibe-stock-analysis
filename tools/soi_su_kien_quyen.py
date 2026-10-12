"""Soi sự kiện quyền rơi trong lúc giữ lệnh ảo — CHỈ ĐỌC (BƯỚC 176, mốc D2).

    ./.venv/Scripts/python.exe tools/soi_su_kien_quyen.py

Kéo sổ THẬT từ Google Sheets vào một DB TẠM (`tools/doc_so_that.keo_ve_so_tam`,
cùng đường với `tools/doc_so_that.py`), tải nến của nguồn giá HÔM NAY mỗi mã MỘT
lần (`nen_su_kien_quyen.tai_nen`, đường của app, nhân `price_multiplier`), rồi gắn
nhãn từng lệnh bằng `su_kien_quyen.kiem_lenh`. In bảng mọi lệnh KHÔNG `SACH`,
tổng theo trạng thái, và tách riêng lệnh CÒN MỞ. Không ghi sổ, không đẩy, không
sửa gì (gác AST: `tests/test_su_kien_quyen.py`).

BƯỚC 182 (Q14): bảng cuối in thêm danh sách lệnh mà ĐIỀU KIỆN DỪNG LOẠI khỏi mẫu,
tính bằng ĐÚNG hàm `nen_su_kien_quyen.loai_tu_nen` mà `run_daily` và
`tools/canh_cong_c5.py` dùng (qua `tap_loai`) — hai danh sách phải trùng nhau.
Dụng cụ này vẫn chỉ đọc: loại là việc của `paper_metrics.dieu_kien_dong_lai`.

Mã thoát: 0 không có lệnh `SU_KIEN_TRONG_LUC_GIU` · 1 có · 2 không đọc được sổ.
"""
from __future__ import annotations

import datetime
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))
sys.path.insert(0, str(GOC))

for _luong in (sys.stdout, sys.stderr):
    try:
        _luong.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import doc_so_that  # noqa: E402
import nen_su_kien_quyen as nsk  # noqa: E402
import su_kien_quyen as skq  # noqa: E402
from so_lenh_app import TRANG_THAI_DONG, TRANG_THAI_MO  # noqa: E402

#: Đường tải nến nằm ở `nen_su_kien_quyen` (BƯỚC 182) để điều kiện dừng dùng CHUNG;
#: hai tên cũ giữ lại cho chỗ gọi và test sẵn có.
_tai_that = nsk.tai_that
tai_nen = nsk.tai_nen


def in_bang(dong: list[skq.DongSoi]) -> None:
    """Bảng lệnh không SACH."""
    def so(x):
        return "—" if x is None else f"{x:.3f}"
    print(f"{'id':>4} {'mã':<5} {'vào':<10} {'ra':<10} {'lệnh':<6} {'f_vào':>6} "
          f"{'f_ra':>6}  {'nhãn':<22} lý do")
    for d in dong:
        k = d.ket_qua
        print(f"{d.id:>4} {d.ma:<5} {d.ngay_vao or '—':<10} {d.ngay_ra or '—':<10} "
              f"{'ĐÓNG' if d.da_dong else 'MỞ':<6} {so(k.he_so_vao):>6} "
              f"{so(k.he_so_ra):>6}  {k.trang_thai:<22} {k.ly_do}")


def main(keo=None, tai=_tai_that, hom_nay=None) -> int:
    ra = (keo or doc_so_that.keo_ve_so_tam)()
    if ra is None:
        print("CHUA DOC DUOC SO — kho ngoai chua cau hinh. Khong doan gi ca.",
              file=sys.stderr)
        return 2
    so, _bao_cao = ra
    trades = so.all_trades()
    vi_the_mo = [t for t in trades if t.status in TRANG_THAI_MO]
    lenh_dong = [t for t in trades if t.status in TRANG_THAI_DONG]

    cac_ma, tu_ngay = skq.pham_vi_tai(vi_the_mo, lenh_dong)
    den_ngay = hom_nay or datetime.date.today().isoformat()
    nen, thieu = (({}, []) if tu_ngay is None
                  else tai_nen(cac_ma, tu_ngay, den_ngay, tai))

    dong = skq.soi_so(vi_the_mo, lenh_dong, nen)
    dem = skq.tom_tat(dong)
    print("=" * 70)
    print("SOI SU KIEN QUYEN — chi doc, chi gan nhan (BUOC 176)")
    print("=" * 70)
    print(f"{len(dong)} lệnh xét ({len(vi_the_mo)} mở/chờ · {len(lenh_dong)} đóng) · "
          f"nến {len(nen)}/{len(cac_ma)} mã · từ {tu_ngay or '—'} đến {den_ngay}")
    if thieu:
        print(f"Không tải được nến: {', '.join(thieu)} "
              "(lệnh của các mã này sẽ là KHONG_KIEM_DUOC)")

    khac = [d for d in dong if d.ket_qua.trang_thai != skq.SACH]
    print(f"\nLỆNH KHÔNG SẠCH: {len(khac)}/{len(dong)}")
    in_bang(khac)
    con_mo = [d for d in khac if not d.da_dong]
    print(f"\nTRONG ĐÓ LỆNH CÒN MỞ: {len(con_mo)}")
    in_bang(con_mo)

    print("\nTỔNG THEO TRẠNG THÁI:")
    for k, v in dem.items():
        print(f"  {k:<22} {v}")
    loai = nsk.loai_tu_nen(trades, nen)
    print(f"\nĐIỀU KIỆN DỪNG LOẠI KHỎI MẪU (tiến-về-trước, đã đóng, "
          f"{skq.SU_KIEN_TRONG_LUC_GIU}): {len(loai)} lệnh"
          + (": " + ", ".join(f"#{i}" for i in sorted(loai)) if loai else ""))
    print("Cùng hàm với run_daily và tools/canh_cong_c5.py (BƯỚC 182, Q14). Lệnh")
    print("còn mở, lệnh mô phỏng, KHONG_KIEM_DUOC và LECH_KHAC KHÔNG bị loại.")
    return 1 if dem[skq.SU_KIEN_TRONG_LUC_GIU] else 0


if __name__ == "__main__":
    raise SystemExit(main())
