"""Gác ý 5 — tra tiền lệ, CHỈ ĐỂ HIỆN (BƯỚC 215; `docs/thiet-ke-y5-tien-le.md` mục 8).

Kho giả tính tay. Khoá = (dải điểm vào, nấc VN-Index cao hơn MA50): dải [62, 70) · [70, ∞),
nấc [0, 2) · [2, 5) · [5, ∞) — người dùng chốt 20/10/2026 *"Dải điểm × độ cao VNI
(Recommended)"*. Hàng rào: tiền lệ chỉ gồm lệnh có NGÀY RA < NGÀY VÀO của lệnh đang xem.
"""
from __future__ import annotations

import ast
import json
import math
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import paper_trading as pt  # noqa: E402
import tien_le as tl  # noqa: E402
from tien_le import KHONG_XEP_DUOC, MO_PHONG, THAT, TienLe  # noqa: E402

THAP, CAO = f"{pt.BUY_THRESHOLD:g}–69", "≥70"


def _t(ra: str, lnr: float, diem: float = 65, vni: float = 1.0, nguon: str = MO_PHONG,
       ma: str = "FPT", vao: str = "2022-01-03") -> TienLe:
    return TienLe(nguon, ma, vao, ra, diem, vni, lnr, "STOP_LOSS")


# ─────────────────────────── khoá nhóm ở mọi biên ───────────────────────────

@pytest.mark.parametrize("diem, mong", [
    (61.99, None), (62, THAP), (69.99, THAP), (70, CAO), (85, CAO),
    (None, None), (float("nan"), None), ("khong", None)])
def test_DAI_DIEM_o_moi_bien(diem, mong):
    assert tl.dai_diem(diem) == mong


@pytest.mark.parametrize("pct, mong", [
    (-0.01, None), (0, "0–2%"), (1.99, "0–2%"), (2, "2–5%"), (4.99, "2–5%"),
    (5, "≥5%"), (12.3, "≥5%"), (None, None), (float("nan"), None)])
def test_NAC_VNI_o_moi_bien(pct, mong):
    assert tl.nac_vni(pct) == mong


def test_KHOA_thieu_mot_chieu_la_KHONG_XEP_DUOC_khong_gop():
    assert tl.khoa_nhom(65, 1.0) == (THAP, "0–2%")
    assert tl.khoa_nhom(61, 1.0) == KHONG_XEP_DUOC
    assert tl.khoa_nhom(65, -0.5) == KHONG_XEP_DUOC
    assert tl.khoa_nhom(None, 3.0) == KHONG_XEP_DUOC


def test_DAI_DIEM_suy_tu_BUY_THRESHOLD_khong_go_tay():
    """Ngưỡng dưới của dải thấp là `paper_trading.BUY_THRESHOLD` (AST: tên, không phải số)."""
    cay = ast.parse((GOC / "tien_le.py").read_text(encoding="utf-8"))
    ham = next(n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == "dai_diem")
    ten = {n.id for n in ast.walk(ham) if isinstance(n, ast.Name)}
    assert "BUY_THRESHOLD" in ten
    so = {n.value for n in ast.walk(ham) if isinstance(n, ast.Constant)
          and isinstance(n.value, (int, float)) and not isinstance(n.value, bool)}
    assert 62 not in so and 62.0 not in so


# ─────────────────────────── hàng rào thời gian ───────────────────────────

def test_HANG_RAO_ngay_ra_PHAI_truoc_ngay_vao_cung_ngay_bi_loai():
    kho = [_t("2026-09-30", 1.0), _t("2026-10-01", 1.0), _t("2026-10-02", 1.0)]
    assert [t.ngay_ra for t in tl.chon_tien_le(kho, "2026-10-01")] == ["2026-09-30"]
    assert [t.ngay_ra for t in tl.chon_tien_le(kho, "2026-10-01 09:15:00")] == ["2026-09-30"]


# ─────────────────────────── tóm tắt nhóm ───────────────────────────

def test_NHOM_9_tien_le_CHUA_DU_10_thi_DU():
    kho = [_t(f"2022-02-{i + 1:02d}", 1.0 if i % 2 else -1.0) for i in range(10)]
    chin = tl.tom_tat(kho[:9], 65, 1.0, "2026-01-05")
    muoi = tl.tom_tat(kho, 65, 1.0, "2026-01-05")
    assert (chin["du"], chin["nhom"]["n"]) == (False, 9)
    assert (muoi["du"], muoi["nhom"]["n"]) == (True, 10)
    assert chin["khong_phan_biet"] is False


def test_DEM_THANG_THUA_HOA_theo_so_bai_hoc_va_dem_nguon():
    kho = [_t("2022-02-01", 2.0), _t("2022-02-02", -1.0), _t("2022-02-03", 0.0, nguon=THAT)]
    g = tl.tom_tat(kho, 65, 1.0, "2026-01-05")["nhom"]
    assert (g["thang"], g["thua"], g["hoa"], g["n_mo_phong"], g["n_that"]) == (1, 1, 1, 2, 1)
    assert g["ty_le"] == pytest.approx(1 / 3)


def test_NHOM_CHI_GOM_CUNG_KHOA_con_NEN_la_moi_tien_le_truoc_ngay_vao():
    kho = ([_t(f"2022-03-{i + 1:02d}", 1.0) for i in range(10)]                     # cùng khoá
           + [_t(f"2022-04-{i + 1:02d}", -1.0, diem=75) for i in range(10)]          # dải khác
           + [_t(f"2022-05-{i + 1:02d}", -1.0, vni=3.0) for i in range(10)])         # nấc khác
    kq = tl.tom_tat(kho, 65, 1.0, "2026-01-05")
    assert kq["khoa"] == (THAP, "0–2%") and kq["nhom"]["n"] == 10 and kq["nhom"]["thang"] == 10
    assert kq["nen"]["n"] == 30 and kq["nen"]["thang"] == 10


def test_KTC_CHUA_nen_thi_KHONG_PHAN_BIET_khong_chua_thi_co():
    nen_nua = ([_t(f"2022-03-{i + 1:02d}", 1.0 if i < 5 else -1.0) for i in range(10)]
               + [_t(f"2022-04-{i + 1:02d}", 1.0 if i < 5 else -1.0, diem=75) for i in range(10)])
    assert tl.tom_tat(nen_nua, 65, 1.0, "2026-01-05")["khong_phan_biet"] is True
    lech = ([_t(f"2022-03-{i + 1:02d}", 1.0) for i in range(12)]
            + [_t(f"2022-05-{i + 1:02d}", -1.0, diem=75) for i in range(28)]
            + [_t(f"2022-06-{i + 1:02d}", -1.0, diem=75) for i in range(28)])
    kq = tl.tom_tat(lech, 65, 1.0, "2026-01-05")
    assert kq["nhom"]["ktc"][0] > kq["nen"]["ty_le"] and kq["khong_phan_biet"] is False


def test_KHONG_XEP_DUOC_thi_nhom_RONG_nhung_van_co_NEN():
    kho = [_t(f"2022-03-{i + 1:02d}", 1.0) for i in range(10)]
    kq = tl.tom_tat(kho, 61, 1.0, "2026-01-05")
    assert kq["khoa"] == KHONG_XEP_DUOC and kq["nhom"]["n"] == 0 and kq["nen"]["n"] == 10


def test_BA_CA_GAN_NHAT_theo_ngay_ra():
    kho = [_t(f"2022-03-{i + 1:02d}", 1.0, ma=f"M{9 - i}") for i in range(6)]   # mã ngược ngày
    gan = tl.tom_tat(kho, 65, 1.0, "2026-01-05")["gan_nhat"]
    assert [t.ngay_ra for t in gan] == ["2022-03-06", "2022-03-05", "2022-03-04"]


@pytest.mark.parametrize("k, n, lo, hi", [(5, 10, 0.2366, 0.7634), (0, 10, 0.0, 0.2775),
                                          (10, 10, 0.7225, 1.0)])
def test_WILSON_so_tinh_tay(k, n, lo, hi):
    a, b = tl.wilson(k, n)
    assert (a, b) == (pytest.approx(lo, abs=1e-4), pytest.approx(hi, abs=1e-4))
    assert tl.wilson(0, 0) is None


# ─────────────────────────── đọc kho và nhật ký ───────────────────────────

def test_DOC_KHO_bo_dong_thieu_ket_cuc():
    du = {"lenh": [
        {"ma": "FPT", "ngay_vao": "2022-01-03", "ngay_ra": "2022-01-10", "diem_vao": 64,
         "vni_pct_tren_ma50": 1.5, "loi_nhuan_rong_pct": -2.0, "ly_do_thoat": "STOP_LOSS"},
        {"ma": "HPG", "ngay_vao": "2022-01-03", "ngay_ra": "", "diem_vao": 64,
         "vni_pct_tren_ma50": 1.5, "loi_nhuan_rong_pct": 1.0},
        {"ma": "VNM", "ngay_vao": "2022-01-03", "ngay_ra": "2022-01-11", "diem_vao": 64,
         "vni_pct_tren_ma50": 1.5, "loi_nhuan_rong_pct": None}]}
    kho = tl.doc_kho(du)
    assert [(t.ma, t.nguon, t.loi_nhuan_rong_pct) for t in kho] == [("FPT", MO_PHONG, -2.0)]


def test_DONG_NHAT_KY_doc_boi_canh_JSON_va_bo_dong_chua_dong():
    dong = {"symbol": "HDB", "entry_date": "2026-10-01", "exit_date": "2026-10-09",
            "entry_score": 66, "loi_nhuan_rong_pct": 3.2, "exit_reason": "SIGNAL_REVERSED",
            "boi_canh": json.dumps({"vni_pct_tren_ma50": 2.4})}
    t = tl.tu_dong_nhat_ky(dong)
    assert (t.nguon, t.ma, t.vni_pct_tren_ma50, t.diem_vao) == (THAT, "HDB", 2.4, 66.0)
    assert tl.tu_dong_nhat_ky(dict(dong, exit_date="")) is None
    assert tl.tu_dong_nhat_ky(dict(dong, boi_canh="khong-phai-json")).vni_pct_tren_ma50 is None


# ─────────────────────────── tệp kho trong repo ───────────────────────────

def test_TEP_KHO_dung_tu_may_do_HIEN_HANH_va_dung_luat_loc():
    du = json.loads((GOC / "docs" / "kho-tien-le.json").read_text(encoding="utf-8"))
    ng = du["nguon"]
    assert ng["bam_cache"].startswith("acf6dca1") and ng["do"] == "ĐO 29"
    assert ng["nguong_mua"] == pt.BUY_THRESHOLD
    lenh = du["lenh"]
    assert lenh, "kho rỗng"
    assert all(d["diem_vao"] >= pt.BUY_THRESHOLD for d in lenh)
    assert all(d["ngay_tin_hieu"] <= d["ngay_vao"] <= d["ngay_ra"] for d in lenh)
    assert lenh == sorted(lenh, key=lambda d: (d["ngay_ra"], d["ma"], d["ngay_tin_hieu"]))
    assert len(tl.doc_kho(du)) == len(lenh)


# ─────────────────────────── một định nghĩa · chỉ để hiện ───────────────────────────

def _goi(p: Path) -> set[str]:
    cay = ast.parse(p.read_text(encoding="utf-8"))
    return {(n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", ""))
            for n in ast.walk(cay) if isinstance(n, ast.Call)}


def test_MOT_DINH_NGHIA_thang_thua_va_do_cao_VNI():
    assert "ket_qua_lenh" in _goi(GOC / "tien_le.py")
    goi_dc = _goi(GOC / "tools" / "dung_kho_tien_le.py")
    assert {"vni_so_voi_ma50", "net_return_pct", "get_vni_df"} <= goi_dc


@pytest.mark.parametrize("ten", [
    "run_daily.py", "paper_trading.py", "paper_runner.py", "paper_metrics.py",
    "master_agent.py", "analysis_agents.py", "debate_agents.py", "data_collectors.py",
    "walkforward.py", "ke_hoach_vao_lenh.py", "cham_bong.py", "cham_xac_nhan.py",
    "post_mortem_learning.py", "so_bai_hoc.py"])
def test_CHI_DE_HIEN_duong_giao_dich_cham_diem_va_do_khong_nhap_tien_le(ten):
    p = GOC / ten
    if not p.exists():
        return
    nhap = set()
    for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
        if isinstance(n, ast.Import):
            nhap |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            nhap.add(n.module.split(".")[0])
    assert "tien_le" not in nhap, ten


def test_MODULE_THUAN_khong_doc_mang_dia_hay_Sheets():
    cay = ast.parse((GOC / "tien_le.py").read_text(encoding="utf-8"))
    nhap = {a.name.split(".")[0] for n in ast.walk(cay) if isinstance(n, ast.Import) for a in n.names}
    nhap |= {n.module.split(".")[0] for n in ast.walk(cay) if isinstance(n, ast.ImportFrom) and n.module}
    assert not nhap & {"requests", "sqlite3", "gspread", "google_sheets_sync", "sheets_store",
                       "vnstock", "pathlib", "os", "backtest", "market_filter"}
    assert "open" not in _goi(GOC / "tien_le.py")
    assert not math.isnan(tl.Z_95)
