"""Gác cho DỤNG CỤ ĐO của ĐO 14 — không phải cho dữ liệu nó kéo về.

VÌ SAO MỘT MÁY ĐO CẦN GÁC
─────────────────────────
`SKILL.md` Bước 3 điều 4: *"MÁY ĐO cũng phải bị nghi ngờ như GÁC — và nó
nguy hiểm hơn, vì một gác sai thì ĐỎ, còn một máy đo sai thì chỉ in ra một
con số."* Ngày 14–15/09/2026 **năm** máy đo liên tiếp hẹp hơn thứ chúng đo,
và cả năm đều cho một con số nghe hợp lý (lỗi 61).

Phép kiểm ở đây không chạm mạng. Nó nhắm vào **hàm phán quyết** — chỗ bảng
tiêu chí đã ký được dịch thành một con số, và cũng là chỗ bản đầu của dụng
cụ này đã sai thật.
"""
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))

import do14_kha_thi_khoi_ngoai as d  # noqa: E402


def _o_a(som: str, doi_chung: str = "2018-09-13") -> dict:
    return {"doc_duoc": True, "som": som, "doi_chung_som": doi_chung}


def _o_b(co: int) -> dict:
    return {"co": co, "tong": 71}


# ── Ô ĐỐI CHỨNG: vế khiến một kết quả ÂM đọc được ─────────────────────

def test_DOI_CHUNG_khong_doc_duoc_thi_CHUA_KIEM_DUOC():
    ma, cau = d.phan_dinh(_o_a("2020-01-02", doi_chung=""), _o_b(70))
    assert ma == 2, cau
    assert "CHUA KIEM DUOC" in cau


def test_CA_HAI_deu_NGAN_thi_CHUA_KIEM_DUOC_chu_KHONG_phai_ket_cuc_3():
    """Đây là lỗi 66, và bản đầu của `phan_dinh` mắc đúng nó.

    `foreign_flow` ngắn VÀ `ohlcv` cũng ngắn thì hai nguyên nhân ngược
    nhau — *nguồn chỉ có từng ấy* và *tham số ngày của tôi bị bỏ qua* —
    không tách được. Trả 1 ở đây là kết tội NGUỒN bằng một phép đo nói
    về DỤNG CỤ.
    """
    ma, cau = d.phan_dinh(_o_a("2025-01-02", doi_chung="2025-01-02"), _o_b(70))
    assert ma == 2, f"phai la CHUA KIEM DUOC, nhan duoc {ma}: {cau}"
    assert "doi chung" in cau.lower()


def test_DOI_CHUNG_DAI_ma_chuoi_NGAN_thi_moi_duoc_ket_toi_NGUON():
    """Đối chứng dương đạt → chuỗi ngắn nói về NGUỒN. Đây là ca ĐỌC ĐƯỢC."""
    ma, cau = d.phan_dinh(_o_a("2025-01-02", doi_chung="2018-09-13"), _o_b(70))
    assert ma == 1, cau
    assert "KET CUC 3" in cau


# ── Ô A và Ô B: ngưỡng đã ký, đọc đúng chứ không nới ──────────────────

@pytest.mark.parametrize("som,cho_doi", [
    ("2018-09-13", True),   # dat manh
    ("2021-09-30", True),   # truoc moc mot ngay
    ("2021-10-01", True),   # DUNG moc — bien phai la DAT
    ("2021-10-02", False),  # sau moc mot ngay
])
def test_O_A_cat_DUNG_tai_moc_da_ky(som, cho_doi):
    ma, cau = d.phan_dinh(_o_a(som), _o_b(70))
    assert (ma == 0) is cho_doi, f"{som} -> ma {ma}: {cau}"


@pytest.mark.parametrize("co,ma_mong,dau", [
    (71, 0, "KET CUC 1"),
    (60, 0, "KET CUC 1"),   # DUNG nguong — bien phai la DAT
    (59, 1, "KET CUC 2"),
    (35, 1, "KET CUC 2"),
])
def test_O_B_cat_DUNG_tai_nguong_da_ky(co, ma_mong, dau):
    ma, cau = d.phan_dinh(_o_a("2019-01-02"), _o_b(co))
    assert ma == ma_mong, f"co={co} -> ma {ma}: {cau}"
    assert cau.startswith(dau), cau


def test_DUOI_NUA_RO_phai_duoc_GOI_TEN_trong_ban_in():
    """Một con số dưới nửa rổ là hạng khác, nên bản in phải nói ra."""
    _, cau = d.phan_dinh(_o_a("2019-01-02"), _o_b(35))
    assert "duoi nua ro" in cau, cau
    _, cau_60 = d.phan_dinh(_o_a("2019-01-02"), _o_b(50))
    assert "duoi nua ro" not in cau_60, cau_60


def test_NGUONG_trong_MA_phai_KHOP_bang_da_ky_trong_TAI_LIEU():
    """Ngưỡng ký trước mà mã lại cầm một con số khác thì bảng ấy vô nghĩa."""
    van = (GOC / "docs" / "TIEU-CHI-DOC-TRUOC.md").read_text(encoding="utf-8")
    dau = van.find("## ĐO 14")
    assert dau > 0, "khong tim thay muc DO 14 trong tai lieu tieu chi"
    muc = van[dau:]
    assert d.MOC_PHU_CACHE_MAC_DINH in muc, d.MOC_PHU_CACHE_MAC_DINH
    assert d.MOC_PHU_CACHE_RONG in muc, d.MOC_PHU_CACHE_RONG
    assert f"{d.NGUONG_PHU_DAT}/71" in muc, f"{d.NGUONG_PHU_DAT}/71"
    assert f"{d.NGUONG_PHU_HONG}/71" in muc, f"{d.NGUONG_PHU_HONG}/71"


# ── `_so_dong`: chỗ cửa `chan_bia_so_lieu` đã chặn bản đầu ────────────

def test_KHONG_DEM_DUOC_phai_la_None_chu_khong_phai_0():
    """0 và 'không đếm được' là hai kết luận NGƯỢC nhau về cùng một mã."""
    assert d._so_dong(None) is None
    assert d._so_dong(object()) is None, "thu khong co len() phai ra None"
    assert d._so_dong([]) == 0
    assert d._so_dong([1, 2, 3]) == 3


# ── `goi_thu`: phải KHAI mọi đường đã thử, không im lặng ──────────────

def test_GOI_THU_lay_hinh_dang_DAU_TIEN_cho_bang_KHONG_RONG():
    def ham(**kw):
        if "start" in kw:
            return []          # doc duoc, nhung RONG -> phai di tiep
        if "start_date" in kw:
            return [1, 2]
        raise TypeError("khong nhan tham so nay")

    ten, kq, nhat_ky = d.goi_thu(ham, "2015-01-01", "2026-09-22")
    assert ten == "start_date/end_date", ten
    assert kq == [1, 2]
    assert len(nhat_ky) == 2, nhat_ky


def test_GOI_THU_khong_im_LANG_khi_moi_duong_deu_hong():
    """Một câu 'không gọi được' mà không nêu ĐƯỜNG đã thử sẽ sai ngay khi
    có đường thứ hai — lỗi 16. Nên nhật ký phải giữ đủ MỌI hình dạng."""
    def ham(*a, **kw):
        raise ValueError("nguon tu choi")

    ten, kq, nhat_ky = d.goi_thu(ham, "2015-01-01", "2026-09-22")
    assert ten == "" and kq is None
    assert len(nhat_ky) == len(d.HINH_DANG), nhat_ky
    assert all("ValueError" in d_ for d_ in nhat_ky), nhat_ky


def test_COT_NGAY_suy_tu_BANG_chu_khong_ghim_mot_ten():
    import pandas as pd
    assert d._cot_ngay(pd.DataFrame(columns=["time", "net"])) == "time"
    assert d._cot_ngay(pd.DataFrame(columns=["TradingDate", "x"])) == "TradingDate"
    assert d._cot_ngay(pd.DataFrame(columns=["a", "b"])) is None

# ── `so_khop_lich`: hàm thuần, và phép CẮT VỀ PHẦN GIAO là cả ý nghĩa ──

def test_HAI_CHUOI_GIONG_HET_thi_khong_ben_nao_thieu():
    n = ["2024-01-02", "2024-01-03", "2024-01-04"]
    assert d.so_khop_lich(n, n) == (3, 0, 0)


def test_PHAN_THUA_O_DAU_khong_phai_la_THIEU():
    """Đây là cả lý do hàm cắt về phần giao.

    Chuỗi khối ngoại lùi tới 2015, chuỗi giá tới 2016. 2015 không phải
    "giá bị thiếu" — nó nằm NGOÀI câu hỏi *hai chuỗi có khớp lịch không*.
    Không cắt thì mọi phiên 2015 đếm thành lỗ hổng, và con số đó vu oan
    cho chuỗi dài hơn.
    """
    kn = ["2015-01-05", "2016-09-21", "2016-09-22"]
    gia = ["2016-09-21", "2016-09-22"]
    chung, chi_kn, chi_gia = d.so_khop_lich(kn, gia)
    assert (chung, chi_kn, chi_gia) == (2, 0, 0), (chung, chi_kn, chi_gia)


def test_MOT_PHIEN_THIEU_O_GIUA_thi_PHAI_dem_duoc():
    """Cắt về phần giao KHÔNG được che một lỗ hổng thật ở giữa."""
    gia = ["2024-01-02", "2024-01-03", "2024-01-04"]
    kn = ["2024-01-02", "2024-01-04"]
    assert d.so_khop_lich(kn, gia) == (2, 0, 1)


def test_MOT_BEN_RONG_thi_khong_duoc_bao_KHOP():
    assert d.so_khop_lich([], ["2024-01-02"]) == (0, 0, 1)
    assert d.so_khop_lich(["2024-01-02"], []) == (0, 1, 0)


def test_NHAN_ca_ngay_dang_DOI_TUONG_chu_khong_chi_chuoi():
    import datetime as dt
    a = [dt.date(2024, 1, 2), dt.date(2024, 1, 3)]
    b = ["2024-01-02", "2024-01-03"]
    assert d.so_khop_lich(a, b) == (2, 0, 0)
