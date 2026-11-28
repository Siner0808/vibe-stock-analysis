"""Test `dow_hai_chi_so` — ghép lật của hai chuỗi chỉ số (BƯỚC 308, Dow phần 2, Lát 2, mốc B7).

VÌ SAO FILE NÀY TỒN TẠI
───────────────────────
Ô trạng thái cặp VN30 – VNMidcap (ĐO 39, đặc tả `DAC-TA-DOW2.md` mục 3) đọc HAI chuỗi lật của phần 1 và ghép
chúng thành các ĐOẠN: `xac_nhan` · `khong_xac_nhan` · `dang_cho`. Lỗi nặng nhất của loại này không nổ: một đoạn
xác nhận ghi sai NGÀY (ngày phá sớm hơn thay vì muộn hơn) hay một lật bị dùng hai lần làm số đoạn và nhãn của MỌI
ô `w` lệch, mà bảng M2/M3 của ĐO 39 vẫn in ra những con số nghe hợp lý. Nên file này chứa ba loại gác:

  1. ĐÁP SỐ TÍNH TAY, viết thẳng từng con số: bảng 16 hàng của đặc tả §3.5 (w = 3 và w = None), và hai chuỗi giá
     dựng tay CHO ĐI QUA phần 1 (`cau_truc_gia`, `la_chi_so=True`) có lật biết trước từ hình học của chuỗi;
  2. TÍNH CHẤT: đối xứng A↔B, một-đối-một, bất biến khi cắt (đặc tả §3.4: với MỌI `t`, cắt cả hai bảng ở `t`, chạy
     lại phần 1 RỒI `ghep_cap`, phải ra đúng trạng thái như chạy đủ rồi đọc tại `t`, không dung sai);
  3. BỐN CA ĐÃ ĐƯỢC NGƯỜI DÙNG DUYỆT 28/11/2026 (*"duyệt"*) mà chữ ký của ĐO 39 chưa nói:
     (Q1) *"Chọn U2"* — một lật chỉ "đã dùng" khi đoạn của nó còn mở hoặc `xac_nhan`; đoạn đóng `khong_xac_nhan`
     (mọi `ly_do`) trả lật về trạng thái RẢNH;
     (Q2) *"Ghi một đoạn 'không xác nhận — trái chiều', trễ 0, đóng ngay, không mở đoạn chờ"* — hai chuỗi lật NGƯỢC
     chiều nhau cùng một hàng (không còn đoạn mở sau bước 1–4);
     (Q3 của đặc tả) `ngay` bắt buộc: đoạn còn mở sau hàng cuối giữ `dang_cho` với `k_ket` = None, chỉ ghi `het_han`
     khi hàng `k_mo + w + 1` CÓ trong bảng.
     Chữ khai ở `docs/TIEU-CHI-DOC-TRUOC.md` (mục "Làm rõ 28/11") do BƯỚC 309 thêm, ở commit riêng, TRƯỚC lượt chạy.

BỨC TƯỜNG ĐO 39: file này chỉ dùng bảng TỔNG HỢP. Không test nào đọc dữ liệu thật của VN30, VNMidcap hay VN100,
không test nào đếm lật trên chúng. Hai gác nhập và gác lời nằm ở `tests/test_dow_hai_chi_so_buc_tuong.py`.

Quy ước: `k` là chỉ số HÀNG (từ 0) của bảng đã căn; bảng 3.5 của đặc tả đánh số p1…p16 nên `k = p − 1`.
"""
from __future__ import annotations

import pathlib
import random
import sys
from types import SimpleNamespace

import pandas as pd
import pytest

GOC = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.append(str(GOC / "tools"))

import cau_truc_gia as C  # noqa: E402
import dow_hai_chi_so as D  # noqa: E402

T, G = C.TANG, C.GIAM
LUOI = (0, 4, 5, 10, 21, None)


# ── dựng dữ liệu ──────────────────────────────────────────────────────────────────────────
def _ngay(n):
    return [d.strftime("%Y-%m-%d") for d in pd.bdate_range("2024-01-01", periods=n)]


def _lat(*dac_ta, n=16):
    """`("A", G, 1)` -> Lat ở hàng 1 của bảng `n` hàng; trả (lat_a, lat_b, ngay)."""
    ngay = _ngay(n)
    a, b = [], []
    for ten, chieu, k in dac_ta:
        (a if ten == "A" else b).append(D.Lat(k=k, ngay=ngay[k], chieu=chieu))
    return tuple(a), tuple(b), ngay


def _ghep(dac_ta, w, n=16):
    a, b, ngay = _lat(*dac_ta, n=n)
    return D.ghep_cap(a, b, w, ngay=ngay), ngay


def _t(d):
    """Dạng so sánh của một đoạn: (lead, chiều, k_mo, kết quả, k_ket, trễ, lý do)."""
    return (d.lead, d.chieu, d.k_mo, d.ket_qua, d.k_ket, d.tre, d.ly_do)


def _bo(doan):
    return [_t(d) for d in doan]


def _tt(doan, t):
    s = D.trang_thai_cap_tai(doan, t)
    return (s.gia_tri, s.chieu, s.lead, s.tre, s.ly_do)


# ═════════════════════════════ 1. BẢNG 3.5 CỦA ĐẶC TẢ ═════════════════════════════════════
#: Lật: A↓p2 · B↓p4 · A↑p7 · B↑p12 · B↓p14 · A↓p15 (p = hàng + 1).
BANG_35 = (("A", G, 1), ("B", G, 3), ("A", T, 6), ("B", T, 11), ("B", G, 13), ("A", G, 14))

# hàng k -> (trạng thái, chiều, lead, trễ, lý do) ở w = 3, từng dòng của bảng 3.5
HANG_W3 = {
    0: ("chua_du", None, None, None, None),                      # p1
    1: ("dang_cho", G, "a", None, None),                         # p2  A↓ mở E1
    2: ("dang_cho", G, "a", None, None),                         # p3
    3: ("xac_nhan", G, "a", 2, None),                            # p4  B↓ (trễ 2 ≤ 3) xác nhận E1
    4: ("xac_nhan", G, "a", 2, None),                            # p5  giữ
    5: ("xac_nhan", G, "a", 2, None),                            # p6  giữ
    6: ("dang_cho", T, "a", None, None),                         # p7  A↑ mở E2
    7: ("dang_cho", T, "a", None, None),                         # p8  tuổi 1
    8: ("dang_cho", T, "a", None, None),                         # p9  tuổi 2
    9: ("dang_cho", T, "a", None, None),                         # p10 tuổi 3 ≤ 3
    10: ("khong_xac_nhan", T, "a", None, "het_han"),             # p11 tuổi 4 > 3: hết hạn
    11: ("dang_cho", T, "b", None, None),                        # p12 B↑ mở E3 (A↑ cũ 5 hàng > 3)
    12: ("dang_cho", T, "b", None, None),                        # p13
    13: ("dang_cho", G, "b", None, None),                        # p14 B↓ lật lại: E3 đóng, E4 mở
    14: ("xac_nhan", G, "b", 1, None),                           # p15 A↓ (trễ 1) xác nhận E4
    15: ("xac_nhan", G, "b", 1, None),                           # p16
}
DOAN_W3 = [("a", G, 1, "xac_nhan", 3, 2, None),
           ("a", T, 6, "khong_xac_nhan", 10, 4, "het_han"),
           ("b", T, 11, "khong_xac_nhan", 13, 2, "lead_dao_chieu"),
           ("b", G, 13, "xac_nhan", 14, 1, None)]

# "Cùng chuỗi lật với w = None: E2 xác nhận ở p12 (trễ 5, lead A), E3 không mở; E1 và E4 như trên."
HANG_NONE = dict(HANG_W3)
HANG_NONE[10] = ("dang_cho", T, "a", None, None)                 # p11: E2 chưa hết hạn
HANG_NONE[11] = ("xac_nhan", T, "a", 5, None)                    # p12: B↑ xác nhận E2 (trễ 5), E3 không mở
HANG_NONE[12] = ("xac_nhan", T, "a", 5, None)                    # p13
DOAN_NONE = [("a", G, 1, "xac_nhan", 3, 2, None),
             ("a", T, 6, "xac_nhan", 11, 5, None),
             ("b", G, 13, "xac_nhan", 14, 1, None)]


@pytest.mark.parametrize("k", range(16))
def test_BANG_3_5_w3_tung_hang(k):
    doan, _ = _ghep(BANG_35, 3)
    assert _tt(doan, k) == HANG_W3[k], f"hàng p{k + 1}"


def test_BANG_3_5_w3_cac_doan_va_ngay():
    doan, ngay = _ghep(BANG_35, 3)
    assert _bo(doan) == DOAN_W3
    e1, e2, e3, e4 = doan
    # xác nhận: ngày = ngày MUỘN hơn trong hai ngày phá (confirmed_ts), không phải ngày mở
    assert (e1.ngay_mo, e1.ngay_ket) == (ngay[1], ngay[3]) and e1.ngay_ket > e1.ngay_mo
    assert (e4.ngay_mo, e4.ngay_ket) == (ngay[13], ngay[14])
    # hết hạn: ngày hết hạn là hàng k_mo + w + 1 = 10 (p11)
    assert (e2.k_ket, e2.ngay_ket) == (10, ngay[10])
    assert e3.ngay_ket == ngay[13]


@pytest.mark.parametrize("k", range(16))
def test_BANG_3_5_w_None_tung_hang(k):
    doan, _ = _ghep(BANG_35, None)
    assert _tt(doan, k) == HANG_NONE[k], f"hàng p{k + 1}"


def test_BANG_3_5_w_None_cac_doan():
    doan, ngay = _ghep(BANG_35, None)
    assert _bo(doan) == DOAN_NONE
    e2 = doan[1]
    assert (e2.ngay_mo, e2.ngay_ket) == (ngay[6], ngay[11])          # p12 = confirmed_ts, trễ 5
    assert all(d.w is None for d in doan)


def test_BANG_3_5_ngay_biet_cua_trang_thai():
    """`ngay_biet` = đầu đoạn không đổi: xac_nhan -> ngày xác nhận; khong_xac_nhan -> ngày kết; dang_cho -> ngày mở."""
    doan, ngay = _ghep(BANG_35, 3)
    assert D.trang_thai_cap_tai(doan, 5).ngay_biet == ngay[3]       # xac_nhan giữ nguyên ngày xác nhận
    assert D.trang_thai_cap_tai(doan, 8).ngay_biet == ngay[6]       # dang_cho: ngày mở
    assert D.trang_thai_cap_tai(doan, 10).ngay_biet == ngay[10]     # khong_xac_nhan: ngày kết (hết hạn)
    assert D.trang_thai_cap_tai(doan, 0).ngay_biet is None


def test_BANG_3_5_con_lai_cua_dang_cho():
    """Đoạn chờ ở w hữu hạn còn `w - (t - k_mo)` phiên (0 ở đúng hàng cuối cùng còn xác nhận được)."""
    doan, _ = _ghep(BANG_35, 3)
    assert [D.trang_thai_cap_tai(doan, t).con_lai for t in (6, 7, 8, 9)] == [3, 2, 1, 0]
    assert D.trang_thai_cap_tai(doan, 3).con_lai is None            # xac_nhan: không còn chờ gì
    nd, _ = _ghep(BANG_35, None)
    assert D.trang_thai_cap_tai(nd, 8).con_lai is None               # w = None: không giới hạn


# Các ô khác của lưới, tính tay trên CÙNG sáu lật (xem chú thích từng ô)
def test_BANG_3_5_w0_chi_cung_ngay_moi_xac_nhan():
    """w = 0: mọi đoạn hết hạn ở hàng kế (k_mo + 1); sáu lật cách nhau nên KHÔNG đoạn nào xác nhận."""
    doan, _ = _ghep(BANG_35, 0)
    assert _bo(doan) == [("a", G, 1, "khong_xac_nhan", 2, 1, "het_han"),
                         ("b", G, 3, "khong_xac_nhan", 4, 1, "het_han"),
                         ("a", T, 6, "khong_xac_nhan", 7, 1, "het_han"),
                         ("b", T, 11, "khong_xac_nhan", 12, 1, "het_han"),
                         ("b", G, 13, "khong_xac_nhan", 14, 1, "het_han"),
                         ("a", G, 14, "khong_xac_nhan", 15, 1, "het_han")]


def test_BANG_3_5_w4_hang_het_han_la_k_mo_cong_w_cong_1():
    """w = 4: E2 (mở p7 = hàng 6) hết hạn ở hàng 11 (6 + 4 + 1), đúng hàng B↑ lật; lật A↑ cũ 5 hàng > 4 nên E3 mở."""
    doan, _ = _ghep(BANG_35, 4)
    assert _bo(doan) == [("a", G, 1, "xac_nhan", 3, 2, None),
                         ("a", T, 6, "khong_xac_nhan", 11, 5, "het_han"),
                         ("b", T, 11, "khong_xac_nhan", 13, 2, "lead_dao_chieu"),
                         ("b", G, 13, "xac_nhan", 14, 1, None)]


@pytest.mark.parametrize("w", [5, 10, 21])
def test_BANG_3_5_w_tu_5_tro_len_trung_w_None(w):
    """w = 5: B↑ ở hàng 11 cách A↑ (hàng 6) ĐÚNG 5 = w nên vẫn xác nhận (biên `≤ w`); w lớn hơn không đổi gì."""
    doan, _ = _ghep(BANG_35, w)
    assert _bo(doan) == DOAN_NONE


def test_BANG_3_5_khong_dung_dem_ngay_lich():
    """Đếm theo HÀNG của bảng đã căn: hàng p11 là hàng thứ 11 dù hai ngày dương lịch cách nhau cuối tuần."""
    doan, ngay = _ghep(BANG_35, 3)
    assert doan[1].k_ket - doan[1].k_mo == 4 and ngay[10] > ngay[6]


# ═════════════════════════ 2. CA ĐÃ DUYỆT 28/11/2026 (Q1 U2 · Q2 trái chiều · Q3 ngay) ═════════════════════
def test_Q1_U2_lat_cua_doan_khong_xac_nhan_thanh_RANH():
    """*"Chọn U2"*. w = 5, n = 8: A↓2 mở E1; B↑3 đóng E1 (ben_kia_nguoc) rồi mở E2; B↓4 đóng E2 (lead_dao_chieu).
    A↓2 đã RẢNH (E1 đóng khong_xac_nhan) và cách B↓4 đúng 2 hàng ≤ 5 -> xác nhận NGAY, lead A, trễ 2.
    Dưới U1 (lật dùng rồi là dùng mãi) chỗ này là một đoạn dang_cho của B."""
    doan, ngay = _ghep((("A", G, 2), ("B", T, 3), ("B", G, 4)), 5, n=8)
    assert _bo(doan) == [("a", G, 2, "khong_xac_nhan", 3, 1, "ben_kia_nguoc"),
                         ("b", T, 3, "khong_xac_nhan", 4, 1, "lead_dao_chieu"),
                         ("a", G, 2, "xac_nhan", 4, 2, None)]
    assert doan[2].ngay_mo == ngay[2] and doan[2].ngay_ket == ngay[4]
    # "đoạn MỚI NHẤT" là đoạn được TẠO sau cùng, không phải đoạn có k_mo lớn nhất (E2 có k_mo = 3 > 2)
    assert [_tt(doan, t) for t in (2, 3, 4, 7)] == [
        ("dang_cho", G, "a", None, None),
        ("dang_cho", T, "b", None, None),
        ("xac_nhan", G, "a", 2, None),
        ("xac_nhan", G, "a", 2, None)]


def test_Q1_U2_bien_dung_w_la_xac_nhan_ngay_w_nho_hon_la_mo_doan():
    """Cùng ca, B↓ ở hàng 5 (cách A↓2 đúng 3), bảng 8 hàng: w = 3 -> xác nhận ngay (≤ w); w = 2 -> KHÔNG (3 > 2), mở
    đoạn chờ (hàng hết hạn 8 không có trong bảng nên vẫn dang_cho)."""
    xn, _ = _ghep((("A", G, 2), ("B", T, 3), ("B", G, 5)), 3, n=8)
    assert _bo(xn)[-1] == ("a", G, 2, "xac_nhan", 5, 3, None)
    cho, _ = _ghep((("A", G, 2), ("B", T, 3), ("B", G, 5)), 2, n=8)
    assert _bo(cho)[-1] == ("b", G, 5, "dang_cho", None, None, None)


def test_buoc_5_chon_lat_ranh_GAN_NHAT_khong_phai_xa_nhat():
    """Hai lật rảnh cùng chiều của chuỗi A (A↓1 và A↓3, cả hai đã được trả rảnh vì đoạn của chúng đóng bằng
    lead_dao_chieu), w = 20. B↓6 đóng đoạn của A↑4 (ben_kia_nguoc) rồi xác nhận với lật GẦN nhất, A↓3 (trễ 3),
    không phải A↓1 (trễ 5)."""
    doan, ngay = _ghep((("A", G, 1), ("A", T, 2), ("A", G, 3), ("A", T, 4), ("B", G, 6)), 20, n=10)
    assert _bo(doan) == [("a", G, 1, "khong_xac_nhan", 2, 1, "lead_dao_chieu"),
                         ("a", T, 2, "khong_xac_nhan", 3, 1, "lead_dao_chieu"),
                         ("a", G, 3, "khong_xac_nhan", 4, 1, "lead_dao_chieu"),
                         ("a", T, 4, "khong_xac_nhan", 6, 2, "ben_kia_nguoc"),
                         ("a", G, 3, "xac_nhan", 6, 3, None)]
    assert doan[-1].ngay_mo == ngay[3]


def test_Q1_lat_dung_trong_doan_lead_dao_chieu_cung_thanh_ranh():
    """A↓1 mở E1; A↑3 lật lại (bước 2: lead_dao_chieu), A↑3 mở E2; B↓4 đóng E2 (bước 3: ben_kia_nguoc). A↓1 RẢNH
    (E1 khong_xac_nhan) nên B↓4 xác nhận với nó (trễ 3). Bỏ bước 2 -> E1 còn mở và danh sách đoạn khác hẳn."""
    doan, _ = _ghep((("A", G, 1), ("A", T, 3), ("B", G, 4)), 5, n=8)
    assert _bo(doan) == [("a", G, 1, "khong_xac_nhan", 3, 2, "lead_dao_chieu"),
                         ("a", T, 3, "khong_xac_nhan", 4, 1, "ben_kia_nguoc"),
                         ("a", G, 1, "xac_nhan", 4, 3, None)]


def test_buoc_3_lat_dong_doan_KHONG_bi_danh_dau_da_dung():
    """Lật đóng đoạn ở bước 3 (B↑3 đóng E1) vẫn đi tiếp sang bước 5 như lật đóng ở bước 2 (bảng 3.5, p14): nó MỞ E2."""
    doan, _ = _ghep((("A", G, 2), ("B", T, 3)), 5, n=8)
    assert _bo(doan) == [("a", G, 2, "khong_xac_nhan", 3, 1, "ben_kia_nguoc"),
                         ("b", T, 3, "dang_cho", None, None, None)]


def test_buoc_3_ben_kia_nguoc_hang_dau_tien():
    """Bước 3 đứng một mình: chuỗi kia lật NGƯỢC chiều đoạn đang mở -> khong_xac_nhan, ben_kia_nguoc, tre = k − k_mo."""
    doan, ngay = _ghep((("A", T, 2), ("B", G, 4)), 10, n=8)
    assert _bo(doan)[0] == ("a", T, 2, "khong_xac_nhan", 4, 2, "ben_kia_nguoc")
    assert doan[0].ngay_ket == ngay[4]


def test_buoc_2_lead_dao_chieu_hang_dau_tien():
    doan, ngay = _ghep((("A", T, 2), ("A", G, 5)), 10, n=8)
    assert _bo(doan)[0] == ("a", T, 2, "khong_xac_nhan", 5, 3, "lead_dao_chieu")
    assert doan[0].ngay_ket == ngay[5]
    # lead là chuỗi B cũng thế: không chỉ A được làm lead
    d2, _ = _ghep((("B", T, 2), ("B", G, 5)), 10, n=8)
    assert _bo(d2)[0] == ("b", T, 2, "khong_xac_nhan", 5, 3, "lead_dao_chieu")


def test_Q2_trai_chieu_mot_doan_dong_ngay_khong_mo_doan_cho():
    """*"Ghi một đoạn 'không xác nhận — trái chiều', trễ 0, đóng ngay, không mở đoạn chờ"*: A↑ và B↓ cùng hàng 7,
    không đoạn mở (E1 do A↓1 mở đã hết hạn ở hàng 5). MỘT đoạn: lead dong_thoi, chiều None, ben_kia_nguoc,
    k_mo = k_ket = 7, trễ 0."""
    doan, ngay = _ghep((("A", G, 1), ("A", T, 7), ("B", G, 7)), 3, n=10)
    assert _bo(doan) == [("a", G, 1, "khong_xac_nhan", 5, 4, "het_han"),
                         ("dong_thoi", None, 7, "khong_xac_nhan", 7, 0, "ben_kia_nguoc")]
    assert doan[1].ngay_mo == doan[1].ngay_ket == ngay[7]
    s = D.trang_thai_cap_tai(doan, 7)
    assert (s.gia_tri, s.chieu, s.lead, s.tre, s.ly_do, s.ngay_biet) == (
        "khong_xac_nhan", None, "dong_thoi", None, "ben_kia_nguoc", ngay[7])
    assert D.trang_thai_cap_tai(doan, 9).gia_tri == "khong_xac_nhan"          # giữ tới khi lật mới mở đoạn kế
    assert not any(d.ket_qua == "dang_cho" for d in doan), "trái chiều KHÔNG mở đoạn chờ"


def test_Q2_trai_chieu_doi_xung_A_B():
    """Đổi A↔B cho đúng cùng đoạn và trạng thái (cả `lead`, vì lead là dong_thoi): đây là ca làm sai đối xứng nếu xử lý
    tuần tự A rồi B (A↑ mở rồi B↓ đóng và mở lại -> trạng thái dang_cho ↓; đảo vai thì dang_cho ↑)."""
    ban, _ = _ghep((("A", T, 5), ("B", G, 5)), 3, n=9)
    dao, _ = _ghep((("B", T, 5), ("A", G, 5)), 3, n=9)
    assert _bo(ban) == _bo(dao) == [("dong_thoi", None, 5, "khong_xac_nhan", 5, 0, "ben_kia_nguoc")]
    for t in range(9):
        assert _tt(ban, t) == _tt(dao, t)


def test_Q2_hai_lat_trai_chieu_deu_RANH_cho_buoc_5_ve_sau():
    """Quyết định của leader theo Q1 = U2: đoạn trái chiều đóng khong_xac_nhan nên CẢ HAI lật rảnh. Ở hàng 7 B↑ lật:
    A↑5 rảnh và cách 2 ≤ 3 -> xác nhận ngay, lead A, k_mo = 5, trễ 2."""
    doan, _ = _ghep((("A", T, 5), ("B", G, 5), ("B", T, 7)), 3, n=10)
    assert _bo(doan) == [("dong_thoi", None, 5, "khong_xac_nhan", 5, 0, "ben_kia_nguoc"),
                         ("a", T, 5, "xac_nhan", 7, 2, None)]


def test_Q2_cung_chieu_cung_hang_la_dong_thoi_tre_0():
    """Cùng hàng, CÙNG chiều: một đoạn xác nhận ngay, lead dong_thoi, trễ 0 (A mở, B xác nhận ở bước 4 cùng hàng)."""
    doan, ngay = _ghep((("A", G, 3), ("B", G, 3)), 3, n=8)
    assert _bo(doan) == [("dong_thoi", G, 3, "xac_nhan", 3, 0, None)]
    assert doan[0].ngay_mo == doan[0].ngay_ket == ngay[3]
    assert _tt(doan, 3) == ("xac_nhan", G, "dong_thoi", 0, None)


def test_cung_hang_lead_lat_lai_va_ben_kia_cung_chieu_cu_la_trai_chieu():
    """Đoạn A↓ đang mở; hôm nay A↑ (bước 2 thắng: lead_dao_chieu) và B↓ (cùng chiều đoạn cũ nhưng đoạn đã đóng).
    Sau bước 1–4 không còn đoạn mở và hai lật hôm nay NGƯỢC nhau -> một đoạn trái chiều."""
    doan, _ = _ghep((("A", G, 1), ("A", T, 4), ("B", G, 4)), 5, n=8)
    assert _bo(doan) == [("a", G, 1, "khong_xac_nhan", 4, 3, "lead_dao_chieu"),
                         ("dong_thoi", None, 4, "khong_xac_nhan", 4, 0, "ben_kia_nguoc")]


def test_Q3_doan_con_mo_sau_hang_cuoi_giu_dang_cho_k_ket_None():
    """Bảng 10 hàng, w = 3. Lật ở hàng 6: hàng hết hạn 10 KHÔNG có -> dang_cho, k_ket và ngay_ket None, tre None."""
    doan, ngay = _ghep((("A", G, 6),), 3, n=10)
    d = doan[0]
    assert (d.ket_qua, d.k_ket, d.ngay_ket, d.tre, d.ly_do) == ("dang_cho", None, None, None, None)
    assert _tt(doan, 9) == ("dang_cho", G, "a", None, None)
    # lật ở hàng 5: hàng hết hạn 9 CÓ trong bảng -> ghi het_han đúng ở hàng 9
    d5, ngay5 = _ghep((("A", G, 5),), 3, n=10)
    assert (d5[0].ket_qua, d5[0].k_ket, d5[0].ngay_ket, d5[0].ly_do) == ("khong_xac_nhan", 9, ngay5[9], "het_han")
    assert _tt(d5, 8)[0] == "dang_cho" and _tt(d5, 9)[0] == "khong_xac_nhan"


def test_Q3_w_None_khong_bao_gio_het_han():
    doan, _ = _ghep((("A", T, 1),), None, n=30)
    assert _bo(doan) == [("a", T, 1, "dang_cho", None, None, None)]
    assert D.trang_thai_cap_tai(doan, 29).gia_tri == "dang_cho"


def test_Q3_ghep_cap_PHAI_nhan_ngay_tu_khoa_va_kiem_tra_no():
    a, b, ngay = _lat(("A", G, 1), n=6)
    with pytest.raises(TypeError):
        D.ghep_cap(a, b, 3)                                   # `ngay` bắt buộc
    with pytest.raises(TypeError):
        D.ghep_cap(a, b, 3, ngay)                             # và phải là từ khoá
    with pytest.raises(ValueError):
        D.ghep_cap((D.Lat(k=9, ngay="2024-01-01", chieu=G),), b, 3, ngay=ngay)          # k ngoài bảng
    with pytest.raises(ValueError):
        D.ghep_cap((D.Lat(k=6, ngay="2024-01-09", chieu=G),), b, 3, ngay=ngay)          # k = số hàng: ngoài bảng
    with pytest.raises(ValueError):
        D.ghep_cap((D.Lat(k=1, ngay="1999-01-01", chieu=G),), b, 3, ngay=ngay)          # ngày ≠ ngay[k]
    with pytest.raises(ValueError):
        D.ghep_cap((D.Lat(k=-1, ngay=ngay[-1], chieu=G),), b, 3, ngay=ngay)             # k âm
    with pytest.raises(ValueError):
        D.ghep_cap(a, b, -1, ngay=ngay)                                                 # w âm
    with pytest.raises(ValueError):
        D.ghep_cap(a, b, 2.5, ngay=ngay)                                                # w không nguyên


def test_hai_lat_cua_mot_chuoi_cung_hang_hay_cung_chieu_nhau_bi_tu_choi():
    """Phần 1 không thể sinh ra chúng (CHOCH luôn ngược thiên hướng, một nến một lật mỗi chuỗi): nổ chứ không đoán."""
    ngay = _ngay(8)
    cung_hang = (D.Lat(2, ngay[2], G), D.Lat(2, ngay[2], T))
    with pytest.raises(ValueError):
        D.ghep_cap(cung_hang, (), 3, ngay=ngay)
    khong_luan_phien = (D.Lat(2, ngay[2], G), D.Lat(4, ngay[4], G))
    with pytest.raises(ValueError):
        D.ghep_cap((), khong_luan_phien, 3, ngay=ngay)
    khong_tang = (D.Lat(4, ngay[4], G), D.Lat(2, ngay[2], T))
    with pytest.raises(ValueError):
        D.ghep_cap(khong_tang, (), 3, ngay=ngay)
    with pytest.raises(ValueError):
        D.ghep_cap((D.Lat(2, ngay[2], "xuong"),), (), 3, ngay=ngay)


def test_khong_co_lat_thi_chua_du_va_khong_doan():
    doan = D.ghep_cap((), (), 3, ngay=_ngay(5))
    assert doan == ()
    assert [_tt(doan, t) for t in range(5)] == [("chua_du", None, None, None, None)] * 5
    assert D.ghep_cap((), (), None, ngay=()) == ()


def test_chi_mot_chuoi_lat_thi_van_mo_doan_cho_roi_het_han():
    doan, _ = _ghep((("B", T, 2),), 3, n=12)
    assert _bo(doan) == [("b", T, 2, "khong_xac_nhan", 6, 4, "het_han")]


# ═════════════════════════════ 3. MỘT-ĐỐI-MỘT ═════════════════════════════════════════════
def test_mot_doi_mot_lat_da_xac_nhan_khong_xac_nhan_lan_nua():
    """w = 5. A↓2 + B↓4 xác nhận E1. B↑5 mở E2, B↓6 đóng E2. B↓6 cách A↓2 là 4 ≤ 5, nhưng A↓2 ĐÃ DÙNG trong đoạn
    xac_nhan -> không xác nhận lần nữa: mở đoạn chờ của B. Bỏ luật một-đối-một thì ra một xac_nhan thứ hai."""
    doan, _ = _ghep((("A", G, 2), ("B", G, 4), ("B", T, 5), ("B", G, 6)), 5, n=10)
    assert _bo(doan) == [("a", G, 2, "xac_nhan", 4, 2, None),
                         ("b", T, 5, "khong_xac_nhan", 6, 1, "lead_dao_chieu"),
                         ("b", G, 6, "dang_cho", None, None, None)]


def _lat_ngau(rng, n, so):
    ks = sorted(rng.sample(range(n), so))
    chieu = rng.choice([T, G])
    ngay = _ngay(n)
    ra = []
    for k in ks:
        ra.append(D.Lat(k, ngay[k], chieu))
        chieu = T if chieu == G else G
    return tuple(ra)


@pytest.mark.parametrize("hat", range(60))
def test_mot_doi_mot_tinh_chat_tren_chuoi_lat_ngau(hat):
    """Tính chất, 60 hạt × lưới w: không lật nào nằm trong hai đoạn CÒN SỐNG (xac_nhan hoặc dang_cho) cùng lúc, và
    đoạn được tạo theo thứ tự (k_tao không giảm; mỗi hàng tạo tối đa một đoạn)."""
    rng = random.Random(hat)
    n = rng.randint(20, 70)
    a, b = _lat_ngau(rng, n, rng.randint(0, 9)), _lat_ngau(rng, n, rng.randint(0, 9))
    ngay = _ngay(n)
    for w in LUOI:
        doan = D.ghep_cap(a, b, w, ngay=ngay)
        song = [d for d in doan if d.ket_qua in ("xac_nhan", "dang_cho")]
        thay = []
        for d in song:
            chuoi_mo = "a" if d.lead == "dong_thoi" else d.lead              # đoạn cùng hàng: lat_mo của A, lat_kia của B
            chuoi_kia = "b" if chuoi_mo == "a" else "a"
            thay.append((chuoi_mo, d.lat_mo))
            if d.lat_kia is not None:
                thay.append((chuoi_kia, d.lat_kia))
        assert len(thay) == len(set(thay)), (hat, w)
        assert [d.k_tao for d in doan] == sorted({d.k_tao for d in doan}), (hat, w)
        for d in doan:
            assert d.k_tao <= (d.k_ket if d.k_ket is not None else n)
            if d.ket_qua == "xac_nhan":
                assert d.tre == d.k_ket - d.k_mo >= 0 and (w is None or d.tre <= w)
            if d.ket_qua == "khong_xac_nhan" and d.ly_do == "het_han":
                assert d.k_ket == d.k_mo + w + 1


# ═════════════════════════════ 4. ĐỐI XỨNG A↔B VÀ BẤT BIẾN KHI CẮT (lật ngẫu nhiên) ═══════════
_DAO = {"a": "b", "b": "a", "dong_thoi": "dong_thoi", None: None}


@pytest.mark.parametrize("hat", range(60))
def test_doi_xung_A_B_cung_trang_thai_chi_lead_doi_nhan(hat):
    """Đối xứng (đặc tả §3.2): đổi A↔B ra CÙNG trạng thái, chỉ `lead` đổi nhãn. Có cả ca hai chuỗi lật cùng hàng
    (cùng chiều lẫn trái chiều)."""
    rng = random.Random(1000 + hat)
    n = rng.randint(12, 60)
    a, b = _lat_ngau(rng, n, rng.randint(1, 9)), _lat_ngau(rng, n, rng.randint(1, 9))
    ngay = _ngay(n)
    for w in LUOI:
        xuoi = D.ghep_cap(a, b, w, ngay=ngay)
        nguoc = D.ghep_cap(b, a, w, ngay=ngay)
        assert [(_DAO[d.lead],) + _t(d)[1:] for d in xuoi] == _bo(nguoc), (hat, w)
        for t in range(n):
            x, y = D.trang_thai_cap_tai(xuoi, t), D.trang_thai_cap_tai(nguoc, t)
            assert (x.gia_tri, x.chieu, x.tre, x.ly_do, x.k_biet, x.ngay_biet, x.con_lai) == (
                y.gia_tri, y.chieu, y.tre, y.ly_do, y.k_biet, y.ngay_biet, y.con_lai), (hat, w, t)
            assert _DAO[x.lead] == y.lead


def test_doi_xung_A_B_tren_bang_3_5():
    xuoi, ngay = _ghep(BANG_35, 3)
    dao = tuple((("B" if ten == "A" else "A"), c, k) for ten, c, k in BANG_35)
    nguoc, _ = _ghep(dao, 3)
    assert [(_DAO[d.lead],) + _t(d)[1:] for d in xuoi] == _bo(nguoc)
    # và `lead` của E1 đúng là chuỗi mở trước, không phải "chuỗi A"
    assert (_bo(xuoi)[0][0], _bo(nguoc)[0][0]) == ("a", "b")


def _cat(lat, t):
    return tuple(x for x in lat if x.k <= t)


@pytest.mark.parametrize("hat", range(60))
def test_bat_bien_khi_cat_tren_lat_ngau(hat):
    """§3.4 ở mức HÀM: với MỌI t, cắt hai chuỗi lật và `ngay` ở t rồi `ghep_cap` ra đúng trạng thái như chạy đủ rồi
    đọc tại t (mọi trường, không dung sai)."""
    rng = random.Random(2000 + hat)
    n = rng.randint(12, 60)
    a, b = _lat_ngau(rng, n, rng.randint(1, 9)), _lat_ngau(rng, n, rng.randint(1, 9))
    ngay = _ngay(n)
    for w in LUOI:
        day_du = D.ghep_cap(a, b, w, ngay=ngay)
        for t in range(n):
            cat = D.ghep_cap(_cat(a, t), _cat(b, t), w, ngay=ngay[:t + 1])
            assert D.trang_thai_cap_tai(cat, t) == D.trang_thai_cap_tai(day_du, t), (hat, w, t)


# ═════════════════════════ 5. `lat_tu_cau_truc`: MỘT LẬT LÀ CHOCH Ở CẤP SWING ═══════════════
def _sk(cap, loai, chieu, k, ngay="2024-01-01"):
    return SimpleNamespace(cap=cap, loai=loai, chieu=chieu, ngay_xay_ra=ngay, ngay_biet=ngay,
                           chi_so_xay_ra=k, chi_so_biet=k)


def test_lat_chi_la_CHOCH_cap_swing_khong_KHOI_DAU_khong_BOS_khong_noi_bo():
    ngay = _ngay(20)
    cs = SimpleNamespace(su_kien=(
        _sk("swing", "KHOI_DAU", T, 3, ngay[3]),     # chưa có gì để đảo: KHÔNG là lật
        _sk("noi_bo", "KHOI_DAU", T, 3, ngay[3]),
        _sk("swing", "BOS", T, 5, ngay[5]),          # cùng thiên hướng: KHÔNG là lật
        _sk("noi_bo", "CHOCH", G, 6, ngay[6]),       # cấp nội bộ: KHÔNG là lật
        _sk("swing", "CHOCH", G, 9, ngay[9]),        # LẬT
        _sk("swing", "BOS", G, 11, ngay[11]),
        _sk("swing", "CHOCH", T, 14, ngay[14])))     # LẬT
    assert D.lat_tu_cau_truc(cs) == (D.Lat(9, ngay[9], G), D.Lat(14, ngay[14], T))
    assert D.lat_tu_cau_truc(SimpleNamespace(su_kien=())) == ()


def test_lat_dung_ngay_biet_va_chi_so_biet():
    """`k` = `chi_so_biet` (hàng nến đóng cửa phá mốc, biết ngay), `ngay` = `ngay_biet`."""
    sk = SimpleNamespace(cap="swing", loai="CHOCH", chieu=G, ngay_xay_ra="2024-02-01", ngay_biet="2024-02-02",
                         chi_so_xay_ra=7, chi_so_biet=8)
    assert D.lat_tu_cau_truc(SimpleNamespace(su_kien=(sk,))) == (D.Lat(8, "2024-02-02", G),)


# ═════════════════════════ 6. HAI CHUỖI GIÁ DỰNG TAY ĐI QUA PHẦN 1 (đáp số biết trước) ═══════
def _chuoi(legs, g0=1000.0):
    """Chuỗi giá tuyến tính từng đoạn: (độ dời, số phiên). high = low = close; bước tròn nên mọi mốc phá tính tay được."""
    dong = [g0]
    for delta, so in legs:
        buoc = delta / so
        for _ in range(so):
            dong.append(dong[-1] + buoc)
    return pd.DataFrame({"time": pd.bdate_range("2024-01-01", periods=len(dong)),
                         "high": dong, "low": dong, "close": dong})


#: A: lên 200 (20 phiên, đỉnh 1200 ở hàng 20), xuống 100 (đáy 1100 ở hàng 30), lên 200 (đỉnh 1300 ở hàng 50),
#: xuống 300 (xuyên đáy 1100 ở hàng 71: 1300 − 10 j < 1100 ⇔ j ≥ 21 -> CHOCH giảm ở hàng 71), lên 150 (đỉnh 1150 ở
#: hàng 95), xuống 100 (đáy 1050 ở hàng 105), lên 200 (đóng cửa vượt đỉnh 1150 ở hàng 116 -> CHOCH tăng), xuống 250
#: (xuyên đáy 1050 ở hàng 146 -> CHOCH giảm), rồi đi ngang 19 phiên cho đủ 170 hàng. KHOI_DAU tăng ở hàng 41
#: (đóng cửa vượt đỉnh 1200 lần đầu): KHÔNG phải lật.
LEGS_A = [(200, 20), (-100, 10), (200, 20), (-300, 30), (150, 15), (-100, 10), (200, 20), (-250, 25), (0, 19)]
#: B: cùng khung nhưng xuống nhanh hơn ở chặng 4 (bước 12: 1300 − 12 j < 1100 ⇔ j ≥ 17 -> CHOCH giảm ở hàng 67,
#: SỚM hơn A 4 hàng), lên 200 trong 40 phiên (bước 5: 1050 + 5 j > 1150 ⇔ j ≥ 21 -> CHOCH tăng ở hàng 121, MUỘN hơn A 5
#: hàng), xuống 250 (đỉnh 1250 ở hàng 140; xuyên đáy 1050 ở hàng 161, MUỘN hơn A 15 hàng).
LEGS_B = [(200, 20), (-100, 10), (200, 20), (-300, 25), (150, 15), (-100, 10), (200, 40), (-250, 25), (0, 4)]
LAT_A = ((71, G), (116, T), (146, G))
LAT_B = ((67, G), (121, T), (161, G))
N_CHUOI = 170


@pytest.fixture(scope="module")
def hai_chuoi():
    return _chuoi(LEGS_A), _chuoi(LEGS_B)


def _lat_phan1(df):
    return D.lat_tu_cau_truc(C.doc_cau_truc(df, la_chi_so=True))


def test_phan_1_cho_dung_lat_biet_truoc_tren_hai_chuoi_dung_tay(hai_chuoi):
    """Đáp số tính tay ở chú thích trên; KHOI_DAU (hàng 41, cả hai chuỗi) KHÔNG nằm trong danh sách lật."""
    df_a, df_b = hai_chuoi
    assert len(df_a) == len(df_b) == N_CHUOI
    ngay = [d.strftime("%Y-%m-%d") for d in df_a["time"]]
    assert _lat_phan1(df_a) == tuple(D.Lat(k, ngay[k], c) for k, c in LAT_A)
    assert _lat_phan1(df_b) == tuple(D.Lat(k, ngay[k], c) for k, c in LAT_B)
    sk = [e for e in C.doc_cau_truc(df_a, la_chi_so=True).su_kien if e.cap == "swing"]
    assert (sk[0].loai, sk[0].chi_so_biet) == ("KHOI_DAU", 41), "KHOI_DAU có thật nhưng không là lật"


def _doan_hai_chuoi(hai_chuoi, w):
    df_a, df_b = hai_chuoi
    ngay = [d.strftime("%Y-%m-%d") for d in df_a["time"]]
    return D.ghep_cap(_lat_phan1(df_a), _lat_phan1(df_b), w, ngay=ngay), ngay


E1 = ("b", G, 67, "xac_nhan", 71, 4, None)           # B↓67 mở, A↓71 xác nhận (trễ 4)
E2 = ("a", T, 116, "xac_nhan", 121, 5, None)         # A↑116 mở, B↑121 xác nhận (trễ 5 = biên của w = 5)


@pytest.mark.parametrize("w", [None, 21])
def test_hai_chuoi_dung_tay_w_lon_ba_doan_deu_xac_nhan(hai_chuoi, w):
    doan, _ = _doan_hai_chuoi(hai_chuoi, w)
    assert _bo(doan) == [E1, E2, ("a", G, 146, "xac_nhan", 161, 15, None)]


def test_hai_chuoi_dung_tay_w10_doan_cuoi_het_han_roi_mo_doan_con_mo_o_cuoi_bang(hai_chuoi):
    """w = 10: A↓146 hết hạn ở hàng 157 (146 + 10 + 1); B↓161 không xác nhận được (A↓146 cách 15 > 10; A↓71 đã dùng)
    nên MỞ đoạn mới; hàng hết hạn 172 không có trong bảng 170 hàng -> dang_cho, k_ket None."""
    doan, ngay = _doan_hai_chuoi(hai_chuoi, 10)
    assert _bo(doan) == [E1, E2, ("a", G, 146, "khong_xac_nhan", 157, 11, "het_han"),
                         ("b", G, 161, "dang_cho", None, None, None)]
    assert doan[2].ngay_ket == ngay[157]
    assert doan[3].ngay_ket is None


def test_hai_chuoi_dung_tay_w5_het_han_ca_hai_doan_cuoi(hai_chuoi):
    """w = 5: E2 vẫn xác nhận (trễ 5 ≤ 5); hai đoạn cuối hết hạn (hàng 152 và 167, cả hai trong bảng 170 hàng)."""
    doan, _ = _doan_hai_chuoi(hai_chuoi, 5)
    assert _bo(doan) == [E1, E2, ("a", G, 146, "khong_xac_nhan", 152, 6, "het_han"),
                         ("b", G, 161, "khong_xac_nhan", 167, 6, "het_han")]


def test_hai_chuoi_dung_tay_w0_khong_doan_nao_xac_nhan(hai_chuoi):
    doan, _ = _doan_hai_chuoi(hai_chuoi, 0)
    assert _bo(doan) == [("b", G, 67, "khong_xac_nhan", 68, 1, "het_han"),
                         ("a", G, 71, "khong_xac_nhan", 72, 1, "het_han"),
                         ("a", T, 116, "khong_xac_nhan", 117, 1, "het_han"),
                         ("b", T, 121, "khong_xac_nhan", 122, 1, "het_han"),
                         ("a", G, 146, "khong_xac_nhan", 147, 1, "het_han"),
                         ("b", G, 161, "khong_xac_nhan", 162, 1, "het_han")]


def test_hai_chuoi_dung_tay_trang_thai_tai_cac_hang_chon_w10(hai_chuoi):
    doan, ngay = _doan_hai_chuoi(hai_chuoi, 10)
    assert _tt(doan, 66)[0] == "chua_du"
    assert _tt(doan, 67) == ("dang_cho", G, "b", None, None)            # B↓ mở trước
    assert _tt(doan, 70) == ("dang_cho", G, "b", None, None)
    s = D.trang_thai_cap_tai(doan, 71)
    assert (s.gia_tri, s.lead, s.tre, s.ngay_biet) == ("xac_nhan", "b", 4, ngay[71])
    assert _tt(doan, 115) == ("xac_nhan", G, "b", 4, None)              # giữ tới khi lật mới mở đoạn kế
    assert _tt(doan, 116) == ("dang_cho", T, "a", None, None)
    assert _tt(doan, 121) == ("xac_nhan", T, "a", 5, None)
    assert _tt(doan, 156) == ("dang_cho", G, "a", None, None) and D.trang_thai_cap_tai(doan, 156).con_lai == 0
    assert _tt(doan, 157) == ("khong_xac_nhan", G, "a", None, "het_han")
    assert _tt(doan, 161) == ("dang_cho", G, "b", None, None)
    assert _tt(doan, N_CHUOI - 1) == ("dang_cho", G, "b", None, None)


def test_tu_ghep_VN30_VN30_moi_doan_xac_nhan_tre_0(hai_chuoi):
    """Đối chứng (i) của ĐO 39 ở mức hàm: hai chuỗi GIỐNG HỆT -> mọi lật cùng hàng cùng chiều -> mọi đoạn xac_nhan,
    trễ 0, lead dong_thoi, ở MỌI ô w."""
    df_a, _ = hai_chuoi
    lat = _lat_phan1(df_a)
    ngay = [d.strftime("%Y-%m-%d") for d in df_a["time"]]
    for w in LUOI:
        doan = D.ghep_cap(lat, lat, w, ngay=ngay)
        assert _bo(doan) == [("dong_thoi", c, k, "xac_nhan", k, 0, None) for k, c in LAT_A], w


def test_doi_xung_A_B_tren_hai_chuoi_dung_tay(hai_chuoi):
    df_a, df_b = hai_chuoi
    ngay = [d.strftime("%Y-%m-%d") for d in df_a["time"]]
    la, lb = _lat_phan1(df_a), _lat_phan1(df_b)
    for w in LUOI:
        xuoi, nguoc = D.ghep_cap(la, lb, w, ngay=ngay), D.ghep_cap(lb, la, w, ngay=ngay)
        assert [(_DAO[d.lead],) + _t(d)[1:] for d in xuoi] == _bo(nguoc), w


def test_BAT_BIEN_KHI_CAT_tren_hai_chuoi_di_qua_phan_1(hai_chuoi):
    """Gác chính của đặc tả §3.4, KHÔNG dung sai: với MỌI hàng t, cắt cả hai BẢNG GIÁ ở t, chạy lại phần 1
    (`la_chi_so=True`) rồi `ghep_cap`, phải ra đúng trạng thái như chạy đủ rồi đọc tại t, ở mọi ô w.
    Đây là phép thử của HÀM; nó không chứng minh nguồn không sửa số cũ."""
    df_a, df_b = hai_chuoi
    ngay = [d.strftime("%Y-%m-%d") for d in df_a["time"]]
    day_du = {w: D.ghep_cap(_lat_phan1(df_a), _lat_phan1(df_b), w, ngay=ngay) for w in LUOI}
    n_lat_cat = 0
    for t in range(N_CHUOI):
        la = _lat_phan1(df_a.iloc[:t + 1].reset_index(drop=True))
        lb = _lat_phan1(df_b.iloc[:t + 1].reset_index(drop=True))
        n_lat_cat += len(la) + len(lb)
        for w in LUOI:
            cat = D.ghep_cap(la, lb, w, ngay=ngay[:t + 1])
            assert D.trang_thai_cap_tai(cat, t) == D.trang_thai_cap_tai(day_du[w], t), (w, t)
    assert n_lat_cat > 0, "phép thử phải THẬT SỰ đi qua lật của phần 1, không phải so hai danh sách rỗng"


# ═════════════════════════════ 7. TRẠNG THÁI: BỐN GIÁ TRỊ, ĐỌC `k_ket > t` ═════════════════════════
def test_trang_thai_doc_k_ket_lon_hon_t_nhu_dang_cho():
    """Một đoạn đã đóng ở hàng k_ket NHƯNG t < k_ket vẫn đọc dang_cho (tại t chưa ai biết nó đóng); từ k_ket thì mới
    đọc kết quả. Biên đúng ở t = k_ket - 1 và t = k_ket."""
    doan, _ = _ghep((("A", G, 1), ("B", G, 4)), 5, n=8)
    assert [_tt(doan, t)[0] for t in range(8)] == [
        "chua_du", "dang_cho", "dang_cho", "dang_cho", "xac_nhan", "xac_nhan", "xac_nhan", "xac_nhan"]


def test_trang_thai_chua_du_truoc_lat_dau_tien_va_sau_do_khong_bao_gio_quay_lai():
    doan, _ = _ghep((("A", G, 3),), None, n=10)
    gia_tri = [_tt(doan, t)[0] for t in range(10)]
    assert gia_tri[:3] == ["chua_du"] * 3 and set(gia_tri[3:]) == {"dang_cho"}


def test_trang_thai_khong_giu_hai_dang_cho_cung_luc():
    """Mỗi hàng có đúng một trạng thái; qua 60 hạt ngẫu nhiên trạng thái luôn là một trong bốn giá trị."""
    for hat in range(30):
        rng = random.Random(3000 + hat)
        n = rng.randint(12, 50)
        a, b = _lat_ngau(rng, n, rng.randint(0, 8)), _lat_ngau(rng, n, rng.randint(0, 8))
        for w in LUOI:
            doan = D.ghep_cap(a, b, w, ngay=_ngay(n))
            for t in range(n):
                assert D.trang_thai_cap_tai(doan, t).gia_tri in ("xac_nhan", "khong_xac_nhan", "dang_cho", "chua_du")


# ═════════════════════════════ 8. HIỂN THỊ BỐN TRẠNG THÁI ═════════════════════════════════════
def _hien(dac_ta, w, t, n=16):
    doan, ngay = _ghep(dac_ta, w, n=n)
    return D.hien_thi(D.trang_thai_cap_tai(doan, t), "VN30", "VNMidcap"), ngay


def _vn(d):
    return f"{d[8:10]}/{d[5:7]}/{d[:4]}"


def test_hien_thi_xac_nhan_giam_noi_theo_sau_bao_nhieu_phien():
    h, ngay = _hien(BANG_35, 3, 4)
    assert h.tieu_de == "Đã xác nhận · giảm"
    assert "cùng đảo chiều swing xuống" in h.mo_ta
    assert "VNMidcap theo sau VN30 2 phiên" in h.mo_ta and _vn(ngay[3]) in h.mo_ta


def test_hien_thi_xac_nhan_lead_la_chuoi_B_va_cung_ngay():
    h, _ = _hien(BANG_35, 3, 14)
    assert h.tieu_de == "Đã xác nhận · giảm" and "VN30 theo sau VNMidcap 1 phiên" in h.mo_ta
    h0, ngay = _hien((("A", T, 3), ("B", T, 3)), 3, 3, n=8)
    assert h0.tieu_de == "Đã xác nhận · tăng" and "cùng một phiên" in h0.mo_ta and "theo sau" not in h0.mo_ta


def test_hien_thi_dang_cho_con_bao_nhieu_phien():
    h, ngay = _hien(BANG_35, 3, 7)
    assert h.tieu_de == "Đang chờ · tăng"
    assert "VN30 đảo chiều swing lên từ " + _vn(ngay[6]) in h.mo_ta and "chờ VNMidcap" in h.mo_ta
    assert "còn 2 phiên" in h.mo_ta
    hn, _ = _hien(BANG_35, None, 7)
    assert "không giới hạn" in hn.mo_ta and "còn" not in hn.mo_ta


def test_hien_thi_khong_xac_nhan_het_han():
    h, ngay = _hien(BANG_35, 3, 10)
    assert h.tieu_de == "Không xác nhận · tăng"
    assert "VN30 đảo chiều swing lên từ " + _vn(ngay[6]) in h.mo_ta and "VNMidcap không theo trong 3 phiên" in h.mo_ta


def test_khong_xac_nhan_chi_con_hai_dang_nhin_thay_duoc_het_han_va_trai_chieu():
    """Phát hiện khi viết hiển thị: một đoạn đóng vì lead_dao_chieu hay ben_kia_nguoc LUÔN được kèm một đoạn mới ở cùng
    hàng (lật đóng đoạn đi tiếp sang bước 5), nên trạng thái đọc được chỉ có thể là het_han (có chiều) hoặc trái chiều
    (chiều None). `hien_thi` từ chối hai lý do kia thay vì bịa một câu cho chúng."""
    thay = set()
    for hat in range(80):
        rng = random.Random(5000 + hat)
        n = rng.randint(12, 50)
        a, b = _lat_ngau(rng, n, rng.randint(0, 8)), _lat_ngau(rng, n, rng.randint(0, 8))
        for w in LUOI:
            doan = D.ghep_cap(a, b, w, ngay=_ngay(n))
            for t in range(n):
                s = D.trang_thai_cap_tai(doan, t)
                if s.gia_tri == "khong_xac_nhan":
                    thay.add((s.ly_do, s.chieu is None))
    assert thay == {("het_han", False), ("ben_kia_nguoc", True)}, thay
    gia = D.TrangThaiCap(gia_tri="khong_xac_nhan", chieu=G, k_biet=4, ngay_biet="2024-01-05", lead="a", tre=None,
                         ly_do="lead_dao_chieu", w=3, con_lai=None, k_mo=1, ngay_mo="2024-01-02")
    with pytest.raises(ValueError):
        D.hien_thi(gia, "VN30", "VNMidcap")


def test_hien_thi_trai_chieu():
    h, ngay = _hien((("A", T, 5), ("B", G, 5)), 3, 5, n=9)
    assert h.tieu_de == "Không xác nhận · trái chiều"
    assert "ngược nhau" in h.mo_ta and _vn(ngay[5]) in h.mo_ta


def test_hien_thi_chua_du():
    h, _ = _hien((("A", T, 5),), 3, 2, n=9)
    assert h.tieu_de == "Chưa đủ bằng chứng" and h.mo_ta


def test_hien_thi_doi_ten_chuoi():
    doan, _ = _ghep(BANG_35, 3)
    h = D.hien_thi(D.trang_thai_cap_tai(doan, 4), "VN30", "VN100")
    assert "VN100 theo sau VN30" in h.mo_ta


def test_hien_thi_khong_co_chu_cam_o_bat_ky_trang_thai_nao():
    """Cùng gác của `tests/test_dow_hai_chi_so_buc_tuong.py` nhưng trên CHUỖI THẬT SỰ SINH RA lúc chạy."""
    cam = ("dự báo", "tín hiệu mua", "tín hiệu bán", "khuyến nghị", "đáng mua", "xác nhận xu hướng chính")
    thay = set()
    for hat in range(40):
        rng = random.Random(4000 + hat)
        n = rng.randint(12, 50)
        a, b = _lat_ngau(rng, n, rng.randint(0, 8)), _lat_ngau(rng, n, rng.randint(0, 8))
        for w in LUOI:
            doan = D.ghep_cap(a, b, w, ngay=_ngay(n))
            for t in range(n):
                s = D.trang_thai_cap_tai(doan, t)
                h = D.hien_thi(s, "VN30", "VNMidcap")
                thay.add(s.gia_tri)
                van = (h.tieu_de + " " + h.mo_ta).lower()
                assert not any(c in van for c in cam), van
                assert " sẽ " not in f" {van} "
    assert thay == {"xac_nhan", "khong_xac_nhan", "dang_cho", "chua_du"}, "quần thể phải phủ đủ bốn trạng thái"
