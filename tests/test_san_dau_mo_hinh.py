"""Gác cho BƯỚC 248, việc 1: mô hình sinh của phép thử độ phủ có khớp chuỗi THẬT không?

Mô hình của BƯỚC 243 (trung bình trượt 20 phiên của nhiễu) cho tự tương quan bậc 1 cỡ 0,87–0,94 và hệ số phương sai
9–17, trong khi tài khoản vào lệnh NGẪU NHIÊN trên cache (`tools/san_dau.py kiem-mo-hinh`) cho 0,04 và ~1. Máy đo hỏng
im lặng (skill, Bước 3 điều 4): một mô hình sinh sai chỉ làm một con số "độ phủ" nghe hợp lý. Các gác ở đây:
  1. công cụ MÔ TẢ (ACF, hệ số phương sai, độ nhọn) bằng số TÍNH TAY;
  2. tài khoản ngẫu nhiên bằng kịch bản tính tay (đóng góp mỗi phiên, e, trừ e×rổ, cắt ở chỗ mất nến);
  3. mô hình mới: trung bình 0, KHÔNG tự tương quan ở mức, phương sai theo cụm, đuôi dày; mô hình cũ KHÔNG đạt
     (bản ghi vì sao nó bị thay);
  4. lệnh `kiem-mo-hinh` chạy offline trên cache tổng hợp và NỔ khi không có thư mục cache.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import numpy as np
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.append(str(GOC / "tools"))

import san_dau as sd  # noqa: E402
from test_san_dau import _nap_cli, _sach_cache_phan_tich  # noqa: E402

assert _sach_cache_phan_tich  # fixture autouse nhập từ test_san_dau, giữ trong module này

DUONG_MODULE = GOC / "san_dau.py"


# ── 1. công cụ mô tả ──────────────────────────────────────────────────────────────────────────
def test_acf_mau_bang_so_tinh_tay():
    """y = 1..4: lệch [−1,5 −0,5 0,5 1,5], mẫu số 5; lag 1 = 1,25/5; lag 2 = −1,5/5; lag 3 = −2,25/5."""
    assert sd.acf_mau([1, 2, 3, 4], so_tre=3) == pytest.approx([0.25, -0.30, -0.45])


def test_acf_mau_bo_nan_va_tru_trung_binh_mau():
    assert sd.acf_mau([1, np.nan, 2, 3, 4], so_tre=3) == pytest.approx([0.25, -0.30, -0.45])
    assert sd.acf_mau([101, 102, 103, 104], so_tre=1) == pytest.approx([0.25])   # dời chuỗi không đổi ACF


def test_he_so_phuong_sai_bang_so_tinh_tay_va_cat_o_bac_vuot_n():
    """ρ = [0,5], n = 4: 1 + 2·(1 − 1/4)·0,5 = 1,75. Bậc k ≥ n có trọng số 0 (không âm)."""
    assert sd.he_so_phuong_sai([0.5], 4) == pytest.approx(1.75)
    # n = 3, bốn bậc: (2/3 + 1/3 + 0 + clip(−1/3)) × 0,5 → 1 + 2 × 0,5 = 2 (không clip sẽ ra 1,667)
    assert sd.he_so_phuong_sai([0.5, 0.5, 0.5, 0.5], 3) == pytest.approx(2.0)
    assert sd.he_so_phuong_sai([0.0, 0.0], 100) == 1.0


def test_kurt_thua_bang_so_tinh_tay():
    assert sd.kurt_thua([1, -1, 1, -1]) == pytest.approx(-2.0)                  # m4/m2² = 1
    assert sd.kurt_thua([1, -1, np.nan, 1, -1]) == pytest.approx(-2.0)
    y = [0, 0, 0, 0, 0, 0, 0, 0, 0, 10]                                         # tập trung đuôi
    d = np.array(y) - 1.0
    assert sd.kurt_thua(y) == pytest.approx((d ** 4).mean() / (d ** 2).mean() ** 2 - 3.0)
    assert sd.kurt_thua(y) > 3.0


def test_mo_ta_chuoi_dung_khoa_va_lam_tron():
    m = sd.mo_ta_chuoi(np.random.default_rng(1).normal(size=(5, 300)))
    assert set(m) == {"so_chuoi", "n", "acf", "acf_tuyet_doi", "he_so_phuong_sai", "kurt_thua"}
    assert (m["so_chuoi"], m["n"]) == (5, 300)
    assert set(m["acf"]) == {str(k) for k in sd.TRE_IN}


# ── 2. tài khoản ngẫu nhiên ───────────────────────────────────────────────────────────────────
class _LuonVao:
    """Rng thay thế: `random()` luôn 0 (xác suất vào 1,0 thì mọi phiên đều vào), `integers` luôn 0."""
    def random(self):
        return 0.0

    def integers(self, lo, hi):
        return 0


def test_tai_khoan_ngau_nhien_bang_kich_ban_tinh_tay():
    """Một mã, 5 phiên [100 110 121 121 100], giữ 2 phiên, tỷ trọng 10%, vào ở mọi phiên s = 0..3. Đóng góp mỗi
    phiên = 0,1 × Δgiá / giá vào × 100. Rổ [0 10 0 0 −10] để thử phép trừ e×rổ."""
    gia = np.array([[100.0], [110.0], [121.0], [121.0], [100.0]])
    ro = np.array([np.nan, 10.0, 0.0, 0.0, -10.0])
    x, e = sd.tai_khoan_ngau_nhien(gia, ro, _LuonVao(), so_phien_giu=2, xac_suat_vao=1.0, ty_trong=0.1)
    ap = -21.0 / 121.0 * 10.0
    assert e == pytest.approx([0.0, 0.1, 0.2, 0.2, 0.2])
    assert x == pytest.approx([0.0, 1.0 - 0.1 * 10.0, 2.1, 0.0, 2 * ap + 0.2 * 10.0])


def test_tai_khoan_ngau_nhien_cat_o_cho_mat_nen_va_khong_vao_khi_mat_gia_dau():
    gia = np.array([[100.0], [110.0], [np.nan], [121.0], [130.0]])
    x, e = sd.tai_khoan_ngau_nhien(gia, np.zeros(5), _LuonVao(), so_phien_giu=3, xac_suat_vao=1.0, ty_trong=0.1)
    # s=0: [100 110] -> phiên 1 +1,0; s=1: [110] (cắt tại NaN) -> bỏ; s=2: giá NaN -> bỏ; s=3: [121 130] -> phiên 4
    assert x == pytest.approx([0.0, 1.0, 0.0, 0.0, 9.0 / 121.0 * 10.0])
    assert e == pytest.approx([0.0, 0.1, 0.0, 0.0, 0.1])


def test_tai_khoan_ngau_nhien_xac_suat_khong_thi_khong_bao_gio_vao_ke_ca_khi_rng_ra_dung_0():
    """`random()` ∈ [0, 1): xác suất 0 phải KHÔNG vào, kể cả khi số ngẫu nhiên đúng bằng 0 (so `>=`, không `>`)."""
    x, e = sd.tai_khoan_ngau_nhien(np.array([[1.0], [2.0], [3.0]]), np.zeros(3), _LuonVao(),
                                   so_phien_giu=2, xac_suat_vao=0.0, ty_trong=0.1)
    assert not x.any() and not e.any()


def test_tai_khoan_ngau_nhien_khong_vao_khi_xac_suat_khong():
    x, e = sd.tai_khoan_ngau_nhien(np.array([[1.0], [2.0], [3.0]]), np.zeros(3), np.random.default_rng(0),
                                   so_phien_giu=2, xac_suat_vao=0.0, ty_trong=0.1)
    assert not x.any() and not e.any()


# ── 3. mô hình sinh mới phải khớp thực tế, mô hình cũ thì không ────────────────────────────────
@pytest.fixture(scope="module")
def mo_hinh_moi():
    return sd.sinh_chuoi_mo_hinh_moi(1000, 300)


def test_hang_so_garch_dung_ban_ghi_va_ben_vung():
    assert (sd.GARCH_ALPHA, sd.GARCH_BETA, sd.GARCH_NU) == (0.14, 0.81, 7.5)
    assert sd.GARCH_ALPHA + sd.GARCH_BETA < 1.0          # có phương sai vô điều kiện
    assert sd.GARCH_NU > 4.0                             # độ nhọn hữu hạn
    assert 0.0 < sd.PHI_CANG_THANG < 0.2


def test_mo_hinh_moi_trung_binh_0_va_khong_tu_tuong_quan_o_muc(mo_hinh_moi):
    a, b, tho = mo_hinh_moi
    assert abs(float(tho.mean())) < 0.02
    for m in (a, b, tho, a - b):
        mt = sd.mo_ta_chuoi(m[:200])
        assert all(abs(v) < 0.06 for v in mt["acf"].values()), mt["acf"]   # chuỗi thật: 0,04
        assert 0.7 < mt["he_so_phuong_sai"] < 1.4, mt["he_so_phuong_sai"]   # chuỗi thật: 0,97–1,15


def test_mo_hinh_moi_co_phuong_sai_theo_cum_va_duoi_day(mo_hinh_moi):
    tho = mo_hinh_moi[2]
    mt = sd.mo_ta_chuoi(tho[:200])
    assert mt["acf_tuyet_doi"]["1"] > 0.10 and mt["acf_tuyet_doi"]["5"] > 0.07, mt["acf_tuyet_doi"]   # thật: 0,20 · 0,14
    assert 1.0 < mt["kurt_thua"] < 5.0, mt["kurt_thua"]                                                # thật: 2,7


def test_mo_hinh_moi_giu_thanh_phan_chung_va_mat_na_khong_giu(mo_hinh_moi):
    a, b, tho = mo_hinh_moi
    giu = a != 0.0
    assert np.array_equal(giu, b != 0.0)                         # A và B cùng mặt nạ
    ty_le_giu = sd.P_VAO_GIU / (sd.P_VAO_GIU + 1.0 / sd.TB_DOAN_GIU)
    assert abs(float(giu.mean()) - ty_le_giu) < 0.03
    rho = float(np.corrcoef(a[giu], b[giu])[0, 1])
    assert 0.4 < rho < 0.6, rho                                  # TY_TRONG_CHUNG = 0,5
    assert np.array_equal(tho[giu], a[giu])                      # A_tho = A trên đoạn giữ


def test_mo_hinh_moi_tat_dinh_va_phu_thuoc_hat_va_n():
    a1 = sd.sinh_chuoi_mo_hinh_moi(40, 6)
    assert all(np.array_equal(p, q) for p, q in zip(a1, sd.sinh_chuoi_mo_hinh_moi(40, 6)))
    assert not np.array_equal(a1[2], sd.sinh_chuoi_mo_hinh_moi(40, 6, hat=1)[2])
    assert not np.array_equal(a1[2][:, :10], sd.sinh_chuoi_mo_hinh_moi(113, 6)[2][:, :10])


def test_mo_hinh_cang_thang_co_tu_hoi_quy_bac_1_bang_phi():
    tho = sd.sinh_chuoi_mo_hinh_moi(1000, 200, phi=sd.PHI_CANG_THANG)[2]
    ac1 = float(np.mean([sd.acf_mau(r, 1)[0] for r in tho]))
    assert ac1 == pytest.approx(sd.PHI_CANG_THANG, abs=0.03)
    # giữ phương sai 1: mẫu lớn (1.500 × 800, hạt 7) cho 1,0027; bỏ hệ số √(1−φ²) cho ~1,026
    y = sd._nhieu_garch(np.random.default_rng(7), 1500, 800, sd.PHI_CANG_THANG)
    assert abs(float(y.var()) - 1.0) < 0.015


def test_mo_hinh_cu_BI_BAC_vi_cho_tu_tuong_quan_thang_hon_chuoi_that():
    """Bản ghi vì sao BƯỚC 248 thay mô hình: cùng dụng cụ đo, mô hình cũ ACF bậc 1 > 0,8 (thật: 0,04)."""
    a, _, tho = sd.sinh_chuoi_do_phu(252, 100)
    assert sd.mo_ta_chuoi(tho)["acf"]["1"] > 0.8
    assert sd.mo_ta_chuoi(a)["he_so_phuong_sai"] > 4.0


def test_nhieu_garch_phuong_sai_vo_dieu_kien_bang_1():
    y = sd._nhieu_garch(np.random.default_rng(3), 400, 500)
    assert y.shape == (400, 500)
    assert abs(float(y.var()) - 1.0) < 0.12


# ── 4. lệnh kiem-mo-hinh ──────────────────────────────────────────────────────────────────────
def _cache_tong_hop(thu_muc: Path, so_ma: int = 4, so_phien: int = 400) -> Path:
    import pandas as pd
    import vn100_symbols as v
    rng = np.random.default_rng(5)
    ngay = [d.strftime("%Y-%m-%d") for d in pd.bdate_range("2024-01-01", periods=so_phien)]
    for ma in list(dict.fromkeys(v.CUSTOM_WATCHLIST_SYMBOLS))[:so_ma]:
        gia = 20.0 * np.exp(np.cumsum(rng.normal(0, 0.01, so_phien)))
        pd.DataFrame({"time": ngay, "open": gia, "high": gia, "low": gia, "close": gia, "volume": 1}).to_csv(
            thu_muc / f"{ma}.csv", index=False)
    return thu_muc


def test_lenh_kiem_mo_hinh_chay_offline_tren_cache_tong_hop(tmp_path, capsys):
    cli = _nap_cli()
    thu_muc = _cache_tong_hop(tmp_path)
    a = cli.dung_parser().parse_args(["kiem-mo-hinh", "--cache", str(thu_muc), "--so-tk", "4", "--so-mo-hinh", "8"])
    assert a.ham(a) == cli.MA_BANG_NHAU
    ra = capsys.readouterr().out
    for dau in ("(a) RO DEU", "(b) TUNG MA", "(c) TAI KHOAN NGAU NHIEN", "(d) MO HINH CU", "(d) MO HINH MOI",
                "(d) CANG THANG"):
        assert dau in ra, dau
    assert "gia: 4 ma, 400 phien" in ra


def test_lenh_kiem_mo_hinh_NO_khi_khong_co_thu_muc_cache(tmp_path, monkeypatch):
    cli = _nap_cli()
    monkeypatch.delenv("VIBE_CACHE_DIR", raising=False)
    with pytest.raises(FileNotFoundError):
        cli.doc_gia_dong_cache(None)
    with pytest.raises(FileNotFoundError):
        cli.doc_gia_dong_cache(str(tmp_path / "khong_co"))


def test_hop_garch_tim_lai_tham_so_cua_chuoi_sinh():
    pytest.importorskip("scipy")
    cli = _nap_cli()
    rng = np.random.default_rng(11)
    y = sd._nhieu_garch(rng, 12, 700)
    alpha, beta, nu = cli.hop_garch(list(y))
    assert 0.07 < alpha < 0.22 and 0.65 < beta < 0.92 and 4.0 < nu < 14.0, (alpha, beta, nu)


def test_module_thuan_khong_nhap_scipy():
    """scipy không có trong requirements.txt: chỉ `tools/san_dau.py::hop_garch` được nạp nó, TRONG hàm."""
    cay = ast.parse(DUONG_MODULE.read_text(encoding="utf-8"))
    assert not [n for n in ast.walk(cay) if isinstance(n, (ast.Import, ast.ImportFrom)) and "scipy" in ast.dump(n)]
    cli = ast.parse((GOC / "tools" / "san_dau.py").read_text(encoding="utf-8"))
    assert not [n for n in cli.body if isinstance(n, (ast.Import, ast.ImportFrom)) and "scipy" in ast.dump(n)]
    trong_ham = [n for f in ast.walk(cli) if isinstance(f, ast.FunctionDef) for n in ast.walk(f)
                 if isinstance(n, ast.ImportFrom) and n.module == "scipy"]
    assert trong_ham, "hop_garch phải nạp scipy trong hàm"
