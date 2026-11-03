"""Gác của `tools/do_dow_cau_truc.py` (BƯỚC 251, Lát 4a của đặc tả Dow; ĐO 34).

Mọi test chạy trên dữ liệu TỔNG HỢP hay dựng tay: không có test nào đọc cache thật, và không có test nào in lợi nhuận
của Dow. Đột biến của từng gác ghi ở `docs/STATE.md` BƯỚC 251.
"""
from __future__ import annotations

import ast
import importlib
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))
sys.path.insert(0, str(GOC))

D = importlib.import_module("do_dow_cau_truc")
import cau_truc_gia as C  # noqa: E402
import san_dau as S  # noqa: E402

DUONG = GOC / "tools" / "do_dow_cau_truc.py"
PHI = 0.001


def _mt(qd, tp, *, vung=None, khoa_tran=None, khoa_san=None, tm=None, tb=None, cuoi=None):
    """MaTran dựng tay từ lợi nhuận qua đêm / trong phiên (T, N)."""
    qd, tp = np.asarray(qd, float), np.asarray(tp, float)
    T, N = qd.shape
    z = np.zeros((T, N), dtype=bool)
    v = np.ones((T, N), dtype=bool) if vung is None else np.asarray(vung, bool)
    c = z.copy()
    if cuoi is None:
        for j in range(N):
            c[np.flatnonzero(v[:, j])[-1], j] = True
    else:
        c = np.asarray(cuoi, bool)
    return D.MaTran(ngay=[f"2022-01-{i + 1:02d}" for i in range(T)], ma=[f"M{j}" for j in range(N)], qua_dem=qd,
                    trong_phien=tp, dong=np.ones((T, N)), vung=v, cuoi_vung=c,
                    khoa_tran=z.copy() if khoa_tran is None else np.asarray(khoa_tran, bool),
                    khoa_san=z.copy() if khoa_san is None else np.asarray(khoa_san, bool),
                    truot_mua=np.zeros((T, N)) if tm is None else np.asarray(tm, float),
                    truot_ban=np.zeros((T, N)) if tb is None else np.asarray(tb, float))


QD = [0.0, 0.01, 0.02, -0.01, 0.03, 0.0]
TP = [0.01, 0.02, -0.01, 0.04, 0.02, 0.01]
S_TAY = [0, 1, 1, 0, 0, 0]        # mục tiêu biết tới hết nến t → hiệu lực từ mở cửa t+1


def _chay(M, s, **kw):
    return D.chay_dong_co(np.asarray(s, float)[None, :, None], M, PHI, **kw)


# ── động cơ khớp, đáp số dựng tay ─────────────────────────────────────────────────────────
def test_DONG_CO_dap_so_dung_tay_vao_o_mo_cua_t_cong_1_ra_o_mo_cua_sau_khi_het():
    M = _mt(np.array([QD]).T, np.array([TP]).T, tm=np.full((6, 1), 0.002), tb=np.full((6, 1), 0.003))
    kq = _chay(M, S_TAY)
    r = kq["ret"][0] * D.SO_MA
    assert r[0] == r[1] == 0.0                                   # chưa vào
    assert r[2] == pytest.approx(-0.01)                          # vào ở mở cửa: chỉ ăn lợi nhuận trong phiên
    assert r[3] == pytest.approx(0.99 * 1.04 - 1)                # giữ trọn phiên: đóng/đóng_trước − 1
    assert r[4] == pytest.approx(0.03)                           # ra ở mở cửa: chỉ ăn phần qua đêm
    assert r[5] == 0.0
    c = kq["chi_phi"][0] * D.SO_MA
    assert c[2] == pytest.approx(PHI + 0.002) and c[4] == pytest.approx(PHI + 0.003)
    assert c[0] == c[1] == c[3] == c[5] == 0.0
    e = kq["phoi"][0] * D.SO_MA
    assert list(np.round(e, 6)) == [0.0, 0.0, 0.5, 1.0, 0.5, 0.0]


def test_DONG_CO_kich_tran_huy_lenh_mua_va_thu_lai_phien_sau():
    kt = np.zeros((6, 1), dtype=bool)
    kt[2, 0] = True
    kq = _chay(_mt(np.array([QD]).T, np.array([TP]).T, khoa_tran=kt), S_TAY)
    r = kq["ret"][0] * D.SO_MA
    assert r[2] == 0.0                                           # lệnh mua huỷ
    assert r[3] == pytest.approx(0.04)                           # vào ở mở cửa phiên sau (s[2] vẫn 1)
    assert r[4] == pytest.approx(0.03)


def test_DONG_CO_kich_san_chan_lenh_ban_va_chi_ban_khi_mo_khoa():
    ks = np.zeros((6, 1), dtype=bool)
    ks[4, 0] = True
    kq = _chay(_mt(np.array([QD]).T, np.array([TP]).T, khoa_san=ks), S_TAY)
    r = kq["ret"][0] * D.SO_MA
    assert r[4] == pytest.approx(1.03 * 1.02 - 1)                # kẹt: vẫn nắm cả phiên
    assert r[5] == pytest.approx(0.0)                            # bán ở mở cửa phiên 5: qua đêm của phiên 5 = 0
    assert kq["phoi"][0, 5] * D.SO_MA == pytest.approx(0.5)


def test_DONG_CO_khoa_tat_thi_khong_chan():
    kt = np.zeros((6, 1), dtype=bool)
    kt[2, 0] = True
    kq = _chay(_mt(np.array([QD]).T, np.array([TP]).T, khoa_tran=kt), S_TAY, khoa=False)
    assert kq["ret"][0, 2] * D.SO_MA == pytest.approx(-0.01)


def test_DONG_CO_cuoi_vung_dong_vi_the_o_phi_nua_cong_truot_ban():
    M = _mt(np.array([QD]).T, np.array([TP]).T, tb=np.full((6, 1), 0.003))
    kq = _chay(M, [0, 1, 1, 1, 1, 1])                            # nắm tới hết vùng
    assert kq["chi_phi"][0, 5] * D.SO_MA == pytest.approx(PHI + 0.003)
    assert kq["chi_phi"][0, 2] * D.SO_MA == pytest.approx(PHI)   # vào (truot_mua = 0)


def test_DONG_CO_mot_lan_phu_nhieu_lan_bang_tung_lan():
    rng = np.random.default_rng(1)
    qd, tp = rng.normal(0, 0.01, (40, 3)), rng.normal(0, 0.01, (40, 3))
    M = _mt(qd, tp, tm=np.full((40, 3), 0.001), tb=np.full((40, 3), 0.001))
    mt = (rng.random((5, 40, 3)) > 0.5).astype(float)
    cung = D.chay_dong_co(mt, M, PHI)
    for k in range(5):
        mot = D.chay_dong_co(mt[k:k + 1], M, PHI)
        for ten in ("ret", "chi_phi", "phoi"):
            assert np.allclose(cung[ten][k], mot[ten][0])


def test_DONG_CO_ngoai_vung_khong_vao_va_khong_ghi_gi():
    vung = np.ones((6, 1), dtype=bool)
    vung[:3, 0] = False
    M = _mt(np.array([QD]).T, np.array([TP]).T, vung=vung)
    kq = _chay(M, [1, 1, 1, 1, 1, 1])
    assert kq["ret"][0, :3].sum() == 0 and kq["phoi"][0, :3].sum() == 0
    assert kq["phoi"][0, 3] * D.SO_MA == pytest.approx(0.5)      # vào ở mở cửa ngày đầu vùng (s[2] tính từ trước vùng)


# ── đối chứng (i): luôn giữ = rổ trừ một vòng phí ─────────────────────────────────────────
def _khung(n, seed, he=1000.0):
    rng = np.random.default_rng(seed)
    dong = 20 * np.exp(np.cumsum(rng.normal(0, 0.015, n)))
    mo = np.concatenate([[dong[0]], dong[:-1]]) * (1 + rng.normal(0, 0.003, n))
    cao = np.maximum(mo, dong) * (1 + np.abs(rng.normal(0, 0.003, n)))
    thap = np.minimum(mo, dong) * (1 - np.abs(rng.normal(0, 0.003, n)))
    return pd.DataFrame({"time": pd.date_range("2022-01-03", periods=n, freq="B").strftime("%Y-%m-%d"),
                         "open": mo, "high": cao, "low": thap, "close": dong, "volume": rng.integers(2e5, 5e5, n)})


def _ma_tran_tong_hop(n=420, so_ma=3):
    chuoi = {f"M{k}": (_khung(n, k), 1000.0, "HOSE") for k in range(so_ma)}
    vung = {m: np.ones(n, dtype=bool) for m in chuoi}
    return chuoi, vung, D.dung_ma_tran(chuoi, vung, von_vnd=1e9)


def test_DOI_CHUNG_i_dong_nhat_thuc_tren_du_lieu_tong_hop():
    _, _, M = _ma_tran_tong_hop()
    kq = D.doi_chung_i(M, PHI)
    assert kq["dat"] and kq["lech_gia_toi_da"] < 1e-9 and kq["lech_phi_toi_da"] < 1e-12


def test_DOI_CHUNG_i_trượt_khi_dong_co_thieu_mot_ngay():
    """Máy đo bị nghi như gác: nếu ngày đầu tính nhầm là close/close_trước (thay vì mở→đóng) thì đồng nhất thức phải vỡ."""
    _, _, M = _ma_tran_tong_hop()
    hong = _mt(M.qua_dem, M.trong_phien)
    hong.trong_phien = hong.trong_phien.copy()
    hong.trong_phien[0, 0] += 0.5                  # ngày đầu: mở→đóng khác dòng đóng(mã dựng)
    kq = D.doi_chung_i(hong, PHI)
    assert not kq["dat"]


def test_DUNG_MA_TRAN_vung_mat_na_va_cuoi_vung():
    chuoi, _, _ = _ma_tran_tong_hop(n=60, so_ma=2)
    vung = {"M0": np.arange(60) < 40, "M1": np.arange(60) >= 20}
    M = D.dung_ma_tran(chuoi, vung, von_vnd=1e9)
    assert M.vung[:, 0].sum() == 40 and M.vung[:, 1].sum() == 40
    assert M.cuoi_vung[:, 0].sum() == 1 and M.ngay[int(np.flatnonzero(M.cuoi_vung[:, 0])[0])] == chuoi["M0"][0]["time"].iloc[39]
    assert (M.truot_mua > 0).any() and (M.truot_ban > 0).any()


def test_CHON_VUNG_sach_truoc_moc_sau_moc_tu_moc_ma_vang_moc_khong_co_vung_sach():
    ngay = np.array(["2022-01-03", "2022-01-04", "2022-01-05"])
    assert list(D.chon_vung(ngay, "2022-01-05", "sach")) == [True, True, False]
    assert list(D.chon_vung(ngay, "2022-01-05", "sau_moc")) == [False, False, True]
    assert not D.chon_vung(ngay, None, "sach").any() and D.chon_vung(ngay, None, "sau_moc").all()
    assert D.chon_vung(ngay, "2022-01-04", "tat_ca").all()
    with pytest.raises(ValueError):
        D.chon_vung(ngay, "2022-01-05", "khac")


# ── rào hoà vốn không đọc lợi nhuận ───────────────────────────────────────────────────────
def test_RAO_HOA_VON_khong_doc_loi_nhuan():
    rng = np.random.default_rng(5)
    s = (rng.random((50, 3)) > 0.5).astype(float)
    a = _mt(rng.normal(0, 0.01, (50, 3)), rng.normal(0, 0.01, (50, 3)), tm=np.full((50, 3), 0.001), tb=np.full((50, 3), 0.001))
    b = _mt(rng.normal(0, 0.5, (50, 3)), rng.normal(0, 0.5, (50, 3)), tm=np.full((50, 3), 0.001), tb=np.full((50, 3), 0.001))
    assert D.rao_hoa_von(a, s, PHI) == D.rao_hoa_von(b, s, PHI)
    assert D.rao_hoa_von(a, s, PHI)["rao"] > 0


# ── trạng thái, thủy triều theo nến ───────────────────────────────────────────────────────
def test_THUY_TRIEU_CHUOI_bang_trang_thai_dow_tai_moi_nen():
    df = _khung(500, 11)
    r = C.doc_cau_truc(df, he_so_gia=1000.0, san="HOSE")
    chuoi = D.thuy_trieu_chuoi(r)
    assert len(chuoi) == 500 and set(chuoi) <= {C.TANG, C.GIAM, C.LAN, C.CHUA_DU}
    assert len(set(chuoi)) >= 3
    for t in range(0, 500, 7):
        assert chuoi[t] == C.trang_thai_dow(r, t).thuy_trieu, t


def test_THUY_TRIEU_CHUOI_nhan_qua_lich_su_chi_dung_cat():
    df = _khung(400, 12)
    day = D.trang_thai_dow(df, 1000.0, "HOSE")
    for t in (60, 150, 299, 399):
        cat = D.trang_thai_dow(df.iloc[:t + 1], 1000.0, "HOSE")
        assert (cat == day[:t + 1]).all(), t


def test_SMA200_chi_dung_den_het_t_va_chua_du_200_thi_dung_ngoai():
    dong = np.concatenate([np.full(200, 10.0), np.full(10, 12.0)])
    s = D.trang_thai_sma200(dong)
    assert not s[:199].any()
    assert not s[199]                           # đóng = SMA200 = 10, KHÔNG vượt
    assert s[200] and s[209]
    dong2 = dong.copy()
    dong2[-1] = 1.0
    assert (D.trang_thai_sma200(dong2)[:-1] == s[:-1]).all()      # đổi nến cuối không đổi quá khứ


def test_TSMOM_trung_binh_dau_cat_0_1_va_cua_so_thieu_dong_gop_0():
    dong = 10.0 * 1.01 ** np.arange(300)
    w = D.trong_so_tsmom(dong)
    assert w[:21].sum() == 0 and w[21] == pytest.approx(1 / 3) and w[63] == pytest.approx(2 / 3)
    assert w[252] == pytest.approx(1.0) and w.max() <= 1.0
    giam = 10.0 * 0.99 ** np.arange(300)
    assert D.trong_so_tsmom(giam).sum() == 0                      # cắt về [0, 1]: không bán khống
    gay = np.concatenate([10.0 * 1.01 ** np.arange(100), 10.0 * 1.01 ** 99 * 0.97 ** np.arange(100)])
    assert D.trong_so_tsmom(gay)[190] < D.trong_so_tsmom(gay)[99]


# ── chuẩn (iv): vào–ra ngẫu nhiên ─────────────────────────────────────────────────────────
def test_DOAN_GIU_dem_dung_cac_doan():
    assert D.doan_giu(np.array([0, 1, 1, 0, 1, 1, 1, 0, 0, 1], bool)) == [2, 3, 1]
    assert D.doan_giu(np.zeros(5, bool)) == []


def test_DAT_NGAU_NHIEN_giu_so_khoang_do_dai_khong_chong_cach_nhau():
    rng = np.random.default_rng(3)
    do_dai = [5, 12, 3, 20]
    vi_tri_gap = set()
    for _ in range(300):
        s = D.dat_ngau_nhien(do_dai, 100, rng)
        assert D.doan_giu(s) == do_dai                            # đúng thứ tự và độ dài, hai đoạn không dính nhau
        vi_tri_gap.add(int(np.flatnonzero(s)[0]))
    assert len(vi_tri_gap) > 10                                   # ngày bắt đầu thực sự ngẫu nhiên
    with pytest.raises(ValueError):
        D.dat_ngau_nhien([50, 50], 100, rng)                      # 100 chỗ không đủ cho 2×50 + 1 khe


def test_DICH_VONG_dich_it_nhat_252_va_giu_so_phien_giu():
    rng = np.random.default_rng(4)
    s = (np.arange(800) % 97) < 30
    for _ in range(100):
        d = D.dich_vong(s, rng)
        assert d.sum() == s.sum()
        k = next(k for k in range(1, 800) if (np.roll(s, k) == d).all())
        assert k >= 252
    ngan = np.arange(100) % 7 < 3
    assert D.dich_vong(ngan, rng).sum() == ngan.sum()             # vùng ngắn hơn 252: vẫn trả, không nổ


def test_NGAU_NHIEN_gia_tri_ky_vong_gan_0_khi_thoi_diem_doc_lap_voi_loi_nhuan():
    """Đối chứng (ii) trên dữ liệu mà ĐỘC LẬP được đảm bảo: 6 mã cùng phân phối, trạng thái dịch vòng → x ≈ 0 trong 2 SE."""
    rng = np.random.default_rng(7)
    T, N = 600, 6
    M = _mt(rng.normal(0, 0.004, (T, N)), rng.normal(0, 0.01, (T, N)))
    s = np.zeros((T, N))
    for j in range(N):
        s[:, j] = (np.arange(T) + 40 * j) % 130 < 50
    kq = D.doi_chung_ii(M, s, PHI, so_luot=200)
    assert kq["dat"] and kq["so_sigma"] < 3
    assert abs(kq["ky_vong_giai_tich_doc_lap"]) < 5 * kq["sai_so_chuan"] + 1e-4


def test_NGAU_NHIEN_bat_duoc_cau_truc_thoi_gian_trong_thi_truong_x_troi():
    """Máy đo phải THẤY thứ nó được thiết kế để thấy: mã nào trôi lên thì có tỷ lệ-trong-thị-trường cao → x kỳ vọng > 0,
    và `ky_vong_doc_lap` phải dương và gần giá trị đo của chính chuẩn đồng bộ thời gian."""
    rng = np.random.default_rng(8)
    T, N = 600, 6
    troi = np.linspace(-0.0005, 0.0015, N)
    M = _mt(rng.normal(0, 0.002, (T, N)) + troi, rng.normal(0, 0.008, (T, N)) + troi)
    p = np.linspace(0.1, 0.9, N)
    s = np.stack([(np.random.default_rng(j).random(T) < p[j]) for j in range(N)], axis=1).astype(float)
    s = np.stack([np.convolve(s[:, j], np.ones(15) / 15, mode="same") > 0.5 for j in range(N)], axis=1).astype(float)
    kq = D.doi_chung_ii(M, s, PHI, so_luot=200)
    assert kq["ky_vong_giai_tich_doc_lap"] > 1e-5
    assert kq["trung_binh_x_tho"] > 0 and not kq["dat"]            # trượt ĐÚNG CHỖ: chữ ký trước đòi ≈ 0
    assert kq["hoan_vi"]["so_sigma"] < kq["so_sigma"]               # hoán vị mã cắt đúng thứ gây lệch


# ── kết cục ───────────────────────────────────────────────────────────────────────────────
def _kc(delta, nua=0.0010, ktc_i=None, ktc_ii=(-1, 1), ktc_iii=(-1, 1), thang=0.5, ok=True):
    ktc_i = (delta - nua, delta + nua) if ktc_i is None else ktc_i
    return D.ket_cuc(delta_i=delta, ktc_i=ktc_i, ktc_ii=ktc_ii, ktc_iii=ktc_iii, thang_iv=thang, doi_chung_dat=ok)


def test_KET_CUC_K0_thang_moi_thu_khi_doi_chung_truot():
    assert _kc(0.005, ok=False)["ket_cuc"] == "K0"


def test_KET_CUC_A_nho_hon_nguong_nho_hoac_KTC_chua_0_ca_ba():
    assert _kc(0.0004)["ket_cuc"] == "A"                          # |Δ| ≤ nửa của nửa bề rộng (0,0005)
    assert _kc(0.0008, ktc_i=(-0.0002, 0.0018))["ket_cuc"] == "A"  # KTC chứa 0 và cả ba KTC chứa 0
    assert _kc(0.0008, ktc_i=(-0.0002, 0.0018), ktc_ii=(0.0001, 0.0009))["ket_cuc"] == D.KET_CUC_KHE


A_CONG_KTC_I = (0.0001, 0.0020)   # KTC LỆCH: Δ = 0,0008 trong (nhỏ, lớn] = (0,000475 ; 0,00095] mà cận dưới vẫn > 0


def test_KET_CUC_A_cong_can_du_bon_dieu_kien():
    d = 0.0008
    ok = {"ktc_i": A_CONG_KTC_I, "ktc_ii": (0.0001, 0.0009), "thang": 0.97}
    assert _kc(d, **ok)["ket_cuc"] == "A+"
    assert _kc(d, **{**ok, "ktc_ii": (-1, 1), "ktc_iii": (0.0001, 0.0009)})["ket_cuc"] == "A+"
    assert _kc(d, **{**ok, "thang": 0.94})["ket_cuc"] == D.KET_CUC_KHE                  # thắng < 95%
    assert _kc(d, **{**ok, "thang": 0.95})["ket_cuc"] == "A+"                           # đúng 95% đủ
    assert _kc(d, **{**ok, "ktc_ii": (-1, 1)})["ket_cuc"] == D.KET_CUC_KHE              # ii, iii đều chứa 0
    assert _kc(d, **{**ok, "ktc_i": (-0.0001, 0.0018)})["ket_cuc"] == D.KET_CUC_KHE     # KTC của Δ_(i) chứa 0
    assert _kc(0.00096, **{**ok, "ktc_i": (0.0001, 0.0020)})["ket_cuc"] == "B"          # vượt ngưỡng lớn (0,00095) → B
    assert _kc(0.00047, **{**ok, "ktc_i": (0.0001, 0.0020)})["ket_cuc"] == "A"          # ≤ ngưỡng nhỏ (0,000475) → A


def test_KET_CUC_A_cong_gan_nhu_khong_bao_gio_dat_khi_KTC_doi_xung():
    """Khe của văn bản ký (khai trong STATE BƯỚC 251): ngưỡng lớn = nửa bề rộng KTC của Δ_(i). Với KTC đối xứng quanh Δ,
    Δ ≤ nửa bề rộng ⇒ cận dưới ≤ 0 ⇒ KTC chứa 0 ⇒ A⁺ không thể khớp. A⁺ chỉ khớp khi KTC bootstrap LỆCH."""
    nua = 0.001
    for d in np.linspace(0.0, 0.002, 41):
        kq = D.ket_cuc(delta_i=d, ktc_i=(d - nua, d + nua), ktc_ii=(0.0002, 0.001), ktc_iii=(0.0002, 0.001), thang_iv=0.99,
                       doi_chung_dat=True)
        assert kq["ket_cuc"] != "A+"


def test_KET_CUC_B_va_C_dung_dau_va_gioi_han():
    assert _kc(0.0011)["ket_cuc"] == "B"
    assert _kc(0.0010)["ket_cuc"] != "B"                          # đúng bằng ngưỡng lớn: không vượt
    assert _kc(-0.0012)["ket_cuc"] == "C"                         # < −nhỏ và KTC loại 0 (đối xứng ⇒ Δ < −nửa bề rộng)
    assert _kc(-0.0008)["ket_cuc"] == "A"                         # KTC chứa 0 và cả ba KTC chứa 0 → A
    assert _kc(-0.0006, ktc_i=(-0.0016, 0.0004), ktc_ii=(0.0001, 0.0009))["ket_cuc"] == D.KET_CUC_KHE
    assert _kc(-0.0005)["ket_cuc"] == "A"                         # đúng −nhỏ: |Δ| ≤ nhỏ → A (biên đóng)
    assert _kc(-0.0006, ktc_i=(-0.0020, -0.0001))["ket_cuc"] == "C"          # KTC lệch loại 0 từ phía âm


def test_KET_CUC_nguong_suy_ra_tu_nua_be_rong_khong_go_tay():
    kq = _kc(0.0, nua=0.004)
    assert kq["nguong_nho"] == pytest.approx(0.002) and kq["nguong_lon"] == pytest.approx(0.004)


def test_KET_CUC_khong_bao_gio_mau_thuan_tren_luoi_day_va_khe_duoc_dem():
    """Quét lưới: hai nhãn không bao giờ cùng khớp; khe (không nhãn nào) tồn tại và chỉ nằm ở vùng đã khai."""
    dem = {"khe": 0, "mau_thuan": 0, "tong": 0}
    nua = 0.001
    for delta, li, lii, liii, th in itertools.product(
            np.linspace(-0.003, 0.003, 25), (-1.5, -0.5, 0.0, 0.5, 1.5), (0, 1), (0, 1), (0.5, 0.96)):
        ktc_i = (delta - nua, delta + nua)
        ktc_ii = (-0.001, 0.001) if lii == 0 else (0.0002, 0.001)
        ktc_iii = (-0.001, 0.001) if liii == 0 else (0.0002, 0.001)
        kq = D.ket_cuc(delta_i=delta, ktc_i=ktc_i, ktc_ii=ktc_ii, ktc_iii=ktc_iii, thang_iv=th, doi_chung_dat=True)
        dem["tong"] += 1
        dem["khe"] += kq["ket_cuc"] == D.KET_CUC_KHE
        dem["mau_thuan"] += kq["ket_cuc"] == D.KET_CUC_MAU_THUAN
    assert dem["mau_thuan"] == 0
    assert 0 < dem["khe"] < dem["tong"]


# ── KTC của sân đấu, cấu hình khoá ────────────────────────────────────────────────────────
def test_KTC_dung_ham_san_dau_va_khop_cau_hinh_khoa(capsys):
    rng = np.random.default_rng(0)
    a, b = rng.normal(0.001, 0.01, 400), rng.normal(0, 0.01, 400)
    k = D.ktc_cap(a, b)
    assert k["ktc"] is not None and "độ phủ" in k["dong"]
    assert D.khop_cau_hinh(k["ktc"]) == []
    assert D.in_cau_hinh_ktc(k["ktc"]) == []
    out = capsys.readouterr().out
    assert "cấu hình KTC dùng" in out and "KHỚP" in out and "PW" in out


def test_KTC_lech_cau_hinh_la_K0_khong_bao_gio_im():
    rng = np.random.default_rng(0)
    a = rng.normal(0, 0.01, 400)
    lech = S.ktc_khoi_co_cap(a, a * 0, do_dai=10)                  # khối 10 phiên: cấu hình đã BỊ BÁC ở BƯỚC 248
    assert D.khop_cau_hinh(lech) and "do_dai_khoi" in D.khop_cau_hinh(lech)[0]
    lech2 = S.ktc_khoi_co_cap(a, a * 0, vong=2000)
    assert any("vong" in x for x in D.khop_cau_hinh(lech2))
    assert D.khop_cau_hinh(None)


def test_KTC_khong_viet_ban_sao_thu_hai_cua_ham_ktc():
    """Luật ghim của ĐO 34: KHÔNG bản sao thứ hai. Dụng cụ không tự gọi `percentile` hay rút khối."""
    cay = ast.parse(DUONG.read_text(encoding="utf-8"))
    ham_ktc = [n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name in ("ktc_cap", "tom_tat_x", "khop_cau_hinh")]
    assert len(ham_ktc) == 3                                       # quần thể KHÁC RỖNG (lỗi 66)
    for ham in ham_ktc:
        goi = {n.func.attr for n in ast.walk(ham) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
        assert not ({"percentile", "quantile", "integers", "choice", "resample"} & goi), ham.name
    goi_tat_ca = {n.func.attr for n in ast.walk(cay) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert "ktc_co_nhan" in goi_tat_ca and "khop_cau_hinh_khoa" in goi_tat_ca
    assert "ktc_khoi_co_cap" not in {n.name for n in cay.body if isinstance(n, ast.FunctionDef)}


# ── đường ra kết cục chạy được trên dữ liệu TỔNG HỢP, và nhạy với lợi thế gài ─────────────────
def _tong_hop_co_loi_the(gai: float, seed=21, T=500, N=4):
    rng = np.random.default_rng(seed)
    s = np.zeros((T, N))
    for j in range(N):
        s[:, j] = (np.arange(T) + 70 * j) % 160 < 60
    truoc = np.vstack([np.zeros((1, N)), s[:-1]])
    tp = rng.normal(0, 0.012, (T, N)) + gai * truoc
    qd = rng.normal(0, 0.004, (T, N))
    return _mt(qd, tp), s


def test_CHAY_KET_QUA_tong_hop_khong_loi_the_la_A_va_co_loi_the_manh_la_B(capsys):
    cls = {}
    for gai in (0.0, 0.01):
        M, s = _tong_hop_co_loi_the(gai)
        sma = (np.arange(M.vung.shape[0])[:, None] % 5 < 3) & np.ones(M.vung.shape, bool)
        ts = np.clip((np.arange(M.vung.shape[0])[:, None] % 9) / 9.0, 0, 1) * np.ones(M.vung.shape)
        kq = D.chay_ket_qua(M, s, sma.astype(float), ts, PHI, doi_chung_dat=True, so_luot=30)
        cls[gai] = kq
        assert kq["lech_cau_hinh_ktc"] == [] and kq["delta"]["i"]["ktc"] is not None
        assert set(kq["delta"]) == {"i", "ii", "iii"} and "cot_tho_cong_don_diem_phan_tram" in kq
    assert cls[0.0]["ket_cuc"]["ket_cuc"] in ("A", D.KET_CUC_KHE)
    assert cls[0.01]["delta"]["i"]["delta"] > cls[0.0]["delta"]["i"]["delta"] + 1e-4
    assert cls[0.01]["ket_cuc"]["ket_cuc"] in ("B", "A+", D.KET_CUC_KHE)
    assert cls[0.01]["delta"]["i"]["delta"] > cls[0.01]["ket_cuc"]["nguong_lon"]


def test_CHAY_KET_QUA_K0_khi_doi_chung_truot():
    M, s = _tong_hop_co_loi_the(0.0)
    kq = D.chay_ket_qua(M, s, s, s, PHI, doi_chung_dat=False, so_luot=20)
    assert kq["ket_cuc"]["ket_cuc"] == "K0"


# ── khoá: lượt chạy dữ liệu thật bị khoá ở Lát 4a ─────────────────────────────────────────
def test_KHOA_lat_4a_khong_doc_ket_qua_that(monkeypatch, capsys):
    assert D.CHO_PHEP_DOC_KET_QUA_THAT is False
    def bom(*a, **k):
        raise AssertionError("khong duoc nap du lieu khi khoa")
    monkeypatch.setattr(D, "nap_cache", bom)
    monkeypatch.setattr(D, "chay_ket_qua", bom)
    assert D.main(["ket-qua", "--cache", "x"]) == 3
    assert D.main(["ket-qua", "--cache", "x", "--xac-nhan", D.CAU_XAC_NHAN_LAT_4B]) == 3          # câu đúng nhưng cờ khoá
    monkeypatch.setattr(D, "CHO_PHEP_DOC_KET_QUA_THAT", True)
    assert D.main(["ket-qua", "--cache", "x", "--xac-nhan", "sai"]) == 3                          # cờ mở nhưng câu sai
    assert "TỪ CHỐI" in capsys.readouterr().out


def test_KHOA_chay_ket_qua_chi_duoc_goi_tu_test_va_mot_ham_khoa():
    """Gác AST: ngoài định nghĩa, `chay_ket_qua` KHÔNG được gọi ở đâu trong tools/do_dow_cau_truc.py (Lát 4a); và
    `lenh_ket_qua` phải đọc cả hai khoá TRƯỚC mọi dòng khác."""
    cay = ast.parse(DUONG.read_text(encoding="utf-8"))
    goi = [n for n in ast.walk(cay) if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "chay_ket_qua"]
    assert goi == []
    lenh = next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == "lenh_ket_qua")
    thuc = [s for s in lenh.body if not (isinstance(s, ast.Expr) and isinstance(getattr(s, "value", None), ast.Constant))]
    dau = thuc[0]
    assert isinstance(dau, ast.If)
    ten = {n.id for n in ast.walk(dau.test) if isinstance(n, ast.Name)}
    assert {"CHO_PHEP_DOC_KET_QUA_THAT", "CAU_XAC_NHAN_LAT_4B"} <= ten
    assert any(isinstance(n, ast.Return) and getattr(n.value, "value", None) == 3 for n in ast.walk(dau))


def test_KHOA_doi_chung_khong_goi_chay_ket_qua_cung_khong_nhap_vao_duong_cham_diem():
    cay = ast.parse(DUONG.read_text(encoding="utf-8"))
    nhap = {a.name.split(".")[0] for n in ast.walk(cay) if isinstance(n, ast.Import) for a in n.names} | \
           {n.module.split(".")[0] for n in ast.walk(cay) if isinstance(n, ast.ImportFrom) and n.module}
    cam = {"paper_trading_journal", "run_daily", "walkforward", "sheets_store", "master_agent", "ke_hoach_vao_lenh"}
    assert not (nhap & cam)


# ── dựng lại độc lập (đối chứng iv) ───────────────────────────────────────────────────────
def test_DUNG_LAI_THU_CONG_khop_nhat_ky_tung_dong_tren_chuoi_tong_hop():
    kq = D.dung_lai_thu_cong(_khung(500, 31), 1000.0, "HOSE")
    assert kq["so_pivot_tay"] >= 3 and kq["khop"]
    assert all(d["khop"] for d in kq["dong"])


def test_DUNG_LAI_THU_CONG_tri_hoan_khi_mo_dun_lech_mot_ngay(monkeypatch):
    """Máy đo bị nghi như gác: đẩy `ngay_biet` của mô-đun lệch 1 phiên thì dựng lại độc lập phải báo LỆCH."""
    df = _khung(500, 31)
    goc = C.doc_cau_truc

    def lech(*a, **k):
        r = goc(*a, **k)
        nk = tuple(p.__class__(**{**p.__dict__, "ngay_biet": p.ngay_xay_ra}) if (p.cap == C.CAP_SWING and p.su_kien == C.XAC_NHAN)
                   else p for p in r.nhat_ky)
        return r.__class__(**{**r.__dict__, "nhat_ky": nk})
    monkeypatch.setattr(C, "doc_cau_truc", lech)
    assert not D.dung_lai_thu_cong(df, 1000.0, "HOSE")["khop"]


# ── H2, H3, lật lại ───────────────────────────────────────────────────────────────────────
def test_LOI_NHUAN_CUA_SO_mo_cua_t_cong_1_toi_dong_cua_t_cong_21():
    mo = np.arange(100, 130, dtype=float)
    dong = mo + 0.5
    assert D.loi_nhuan_cua_so(mo, dong, 3) == pytest.approx(dong[24] / mo[4] - 1)
    assert D.loi_nhuan_cua_so(mo, dong, 29 - 21) is not None        # t + 21 = 29 là nến cuối
    assert D.loi_nhuan_cua_so(mo, dong, 29 - 21 + 1) is None


def test_SU_KIEN_H2_chi_lay_CHoCH_cap_swing_va_chuan_cung_thang():
    df = _khung(900, 41)
    thang = np.zeros(len(df))
    kq = D.su_kien_h2(df, 1000.0, "HOSE", thang, np.random.default_rng(0), so_luot=50)
    r = C.doc_cau_truc(df, he_so_gia=1000.0, san="HOSE")
    so_choch = sum(1 for e in r.su_kien if e.cap == C.CAP_SWING and e.loai == C.CHOCH)
    assert 0 < len(kq) <= so_choch
    assert all(k["chieu"] in (C.TANG, C.GIAM) and np.isfinite(k["du"]) for k in kq)


def test_H3_dem_su_kien_va_do_tre_mo_ta_khong_loi_nhuan():
    kq = D.h3_chi_so(_khung(900, 42), 1000.0, "HOSE")
    assert set(kq["su_kien"]) == {C.BOS, C.CHOCH, C.KHOI_DAU} and kq["tre_trung_vi"] >= 1
    assert not any("loi_nhuan" in k or "lai" in k for k in kq)


def test_LAT_LAI_dat_ten_ro_hai_dinh_nghia():
    df = _khung(900, 43)
    r = C.doc_cau_truc(df, he_so_gia=1000.0, san="HOSE")
    kq = D.lat_lai_hai_dinh_nghia(df, r)
    assert kq and all({"n", "lat_lai_sau_su_kien_nguoc", "lat_lai_dong_cua_qua_moc"} <= set(v) for v in kq.values())
    assert any(v["n"] > 0 for v in kq.values())
    assert all(v["lat_lai_sau_su_kien_nguoc"] <= v["n"] and v["lat_lai_dong_cua_qua_moc"] <= v["n"] for v in kq.values())


# ── cấu hình CLI ──────────────────────────────────────────────────────────────────────────
def test_CLI_cau_hinh_ktc_thoat_0_va_in_khop(capsys):
    assert D.main(["cau-hinh-ktc"]) == 0
    assert "KHỚP" in capsys.readouterr().out


def test_HANG_SO_khop_ky_ho_so_cache_va_ngay_khong_rong():
    assert D.BAM_CACHE_KY.startswith("acf6dca1") and len(D.BAM_CACHE_KY) == 64
    assert D.SO_MA == 71 == len(D.CUSTOM_WATCHLIST_SYMBOLS)
    assert (D.SO_LUOT_NGAU_NHIEN, D.DICH_TOI_THIEU, D.SO_LAP_TIEM, D.NGUONG_BAT_TIEM) == (1000, 252, 30, 0.8)
    assert D.CUA_SO_TSMOM == (21, 63, 252) and D.PHIEN_SMA == 200 and D.CUA_SO_SU_KIEN == 21
    assert D.HE_SO_NUA_RAO == 0.5 and D.NGUONG_THANG_A_CONG == 0.95
    assert D.phi_nua() == pytest.approx(0.0046 / 2)
