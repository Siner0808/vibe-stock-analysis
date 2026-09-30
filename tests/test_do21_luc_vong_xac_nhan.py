"""Gác dụng cụ ĐO 21 — lực của vòng xác nhận ở tầng 3.

Chạy trên dữ liệu TỔNG HỢP, không chạm cache giá: phép đo thật chỉ được chạy
sau khi tiêu chí đã ký (`docs/TIEU-CHI-DOC-TRUOC.md` mục ĐO 21).

Ba thứ phải đúng, vì cả ba đều là chỗ một máy đo lực có thể tự khen mình:
1. null HOÁN VỊ MÃ đúng là IC gộp dưới một phép gán lại mã — hoán vị đồng
   nhất phải cho LẠI ĐÚNG IC thật;
2. nền của phép tiêm RỜI nhãn — không cột nào giữ lại chính mã của nó;
3. phán quyết đọc ở cột BẤT LỢI, và máy đo hỏng thì KHÔNG phán.
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

GOC = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "do21_luc_vong_xac_nhan", GOC / "tools" / "do21_luc_vong_xac_nhan.py")
T = importlib.util.module_from_spec(_spec)
sys.modules["do21_luc_vong_xac_nhan"] = T
_spec.loader.exec_module(T)

import experiment_tran_dac_trung as E  # noqa: E402
import experiment_khoi_ngoai_nhip_dai as D  # noqa: E402
from paper_metrics import ROUND_TRIP_COST_PCT  # noqa: E402


def _ngau_nhien(W=60, M=50, hat=1):
    rng = np.random.default_rng(hat)
    return rng.standard_normal((W, M)), rng.standard_normal((W, M))


# ── 1. null hoán vị mã ───────────────────────────────────────────────────

class _Dong:
    """rng giả: permutation trả hoán vị ĐỒNG NHẤT."""
    def permutation(self, m):
        return np.arange(m)


def test_hoan_vi_DONG_NHAT_cho_lai_DUNG_ic_that():
    X, Y = _ngau_nhien()
    Y = Y + 0.4 * X                       # có liên kết, để IC khác 0 rõ
    ic = T.ic_gop(X, Y)
    null = T.null_hoan_vi_ma(X, Y, _Dong(), so=3)
    assert ic > 0.2
    assert null == pytest.approx([ic] * 3, abs=1e-12)


def test_ic_gop_di_qua_rho_hang_cua_E():
    X, Y = _ngau_nhien(hat=2)
    assert T.ic_gop(X, Y) == E.rho_hang(X.ravel(), Y.ravel())


def test_null_PHA_lien_ket_theo_ma():
    """X = Y theo từng mã: IC = 1, còn null phải nằm xa dưới 1."""
    X, _ = _ngau_nhien(hat=3)
    null = T.null_hoan_vi_ma(X, X.copy(), np.random.default_rng(0), so=200)
    assert T.ic_gop(X, X) == pytest.approx(1.0)
    assert abs(float(np.mean(null))) < 0.05
    assert float(np.max(null)) < 0.5


def test_moi_gia_tri_null_la_IC_cua_nhan_HOAN_VI_THEO_COT():
    """Nhãn của MỘT mã đi NGUYÊN KHỐI sang mã khác — cả chuỗi thời gian của
    nó — chứ không xáo theo hàng. So thẳng với IC của `Y[:, p]`."""
    X, Y = _ngau_nhien(W=50, M=9, hat=12)
    Y = Y + 0.5 * X
    for p in (np.array([3, 0, 1, 2, 8, 7, 6, 5, 4]),
              np.array([1, 2, 3, 4, 5, 6, 7, 8, 0])):
        class _Co:
            def permutation(self, m, _p=p):
                return _p
        v = T.null_hoan_vi_ma(X, Y, _Co(), so=1)[0]
        assert v == pytest.approx(T.ic_gop(X, Y[:, p]), abs=1e-12)


# ── 2. p hai phía ────────────────────────────────────────────────────────

def test_p_HAI_PHIA_doi_xung():
    null = np.random.default_rng(4).standard_normal(20000)
    m, s = float(null.mean()), float(null.std())
    p_duong = T.tri_so_p_z(m + 1.96 * s, null)
    p_am = T.tri_so_p_z(m - 1.96 * s, null)
    assert p_duong == pytest.approx(0.05, abs=1e-3)
    assert p_am == pytest.approx(p_duong)
    assert T.tri_so_p_z(m, null) == pytest.approx(1.0)


def test_p_null_SUY_BIEN_la_1_khong_phai_0():
    assert T.tri_so_p_z(0.3, np.zeros(10)) == 1.0


# ── 3. phép tiêm ─────────────────────────────────────────────────────────

def test_nen_ROI_nhan_moi_cot_la_cot_cua_MA_KHAC():
    W, M = 30, 12
    X = np.tile(np.arange(M, dtype=float), (W, 1)) + \
        np.random.default_rng(5).standard_normal((W, M)) * 1e-6
    Y = np.random.default_rng(6).standard_normal((W, M))
    for hat in range(40):
        G = T.tiem(X, Y, 0.0, np.random.default_rng(hat))
        nguon = np.argsort(np.argsort(G.mean(axis=0)))   # hạng cột = mã gốc
        assert not np.any(nguon == np.arange(M)), f"hat {hat}: cot giu ma cu"


def test_tiem_muc_1_la_chinh_nhan_chuan_hoa():
    X, Y = _ngau_nhien(hat=7)
    G = T.tiem(X, Y, 1.0, np.random.default_rng(0))
    assert G == pytest.approx((Y - Y.mean()) / Y.std())


def test_tiem_dat_DUNG_muc_tuong_quan():
    X, Y = _ngau_nhien(W=400, M=60, hat=8)
    G = T.tiem(X, Y, 0.3, np.random.default_rng(0))
    r = np.corrcoef(G.ravel(), Y.ravel())[0, 1]
    assert r == pytest.approx(0.3, abs=0.03)


# ── 4. rào hiện hành ─────────────────────────────────────────────────────

def test_rao_HIEN_HANH_dung_chi_phi_MOI_khong_dung_0_43():
    for s in (3.0, 9.0):
        ti_le = T.rao_hien_hanh(s) / E.rao_hoa_von(s)
        assert ti_le == pytest.approx(
            (ROUND_TRIP_COST_PCT + T.CHI_PHI_THUC_THI_HIEN_HANH)
            / (ROUND_TRIP_COST_PCT + E.TRUOT_GIA_DPT))
    assert T.CHI_PHI_THUC_THI_HIEN_HANH > E.TRUOT_GIA_DPT


def test_chi_phi_hien_hanh_KHOP_so_DO_20_trong_nhat_ky_BUOC_136():
    """Hằng số chép từ một phép đo — gác để nó không trôi khỏi nguồn.

    Nguồn là dòng nhật ký chỉ-thêm của BƯỚC 136 (ĐO 20), KHÔNG phải bảng "hiện
    hành" trong CLAUDE.md: bảng ấy đổi theo từng ĐO (ĐO 22 nay ghi 0,96), còn ĐO 21
    đã ký và chạy với 0,76 nên hằng số không được đổi theo nó.
    """
    s = (GOC / "docs" / "STATE.md").read_text(encoding="utf-8")
    assert "**0,76** theo ngày" in s
    assert T.CHI_PHI_THUC_THI_HIEN_HANH == 0.76


# ── 5. cửa sổ ────────────────────────────────────────────────────────────

def _bang_co_lo():
    ngay = [f"2026-01-{i:02d}" for i in range(1, 31)]
    Y = pd.DataFrame(np.ones((30, 4)), index=ngay, columns=list("ABCD"))
    X = Y.copy()
    Y.loc[ngay[10], "C"] = np.nan          # C thủng ở hàng 10
    X.loc[ngay[20], "D"] = np.nan          # D thủng ở hàng 20 (phía nền)
    return Y, X


def test_cua_so_CHI_giu_ma_DU_ca_nhan_lan_nen():
    Y, X = _bang_co_lo()
    x, y, d0, d1, cot = T.cua_so(Y, X, 5, 10, min_ma=2)
    assert cot == ["A", "B", "D"] and d0 == "2026-01-06" and d1 == "2026-01-15"
    x, y, _, _, cot = T.cua_so(Y, X, 15, 10, min_ma=2)
    assert cot == ["A", "B", "C"]
    assert T.cua_so(Y, X, 5, 10, min_ma=4) is None
    assert T.cua_so(Y, X, 25, 10, min_ma=1) is None          # vượt đáy bảng


def test_diem_bat_dau_KHOP_cua_so():
    Y, X = _bang_co_lo()
    bd = T.diem_bat_dau(Y, X, 10, min_ma=4)
    assert bd == [0]
    bd3 = T.diem_bat_dau(Y, X, 10, min_ma=3)
    assert bd3 == [i for i in range(21) if T.cua_so(Y, X, i, 10, 3) is not None]


# ── 6. phán quyết ────────────────────────────────────────────────────────

def test_doc_o():
    im = D.nguong_im(30, 0.05)
    assert T.doc_o(24, 30, 0, 0.05) == "BAT"
    assert T.doc_o(23, 30, 0, 0.05) == "KHONG"
    assert T.doc_o(30, 30, im + 1, 0.05) == "KHONG DOC"
    assert T.doc_o(30, 30, im, 0.05) == "BAT"
    assert T.doc_o(29, 29, 0, 0.05) == "KHONG DOC"             # dưới R_TOI_THIEU


def _bang(w_theo_nen: dict) -> dict:
    """Ô (nen, 21, W, 20) BAT từ W đã cho trở lên; None = không W nào."""
    b = {}
    for n, w0 in w_theo_nen.items():
        for W in T.CUA_SO:
            b[(n, 21, W, 20)] = "BAT" if (w0 is not None and W >= w0) else "KHONG"
    return b


def test_phan_dinh_ba_ket_cuc_va_doc_o_cot_BAT_LOI():
    n1, n2 = T.NEN
    assert T.phan_dinh(_bang({n1: 21, n2: 21}), True)[1].startswith("KET CUC A")
    ma, cau = T.phan_dinh(_bang({n1: 63, n2: 252}), True)
    assert ma == 0 and cau.startswith("KET CUC B") and "252" in cau
    ma, cau = T.phan_dinh(_bang({n1: 21, n2: 126}), True)
    assert "126" in cau                   # KHÔNG lấy nền dễ (21)
    assert T.phan_dinh(_bang({n1: 21, n2: None}), True)[1].startswith("KET CUC C")


def test_phan_dinh_KHONG_phan_khi_may_do_hong():
    n1, n2 = T.NEN
    assert T.phan_dinh(_bang({n1: 21, n2: 21}), False)[0] == 2
    b = _bang({n1: 21, n2: 21})
    b[(n2, 21, 63, 20)] = "KHONG DOC"
    assert T.phan_dinh(b, True)[0] == 2
    del b[(n2, 21, 63, 20)]
    assert T.phan_dinh(b, True)[0] == 2


def test_qua_doi_chieu():
    assert T.qua_doi_chieu([]) is False
    assert T.qua_doi_chieu([{"ty_le": 0.80}, {"ty_le": 1.25}]) is True
    assert T.qua_doi_chieu([{"ty_le": 1.0}, {"ty_le": 1.30}]) is False
    assert T.qua_doi_chieu([{"ty_le": 0.74}]) is False


# ── 7. chứng cứ dương trên dữ liệu tổng hợp ─────────────────────────────

def _bang_tong_hop(W=300, M=60, hat=9):
    rng = np.random.default_rng(hat)
    ngay = [str(d.date()) for d in pd.bdate_range("2024-01-01", periods=W)]
    Y = pd.DataFrame(rng.standard_normal((W, M)), index=ngay)
    X = pd.DataFrame(rng.standard_normal((W, M)), index=ngay)
    return Y, X


def test_CHUNG_CU_DUONG_tong_hop_bat_muc_lon_va_im_o_muc_0():
    Y, X = _bang_tong_hop()
    bd = T.diem_bat_dau(Y, X, 126, min_ma=40)
    rng = np.random.default_rng(11)
    lon = [T.mot_luot(Y, X, 126, 0.15, bd, rng, so=300)["p"] for _ in range(10)]
    khong = [T.mot_luot(Y, X, 126, 0.0, bd, rng, so=300)["p"] for _ in range(30)]
    assert sum(p < 0.05 for p in lon) == 10
    assert sum(p < 0.05 for p in khong) <= D.nguong_im(30, 0.05)
