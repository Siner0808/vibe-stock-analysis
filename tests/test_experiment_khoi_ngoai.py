"""Gác cho dụng cụ đo của ĐO 15 — không phải cho kết quả nó cho ra.

`SKILL.md` Bước 3 điều 4: *"MÁY ĐO cũng phải bị nghi ngờ như GÁC — và nó
nguy hiểm hơn, vì một gác sai thì ĐỎ, còn một máy đo sai thì chỉ in ra một
con số."* Ngày 14–15/09/2026 năm máy đo liên tiếp hẹp hơn thứ chúng đo, và
cả năm đều cho một con số nghe hợp lý (lỗi 61).

Không phép kiểm nào ở đây chạm mạng hay chạm cache.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import experiment_khoi_ngoai as K  # noqa: E402


def _gia(n: int = 300, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    ngay = pd.bdate_range("2022-01-03", periods=n).strftime("%Y-%m-%d")
    c = 20_000 + np.cumsum(rng.normal(0, 200, n))
    return pd.DataFrame({"close": c, "volume": rng.uniform(1e5, 1e6, n)},
                        index=ngay)


def _kn(gia: pd.DataFrame, seed: int = 1) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n = len(gia)
    bv = rng.uniform(1e9, 1e10, n)
    sv = rng.uniform(1e9, 1e10, n)
    return pd.DataFrame({"buy_vol": rng.uniform(1e4, 1e5, n),
                         "buy_val": bv,
                         "sell_vol": rng.uniform(1e4, 1e5, n),
                         "sell_val": sv,
                         "net_vol": rng.normal(0, 5e4, n),
                         "net_val": bv - sv}, index=gia.index)


# ── BẤT BIẾN 1: không nhìn trộm ───────────────────────────────────────

def test_KHONG_NHIN_TROM_them_phien_TUONG_LAI_khong_doi_gia_tri_cu():
    """Đây là phép kiểm đắt nhất của file này.

    Mọi đặc trưng ở hàng t chỉ được dùng dữ liệu tới hết hàng t. Cách rẻ
    nhất để chứng minh: nối thêm phiên vào CUỐI rồi đòi mọi hàng cũ giống
    hệt. Một `rolling(...).mean()` viết ngược hay một `shift(-1)` lọt vào
    sẽ đỏ ngay.
    """
    g = _gia(320)
    k = _kn(g)
    a = K.dac_trung_kn(g, k)

    g2 = pd.concat([g, _gia(40, seed=9).set_index(
        pd.bdate_range("2023-06-01", periods=40).strftime("%Y-%m-%d"))])
    k2 = pd.concat([k, _kn(g2.iloc[len(g):], seed=9)])
    b = K.dac_trung_kn(g2, k2)

    cu = b.loc[a.index]
    pd.testing.assert_frame_equal(a, cu, check_exact=False, rtol=1e-12)


# ── Phiên thiếu khối ngoại: NaN, KHÔNG phải 0 ─────────────────────────

def test_PHIEN_THIEU_KHOI_NGOAI_thanh_NaN_chu_KHONG_thanh_0():
    """`0` là một giá trị CÓ NGHĨA THẬT trong chuỗi này.

    ĐO 14 đếm được 16–36% số phiên các năm đầu có `net_val == 0`. Điền 0
    cho phiên thiếu dữ liệu là trộn *"khối ngoại không giao dịch"* với
    *"ta không biết"* — hai thứ khác hẳn nhau.
    """
    g = _gia(300)
    k = _kn(g).iloc[:-30]          # 30 phien cuoi khong co khoi ngoai
    a = K.dac_trung_kn(g, k)
    duoi = a.iloc[-25:]
    assert duoi.isna().all().all(), "phien thieu phai la NaN"
    assert not (duoi.fillna(-1) == 0).any().any()


# ── Không thứ nguyên: đổi đơn vị không đổi đặc trưng ──────────────────

def test_TY_TRONG_khong_doi_khi_DOI_DON_VI_khoi_luong():
    g = _gia(300)
    k = _kn(g)
    a = K.dac_trung_kn(g, k)

    g2 = g.assign(volume=g["volume"] * 1000)
    k2 = k.assign(net_vol=k["net_vol"] * 1000)
    b = K.dac_trung_kn(g2, k2)
    for cot in ("kn_ty_trong_5", "kn_ty_trong_20"):
        pd.testing.assert_series_equal(a[cot], b[cot], check_exact=False,
                                       rtol=1e-10)


def test_AP_LUC_nam_trong_dai_TRU_MOT_den_MOT():
    g = _gia(300)
    a = K.dac_trung_kn(g, _kn(g))["kn_ap_luc_5"].dropna()
    assert len(a) > 100
    assert a.between(-1, 1).all(), (a.min(), a.max())


def test_NAM_DAC_TRUNG_DUNG_TEN_va_dung_so():
    g = _gia(300)
    a = K.dac_trung_kn(g, _kn(g))
    assert tuple(a.columns) == K.TEN_DAC_TRUNG
    assert len(K.TEN_DAC_TRUNG) == 5
    assert K.O_DOI_CHUNG in K.TEN_DAC_TRUNG


def test_KHONG_DAC_TRUNG_NAO_DEM_THEO_THOI_GIAN():
    """Tiêu chí ĐO 15 khai trước: không có đặc trưng đếm phiên.

    Lý do đo được ở BƯỚC 112: tỷ lệ phiên `net_val == 0` đi từ 16,5%
    (2015) xuống đúng 0,0% (2025–26), nên một đặc trưng đếm sẽ trôi theo
    CẤU TẠO DỮ LIỆU chứ không theo thị trường.
    """
    xau = [t for t in K.TEN_DAC_TRUNG
           if any(x in t for x in ("phien_ke", "so_ngay", "streak", "dem"))]
    assert not xau, xau


# ── Bonferroni suy ra, không gõ tay ───────────────────────────────────

def test_BONFERRONI_SUY_TU_SO_DAC_TRUNG_chu_khong_go_tay():
    assert K.ALPHA_BONFERRONI == pytest.approx(0.05 / len(K.TEN_DAC_TRUNG))


def test_HAI_NHIP_deu_nam_trong_danh_sach_DA_DOI_CHIEU():
    """Ngoài danh sách ấy thì sàn nhiễu chưa ai kiểm — BƯỚC 9."""
    import experiment_tran_dac_trung as E
    ngoai = [h for h in K.HORIZONS if h not in E.NHIP_DA_DOI_CHIEU]
    assert not ngoai, f"nhip chua doi chieu: {ngoai}"


# ── Hàm phán quyết: bốn kết cục đã ký ─────────────────────────────────

def _ket(vuot_san: bool, vuot_rao: bool = False) -> dict:
    return {t: {"vuot_san": vuot_san and t == "kn_z_20",
                "vuot_rao": vuot_rao and t == "kn_z_20"}
            for t in K.TEN_DAC_TRUNG}


def test_CHUNG_CU_DUONG_CHUA_CHAY_thi_CHUA_KIEM_DUOC():
    ma, cau = K.phan_dinh(_ket(False), None)
    assert ma == 2 and "CHUA KIEM DUOC" in cau


def test_NULL_ma_CHUNG_CU_DUONG_IM_la_THIEU_LUC_chu_khong_phai_VANG_MAT():
    """Hai thứ này KHÔNG được báo cáo bằng cùng một câu."""
    ma, cau = K.phan_dinh(_ket(False), False)
    assert ma == 2, cau
    assert "KET CUC 4" in cau and "THIEU LUC" in cau


def test_NULL_ma_CHUNG_CU_DUONG_KEU_la_BANG_CHUNG_VANG_MAT():
    ma, cau = K.phan_dinh(_ket(False), True)
    assert ma == 0, cau
    assert "KET CUC 3" in cau and "VANG MAT" in cau


def test_VUOT_SAN_ma_DUOI_RAO_la_ket_cuc_2():
    ma, cau = K.phan_dinh(_ket(True, vuot_rao=False), True)
    assert ma == 1 and "KET CUC 2" in cau


def test_VUOT_CA_HAI_la_ket_cuc_1():
    ma, cau = K.phan_dinh(_ket(True, vuot_rao=True), True)
    assert ma == 1 and "KET CUC 1" in cau


# ── Độ phủ ghép ───────────────────────────────────────────────────────

def test_DO_PHU_GHEP_dem_dung_ma_KHONG_co_file():
    g = _gia(300)
    kh = {"AAA": g, "BBB": g}
    kn = {"AAA": _kn(g)}
    d = K.do_phu_ghep(kh, kn)
    assert d["ma_thieu_han"] == ["BBB"]
    assert d["thieu_kn"] == len(g)
    assert d["co_gia"] == 2 * len(g)


def test_BIEN_THIEN_SAU_GHEP_dem_gia_tri_KHAC_NHAU():
    X = np.column_stack([np.zeros(50), np.arange(50.0),
                         np.tile([1.0, 2.0], 25), np.arange(50.0),
                         np.arange(50.0)])
    d = K.bien_thien_sau_ghep(X)
    assert d["kn_ty_trong_5"] == 1, "cot hang so phai ra 1"
    assert d["kn_ty_trong_20"] == 50
    assert d["kn_ap_luc_5"] == 2

# ── Trị số p: dùng CẢ phân phối null, không chỉ hai thống kê thứ tự ───

def test_TRI_SO_P_khong_bao_gio_tra_0():
    """Một phép đo n hoán vị không thể khẳng định p < 1/(n+1)."""
    null = np.zeros(100)
    assert K.tri_so_p(999.0, null) == pytest.approx(1 / 101)


def test_TRI_SO_P_hai_phia_dem_ca_hai_duoi():
    null = np.array([-0.9, -0.5, 0.0, 0.5, 0.9])
    assert K.tri_so_p(0.6, null) == pytest.approx(3 / 6)
    assert K.tri_so_p(-0.6, null) == pytest.approx(3 / 6)


def test_TRI_SO_P_bang_1_khi_IC_nam_giua_null():
    null = np.linspace(-1, 1, 21)
    assert K.tri_so_p(0.0, null) == pytest.approx(1.0)


def test_IT_HOAN_VI_thi_KHONG_the_vuot_Bonferroni():
    """Gác chính cái đã hỏng ở lượt dò 40 hoán vị.

    Với `n` hoán vị, trị số p nhỏ nhất có thể là `1/(n+1)`. Nên một lượt
    40 hoán vị KHÔNG BAO GIỜ đạt được `p < 0,01` — nó không thể tuyên bố
    vượt sàn, thay vì tuyên bố nhầm như một phân vị 0,5% dựng từ 40 mẫu.
    """
    null = np.zeros(40)
    assert K.tri_so_p(999.0, null) > K.ALPHA_BONFERRONI
    null_du = np.zeros(2000)
    assert K.tri_so_p(999.0, null_du) < K.ALPHA_BONFERRONI

# ── CHỨNG CỨ DƯƠNG IM thì KHÔNG con số nào ở nhịp ấy đọc được ─────────

def test_VUOT_SAN_ma_CHUNG_CU_DUONG_IM_van_la_KET_CUC_4():
    """Đây đúng ca h=21 của lượt chạy 22/09/2026.

    `kn_z_20` ra IC +0,0557, vượt cả sàn nhiễu lẫn rào hoà vốn — nghe như
    kết cục 1. Nhưng chứng cứ dương ở nhịp ấy KHÔNG bắt nổi một tín hiệu
    tiêm ĐÚNG BẰNG RÀO (p = 0,0200 > 0,01), tức máy đo không đủ lực ở đó.
    Một con số từ một phép đo thiếu lực thì không đọc được, kể cả khi nó
    đẹp — nhất là khi nó đẹp.
    """
    ma, cau = K.phan_dinh(_ket(True, vuot_rao=True), False)
    assert ma == 2, cau
    assert "KET CUC 4" in cau and "THIEU LUC" in cau


def test_CAN_TREN_VUOT_SAN_thi_KHONG_con_la_BANG_CHUNG_VANG_MAT():
    """IC từng đặc trưng im mà CẬN TRÊN kêu thì câu hỏi CHƯA đóng.

    Dự án đóng câu hỏi bằng cách gộp tuyến tính tối ưu, không bằng IC đơn
    lẻ — hai khẳng định khác nhau (lượt hỏi sổ tay 22/09/2026).
    """
    ma, cau = K.phan_dinh(_ket(False), True,
                          {"vuot_san": True, "vuot_rao": False})
    assert ma == 1, cau
    assert "KET CUC 2" in cau and "CAN TREN" in cau


def test_CAN_TREN_im_CUNG_voi_moi_dac_trung_thi_moi_la_VANG_MAT():
    ma, cau = K.phan_dinh(_ket(False), True,
                          {"vuot_san": False, "vuot_rao": False})
    assert ma == 0 and "KET CUC 3" in cau

# ── Phán quyết của chứng cứ dương: HAI vế, cả hai bắt buộc ────────────

@pytest.mark.parametrize("khong_co_gi,dung_rao,cho_doi", [
    (False, True, True),    # dung ca hai ve -> doc duoc
    (True, True, False),    # may do TU KEU tren hu khong -> KHONG doc duoc
    (False, False, False),  # thieu luc
    (True, False, False),
])
def test_DOC_DUOC_doi_CA_HAI_ve(khong_co_gi, dung_rao, cho_doi):
    """Bỏ vế "không có gì" là bỏ đúng phép kiểm đã bắt lỗi thật 22/09."""
    assert K.doc_duoc_khong({"khong co gi": khong_co_gi,
                             "dung bang rao": dung_rao}) is cho_doi


def test_DOC_DUOC_thieu_khoa_thi_FAIL_CLOSED():
    """Thiếu thông tin thì KHÔNG được tự xưng là đọc được."""
    assert K.doc_duoc_khong({}) is False
    assert K.doc_duoc_khong({"dung bang rao": True}) is False


def test_NEN_NHIEU_phai_DICH_VONG_nen_o_KHONG_TIEM_GI_moi_im():
    """Gác chính lỗi đã xảy ra ngày 22/09/2026.

    Nền lấy thẳng cột thật thì ô "không tiêm gì" hoá ra là ĐO LẠI CHÍNH
    cột ấy — phép hiệu chuẩn tự kiểm thứ nó đi kiểm. Ở đây dựng một cột
    nền CÓ tương quan mạnh với nhãn; không dịch vòng thì ô ấy kêu và hàm
    phải trả False.
    """
    rng = np.random.default_rng(7)
    n_ma, n = 6, 400
    ys, Xs, chi_so, dau = [], [], {}, 0
    for i in range(n_ma):
        yy = rng.standard_normal(n)
        z = 0.9 * yy + 0.4 * rng.standard_normal(n)   # nen DINH chat voi nhan
        cot = np.column_stack([rng.standard_normal(n) for _ in range(4)])
        Xs.append(np.column_stack([cot[:, 0], cot[:, 1], cot[:, 2], z,
                                   cot[:, 3]]))
        ys.append(yy)
        chi_so[f"M{i}"] = np.arange(dau, dau + n)
        dau += n
    X, y = np.vstack(Xs), np.concatenate(ys)
    ra = K.chung_cu_duong_kn(X, y, chi_so, h=5, rng=rng, so_vong=200)
    assert ra is True, ("nen da dich vong ma o 'khong tiem gi' van keu — "
                        "phep hieu chuan dang tu kiem chinh no")
