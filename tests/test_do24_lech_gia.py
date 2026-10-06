"""Gác của `tools/do24_lech_gia.py` (ĐO 24) — dữ liệu TỔNG HỢP, không chạm cache hay sổ thật.

Máy phân loại bị nghi như một gác: bốn ô đối chứng của tiêu chí (M3) là bốn test ở
đây, cộng ngưỡng K1/K2, công thức M6 và việc M8 không SELECT cột điểm.
"""
from __future__ import annotations

import ast
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))
sys.path.insert(0, str(GOC))

import do24_lech_gia as D  # noqa: E402


def chuoi(n=400, gia0=20.0, hat=1):
    rng = np.random.default_rng(hat)
    c = np.round(gia0 * np.exp(np.cumsum(rng.normal(0, 0.012, n))), 2)
    ngay = pd.bdate_range("2022-01-03", periods=n).strftime("%Y-%m-%d")
    return pd.Series(c, index=ngay)


def test_KHONG_TIEM_thi_KHOP():
    b = chuoi()
    r = D.phan_loai(b.copy(), b)
    assert r["loai"] == "KHOP" and r["n_lech_that"] == 0


def test_BAC_NHAY_roi_giu_la_DANG_DIEU_CHINH():
    b = chuoi()
    a = b.copy()
    a.iloc[:200] = np.round(a.iloc[:200] * 0.97, 2)
    r = D.phan_loai(a, b)
    assert r["loai"] == "DANG DIEU CHINH" and r["n_diem_doi"] == 1
    assert r["doan"][1]["tu"] == 200
    assert abs(r["doan"][0]["khat"] - 0.97) < 1e-3


def test_HE_SO_HANG_toan_chuoi_la_DANG_DIEU_CHINH_khong_diem_doi():
    b = chuoi()
    r = D.phan_loai(np.round(b * 1.012, 2), b)
    assert r["loai"] == "DANG DIEU CHINH" and r["n_diem_doi"] == 0


def test_NHIEU_hang_ngay_KHONG_phai_dieu_chinh():
    b = chuoi()
    rng = np.random.default_rng(3)
    a = np.round(b * (1 + rng.uniform(-0.005, 0.005, len(b))), 2)
    assert D.phan_loai(a, b)["loai"] == "KHONG DANG DIEU CHINH"


def test_MOT_NEN_LAC_KHONG_phai_dieu_chinh():
    b = chuoi()
    a = b.copy()
    a.iloc[150] = np.round(a.iloc[150] * 1.05, 2)
    assert D.phan_loai(a, b)["loai"] == "KHONG DANG DIEU CHINH"


def test_NHIEU_bac_nhay_hon_ba_la_KHONG():
    b = chuoi()
    a = b.copy()
    for i, (s, e) in enumerate([(0, 60), (120, 180), (240, 300), (330, 380)]):
        a.iloc[s:e] = np.round(a.iloc[s:e] * 1.04, 2)
    r = D.phan_loai(a, b)
    assert r["n_diem_doi"] > D.TOI_DA_DIEM_DOI and r["loai"] == "KHONG DANG DIEU CHINH"


def test_DOAN_ngan_hon_nam_nen_KHONG():
    b = chuoi()
    a = b.copy()
    a.iloc[100:104] = np.round(a.iloc[100:104] * 1.05, 2)
    assert D.phan_loai(a, b)["loai"] == "KHONG DANG DIEU CHINH"


def test_LAM_TRON_mot_nac_khong_tinh_la_lech_that():
    b = chuoi()
    a = b.copy()
    a.iloc[::7] = a.iloc[::7] + 0.01
    assert D.phan_loai(a, b)["loai"] == "KHOP"


def test_TROI_DAN_tung_buoc_nho_bi_bat_boi_dung_sai_doan():
    ngay = pd.bdate_range("2022-01-03", periods=400).strftime("%Y-%m-%d")
    b = pd.Series(np.full(400, 10.0), index=ngay)
    r = D.phan_loai(pd.Series(10.0 * np.exp(np.linspace(0, 0.08, 400)), index=ngay), b)
    assert r["n_diem_doi"] == 0, "phai la troi, khong phai bac nhay"
    assert r["loai"] == "KHONG DANG DIEU CHINH"


def _gia_phang(n=60):
    ngay = pd.bdate_range("2022-01-03", periods=n).strftime("%Y-%m-%d")
    return ngay, pd.Series(np.full(n, 1.0), index=ngay)


def test_DUNG_SAI_dung_gia_NHO_NHAT_chu_khong_gia_lon_nhat_o_diem_doi():
    """B = 1,00; A nhảy từ 1,20 lên 1,20·e^0,0185. ℓ nhảy 0,0185 < 0,0202/1,00 nhưng
    > 0,0202/1,22: dùng giá lớn nhất thì sinh điểm đổi oan."""
    ngay, b = _gia_phang()
    a = pd.Series([1.2] * 30 + [1.2 * np.exp(0.0185)] * 30, index=ngay)
    r = D.phan_loai(a, b)
    assert r["n_diem_doi"] == 0 and r["loai"] == "DANG DIEU CHINH"


def test_DUNG_SAI_DOAN_dung_gia_NHO_NHAT_chu_khong_gia_lon_nhat():
    """Dốc ℓ từ ln1,2 − 0,0185 đến ln1,2 + 0,0185, mỗi bước 0,0006 (< ngưỡng bậc):
    lệch tối đa khỏi trung vị 0,0185 < 0,0202/1,00 nhưng > 0,0202/1,22."""
    ngay, b = _gia_phang(62)
    ramp = np.linspace(-0.0185, 0.0185, 62)
    a = pd.Series(1.2 * np.exp(ramp), index=ngay)
    r = D.phan_loai(a, b)
    assert r["n_diem_doi"] == 0 and r["loai"] == "DANG DIEU CHINH"


def test_DOAN_DUNG_nam_nen_duoc_chap_nhan_va_bon_nen_thi_khong():
    b = chuoi()
    a5 = b.copy()
    a5.iloc[100:105] = np.round(a5.iloc[100:105] * 1.05, 2)
    r5 = D.phan_loai(a5, b)
    assert r5["loai"] == "DANG DIEU CHINH" and [d["dai"] for d in r5["doan"]] == [100, 5, 295]
    assert D.p_doan_tot({"X": (a5, b)}, {"X": r5}) == 1.0
    a4 = b.copy()
    a4.iloc[100:104] = np.round(a4.iloc[100:104] * 1.05, 2)
    assert D.phan_loai(a4, b)["loai"] == "KHONG DANG DIEU CHINH"


def test_MA_DOI_CHUNG_chon_theo_do_dai_lon_nhat_roi_theo_ten():
    b1, b2 = chuoi(300), chuoi(500)
    assert D.chon_ma_doi_chung({"ZZZ": (b2, b2), "AAA": (b1, b1)}) == "ZZZ"
    assert D.chon_ma_doi_chung({"ZZZ": (b2, b2), "BBB": (b2, b2)}) == "BBB"


def test_DOI_CHUNG_bon_o_dat_tren_chuoi_tong_hop():
    for hat in range(1, 6):
        r = D.doi_chung(chuoi(hat=hat))
        assert r["dat_ca_bon"], r


def test_DOI_CHUNG_o_2_bat_duoc_diem_doi_sai_cho():
    b = chuoi()
    a = b.copy()
    a.iloc[:50] = np.round(a.iloc[:50] * 0.97, 2)
    r = D.phan_loai(a, b)
    assert r["doan"][1]["tu"] != len(b) // 2


@pytest.mark.parametrize("p,m0,m3,kq", [
    (0.95, True, True, "K1"), (0.90, True, True, "K1"), (0.8999, True, True, "K3"),
    (0.50, True, True, "K2"), (0.5001, True, True, "K3"),
    (0.99, False, True, "K0"), (0.99, True, False, "K0")])
def test_KET_CUC_Q1_theo_nguong_da_ky(p, m0, m3, kq):
    assert D.ket_cuc_q1(p, m0, m3) == kq


def test_NEN_LAC_o_rim_keo_ca_ma_xuong_KHONG_nhung_p_doan_tot_giu_phan_dai():
    """Mã 400 nến hệ số hằng 1,2 nhưng nến cuối lạc: M2 xếp KHÔNG (đúng chữ ký),
    chẩn đoán p_doan_tot vẫn tính 399/400 nến vào đoạn hệ-số-hằng."""
    b = chuoi()
    a = np.round(b * 1.2, 2)
    a.iloc[-1] = np.round(a.iloc[-1] * 1.03, 2)
    v = D.phan_loai(a, b)
    assert v["loai"] == "KHONG DANG DIEU CHINH"
    assert D.ly_do_khong(v) == ["doan_ngan"]
    assert D.m2({"X": (a, b)})["P_adj"] == 0.0
    assert D.p_doan_tot({"X": (a, b)}, {"X": v}) == pytest.approx(399 / 400)


def test_P_ADJ_DO_NHAY_noi_tran_diem_doi_dua_mot_ma_nhieu_buoc_vao():
    b = chuoi()
    a = b.copy()
    for s, e in [(0, 80), (80, 160), (160, 240), (240, 320), (320, 400)]:
        a.iloc[s:e] = np.round(a.iloc[s:e] * (1 + 0.01 * (s // 80)), 2)
    v = D.phan_loai(a, b)
    assert v["n_diem_doi"] == 4 and D.ly_do_khong(v) == ["qua_nhieu_diem_doi"]
    pl = {"X": v}
    assert D.p_adj_do_nhay(pl, 3, 5) == 0.0
    assert D.p_adj_do_nhay(pl, 4, 5) == 1.0


def test_LY_DO_KHONG_rong_voi_ma_dat_hoac_khop():
    b = chuoi()
    assert D.ly_do_khong(D.phan_loai(b.copy(), b)) == []
    assert D.ly_do_khong(D.phan_loai(np.round(b * 1.02, 2), b)) == []


def test_M6_cong_thuc_e_dung_hai_dau_cua_cua_so():
    n = D.NHIP + 6
    ngay = pd.bdate_range("2022-01-03", periods=n).strftime("%Y-%m-%d")
    b = pd.Series(np.full(n, 10.0), index=ngay)
    a = b.copy()
    a.iloc[: D.NHIP + 1] = 10.0 * 1.05
    r = D.m6({"X": (a, b)})
    assert r["n_cua_so"] == n - D.NHIP - 1
    e = abs(np.log(1.05)) * 100
    assert r["e_max"] == pytest.approx(e)
    assert r["ty_le_e_gt_0.5"] > 0


def test_M6_buoc_o_CUOI_cua_so_cung_duoc_bat_bang_gia_tri_tuyet_doi():
    n = D.NHIP + 6
    ngay = pd.bdate_range("2022-01-03", periods=n).strftime("%Y-%m-%d")
    b = pd.Series(np.full(n, 10.0), index=ngay)
    a = b.copy()
    a.iloc[D.NHIP + 1:] = 10.0 * 1.05
    r = D.m6({"X": (a, b)})
    assert r["e_max"] == pytest.approx(abs(np.log(1.05)) * 100)
    assert r["ty_le_e_gt_0.5"] > 0 and r["n_ma_cham_0_5"] == 1


def test_M0a_dem_dung_va_chi_tai_lap_khi_du_ba_so():
    b = chuoi(100)
    a = b.copy()
    a.iloc[:10] = a.iloc[:10] + 0.5
    r = D.m0a({"X": (a, b), "Y": (b.copy(), b)})
    assert (r["n_nen_chung"], r["n_nen_khac"], r["n_ma_co_nen_khac"]) == (200, 10, 1)
    assert r["tai_lap_ODO23"] is False


def test_M9_vung_OOS_cat_theo_moc_cua_ma_va_bien_la_nghiem_ngat():
    b = chuoi(100)
    a = b.copy()
    moc = b.index[30]
    a.iloc[:30] = a.iloc[:30] + 0.5
    r = D.m9({"X": (a, b)}, {}, {"X": moc})
    o = r["dung_lai_DO5b"]
    assert o["nen_oos"] == 30 and o["lech_that_oos"] == 30
    assert o["ty_le_lech_that_ngoai_oos"] == 0.0


def test_M6_khong_buoc_khong_loi():
    b = chuoi()
    r = D.m6({"X": (b.copy(), b)})
    assert r["e_max"] == pytest.approx(0.0, abs=1e-9) and not r["ghep_khong_chap_nhan"]


def test_M8_chi_COUNT_va_mo_chi_doc(tmp_path):
    db = tmp_path / "t.db"
    con = sqlite3.connect(db)
    con.execute("create table decisions(seq integer, symbol text, signal_date text, score int)")
    con.executemany("insert into decisions values(?,?,?,?)",
                    [(1, "A", "2026-08-07", 50), (2, "A", "2026-08-07", 51),
                     (3, "B", "2026-08-07", 52), (4, "A", "2026-08-10", 53)])
    con.commit()
    con.close()
    r = D.m8(db)
    assert r["truoc_moc"] == {"dong": 3, "mot_lan_ma_phien": 2}
    assert r["tu_moc"] == {"dong": 1, "mot_lan_ma_phien": 1}
    ham = ast.get_source_segment(Path(D.__file__).read_text(encoding="utf-8"),
                                 next(n for n in ast.parse(Path(D.__file__).read_text(encoding="utf-8")).body
                                      if isinstance(n, ast.FunctionDef) and n.name == "m8"))
    assert "score" not in ham and "components" not in ham


def test_KHONG_import_vnstock_va_KHONG_goi_mang():
    cay = ast.parse(Path(D.__file__).read_text(encoding="utf-8"))
    ten = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            ten |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            ten.add(n.module.split(".")[0])
    assert not ten & {"vnstock", "vnai", "vnstock_data", "requests", "urllib", "httpx", "socket"}


def test_NAP_cat_nen_tu_moc(tmp_path):
    ngay = ["2026-08-07", "2026-08-10", "2026-08-11"]
    pd.DataFrame({"time": ngay, "close": [1.0, 2.0, 3.0]}).to_csv(tmp_path / "X.csv", index=False)
    s = D.doc_close(tmp_path / "X.csv")
    assert list(s.index) == ["2026-08-07"]
