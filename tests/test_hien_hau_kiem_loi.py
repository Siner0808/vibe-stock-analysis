"""Hiện hậu kiểm bằng lời (B1, BƯỚC 205): bản tin + vế "có lời" của chuông bài học.

Bản tin chỉ hiện bản `DAT` mới nhất (`hau_kiem_loi.ban_moi_nhat`), và chỉ in dòng hậu
kiểm lời khi người gọi CÓ truyền tab `hau_kiem` — không biết thì không nói "chưa có".
Chuông: B1 chưa bật (`NGAY_HAU_KIEM_LOI_BAT_DAU` None) thì vế ấy không đo, không đổi mã
thoát, và không chạm Sheets; đã bật thì lệnh quá một phiên chưa có dòng `DAT` là VI PHẠM.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import ban_tin as bt
import hau_kiem_loi as hkl
import nhat_ky_vi_sao as nk
from paper_trading import ExitReason, Status, Trade

GOC = Path(__file__).resolve().parent.parent
NGAY = "2026-10-28"


def _nap_chuong():
    spec = importlib.util.spec_from_file_location(
        "chuong_bai_hoc_hk", GOC / "tools" / "chuong_bai_hoc.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


CHUONG = _nap_chuong()


def _hk(trade_id=7, lan=1, trang_thai=hkl.TT_DAT, **doi):
    d = {c: None for c in hkl.COT_HAU_KIEM}
    d.update(trade_id=trade_id, lan=lan, trang_thai=trang_thai,
             ke_lai=f"kể lại lần {lan}", khong_chung_minh="không chứng minh",
             theo_doi="Chưa kiểm: x", kien_thuc="kiến thức")
    d.update(doi)
    return d


def _ban_tin(hau_kiem):
    lenh = [{"id": 7, "symbol": "HPG", "exit_reason": "STOP_LOSS", "status": Status.CLOSED,
             "exit_date": NGAY, "entry_date": "2026-10-20"}]
    dong = {c: None for c in nk.COT_NHAT_KY}
    dong.update(trade_id=7, symbol="HPG", exit_date=NGAY, loi_nhuan_rong_pct=-5.2,
                ket_qua_R=-1.0, alpha_pct=-4.1, hau_kiem_may="THUA")
    return bt.lap_ban_tin([], lenh, [dong], None, NGAY, 62, hau_kiem=hau_kiem)


# ── Bản tin ──────────────────────────────────────────────────────────────

def test_BAN_TIN_hien_ban_DAT_moi_nhat_va_nhan():
    b = _ban_tin([_hk(lan=1), _hk(lan=2), _hk(lan=3, trang_thai=hkl.TT_BI_BAC)])
    assert b.hoc[0].hau_kiem_loi["ke_lai"] == "kể lại lần 2"
    md = bt.ban_tin_markdown(b)
    assert hkl.NHAN_HIEN in md and "kể lại lần 2" in md
    assert "kể lại lần 3" not in md
    for t in hkl.TRUONG:
        assert hkl.NHAN_TRUONG[t] in md


def test_BAN_TIN_co_tab_ma_chua_co_ban_DAT_thi_noi_CHUA_CO():
    md = bt.ban_tin_markdown(_ban_tin([_hk(trang_thai=hkl.TT_BI_BAC)]))
    assert bt.CAU_CHUA_CO_LOI in md and "kể lại" not in md


def test_BAN_TIN_khong_truyen_tab_thi_KHONG_in_dong_hau_kiem_loi():
    md = bt.ban_tin_markdown(_ban_tin(None))
    assert bt.CAU_CHUA_CO_LOI not in md and hkl.NHAN_HIEN not in md


# ── Chuông: vế "có lời" ──────────────────────────────────────────────────

def _trade(i, ra):
    return Trade(id=i, symbol="AAA", signal_date="2026-10-19", entry_date="2026-10-20",
                 entry_price=100.0, exit_date=ra, exit_price=95.0,
                 exit_reason=ExitReason.STOP_LOSS, stop_loss=95.0, take_profit=120.0,
                 size_pct=5.0, entry_score=70, status=Status.CLOSED, created_at=2_000.0)


def _dong_nk(i, ra):
    d = {c: None for c in nk.COT_NHAT_KY}
    d.update(trade_id=i, symbol="AAA", signal_date="2026-10-19", entry_date="2026-10-20",
             exit_date=ra, loi_nhuan_rong_pct=-2.0, ro_chuan_pct=0.5)
    return d


def test_CHUONG_B1_chua_bat_khong_do_va_khong_doi_ma(monkeypatch):
    monkeypatch.setattr(hkl, "NGAY_HAU_KIEM_LOI_BAT_DAU", None)
    ma, dong, _ = CHUONG.kiem([_trade(1, "2026-10-28")], [_dong_nk(1, "2026-10-28")], "2026-11-03")
    assert ma == CHUONG.MA_XANH
    assert "Vế có lời (B1): chưa bật — chưa đo." in dong


def test_CHUONG_B1_da_bat_qua_han_khong_DAT_la_VI_PHAM_va_dong_dau_noi_ve_loi(monkeypatch):
    monkeypatch.setattr(hkl, "NGAY_HAU_KIEM_LOI_BAT_DAU", "2026-10-26")
    t, d = [_trade(1, "2026-10-28")], [_dong_nk(1, "2026-10-28")]
    ma, dong, _ = CHUONG.kiem(t, d, "2026-11-03", dong_hk=[])
    assert ma == CHUONG.MA_VI_PHAM
    assert dong[0].startswith("Vế có lời (B1, từ 2026-10-26)")
    ma, dong, _ = CHUONG.kiem(t, d, "2026-11-03", dong_hk=[_hk(trade_id=1)])
    assert ma == CHUONG.MA_XANH


def test_CHUONG_B1_chua_bat_thi_KHONG_cham_Sheets(monkeypatch):
    monkeypatch.setattr(hkl, "NGAY_HAU_KIEM_LOI_BAT_DAU", None)

    class _Hong:
        def read_rows(self, tab):
            raise AssertionError("chạm Sheets khi B1 chưa bật")

    assert CHUONG.doc_hau_kiem(_Hong()) == []
