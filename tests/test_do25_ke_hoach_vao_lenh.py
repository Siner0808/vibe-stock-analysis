"""Gác của `tools/do25_ke_hoach_vao_lenh.py` (ĐO 25) — dữ liệu TỔNG HỢP, không chạm cache thật.

Tiêu chí ký trước: `docs/TIEU-CHI-DOC-TRUOC.md`, mục *ĐO 25*. Máy đo bị nghi như một gác: mọi đáp
số ở đây là SỐ TÍNH TAY (phép tính ghi ở chú thích từng ca), không dựng lại công thức của mã.

Bốn đột biến leader yêu cầu — mỗi cái có ca riêng:
  1. khớp khi low ≤ trần (bỏ "− MỘT bước giá")      → `test_TIM_KHOP_*`
  2. lệnh lỡ bị LOẠI khỏi quần thể thay vì alpha 0   → `test_CHENH_*`
  3. nền dùng close t thay vì open t+1               → `test_BAN_GHI_nen_*`
  4. bootstrap theo dòng thay vì theo khối ngày      → `test_BOOTSTRAP_*`
"""
from __future__ import annotations

import ast
import contextlib
import datetime
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))
sys.path.insert(0, str(GOC))

import do25_ke_hoach_vao_lenh as D  # noqa: E402

KH = D.KH
CHO, MUA, BO = KH.CHO_VUNG, KH.MUA_NGAY, KH.BO_QUA


# ── dựng dữ liệu ─────────────────────────────────────────────────────────────────────────────
def bang(n=30, gia=21.0, doi=None):
    """Bảng OHLCV phẳng ở `gia` (nghìn đồng); `doi` = {chỉ số hàng: (o, h, l, c)}."""
    ngay = pd.bdate_range("2022-01-03", periods=n).strftime("%Y-%m-%d")
    hang = [(gia, gia, gia, gia)] * n
    for i, h in (doi or {}).items():
        hang[i] = h
    o, h, l, c = zip(*hang)
    return pd.DataFrame({"time": ngay, "open": o, "high": h, "low": l, "close": c,
                         "volume": [1e5] * n})


def the_gioi(doi_them=None):
    """Thế giới của các ca tính tay. Tín hiệu ở t = 5; ra ở t + 20 = 25.

    gia nền 21,0 nghìn đồng; hàng 6 mở 21,10 (không chạm vùng); hàng 25 đóng 23,1 (= +10% so
    với 21,0). Khớp vùng chờ (trần 20.000) CHỈ xảy ra ở hàng mà `doi_them` hạ low xuống.
    """
    doi = {6: (21.10, 21.5, 20.9, 21.0), 25: (23.1, 23.1, 23.1, 23.1)}
    doi.update(doi_them or {})
    return bang(30, 21.0, doi)


def ke_hoach(phan_quyet, vung=None):
    return KH._ket(phan_quyet, ["x"], "x", vung=vung)


def chuan_b():
    """Mã chuẩn B: phẳng 10,0, hàng 25 đóng 11,0 (+10%)."""
    return bang(30, 10.0, {25: (11.0, 11.0, 11.0, 11.0)})


# ── M0: hằng số ký trước ────────────────────────────────────────────────────────────────────
def test_HANG_SO_DA_KY_ghim_bang_SO_VIET_THANG():
    """Đổi một con số nào ở đây là đổi tiêu chí đã ký — phải khai ĐO mới (bất biến 7)."""
    assert D.KHUNG_H == 20
    assert D.SO_LUOT_BOOTSTRAP == 10_000
    assert D.HAT_BOOTSTRAP == 20261010
    assert D.NGUONG_DA_KY == 62
    assert D.NGUONG_QUY_TAC_1 == 2.0
    assert D.COMMIT_KE_HOACH == "d44cc87"
    assert D.PM.N_TOI_THIEU == 113
    assert D.PM.ROUND_TRIP_COST_PCT == pytest.approx(0.46)
    assert D.PT.BUY_THRESHOLD == 62
    print("PASS  hằng số ĐO 25 ghim")


def test_HANG_SO_B6_ghim_dung_nhu_o_commit_d44cc87():
    """Tám hằng số của `ke_hoach_vao_lenh` mà ĐO 25 khai GHIM. Đỏ ở đây = hằng số B6 đã đổi,
    tức phép đo không còn đo cái đã ký."""
    assert KH.CUA_SO_DAY == 20
    assert KH.SO_PHIEN_XAC_NHAN_DAY == 2
    assert KH.HE_SO_DEM_ATR == 0.5
    assert KH.KEO_GIAN_TOI_DA_ATR == 2.0
    assert KH.LUI_TOI_DA_ATR == 2.0
    assert KH.SO_PHIEN_CHO == 5
    assert KH.SL_HEP_NHAT == 0.04
    assert KH.SL_RONG_NHAT == 0.065


def test_MAC_DINH_lay_tu_walkforward_chay_khong_go_lai():
    assert D.mac_dinh_walkforward() == {"stride": 2, "min_history": 60, "che_do_hoc": "co_san"}


# ── mô phỏng khớp ───────────────────────────────────────────────────────────────────────────
def test_TIM_KHOP_low_dung_bang_tran_KHONG_khop__thieu_mot_buoc_thi_khop():
    """Trần 20.000, HOSE, bước giá 50 → ngưỡng khớp 19.950.

    low 19,96 → 19.960 > 19.950: không khớp (ĐỘT BIẾN 1 'low ≤ trần' sẽ khớp).
    low 19,95 → 19.950 ≤ 19.950: khớp. Giá khớp = min(mở 19.980, trần 20.000) = 19.980.
    """
    df = the_gioi({7: (19.98, 21.0, 19.96, 21.0)})
    assert D.tim_khop(df, 5, 20000.0, "HOSE", 1000.0) is None
    df = the_gioi({7: (19.98, 21.0, 19.95, 21.0)})
    assert D.tim_khop(df, 5, 20000.0, "HOSE", 1000.0) == (7, 19980.0)


def test_TIM_KHOP_bien_the_cham_la_khop_khop_ngay_khi_low_le_tran():
    df = the_gioi({7: (20.2, 21.0, 19.96, 21.0)})
    assert D.tim_khop(df, 5, 20000.0, "HOSE", 1000.0) is None
    # mở 20.200 > trần: giá khớp bị chặn ở trần 20.000
    assert D.tim_khop(df, 5, 20000.0, "HOSE", 1000.0, cham=True) == (7, 20000.0)


def test_TIM_KHOP_mo_cua_cao_hon_tran_thi_khop_o_TRAN():
    df = the_gioi({8: (20.5, 21.0, 19.9, 21.0)})   # mở 20.500, low 19.900 ≤ 19.950
    assert D.tim_khop(df, 5, 20000.0, "HOSE", 1000.0) == (8, 20000.0)


def test_TIM_KHOP_phien_dau_tien_thang():
    df = the_gioi({7: (19.98, 21.0, 19.95, 21.0), 8: (19.0, 21.0, 18.9, 21.0)})
    assert D.tim_khop(df, 5, 20000.0, "HOSE", 1000.0) == (7, 19980.0)


def test_TIM_KHOP_cua_so_la_t_cong_1_toi_t_cong_5__khong_gom_t_va_khong_qua_t_cong_5():
    cuoi = (19.0, 21.0, 18.9, 21.0)
    assert D.tim_khop(the_gioi({5: cuoi}), 5, 20000.0, "HOSE", 1000.0) is None   # chính ngày t
    assert D.tim_khop(the_gioi({10: cuoi}), 5, 20000.0, "HOSE", 1000.0) is not None   # t + 5
    assert D.tim_khop(the_gioi({11: cuoi}), 5, 20000.0, "HOSE", 1000.0) is None   # t + 6


def test_TIM_KHOP_buoc_gia_theo_SAN_va_theo_MUC_GIA_cua_tran():
    # HNX bước 100: trần 20.000 → ngưỡng 19.900. low 19.950 không khớp, 19.900 khớp.
    assert D.tim_khop(the_gioi({7: (19.98, 21.0, 19.95, 21.0)}), 5, 20000.0, "HNX", 1000.0) is None
    assert D.tim_khop(the_gioi({7: (19.98, 21.0, 19.90, 21.0)}), 5, 20000.0, "HNX", 1000.0) is not None
    # HOSE trên 50.000 bước 100: trần 60.000 → ngưỡng 59.900.
    doi = lambda low: bang(30, 61.0, {7: (59.98, 61.0, low, 61.0)})  # noqa: E731
    assert D.tim_khop(doi(59.95), 5, 60000.0, "HOSE", 1000.0) is None
    assert D.tim_khop(doi(59.90), 5, 60000.0, "HOSE", 1000.0) is not None


def test_TIM_KHOP_khong_nhieu_dau_phay_dong_o_bien():
    """16,1 × 1000 = 16100,000000000002 trong số thực (đã đo). Trần 16.150, bước 50 → ngưỡng 16.100:
    low 16,1 PHẢI khớp. Không làm tròn trước khi so thì 16100,000000000002 > 16100 → lỡ oan."""
    assert 16.1 * 1000 != 16100.0
    df = the_gioi({7: (16.12, 21.0, 16.1, 21.0)})
    assert D.tim_khop(df, 5, 16150.0, "HOSE", 1000.0) == (7, 16120.0)


# ── bản ghi một tín hiệu ────────────────────────────────────────────────────────────────────
def test_BAN_GHI_nen_mua_o_MO_CUA_t_cong_1_va_ra_o_DONG_CUA_t_cong_20():
    """Hàng 6 mở 21,10 → vào 21.100 (đột biến 3 'close t' sẽ ra 21.000). Hàng 25 đóng 23,1 → ra
    23.100. Hàng 24 đóng 21,0: đột biến 't + H − 1' sẽ ra 21.000."""
    df = the_gioi()
    b = D.ban_ghi_tin_hieu("AAA", df, 5, 70.0, "HOSE", ke_hoach(MUA))
    n = b["lenh_nen"]
    assert (n.entry_price, n.exit_price) == (21100.0, 23100.0)
    assert (n.entry_date, n.exit_date) == (df["time"].iloc[6], df["time"].iloc[25])
    assert b["lenh_khop"] is None and b["lenh_cham"] is None
    assert b["phan_quyet"] == MUA and b["ma"] == "AAA" and b["ngay"] == df["time"].iloc[5]


def test_BAN_GHI_du_tuong_lai_o_BIEN_t_cong_20_bang_chi_so_cuoi():
    df = the_gioi()   # 30 hàng, chỉ số cuối 29
    assert D.ban_ghi_tin_hieu("A", df, 9, 70.0, "HOSE", ke_hoach(MUA)) is not None   # 9 + 20 = 29
    assert D.ban_ghi_tin_hieu("A", df, 10, 70.0, "HOSE", ke_hoach(MUA)) is None      # 30 > 29


def test_BAN_GHI_cho_vung_khop_vao_gia_khop_va_ra_cung_ngay_voi_nen():
    df = the_gioi({7: (19.98, 21.0, 19.95, 21.0)})
    b = D.ban_ghi_tin_hieu("AAA", df, 5, 70.0, "HOSE", ke_hoach(CHO, (19500.0, 20000.0)))
    k = b["lenh_khop"]
    assert (k.entry_price, k.entry_date) == (19980.0, df["time"].iloc[7])
    assert (k.exit_price, k.exit_date) == (23100.0, df["time"].iloc[25])
    assert b["lenh_cham"].entry_price == 19980.0


def test_BAN_GHI_cho_vung_khong_khop_nghiem_nhung_khop_neu_cham():
    df = the_gioi({7: (20.2, 21.0, 19.96, 21.0)})
    b = D.ban_ghi_tin_hieu("AAA", df, 5, 70.0, "HOSE", ke_hoach(CHO, (19500.0, 20000.0)))
    assert b["lenh_khop"] is None
    assert b["lenh_cham"].entry_price == 20000.0


def test_BAN_GHI_trần_vung_lay_o_PHAN_TU_THU_HAI_cua_vung():
    """`vung` = (đáy, trần). Lệnh giới hạn ở TRẦN (20.000), không ở đáy (19.500): low 19.95 khớp
    ở trần nhưng sẽ không bao giờ khớp ở đáy."""
    df = the_gioi({7: (19.98, 21.0, 19.95, 21.0)})
    b = D.ban_ghi_tin_hieu("A", df, 5, 70.0, "HOSE", ke_hoach(CHO, (19500.0, 20000.0)))
    assert b["lenh_khop"] is not None


def test_BAN_GHI_cho_vung_ma_khong_co_vung_thi_NO():
    with pytest.raises(ValueError):
        D.ban_ghi_tin_hieu("A", the_gioi(), 5, 70.0, "HOSE", ke_hoach(CHO, None))


@pytest.mark.parametrize("pq", [BO, KH.CHUA_LAP_DUOC, KH.KHONG_XET])
def test_BAN_GHI_phan_quyet_khac_thi_KHONG_co_lenh_cua_B6(pq):
    b = D.ban_ghi_tin_hieu("A", the_gioi(), 5, 70.0, "HOSE", ke_hoach(pq))
    assert b["lenh_khop"] is None and b["lenh_cham"] is None and b["lenh_nen"] is not None


# ── alpha ───────────────────────────────────────────────────────────────────────────────────
def test_ALPHA_tinh_tay_nen_khop_va_cham():
    """Số tính tay (chi phí vòng 0,46):
    nền    : (23.100 − 21.100)/21.100 = 9,4787% ; − 0,46 = 9,0187% ; chuẩn 10,0% → alpha −0,9813
    khớp   : (23.100 − 19.980)/19.980 = 15,6156% ; − 0,46 = 15,1556% ; chuẩn 10,0% → alpha +5,1556
    chuẩn  : mã A 21→23,1 = +10%, mã B 10→11 = +10% → trung bình 10,0% ở cả hai cặp ngày.
    Δ = 5,1556 − (−0,9813) = +6,1369.
    """
    df = the_gioi({7: (19.98, 21.0, 19.95, 21.0)})
    b = D.ban_ghi_tin_hieu("AAA", df, 5, 70.0, "HOSE", ke_hoach(CHO, (19500.0, 20000.0)))
    giu, bo = D.gan_alpha([b], {"AAA": df, "BBB": chuan_b()})
    assert (len(giu), bo) == (1, 0)
    r = giu[0]
    assert r["ret_nen"] == pytest.approx(9.01867, abs=1e-4)
    assert r["alpha_nen"] == pytest.approx(-0.98133, abs=1e-4)
    assert r["ret_khop"] == pytest.approx(15.15562, abs=1e-4)
    assert r["alpha_khop"] == pytest.approx(5.15562, abs=1e-4)
    assert r["alpha_cham"] == pytest.approx(5.15562, abs=1e-4)
    c = D.chenh(giu)
    assert c["d_alpha"] == [pytest.approx(6.13694, abs=1e-4)]
    assert c["d_ret"] == [pytest.approx(15.15562 - 9.01867, abs=1e-4)]


def test_ALPHA_dau_la_loi_nhuan_TRU_chuan():
    """Đột biến '+ chuẩn' đổi dấu: chuẩn 10% mà alpha lại ra ~+19."""
    df = the_gioi()
    b = D.ban_ghi_tin_hieu("AAA", df, 5, 70.0, "HOSE", ke_hoach(MUA))
    giu, _ = D.gan_alpha([b], {"AAA": df, "BBB": chuan_b()})
    assert giu[0]["alpha_nen"] < 0 < giu[0]["ret_nen"]


def test_ALPHA_khop_voi_vs_benchmark_cua_paper_metrics():
    """Trung bình alpha từng lệnh của dụng cụ == `alpha` của `vs_benchmark` trên cùng các lệnh
    (>= 10 lệnh để hàm ấy trả số) — định nghĩa chuẩn không bị chép lệch."""
    rng = np.random.default_rng(3)
    lenh, chuan = [], {}
    for i in range(12):
        vao, ra = f"2022-02-{i + 1:02d}", f"2022-03-{i + 1:02d}"
        gv = 20000.0 + 100 * i
        lenh.append(D.dung_lenh("X", vao, 70.0, vao, gv, ra, gv * (1 + rng.normal(0.02, 0.05))))
        chuan[(vao, ra)] = float(rng.normal(1.0, 3.0))
    mine = np.mean([D.alpha_cua_lenh(l, chuan) for l in lenh])
    assert mine == pytest.approx(D.PM.vs_benchmark(lenh, chuan)["alpha"], abs=1e-9)


def test_GAN_ALPHA_thieu_chuan_thi_BO_CA_tin_hieu_va_DEM():
    """Mọi `close` ở ngày vào đều 0 → rổ chuẩn không có cặp ngày → bỏ tín hiệu, đếm 1."""
    df = the_gioi({6: (21.10, 21.5, 20.9, 0.0)})
    b = D.ban_ghi_tin_hieu("AAA", df, 5, 70.0, "HOSE", ke_hoach(MUA))
    giu, bo = D.gan_alpha([b], {"AAA": df})
    assert (giu, bo) == ([], 1)


def test_KHU_TRUNG_theo_ma_va_ngay_t():
    a = {"ma": "A", "ngay": "2022-01-10", "x": 1}
    b = {"ma": "A", "ngay": "2022-01-10", "x": 2}
    c = {"ma": "B", "ngay": "2022-01-10", "x": 3}
    d = {"ma": "A", "ngay": "2022-01-11", "x": 4}
    ra, so = D.khu_trung([a, b, c, d])
    assert [r["x"] for r in ra] == [1, 3, 4] and so == 1


# ── chênh lệch, đối chứng ───────────────────────────────────────────────────────────────────
DAU = object()   # đánh dấu "có lệnh"


def rec(pq, ret_nen, alpha_nen, khop=None, ngay="2022-01-10"):
    """Bản ghi dựng tay. `khop` = (ret, alpha) của chính sách khớp nghiêm, hoặc None (lỡ/không có)."""
    r = {"ma": "X", "ngay": ngay, "phan_quyet": pq, "lenh_nen": DAU,
         "ret_nen": ret_nen, "alpha_nen": alpha_nen,
         "lenh_khop": DAU if khop else None, "lenh_cham": DAU if khop else None,
         "ret_khop": khop[0] if khop else None, "alpha_khop": khop[1] if khop else None}
    r["ret_cham"], r["alpha_cham"] = r["ret_khop"], r["alpha_khop"]
    return r


BON = [rec(MUA, 5.0, 2.0),                 # Δα 0
       rec(CHO, 3.0, 1.0, khop=(6.0, 4.0)),   # Δα +3 · Δret +3
       rec(CHO, -2.0, -1.0),               # LỠ: alpha_P = 0  → Δα +1 · Δret +2
       rec(BO, 4.0, 2.5)]                  # không nắm giữ    → Δα −2,5 · Δret −4


def test_CHENH_lo_tinh_alpha_0_chu_KHONG_bi_loai_khoi_quan_the():
    """Δα = [0, 3, 1, −2,5] → trung bình 0,375 trên 4 tín hiệu.
    ĐỘT BIẾN 2 (loại lệnh lỡ) cho (0 + 3 − 2,5)/3 = 0,1667 trên 3."""
    c = D.chenh(BON)
    assert c["d_alpha"] == [0.0, 3.0, 1.0, -2.5]
    assert c["d_ret"] == [0.0, 3.0, 2.0, -4.0]
    t = D.thong_ke(BON)
    assert t["n"] == 4
    assert t["delta_alpha"] == pytest.approx(0.375)
    assert t["delta_ret"] == pytest.approx(0.25)


def test_CHENH_bien_the_cham_dung_cot_cham():
    r = rec(CHO, 3.0, 1.0, khop=(6.0, 4.0))
    r["ret_cham"], r["alpha_cham"] = 9.0, 7.0
    assert D.chenh([r], cham=False)["d_alpha"] == [3.0]
    assert D.chenh([r], cham=True)["d_alpha"] == [6.0]


def test_DOI_CHUNG_ep_hai_dau_tren_ban_ghi_tay():
    """(i) ép MUA_NGAY → Δ ≡ 0. (ii) ép BO_QUA → Δ = −alpha nền: [−2, −1, +1, −2,5], trung bình −1,125."""
    assert D.chenh(BON, ep=MUA)["d_alpha"] == [0.0, 0.0, 0.0, 0.0]
    assert D.chenh(BON, ep=BO)["d_alpha"] == [-2.0, -1.0, 1.0, -2.5]
    dc = D.doi_chung_ep(BON)
    assert dc["i"]["dat"] and dc["ii"]["dat"]
    assert dc["ii"]["delta_alpha_tb"] == pytest.approx(-1.125)
    assert dc["ii"]["tru_alpha_nen_tb"] == pytest.approx(-1.125)


def test_DOI_CHUNG_ep_bat_duoc_chinh_sach_bo_qua_tham_so_ep(monkeypatch):
    """Một `ket_qua_chinh_sach` lờ `ep` thì đối chứng (i) và (ii) phải TRƯỢT (hai chiều)."""
    goc = D.ket_qua_chinh_sach
    monkeypatch.setattr(D, "ket_qua_chinh_sach", lambda b, ep=None, cham=False: goc(b, None, cham))
    dc = D.doi_chung_ep(BON)
    assert not dc["i"]["dat"] and not dc["ii"]["dat"]


def test_DOI_CHUNG_ep_khong_co_nghia_khi_alpha_nen_toan_0():
    """Mọi alpha nền = 0 thì 'Δ = −alpha nền' đúng một cách RỖNG — không được báo ĐẠT."""
    toan_0 = [rec(MUA, 1.0, 0.0), rec(BO, 2.0, 0.0)]
    dc = D.doi_chung_ep(toan_0)
    assert dc["i"]["dat"] and not dc["ii"]["dat"] and not dc["ii"]["co_nghia"]


def test_DOI_CHUNG_ep_khong_tin_hieu_thi_truot():
    dc = D.doi_chung_ep([])
    assert not dc["i"]["dat"] and not dc["ii"]["dat"]


# ── bootstrap ───────────────────────────────────────────────────────────────────────────────
def test_BOOTSTRAP_khoi_ngay_hai_ngay_cong_tru_1_cho_KTC_dung_bang_cong_tru_1():
    """Hai ngày, mỗi ngày 50 tín hiệu: ngày A toàn +1, ngày B toàn −1. Rút lại CẢ NGÀY: trung bình
    mỗi lượt ∈ {+1 (AA, 1/4), 0 (AB/BA, 1/2), −1 (BB, 1/4)} nên cận 2,5% = −1 và 97,5% = +1.
    ĐỘT BIẾN 4 (rút theo dòng) cho KTC ~ ±0,2 (độ lệch chuẩn 1/√100)."""
    gia_tri = [1.0] * 50 + [-1.0] * 50
    ngay = ["2022-01-10"] * 50 + ["2022-01-11"] * 50
    assert D.bootstrap_khoi_ngay(gia_tri, ngay) == (-1.0, 1.0)


def test_BOOTSTRAP_ngay_nhieu_tin_hieu_hon_co_trong_so_theo_so_tin_hieu():
    """Ngày A: 3 tín hiệu Δ = +3 ; ngày B: 1 tín hiệu Δ = −1. Lượt rút: AA → 18/6 = 3 ; AB → 8/4 = 2 ;
    BB → −1. Cận 2,5% = −1, cận 97,5% = 3."""
    gia_tri = [3.0, 3.0, 3.0, -1.0]
    ngay = ["2022-01-10"] * 3 + ["2022-01-11"]
    assert D.bootstrap_khoi_ngay(gia_tri, ngay) == (-1.0, 3.0)


def test_BOOTSTRAP_mac_dinh_la_10000_luot_hat_20261010_va_KTC_95_phan_tram():
    """Hằng số đã ký, ghim ở BA chỗ: mặc định của hàm, phân vị, và việc `thong_ke` không ghi đè."""
    tham = D.inspect.signature(D.bootstrap_khoi_ngay).parameters
    assert tham["so_luot"].default == 10_000 and tham["hat"].default == 20261010
    assert D.PHAN_VI_KTC == (2.5, 97.5)
    goi = next(n for n in ast.walk(_ham("thong_ke")) if isinstance(n, ast.Call)
               and isinstance(n.func, ast.Name) and n.func.id == "bootstrap_khoi_ngay")
    assert len(goi.args) == 2 and not goi.keywords


def test_BOOTSTRAP_tat_dinh_theo_hat_va_hang_so_khong_co_KTC_rong():
    gt = list(np.random.default_rng(7).normal(0, 1, 40))
    ng = [f"2022-01-{1 + i // 4:02d}" for i in range(40)]
    assert D.bootstrap_khoi_ngay(gt, ng) == D.bootstrap_khoi_ngay(gt, ng)
    assert D.bootstrap_khoi_ngay(gt, ng, so_luot=500) != D.bootstrap_khoi_ngay(gt, ng, so_luot=500, hat=1)
    assert D.bootstrap_khoi_ngay([2.5] * 6, ["a", "a", "b", "b", "c", "c"]) == (2.5, 2.5)


# ── kết cục ─────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("n, lo, hi, mong", [
    (112, 5.0, 6.0, D.KET_CUC_CHUA_DU),      # dưới 113 → chưa đủ, KHÔNG đọc dấu
    (113, 0.1, 0.5, D.KET_CUC_A),
    (113, 0.0, 0.5, D.KET_CUC_B),            # cận dưới == 0 không phải > 0
    (113, -0.5, 0.0, D.KET_CUC_B),           # cận trên == 0 không phải < 0
    (113, -0.5, 0.2, D.KET_CUC_B),
    (113, -0.5, -0.1, D.KET_CUC_C),
    (500, 0.01, 0.9, D.KET_CUC_A),
])
def test_KET_CUC_theo_ba_nhanh_da_ky_va_bien_113(n, lo, hi, mong):
    assert D.ket_cuc(n, lo, hi) == mong


def test_QUY_TAC_1_co_khi_delta_lon_hon_2_va_khong_co_khi_dung_bang_2():
    def mot(delta):
        return [rec(CHO, 0.0, 0.0, khop=(delta, delta), ngay=f"2022-01-{i + 1:02d}") for i in range(3)]
    assert D.thong_ke(mot(2.5))["quy_tac_1"] is True
    assert D.thong_ke(mot(2.0))["quy_tac_1"] is False


def test_THONG_KE_rong_la_chua_du():
    t = D.thong_ke([])
    assert t["n"] == 0 and t["ket_cuc"] == D.KET_CUC_CHUA_DU


# ── quét tín hiệu ───────────────────────────────────────────────────────────────────────────
def _lap_gia(ghi):
    def lap(df, he, diem, nguong, bay_gio, san):
        ghi.append({"n": len(df), "he": he, "diem": diem, "nguong": nguong,
                    "bay_gio": bay_gio, "san": san, "cuoi": str(df["time"].iloc[-1])})
        return ke_hoach(BO)
    return lap


def test_THU_THAP_chi_cham_phien_QUYET_DINH_voi_lich_su_den_het_t(monkeypatch):
    """75 hàng, min_history 60, stride 2 → phiên quyết định ở 60, 62, …, 74 (8 phiên); phiên lẻ
    (61, 63, …) chỉ để KHỚP và KHÔNG được chấm. Lịch sử đưa cho máy chấm có đúng t + 1 hàng."""
    goi = []
    monkeypatch.setattr(KH, "lap_ke_hoach", _lap_gia([]))
    df = bang(75)

    def cham(ma, ls, ngay):
        goi.append((ma, len(ls), ngay))
        return 70.0

    tin, qs = D.thu_thap_tin_hieu({"FPT": df}, cham, 2, 60)
    assert [g[1] for g in goi] == [61, 63, 65, 67, 69, 71, 73, 75]
    assert [g[2] for g in goi] == [df["time"].iloc[i] for i in range(60, 75, 2)]
    assert qs["so_phien_cham"] == 8 and len(tin) == 8


def test_THU_THAP_nguong_62_gom_dung_bang_62_va_loai_61_99(monkeypatch):
    monkeypatch.setattr(KH, "lap_ke_hoach", _lap_gia([]))
    diem = iter([62.0, 61.99, 80.0, 0.0, 62.0, 62.01, 10.0, 99.0])
    tin, _ = D.thu_thap_tin_hieu({"FPT": bang(75)}, lambda ma, ls, ngay: next(diem), 2, 60)
    assert [s["diem"] for s in tin] == [62.0, 80.0, 62.0, 62.01, 99.0]


def test_THU_THAP_loc_theo_ngay_tu_den_gom_hai_dau(monkeypatch):
    monkeypatch.setattr(KH, "lap_ke_hoach", _lap_gia([]))
    df = bang(75)
    tu, den = df["time"].iloc[64], df["time"].iloc[68]
    tin, qs = D.thu_thap_tin_hieu({"FPT": df}, lambda ma, ls, ngay: 70.0, 2, 60, tu, den)
    assert [df["time"].iloc[s["t"]] for s in tin] == [df["time"].iloc[i] for i in (64, 66, 68)]
    assert qs["so_phien_cham"] == 3


def test_LAP_KE_HOACH_goi_B6_voi_lich_su_den_het_t_he_so_don_vi_nguong_gio_va_san(monkeypatch):
    """Nguồn của nhìn trộm: nếu đưa cả `df` thì B6 thấy tương lai. Đối số đo bằng độ dài, hệ số 1000
    (giá 21,0 nghìn đồng), ngưỡng 62, giờ sau đóng cửa NGÀY t, sàn do người gọi đưa."""
    ghi = []
    monkeypatch.setattr(KH, "lap_ke_hoach", _lap_gia(ghi))
    df = bang(75)
    D.lap_ke_hoach_cho_tin_hieu(df, 66, 71.5, "HNX")
    g = ghi[0]
    assert g["n"] == 67 and g["cuoi"] == df["time"].iloc[66]
    assert g["he"] == 1000.0 and g["diem"] == 71.5 and g["nguong"] == 62 and g["san"] == "HNX"
    assert g["bay_gio"] == datetime.datetime.combine(
        datetime.date.fromisoformat(df["time"].iloc[66]), datetime.time(23, 0))


def test_THU_THAP_san_theo_MA_khong_theo_o_chon(monkeypatch):
    ghi = []
    monkeypatch.setattr(KH, "lap_ke_hoach", _lap_gia(ghi))
    D.thu_thap_tin_hieu({"PVS": bang(75), "FPT": bang(75)}, lambda ma, ls, ngay: 70.0, 2, 60)
    assert {g["san"] for g in ghi} == {"HNX", "HOSE"}


# ── đối chứng (iii): xáo nến sau t ──────────────────────────────────────────────────────────
def _tin_hieu_ngau_nhien(n=90):
    rng = np.random.default_rng(5)
    gia = np.round(20 + np.cumsum(rng.normal(0, 0.4, n)), 2)
    df = pd.DataFrame({"time": pd.bdate_range("2022-01-03", periods=n).strftime("%Y-%m-%d"),
                       "open": gia, "high": gia + 0.2, "low": gia - 0.2, "close": gia,
                       "volume": 1e5})
    return df, [{"ma": "X", "df": df, "t": t, "diem": 70.0, "san": "HOSE",
                 "ke_hoach": D.lap_ke_hoach_cho_tin_hieu(df, t, 70.0, "HOSE")} for t in (60, 65, 70)]


def _lap_theo_gia_cuoi(df, he, diem, nguong, bay_gio, san):
    """Giả: kế hoạch mang `gia_dong` = đóng cửa của hàng CUỐI bảng nhận được — nên chỉ đúng KHI và
    CHỈ KHI bộ lập kế hoạch đưa đúng lát cắt ≤ t."""
    return KH._ket(MUA, ["x"], "x", gia_dong=float(df["close"].iloc[-1]))


def test_DOI_CHUNG_xao_DAT_khi_chi_dung_lich_su_den_t(monkeypatch):
    monkeypatch.setattr(KH, "lap_ke_hoach", _lap_theo_gia_cuoi)
    df, tin = _tin_hieu_ngau_nhien()
    tin = [dict(s, ke_hoach=D.lap_ke_hoach_cho_tin_hieu(df, s["t"], 70.0, "HOSE")) for s in tin]
    kq = D.doi_chung_xao_tuong_lai(tin)
    assert kq["dat"] and kq["so_lech"] == 0 and kq["so_tin_hieu"] == 3
    assert kq["so_lan_tuong_lai_that_su_doi"] == 3


def test_DOI_CHUNG_xao_TRUOT_khi_lap_ke_hoach_nhin_ca_bang(monkeypatch):
    """Một bộ lập kế hoạch RÒ (đưa cả `df`) thì sau khi xáo nến sau t, hàng cuối đổi → phán quyết
    đổi → đối chứng (iii) phải TRƯỢT. Đây là ĐỘT BIẾN nhìn trộm."""
    monkeypatch.setattr(KH, "lap_ke_hoach", _lap_theo_gia_cuoi)
    df, tin = _tin_hieu_ngau_nhien()
    tin = [dict(s, ke_hoach=D.lap_ke_hoach_cho_tin_hieu(df, s["t"], 70.0, "HOSE")) for s in tin]

    def ro(d, t, diem, san):
        return KH.lap_ke_hoach(d, 1000.0, diem, 62, datetime.datetime(2030, 1, 1), san)
    monkeypatch.setattr(D, "lap_ke_hoach_cho_tin_hieu", ro)
    # kế hoạch gốc (cũng rò) lập trên bảng gốc — hàng cuối là hàng cuối của bảng
    tin = [dict(s, ke_hoach=ro(df, s["t"], 70.0, "HOSE")) for s in tin]
    kq = D.doi_chung_xao_tuong_lai(tin)
    assert not kq["dat"] and kq["so_lech"] > 0


def test_DOI_CHUNG_xao_khong_co_nghia_khi_tuong_lai_khong_doi_duoc(monkeypatch):
    """Tương lai là các nến GIỐNG HỆT nhau → xáo không đổi gì → đối chứng phải báo KHÔNG ĐẠT, vì
    'không lệch' khi không thể lệch là bằng chứng rỗng."""
    monkeypatch.setattr(KH, "lap_ke_hoach", _lap_theo_gia_cuoi)
    df = bang(90, 25.0)
    tin = [{"ma": "X", "df": df, "t": 60, "diem": 70.0, "san": "HOSE",
            "ke_hoach": D.lap_ke_hoach_cho_tin_hieu(df, 60, 70.0, "HOSE")}]
    kq = D.doi_chung_xao_tuong_lai(tin)
    assert kq["so_lan_tuong_lai_that_su_doi"] == 0 and not kq["dat"]


# ── nhóm VN-INDEX ───────────────────────────────────────────────────────────────────────────
def _vni(gia):
    n = len(gia)
    return pd.DataFrame({"time": pd.bdate_range("2022-01-03", periods=n).strftime("%Y-%m-%d"),
                         "close": gia})


def test_VNI_tren_duoi_MA50_va_phang_la_TREN_vi_so_sanh_la_ge():
    ngay = lambda v, i: v["time"].iloc[i]  # noqa: E731
    tang = _vni(list(np.linspace(100, 160, 80)))
    giam = _vni(list(np.linspace(160, 100, 80)))
    phang = _vni([100.0] * 80)
    assert D.vni_tren_ma50(tang, ngay(tang, 79)) is True
    assert D.vni_tren_ma50(giam, ngay(giam, 79)) is False
    assert D.vni_tren_ma50(phang, ngay(phang, 79)) is True       # close == MA50, ">="


def test_VNI_chi_dung_du_lieu_den_het_ngay_khong_nhin_phien_sau():
    tang = _vni(list(np.linspace(100, 160, 80)) + [1.0] * 10)    # 10 phiên sau sập về 1
    assert D.vni_tren_ma50(tang, tang["time"].iloc[79]) is True


def test_VNI_thieu_du_lieu_thi_None_khong_bia_nhan():
    assert D.vni_tren_ma50(None, "2022-06-01") is None
    assert D.vni_tren_ma50(_vni([100.0] * 49), "2030-01-01") is None
    assert D.vni_tren_ma50(_vni([100.0] * 60), "2022-01-05") is None   # ngày chưa đủ 50 phiên


# ── nạp dữ liệu ─────────────────────────────────────────────────────────────────────────────
def test_VUNG_OOS_chi_ma_co_moc_cat_truoc_moc_va_phai_dai_hon_min_history():
    tat_ca = {"A": bang(10), "B": bang(10), "C": bang(10)}
    moc = {"A": tat_ca["A"]["time"].iloc[6],   # OOS = hàng 0..5 (6 hàng)
           "C": tat_ca["C"]["time"].iloc[3]}   # OOS = hàng 0..2 (3 hàng)
    ra = D.dung_vung_oos(tat_ca, moc, 4)       # "dài hơn" 4: A (6) giữ, C (3) bỏ, B không mốc → bỏ
    assert list(ra) == ["A"] and len(ra["A"]) == 6
    assert list(ra["A"].index) == list(range(6))
    assert ra["A"]["time"].iloc[-1] == tat_ca["A"]["time"].iloc[5]
    assert list(D.dung_vung_oos(tat_ca, moc, 2)) == ["A", "C"]      # C có 3 hàng > 2
    assert "C" not in D.dung_vung_oos(tat_ca, moc, 3)               # 3 hàng KHÔNG dài hơn 3


def test_BAM_THU_MUC_on_dinh_va_nhay_voi_noi_dung_va_ten(tmp_path):
    (tmp_path / "A.csv").write_text("x\n1\n", encoding="utf-8")
    (tmp_path / "B.csv").write_text("x\n2\n", encoding="utf-8")
    (tmp_path / "ghi_chu.txt").write_text("khong tinh", encoding="utf-8")
    m1 = D.bam_thu_muc(tmp_path)
    assert m1["so_file"] == 2 and m1 == D.bam_thu_muc(tmp_path)
    (tmp_path / "B.csv").write_text("x\n3\n", encoding="utf-8")
    assert D.bam_thu_muc(tmp_path)["sha256"] != m1["sha256"]
    (tmp_path / "B.csv").write_text("x\n2\n", encoding="utf-8")
    assert D.bam_thu_muc(tmp_path)["sha256"] == m1["sha256"]
    (tmp_path / "B.csv").rename(tmp_path / "C.csv")
    assert D.bam_thu_muc(tmp_path)["sha256"] != m1["sha256"]


def _git(repo, *args):
    r = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t",
                        "-c", "commit.gpgsign=false", *args], cwd=str(repo), capture_output=True,
                       text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


def test_KIEM_MA_KE_HOACH_khop_lech_va_chua_kiem_duoc(tmp_path, tmp_path_factory):
    _git(tmp_path, "init", "-q")
    (tmp_path / "ke_hoach_vao_lenh.py").write_text("A = 1\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "x")
    ma = _git(tmp_path, "rev-parse", "HEAD")
    assert D.kiem_ma_ke_hoach(tmp_path, ma) == "khop"
    (tmp_path / "ke_hoach_vao_lenh.py").write_text("A = 2\n", encoding="utf-8")
    assert D.kiem_ma_ke_hoach(tmp_path, ma) == "lech"
    assert D.kiem_ma_ke_hoach(tmp_path, "0" * 40) == "chua_kiem_duoc"      # commit không có
    khong_git = tmp_path_factory.mktemp("khong_git")
    assert D.kiem_ma_ke_hoach(khong_git, ma) == "chua_kiem_duoc"


# ── cả đường chạy ───────────────────────────────────────────────────────────────────────────
def test_DOI_CHUNG_tong_hop_dat_ca_ba_va_KHONG_rong(capsys):
    """Dữ liệu tổng hợp qua CHÍNH đường `thu_thap_tin_hieu` → `do_tin_hieu`. Phải có đủ các loại
    phán quyết thì đối chứng (iii) mới có nghĩa; có cả CHO_VUNG khớp lẫn lỡ."""
    kq = D.doi_chung_tong_hop()
    assert D.doi_chung_dat(kq)
    pq = kq["bao_kem"]["ty_le_phan_quyet"]
    assert {MUA, BO, CHO} <= set(pq)
    cv = kq["bao_kem"]["cho_vung"]
    assert cv["khop"] > 0 and cv["lo"] > 0
    assert kq["chinh"]["n"] >= 113


def test_LENH_doi_chung_tra_0_va_in_bang(capsys):
    assert D.main(["doi-chung"]) == 0
    ra = capsys.readouterr().out
    assert "ĐỐI CHỨNG" in ra and "ĐẠT" in ra and "TRƯỢT" not in ra


def _cache_gia(thu_muc, ma_list, n=150):
    for i, ma in enumerate(ma_list):
        D.chuoi_tong_hop(n=n, gia0=20.0 + 5 * i, hat=100 + i).to_csv(thu_muc / f"{ma}.csv", index=False)


class _May:
    sl_patterns = [1, 2, 3]


@contextlib.contextmanager
def _moi_truong_gia(che_do_hoc):
    yield _May()


def test_LENH_chay_di_het_duong_va_ghi_JSON_o_duong_dan_nguoi_goi_chon(tmp_path, monkeypatch, capsys):
    """Cache giả, máy chấm giả (70), nhớ giả. Đường: M0 → nạp → vùng OOS theo mốc → quét → đo → in →
    ghi JSON. Mốc OOS đặt ở hàng 140: vùng OOS = hàng 0..139 của mỗi mã."""
    cache = tmp_path / "cache"
    cache.mkdir()
    _cache_gia(cache, ["AAA", "BBB", "CCC"])
    moc = {ma: pd.read_csv(cache / f"{ma}.csv")["time"].iloc[140] for ma in ("AAA", "BBB", "CCC")}
    monkeypatch.setattr(D.WF, "nap_moc_sach", lambda *a, **k: moc)
    monkeypatch.setattr(D, "moi_truong_cham_diem", _moi_truong_gia)
    monkeypatch.setattr(D, "cham_diem_that", lambda ma, ls, ngay: 70.0)
    monkeypatch.setattr(D, "kiem_ma_ke_hoach", lambda *a, **k: "khop")
    ra = tmp_path / "ket_qua.json"
    ma = D.main(["chay", "--cache", str(cache), "--ghi", str(ra), "--symbols", "AAA,BBB,CCC"])
    out = capsys.readouterr().out
    d = json.loads(ra.read_text(encoding="utf-8"))
    assert ma == 0, out
    assert d["m0"]["cache"]["so_file"] == 3 and d["m0"]["mau_bo_nho"] == 3
    assert d["m0"]["so_ma_oos"] == 3 and d["m0"]["stride"] == 2 and d["m0"]["che_do_hoc"] == "co_san"
    assert d["ket_qua"]["chinh"]["n"] > 0 and d["ket_qua"]["doi_chung"]["xao_tuong_lai"]["dat"]
    assert "KẾT CỤC KÝ TRƯỚC" in out or "CHƯA ĐỦ" in out
    # băm cache lệch → DỪNG, không ghi
    ra2 = tmp_path / "ra2.json"
    assert D.main(["chay", "--cache", str(cache), "--ghi", str(ra2), "--symbols", "AAA",
                   "--bam-mong-doi", "0" * 64]) == 1
    assert not ra2.exists()


def test_LENH_chay_DUNG_khi_ke_hoach_vao_lenh_lech_commit_hoac_khong_kiem_duoc(tmp_path, monkeypatch):
    cache = tmp_path / "cache"
    cache.mkdir()
    _cache_gia(cache, ["AAA"])
    ra = tmp_path / "ra.json"
    for tinh, ma_thoat in (("lech", 1), ("chua_kiem_duoc", 2)):
        monkeypatch.setattr(D, "kiem_ma_ke_hoach", lambda *a, _t=tinh, **k: _t)
        assert D.main(["chay", "--cache", str(cache), "--ghi", str(ra)]) == ma_thoat
    assert not ra.exists()


def test_LENH_chay_DUNG_khi_nguong_mua_khong_con_la_62(tmp_path, monkeypatch):
    monkeypatch.setattr(D.PT, "BUY_THRESHOLD", 60)
    monkeypatch.setattr(D, "kiem_ma_ke_hoach", lambda *a, **k: "khop")
    assert D.main(["chay", "--cache", str(tmp_path), "--ghi", str(tmp_path / "x.json")]) == 1


def test_LENH_chay_cache_rong_la_chua_kiem_duoc_ma_2(tmp_path, monkeypatch):
    monkeypatch.setattr(D, "kiem_ma_ke_hoach", lambda *a, **k: "khop")
    assert D.main(["chay", "--cache", str(tmp_path), "--ghi", str(tmp_path / "x.json")]) == 2


def test_BAO_CAO_in_so_da_tinh_va_canh_bao_quy_tac_1_va_doi_chung_truot():
    kq = D.doi_chung_tong_hop(so_ma=3)
    kq["chinh"]["quy_tac_1"] = True
    dong = "\n".join(D.dong_bao_cao(kq))
    assert "QUY TẮC 1" in dong
    kq["doi_chung"]["ep"]["i"]["dat"] = False
    dong = "\n".join(D.dong_bao_cao(kq))
    assert "ĐỐI CHỨNG TRƯỢT" in dong and "KHÔNG đọc kết cục" in dong


# ── AST: chỉ đọc, đúng máy chấm ─────────────────────────────────────────────────────────────
def _cay():
    return ast.parse(Path(D.__file__).read_text(encoding="utf-8"))


def _ham(ten):
    return next(n for n in _cay().body if isinstance(n, ast.FunctionDef) and n.name == ten)


def _goi_trong(nut):
    ten = set()
    for n in ast.walk(nut):
        if isinstance(n, ast.Call):
            f = n.func
            ten.add(f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else "")
    return ten


def test_AST_KHONG_import_mang_vnstock_so_lenh_hay_kho_ngoai():
    ten = set()
    for n in ast.walk(_cay()):
        if isinstance(n, ast.Import):
            ten |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            ten.add(n.module.split(".")[0])
    cam = {"vnstock", "vnai", "vnstock_data", "requests", "urllib", "httpx", "socket", "sqlite3",
           "sheets_store", "gspread", "google_sheets_sync", "market_filter", "shutil"}
    assert not ten & cam, ten & cam


def test_AST_KHONG_goi_ham_ghi_so_hay_mo_so_lenh():
    goi = _goi_trong(_cay())
    cam = {"PaperTradingJournal", "consider_entry", "record_decision", "open_position", "fill_pending",
           "evaluate_open", "push", "pull", "execute", "executemany", "commit", "to_csv", "to_sql",
           "unlink", "rmtree", "remove", "rename", "mkdir", "touch"}
    assert not goi & cam, goi & cam


def test_AST_chi_MOT_cho_ghi_file_la_lenh_chay():
    ghi = [h.name for h in _cay().body if isinstance(h, ast.FunctionDef) and "write_text" in _goi_trong(h)]
    assert ghi == ["lenh_chay"], ghi


def test_AST_dung_dung_may_cham_diem_cua_walkforward():
    """Điểm = `paper_runner._analyze(...)["final_score"]`; lịch = `walkforward.lich_theo_ngay` với
    độ trễ khớp 1; vùng OOS = `chia_vung` + `nap_moc_sach`; bộ nhớ = `_dung_bo_nho`."""
    assert "_analyze" in _goi_trong(_ham("cham_diem_that"))
    thu_thap = _ham("thu_thap_tin_hieu")
    assert "lich_theo_ngay" in _goi_trong(thu_thap)
    lich = next(n for n in ast.walk(thu_thap) if isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute) and n.func.attr == "lich_theo_ngay")
    assert [ast.unparse(a) for a in lich.args] == ["vung_oos", "min_history", "stride", "1"]
    assert "chia_vung" in _goi_trong(_ham("dung_vung_oos"))
    assert "nap_moc_sach" in _goi_trong(_ham("lenh_chay"))
    assert "_dung_bo_nho" in _goi_trong(_ham("moi_truong_cham_diem"))
    assert "build_benchmark" in _goi_trong(_ham("gan_alpha"))
    assert "net_return_pct" in _goi_trong(_ham("alpha_cua_lenh"))


def test_AST_B6_chi_nhan_lich_su_den_het_t_va_nguong_ky_truoc():
    ham = _ham("lap_ke_hoach_cho_tin_hieu")
    gan = {n.targets[0].id: ast.unparse(n.value) for n in ast.walk(ham)
           if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)}
    assert gan["lich_su"] == "df.iloc[:t + 1]"
    goi = next(n for n in ast.walk(ham) if isinstance(n, ast.Call)
               and isinstance(n.func, ast.Attribute) and n.func.attr == "lap_ke_hoach")
    assert [ast.unparse(a) for a in goi.args] == [
        "lich_su", "price_multiplier(lich_su)", "diem", "NGUONG_DA_KY", "bay_gio", "san"]


def test_AST_nguong_mua_duoc_so_voi_BUY_THRESHOLD_o_lenh_chay():
    nguon = ast.get_source_segment(Path(D.__file__).read_text(encoding="utf-8"), _ham("lenh_chay"))
    assert "PT.BUY_THRESHOLD != NGUONG_DA_KY" in nguon


def test_AST_mac_dinh_stride_va_che_do_hoc_doc_tu_walkforward_khong_gan_so():
    nguon = ast.get_source_segment(Path(D.__file__).read_text(encoding="utf-8"), _ham("lenh_chay"))
    for ten in ("stride", "min_history", "che_do_hoc"):
        assert f'mac_dinh["{ten}"]' in nguon


def test_CHAY_nhu_script_co_lenh_tro_giup():
    r = subprocess.run([sys.executable, str(Path(D.__file__)), "--help"], capture_output=True,
                       text=True, encoding="utf-8")
    assert r.returncode == 0 and "doi-chung" in r.stdout and "chay" in r.stdout
