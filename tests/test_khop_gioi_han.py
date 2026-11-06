"""Gác cho `khop_gioi_han.py` (BƯỚC 257, Lát 4 của C1; `docs/thiet-ke-c1-san-dau.md` mục 7).

Mô hình khớp lệnh giới hạn MUA của ĐO 25 được chuyển ra một module thuần dùng chung. Ba điều phải giữ:
  1. định nghĩa khớp nghiêm (ngưỡng = trần trừ MỘT bước giá, giá khớp = min(mở, trần)) KHÔNG đổi một ô nào so với
     bản cũ ở `tools/do25_ke_hoach_vao_lenh.py` (`tests/test_do25_ke_hoach_vao_lenh.py` vẫn xanh không sửa);
  2. `tim_khop` (cả cửa sổ) và `khop_mot_phien` (từng phiên) là CÙNG một phép: bộ phát lại của sân đấu đi từng
     phiên qua `khop_mot_phien`, dụng cụ ĐO 25 đi cả cửa sổ qua `tim_khop`;
  3. module KHÔNG nhập `ke_hoach_vao_lenh` (chỉ ba nơi được nhập nó) nên `so_phien_cho` là tham số, và dụng cụ ĐO 25
     là nơi truyền `ke_hoach_vao_lenh.SO_PHIEN_CHO`.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import numpy as np
import pandas as pd

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.append(str(GOC / "tools"))

import khop_gioi_han as KG  # noqa: E402
import ke_hoach_vao_lenh as KH  # noqa: E402

DUONG = GOC / "khop_gioi_han.py"
DUONG_DO25 = GOC / "tools" / "do25_ke_hoach_vao_lenh.py"


def _cay(duong):
    return ast.parse(duong.read_text(encoding="utf-8"))


def _khung(dong):
    """DataFrame {time, open, low}: `dong` = {hàng: (mở, thấp)} (nghìn đồng), mặc định mở 30, thấp 30 (KHÔNG khớp)."""
    ra = pd.DataFrame({"time": [f"2026-10-{d:02d}" for d in range(1, 21)], "open": 30.0, "low": 30.0})
    for i, (mo, thap) in dong.items():
        ra.loc[i, "open"], ra.loc[i, "low"] = mo, thap
    return ra


# ── 1. khop_mot_phien: biên của định nghĩa ────────────────────────────────────────────────────
def test_khop_mot_phien_bien_thieu_mot_buoc_gia_HOSE_duoi_50k():
    """Trần 20.000, HOSE, bước 50 → ngưỡng 19.950: thấp 19.950 khớp, 19.951 không."""
    assert KG.khop_mot_phien(19980.0, 19950.0, 20000.0, "HOSE") == (True, 19980.0)
    assert KG.khop_mot_phien(19980.0, 19951.0, 20000.0, "HOSE") == (False, None)


def test_khop_mot_phien_buoc_gia_theo_SAN_va_theo_MUC_GIA_cua_tran():
    assert KG.khop_mot_phien(19980.0, 19950.0, 20000.0, "HNX")[0] is False       # HNX bước 100 → ngưỡng 19.900
    assert KG.khop_mot_phien(19980.0, 19900.0, 20000.0, "HNX")[0] is True
    assert KG.khop_mot_phien(59980.0, 59950.0, 60000.0, "HOSE")[0] is False      # HOSE trên 50k bước 100
    assert KG.khop_mot_phien(59980.0, 59900.0, 60000.0, "HOSE")[0] is True


def test_khop_mot_phien_gia_khop_la_min_mo_cua_tran__mo_cao_hon_tran_thi_khop_o_TRAN():
    assert KG.khop_mot_phien(20500.0, 19900.0, 20000.0, "HOSE") == (True, 20000.0)
    assert KG.khop_mot_phien(19900.0, 19900.0, 20000.0, "HOSE") == (True, 19900.0)


def test_khop_mot_phien_bien_the_cham_la_khop_chi_dung_trong_ham_va_khong_tru_buoc_gia():
    assert KG.khop_mot_phien(20200.0, 19960.0, 20000.0, "HOSE") == (False, None)
    assert KG.khop_mot_phien(20200.0, 19960.0, 20000.0, "HOSE", cham=True) == (True, 20000.0)
    assert KG.khop_mot_phien(20200.0, 20001.0, 20000.0, "HOSE", cham=True) == (False, None)


def test_khop_mot_phien_khong_nhieu_dau_phay_dong_o_bien():
    """16,1 × 1000 = 16100,000000000002 (đã đo): trần 16.150, bước 50 → ngưỡng 16.100 và thấp 16,1 PHẢI khớp."""
    assert 16.1 * 1000 != 16100.0
    assert KG.khop_mot_phien(16.12 * 1000, 16.1 * 1000, 16150.0, "HOSE") == (True, 16120.0)


# ── 2. tim_khop: cửa sổ ───────────────────────────────────────────────────────────────────────
def test_tim_khop_cua_so_la_t_cong_1_toi_t_cong_so_phien_cho__khong_gom_t():
    cuoi = (29.0, 28.9)       # mở 29, thấp 28,9 → khớp được ở trần 30.000
    t = 5
    for so, hang, mong in [(5, 5, None), (5, 6, 6), (5, 10, 10), (5, 11, None), (3, 8, 8), (3, 9, None)]:
        kq = KG.tim_khop(_khung({hang: cuoi}), t, 30000.0, "HOSE", 1000.0, so_phien_cho=so)
        assert (kq[0] if kq else None) == mong, (so, hang)


def test_tim_khop_bi_cat_o_hang_cuoi_cua_khung():
    df = _khung({}).iloc[:8]
    assert KG.tim_khop(df, 5, 30000.0, "HOSE", 1000.0, so_phien_cho=5) is None


def _tim_khop_cu(df, t, tran_vnd, san, he_so, cham, so_phien_cho):
    """Bản NGUYÊN VĂN của `tools/do25_ke_hoach_vao_lenh.tim_khop` trước BƯỚC 257 (cây `1811b37`), làm oracle."""
    import truot_gia
    nguong = tran_vnd if cham else tran_vnd - truot_gia.buoc_gia(tran_vnd, san)
    cuoi = min(t + so_phien_cho, len(df) - 1)
    for d in range(t + 1, cuoi + 1):
        if round(float(df["low"].iloc[d]) * he_so, 6) <= nguong:
            mo = round(float(df["open"].iloc[d]) * he_so, 6)
            return d, min(mo, float(tran_vnd))
    return None


def test_tim_khop_va_khop_mot_phien_la_cung_mot_phep__duyet_ngau_nhien_co_hat_giong():
    rng = np.random.default_rng(257)
    for _ in range(300):
        mo = np.round(rng.uniform(20, 70, 30), 1)
        thap = np.round(mo - rng.uniform(0, 1.5, 30), 1)
        df = pd.DataFrame({"open": mo, "low": thap})
        t = int(rng.integers(0, 20))
        tran = float(np.round(rng.uniform(20, 70), 1) * 1000)
        san = str(rng.choice(["HOSE", "HNX", "UPCOM"]))
        cham = bool(rng.integers(0, 2))
        kq = KG.tim_khop(df, t, tran, san, 1000.0, so_phien_cho=5, cham=cham)
        mong = None
        for d in range(t + 1, min(t + 5, len(df) - 1) + 1):
            khop, gia = KG.khop_mot_phien(mo[d] * 1000.0, thap[d] * 1000.0, tran, san, cham)
            if khop:
                mong = (d, gia)
                break
        assert kq == mong, (t, tran, san, cham)
        assert kq == _tim_khop_cu(df, t, tran, san, 1000.0, cham, 5), (t, tran, san, cham)


# ── 3. gác AST ────────────────────────────────────────────────────────────────────────────────
def _nhap(cay):
    ra = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            ra |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            ra.add((n.module or "").split(".")[0])
    return ra


def _goi(cay):
    ra = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Call):
            ra.add(n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", ""))
    return ra


def test_module_thuan_chi_nhap_truot_gia_va_KHONG_nhap_ke_hoach_vao_lenh():
    nhap = _nhap(_cay(DUONG))
    assert nhap <= {"__future__", "typing", "truot_gia"}, nhap
    assert "ke_hoach_vao_lenh" not in nhap
    assert not ({"now", "today", "now_vn", "today_vn", "read_csv", "urlopen", "request", "open", "sleep"}
                & _goi(_cay(DUONG)))


def test_do25_tim_khop_truyen_SO_PHIEN_CHO_cua_ke_hoach_vao_lenh_cho_khop_gioi_han():
    """Hình dạng lời gọi bằng AST: `KG.tim_khop(..., so_phien_cho=KH.SO_PHIEN_CHO, cham=cham)`. Gõ tay số 5 ở
    đây là cách để hai nơi trôi khỏi nhau."""
    cay = _cay(DUONG_DO25)
    ham = next(n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == "tim_khop")
    goi = [n for n in ast.walk(ham) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
           and n.func.attr == "tim_khop" and isinstance(n.func.value, ast.Name) and n.func.value.id == "KG"]
    assert len(goi) == 1
    kw = {k.arg: ast.unparse(k.value) for k in goi[0].keywords}
    assert kw == {"so_phien_cho": "KH.SO_PHIEN_CHO", "cham": "cham"}, kw


def test_bon_phan_quyet_bang_ke_hoach_vao_lenh():
    assert (KG.MUA_NGAY, KG.CHO_VUNG, KG.BO_QUA, KG.CHUA_LAP_DUOC) == (
        KH.MUA_NGAY, KH.CHO_VUNG, KH.BO_QUA, KH.CHUA_LAP_DUOC)
    assert set(KG.PHAN_QUYET) == {KH.MUA_NGAY, KH.CHO_VUNG, KH.BO_QUA, KH.CHUA_LAP_DUOC}


def test_do25_van_xuat_ten_tim_khop_va_cho_ra_cung_ket_qua():
    import do25_ke_hoach_vao_lenh as D
    df = _khung({7: (29.98, 29.95)})
    assert D.tim_khop(df, 5, 30000.0, "HOSE", 1000.0) == KG.tim_khop(
        df, 5, 30000.0, "HOSE", 1000.0, so_phien_cho=KH.SO_PHIEN_CHO)
    assert D.tim_khop(df, 5, 30000.0, "HOSE", 1000.0)[0] == 7
