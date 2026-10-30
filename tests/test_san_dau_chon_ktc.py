"""Gác cho BƯỚC 248, việc 2–3: các ứng viên cách tính KTC và bộ CHỌN theo thứ tự đã khai (`docs/thiet-ke-c1-san-dau.md`
mục 8.4b).

Máy đo hỏng im lặng (skill, Bước 3 điều 4). Ở đây:
  1. quy tắc Politis–White: số tính tay, bất biến (dời/co giãn chuỗi), cận, và độ lớn đúng bậc ở AR(1) (kết quả lý thuyết
     b ≈ (1,5·(2ρ/(1−ρ²))²)^(1/3)·n^(1/3));
  2. `ktc_khoi_co_cap` nhận quy tắc: cùng kết quả với con số mà quy tắc trả, dạng cặp tính quy tắc trên a − b;
  3. bộ chọn: DỪNG ở ứng viên đầu tiên đạt, không chạy ứng viên nào sau nó; khối cố định dài hơn n là ô KHÔNG đạt;
     không ứng viên nào đạt thì không chốt gì;
  4. thứ tự ứng viên đúng bản khai (đổi thứ tự sau khi thấy số là chế điều kiện).
"""
from __future__ import annotations

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


def _ar1(rho: float, n: int, hat: int = 0) -> np.ndarray:
    e = np.random.default_rng(hat).normal(size=n + 200)
    y = np.zeros(n + 200)
    for t in range(1, n + 200):
        y[t] = rho * y[t - 1] + e[t]
    return y[200:]


# ── 1. Politis–White ──────────────────────────────────────────────────────────────────────────
def test_pw_chuoi_hang_hay_qua_ngan_thi_khoi_1():
    assert sd.do_dai_politis_white(np.full(50, 3.0)) == 1
    assert sd.do_dai_politis_white([1.0, 2.0, 3.0]) == 1
    assert sd.do_dai_politis_white([]) == 1


def test_pw_ghat_duong_nho_hon_khong_thi_khoi_1():
    """x = [1,−1,1,−1]: ρ̂ = [1, −0,75, 0,5, −0,25]; ĝ = 1 + 2·(−0,75) = −0,5 ≤ 0 → 1 (tính tay)."""
    assert sd.do_dai_politis_white([1.0, -1.0, 1.0, -1.0]) == 1


def test_pw_vi_du_nho_tinh_tay_ra_1():
    """x = [1,1,−1,−1]: M = 2, ĝ = 1,5, Ĝ = 0,5, b = (1,5·(1/3)²)^(1/3)·4^(1/3) = 0,874 → làm tròn 1."""
    assert sd.do_dai_politis_white([1.0, 1.0, -1.0, -1.0]) == 1


def test_pw_bat_bien_khi_doi_va_co_gian_chuoi():
    x = _ar1(0.5, 400, 3)
    L = sd.do_dai_politis_white(x)
    assert sd.do_dai_politis_white(x + 1000.0) == L
    assert sd.do_dai_politis_white(7.5 * x) == L
    assert sd.do_dai_politis_white(-x) == L


def test_pw_ar1_cang_tu_tuong_quan_manh_cang_khoi_dai_va_dung_bac_ly_thuyet():
    n = 20000
    ly_thuyet = {r: (1.5 * (2 * r / (1 - r * r)) ** 2) ** (1 / 3) * n ** (1 / 3) for r in (0.5, 0.8)}
    L5 = sd.do_dai_politis_white(_ar1(0.5, n, 1))
    L8 = sd.do_dai_politis_white(_ar1(0.8, n, 2))
    assert 0.6 * ly_thuyet[0.5] < L5 < 1.6 * ly_thuyet[0.5], (L5, ly_thuyet[0.5])      # ~37,6
    assert 0.6 * ly_thuyet[0.8] < L8 < 1.6 * ly_thuyet[0.8], (L8, ly_thuyet[0.8])      # ~92
    assert L8 > L5 > 5


def test_pw_nhieu_trang_cho_khoi_rat_ngan():
    """Chuỗi KHÔNG tự tương quan: khối ngắn (thật: các lát đo ở mục 8.4b)."""
    ls = [sd.do_dai_politis_white(np.random.default_rng(s).normal(size=252)) for s in range(40)]
    assert float(np.median(ls)) <= 3 and max(ls) <= 20, ls


def test_pw_ton_trong_can_tren_min_3_can_n_va_n_chia_3():
    xu_huong = np.arange(40, dtype=float)                       # tự tương quan gần 1: b rất lớn, bị cắt ở cận
    assert sd.do_dai_politis_white(xu_huong) <= int(np.ceil(min(3 * np.sqrt(40), 40 / 3)))   # 14
    assert sd.do_dai_politis_white(np.arange(400, dtype=float)) <= int(np.ceil(min(3 * np.sqrt(400), 400 / 3)))   # 60


def _pw_tham_chieu(x) -> int:
    """Bản dựng lại KHÁC CẤU TRÚC của `do_dai_politis_white` (vòng lặp k = −M..M đối xứng, np.correlate), từ công thức
    trong đặc tả 8.4b. Dùng để so trên nhiều chuỗi đủ chạm mọi nhánh; số vàng bên dưới ghim kết quả."""
    x = np.asarray(x, float)
    n = x.size
    d = x - x.mean()
    if n < 4 or not d.any():
        return 1
    kn = max(5, int(np.ceil(np.log10(n))))
    mmax = int(np.ceil(np.sqrt(n))) + kn
    toi_da = min(mmax + kn, n - 1)
    full = np.correlate(d, d, mode="full")[n - 1:] / n          # R(0..n−1)
    rho = full / full[0]
    crit = 2.0 * np.sqrt(np.log10(n) / n)
    mhat = mmax
    for m in range(mmax + 1):
        if all((abs(rho[m + j]) if m + j <= toi_da else 0.0) < crit for j in range(1, kn + 1)):
            mhat = m
            break
    big_m = min(2 * max(mhat, 1), toi_da)
    g = gg = 0.0
    for k in range(-big_m, big_m + 1):
        s = abs(k) / big_m
        lam = 1.0 if s <= 0.5 else (2.0 * (1.0 - s) if s <= 1.0 else 0.0)
        g += lam * full[abs(k)]
        gg += lam * abs(k) * full[abs(k)]
    if g <= 0:
        return 1
    b = ((2.0 * gg * gg) / ((4.0 / 3.0) * g * g)) ** (1.0 / 3.0) * n ** (1.0 / 3.0)
    return max(1, int(np.floor(min(b, np.ceil(min(3 * np.sqrt(n), n / 3))) + 0.5)))


_CHUOI_PW = [(r, n, h) for r in (-0.8, -0.4, 0.0, 0.3, 0.6, 0.9, 0.97) for n in (40, 113, 252, 600) for h in (1, 2)]


def test_pw_bang_ban_dung_lai_khac_cau_truc_tren_56_chuoi():
    sai = [(r, n, h, sd.do_dai_politis_white(_ar1(r, n, h)), _pw_tham_chieu(_ar1(r, n, h)))
           for r, n, h in _CHUOI_PW if sd.do_dai_politis_white(_ar1(r, n, h)) != _pw_tham_chieu(_ar1(r, n, h))]
    assert not sai, sai


def test_pw_cham_du_cac_nhanh_cua_quy_tac():
    """Bộ chuỗi trên phải CHẠM: khối 1 do ĝ ≤ 0 hay nhiễu trắng, khối bị cắt ở cận, và m̂ rơi về m_max (chuỗi rất dai)."""
    ket = {(r, n, h): sd.do_dai_politis_white(_ar1(r, n, h)) for r, n, h in _CHUOI_PW}
    tran = lambda n: int(np.ceil(min(3 * np.sqrt(n), n / 3)))      # noqa: E731
    assert any(v == 1 for v in ket.values())
    assert any(v == tran(n) for (r, n, h), v in ket.items()), "không chuỗi nào chạm cận trên"
    assert len({v for v in ket.values()}) >= 12, sorted(set(ket.values()))
    assert max(ket[(0.97, 600, h)] for h in (1, 2)) > 20


# số vàng: kết quả của hàm tại lúc viết, trên chuỗi dựng lại được bằng `_ar1` (hạt cố định)
SO_VANG_PW = {(0.0, 252, 1): 5, (0.6, 252, 1): 9, (0.9, 113, 2): 14, (0.97, 40, 1): 10, (-0.8, 40, 2): 1}


def test_pw_so_vang():
    for khoa, mong in SO_VANG_PW.items():
        r, n, h = khoa
        assert sd.do_dai_politis_white(_ar1(r, n, h)) == mong, (khoa, sd.do_dai_politis_white(_ar1(r, n, h)))


# ── 2. ktc_khoi_co_cap nhận quy tắc ───────────────────────────────────────────────────────────
def test_ktc_voi_quy_tac_PW_dung_do_dai_pw_cua_chuoi():
    x = _ar1(0.6, 252, 5)
    k = sd.ktc_khoi_co_cap(x, do_dai=sd.QUY_TAC_PW)
    L = sd.do_dai_politis_white(x)
    assert (k["do_dai"], k["do_dai_yeu_cau"], k["so_khoi"]) == (L, "PW", -(-252 // L))
    k2 = sd.ktc_khoi_co_cap(x, do_dai=L)
    assert (k["can_duoi"], k["can_tren"], k["tb"]) == (k2["can_duoi"], k2["can_tren"], k2["tb"])


def test_ktc_dang_cap_tinh_quy_tac_tren_hieu_a_tru_b():
    a = _ar1(0.9, 300, 7)
    b = a.copy()                                   # a − b ≡ 0: chuỗi hằng → khối 1, bất kể a rất tự tương quan
    assert sd.ktc_khoi_co_cap(a, b, do_dai="PW")["do_dai"] == 1
    assert sd.do_dai_politis_white(a) > 3
    c = _ar1(0.0, 300, 8)
    assert sd.ktc_khoi_co_cap(a, c, do_dai="PW")["do_dai"] == sd.do_dai_politis_white(a - c)


@pytest.mark.parametrize("n, mong", [(40, 4), (113, 5), (252, 7), (27, 3), (125, 5), (126, 6), (1000, 10)])
def test_quy_tac_N13_la_tran_can_bac_ba_cua_n(n, mong):
    assert sd.do_dai_theo_quy_tac("N13", np.zeros(n)) == mong
    assert sd.ktc_khoi_co_cap(np.random.default_rng(n).normal(size=n), do_dai="N13")["do_dai"] == mong


def test_quy_tac_la_NO():
    with pytest.raises(ValueError):
        sd.ktc_khoi_co_cap([1.0, 2.0, 3.0, 4.0], do_dai="la")
    with pytest.raises(ValueError):
        sd.ktc_khoi_co_cap([1.0, 2.0, 3.0, 4.0], do_dai=5)


def test_nhan_do_dai():
    assert [sd.nhan_do_dai(v) for v in (10, np.int64(5), "PW", "N13")] == ["L10", "L5", "PW", "N13"]


# ── 3. bộ chọn ────────────────────────────────────────────────────────────────────────────────
def _sinh_trang(n: int, so_lan: int, hat: int = 0) -> tuple:
    r = np.random.default_rng([hat, n])
    a, b = r.normal(size=(2, so_lan, n))
    return a, b, a


def test_o_khong_xac_dinh_khi_khoi_co_dinh_dai_hon_n_va_khong_dat():
    assert sd.do_phu_mot_o(40, 42, "mot_chuoi", so_lan=4, vong=50, chuoi=_sinh_trang(40, 4)) is None
    assert sd.do_phu_mot_o(40, 40, "mot_chuoi", so_lan=4, vong=50, chuoi=_sinh_trang(40, 4)) is not None   # L = n: xác định
    assert sd.do_phu_mot_o(40, "PW", "tho", so_lan=4, vong=50, chuoi=_sinh_trang(40, 4)) is not None
    assert sd.o_dat(None) is False
    assert sd.o_dat(0.9) is True and sd.o_dat(0.8999) is False


def test_ung_vien_dat_can_ca_chin_o():
    bang = {str(n): {d: 0.95 for d in sd.DANG_KTC} for n in sd.LUOI_N}
    assert sd.ung_vien_dat(bang)
    for n in sd.LUOI_N:
        for d in sd.DANG_KTC:
            xau = {k: dict(v) for k, v in bang.items()}
            xau[str(n)][d] = 0.899
            assert not sd.ung_vien_dat(xau), (n, d)
            xau[str(n)][d] = None
            assert not sd.ung_vien_dat(xau), (n, d)
    thieu = dict(bang)
    del thieu["113"]
    assert not sd.ung_vien_dat(thieu)


def test_chon_dung_o_ung_vien_dau_tien_dat_va_khong_chay_ung_vien_sau_no(monkeypatch):
    monkeypatch.setattr(sd, "NGUONG_DO_PHU", 0.0)             # mọi ô ĐÃ XÁC ĐỊNH đều đạt; ô None thì không
    da_chay = []
    kq = sd.chon_ung_vien(ung_vien=(42, 3, 5), luoi_n=(40,), so_lan=6, vong=50, sinh=_sinh_trang,
                          ghi=lambda nhan, bang, dat: da_chay.append((nhan, dat)))
    assert da_chay == [("L42", False), ("L3", True)]           # L5 KHÔNG được chạy
    assert kq["chot"] == "L3" and [t for t, _ in kq["da_thu"]] == ["L42", "L3"]
    assert kq["da_thu"][0][1]["40"] == {"cap": None, "mot_chuoi": None, "tho": None}


def test_chon_khong_chot_gi_khi_khong_ung_vien_nao_dat(monkeypatch):
    monkeypatch.setattr(sd, "NGUONG_DO_PHU", 1.01)
    da_chay = []
    kq = sd.chon_ung_vien(ung_vien=(42, 3, "PW"), luoi_n=(40,), so_lan=4, vong=50, sinh=_sinh_trang,
                          ghi=lambda nhan, bang, dat: da_chay.append(nhan))
    assert kq["chot"] is None and da_chay == ["L42", "L3", "PW"]


def test_chon_dung_toan_bo_chin_o_khong_chi_mot_n(monkeypatch):
    """Ứng viên đạt ở n = 113 mà hỏng ở n = 40 vẫn KHÔNG đạt."""
    monkeypatch.setattr(sd, "NGUONG_DO_PHU", 0.0)
    kq = sd.chon_ung_vien(ung_vien=(50,), luoi_n=(40, 113), so_lan=4, vong=50, sinh=_sinh_trang)
    assert kq["chot"] is None                                   # L = 50 > 40 → ô n = 40 là None


def test_do_phu_mot_o_dem_dung_ty_le_voi_quy_tac():
    khong = np.zeros((6, 40))
    assert sd.do_phu_mot_o(40, "PW", "mot_chuoi", so_lan=6, vong=50, chuoi=(khong, khong, khong)) == 1.0
    mot = np.ones((6, 40))
    assert sd.do_phu_mot_o(40, "N13", "mot_chuoi", so_lan=6, vong=50, chuoi=(mot, mot, mot)) == 0.0


# ── 4. thứ tự đã khai ─────────────────────────────────────────────────────────────────────────
def test_thu_tu_ung_vien_dung_ban_khai_o_muc_8_4b():
    assert sd.UNG_VIEN_KTC == (42, 63, 21, "PW", 10, "N13", 5)
    assert sd.SO_LAN_CHON == 10_000
    dac_ta = (GOC / "docs" / "thiet-ke-c1-san-dau.md").read_text(encoding="utf-8")
    muc = dac_ta[dac_ta.index("### 8.4b"):dac_ta.index("### 8.5")]
    nhan = ["`L` = 42", "`L` = 63", "`L` = 21", "Politis–White", "`L` = 10", "`L` = ⌈n^(1/3)⌉", "`L` = 5"]
    vi_tri = [muc.index(t) for t in nhan]
    assert vi_tri == sorted(vi_tri), "thứ tự ứng viên trong đặc tả phải là thứ tự khai"
    assert "10.000" in muc


def test_lenh_chon_in_va_ma_thoat(monkeypatch, capsys):
    cli = _nap_cli()
    monkeypatch.setattr(sd, "UNG_VIEN_KTC", (42, 3))
    monkeypatch.setattr(sd, "NGUONG_DO_PHU", 0.0)
    a = cli.dung_parser().parse_args(["do-phu", "--chon", "--so-lan-chon", "3", "--hat", "0"])
    assert a.ham(a) == cli.MA_BANG_NHAU
    ra = capsys.readouterr().out
    assert "CHON UNG VIEN KTC" in ra and "CHOT: L3" in ra and "KHONG DAT" in ra
    monkeypatch.setattr(sd, "NGUONG_DO_PHU", 1.01)
    a = cli.dung_parser().parse_args(["do-phu", "--chon", "--so-lan-chon", "3"])
    assert a.ham(a) == cli.MA_KHAC
    assert "KHONG UNG VIEN NAO DAT" in capsys.readouterr().out
