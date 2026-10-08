"""KÉO bảng giá MỘT lượt cho máy chấm xác nhận của tầng 3 (P3d, BƯỚC 162).

CHẠY THẬT là việc trên MÁY người dùng (cần gói vnstock và mạng giá). Phiên đám mây
không chạy được lệnh này: nó chỉ có test bằng hàm kéo GIẢ.

    ./.venv/Scripts/python.exe tools/keo_bang_gia.py \
        --quyet-dinh <decisions.json|decisions.csv> --ra <bang_gia.csv>

Đầu ra là CSV dài `symbol,date,close,nguon,keo_luc` đúng định dạng `cham_xac_nhan`
(đọc bằng `tools/cham_xac_nhan.py --bang-gia`). Danh sách mã: `--ma A,B,C` hoặc mọi mã có
trong tệp quyết định. `--tu` mặc định là ngày đầu của dữ liệu chấm sớm nhất trong sổ
phương án (`cham_xac_nhan.tu_ngay_doc`); `--den` mặc định là hôm nay (giờ VN).

KHÔNG ghi gì cả nếu còn một mã kéo hỏng — mã thoát 1 và in TÊN từng mã kèm lý do. Tệp
`--ra` đã tồn tại thì từ chối (mở chế độ tạo mới): ghép hai lượt kéo vào một tệp là đúng
thứ `cham_xac_nhan` cấm, nên không có đường nào ghi đè hay ghi nối.

Mã thoát: 0 đã ghi tệp · 1 TỪ CHỐI (mã hỏng, nến cuối còn dở, thiếu gói, tệp đã có) ·
2 dùng sai lệnh.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import cham_bong as cb  # noqa: E402
import cham_xac_nhan as cx  # noqa: E402
import data_quality as dq  # noqa: E402
import keo_bang_gia as kg  # noqa: E402


def main(argv=None, lay=None, bay_gio=None, ngu=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    nguon = ap.add_mutually_exclusive_group(required=True)
    nguon.add_argument("--ma", help="mã cách nhau bằng dấu phẩy")
    nguon.add_argument("--quyet-dinh", help="tệp dòng tab decisions (.json/.csv): lấy mọi mã trong đó")
    ap.add_argument("--ra", required=True, help="tệp CSV sẽ tạo (phải CHƯA tồn tại)")
    ap.add_argument("--tu", help="ngày đầu YYYY-MM-DD (mặc định: dữ liệu chấm sớm nhất của sổ phương án)")
    ap.add_argument("--den", help="ngày cuối YYYY-MM-DD (mặc định: hôm nay giờ VN)")
    ap.add_argument("--ung-vien", default=str(cb.SO_UNG_VIEN), help="sổ phương án (mặc định docs/ung-vien.json)")
    ap.add_argument("--nghi-giay", type=float, default=kg.NGHI_GIAY,
                    help=f"giây nghỉ giữa hai mã (mặc định {kg.NGHI_GIAY})")
    a = ap.parse_args(argv)
    try:
        if a.ma:
            ma = [m for m in a.ma.split(",") if m.strip()]
        else:
            ma = sorted({str(r["symbol"]) for r in cx.doc_dong_quyet_dinh(a.quyet_dinh)})
        tu = a.tu or min(cx.tu_ngay_doc(d["khai_ngay"]) for d in
                         cb.doc_so_ung_vien(Path(a.ung_vien))["ung_vien"].values())
        den = a.den or dq.now_vn().date().isoformat()
        ra = Path(a.ra)
        if ra.exists():
            raise kg.KeoLoi(f"{ra} da ton tai: khong ghi de, khong ghi noi")
        kq = kg.keo(ma, tu, den, lay=lay, nghi_giay=a.nghi_giay, bay_gio=bay_gio,
                    **({"ngu": ngu} if ngu else {}))
    except (kg.KeoLoi, cx.BangGiaLoi, ValueError, KeyError, OSError) as e:
        print(f"TU CHOI: {e}")
        return 1
    if kq["hong"]:
        print(f"TU CHOI: {len(kq['hong'])}/{len(ma)} ma keo hong — KHONG ghi bang gia "
              f"(khong dien gia, khong bo ma):")
        for m, ly_do in sorted(kq["hong"].items()):
            print(f"  {m}: {ly_do}")
        return 1
    try:
        with ra.open("x", encoding="utf-8", newline="") as f:
            f.write(kq["van_ban"])
    except OSError as e:
        print(f"TU CHOI: khong ghi duoc {ra}: {e}")
        return 1
    g = kq["gia"]
    print(f"da ghi {ra}: {g.shape[1]} ma · {g.index[0]} .. {g.index[-1]} ({g.shape[0]} phien) · "
          f"nguon {','.join(sorted(set(kq['nguon'].values())))} · keo luc {kq['keo_luc']}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main())
