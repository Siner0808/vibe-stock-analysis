"""Ghép các lần đảo chiều (lật) của HAI chuỗi chỉ số thành đoạn, và đọc trạng thái cặp tại một hàng (BƯỚC 308,
Dow phần 2, Lát 2; đặc tả `DAC-TA-DOW2.md` mục 3; ĐO 39 *Luật trạng thái ghim*).

Mô-đun MÔ TẢ, hàm THUẦN, không dữ liệu thật, không mạng, không đồng hồ. Nó không là tín hiệu, bộ lọc, vùng kế hoạch,
thành phần điểm hay phép đo lợi nhuận; chỉ `app.py` và `tools/mo_ta_dow_hai_chi_so.py` được nhập nó (gác AST ở
`tests/test_dow_hai_chi_so_buc_tuong.py`). Chữ "xác nhận" ở đây chỉ nghĩa là hai chuỗi CÙNG đảo chiều cấp swing
(xấp xỉ), không phải xu hướng chính của Dow.

Một LẬT (`Lat`) là một `SuKienPha` cấp swing loại CHOCH của phần 1 (`cau_truc_gia`), mang `k` = `chi_so_biet` = chỉ số
HÀNG của bảng đã căn mà `chuoi_chi_so.can_theo_giao` dựng (một bảng căn, không viết bảng căn thứ hai). KHOI_DAU, BOS và
cấp nội bộ KHÔNG là lật.

`ghep_cap(lat_a, lat_b, w, *, ngay)`: quét từng hàng `k` của bảng; ở mỗi hàng, ĐÚNG thứ tự:
  1. đoạn đang mở có `k - k_mo > w` -> khong_xac_nhan, `het_han` (hàng hết hạn là `k_mo + w + 1`);
  2. chuỗi `lead` lật lại -> đoạn đóng khong_xac_nhan, `lead_dao_chieu`;
  3. chuỗi kia lật NGƯỢC chiều đoạn -> đóng khong_xac_nhan, `ben_kia_nguoc`;
  4. chuỗi kia lật CÙNG chiều đoạn (và `k - k_mo <= w`) -> xac_nhan, `ngay_ket` = ngày MUỘN hơn trong hai ngày phá;
  5. mỗi lật chưa đặt: không có đoạn mở và có lật RẢNH gần nhất của chuỗi kia cùng chiều trong `w` hàng -> xac_nhan
     ngay (lead = chuỗi kia); không thì mở đoạn dang_cho.
Lật đóng đoạn ở bước 2 hay 3 KHÔNG bị tính là đã dùng: nó đi tiếp sang bước 5 (bảng 3.5, hàng p14).

Ba điều đặc tả chưa nói, NGƯỜI DÙNG ĐÃ DUYỆT 28/11/2026 (*"duyệt"*), ghi ở `docs/STATE.md` BƯỚC 308; chữ khai ở
`docs/TIEU-CHI-DOC-TRUOC.md` do BƯỚC 309 thêm, ở commit riêng, TRƯỚC lượt chạy:
  * (Q1) *"Chọn U2"*: một lật chỉ "đã dùng" khi nó thuộc một đoạn đang mở hay xac_nhan; đoạn đóng khong_xac_nhan (mọi
    lý do) trả lật về trạng thái RẢNH, và bước 5 dùng được nó.
  * (Q2) *"Ghi một đoạn 'không xác nhận — trái chiều', trễ 0, đóng ngay, không mở đoạn chờ"*: sau bước 1–4 không còn
    đoạn mở mà cả hai chuỗi lật cùng hàng và NGƯỢC chiều nhau -> MỘT đoạn khong_xac_nhan, `ben_kia_nguoc`, `tre` 0,
    `lead` dong_thoi, `chieu` None. Theo Q1 = U2 cả hai lật rảnh sau đó (quyết định của leader). Cùng hàng, CÙNG chiều
    -> một đoạn xac_nhan, `tre` 0, `lead` dong_thoi (A mở, B xác nhận ở bước 4 cùng hàng, như đặc tả).
  * (Q3 của đặc tả) `ngay` là tham số BẮT BUỘC (ngày của MỌI hàng bảng đã căn; `len(ngay)` = số hàng). Đoạn còn mở sau
    hàng cuối giữ dang_cho với `k_ket` và `ngay_ket` là None; `het_han` chỉ ghi khi hàng `k_mo + w + 1` CÓ trong bảng.

"Đoạn mới nhất" của `trang_thai_cap_tai` là đoạn được TẠO sau cùng (`k_tao`), không phải đoạn có `k_mo` lớn nhất: một
đoạn xac_nhan tạo ngay ở bước 5 mang `k_mo` của lật cũ nên có thể nhỏ hơn `k_mo` của đoạn vừa đóng cùng hàng.
Một đoạn mà `k_ket > t` (hay `k_ket` là None) đọc như dang_cho. Hết hạn là hàm của số hàng, không của đồng hồ; bất biến
khi cắt (đặc tả 3.4) được canh ở `tests/test_dow_hai_chi_so.py`.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

import cau_truc_gia as C

LEAD_A, LEAD_B, DONG_THOI = "a", "b", "dong_thoi"
XAC_NHAN, KHONG_XAC_NHAN, DANG_CHO, CHUA_DU = "xac_nhan", "khong_xac_nhan", "dang_cho", "chua_du"
HET_HAN, LEAD_DAO_CHIEU, BEN_KIA_NGUOC = "het_han", "lead_dao_chieu", "ben_kia_nguoc"

_TEN_CHIEU = {C.TANG: "tăng", C.GIAM: "giảm"}
_HUONG = {C.TANG: "lên", C.GIAM: "xuống"}


@dataclass(frozen=True)
class Lat:
    """Một lần đảo chiều swing của MỘT chuỗi: hàng biết (`chi_so_biet`), ngày biết, chiều mới."""
    k: int
    ngay: str
    chieu: str


@dataclass(frozen=True)
class Doan:
    """Một đoạn ghép. `lead` là chuỗi lật TRƯỚC ('a' · 'b' · 'dong_thoi'); `k_mo` là hàng lật của lead (đầu đoạn);
    `k_tao` là hàng đoạn được tạo (khác `k_mo` khi bước 5 xác nhận ngay với lật cũ). `chieu` None = trái chiều.
    `lat_mo` là lật của lead; `lat_kia` là lật của chuỗi kia nếu đoạn đã có (xac_nhan, hoặc cặp trái chiều)."""
    lead: str
    chieu: str | None
    k_mo: int
    ngay_mo: str
    k_tao: int
    ket_qua: str
    k_ket: int | None
    ngay_ket: str | None
    tre: int | None
    ly_do: str | None
    w: int | None
    lat_mo: Lat
    lat_kia: Lat | None


@dataclass(frozen=True)
class TrangThaiCap:
    """Trạng thái cặp tại một hàng. `k_biet`/`ngay_biet` = đầu đoạn không đổi: xac_nhan -> ngày xác nhận;
    khong_xac_nhan -> ngày kết; dang_cho -> ngày mở. `con_lai` = số hàng còn xác nhận được (None khi w là None)."""
    gia_tri: str
    chieu: str | None
    k_biet: int | None
    ngay_biet: str | None
    lead: str | None
    tre: int | None
    ly_do: str | None
    w: int | None
    con_lai: int | None
    k_mo: int | None
    ngay_mo: str | None


@dataclass(frozen=True)
class HienThi:
    tieu_de: str
    mo_ta: str


def lat_tu_cau_truc(cau_truc) -> tuple[Lat, ...]:
    """Các lật của MỘT chuỗi từ kết quả `cau_truc_gia.doc_cau_truc(..., la_chi_so=True)`: chỉ CHOCH ở cấp swing."""
    return tuple(Lat(k=e.chi_so_biet, ngay=e.ngay_biet, chieu=e.chieu)
                 for e in cau_truc.su_kien if e.cap == C.CAP_SWING and e.loai == C.CHOCH)


def _kia(chuoi: str) -> str:
    return LEAD_B if chuoi == LEAD_A else LEAD_A


def _kiem_w(w) -> None:
    if w is not None and (isinstance(w, bool) or not isinstance(w, int) or w < 0):
        raise ValueError(f"w phải là None hoặc số nguyên không âm, nhận {w!r}")


def _kiem_chuoi(ten: str, lat, ngay: tuple) -> tuple[Lat, ...]:
    lat = tuple(lat)
    truoc = None
    for x in lat:
        if isinstance(x.k, bool) or not isinstance(x.k, int) or not 0 <= x.k < len(ngay):
            raise ValueError(f"lật của chuỗi {ten} ở hàng {x.k!r} nằm ngoài bảng {len(ngay)} hàng")
        if x.ngay != ngay[x.k]:
            raise ValueError(f"lật của chuỗi {ten} ở hàng {x.k} mang ngày {x.ngay!r}, bảng ghi {ngay[x.k]!r}")
        if x.chieu not in (C.TANG, C.GIAM):
            raise ValueError(f"lật của chuỗi {ten} ở hàng {x.k} có chiều lạ {x.chieu!r}")
        if truoc is not None:
            if x.k <= truoc.k:
                raise ValueError(f"chuỗi {ten}: hai lật cùng hàng hay không tăng ({truoc.k} rồi {x.k})")
            if x.chieu == truoc.chieu:
                raise ValueError(f"chuỗi {ten}: hai lật liền nhau cùng chiều ở hàng {truoc.k} và {x.k}")
        truoc = x
    return lat


def _lat_ranh_gan_nhat(lat_kia: tuple, chieu: str, k: int, w, dung: set, ten_kia: str):
    """Lật RẢNH gần nhất của chuỗi kia, cùng `chieu`, nằm trong `w` hàng (`k - k_lat <= w`) và trước hàng `k`."""
    for x in reversed(lat_kia):
        if x.k >= k:
            continue
        if w is not None and k - x.k > w:
            break
        if x.chieu == chieu and (ten_kia, x.k) not in dung:
            return x
    return None


def ghep_cap(lat_a, lat_b, w, *, ngay) -> tuple[Doan, ...]:
    """Ghép hai chuỗi lật thành đoạn, theo đúng thứ tự năm bước ở đầu file. `ngay` = ngày của MỌI hàng bảng đã căn.
    Trả các đoạn theo thứ tự TẠO. Lật nằm ngoài bảng, ngày lệch, hai lật cùng hàng/cùng chiều liền nhau -> ValueError."""
    ngay = tuple(ngay)
    _kiem_w(w)
    lat = {LEAD_A: _kiem_chuoi("a", lat_a, ngay), LEAD_B: _kiem_chuoi("b", lat_b, ngay)}
    theo_hang = {ten: {x.k: x for x in cs} for ten, cs in lat.items()}
    dung: set = set()          # (chuỗi, hàng) của các lật đang nằm trong đoạn MỞ hoặc xac_nhan (Q1 = U2)
    ra: list[Doan] = []
    mo: Doan | None = None
    for k in range(len(ngay)):
        hom_nay = {ten: theo_hang[ten][k] if k in theo_hang[ten] else None for ten in (LEAD_A, LEAD_B)}
        con = [ten for ten in (LEAD_A, LEAD_B) if hom_nay[ten] is not None]      # lật hôm nay CHƯA đặt vào đâu
        if mo is not None and w is not None and k - mo.k_mo > w:                 # bước 1
            ra.append(_dong(mo, KHONG_XAC_NHAN, k, ngay, HET_HAN))       # lật của đoạn hết hạn xa hơn `w` mọi lật sau:
            mo = None                                                    # không cần trả rảnh (đột biến L1 là tương đương)
        if mo is not None:
            lead, kia = mo.lead, _kia(mo.lead)
            if hom_nay[lead] is not None and hom_nay[lead].chieu != mo.chieu:    # bước 2
                ra.append(_dong(mo, KHONG_XAC_NHAN, k, ngay, LEAD_DAO_CHIEU))
                dung.discard((lead, mo.lat_mo.k))
                mo = None
            elif hom_nay[kia] is not None:
                f = hom_nay[kia]
                if f.chieu != mo.chieu:                                          # bước 3
                    ra.append(_dong(mo, KHONG_XAC_NHAN, k, ngay, BEN_KIA_NGUOC))
                    dung.discard((lead, mo.lat_mo.k))
                    mo = None
                elif w is None or k - mo.k_mo <= w:                              # bước 4
                    ra.append(_dong(mo, XAC_NHAN, k, ngay, None, lat_kia=f))
                    dung.add((kia, k))
                    con.remove(kia)
                    mo = None
        if mo is None and con:                                                   # bước 5
            if len(con) == 2:
                fa, fb = hom_nay[LEAD_A], hom_nay[LEAD_B]
                if fa.chieu == fb.chieu:
                    ra.append(_doan_cung_hang(fa.chieu, k, ngay, w, fa, fb, XAC_NHAN, None))
                    dung |= {(LEAD_A, k), (LEAD_B, k)}
                else:
                    ra.append(_doan_cung_hang(None, k, ngay, w, fa, fb, KHONG_XAC_NHAN, BEN_KIA_NGUOC))
            else:
                ten = con[0]
                f = hom_nay[ten]
                cu = _lat_ranh_gan_nhat(lat[_kia(ten)], f.chieu, k, w, dung, _kia(ten))
                if cu is not None:
                    ra.append(Doan(lead=_kia(ten), chieu=f.chieu, k_mo=cu.k, ngay_mo=cu.ngay, k_tao=k,
                                   ket_qua=XAC_NHAN, k_ket=k, ngay_ket=ngay[k], tre=k - cu.k, ly_do=None, w=w,
                                   lat_mo=cu, lat_kia=f))
                    dung |= {(_kia(ten), cu.k), (ten, k)}
                else:
                    mo = Doan(lead=ten, chieu=f.chieu, k_mo=k, ngay_mo=f.ngay, k_tao=k, ket_qua=DANG_CHO,
                              k_ket=None, ngay_ket=None, tre=None, ly_do=None, w=w, lat_mo=f, lat_kia=None)
                    dung.add((ten, k))
    if mo is not None:
        ra.append(mo)
    return tuple(ra)


def _dong(mo: Doan, ket_qua: str, k: int, ngay: tuple, ly_do, lat_kia: Lat | None = None) -> Doan:
    return replace(mo, ket_qua=ket_qua, k_ket=k, ngay_ket=ngay[k], tre=k - mo.k_mo, ly_do=ly_do, lat_kia=lat_kia)


def _doan_cung_hang(chieu, k: int, ngay: tuple, w, fa: Lat, fb: Lat, ket_qua: str, ly_do) -> Doan:
    return Doan(lead=DONG_THOI, chieu=chieu, k_mo=k, ngay_mo=ngay[k], k_tao=k, ket_qua=ket_qua, k_ket=k,
                ngay_ket=ngay[k], tre=0, ly_do=ly_do, w=w, lat_mo=fa, lat_kia=fb)


def trang_thai_cap_tai(doan, t: int) -> TrangThaiCap:
    """Trạng thái cặp tại hàng `t`: đoạn được TẠO sau cùng trong số đoạn có `k_tao <= t`. Đoạn có `k_ket` là None hay
    `k_ket > t` đọc như dang_cho. `chua_du` khi chưa có đoạn nào."""
    moi = None
    for d in doan:
        if d.k_tao <= t:
            moi = d
    if moi is None:
        return TrangThaiCap(CHUA_DU, None, None, None, None, None, None, None, None, None, None)
    if moi.k_ket is None or moi.k_ket > t:
        con_lai = None if moi.w is None else moi.w - (t - moi.k_mo)
        return TrangThaiCap(DANG_CHO, moi.chieu, moi.k_mo, moi.ngay_mo, moi.lead, None, None, moi.w, con_lai,
                            moi.k_mo, moi.ngay_mo)
    return TrangThaiCap(moi.ket_qua, moi.chieu, moi.k_ket, moi.ngay_ket, moi.lead,
                        moi.tre if moi.ket_qua == XAC_NHAN else None, moi.ly_do, moi.w, None, moi.k_mo, moi.ngay_mo)


# ── hiển thị (lời MÔ TẢ, không dự đoán; gác lời ở tests/test_dow_hai_chi_so_buc_tuong.py) ──────────────
def _ngay_vn(ngay: str) -> str:
    nam, thang, ngay_thang = ngay[:10].split("-")
    return f"{ngay_thang}/{thang}/{nam}"


def hien_thi(tt: TrangThaiCap, ten_a: str, ten_b: str) -> HienThi:
    """Tiêu đề và một dòng mô tả cho bốn trạng thái. Chân khối (con số của ĐO 39) do ô trên app thêm, không ở đây."""
    ten = {LEAD_A: ten_a, LEAD_B: ten_b}
    if tt.gia_tri == CHUA_DU:
        return HienThi("Chưa đủ bằng chứng", "chưa có đảo chiều swing nào ở cả hai chuỗi")
    if tt.gia_tri == XAC_NHAN:
        tieu_de = f"Đã xác nhận · {_TEN_CHIEU[tt.chieu]}"
        if tt.lead == DONG_THOI or tt.tre == 0:
            return HienThi(tieu_de, f"cả hai chuỗi cùng đảo chiều swing {_HUONG[tt.chieu]} trong cùng một phiên; "
                                    f"xác nhận {_ngay_vn(tt.ngay_biet)}")
        return HienThi(tieu_de, f"cả hai chuỗi cùng đảo chiều swing {_HUONG[tt.chieu]}; xác nhận "
                                f"{_ngay_vn(tt.ngay_biet)}; {ten[_kia(tt.lead)]} theo sau {ten[tt.lead]} {tt.tre} phiên")
    if tt.gia_tri == DANG_CHO:
        sau = "không giới hạn số phiên" if tt.con_lai is None else f"còn {tt.con_lai} phiên"
        return HienThi(f"Đang chờ · {_TEN_CHIEU[tt.chieu]}",
                       f"{ten[tt.lead]} đảo chiều swing {_HUONG[tt.chieu]} từ {_ngay_vn(tt.ngay_mo)}, "
                       f"chờ {ten[_kia(tt.lead)]} ({sau})")
    if tt.gia_tri == KHONG_XAC_NHAN and tt.chieu is None and tt.ly_do == BEN_KIA_NGUOC:
        return HienThi("Không xác nhận · trái chiều",
                       f"hai chuỗi đảo chiều swing ngược nhau trong cùng ngày {_ngay_vn(tt.ngay_biet)}")
    if tt.gia_tri == KHONG_XAC_NHAN and tt.chieu is not None and tt.ly_do == HET_HAN:
        return HienThi(f"Không xác nhận · {_TEN_CHIEU[tt.chieu]}",
                       f"{ten[tt.lead]} đảo chiều swing {_HUONG[tt.chieu]} từ {_ngay_vn(tt.ngay_mo)}; "
                       f"{ten[_kia(tt.lead)]} không theo trong {tt.w} phiên")
    raise ValueError(f"trạng thái không đọc được thành lời: {tt.gia_tri!r} · {tt.ly_do!r} · chiều {tt.chieu!r}")
