"""ĐO 26 — hai ngưỡng của nhãn sự kiện quyền có gắn nhãn đúng trên sổ thật không
(BƯỚC 192, mốc D2). CHỈ ĐỌC.

    ./.venv/Scripts/python.exe tools/do26_nguong_su_kien_quyen.py [--json <tệp>]

Tiêu chí KÝ TRƯỚC ở `docs/TIEU-CHI-DOC-TRUOC.md`, mục `## ĐO 26` (commit f93394c,
trước khi file này tồn tại). File này chỉ THI HÀNH bản ký; chỗ nào bản ký chưa nói
thì ghi ở "CHỖ BẢN KÝ CHƯA NÓI" bên dưới, không tự chọn khác đi.

Ba nguồn, mỗi nguồn MỘT lượt kéo (giờ kéo và băm in ra = M0):
- sổ thật: `doc_so_that.keo_ve_so_tam` (DB tạm), mọi lệnh có ngày vào, trừ `HUY`;
- giá: `nen_su_kien_quyen.tai_nen` — đúng đường nhãn dùng trong `run_daily`;
- ĐÁP ÁN: lịch sự kiện VCI, `vnstock.explorer.vci.company.Company(mã)._fetch_events`
  (hàm NỘI BỘ của thư viện; hàm công khai `events()` chỉ trả 50 dòng mới nhất của
  mọi loại sự kiện), mã `DIV,ISS`, lật hết trang.

Nhãn lấy bằng `su_kien_quyen.soi_so` — đúng hàm của sản phẩm, hai ngưỡng GHIM.

CHỖ BẢN KÝ CHƯA NÓI (leader chọn khi viết dụng cụ, TRƯỚC khi chạy):
1. "Cỡ" của sự kiện trong lúc giữ = F − 1 với F của mô hình M_CKTM, tức CÙNG đơn
   vị với |f_vào − 1| mà nhãn so với `NGUONG_LECH`. Với một TM đơn lẻ F − 1 =
   v/(P − v), lớn hơn v/P một chút — nghiêng về phía báo âm tính giả NHIỀU hơn.
   So DẠNG NHÂN `F > 1 + NGUONG_LECH` (1,05 − 1 = 0,050000000000000044 > 0,05).
   Thiếu số (tỷ lệ CK, tiền TM) thì F = vô cực: tính là cỡ lớn, báo ra.
2. Nhóm biên rỗng (N = 0) thì biên CHƯA ĐO ĐƯỢC, tính như biên trượt (A′), không
   tính là qua.
3. Đối chứng (iii) trượt cũng là K0: tiêu đề mục đối chứng của bản ký nói "trượt
   thì KHÔNG kết luận" cho cả ba ô.
4. p95 lấy theo hạng gần nhất: phần tử thứ ⌈0,95·N⌉ của dãy tăng dần.

Mã thoát: 0 kết cục A/A′ · 1 kết cục B và/hoặc C · 2 không đọc được sổ · 3 K0.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import math
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Optional

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))
sys.path.insert(0, str(GOC))

for _luong in (sys.stdout, sys.stderr):
    try:
        _luong.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import nen_su_kien_quyen as nsk  # noqa: E402
import su_kien_quyen as skq  # noqa: E402

#: Đối chứng (ii): sai số cho phép giữa f_vào và hệ số lý thuyết F (bản ký).
SAI_SO_KHOP = 0.02
#: Đối chứng (ii): cỡ nhóm tối thiểu và tỷ lệ khớp tối thiểu (bản ký).
N_TOI_THIEU_DOI_CHUNG = 10
TY_LE_KHOP_TOI_THIEU = 0.80
#: Dưới mức này chỉ đếm, không suy tỷ lệ (bản ký, mục Thống kê chính).
N_SUY_TY_LE = 30
#: Ca dương đã biết (bản ký, đối chứng (i)).
CA_DUONG = {"id": 122, "ma": "HDB", "ngay": "2026-10-09", "ty_le": (0.05, 0.25)}
#: Cỡ trang và trần số trang khi lật lịch sự kiện.
CO_TRANG = 50
TRAN_TRANG = 40

CK, TM, QM = "CK", "TM", "QM"


# ───────────────────────── Lịch sự kiện: chuẩn hoá ─────────────────────────
def _nfc(s: Any) -> str:
    return unicodedata.normalize("NFC", str(s or "")).lower()


def phan_loai(ma_su_kien: Any, tieu_de: Any) -> Optional[str]:
    """CK · TM · QM, hoặc None với sự kiện không điều chỉnh giá (bản ký)."""
    ma = str(ma_su_kien or "").upper()
    td = _nfc(tieu_de)
    if ma == "DIV":
        return TM
    if ma != "ISS":
        return None
    if "cổ phiếu thưởng" in td or "trả cổ tức bằng cổ phiếu" in td:
        return CK
    if "quyền mua" in td:
        return QM
    return None


@dataclass(frozen=True)
class SuKien:
    ma: str
    loai: str
    ngay: str            # ngày GDKHQ 'YYYY-MM-DD'
    ty_le: Optional[float]
    tien: Optional[float]
    tieu_de: str


def _lay(dong: Mapping[str, Any], *khoa: str) -> Any:
    for k in khoa:
        if k in dong and dong[k] is not None:
            return dong[k]
    return None


def _so(x: Any) -> Optional[float]:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if v == v else None


def chuan_hoa(ma: str, dong_tho: Iterable[Mapping[str, Any]]) -> list[SuKien]:
    """Dòng thô của API → sự kiện ĐIỀU CHỈNH có ngày GDKHQ, đúng mã, sắp theo ngày."""
    ra = []
    for d in dong_tho:
        ticker = _lay(d, "ticker")
        if ticker is not None and str(ticker).upper() != ma.upper():
            continue
        loai = phan_loai(_lay(d, "eventCode", "event_code"),
                         _lay(d, "eventTitleVi", "event_title_vi"))
        ngay = str(_lay(d, "exrightDate", "exright_date") or "")[:10]
        if loai is None or len(ngay) != 10:
            continue
        ra.append(SuKien(ma, loai, ngay,
                         _so(_lay(d, "exerciseRatio", "exercise_ratio")),
                         _so(_lay(d, "valuePerShare", "value_per_share")),
                         str(_lay(d, "eventTitleVi", "event_title_vi") or "")))
    return sorted(ra, key=lambda s: (s.ngay, s.loai, s.tieu_de))


def trong_khoang(su_kien: Iterable[SuKien], tu: str, den: str) -> list[SuKien]:
    """Sự kiện có ngày GDKHQ ∈ (tu, den]: bán trước ngày GDKHQ thì không bị điều
    chỉnh; mua đúng ngày GDKHQ thì đã mua giá sau quyền."""
    return [s for s in su_kien if tu < s.ngay <= den]


def he_so(su_kien: Iterable[SuKien], gia_vao: float, mo_hinh: str) -> Optional[float]:
    """Hệ số lý thuyết F (bản ký): M_CK = Π(1+r); M_CKTM = Π(1+r) × Π 1/(1 − v/giá vào).

    None khi thiếu số (tỷ lệ CK hay tiền TM không đọc được) hoặc có QM.
    """
    f = 1.0
    for s in su_kien:
        if s.loai == QM:
            return None
        if s.loai == CK:
            if s.ty_le is None or s.ty_le < 0:
                return None
            f *= 1 + s.ty_le
        elif s.loai == TM and mo_hinh == "M_CKTM":
            if s.tien is None or s.tien <= 0 or s.tien >= gia_vao:
                return None
            f *= 1 / (1 - s.tien / gia_vao)
    return f


def lech_xuong(gia_ra: float, f_vao: float, thap: float) -> float:
    """e = (thấp − giá ra ÷ f_vào) ÷ thấp; 0 khi giá ra ÷ f_vào ≥ thấp (bản ký)."""
    quy_ve = gia_ra / f_vao
    return 0.0 if quy_ve >= thap else (thap - quy_ve) / thap


def p95(gia_tri: list[float]) -> Optional[float]:
    """Hạng gần nhất: phần tử thứ ⌈0,95·N⌉ của dãy tăng dần (CHỖ BẢN KÝ CHƯA NÓI 4)."""
    if not gia_tri:
        return None
    day = sorted(gia_tri)
    return day[math.ceil(0.95 * len(day)) - 1]


# ───────────────────────── Chấm từng lệnh ─────────────────────────
@dataclass
class Dong:
    id: Any
    ma: str
    ngay_vao: str
    ngay_ra: str
    da_dong: bool
    tien_ve_truoc: bool
    nhan: str
    f_vao: Optional[float]
    f_ra: Optional[float]
    gia_vao: Optional[float]
    co_lich: bool                      # mã có lịch sự kiện đọc được
    qua_cong: bool = False             # cổng `NGUONG_LECH` của nhãn (dạng nhân của nó)
    giu: list = field(default_factory=list)       # sự kiện ∈ (vào, ra]
    sau_vao: list = field(default_factory=list)   # sự kiện ∈ (vào, ngày kéo]
    F_giu: float = 1.0                 # hệ số M_CKTM của sự kiện CK/TM trong lúc giữ
    e: Optional[float] = None          # lệch xuống ở ngày ra (lệnh đóng, đủ nến)


def cham(trades: list, nen: Mapping[str, Mapping[str, Any]],
         lich: Mapping[str, list[SuKien]], ngay_keo: str) -> list[Dong]:
    """Gắn nhãn bằng `skq.soi_so` rồi ghép với lịch sự kiện."""
    from so_lenh_app import TRANG_THAI_DONG, TRANG_THAI_MO
    mo = [t for t in trades if t.status in TRANG_THAI_MO]
    dong = [t for t in trades if t.status in TRANG_THAI_DONG]
    tien = {t.id for t in nsk.lenh_dong_tien_ve_truoc(trades)}
    gia = {t.id: t for t in trades}
    ra = []
    for d in skq.soi_so(mo, dong, nen):
        if not d.ngay_vao:
            continue
        t = gia[d.id]
        sk = lich.get(d.ma)
        nen_vao = skq._lay_nen(nen.get(d.ma, {}), d.ngay_vao)
        r = Dong(d.id, d.ma, d.ngay_vao, d.ngay_ra, d.da_dong, d.id in tien,
                 d.ket_qua.trang_thai, d.ket_qua.he_so_vao, d.ket_qua.he_so_ra,
                 t.entry_price, sk is not None,
                 nen_vao is not None and skq._lech_qua_nguong(t.entry_price, nen_vao[0]))
        if sk is not None:
            r.sau_vao = trong_khoang(sk, d.ngay_vao, ngay_keo)
            if d.da_dong and d.ngay_ra:
                r.giu = trong_khoang(sk, d.ngay_vao, d.ngay_ra)
                ck_tm = [s for s in r.giu if s.loai in (CK, TM)]
                f = he_so(ck_tm, t.entry_price, "M_CKTM") if ck_tm else 1.0
                r.F_giu = f if f is not None else math.inf
        nen_ra = skq._lay_nen(nen.get(d.ma, {}), d.ngay_ra) if d.da_dong else None
        if nen_ra is not None and r.f_vao and skq._la_so(t.exit_price):
            r.e = lech_xuong(t.exit_price, r.f_vao, nen_ra[1])
        ra.append(r)
    return ra


# ───────────────────────── Tổng hợp theo bản ký ─────────────────────────
def tong_hop(dong: list[Dong], tap_loai_san_pham: Optional[set]) -> dict:
    """Mọi con số bản ký đòi, và kết cục. `tap_loai_san_pham` = `nsk.tap_loai(...).loai`
    của cùng lượt (None nếu nó lỗi)."""
    xet = [d for d in dong if d.co_lich]
    dong_kin = [d for d in xet if d.da_dong]

    duong_gia = [d for d in dong_kin
                 if d.nhan == skq.SU_KIEN_TRONG_LUC_GIU and not d.giu]
    am_gia = [d for d in dong_kin
              if d.nhan in (skq.SACH, skq.LECH_KHAC)
              and any(s.loai in (CK, TM) for s in d.giu)
              and d.F_giu > 1 + skq.NGUONG_LECH]   # dạng nhân: 1,05 − 1 > 0,05 trong float

    nhom_noi_bien = [d for d in dong_kin
                     if d.qua_cong
                     and not d.giu and d.e is not None]
    nhom_sach = [d for d in xet if d.f_vao is not None and not d.sau_vao]
    lech_sach = [abs(d.f_vao - 1) for d in nhom_sach]

    # Đối chứng (i)
    ca = [d for d in dong if d.id == CA_DUONG["id"] and d.ma == CA_DUONG["ma"]]
    ty_le_ca = sorted(round(s.ty_le, 4) for s in (ca[0].giu if ca else [])
                      if s.loai == CK and s.ngay == CA_DUONG["ngay"]
                      and s.ty_le is not None)
    dc1 = bool(ca) and ca[0].nhan == skq.SU_KIEN_TRONG_LUC_GIU and \
        tuple(ty_le_ca) == tuple(sorted(CA_DUONG["ty_le"]))

    # Đối chứng (ii)
    nhom2 = [d for d in xet if d.f_vao is not None and d.gia_vao
             and any(s.loai in (CK, TM) for s in d.sau_vao)
             and not any(s.loai == QM for s in d.sau_vao)]
    khop = {}
    truot = {}
    for mh in ("M_CK", "M_CKTM"):
        k, tr = 0, []
        for d in nhom2:
            f = he_so(d.sau_vao, d.gia_vao, mh)
            if f is not None and abs(d.f_vao / f - 1) <= SAI_SO_KHOP:
                k += 1
            else:
                tr.append((d.id, d.ma, d.f_vao, f))
        khop[mh] = k
        truot[mh] = tr
    n2 = len(nhom2)
    ty_le_khop = {mh: (khop[mh] / n2 if n2 else 0.0) for mh in khop}
    dc2 = n2 >= N_TOI_THIEU_DOI_CHUNG and \
        max(ty_le_khop.values()) >= TY_LE_KHOP_TOI_THIEU

    # Đối chứng (iii)
    tap_cu = {d.id for d in dong if d.da_dong and d.tien_ve_truoc
              and d.nhan == skq.SU_KIEN_TRONG_LUC_GIU}
    dc3 = tap_loai_san_pham is not None and tap_cu == set(tap_loai_san_pham)

    max_e = max((d.e for d in nhom_noi_bien), default=None)
    max_lech = max(lech_sach, default=None)
    bien_noi = max_e is not None and max_e <= skq.NOI_BIEN / 2
    bien_nguong = max_lech is not None and max_lech <= skq.NGUONG_LECH / 2

    if not (dc1 and dc2 and dc3):
        ket = "K0"
    elif duong_gia or am_gia:
        ket = "+".join(k for k, co in (("B", duong_gia), ("C", am_gia)) if co)
    elif bien_noi and bien_nguong:
        ket = "A"
    else:
        ket = "A′"

    return {
        "ket_cuc": ket,
        "duong_tinh_gia": duong_gia,
        "duong_tinh_gia_tien": [d for d in duong_gia if d.tien_ve_truoc],
        "am_tinh_gia_lon": am_gia,
        "nhom_noi_bien": nhom_noi_bien, "max_e": max_e, "bien_noi_qua": bien_noi,
        "nhom_sach": nhom_sach, "max_lech_sach": max_lech, "p95_lech_sach": p95(lech_sach),
        "bien_nguong_qua": bien_nguong,
        "dc1": dc1, "dc2": dc2, "dc3": dc3,
        "n2": n2, "khop": khop, "ty_le_khop": ty_le_khop, "truot": truot,
        "tap_cu": tap_cu, "tap_san_pham": tap_loai_san_pham,
        "khong_lich": sorted({d.ma for d in dong if not d.co_lich}),
    }


# ───────────────────────── Tải (mạng) ─────────────────────────
def tai_lich_that(ma: str, tu_ngay: str) -> list[dict]:
    """Mọi dòng `DIV,ISS` của VCI từ `tu_ngay`, lật hết trang. Lỗi thì NÉM."""
    from vnstock.explorer.vci.company import Company
    c = Company(ma)
    tu = tu_ngay.replace("-", "")
    dong: list[dict] = []
    for trang in range(TRAN_TRANG):
        lo = c._fetch_events(event_codes="DIV,ISS", from_date=tu,
                             page=trang, size=CO_TRANG)
        dong.extend(lo)
        if len(lo) < CO_TRANG:
            return dong
    raise RuntimeError(f"{ma}: quá {TRAN_TRANG} trang sự kiện — không tin là đã đủ")


def _bam(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True,
                                     default=str).encode("utf-8")).hexdigest()[:16]


def _f(x: Optional[float], n: int = 3) -> str:
    return "—" if x is None else f"{x:.{n}f}"


def _in_dong(d: Dong) -> str:
    sk = "; ".join(f"{s.loai} {s.ngay} r={_f(s.ty_le, 4)} v={_f(s.tien, 0)}"
                   for s in d.giu) or "—"
    return (f"#{d.id} {d.ma} {d.ngay_vao}→{d.ngay_ra or 'MỞ'} {d.nhan} "
            f"f_vào={_f(d.f_vao)} f_ra={_f(d.f_ra)} e={_f(d.e, 4)} "
            f"F_giữ={_f(d.F_giu, 4)} {'TIẾN' if d.tien_ve_truoc else 'MÔ PHỎNG'} "
            f"| giữ: {sk}")


def main(argv: Optional[list[str]] = None, keo: Optional[Callable] = None,
         tai: Callable = nsk.tai_that, tai_lich: Callable = tai_lich_that,
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
    trades = [t for t in so.all_trades() if t.status != "HUY" and t.entry_date]
    ngay_keo = hom_nay or datetime.date.today().isoformat()
    cac_ma, tu_ngay = skq.pham_vi_tai((), trades)
    nen, thieu_nen = nsk.tai_nen(cac_ma, tu_ngay, ngay_keo, tai) if tu_ngay else ({}, [])

    lich: dict[str, list[SuKien]] = {}
    lich_tho: dict[str, list] = {}
    thieu_lich: list[str] = []
    for ma in cac_ma:
        try:
            lich_tho[ma] = tai_lich(ma, tu_ngay)
        except Exception as e:
            thieu_lich.append(f"{ma} ({type(e).__name__}: {e})")
            continue
        lich[ma] = chuan_hoa(ma, lich_tho[ma])

    kq_loai = nsk.tap_loai(so.all_trades(), hom_nay=ngay_keo, tai=tai)
    tap_sp = None if kq_loai.loi else set(kq_loai.loai)

    dong = cham(trades, nen, lich, ngay_keo)
    th = tong_hop(dong, tap_sp)

    so_tho = [(t.id, t.symbol, t.status, t.entry_date, t.entry_price,
               t.exit_date, t.exit_price) for t in trades]
    print("=" * 72)
    print("ĐO 26 — nhãn sự kiện quyền đối chiếu lịch sự kiện VCI (BƯỚC 192)")
    print("=" * 72)
    print(f"M0  giờ kéo {gio_keo} · ngày kéo {ngay_keo} · nến từ {tu_ngay}")
    print(f"M0  băm sổ {_bam(so_tho)} · băm nến {_bam(nen)} · băm lịch {_bam(lich_tho)}")
    print(f"M0  {len(trades)} lệnh có ngày vào (trừ HUY) · nến {len(nen)}/{len(cac_ma)} mã"
          f" · lịch {len(lich)}/{len(cac_ma)} mã")
    if thieu_nen:
        print(f"    thiếu nến: {', '.join(thieu_nen)}")
    if thieu_lich:
        print(f"    thiếu lịch (lệnh của mã ấy KHÔNG vào phép đối chiếu): {'; '.join(thieu_lich)}")
    print(f"    hai ngưỡng GHIM: NGUONG_LECH={skq.NGUONG_LECH} · NOI_BIEN={skq.NOI_BIEN}")

    print("\nĐỐI CHỨNG CỦA MÁY ĐO")
    print(f"  (i)   HDB #122 dương đã biết: {'QUA' if th['dc1'] else 'TRƯỢT'}")
    print(f"  (ii)  giá ↔ lịch: N={th['n2']} · M_CK khớp {th['khop']['M_CK']}"
          f" ({th['ty_le_khop']['M_CK']:.1%}) · M_CKTM khớp {th['khop']['M_CKTM']}"
          f" ({th['ty_le_khop']['M_CKTM']:.1%}) → {'QUA' if th['dc2'] else 'TRƯỢT'}")
    for mh in ("M_CK", "M_CKTM"):
        for i, m, f, F in th["truot"][mh]:
            print(f"        trượt {mh}: #{i} {m} f_vào={_f(f)} F={_f(F)}")
    print(f"  (iii) cùng tập loại: dụng cụ {sorted(th['tap_cu'])} · tap_loai "
          f"{'LỖI ' + kq_loai.loi if th['tap_san_pham'] is None else sorted(th['tap_san_pham'])}"
          f" → {'QUA' if th['dc3'] else 'TRƯỢT'}")

    print("\nTHỐNG KÊ CHÍNH")
    print(f"  DƯƠNG TÍNH GIẢ: {len(th['duong_tinh_gia'])} "
          f"(trong đó tiến-về-trước, đang bị loại: {len(th['duong_tinh_gia_tien'])})")
    for d in th["duong_tinh_gia"]:
        print("    " + _in_dong(d))
    print(f"  ÂM TÍNH GIẢ LỚN: {len(th['am_tinh_gia_lon'])}")
    for d in th["am_tinh_gia_lon"]:
        print("    " + _in_dong(d))
    print(f"  Biên NOI_BIEN: N={len(th['nhom_noi_bien'])} · max e={_f(th['max_e'], 4)}"
          f" (cần ≤ {skq.NOI_BIEN / 2}) → {'qua' if th['bien_noi_qua'] else 'TRƯỢT/chưa đo được'}")
    for d in sorted(th["nhom_noi_bien"], key=lambda x: -(x.e or 0)):
        print("    " + _in_dong(d))
    print(f"  Biên NGUONG_LECH: N={len(th['nhom_sach'])} · max |f_vào−1|="
          f"{_f(th['max_lech_sach'], 4)} · p95={_f(th['p95_lech_sach'], 4)}"
          f" (cần max ≤ {skq.NGUONG_LECH / 2}) → "
          f"{'qua' if th['bien_nguong_qua'] else 'TRƯỢT/chưa đo được'}")
    if len(th["nhom_sach"]) < N_SUY_TY_LE:
        print(f"    nhóm < {N_SUY_TY_LE}: chỉ đếm, không suy tỷ lệ")

    print("\nBÁO KÈM")
    for nhom, ten in ((False, "MÔ PHỎNG"), (True, "TIẾN-VỀ-TRƯỚC")):
        bang: dict = {}
        for d in dong:
            if d.da_dong and d.co_lich and d.tien_ve_truoc == nhom:
                k = (d.nhan, "có sự kiện" if d.giu else "không")
                bang[k] = bang.get(k, 0) + 1
        print(f"  {ten} (lệnh đóng): " + (" · ".join(
            f"{a}/{b}={n}" for (a, b), n in sorted(bang.items())) or "—"))
    for d in dong:
        if d.nhan in (skq.LECH_KHAC, skq.KHONG_KIEM_DUOC) and d.giu:
            print("    " + _in_dong(d))
    print(f"  mã không có lịch: {', '.join(th['khong_lich']) or '—'}")

    print(f"\nKẾT CỤC (ký trước): {th['ket_cuc']}")
    if tep_json:
        Path(tep_json).write_text(json.dumps({
            "gio_keo": gio_keo, "ngay_keo": ngay_keo,
            "dong": [{**{k: v for k, v in d.__dict__.items() if k not in ("giu", "sau_vao")},
                      "giu": [s.__dict__ for s in d.giu],
                      "sau_vao": [s.__dict__ for s in d.sau_vao]} for d in dong],
            "ket_cuc": th["ket_cuc"]}, ensure_ascii=False, indent=1, default=str),
            encoding="utf-8")
        print(f"(dữ liệu thô: {tep_json})")
    if th["ket_cuc"] == "K0":
        return 3
    return 0 if th["ket_cuc"] in ("A", "A′") else 1


if __name__ == "__main__":
    raise SystemExit(main())
