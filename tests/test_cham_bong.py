"""Gác P3a — CHẤM BÓNG ứng viên của tầng 3 (BƯỚC 144).

Người dùng chọn 29/09/2026: *"chấm bóng công khai"* — ứng viên chạy song song
với bản đang chạy trên dữ liệu CHƯA nhìn, và chỉ lên phiên bản khi qua ngưỡng
thống kê. ĐO 21 (BƯỚC 142) cho biết việc ấy HIẾM; module này không được làm
nó dễ hơn thật.

Bốn điều, mỗi điều một cách một vòng xác nhận tự khen mình:
1. Bản đang chạy là ĐIỂM ĐÃ GHI trong sổ quyết định — không tính lại. (Áp cho
   vòng XÁC NHẬN; vòng SÀNG là ngoại lệ có tên, `tools/sang_ung_vien.py`, ĐO 23.)
2. Mỗi (mã, phiên) đếm MỘT lần — sổ có dòng lặp (BƯỚC 125).
3. Phép so là so CẶP trên cùng nhãn, null hoán vị MÃ áp cho CẢ HAI điểm.
4. Ngưỡng chia cho K = TỔNG số ứng viên đã sàng, kể cả ứng viên rớt sàng.
"""
import json

import numpy as np
import pandas as pd
import pytest

import cham_bong as cb
import experiment_tran_dac_trung as E


def _tp(t=50.0, m=50.0, v=50.0, s=50.0, r=50.0):
    return {"trend_score": t, "momentum_score": m, "volume_score": v,
            "sr_score": s, "risk_score": r}


def _dong(ma, ngay, diem, tp, at, seq):
    return {"seq": seq, "at": at, "symbol": ma, "signal_date": ngay,
            "score": diem, "components": json.dumps(tp)}


# ── 1. đọc sổ quyết định ─────────────────────────────────────────────────

def test_doc_quyet_dinh_KHU_TRUNG_giu_dong_GHI_SAU_CUNG():
    rows = [_dong("FPT", "2026-09-01", 60, _tp(t=10), 100.0, 1),
            _dong("FPT", "2026-09-01 00:00:00", 61, _tp(t=20), 200.0, 2),
            _dong("HPG", "2026-09-01", 55, _tp(), 150.0, 3)]
    b = cb.doc_quyet_dinh(rows, tu_ngay="2026-08-10")
    assert len(b) == 2
    fpt = b[b["symbol"] == "FPT"].iloc[0]
    assert fpt["score"] == 61 and fpt["trend_score"] == 20
    assert fpt["ngay"] == "2026-09-01"               # 10 ký tự, bỏ hậu tố giờ


def test_doc_quyet_dinh_chi_lay_tu_MOC_tien_ve_truoc():
    rows = [_dong("FPT", "2026-08-07", 60, _tp(), 1.0, 1),
            _dong("FPT", "2026-08-10", 61, _tp(), 2.0, 2)]
    b = cb.doc_quyet_dinh(rows, tu_ngay="2026-08-10")
    assert list(b["ngay"]) == ["2026-08-10"]


def test_doc_quyet_dinh_BO_dong_THIEU_thanh_phan_va_DEM_ra():
    tp = _tp()
    del tp["volume_score"]
    rows = [_dong("FPT", "2026-09-01", 60, tp, 1.0, 1),
            {"seq": 2, "at": 2.0, "symbol": "HPG", "signal_date": "2026-09-01",
             "score": 50, "components": "{khong phai json"},
            _dong("VNM", "2026-09-01", 50, _tp(), 3.0, 3)]
    b = cb.doc_quyet_dinh(rows, tu_ngay="2026-08-10")
    assert list(b["symbol"]) == ["VNM"]
    assert b.attrs["bo"] == 2


def test_BAN_DANG_CHAY_la_diem_DA_GHI_khong_tinh_lai():
    """Điểm ghi trong sổ đã qua cả bộ nhớ hậu kiểm, harness, trọng số động —
    tính lại từ thành phần là so ứng viên với một bản KHÔNG hề chạy."""
    rows = [_dong("FPT", "2026-09-01", 77, _tp(), 1.0, 1)]
    b = cb.doc_quyet_dinh(rows, tu_ngay="2026-08-10")
    assert b.iloc[0]["score"] == 77


# ── 2. ứng viên ──────────────────────────────────────────────────────────

def test_diem_ung_vien_TRONG_SO():
    spec = {"loai": "trong_so", "trong_so": {"trend_score": 0.5, "volume_score": 0.5}}
    assert cb.diem_ung_vien(spec, _tp(t=80, v=40)) == pytest.approx(60.0)


@pytest.mark.parametrize("spec", [
    {"loai": "trong_so", "trong_so": {"trend_score": 0.5, "volume_score": 0.4}},   # tổng ≠ 1
    {"loai": "trong_so", "trong_so": {"trend_score": 1.2, "volume_score": -0.2}},  # âm
    {"loai": "trong_so", "trong_so": {"news_score": 1.0}},                         # ngoài tập
    {"loai": "ma_tuy_y", "ma": "lambda x: 1"},                                      # loại lạ
    {"loai": "trong_so", "trong_so": {}},
])
def test_spec_SAI_KHUON_bi_tu_choi(spec):
    with pytest.raises(ValueError):
        cb.kiem_spec(spec)


def test_THANH_PHAN_la_dung_nam_so_hang_cua_diem_truoc_tranh_luan():
    """`news_score` chỉ để hiện (MO-XE Tầng 2) — không cho nó vào ứng viên."""
    assert set(cb.THANH_PHAN) == {"trend_score", "momentum_score", "volume_score",
                                  "sr_score", "risk_score"}


# ── 3. phép so cặp ───────────────────────────────────────────────────────

def _bang_tong_hop(W=120, M=50, hat=0, lech=0.0):
    """Bảng dài: điểm gốc là nhiễu; ứng viên = gốc + `lech` × nhãn chuẩn hoá."""
    rng = np.random.default_rng(hat)
    ngay = [str(d.date()) for d in pd.bdate_range("2026-01-05", periods=W)]
    ma = [f"M{j:02d}" for j in range(M)]
    Y = rng.standard_normal((W, M))
    B = rng.standard_normal((W, M))
    C = B + lech * Y
    return B, C, Y


def test_so_cap_HOAN_VI_DONG_NHAT_cho_lai_DUNG_delta():
    B, C, Y = _bang_tong_hop(lech=0.3)

    class _Dong:
        def permutation(self, m):
            return np.arange(m)
    k = cb.so_cap(B, C, Y, _Dong(), so=2)
    assert k["delta"] == pytest.approx(
        E.rho_hang(C.ravel(), Y.ravel()) - E.rho_hang(B.ravel(), Y.ravel()))
    assert k["null"] == pytest.approx([k["delta"]] * 2, abs=1e-12)


def test_so_cap_null_HOAN_VI_CUNG_MOT_phep_cho_CA_HAI_diem():
    B, C, Y = _bang_tong_hop(W=40, M=9, lech=0.4, hat=3)
    p = np.array([2, 0, 1, 5, 3, 4, 8, 6, 7])
    khac = np.array([8, 7, 6, 5, 4, 3, 2, 1, 0])

    class _Co:
        """Lần gọi đầu trả `p`, mọi lần sau trả `khac` — một bản rút HAI
        hoán vị cho hai điểm sẽ lấy `khac` cho điểm thứ hai và lệch."""
        def __init__(self):
            self.n = 0

        def permutation(self, m):
            self.n += 1
            return p if self.n == 1 else khac
    v = cb.so_cap(B, C, Y, _Co(), so=1)["null"][0]
    Yp = Y[:, p]
    assert v == pytest.approx(E.rho_hang(C.ravel(), Yp.ravel())
                              - E.rho_hang(B.ravel(), Yp.ravel()), abs=1e-12)


def test_so_cap_BAT_ung_vien_that_su_tot_va_IM_voi_ung_vien_ngau_nhien():
    B, C, Y = _bang_tong_hop(lech=0.3, hat=5)
    tot = cb.so_cap(B, C, Y, np.random.default_rng(1), so=500)
    assert tot["delta"] > 0 and tot["p"] < 0.001
    # HAI PHÍA: ứng viên TỆ hơn hẳn cũng phải bị phát hiện (để thành THUA)
    xau = cb.so_cap(B, B - 0.3 * Y, Y, np.random.default_rng(2), so=500)
    assert xau["delta"] < 0 and xau["p"] < 0.001
    im = 0
    for hat in range(30):
        B, C, Y = _bang_tong_hop(lech=0.0, hat=100 + hat)
        C = np.random.default_rng(hat).standard_normal(B.shape)   # ứng viên ngẫu nhiên
        im += cb.so_cap(B, C, Y, np.random.default_rng(hat), so=300)["p"] < 0.05
    assert im <= 4                     # D.nguong_im(30, 0,05)


# ── 4. ngưỡng và trạng thái ──────────────────────────────────────────────

def test_NGUONG_chia_cho_TONG_so_ung_vien_da_SANG():
    so = {"ung_vien": {"UV-001": {"qua_sang": True}, "UV-002": {"qua_sang": False},
                       "UV-003": {"qua_sang": False}}}
    assert cb.so_da_sang(so) == 3
    assert cb.nguong(so) == pytest.approx(0.05 / 3)


@pytest.mark.parametrize("delta, p, n_phien, n_ma, ky_vong", [
    (+0.05, 0.0001, 300, 60, "QUA"),
    (-0.05, 0.0001, 300, 60, "THUA"),
    (+0.05, 0.2000, 300, 60, "DANG CHAM"),
    (+0.05, 0.0001, 10, 60, "CHUA DU DU LIEU"),     # dưới một nhịp nhãn
    (+0.05, 0.0001, 300, 20, "CHUA DU DU LIEU"),    # quá ít mã
])
def test_trang_thai(delta, p, n_phien, n_ma, ky_vong):
    assert cb.trang_thai({"delta": delta, "p": p}, alpha_k=0.01,
                         n_phien=n_phien, n_ma=n_ma) == ky_vong


# ── 5. sổ đăng ký ứng viên ───────────────────────────────────────────────

def test_so_ung_vien_THAT_dung_khuon():
    so = cb.doc_so_ung_vien()
    cb.kiem_so_ung_vien(so)            # nổ nếu sai khuôn


def _uv(ngay, qua=True):
    return {"khai_ngay": ngay, "mo_ta": "x" * 20, "ly_do": "y" * 20, "qua_sang": qua,
            "spec": {"loai": "trong_so", "trong_so": {"trend_score": 1.0}}}


def test_TRAN_5_ung_vien_MOI_TUAN():
    so = {"ung_vien": {f"UV-{i:03d}": _uv("2026-10-05") for i in range(1, 6)}}
    cb.kiem_so_ung_vien(so)
    so["ung_vien"]["UV-006"] = _uv("2026-10-09")      # cùng tuần ISO
    with pytest.raises(ValueError, match="tuan"):
        cb.kiem_so_ung_vien(so)
    so["ung_vien"]["UV-006"] = _uv("2026-10-12")      # tuần sau: được
    cb.kiem_so_ung_vien(so)


def test_so_ung_vien_NHAN_qua_sang_NULL_va_TU_CHOI_kieu_khac():
    """BƯỚC 153: commit khai mang `qua_sang: null` — trước đó kiem_so_ung_vien
    đòi true/false, tức đòi kết quả của chính vòng sàng ngay lúc khai."""
    for q in (None, True, False):
        cb.kiem_so_ung_vien({"ung_vien": {"UV-001": _uv("2026-10-05", q)}})
    for q in (1, 0, "true", "null"):
        with pytest.raises(ValueError, match="qua_sang"):
            cb.kiem_so_ung_vien({"ung_vien": {"UV-001": _uv("2026-10-05", q)}})


def test_K_dem_CA_dong_CHUA_SANG():
    """K = mọi dòng đã khai, kể cả chưa sàng — chiều chặt hơn (BƯỚC 153)."""
    so = {"ung_vien": {"UV-001": _uv("2026-10-05", True), "UV-002": _uv("2026-10-05", None),
                       "UV-003": _uv("2026-10-05", None)}}
    assert cb.so_da_sang(so) == 3
    assert cb.nguong(so) == pytest.approx(0.05 / 3)


def test_so_ung_vien_TU_CHOI_spec_sai_va_thieu_truong():
    so = {"ung_vien": {"UV-001": _uv("2026-10-05")}}
    so["ung_vien"]["UV-001"]["spec"] = {"loai": "trong_so", "trong_so": {"news_score": 1.0}}
    with pytest.raises(ValueError):
        cb.kiem_so_ung_vien(so)
    so = {"ung_vien": {"UV-001": _uv("2026-10-05")}}
    del so["ung_vien"]["UV-001"]["ly_do"]
    with pytest.raises(ValueError):
        cb.kiem_so_ung_vien(so)
