"""NULL CÓ NHỚ (NULL-M) — BƯỚC 301, ĐO 38. Gác của HÀM MỚI trong `thi_truong_gia.py` (`_sinh_loi_m`, `tinh_su_that_m`,
`ic_da_ghi_m`, `sinh_thi_truong_m`) và gác "thị trường cũ không đổi một bit".

Đặc tả: `docs/thiet-ke-c4-thi-truong-gia.md` (mục tuyên bố sửa C4) và vibe_logs_c4sua/DAC-TA-SUA-C4.md mục 4. Chỉ dòng
hạt 9001 (dòng thử) và dòng 1 chỉ số nhỏ ở phép băm cũ; KHÔNG BAO GIỜ dòng 2–10.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

import thi_truong_gia as T

GOC = Path(__file__).resolve().parent.parent
LUONG_THU = 9001


# ── băm thị trường CŨ ────────────────────────────────────────────────────────────────────────────────────
# Các băm dưới đây được TÍNH Ở COMMIT CƠ SỞ 8020ea8 (đầu PR #345), TRƯỚC khi thêm bất kỳ dòng nào của NULL-M:
#   ../vibe_preview/.venv/Scripts/python.exe -X utf8 <script băm> (script: băm `_sinh_loi`, `tinh_su_that`, `sinh_thi_truong`)
# Làm tròn 7 chữ số thập phân với mảng thực (sin/cos của libm khác nhau giữa máy có thể lệch bit cuối); nấc và điểm là số nguyên.

def _bam_mau(m: dict) -> str:
    h = hashlib.sha256()
    h.update(np.round(np.ascontiguousarray(m["close"]), 7).tobytes())
    h.update(np.ascontiguousarray(m["diem"]).tobytes())
    h.update(np.round(np.ascontiguousarray(m["z"]), 7).tobytes())
    for k in sorted(m["thanh_phan"]):
        h.update(k.encode())
        h.update(np.round(np.ascontiguousarray(m["thanh_phan"][k]), 7).tobytes())
    return h.hexdigest()[:20]


BAM_CU_SINH_LOI = {
    (LUONG_THU, 1, 0.0, 400): "b607dee0dd38ffa7b855",
    (LUONG_THU, 1, 0.02, 400): "401dc93524b9dba48294",
    (LUONG_THU, 7, 0.0, 400): "628d6ca84c8ecd209a43",
    (LUONG_THU, 7, 0.03, 600): "84431c7418e992bd385f",
}
BAM_CU_SU_THAT = "3bd104f58f9517d8348a"      # tinh_su_that(9001, 1, 0.02, 800)
BAM_CU_THI_TRUONG = "6a1c48a0bc0546600c27"   # sinh_thi_truong(9001, 1, 0.02, 300, co_su_that=False): giá + điểm


@pytest.mark.parametrize("khoa", sorted(BAM_CU_SINH_LOI))
def test_sinh_loi_cu_khong_doi_mot_bit(khoa):
    luong, chi_so, kappa, n = khoa
    assert _bam_mau(T._sinh_loi(np.random.default_rng([luong, chi_so]), n, kappa)) == BAM_CU_SINH_LOI[khoa]


def test_tinh_su_that_va_sinh_thi_truong_cu_khong_doi():
    s = T.tinh_su_that(LUONG_THU, 1, 0.02, 800)
    bam = hashlib.sha256(json.dumps({k: [round(v["delta_ic"], 9), round(v["se_mc"], 9)] for k, v in s["spec"].items()},
                                    sort_keys=True).encode()).hexdigest()[:20]
    assert bam == BAM_CU_SU_THAT
    tt = T.sinh_thi_truong(LUONG_THU, 1, 0.02, 300, co_su_that=False)
    assert hashlib.sha256(np.round(np.ascontiguousarray(tt.gia.to_numpy(float)), 7).tobytes()
                          + tt.diem.tobytes()).hexdigest()[:20] == BAM_CU_THI_TRUONG


def test_nho_he_so_d_0_va_kappa_d_0_cho_dung_bit_mau_cu():
    """Hàm mới rút `d` SAU mọi thứ cũ và `he_so_d = 0` không đổi tiềm ẩn: nên trùng từng bit `_sinh_loi(kappa = 0)`. Bắt
    một hàm mới mà sai thứ tự rút số hay sai công thức tiềm ẩn."""
    for chi_so in (3, 11):
        a = T._sinh_loi(np.random.default_rng([LUONG_THU, chi_so]), 500, 0.0)
        b = T._sinh_loi_m(np.random.default_rng([LUONG_THU, chi_so]), 500, 0.0, 0.0)
        assert np.array_equal(a["close"], b["close"]) and np.array_equal(a["diem"], b["diem"])
        assert all(np.array_equal(a["thanh_phan"][k], b["thanh_phan"][k]) for k in a["thanh_phan"])


# ── NULL-M: tính chất của bộ sinh mới ────────────────────────────────────────────────────────────────────

def test_he_so_d_la_he_so_z_da_khai_khong_so_moi():
    assert T.HE_SO_D == T.HE_SO_Z == 0.5 and T.PHI_D == 0.97


def test_d_chung_trong_nganh_va_khac_giua_cac_nganh():
    d = T._sinh_loi_m(np.random.default_rng([LUONG_THU, 5]), 300, 0.02)["d"].T    # m × n: d của ngành của từng mã
    ma_nganh = np.arange(T.SO_MA) * T.SO_NGANH // T.SO_MA
    for g in range(T.SO_NGANH):
        mot = d[ma_nganh == g]
        assert (mot == mot[0]).all(), f"nganh {g}: d khong chung giua cac ma cung nganh"
    ten = {tuple(d[ma_nganh == g][0][:20].round(9)) for g in range(T.SO_NGANH)}
    assert len(ten) == T.SO_NGANH


def test_d_vao_CA_NAM_thanh_phan_cung_he_so():
    """Mỗi thành phần tương quan với d cỡ b_d · (hệ số của việc rời rạc hoá); bắt `b_d` chỉ vào một thành phần."""
    mau = T._sinh_loi_m(np.random.default_rng([LUONG_THU, 5]), 1500, 0.02)
    d = mau["d"].ravel()
    r = {k: float(np.corrcoef(v.ravel(), d)[0, 1]) for k, v in mau["thanh_phan"].items()}
    for k, v in r.items():
        assert 0.36 < v < 0.56, (k, v, r)


def test_phuong_sai_tiem_an_van_1_cac_nac_van_deu_xac_suat():
    """Thêm `d` không làm lệch xác suất nấc (tiềm ẩn mới có phương sai 1). Volume có 13 nấc; sai lệch tối đa ≤ 2 điểm %."""
    mau = T._sinh_loi_m(np.random.default_rng([LUONG_THU, 9]), 2000, 0.02)
    for ten, (so, _lo, _hi) in T.NAC.items():
        v = mau["thanh_phan"][ten].ravel()
        _, dem = np.unique(v, return_counts=True)
        assert len(dem) == so and np.abs(dem / v.size - 1.0 / so).max() < 0.02, ten


def test_kappa_d_chi_doi_gia_khong_doi_dong_quyet_dinh():
    """Như `kappa` của bộ sinh cũ: κ_d chỉ đi vào LỢI NHUẬN; cùng hạt thì cùng dòng quyết định, khác giá."""
    a = T.sinh_thi_truong_m(LUONG_THU, 4, 0.0, 300, co_su_that=False)
    b = T.sinh_thi_truong_m(LUONG_THU, 4, 0.03, 300, co_su_that=False)
    assert np.array_equal(a.diem, b.diem)
    assert all(np.array_equal(a.thanh_phan[k], b.thanh_phan[k]) for k in a.thanh_phan)
    assert not np.array_equal(a.gia.to_numpy(), b.gia.to_numpy())
    assert a.dong_quyet_dinh() == b.dong_quyet_dinh()


def test_kappa_d_vao_loi_nhuan_dung_kieu_z_d_o_phien_s_tru_2_chia_21():
    """Cùng hạt: lợi nhuận ở phiên s của thị trường có κ_d trừ lợi nhuận của thị trường κ_d = 0 bằng ĐÚNG κ_d · d(s−2) / 21
    (trừ ô bị kẹp ±7%). Bắt `d` lệch phiên (s thay vì s−2), sai hệ số chia, hay d không chung đúng ngành."""
    kd, n = 0.3, 400
    m0 = T._sinh_loi_m(np.random.default_rng([LUONG_THU, 6]), n, 0.0)
    m1 = T._sinh_loi_m(np.random.default_rng([LUONG_THU, 6]), n, kd)
    ln0 = m0["close"][1:] / m0["close"][:-1] - 1.0           # phiên s = 1…n−1
    ln1 = m1["close"][1:] / m1["close"][:-1] - 1.0
    d = m1["d"]                                               # n × m: d ở CHÍNH phiên t
    s = np.arange(1, n)
    du = (s >= 2)[:, None] & (np.abs(ln0) < 0.06) & (np.abs(ln1) < 0.06)
    ky_vong = kd * d[np.clip(s - 2, 0, n - 1)] / T.cb.NHIP
    assert du.sum() > 0.8 * du.size
    assert np.allclose((ln1 - ln0)[du], ky_vong[du], atol=1e-9)


def test_kappa_d_vao_loi_nhuan_ic_cua_diem_da_ghi_len_theo_kappa_d():
    ic0 = np.mean([T.ic_da_ghi_m(LUONG_THU, i, 0.0) for i in range(1, 5)])
    ic2 = np.mean([T.ic_da_ghi_m(LUONG_THU, i, 0.02) for i in range(1, 5)])
    ic4 = np.mean([T.ic_da_ghi_m(LUONG_THU, i, 0.04) for i in range(1, 5)])
    assert abs(ic0) < 0.03 and 0.06 < ic2 < 0.14 and ic4 > ic2 + 0.05, (ic0, ic2, ic4)


def test_thi_truong_m_khuon_dung_va_xac_dinh():
    a = T.sinh_thi_truong_m(LUONG_THU, 2, 0.02, 200, co_su_that=False)
    b = T.sinh_thi_truong_m(LUONG_THU, 2, 0.02, 200, co_su_that=False)
    assert a.gia.equals(b.gia) and np.array_equal(a.diem, b.diem)
    assert a.gia.shape == (200, T.SO_MA) and str(a.gia.index[0]) >= T.NGAY_DAU and a.kappa == 0.02 and a.su_that is None
    assert len(a.dong_quyet_dinh()) == 200 * T.SO_MA
    with pytest.raises(ValueError):
        T.sinh_thi_truong_m(LUONG_THU, 2, -0.01, 200, co_su_that=False)
    with pytest.raises(ValueError):
        T.sinh_thi_truong_m(0, 2, 0.01, 200, co_su_that=False)
    with pytest.raises(ValueError):
        T._sinh_loi_m(np.random.default_rng(1), 50, 0.01, 1.0)


# ── oracle của NULL-M ────────────────────────────────────────────────────────────────────────────────────

def test_oracle_nho_o_kappa_d_0_cac_spec_trong_hai_se_nhu_may_do_NULL():
    """Ở κ_d = 0 nhân tố ngành KHÔNG vào lợi nhuận nên mọi ΔIC_true ≈ 0 — kể cả khi `d` vẫn có trong điểm (b_d > 0):
    điểm không biết gì về nhãn. Cùng ba tiêu chí `MAY_DO_NULL` của ĐO 37: ≥ 85% ô trong 2 sai số MC, sd(z) ∈ [0,7 ; 1,5],
    |trung bình z| < 0,5; trên 3 thị trường × 12 spec = 36 ô, hạt cố định (dòng thử 9001)."""
    z = []
    for chi_so in (1, 2, 3):
        su = T.tinh_su_that_m(LUONG_THU, chi_so, 0.0, 4000)
        z += [v["delta_ic"] / v["se_mc"] for v in su["spec"].values()]
    z = np.asarray(z)
    assert z.size == 36
    assert (np.abs(z) < 2.0).mean() >= 0.85 and 0.7 <= z.std(ddof=1) <= 1.5 and abs(z.mean()) < 0.5, z.round(2).tolist()


def test_oracle_nho_khuon_va_ic_da_ghi_duong_khi_co_kappa_d():
    su = T.tinh_su_that_m(LUONG_THU, 1, 0.03, 2000)
    assert set(su["spec"]) == set(T.ho_spec_oracle()) and len(su["spec"]) == 12
    assert su["kappa_d"] == 0.03 and su["he_so_d"] == T.HE_SO_D and su["hat"] == [LUONG_THU, 1, T.HAT_SU_THAT]
    assert su["ic_da_ghi"] > 0.1
    assert all(np.isfinite(v["delta_ic"]) and v["se_mc"] > 0 for v in su["spec"].values())
    # NULL-M có ΔIC_true KHÁC 0 với vài spec (cộng nhiều thành phần giảm nhiễu riêng); M1 đọc dấu của nó, nên oracle phải tách được
    assert len(T.spec_ngoai_hai_se(su)) >= 1


def test_oracle_cu_tinh_su_that_khong_nhin_thay_d():
    """`tinh_su_that` (oracle cũ) rút mẫu bằng `_sinh_loi`: không dùng được cho NULL-M. Bắt việc nhầm dùng nó."""
    cu = T.tinh_su_that(LUONG_THU, 1, 0.0, 2000)
    nho = T.tinh_su_that_m(LUONG_THU, 1, 0.03, 2000)
    assert "ic_da_ghi" not in cu and "ic_da_ghi" in nho
    assert cu["spec"]["deu"]["delta_ic"] != nho["spec"]["deu"]["delta_ic"]


# ── gác AST: chỉ dòng 1 và 9001; không dòng 2–10 ─────────────────────────────────────────────────────────

def _ham_moi(ten_file: str, ten_ham: set[str]) -> list[ast.FunctionDef]:
    cay = ast.parse((GOC / ten_file).read_text(encoding="utf-8"))
    return [n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name in ten_ham]


def test_ham_moi_cua_nho_khong_chua_hang_so_dong_hat_2_den_10():
    """Đọc NGUỒN bằng AST: trong các hàm NULL-M, không số nguyên 2–10 nào làm đối số vị trí đầu tiên của một lời gọi
    (cách một dòng hạt đi vào `default_rng`/`sinh_*`), và không có `[2…10, …]` làm hạt."""
    ham = _ham_moi("thi_truong_gia.py", {"_sinh_loi_m", "_su_that_tu_mau", "tinh_su_that_m", "ic_da_ghi_m", "sinh_thi_truong_m"})
    assert len(ham) == 5
    for f in ham:
        for n in ast.walk(f):
            if isinstance(n, ast.Call) and n.args and isinstance(n.args[0], ast.Constant):
                assert not (isinstance(n.args[0].value, int) and not isinstance(n.args[0].value, bool)
                            and 2 <= n.args[0].value <= 10 and getattr(n.func, "attr", getattr(n.func, "id", "")) in
                            {"default_rng", "sinh_thi_truong_m", "tinh_su_that_m", "ic_da_ghi_m", "_kiem_hat"}), f.name
            if isinstance(n, ast.List) and n.elts and isinstance(n.elts[0], ast.Constant):
                assert not (isinstance(n.elts[0].value, int) and 2 <= n.elts[0].value <= 10), f.name
