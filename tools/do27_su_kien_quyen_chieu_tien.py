"""ĐO 27 — nhãn sự kiện quyền trên lệnh TIẾN-VỀ-TRƯỚC đóng SAU ngày ký, đo theo
chiều tiến (BƯỚC 194, mốc D2). CHỈ ĐỌC.

    ./.venv/Scripts/python.exe tools/do27_su_kien_quyen_chieu_tien.py [--json <tệp>]

Tiêu chí KÝ TRƯỚC ở `docs/TIEU-CHI-DOC-TRUOC.md`, mục `## ĐO 27` (commit 19a7950,
trước khi file này tồn tại). Thay ĐO 26 (kết cục K0, BƯỚC 193 — lỗi 178: lệnh mô
phỏng mang giá đã điều chỉnh tới NGÀY GHI SỔ).

Khác ĐO 26 đúng HAI chỗ, mọi định nghĩa khác dùng lại nguyên hàm của
`tools/do26_nguong_su_kien_quyen.py` (`cham`, `tong_hop`, lịch, M0):
1. Khoảng sự kiện bắt đầu ở max(ngày vào, ngày ghi sổ); ngày ghi sổ = `created_at`
   theo giờ VN. Lệnh ghi sau ngày ra thì khoảng giữ rỗng (hai giá cùng cơ sở).
2. Thống kê chính và hai biên tính trên QUẦN THỂ: lệnh tiến-về-trước
   (`nen_su_kien_quyen.lenh_dong_tien_ve_truoc`) có ngày ra SAU `NGAY_KY`. Ba đối
   chứng tính trên MỌI lệnh, như bản ký.

CHỖ BẢN KÝ CHƯA NÓI (chọn khi viết, TRƯỚC lượt đọc đầu):
- "Quần thể ≥ 30 lệnh" đếm lệnh của quần thể CÓ lịch sự kiện đọc được (lệnh không
  đối chiếu được thì không thể là bằng chứng cho A).

Mã thoát: 0 A/A′/CHƯA ĐỦ · 1 B và/hoặc C · 2 không đọc được sổ · 3 K0.
"""
from __future__ import annotations

import datetime
import json
import math
import sys
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))
sys.path.insert(0, str(GOC))

for _luong in (sys.stdout, sys.stderr):
    try:
        _luong.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import do26_nguong_su_kien_quyen as do26  # noqa: E402
import nen_su_kien_quyen as nsk  # noqa: E402
import su_kien_quyen as skq  # noqa: E402

#: Ngày của commit ký ĐO 27 (19a7950). Quần thể = lệnh đóng SAU ngày này.
NGAY_KY = "2026-10-15"
#: Kết cục A/A′ chỉ khi quần thể đủ lớn và có đủ ca dương thật (bản ký).
N_QUAN_THE_TOI_THIEU = 30
N_DUONG_THAT_TOI_THIEU = 3
GIO_VN = datetime.timezone(datetime.timedelta(hours=7))


def ngay_ghi(created_at: Any) -> Optional[str]:
    """`created_at` (giây Unix) → ngày theo giờ VN, hoặc None."""
    if not isinstance(created_at, (int, float)) or isinstance(created_at, bool):
        return None
    return datetime.datetime.fromtimestamp(created_at, GIO_VN).date().isoformat()


def cham(trades: list, nen: Mapping[str, Mapping[str, Any]],
         lich: Mapping[str, list], ngay_keo: str) -> list:
    """`do26.cham` rồi đặt lại khoảng sự kiện từ max(ngày vào, ngày ghi sổ)."""
    dong = do26.cham(trades, nen, lich, ngay_keo)
    t_theo_id = {t.id: t for t in trades}
    for d in dong:
        sk = lich.get(d.ma)
        if sk is None:
            continue
        t = t_theo_id[d.id]
        bat_dau = max(d.ngay_vao, ngay_ghi(t.created_at) or d.ngay_vao)
        d.sau_vao = do26.trong_khoang(sk, bat_dau, ngay_keo)
        d.giu = []
        d.F_giu = 1.0
        if d.da_dong and d.ngay_ra:
            d.giu = do26.trong_khoang(sk, bat_dau, d.ngay_ra)
            ck_tm = [s for s in d.giu if s.loai in (do26.CK, do26.TM)]
            f = do26.he_so(ck_tm, t.entry_price, "M_CKTM") if ck_tm else 1.0
            d.F_giu = f if f is not None else math.inf
    return dong


def quan_the(trades: list) -> set:
    """id lệnh tiến-về-trước đã đóng có ngày ra SAU `NGAY_KY`."""
    return {t.id for t in nsk.lenh_dong_tien_ve_truoc(trades)
            if str(t.exit_date or "")[:10] > NGAY_KY}


def tong_hop(dong: list, tap_loai_san_pham: Optional[set], qt: set) -> dict:
    """Đối chứng trên MỌI lệnh; thống kê chính + biên trên quần thể; kết cục ĐO 27."""
    th_moi = do26.tong_hop(dong, tap_loai_san_pham)
    pop = [d for d in dong if d.id in qt and d.co_lich]
    th_qt = do26.tong_hop(pop, tap_loai_san_pham)
    duong_that = [d for d in pop
                  if d.nhan == skq.SU_KIEN_TRONG_LUC_GIU and d.giu]
    if not (th_moi["dc1"] and th_moi["dc2"] and th_moi["dc3"]):
        ket = "K0"
    elif th_qt["duong_tinh_gia"] or th_qt["am_tinh_gia_lon"]:
        ket = "+".join(k for k, co in (("B", th_qt["duong_tinh_gia"]),
                                       ("C", th_qt["am_tinh_gia_lon"])) if co)
    elif len(pop) < N_QUAN_THE_TOI_THIEU or len(duong_that) < N_DUONG_THAT_TOI_THIEU:
        ket = "CHƯA ĐỦ"
    elif th_qt["bien_noi_qua"] and th_qt["bien_nguong_qua"]:
        ket = "A"
    else:
        ket = "A′"
    return {"ket_cuc": ket, "doi_chung": th_moi, "quan_the": th_qt,
            "n_quan_the": len(pop), "duong_that": duong_that,
            "qt_khong_lich": sorted(d.id for d in dong if d.id in qt and not d.co_lich)}


def main(argv: Optional[list[str]] = None, keo: Optional[Callable] = None,
         tai: Callable = nsk.tai_that, tai_lich: Callable = do26.tai_lich_that,
         hom_nay: Optional[str] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    tep_json = argv[argv.index("--json") + 1] if "--json" in argv else None
    import doc_so_that
    gio_keo = datetime.datetime.now().isoformat(timespec="seconds")
    ra = (keo or doc_so_that.keo_ve_so_tam)()
    if ra is None:
        print("CHUA DOC DUOC SO — khong doan gi ca.", file=sys.stderr)
        return 2
    so, _bc = ra
    tat_ca = so.all_trades()
    trades = [t for t in tat_ca if t.status != "HUY" and t.entry_date]
    ngay_keo = hom_nay or datetime.date.today().isoformat()
    cac_ma, tu_ngay = skq.pham_vi_tai((), trades)
    nen, thieu_nen = nsk.tai_nen(cac_ma, tu_ngay, ngay_keo, tai) if tu_ngay else ({}, [])
    lich, lich_tho, thieu_lich = {}, {}, []
    for ma in cac_ma:
        try:
            lich_tho[ma] = tai_lich(ma, tu_ngay)
        except Exception as e:
            thieu_lich.append(f"{ma} ({type(e).__name__}: {e})")
            continue
        lich[ma] = do26.chuan_hoa(ma, lich_tho[ma])
    kq_loai = nsk.tap_loai(tat_ca, hom_nay=ngay_keo, tai=tai)
    tap_sp = None if kq_loai.loi else set(kq_loai.loai)

    dong = cham(trades, nen, lich, ngay_keo)
    qt = quan_the(trades)
    th = tong_hop(dong, tap_sp, qt)
    dc, q = th["doi_chung"], th["quan_the"]

    so_tho = [(t.id, t.symbol, t.status, t.entry_date, t.entry_price,
               t.exit_date, t.exit_price, t.created_at) for t in trades]
    print("=" * 72)
    print(f"ĐO 27 — chiều tiến, quần thể: tiến-về-trước đóng sau {NGAY_KY} (BƯỚC 194)")
    print("=" * 72)
    print(f"M0  giờ kéo {gio_keo} · ngày kéo {ngay_keo} · nến từ {tu_ngay}")
    print(f"M0  băm sổ {do26._bam(so_tho)} · băm nến {do26._bam(nen)} · "
          f"băm lịch {do26._bam(lich_tho)}")
    print(f"M0  nến {len(nen)}/{len(cac_ma)} mã · lịch {len(lich)}/{len(cac_ma)} mã")
    if thieu_nen:
        print(f"    thiếu nến: {', '.join(thieu_nen)}")
    if thieu_lich:
        print(f"    thiếu lịch: {'; '.join(thieu_lich)}")
    print(f"    hai ngưỡng GHIM: NGUONG_LECH={skq.NGUONG_LECH} · NOI_BIEN={skq.NOI_BIEN}")
    print("\nĐỐI CHỨNG (mọi lệnh, khoảng từ ngày ghi sổ)")
    print(f"  (i)   HDB #122: {'QUA' if dc['dc1'] else 'TRƯỢT'}")
    print(f"  (ii)  giá ↔ lịch: N={dc['n2']} · M_CK {dc['khop']['M_CK']} "
          f"({dc['ty_le_khop']['M_CK']:.1%}) · M_CKTM {dc['khop']['M_CKTM']} "
          f"({dc['ty_le_khop']['M_CKTM']:.1%}) → {'QUA' if dc['dc2'] else 'TRƯỢT'}")
    for mh in ("M_CK", "M_CKTM"):
        for i, m, f, F in dc["truot"][mh]:
            print(f"        trượt {mh}: #{i} {m} f_vào={do26._f(f)} F={do26._f(F)}")
    print(f"  (iii) cùng tập loại: dụng cụ {sorted(dc['tap_cu'])} · tap_loai "
          f"{'LỖI ' + kq_loai.loi if dc['tap_san_pham'] is None else sorted(dc['tap_san_pham'])}"
          f" → {'QUA' if dc['dc3'] else 'TRƯỢT'}")
    print(f"\nQUẦN THỂ: {th['n_quan_the']} lệnh có lịch"
          + (f" · không có lịch: {th['qt_khong_lich']}" if th["qt_khong_lich"] else ""))
    print(f"  DƯƠNG THẬT: {len(th['duong_that'])}")
    for d in th["duong_that"]:
        print("    " + do26._in_dong(d))
    print(f"  DƯƠNG TÍNH GIẢ: {len(q['duong_tinh_gia'])}")
    for d in q["duong_tinh_gia"]:
        print("    " + do26._in_dong(d))
    print(f"  ÂM TÍNH GIẢ LỚN: {len(q['am_tinh_gia_lon'])}")
    for d in q["am_tinh_gia_lon"]:
        print("    " + do26._in_dong(d))
    print(f"  Biên NOI_BIEN: N={len(q['nhom_noi_bien'])} · max e={do26._f(q['max_e'], 4)}")
    print(f"  Biên NGUONG_LECH: N={len(q['nhom_sach'])} · max |f_vào−1|="
          f"{do26._f(q['max_lech_sach'], 4)} · p95={do26._f(q['p95_lech_sach'], 4)}")
    print(f"\nKẾT CỤC LƯỢT ĐỌC (ký trước): {th['ket_cuc']}")
    if tep_json:
        Path(tep_json).write_text(json.dumps({
            "gio_keo": gio_keo, "ngay_keo": ngay_keo, "ket_cuc": th["ket_cuc"],
            "quan_the": sorted(qt)}, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"(dữ liệu thô: {tep_json})")
    if th["ket_cuc"] == "K0":
        return 3
    return 1 if th["ket_cuc"] in ("B", "C", "B+C") else 0


if __name__ == "__main__":
    raise SystemExit(main())
