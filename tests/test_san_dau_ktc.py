"""Gác cho Lát 3b của C1 (BƯỚC 243): KTC bootstrap khối vòng CÓ CẶP, phép thử độ phủ ở n = 40, 113, 252, nhãn độ phủ
trên mọi KTC mà `tools/san_dau.py bang` in, và lệnh `do-phu` (`docs/thiet-ke-c1-san-dau.md` mục 8.3, 8.4, 10.2, 11 G6).

MÁY ĐO cũng bị nghi ngờ như gác (skill, Bước 3 điều 4): một KTC sai chỉ IN một khoảng nghe hợp lý, và một phép thử
độ phủ hỏng cho ra con số "độ phủ" nghe hợp lý. Nên có năm lớp:
  1. hàm KTC bằng bản dựng chỉ số TƯỜNG MINH (mỗi lần rút ghép khối rồi cắt về n) và bằng số tính tay;
  2. máy đo đi qua một ca THẬT đã biết trước: dữ liệu iid với khối 1 phải phủ ~95% (kết quả ÂM của phép thử độ phủ
     chỉ đáng tin khi máy cho được kết quả DƯƠNG);
  3. CẶP: một bộ khối cho hai chuỗi, không phải hai bộ;
  4. mô hình sinh của phép thử độ phủ đúng như đặc tả (trung bình 0, tự tương quan, thành phần chung, đoạn không giữ,
     đuôi dày) và file `docs/san-dau-do-phu.json` đã commit khớp mã;
  5. mọi KTC in ra mang nhãn độ phủ, và chuỗi KTC danh nghĩa chỉ được ghép ở MỘT hàm (gác G6).
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import numpy as np
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.append(str(GOC / "tools"))

import san_dau as sd  # noqa: E402
import sinh_bang_vang_phien as S  # noqa: E402
from test_san_dau import _nap_cli, _sach_cache_phan_tich  # noqa: E402
from test_san_dau_bang import _dung  # noqa: E402

assert _sach_cache_phan_tich  # fixture autouse nhập từ test_san_dau, giữ trong module này

DUONG_MODULE = GOC / "san_dau.py"
DUONG_CLI = GOC / "tools" / "san_dau.py"
DUONG_DO_PHU = GOC / "docs" / "san-dau-do-phu.json"


def _chua_0(k: dict) -> bool:
    return k["can_duoi"] <= 0.0 <= k["can_tren"]


# ── 1. hàm KTC ────────────────────────────────────────────────────────────────────────────────
def _ktc_tuong_minh(a, b, do_dai, vong, hat):
    """Bản dựng CHỈ SỐ tường minh: mỗi lần rút ghép ceil(n/L) khối vòng dài L rồi cắt về n."""
    a = np.asarray(a, float)
    n = a.size
    so_khoi = -(-n // do_dai)
    dau = np.random.default_rng(hat).integers(0, n, size=(vong, so_khoi))
    idx = ((dau[:, :, None] + np.arange(do_dai)) % n).reshape(vong, -1)[:, :n]
    boot = a[idx].mean(axis=1)
    if b is not None:
        boot = boot - np.asarray(b, float)[idx].mean(axis=1)
    return np.percentile(boot, [2.5, 97.5])


@pytest.mark.parametrize("n, do_dai", [(40, 10), (40, 21), (113, 10), (113, 5), (252, 21), (23, 10), (7, 7), (9, 4), (10, 1)])
def test_ktc_bang_ban_dung_chi_so_tuong_minh__ca_khoi_cuoi_bi_cat_va_ca_co_cap_lan_mot_chuoi(n, do_dai):
    rng = np.random.default_rng(1000 + n)
    a, b = rng.standard_normal(n), rng.standard_t(4, n)
    for cap in (b, None):
        k = sd.ktc_khoi_co_cap(a, cap, do_dai=do_dai, vong=700, hat=3)
        lo, hi = _ktc_tuong_minh(a, cap, do_dai, 700, 3)
        assert (k["can_duoi"], k["can_tren"]) == pytest.approx((lo, hi), abs=1e-12), (n, do_dai, cap is None)
        assert k["so_khoi"] == -(-n // do_dai) and k["n"] == n and k["do_dai"] == do_dai
        assert k["tb"] == pytest.approx(a.mean() - (b.mean() if cap is not None else 0.0))


def test_ktc_so_tay__khoi_dai_bang_n_thi_moi_lan_rut_bang_trung_binh_that():
    """Khối dài n: mỗi khối là một vòng xoay trọn của chuỗi nên trung bình bootstrap LUÔN bằng trung bình thật."""
    k = sd.ktc_khoi_co_cap([1.0, 2.0, 6.0, 7.0], do_dai=4, vong=200)
    assert k["can_duoi"] == pytest.approx(4.0) and k["can_tren"] == pytest.approx(4.0) and k["tb"] == pytest.approx(4.0)


def test_ktc_so_tay__chuoi_4_phien_khoi_2_chi_nhan_cac_gia_tri_dem_duoc():
    """a = [1,2,3,4], L = 2: tổng khối vòng từ mỗi điểm đầu = [3,5,7,5]; hai khối ghép nên trung bình bootstrap =
    (s_i + s_j)/4. Nhỏ nhất (3+3)/4 = 1,5 và lớn nhất (7+7)/4 = 3,5, mỗi giá trị xảy ra với xác suất 1/16 (~312 trên
    5000 lần rút, nhiều hơn xa 2,5% = 125), nên khoảng là ĐÚNG [1,5 ; 3,5]; trung bình thật 2,5."""
    k = sd.ktc_khoi_co_cap([1.0, 2.0, 3.0, 4.0], do_dai=2)
    assert (k["can_duoi"], k["can_tren"], k["tb"]) == (1.5, 3.5, 2.5)


def test_ktc_chuoi_hang_so_co_khoang_suy_bien_va_dich_chuoi_thi_khoang_dich_theo():
    k0 = sd.ktc_khoi_co_cap(np.full(60, 0.37), do_dai=10)
    assert k0["can_duoi"] == pytest.approx(0.37) and k0["can_tren"] == pytest.approx(0.37)
    x = np.random.default_rng(4).standard_normal(80)
    k1, k2 = sd.ktc_khoi_co_cap(x, do_dai=10), sd.ktc_khoi_co_cap(x + 5.0, do_dai=10)
    assert k2["can_duoi"] == pytest.approx(k1["can_duoi"] + 5.0) and k2["can_tren"] == pytest.approx(k1["can_tren"] + 5.0)
    assert k1["can_duoi"] < k1["tb"] < k1["can_tren"]


def test_ktc_cap_la_mean_A_tru_mean_B_va_dao_cho_thi_dao_dau():
    rng = np.random.default_rng(8)
    a, b = rng.standard_normal(90) + 1.0, rng.standard_normal(90)
    k_ab, k_ba = sd.ktc_khoi_co_cap(a, b, do_dai=10), sd.ktc_khoi_co_cap(b, a, do_dai=10)
    assert k_ab["tb"] == pytest.approx(a.mean() - b.mean()) and k_ba["tb"] == pytest.approx(-k_ab["tb"])
    assert k_ba["can_duoi"] == pytest.approx(-k_ab["can_tren"]) and k_ba["can_tren"] == pytest.approx(-k_ab["can_duoi"])


def test_ktc_cap_MOT_bo_khoi_cho_hai_chuoi__bang_ktc_cua_chuoi_hieu_va_hep_hon_hai_bo_khoi_doc_lap():
    """Phần chung của hai chuỗi chỉ triệt tiêu khi dùng CÙNG khối. Rút khối ĐỘC LẬP cho B thì khoảng rộng hơn nhiều
    và KHÔNG bằng KTC của chuỗi hiệu."""
    rng = np.random.default_rng(21)
    n = 120
    chung = np.convolve(rng.standard_normal(n + 19), np.ones(20) / 20, "valid") * 4.0
    a = chung + 0.3 * rng.standard_normal(n)
    b = chung + 0.3 * rng.standard_normal(n)
    cap = sd.ktc_khoi_co_cap(a, b, do_dai=10)
    hieu = sd.ktc_khoi_co_cap(a - b, do_dai=10)
    assert (cap["can_duoi"], cap["can_tren"]) == pytest.approx((hieu["can_duoi"], hieu["can_tren"]), abs=1e-9)
    doc_lap = sd.ktc_khoi_co_cap(a, do_dai=10, hat=0)
    doc_lap_b = sd.ktc_khoi_co_cap(b, do_dai=10, hat=1)
    rong_doc_lap = (doc_lap["can_tren"] - doc_lap["can_duoi"]) + (doc_lap_b["can_tren"] - doc_lap_b["can_duoi"])
    assert (cap["can_tren"] - cap["can_duoi"]) * 3 < rong_doc_lap


def test_ktc_khoi_dai_thi_khoang_rong_hon_khoi_1_tren_chuoi_tu_tuong_quan():
    """Chuỗi gồm các đoạn hằng số ngẫu nhiên dấu: khối 1 coi từng phiên độc lập (khoảng hẹp, sai), khối 10 giữ được
    đoạn (khoảng rộng, đúng)."""
    rng = np.random.default_rng(2)
    x = np.repeat(rng.choice([-1.0, 1.0], 12), 10)
    w1, w10 = (sd.ktc_khoi_co_cap(x, do_dai=d) for d in (1, 10))
    assert (w10["can_tren"] - w10["can_duoi"]) > 2 * (w1["can_tren"] - w1["can_duoi"])


def test_ktc_hat_giong_co_dinh_va_hat_khac_cho_khoang_khac():
    x = np.random.default_rng(6).standard_normal(70)
    k0, k0b, k1 = (sd.ktc_khoi_co_cap(x, do_dai=10, hat=h) for h in (0, 0, 1))
    assert k0 == k0b and k0["hat"] == 0 and k0["vong"] == sd.VONG_KTC == 5000
    assert (k0["can_duoi"], k0["can_tren"]) != (k1["can_duoi"], k1["can_tren"])


def test_ktc_nho_dau_vao_sai_thi_NO():
    with pytest.raises(ValueError):
        sd.ktc_khoi_co_cap([1.0, 2.0], [1.0, 2.0, 3.0], do_dai=1)
    with pytest.raises(ValueError):
        sd.ktc_khoi_co_cap([1.0, 2.0, 3.0], [1.0, 2.0], do_dai=1)
    with pytest.raises(ValueError):
        sd.ktc_khoi_co_cap([1.0, 2.0, 3.0], do_dai=4)
    with pytest.raises(ValueError):
        sd.ktc_khoi_co_cap([1.0, 2.0, 3.0], do_dai=0)
    with pytest.raises(ValueError):
        sd.ktc_khoi_co_cap([])


def test_hang_so_dac_ta_8_3_va_8_4():
    assert (sd.DO_DAI_KHOI, sd.DO_DAI_KHOI_NHAY) == (10, (5, 21))
    assert (sd.VONG_KTC, sd.HAT_KTC, sd.PHAN_VI_KTC) == (5000, 0, (2.5, 97.5))
    assert (sd.LUOI_N, sd.SO_LAN_LAP_DO_PHU, sd.HAT_DO_PHU, sd.NGUONG_DO_PHU) == ((40, 113, 252), 2000, 0, 0.90)
    import paper_metrics as pm
    import inspect
    assert "VONG = 5000" in inspect.getsource(pm.vs_benchmark), "cùng VONG với vs_benchmark"


# ── 2. máy đo đi qua ca THẬT đã biết trước ────────────────────────────────────────────────────
@pytest.mark.parametrize("n", [40, 113, 252])
def test_may_do_do_phu_cho_KET_QUA_DUONG__iid_voi_khoi_1_phu_gan_95_phan_tram(n):
    """Trước khi tin một kết quả ÂM (độ phủ thấp): máy đo CÓ khả năng cho kết quả dương không? Dữ liệu iid, khối 1
    là bootstrap thường: độ phủ gần danh nghĩa. Nếu hàm KTC hay phép đếm sai thì ô này lệch."""
    rng = np.random.default_rng(77 + n)
    lap = 400
    x = rng.standard_normal((lap, n))
    phu = np.mean([_chua_0(sd.ktc_khoi_co_cap(x[i], do_dai=1, vong=1000)) for i in range(lap)])
    assert 0.91 <= phu <= 0.985, (n, phu)


def test_do_phu_mot_o_dem_dung_ty_le_va_dung_dau_bang_khi_khoang_la_diem_0():
    """Khoảng [0, 0] (chuỗi toàn 0) CHỨA 0: so sánh `<=` hai đầu. Dạng chuỗi cũng đi đúng nhánh."""
    khong = np.zeros((6, 40))
    for dang in sd.DANG_KTC:
        assert sd.do_phu_mot_o(40, 10, dang, so_lan=6, vong=50, chuoi=(khong, khong, khong)) == 1.0
    # hằng số 1: khoảng [1, 1] không chứa 0
    mot = np.ones((6, 40))
    for dang in sd.DANG_KTC:
        assert sd.do_phu_mot_o(40, 10, dang, so_lan=6, vong=50, chuoi=(mot, 0 * mot, mot)) == 0.0
    # dạng nào đọc chuỗi nào: cặp = A − B; một chuỗi = A; thô = A_tho
    a, b, tho = np.ones((5, 40)), np.ones((5, 40)), np.zeros((5, 40))
    assert sd.do_phu_mot_o(40, 10, "cap", so_lan=5, vong=50, chuoi=(a, b, tho)) == 1.0      # 1 − 1 = 0
    assert sd.do_phu_mot_o(40, 10, "mot_chuoi", so_lan=5, vong=50, chuoi=(a, b, tho)) == 0.0   # A = 1
    assert sd.do_phu_mot_o(40, 10, "tho", so_lan=5, vong=50, chuoi=(a, b, tho)) == 1.0        # A_tho = 0
    with pytest.raises(ValueError):
        sd.do_phu_mot_o(40, 10, "dang_la", so_lan=2, vong=50)


# ── 3. mô hình sinh của phép thử độ phủ ───────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def chuoi_sinh():
    return sd.sinh_chuoi_do_phu(252, 400)


def _cap_ke_nhau_khac_0(a):
    x, y = a[:, :-1], a[:, 1:]
    ok = (x != 0) & (y != 0)
    return x[ok], y[ok]


def test_mo_hinh_sinh_trung_binh_that_bang_0_va_phan_doan_khong_giu_dung_dac_ta(chuoi_sinh):
    a, b, a_tho = chuoi_sinh
    assert a.shape == b.shape == a_tho.shape == (400, 252)
    assert abs(a.mean()) < 0.05 and abs(b.mean()) < 0.05 and abs(a_tho.mean()) < 0.05
    ty_le_khong = float((a == 0).mean())
    ky_vong = (1 / sd.TB_DOAN_GIU) / (1 / sd.TB_DOAN_GIU + sd.P_VAO_GIU)      # tỷ lệ KHÔNG giữ ở phân phối dừng
    assert ky_vong == pytest.approx(0.4) and abs(ty_le_khong - ky_vong) < 0.04, ty_le_khong
    assert ((a == 0) == (b == 0)).all(), "A và B chung mặt nạ không giữ"
    assert (a_tho != 0).all() and np.array_equal(a_tho * (a != 0), a)


def test_mo_hinh_sinh_tu_tuong_quan_thanh_phan_chung_va_duoi_day(chuoi_sinh):
    a, b, a_tho = chuoi_sinh
    x, y = _cap_ke_nhau_khac_0(a)
    rho1 = float(np.corrcoef(x, y)[0, 1])
    assert 0.90 < rho1 < 0.99, rho1                       # trung bình trượt 20 phiên: ρ(1) = 19/20
    ok = (a != 0)
    rho_ab = float(np.corrcoef(a[ok], b[ok])[0, 1])
    assert 0.40 < rho_ab < 0.60, rho_ab                   # TY_TRONG_CHUNG = 0,5
    # đuôi dày t4: phương sai t4 = 2 (t100 = 1,02); mô hình có phương sai ~ 2 trước mặt nạ
    assert 1.5 < float(a_tho.var()) < 2.6, float(a_tho.var())
    # độc lập giữa phần riêng: sinh hai lần cùng hạt thì GIỐNG nhau, đổi n hay hạt thì khác
    assert all(np.array_equal(p, q) for p, q in zip(sd.sinh_chuoi_do_phu(252, 400), chuoi_sinh))
    assert not np.array_equal(sd.sinh_chuoi_do_phu(113, 4)[2][0, :10], sd.sinh_chuoi_do_phu(252, 4)[2][0, :10])
    assert not np.array_equal(sd.sinh_chuoi_do_phu(40, 4, hat=1)[0], sd.sinh_chuoi_do_phu(40, 4, hat=0)[0])


# ── 4. file đã commit ─────────────────────────────────────────────────────────────────────────
def _bang_that() -> dict:
    return json.loads(DUONG_DO_PHU.read_text(encoding="utf-8"))


def test_file_do_phu_da_commit_hop_le_va_khop_hang_so_cua_ma():
    bang = _bang_that()
    assert sd.vi_pham_bang_do_phu(bang) == []
    assert set(bang["do_phu"]) == {"L10", "L5", "L21"} and list(bang["tham_so"]["luoi_n"]) == [40, 113, 252]
    for theo_n in bang["do_phu"].values():
        for o in theo_n.values():
            assert set(o) == set(sd.DANG_KTC) and all(0.0 <= p <= 1.0 for p in o.values())
    assert bang["sai_so_monte_carlo_toi_da"] == pytest.approx(
        max(float(np.sqrt(p * (1 - p) / bang["tham_so"]["so_lan_lap"])) for o in
            (x for t in bang["do_phu"].values() for x in t.values()) for p in o.values()))


@pytest.mark.parametrize("ld, n, dang", [("L10", 40, "cap"), ("L21", 40, "mot_chuoi"), ("L5", 40, "tho")])
def test_file_do_phu_da_commit_BANG_do_lai_o_ba_o_n_40(ld, n, dang):
    """Ghim file vào mã: đổi hàm KTC, mô hình sinh hay phép đếm mà không chạy lại `do-phu` thì ô này lệch. Ba ô ở
    n = 40 (đo lại đủ 2000 lần, vài giây mỗi ô); cả file đo lại bằng `tools/san_dau.py do-phu --kiem`."""
    do_dai = int(ld[1:])
    p = sd.do_phu_mot_o(n, do_dai, dang)
    assert p == _bang_that()["do_phu"][ld][str(n)][dang]


def test_dung_bang_do_phu_sai_so_monte_carlo_la_can_p_1_tru_p_chia_so_lan_cua_o_xau_nhat():
    dp = {"L10": {"40": {"cap": 0.5, "mot_chuoi": 0.9, "tho": 0.0}}}
    b = sd.dung_bang_do_phu(dp, so_lan=2000)
    assert b["sai_so_monte_carlo_toi_da"] == pytest.approx((0.25 / 2000) ** 0.5)
    b = sd.dung_bang_do_phu({"L10": {"40": {"cap": 0.9, "mot_chuoi": 1.0, "tho": 0.0}}}, so_lan=100)
    assert b["sai_so_monte_carlo_toi_da"] == pytest.approx((0.09 / 100) ** 0.5)
    assert b["tham_so"]["so_lan_lap"] == 100 and b["do_phu"]["L10"]["40"]["cap"] == 0.9


def test_vi_pham_bang_do_phu_bat_file_lech_hang_so_thieu_o_va_ty_le_vo_ly():
    bang = _bang_that()
    assert sd.vi_pham_bang_do_phu(bang) == []
    for sua in (lambda b: b["tham_so"].update(hat=1), lambda b: b["tham_so"].update(so_lan_lap=100),
                lambda b: b["tham_so"].update(luoi_n=[40, 113]), lambda b: b["mo_hinh"].update(bac_tu_do_t=30),
                lambda b: b["mo_hinh"].update(cua_so_vi_the=1), lambda b: b["mo_hinh"].update(tb_doan_giu=3),
                lambda b: b["do_phu"]["L10"].pop("113"), lambda b: b["do_phu"]["L21"]["252"].pop("tho"),
                lambda b: b["do_phu"]["L5"]["40"].update(cap=1.2), lambda b: b["do_phu"]["L5"]["40"].update(cap=True),
                lambda b: b.pop("do_phu")):
        x = json.loads(json.dumps(bang))
        sua(x)
        assert sd.vi_pham_bang_do_phu(x), sua
    assert sd.vi_pham_bang_do_phu([]) and sd.vi_pham_bang_do_phu(None)


# ── 5. nhãn độ phủ ────────────────────────────────────────────────────────────────────────────
def _bang_gia(ghi_de: dict | None = None) -> dict:
    """Bảng độ phủ tổng hợp: mọi ô 0,93, trừ ô được ghi đè {(L, n, dạng): p}."""
    dp = {f"L{ld}": {str(n): {d: 0.93 for d in sd.DANG_KTC} for n in sd.LUOI_N}
          for ld in (sd.DO_DAI_KHOI, *sd.DO_DAI_KHOI_NHAY)}
    for (ld, n, d), p in (ghi_de or {}).items():
        dp[f"L{ld}"][str(n)][d] = p
    return sd.dung_bang_do_phu(dp)


KTC_MAU = {"can_duoi": -0.1234, "can_tren": 0.4321}


def test_nhan_n_nho_hon_40_la_mau_qua_ngan_va_khong_in_KTC_hay_95():
    for n in (1, 23, 39):
        dong = sd.dinh_dang_ktc(n, "cap", None, _bang_gia())
        assert dong.startswith("mẫu quá ngắn") and f"n={n} < 40" in dong and "không in KTC" in dong
        assert "95" not in dong and "0.4321" not in dong
    # KHÔNG có bảng độ phủ cũng không in 95 (n đủ lớn nhưng chưa đo)
    dong = sd.dinh_dang_ktc(90, "cap", KTC_MAU, None)
    assert "95" not in dong and "chưa có bảng độ phủ" in dong and "-0.123" not in dong


@pytest.mark.parametrize("n, n_luoi", [(40, 40), (41, 40), (112, 40), (113, 113), (200, 113), (251, 113),
                                       (252, 252), (253, 252), (10_000, 252)])
def test_nhan_n_khong_co_tren_luoi_dung_diem_luoi_lon_nhat_khong_vuot_n(n, n_luoi):
    dong = sd.dinh_dang_ktc(n, "mot_chuoi", KTC_MAU, _bang_gia())
    assert f"(n={n_luoi}, L=10)" in dong
    assert dong.startswith("KTC danh nghĩa 95% [-0.123 ; +0.432] — độ phủ đo được 93.0% (")


def test_nhan_do_phu_duoi_90_them_nhan_mau_qua_ngan_va_tu_90_tro_len_thi_khong():
    bang = _bang_gia({(10, 113, "cap"): 0.8999, (10, 252, "cap"): 0.90, (10, 40, "cap"): 0.5905,
                        (10, 113, "tho"): 0.0})
    thap = sd.dinh_dang_ktc(113, "cap", KTC_MAU, bang)
    assert thap.endswith("mẫu quá ngắn: độ phủ đo được dưới 90%") and "độ phủ đo được 90.0%" in thap
    dung = sd.dinh_dang_ktc(252, "cap", KTC_MAU, bang)
    assert "dưới 90%" not in dung and "mẫu quá ngắn" not in dung and "độ phủ đo được 90.0%" in dung
    assert "độ phủ đo được 59.1%" in sd.dinh_dang_ktc(40, "cap", KTC_MAU, bang)
    assert "độ phủ đo được 0.0%" in sd.dinh_dang_ktc(113, "tho", KTC_MAU, bang)
    # mỗi DẠNG đọc cột của MÌNH
    assert "độ phủ đo được 93.0%" in sd.dinh_dang_ktc(113, "mot_chuoi", KTC_MAU, bang)


def test_nhan_doc_dung_do_dai_khoi_va_o_chua_do_thi_khong_in():
    bang = _bang_gia({(21, 113, "cap"): 0.61})
    assert "độ phủ đo được 93.0%" in sd.dinh_dang_ktc(113, "cap", KTC_MAU, bang, do_dai=10)
    dong = sd.dinh_dang_ktc(113, "cap", KTC_MAU, bang, do_dai=21)
    assert "độ phủ đo được 61.0% (n=113, L=21)" in dong
    bang["do_phu"]["L10"]["113"].pop("cap")
    dong = sd.dinh_dang_ktc(113, "cap", KTC_MAU, bang)
    assert "chưa đo độ phủ" in dong and "95" not in dong


def test_ktc_co_nhan_chi_tinh_KTC_khi_se_duoc_in_va_ghep_dung_hai_chuoi():
    rng = np.random.default_rng(5)
    a, b = rng.standard_normal(90), rng.standard_normal(90)
    kq = sd.ktc_co_nhan(a, b, "cap", _bang_gia())
    ref = sd.ktc_khoi_co_cap(a, b)
    assert kq["n"] == 90 and kq["ktc"] == ref and kq["dong"] == sd.dinh_dang_ktc(90, "cap", ref, _bang_gia())
    assert sd.ktc_co_nhan(a[:23], None, "tho", _bang_gia())["ktc"] is None
    assert sd.ktc_co_nhan(a, None, "tho", None)["ktc"] is None and "95" not in sd.ktc_co_nhan(a, None, "tho", None)["dong"]
    assert sd.ktc_co_nhan(a, None, "tho", _bang_gia())["ktc"] == sd.ktc_khoi_co_cap(a)


# ── 6. G6: nơi DUY NHẤT ghép "95%" ────────────────────────────────────────────────────────────
def _chuoi_95(duong: Path) -> list[tuple[str, str]]:
    """Mọi hằng chuỗi (bỏ docstring) có "95%", kèm tên hàm bao quanh."""
    cay = ast.parse(duong.read_text(encoding="utf-8"))
    ra: list = []

    def duyet(nut, ham):
        for con in ast.iter_child_nodes(nut):
            ten = con.name if isinstance(con, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) else ham
            if isinstance(con, ast.Constant) and isinstance(con.value, str) and "95%" in con.value:
                ra.append((ham, con.value))
            duyet(con, ten)

    # bỏ docstring
    for n in ast.walk(cay):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body and isinstance(n.body[0], ast.Expr) \
                and isinstance(n.body[0].value, ast.Constant) and isinstance(n.body[0].value.value, str):
            n.body[0].value.value = ""
    duyet(cay, "<module>")
    return ra


def test_G6_chuoi_KTC_danh_nghia_95_chi_duoc_ghep_o_dinh_dang_ktc_va_ngay_trong_chuoi_do_co_do_phu():
    assert _chuoi_95(DUONG_CLI) == [], "tools/san_dau.py chỉ in chuỗi do `sd.dinh_dang_ktc` ghép"
    kq = _chuoi_95(DUONG_MODULE)
    assert [ham for ham, _ in kq] == ["dinh_dang_ktc"], kq
    cay = ast.parse(DUONG_MODULE.read_text(encoding="utf-8"))
    ham = next(n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == "dinh_dang_ktc")
    f_chuoi = [n for n in ast.walk(ham) if isinstance(n, ast.JoinedStr)
               and any(isinstance(v, ast.Constant) and "95%" in str(v.value) for v in n.values)]
    assert len(f_chuoi) == 1
    cac_ben = "".join(str(v.value) for v in f_chuoi[0].values if isinstance(v, ast.Constant))
    # "95%" và "độ phủ đo được" nằm trong CÙNG MỘT f-chuỗi (không thể ghép một cái mà thiếu cái kia)
    assert "KTC danh nghĩa 95%" in cac_ben and "độ phủ đo được" in cac_ben
    assert any(isinstance(v, ast.FormattedValue) for v in f_chuoi[0].values)


def test_G6_phep_do_bat_duoc_mau_xau():
    xau = 'def in_ktc(k):\n    return f"KTC danh nghĩa 95% [{k}]"\n'
    tmp = ast.parse(xau)
    ham = next(n for n in ast.walk(tmp) if isinstance(n, ast.FunctionDef))
    co_95 = [n for n in ast.walk(ham) if isinstance(n, ast.JoinedStr)
             and any(isinstance(v, ast.Constant) and "95%" in str(v.value) for v in n.values)]
    assert co_95 and ham.name != "dinh_dang_ktc"


def test_tab_app_chua_co_nhung_neu_co_thi_khong_ghep_95_rieng():
    """Lát 4 mới thêm tab; từ nay app.py không được tự ghép KTC danh nghĩa."""
    mau = [s for s in (GOC / "app.py").read_text(encoding="utf-8").splitlines() if "KTC danh ngh" in s]
    assert mau == [], mau


# ── 7. KTC trong bảng `bang` ──────────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def bang_co_do_phu(gia_ktc):
    mp = pytest.MonkeyPatch()
    try:
        yield _dung(gia_ktc, mp, do_phu=_bang_gia({(10, 40, "cap"): 0.7, (10, 40, "mot_chuoi"): 0.95,
                                                     (10, 40, "tho"): 0.5}))
    finally:
        mp.undo()


@pytest.fixture(scope="module")
def gia_ktc():
    return S.dung_gia()


def test_bang_moi_KTC_mang_nhan_do_phu_cua_dung_dang_va_thuoc_2_tinh_tren_cap_phien_chung(bang_co_do_phu):
    cli, b, *_ = bang_co_do_phu
    ra: list = []
    cli.in_bang(b, ghi=ra.append)
    van = "\n".join(ra)
    dong_ktc = [d for d in ra if d.lstrip().startswith("KTC thuoc") or d.lstrip().startswith("KTC tho")]
    assert len(b["phuong_an"]) == 2 and len(dong_ktc) == 2 + 3 * 2, "đường thật 2 + mỗi phương án (thước 1, thô, thước 2) × 3"
    for d in dong_ktc:
        assert "KTC danh nghĩa 95%" in d and "độ phủ đo được" in d and "(n=40, L=10)" in d, d
    assert sum("mẫu quá ngắn: độ phủ đo được dưới 90%" in d for d in dong_ktc) == 2 + 3   # thước 2 ×2 (0,70) + thô ×3 (0,50)
    assert all(("độ phủ đo được 95.0%" in d) for d in dong_ktc if d.lstrip().startswith("KTC thuoc 1"))
    assert all(("độ phủ đo được 70.0%" in d) for d in dong_ktc if d.lstrip().startswith("KTC thuoc 2"))
    assert all(("độ phủ đo được 50.0%" in d) for d in dong_ktc if d.lstrip().startswith("KTC tho "))
    # trung bình in cạnh KTC = cộng dồn / n của CHÍNH chuỗi đó (cửa sổ có phiên không giữ lẫn phiên giữ)
    for h, bd in zip([b["that"], *b["phuong_an"]], range(3)):
        t1 = h["thuoc1"]
        l1, l2 = [d for d in dong_ktc if d.lstrip().startswith("KTC thuoc 1")][bd], [
            d for d in dong_ktc if d.lstrip().startswith("KTC tho ")][bd]
        assert f"= {t1['x_cong_don'] / t1['n_phien']:+.3f} diem%/phien, n={t1['n_phien']})" in l1
        assert f"= {t1['tho_cong_don'] / t1['n_phien']:+.3f} diem%/phien, n={t1['n_phien']})" in l2
    for h, d in zip(b["phuong_an"], [x for x in dong_ktc if x.lstrip().startswith("KTC thuoc 2")]):
        assert f"= {h['thuoc2']['cong_don'] / h['thuoc2']['n_phien']:+.3f} diem%/phien, n={h['thuoc2']['n_phien']})" in d
    assert "KTC: khong co (ro la thuoc do" in van and "doc tu docs/san-dau-do-phu.json" in van
    assert "(hai khoi tren: chi gia tri diem, KHONG in KTC)" in van
    assert "chưa có bảng" not in van and b["co_do_phu"] is True


def test_bang_ktc_thuoc_2_la_tren_hieu_tung_phien_cua_cua_so_CHUNG_va_thuoc_1_tren_x(bang_co_do_phu):
    _, b, *_ = bang_co_do_phu
    that = b["that"]
    for h in b["phuong_an"]:
        t2, k2 = h["thuoc2"], h["ktc"]["thuoc2"]
        chung = [d for d in h["phien_dung"] if d in h["r"] and d in that["r"]]
        assert t2["n_phien"] == k2["n"] == len(chung) == len(h["phien_dung"]) < len(b["phien"])    # 5 phiên loại
        d_t = [h["r"][d] - that["r"][d] for d in chung]
        assert k2["ktc"] == sd.ktc_khoi_co_cap([h["r"][d] for d in chung], [that["r"][d] for d in chung])
        assert (k2["ktc"]["can_duoi"], k2["ktc"]["can_tren"]) == pytest.approx(
            tuple(sd.ktc_khoi_co_cap(d_t)[k] for k in ("can_duoi", "can_tren")), abs=1e-9), "cặp = chuỗi hiệu"
        assert k2["ktc"]["tb"] == pytest.approx(t2["cong_don"] / t2["n_phien"])
    for h in [that, *b["phuong_an"]]:
        t1 = h["thuoc1"]
        assert len(t1["x_chuoi"]) == len(t1["tho_chuoi"]) == t1["n_phien"] == h["ktc"]["thuoc1"]["n"]
        assert sum(t1["x_chuoi"]) == pytest.approx(t1["x_cong_don"]) and sum(t1["tho_chuoi"]) == pytest.approx(t1["tho_cong_don"])
        assert h["ktc"]["thuoc1"]["ktc"] == sd.ktc_khoi_co_cap(t1["x_chuoi"])
        assert h["ktc"]["tho"]["ktc"] == sd.ktc_khoi_co_cap(t1["tho_chuoi"])
        assert h["ktc"]["thuoc1"]["dang"] == "mot_chuoi" and h["ktc"]["tho"]["dang"] == "tho"
    assert "thuoc2" not in that["ktc"] and all(h["ktc"]["thuoc2"]["dang"] == "cap" for h in b["phuong_an"])


def test_bang_cua_so_ngan_hon_40_phien_in_mau_qua_ngan_khong_in_KTC(gia_ktc, monkeypatch):
    cli, b, *_ = _dung(gia_ktc, monkeypatch, do_phu=_bang_gia(), den_ngay=S.PHIEN[22])
    assert b["that"]["thuoc1"]["n_phien"] < 40
    ra: list = []
    cli.in_bang(b, ghi=ra.append)
    dong_ktc = [d for d in ra if d.lstrip().startswith("KTC thuoc") or d.lstrip().startswith("KTC tho")]
    assert dong_ktc and all("mẫu quá ngắn (n=" in d and "không in KTC" in d for d in dong_ktc), dong_ktc
    assert not any("95%" in d for d in ra)


def test_bang_khong_co_bang_do_phu_thi_ktc_none_va_khong_in_95(gia_ktc, monkeypatch):
    cli, b, *_ = _dung(gia_ktc, monkeypatch)
    assert b["co_do_phu"] is False
    for h in [b["that"], *b["phuong_an"]]:
        assert all(v["ktc"] is None for v in h["ktc"].values())
    ra: list = []
    cli.in_bang(b, ghi=ra.append)
    assert not any("95%" in d for d in ra)


# ── 8. dụng cụ ────────────────────────────────────────────────────────────────────────────────
def test_doc_bang_do_phu_thieu_file_la_None_file_hong_thi_NO_file_that_doc_duoc(tmp_path):
    cli = _nap_cli()
    assert cli.doc_bang_do_phu(tmp_path / "khong_co.json") is None
    bang = _bang_gia()
    ok = tmp_path / "ok.json"
    ok.write_text(json.dumps(bang), encoding="utf-8")
    assert cli.doc_bang_do_phu(ok) == bang
    bang["do_phu"]["L10"]["40"]["cap"] = 7
    xau = tmp_path / "xau.json"
    xau.write_text(json.dumps(bang), encoding="utf-8")
    with pytest.raises(ValueError):
        cli.doc_bang_do_phu(xau)
    assert cli.doc_bang_do_phu() == _bang_that() and cli.SO_DO_PHU == DUONG_DO_PHU


def test_lenh_do_phu_json_in_bang_hop_le_khong_ghi_file_va_kiem_so_voi_file(tmp_path, capsys):
    cli = _nap_cli()
    truoc = DUONG_DO_PHU.read_bytes()
    assert cli.main(["do-phu", "--json", "--so-lan", "8"]) == cli.MA_BANG_NHAU
    ra = json.loads(capsys.readouterr().out)
    assert ra["tham_so"]["so_lan_lap"] == 8 and set(ra["do_phu"]) == {"L10", "L5", "L21"}
    assert sd.vi_pham_bang_do_phu(ra), "so-lan 8 khác đặc tả nên file in ra KHÔNG hợp lệ với hằng số: gác bắt"
    assert DUONG_DO_PHU.read_bytes() == truoc, "lệnh không ghi file"
    f = tmp_path / "dp.json"
    f.write_text(json.dumps(ra), encoding="utf-8")
    assert cli.main(["do-phu", "--kiem", "--so-lan", "8", "--duong", str(f)]) == cli.MA_BANG_NHAU
    assert "KHOP" in capsys.readouterr().out
    ra["do_phu"]["L10"]["40"]["cap"] = 0.123
    f.write_text(json.dumps(ra), encoding="utf-8")
    assert cli.main(["do-phu", "--kiem", "--so-lan", "8", "--duong", str(f)]) == cli.MA_KHAC
    assert "KHAC" in capsys.readouterr().out
    assert cli.main(["do-phu", "--so-lan", "8"]) == cli.MA_BANG_NHAU
    ban = capsys.readouterr().out
    assert "DO PHU KTC" in ban and " L10    40 " in ban and "L21   252" in ban


def test_lenh_bang_doc_bang_do_phu_tu_co_do_phu_va_canh_bao_khi_thieu_file(gia_ktc, tmp_path, monkeypatch, capsys):
    import sqlite3
    from test_san_dau import _cfg, _chay_that, _khung_vni
    cli = _nap_cli()
    monkeypatch.setattr(sd, "NGAY_TIEN_VE_TRUOC", S.PHIEN[0])
    vni = _khung_vni(gia_ktc)
    so, _ = _chay_that(_cfg(), gia_ktc, vni_df=vni)
    db = tmp_path / "so_tam.db"
    dich = sqlite3.connect(db)
    so.db.backup(dich)
    dich.close()
    so.db.close()
    pa = tmp_path / "pa.json"
    pa.write_text(json.dumps({"phuong_an": {"PB-001": {"lop": "tham_do", "bo_co": {"nghi_sau_lo_ngay": 7},
                  "khai_ngay": S.PHIEN[48], "commit": None, "mo_ta": "x", "ly_do": "y"}}}), encoding="utf-8")
    monkeypatch.setattr(cli, "doc_gia_cache", lambda ds: dict({m: gia_ktc[m] for m in ds if m in gia_ktc},
                                                              **({"VNINDEX": vni} if "VNINDEX" in ds else {})))
    chung = ["bang", "--so-tam", str(db), "--tu-ngay", S.PHIEN[0], "--den-ngay", S.PHIEN[80], "--so-phuong-an", str(pa)]
    dp = tmp_path / "dp.json"
    dp.write_text(json.dumps(_bang_gia({(10, 40, "cap"): 0.66})), encoding="utf-8")
    assert cli.main([*chung, "--do-phu", str(dp)]) == cli.MA_BANG_NHAU
    ra = capsys.readouterr().out
    assert "doc tu docs/san-dau-do-phu.json" in ra and "độ phủ đo được 66.0% (n=40, L=10)" in ra
    assert "CANH BAO: khong co bang do phu" not in ra
    assert cli.main([*chung, "--do-phu", str(tmp_path / "khong_co.json")]) == cli.MA_BANG_NHAU
    ra = capsys.readouterr().out
    assert "CANH BAO: khong co bang do phu" in ra and "95%" not in ra and "KHONG co docs/san-dau-do-phu.json" in ra
    dp.write_text(json.dumps({"tham_so": {}}), encoding="utf-8")
    with pytest.raises(ValueError):
        cli.main([*chung, "--do-phu", str(dp)])


def test_in_bang_do_phu_ghi_thang_o_nao_duoi_90():
    cli = _nap_cli()
    ra: list = []
    cli.in_bang_do_phu(_bang_gia({(10, 113, "cap"): 0.71}), ghi=ra.append)
    van = "\n".join(ra)
    assert "DUOI 90%: cap" in van and van.count("DUOI 90%") == 1
    assert "sai so Monte Carlo toi da" in van
