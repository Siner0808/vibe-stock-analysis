"""Gác cho dụng cụ đo của ĐO 16 — không phải cho kết quả nó cho ra.

ĐO 16 là một phép LẶP LẠI NGOÀI MẪU. Bốn cách hỏng im lặng, mỗi cách một gác:

    doc nham thu muc gia   "tap kiem" hoa ra la cua so DO 15 -> mot lan do
                           lai thu da nhin, in ra nhu mot phep lap lai
    tach tap theo MOC      phien da nhin lot vao tap kiem, hoac phien chua
                           nhin bi bo -- vi bang DO 15 bat dau o moi ma
                           mot ngay khac
    phan quyet luc         MOT luot rut la mot dong xu 70/30 o h=21 (loi 99)
    nguoc dau              mot IC AM co y nghia duoc doc thanh 'lap lai'
                           -- phep kiem hai phia bat duoc ca hai chieu

Không phép kiểm nào ở đây chạm mạng hay chạm cache thật.
"""
import inspect
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import experiment_tran_dac_trung as E  # noqa: E402
import experiment_khoi_ngoai as K  # noqa: E402
import experiment_khoi_ngoai_nhip_dai as N  # noqa: E402


def _bang_gia(ngay, seed):
    rng = np.random.default_rng(seed)
    n = len(ngay)
    c = 20_000 * np.exp(np.cumsum(rng.normal(0, 0.02, n)))
    return pd.DataFrame({"close": c, "volume": rng.uniform(1e5, 1e6, n)},
                        index=list(ngay))


def _bang_kn(gia, seed):
    rng = np.random.default_rng(seed)
    n = len(gia)
    bv = rng.uniform(1e9, 1e10, n)
    sv = rng.uniform(1e9, 1e10, n)
    return pd.DataFrame({"buy_val": bv, "sell_val": sv,
                         "net_vol": rng.normal(0, 5e4, n),
                         "net_val": bv - sv}, index=gia.index)


def _ro(so_ma=3, n=520):
    ngay = pd.bdate_range("2020-01-02", periods=n).strftime("%Y-%m-%d")
    kh = {f"M{i}": _bang_gia(ngay, 10 + i) for i in range(so_ma)}
    kn = {m: _bang_kn(g, 50 + i) for i, (m, g) in enumerate(kh.items())}
    return kh, kn, list(ngay)


# ── ĐỌC ĐÚNG THƯ MỤC ──────────────────────────────────────────────────


def test_NAP_GIA_MAC_DINH_van_la_CACHE_cua_DO_15():
    """Thêm tham số KHÔNG được đổi phép đo cũ. ĐO 15 gọi `nap_gia()` trần."""
    mac_dinh = inspect.signature(E.nap_gia).parameters["thu_muc"].default
    assert mac_dinh == E.CACHE, mac_dinh


def test_NAP_GIA_doc_DUNG_thu_muc_duoc_chi(tmp_path):
    """Tham số phải được DÙNG, không chỉ được nhận.

    Hình dạng hỏng đáng sợ nhất: nhận `cache_2018` rồi vẫn đọc `cache`.
    Khi ấy tập kiểm rỗng — hoặc tệ hơn, là chính cửa sổ đã nhìn.
    """
    import json
    ma = next(iter(json.loads(E.FILE_MOC.read_text(encoding="utf-8"))
                   ["moc_theo_ma"]))
    n = E.MIN_HIST + 100
    ngay = pd.bdate_range("2018-09-13", periods=n).strftime("%Y-%m-%d")
    pd.DataFrame({"time": ngay, "open": 1.0, "high": 1.0, "low": 1.0,
                  "close": 1.0, "volume": 1.0}).to_csv(
        tmp_path / f"{ma}.csv", index=False)
    kh = E.nap_gia(tmp_path)
    assert list(kh) == [ma], list(kh)
    assert len(kh[ma]) == n and kh[ma].index[0] == "2018-09-13"


def test_DO16_doc_CACHE_2018_chu_khong_phai_cua_so_DO_15():
    assert N.CACHE_GIA.name == "cache_2018"
    assert N.CACHE_GIA != E.CACHE


def test_NHIP_21_DU_BAO_kn_z_20_DAU_DUONG():
    """Cả ba khai TRƯỚC, từ ĐO 15 — không cái nào được chọn trên tập kiểm."""
    assert N.NHIP == 21 and N.NHIP in E.NHIP_DA_DOI_CHIEU
    assert N.DU_BAO == "kn_z_20" and N.DU_BAO in K.TEN_DAC_TRUNG
    assert N.DAU == +1


def test_MOC_DO15_chep_DUNG_tu_TIEU_CHI_DO_15():
    """Một mốc gõ tay ở hai chỗ sẽ trôi khỏi nhau — đọc nó từ tiêu chí."""
    tc = (GOC / "docs" / "TIEU-CHI-DOC-TRUOC.md").read_text(encoding="utf-8")
    muc = tc.split("## ĐO 15 —", 1)[1].split("\n## ĐO ", 1)[0]
    m = re.search(r"Cửa sổ dùng được là \*\*(\d{4}-\d{2}-\d{2})", muc)
    assert m, "khong tim thay cau khai cua so trong tieu chi DO 15"
    assert N.MOC_DO15 == m.group(1), (N.MOC_DO15, m.group(1))


def test_BA_CON_SO_TAI_LAP_nam_that_trong_BUOC_113():
    """Tiền kiểm chỉ có nghĩa nếu nó so với con số ĐÃ GHI, không gõ lại."""
    st = (GOC / "docs" / "STATE.md").read_text(encoding="utf-8")
    muc = st.split("## BƯỚC 113 —", 1)[1].split("\n## BƯỚC ", 1)[0]
    for ten, v in N.DO15_H21.items():
        chu = f"{v:.4f}".replace(".", ",")
        assert chu in muc, (ten, chu)


# ── TÁCH TẬP THEO KHOÁ ────────────────────────────────────────────────


def test_BANG_KN_KHOA_cho_DUNG_bang_cua_BANG_KN():
    """Một vòng lặp, hai lối ra. Khoá phải đi kèm ĐÚNG dòng của nó."""
    kh, kn, _ = _ro()
    X, y, cs = K._bang_kn(kh, kn, 5)
    X2, y2, cs2, khoa = K._bang_kn_khoa(kh, kn, 5)
    assert np.array_equal(X, X2) and np.array_equal(y, y2)
    assert cs.keys() == cs2.keys() and len(khoa) == len(y)
    nhan = E.nhan_vuot_ro(kh, 5)
    for i in (0, len(khoa) // 2, len(khoa) - 1):
        ma, ngay = khoa[i]
        assert y[i] == pytest.approx(nhan.loc[ngay, ma]), (i, ma, ngay)


def test_TACH_CHUA_NHIN_theo_KHOA_chu_khong_theo_NGAY():
    """Cùng một ngày có thể đã nhìn ở mã này và chưa nhìn ở mã kia."""
    da = [("A", "2022-01-03"), ("A", "2022-01-04")]
    khoa = [("A", "2022-01-03"), ("B", "2022-01-03"), ("A", "2022-01-05")]
    assert N.tach_chua_nhin(da, khoa).tolist() == [False, True, True]


def test_TAP_KIEM_la_bang_GOP_tru_bang_DO15_va_BO_ma_QUA_NGAN():
    """Bảng 'ĐO 15' là bảng gộp cắt đầu — ở mỗi mã một độ dài khác, đúng như
    `cache/` thật. Tập kiểm phải là ĐÚNG phần bị cắt, và một mã chỉ mới
    thêm vài phiên thì bị bỏ khỏi tập kiểm thay vì để nguyên không dịch."""
    kh, kn, ngay = _ro(so_ma=3, n=700)
    cat = {"M0": 150, "M1": 100, "M2": 20}          # M2 chi moi them 20 phien
    kh15 = {m: g.iloc[cat[m]:] for m, g in kh.items()}
    kn15 = kn
    t = N.tap_kiem(kh, kh15, kn15, 5)
    _, _, _, kg = K._bang_kn_khoa(kh, kn, 5)
    _, _, _, k15 = K._bang_kn_khoa(kh15, kn15, 5)
    moi = set(kg) - set(k15)
    assert t["n_chua_nhin"] == len(moi)
    assert t["ma_bo"] == ["M2"], t["ma_bo"]
    ky_vong = sum(1 for k in moi if k[0] != "M2")
    assert t["n_kiem"] == ky_vong == len(t["y"]), (t["n_kiem"], ky_vong)
    assert set(t["chi_so"]) == {"M0", "M1"}


# ── p MỘT PHÍA ────────────────────────────────────────────────────────


def test_P_MOT_PHIA_khong_THUONG_cho_ket_qua_NGUOC_DAU():
    null = np.linspace(-0.05, 0.05, 999)
    assert N.tri_so_p_mot_phia(+0.06, null) == pytest.approx(1 / 1000)
    assert N.tri_so_p_mot_phia(-0.06, null) == pytest.approx(1.0)
    # hai phia cua DO 15 thi coi -0,06 la VUOT -- mot phia thi khong
    assert K.tri_so_p(-0.06, null) == pytest.approx(1 / 1000)


def test_P_MOT_PHIA_dem_CA_diem_BANG():
    null = np.array([0.01, 0.02, 0.03])
    assert N.tri_so_p_mot_phia(0.02, null) == pytest.approx(3 / 4)


# ── PHÁN QUYẾT LỰC: nhiều lượt, không phải một đồng xu ───────────────


@pytest.mark.parametrize("r,alpha,mong", [(50, .05, 5), (30, .01, 1),
                                          (50, .01, 2), (20, .05, 3)])
def test_NGUONG_IM_khop_DAP_AN_NHI_THUC_doc_lap(r, alpha, mong):
    """Đáp án tính bằng `scipy.stats.binom.sf` ngày 24/09/2026 — một đường
    khác với vòng cộng dồn trong hàm, nên test không tự dựng lại công thức
    của chính thứ nó kiểm (CLAUDE.md, mục "Test KIỂM LẠI CHÍNH NÓ")."""
    assert N.nguong_im(r, alpha) == mong


@pytest.mark.parametrize("k0,k1,mong", [
    (0, 40, True),     # dung 80% -> dat
    (0, 39, False),    # 78% -> thieu luc
    (5, 50, True),     # im o dung nguong nhi thuc
    (6, 50, False),    # tu keu tren hu khong
])
def test_DOC_DUOC_doi_CA_HAI_ve(k0, k1, mong):
    luc = {"R": 50, "alpha": 0.05, "khong co gi": k0, "dung bang rao": k1}
    assert N.doc_duoc_nhieu_luot(luc) is mong


def test_MOT_LUOT_RUT_KHONG_BAO_GIO_DU_de_DOC_DUOC():
    """Dựng lại NGUYÊN VĂN lỗi 99. Chứng cứ dương của ĐO 15 phán trên MỘT
    lượt tiêm; lặp lại 30 lần trên cùng dữ liệu thì h=21 bắt 21/30. Một
    lượt may mắn — 1/1 — không được là phán quyết."""
    for r in (1, 2, N.R_TOI_THIEU - 1):
        luc = {"R": r, "alpha": 0.05, "khong co gi": 0, "dung bang rao": r}
        assert N.doc_duoc_nhieu_luot(luc) is False, r
    assert N.R_TIEM >= N.R_TOI_THIEU


@pytest.mark.parametrize("luc", [
    None, {}, {"R": 50, "khong co gi": 0, "dung bang rao": 50},
    {"R": 0, "alpha": .05, "khong co gi": 0, "dung bang rao": 0},
])
def test_DOC_DUOC_thieu_khoa_thi_FAIL_CLOSED(luc):
    assert N.doc_duoc_nhieu_luot(luc) is False


def test_TIEM_KHONG_CO_GI_phai_ROI_NHAN():
    """Bản 2 của ĐO 15 lấy nền từ chính cột thật, KHÔNG dịch — ô 'không
    tiêm gì' khi ấy đo lại chính đặc trưng. Dựng ca rò TUYỆT ĐỐI: cột
    `kn_z_20` BẰNG nhãn. Nền đã dịch vòng thì IC phải về gần 0."""
    rng = np.random.default_rng(3)
    so_ma, n, h = 4, 400, 5
    y = rng.normal(0, 3, so_ma * n)
    X = rng.normal(0, 1, (so_ma * n, len(K.TEN_DAC_TRUNG)))
    X[:, K.TEN_DAC_TRUNG.index("kn_z_20")] = y
    chi_so = {f"M{i}": np.arange(i * n, (i + 1) * n) for i in range(so_ma)}
    assert E.rho_hang(X[:, K.TEN_DAC_TRUNG.index("kn_z_20")], y) > 0.99
    ra = N.mot_luot_tiem(X, y, chi_so, h, rng, he_so=0.0, so_vong=20)
    assert abs(ra["ic"]) < 0.2, ra


def test_TIEM_NGUOC_DAU_hai_phia_BAT_mot_phia_BO_QUA():
    """Luật của ĐO 16 là hai phía; `mot_phia` chỉ để tái lập một con số —
    nhưng nó phải đổi THẬT phép kiểm. Một tín hiệu âm mạnh: hai phía bắt,
    một phía (+) thì không được thưởng cho nó."""
    rng = np.random.default_rng(7)
    so_ma, n, h = 4, 400, 5
    y = rng.normal(0, 3, so_ma * n)
    X = rng.normal(0, 1, (so_ma * n, len(K.TEN_DAC_TRUNG)))
    chi_so = {f"M{i}": np.arange(i * n, (i + 1) * n) for i in range(so_ma)}
    hai = N.mot_luot_tiem(X, y, chi_so, h, np.random.default_rng(1),
                          he_so=-5.0, so_vong=40)
    mot = N.mot_luot_tiem(X, y, chi_so, h, np.random.default_rng(1),
                          he_so=-5.0, so_vong=40, mot_phia=True)
    assert hai["ic"] < -0.3 and hai["ic"] == mot["ic"], (hai, mot)
    assert hai["bat"] and not mot["bat"], (hai, mot)


# ── BẢNG KẾT CỤC ──────────────────────────────────────────────────────


def _kq(ic, p, sd=0.005):
    return {"ic": ic, "p": p, "null_sd": sd}


def test_KHONG_DOC_DUOC_thi_KET_CUC_4_du_so_dep():
    m, cau = N.phan_dinh_lap_lai(_kq(0.09, 0.001), 0.05, False)
    assert m == 2 and "KET CUC 4" in cau


@pytest.mark.parametrize("kq,rao,dd", [
    (None, 0.05, True), (_kq(.02, .5), None, True), (_kq(.02, .5), .05, None),
    ({"ic": .02, "p": .5}, .05, True),
])
def test_THIEU_DU_LIEU_thi_CHUA_KIEM_DUOC(kq, rao, dd):
    m, cau = N.phan_dinh_lap_lai(kq, rao, dd)
    assert m == 2 and "CHUA KIEM DUOC" in cau


def test_KHONG_VUOT_NHIEU_la_KHONG_LAP_LAI_va_DONG():
    m, cau = N.phan_dinh_lap_lai(_kq(0.03, 0.20), 0.05, True)
    assert m == 0 and "KET CUC 3" in cau


def test_P_DUNG_BANG_ALPHA_la_CHUA_VUOT():
    m, cau = N.phan_dinh_lap_lai(_kq(0.09, N.ALPHA), 0.05, True)
    assert m == 0 and "KET CUC 3" in cau


def test_VUOT_RAO_la_KET_CUC_1_va_KHONG_dong():
    m, cau = N.phan_dinh_lap_lai(_kq(0.06, 0.001), 0.05, True)
    assert m == 1 and "KET CUC 1" in cau


def test_DUNG_BANG_RAO_chua_phai_VUOT_RAO():
    m, cau = N.phan_dinh_lap_lai(_kq(0.05, 0.001), 0.05, True)
    assert "KET CUC 1" not in cau


def test_DUOI_RAO_CHAC_la_KET_CUC_2_va_DONG():
    # bien = 1,96 x 0,005 = 0,0098 ; 0,02 + 0,0098 < 0,05
    m, cau = N.phan_dinh_lap_lai(_kq(0.02, 0.001), 0.05, True)
    assert m == 0 and "KET CUC 2 " in cau


def test_DUOI_RAO_TRONG_BIEN_NHIEU_la_2b_va_KHONG_dong():
    """0,045 dưới rào 0,05 — nhưng chỉ 0,005, nhỏ hơn biên 0,0098. Đọc
    điểm ước lượng ở đây là đọc nhiễu thành kết luận."""
    m, cau = N.phan_dinh_lap_lai(_kq(0.045, 0.001), 0.05, True)
    assert m == 1 and "KET CUC 2b" in cau


def test_BIEN_dung_z_HAI_PHIA():
    """Phép kiểm hai phía thì biên cũng hai phía: 1,96 chứ không 1,645.
    Ở IC 0,041: 0,041 + 1,96 x 0,005 = 0,0508 > 0,05 -> SÁT RÀO; biên một
    phía cho 0,041 + 1,645 x 0,005 = 0,0492 < 0,05 -> sẽ đọc nhầm là CHẮC."""
    m, cau = N.phan_dinh_lap_lai(_kq(0.041, 0.001), 0.05, True)
    assert m == 1 and "KET CUC 2b" in cau, cau


def test_NGUOC_DAU_CO_Y_NGHIA_la_KHONG_LAP_LAI_va_DONG():
    """Hai phía bắt được cả một IC ÂM lớn. Hướng đã khai là +, nên một IC
    âm có ý nghĩa là bằng chứng NGƯỢC giả thuyết — không phải tín hiệu,
    và càng không được rơi vào ô "dưới rào chắc"."""
    m, cau = N.phan_dinh_lap_lai(_kq(-0.06, 0.001), 0.05, True)
    assert m == 0 and "KET CUC 3" in cau and "NGUOC DAU" in cau, cau
    m, cau = N.phan_dinh_lap_lai(_kq(0.0, 0.001), 0.05, True)
    assert "NGUOC DAU" in cau, cau
