"""Hiệu chuẩn MDE₈₀ trên thị trường giả (C4 Lát 2, BƯỚC 289; `tools/hieu_chuan_thi_truong_gia.py`).

Đề bài: `docs/thiet-ke-c4-thi-truong-gia.md` mục 4.4, 4.8, 7, 8 ("Lát 2"). Hai loại phép thử:

* GÁC — dụng cụ KHÔNG THỂ trỏ vào dòng hạt 2, 3, 4 (bất biến 7: các dòng ấy dành cho lượt chạy
  chính của Lát 5 sau khi tiêu chí được ký); không ghi gì ngoài một file; không đọc thế giới thật.
* MÁY ĐO — dò nhị phân, khớp probit, Wilson, so sánh `--kiem` được thử trên ca có đáp án biết
  trước; cả quy trình chạy trên bộ ước lượng GIẢ (rẻ, đáp án đã biết) và MỘT lượt thật trên
  thị trường giả qua `cham_xac_nhan.cham`.

Chỉ số thị trường của test nằm ở vai trò `tham_do`, khối 990.000 trở lên (`CHI_SO_TEST`): ngoài
mọi khối của lượt chính ghi trong `docs/thi-truong-gia-hieu-chuan.json`.
"""
import ast
import importlib.util
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
DUONG = GOC / "tools" / "hieu_chuan_thi_truong_gia.py"
_spec = importlib.util.spec_from_file_location("hieu_chuan_thi_truong_gia", DUONG)
H = importlib.util.module_from_spec(_spec)
sys.modules["hieu_chuan_thi_truong_gia"] = H
_spec.loader.exec_module(H)

import cham_bong as cb  # noqa: E402
import thi_truong_gia as T  # noqa: E402

CHI_SO_TEST = 999_001    # vai trò tham_do, khối 990.000+: không thị trường nào của lượt chính
KAPPA_CO = 0.05          # lợi thế rất lớn: G phải bị bắt, H phải bị phạt (ca THẬT đã biết)
_ND = H._ND


# ── gác hạt: chỉ dòng 1 ─────────────────────────────────────────────────────

@pytest.mark.parametrize("luong", [0, 2, 3, 4, 5, 6, 7, 9001, -1, True, 1.0, "1", None])
def test_kiem_luong_nổ_với_moi_dong_khac_1(luong):
    with pytest.raises(ValueError):
        H.kiem_luong(luong)


def test_kiem_luong_nhan_dong_1_ca_kieu_numpy():
    H.kiem_luong(1)
    H.kiem_luong(np.int64(1))
    assert H.LUONG == 1 and H.LUONG_DUOC_PHEP == (1,)


@pytest.mark.parametrize("luong", [2, 3, 4, 5, 6])
def test_moi_duong_vao_bo_sinh_nổ_voi_dong_2_den_6(luong, monkeypatch):
    """Mỗi cửa công khai tới bộ sinh phải nổ VÀ không để bộ sinh chạy (thay bộ sinh bằng bẫy)."""
    def bay(*a, **k):
        raise AssertionError("bo sinh da chay")
    monkeypatch.setattr(T, "sinh_thi_truong", bay)
    monkeypatch.setattr(T, "tinh_su_that", bay)
    with pytest.raises(ValueError, match="dong hat"):
        H.cham_mot_thi_truong(CHI_SO_TEST, 0.01, luong=luong)
    with pytest.raises(ValueError, match="dong hat"):
        H.oracle_mot_mau(CHI_SO_TEST, 0.01, 800, luong=luong)
    with pytest.raises(ValueError, match="dong hat"):
        H._sinh(luong, CHI_SO_TEST, 0.01)
    with pytest.raises(ValueError, match="dong hat"):
        H.kiem_cau_hinh({**H.CAU_HINH_MAC_DINH, "luong": luong})
    with pytest.raises(ValueError, match="dong hat"):
        H.chay({**H.CAU_HINH_MAC_DINH, "luong": luong})


def test_file_ket_qua_bi_sua_sang_dong_khac_thi_doc_nổ(tmp_path):
    ket = {"cau_hinh": {**H.CAU_HINH_MAC_DINH, "luong": 2}}
    p = tmp_path / "x.json"
    p.write_text(json.dumps(ket), encoding="utf-8")
    with pytest.raises(ValueError, match="dong hat"):
        H.doc_ket_qua(p)
    ket["cau_hinh"]["luong"] = 1
    p.write_text(json.dumps(ket), encoding="utf-8")
    assert H.doc_ket_qua(p)["cau_hinh"]["luong"] == 1


def _ham(cay) -> dict:
    return {n.name: n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef)}


def _goi_ten(nut) -> list[str]:
    ra = []
    for n in ast.walk(nut):
        if isinstance(n, ast.Call):
            f = n.func
            ra.append(f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else "")
    return ra


VAO_BO_SINH = {"sinh_thi_truong", "sinh_null", "tinh_su_that", "_sinh_loi"}


def _ham_goi_bo_sinh_thieu_cua(nguon: str) -> list[str]:
    """Hàm nào GỌI bộ sinh mà không gọi `kiem_luong` TRƯỚC lời gọi bộ sinh (theo số dòng)."""
    sai = []
    for ten, f in _ham(ast.parse(nguon)).items():
        dong_sinh = [n.lineno for n in ast.walk(f) if isinstance(n, ast.Call)
                     and ((isinstance(n.func, ast.Attribute) and n.func.attr in VAO_BO_SINH)
                          or (isinstance(n.func, ast.Name) and n.func.id in VAO_BO_SINH))]
        if not dong_sinh:
            continue
        dong_cua = [n.lineno for n in ast.walk(f) if isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Name) and n.func.id == "kiem_luong"]
        if not dong_cua or min(dong_cua) > min(dong_sinh):
            sai.append(ten)
    return sai


def test_AST_moi_ham_goi_bo_sinh_phai_goi_kiem_luong_truoc():
    nguon = DUONG.read_text(encoding="utf-8")
    assert _ham_goi_bo_sinh_thieu_cua(nguon) == []
    goi = {t for t, f in _ham(ast.parse(nguon)).items() if set(_goi_ten(f)) & VAO_BO_SINH}
    assert {"_sinh", "oracle_mot_mau"} <= goi, goi   # phép đo chạm đúng chỗ cần chạm


def test_AST_phep_do_bat_dung_mau_xau():
    xau = "def f(l):\n    return T.sinh_thi_truong(l, 1, 0.0)\n"
    xau2 = "def f(l):\n    x = T.tinh_su_that(l, 1, 0.0)\n    kiem_luong(l)\n"
    tot = "def f(l):\n    kiem_luong(l)\n    return T.sinh_thi_truong(l, 1, 0.0)\n"
    khong_goi = "def f(l):\n    return 1\n"
    assert _ham_goi_bo_sinh_thieu_cua(xau) == ["f"]
    assert _ham_goi_bo_sinh_thieu_cua(xau2) == ["f"]
    assert _ham_goi_bo_sinh_thieu_cua(tot) == []
    assert _ham_goi_bo_sinh_thieu_cua(khong_goi) == []


def test_AST_khong_co_doi_so_dong_hat_tren_dong_lenh():
    """Không `--luong`/`--hat`: người chạy không có đường nào chọn dòng hạt từ dòng lệnh."""
    cay = ast.parse(DUONG.read_text(encoding="utf-8"))
    cac_co = [n.args[0].value for n in ast.walk(cay) if isinstance(n, ast.Call)
              and isinstance(n.func, ast.Attribute) and n.func.attr == "add_argument"
              and n.args and isinstance(n.args[0], ast.Constant)]
    assert cac_co and not [c for c in cac_co if "luong" in c or "hat" in c or "stream" in c], cac_co


def test_AST_hat_thi_truong_va_oracle_chi_den_tu_hang_LUONG():
    """Lời gọi vào bộ sinh nhận `luong` từ tham số đã qua `kiem_luong`, không từ số viết tay 2–9."""
    cay = ast.parse(DUONG.read_text(encoding="utf-8"))
    # `LUONG = 1` và `LUONG_DUOC_PHEP = (1,)` là hai nơi duy nhất khai dòng hạt; nếu ai viết thêm
    # `luong=2` ở một lời gọi thì nó hiện ra ở đây dưới dạng khoá từ khoá.
    tu_khoa = [(k.arg, k.value.value) for n in ast.walk(cay) if isinstance(n, ast.Call)
               for k in n.keywords if k.arg == "luong" and isinstance(k.value, ast.Constant)]
    assert tu_khoa == [], tu_khoa
    gan = {t.id: n.value.value for n in ast.walk(cay) if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant)
           for t in n.targets if isinstance(t, ast.Name) and t.id == "LUONG"}
    assert gan == {"LUONG": 1}


# ── vai trò chỉ số thị trường: các tập không chạm nhau ────────────────────────

def test_chi_so_cac_vai_tro_khong_giao_nhau_va_deu_la_so_nguyen_duong():
    goc = sorted(H.CHI_SO_GOC.items(), key=lambda kv: kv[1])
    khoi = H.BUOC_DIEM * (len(H.CAU_HINH_MAC_DINH["luoi_kappa"]) + 1)
    for (ten, g), (_, g_sau) in zip(goc, goc[1:]):
        assert g + khoi <= g_sau, f"khối {ten} tràn sang khối sau"
    tap = {}
    for vai_tro in ("luoi", "muc", "null"):
        for diem in range(len(H.CAU_HINH_MAC_DINH["luoi_kappa"])):
            for i in (1, H.CAU_HINH_MAC_DINH["so_thi_truong_luoi"], H.TOI_DA_MOI_DIEM):
                v = H.chi_so_thi_truong(vai_tro, diem, i)
                assert v >= 1 and v not in tap, (vai_tro, diem, i)
                tap[v] = (vai_tro, diem, i)
    assert H.chi_so_thi_truong("luoi", 0, 1) == 1
    assert max(H.CHI_SO_GOC.values()) <= CHI_SO_TEST - 9_000   # khối `tham_do` bắt đầu ở 900.000, test ở 999.001


@pytest.mark.parametrize("vai_tro,diem,thu_tu", [("la", 0, 1), ("luoi", 0, 0), ("luoi", 0, H.TOI_DA_MOI_DIEM + 1),
                                                  ("luoi", -1, 1)])
def test_chi_so_ngoai_khoi_nổ(vai_tro, diem, thu_tu):
    with pytest.raises(ValueError):
        H.chi_so_thi_truong(vai_tro, diem, thu_tu)


# ── sổ ứng viên giả của bộ ba ────────────────────────────────────────────────

def test_so_ung_vien_bo_ba_dung_khuon_va_K_bang_3():
    so = H.so_ung_vien_bo_ba()
    cb.kiem_so_ung_vien(so)
    uv = so["ung_vien"]
    assert sorted(uv) == ["G", "H", "Z"] and cb.so_da_sang(so) == 3
    assert cb.nguong(so) == pytest.approx(0.05 / 3)
    ngay = [uv[t]["khai_ngay"] for t in H.TEN_BO_BA]
    assert ngay == T.dong_thoi_gian()["khai_ngay"] and len({n[:7] for n in ngay}) == 3
    ho = T.ho_spec_oracle()
    for t, ten in H.TEN_SPEC_BO_BA.items():
        assert uv[t]["spec"] == ho[ten] and uv[t]["qua_sang"] is None
    assert H.TEN_SPEC_BO_BA == {"G": T.TEN_SPEC_G, "Z": T.TEN_SPEC_Z, "H": T.TEN_SPEC_H}


# ── MỘT lượt thật: thị trường giả → cham_xac_nhan.cham ───────────────────────

@pytest.fixture(scope="module")
def ca_that():
    return {"co": H.cham_mot_thi_truong(CHI_SO_TEST, KAPPA_CO), "khong": H.cham_mot_thi_truong(CHI_SO_TEST, 0.0)}


def test_that_ca_lon_G_bi_bat_H_bi_phat_va_ngưỡng_la_005_chia_3(ca_that):
    r = ca_that["co"]
    assert r["K"] == 3 and r["nguong"] == pytest.approx(0.05 / 3)
    assert r["G"]["trang_thai"] == "QUA" and r["G"]["delta"] > 0
    assert r["H"]["trang_thai"] == "THUA" and r["H"]["delta"] < 0
    for t in H.TEN_BO_BA:
        assert r[t]["n_phien"] == cb.MOC_DOC == 252 and r[t]["n_ma"] == T.SO_MA == 60


def test_that_NULL_G_khong_bi_bat_va_H_khong_bi_khen(ca_that):
    r = ca_that["khong"]
    assert r["kappa"] == 0.0 and r["G"]["trang_thai"] != "QUA" and r["H"]["trang_thai"] != "QUA"


def test_that_bang_gia_di_thang_bang_dict_cho_cung_ket_qua_nhu_di_qua_CSV_cua_cham_xac_nhan():
    """Dụng cụ bỏ qua bước CSV (`dinh_dang_bang_gia` → `phan_tich_bang_gia`) cho nhanh; phải chứng minh
    bước ấy KHÔNG đổi kết quả và bảng giá giả qua được các phép kiểm của nó (nến cuối, lịch, nguồn)."""
    tt = H._sinh(H.LUONG, CHI_SO_TEST, KAPPA_CO)
    nguon = {m: "vci" for m in tt.ma}
    keo = H.keo_luc_gia(tt.ngay[-1])
    assert tt.ngay[-1] == "2102-04-13" and keo == "2102-04-14T00:00:00+07:00"   # dải giả trải tới năm 2102
    van_ban = H.cx.dinh_dang_bang_gia(tt.gia, keo, nguon)
    qua_csv = H.cx.phan_tich_bang_gia(van_ban)
    assert qua_csv["keo_luc"] == keo and qua_csv["nguon"] == nguon
    assert (qua_csv["gia"].index == tt.gia.index).all() and list(qua_csv["gia"].columns) == list(tt.gia.columns)
    # `pd.read_csv` đọc số thực bằng bộ đọc nhanh, KHÔNG tròn–đi–về (lệch ~1 ULP): không đòi bằng từng bit
    assert np.allclose(qua_csv["gia"].to_numpy(), tt.gia.to_numpy(), rtol=1e-13, atol=0.0)
    so = H.so_ung_vien_bo_ba()
    rows = tt.dong_quyet_dinh()
    truc_tiep = H.cx.cham(rows, so, {"gia": tt.gia, "keo_luc": keo, "nguon": nguon})
    r_csv = H.cx.cham(rows, so, qua_csv)
    for t in H.TEN_BO_BA:
        a, b = truc_tiep["chi_tiet"][t], r_csv["chi_tiet"][t]
        assert (a["trang_thai"], a["n_phien"], a["n_ma"]) == (b["trang_thai"], b["n_phien"], b["n_ma"])
        assert a["delta"] == pytest.approx(b["delta"], rel=1e-9, abs=1e-12)
        assert a["p"] == pytest.approx(b["p"], rel=1e-6, abs=1e-12)
    assert truc_tiep["lich"] == r_csv["lich"] and truc_tiep["lich"]["kiem_duoc"] == 0   # mọi ngày giả ở NGOÀI lịch công bố


def test_that_tai_lap_bit_cung_chi_so_cung_ket_qua(ca_that):
    assert H.cham_mot_thi_truong(CHI_SO_TEST, KAPPA_CO) == ca_that["co"]


def test_that_chay_qua_pool_cho_cung_ket_qua_tuan_tu(ca_that):
    viec = [(CHI_SO_TEST, KAPPA_CO, H.LUONG, H.cx.SO_HOAN_VI), (CHI_SO_TEST, 0.0, H.LUONG, H.cx.SO_HOAN_VI)]
    with H.tao_pool(2) as pool:
        song = H._map(pool, H._viec_cham, viec)
    assert song == [ca_that["co"], ca_that["khong"]]


def test_that_oracle_G_duong_H_am_va_NULL_gan_0():
    co = H.oracle_mot_mau(1, KAPPA_CO, 1500)
    khong = H.oracle_mot_mau(1, 0.0, 1500)
    assert co["G"] > 0.05 and co["H"] < 0 and abs(co["Z"]) < 0.03
    assert abs(khong["G"]) < 0.03 and co["G"] > khong["G"] + 0.05


def test_tham_do_do_luc_do_duoc_khop_oracle_that():
    """MÁY ĐO đi qua ca thật đã biết: Δ đo trung bình trên các thị trường ≈ ΔIC_true của oracle."""
    kq = [H.cham_mot_thi_truong(CHI_SO_TEST + i, 0.02) for i in range(4)]
    d = float(np.mean([r["G"]["delta"] for r in kq]))
    orc = float(np.mean([H.oracle_mot_mau(CHI_SO_TEST + i, 0.02, 3000)["G"] for i in range(3)]))
    assert d == pytest.approx(orc, abs=0.03), (d, orc)


# ── thống kê thuần ────────────────────────────────────────────────────────────

def test_wilson_khop_gia_tri_tay_va_bien():
    lo, hi = H.wilson(320, 400)
    assert (lo, hi) == pytest.approx((0.75803, 0.83626), abs=1e-4)
    lo0, hi0 = H.wilson(0, 400)
    assert lo0 == pytest.approx(0.0, abs=1e-12) and 0.0 < hi0 < 0.02
    lo1, hi1 = H.wilson(400, 400)
    assert hi1 == pytest.approx(1.0, abs=1e-12) and 0.98 < lo1 < 1.0
    assert H.wilson(200, 400)[0] < 0.5 < H.wilson(200, 400)[1]


def test_nhi_thuc_khop_cac_so_cua_dac_ta_muc_6():
    """Chính các số in ở `docs/thiet-ke-c4-thi-truong-gia.md` mục 6 (sinh bằng scipy), tính lại không scipy."""
    assert 1 - H.nhi_thuc_cdf(75, 1000, .05) == pytest.approx(0.0003, abs=1e-4)
    assert H.nhi_thuc_cdf(75, 1000, .10) == pytest.approx(0.0038, abs=1e-4)
    assert 1 - H.nhi_thuc_cdf(359, 400, .90) == pytest.approx(0.542, abs=1e-3)
    assert 1 - H.nhi_thuc_cdf(319, 400, .85) == pytest.approx(0.9972, abs=1e-4)
    assert H.nhi_thuc_cdf(-1, 10, .5) == 0.0 and H.nhi_thuc_cdf(10, 10, .5) == pytest.approx(1.0)


def test_dai_khop_400_la_299_340_nhu_dac_ta():
    assert H.dai_khop(400) == (299, 340)
    k = H.nhi_thuc_ppf(0.995, 400, 0.8)
    assert H.nhi_thuc_cdf(k, 400, 0.8) >= 0.995 > H.nhi_thuc_cdf(k - 1, 400, 0.8)


def test_probit_tim_lai_a_b_tu_so_lieu_khong_nhieu():
    a0, b0 = -4.0, 70.0
    x = np.linspace(0.02, 0.10, 8)
    n = np.full(8, 10_000)
    k = n * np.array([_ND.cdf(a0 + b0 * v) for v in x])        # kỳ vọng chính xác (k thực)
    a, b = H.khop_probit(x, n, k)
    assert (a, b) == pytest.approx((a0, b0), rel=1e-6)
    mde = H.mde_tu_probit(a, b)
    assert _ND.cdf(a + b * mde) == pytest.approx(0.80, abs=1e-9)
    assert mde == pytest.approx((_ND.inv_cdf(0.8) + 4.0) / 70.0)


def test_probit_tim_lai_tu_nhi_thuc_co_nhieu_trong_3_sai_so():
    rng = np.random.default_rng(7)
    a0, b0 = -4.0, 70.0
    x = np.linspace(0.02, 0.10, 8)
    n = np.full(8, 500)
    p = np.array([_ND.cdf(a0 + b0 * v) for v in x])
    mde_that = (_ND.inv_cdf(0.8) - a0) / b0
    sai = [H.mde_tu_probit(*H.khop_probit(x, n, rng.binomial(n, p))) - mde_that for _ in range(40)]
    assert abs(float(np.mean(sai))) < 3 * float(np.std(sai, ddof=1)) / math.sqrt(40)
    assert 0.0 < float(np.std(sai, ddof=1)) < 0.01


def test_probit_nổ_khi_luc_khong_tang_theo_loi_the():
    x = np.linspace(0.02, 0.10, 6)
    with pytest.raises(RuntimeError, match="b ="):
        H.khop_probit(x, np.full(6, 400), np.array([360, 300, 220, 140, 80, 30]))


def test_bootstrap_mde_tat_dinh_va_so_sai_hop_ly():
    x = np.linspace(0.02, 0.10, 8)
    n = np.full(8, 400)
    k = np.round(n * np.array([_ND.cdf(-4.0 + 70.0 * v) for v in x]))
    b1 = H.bootstrap_mde(x, n, k, 60)
    assert b1 == H.bootstrap_mde(x, n, k, 60)
    assert b1["so_lan_hong"] == 0 and 0.0005 < b1["se"] < 0.01
    assert b1["khoang_95"][0] < H.mde_tu_probit(*H.khop_probit(x, n, k)) < b1["khoang_95"][1]


# ── dò nhị phân ───────────────────────────────────────────────────────────────

def test_nhi_phan_tim_kappa_dung_theo_ham_don_dieu_tang():
    f = lambda kap: 4.0 * kap + 3.0 * kap * kap                 # noqa: E731  (đơn điệu tăng, phi tuyến)
    kap, fk, vet = H.nhi_phan(f, 0.06, 0.0, 0.05, 0.02, 30)
    assert abs(fk - 0.06) <= 0.02 * 0.06 and fk == f(kap) and len(vet) >= 3
    assert kap == pytest.approx(0.01442, abs=6e-4)               # 4κ + 3κ² = 0,06
    kap2, fk2, _ = H.nhi_phan(f, 0.12, 0.0, 0.1, 0.001, 40)
    assert abs(fk2 - 0.12) <= 0.001 * 0.12 and kap2 > kap


def test_nhi_phan_cung_huong_voi_ham_tang_khong_dao_dau():
    """Hàm giảm KHÔNG được âm thầm cho một κ: khoảng phải bao mục tiêu theo chiều tăng."""
    with pytest.raises(RuntimeError, match="khong bao"):
        H.nhi_phan(lambda k: -k, 0.05, 0.0, 1.0, 0.02, 30)


def test_nhi_phan_nổ_khi_khoang_khong_bao_muc_tieu_hoac_khong_hoi_tu():
    with pytest.raises(RuntimeError, match="khong bao"):
        H.nhi_phan(lambda k: k, 5.0, 0.0, 1.0, 0.02, 30)
    with pytest.raises(RuntimeError, match="khong hoi tu"):
        H.nhi_phan(lambda k: 0.0 if k < 0.5 else 1.0, 0.5, 0.0, 1.0, 0.001, 20)  # bước nhảy: không có nghiệm


# ── so sánh --kiem ────────────────────────────────────────────────────────────

def test_so_sanh_so_nguyen_phai_bang_so_thuc_trong_dung_sai_thi_bang():
    a = {"n": 5, "x": 0.1 + 0.2, "ten": "g", "ok": True, "l": [1, 2.0], "moi_truong": {"python": "3.13"}}
    b = {"n": 5, "x": 0.3, "ten": "g", "ok": True, "l": [1, 2.0 + 1e-12], "moi_truong": {"python": "3.11"}}
    assert H.so_sanh(a, b) == []
    assert H.so_sanh({"n": 5}, {"n": 6}) == ["/n: 5 != 6"]
    assert H.so_sanh({"x": 0.3}, {"x": 0.3001}) != []
    assert H.so_sanh({"ok": True}, {"ok": 1}) != []
    assert H.so_sanh({"ok": True}, {"ok": False}) != []
    assert H.so_sanh({"l": [1, 2]}, {"l": [1, 2, 3]}) != []
    assert H.so_sanh({"a": 1}, {"b": 1}) != [] and H.so_sanh({"a": "x"}, {"a": "y"}) != []
    assert H.so_sanh({"n": 5.0}, {"n": 5}) == []                 # 5 và 5.0 cùng giá trị


def test_so_sanh_chi_bo_qua_khoa_moi_truong_o_cap_goc():
    assert H.so_sanh({"a": {"moi_truong": 1}}, {"a": {"moi_truong": 2}}) != []
    assert H.so_sanh({"moi_truong": 1, "lenh": "x", "thoi_gian_chay_giay": 3.0}, {"moi_truong": 2, "lenh": "y",
                     "thoi_gian_chay_giay": 9.0}) == []


# ── toàn quy trình trên bộ ước lượng GIẢ có đáp án biết trước ─────────────────

HE_SO_DOC = 4.0        # ΔIC_true(G) = 4κ (giả)
MDE_GIA = 0.064        # lực thật = Φ((ΔIC − MDE_GIA)/SIGMA_GIA + Φ⁻¹(0,8))… xem `_luc_gia`
SIGMA_GIA = 0.025


def _luc_gia(kappa):
    return _ND.cdf((HE_SO_DOC * kappa - MDE_GIA) / SIGMA_GIA + _ND.inv_cdf(0.8))


class _Gia:
    def __init__(self, monkeypatch, lech_kiem=0.0, bao_dong_null=0.01, lech_tuyet_doi_kiem=0.0,
                 so_bao_dong_chinh_xac=None):
        self.chi_so_thi_truong = []
        self.chi_so_oracle = []
        self.lech_kiem = lech_kiem
        self.lech_tuyet_doi_kiem = lech_tuyet_doi_kiem
        self.so_bao_dong_chinh_xac = so_bao_dong_chinh_xac
        monkeypatch.setattr(H, "cham_mot_thi_truong", self.cham)
        monkeypatch.setattr(H, "oracle_mot_mau", self.oracle)
        self.bao_dong_null = bao_dong_null

    def cham(self, chi_so, kappa, luong=1, so_hoan_vi=2000):
        H.kiem_luong(luong)
        self.chi_so_thi_truong.append(chi_so)
        u = np.random.default_rng([chi_so, 17]).random(4)
        qua = u[0] < _luc_gia(kappa)
        bd = u[1] < (self.bao_dong_null if kappa == 0.0 else 0.02)
        if self.so_bao_dong_chinh_xac is not None and kappa == 0.0:   # đúng N thị trường NULL đầu có báo động
            qua = False
            bd = chi_so - H.CHI_SO_GOC["null"] <= self.so_bao_dong_chinh_xac
        return {"chi_so": chi_so, "kappa": kappa, "K": 3, "nguong": 0.05 / 3,
                "G": {"trang_thai": "QUA" if qua else "DANG CHAM", "n_phien": 252, "n_ma": 60,
                      "delta": HE_SO_DOC * kappa + 0.01 * (u[2] - 0.5), "p": 0.001 if qua else 0.4},
                "Z": {"trang_thai": "DANG CHAM", "n_phien": 252, "n_ma": 60, "delta": 0.0, "p": 0.5},
                "H": {"trang_thai": "QUA" if bd else "DANG CHAM", "n_phien": 252, "n_ma": 60,
                      "delta": -0.01, "p": 0.001 if bd else 0.5}}

    def oracle(self, chi_so, kappa, so_phien, luong=1):
        H.kiem_luong(luong)
        self.chi_so_oracle.append(chi_so)
        nhieu = (np.random.default_rng([chi_so, 5]).random() - 0.5) * 0.002
        he = 1.0 + (self.lech_kiem if chi_so >= H.CHI_SO_GOC["or_kiem"] else 0.0)
        g = HE_SO_DOC * kappa * he + nhieu + (self.lech_tuyet_doi_kiem if chi_so >= H.CHI_SO_GOC["or_kiem"] else 0.0)
        return {"G": g, "Z": 0.0, "H": -0.3 * g}


def _cau_hinh_gia(**kw):
    return {**H.CAU_HINH_MAC_DINH, "luoi_kappa": [0.008, 0.010, 0.012, 0.014, 0.016, 0.018, 0.020, 0.022],
            "so_thi_truong_luoi": 800, "so_thi_truong_muc": 800, "so_thi_truong_null": 800,
            "so_oracle_tim": 4, "so_oracle_kiem": 4, "so_bootstrap": 80, "so_phien_oracle": 100, **kw}


@pytest.fixture(scope="module")
def ket_gia():
    mp = pytest.MonkeyPatch()
    g = _Gia(mp)
    try:
        return g, H.chay(_cau_hinh_gia())
    finally:
        mp.undo()


def test_quy_trinh_gia_tim_dung_MDE_va_ba_muc_kappa(ket_gia):
    _, k = ket_gia
    assert k["mde80"]["delta_ic_true"] == pytest.approx(MDE_GIA, abs=0.004)
    for m in k["muc"]:
        assert m["kappa"] == pytest.approx(m["he_so"] * k["mde80"]["delta_ic_true"] / HE_SO_DOC, rel=0.03, abs=1e-12)
        assert m["muc_tieu_delta_ic"] == m["he_so"] * k["mde80"]["delta_ic_true"]
    assert [m["he_so"] for m in k["muc"]] == [0.0, 0.5, 1.0, 2.0]
    assert k["muc"][0]["kappa"] == 0.0 and k["muc"][0]["luc"] is None and k["muc"][0]["vet_nhi_phan"] == []
    assert [m["kappa"] for m in k["muc"]] == sorted(m["kappa"] for m in k["muc"])
    assert k["dat_dung_sai_10pct_ca_bon_muc"] is True and all(m["dat_dung_sai_10pct"] for m in k["muc"])
    assert all(abs(m["lech_tuong_doi_tren_mau_kiem"]) <= 0.10 for m in k["muc"][1:])


def test_quy_trinh_gia_luc_thuc_o_cac_muc_khop_mo_hinh(ket_gia):
    _, k = ket_gia
    mp1 = next(m for m in k["muc"] if m["he_so"] == 1.0)
    assert mp1["luc"]["ty_le_bat_G"] == pytest.approx(0.8, abs=0.08)
    luc = [m["luc"]["ty_le_bat_G"] for m in k["muc"][1:]]
    assert luc == sorted(luc) and luc[0] < 0.5 and luc[-1] > 0.95
    assert k["kiem_1x_trong_dai_99"]["dai_99_quanh_80"] == [H.dai_khop(800)[0], H.dai_khop(800)[1]]
    assert k["kiem_1x_trong_dai_99"]["n_QUA_G"] == mp1["luc"]["n_QUA_G"]


def test_quy_trinh_gia_bang_sap_theo_delta_ic_va_khop_so_dem(ket_gia):
    _, k = ket_gia
    b = k["bang_ic_true_ty_le_bat"]
    assert len(b) == len(k["luoi"]) + 3
    assert [r["delta_ic_true"] for r in b] == sorted(r["delta_ic_true"] for r in b)
    for r in b:
        assert r["ty_le_bat_G"] == r["n_QUA_G"] / r["R"] and r["khoang_wilson_95"][0] <= r["ty_le_bat_G"] <= r["khoang_wilson_95"][1]
    tong = sum(r["n_QUA_G"] for r in b)
    assert tong == sum(r["n_QUA_G"] for r in k["luoi"]) + sum(m["luc"]["n_QUA_G"] for m in k["muc"][1:])


def test_quy_trinh_gia_khong_thi_truong_nao_dung_hai_lan_va_khong_oracle_nao_chung_hat(ket_gia):
    g, k = ket_gia
    r_tong = len(k["luoi"]) * 800 + 3 * 800 + 800
    assert len(g.chi_so_thi_truong) == r_tong == len(set(g.chi_so_thi_truong))
    for v in g.chi_so_thi_truong:
        assert H.CHI_SO_GOC["luoi"] < v < H.CHI_SO_GOC["or_tim"]
    tim = {v for v in g.chi_so_oracle if v < H.CHI_SO_GOC["or_kiem"]}
    kiem = {v for v in g.chi_so_oracle if v >= H.CHI_SO_GOC["or_kiem"]}
    assert tim and kiem and not (tim & kiem)
    assert all(H.CHI_SO_GOC["or_tim"] < v <= H.CHI_SO_GOC["or_tim"] + 4 for v in tim)
    assert all(H.CHI_SO_GOC["or_kiem"] < v <= H.CHI_SO_GOC["or_kiem"] + 4 for v in kiem)


def test_quy_trinh_gia_NULL_smoke_dem_dung_va_so_voi_nguong_B1(ket_gia):
    _, k = ket_gia
    ns = k["null_smoke"]
    assert ns["R"] == 800 and ns["nguong_B1"] == 0.075 and ns["toi_da_cho_phep"] == 60
    assert ns["n_co_bao_dong"] >= max(ns["n_QUA_H"], ns["n_QUA_G"])
    assert ns["dat"] is (ns["n_co_bao_dong"] <= 60)
    assert ns["ty_le_bao_dong"] == ns["n_co_bao_dong"] / 800
    assert 0.03 < ns["ty_le_bao_dong"] < 0.075 and ns["dat"] is True        # mô hình giả: ≈ 5,3%
    assert ns["muc_danh_nghia_neu_doc_lap"] == pytest.approx(1 - (1 - 0.05 / 3) ** 3)


def test_quy_trinh_gia_NULL_smoke_TRUOT_khi_bao_dong_qua_nguong(monkeypatch):
    _Gia(monkeypatch, bao_dong_null=0.20)
    k = H.chay(_cau_hinh_gia(so_thi_truong_null=400))
    assert k["null_smoke"]["dat"] is False and k["null_smoke"]["n_co_bao_dong"] > k["null_smoke"]["toi_da_cho_phep"]
    assert k["null_smoke"]["toi_da_cho_phep"] == 30


def test_quy_trinh_gia_lech_hon_10pct_o_mau_kiem_bi_bat(monkeypatch):
    _Gia(monkeypatch, lech_kiem=+0.15)
    k = H.chay(_cau_hinh_gia(so_thi_truong_luoi=300, so_thi_truong_muc=100, so_thi_truong_null=50))
    assert k["dat_dung_sai_10pct_ca_bon_muc"] is False
    assert all(m["dat_dung_sai_10pct"] is False for m in k["muc"][1:])
    assert all(m["lech_tuong_doi_tren_mau_kiem"] == pytest.approx(0.15, abs=0.03) for m in k["muc"][1:])
    assert k["muc"][0]["dat_dung_sai_10pct"] is True      # mức 0×: κ = 0 đúng nghĩa đen


def test_quy_trinh_gia_bang_dung_mau_kiem_cho_cac_muc_va_mau_tim_cho_luoi(monkeypatch):
    _Gia(monkeypatch, lech_kiem=+0.05)
    k = H.chay(_cau_hinh_gia(so_thi_truong_luoi=200, so_thi_truong_muc=100, so_thi_truong_null=50))
    b = k["bang_ic_true_ty_le_bat"]
    for m in k["muc"][1:]:
        r = next(x for x in b if x["nguon"] == f"muc {m['he_so']}x")
        assert r["delta_ic_true"] == m["oracle_kiem"]["G"]["delta_ic"] != m["oracle_tim"]["G"]["delta_ic"]
        assert r["kappa"] == m["kappa"] and r["R"] == 100
    for lu in k["luoi"]:
        r = next(x for x in b if x["nguon"] == "luoi" and x["kappa"] == lu["kappa"])
        assert r["delta_ic_true"] == lu["oracle"]["G"]["delta_ic"] and r["R"] == 200


def test_quy_trinh_gia_muc_0x_trat_khi_oracle_NULL_o_mau_kiem_khac_0(monkeypatch):
    _Gia(monkeypatch, lech_tuyet_doi_kiem=0.05)
    k = H.chay(_cau_hinh_gia(so_thi_truong_luoi=200, so_thi_truong_muc=100, so_thi_truong_null=50))
    assert k["muc"][0]["dat_dung_sai_10pct"] is False and k["dat_dung_sai_10pct_ca_bon_muc"] is False
    assert k["muc"][0]["oracle_kiem"]["G"]["delta_ic"] > 0.04 and k["muc"][0]["lech_tuong_doi_tren_mau_kiem"] is None


@pytest.mark.parametrize("so_bd,dat", [(59, True), (60, True), (61, False), (0, True)])
def test_quy_trinh_gia_NULL_smoke_bien_dung_toi_da_cho_phep_va_dem_dung(monkeypatch, so_bd, dat):
    """R = 800 → tối đa 60 (7,5%): đúng 60 vẫn ĐẠT, 61 TRƯỢT; số đếm in ra đúng N."""
    _Gia(monkeypatch, so_bao_dong_chinh_xac=so_bd)
    k = H.chay(_cau_hinh_gia(so_thi_truong_luoi=100, so_thi_truong_muc=50, so_thi_truong_null=800))
    ns = k["null_smoke"]
    assert ns["n_co_bao_dong"] == so_bd and ns["n_QUA_H"] == so_bd and ns["toi_da_cho_phep"] == 60
    assert ns["dat"] is dat
    assert ns["ky_vong_bao_dong"] == pytest.approx(800 * (1 - (1 - 0.05 / 3) ** 3))
    if so_bd == 0:
        assert ns["p_nhi_thuc_tu_so_do_tro_len"] == pytest.approx(1.0)


def test_oracle_trung_binh_se_la_do_lech_chuan_mau_chia_can_so_mau(monkeypatch):
    kq = {}

    def gia(chi_so, kappa, so_phien, luong=1):
        v = {"G": float(chi_so % 7) * 0.01 + kappa, "Z": 0.0, "H": -1.0 * (chi_so % 5)}
        kq[chi_so] = v
        return v
    monkeypatch.setattr(H, "oracle_mot_mau", gia)
    r = H.oracle_trung_binh(None, 0.02, "or_tim", 5, 123)
    g = np.array([kq[H.chi_so_thi_truong("or_tim", 0, i + 1)]["G"] for i in range(5)])
    assert r["G"]["delta_ic"] == pytest.approx(g.mean()) and r["G"]["se"] == pytest.approx(g.std(ddof=1) / math.sqrt(5))
    assert r["so_mau"] == 5 and r["kappa"] == 0.02
    h = np.array([kq[H.chi_so_thi_truong("or_tim", 0, i + 1)]["H"] for i in range(5)])
    assert r["H"]["delta_ic"] == pytest.approx(h.mean())
    assert set(kq) == {H.CHI_SO_GOC["or_tim"] + i for i in range(1, 6)}
    kq.clear()
    H.oracle_trung_binh(None, 0.02, "or_kiem", 3, 123)
    assert set(kq) == {H.CHI_SO_GOC["or_kiem"] + i for i in range(1, 4)}


def test_dem_dung_tung_loai_ket_qua():
    def r(g, z, h, nguong=0.05 / 3):
        mot = lambda tt, p, d: {"trang_thai": tt, "n_phien": 252, "n_ma": 60, "delta": d, "p": p}   # noqa: E731
        return {"nguong": nguong, "G": mot(*g), "Z": mot(*z), "H": mot(*h)}
    kq = [r(("QUA", 0.001, 0.05), ("DANG CHAM", 0.5, 0.0), ("THUA", 0.001, -0.02)),
          r(("DANG CHAM", 0.4, 0.01), ("QUA", 0.01, 0.02), ("DANG CHAM", 0.3, 0.0)),
          r(("THUA", 0.001, -0.03), ("DANG CHAM", 0.5, 0.0), ("QUA", 0.001, 0.02)),
          r(("DANG CHAM", 0.4, 0.01), ("DANG CHAM", 0.2, 0.0), ("DANG CHAM", 0.3, 0.0))]
    d = H._dem(kq)
    assert (d["R"], d["n_QUA_G"], d["n_THUA_G"], d["n_QUA_H"], d["n_THUA_H"]) == (4, 1, 1, 1, 1)
    assert (d["n_bao_dong_Z"], d["n_co_bao_dong"], d["n_co_QUA"]) == (1, 3, 3)
    assert d["ty_le_bat_G"] == 0.25 and d["delta_do_G"] == pytest.approx((0.05 + 0.01 - 0.03 + 0.01) / 4)
    assert d["khoang_wilson_95"] == pytest.approx(list(H.wilson(1, 4)))


@pytest.mark.parametrize("dat_muc,dat_null,ma", [(True, True, 0), (False, True, 1), (True, False, 1)])
def test_main_chay_ma_thoat_theo_dung_sai_va_NULL_smoke(monkeypatch, tmp_path, dat_muc, dat_null, ma):
    ghi = []
    gia = {"dat_dung_sai_10pct_ca_bon_muc": dat_muc, "null_smoke": {"dat": dat_null}, "thoi_gian_chay_giay": 1.0}
    monkeypatch.setattr(H, "chay", lambda ch, n, in_tien_do=False: dict(gia))
    monkeypatch.setattr(H, "ghi_ket_qua", lambda ket, duong=None: ghi.append(ket))
    monkeypatch.setattr(H, "in_bang", lambda ket: None)
    assert H.main(["--chay", "--tien-trinh", "1"]) == ma
    assert len(ghi) == 1 and ghi[0]["lenh"].endswith("--chay") and ghi[0]["thoi_gian_chay_giay"] == 1.0


def test_main_phai_chon_dung_mot_che_do():
    with pytest.raises(SystemExit):
        H.main([])
    with pytest.raises(SystemExit):
        H.main(["--chay", "--kiem"])


@pytest.mark.parametrize("trung_binh,dat", [(0.010, False), (0.004, False), (0.0005, True), (0.0, True)])
def test_quy_trinh_gia_muc_0x_bien_o_2_sai_so_cua_chinh_mau_kiem(monkeypatch, trung_binh, dat):
    """Oracle NULL ở mẫu kiểm: bốn giá trị xung quanh `trung_binh` (độ lệch chuẩn mẫu 0,001633, sai số
    0,000816) → tỷ số 12,2 · 4,9 · 0,61 · 0: ĐẠT khi |trung bình| < 2 sai số, nên 4,9 sai số phải TRƯỢT
    (một ngưỡng 20 sai số sẽ cho nó qua)."""
    g = _Gia(monkeypatch)
    goc = g.oracle

    def oracle(chi_so, kappa, so_phien, luong=1):
        if kappa == 0.0 and chi_so >= H.CHI_SO_GOC["or_kiem"]:
            v = trung_binh + (0.002, -0.002, 0.0, 0.0)[chi_so - H.CHI_SO_GOC["or_kiem"] - 1]
            return {"G": v, "Z": 0.0, "H": 0.0}
        return goc(chi_so, kappa, so_phien, luong)
    monkeypatch.setattr(H, "oracle_mot_mau", oracle)
    k = H.chay(_cau_hinh_gia(so_thi_truong_luoi=200, so_thi_truong_muc=100, so_thi_truong_null=50, so_oracle_kiem=4))
    m0 = k["muc"][0]["oracle_kiem"]["G"]
    assert m0["delta_ic"] == pytest.approx(trung_binh) and m0["se"] == pytest.approx(0.0016329931618554522 / 2.0)
    assert k["muc"][0]["dat_dung_sai_10pct"] is dat


def test_quy_trinh_gia_lech_9pct_van_dat_va_dung_sai_la_10pct(monkeypatch):
    _Gia(monkeypatch, lech_kiem=-0.09)
    k = H.chay(_cau_hinh_gia(so_thi_truong_luoi=300, so_thi_truong_muc=100, so_thi_truong_null=50))
    assert k["dat_dung_sai_10pct_ca_bon_muc"] is True and H.DUNG_SAI_MUC == 0.10
    assert all(m["lech_tuong_doi_tren_mau_kiem"] == pytest.approx(-0.09, abs=0.03) for m in k["muc"][1:])


def test_quy_trinh_gia_tai_lap_bit_va_so_sanh_bang_khong(monkeypatch):
    _Gia(monkeypatch)
    cu = H.chay(_cau_hinh_gia(so_thi_truong_luoi=200, so_thi_truong_muc=100, so_thi_truong_null=100))
    moi = H.chay(_cau_hinh_gia(so_thi_truong_luoi=200, so_thi_truong_muc=100, so_thi_truong_null=100))
    assert H.so_sanh(cu, moi) == [] and json.dumps(cu["luoi"]) == json.dumps(moi["luoi"])
    kh = H.chay(_cau_hinh_gia(so_thi_truong_luoi=200, so_thi_truong_muc=100, so_thi_truong_null=101))
    assert H.so_sanh(cu, kh) != []


def test_quy_trinh_nổ_voi_cau_hinh_sai(monkeypatch):
    _Gia(monkeypatch)
    sai = [{"luoi_kappa": [0.01, 0.01]}, {"luoi_kappa": [0.02, 0.01, 0.03]}, {"luoi_kappa": [0.0, 0.01, 0.02]},
           {"so_thi_truong_luoi": 1}, {"so_thi_truong_null": H.TOI_DA_MOI_DIEM + 1}, {"he_so_muc": [0.5, 2.0]},
           {"he_so_muc": [2.0, 1.0]}, {"so_oracle_tim": 1}]
    for kw in sai:
        with pytest.raises(ValueError):
            H.kiem_cau_hinh({**H.CAU_HINH_MAC_DINH, **kw})
    thieu = dict(H.CAU_HINH_MAC_DINH)
    del thieu["so_bootstrap"]
    with pytest.raises(ValueError, match="thieu"):
        H.kiem_cau_hinh(thieu)


def test_main_kiem_tra_ve_0_khi_khop_va_1_khi_lech(monkeypatch, tmp_path, capsys):
    _Gia(monkeypatch)
    cfg = _cau_hinh_gia(so_thi_truong_luoi=200, so_thi_truong_muc=100, so_thi_truong_null=100)
    ghi = H.chay(cfg)
    p = tmp_path / "hc.json"
    monkeypatch.setattr(H, "DUONG_KET_QUA", p)
    H.ghi_ket_qua(ghi, p)
    monkeypatch.setattr(H, "doc_ket_qua", lambda: json.loads(p.read_text(encoding="utf-8")))
    assert H.main(["--kiem", "--tien-trinh", "1"]) == 0
    assert "OK" in capsys.readouterr().out
    d = json.loads(p.read_text(encoding="utf-8"))
    d["luoi"][0]["n_QUA_G"] += 1
    p.write_text(json.dumps(d), encoding="utf-8")
    assert H.main(["--kiem", "--tien-trinh", "1"]) == 1
    assert "LỆCH" in capsys.readouterr().out


def test_ghi_ket_qua_di_qua_va_an_toan_va_doc_lai_dung(monkeypatch, tmp_path):
    _Gia(monkeypatch)
    ket = H.chay(_cau_hinh_gia(so_thi_truong_luoi=100, so_thi_truong_muc=50, so_thi_truong_null=50))
    p = tmp_path / "ra.json"
    H.ghi_ket_qua(ket, p)
    assert not list(tmp_path.glob("*.dang-ghi")), "file tạm phải được đổi tên đi"
    assert H.so_sanh(ket, H.doc_ket_qua(p)) == []
    assert p.read_text(encoding="utf-8").endswith("\n")


# ── file kết quả ĐÃ COMMIT ────────────────────────────────────────────────────

KET_QUA_DA_GHI = GOC / "docs" / "thi-truong-gia-hieu-chuan.json"


@pytest.fixture(scope="module")
def da_ghi():
    return H.doc_ket_qua(KET_QUA_DA_GHI)


def test_file_da_ghi_dung_dong_hat_1_va_cau_hinh_la_cau_hinh_mac_dinh(da_ghi):
    assert da_ghi["cau_hinh"]["luong"] == 1 and da_ghi["buoc"] == 289
    assert da_ghi["cau_hinh"] == H.CAU_HINH_MAC_DINH
    tt = da_ghi["thong_so_vong"]
    assert (tt["K"], tt["W"], tt["M"]) == (3, cb.MOC_DOC, T.SO_MA) and tt["alpha_k"] == pytest.approx(0.05 / 3)
    assert tt["hat_hoan_vi"] == H.cx.HAT_RNG and tt["so_hoan_vi"] == H.cx.SO_HOAN_VI
    assert not any(k in json.dumps(da_ghi) for k in ('"luong": 2', '"luong": 3', '"luong": 4', '"luong": 5'))


def test_file_da_ghi_probit_va_MDE_tai_lap_duoc_tu_so_dem_da_ghi(da_ghi):
    x = [r["oracle"]["G"]["delta_ic"] for r in da_ghi["luoi"]]
    a, b = H.khop_probit(x, [r["R"] for r in da_ghi["luoi"]], [r["n_QUA_G"] for r in da_ghi["luoi"]])
    assert (a, b) == pytest.approx((da_ghi["mde80"]["probit"]["a"], da_ghi["mde80"]["probit"]["b"]), rel=1e-9)
    assert H.mde_tu_probit(a, b) == pytest.approx(da_ghi["mde80"]["delta_ic_true"], rel=1e-9)
    # Bootstrap rút từ `Generator.binomial`, mà NumPy không hứa dòng số ổn định giữa các bản: so trong dung
    # sai (sai số của sai số bootstrap ~3% ≈ 2e-5), không đòi bằng từng chữ số.
    lai = H.bootstrap_mde(x, [r["R"] for r in da_ghi["luoi"]], [r["n_QUA_G"] for r in da_ghi["luoi"]],
                          da_ghi["cau_hinh"]["so_bootstrap"])
    ghi_ = da_ghi["mde80"]["bootstrap"]
    assert lai["so_lan"] == ghi_["so_lan"] and lai["so_lan_hong"] == 0 == ghi_["so_lan_hong"]
    assert lai["se"] == pytest.approx(ghi_["se"], abs=2e-4)
    assert lai["khoang_95"] == pytest.approx(ghi_["khoang_95"], abs=5e-4)


def test_file_da_ghi_bon_muc_trong_10pct_va_dung_thu_tu(da_ghi):
    muc = da_ghi["muc"]
    mde = da_ghi["mde80"]["delta_ic_true"]
    assert [m["he_so"] for m in muc] == [0.0] + da_ghi["cau_hinh"]["he_so_muc"]
    for m in muc:
        assert m["muc_tieu_delta_ic"] == pytest.approx(m["he_so"] * mde, rel=1e-12)
    assert muc[0]["kappa"] == 0.0
    assert [m["kappa"] for m in muc] == sorted(m["kappa"] for m in muc) and len({m["kappa"] for m in muc}) == 4
    for m in muc[1:]:
        assert abs(m["lech_tuong_doi_tren_mau_kiem"]) <= H.DUNG_SAI_MUC, m["he_so"]
        assert abs(m["lech_tuong_doi_tren_mau_kiem"]) == pytest.approx(
            abs(m["oracle_kiem"]["G"]["delta_ic"] - m["muc_tieu_delta_ic"]) / m["muc_tieu_delta_ic"], rel=1e-9)
        assert m["vet_nhi_phan"] and m["luc"]["R"] == da_ghi["cau_hinh"]["so_thi_truong_muc"]
    assert abs(muc[0]["oracle_kiem"]["G"]["delta_ic"]) < 2 * muc[0]["oracle_kiem"]["G"]["se"]
    assert da_ghi["dat_dung_sai_10pct_ca_bon_muc"] is True
    assert muc[2]["kappa"] == da_ghi["mde80"]["kappa_tuong_ung"]


def test_file_da_ghi_bang_ty_le_bat_nhat_quan_va_tang_theo_loi_the(da_ghi):
    b = da_ghi["bang_ic_true_ty_le_bat"]
    assert len(b) == len(da_ghi["luoi"]) + 3
    assert [r["delta_ic_true"] for r in b] == sorted(r["delta_ic_true"] for r in b)
    for r in b:
        assert 0 <= r["n_QUA_G"] <= r["R"] and r["ty_le_bat_G"] == r["n_QUA_G"] / r["R"]
        assert r["khoang_wilson_95"] == pytest.approx(list(H.wilson(r["n_QUA_G"], r["R"])), rel=1e-9)
    luoi = [r["ty_le_bat_G"] for r in da_ghi["luoi"]]
    assert luoi[0] < luoi[-1]
    assert da_ghi["luoi"][0]["ty_le_bat_G"] < 0.80 < da_ghi["luoi"][-1]["ty_le_bat_G"], "lưới phải bao mức 80%"
    assert min(abs(r["ty_le_bat_G"] - 0.8) for r in da_ghi["luoi"]) < 0.15


def test_file_da_ghi_NULL_smoke_va_dai_1x_khop_cach_tinh(da_ghi):
    ns = da_ghi["null_smoke"]
    assert ns["toi_da_cho_phep"] == math.floor(H.NGUONG_B1 * ns["R"] + 1e-9)
    assert ns["dat"] is (ns["n_co_bao_dong"] <= ns["toi_da_cho_phep"])
    assert ns["ty_le_bao_dong"] == ns["n_co_bao_dong"] / ns["R"] and ns["R"] == da_ghi["cau_hinh"]["so_thi_truong_null"]
    k1 = da_ghi["kiem_1x_trong_dai_99"]
    assert k1["dai_99_quanh_80"] == list(H.dai_khop(k1["R"])) and k1["trong_dai"] is (
        k1["dai_99_quanh_80"][0] <= k1["n_QUA_G"] <= k1["dai_99_quanh_80"][1])


def test_pearson_chi2_va_tong_hop_Z_H_dung_tren_so_dem_dung_tay():
    a, b = -4.0, 70.0
    ket = {"mde80": {"probit": {"a": a, "b": b}}, "thong_so_vong": {"alpha_k": 0.05 / 3},
           "bang_ic_true_ty_le_bat": [{"delta_ic_true": x, "R": 400, "n_QUA_G": k}
                                      for x, k in ((0.04, 100), (0.06, 250), (0.08, 380), (0.20, 400))],
           "luoi": [{"R": 500, "n_bao_dong_Z": 10, "n_QUA_H": 0}],
           "muc": [{"luc": None}, {"luc": {"R": 400, "n_bao_dong_Z": 6, "n_QUA_H": 1}}]}
    chi2, bac = H.pearson_chi2(ket)
    tay = 0.0
    for x, k in ((0.04, 100), (0.06, 250), (0.08, 380)):
        p = _ND.cdf(a + b * x)
        tay += (k - 400 * p) ** 2 / (400 * p * (1 - p))
    tay += (400 - 400 * (1 - 1e-12)) ** 2 / (400 * (1 - 1e-12) * 1e-12)     # p ≈ 1 bị kẹp, không chia cho 0
    assert chi2 == pytest.approx(tay, rel=1e-6) and bac == 2 and math.isfinite(chi2)
    zh = H.tong_hop_Z_H(ket)
    assert zh == {"R": 900, "n_bao_dong_Z": 16, "ty_le_bao_dong_Z": 16 / 900, "n_QUA_H": 1,
                  "danh_nghia_moi_ung_vien": 0.05 / 3}


def test_main_in_bang_khong_chay_thi_truong_nao_va_in_dung_bang_da_ghi(monkeypatch, capsys):
    cho = {"n": 0}
    monkeypatch.setattr(H, "chay", lambda *a, **k: cho.update(n=cho["n"] + 1))
    monkeypatch.setattr(H, "cham_mot_thi_truong", lambda *a, **k: cho.update(n=cho["n"] + 1))
    assert H.main(["--in-bang"]) == 0
    ra = capsys.readouterr().out
    assert cho["n"] == 0 and "MDE80 = " in ra and "Pearson" in ra and "NULL smoke" in ra
    ket = H.doc_ket_qua(KET_QUA_DA_GHI)
    assert f"{ket['mde80']['delta_ic_true']:.4f}" in ra


def test_file_da_ghi_probit_khop_du_lieu_chi2_duoi_phan_vi_99_9(da_ghi):
    chi2, bac = H.pearson_chi2(da_ghi)
    assert bac == 9 and 0.0 < chi2 < 27.88      # χ²(9) phân vị 99,9% = 27,88: đường probit không lệch rõ
    zh = H.tong_hop_Z_H(da_ghi)
    assert zh["n_QUA_H"] == 0 and zh["ty_le_bao_dong_Z"] < 0.05     # B4 (H không bao giờ QUA) và B3 (Z ≤ 5%)


# ── gác G1 · G3 trên chính dụng cụ ────────────────────────────────────────────

TEN_GHI = {"push", "write_all", "append_rows", "ghi_ke_hoach", "record_trade", "update_trade", "write_text",
           "write_bytes", "to_csv", "to_json", "dump", "to_parquet", "to_pickle", "savetxt", "save", "savez",
           "executemany", "commit", "open"}
CAM_TEN_THAT = {"SO_UNG_VIEN", "doc_so_ung_vien", "sheets_store", "keo_bang_gia", "doc_so_that",
                "PaperTradingJournal"}
CAM_CHUOI = ("ung-vien", "phuong-an-bong", "UV-", "backtest", "cache")
NHAP_DUOC = {"__future__", "argparse", "contextlib", "datetime", "importlib", "json", "math", "os", "sys", "time",
             "concurrent", "pathlib", "statistics", "numpy", "cham_bong", "cham_xac_nhan", "thi_truong_gia"}


def test_G1_dung_cu_chi_ghi_bang_va_an_toan_ghi_va_khong_mo_file():
    cay = ast.parse(DUONG.read_text(encoding="utf-8"))
    goi = set(_goi_ten(cay))
    assert not (goi & TEN_GHI), sorted(goi & TEN_GHI)
    gi = [n for n in ast.walk(cay) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
          and n.func.attr == "ghi"]
    assert len(gi) == 1, "đúng MỘT chỗ ghi (`va_an_toan.ghi` trong `ghi_ket_qua`)"
    ham_ghi = _ham(cay)["ghi_ket_qua"]
    assert gi[0] in list(ast.walk(ham_ghi))


def test_G1_chuoi_duong_ghi_chi_la_file_ket_qua_duy_nhat():
    cay = ast.parse(DUONG.read_text(encoding="utf-8"))
    chuoi = [n.value for n in ast.walk(cay) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    duong = [s for s in chuoi if s.endswith(".json")]
    assert duong == ["thi-truong-gia-hieu-chuan.json"], duong


def test_G3_khong_thay_the_gioi_that_va_nhap_chi_trong_danh_sach():
    cay = ast.parse(DUONG.read_text(encoding="utf-8"))
    chuoi = [n.value for n in ast.walk(cay) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    sai = [s for s in chuoi if any(c in s for c in CAM_CHUOI)]
    assert not sai, sai
    ten = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Name):
            ten.add(n.id)
        elif isinstance(n, ast.Attribute):
            ten.add(n.attr)
    assert not (ten & CAM_TEN_THAT), sorted(ten & CAM_TEN_THAT)
    nhap = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            nhap |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            nhap.add((n.module or "").split(".")[0])
    assert nhap <= NHAP_DUOC, sorted(nhap - NHAP_DUOC)


def test_G3_nap_dung_cu_khong_keo_theo_gioi_that():
    ma = ("import sys, json, importlib.util; sys.path.insert(0, %r); "
          "s = importlib.util.spec_from_file_location('hc', %r); m = importlib.util.module_from_spec(s); "
          "s.loader.exec_module(m); "
          "cam = ['sheets_store', 'keo_bang_gia', 'doc_so_that', 'gspread', 'google_sheets_sync', "
          "'paper_trading', 'paper_runner', 'run_daily', 'vnstock', 'vnstock_data']; "
          "print(json.dumps([x for x in cam if x in sys.modules]))" % (str(GOC), str(DUONG)))
    r = subprocess.run([sys.executable, "-I", "-c", ma], capture_output=True, text=True, cwd=str(GOC),
                       timeout=180, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    assert r.returncode == 0, r.stderr[-800:]
    assert json.loads(r.stdout.strip().splitlines()[-1]) == [], r.stdout


def test_G1_chay_that_khong_de_lai_dau_vet_tren_dia(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    H.cham_mot_thi_truong(CHI_SO_TEST, 0.01)
    assert list(tmp_path.iterdir()) == []
