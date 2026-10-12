"""Phát hiện SỰ KIỆN QUYỀN rơi trong lúc giữ lệnh ảo — CHỈ ĐỌC, CHỈ GẮN NHÃN (BƯỚC 176).

VÌ SAO CÓ FILE NÀY
──────────────────
Sổ lệnh lưu giá CHƯA điều chỉnh lúc khớp. Nguồn giá (`VNStockCollectorAgent`)
điều chỉnh LÙI cả lịch sử sau một sự kiện quyền (chia cổ phiếu, thưởng cổ phiếu…).
Tới ngày giao dịch không hưởng quyền, giá thị trường rơi cơ học; giá sổ ở cơ sở
CŨ nên chạm cắt lỗ, và lệnh đóng với một khoản lỗ GIẢ. Ca đã thấy (do leader đo
10/10/2026, dữ liệu thật): lệnh HDB #122 vào 28/09 giá 27.950, đóng 09/10
`STOP_LOSS` −23,18%, trong khi nguồn hôm nay cho giá mở ngày 28/09 chỉ ≈ 21.460.

Module này đo HỆ SỐ f = giá vào sổ ÷ giá mở của nguồn CÙNG NGÀY, rồi hỏi: giá ra
của sổ có còn nằm trong biên giá của nguồn ở ngày ra, sau khi quy về cơ sở của
nguồn bằng f_vào? Có thì hai đầu cùng một cơ sở giá (sự kiện, nếu có, xảy ra SAU
khi lệnh đóng): SẠCH. Không thì cơ sở giá đổi GIỮA lúc vào và ra.

HÀM THUẦN. Không mạng, không đồng hồ, không đĩa, không ghi sổ. Không nằm trên
đường đo: `run_daily` · `paper_trading` · `paper_metrics` · `master_agent` ·
`backtest/` KHÔNG được nhập nó (gác AST ở `tests/test_su_kien_quyen.py`). Việc
LOẠI các lệnh này khỏi điều kiện dừng là ĐỔI LUẬT ĐO — một bước riêng có hỏi
NotebookLM, KHÔNG làm ở đây (`docs/QUYET-DINH-CHO.md` Q14).

GIỚI HẠN (đọc trước khi tin nhãn)
─────────────────────────────────
· f chỉ thấy sự kiện làm GIẢM giá. Cổ tức tiền mặt nhỏ (< `NGUONG_LECH`) không
  làm f nhích khỏi 1 quá ngưỡng nên KHÔNG thấy.
· `SACH` nghĩa là "không thấy dấu hiệu", không phải "đã chứng minh sạch".
· Lệnh có |f_vào − 1| ≤ `NGUONG_LECH` là `SACH` ngay, kể cả khi giá ra của sổ
  lệch biên ngày ra vì một lý do khác (gap ghi ở giá SL): không soi tới đó.
· Nhãn dựa vào giá của NGUỒN HÔM NAY; nguồn đổi cơ sở lần nữa thì nhãn đổi.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional

#: Bốn trạng thái. Chuỗi, để sổ/bảng in thẳng không cần dịch.
SACH = "SACH"
SU_KIEN_TRONG_LUC_GIU = "SU_KIEN_TRONG_LUC_GIU"
LECH_KHAC = "LECH_KHAC"
KHONG_KIEM_DUOC = "KHONG_KIEM_DUOC"

#: ĐỀ XUẤT, CHƯA ĐO. Giá sổ lệch giá nguồn quá 5% cùng ngày thì coi là khác cơ sở
#: giá. Vì sao 5%: trượt giá mô phỏng của sổ (`truot_gia`: bước giá + tác động
#: thị trường ở vốn 1 tỷ) nhỏ hơn nhiều so với 5%, nên lệch lớn hơn mức ấy không
#: thể là trượt giá; còn sự kiện quyền thấy ở HDB lệch ≈ 30%. Chưa đo phân bố f
#: trên toàn sổ để chọn ngưỡng tối ưu — đổi thì sửa ở đây và test đi cùng.
NGUONG_LECH = 0.05

#: ĐỀ XUẤT, CHƯA ĐO. Nới biên [thấp, cao] của nến ngày ra thêm 2% mỗi phía trước
#: khi kết luận giá ra "nằm ngoài biên": làm tròn bước giá và chênh lệch nguồn giữa
#: hai lần kéo không được tính thành sự kiện.
NOI_BIEN = 0.02

#: Nến của một ngày: (mở, thấp, cao), VNĐ.
Nen = tuple[float, float, float]


@dataclass(frozen=True)
class KetQua:
    """Nhãn của MỘT lệnh. `he_so_*` là None khi không tính được/không áp dụng."""
    trang_thai: str
    he_so_vao: Optional[float]
    he_so_ra: Optional[float]
    ly_do: str


def _la_so(x: Any) -> bool:
    return (isinstance(x, (int, float)) and not isinstance(x, bool)
            and x == x and x > 0)


def _ngay(gia_tri: Any) -> str:
    return str(gia_tri or "")[:10]


def _lay_nen(nen: Mapping[str, Nen], ngay: str) -> Optional[Nen]:
    """Nến hợp lệ (mở, thấp, cao đều là số dương) của ngày, hoặc None."""
    n = nen.get(ngay)
    if n is None or len(n) != 3 or not all(_la_so(v) for v in n):
        return None
    return n


def _lech_qua_nguong(gia: float, mo: float) -> bool:
    """|gia/mo − 1| > NGUONG_LECH, viết dạng nhân để biên đúng 5% không trôi
    theo sai số dấu phẩy động (|1050/1000 − 1| = 0,05000000000000004)."""
    return abs(gia - mo) > NGUONG_LECH * mo


def kiem_lenh(lenh: Mapping[str, Any], nen: Mapping[str, Nen],
              da_dong: bool) -> KetQua:
    """Gắn nhãn một lệnh. Đọc `entry_date` · `entry_price` · `exit_date` ·
    `exit_price` của `lenh`; `nen` là {ngày 'YYYY-MM-DD': (mở, thấp, cao)} VNĐ
    của nguồn giá HÔM NAY cho đúng mã của lệnh.

    Thiếu gì thì `KHONG_KIEM_DUOC` kèm lý do, không đoán, không điền.
    """
    gia_vao = lenh.get("entry_price")
    ngay_vao = _ngay(lenh.get("entry_date"))
    if not _la_so(gia_vao) or not ngay_vao:
        return KetQua(KHONG_KIEM_DUOC, None, None,
                      "thiếu giá vào hoặc ngày vào của lệnh")
    nen_vao = _lay_nen(nen, ngay_vao)
    if nen_vao is None:
        return KetQua(KHONG_KIEM_DUOC, None, None,
                      f"thiếu nến nguồn ngày vào {ngay_vao}")
    mo_vao = nen_vao[0]
    f_vao = gia_vao / mo_vao

    gia_ra = lenh.get("exit_price")
    ngay_ra = _ngay(lenh.get("exit_date"))
    nen_ra: Optional[Nen] = None
    if da_dong:
        if not _la_so(gia_ra) or not ngay_ra:
            return KetQua(KHONG_KIEM_DUOC, f_vao, None,
                          "lệnh đã đóng nhưng thiếu giá ra hoặc ngày ra")
        nen_ra = _lay_nen(nen, ngay_ra)
        if nen_ra is None:
            return KetQua(KHONG_KIEM_DUOC, f_vao, None,
                          f"thiếu nến nguồn ngày ra {ngay_ra}")

    if not _lech_qua_nguong(gia_vao, mo_vao):
        f_ra = None if nen_ra is None else gia_ra / ((nen_ra[1] + nen_ra[2]) / 2)
        return KetQua(SACH, f_vao, f_ra,
                      f"giá vào sổ lệch giá mở nguồn {abs(f_vao - 1):.1%}, "
                      f"trong ngưỡng {NGUONG_LECH:.0%}")

    if not da_dong:
        chieu = ("nguồn thấp hơn sổ — đúng dạng sự kiện quyền" if f_vao > 1
                 else "nguồn CAO hơn sổ — không phải dạng sự kiện quyền")
        return KetQua(SU_KIEN_TRONG_LUC_GIU, f_vao, None,
                      f"lệnh CÒN MỞ, giá vào sổ ÷ giá mở nguồn = {f_vao:.3f} "
                      f"(lệch quá {NGUONG_LECH:.0%}; {chieu}): cắt lỗ của sổ "
                      "đang ở cơ sở giá cũ")

    _mo, thap, cao = nen_ra
    f_ra = gia_ra / ((thap + cao) / 2)
    quy_ve = gia_ra / f_vao
    if thap * (1 - NOI_BIEN) <= quy_ve <= cao * (1 + NOI_BIEN):
        return KetQua(SACH, f_vao, f_ra,
                      f"f_vào = {f_vao:.3f} nhưng giá ra ÷ f_vào = {quy_ve:,.0f} "
                      f"nằm trong biên nguồn ngày ra [{thap:,.0f}; {cao:,.0f}]: "
                      "hai đầu cùng cơ sở giá")
    if f_ra < f_vao:
        return KetQua(SU_KIEN_TRONG_LUC_GIU, f_vao, f_ra,
                      f"f_vào = {f_vao:.3f} → f_ra = {f_ra:.3f}; giá ra ÷ f_vào = "
                      f"{quy_ve:,.0f} ngoài biên nguồn ngày ra [{thap:,.0f}; "
                      f"{cao:,.0f}]: cơ sở giá đổi GIỮA lúc vào và ra")
    return KetQua(LECH_KHAC, f_vao, f_ra,
                  f"f_vào = {f_vao:.3f} → f_ra = {f_ra:.3f} (không giảm): không "
                  "phải dạng sự kiện quyền; nghi lỗi ghi khớp cũ (gap ở SL "
                  "trước BƯỚC 123), chưa kiểm")


def dung_nen(ngay: Iterable[Any], mo: Iterable[Any], thap: Iterable[Any],
             cao: Iterable[Any], he_so: float) -> dict[str, Nen]:
    """Bốn cột của bảng OHLCV -> {ngày[:10]: (mở, thấp, cao) × hệ số}.

    `he_so` là `data_quality.price_multiplier(df)` của chính bảng ấy: sổ ghi
    VNĐ, vnstock trả nghìn đồng. Phiên có ô không phải số dương thì BỎ (không
    điền); ngày trùng thì giữ dòng cuối.
    """
    ra: dict[str, Nen] = {}
    for d, o, l, h in zip(ngay, mo, thap, cao):
        if _la_so(o) and _la_so(l) and _la_so(h):
            ra[_ngay(d)] = (float(o) * he_so, float(l) * he_so, float(h) * he_so)
    return ra


#: Trường của `Trade` mà `kiem_lenh` đọc.
TRUONG_LENH = ("id", "symbol", "entry_date", "entry_price", "exit_date",
               "exit_price")

#: Lùi thêm bấy nhiêu ngày lịch trước ngày vào sớm nhất khi tải nến, để ngày vào
#: không rơi sát mép cửa sổ tải.
LUI_NGAY_TAI = 10


@dataclass(frozen=True)
class DongSoi:
    """Một dòng kết quả cho cả sổ: lệnh + nhãn."""
    id: Any
    ma: str
    ngay_vao: str
    ngay_ra: str
    da_dong: bool
    ket_qua: KetQua


def pham_vi_tai(vi_the_mo: Iterable[Any], lenh_dong: Iterable[Any]
                ) -> tuple[list[str], Optional[str]]:
    """(danh sách mã cần nến, ngày bắt đầu tải 'YYYY-MM-DD' hoặc None).

    Chỉ tính lệnh CÓ ngày vào (lệnh chờ chưa khớp không cần nến). Ngày bắt đầu =
    ngày vào sớm nhất − `LUI_NGAY_TAI` ngày. Người gọi tải MỖI MÃ MỘT LẦN.
    """
    import datetime
    ma: set[str] = set()
    ngay_vao: list[str] = []
    for t in (*vi_the_mo, *lenh_dong):
        d = _ngay(getattr(t, "entry_date"))
        if d:
            ma.add(str(getattr(t, "symbol")))
            ngay_vao.append(d)
    if not ngay_vao:
        return sorted(ma), None
    dau = datetime.date.fromisoformat(min(ngay_vao)) - datetime.timedelta(
        days=LUI_NGAY_TAI)
    return sorted(ma), dau.isoformat()


def soi_so(vi_the_mo: Iterable[Any], lenh_dong: Iterable[Any],
           nen_theo_ma: Mapping[str, Mapping[str, Nen]]) -> list[DongSoi]:
    """Gắn nhãn mọi lệnh của `SoLenhApp` (đối tượng có `TRUONG_LENH`), theo `id`.

    `lenh_dong` mới được coi là ĐÃ ĐÓNG; `vi_the_mo` (OPEN/PENDING/CLOSING) là
    còn mở — kể cả CLOSING, lệnh đã có `exit_date` nhưng chưa khớp ra. Mã không
    có trong `nen_theo_ma` thì nến rỗng -> `KHONG_KIEM_DUOC`.
    """
    ra: list[DongSoi] = []
    for dong, nhom in ((False, vi_the_mo), (True, lenh_dong)):
        for t in nhom:
            l = {k: getattr(t, k) for k in TRUONG_LENH}
            kq = kiem_lenh(l, nen_theo_ma.get(str(l["symbol"]), {}), dong)
            ra.append(DongSoi(l["id"], str(l["symbol"]), _ngay(l["entry_date"]),
                              _ngay(l["exit_date"]) if dong else "", dong, kq))
    return sorted(ra, key=lambda d: d.id)


def tom_tat(dong: Iterable[DongSoi]) -> dict[str, int]:
    """Đếm theo trạng thái (đủ bốn khoá, kể cả 0)."""
    dem = {SACH: 0, SU_KIEN_TRONG_LUC_GIU: 0, LECH_KHAC: 0, KHONG_KIEM_DUOC: 0}
    for d in dong:
        dem[d.ket_qua.trang_thai] += 1
    return dem
