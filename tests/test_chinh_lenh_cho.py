"""BƯỚC 282 — gác của bộ chỉnh THANG GIÁ lệnh CHỜ KHỚP (`chinh_lenh_cho.py`).

Ca hỏng (phiên con của leader, `vibe_logs_282/vi_du_hong_282.py`): lệnh `PENDING` tạo ở ngày T mang cắt lỗ · chốt
lời ở thang LÚC QUÉT; nến đầu tiên sau T là ngày giao dịch không hưởng quyền, nguồn điều chỉnh lùi cả lịch sử.
`fill_pending` khớp ở giá mở thang MỚI, cắt lỗ còn thang CŨ (cao hơn giá mới) nên phiên kế `low <= stop_loss` đúng:
một cú STOP_LOSS GIẢ, mà nhãn `su_kien_quyen` gọi là `SACH`.

Số kỳ vọng là SỐ TÍNH TAY: hệ số f = 1,25 (nến T đóng 100.000 thang cũ = 80,0 nghìn thang mới), nên cắt lỗ
93.000 → 74.400 và chốt lời 115.000 → 92.000. Khung giá tiêm: nghìn đồng, thang MỚI cho mọi nến (đúng cách
nguồn điều chỉnh lùi). Gác AST ở cuối file: chỗ nhập, thứ tự lời gọi ở `run_daily`, và những thứ module KHÔNG làm.
"""
from __future__ import annotations

import ast
import json
import pathlib
import sys

import pandas as pd
import pytest

GOC = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))
sys.path.insert(0, str(GOC))

import chinh_lenh_cho as clc  # noqa: E402
import chinh_thang_gia as ct  # noqa: E402
import duyet_repo  # noqa: E402
import paper_trading as pt  # noqa: E402
from nhat_ky_vi_sao import COT_NHAT_KY  # noqa: E402
from paper_runner import buoc_phien  # noqa: E402
from paper_trading import CauHinhVao, PaperTradingJournal  # noqa: E402

MA = "FPT"            # HOSE
T = "2026-11-10"      # ngày tín hiệu (quét SAU đóng cửa, thang CŨ)
GIA_DONG_CU = 100_000.0
SL_CU, TP_CU = 93_000.0, 115_000.0

# (ngày, mở, cao, thấp, đóng) nghìn đồng, THANG MỚI. Nến T đóng 80,0 = 100.000 ÷ 1,25; ngày GDKHQ 11/11 mở ~80.
NEN_MOI = [
    ("2026-11-06", 79.2, 80.8, 78.4, 80.0),
    ("2026-11-09", 80.0, 81.2, 79.2, 80.4),
    (T, 80.4, 81.6, 79.6, 80.0),
    ("2026-11-11", 79.6, 81.0, 78.8, 80.4),   # GDKHQ
    ("2026-11-12", 80.4, 81.5, 79.6, 81.0),   # +0,75% bình thường
]


def _khung(nen):
    return pd.DataFrame({"time": pd.to_datetime([n[0] for n in nen]),
                         "open": [n[1] for n in nen], "high": [n[2] for n in nen],
                         "low": [n[3] for n in nen], "close": [n[4] for n in nen],
                         "volume": [3_000_000.0] * len(nen)})


def _so(that=False):
    return PaperTradingJournal(":memory:", cho_phep_so_that=that)


def _cho(j, *, id=1, ma=MA, tin=T, sl=SL_CU, tp=TP_CU, size=20.0, trang_thai="PENDING", co_nhat_ky=True,
         boi_canh=None):
    j.db.execute(
        "INSERT INTO trades (id, symbol, exchange, signal_date, entry_date, entry_price, exit_date, exit_price,"
        " exit_reason, stop_loss, take_profit, size_pct, entry_score, entry_recommendation, components, reasons,"
        " status, created_at) VALUES (?,?,?,?,NULL,NULL,NULL,NULL,NULL,?,?,?,70,'MUA','{}','[]',?,0)",
        (id, ma, "HOSE", tin, sl, tp, size, trang_thai))
    if co_nhat_ky:
        d = {c: None for c in COT_NHAT_KY}
        d.update(trade_id=id, symbol=ma, signal_date=tin, diem_agent="{}", ly_do="[]", boi_canh=boi_canh)
        j.db.execute(f"INSERT INTO nhat_ky ({','.join(COT_NHAT_KY)}) VALUES ({','.join('?' * len(COT_NHAT_KY))})",
                     [d[c] for c in COT_NHAT_KY])
    j.db.commit()


def _ke_hoach(j, *, ma=MA, ngay=T, gia_dong=GIA_DONG_CU):
    j.db.execute("INSERT INTO ke_hoach (at, symbol, signal_date, gia_dong) VALUES (0, ?, ?, ?)",
                 (ma, ngay, gia_dong))
    j.db.commit()


def _trade(j, id=1):
    return j.db.execute("SELECT * FROM trades WHERE id=?", (id,)).fetchone()


def _nk(j, id=1):
    return j.db.execute("SELECT * FROM nhat_ky WHERE trade_id=?", (id,)).fetchone()


def _luot(j, ngay, *, goi_lenh_cho=True, ghi=None):
    """MỘT lượt quét: bộ chỉnh lệnh mở (276) → bộ chỉnh lệnh chờ (282, nếu `goi_lenh_cho`) → khớp
    (`buoc_phien` chỉ-khớp: fill_pending → fill_closing → lệnh đặt sẵn). Đúng thứ tự của `run_daily`."""
    df = _khung([n for n in NEN_MOI if n[0] <= ngay])
    ct.chinh_thang_mot_ma(j, MA, df, ngay, nguon="gia-lap", san="HOSE", ghi=lambda m: None)
    sk = []
    if goi_lenh_cho:
        sk = clc.chinh_lenh_cho_mot_ma(j, MA, df, ngay, nguon="gia-lap", ghi=ghi or (lambda m: None))
    r = df.iloc[-1]
    bar = {k: float(r[k]) for k in ("open", "high", "low", "close", "volume")}
    buoc_phien(j, MA, df, bar, ngay, "HOSE", CauHinhVao.tu_module(), lambda: {"final_score": 70.0},
               chi_khop=True)
    return sk


# ─────────────────────────── ca hỏng, đỏ trên mã cũ ───────────────────────────
def test_DOI_CHUNG_khong_chinh_lenh_cho_thi_co_cat_lo_GIA_va_nhan_noi_SACH():
    """Máy đo không mù: KHÔNG gọi bộ mới thì ca hỏng xảy ra y như hiện trạng — cắt lỗ thang cũ (93.000) trên giá
    khớp ~79.600: STOP_LOSS sau MỘT phiên, ở giá > giá vào (không phải lỗ), và nhãn Q14 nói SẠCH."""
    j = _so()
    _cho(j)
    _ke_hoach(j)
    _luot(j, "2026-11-11", goi_lenh_cho=False)
    t = _trade(j)
    assert t["status"] == "OPEN" and t["stop_loss"] == SL_CU and 79_000 < t["entry_price"] < 80_200
    _luot(j, "2026-11-12", goi_lenh_cho=False)
    t = _trade(j)
    assert t["status"] == "CLOSED" and t["exit_reason"] == "STOP_LOSS"
    assert t["exit_price"] > t["entry_price"] > 79_000      # "cắt lỗ" ở giá CAO hơn giá vào: giả
    import su_kien_quyen as skq
    nen = skq.dung_nen([n[0] for n in NEN_MOI], [n[1] for n in NEN_MOI], [n[3] for n in NEN_MOI],
                       [n[2] for n in NEN_MOI], 1000.0)
    kq = skq.kiem_lenh({k: t[k] for k in ("entry_date", "entry_price", "exit_date", "exit_price")}, nen, True)
    assert kq.trang_thai == skq.SACH


def test_KICH_BAN_chinh_lenh_cho_thi_lenh_o_lai_OPEN_va_cat_lo_chot_loi_chia_dung_f():
    j = _so()
    _cho(j)
    _ke_hoach(j)
    sk = _luot(j, "2026-11-11")
    assert [s["trang_thai"] for s in sk] == [clc.CHINH] and sk[0]["f"] == pytest.approx(1.25, rel=1e-12)
    t = _trade(j)
    assert t["status"] == "OPEN"
    assert t["stop_loss"] == pytest.approx(74_400.0, rel=1e-12)     # 93.000 ÷ 1,25
    assert t["take_profit"] == pytest.approx(92_000.0, rel=1e-12)   # 115.000 ÷ 1,25
    assert 79_000 < t["entry_price"] < 80_200                        # giá khớp KHÔNG bị chạm
    assert t["size_pct"] == pytest.approx(20.0, abs=1.0)
    _luot(j, "2026-11-12")
    t = _trade(j)
    assert t["status"] == "OPEN" and t["exit_reason"] is None        # không còn cú cắt lỗ giả
    # lệnh mở sau khi khớp: bộ 276 đo f ≈ 1 (giá vào thang mới) nên KHÔNG chia lần hai
    assert t["stop_loss"] == pytest.approx(74_400.0, rel=1e-12)


def test_nhat_ky_ghi_dau_loai_lenh_cho_giu_khoa_cu_va_stop_loss_ban_dau_theo_thang_moi():
    j = _so(that=True)
    _cho(j, boi_canh=json.dumps({"diem_cuoi": 71.0, "nguong_mua": 62.0}, sort_keys=True))
    _ke_hoach(j)
    _luot(j, "2026-11-11")
    bc = json.loads(_nk(j)["boi_canh"])
    assert bc["diem_cuoi"] == 71.0 and bc["nguong_mua"] == 62.0
    assert len(bc[ct.KHOA_NHAT_KY]) == 1
    m = bc[ct.KHOA_NHAT_KY][0]
    assert (m["loai"], m["ngay_tin_hieu"], m["ngay_quet"], m["nguon"]) == ("lenh_cho", T, "2026-11-11", "gia-lap")
    assert m["f"] == pytest.approx(1.25, rel=1e-12)
    # `_ghi_nua_vao` (lúc khớp) chép `trades.stop_loss` — đã là thang mới; và chép nguyên boi_canh
    nk = _nk(j)
    assert nk["entry_date"] == "2026-11-11" and nk["stop_loss_ban_dau"] == pytest.approx(74_400.0, rel=1e-12)
    assert nk["rui_ro_pct"] > 0                                         # cắt lỗ DƯỚI giá vào
    assert ct.KHOA_NHAT_KY in json.loads(nk["boi_canh"])


def test_chia_mot_lan_duy_nhat_du_quet_lai_nhieu_luot_trong_luc_lenh_van_cho():
    """`ke_hoach.gia_dong` còn thang cũ nên lượt sau đo ra f cũ; dấu trong boi_canh chặn lần chia thứ hai."""
    j = _so()
    _cho(j)
    _ke_hoach(j)
    df = _khung([n for n in NEN_MOI if n[0] <= "2026-11-11"])
    ghi = []
    a = clc.chinh_lenh_cho_mot_ma(j, MA, df, "2026-11-11", ghi=ghi.append)
    b = clc.chinh_lenh_cho_mot_ma(j, MA, df, "2026-11-11", ghi=ghi.append)
    c = clc.chinh_lenh_cho_mot_ma(j, MA, df, "2026-11-12", ghi=ghi.append)
    assert [x[0]["trang_thai"] for x in (a, b, c)] == [clc.CHINH, clc.DA_CHINH, clc.DA_CHINH]
    assert _trade(j)["stop_loss"] == pytest.approx(74_400.0, rel=1e-12)
    assert len(json.loads(_nk(j)["boi_canh"])[ct.KHOA_NHAT_KY]) == 1
    assert len([g for g in ghi if "🔧" in g]) == 1 and not [g for g in ghi if "##[warning]" in g]


def test_muc_cu_cua_lenh_mo_276_hoac_cua_ngay_tin_hieu_khac_khong_chan_va_duoc_giu():
    """Dấu chống chia hai lần chỉ nhận mục `loai = lenh_cho` CÙNG ngày tín hiệu; mục của bộ 276 (không có
    `loai`) hay của ngày khác ở lại nguyên, mục mới cộng dồn sau chúng."""
    cu = [{"ngay_quet": "2026-10-20", "f": 1.2, "ngay_nen_vao": "2026-10-01", "nguon": "x"},
          {"loai": "lenh_cho", "ngay_quet": "2026-10-21", "f": 1.1, "ngay_tin_hieu": "2026-10-02",
           "nguon": "x"}]
    j = _so()
    _cho(j, boi_canh=json.dumps({ct.KHOA_NHAT_KY: cu}, sort_keys=True))
    _ke_hoach(j)
    sk = clc.chinh_lenh_cho_mot_ma(j, MA, _khung(NEN_MOI), "2026-11-11", ghi=lambda m: None)
    assert sk[0]["trang_thai"] == clc.CHINH
    lan = json.loads(_nk(j)["boi_canh"])[ct.KHOA_NHAT_KY]
    assert lan[:2] == cu and len(lan) == 3 and lan[2]["ngay_tin_hieu"] == T


def test_dau_chong_chia_hai_lan_doi_CA_loai_lai_ngay_tin_hieu():
    """Một mục cùng `ngay_tin_hieu` nhưng KHÁC `loai` không phải dấu của bộ này."""
    la = [{"loai": "khac", "ngay_tin_hieu": T, "f": 1.5}]
    j = _so()
    _cho(j, boi_canh=json.dumps({ct.KHOA_NHAT_KY: la}, sort_keys=True))
    _ke_hoach(j)
    sk = clc.chinh_lenh_cho_mot_ma(j, MA, _khung(NEN_MOI), "2026-11-11", ghi=lambda m: None)
    assert sk[0]["trang_thai"] == clc.CHINH and _trade(j)["stop_loss"] == pytest.approx(74_400.0, rel=1e-12)


# ─────────────────────── không đổi gì khi không phải sự kiện ───────────────────────
@pytest.mark.parametrize("gia_dong, trang_thai", [
    (80_000.0, clc.BINH_THUONG),            # f = 1 đúng
    (84_000.0, clc.BINH_THUONG),            # f = 1,05 ĐÚNG ngưỡng: so `>` chặt, không kích hoạt
    (84_000.1, clc.CHINH),                  # vừa quá ngưỡng
    (76_200.0, clc.BINH_THUONG),            # f = 0,9525: nguồn cao hơn nhẹ, trong ngưỡng (76.200 × 1,05 = 80.010)
    (76_000.0, clc.NGUON_CAO_HON),          # f = 0,95 < 1/1,05: không phải dạng sự kiện quyền
])
def test_bang_ngưỡng_f_tinh_tay(gia_dong, trang_thai):
    j = _so()
    _cho(j)
    _ke_hoach(j, gia_dong=gia_dong)
    sk = clc.chinh_lenh_cho_mot_ma(j, MA, _khung([n for n in NEN_MOI if n[0] <= "2026-11-11"]), "2026-11-11",
                                   ghi=lambda m: None)
    assert sk[0]["trang_thai"] == trang_thai
    if trang_thai != clc.CHINH:
        assert _trade(j)["stop_loss"] == SL_CU and _trade(j)["take_profit"] == TP_CU
        assert ct.KHOA_NHAT_KY not in json.loads(_nk(j)["boi_canh"] or "{}")


def test_f_bang_1_lenh_nguyen_ven_ke_ca_khi_phien_khop_gap_xuong_manh_khong_huy_khong_doi():
    """Gap xuống THẬT (không có sự kiện: f = 1) — bộ mới KHÔNG huỷ, KHÔNG đổi cắt lỗ. Huỷ/nâng theo gap làm
    số đẹp lên (Quy tắc 1). Lệnh khớp ở giá mở thấp hơn cắt lỗ và bị cắt lỗ THẬT ở phiên kế."""
    nen = [("2026-11-06", 99.0, 101.0, 98.0, 100.0), ("2026-11-09", 100.0, 101.5, 99.0, 100.5),
           (T, 100.5, 102.0, 99.5, 100.0),
           ("2026-11-11", 85.0, 86.0, 84.0, 85.5),      # gap −15% (vượt biên độ chỉ vì dữ liệu dựng tay)
           ("2026-11-12", 85.5, 87.0, 85.0, 86.0)]
    j = _so()
    _cho(j)
    _ke_hoach(j)
    df = _khung(nen[:4])
    sk = clc.chinh_lenh_cho_mot_ma(j, MA, df, "2026-11-11", ghi=lambda m: None)
    assert sk[0]["trang_thai"] == clc.BINH_THUONG
    t = _trade(j)
    assert t["status"] == "PENDING" and t["stop_loss"] == SL_CU and t["take_profit"] == TP_CU


# ─────────────────────── thiếu dữ liệu: giữ nguyên + cảnh báo ───────────────────────
def test_thieu_dong_ke_hoach_lenh_giu_nguyen_va_in_canh_bao_khong_loi():
    j = _so()
    _cho(j)
    ghi = []
    sk = clc.chinh_lenh_cho_mot_ma(j, MA, _khung(NEN_MOI), "2026-11-11", ghi=ghi.append)
    assert sk[0]["trang_thai"] == clc.KHONG_DO_DUOC
    assert len(ghi) == 1 and ghi[0].startswith("##[warning]chỉnh lệnh chờ FPT #1: không chỉnh")
    assert "ke_hoach.gia_dong" in ghi[0]
    t = _trade(j)
    assert t["stop_loss"] == SL_CU and t["take_profit"] == TP_CU and t["status"] == "PENDING"


def test_ke_hoach_cua_ngay_khac_hoac_ma_khac_khong_duoc_dung():
    j = _so()
    _cho(j)
    _ke_hoach(j, ngay="2026-11-09")
    _ke_hoach(j, ma="HPG")
    sk = clc.chinh_lenh_cho_mot_ma(j, MA, _khung(NEN_MOI), "2026-11-11", ghi=lambda m: None)
    assert sk[0]["trang_thai"] == clc.KHONG_DO_DUOC and _trade(j)["stop_loss"] == SL_CU


def test_gia_dong_rong_hoac_khung_gia_thieu_nen_ngay_tin_hieu_giu_nguyen_va_canh_bao():
    j = _so()
    _cho(j)
    j.db.execute("INSERT INTO ke_hoach (at, symbol, signal_date, gia_dong) VALUES (0, ?, ?, NULL)", (MA, T))
    j.db.commit()
    ghi = []
    assert clc.chinh_lenh_cho_mot_ma(j, MA, _khung(NEN_MOI), "2026-11-11", ghi=ghi.append)[0]["trang_thai"] == \
        clc.KHONG_DO_DUOC
    j2 = _so()
    _cho(j2)
    _ke_hoach(j2)
    ghi2 = []
    khung = _khung([n for n in NEN_MOI if n[0] != T])          # nến ngày tín hiệu vắng
    assert clc.chinh_lenh_cho_mot_ma(j2, MA, khung, "2026-11-11", ghi=ghi2.append)[0]["trang_thai"] == \
        clc.KHONG_DO_DUOC
    assert _trade(j2)["stop_loss"] == SL_CU and ghi and ghi2 and ghi2[0].startswith("##[warning]")
    assert clc.chinh_lenh_cho_mot_ma(j2, MA, None, "2026-11-11", ghi=lambda m: None)[0]["trang_thai"] == \
        clc.KHONG_DO_DUOC


def test_khong_co_dong_nhat_ky_thi_khong_chinh_vi_khong_co_cho_ghi_dau():
    j = _so()
    _cho(j, co_nhat_ky=False)
    _ke_hoach(j)
    ghi = []
    sk = clc.chinh_lenh_cho_mot_ma(j, MA, _khung(NEN_MOI), "2026-11-11", ghi=ghi.append)
    assert sk[0]["trang_thai"] == clc.KHONG_DO_DUOC and "nhật ký" in sk[0]["ly_do"]
    assert _trade(j)["stop_loss"] == SL_CU and len(ghi) == 1 and ghi[0].startswith("##[warning]")


def test_boi_canh_hong_hoac_ghi_nua_chung_thi_hoan_tac_lenh_giu_thang_cu():
    # (a) boi_canh không phải JSON object -> không chỉnh, cảnh báo
    j = _so()
    _cho(j, boi_canh="[1, 2]")
    _ke_hoach(j)
    ghi = []
    sk = clc.chinh_lenh_cho_mot_ma(j, MA, _khung(NEN_MOI), "2026-11-11", ghi=ghi.append)
    assert sk[0]["loi"].startswith("ValueError") and ghi[0].startswith("##[warning]")
    assert _trade(j)["stop_loss"] == SL_CU
    # (b) `trades` đã đổi nhưng ghi nhật ký nổ giữa chừng -> SAVEPOINT hoàn tác cả hai
    j2 = _so()
    _cho(j2)
    _ke_hoach(j2)
    j2.db.execute("CREATE TRIGGER no_giua_chung BEFORE UPDATE ON nhat_ky BEGIN SELECT RAISE(ABORT, 'nổ giữa chừng'); END")
    j2.db.commit()
    ghi2 = []
    sk2 = clc.chinh_lenh_cho_mot_ma(j2, MA, _khung(NEN_MOI), "2026-11-11", ghi=ghi2.append)
    assert "nổ giữa chừng" in sk2[0]["loi"] and "đã hoàn tác" in ghi2[0]
    t = _trade(j2)
    assert t["stop_loss"] == SL_CU and t["take_profit"] == TP_CU


# ─────────────────────── phạm vi: chỉ PENDING của đúng mã ───────────────────────
@pytest.mark.parametrize("trang_thai", ["OPEN", "CLOSING", "CLOSED", "HUY"])
def test_lenh_khong_phai_PENDING_khong_bi_chay_qua(trang_thai):
    j = _so()
    _cho(j, trang_thai=trang_thai)
    _ke_hoach(j)
    assert clc.chinh_lenh_cho_mot_ma(j, MA, _khung(NEN_MOI), "2026-11-11", ghi=lambda m: None) == []
    t = _trade(j)
    assert t["stop_loss"] == SL_CU and t["take_profit"] == TP_CU
    assert ct.KHOA_NHAT_KY not in json.loads(_nk(j)["boi_canh"] or "{}")


def test_chi_chinh_lenh_cua_dung_ma_va_chi_stop_loss_take_profit_boi_canh_doi():
    j = _so()
    _cho(j, id=1)
    _cho(j, id=2, ma="HPG")
    _ke_hoach(j)
    _ke_hoach(j, ma="HPG")
    truoc = dict(_trade(j, 1))
    clc.chinh_lenh_cho_mot_ma(j, MA, _khung(NEN_MOI), "2026-11-11", ghi=lambda m: None)
    assert _trade(j, 2)["stop_loss"] == SL_CU                            # mã khác: nguyên
    sau = dict(_trade(j, 1))
    doi = {k for k in truoc if truoc[k] != sau[k]}
    assert doi == {"stop_loss", "take_profit"}, doi                       # entry · size · status · ngày: nguyên


def test_f_do_lai_moi_luot_tu_khung_gia_he_so_nghin_dong_khong_lam_lech():
    """`price_multiplier` quy nghìn đồng → VNĐ; một khung đã ở VNĐ (> 500) cho hệ số 1 và cùng f."""
    j = _so()
    _cho(j)
    _ke_hoach(j)
    vnd = _khung([(n[0], n[1] * 1000, n[2] * 1000, n[3] * 1000, n[4] * 1000) for n in NEN_MOI])
    sk = clc.chinh_lenh_cho_mot_ma(j, MA, vnd, "2026-11-11", ghi=lambda m: None)
    assert sk[0]["trang_thai"] == clc.CHINH and sk[0]["f"] == pytest.approx(1.25, rel=1e-12)


# ─────────────────────────── gác AST ───────────────────────────
def _nhap(cay):
    ra = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            ra |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            ra.add(n.module.split(".")[0])
    return ra


def _ma_nguon():
    bo = {"tests", ".venv", ".git", "node_modules", "__pycache__"}
    return [p for p in duyet_repo.duyet(GOC, "*.py") if not (set(p.relative_to(GOC).parts) & bo)]


def _ten_goi(n):
    return getattr(n.func, "attr", getattr(n.func, "id", ""))


def test_gac_chi_run_daily_nhap_chinh_lenh_cho_va_loi_giao_dich_khong_bao_gio():
    ai = {p.relative_to(GOC).as_posix() for p in _ma_nguon()
          if "chinh_lenh_cho" in _nhap(ast.parse(p.read_text(encoding="utf-8")))}
    assert ai == {"run_daily.py"}, sorted(ai)
    for ten in ("paper_trading.py", "paper_runner.py", "paper_metrics.py", "walkforward.py", "sheets_store.py",
                "google_sheets_sync.py", "master_agent.py", "san_dau.py", "nhat_ky_vi_sao.py", "su_kien_quyen.py",
                "chinh_thang_gia.py"):
        assert "chinh_lenh_cho" not in _nhap(ast.parse((GOC / ten).read_text(encoding="utf-8"))), ten
    bt = [p for p in duyet_repo.duyet(GOC / "backtest", "*.py")
          if "chinh_lenh_cho" in _nhap(ast.parse(p.read_text(encoding="utf-8")))]
    assert not bt, bt


def test_gac_ngưỡng_DUNG_LAI_tu_chinh_thang_gia_khong_khai_lai_so():
    cay = ast.parse((GOC / "chinh_lenh_cho.py").read_text(encoding="utf-8"))
    assert clc.NGUONG_LECH is ct.NGUONG_LECH and clc.KHOA_NHAT_KY is ct.KHOA_NHAT_KY
    nhap = [n for n in ast.walk(cay) if isinstance(n, ast.ImportFrom) and n.module == "chinh_thang_gia"]
    assert len(nhap) == 1 and {"NGUONG_LECH", "KHOA_NHAT_KY"} <= {a.name for a in nhap[0].names}
    # không số thực nào trong phần mã (ngoài docstring) khai ngưỡng: 0,05 / 0,02 / 1,05 / 5
    so = [n.value for n in ast.walk(cay) if isinstance(n, ast.Constant) and isinstance(n.value, float)]
    assert not so, so
    gan = [t.id for n in ast.walk(cay) if isinstance(n, ast.Assign) for t in n.targets if isinstance(t, ast.Name)]
    assert "NGUONG_LECH" not in gan and "NOI_BIEN" not in gan


def test_gac_module_khong_mang_khong_huy_khong_xoa_chi_ghi_stop_loss_take_profit_va_boi_canh():
    cay = ast.parse((GOC / "chinh_lenh_cho.py").read_text(encoding="utf-8"))
    nhap = _nhap(cay)
    assert not ({"requests", "urllib", "vnstock", "vnstock_data", "gspread", "sheets_store", "google_sheets_sync",
                 "nen_su_kien_quyen", "su_kien_quyen", "paper_runner"} & nhap), nhap
    sql = [n.value.strip() for n in ast.walk(cay) if isinstance(n, ast.Constant) and isinstance(n.value, str)
           and n.value.strip().split(" ")[0].upper() in ("UPDATE", "DELETE", "INSERT")]
    assert sorted(sql) == sorted([
        "UPDATE trades SET stop_loss=?, take_profit=? WHERE id=? AND status=?",
        "UPDATE nhat_ky SET boi_canh=? WHERE trade_id=?"]), sql
    chu = " ".join(n.value for n in ast.walk(cay) if isinstance(n, ast.Constant) and isinstance(n.value, str)
                   and not n.value.startswith("Chỉnh THANG"))
    assert "HUY" not in chu and "Status.HUY" not in ast.unparse(cay)


def _vong_quet_run_daily():
    cay = ast.parse((GOC / "run_daily.py").read_text(encoding="utf-8"))
    ham = next(n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == "execute_daily_scan")
    vong = [n for n in ast.walk(ham) if isinstance(n, ast.For)
            and isinstance(n.iter, ast.Call) and _ten_goi(n.iter) == "enumerate"
            and any(isinstance(a, ast.Name) and a.id == "CUSTOM_WATCHLIST_SYMBOLS" for a in n.iter.args)]
    assert len(vong) == 1
    return cay, vong[0]


def test_gac_run_daily_goi_chinh_lenh_cho_dung_mot_lan_trong_vong_sau_bo_chinh_lenh_mo_truoc_run_session():
    """HÌNH DẠNG AST: một lời gọi, TRONG vòng từng mã, SAU `chinh_thang_mot_ma` (276), TRƯỚC `run_session` (nơi
    `fill_pending` chạy), không nằm dưới `if` nào; chỉ truyền `nguon` (không có cờ/nhân tay)."""
    cay, vong = _vong_quet_run_daily()
    moi = [n for n in ast.walk(cay) if isinstance(n, ast.Call) and _ten_goi(n) == "chinh_lenh_cho_mot_ma"]
    trong = [n for n in ast.walk(vong) if isinstance(n, ast.Call) and _ten_goi(n) == "chinh_lenh_cho_mot_ma"]
    assert len(moi) == 1 and len(trong) == 1
    chinh_mo = [n for n in ast.walk(vong) if isinstance(n, ast.Call) and _ten_goi(n) == "chinh_thang_mot_ma"]
    chay = [n for n in ast.walk(vong) if isinstance(n, ast.Call) and _ten_goi(n) == "run_session"]
    assert len(chinh_mo) == 1 and len(chay) == 1
    assert chinh_mo[0].lineno < trong[0].lineno < chay[0].lineno, (chinh_mo[0].lineno, trong[0].lineno,
                                                                    chay[0].lineno)
    cha = {con: c for c in ast.walk(vong) for con in ast.iter_child_nodes(c)}
    nut = trong[0]
    while nut is not vong:
        nut = cha[nut]
        assert not isinstance(nut, ast.If), "lời gọi bộ chỉnh lệnh chờ không được nằm dưới một `if`"
    assert {k.arg for k in trong[0].keywords} == {"nguon"}
    # nằm trong `try` có `except Exception` in cảnh báo: lỗi không lường trước không bỏ cả mã
    cha_try = trong[0]
    while not isinstance(cha_try, ast.Try):
        cha_try = cha[cha_try]
    assert any(isinstance(h.type, ast.Name) and h.type.id == "Exception" for h in cha_try.handlers)


def test_gac_ham_chinh_cua_276_van_dung_nguyen_blob_khong_bi_dong_vao():
    """`chinh_thang_gia.py` được ĐO 36 ghim bằng blob; BƯỚC 282 thêm module MỚI nên không được chạm nó."""
    import hashlib
    d = (GOC / "chinh_thang_gia.py").read_bytes().replace(b"\r\n", b"\n")
    blob = hashlib.sha1(b"blob %d\x00" % len(d) + d).hexdigest()
    assert blob == "e8bdc1530593d98396fb7b79ca45c4109941fb65"
