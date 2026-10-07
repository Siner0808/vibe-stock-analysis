"""Chạy MÁY CHẤM XÁC NHẬN của tầng 3 trên một bảng giá và một tệp quyết định (P3d, BƯỚC 161).

CHỈ IN ra màn hình: không ghi app, không ghi Google Sheets, không ghi file, không gọi mạng.
Nối kết quả vào tab "🔬 Kiểm định chiến lược" là việc SAU, làm trên máy.

    ./.venv/Scripts/python.exe tools/cham_xac_nhan.py \
        --bang-gia <bang_gia.csv> --quyet-dinh <decisions.json|decisions.csv>

Định dạng bảng giá, luật "một lượt kéo", biên `khai_ngay`: docstring của `cham_xac_nhan`.
Mã thoát: 0 chấm xong (mọi trạng thái, kể cả chưa đủ dữ liệu) · 1 TỪ CHỐI bảng giá hoặc
dữ liệu (nói rõ lý do) · 2 dùng sai lệnh.
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import cham_bong as cb  # noqa: E402
import cham_xac_nhan as cx  # noqa: E402


def _so(x: float, mau: str) -> str:
    return "chua tinh (NaN)" if math.isnan(x) else format(x, mau)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bang-gia", required=True, help="CSV dài một lượt kéo")
    ap.add_argument("--quyet-dinh", required=True, help="dòng tab decisions: .json hoặc .csv")
    ap.add_argument("--ung-vien", default=str(cb.SO_UNG_VIEN), help="sổ ứng viên (mặc định docs/ung-vien.json)")
    ap.add_argument("--hat", type=int, default=cx.HAT_RNG, help=f"hạt RNG (mặc định {cx.HAT_RNG})")
    ap.add_argument("--so-hoan-vi", type=int, default=cx.SO_HOAN_VI,
                    help=f"số lượt hoán vị (mặc định {cx.SO_HOAN_VI})")
    a = ap.parse_args(argv)
    try:
        bg = cx.doc_bang_gia(a.bang_gia)
        rows = cx.doc_dong_quyet_dinh(a.quyet_dinh)
        so = cb.doc_so_ung_vien(Path(a.ung_vien))
        kq = cx.cham(rows, so, bg, hat=a.hat, so=a.so_hoan_vi)
    except (cx.BangGiaLoi, ValueError, OSError) as e:
        print(f"TU CHOI: {e}")
        return 1
    print(f"bang gia   : {kq['n_ma_bang_gia']} ma · {kq['phien_dau']} .. {kq['phien_cuoi']} · "
          f"nguon {','.join(kq['nguon'])} · keo luc {kq['keo_luc']}")
    print(f"lich       : doi chieu {kq['lich']['kiem_duoc']} ngay voi lich cong bo · "
          f"{kq['lich']['ngoai_lich']} ngay NGOAI lich (chua kiem duoc)")
    print(f"quyet dinh : {len(rows)} dong tho")
    print(f"so         : K = {kq['K']} · nguong 0,05/K = {kq['nguong']:.4f} · hat {kq['hat']} · "
          f"{kq['so_hoan_vi']} luot hoan vi · bien khai_ngay {cx.BIEN_KHAI_NGAY!r}")
    for ma, c in kq["chi_tiet"].items():
        print(f"\n{ma}  khai {c['khai_ngay']}  du lieu tu {c['tu_ngay']}")
        print(f"  trang thai : {c['trang_thai']}")
        print(f"  dong       : {c['n_dong']} dung · {c['n_dong_bo']} bo (thieu thanh phan / JSON hong) · "
              f"{c['n_phien_quyet_dinh']} phien co quyet dinh · {len(c['phien_chua_co_nhan'])} phien chua co nhan")
        print(f"  ma tran    : {c['n_phien']} phien co nhan x {c['n_ma']} ma day du "
              f"(can >= {cb.NHIP} phien va >= {cb.MIN_MA} ma)")
        print(f"  delta      : {_so(c['delta'], '+.4f')}")
        print(f"  p          : {_so(c['p'], '.4f')}   z {_so(c['z'], '+.2f')}   (nguong {c['nguong']:.4f})")
    print("\nBANG CONG KHAI (ten noi bo):")
    print(cb.bang_cong_khai(so, kq["ket"])[["Ứng viên", "Khai ngày", "Sàng", "Trạng thái"]]
          .to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main())
