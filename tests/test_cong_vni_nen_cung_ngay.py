"""Cổng VN-INDEX của đường THẬT phải đọc nến của CHÍNH ngày tín hiệu — BƯỚC 241, lỗi 195.

SỰ CỐ (BƯỚC 240 phát hiện, BƯỚC 241 đo): `market_filter.is_vni_bullish` lọc
`vni_df["time"] <= signal_date` bằng so CHUỖI. `get_vni_df()` ưu tiên cache CSV
(`time` = `2026-09-30`) nhưng trên GitHub Actions không có cache nên nó tải mạng, và cột
`time` của nguồn mạng là `2026-09-30 07:00:00`. `"2026-09-30 07:00:00" <= "2026-09-30"` là
False, nên nến của chính ngày tín hiệu bị loại: cổng chạy thật đọc VN-INDEX TRỄ MỘT PHIÊN,
còn backtest (cache) đọc nến cùng ngày. Lệnh #126 · #127 (tín hiệu 30/09) và #128–#133 (tín hiệu
26/10) qua cổng chỉ nhờ độ trễ ấy; ngày 23/10 thì cổng chặn oan 5 tín hiệu điểm ≥ 62.

KHÔNG NHÌN TRỘM TƯƠNG LAI: `signal_date` của đường thật là ngày của một nến ĐÃ ĐÓNG
(`run_daily.execute_daily_scan` bỏ nến cuối khi `data_quality.nen_cuoi_dang_do`). Nến VN-INDEX của
đúng ngày ấy cũng đã đóng (cùng phiên HOSE, cùng giờ chốt `GIO_NEN_DA_DONG`); nến của ngày SAU vẫn
bị loại vì so ngày 10 ký tự là `<=`.
"""
import ast
import importlib.util as _ilu
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

# BẢN SAO RIÊNG của market_filter (xem lý do ở đầu tests/test_market_filter.py: nhiều file ghim
# `is_vni_bullish` thành hàm giả ở mức module và lời ghim sống suốt tiến trình).
_spec = _ilu.spec_from_file_location("market_filter_ban_sao_241", GOC / "market_filter.py")
mf = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(mf)

_spec2 = _ilu.spec_from_file_location("nhat_ky_vi_sao_ban_sao_241", GOC / "nhat_ky_vi_sao.py")
nk = _ilu.module_from_spec(_spec2)
_spec2.loader.exec_module(nk)

HAU_TO = ["", " 07:00:00", " 00:00:00"]
IDS = ["ngay_tron", "kem_07h", "kem_00h"]


def _khung(hau_to: str, nen_cuoi_tren_ma: bool) -> pd.DataFrame:
    """60 phiên; nến CUỐI nằm trên (hoặc dưới) MA50 còn nến liền trước nằm phía NGƯỢC LẠI — nên đáp án
    của nến cùng ngày và của nến hôm trước KHÁC nhau."""
    ngay = pd.bdate_range(end="2026-10-26", periods=60).strftime("%Y-%m-%d")
    close = np.full(60, 1000.0)
    if nen_cuoi_tren_ma:
        close[-2], close[-1] = 900.0, 1100.0      # hôm trước dưới MA50, hôm nay trên
    else:
        close[-2], close[-1] = 1100.0, 900.0      # hôm trước trên MA50, hôm nay dưới
    d = pd.DataFrame({"time": [x + hau_to for x in ngay], "close": close})
    d["vni_ma50"] = d["close"].rolling(mf.MA_WINDOW).mean()
    return d


@pytest.mark.parametrize("hau_signal", ["", " 00:00:00", " 07:00:00"], ids=["signal_10", "signal_00h", "signal_07h"])
@pytest.mark.parametrize("hau_to", HAU_TO, ids=IDS)
@pytest.mark.parametrize("tren", [True, False], ids=["cuoi_tren_MA50", "cuoi_duoi_MA50"])
def test_is_vni_bullish_doc_nen_CUNG_NGAY_ca_ba_dang_cot_time(hau_to, tren, hau_signal, monkeypatch):
    """Đáp án = nến của chính `signal_date`. Dạng kèm giờ (nguồn mạng, Actions) KHÔNG được lùi một phiên,
    và `signal_date` mang giờ khác giờ của cột `time` (`00:00:00` so `07:00:00`) cũng không đổi đáp án."""
    khung = _khung(hau_to, tren)
    monkeypatch.setattr(mf, "get_vni_df", lambda: khung)
    assert mf.is_vni_bullish("2026-10-26" + hau_signal) is tren
    # và nến hôm trước (phía ngược lại) đúng là đáp án của ngày hôm trước
    assert mf.is_vni_bullish("2026-10-23" + hau_signal) is (not tren)


def test_is_vni_bullish_ba_dang_cot_time_cho_CUNG_dap_an_tren_moi_ngay(monkeypatch):
    """Backtest (cache, `time` 10 ký tự) và đường thật (mạng, kèm giờ) phải ra cùng phán quyết MỌI ngày."""
    kq = {}
    for hau_to in HAU_TO:
        khung = _khung(hau_to, True)
        monkeypatch.setattr(mf, "get_vni_df", lambda k=khung: k)
        kq[hau_to] = [mf.is_vni_bullish(str(d)[:10]) for d in khung["time"].iloc[50:]]
    assert kq[""] == kq[" 07:00:00"] == kq[" 00:00:00"]
    assert True in kq[""] and False in kq[""], "khung không cắt MA50: phép so trống rỗng"


@pytest.mark.parametrize("hau_to", HAU_TO, ids=IDS)
def test_KHONG_nhin_trom_nen_cua_ngay_SAU(hau_to, monkeypatch):
    """Sửa sang so 10 ký tự không được kéo nến ngày sau vào: ngày tín hiệu 23/10 vẫn chỉ thấy nến ≤ 23/10."""
    khung = _khung(hau_to, True)
    monkeypatch.setattr(mf, "get_vni_df", lambda: khung)
    # nến 26/10 (trên MA50) tồn tại trong khung nhưng ngày tín hiệu 23/10 không được nhìn thấy nó
    assert mf.is_vni_bullish("2026-10-23") is False


@pytest.mark.parametrize("hau_to", HAU_TO, ids=IDS)
def test_boi_canh_nhat_ky_dung_CUNG_nen_voi_cong(hau_to):
    """`vni_so_voi_ma50` (bối cảnh ghi vào nhật ký lúc tín hiệu) phải đọc đúng nến mà cổng đã nhìn."""
    khung = _khung(hau_to, True)
    bc = nk.vni_so_voi_ma50(khung, "2026-10-26")
    assert bc["vni_close"] == 1100.0, "bối cảnh đọc nến hôm trước: lệch nến với cổng"
    assert nk.vni_so_voi_ma50(khung, "2026-10-26 00:00:00")["vni_close"] == 1100.0
    assert nk.vni_so_voi_ma50(khung, "2026-10-23")["vni_close"] == 900.0


def _so_sanh_thoi_gian_tran(ten_file: str, ten_ham: str) -> list:
    """Mọi phép so `<column>["time"] <=/< ...` trong hàm — dạng `X["time"] <= Y` TRẦN (không `.astype`/
    cắt 10 ký tự ở vế trái) là đúng hình dạng của lỗi 195."""
    cay = ast.parse((GOC / ten_file).read_text(encoding="utf-8"))
    ham = next(n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == ten_ham)
    tran = []
    for n in ast.walk(ham):
        if isinstance(n, ast.Compare) and isinstance(n.ops[0], (ast.LtE, ast.Lt, ast.GtE, ast.Gt)):
            trai = n.left
            if (isinstance(trai, ast.Subscript) and isinstance(trai.slice, ast.Constant)
                    and trai.slice.value == "time"):
                tran.append(ast.unparse(n))
    return tran


@pytest.mark.parametrize("file,ham", [("market_filter.py", "is_vni_bullish"),
                                      ("nhat_ky_vi_sao.py", "vni_so_voi_ma50")])
def test_AST_khong_con_phep_so_time_TRAN_trong_cong_va_boi_canh(file, ham):
    assert _so_sanh_thoi_gian_tran(file, ham) == [], (
        f"{file}::{ham} còn so cột time TRẦN với ngày tín hiệu — hình dạng lỗi 195")


def test_AST_gac_tu_kiem_mau_xau_va_mau_tot():
    xau = "def f(d, s):\n    return d[d['time'] <= s]\n"
    tot = "def f(d, s):\n    return d[d['time'].astype(str).str[:10] <= str(s)[:10]]\n"
    for nguon, mong in ((xau, 1), (tot, 0)):
        cay = ast.parse(nguon)
        ham = cay.body[0]
        dem = sum(1 for n in ast.walk(ham) if isinstance(n, ast.Compare)
                  and isinstance(n.left, ast.Subscript) and isinstance(n.left.slice, ast.Constant)
                  and n.left.slice.value == "time")
        assert dem == mong
