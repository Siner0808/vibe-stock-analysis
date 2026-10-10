"""Test kế hoạch vào lệnh — `ke_hoach_vao_lenh` (BƯỚC 173, mốc B6, CHỈ ĐỂ HIỆN).

VÌ SAO FILE NÀY TỒN TẠI
───────────────────────
Module phán quyết ĐIỂM VÀO nhưng CHƯA ĐO và KHÔNG vào sổ. Một phán quyết sai
ngầm trông y như đúng, nên các gác ở đây là:

  · SỐ TÍNH TAY — mỗi phán quyết một ca, `df` giả dựng tay, đáp số viết bằng
    SỐ cùng phép tính trong chú thích. Không dựng lại công thức trong test
    (luật "test kiểm lại chính nó": test dựng lại công thức của mã chỉ kiểm
    công thức của test).
  · TÍNH CHẤT — ATR khớp `_compute_local_indicators`, nến dở không đổi kế
    hoạch, hàm không nhớ gì giữa hai lần gọi, đơn vị đi vào bằng đơn vị đi ra.
  · AST — ai được nhập, app gọi đúng, hình dạng biểu thức vùng, không có bảng
    bước giá gõ lại.

LẦN SỬA 10/10/2026 (phản hồi người dùng, ca MSR): luật cũ "cắt lỗ = đáy thấp
nhất 20 phiên" đẩy vùng chờ ra xa giá tới −29,4% (xem docstring module). Các ca
mới là hệ quả: ĐÁY XOAY GẦN NHẤT (không phải đáy nền cũ), vùng phải CHẠM ĐƯỢC,
mọi giá đi qua bước giá của sàn. Bản đầu có 53 test, đột biến 7/7 và năm cổng
xanh — chúng kiểm mã khớp đề bài, không kiểm đề bài khớp thị trường (lỗi 147).

Mọi test offline, dữ liệu giả. Không cần vnstock.

Dựng ca: `_nen(c0, cao, thap, cuoi, lows)` = 29 nến giống nhau (mở = đóng = c0,
cao, thấp) rồi MỘT nến cuối tuỳ ý (mở, cao, thấp, đóng); `lows` ghi đè đáy của
vài nến để dựng đáy xoay. Giá trong `df` là NGHÌN ĐỒNG (như vnstock), `he_so_gia`
= 1000 → VNĐ. Sàn mặc định của ca là UPCOM (bước giá 100đ ở mọi mức) để số tay
gọn; ca HOSE ở dải 10/50/100 có test riêng.
"""
from __future__ import annotations

import ast
import math
import pathlib
import sys
from datetime import datetime

import numpy as np
import pandas as pd
import pytest

GOC = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(GOC / "tools"))

import duyet_repo  # noqa: E402
import khung_thoi_gian  # noqa: E402
import ke_hoach_vao_lenh as kh  # noqa: E402
import muc_fibonacci  # noqa: E402
import pha_wyckoff  # noqa: E402

XA = datetime(2027, 6, 1, 20, 0)      # sau mọi dữ liệu giả: nến nào cũng đã đóng
DIEM, NGUONG = 70.0, 62.0
HE = 1000.0
GAN_DUNG = pytest.approx


# ─────────────────────────────────────────────────────────────────────
# Dựng dữ liệu giả
# ─────────────────────────────────────────────────────────────────────

def _nen(c0, cao, thap, cuoi, lows=None, n=30, bat_dau="2026-03-02"):
    """n−1 nến nền (mở = đóng = c0) + nến cuối (mở, cao, thấp, đóng).

    `lows` = {chỉ số nến: đáy mới} ghi đè đáy của nến nền (dựng đáy xoay).
    """
    ngay = pd.date_range(bat_dau, periods=n, freq="B").strftime("%Y-%m-%d")
    dong = [[c0, cao, thap, c0, 1000.0] for _ in range(n - 1)]
    dong.append(list(cuoi) + [1000.0])
    for i, d in (lows or {}).items():
        dong[i][2] = d
    return pd.DataFrame(dong, columns=["open", "high", "low", "close",
                                       "volume"]).assign(time=ngay)


def _lap(df, he=HE, diem=DIEM, nguong=NGUONG, bay_gio=XA, san="UPCOM"):
    return kh.lap_ke_hoach(df, he, diem, nguong, bay_gio, san)


# Các ca tay, dùng lại nhiều nơi. Mỗi ca ghi phép tính ở chú thích.
# ATR cửa sổ = 14 nến CUỐI (chỉ số 16..29); nến đáy xoay ở chỉ số 12 nằm NGOÀI
# cửa sổ ATR nhưng TRONG cửa sổ đáy (10..27), nên không làm đổi ATR.

def ca_mua_ngay():
    """Nền 100 / 101 / 97 (nghìn đ). Nến cuối 100 / 101 / 97 / 100. Đáy xoay: nến
    12 có đáy 96,55.

    true range mọi nến cửa sổ = 101 − 97 = 4        → ATR14 = 4,0 = 4.000 VNĐ
    MA20 = 100                                      → kéo giãn k = 0
    cắt lỗ = 96.550 − 0,5×4.000 = 94.550 → XUỐNG bước 100 → 94.500
    rủi ro r = (100.000 − 94.500)/100.000 = 5,5%  (trong [4%; 6,5%])
    trần ngân sách = 94.500/0,935 = 101.070 ≥ 100.000   → MUA_NGAY
    """
    return _nen(100.0, 101.0, 97.0, (100.0, 101.0, 97.0, 100.0), {12: 96.55})


def ca_mua_ngay_cat_lo_sat():
    """Nền 100 / 101 / 99,5. Nến cuối y hệt. Đáy xoay: nến 12, đáy 99,0.

    true range = 1,5 → ATR = 1.500 VNĐ ; MA20 = 100.000 ; k = 0
    cắt lỗ = 99.000 − 750 = 98.250 → XUỐNG → 98.200
    r = (100.000 − 98.200)/100.000 = 1,8% < 4%
    trần ngân sách = 98.200/0,935 = 105.026 ≥ 100.000 → MUA_NGAY, kèm lý do
    "sát hơn".
    """
    return _nen(100.0, 101.0, 99.5, (100.0, 101.0, 99.5, 100.0), {12: 99.0})


def ca_cho_vung_do_rui_ro():
    """Như ca_mua_ngay nhưng đáy xoay 96,05 và nến cuối đóng 101 (cao 101).

    ATR = 4.000 ; MA20 = (19×100 + 101)/20 = 100,05 → 100.050 ; k = 0,95/4 = 0,2375
    cắt lỗ = 96.050 − 2.000 = 94.050 → XUỐNG → 94.000
    r = (101.000 − 94.000)/101.000 = 6,931% > 6,5%
    trần ngân sách = 94.000/0,935 = 100.535 < 101.000        → trượt vì RỦI RO
    trần kéo giãn = 100.050 + 2×4.000 = 108.050
    đáy vùng = 94.000/0,96 = 97.917 → LÊN → 98.000
    trần vùng = min(100.535 ; 108.050) = 100.535 → XUỐNG → 100.500
    vùng = [98.000 ; 100.500] ; cách giá đóng 101.000 − 100.500 = 500 = 0,125 ATR
    (0,5%) — chạm được.
    """
    return _nen(100.0, 101.0, 97.0, (100.0, 101.0, 97.0, 101.0), {12: 96.05})


def ca_cho_vung_do_keo_gian():
    """Nền 100 / 102 / 100. Nến cuối 100 / 105 / 100 / 105. Đáy xoay: nến 12, 99,5.

    true range nền = 2 ; nến cuối = max(5 ; |105−100| ; 0) = 5
    ATR = (13×2 + 5)/14 = 31/14 = 2,2143 nghìn = 2.214,29 VNĐ
    MA20 = (19×100 + 105)/20 = 100,25 → 100.250 ; k = 4,75/2,2143 = 2,1452 > 2
    cắt lỗ = 99.500 − 1.107,14 = 98.392,86 → XUỐNG → 98.300
    r = (105.000 − 98.300)/105.000 = 6,381% (không vượt 6,5%)
    trần ngân sách = 98.300/0,935 = 105.134 ≥ 105.000 → KHÔNG trượt vì rủi ro
    trần kéo giãn = 100.250 + 2×2.214,29 = 104.678,57
    đáy vùng = 98.300/0,96 = 102.395,83 → LÊN → 102.400
    trần vùng = min(105.134 ; 104.678,57) → XUỐNG → 104.600
    vùng = [102.400 ; 104.600] ; cách giá đóng 400 = 0,18 ATR (0,4%).
    """
    return _nen(100.0, 102.0, 100.0, (100.0, 105.0, 100.0, 105.0), {12: 99.5})


def ca_cho_vung_do_ca_hai():
    """Nền 100 / 101 / 99. Nến cuối 100 / 106 / 100 / 106. Đáy xoay: nến 12, 98,5.

    true range nền = 2 ; nến cuối = max(6 ; 6 ; 0) = 6
    ATR = (13×2 + 6)/14 = 32/14 = 2.285,71 VNĐ ; MA20 = (1900 + 106)/20 = 100.300
    k = 5,7/2,2857 = 2,4938 > 2
    cắt lỗ = 98.500 − 1.142,86 = 97.357,14 → XUỐNG → 97.300
    r = (106.000 − 97.300)/106.000 = 8,208% > 6,5%
    trần ngân sách = 97.300/0,935 = 104.064,17 ; trần kéo giãn = 100.300 + 4.571,43
    = 104.871,43 ; đáy vùng = 97.300/0,96 = 101.354,17 → LÊN → 101.400
    trần vùng = min(104.064,17 ; 104.871,43) → XUỐNG → 104.000
    vùng = [101.400 ; 104.000] ; cách giá đóng 2.000 = 0,875 ATR (1,9%).
    """
    return _nen(100.0, 101.0, 99.0, (100.0, 106.0, 100.0, 106.0), {12: 98.5})


def ca_bo_qua_khong_co_vung():
    """Nền 100 / 100,5 / 99,5. Nến cuối 100 / 104 / 100 / 104. Đáy xoay: nến 12, 99,4.

    true range nền = 1 ; nến cuối = max(4 ; 4 ; 0) = 4
    ATR = (13×1 + 4)/14 = 17/14 = 1.214,29 VNĐ ; MA20 = (1900 + 104)/20 = 100.200
    k = 3,8/1,2143 = 3,1294 > 2
    cắt lỗ = 99.400 − 607,14 = 98.792,86 → XUỐNG → 98.700 ; r = 5,096% (không
    trượt rủi ro : trần ngân sách = 98.700/0,935 = 105.561 ≥ 104.000)
    trần kéo giãn = 100.200 + 2×1.214,29 = 102.628,57 → XUỐNG → 102.600
    đáy vùng = 98.700/0,96 = 102.812,5 → LÊN → 102.900 > 102.600 → trần < đáy.
    """
    return _nen(100.0, 100.5, 99.5, (100.0, 104.0, 100.0, 104.0), {12: 99.4})


def ca_msr(dap):
    """Dựng kiểu MSR 10/10/2026: nền → bứt phá → nhịp chỉnh tạo đáy xoay → đi ngang.

    Nến 0..11 : nền 50 (mở = đóng 50, cao 50,5, thấp 49,5)
    Nến 12    : bứt phá 50 / 60 / 50 / 60
    Nến 13..29: 60 (cao 60,5, thấp 59,5) NGOẠI TRỪ nến 17 có đáy `dap`
    Đáy xoay: nến 11 (đáy 49,5 — nền CŨ trước bứt phá, vẫn còn trong 20 phiên)
    và nến 17 (đáy `dap`). Luật mới phải chọn nến 17 (GẦN NHẤT).
    MA20 = (2×50 + 18×60)/20 = 59 → 59.000.
    """
    dong = []
    for i in range(30):
        if i <= 11:
            dong.append([50.0, 50.5, 49.5, 50.0])
        elif i == 12:
            dong.append([50.0, 60.0, 50.0, 60.0])
        elif i == 17:
            dong.append([60.0, 60.5, dap, 60.0])
        else:
            dong.append([60.0, 60.5, 59.5, 60.0])
    ngay = pd.date_range("2026-03-02", periods=30, freq="B").strftime("%Y-%m-%d")
    return pd.DataFrame(dong, columns=["open", "high", "low", "close"]).assign(
        volume=1000.0, time=ngay)


# ─────────────────────────────────────────────────────────────────────
# KHONG_XET · ngưỡng
# ─────────────────────────────────────────────────────────────────────

def test_KHONG_XET_duoi_nguong_khong_tinh_gi_them():
    p = _lap(ca_mua_ngay(), diem=61.9)
    assert p.phan_quyet == kh.KHONG_XET
    assert p.ly_do == ("điểm 61.9 dưới ngưỡng 62 — chưa phải ứng viên",)
    for ten in ("ngay", "gia_dong", "atr", "ma20", "keo_gian_atr",
                "day_xoay_ngay", "day_xoay_gia", "cat_lo_cau_truc",
                "rui_ro_pct", "vung", "so_phien_cho"):
        assert getattr(p, ten) is None, ten


def test_diem_BANG_nguong_thi_duoc_xet():
    """Biên: 62 vào 62 là ứng viên (như `consider_entry`: chỉ bỏ khi < ngưỡng)."""
    assert _lap(ca_mua_ngay(), diem=62.0).phan_quyet == kh.MUA_NGAY
    assert _lap(ca_mua_ngay(), diem=61.99).phan_quyet == kh.KHONG_XET


def test_nguong_va_san_la_tham_so_bat_buoc_khong_co_mac_dinh():
    cay = ast.parse((GOC / "ke_hoach_vao_lenh.py").read_text(encoding="utf-8"))
    ham = next(n for n in cay.body if isinstance(n, ast.FunctionDef)
               and n.name == "lap_ke_hoach")
    assert ham.args.defaults == [] and ham.args.kw_defaults == []
    assert [a.arg for a in ham.args.args] == [
        "df", "he_so_gia", "diem", "nguong", "bay_gio", "san"]


def test_phep_so_nguong_la_diem_nho_hon_nguong__kiem_hinh_dang_bang_AST():
    cay = ast.parse((GOC / "ke_hoach_vao_lenh.py").read_text(encoding="utf-8"))
    ham = next(n for n in cay.body if isinstance(n, ast.FunctionDef)
               and n.name == "lap_ke_hoach")
    so = [n for n in ast.walk(ham) if isinstance(n, ast.Compare)
          and isinstance(n.left, ast.Name) and n.left.id == "diem"
          and isinstance(n.comparators[0], ast.Name)
          and n.comparators[0].id == "nguong"]
    assert len(so) == 1 and isinstance(so[0].ops[0], ast.Lt)


# ─────────────────────────────────────────────────────────────────────
# CHUA_LAP_DUOC · thiếu dữ liệu thì không đoán
# ─────────────────────────────────────────────────────────────────────

def test_CHUA_LAP_DUOC_thieu_nen_va_bien_dung_du():
    n_can = kh.SO_NEN_TOI_THIEU
    mot_nen = (100.0, 101.0, 97.0, 100.0)
    thieu = _lap(_nen(100.0, 101.0, 97.0, mot_nen, {12: 96.55}, n=n_can - 1))
    assert thieu.phan_quyet == kh.CHUA_LAP_DUOC
    assert f"chỉ có {n_can - 1} nến" in thieu.ly_do[0]
    du = _lap(_nen(100.0, 101.0, 97.0, mot_nen, {12: 96.55}, n=n_can))
    assert du.phan_quyet == kh.MUA_NGAY


def test_CHUA_LAP_DUOC_ATR_bang_0():
    phang = _nen(100.0, 100.0, 100.0, (100.0, 100.0, 100.0, 100.0))
    p = _lap(phang)
    assert p.phan_quyet == kh.CHUA_LAP_DUOC and "ATR" in p.ly_do[0]


def test_CHUA_LAP_DUOC_cat_lo_khong_duong():
    """Nền 5 / 9 / 3 (ATR = 6 nghìn), đáy xoay 1 → 1.000 − 3.000 = −2.000 ≤ 0."""
    p = _lap(_nen(5.0, 9.0, 3.0, (5.0, 9.0, 3.0, 5.0), {12: 1.0}))
    assert p.phan_quyet == kh.CHUA_LAP_DUOC
    assert p.ly_do == ("cắt lỗ cấu trúc không dương",)


@pytest.mark.parametrize("df", [None, pd.DataFrame(),
                                pd.DataFrame({"close": [1.0] * 40})])
def test_CHUA_LAP_DUOC_df_hong(df):
    assert _lap(df).phan_quyet == kh.CHUA_LAP_DUOC


def test_CHUA_LAP_DUOC_diem_khong_doc_duoc():
    assert _lap(ca_mua_ngay(), diem=float("nan")).phan_quyet == kh.CHUA_LAP_DUOC
    assert _lap(ca_mua_ngay(), diem=None).phan_quyet == kh.CHUA_LAP_DUOC


def test_CHUA_LAP_DUOC_khong_co_day_xoay():
    """Đáy phẳng: không nến nào thấp HƠN HẲN hai nến sau nó → không đáy xoay."""
    p = _lap(_nen(100.0, 101.0, 99.5, (100.0, 101.0, 99.5, 100.0)))
    assert p.phan_quyet == kh.CHUA_LAP_DUOC
    assert p.ly_do == (f"không có đáy xoay nào trong {kh.CUA_SO_DAY} phiên gần "
                       f"nhất",)
    assert p.atr == GAN_DUNG(1500.0)            # phần đã tính được vẫn hiện


# ─────────────────────────────────────────────────────────────────────
# Sàn: bước giá thật, làm tròn đúng hướng
# ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("san,gia,xuong,len_", [
    # HOSE dải < 10.000: bước 10đ
    ("HOSE", 9995.0, 9990.0, 10000.0),
    ("HOSE", 9999.0, 9990.0, 10000.0),
    ("HOSE", 9990.0, 9990.0, 9990.0),
    # sát biên dải 10.000: từ đây bước 50đ
    ("HOSE", 10000.0, 10000.0, 10000.0),
    ("HOSE", 10010.0, 10000.0, 10050.0),
    ("HOSE", 10049.0, 10000.0, 10050.0),
    # dải 10.000–50.000: bước 50đ, sát biên 50.000
    ("HOSE", 49990.0, 49950.0, 50000.0),
    ("HOSE", 49950.0, 49950.0, 49950.0),
    # từ 50.000: bước 100đ
    ("HOSE", 50000.0, 50000.0, 50000.0),
    ("HOSE", 50030.0, 50000.0, 50100.0),
    ("HOSE", 50099.0, 50000.0, 50100.0),
    # HNX / UPCoM: 100đ ở MỌI mức (kể cả dưới 10.000)
    ("UPCOM", 5432.0, 5400.0, 5500.0),
    ("UPCOM", 12345.0, 12300.0, 12400.0),
    ("HNX", 30050.0, 30000.0, 30100.0),
    ("upcom", 12345.0, 12300.0, 12400.0),
])
def test_lam_tron_theo_buoc_gia_cua_san(san, gia, xuong, len_):
    assert kh.lam_tron_xuong(gia, san) == xuong
    assert kh.lam_tron_len(gia, san) == len_


def test_lam_tron_khong_nhay_buoc_vi_nhieu_dau_phay_dong():
    """16,1 × 1000 = 16100,000000000002 ; nếu chia thẳng thì ceil nhảy sang 16.200.
    32,3 × 1000 = 32299,999999999996 ; nếu chia thẳng thì floor tụt xuống 32.200.
    (Hai giá này ĐÃ nằm trên lưới 100đ; nhiễu chỉ do phép nhân.) Phép kiểm đầu
    mỗi khối đòi nhiễu CÓ THẬT, nếu không phép so bên dưới xanh vì lý do khác.
    """
    assert 16.1 * 1000 != 16100.0 and 32.3 * 1000 != 32300.0
    assert kh.lam_tron_len(16.1 * 1000, "UPCOM") == 16100.0
    assert kh.lam_tron_xuong(16.1 * 1000, "UPCOM") == 16100.0
    assert kh.lam_tron_xuong(32.3 * 1000, "UPCOM") == 32300.0
    assert kh.lam_tron_len(32.3 * 1000, "UPCOM") == 32300.0
    # Cùng bệnh ở bước 10đ của HOSE dưới 10.000đ.
    assert 2.01 * 1000 != 2010.0 and 4.03 * 1000 != 4030.0
    assert kh.lam_tron_xuong(2.01 * 1000, "HOSE") == 2010.0
    assert kh.lam_tron_len(4.03 * 1000, "HOSE") == 4030.0


def test_san_la_thi_no_o_ham_lam_tron_va_CHUA_LAP_o_ham_lap():
    with pytest.raises(ValueError):
        kh.lam_tron_xuong(100.0, "HSX")
    assert not kh.san_hop_le("HSX") and not kh.san_hop_le(None)
    assert kh.san_hop_le("HOSE") and kh.san_hop_le("upcom")
    for san in ("HSX", "", None, 7):
        p = _lap(ca_mua_ngay(), san=san)
        assert p.phan_quyet == kh.CHUA_LAP_DUOC, san
        assert "không có trong bảng bước giá" in p.ly_do[0]
    # Sàn dưới ngưỡng: vẫn KHONG_XET (không tính gì thêm).
    assert _lap(ca_mua_ngay(), san="HSX", diem=10.0).phan_quyet == kh.KHONG_XET


def test_san_viet_thuong_cho_cung_ke_hoach():
    assert _lap(ca_cho_vung_do_rui_ro(), san="upcom") == _lap(
        ca_cho_vung_do_rui_ro(), san="UPCOM")


def test_buoc_gia_HOSE_dai_50d_khac_UPCOM_100d__ca_tich_hop():
    """Ca mua ngay thu nhỏ 0,3 lần: giá ~30.000 (dải 10–50 nghìn của HOSE).

    ATR = 0,3×4.000 = 1.200 ; đáy xoay 28,965 → 28.965 − 600 = 28.365
    HOSE (bước 50) → XUỐNG 28.350 ; UPCOM (bước 100) → XUỐNG 28.300.
    """
    df = _nen(30.0, 30.3, 29.1, (30.0, 30.3, 29.1, 30.0), {12: 28.965})
    hose, upcom = _lap(df, san="HOSE"), _lap(df, san="UPCOM")
    assert hose.cat_lo_cau_truc == 28350.0
    assert upcom.cat_lo_cau_truc == 28300.0
    assert hose.rui_ro_pct == GAN_DUNG(5.5)
    assert upcom.rui_ro_pct == GAN_DUNG(100 * 1700 / 30000)


def test_buoc_gia_HOSE_dai_10d_duoi_10_nghin__ca_tich_hop():
    """Thu nhỏ 0,05 lần: giá ~5.000 (dải < 10 nghìn của HOSE, bước 10đ).

    ATR = 200 ; đáy xoay 4,8275 → 4.827,5 − 100 = 4.727,5
    HOSE (bước 10) → XUỐNG 4.720 ; UPCOM (bước 100) → XUỐNG 4.700.
    """
    df = _nen(5.0, 5.05, 4.85, (5.0, 5.05, 4.85, 5.0), {12: 4.8275})
    assert _lap(df, san="HOSE").cat_lo_cau_truc == 4720.0
    assert _lap(df, san="UPCOM").cat_lo_cau_truc == 4700.0


# ─────────────────────────────────────────────────────────────────────
# MUA_NGAY · CHO_VUNG · BO_QUA — số tính tay
# ─────────────────────────────────────────────────────────────────────

def test_MUA_NGAY_so_tinh_tay():
    df = ca_mua_ngay()
    p = _lap(df)
    assert p.phan_quyet == kh.MUA_NGAY
    assert p.ngay == "2026-04-10"
    assert p.gia_dong == GAN_DUNG(100000.0)
    assert p.atr == GAN_DUNG(4000.0)
    assert p.ma20 == GAN_DUNG(100000.0)
    assert p.keo_gian_atr == GAN_DUNG(0.0, abs=1e-12)
    assert p.day_xoay_gia == GAN_DUNG(96550.0)
    assert p.day_xoay_ngay == df["time"].iloc[12]
    assert p.cat_lo_cau_truc == 94500.0
    assert p.rui_ro_pct == GAN_DUNG(5.5)
    assert p.vung is None and p.so_phien_cho is None
    assert len(p.ly_do) == 1 and "sát hơn" not in p.ly_do[0]
    assert df["time"].iloc[12] in p.ly_do[0]


def test_MUA_NGAY_cat_lo_sat_hon_bien_duoi_thi_them_ly_do():
    p = _lap(ca_mua_ngay_cat_lo_sat())
    assert p.phan_quyet == kh.MUA_NGAY
    assert p.cat_lo_cau_truc == 98200.0
    assert p.rui_ro_pct == GAN_DUNG(1.8)
    assert len(p.ly_do) == 2
    assert "sát hơn biên dưới ngân sách rủi ro" in p.ly_do[1]


def test_CHO_VUNG_do_rui_ro_so_tinh_tay():
    p = _lap(ca_cho_vung_do_rui_ro())
    assert p.phan_quyet == kh.CHO_VUNG
    assert p.atr == GAN_DUNG(4000.0)
    assert p.ma20 == GAN_DUNG(100050.0)
    assert p.keo_gian_atr == GAN_DUNG(0.95 / 4.0)
    assert p.day_xoay_gia == GAN_DUNG(96050.0)
    assert p.cat_lo_cau_truc == 94000.0                    # XUỐNG (94.050 → 94.000)
    assert p.rui_ro_pct == GAN_DUNG(6.930693, rel=1e-6)
    assert p.vung == (98000.0, 100500.0)   # đáy LÊN (97.917), trần XUỐNG (100.535)
    assert p.so_phien_cho == kh.SO_PHIEN_CHO == 5
    # Chỉ trượt vì RỦI RO + một dòng khoảng cách tới giá đóng.
    assert p.ly_do == ("rủi ro 6.9% vượt 6.5% nếu vào ở giá đóng",
                       "trần vùng cách giá đóng 0.1 ATR (0.5%)")


def test_CHO_VUNG_do_keo_gian_so_tinh_tay():
    p = _lap(ca_cho_vung_do_keo_gian())
    assert p.phan_quyet == kh.CHO_VUNG
    assert p.atr == GAN_DUNG(31 / 14 * 1000)
    assert p.ma20 == GAN_DUNG(100250.0)
    assert p.keo_gian_atr == GAN_DUNG(4.75 / (31 / 14))
    assert p.keo_gian_atr == GAN_DUNG(2.14516, rel=1e-5)
    assert p.cat_lo_cau_truc == 98300.0                    # 98.392,86 → XUỐNG
    assert p.rui_ro_pct == GAN_DUNG(6.380952, rel=1e-6)
    assert p.vung == (102400.0, 104600.0)  # 102.395,83 LÊN ; 104.678,57 XUỐNG
    # Chỉ trượt vì KÉO GIÃN.
    assert p.ly_do == ("giá cách MA20 2.1 ATR, vượt 2 ATR",
                       "trần vùng cách giá đóng 0.2 ATR (0.4%)")


def test_CHO_VUNG_do_ca_hai_dieu_kien_thi_ly_do_nen_ca_hai():
    p = _lap(ca_cho_vung_do_ca_hai())
    assert p.phan_quyet == kh.CHO_VUNG
    assert p.cat_lo_cau_truc == 97300.0
    assert p.vung == (101400.0, 104000.0)
    assert p.ly_do == ("rủi ro 8.2% vượt 6.5% nếu vào ở giá đóng",
                       "giá cách MA20 2.5 ATR, vượt 2 ATR",
                       "trần vùng cách giá đóng 0.9 ATR (1.9%)")


def test_CHO_VUNG_tran_vung_luon_duoi_gia_dong_va_vung_khong_dao():
    """Lệnh giới hạn ở trần vùng phải là lệnh CHỜ GIÁ XUỐNG (trần < giá đóng)."""
    for ca in (ca_cho_vung_do_rui_ro, ca_cho_vung_do_keo_gian,
               ca_cho_vung_do_ca_hai):
        p = _lap(ca())
        assert p.phan_quyet == kh.CHO_VUNG
        assert p.vung[0] <= p.vung[1] < p.gia_dong


def test_BO_QUA_khong_co_vung_so_tinh_tay():
    p = _lap(ca_bo_qua_khong_co_vung())
    assert p.phan_quyet == kh.BO_QUA
    assert p.vung is None and p.so_phien_cho is None
    assert p.cat_lo_cau_truc == 98700.0
    assert p.keo_gian_atr == GAN_DUNG(3.12941, rel=1e-5)
    assert p.rui_ro_pct == GAN_DUNG(5.096154, rel=1e-6)
    assert p.ly_do == ("giá cách MA20 3.1 ATR, vượt 2 ATR",
                       "không có giá nào vừa cả ngân sách rủi ro lẫn độ kéo giãn")


# ─────────────────────────────────────────────────────────────────────
# Ca MSR: đáy xoay GẦN NHẤT, vùng phải CHẠM ĐƯỢC
# ─────────────────────────────────────────────────────────────────────

def test_MSR_cat_lo_duoi_day_xoay_GAN_khong_phai_day_nen_cu():
    """Đáy 49,5 (nến 11) là nền CŨ trước bứt phá, vẫn trong 20 phiên; đáy xoay
    gần là nến 17 (57,0). Luật cũ (đáy thấp nhất 20 phiên) cắt lỗ ở ~48,9 nghìn
    — −18,5% — luật mới ở 56.400.

    TR cửa sổ ATR (nến 16..29): nến 16 = 1 ; nến 17 = max(3,5 ; 0,5 ; 3) = 3,5 ;
    12 nến còn lại = 1 → ATR = 16,5/14 = 1,1786 nghìn = 1.178,57 VNĐ.
    cắt lỗ = 57.000 − 589,29 = 56.410,71 → XUỐNG → 56.400 ; r = 3.600/60.000 = 6,0%
    trần ngân sách = 56.400/0,935 = 60.321 ≥ 60.000 ; k = (60 − 59)/1,1786 = 0,848
    → MUA_NGAY.
    """
    df = ca_msr(57.0)
    p = _lap(df)
    assert p.phan_quyet == kh.MUA_NGAY
    assert p.day_xoay_gia == GAN_DUNG(57000.0)
    assert p.day_xoay_ngay == df["time"].iloc[17]
    assert p.atr == GAN_DUNG(16.5 / 14 * 1000)
    assert p.ma20 == GAN_DUNG(59000.0)
    assert p.cat_lo_cau_truc == 56400.0
    assert p.rui_ro_pct == GAN_DUNG(6.0)
    assert p.keo_gian_atr == GAN_DUNG(1.0 / (16.5 / 14))
    assert p.day_xoay_ngay != df["time"].iloc[11]      # không phải nền cũ


def test_MSR_vung_qua_xa_gia_dong_thi_BO_QUA_co_so():
    """Đáy xoay 52 (nến 17): ATR = (1 + 8,5 + 12)/14 = 21,5/14 = 1.535,71 VNĐ.

    cắt lỗ = 52.000 − 767,86 = 51.232,14 → XUỐNG → 51.200 ; r = 8.800/60.000 = 14,67%
    trần ngân sách = 51.200/0,935 = 54.759,36 ; trần kéo giãn = 59.000 + 3.071,43
    đáy vùng = 51.200/0,96 = 53.333,33 → LÊN → 53.400
    trần vùng = min(54.759,36 ; 62.071,43) → XUỐNG → 54.700
    cách giá đóng 60.000 − 54.700 = 5.300 = 3,45 ATR (8,8%) > 2 ATR → BO_QUA.
    """
    p = _lap(ca_msr(52.0))
    assert p.phan_quyet == kh.BO_QUA
    assert p.vung is None and p.so_phien_cho is None
    assert p.cat_lo_cau_truc == 51200.0
    assert p.rui_ro_pct == GAN_DUNG(14.666667, rel=1e-6)
    assert p.ly_do == (
        "rủi ro 14.7% vượt 6.5% nếu vào ở giá đóng",
        "vùng vừa rủi ro 53,400–54,700 cách giá đóng 3.5 ATR (8.8%) — quá xa "
        "để chờ trong 5 phiên; chờ nền giá mới")


def test_LUI_TOI_DA_ATR_la_cua_chan_giua_CHO_VUNG_va_BO_QUA__hai_ca_sat_bien():
    """Hai ca MSR chỉ khác đáy xoay (54,5 và 54,0), khoảng cách tới trần vùng
    nằm hai phía của 2 ATR.

    TR cửa sổ ATR = 1 (nến 16) + (60,5 − đáy) (nến 17) + 12×1 → ATR = (73,5 − đáy)/14.
    Đáy 54,5: ATR = 19/14 = 1.357,14 ; cắt lỗ = 54.500 − 678,57 = 53.821,43 → 53.800
      r = 6.200/60.000 = 10,33% ; đáy vùng = 53.800/0,96 = 56.041,67 → LÊN 56.100
      trần vùng = min(57.540,1 ; 61.714,3) → XUỐNG 57.500 ; cách giá đóng 2.500
      = 1,84 ATR (4,2%) ≤ 2 → CHO_VUNG.
    Đáy 54,0: ATR = 19,5/14 = 1.392,86 ; cắt lỗ = 54.000 − 696,43 → 53.300
      r = 11,17% ; đáy vùng = 55.520,8 → LÊN 55.600 ; trần vùng = 57.005,3 →
      XUỐNG 57.000 ; cách giá đóng 3.000 = 2,15 ATR (5,0%) > 2 → BO_QUA.
    """
    gan = _lap(ca_msr(54.5))
    assert gan.phan_quyet == kh.CHO_VUNG
    assert gan.cat_lo_cau_truc == 53800.0
    assert gan.vung == (56100.0, 57500.0)
    assert gan.ly_do[-1] == "trần vùng cách giá đóng 1.8 ATR (4.2%)"
    xa = _lap(ca_msr(54.0))
    assert xa.phan_quyet == kh.BO_QUA
    assert xa.cat_lo_cau_truc == 53300.0
    assert xa.ly_do[-1] == (
        "vùng vừa rủi ro 55,600–57,000 cách giá đóng 2.2 ATR (5.0%) — quá xa "
        "để chờ trong 5 phiên; chờ nền giá mới")
    assert 1.84 < kh.LUI_TOI_DA_ATR < 2.15


def test_gia_thung_moi_day_xoay_thi_BO_QUA():
    """Nền 100 / 101 / 99,5, đáy xoay duy nhất 99,0 (nến 12) ; nến cuối đóng 95.

    Mọi đáy xoay (99.000) ≥ giá đóng (95.000) → chưa có đáy đỡ dưới giá.
    """
    p = _lap(_nen(100.0, 101.0, 99.5, (100.0, 100.0, 94.0, 95.0), {12: 99.0}))
    assert p.phan_quyet == kh.BO_QUA
    assert p.ly_do == (f"giá đã thủng mọi đáy xoay trong {kh.CUA_SO_DAY} phiên — "
                       f"chưa có đáy đỡ dưới giá",)
    assert p.cat_lo_cau_truc is None and p.day_xoay_gia is None
    assert p.gia_dong == GAN_DUNG(95000.0)


# ─────────────────────────────────────────────────────────────────────
# Định nghĩa đáy xoay — biên K, dấu bằng, cửa sổ, chọn đáy GẦN NHẤT
# ─────────────────────────────────────────────────────────────────────

def test_day_xoay_can_K_phien_xac_nhan_moi_ben__K_bang_2_khong_phai_1():
    """Đáy nông ở nến 22 (96,8) có K=1 là đáy xoay nhưng K=2 thì không: hai nến
    trước nó là (96,0 ; 97) và 96,0 < 96,8. K=2 nên đáy xoay GẦN NHẤT là nến 20
    (96,0), không phải nến 22.

    TR cửa sổ ATR: nến 20 = 5 ; nến 22 = 4,2 ; 12 nến còn lại = 4
    → ATR = 57,2/14 = 4,0857 nghìn ; cắt lỗ = 96.000 − 2.042,86 = 93.957,14 → 93.900.
    """
    assert kh.SO_PHIEN_XAC_NHAN_DAY == 2
    df = _nen(100.0, 101.0, 97.0, (100.0, 101.0, 97.0, 100.0),
              {12: 96.55, 20: 96.0, 22: 96.8})
    p = _lap(df)
    assert p.day_xoay_ngay == df["time"].iloc[20]
    assert p.day_xoay_gia == GAN_DUNG(96000.0)
    assert p.atr == GAN_DUNG(57.2 / 14 * 1000)
    assert p.cat_lo_cau_truc == 93900.0


def test_day_xoay_cho_phep_bang_nen_truoc_nhung_phai_THAP_HON_HAN_nen_sau():
    """Đáy kép: nến 15 và 16 cùng đáy 96,0 (nền 97).

    Nến 16: 96,0 ≤ min(97 ; 96,0) ✓ và 96,0 < min(97 ; 97) ✓ → đáy xoay.
    Nến 15: 96,0 < min(96,0 ; 97) ✗ (bằng nến sau) → không phải.
    """
    df = _nen(100.0, 101.0, 97.0, (100.0, 101.0, 97.0, 100.0),
              {15: 96.0, 16: 96.0})
    p = _lap(df)
    assert p.phan_quyet == kh.MUA_NGAY
    assert p.day_xoay_ngay == df["time"].iloc[16]
    assert p.day_xoay_gia == GAN_DUNG(96000.0)


def test_day_xoay_bang_phang_tiep_sau_bang_mot_day_thap_hon_khong_phai_day_xoay():
    """Nến 25 và 26 cùng đáy 96,5 ; nến 27 = 97 ; nến 28 = 95,5 (chỉ còn MỘT nến
    sau nên nến 28 chưa xác nhận được). Nến 25 có đáy BẰNG nến 26 (không thấp hơn
    hẳn) ; nến 26 có đáy cao hơn nến 28 → không nến nào ở đuôi là đáy xoay, và đáy
    xoay GẦN NHẤT vẫn là nến 12 (96,55)."""
    df = _nen(100.0, 101.0, 97.0, (100.0, 101.0, 97.0, 100.0),
              {12: 96.55, 25: 96.5, 26: 96.5, 28: 95.5})
    p = _lap(df)
    assert p.day_xoay_ngay == df["time"].iloc[12]
    assert p.day_xoay_gia == GAN_DUNG(96550.0)


def test_cua_so_day_la_20_phien_bien_trong_va_ngoai():
    """Biên của cửa sổ: nến thứ 20 tính từ cuối (chỉ số 10) được xét, thứ 21
    (chỉ số 9) thì không. Biên sau: nến cần K=2 nến sau, nên chỉ số 27 được xét,
    chỉ số 28 thì không."""
    tren = lambda i: _lap(_nen(100.0, 101.0, 97.0,        # noqa: E731
                               (100.0, 101.0, 97.0, 100.0), {i: 96.55}))
    df = _nen(100.0, 101.0, 97.0, (100.0, 101.0, 97.0, 100.0))
    for i in (10, 27):
        p = tren(i)
        assert p.phan_quyet == kh.MUA_NGAY, i
        assert p.day_xoay_gia == GAN_DUNG(96550.0), i
        assert p.day_xoay_ngay == df["time"].iloc[i], i
    for i in (9, 28):
        assert tren(i).phan_quyet == kh.CHUA_LAP_DUOC, i


def test_day_xoay_phai_THAP_HON_gia_dong__bo_day_o_tren_gia_roi_lay_day_cu_hon():
    """Nến 0..19: nền 100 (đáy 97 ; nến 12 đáy 96). Nến 20..29: giá lên 110
    rồi sập về 100. Nến 24 có đáy 106,5 là đáy xoay GẦN NHẤT nhưng 106,5 ≥ giá
    đóng 100 → bỏ. Nến 19 (đáy 97, bằng nền trước, thấp hơn hẳn hai nến sau)
    là đáy xoay gần nhất còn DƯỚI giá đóng."""
    dong = []
    for i in range(30):
        if i == 12:
            dong.append([100.0, 101.0, 96.0, 100.0])
        elif i <= 19:
            dong.append([100.0, 101.0, 97.0, 100.0])
        elif i <= 23:
            dong.append([110.0, 111.0, 107.0, 110.0])
        elif i == 24:
            dong.append([110.0, 111.0, 106.5, 110.0])
        elif i in (25, 26):
            dong.append([110.0, 111.0, 107.0, 108.0])
        elif i == 27:
            dong.append([108.0, 108.0, 103.0, 104.0])
        elif i == 28:
            dong.append([104.0, 104.0, 101.0, 102.0])
        else:
            dong.append([102.0, 102.0, 99.0, 100.0])
    ngay = pd.date_range("2026-03-02", periods=30, freq="B").strftime("%Y-%m-%d")
    df = pd.DataFrame(dong, columns=["open", "high", "low", "close"]).assign(
        volume=1000.0, time=ngay)
    p = _lap(df)
    assert p.gia_dong == GAN_DUNG(100000.0)
    assert p.phan_quyet != kh.CHUA_LAP_DUOC
    assert p.day_xoay_ngay == df["time"].iloc[19]
    assert p.day_xoay_gia == GAN_DUNG(97000.0)


# ─────────────────────────────────────────────────────────────────────
# Wyckoff hướng giảm → BO_QUA
# ─────────────────────────────────────────────────────────────────────

def _khung_wy(closes, vols):
    n = len(closes)
    return pd.DataFrame({
        "time": pd.date_range("2025-01-01", periods=n,
                              freq="B").strftime("%Y-%m-%d"),
        "open": list(closes), "close": list(closes),
        "high": [c * 1.005 for c in closes], "low": [c * 0.995 for c in closes],
        "volume": list(vols)})


def _doan(tu, den, n):
    buoc = (den - tu) / (n - 1)
    return [tu + buoc * i for i in range(n)]


def _phan_phoi_utad():
    """100 phiên: tăng → cao trào mua → AR sụt → nền → UTAD ở phiên 93.

    Dựng như `tests/test_pha_wyckoff.py::_phan_phoi` + `test_utad_...`.
    """
    closes = (_doan(80, 100, 50) + _doan(102, 108, 3) + _doan(107, 100, 6)
              + [102, 103, 104, 102, 103, 105, 102, 103, 104, 103] * 3 + [103])
    vols = [1000] * 50 + [4000] * 3 + [1500] * 6 + [800] * 31
    closes, vols = closes[:90], vols[:90]
    closes += [103, 104, 103, 104, 103, 104, 103, 104, 103, 104]
    vols += [800] * 10
    df = _khung_wy(closes, vols)
    df.loc[93, "close"] = df.loc[93, "open"] = 104.0
    df.loc[93, "high"] = 112.0
    df.loc[93, "volume"] = 2500
    return df


def _wy_gia(huong):
    """Một kết quả Wyckoff KẾT LUẬN ĐƯỢC với hướng cho trước (dựng tay)."""
    return pha_wyckoff.PhaWyckoff(
        pha="C", cau_truc="PHÂN PHỐI", su_kien="UTAD", do_tin="nhiều khả năng",
        nhan_ngan="Pha C — UTAD", nhan_day="x", huong=huong, san=1.0, tran=2.0,
        so_phien_nen=40, bang_chung=(), phan_bien=(), phu_dinh="")


def test_BO_QUA_do_Wyckoff_giam__ca_THAT():
    """Bảng 100 phiên có UTAD thật → `doc_pha` nói GIAM → BO_QUA.

    Chính cây nến cuối ấy KHÔNG trượt điều kiện nào (rủi ro 3,5% — sát hơn
    biên dưới, kéo giãn 0,33 ATR) nên nếu bỏ nhánh Wyckoff thì nó là MUA_NGAY:
    ca kế dưới đây chứng minh chính Wyckoff đổi phán quyết.
    """
    df = _phan_phoi_utad()
    assert pha_wyckoff.doc_pha(df).huong == pha_wyckoff.GIAM
    p = _lap(df)
    assert p.phan_quyet == kh.BO_QUA
    assert p.ly_do == ("cấu trúc Wyckoff hướng giảm: Pha C — UTAD",)
    assert p.ngay == "2025-05-20" and p.gia_dong == GAN_DUNG(104000.0)
    assert p.vung is None


def test_Wyckoff_giam_la_nguyen_nhan_duy_nhat__doi_thanh_trung_tinh_thi_MUA_NGAY(
        monkeypatch):
    df = _phan_phoi_utad()
    monkeypatch.setattr(kh.pha_wyckoff, "doc_pha",
                        lambda d, he=1.0: _wy_gia(pha_wyckoff.TRUNG_TINH))
    p = _lap(df)
    assert p.phan_quyet == kh.MUA_NGAY
    assert p.rui_ro_pct < muc_fibonacci.SL_HEP_NHAT * 100


def test_Wyckoff_giam_cong_voi_dieu_kien_truot_thi_giu_MOI_ly_do(monkeypatch):
    monkeypatch.setattr(kh.pha_wyckoff, "doc_pha",
                        lambda d, he=1.0: _wy_gia(pha_wyckoff.GIAM))
    p = _lap(ca_cho_vung_do_ca_hai())       # lẽ ra CHO_VUNG
    assert p.phan_quyet == kh.BO_QUA and p.vung is None
    assert len(p.ly_do) == 4
    assert p.ly_do[0].startswith("cấu trúc Wyckoff hướng giảm")
    assert "rủi ro" in p.ly_do[1] and "ATR, vượt" in p.ly_do[2]
    assert p.ly_do[3].startswith("trần vùng cách giá đóng")


def test_Wyckoff_giam_cong_voi_vung_qua_xa_thi_van_giu_ca_hai(monkeypatch):
    monkeypatch.setattr(kh.pha_wyckoff, "doc_pha",
                        lambda d, he=1.0: _wy_gia(pha_wyckoff.GIAM))
    p = _lap(ca_msr(52.0))
    assert p.phan_quyet == kh.BO_QUA
    assert p.ly_do[0].startswith("cấu trúc Wyckoff hướng giảm")
    assert "quá xa để chờ" in p.ly_do[-1]


def test_Wyckoff_khong_ket_luan_duoc_thi_khong_bo_qua(monkeypatch):
    """`ket_luan_duoc` False (pha=None) dù `huong` là GIAM → không được BO_QUA."""
    gia = _wy_gia(pha_wyckoff.GIAM)
    khong = pha_wyckoff.PhaWyckoff(**{**gia.__dict__, "pha": None})
    monkeypatch.setattr(kh.pha_wyckoff, "doc_pha", lambda d, he=1.0: khong)
    assert _lap(ca_mua_ngay()).phan_quyet == kh.MUA_NGAY


# ─────────────────────────────────────────────────────────────────────
# Tính chất
# ─────────────────────────────────────────────────────────────────────

def test_ATR_khop_compute_local_indicators__goi_hai_ham_THAT():
    """ATR của module = ATR của `DataOrchestrator._compute_local_indicators`."""
    from data_collectors import DataOrchestrator
    rng = np.random.default_rng(11)
    n = 60
    dong = 50 + rng.normal(0, 1, n).cumsum()
    df = pd.DataFrame({
        "time": pd.date_range("2026-01-05", periods=n,
                              freq="B").strftime("%Y-%m-%d"),
        "open": dong + rng.normal(0, .3, n),
        "high": dong + rng.uniform(.2, 1.5, n),
        "low": dong - rng.uniform(.2, 1.5, n),
        "close": dong, "volume": rng.integers(1000, 9000, n).astype(float)})
    tham_chieu = DataOrchestrator("XXX", "2026-01-01", "2026-12-31",
                                  collect_news=False)._compute_local_indicators(df)
    p = _lap(df)
    assert p.atr is not None, "ATR phải hiện dù phán quyết là gì"
    assert p.atr / HE == GAN_DUNG(tham_chieu["ATR"], rel=1e-12)
    # ...và MA20 của module là SMA(20) của chính cột đóng cửa.
    assert p.ma20 / HE == GAN_DUNG(df["close"].tail(20).mean(), rel=1e-12)


def test_chu_ky_MA_trung_chu_ky_MA_ngan_cua_khung_thoi_gian():
    assert kh.CHU_KY_MA == khung_thoi_gian.CHU_KY_MA_NGAN


def test_so_nen_toi_thieu_la_phep_SUY_RA__kiem_hinh_dang_bang_AST():
    cay = ast.parse((GOC / "ke_hoach_vao_lenh.py").read_text(encoding="utf-8"))
    gan = next(n.value for n in cay.body if isinstance(n, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id == "SO_NEN_TOI_THIEU"
                       for t in n.targets))
    assert isinstance(gan, ast.Call) and gan.func.id == "max"
    ten = {n.id for n in ast.walk(gan) if isinstance(n, ast.Name)}
    assert ten == {"max", "CHU_KY_MA", "CHU_KY_ATR", "CUA_SO_DAY"}


def test_nen_do_khong_doi_ke_hoach():
    """Thêm một nến HÔM NAY chưa đóng (cực đoan) → kế hoạch y hệt không có nó."""
    goc = ca_cho_vung_do_rui_ro()                     # nến cuối 2026-04-10
    dang_do = pd.concat([goc, pd.DataFrame([{
        "time": "2026-04-13", "open": 1000.0, "high": 1000.0, "low": 1.0,
        "close": 500.0, "volume": 1.0}])], ignore_index=True)
    trong_phien = datetime(2026, 4, 13, 10, 0)
    assert _lap(dang_do, bay_gio=trong_phien) == _lap(goc, bay_gio=trong_phien)
    # Đối chứng: sau giờ đóng cửa nến ấy là nến thật và PHẢI đổi kế hoạch —
    # nếu không, phép so ở trên xanh vì nến cực đoan không có sức nặng.
    sau_dong = datetime(2026, 4, 13, 16, 0)
    p = _lap(dang_do, bay_gio=sau_dong)
    assert p.ngay == "2026-04-13" and p != _lap(goc, bay_gio=sau_dong)


def test_ngay_cua_ke_hoach_la_nen_da_dong_cuoi_cung():
    goc = ca_mua_ngay()
    assert _lap(goc).ngay == "2026-04-10"
    dang_do = goc.copy()
    dang_do.loc[len(dang_do) - 1, "time"] = "2026-04-13"
    assert _lap(dang_do, bay_gio=datetime(2026, 4, 13, 14, 29)).ngay == "2026-04-09"
    assert _lap(dang_do, bay_gio=datetime(2026, 4, 13, 15, 30)).ngay == "2026-04-13"


def test_khong_nhin_trom_va_khong_nho_gi_giua_hai_lan_goi():
    """Kế hoạch tại t chỉ phụ thuộc các dòng ≤ t và các dòng TRONG CỬA SỔ.

    (1) Nối nến sau t với giá cực đoan làm t dời đi (đối chứng: kế hoạch ĐỔI),
        rồi gọi lại với bảng cắt tới t → kế hoạch y hệt lần đầu: hàm không giữ
        trạng thái nào giữa hai lần gọi.
    (2) Hàm không sửa bảng của người gọi.
    (3) Dòng cũ hơn cửa sổ (đây là 10 nến cực đoan chèn TRƯỚC) không đổi gì.
    """
    t = ca_cho_vung_do_rui_ro()
    ban_dau = _lap(t)
    sau_t = _nen(1000.0, 5000.0, 1.0, (1.0, 5000.0, 1.0, 4000.0), n=3,
                 bat_dau="2026-04-13")
    noi = pd.concat([t, sau_t], ignore_index=True)
    assert _lap(noi) != ban_dau                          # đối chứng
    t_sao = t.copy(deep=True)
    assert _lap(t) == ban_dau
    pd.testing.assert_frame_equal(t, t_sao)              # (2)
    cu = _nen(900.0, 9000.0, 1.0, (900.0, 9000.0, 1.0, 900.0), n=10,
              bat_dau="2025-01-06")
    assert _lap(pd.concat([cu, t], ignore_index=True)) == ban_dau   # (3)


def test_don_vi_di_vao_bang_don_vi_di_ra():
    """Bảng nghìn đồng + `he_so_gia`=1000 cho cùng kế hoạch như bảng VNĐ + 1."""
    nghin = _lap(ca_cho_vung_do_rui_ro(), he=1000.0)
    vnd_df = ca_cho_vung_do_rui_ro()
    for c in ("open", "high", "low", "close"):
        vnd_df[c] = vnd_df[c] * 1000.0
    p = _lap(vnd_df, he=1.0)
    assert p.phan_quyet == nghin.phan_quyet
    for ten in ("gia_dong", "atr", "ma20", "cat_lo_cau_truc", "day_xoay_gia"):
        assert getattr(p, ten) == GAN_DUNG(getattr(nghin, ten), rel=1e-9)
    assert p.vung == (GAN_DUNG(nghin.vung[0], rel=1e-9),
                      GAN_DUNG(nghin.vung[1], rel=1e-9))
    assert p.keo_gian_atr == GAN_DUNG(nghin.keo_gian_atr, rel=1e-9)
    assert p.rui_ro_pct == GAN_DUNG(nghin.rui_ro_pct, rel=1e-9)
    assert p.ly_do == nghin.ly_do


def test_gia_ra_deu_nam_tren_luoi_buoc_gia_cua_san():
    """Mọi giá ra do module TẠO (cắt lỗ, hai biên vùng) chia hết cho bước giá."""
    for ca in (ca_mua_ngay, ca_mua_ngay_cat_lo_sat, ca_cho_vung_do_rui_ro,
               ca_cho_vung_do_keo_gian, ca_cho_vung_do_ca_hai):
        p = _lap(ca())
        gia = [p.cat_lo_cau_truc] + list(p.vung or ())
        assert gia and all(g % 100 == 0 for g in gia), (ca.__name__, gia)


def test_bang_hien_thi_phu_du_moi_phan_quyet():
    tat_ca = {kh.KHONG_XET, kh.CHUA_LAP_DUOC, kh.BO_QUA, kh.MUA_NGAY,
              kh.CHO_VUNG}
    assert set(kh.HIEN_THI) == tat_ca
    assert kh.HIEN_THI[kh.KHONG_XET] == ("THEO DÕI", "neu")
    assert kh.HIEN_THI[kh.MUA_NGAY] == ("MUA NGAY", "pos")
    assert kh.HIEN_THI[kh.CHO_VUNG] == ("CHỜ VÙNG", "neu")
    assert kh.HIEN_THI[kh.BO_QUA] == ("BỎ QUA", "neg")
    assert kh.HIEN_THI[kh.CHUA_LAP_DUOC] == ("CHƯA LẬP ĐƯỢC", "neu")


def test_ket_qua_bat_bien_va_gia_la_so_huu_han():
    p = _lap(ca_cho_vung_do_rui_ro())
    with pytest.raises(Exception):
        p.phan_quyet = kh.MUA_NGAY                      # frozen
    for x in (p.gia_dong, p.atr, p.ma20, p.keo_gian_atr, p.cat_lo_cau_truc,
              p.rui_ro_pct, p.day_xoay_gia, *p.vung):
        assert math.isfinite(x)


def test_gia_xa_DUOI_MA20_khong_bi_coi_la_keo_gian():
    """Kéo giãn có DẤU: giá dưới MA20 hơn 2 ATR không phải "chạy xa lên".

    Nền 100 / 101 / 99 ; đáy xoay nến 12 = 90 ; nến cuối 100 / 100 / 93 / 94.
    true range nến cuối = max(7 ; |100−100| ; |93−100|) = 7
    ATR = (13×2 + 7)/14 = 33/14 ; MA20 = (1900 + 94)/20 = 99,7
    k = (94 − 99,7)/(33/14) = −2,418 → không vượt +2 → vẫn xét theo rủi ro
    cắt lỗ = 90.000 − 1.178,57 = 88.821,43 → 88.800 ; r = 5.200/94.000 = 5,53% → MUA_NGAY.
    """
    p = _lap(_nen(100.0, 101.0, 99.0, (100.0, 100.0, 93.0, 94.0), {12: 90.0}))
    assert p.keo_gian_atr == GAN_DUNG(-5.7 * 14 / 33)
    assert p.cat_lo_cau_truc == 88800.0
    assert p.phan_quyet == kh.MUA_NGAY


# ─────────────────────────────────────────────────────────────────────
# AST — hình dạng biểu thức vùng, và không có bảng bước giá gõ lại
# ─────────────────────────────────────────────────────────────────────

def _ham_lap():
    cay = ast.parse((GOC / "ke_hoach_vao_lenh.py").read_text(encoding="utf-8"))
    return cay, next(n for n in cay.body if isinstance(n, ast.FunctionDef)
                     and n.name == "lap_ke_hoach")


def _gan(ham, ten):
    for n in ast.walk(ham):
        if isinstance(n, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == ten for t in n.targets):
            return n.value
    raise AssertionError(f"không thấy phép gán {ten}")


def _la_chia_cho_1_tru(bt, ten_chia, ten_tru):
    """`ten_chia / (1.0 - ten_tru)` — cả hai đều là TÊN, không phải số."""
    return (isinstance(bt, ast.BinOp) and isinstance(bt.op, ast.Div)
            and isinstance(bt.left, ast.Name) and bt.left.id == ten_chia
            and isinstance(bt.right, ast.BinOp)
            and isinstance(bt.right.op, ast.Sub)
            and isinstance(bt.right.left, ast.Constant)
            and bt.right.left.value == 1
            and isinstance(bt.right.right, ast.Name)
            and bt.right.right.id == ten_tru)


def test_bien_vung_la_bieu_thuc_theo_TEN_SL_HEP_NHAT_va_SL_RONG_NHAT():
    cay, ham = _ham_lap()
    assert _la_chia_cho_1_tru(_gan(ham, "day_ngan_sach"), "cat_lo",
                              "SL_HEP_NHAT")
    assert _la_chia_cho_1_tru(_gan(ham, "tran_ngan_sach"), "cat_lo",
                              "SL_RONG_NHAT")
    # Hai hằng số được NHẬP từ muc_fibonacci, không khai lại ở đây.
    nhap = [n for n in cay.body if isinstance(n, ast.ImportFrom)
            and n.module == "muc_fibonacci"]
    assert nhap and {a.name for a in nhap[0].names} == {
        "SL_HEP_NHAT", "SL_RONG_NHAT"}
    ten_gan = {t.id for n in ast.walk(cay) if isinstance(n, ast.Assign)
               for t in n.targets if isinstance(t, ast.Name)}
    assert not ({"SL_HEP_NHAT", "SL_RONG_NHAT"} & ten_gan)


def _goi_ten(bt, ten):
    return (isinstance(bt, ast.Call) and isinstance(bt.func, ast.Name)
            and bt.func.id == ten)


def test_hai_bien_vung_va_cat_lo_di_qua_dung_ham_lam_tron_dung_huong():
    """Cắt lỗ XUỐNG · đáy vùng LÊN · trần vùng XUỐNG (kèm `min` của hai trần)."""
    _, ham = _ham_lap()
    cl = _gan(ham, "cat_lo")
    assert _goi_ten(cl, "lam_tron_xuong")
    dv = _gan(ham, "day_vung")
    assert _goi_ten(dv, "lam_tron_len")
    assert [a.id for a in dv.args] == ["day_ngan_sach", "san"]
    tv = _gan(ham, "tran_vung")
    assert _goi_ten(tv, "lam_tron_xuong")
    mn = tv.args[0]
    assert _goi_ten(mn, "min")
    assert [a.id for a in mn.args] == ["tran_ngan_sach", "tran_keo_gian"]
    assert tv.args[1].id == "san"


def test_tran_keo_gian_la_ma20_cong_he_so_nhan_atr_theo_ten():
    _, ham = _ham_lap()
    tk = _gan(ham, "tran_keo_gian")
    assert (isinstance(tk, ast.BinOp) and isinstance(tk.op, ast.Add)
            and {n.id for n in ast.walk(tk) if isinstance(n, ast.Name)}
            == {"ma20_v", "KEO_GIAN_TOI_DA_ATR", "atr_v"})


def test_kiem_xa_dung_LUI_TOI_DA_ATR_nhan_ATR():
    _, ham = _ham_lap()
    xa = _gan(ham, "xa")
    assert (isinstance(xa, ast.Compare) and isinstance(xa.ops[0], ast.Gt)
            and isinstance(xa.left, ast.Name) and xa.left.id == "khoang"
            and isinstance(xa.comparators[0], ast.BinOp)
            and {n.id for n in ast.walk(xa.comparators[0])
                 if isinstance(n, ast.Name)} == {"LUI_TOI_DA_ATR", "atr_v"})


def test_khong_co_bang_buoc_gia_go_lai_trong_module():
    """Bước giá đọc từ `truot_gia` (`buoc_gia` / `BUOC_GIA`), không gõ lại."""
    cay = ast.parse((GOC / "ke_hoach_vao_lenh.py").read_text(encoding="utf-8"))
    docstring = set()
    for n in ast.walk(cay):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            if (n.body and isinstance(n.body[0], ast.Expr)
                    and isinstance(n.body[0].value, ast.Constant)
                    and isinstance(n.body[0].value.value, str)):
                docstring.add(id(n.body[0].value))
    # Hằng nằm trong chỉ số cắt (`ngay = str(...)[:10]` lấy 10 ký tự đầu của một
    # ngày ISO) không phải bước giá.
    cat_chuoi = {id(c) for n in ast.walk(cay) if isinstance(n, ast.Slice)
                 for c in ast.walk(n) if isinstance(c, ast.Constant)}
    cam_so = {10, 50, 10000, 50000, 10_000.0, 50_000.0}
    cam_chuoi = {"HOSE", "HNX", "UPCOM"}
    loi = []
    for n in ast.walk(cay):
        if (isinstance(n, ast.Constant) and id(n) not in docstring
                and id(n) not in cat_chuoi):
            if isinstance(n.value, (int, float)) and not isinstance(
                    n.value, bool) and n.value in cam_so:
                loi.append((n.lineno, n.value))
            if isinstance(n.value, str) and n.value.upper() in cam_chuoi:
                loi.append((n.lineno, n.value))
    assert not loi, f"bảng bước giá gõ lại trong module: {loi}"
    nhap = {n.names[0].name for n in ast.walk(cay) if isinstance(n, ast.Import)}
    assert "truot_gia" in nhap
    thuoc_tinh = {(n.value.id, n.attr) for n in ast.walk(cay)
                  if isinstance(n, ast.Attribute)
                  and isinstance(n.value, ast.Name)}
    assert ("truot_gia", "buoc_gia") in thuoc_tinh
    assert ("truot_gia", "BUOC_GIA") in thuoc_tinh


def test_hang_so_de_xuat_deu_duoc_danh_dau_CHUA_DO():
    src = (GOC / "ke_hoach_vao_lenh.py").read_text(encoding="utf-8")
    assert "ĐỀ XUẤT, CHƯA ĐO" in src
    assert "bất biến 7" in src
    # Docstring của module (không quét văn bản nguồn: "MSR" là mã cổ phiếu).
    assert "VÌ SAO ĐỔI (10/10/2026)" in kh.__doc__ and "MSR" in kh.__doc__


# ─────────────────────────────────────────────────────────────────────
# AST — CHỈ ĐỂ HIỆN: ai được nhập, app gọi gì
# ─────────────────────────────────────────────────────────────────────

def _nhap_va_goi(duong: pathlib.Path) -> tuple[set[str], set[str]]:
    cay = ast.parse(duong.read_text(encoding="utf-8"))
    nhap, goi = set(), set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            nhap |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            nhap.add(n.module.split(".")[0])
        elif isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name):
                goi.add(f.id)
            elif isinstance(f, ast.Attribute):
                goi.add(f.attr)
    return nhap, goi


def _file_ma_nguon() -> list[pathlib.Path]:
    bo = {"tests", ".venv", ".git", "node_modules", "__pycache__"}
    return [p for p in duyet_repo.duyet(GOC, "*.py")
            if not (set(p.relative_to(GOC).parts) & bo)]


def test_CHI_app_py_duoc_nhap_ke_hoach_vao_lenh():
    """Danh sách cấm cụ thể dễ bị quên khi có file mới → cho phép đúng MỘT nơi."""
    nguoi_nhap = {p.relative_to(GOC).as_posix() for p in _file_ma_nguon()
                  if "ke_hoach_vao_lenh" in _nhap_va_goi(p)[0]}
    assert nguoi_nhap == {"app.py"}, (
        f"ke_hoach_vao_lenh CHỈ ĐỂ HIỆN, chỉ app.py được nhập; đang có: "
        f"{sorted(nguoi_nhap)}")


@pytest.mark.parametrize("ten", [
    "run_daily.py", "paper_trading.py", "paper_runner.py", "paper_metrics.py",
    "master_agent.py", "analysis_agents.py", "debate_agents.py",
    "news_sentiment_agent.py", "fundamental_agent.py", "data_collectors.py",
    "walkforward.py", "sheets_store.py"])
def test_duong_giao_dich_cham_diem_va_du_lieu_KHONG_nhap(ten):
    duong = GOC / ten
    if duong.exists():
        assert "ke_hoach_vao_lenh" not in _nhap_va_goi(duong)[0], ten
    assert not [p for p in duyet_repo.duyet(GOC / "backtest", "*.py")
                if "ke_hoach_vao_lenh" in _nhap_va_goi(p)[0]]


def test_module_chi_nhap_thu_trung_tinh():
    nhap, goi = _nhap_va_goi(GOC / "ke_hoach_vao_lenh.py")
    assert nhap <= {"__future__", "math", "dataclasses", "datetime", "pandas",
                    "data_quality", "pha_wyckoff", "muc_fibonacci",
                    "truot_gia"}, nhap
    # Hàm thuần: không đồng hồ, không mạng.
    assert not ({"now", "today", "now_vn", "today_vn", "read_csv", "get",
                 "request", "urlopen"} & goi), goi
    assert "nen_cuoi_dang_do" in goi and "doc_pha" in goi


def _app_goi(cay, ten):
    return [n for n in ast.walk(cay) if isinstance(n, ast.Call)
            and ((isinstance(n.func, ast.Attribute) and n.func.attr == ten)
                 or (isinstance(n.func, ast.Name) and n.func.id == ten))]


def test_APP_goi_lap_ke_hoach_voi_BUY_THRESHOLD_va_cung_bay_gio_voi_gop_nen():
    cay = ast.parse((GOC / "app.py").read_text(encoding="utf-8"))
    nhap, _ = _nhap_va_goi(GOC / "app.py")
    assert "ke_hoach_vao_lenh" in nhap

    lenh = _app_goi(cay, "lap_ke_hoach")
    assert len(lenh) == 1, "app phải lập kế hoạch ĐÚNG MỘT lần"
    goi = lenh[0]
    ten_doi = ("df", "he_so_gia", "diem", "nguong", "bay_gio", "san")
    doi = dict(zip(ten_doi, goi.args))
    doi.update({k.arg: k.value for k in goi.keywords})
    assert set(doi) == set(ten_doi)
    # Ngưỡng là TÊN `BUY_THRESHOLD`, không phải một con số.
    assert isinstance(doi["nguong"], ast.Name)
    assert doi["nguong"].id == "BUY_THRESHOLD"
    assert isinstance(doi["he_so_gia"], ast.Name) and doi["he_so_gia"].id == "mult"
    assert isinstance(doi["diem"], ast.Name) and doi["diem"].id == "score"
    # CÙNG `bay_gio` với lời gọi `_nen_ba_khung(...)` (đưa vào `gop_nen`).
    ba_khung = _app_goi(cay, "_nen_ba_khung")
    assert ba_khung
    assert any(ast.dump(doi["bay_gio"]) == ast.dump(g.args[2])
               for g in ba_khung), "bay_gio khác với bay_gio đưa vào gop_nen"


def _gan_app(cay, ten):
    return [n.value for n in ast.walk(cay) if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == ten for t in n.targets)]


def test_APP_truyen_san_tra_theo_MA_khong_theo_o_chon_san():
    """Sàn tra theo MÃ (`san_giao_dich.tra_san`, BƯỚC 143); ô chọn sàn ở thanh
    bên (`exchange`, mặc định HOSE) chỉ là đường LUI khi mã không có trong bảng.
    MSR là UPCoM trong khi ô ấy mặc định HOSE."""
    cay = ast.parse((GOC / "app.py").read_text(encoding="utf-8"))
    goi = _app_goi(cay, "lap_ke_hoach")[0]
    doi = dict(zip(("df", "he_so_gia", "diem", "nguong", "bay_gio", "san"),
                   goi.args))
    doi.update({k.arg: k.value for k in goi.keywords})
    assert isinstance(doi["san"], ast.Name) and doi["san"].id == "san_gd"
    gan = _gan_app(cay, "san_gd")
    assert len(gan) == 1
    bt = gan[0]
    assert isinstance(bt, ast.BoolOp) and isinstance(bt.op, ast.Or)
    assert len(bt.values) == 2
    tra, lui = bt.values
    assert (isinstance(tra, ast.Call) and isinstance(tra.func, ast.Attribute)
            and tra.func.attr == "tra_san"
            and [a.id for a in tra.args] == ["symbol"])
    assert isinstance(lui, ast.Name) and lui.id == "exchange"
    nhap, _ = _nhap_va_goi(GOC / "app.py")
    assert "san_giao_dich" in nhap


def test_APP_lam_tron_SL_xuong_TP_len_theo_buoc_gia_cua_san():
    """SL của risk agent làm tròn XUỐNG, TP làm tròn LÊN, bằng hai hàm của module;
    sổ vẫn lưu số chưa làm tròn (app chỉ làm tròn để HIỆN). Không sửa
    `analysis_agents.py` / `paper_trading.py`."""
    cay = ast.parse((GOC / "app.py").read_text(encoding="utf-8"))

    def _gan_goi(ten_bien, ten_ham):
        for v in _gan_app(cay, ten_bien):
            if (isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute)
                    and v.func.attr == ten_ham
                    and [getattr(a, "id", None) for a in v.args]
                    == [ten_bien, "san_gd"]):
                return True
        return False

    assert _gan_goi("est_stop_loss", "lam_tron_xuong")
    assert _gan_goi("est_tp", "lam_tron_len")
    src = (GOC / "app.py").read_text(encoding="utf-8")
    assert "low ≤ 63.486" in src and "high ≥ 81.480" in src   # chú thích vì sao đúng


def test_APP_bang_ke_hoach_co_cot_ngay_phan_quyet_va_hieu_luc_tu_phien_sau():
    cay = ast.parse((GOC / "app.py").read_text(encoding="utf-8"))
    khoa = {k.value for n in ast.walk(cay) if isinstance(n, ast.Dict)
            for k in n.keys
            if isinstance(k, ast.Constant) and isinstance(k.value, str)}
    assert "Ngày phán quyết" in khoa and "Hiệu lực" in khoa
    chuoi = " ".join(n.value for n in ast.walk(cay)
                     if isinstance(n, ast.Constant) and isinstance(n.value, str))
    assert "từ phiên sau" in chuoi and "đáy xoay" in chuoi
    # Ngày hiển thị dd/mm/yyyy.
    assert "%d/%m/%Y" in chuoi


def test_APP_khong_con_khuyen_nghi_theo_chuoi_va_nhanh_chet():
    """Bỏ "MUA 30%" và "MUA THĂM DÒ" (nhánh sau KHÔNG BAO GIỜ tới được: ngưỡng
    62 > 60 nên mọi điểm qua ngưỡng đã rơi vào `score >= 60.0`).

    Đọc bằng AST: hai chuỗi ấy còn nằm trong chú thích ghi lại lỗi cũ.
    """
    cay = ast.parse((GOC / "app.py").read_text(encoding="utf-8"))
    chuoi = [n.value for n in ast.walk(cay) if isinstance(n, ast.Constant)
             and isinstance(n.value, str)]
    for cam in ("MUA 30%", "MUA THĂM DÒ", "SẴN SÀNG GIẢI NGÂN"):
        assert not [c for c in chuoi if cam in c], cam
    # Không còn so `dyn_rec` với một CHUỖI (điều kiện bảng kế hoạch phải là so
    # điểm với ngưỡng).
    so_chuoi = [n.lineno for n in ast.walk(cay) if isinstance(n, ast.Compare)
                and isinstance(n.left, ast.Name) and n.left.id == "dyn_rec"
                and any(isinstance(c, ast.Constant) and isinstance(c.value, str)
                        for c in n.comparators)]
    assert not so_chuoi, f"app.py so dyn_rec với chuỗi ở dòng {so_chuoi}"
    # Nhãn đến từ bảng hiển thị của module, không gõ lại trong app.
    ten_dung = {n.attr for n in ast.walk(cay) if isinstance(n, ast.Attribute)
                and isinstance(n.value, ast.Name)
                and n.value.id == "_kh"}
    assert "HIEN_THI" in ten_dung


def test_APP_giu_cau_chu_thich_bat_buoc_va_nhanh_duoi_nguong():
    # Đọc các hằng chuỗi bằng AST: chuỗi dài bị ngắt dòng trong mã nguồn nhưng
    # trình phân tích đã nối lại thành MỘT hằng.
    cay = ast.parse((GOC / "app.py").read_text(encoding="utf-8"))
    chuoi = " ".join(n.value for n in ast.walk(cay)
                     if isinstance(n, ast.Constant) and isinstance(n.value, str))
    assert "CHỈ ĐỂ HIỆN và CHƯA ĐO" in chuoi
    assert "khớp ở giá mở cửa phiên sau" in chuoi
    assert "kể cả khi ở đây ghi CHỜ hay BỎ QUA" in chuoi
    # Sổ có cổng RIÊNG (VN-INDEX, chất lượng dữ liệu, mã đang giữ, trần vốn):
    # câu cũ "vẫn mở lệnh cho mọi mã đạt ngưỡng" sai mỗi ngày VN-INDEX dưới
    # MA50 (lỗi 146, leader soát PR #219).
    assert "KHÔNG làm theo" in chuoi and "cổng riêng của sổ" in chuoi
    assert "vẫn mở lệnh cho mọi mã đạt ngưỡng" not in chuoi
    assert "hai mức KHÁC nhau" in chuoi and "dùng mức theo ATR" in chuoi
    # Câu chú thích tả ĐÚNG luật cắt lỗ hiện hành (đáy xoay), không phải luật
    # cũ "dưới đáy 20 phiên" đã bỏ sau ca MSR (leader soát lượt sửa, 10/10).
    assert "dưới đáy xoay gần nhất trong" in chuoi
    assert "chưa kích hoạt mở vị thế mua" in chuoi          # nhánh dưới ngưỡng
