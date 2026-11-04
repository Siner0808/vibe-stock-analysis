"""Gác của `tools/do_dow_cau_truc.py` (BƯỚC 251, Lát 4a của đặc tả Dow; ĐO 34).

Mọi test chạy trên dữ liệu TỔNG HỢP hay dựng tay: không có test nào đọc cache thật, và không có test nào in lợi nhuận
của Dow. Đột biến của từng gác ghi ở `docs/STATE.md` BƯỚC 251.
"""
from __future__ import annotations

import ast
import importlib
import itertools
import json
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
    """Máy đo bị nghi như gác: bơm một sai số vào lợi nhuận qua đêm ở GIỮA vùng (không đổi giá đóng cửa) thì đồng nhất thức
    lợi nhuận ghép = đóng_cuối / mở_vào − 1 phải vỡ; và một phí thiếu cũng phải vỡ."""
    import dataclasses
    _, _, M = _ma_tran_tong_hop()
    qd = M.qua_dem.copy()
    qd[100, 0] += 1e-3
    assert not D.doi_chung_i(dataclasses.replace(M, qua_dem=qd), PHI)["dat"]
    assert D.doi_chung_i(M, PHI)["dat"]
    assert D.doi_chung_i(M, PHI)["lech_phi_toi_da"] < 1e-12


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
    assert abs(kq["ky_vong_giai_tich"]) < 5 * kq["sai_so_chuan"] + 1e-4


def _m_x_troi(seed=8, T=600, N=6):
    """Mã nào trôi lên thì có tỷ lệ-trong-thị-trường cao: E[x̄] của chuẩn đồng bộ thời gian KHÁC 0 dù thời điểm vô nghĩa."""
    rng = np.random.default_rng(seed)
    troi = np.linspace(-0.0005, 0.0015, N)
    M = _mt(rng.normal(0, 0.002, (T, N)) + troi, rng.normal(0, 0.008, (T, N)) + troi)
    p = np.linspace(0.1, 0.9, N)
    s = np.stack([(np.random.default_rng(j).random(T) < p[j]) for j in range(N)], axis=1).astype(float)
    s = np.stack([np.convolve(s[:, j], np.ones(15) / 15, mode="same") > 0.5 for j in range(N)], axis=1).astype(float)
    return M, s


def test_NGAU_NHIEN_cau_truc_thoi_gian_trong_thi_truong_x_troi_KHONG_con_lam_doi_chung_ii_truot():
    """SỬA S1 (BƯỚC 252): chữ ký cũ đòi x̄ ≈ 0 và trượt ĐÚNG vì cấu trúc này; kỳ vọng GIẢI TÍCH tính cấu trúc ấy vào, nên đối chứng
    ĐẠT dù x̄ > 0 rõ rệt (bản cũ trượt ở đúng dữ liệu này)."""
    M, s = _m_x_troi()
    kq = D.doi_chung_ii(M, s, PHI, so_luot=200)
    assert kq["ky_vong_giai_tich"] > 1e-5 and kq["trung_binh_x_tho"] > 1e-5      # x̄ ≠ 0 vì tương quan tỷ lệ × độ trôi
    assert kq["dat"] and kq["so_sigma"] < 2.5


def test_DOI_CHUNG_ii_BAT_loi_gai_he_thong_va_im_khi_dong_co_lanh():
    """Đối chứng (ii) phải CÓ THỂ trượt (chỉ khi nó trượt được thì ĐẠT mới có nghĩa): gài một cộng-thêm cố định mỗi đơn-vị-đầu-tư-ngày
    vào động cơ thì trượt; động cơ lành ĐẠT cùng hạt."""
    M, s = _m_x_troi()
    sach = D.doi_chung_ii(M, s, PHI, so_luot=200)
    cay = D.doi_chung_ii(M, s, PHI, so_luot=200, dong_co=D.LOI_CAY["cong_1bp"])
    assert sach["dat"] and not cay["dat"]
    assert cay["lech"] - sach["lech"] == pytest.approx(1e-4 * 0.04, rel=0.5)                    # cỡ 1 bp × mức đầu tư trung bình (~0,04 ở dữ liệu này)
    assert set(D.LOI_CAY) == {"cong_0.15bp", "cong_0.5bp", "cong_1bp", "nhan_1.01", "nhan_1.05"}


def test_KY_VONG_GIAI_TICH_dap_so_dung_tay_mot_ma_mot_xung():
    """Một mã, n = 6, chuỗi trạng thái [1,0,0,0,0,0], dịch k ∈ {1..5} đều (dich_toi_thieu = 1), qua đêm 0, trong phiên 1..6%:
    w_sau(i) = 0,2 ở i = 2..5; w_trước(i) = 0,2 ở i = 3..5; e = (0,1 ; 0,2 ; 0,2 ; 0,2) ở i = 2..5. Σ lai = 0,2 × (0,03 + 0,04 +
    0,05 + 0,06) − ... : x = Σ(lai − e × r_rổ)/71 = (0,036 − 0,033)/71 trên 6 ngày. Nửa ngày TẮT cho 0 (qua đêm 0 ⇒ cả ngày = trong phiên)."""
    M = _mt(np.zeros((6, 1)), np.array([[0.01, 0.02, 0.03, 0.04, 0.05, 0.06]]).T)
    s = np.array([[1, 0, 0, 0, 0, 0]], float).T
    assert D.ky_vong_dich_giai_tich(M, s, dich_toi_thieu=1) == pytest.approx(0.003 / 6 / D.SO_MA)
    assert D.ky_vong_dich_giai_tich(M, s, dich_toi_thieu=1, nua_ngay=False) == pytest.approx(0.0, abs=1e-15)


def test_KY_VONG_GIAI_TICH_vung_dung_bang_dich_toi_thieu_van_dich_tu_1_den_n_tru_1():
    """Biên của phân bố dịch (đúng `dich_vong`): n ≤ dich_toi_thieu → k ∈ [1, n−1]; n > dich_toi_thieu → k ∈ [dich_toi_thieu, n−1]."""
    M = _mt(np.zeros((6, 1)), np.array([[0.01, 0.02, 0.03, 0.04, 0.05, 0.06]]).T)
    s = np.array([[1, 0, 0, 0, 0, 0]], float).T
    tay = 0.003 / 6 / D.SO_MA
    assert D.ky_vong_dich_giai_tich(M, s, dich_toi_thieu=6) == pytest.approx(tay)               # n = 6 = ngưỡng: vẫn [1, 5]
    assert D.ky_vong_dich_giai_tich(M, s, dich_toi_thieu=5) != pytest.approx(tay)               # n = 6 > 5: k ∈ [5, 5] một dịch chuyển


def test_DOI_CHUNG_ii_chay_dong_co_TAT_khoa_bien_nen_khoa_day_dac_khong_lam_trượt():
    """(ii) kiểm tính lợi nhuận và mức đầu tư, KHÔNG kiểm khoá biên (S1): đặt cờ kịch trần dày; động cơ tắt khoá vẫn khớp E_gt, trong khi
    bản có khoá chặn nhiều lệnh mua nên lệch hẳn (báo kèm `khoa_truot_chenh_cap`)."""
    M, s = _m_x_troi()
    rng = np.random.default_rng(3)
    M = D.MaTran(**{**M.__dict__, "khoa_tran": rng.random(M.vung.shape) < 0.4})
    kq = D.doi_chung_ii(M, s, PHI, so_luot=200)
    assert kq["dat"]
    ch = kq["khoa_truot_chenh_cap"]
    assert abs(ch["trung_binh"]) > 5 * ch["sai_so_chuan"]


def test_KY_VONG_GIAI_TICH_bang_dong_co_khi_liet_ke_MOI_cap_dich_chuyen():
    """Độc lập với động cơ: liệt kê mọi cặp dịch chuyển (hai mã, qua đêm và trong phiên khác 0 nên số hạng nén chéo CÓ MẶT) rồi cho
    qua CHÍNH động cơ khớp; trung bình x̄ gộp trên mọi lượt phải bằng kỳ vọng giải tích tới sai số máy."""
    rng = np.random.default_rng(31)
    T, N = 14, 2
    M = _mt(rng.normal(0.001, 0.02, (T, N)), rng.normal(-0.001, 0.02, (T, N)))
    s = (rng.random((T, N)) > 0.5).astype(float)
    ks = range(1, T)
    muc = np.zeros((len(ks) ** 2, T, N))
    for i, (k0, k1) in enumerate(itertools.product(ks, ks)):
        muc[i, :, 0], muc[i, :, 1] = np.roll(s[:, 0], k0), np.roll(s[:, 1], k1)
    kq = D.chay_dong_co(muc, M, PHI, khoa=False, truot=False)
    ro = D.ro_trung_binh(M)
    x_tho = (kq["ret"] - kq["phoi"] * ro[None, :]).mean(axis=1).mean()
    assert D.ky_vong_dich_giai_tich(M, s, dich_toi_thieu=1) == pytest.approx(x_tho, abs=1e-12)
    # bỏ số hạng nén chéo thì phải lệch (gác chính gác)
    assert abs(D.ky_vong_dich_giai_tich(M, s, dich_toi_thieu=1, nua_ngay=False) - x_tho) > 1e-9


def test_KHOANG_CACH_ii_xap_xi_cu_khong_phai_E_gt_khi_cua_so_khong_dong_deu():
    """Hai yếu tố công thức BƯỚC 251 thiếu: mã có cửa sổ ngắn hơn T (trọng số số-ngày hiện diện) và dịch ≥ 252 (cửa sổ dài)."""
    rng = np.random.default_rng(5)
    T, N = 400, 3
    vung = np.ones((T, N), bool)
    vung[:150, 1] = False
    vung[300:, 2] = False
    M = _mt(rng.normal(0.0005, 0.01, (T, N)), rng.normal(0.0005, 0.01, (T, N)), vung=vung)
    s = ((np.arange(T)[:, None] // 40 + np.arange(N)[None, :]) % 2 == 0).astype(float)
    buoc = dict(D.phan_ra_khoang_cach_ii(M, s))
    cu, co_trong_so, e_gt = buoc["xấp xỉ BƯỚC 251"], buoc["+ trọng số số-ngày hiện diện, r_rổ theo cửa sổ từng mã"], buoc["liệt kê, dịch ≥ 252, nửa ngày (= E_gt)"]
    assert len({round(v, 12) for v in (cu, co_trong_so, e_gt)}) == 3 and len(buoc) == 5
    assert e_gt == pytest.approx(D.ky_vong_dich_giai_tich(M, s))


# ── kết cục ───────────────────────────────────────────────────────────────────────────────
def _kc(delta, nua=0.0010, ktc_i=None, ktc_ii=(-1, 1), ktc_iii=(-1, 1), thang=0.5, ok=True):
    ktc_i = (delta - nua, delta + nua) if ktc_i is None else ktc_i
    return D.ket_cuc(delta_i=delta, ktc_i=ktc_i, ktc_ii=ktc_ii, ktc_iii=ktc_iii, thang_iv=thang, doi_chung_dat=ok)


A_CONG_OK = {"ktc_i": (0.0005, 0.0025), "ktc_ii": (0.0001, 0.0009), "thang": 0.97}      # Δ = 0,0015 ∈ (nhỏ 0,0005 ; lớn 0,002]


def test_KET_CUC_K0_thang_moi_thu_khi_doi_chung_truot():
    assert _kc(0.005, ok=False)["ket_cuc"] == "K0"


def test_KET_CUC_A_la_mac_dinh_cho_moi_vung_con_lai_va_ghi_ly_do():
    assert _kc(0.0004)["ket_cuc"] == "A" and _kc(0.0004)["ly_do_A"].startswith("a")            # KTC chứa 0
    assert _kc(0.0008)["ly_do_A"].startswith("a")                                              # Δ > nhỏ nhưng KTC chứa 0
    assert _kc(0.0004, ktc_i=(0.0001, 0.0021))["ly_do_A"].startswith("b")                      # KTC loại 0 nhưng |Δ| ≤ nhỏ
    assert _kc(-0.0008)["ket_cuc"] == "A" and _kc(-0.0008)["ly_do_A"].startswith("a")           # Δ < −nhỏ mà KTC chứa 0 → A, KHÔNG còn khe
    assert _kc(-0.0010, ktc_i=(0.0001, 0.0030))["ly_do_A"].startswith("d")                      # KTC lệch dấu với Δ
    # vùng từng bị bỏ trống ở bản ký: Δ dương rõ, KTC loại 0, nhưng thiếu điều kiện của A⁺ → A kèm lý do c
    for thieu in ({"thang": 0.94}, {"ktc_ii": (-1, 1)}):
        kq = _kc(0.0015, **{**A_CONG_OK, **thieu})
        assert kq["ket_cuc"] == "A" and kq["ly_do_A"].startswith("c")


def test_KET_CUC_A_cong_can_du_bon_dieu_kien_va_VOI_TOI_DUOC_khi_KTC_doi_xung():
    d = 0.0015
    assert _kc(d, **A_CONG_OK)["ket_cuc"] == "A+"
    assert _kc(d, **{**A_CONG_OK, "ktc_ii": (-1, 1), "ktc_iii": (0.0001, 0.0009)})["ket_cuc"] == "A+"
    assert _kc(d, **{**A_CONG_OK, "thang": 0.95})["ket_cuc"] == "A+"                                 # đúng 95% đủ
    assert _kc(d, **{**A_CONG_OK, "ktc_i": (-0.0001, 0.0031)})["ket_cuc"] == "A"                    # KTC của Δ_(i) chứa 0
    assert _kc(d, **{**A_CONG_OK, "ktc_ii": (-0.002, -0.0001)})["ket_cuc"] == "A"                   # loại 0 phía ÂM không phải "hơn"
    assert _kc(d, **{**A_CONG_OK, "ktc_i": (0.0, 0.0030)})["ket_cuc"] == "A"                         # cận dưới đúng 0: chưa "loại 0"
    assert _kc(d, **{**A_CONG_OK, "ktc_ii": (0.0, 0.0009), "ktc_iii": (-1, 1)})["ket_cuc"] == "A"     # ii cận dưới đúng 0: chưa "hơn"
    assert _kc(d, **{**A_CONG_OK, "ktc_ii": (-1, 1), "ktc_iii": (0.0, 0.0009)})["ket_cuc"] == "A"     # iii cận dưới đúng 0: chưa "hơn"
    assert _kc(0.0021, **A_CONG_OK)["ket_cuc"] == "B"                                                # vượt lớn (2H = 0,002)
    assert _kc(0.0020, **{**A_CONG_OK, "ktc_i": (0.0010, 0.0030)})["ket_cuc"] == "A+"               # đúng bằng lớn: biên đóng
    # SỬA S3: bản ký (lớn = H) làm A⁺ rỗng khi KTC đối xứng; nay có Δ cho A⁺ ở mọi KTC đối xứng
    nua = 0.001
    nhan = {D.ket_cuc(delta_i=d, ktc_i=(d - nua, d + nua), ktc_ii=(0.0002, 0.001), ktc_iii=(0.0002, 0.001),
                      thang_iv=0.99, doi_chung_dat=True)["ket_cuc"] for d in np.linspace(0.0, 0.003, 61)}
    assert nhan == {"A", "A+", "B"}


def test_KET_CUC_B_va_C_dung_dau_va_gioi_han():
    assert _kc(0.0021)["ket_cuc"] == "B"
    assert _kc(0.0020)["ket_cuc"] != "B"                          # đúng bằng lớn (2H): không vượt
    assert _kc(-0.0012)["ket_cuc"] == "C"                         # < −nhỏ và KTC loại 0 phía âm
    assert _kc(-0.0005)["ket_cuc"] == "A"                         # đúng −nhỏ: biên đóng của A
    assert _kc(-0.0006, ktc_i=(-0.0020, -0.0001))["ket_cuc"] == "C"          # KTC lệch loại 0 từ phía âm
    assert _kc(-0.0006, ktc_i=(-0.0020, 0.0000))["ket_cuc"] == "A"           # cận trên đúng 0: chưa loại 0


def test_KET_CUC_nguong_suy_ra_tu_nua_be_rong_khong_go_tay():
    kq = _kc(0.0, nua=0.004)
    assert kq["nguong_nho"] == pytest.approx(0.002) and kq["nguong_lon"] == pytest.approx(0.008)
    assert (D.HE_SO_NHO, D.HE_SO_LON) == (0.5, 2.0)


def test_KET_CUC_toan_phan_mot_nhan_duy_nhat_va_ca_bon_nhan_deu_toi_duoc():
    """SỬA S3: quét lưới — đúng MỘT nhãn trong {K0, A, A+, B, C}, không còn nhãn "không phân loại được"/"mâu thuẫn", và A, A⁺, B, C
    đều tới được (không nhãn nào chết)."""
    thay = set()
    nua = 0.001
    for delta, lo_lech, lii, liii, th in itertools.product(
            np.linspace(-0.004, 0.004, 33), (-1.5, -0.5, 0.0, 0.5, 1.5), (0, 1, -1), (0, 1, -1), (0.5, 0.96)):
        ktc_i = (delta - nua * (1 + 0.5 * lo_lech), delta + nua * (1 - 0.3 * lo_lech))
        k = lambda c: (-0.001, 0.001) if c == 0 else ((0.0002, 0.001) if c == 1 else (-0.001, -0.0002))  # noqa: E731
        kq = D.ket_cuc(delta_i=delta, ktc_i=ktc_i, ktc_ii=k(lii), ktc_iii=k(liii), thang_iv=th, doi_chung_dat=True)
        assert kq["khop"] == [kq["ket_cuc"]] and kq["ket_cuc"] in ("A", "A+", "B", "C")
        assert (kq["ly_do_A"] is not None) == (kq["ket_cuc"] == "A")
        thay.add(kq["ket_cuc"])
    assert thay == {"A", "A+", "B", "C"}
    assert not hasattr(D, "KET_CUC_KHE") and not hasattr(D, "KET_CUC_MAU_THUAN")


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
        nam = kq["nua_h_quy_nam"]
        assert nam["diem_pt_von_moi_nam"] == pytest.approx(nam["nua_be_rong_ktc_i"] * D.NGAY_NAM * 100)
        assert nam["diem_pt_dang_dau_tu_moi_nam"] == pytest.approx(nam["diem_pt_von_moi_nam"] / nam["phoi_trung_binh"])
    assert cls[0.0]["ket_cuc"]["ket_cuc"] == "A"
    assert cls[0.01]["delta"]["i"]["delta"] > cls[0.0]["delta"]["i"]["delta"] + 1e-4
    assert cls[0.01]["ket_cuc"]["ket_cuc"] in ("B", "A+")
    assert cls[0.01]["delta"]["i"]["delta"] > cls[0.01]["ket_cuc"]["nguong_lon"]


def test_CHAY_KET_QUA_K0_khi_doi_chung_truot():
    M, s = _tong_hop_co_loi_the(0.0)
    kq = D.chay_ket_qua(M, s, s, s, PHI, doi_chung_dat=False, so_luot=20)
    assert kq["ket_cuc"]["ket_cuc"] == "K0"


# ── khoá: lượt chạy dữ liệu thật bị khoá ở Lát 4a ─────────────────────────────────────────
def test_KHOA_hang_so_cua_lat_4b():
    """Giá trị HIỆN TẠI của khoá: False ngoài đúng lượt chạy duy nhất của BƯỚC 253 (commit mở khoá riêng, commit khoá lại riêng)."""
    assert D.CHO_PHEP_DOC_KET_QUA_THAT is True        # commit MO KHOA (BUOC 253); commit khoa lai dua ve False


def test_KHOA_hai_khoa_doc_lap_khong_doc_ket_qua_that_khi_thieu_mot(monkeypatch, capsys):
    monkeypatch.setattr(D, "CHO_PHEP_DOC_KET_QUA_THAT", False)       # không phụ thuộc giá trị hằng số của commit
    def bom(*a, **k):
        raise AssertionError("khong duoc nap du lieu khi khoa")
    monkeypatch.setattr(D, "nap_cache", bom)
    monkeypatch.setattr(D, "chay_ket_qua", bom)
    monkeypatch.setattr(D, "chay_lat_4b", bom)
    assert D.main(["ket-qua", "--cache", "x"]) == 3
    assert D.main(["ket-qua", "--cache", "x", "--xac-nhan", D.CAU_XAC_NHAN_LAT_4B]) == 3          # câu đúng nhưng cờ khoá
    monkeypatch.setattr(D, "CHO_PHEP_DOC_KET_QUA_THAT", True)
    assert D.main(["ket-qua", "--cache", "x", "--xac-nhan", "sai"]) == 3                          # cờ mở nhưng câu sai
    assert "TỪ CHỐI" in capsys.readouterr().out


def test_KHOA_chay_ket_qua_chi_duoc_goi_tu_test_va_mot_ham_khoa():
    """Gác AST (Lát 4b, BƯỚC 253): ngoài định nghĩa, `chay_ket_qua` chỉ được gọi BÊN TRONG `chay_lat_4b`; `chay_lat_4b` chỉ được gọi
    từ `lenh_ket_qua`, SAU câu lệnh khoá đầu hàm; và `lenh_ket_qua` phải đọc cả hai khoá TRƯỚC mọi dòng khác."""
    cay = ast.parse(DUONG.read_text(encoding="utf-8"))

    def goi_trong(ten_ham_goi):
        ra = []
        for ham in (n for n in cay.body if isinstance(n, ast.FunctionDef)):
            for n in ast.walk(ham):
                if isinstance(n, ast.Call) and getattr(n.func, "id", None) == ten_ham_goi:
                    ra.append(ham.name)
        return ra
    dong_goi = goi_trong("chay_ket_qua")
    assert dong_goi and set(dong_goi) == {"chay_lat_4b"}                       # quần thể KHÁC RỖNG (lỗi 66)
    assert goi_trong("chay_lat_4b") == ["lenh_ket_qua"]
    assert goi_trong("lenh_ket_qua") == ["main"]
    lk = next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == "lenh_ket_qua")
    thuc0 = [s for s in lk.body if not (isinstance(s, ast.Expr) and isinstance(getattr(s, "value", None), ast.Constant))]
    assert len(thuc0) >= 2 and isinstance(thuc0[0], ast.If)
    assert not [n for n in ast.walk(thuc0[0]) if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "chay_lat_4b"]
    assert [n for s in thuc0[1:] for n in ast.walk(s) if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "chay_lat_4b"]
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
    import mo_ta_cau_truc_gia as MT
    goc = MT.lat_lai(df, r)
    assert set(goc) == set(kq)
    for k, v in kq.items():
        assert v["lat_lai_sau_su_kien_nguoc"] == goc[k].get("su_kien_nguoc", 0)
        assert v["lat_lai_dong_cua_qua_moc"] == goc[k].get("dong_cua_quay_lai", 0)
    assert any(goc[k].get("su_kien_nguoc", 0) != goc[k].get("dong_cua_quay_lai", 0) for k in goc)    # hai định nghĩa KHÁC nhau


# ── bổ sung sau vòng đột biến thứ nhất ────────────────────────────────────────────────────
def test_DONG_CO_mot_ma_het_vung_som_khong_tinh_phi_hai_lan_va_khong_ghi_sau_vung():
    vung = np.ones((8, 2), dtype=bool)
    vung[5:, 0] = False                                            # mã 0 hết vùng sau phiên 4; mã 1 chạy hết
    M = _mt(np.full((8, 2), 0.01), np.full((8, 2), 0.01), vung=vung, tb=np.full((8, 2), 0.002))
    mt = np.ones((1, 8, 2))
    kq = D.chay_dong_co(mt, M, PHI)
    ca_hai = kq["chi_phi"].sum() * D.SO_MA
    # mã 0: vào (PHI) + đóng cuối vùng (PHI + 0,002); mã 1: vào (PHI) + đóng cuối vùng (PHI + 0,002)
    assert ca_hai == pytest.approx(2 * (2 * PHI + 0.002))
    assert kq["phoi"][0, 5:].sum() * D.SO_MA == pytest.approx(3 * 1.0)          # chỉ mã 1 còn nắm, 3 phiên


def test_SMA200_khong_tinh_trung_binh_rieng_phan_khi_chua_du_200_phien():
    dong = 10.0 * 1.001 ** np.arange(260)                           # luôn tăng: SMA luôn dưới giá
    s = D.trang_thai_sma200(dong)
    assert not s[:199].any() and s[199:].all()


def test_TSMOM_dau_lon_khac_chi_so_duong_khi_cua_so_ngan_len_dai_xuong():
    dong = np.concatenate([10.0 * 0.995 ** np.arange(280), 10.0 * 0.995 ** 279 * 1.001 ** np.arange(1, 25)])
    w = D.trong_so_tsmom(dong)
    assert dong[-1] > dong[-22] and dong[-1] < dong[-64] and dong[-1] < dong[-253]        # +1, −1, −1
    # tổng dấu −1/3 → cắt 0; nếu chỉ đếm "tăng" (bỏ dấu âm) sẽ ra 1/3
    assert w[-1] == 0.0


def test_KET_CUC_bien_chinh_xac_dung_so_nhi_phan():
    ii_loai = (0.1, 0.9)
    k = lambda **kw: D.ket_cuc(doi_chung_dat=True, ktc_iii=(-1.0, 1.0), thang_iv=0.99, **kw)["ket_cuc"]  # noqa: E731
    # KTC của Δ_(i) = (−1, 1): nửa bề rộng 1 → nhỏ 0,5, lớn 2 (SỬA S3: bản ký lớn = 1)
    assert k(delta_i=0.5, ktc_i=(-1.0, 1.0), ktc_ii=ii_loai) == "A"                      # |Δ| = nhỏ: biên đóng của A
    assert k(delta_i=-0.5, ktc_i=(-1.0, 1.0), ktc_ii=ii_loai) == "A"
    assert k(delta_i=0.5, ktc_i=(0.5, 2.5), ktc_ii=ii_loai) == "A"                        # Δ = nhỏ, A+ mở (nhỏ, lớn]: KHÔNG A+
    assert k(delta_i=1.0, ktc_i=(0.5, 2.5), ktc_ii=ii_loai) == "A+"                       # trong (nhỏ, lớn]
    assert k(delta_i=2.0, ktc_i=(0.5, 2.5), ktc_ii=ii_loai) == "A+"                       # Δ = lớn: biên đóng của A+
    assert k(delta_i=2.0001, ktc_i=(0.5, 2.5), ktc_ii=ii_loai) == "B"
    assert k(delta_i=-0.125, ktc_i=(-1.0, -0.5), ktc_ii=ii_loai) == "A"                   # nhỏ = 0,125 = |Δ| → A, không C
    assert k(delta_i=-0.1251, ktc_i=(-1.0, -0.5), ktc_ii=ii_loai) == "C"


def test_PHAN_QUYET_TIEM_can_ca_hai_ve_va_dung_bien():
    assert D.phan_quyet_tiem(0.0, 0.8) and D.phan_quyet_tiem(0.10, 1.0)
    assert not D.phan_quyet_tiem(0.11, 1.0)                        # ô không tiêm KÊU
    assert not D.phan_quyet_tiem(0.0, 0.79)                        # ô K0 (20× rào) không bắt đủ
    assert not D.phan_quyet_tiem(1.0, 0.0)


def test_KHOANG_WILSON_va_MDE_80_dung_bien():
    lo, hi = D.khoang_wilson(0, 100)
    assert lo == 0.0 and 0.03 < hi < 0.04                          # 0/100 → [0 ; ~3,7%]
    lo, hi = D.khoang_wilson(50, 100)
    assert lo == pytest.approx(0.4038, abs=1e-3) and hi == pytest.approx(0.5962, abs=1e-3) and (lo + hi) / 2 == pytest.approx(0.5)
    assert D.khoang_wilson(1, 0) == (0.0, 1.0)
    o = {str(h): {"he_so_rao": h, "ty_le": t} for h, t in ((0.0, 0.05), (5.0, 0.79), (10.0, 0.80), (20.0, 1.0))}
    assert D.mde_80(o) == 10.0                                      # biên đóng: đúng 80% đủ; 79% chưa
    assert D.mde_80({"0.0": {"he_so_rao": 0.0, "ty_le": 0.05}}) is None


def test_THUY_TRIEU_CHUOI_khop_trang_thai_dow_o_MOI_nen_va_bool_dung_la_tang():
    df = _khung(500, 11)
    r = C.doc_cau_truc(df, he_so_gia=1000.0, san="HOSE")
    chuoi = D.thuy_trieu_chuoi(r)
    assert all(chuoi[t] == C.trang_thai_dow(r, t).thuy_trieu for t in range(500))
    s = D.trang_thai_dow(df, 1000.0, "HOSE")
    assert list(s) == [x == C.TANG for x in chuoi] and 0 < s.mean() < 0.9
    assert not s[:20].any() and chuoi[0] == C.CHUA_DU


def test_DUNG_MA_TRAN_nhan_dung_kich_tran_kich_san_va_truot_theo_chieu():
    df = _khung(40, 51)
    df.loc[10, ["open", "high", "low", "close"]] = df.loc[9, "close"] * 1.07           # kịch trần HOSE (7%)
    df.loc[20, ["open", "high", "low", "close"]] = df.loc[19, "close"] * 0.93          # kịch sàn
    M = D.dung_ma_tran({"A": (df, 1000.0, "HOSE")}, {"A": np.ones(40, bool)}, von_vnd=1e9)
    assert list(np.flatnonzero(M.khoa_tran[:, 0])) == [10] and list(np.flatnonzero(M.khoa_san[:, 0])) == [20]
    assert (M.truot_mua >= 0).all() and (M.truot_ban >= 0).all() and M.truot_mua.sum() > 0
    assert M.qua_dem[11, 0] == pytest.approx(df.loc[11, "open"] / df.loc[10, "close"] - 1)
    assert M.trong_phien[11, 0] == pytest.approx(df.loc[11, "close"] / df.loc[11, "open"] - 1)
    assert M.cuoi_vung[39, 0] and M.cuoi_vung.sum() == 1


def test_COT_THO_bang_danh_muc_sau_phi_tru_rổ_o_cung_muc_dau_tu_toi_da():
    rng = np.random.default_rng(2)
    M = _mt(rng.normal(0, 0.01, (30, 3)), rng.normal(0, 0.01, (30, 3)), tb=np.full((30, 3), 0.001))
    s = (rng.random((1, 30, 3)) > 0.5).astype(float)
    kq = D.chay_dong_co(s, M, PHI)
    ro = D.ro_trung_binh(M)
    tho = D.cot_tho(kq, ro, M)[0]
    assert np.allclose(tho, kq["ret"][0] - kq["chi_phi"][0] - 3 / D.SO_MA * ro)


def test_CHUAN_i_la_ro_tru_hai_nua_phi_khong_truot_khong_khoa_ke_ca_khi_co_khoa_va_truot():
    rng = np.random.default_rng(3)
    kt = np.zeros((30, 3), bool)
    kt[4, :] = True
    M = _mt(rng.normal(0, 0.01, (30, 3)), rng.normal(0, 0.01, (30, 3)), khoa_tran=kt,
            tm=np.full((30, 3), 0.01), tb=np.full((30, 3), 0.01))
    x = D.chuan_i(M, PHI, D.ro_trung_binh(M))
    assert x.sum() == pytest.approx(-2 * PHI * 3 / D.SO_MA)
    assert np.count_nonzero(x) == 2 and x[-1] == pytest.approx(-PHI * 3 / D.SO_MA)      # chỉ ngày vào và ngày đóng cuối vùng


def test_THANG_TONG_HOP_lay_so_nho_hon_cua_hai_ban():
    assert D.thang_tong_hop({"dat": {"thang": 0.99}, "dich": {"thang": 0.90}}) == 0.90
    assert D.thang_tong_hop({"dat": {"thang": 0.91}, "dich": {"thang": 0.99}}) == 0.91


def _m_tiem(nhieu, gai=0.0, T=500, N=6, seed=9):
    rng = np.random.default_rng(seed)
    s = np.zeros((T, N))
    for j in range(N):
        s[:, j] = (np.arange(T) + 53 * j) % 120 < 45
    truoc = np.vstack([np.zeros((1, N)), s[:-1]])
    M = _mt(np.zeros((T, N)), rng.normal(0, nhieu, (T, N)) + gai * truoc)
    return M, s


LUOI_NHO = (0.0, 0.5, 20.0)


def test_DOI_CHUNG_iii_bat_duoc_o_K0_khi_nhieu_nho_va_im_o_he_so_0_va_bao_MDE():
    M, s = _m_tiem(1e-6)
    kq = D.doi_chung_iii(M, s, PHI, so_lap=12, so_ngan_hang=60, he_so=LUOI_NHO)
    assert kq["rao_hoa_von"] > 0 and kq["phoi_trung_binh"] > 0
    assert kq["o"]["0.0"]["ty_le"] <= 0.10 and kq["o"][str(D.HE_SO_K0)]["ty_le"] >= 0.8 and kq["dat"]
    m = kq["mde_80"]
    assert m["he_so_rao"] <= D.HE_SO_K0 and m["tiem_moi_don_vi_ngay"] == pytest.approx(m["he_so_rao"] * kq["rao_hoa_von"])
    assert m["diem_pt_dang_dau_tu_moi_nam"] == pytest.approx(m["tiem_moi_don_vi_ngay"] * D.NGAY_NAM * 100)
    assert m["diem_pt_von_moi_nam"] == pytest.approx(m["diem_pt_dang_dau_tu_moi_nam"] * kq["phoi_trung_binh"])
    assert all(0 <= v["wilson"][0] <= v["ty_le"] <= v["wilson"][1] <= 1 for v in kq["o"].values())


def test_DOI_CHUNG_iii_truot_khi_nhieu_rat_lon_khong_bat_noi_ngay_ca_20_lan_rao():
    M, s = _m_tiem(0.3)
    kq = D.doi_chung_iii(M, s, PHI, so_lap=12, so_ngan_hang=60, he_so=LUOI_NHO)
    assert kq["o"][str(D.HE_SO_K0)]["ty_le"] < 0.8 and not kq["dat"] and kq["mde_80"] is None


def test_DOI_CHUNG_iii_nua_rao_khong_con_la_dieu_kien_K0():
    """SỬA S2: ở nhiễu vừa phải, nửa rào KHÔNG bắt được nhưng 20× rào bắt được ⇒ ĐẠT (câu hỏi sức mạnh chỉ BÁO, không làm K0)."""
    M, s = _m_tiem(0.01)
    kq = D.doi_chung_iii(M, s, PHI, so_lap=12, so_ngan_hang=60, he_so=LUOI_NHO)
    assert kq["o"]["0.5"]["ty_le"] < 0.8 <= kq["o"][str(D.HE_SO_K0)]["ty_le"] and kq["dat"]


def test_DOI_CHUNG_iii_luoi_thieu_o_0_hoac_o_K0_la_loi():
    M, s = _m_tiem(1e-6)
    for luoi in ((0.5, 20.0), (0.0, 0.5, 1.0)):
        with pytest.raises(ValueError):
            D.doi_chung_iii(M, s, PHI, so_lap=2, so_ngan_hang=10, he_so=luoi)


def test_DOI_CHUNG_iii_nen_roi_khoi_nhan_loi_the_gan_voi_trang_thai_khong_duoc_goi_la_tiem():
    """Lỗi 94: nền phải RỜI khỏi nhãn. Ở đây lợi nhuận THẬT dính chặt trạng thái (gai); nếu nền không dịch vòng thì ô
    "không tiêm gì" sẽ kêu (đo lại chính nó). Dịch vòng ⇒ ô ấy im."""
    M, s = _m_tiem(1e-6, gai=4e-5)
    kq = D.doi_chung_iii(M, s, PHI, so_lap=12, so_ngan_hang=60, he_so=LUOI_NHO)
    assert kq["o"]["0.0"]["ty_le"] <= 0.10 and kq["dat"]


def test_TRONG_KHOANG_SE_bien_dong_2_sai_so_chuan():
    assert D.trong_khoang_se(2.0, 1.0) and D.trong_khoang_se(-2.0, 1.0) and not D.trong_khoang_se(2.0001, 1.0)
    assert D.trong_khoang_se(0.0, 0.0) and not D.trong_khoang_se(1e-9, 0.0)


def test_KY_VONG_XAP_XI_CU_dap_so_dung_tay():
    """Mã 0 luôn trong thị trường và trôi +1%/ngày; mã 1 luôn ngoài và trôi 0: p = (1, 0), m = (0,01 ; 0), r_rổ = 0,005.
    Kỳ vọng = (1×0,01 + 0×0)/71 − (1/71)×0,005 = 0,005/71. Quên trừ phần rổ cho 0,01/71."""
    T = 100
    M = _mt(np.zeros((T, 2)), np.stack([np.full(T, 0.01), np.zeros(T)], axis=1))
    s = np.stack([np.ones(T), np.zeros(T)], axis=1)
    assert D.ky_vong_xap_xi_cu(M, s) == pytest.approx(0.005 / D.SO_MA)


def test_DOI_CHUNG_iii_nen_la_ban_DICH_VONG_khong_phai_dat_ngau_nhien():
    """Gác AST (lỗi 94): nền của phép hiệu chuẩn phải có cùng bản chất với lượt tiêm (dịch vòng), gọi `ngau_nhien(..., "dich", ...)`."""
    cay = ast.parse(DUONG.read_text(encoding="utf-8"))
    ham = next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == "doi_chung_iii")
    goi = [n for n in ast.walk(ham) if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "ngau_nhien"]
    assert len(goi) == 1 and goi[0].args[3].value == "dich"
    dv = [n for n in ast.walk(ham) if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "dich_vong"]
    assert len(dv) == 1                                           # lượt tiêm cũng dịch vòng


# ── cấu hình CLI ──────────────────────────────────────────────────────────────────────────
def test_CLI_cau_hinh_ktc_thoat_0_va_in_khop(capsys):
    assert D.main(["cau-hinh-ktc"]) == 0
    assert "KHỚP" in capsys.readouterr().out


# ── Lát 4b (BƯỚC 253): các hàm của lượt chạy duy nhất, trên cache TỔNG HỢP (không test nào đọc cache thật) ─────────────
def test_THANG_CUA_SO_RO_dap_so_dung_tay_mo_cua_t_cong_1_toi_dong_cua_t_cong_do_dai():
    dong = np.array([[10, 20], [11, 21], [12, 22], [13, 23], [14, 24], [15, 25]], float)
    M = _mt(np.zeros((6, 2)), np.zeros((6, 2)))
    M.dong = dong                                                # mở = đóng (lợi nhuận trong phiên 0)
    th = D.thang_cua_so_ro(M, 2)
    assert th[0] == pytest.approx(((12 / 11 - 1) + (22 / 21 - 1)) / 2)
    assert th[3] == pytest.approx(((15 / 14 - 1) + (25 / 24 - 1)) / 2)
    assert np.isnan(th[4]) and np.isnan(th[5])
    vung = np.ones((6, 2), bool)
    vung[2, 1] = False                                           # mã 1 ra khỏi vùng ở cuối cửa sổ của t = 0
    M2 = _mt(np.zeros((6, 2)), np.zeros((6, 2)), vung=vung, cuoi=np.zeros((6, 2), bool))
    M2.dong = dong
    assert D.thang_cua_so_ro(M2, 2)[0] == pytest.approx(12 / 11 - 1)        # chỉ mã 0 còn ở cả hai đầu
    mo = _mt(np.zeros((6, 1)), np.full((6, 1), 0.1))
    mo.dong = dong[:, :1]                                        # đóng/mở − 1 = 0,1 → mở = đóng / 1,1
    assert D.thang_cua_so_ro(mo, 2)[0] == pytest.approx(12 / (11 / 1.1) - 1)


def test_CHUAN_II_III_xep_hang_cung_ngay_toan_cuc_va_nhan_qua():
    chuoi = {f"M{k}": (_khung(420, k), 1000.0, "HOSE") for k in (3, 4)}          # hạt 3, 4: giá nằm trên SMA200 một phần dài
    M = D.dung_ma_tran(chuoi, {m: np.ones(420, dtype=bool) for m in chuoi}, von_vnd=1e9)
    sma, ts = D.chuan_ii_iii(M, chuoi)
    assert sma.shape == ts.shape == M.vung.shape
    for j, m in enumerate(M.ma):
        dong = chuoi[m][0]["close"].to_numpy(float)
        assert np.array_equal(sma[:, j], D.trang_thai_sma200(dong).astype(float))
        assert np.allclose(ts[:, j], D.trong_so_tsmom(dong))
        assert np.array_equal(sma[:300, j], D.trang_thai_sma200(dong[:300]).astype(float))       # cắt đuôi không đổi phần đầu
        assert np.allclose(ts[:300, j], D.trong_so_tsmom(dong[:300]))
        assert sma[:199, j].sum() == 0.0
        assert set(np.round(np.unique(ts[:, j]), 9)) <= {0.0, round(1 / 3, 9), round(2 / 3, 9), 1.0}
    assert sma.sum() > 0 and ts.sum() > 0                           # quần thể KHÁC RỖNG (lỗi 66)


def test_H2_MO_TA_chuyen_dung_thang_cua_so_ro_theo_ngay_cua_ma():
    chuoi, vung, M = _ma_tran_tong_hop(n=900, so_ma=2)
    bat = []
    goc = D.su_kien_h2

    def ghi(df, he, san, thang, rng, *a, **k):
        bat.append(np.array(thang))
        return goc(df, he, san, thang, rng, *a, **k)
    import unittest.mock as um
    with um.patch.object(D, "su_kien_h2", ghi):
        ds = D.h2_mo_ta(M, chuoi, vung)
    assert len(bat) == 2 and ds["so_su_kien"] > 0
    assert ds[C.TANG]["n"] + ds[C.GIAM]["n"] == ds["so_su_kien"]
    mo = [chuoi[k][0]["open"].to_numpy(float) for k in M.ma]
    dg = [chuoi[k][0]["close"].to_numpy(float) for k in M.ma]
    for j in range(2):
        for i in (0, 100, 500, 870):
            mong = np.mean([dg[q][i + 21] / mo[q][i + 1] - 1 for q in range(2)])
            assert bat[j][i] == pytest.approx(mong)
        assert np.isnan(bat[j][900 - 21:]).all() and len(bat[j]) == 900


def test_MO_TA_BAO_KEM_khop_dem_truc_tiep_tren_bang_da_cat():
    chuoi, vung, _ = _ma_tran_tong_hop(n=700, so_ma=1)
    m = next(iter(chuoi))
    vung[m][600:] = False                                         # vùng sạch = 600 nến đầu
    kq = D.mo_ta_bao_kem(chuoi, vung)
    df = chuoi[m][0].iloc[:600].reset_index(drop=True)
    r = C.doc_cau_truc(df, he_so_gia=1000.0, san="HOSE")
    assert kq["so_nam_ma"] == pytest.approx(600 / 252)
    for cap in C.CAPS:
        assert kq["su_kien_dem"][cap].get(C.CHOCH, 0) == sum(1 for e in r.su_kien if e.cap == cap and e.loai == C.CHOCH)
        tre = [p.chi_so_biet - p.chi_so_xay_ra for p in r.nhat_ky if p.cap == cap]
        assert kq["do_tre_trung_vi"][cap] == float(np.median(tre)) and kq["do_tre_p90"][cap] == float(np.percentile(tre, 90))
        assert kq["su_kien_moi_ma_moi_nam"][cap][C.BOS] == pytest.approx(kq["su_kien_dem"][cap][C.BOS] / (600 / 252))
    assert set(kq["lat_lai_3_phien"]) == set(D.lat_lai_hai_dinh_nghia(df, r))
    assert all(v["n"] >= v["lat_lai_sau_su_kien_nguoc"] for v in kq["lat_lai_3_phien"].values())


@pytest.fixture
def cache_tong_hop(tmp_path):
    ma = list(D.CUSTOM_WATCHLIST_SYMBOLS[:3])
    for k, m in enumerate(ma + ["VNINDEX"]):
        df = _khung(800, 60 + k)
        if m == "VNINDEX":
            df[["open", "high", "low", "close"]] *= 60.0
        df.to_csv(tmp_path / f"{m}.csv", index=False)
    return tmp_path, ma, {m: _khung(800, 0)["time"].iloc[600] for m in ma}


def _bam(cache):
    import mo_ta_cau_truc_gia as MT
    return MT.bam_cache(cache)["sha256"]


def _chay_4b(cache_tong_hop, monkeypatch, *, dat=True, **kw):
    cache, ma, moc = cache_tong_hop
    monkeypatch.setattr(D, "doi_chung_tat_ca", lambda cache, ra=print, so_luot=None: {"tat_ca_dat": dat})
    dong = []
    if "bam_ky" not in kw:                                  # KHÔNG setdefault: nó tính đối số ngay cả khi đã có khoá
        kw["bam_ky"] = _bam(cache)
    out = D.chay_lat_4b(cache, ra=dong.append, so_luot=20, ma_ds=ma, moc=moc, **kw)
    return out, dong


def test_CHAY_LAT_4B_tong_hop_in_ket_cuc_TRUOC_bao_kem_va_ghi_json(cache_tong_hop, monkeypatch, tmp_path):
    ghi = tmp_path / "kq.json"
    out, dong = _chay_4b(cache_tong_hop, monkeypatch, ghi=ghi)
    vt = {k: next(i for i, x in enumerate(dong) if x.startswith(k)) for k in ("KẾT CỤC:", "== BÁO KÈM", "KẾT CỤC CUỐI", "băm cache SAU")}
    assert vt["KẾT CỤC:"] < vt["== BÁO KÈM"] < vt["băm cache SAU"] < vt["KẾT CỤC CUỐI"]
    nhan = out["ket_cuc_cuoi"]["ket_cuc"]
    assert nhan in ("A", "A+", "B", "C") and nhan == out["ket_qua"]["ket_cuc"]["ket_cuc"] == out["ket_cuc_truoc_bam_sau"]
    bk = out["bao_kem"]
    assert not [k for k, v in bk.items() if isinstance(v, dict) and "loi" in v], bk
    assert len(bk["luoi_10_o"]) == 10 and sum(o["mac_dinh"] for o in bk["luoi_10_o"]) == 1
    assert bk["nhay_phi_0_76"]["phi_pct"] == 0.76 and "ghi_chu" in bk["vung_sau_moc"]
    assert out["bam_truoc_chay"]["sha256"] == out["bam_sau_chay"]["sha256"] == out["bam_ky"]
    kq_file = json.loads(ghi.read_text(encoding="utf-8"))
    assert kq_file["ket_cuc_cuoi"]["ket_cuc"] == nhan and set(kq_file["bao_kem"]) == set(bk)
    assert any(x.startswith("cấu hình KTC đã dùng ở Δ_(i): KHỚP") for x in dong)
    assert any(x.startswith(f"KẾT CỤC: {nhan}") for x in dong) and f"KẾT CỤC CUỐI (sau băm cache): {nhan}" in dong      # dòng in = nhãn tính ra
    assert bk["vung_sau_moc"]["so_ngay"] == 200 and out["ket_qua"]["so_ngay"] == 600           # sạch 600 nến đầu, sau mốc 200 nến cuối
    nhay = bk["nhay_phi_0_76"]["delta_i"]
    assert nhay["delta"] < out["ket_qua"]["delta"]["i"]["delta"]                              # phí cao hơn → Dow (nhiều chuyến hơn rổ) kém đi


def test_CHAY_LAT_4B_dung_hat_0_va_cung_so_luot_nhu_chay_ket_qua_truc_tiep(cache_tong_hop, monkeypatch):
    out, _ = _chay_4b(cache_tong_hop, monkeypatch)
    cache, ma, moc = cache_tong_hop
    chuoi, vung, s = D.nap_cache(cache, ma, moc, vung="sach")
    M = D.dung_ma_tran(chuoi, vung)
    sma, ts = D.chuan_ii_iii(M, chuoi)
    truc_tiep = D.chay_ket_qua(M, D.s_matran(M, chuoi, s), sma, ts, D.phi_nua(), doi_chung_dat=True, so_luot=20, hat=D.HAT)
    assert out["hat"] == D.HAT == 0
    assert out["ket_qua"]["ngau_nhien"] == truc_tiep["ngau_nhien"] and out["ket_qua"]["thang_iv"] == truc_tiep["thang_iv"]
    assert out["ket_qua"]["delta"]["i"]["delta"] == truc_tiep["delta"]["i"]["delta"]


def test_CHAY_LAT_4B_ban_khong_khoa_bien_that_su_tat_khoa_cua_dong_co():
    """Gác AST: mục 'bản không có sự kiện nến khoá biên' gọi động cơ với `khoa=False` (cả hai bản trùng nhau trên dữ liệu
    không có nến kịch trần / sàn, nên so giá trị không bắt được việc quên cờ)."""
    cay = ast.parse(DUONG.read_text(encoding="utf-8"))
    ham = next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == "chay_lat_4b")
    kk = next(n for n in ast.walk(ham) if isinstance(n, ast.FunctionDef) and n.name == "khong_khoa")
    goi = [n for n in ast.walk(kk) if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "chay_dong_co"]
    assert len(goi) == 1
    assert {k.arg: getattr(k.value, "value", None) for k in goi[0].keywords}.get("khoa") is False


def test_CHAY_LAT_4B_luoi_mac_dinh_trung_delta_i_cua_ket_qua(cache_tong_hop, monkeypatch):
    out, _ = _chay_4b(cache_tong_hop, monkeypatch)
    o = next(o for o in out["bao_kem"]["luoi_10_o"] if o["mac_dinh"])
    assert (o["ho"], tuple(o["tham_so"])) == C.MAC_DINH
    assert o["delta"] == pytest.approx(out["ket_qua"]["delta"]["i"]["delta"], abs=0, rel=1e-12)


def test_CHAY_LAT_4B_bam_ky_lech_hoac_doi_chung_truot_thi_K0(cache_tong_hop, monkeypatch):
    out, _ = _chay_4b(cache_tong_hop, monkeypatch, bam_ky="0" * 64)
    assert out["ket_cuc_cuoi"]["ket_cuc"] == "K0" == out["ket_cuc_truoc_bam_sau"]            # dòng in sớm cũng là K0, không lộ nhãn khác
    out, _ = _chay_4b(cache_tong_hop, monkeypatch, dat=False)
    assert out["ket_cuc_cuoi"]["ket_cuc"] == "K0"


def test_CHAY_LAT_4B_bam_sau_lech_thi_ket_cuc_cuoi_K0_du_ket_cuc_dau_khac(cache_tong_hop, monkeypatch):
    import mo_ta_cau_truc_gia as MT
    that = MT.bam_cache
    ky = that(cache_tong_hop[0])["sha256"]
    dem = {"n": 0}

    def gia(cache):
        dem["n"] += 1
        r = dict(that(cache))
        if dem["n"] >= 2:
            r["sha256"] = "f" * 64
        return r
    monkeypatch.setattr(MT, "bam_cache", gia)
    out, dong = _chay_4b(cache_tong_hop, monkeypatch, bam_ky=ky)
    assert out["ket_cuc_truoc_bam_sau"] != "K0" and out["ket_cuc_cuoi"]["ket_cuc"] == "K0"
    assert any("LỆCH → K0" in x for x in dong)


def test_CHAY_LAT_4B_mot_muc_bao_kem_hong_khong_lam_mat_ket_cuc_va_muc_sau(cache_tong_hop, monkeypatch):
    def hong(*a, **k):
        raise RuntimeError("gai loi")
    monkeypatch.setattr(D, "luoi_h1", hong)
    out, dong = _chay_4b(cache_tong_hop, monkeypatch)
    bk = out["bao_kem"]
    assert "gai loi" in bk["luoi_10_o"]["loi"] and any("BÁO KÈM LỖI" in x for x in dong)
    assert out["ket_cuc_cuoi"]["ket_cuc"] in ("A", "A+", "B", "C") and "delta" in bk["vung_sau_moc"]


def test_LENH_KET_QUA_sau_hai_khoa_goi_chay_lat_4b_dung_doi_so(monkeypatch):
    goi = []
    monkeypatch.setattr(D, "chay_lat_4b", lambda cache, **k: goi.append((cache, k)) or {})
    monkeypatch.setattr(D, "CHO_PHEP_DOC_KET_QUA_THAT", True)
    assert D.main(["ket-qua", "--cache", "x", "--xac-nhan", D.CAU_XAC_NHAN_LAT_4B, "--ghi", "kq.json"]) == 0
    assert goi == [(Path("x"), {"ghi": "kq.json"})]
    goi.clear()
    assert D.main(["ket-qua", "--cache", "x", "--xac-nhan", "sai"]) == 3 and goi == []


def test_IN_KET_QUA_in_nhan_va_cac_con_so_cua_ket_qua():
    M, s = _tong_hop_co_loi_the(0.0)
    sma = (np.arange(M.vung.shape[0])[:, None] % 5 < 3) & np.ones(M.vung.shape, bool)
    ts = np.clip((np.arange(M.vung.shape[0])[:, None] % 9) / 9.0, 0, 1) * np.ones(M.vung.shape)
    kq = D.chay_ket_qua(M, s, sma.astype(float), ts, PHI, doi_chung_dat=True, so_luot=20)
    dong = []
    D.in_ket_qua(kq, dong.append)
    txt = "\n".join(dong)
    assert f"KẾT CỤC: {kq['ket_cuc']['ket_cuc']}" in txt and "Δ_(i) rổ" in txt and "(iv) đặt ngẫu nhiên" in txt
    assert f"{kq['nua_h_quy_nam']['diem_pt_von_moi_nam']:.2f} điểm % vốn" in txt
    assert "ngưỡng nhỏ = H/2" in txt and "cấu hình KTC đã dùng ở Δ_(i): KHỚP" in txt
    for nhan in ("B", "C", "A+", "K0"):                                  # nhãn in ra là nhãn của kết quả, không phải chữ gõ cứng
        d2 = []
        D.in_ket_qua({**kq, "ket_cuc": {**kq["ket_cuc"], "ket_cuc": nhan, "ly_do_A": None}}, d2.append)
        assert d2[-1] == f"KẾT CỤC: {nhan}"


def test_HANG_SO_khop_ky_ho_so_cache_va_ngay_khong_rong():
    assert D.BAM_CACHE_KY.startswith("acf6dca1") and len(D.BAM_CACHE_KY) == 64
    assert D.SO_MA == 71 == len(D.CUSTOM_WATCHLIST_SYMBOLS)
    assert (D.SO_LUOT_NGAU_NHIEN, D.DICH_TOI_THIEU, D.SO_LAP_TIEM, D.NGUONG_BAT_TIEM) == (1000, 252, 100, 0.8)
    assert D.CUA_SO_TSMOM == (21, 63, 252) and D.PHIEN_SMA == 200 and D.CUA_SO_SU_KIEN == 21
    assert D.HE_SO_K0 == 20.0 and D.HE_SO_LUOI_TIEM == (0.0, 0.5, 1.0, 2.0, 5.0, 7.0, 10.0, 14.0, 20.0) and D.NGUONG_THANG_A_CONG == 0.95
    assert D.phi_nua() == pytest.approx(0.0046 / 2)
