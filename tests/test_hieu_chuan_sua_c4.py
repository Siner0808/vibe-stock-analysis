"""Gác của `tools/hieu_chuan_sua_c4.py` (BƯỚC 301, ĐO 38): hiệu chuẩn A0 · PT · bảng 2×2 · κ_d của NULL-M.

Chỉ dòng hạt 9001 (thử) và các hàm thuần; KHÔNG BAO GIỜ dòng 2–10, không chạy lượt hiệu chuẩn thật. Đặc tả:
vibe_logs_c4sua/DAC-TA-SUA-C4.md mục 2–5, 7 (L2).
"""
from __future__ import annotations

import ast
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.append(str(GOC / "tools"))      # SAU gốc repo: `tools/cham_xac_nhan.py` là công cụ khác, không được che mô-đun cùng tên ở gốc

import cham_xac_nhan as cx  # noqa: E402
import hieu_chuan_sua_c4 as H  # noqa: E402
import thi_truong_gia as T  # noqa: E402
import vong_hoc_gia as V  # noqa: E402

DUONG_TOOL = GOC / "tools" / "hieu_chuan_sua_c4.py"


# ══ DÒNG HẠT ══════════════════════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("luong", [1, 9001, np.int64(1)])
def test_kiem_luong_nhan_dong_1_va_9001(luong):
    H.kiem_luong(luong)


@pytest.mark.parametrize("luong", [0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 9000, 9002, -1, True, 1.0, "1", None, np.int64(4)])
def test_kiem_luong_no_voi_moi_dong_khac_va_kieu_la(luong):
    with pytest.raises(ValueError):
        H.kiem_luong(luong)


def test_moi_don_vi_chay_deu_di_qua_kiem_luong():
    """Mỗi hàm chạm bộ sinh nổ với dòng 4 TRƯỚC khi sinh bất cứ gì (nếu không, `kiem_luong` bị tháo ở một đường)."""
    for ham, tham in ((H.don_a0, (4, 1)), (H.don_pt, (4, 1, 0.01)), (H.don_t1, (4, 1, 0.01)), (H.don_kd, (4, "k", 0.02, 1))):
        with pytest.raises(ValueError):
            ham(*tham)
    with pytest.raises(ValueError):
        H._viec_don_vi(("a0", 4, 1100001, 1100001))
    with pytest.raises(ValueError):
        T.ic_da_ghi_m(0, 1, 0.02)


def test_main_tu_choi_dong_ngoai_1_va_9001_ma_thoat_2(monkeypatch):
    monkeypatch.setattr(H, "_viec_don_vi", lambda a: pytest.fail("khong duoc chay don vi nao"))
    for luong in ("2", "3", "4", "5", "6", "9", "10", "0"):
        assert H.main(["--viec", "kd", "--luong", luong]) == 2


def test_main_dong_thu_phai_co_ra_va_khong_duoc_ghi_ra_file_chinh_thuc(monkeypatch, tmp_path):
    """`DUONG_KET_QUA` được đổi sang file tạm: một đột biến làm cửa mở sẽ ghi vào file tạm, không bao giờ vào `docs/` thật."""
    monkeypatch.setattr(H, "DUONG_KET_QUA", tmp_path / "chinh_thuc.json")
    monkeypatch.setattr(H, "_viec_don_vi", lambda a: pytest.fail("khong duoc chay don vi nao"))
    with pytest.raises(SystemExit):
        H.main(["--viec", "kd", "--luong", "9001"])
    assert H.main(["--viec", "kd", "--luong", "9001", "--ra", str(H.DUONG_KET_QUA)]) == 3


def _hang_so_nguyen(cay: ast.AST):
    for n in ast.walk(cay):
        if isinstance(n, ast.Constant) and isinstance(n.value, int) and not isinstance(n.value, bool):
            yield n


def test_AST_khong_dong_hat_2_den_10_o_dung_cu_ngoai_danh_sach_tu_choi():
    """Đọc NGUỒN: không số nguyên 2–10 nào là đối số vị trí của lời gọi sinh/chấm/oracle, và mọi phép gán tên chứa `LUONG`
    chỉ mang 1 · 9001 (hay `range`/`tuple` của nó). Danh sách từ chối duy nhất là `kiem_luong` (so với `LUONG_DUOC_PHEP`)."""
    cay = ast.parse(DUONG_TOOL.read_text(encoding="utf-8"))
    ten_cam = {"sinh_thi_truong", "sinh_null", "sinh_thi_truong_m", "sinh_thi_truong_2", "tinh_su_that", "tinh_su_that_m",
               "ic_da_ghi_m", "don_a0", "don_pt", "don_t1", "don_kd", "default_rng", "kiem_luong"}
    for n in ast.walk(cay):
        if isinstance(n, ast.Call):
            ten = getattr(n.func, "attr", getattr(n.func, "id", ""))
            if ten in ten_cam and n.args:
                a0 = n.args[0]
                assert not (isinstance(a0, ast.Constant) and isinstance(a0.value, int) and 2 <= a0.value <= 10), ten
        if isinstance(n, (ast.Assign, ast.AnnAssign)):
            muc = n.targets if isinstance(n, ast.Assign) else [n.target]
            if any(isinstance(t, ast.Name) and "LUONG" in t.id for t in muc):
                so = {c.value for c in _hang_so_nguyen(n.value)}
                assert so <= {1, 9001}, (ast.unparse(n), so)
    assert H.LUONG_DUOC_PHEP == (1, 9001)


def test_khong_nhap_dung_cu_chinh_thuc_va_khong_import_scipy():
    cay = ast.parse(DUONG_TOOL.read_text(encoding="utf-8"))
    nhap = {a.name.split(".")[0] for n in ast.walk(cay) if isinstance(n, ast.Import) for a in n.names} | \
           {(n.module or "").split(".")[0] for n in ast.walk(cay) if isinstance(n, ast.ImportFrom)}
    assert "chay_chinh_thuc_thi_truong_gia" not in nhap
    assert "scipy" not in nhap, "scipy khong nam trong requirements.txt (CI khong co)"


def test_khoi_chi_so_da_khai_roi_nhau_nam_ngoai_khoi_cu_va_khong_trung_bat_ky_dong_nao_khac():
    kd_max = H.chi_so_kd(H.KHAI["kd"]["dau"], len(H.KD_LUOI), H.KD_SO_KIEM - 1)
    khoi = {"a0": (H.KHAI["a0"]["dau"], H.KHAI["a0"]["dau"] + H.KHAI["a0"]["so"] - 1),
            "pt": (H.KHAI["pt"]["dau"], H.KHAI["pt"]["dau"] + H.KHAI["pt"]["so"] - 1),
            "t1": (H.KHAI["t1"]["dau"], H.KHAI["t1"]["dau"] + H.KHAI["t1"]["so"] - 1),
            "kd": (H.KHAI["kd"]["dau"], kd_max)}
    assert khoi["a0"] == (1_100_001, 1_120_000) and khoi["pt"] == (1_200_001, 1_200_200)
    assert khoi["t1"] == (1_300_001, 1_301_000) and khoi["kd"] == (1_400_001, 1_409_100)
    ds = sorted(khoi.values())
    assert all(a[1] < b[0] for a, b in zip(ds, ds[1:])), khoi
    assert ds[0][0] >= 1_100_001
    import hieu_chuan_thi_truong_gia as H1
    cu_max = max(H1.CHI_SO_GOC.values()) + 10 * H1.BUOC_DIEM
    assert cu_max < 1_100_001, "khoi moi phai nam NGOAI moi chi so ma hieu_chuan_thi_truong_gia dung"


def test_chi_so_kd_khong_cho_vuot_khoi_hay_diem_luoi():
    with pytest.raises(ValueError):
        H.chi_so_kd(1, len(H.KD_LUOI) + 1, 0)
    with pytest.raises(ValueError):
        H.chi_so_kd(1, 0, H.KD_BUOC_LUOI)
    with pytest.raises(ValueError):
        H.chi_so_kd(1, -1, 0)
    assert len({H.chi_so_kd(100, j, t) for j in range(len(H.KD_LUOI) + 1) for t in range(H.KD_SO_KIEM)}) == (len(H.KD_LUOI) + 1) * H.KD_SO_KIEM


# ══ BETA-NHỊ THỨC VÀ NHỊ THỨC ═════════════════════════════════════════════════════════════════════════════

def test_dai_betabinom_pin_so_da_tinh_bang_scipy():
    """Số cụ thể tính ở phiên này bằng `scipy.stats.betabinom.ppf` (lệnh ở docstring của test dưới) — ví dụ của đặc tả
    mục 3: k = 84/200 → [27 ; 58]. Hoán đổi a↔b cho dải gương [42 ; 73]; đổi 0,005 → 0,05 cho dải hẹp hơn."""
    d = H.dai_betabinom(84, 200)
    assert (d["thap"], d["cao"]) == (27, 58) and (d["a"], d["b"]) == (84.5, 116.5)
    assert (H.dai_betabinom(0, 200)["thap"], H.dai_betabinom(0, 200)["cao"]) == (0, 3)
    assert (H.dai_betabinom(200, 200)["thap"], H.dai_betabinom(200, 200)["cao"]) == (97, 100)
    hep = H.dai_betabinom(84, 200, q=0.05)
    assert hep["thap"] > 27 and hep["cao"] < 58


def test_dai_betabinom_khong_doi_xung_theo_k_va_co_dung_chieu():
    thap = H.dai_betabinom(40, 200)
    cao = H.dai_betabinom(160, 200)
    assert (thap["thap"], thap["cao"]) == (100 - cao["cao"], 100 - cao["thap"])     # gương qua k ↔ n − k
    assert thap["cao"] < H.dai_betabinom(120, 200)["thap"]


def test_betabinom_khop_scipy_neu_co_scipy():
    st = pytest.importorskip("scipy.stats")
    for k in range(0, 201, 7):
        a, b = k + 0.5, 200 - k + 0.5
        assert H.betabinom_ppf(0.005, 100, a, b) == st.betabinom.ppf(0.005, 100, a, b)
        assert H.betabinom_ppf(0.995, 100, a, b) == st.betabinom.ppf(0.995, 100, a, b)
        for x in (0, 13, 50, 99, 100):
            assert H.betabinom_pmf(x, 100, a, b) == pytest.approx(st.betabinom.pmf(x, 100, a, b), rel=1e-9, abs=1e-15)
        assert H.betabinom_cdf(37, 100, a, b) == pytest.approx(st.betabinom.cdf(37, 100, a, b), rel=1e-9)


def test_betabinom_pmf_tong_bang_1_va_ngoai_mien_bang_0():
    assert math.fsum(H.betabinom_pmf(x, 100, 84.5, 116.5) for x in range(101)) == pytest.approx(1.0, abs=1e-12)
    assert H.betabinom_pmf(-1, 100, 1, 1) == 0.0 and H.betabinom_pmf(101, 100, 1, 1) == 0.0
    assert H.betabinom_pmf(3, 10, 1, 1) == pytest.approx(1 / 11)       # Beta(1,1) → đều trên 0…n


def test_dai_betabinom_tu_choi_k_ngoai_mien():
    for k, n in ((-1, 200), (201, 200), (0, 0)):
        with pytest.raises(ValueError):
            H.dai_betabinom(k, n)


def test_nhi_thuc_ppf_khop_scipy_va_so_cua_dac_ta():
    assert H.nhi_thuc_ppf(0.999, 1000, 0.2677) == 312       # ví dụ của đặc tả mục 2 (scipy: binom.ppf → 312)
    assert H.nhi_thuc_ppf(0.999, 1000, 3 / 11) == 317       # ngưỡng ĐO 37
    st = pytest.importorskip("scipy.stats")
    for p in (0.2, 0.25, 0.2677, 0.2727272727, 0.29, 0.3):
        assert H.nhi_thuc_ppf(0.999, 1000, p) == st.binom.ppf(0.999, 1000, p)


# ══ A0 ════════════════════════════════════════════════════════════════════════════════════════════════════

def _ban_ghi_a0(k_g: int, n: int) -> list[dict]:
    ig = H.ten_spec_f().index(T.TEN_SPEC_G)
    return [{"khoa": i, "chon": [ig, (ig + 1) % 11, (ig + 2) % 11] if i < k_g else [(ig + 1) % 11, (ig + 2) % 11]} for i in range(n)]


def test_a0_nguong_doc_tu_p_hat_khong_phai_3_tren_11():
    kq = H.tong_hop_a0(_ban_ghi_a0(5354, 20000))        # p̂ = 0,2677
    assert kq["p_hat"] == pytest.approx(0.2677) and kq["nguong"] == 312 and not kq["dung"] and kq["N"] == 20000
    assert kq["nguong"] != 317, "ngưỡng không được lấy từ 3/11"
    assert kq["se"] == pytest.approx(math.sqrt(0.2677 * (1 - 0.2677) / 20000))


def test_a0_nguong_bam_theo_p_hat_hai_gia_tri_khac_nhau():
    a = H.tong_hop_a0(_ban_ghi_a0(4000, 20000))
    b = H.tong_hop_a0(_ban_ghi_a0(5000, 20000))
    assert a["p_hat"] == 0.2 and b["p_hat"] == 0.25
    assert a["nguong"] == H.nhi_thuc_ppf(0.999, 1000, 0.2) and b["nguong"] == H.nhi_thuc_ppf(0.999, 1000, 0.25)
    assert a["nguong"] < b["nguong"]


def test_a0_luat_dung_p_hat_cong_3_se_tu_0_3_khong_co_nguong():
    # N lớn: p̂ = 0,2980 → p̂ + 3·SE = 0,2980 + 0,00970 = 0,3077 ≥ 0,3 → DỪNG
    dung = H.tong_hop_a0(_ban_ghi_a0(5960, 20000))
    assert dung["dung"] and dung["nguong"] is None and dung["ly_do_dung"]
    # p̂ = 0,2900 → 0,2900 + 0,00961 = 0,2996 < 0,3: KHÔNG dừng
    ok = H.tong_hop_a0(_ban_ghi_a0(5800, 20000))
    assert not ok["dung"] and ok["nguong"] is not None
    # đúng chỗ 3 SE khác 2 SE: p̂ = 0,2925 → p̂ + 2·SE = 0,2989 < 0,3 ≤ p̂ + 3·SE = 0,3022 → DỪNG (đột biến "2 SE" phải đỏ)
    assert H.tong_hop_a0(_ban_ghi_a0(5850, 20000))["dung"]
    # N nhỏ làm SE lớn: p̂ = 0,25 với N = 100 → 0,25 + 3·0,0433 = 0,38 → DỪNG
    assert H.tong_hop_a0(_ban_ghi_a0(25, 100))["dung"]


def test_a0_ty_le_theo_spec_va_loi_khong_co_thi_truong():
    kq = H.tong_hop_a0(_ban_ghi_a0(5, 10))
    assert kq["ty_le_theo_spec"][T.TEN_SPEC_G] == 0.5 and set(kq["ty_le_theo_spec"]) == set(T.ho_spec_f())
    with pytest.raises(ValueError):
        H.tong_hop_a0([])


def test_a0_kiem_co_z_tu_choi_dau_ra_thieu_z_khong_huu_han_hay_rong():
    ok = [{"ten": "a", "z": 0.5}, {"ten": "b", "z": -1.0}, {"ten": "c", "z": 0}]
    H.kiem_co_z(ok)
    for xau in ([{"ten": "a"}], [{"ten": "a", "z": 1.0}, {"ten": "b"}], [{"ten": "a", "z": float("nan")}],
                [{"ten": "a", "z": float("inf")}], [{"ten": "a", "z": None}], [{"ten": "a", "z": "1"}], []):
        with pytest.raises(H.DeXuatThieuZ):
            H.kiem_co_z(xau)


def _boc_de_xuat(monkeypatch, them_z: bool):
    goc = V.de_xuat

    def boc(dong, gia):
        xep = goc(dong, gia)
        for x in xep:
            if them_z:
                x["z"] = float(x["delta"] * 10)
            else:
                x.pop("z", None)        # sau BƯỚC 300 bộ thật có z: gỡ đi để dựng đúng ca "thiếu z"
        return xep
    monkeypatch.setattr(V, "de_xuat", boc)


def test_a0_tu_choi_chay_khi_bo_de_xuat_that_thieu_z_va_khong_sinh_thi_truong_dong_1(monkeypatch, tmp_path):
    """Cây hiện tại (trước BƯỚC 300) KHÔNG có `z` ở `vong_hoc_gia.de_xuat`; cửa nổ trước khi sinh bất cứ thị trường dòng 1."""
    _boc_de_xuat(monkeypatch, False)
    monkeypatch.setattr(H, "_viec_don_vi", lambda a: pytest.fail("khong duoc chay don vi nao"))
    ra = tmp_path / "a0.json"
    assert H.main(["--viec", "a0", "--luong", "9001", "--so", "2", "--ra", str(ra)]) == 3
    assert not ra.exists()
    with pytest.raises(H.DeXuatThieuZ):
        H.kiem_de_xuat_co_z_truoc_khi_chay()
    _boc_de_xuat(monkeypatch, True)
    H.kiem_de_xuat_co_z_truoc_khi_chay()


def test_a0_don_vi_dung_cach_chay_vong_goi_bo_de_xuat(monkeypatch):
    """`don_a0` phải khai ĐÚNG những spec mà `chay_vong` khai trên cùng thị trường (cùng cửa sổ đã nhìn, cùng `chon_khai`)."""
    _boc_de_xuat(monkeypatch, True)
    tt = T.sinh_null(9001, 2, co_su_that=False)
    r = H.don_a0(9001, 2)
    ten = H.ten_spec_f()
    cua_so = []
    boc = V.de_xuat

    def ghi_cua_so(dong, gia):
        cua_so.append(len(gia))
        return boc(dong, gia)
    monkeypatch.setattr(V, "de_xuat", ghi_cua_so)
    H.de_xuat_va_chon(tt.dong_quyet_dinh(), tt.gia)
    vong = V.chay_vong(tt.dong_quyet_dinh(), tt.gia, so_hoan_vi=50)
    assert [ten[i] for i in r["chon"]] == vong["de_xuat"]["da_chon"] and r["khoa"] == 2
    assert len(cua_so) == 2 and cua_so[0] == cua_so[1] == vong["cua_so_nhin"], "bo de xuat phai thay DUNG cua so da nhin cua chay_vong"


# ══ PT, 2×2 ═══════════════════════════════════════════════════════════════════════════════════════════════

def _gp(tt, delta, p, sd=0.01):
    return {"tt": tt, "delta": delta, "p": p, "z": 0.0, "sd_null": sd, "n_phien": 252, "n_ma": 60}


def _ban_ghi_pt(k: int, n: int, dq: int = 0) -> list[dict]:
    return [{"khoa": i, "nguong": 0.05 / 3, "dq_khong_ok": dq if i == 0 else 0, "so_dong": 100,
             "Gp": _gp("QUA" if i < k else "DANG CHAM", 0.03, 0.001 if i < k else 0.4),
             "G": _gp("DANG CHAM", 0.01, 0.3), "Z": _gp("DANG CHAM", 0.0, 0.5), "H": _gp("THUA", -0.01, 0.001)}
            for i in range(n)]


def test_pt_dai_va_luat_dung():
    kq = H.tong_hop_pt(_ban_ghi_pt(84, 200))
    assert kq["k"] == 84 and kq["n_cal"] == 200 and kq["dai_99"] == [27, 58] and not kq["dung"]
    assert kq["o"]["Gp"]["QUA"] == 84 and kq["o"]["H"]["bao_dong"] == 200 and kq["o"]["G"]["bao_dong"] == 0
    assert H.tong_hop_pt(_ban_ghi_pt(39, 200))["dung"]               # 0,195 < 0,2
    assert not H.tong_hop_pt(_ban_ghi_pt(40, 200))["dung"]           # 0,2 đúng biên: KHÔNG dừng
    assert not H.tong_hop_pt(_ban_ghi_pt(140, 200))["dung"]          # 0,7 đúng biên
    assert H.tong_hop_pt(_ban_ghi_pt(141, 200))["dung"]
    dq = H.tong_hop_pt(_ban_ghi_pt(84, 200, dq=1))
    assert dq["dung"] and any("data_quality" in s for s in dq["ly_do_dung"])


def test_pt_dem_QUA_theo_trang_thai_cua_g_phay_khong_theo_p_hay_delta():
    ban = _ban_ghi_pt(10, 20)
    ban[0]["Gp"]["tt"] = "THUA"                   # p nhỏ nhưng Δ âm: không QUA
    assert H.tong_hop_pt(ban)["k"] == 9


def test_o_2x2_tinh_m_s_sigma_P():
    ban = [{"nguong": 0.05 / 3, "G": _gp("QUA", d, 0.001, sd)} for d, sd in ((0.02, 0.01), (0.04, 0.03), (0.06, 0.02))]
    ban += [{"nguong": 0.05 / 3, "G": _gp("DANG CHAM", 0.03, 0.4, 0.02)}]
    o = H.o_2x2(ban, "G")
    assert o["n"] == 4 and o["QUA"] == 3 and o["P"] == 0.75
    assert o["m"] == pytest.approx((0.02 + 0.04 + 0.06 + 0.03) / 4)
    assert o["s"] == pytest.approx(np.std([0.02, 0.04, 0.06, 0.03], ddof=1))
    assert o["sigma_bar"] == pytest.approx((0.01 + 0.03 + 0.02 + 0.02) / 4)


def test_in_khoi_chiu_duoc_mot_thi_truong_khong_co_do_lech_chuan():
    """Dòng thử 9001 với `--so 1`: s = None. (Lỗi thật gặp ở lượt thử pt: `format` nổ sau 5 phút chạy.)"""
    for viec, tong in (("pt", H.tong_hop_pt), ("t1", H.tong_hop_t1)):
        khoi = {"luong": 9001, "trang_thai": "XONG", "git": {"sha": "abc", "sach": False}, "giay": 1.0, "ket_qua": tong(_ban_ghi_pt(1, 1))}
        assert "m " in "\n".join(H.in_khoi(viec, khoi))


def test_tom_tat_cham_no_khi_chua_toi_moc():
    with pytest.raises(ValueError):
        H.tom_tat_cham({"ket": None, "trang_thai": "CHUA TOI MOC"})


def test_cham_g_va_gp_khop_cx_cham_ba_ung_vien_cua_chinh_so_tay_o_tang_1():
    """`cham_mot` cho G ở khe của G′ cho ĐÚNG Δ, p mà `cx.cham` với sổ (G, Z, H) cho — tắt đường tắt thì Z, H không chấm hai lần."""
    import hieu_chuan_thi_truong_gia as H1
    tt = T.sinh_thi_truong(9001, 3, 0.02, co_su_that=False)
    dong, kh = tt.dong_quyet_dinh(), T.dong_thoi_gian()["khai_ngay"]
    ra = H.cham_g_va_gp(dong, tt.gia, kh, so_hoan_vi=200)
    r = cx.cham(dong, H1.so_ung_vien_bo_ba(), {"gia": tt.gia, "keo_luc": H1.keo_luc_gia(tt.ngay[-1]),
                                                "nguon": {m: "vci" for m in tt.ma}}, cx.HAT_RNG, 200)
    for t_ra, t_cu in (("G", "G"), ("Z", "Z"), ("H", "H")):
        assert ra[t_ra]["delta"] == r["chi_tiet"][t_cu]["delta"] and ra[t_ra]["p"] == r["chi_tiet"][t_cu]["p"]
    assert ra["nguong"] == r["nguong"] == pytest.approx(0.05 / 3)
    assert set(ra) == {"G", "Gp", "Z", "H", "nguong"} and ra["Gp"]["delta"] != ra["G"]["delta"]
    assert ra["G"]["sd_null"] > 0 and ra["Gp"]["sd_null"] > 0


def test_so_ung_vien_bo_ba_gp_dung_spec_va_ngay():
    kh = T.dong_thoi_gian()["khai_ngay"]
    so = H.so_ung_vien_bo_ba_gp(kh)
    ho = T.ho_spec_oracle()
    assert [so["ung_vien"][t]["spec"] for t in ("Gp", "Z", "H")] == [ho["bo_momentum_score"], ho[T.TEN_SPEC_Z], ho[T.TEN_SPEC_H]]
    assert [so["ung_vien"][t]["khai_ngay"] for t in ("Gp", "Z", "H")] == list(kh)
    assert H.TEN_SPEC_GP == "bo_momentum_score"


def test_doc_kappa_2x_doc_dung_muc_2x_cua_file_hieu_chuan():
    muc = json.loads((GOC / "docs" / "thi-truong-gia-hieu-chuan.json").read_text(encoding="utf-8"))["muc"]
    assert H.doc_kappa_2x() == [m["kappa"] for m in muc if m["he_so"] == 2.0][0] > 0


# ══ κ_d ═══════════════════════════════════════════════════════════════════════════════════════════════════

def _luoi_ic(ic: list[float], n: int = 50, sd: float = 0.0) -> dict:
    rng = np.random.default_rng(0)
    return {k: list(v + sd * rng.standard_normal(n)) if sd else [v] * n for k, v in zip(H.KD_LUOI, ic)}


def test_kd_chon_diem_gan_nhat_muc_tieu():
    ic = [0.06, 0.07, 0.08, 0.09, 0.097, 0.108, 0.118, 0.127, 0.136]
    kq = H.chon_kappa_d(_luoi_ic(ic))
    assert not kq["that_bai"] and kq["kappa_d"] == H.KD_LUOI[4] == 0.02 and kq["ly_do"] == []
    ic2 = list(ic)
    ic2[4], ic2[5] = 0.0960, 0.1012
    assert H.chon_kappa_d(_luoi_ic(ic2))["kappa_d"] == H.KD_LUOI[5]


def test_kd_hoa_chon_kappa_nho_hon(monkeypatch):
    """Mục tiêu 0,5 và hai điểm 0,4375 · 0,5625 cách ĐÚNG 0,0625 (số nhị phân đúng): hoà → κ_d nhỏ hơn."""
    monkeypatch.setattr(H, "KD_MUC_TIEU", 0.5)
    ic = [0.1, 0.2, 0.3, 0.4, 0.4375, 0.5625, 0.6, 0.7, 0.8]
    assert H.chon_kappa_d(_luoi_ic(ic))["gan_nhat"] == H.KD_LUOI[4]


@pytest.mark.parametrize("ic,nhan", [
    ([0.11, 0.12, 0.13, 0.14, 0.15, 0.16, 0.17, 0.18, 0.19], "kep"),
    ([0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09], "kep"),
    ([0.05, 0.06, 0.07, 0.08, 0.10, 0.09, 0.112, 0.12, 0.13], "giam"),     # 0,10 → 0,09: giảm quá 2 SE (SE ≈ 0)
    ([0.10, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16, 0.17, 0.18], "RIA"),
    ([0.04, 0.05, 0.06, 0.07, 0.08, 0.085, 0.12, 0.13, 0.14], "> 0.01"),
])
def test_kd_that_bai_va_khong_chon(ic, nhan):
    kq = H.chon_kappa_d(_luoi_ic(ic))
    assert kq["that_bai"] and kq["kappa_d"] is None and any(nhan in s for s in kq["ly_do"]), kq["ly_do"]


def test_kd_don_dieu_chiu_nhieu_trong_hai_se():
    """Một điểm tụt nhỏ nằm trong 2 SE ghép KHÔNG là thất bại (nhiễu mẫu)."""
    ic = [0.06, 0.07, 0.08, 0.09, 0.1005, 0.0995, 0.118, 0.127, 0.136]
    kq = H.chon_kappa_d(_luoi_ic(ic, n=50, sd=0.01))
    assert not any("giam" in s for s in kq["ly_do"])


def test_kd_kiem_dai_10_phan_tram():
    assert H.kiem_kd([0.0905] * 40)["dat"] and H.kiem_kd([0.1095] * 40)["dat"]
    assert not H.kiem_kd([0.089] * 40)["dat"] and not H.kiem_kd([0.111] * 40)["dat"]
    assert H.kiem_kd([0.1, 0.1])["dai"] == [pytest.approx(0.09), pytest.approx(0.11)]


# ══ CỬA ═══════════════════════════════════════════════════════════════════════════════════════════════════

def _git_gia(sach: bool = True, sha: str = "abc123", loi: bool = False):
    def git(*doi):
        if loi:
            return 127, ""
        if doi[:2] == ("rev-parse", "HEAD"):
            return 0, sha + "\n"
        if doi[0] == "status":
            return 0, "" if sach else " M thi_truong_gia.py\n?? x.py\n"
        return 1, ""
    return git


def _cong(viec="a0", luong=1, dau=None, so="mac_dinh", ra=None, **kw):
    khai = H.KHAI[viec]
    kw.setdefault("ket_hien_co", {"cac_viec": {}})        # KHÔNG đọc docs/thi-truong-gia-hieu-chuan-do38.json thật trên đĩa
    return H.kiem_cong(viec, luong, khai["dau"] if dau is None else dau, khai.get("so") if so == "mac_dinh" else so,
                       H.DUONG_KET_QUA if ra is None else ra, git=kw.pop("git", _git_gia()), **kw)


def test_cong_dong_1_cay_sach_dung_khai_di_qua_va_ghi_ma_bam():
    assert _cong() == {"sha": "abc123", "sach": True}


def test_cong_tu_choi_cay_ban_o_dong_1_va_in_het_ly_do():
    with pytest.raises(H.CongTu) as e:
        _cong(git=_git_gia(sach=False), dau=5)
    assert len(e.value.ly_do) == 2 and any("ban" in s for s in e.value.ly_do) and any("da khai" in s for s in e.value.ly_do)


def test_cong_cay_chi_ban_vi_chinh_file_ket_qua_van_sach():
    def git(*doi):
        if doi[0] == "status":
            return 0, f"?? {H.TEN_FILE}\n"
        return _git_gia()(*doi)
    assert _cong(git=git)["sach"] is True


def test_cong_khong_doc_duoc_git_la_khong_chay():
    with pytest.raises(H.CongTu):
        _cong(git=_git_gia(loi=True))


def test_cong_dong_thu_cay_ban_chi_ghi_nhan(tmp_path):
    ra = tmp_path / "thu.json"
    kq = H.kiem_cong("a0", 9001, 1, 2, ra, git=_git_gia(sach=False), ket_hien_co={})
    assert kq["sach"] is False


def test_cong_dong_thu_khong_duoc_ghi_ra_file_chinh_thuc():
    with pytest.raises(H.CongTu):
        H.kiem_cong("pt", 9001, 1, 1, H.DUONG_KET_QUA, git=_git_gia(), ket_hien_co={})


def test_cong_dong_1_chi_ghi_ra_file_chinh_thuc(tmp_path):
    with pytest.raises(H.CongTu):
        _cong(ra=tmp_path / "khac.json")


@pytest.mark.parametrize("viec", H.TEN_VIEC)
def test_cong_khoi_da_XONG_khong_chay_lai_ke_ca_tiep_tuc(viec):
    hien_co = {"cac_viec": {viec: {"trang_thai": "XONG", "luong": 1, "git": {"sha": "abc123"}}}}
    for tiep in (False, True):
        with pytest.raises(H.CongTu) as e:
            _cong(viec=viec, ket_hien_co=hien_co, tiep_tuc=tiep)
        assert any("DA xong" in s for s in e.value.ly_do)


def test_cong_khoi_dang_do_chi_chay_tiep_cung_ma_bam_va_cung_dong():
    do = {"cac_viec": {"a0": {"trang_thai": "DANG CHAY", "luong": 1, "git": {"sha": "abc123"}}}}
    with pytest.raises(H.CongTu):
        _cong(ket_hien_co=do)                                        # không --tiep-tuc
    assert _cong(ket_hien_co=do, tiep_tuc=True)["sha"] == "abc123"
    with pytest.raises(H.CongTu):
        _cong(ket_hien_co=do, tiep_tuc=True, git=_git_gia(sha="khac"))
    do9 = {"cac_viec": {"a0": {"trang_thai": "DANG CHAY", "luong": 9001, "git": {"sha": "abc123"}}}}
    with pytest.raises(H.CongTu):
        _cong(ket_hien_co=do9, tiep_tuc=True)
    with pytest.raises(H.CongTu):
        _cong(ket_hien_co={"cac_viec": {}}, tiep_tuc=True)           # không có gì để chạy tiếp


def test_cong_khoi_khac_khong_can_tro():
    do = {"cac_viec": {"kd": {"trang_thai": "XONG", "luong": 1, "git": {"sha": "abc123"}}}}
    assert _cong(viec="a0", ket_hien_co=do)["sha"] == "abc123"


def test_cong_nong_tu_choi_dong_ngoai_1_va_9001_va_viec_la():
    with pytest.raises(ValueError):
        H.kiem_cong("a0", 4, 1, 1, Path("x.json"), git=_git_gia(), ket_hien_co={})
    with pytest.raises(ValueError):
        H.kiem_cong("zz", 1, 1, 1, Path("x.json"), git=_git_gia(), ket_hien_co={})


# ══ CHẠY: nguyên tử, chạy tiếp, ghi mỗi 12 ════════════════════════════════════════════════════════════════

def test_ghi_file_di_qua_va_an_toan_ghi_khong_ghi_tay():
    cay = ast.parse(DUONG_TOOL.read_text(encoding="utf-8"))
    ham = next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == "ghi_khoi")
    goi = {ast.unparse(n.func) for n in ast.walk(ham) if isinstance(n, ast.Call)}
    assert "va_an_toan.ghi" in goi
    for n in ast.walk(cay):
        if isinstance(n, ast.Call):
            ten = ast.unparse(n.func)
            assert not ten.endswith("write_text") and not ten.endswith("write_bytes") and ten != "open", ast.unparse(n)


def test_luu_moi_khong_qua_12():
    assert H.LUU_MOI <= 12


@pytest.fixture
def kd_gia(monkeypatch):
    """IC giả TẤT ĐỊNH = 5·κ_d (+ nhiễu nhỏ theo chỉ số): chỉ để kiểm cơ chế chạy/ghi/chạy tiếp, không phải số đo."""
    monkeypatch.setattr(H, "don_kd", lambda luong, khoa, kappa_d, chi_so: {
        "khoa": khoa, "kappa_d": float(kappa_d), "chi_so": int(chi_so), "ic": 5.0 * kappa_d + 0.0005 * ((chi_so % 7) - 3) / 3})


def test_chay_kd_dong_thu_xong_ghi_khoi_va_in_duoc(tmp_path, capsys, kd_gia):
    ra = tmp_path / "kd.json"
    khoi = H.chay_viec("kd", 9001, 1, 2, ra, {"sha": "x", "sach": False}, so_kiem=3, in_tien_do=False)
    ghi = json.loads(ra.read_text(encoding="utf-8"))["cac_viec"]["kd"]
    assert ghi["trang_thai"] == "XONG" and ghi["luong"] == 9001 and ghi["git"] == {"sha": "x", "sach": False}
    assert len(ghi["ban_ghi"]) == 2 * len(H.KD_LUOI) + 3 and ghi["chon"]["ic_tb"].keys() == {str(k) for k in H.KD_LUOI}
    assert ghi["cau_hinh"]["he_so_d"] == T.HE_SO_D and ghi["cau_hinh"]["luoi"] == list(H.KD_LUOI)
    assert "κ_d" in "\n".join(H.in_khoi("kd", khoi))


def test_chay_tiep_sau_gian_doan_cho_dung_ket_qua_nhu_chay_mot_mach(tmp_path, monkeypatch, kd_gia):
    goc = H._viec_don_vi
    dem = {"n": 0}

    def hong(a):
        dem["n"] += 1
        if dem["n"] > 7:
            raise RuntimeError("mat dien")
        return goc(a)

    ra1, ra2 = tmp_path / "mot_mach.json", tmp_path / "gian_doan.json"
    H.chay_viec("kd", 9001, 1, 2, ra1, {"sha": "x", "sach": True}, luu_moi=3, so_kiem=2, in_tien_do=False)
    monkeypatch.setattr(H, "_viec_don_vi", hong)
    with pytest.raises(RuntimeError):
        H.chay_viec("kd", 9001, 1, 2, ra2, {"sha": "x", "sach": True}, luu_moi=3, so_kiem=2, in_tien_do=False)
    giua = json.loads(ra2.read_text(encoding="utf-8"))["cac_viec"]["kd"]
    assert giua["trang_thai"] == "DANG CHAY" and 6 <= len(giua["ban_ghi"]) <= 7      # lưu mỗi 3: mất tối đa 2 đơn vị
    monkeypatch.setattr(H, "_viec_don_vi", goc)
    H.chay_viec("kd", 9001, 1, 2, ra2, {"sha": "x", "sach": True}, tiep_tuc=True, luu_moi=3, so_kiem=2, in_tien_do=False)
    a = json.loads(ra1.read_text(encoding="utf-8"))["cac_viec"]["kd"]
    b = json.loads(ra2.read_text(encoding="utf-8"))["cac_viec"]["kd"]
    assert b["trang_thai"] == "XONG"
    assert sorted(map(json.dumps, a["ban_ghi"])) == sorted(map(json.dumps, b["ban_ghi"]))     # không trùng, không thiếu
    assert a["ket_qua"] == b["ket_qua"] and a["chon"] == b["chon"]


def test_ghi_khoi_khong_de_khoi_khac(tmp_path):
    ra = tmp_path / "f.json"
    H.ghi_khoi(ra, "a0", {"trang_thai": "XONG", "x": 1})
    H.ghi_khoi(ra, "kd", {"trang_thai": "DANG CHAY", "x": 2})
    d = json.loads(ra.read_text(encoding="utf-8"))["cac_viec"]
    assert d["a0"]["x"] == 1 and d["kd"]["x"] == 2


def test_chay_khong_ghi_de_khoi_da_xong_qua_main(tmp_path):
    ra = tmp_path / "t.json"
    assert H.main(["--viec", "kd", "--luong", "9001", "--so", "1", "--ra", str(ra)]) in (0, 4)     # THẬT (n = 1 mỗi điểm lưới)
    truoc = ra.read_text(encoding="utf-8")
    assert H.main(["--viec", "kd", "--luong", "9001", "--so", "1", "--ra", str(ra)]) == 3
    assert H.main(["--viec", "kd", "--luong", "9001", "--so", "1", "--ra", str(ra), "--tiep-tuc"]) == 3
    assert ra.read_text(encoding="utf-8") == truoc


def test_kd_that_bai_ghi_dung_va_ma_thoat_4(tmp_path, monkeypatch):
    """Lưới không kẹp 0,10 → khối XONG với `dung`, không khối KIỂM, mã thoát 4 (báo, không chọn lại)."""
    monkeypatch.setattr(H, "don_kd", lambda luong, khoa, kappa_d, chi_so: {"khoa": khoa, "kappa_d": kappa_d, "chi_so": chi_so, "ic": 0.5})
    ra = tmp_path / "kd.json"
    assert H.main(["--viec", "kd", "--luong", "9001", "--so", "2", "--ra", str(ra)]) == 4
    k = json.loads(ra.read_text(encoding="utf-8"))["cac_viec"]["kd"]
    assert k["trang_thai"] == "XONG" and k["ket_qua"]["dung"] and k["ket_qua"]["kappa_d"] is None
    assert not any(r["khoa"].startswith("kiem|") for r in k["ban_ghi"])


def test_doc_in_ket_qua_da_ghi_khong_sinh_gi(tmp_path, capsys, monkeypatch):
    ra = tmp_path / "kd.json"
    H.chay_viec("kd", 9001, 1, 1, ra, {"sha": "x", "sach": True}, so_kiem=1, in_tien_do=False)
    monkeypatch.setattr(H, "_viec_don_vi", lambda a: pytest.fail("khong sinh"))
    assert H.main(["--doc", "--ra", str(ra)]) == 0
    assert "== kd" in capsys.readouterr().out
    assert H.main(["--doc", "--ra", str(tmp_path / "khong_co.json")]) == 2
