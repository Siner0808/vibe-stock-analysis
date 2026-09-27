"""Gác của `nhat_ky_vi_sao.boi_canh_luc_tin_hieu` — P2b-1 (BƯỚC 132).

Người dùng chọn bối cảnh GIÀU (có chỉ số thị trường). Đòi hỏi cứng đi kèm là
bất biến 1: mọi con số phải là của phiên TÍN HIỆU. Phép kiểm đứng đầu: thêm
dữ liệu TƯƠNG LAI vào VN-INDEX thì bối cảnh KHÔNG được đổi.
"""
import ast
import math
from pathlib import Path

import pandas as pd
import pytest

import nhat_ky_vi_sao as nk

GOC = Path(__file__).resolve().parent.parent

KET_QUA = {
    "final_score": 66, "recommendation": "MUA", "data_quality": "OK",
    "analyses": {
        "risk": {"metrics": {"volatility_annual": 31.2, "max_drawdown": -18.4,
                             "sharpe_ratio": 0.9, "atr_pct": 2.4}},
        "volume": {"stats": {"last_volume": 1_200_000, "avg_vol_20": 800_000,
                             "vol_ratio_vs_ma20": 1.5}},
    },
}


def _vni(them_tuong_lai: bool = False) -> pd.DataFrame:
    df = pd.DataFrame({
        "time": ["2026-09-22", "2026-09-23", "2026-09-24", "2026-09-25"],
        "close": [1700.0, 1710.0, 1720.0, 1740.0],
        "vni_ma50": [1690.0, 1692.0, 1695.0, 1700.0],
    })
    if them_tuong_lai:
        df = pd.concat([df, pd.DataFrame({
            "time": ["2026-09-26", "2026-09-29"],
            "close": [900.0, 5000.0], "vni_ma50": [1.0, 99999.0]})],
            ignore_index=True)
    return df


def test_KHONG_NHIN_TROM_du_lieu_tuong_lai_khong_doi_boi_canh():
    a = nk.boi_canh_luc_tin_hieu(KET_QUA, "2026-09-25", _vni(), 62)
    b = nk.boi_canh_luc_tin_hieu(KET_QUA, "2026-09-25", _vni(them_tuong_lai=True), 62)
    assert a == b
    assert a["vni_close"] == 1740.0 and a["vni_ma50"] == 1700.0
    assert a["vni_pct_tren_ma50"] == pytest.approx(40 / 1700 * 100)


def test_PHIEN_TIN_HIEU_la_phien_cuoi_TOI_HET_ngay_ay():
    bc = nk.vni_so_voi_ma50(_vni(them_tuong_lai=True), "2026-09-24")
    assert bc["vni_close"] == 1720.0


def test_CAT_DU_LIEU_dung_BIEU_THUC_cua_is_vni_bullish():
    """AST: `vni_df[vni_df["time"] <= signal_date]` trong CẢ HAI hàm."""
    def bieu_thuc(file, ham):
        cay = ast.parse((GOC / file).read_text(encoding="utf-8"))
        f = next(n for n in ast.walk(cay)
                 if isinstance(n, ast.FunctionDef) and n.name == ham)
        return {ast.dump(n) for n in ast.walk(f)
                if isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Compare)}
    goc = bieu_thuc("market_filter.py", "is_vni_bullish")
    moi = bieu_thuc("nhat_ky_vi_sao.py", "vni_so_voi_ma50")
    assert goc and goc == moi, (goc, moi)


def test_DU_CAC_O_va_DUNG_THU_TU_khoa():
    bc = nk.boi_canh_luc_tin_hieu(KET_QUA, "2026-09-25", _vni(), 62)
    assert tuple(bc) == nk.KHOA_BOI_CANH
    assert bc["bien_dong_nam_pct"] == 31.2 and bc["atr_pct"] == 2.4
    assert bc["kl_so_tb20"] == 1.5 and bc["nguong_mua"] == 62
    assert bc["diem_cuoi"] == 66 and bc["chat_luong_du_lieu"] == "OK"


@pytest.mark.parametrize("ket_qua", [{}, {"analyses": {}}, None,
                                     {"analyses": {"risk": {}, "volume": {"stats": {}}}}])
def test_THIEU_du_lieu_thi_None_KHONG_so_mac_dinh(ket_qua):
    bc = nk.boi_canh_luc_tin_hieu(ket_qua, "2026-09-25", None, 62)
    for k in nk.KHOA_BOI_CANH:
        if k != "nguong_mua":
            assert bc[k] is None, k


def test_VNI_rong_truoc_ngay_hoac_MA50_NaN_thi_None():
    assert nk.vni_so_voi_ma50(_vni(), "2026-01-01")["vni_close"] is None
    df = _vni()
    df.loc[3, "vni_ma50"] = math.nan
    bc = nk.vni_so_voi_ma50(df, "2026-09-25")
    assert bc["vni_close"] == 1740.0
    assert bc["vni_ma50"] is None and bc["vni_pct_tren_ma50"] is None
