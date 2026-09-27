"""Gác của `nhat_ky_vi_sao.py` — P2a, nhật ký "vì sao" (BƯỚC 131).

Phép kiểm đứng đầu là quyết định 1 của module: sau khi trailing NÂNG
`stop_loss`, R vẫn phải tính trên cắt lỗ BAN ĐẦU. Đó đúng là thứ sổ lệnh
đánh mất, và là lý do nhật ký phải ghi lúc khớp chứ không suy lại về sau.
"""
import ast
import dataclasses
import json
from pathlib import Path

import pytest

import nhat_ky_vi_sao as nk
from paper_trading import ExitReason, Status, Trade

GOC = Path(__file__).resolve().parent.parent

DIEM = {"trend_score": 100, "momentum_score": 62.5, "volume_score": 80,
        "sr_score": 40, "risk_score": 20, "news_score": 50,
        "fundamental_score": None, "tv_bonus": 0, "debate_adjustment": 0}


def _lenh(**thay) -> Trade:
    t = Trade(id=7, symbol="FPT", signal_date="2026-09-25 00:00:00",
              entry_date="2026-09-26", entry_price=100.0, exit_date=None,
              exit_price=None, exit_reason=None, stop_loss=95.0,
              take_profit=115.0, size_pct=20.0, entry_score=65,
              status=Status.OPEN)
    return dataclasses.replace(t, **thay)


def _vao(**thay):
    return nk.dong_vao_lenh(_lenh(**thay), json.dumps(DIEM), ["xu hướng tăng"],
                            {"vni_tren_ma50": True, "data_quality": "OK", "nguong": 62})


def _dong(dong, **thay):
    t = _lenh(status=Status.CLOSED, exit_date="2026-10-03",
              exit_price=110.0, exit_reason=ExitReason.SIGNAL_REVERSED)
    return dataclasses.replace(t, **thay)


# ── quyết định 1: cắt lỗ BAN ĐẦU ─────────────────────────────────────────

def test_R_tinh_tren_SL_BAN_DAU_ke_ca_khi_trailing_da_NANG_stop():
    d = _vao()                                     # khớp: SL 95
    t = _dong(d, stop_loss=108.0, exit_price=108.0,  # trailing nâng tới 108 rồi cắt
              exit_reason=ExitReason.STOP_LOSS)
    moi = nk.dong_dong_lenh(d, t, ro_chuan_pct=1.0)
    assert moi["stop_loss_ban_dau"] == 95.0
    assert moi["ket_qua_R"] == pytest.approx(t.net_return_pct() / 5.0)
    assert "ĐÃ NÂNG" in moi["hau_kiem_may"]


def test_VAO_tu_choi_lenh_CHUA_KHOP_va_lenh_DA_QUA_luc_khop():
    with pytest.raises(ValueError, match="chưa khớp"):
        _vao(status=Status.PENDING, entry_price=None, entry_date=None)
    for st in (Status.CLOSING, Status.CLOSED):
        with pytest.raises(ValueError, match="OPEN"):
            _vao(status=st)


# ── R và rủi ro ──────────────────────────────────────────────────────────

def test_RUI_RO_va_R_so_don_gian():
    assert nk.rui_ro_pct(100.0, 95.0) == pytest.approx(5.0)
    assert nk.ket_qua_R(10.0, 5.0) == pytest.approx(2.0)
    assert nk.ket_qua_R(-5.0, 5.0) == pytest.approx(-1.0)


@pytest.mark.parametrize("gia_vao, sl", [(100.0, 100.0), (100.0, 103.0)])
def test_KHONG_co_R_khi_rui_ro_KHONG_DUONG_va_giu_dau_rui_ro(gia_vao, sl):
    rr = nk.rui_ro_pct(gia_vao, sl)
    assert rr <= 0                                  # giữ dấu, không kẹp
    assert nk.ket_qua_R(-4.0, rr) is None
    d = _vao(entry_price=gia_vao, stop_loss=sl)
    assert nk.dong_dong_lenh(d, _dong(d, entry_price=gia_vao, stop_loss=sl),
                             ro_chuan_pct=0.0)["ket_qua_R"] is None


def test_KHONG_co_R_khi_thieu_du_lieu():
    assert nk.rui_ro_pct(None, 95.0) is None
    assert nk.rui_ro_pct(100.0, None) is None
    assert nk.ket_qua_R(None, 5.0) is None


# ── quyết định 2: một công thức phí, một phép so rổ ──────────────────────

def test_LOI_NHUAN_ROng_la_net_return_pct_va_ALPHA_la_rong_tru_ro():
    d = _vao()
    t = _dong(d)
    moi = nk.dong_dong_lenh(d, t, ro_chuan_pct=3.0)
    assert moi["loi_nhuan_rong_pct"] == t.net_return_pct()
    assert moi["alpha_pct"] == pytest.approx(t.net_return_pct() - 3.0)


def test_MODULE_khong_co_CONG_THUC_PHI_thu_hai():
    """AST: gọi `net_return_pct`, và không chạm tới hằng số phí nào."""
    cay = ast.parse((GOC / "nhat_ky_vi_sao.py").read_text(encoding="utf-8"))
    ten = {n.id for n in ast.walk(cay) if isinstance(n, ast.Name)}
    thuoc_tinh = {n.attr for n in ast.walk(cay) if isinstance(n, ast.Attribute)}
    assert "net_return_pct" in thuoc_tinh
    phi = {"BROKER_FEE_PCT", "EXCHANGE_FEE_PCT", "SELL_TAX_PCT",
           "ROUND_TRIP_COST_PCT"}
    assert not (phi & (ten | thuoc_tinh)), phi & (ten | thuoc_tinh)
    assert "gross_return_pct" not in thuoc_tinh


def test_KHONG_co_ro_thi_KHONG_co_alpha_va_NOI_RA():
    d = _vao()
    moi = nk.dong_dong_lenh(d, _dong(d), ro_chuan_pct=None)
    assert moi["alpha_pct"] is None
    assert "chưa có rổ chuẩn" in moi["hau_kiem_may"]


# ── quyết định 3: hậu kiểm máy ───────────────────────────────────────────

def test_HAU_KIEM_gap_DUOI_cat_lo_ban_dau_va_lo_VUOT_1R():
    d = _vao()
    t = _dong(d, exit_price=90.0, exit_reason=ExitReason.STOP_LOSS)  # gap từ SL 95
    moi = nk.dong_dong_lenh(d, t, ro_chuan_pct=0.5)
    assert moi["ket_qua_R"] < -1.0
    assert "thoát DƯỚI cắt lỗ ban đầu" in moi["hau_kiem_may"]
    assert "vượt mức rủi ro dự kiến 1R" in moi["hau_kiem_may"]
    assert moi["hau_kiem_may"].startswith("THUA")
    assert "thua rổ" in moi["hau_kiem_may"]


def test_NGUONG_1R_ca_giua_hai_bien():
    """R ~ -1,3: gap NHẸ dưới SL. Ca -2,09 ở trên không phân biệt được -1 với -2."""
    d = _vao()
    moi = nk.dong_dong_lenh(d, _dong(d, exit_price=94.0, exit_reason=ExitReason.STOP_LOSS),
                            ro_chuan_pct=0.0)
    assert -2.0 < moi["ket_qua_R"] < -1.0
    assert "vượt mức rủi ro dự kiến 1R" in moi["hau_kiem_may"]
    vua = nk.dong_dong_lenh(d, _dong(d, exit_price=95.5, exit_reason=ExitReason.STOP_LOSS),
                            ro_chuan_pct=0.0)
    assert -1.0 < vua["ket_qua_R"] < 0
    assert "1R" not in vua["hau_kiem_may"]


def test_HAU_KIEM_HOA_khi_loi_nhuan_rong_BANG_0():
    nhan = nk.hau_kiem_may(sl_ban_dau=95.0, exit_price=100.5, exit_reason="",
                           loi_nhuan_rong_pct=0.0, R=0.0, alpha=None, diem={})
    assert nhan[0] == "HOÀ"


def test_HAU_KIEM_THANG_vuot_ro_va_KHONG_gan_nhan_gap():
    d = _vao()
    moi = nk.dong_dong_lenh(d, _dong(d), ro_chuan_pct=1.0)
    hk = moi["hau_kiem_may"]
    assert hk.startswith("THẮNG") and "vượt rổ" in hk
    assert "DƯỚI cắt lỗ" not in hk and "ĐÃ NÂNG" not in hk and "1R" not in hk


def test_XEP_HANG_agent_BO_news_hang_so_va_fundamental_trong_so_0():
    d = _vao()
    hk = nk.dong_dong_lenh(d, _dong(d), ro_chuan_pct=1.0)["hau_kiem_may"]
    assert "cao nhất lúc vào: trend 100" in hk
    assert "thấp nhất: risk 20" in hk
    assert "news" not in hk and "fundamental" not in hk
    assert set(nk.KHOA_KHONG_XEP_HANG) == {"news_score", "fundamental_score"}


def test_HAU_KIEM_tat_dinh():
    d = _vao()
    a = nk.dong_dong_lenh(d, _dong(d), ro_chuan_pct=1.0)["hau_kiem_may"]
    b = nk.dong_dong_lenh(_vao(), _dong(d), ro_chuan_pct=1.0)["hau_kiem_may"]
    assert a == b


# ── hợp đồng cột ─────────────────────────────────────────────────────────

def test_MOI_DONG_mang_DUNG_bo_cot_hop_dong():
    d = _vao()
    assert tuple(d) == nk.COT_NHAT_KY
    assert len(set(nk.COT_NHAT_KY)) == len(nk.COT_NHAT_KY)
    moi = nk.dong_dong_lenh(d, _dong(d), ro_chuan_pct=1.0)
    assert tuple(moi) == nk.COT_NHAT_KY
    assert moi["hau_kiem_loi"] is None               # P2c — chưa có
    for c in ("trade_id", "symbol", "signal_date", "entry_date", "entry_price",
              "stop_loss_ban_dau", "rui_ro_pct", "entry_score", "diem_agent",
              "ly_do", "boi_canh"):
        assert moi[c] == d[c], f"nửa ĐÓNG đã đổi cột VÀO {c}"


def test_NGAY_chuan_hoa_10_ky_tu():
    d = _vao()
    assert d["signal_date"] == "2026-09-25" and len(d["entry_date"]) == 10


def test_DONG_tu_choi_LECH_lenh_va_lenh_CHUA_DONG():
    d = _vao()
    with pytest.raises(ValueError, match="lệnh 7"):
        nk.dong_dong_lenh(d, _dong(d, id=8), ro_chuan_pct=0.0)
    with pytest.raises(ValueError, match="chưa đóng"):
        nk.dong_dong_lenh(d, _lenh(), ro_chuan_pct=0.0)
