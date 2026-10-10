"""Soi sự kiện quyền rơi trong lúc giữ lệnh ảo — CHỈ ĐỌC (BƯỚC 176, mốc D2).

    ./.venv/Scripts/python.exe tools/soi_su_kien_quyen.py

Kéo sổ THẬT từ Google Sheets vào một DB TẠM (`tools/doc_so_that.keo_ve_so_tam`,
cùng đường với `tools/doc_so_that.py`), tải nến của nguồn giá HÔM NAY mỗi mã MỘT
lần (`VNStockCollectorAgent().collect`, đường của app, nhân `price_multiplier`),
rồi gắn nhãn từng lệnh bằng `su_kien_quyen.kiem_lenh`. In bảng mọi lệnh KHÔNG
`SACH`, tổng theo trạng thái, và tách riêng lệnh CÒN MỞ. Không ghi sổ, không đẩy,
không sửa gì (gác AST: `tests/test_su_kien_quyen.py`).

Chỉ GẮN NHÃN. Việc loại các lệnh này khỏi điều kiện dừng là một bước riêng.

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
import su_kien_quyen as skq  # noqa: E402
from so_lenh_app import TRANG_THAI_DONG, TRANG_THAI_MO  # noqa: E402


def _tai_that(ma: str, tu_ngay: str, den_ngay: str):
    """(trạng thái, bảng OHLCV, hệ số VNĐ) của MỘT mã, qua đường của app."""
    from data_collectors import VNStockCollectorAgent
    from data_quality import price_multiplier
    import san_giao_dich

    kq = VNStockCollectorAgent().collect(
        ma, tu_ngay, den_ngay, exchange=san_giao_dich.san_cua(ma))
    df = kq.get("df")
    return kq.get("status"), df, price_multiplier(df)


def tai_nen(cac_ma: list[str], tu_ngay: str, den_ngay: str,
            tai=_tai_that) -> tuple[dict[str, dict], list[str]]:
    """Nến (mở, thấp, cao) VNĐ của từng mã, MỖI MÃ MỘT LẦN. Trả (nến, mã không tải được)."""
    nen: dict[str, dict] = {}
    thieu: list[str] = []
    for ma in cac_ma:
        try:
            tt, df, he = tai(ma, tu_ngay, den_ngay)
        except Exception:
            thieu.append(ma)
            continue
        if tt != "OK" or df is None or len(df) == 0:
            thieu.append(ma)
            continue
        nen[ma] = skq.dung_nen(df["time"], df["open"], df["low"], df["high"], he)
    return nen, thieu


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
    print("\nCHỈ GẮN NHÃN. Lệnh có sự kiện quyền trong lúc giữ mang lãi/lỗ GIẢ; việc")
    print("loại chúng khỏi điều kiện dừng là một bước riêng, CHƯA áp dụng.")
    return 1 if dem[skq.SU_KIEN_TRONG_LUC_GIU] else 0


if __name__ == "__main__":
    raise SystemExit(main())
