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
  · AST — ai được nhập, app gọi đúng, hình dạng biểu thức vùng.

Mọi test offline, dữ liệu giả. Không cần vnstock.

Dựng ca: `_nen(c0, cao, thap, cuoi)` = 29 nến giống nhau (mở = đóng = c0,
cao, thấp) rồi MỘT nến cuối tuỳ ý (mở, cao, thấp, đóng). Với nến nền như vậy
true range của nền = cao − thấp (giá đóng trước = c0 nằm trong [thấp, cao]).
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
GAN_DUNG = pytest.approx


# ─────────────────────────────────────────────────────────────────────
# Dựng dữ liệu giả
# ─────────────────────────────────────────────────────────────────────

def _nen(c0, cao, thap, cuoi, n=30, bat_dau="2026-03-02"):
    """n−1 nến nền (mở = đóng = c0) + nến cuối (mở, cao, thấp, đóng)."""
    ngay = pd.date_range(bat_dau, periods=n, freq="B").strftime("%Y-%m-%d")
    dong = [(c0, cao, thap, c0, 1000.0)] * (n - 1) + [tuple(cuoi) + (1000.0,)]
    return pd.DataFrame(dong, columns=["open", "high", "low", "close",
                                       "volume"]).assign(time=ngay)


def _lap(df, he=1.0, diem=DIEM, nguong=NGUONG, bay_gio=XA):
    return kh.lap_ke_hoach(df, he, diem, nguong, bay_gio)


# Sáu ca tay, dùng lại nhiều nơi. Mỗi ca ghi phép tính ở chú thích.

def ca_mua_ngay():
    """Nền: mở=đóng=100, cao 101, thấp 96,5. Nến cuối: 100 / 101 / 96,5 / 100.

    true range mọi nến = 101 − 96,5 = 4,5            → ATR14 = 4,5
    MA20 = 100                                       → kéo giãn k = 0
    đáy 20 phiên = 96,5 → cắt lỗ s = 96,5 − 0,5×4,5 = 94,25
    rủi ro r = (100 − 94,25)/100 = 5,75%  (trong [4%; 6,5%])
    trần ngân sách = 94,25/0,935 = 100,8021 ≥ 100   → MUA_NGAY
    """
    return _nen(100.0, 101.0, 96.5, (100.0, 101.0, 96.5, 100.0))


def ca_mua_ngay_cat_lo_sat():
    """Nền 100 / 101 / 99. Nến cuối y hệt.

    true range = 2 → ATR = 2 ; MA20 = 100 ; k = 0
    đáy = 99 → s = 99 − 0,5×2 = 98 ; r = (100 − 98)/100 = 2% < 4%
    trần ngân sách = 98/0,935 = 104,81 ≥ 100 → MUA_NGAY, kèm lý do "sát hơn".
    """
    return _nen(100.0, 101.0, 99.0, (100.0, 101.0, 99.0, 100.0))


def ca_cho_vung_do_rui_ro():
    """Như ca_mua_ngay nhưng nến cuối đóng 101 (cao 101).

    ATR = 4,5 ; MA20 = (19×100 + 101)/20 = 100,05 ; k = 0,95/4,5 = 0,2111
    s = 94,25 ; r = (101 − 94,25)/101 = 6,683% > 6,5%
    trần ngân sách = 94,25/0,935 = 100,8021 < 101           → trượt vì RỦI RO
    trần kéo giãn = 100,05 + 2×4,5 = 109,05
    đáy vùng = 94,25/0,96 = 98,1771
    vùng = [98,1771 ; min(100,8021 ; 109,05)] = [98,1771 ; 100,8021]
    """
    return _nen(100.0, 101.0, 96.5, (100.0, 101.0, 96.5, 101.0))


def ca_cho_vung_do_keo_gian():
    """Nền 100 / 102 / 100. Nến cuối 100 / 105 / 100 / 105.

    true range nền = 2 ; nến cuối = max(5 ; |105−100| ; 0) = 5
    ATR = (13×2 + 5)/14 = 31/14 = 2,2143
    MA20 = (19×100 + 105)/20 = 100,25 ; k = 4,75/2,2143 = 2,1452 > 2
    đáy = 100 → s = 100 − 31/28 = 98,8929 ; r = (105 − 98,8929)/105 = 5,816%
    trần ngân sách = 98,8929/0,935 = 105,768 ≥ 105 → KHÔNG trượt vì rủi ro
    trần kéo giãn = 100,25 + 2×31/14 = 104,6786
    đáy vùng = 98,8929/0,96 = 103,0134
    vùng = [103,0134 ; min(105,768 ; 104,6786)] = [103,0134 ; 104,6786]
    """
    return _nen(100.0, 102.0, 100.0, (100.0, 105.0, 100.0, 105.0))


def ca_cho_vung_do_ca_hai():
    """Nền 100 / 101 / 99. Nến cuối 100 / 106 / 100 / 106.

    true range nền = 2 ; nến cuối = max(6 ; 6 ; 0) = 6
    ATR = (13×2 + 6)/14 = 32/14 = 2,2857 ; MA20 = (1900 + 106)/20 = 100,3
    k = 5,7/2,2857 = 2,4938 > 2
    đáy = 99 → s = 99 − 32/28 = 97,8571 ; r = (106 − 97,8571)/106 = 7,682% > 6,5%
    trần ngân sách = 97,8571/0,935 = 104,6600 ; trần kéo giãn = 100,3 + 4,5714
    = 104,8714 ; đáy vùng = 97,8571/0,96 = 101,9345
    vùng = [101,9345 ; min(104,66 ; 104,8714)] = [101,9345 ; 104,6600]
    """
    return _nen(100.0, 101.0, 99.0, (100.0, 106.0, 100.0, 106.0))


def ca_bo_qua_khong_co_vung():
    """Nền 100 / 100,5 / 99,5. Nến cuối 100 / 104 / 100 / 104.

    true range nền = 1 ; nến cuối = max(4 ; 4 ; 0) = 4
    ATR = (13×1 + 4)/14 = 17/14 = 1,2143 ; MA20 = (1900 + 104)/20 = 100,2
    k = 3,8/1,2143 = 3,1294 > 2
    đáy = 99,5 → s = 99,5 − 17/28 = 98,8929 ; r = 4,911% (không trượt rủi ro)
    trần kéo giãn = 100,2 + 2×17/14 = 102,6286
    đáy vùng = 98,8929/0,96 = 103,0134 > 102,6286 → trần vùng < đáy vùng.
    """
    return _nen(100.0, 100.5, 99.5, (100.0, 104.0, 100.0, 104.0))


# ─────────────────────────────────────────────────────────────────────
# KHONG_XET · ngưỡng
# ─────────────────────────────────────────────────────────────────────

def test_KHONG_XET_duoi_nguong_khong_tinh_gi_them():
    p = _lap(ca_mua_ngay(), diem=61.9)
    assert p.phan_quyet == kh.KHONG_XET
    assert p.ly_do == ("điểm 61.9 dưới ngưỡng 62 — chưa phải ứng viên",)
    for ten in ("ngay", "gia_dong", "atr", "ma20", "keo_gian_atr",
                "cat_lo_cau_truc", "rui_ro_pct", "vung", "so_phien_cho"):
        assert getattr(p, ten) is None, ten


def test_diem_BANG_nguong_thi_duoc_xet():
    """Biên: 62 vào 62 là ứng viên (như `consider_entry`: chỉ bỏ khi < ngưỡng)."""
    assert _lap(ca_mua_ngay(), diem=62.0).phan_quyet == kh.MUA_NGAY
    assert _lap(ca_mua_ngay(), diem=61.99).phan_quyet == kh.KHONG_XET


def test_nguong_la_tham_so_bat_buoc_khong_co_mac_dinh():
    cay = ast.parse((GOC / "ke_hoach_vao_lenh.py").read_text(encoding="utf-8"))
    ham = next(n for n in cay.body if isinstance(n, ast.FunctionDef)
               and n.name == "lap_ke_hoach")
    assert ham.args.defaults == [] and ham.args.kw_defaults == []
    assert [a.arg for a in ham.args.args] == [
        "df", "he_so_gia", "diem", "nguong", "bay_gio"]


def test_phep_so_ngưỡng_la_diem_nho_hon_nguong__kiem_hinh_dang_bang_AST():
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
    thieu = _lap(_nen(100.0, 101.0, 96.5, (100.0, 101.0, 96.5, 100.0),
                      n=n_can - 1))
    assert thieu.phan_quyet == kh.CHUA_LAP_DUOC
    assert f"chỉ có {n_can - 1} nến" in thieu.ly_do[0]
    du = _lap(_nen(100.0, 101.0, 96.5, (100.0, 101.0, 96.5, 100.0), n=n_can))
    assert du.phan_quyet == kh.MUA_NGAY


def test_CHUA_LAP_DUOC_ATR_bang_0():
    phang = _nen(100.0, 100.0, 100.0, (100.0, 100.0, 100.0, 100.0))
    p = _lap(phang)
    assert p.phan_quyet == kh.CHUA_LAP_DUOC and "ATR" in p.ly_do[0]


def test_CHUA_LAP_DUOC_cat_lo_khong_duong():
    """Nền 5 / 9 / 1: ATR = 8 ; đáy 1 → s = 1 − 4 = −3 ≤ 0."""
    p = _lap(_nen(5.0, 9.0, 1.0, (5.0, 9.0, 1.0, 5.0)))
    assert p.phan_quyet == kh.CHUA_LAP_DUOC
    assert "cắt lỗ" in p.ly_do[0]


@pytest.mark.parametrize("df", [None, pd.DataFrame(),
                                pd.DataFrame({"close": [1.0] * 40})])
def test_CHUA_LAP_DUOC_df_hong(df):
    assert _lap(df).phan_quyet == kh.CHUA_LAP_DUOC


def test_CHUA_LAP_DUOC_diem_khong_doc_duoc():
    assert _lap(ca_mua_ngay(), diem=float("nan")).phan_quyet == kh.CHUA_LAP_DUOC
    assert _lap(ca_mua_ngay(), diem=None).phan_quyet == kh.CHUA_LAP_DUOC


# ─────────────────────────────────────────────────────────────────────
# MUA_NGAY · CHO_VUNG · BO_QUA — số tính tay
# ─────────────────────────────────────────────────────────────────────

def test_MUA_NGAY_so_tinh_tay():
    p = _lap(ca_mua_ngay())
    assert p.phan_quyet == kh.MUA_NGAY
    assert p.ngay == "2026-04-10"
    assert p.gia_dong == 100.0
    assert p.atr == GAN_DUNG(4.5)
    assert p.ma20 == GAN_DUNG(100.0)
    assert p.keo_gian_atr == GAN_DUNG(0.0, abs=1e-12)
    assert p.cat_lo_cau_truc == GAN_DUNG(94.25)
    assert p.rui_ro_pct == GAN_DUNG(5.75)
    assert p.vung is None and p.so_phien_cho is None
    assert len(p.ly_do) == 1 and "sát hơn" not in p.ly_do[0]


def test_MUA_NGAY_cat_lo_sat_hon_bien_duoi_thi_them_ly_do():
    p = _lap(ca_mua_ngay_cat_lo_sat())
    assert p.phan_quyet == kh.MUA_NGAY
    assert p.cat_lo_cau_truc == GAN_DUNG(98.0)
    assert p.rui_ro_pct == GAN_DUNG(2.0)
    assert len(p.ly_do) == 2
    assert "sát hơn biên dưới ngân sách rủi ro" in p.ly_do[1]


def test_CHO_VUNG_do_rui_ro_so_tinh_tay():
    p = _lap(ca_cho_vung_do_rui_ro())
    assert p.phan_quyet == kh.CHO_VUNG
    assert p.atr == GAN_DUNG(4.5)
    assert p.ma20 == GAN_DUNG(100.05)
    assert p.keo_gian_atr == GAN_DUNG(0.95 / 4.5)
    assert p.cat_lo_cau_truc == GAN_DUNG(94.25)
    assert p.rui_ro_pct == GAN_DUNG(6.683168, rel=1e-6)
    assert p.vung == (GAN_DUNG(98.177083, rel=1e-7),
                      GAN_DUNG(100.802139, rel=1e-7))
    assert p.so_phien_cho == kh.SO_PHIEN_CHO == 5
    # Chỉ trượt vì RỦI RO: lý do nêu rủi ro, KHÔNG nêu kéo giãn.
    assert len(p.ly_do) == 1
    assert "rủi ro 6.7% vượt 6.5%" in p.ly_do[0]


def test_CHO_VUNG_do_keo_gian_so_tinh_tay():
    p = _lap(ca_cho_vung_do_keo_gian())
    assert p.phan_quyet == kh.CHO_VUNG
    assert p.atr == GAN_DUNG(31 / 14)
    assert p.ma20 == GAN_DUNG(100.25)
    assert p.keo_gian_atr == GAN_DUNG(4.75 / (31 / 14))
    assert p.keo_gian_atr == GAN_DUNG(2.14516, rel=1e-5)
    assert p.cat_lo_cau_truc == GAN_DUNG(100.0 - 31 / 28)
    assert p.rui_ro_pct == GAN_DUNG(5.81633, rel=1e-5)
    assert p.vung == (GAN_DUNG(103.013393, rel=1e-7),
                      GAN_DUNG(104.678571, rel=1e-7))
    # Chỉ trượt vì KÉO GIÃN.
    assert len(p.ly_do) == 1
    assert "2.1 ATR, vượt 2 ATR" in p.ly_do[0] and "rủi ro" not in p.ly_do[0]


def test_CHO_VUNG_do_ca_hai_dieu_kien_thi_ly_do_nen_ca_hai():
    p = _lap(ca_cho_vung_do_ca_hai())
    assert p.phan_quyet == kh.CHO_VUNG
    assert p.vung == (GAN_DUNG(101.934524, rel=1e-7),
                      GAN_DUNG(104.660046, rel=1e-7))
    assert len(p.ly_do) == 2
    assert "rủi ro 7.7% vượt 6.5%" in p.ly_do[0]
    assert "2.5 ATR, vượt 2 ATR" in p.ly_do[1]


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
    assert p.keo_gian_atr == GAN_DUNG(3.12941, rel=1e-5)
    assert p.rui_ro_pct == GAN_DUNG(4.91071, rel=1e-5)
    assert p.ly_do[-1] == ("không có giá nào vừa cả ngân sách rủi ro lẫn độ "
                           "kéo giãn")
    assert "3.1 ATR, vượt 2 ATR" in p.ly_do[0]


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

    Chính cây nến cuối ấy KHÔNG trượt điều kiện nào (rủi ro 3,4% — sát hơn
    biên dưới, kéo giãn 0,33 ATR) nên nếu bỏ nhánh Wyckoff thì nó là MUA_NGAY:
    bước 2 dưới đây chứng minh chính Wyckoff đổi phán quyết.
    """
    df = _phan_phoi_utad()
    assert pha_wyckoff.doc_pha(df).huong == pha_wyckoff.GIAM
    p = _lap(df)
    assert p.phan_quyet == kh.BO_QUA
    assert p.ly_do == ("cấu trúc Wyckoff hướng giảm: Pha C — UTAD",)
    assert p.ngay == "2025-05-20" and p.gia_dong == 104.0
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
    assert len(p.ly_do) == 3
    assert p.ly_do[0].startswith("cấu trúc Wyckoff hướng giảm")
    assert "rủi ro" in p.ly_do[1] and "ATR, vượt" in p.ly_do[2]


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
    assert p.atr == GAN_DUNG(tham_chieu["ATR"], rel=1e-12)
    # ...và MA20 của module là SMA(20) của chính cột đóng cửa.
    assert p.ma20 == GAN_DUNG(df["close"].tail(20).mean(), rel=1e-12)


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
    """Bảng nghìn đồng + `he_so_gia`=1000 cho cùng kế hoạch như bảng VNĐ."""
    vnd = _lap(ca_cho_vung_do_rui_ro())
    nghin = ca_cho_vung_do_rui_ro()
    for c in ("open", "high", "low", "close"):
        nghin[c] = nghin[c] / 1000.0
    p = _lap(nghin, he=1000.0)
    assert p.phan_quyet == vnd.phan_quyet
    for ten in ("gia_dong", "atr", "ma20", "cat_lo_cau_truc"):
        assert getattr(p, ten) == GAN_DUNG(getattr(vnd, ten), rel=1e-9)
    assert p.vung == (GAN_DUNG(vnd.vung[0], rel=1e-9),
                      GAN_DUNG(vnd.vung[1], rel=1e-9))
    assert p.keo_gian_atr == GAN_DUNG(vnd.keo_gian_atr, rel=1e-9)
    assert p.rui_ro_pct == GAN_DUNG(vnd.rui_ro_pct, rel=1e-9)


def _nen_co_dinh(chi_so_dinh):
    """Nền 100 / 101 / 99 (30 nến, ATR = 2, MA20 = 100) với MỘT nến có đáy 90.

    Nến đáy 90 nằm ở chỉ số `chi_so_dinh`. Chỉ số 10 = nến thứ 20 tính từ cuối
    (còn TRONG cửa sổ 20 phiên: 10..29); chỉ số 9 là nến thứ 21 (NGOÀI cửa sổ).
    Cả hai đều ngoài 14 nến cuối của ATR nên ATR vẫn bằng 2, MA20 vẫn bằng 100.
    """
    df = ca_mua_ngay_cat_lo_sat()
    df.loc[chi_so_dinh, "low"] = 90.0
    return df


def test_cua_so_day_la_20_phien_bien_trong_va_ngoai():
    """Biên của cửa sổ đáy: nến thứ 20 tính từ cuối được tính, thứ 21 thì không.

    Trong: đáy 90 → s = 90 − 0,5×2 = 89 ; r = (100 − 89)/100 = 11%.
    Ngoài: đáy 90 bị bỏ → s = 99 − 0,5×2 = 98 (như ca_mua_ngay_cat_lo_sat).
    """
    trong = _lap(_nen_co_dinh(10))
    assert trong.cat_lo_cau_truc == GAN_DUNG(89.0)
    assert trong.rui_ro_pct == GAN_DUNG(11.0)
    ngoai = _lap(_nen_co_dinh(9))
    assert ngoai.cat_lo_cau_truc == GAN_DUNG(98.0)
    assert ngoai.phan_quyet == kh.MUA_NGAY


def test_gia_xa_DUOI_MA20_khong_bi_coi_la_keo_gian():
    """Kéo giãn có DẤU: giá dưới MA20 hơn 2 ATR không phải "chạy xa lên".

    Nền 100 / 101 / 99 ; nến cuối 100 / 100 / 93 / 94.
    true range nến cuối = max(7 ; |100−100| ; |93−100|) = 7
    ATR = (13×2 + 7)/14 = 33/14 ; MA20 = (1900 + 94)/20 = 99,7
    k = (94 − 99,7)/(33/14) = −2,418 → không vượt +2 → vẫn xét theo rủi ro
    đáy = 93 → s = 93 − 33/28 = 91,8214 ; r = 2,318% ≤ 6,5% → MUA_NGAY.
    """
    p = _lap(_nen(100.0, 101.0, 99.0, (100.0, 100.0, 93.0, 94.0)))
    assert p.keo_gian_atr == GAN_DUNG(-5.7 * 14 / 33)
    assert p.phan_quyet == kh.MUA_NGAY


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
              p.rui_ro_pct, *p.vung):
        assert math.isfinite(x)


# ─────────────────────────────────────────────────────────────────────
# AST — hình dạng biểu thức vùng
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


def test_tran_vung_la_MIN_cua_hai_tran_va_ma_tran_keo_gian_theo_ten():
    cay, ham = _ham_lap()
    tv = _gan(ham, "tran_vung")
    assert (isinstance(tv, ast.Call) and tv.func.id == "min"
            and [a.id for a in tv.args] == ["tran_ngan_sach", "tran_keo_gian"])
    tk = _gan(ham, "tran_keo_gian")
    assert (isinstance(tk, ast.BinOp) and isinstance(tk.op, ast.Add)
            and {n.id for n in ast.walk(tk) if isinstance(n, ast.Name)}
            == {"ma20", "KEO_GIAN_TOI_DA_ATR", "atr"})


def test_hang_so_de_xuat_deu_duoc_danh_dau_CHUA_DO():
    src = (GOC / "ke_hoach_vao_lenh.py").read_text(encoding="utf-8")
    assert "ĐỀ XUẤT, CHƯA ĐO" in src
    assert "bất biến 7" in src


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
                    "data_quality", "pha_wyckoff", "muc_fibonacci"}, nhap
    # Hàm thuần: không đồng hồ, không mạng.
    assert not ({"now", "today", "now_vn", "today_vn", "read_csv", "get",
                 "request", "urlopen"} & goi), goi
    assert "nen_cuoi_dang_do" in goi and "doc_pha" in goi


def test_APP_goi_lap_ke_hoach_voi_BUY_THRESHOLD_va_cung_bay_gio_voi_gop_nen():
    cay = ast.parse((GOC / "app.py").read_text(encoding="utf-8"))
    nhap, _ = _nhap_va_goi(GOC / "app.py")
    assert "ke_hoach_vao_lenh" in nhap

    def _goi(ten):
        return [n for n in ast.walk(cay) if isinstance(n, ast.Call)
                and ((isinstance(n.func, ast.Attribute) and n.func.attr == ten)
                     or (isinstance(n.func, ast.Name) and n.func.id == ten))]

    lenh = _goi("lap_ke_hoach")
    assert len(lenh) == 1, "app phải lập kế hoạch ĐÚNG MỘT lần"
    goi = lenh[0]
    ten_doi = ("df", "he_so_gia", "diem", "nguong", "bay_gio")
    doi = dict(zip(ten_doi, goi.args))
    doi.update({k.arg: k.value for k in goi.keywords})
    assert set(doi) == set(ten_doi)
    # Ngưỡng là TÊN `BUY_THRESHOLD`, không phải một con số.
    assert isinstance(doi["nguong"], ast.Name)
    assert doi["nguong"].id == "BUY_THRESHOLD"
    assert isinstance(doi["he_so_gia"], ast.Name) and doi["he_so_gia"].id == "mult"
    assert isinstance(doi["diem"], ast.Name) and doi["diem"].id == "score"
    # CÙNG `bay_gio` với lời gọi `_nen_ba_khung(...)` (đưa vào `gop_nen`).
    ba_khung = [g for g in _goi("_nen_ba_khung")]
    assert ba_khung
    assert any(ast.dump(doi["bay_gio"]) == ast.dump(g.args[2])
               for g in ba_khung), "bay_gio khác với bay_gio đưa vào gop_nen"


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
    assert "hai mức KHÁC nhau" in chuoi and "dùng mức theo ATR" in chuoi
    assert "chưa kích hoạt mở vị thế mua" in chuoi          # nhánh dưới ngưỡng
