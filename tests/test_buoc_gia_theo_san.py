"""BƯỚC 143 — bước giá theo SÀN THẬT (phần dư đã khai ở BƯỚC 136).

`truot_gia.BUOC_GIA` đã có thang HNX/UPCOM (100đ mọi mức giá), nhưng không
đường nào truyền sàn thật vào nó: `run_daily` ghim `"HOSE"` cho mọi mã, và
`_khop_that` · `_gia_ban_that` gọi `dat_lenh` / `truot_gia` với `san` mặc
định. Rổ có 4 mã HNX (PVS · HUT · SHS · MBS) và 3 mã UPCoM (OIL · MSR · ACV)
— đo 29/09/2026, hai nguồn VCI và KBS khớp từng mã sau khi chuẩn hoá nhãn
(VCI ghi `HSX`, KBS ghi `HOSE`).

Hệ quả đo được (`docs/STATE.md` BƯỚC 143): giá vào/ra của mã HNX/UPCoM được
làm tròn theo lưới HOSE — 50đ ở 10–50 nghìn, 10đ dưới 10 nghìn — nên có giá
không thể tồn tại trên sàn thật (HUT vào 13.250đ trên sổ thật), và trượt giá
bị tính THẤP: chiều làm số đẹp lên.

Các phép kiểm ở đây được viết TRƯỚC khi sửa, dưới `xfail(strict=True)`, và
KHÔNG đổi hành vi: phép sửa làm chúng XPASS, strict làm đỏ, và dấu được gỡ.
Ba phép kiểm không mang dấu là phép GHIM — chúng xanh cả trước lẫn sau, và
canh việc phép sửa áp thang HNX cho MỌI mã.
"""
import ast
from pathlib import Path

import pandas as pd
import pytest

import market_filter
import paper_trading as pt
import truot_gia
from paper_trading import PaperTradingJournal, Status

GOC = Path(__file__).resolve().parent.parent

TIN_HIEU = "2026-09-03"
PHIEN_KHOP = "2026-09-04"
PHIEN_SAU = "2026-09-07"

_ngay = pd.bdate_range("2026-07-01", "2026-09-30")
VNI = pd.DataFrame({
    "time": _ngay.strftime("%Y-%m-%d"),
    "close": [1600.0 + i for i in range(len(_ngay))],
    "vni_ma50": [1550.0] * len(_ngay),
})

# Nến mỏng tác động: khối lượng lớn, biên độ 1.000đ — trượt giá chủ yếu là
# phần LÀM TRÒN lên/xuống bước giá, đúng thứ phép sửa đụng tới.
KHOI_LUONG = 3_000_000.0


def _kq(gia: float) -> dict:
    return {
        "final_score": 70, "recommendation": "MUA", "data_quality": "OK",
        "score_breakdown": {}, "key_reasons": [],
        "analyses": {"risk": {"recommendations": {
            "entry_price": gia, "stop_loss_price": gia * 0.95,
            "take_profit_price": gia * 1.2}}},
    }


def _nen(gia_mo: float, tham_chieu: float, bien_do: float = 1_000.0) -> dict:
    return {"high": gia_mo + bien_do / 2, "low": gia_mo - bien_do / 2,
            "volume": KHOI_LUONG, "tham_chieu": tham_chieu}


@pytest.fixture
def moi_truong(monkeypatch):
    monkeypatch.setattr(market_filter, "is_vni_bullish", lambda *a, **k: True)
    monkeypatch.setattr(market_filter, "get_vni_df", lambda: VNI)
    monkeypatch.setattr(pt, "CHO_PHEP_MO_LENH_MOI", True)
    monkeypatch.setattr(pt, "MO_PHONG_TRUOT_GIA", True)


def _khop_vao(so, ma, san, gia_mo):
    """Mở một lệnh chờ rồi khớp nó ở giá mở cửa `gia_mo`; trả giá vào ghi sổ."""
    tid = so.consider_entry(ma, TIN_HIEU, _kq(gia_mo), exchange=san,
                            buy_threshold=50.0)
    if tid is None:
        pytest.fail(f"TIỀN ĐỀ gãy: consider_entry({ma}) không mở lệnh chờ — "
                    f"phép kiểm dưới đây không đo được gì")
    khop = so.fill_pending(ma, PHIEN_KHOP, gia_mo, _nen(gia_mo, gia_mo))
    lenh = so.all_trades()
    if khop != 1 or lenh[0].status != Status.OPEN:
        pytest.fail(f"TIỀN ĐỀ gãy: {ma} khớp={khop}, {[t.status for t in lenh]}")
    return float(lenh[0].entry_price)


def _chia_het(x: float, b: int) -> bool:
    return abs(round(x / b) * b - x) < 1e-6


# ─────────────────────────────────────────────────────────────────────
# GHIM — thang đã có sẵn, và HOSE không được đổi (xanh trước lẫn sau)
# ─────────────────────────────────────────────────────────────────────

def test_GHIM_thang_HNX_UPCOM_la_100d_o_moi_muc_gia():
    for san in ("HNX", "UPCOM"):
        for gia in (5_000, 9_999, 10_000, 30_000, 49_999, 80_000):
            assert truot_gia.buoc_gia(gia, san) == 100, (san, gia)


def test_GHIM_HOSE_van_la_ba_bac_10_50_100():
    assert [truot_gia.buoc_gia(g, "HOSE") for g in (9_999, 10_000, 49_999, 50_000)] \
        == [10, 50, 50, 100]


def test_GHIM_ma_HOSE_van_khop_o_luoi_50d_khong_bi_ep_sang_100d(moi_truong):
    """Phép sửa sai kiểu *áp thang HNX cho mọi mã* làm PDR (HOSE) vào 30.100đ."""
    so = PaperTradingJournal(":memory:")
    gia = _khop_vao(so, "PDR", "HOSE", 30_000.0)
    assert gia == 30_050.0, (
        f"PDR (HOSE) mở cửa 30.000đ phải vào ở 30.050đ (làm tròn LÊN theo lưới "
        f"50đ, cộng tác động), ghi sổ {gia:,.0f}")


# ─────────────────────────────────────────────────────────────────────
# PHÍA VÀO — giá vào của mã HNX/UPCoM phải nằm trên lưới 100đ
# ─────────────────────────────────────────────────────────────────────

_DO = "BƯỚC 143 — sàn thật chưa được truyền vào bước giá"


@pytest.mark.xfail(strict=True, reason=_DO)
@pytest.mark.parametrize("ma, san, gia_mo", [
    ("PVS", "HNX", 30_000.0),       # 10–50 nghìn: HOSE 50đ -> đúng 100đ
    ("HUT", "HNX", 9_000.0),        # dưới 10 nghìn: HOSE 10đ -> đúng 100đ
    ("MSR", "UPCOM", 30_000.0),
    ("OIL", "UPCOM", 9_000.0),
])
def test_gia_VAO_cua_ma_HNX_UPCOM_phai_chia_het_100(moi_truong, ma, san, gia_mo):
    so = PaperTradingJournal(":memory:")
    gia = _khop_vao(so, ma, san, gia_mo)
    assert _chia_het(gia, 100), (
        f"{ma} ({san}) mở cửa {gia_mo:,.0f}đ, vào {gia:,.0f}đ: bước giá {san} là "
        f"100đ nên đây là một giá KHÔNG THỂ tồn tại trên sàn — mã đang được "
        f"làm tròn theo lưới HOSE.")


# ─────────────────────────────────────────────────────────────────────
# PHÍA RA — cả hai đường bán đi qua `_gia_ban_that`
# ─────────────────────────────────────────────────────────────────────

def _mo_vi_the(so, ma, san):
    """Một vị thế đang MỞ: vào ở 30.000đ phiên 04/09."""
    _khop_vao(so, ma, san, 30_000.0)
    return so.all_trades()[0]


@pytest.mark.xfail(strict=True, reason=_DO)
def test_gia_RA_cat_lo_cua_ma_HNX_phai_chia_het_100(moi_truong):
    so = PaperTradingJournal(":memory:")
    lenh = _mo_vi_the(so, "PVS", "HNX")
    sl = float(lenh.stop_loss)                     # 28.500đ
    # mở cửa TRÊN sl, đáy chạm dưới sl -> khớp ở đúng sl, trượt xuống theo lưới
    bar = {"open": sl + 500.0, "high": sl + 1_000.0, "low": sl - 500.0,
           "close": sl, "volume": KHOI_LUONG}
    dong = so.evaluate_open("PVS", PHIEN_SAU, bar)
    assert len(dong) == 1, f"tiền đề gãy: SL không chạm ({dong})"
    gia = float(dong[0]["exit_price"])
    assert _chia_het(gia, 100), (
        f"PVS (HNX) cắt lỗ ở sl {sl:,.0f}đ, ra {gia:,.0f}đ — không nằm trên "
        f"lưới 100đ của sàn thật.")


@pytest.mark.xfail(strict=True, reason=_DO)
def test_gia_RA_theo_tin_hieu_cua_ma_UPCOM_phai_chia_het_100(moi_truong):
    so = PaperTradingJournal(":memory:")
    lenh = _mo_vi_the(so, "MSR", "UPCOM")
    so.db.execute("UPDATE trades SET status=? WHERE id=?",
                  (Status.CLOSING, lenh.id))
    so.db.commit()
    gia_mo = 31_000.0
    n = so.fill_closing("MSR", PHIEN_SAU, gia_mo, _nen(gia_mo, gia_mo))
    ra = [t for t in so.all_trades() if t.status == Status.CLOSED]
    assert n == 1 and len(ra) == 1, f"tiền đề gãy: fill_closing={n}"
    gia = float(ra[0].exit_price)
    assert _chia_het(gia, 100), (
        f"MSR (UPCoM) thoát theo tín hiệu, mở cửa {gia_mo:,.0f}đ, ra {gia:,.0f}đ "
        f"— không nằm trên lưới 100đ.")


# ─────────────────────────────────────────────────────────────────────
# ĐƯỜNG DÂY — `run_daily` không được ghim cứng "HOSE" cho mọi mã
# ─────────────────────────────────────────────────────────────────────

def _lan_goi(ten_ham: str):
    cay = ast.parse((GOC / "run_daily.py").read_text(encoding="utf-8"))
    return [n for n in ast.walk(cay) if isinstance(n, ast.Call)
            and getattr(n.func, "id", getattr(n.func, "attr", None)) == ten_ham]


@pytest.mark.xfail(strict=True, reason=_DO)
def test_run_daily_khong_ghim_HOSE_khi_goi_run_session():
    lan = _lan_goi("run_session")
    assert lan, "tiền đề gãy: run_daily không còn gọi run_session"
    for c in lan:
        # run_session(journal, symbol, df, bar, session_date, exchange, ...)
        arg = c.args[5]
        assert not (isinstance(arg, ast.Constant) and arg.value == "HOSE"), (
            "run_daily truyền cứng \"HOSE\" làm sàn của MỌI mã trong rổ — cột "
            "`exchange` của sổ thật ghi HOSE cả cho PVS · HUT · SHS · MBS · OIL "
            "· MSR · ACV, và bước giá theo thang HOSE.")
