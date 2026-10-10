"""In BẢNG SỨC KHOẺ HỆ THỐNG ra màn hình — CHỈ ĐỌC (BƯỚC 177, mốc B4).

    ./.venv/Scripts/python.exe tools/suc_khoe.py [--chi ten1,ten2] [--ds]

Chạy TUẦN TỰ các phép kiểm trong `suc_khoe.DANH_MUC` (chuông quét, chuông nguồn
đứng, chuông cổng C5, chuông bài học, lệch bản gói, hạng gói, bộ lọc VN-INDEX, cửa
tự động, đường ngoài repo, soát tuần) rồi in một bảng: tên · trạng thái · chi tiết ·
lệnh tái lập. `--ds` chỉ liệt kê tên các phép. Có phép đi mạng / kéo sổ Sheets nên
cả bảng có thể mất vài phút; không chạy tự động ở đâu cả.

Mã thoát: 0 mọi phép XANH (hoặc VANG, cảnh báo của chính công cụ) · 1 có phép DO ·
2 không có DO nhưng có phép CHUA_KIEM_DUOC (hoặc không phép nào chạy) · 3 dùng sai
lệnh (tên phép lạ). CHUA_KIEM_DUOC không bao giờ là XANH.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
# `tools/` có file cùng tên với module gốc `suc_khoe.py` (như `ban_tin`): đặt GOC SAU
# CÙNG để nó đứng TRƯỚC `tools/` và `import suc_khoe` ra module thuần.
sys.path.insert(0, str(GOC / "tools"))
sys.path.insert(0, str(GOC))

for _luong in (sys.stdout, sys.stderr):
    try:
        _luong.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import suc_khoe  # noqa: E402

MA_SAI_LENH = 3

NHAN = {suc_khoe.XANH: "XANH", suc_khoe.VANG: "VANG", suc_khoe.DO: "DO",
        suc_khoe.CHUA_KIEM_DUOC: "CHUA KIEM DUOC"}


def dong_bang(k: "suc_khoe.KetQua") -> list[str]:
    """Các dòng in của MỘT kết quả: tiêu đề, tối đa 3 dòng chi tiết, lệnh tái lập."""
    ra = [f"{k.ten:<22} {NHAN[k.trang_thai]:<15} ({k.thoi_gian_giay:g}s)"]
    ra += [f"    | {d}" for d in k.chi_tiet]
    ra.append(f"    $ {k.lenh_tai_lap}")
    return ra


def main(argv: list[str] | None = None, kiem=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--chi", help="chỉ chạy các phép này (tên cách nhau bởi dấu phẩy)")
    ap.add_argument("--ds", action="store_true", help="liệt kê tên các phép rồi thoát")
    a = ap.parse_args(argv)

    if a.ds:
        for p in suc_khoe.DANH_MUC:
            print(f"{p.ten:<22} {p.mo_ta}")
        return 0

    chon = None
    if a.chi is not None:
        chon = [t.strip() for t in a.chi.split(",") if t.strip()]
    chay = kiem if kiem is not None else suc_khoe.kiem_tat_ca
    try:
        ket_qua = chay(chon)
    except ValueError as e:
        print(f"Dùng sai lệnh: {e}", file=sys.stderr)
        return MA_SAI_LENH

    print("BẢNG SỨC KHOẺ HỆ THỐNG (chỉ đọc)")
    print("=" * 62)
    for k in ket_qua:
        for d in dong_bang(k):
            print(d)
    print("=" * 62)
    dem = {tt: sum(1 for k in ket_qua if k.trang_thai == tt) for tt in suc_khoe.TRANG_THAI}
    print("  ".join(f"{NHAN[tt]}: {dem[tt]}" for tt in suc_khoe.TRANG_THAI))
    ma = suc_khoe.ma_thoat_tong(ket_qua)
    if ma == 2 and dem[suc_khoe.CHUA_KIEM_DUOC] == 0:
        print("Không phép nào chạy — không có gì để gọi là xanh.")
    return ma


if __name__ == "__main__":
    sys.exit(main())
