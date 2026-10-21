"""Gác ĐO 28 (BƯỚC 209): sổ ảo KHÔNG khớp được ở phiên KỊCH TRẦN/SÀN MỘT GIÁ.

Nến cao = thấp ở biên độ là phiên trắng một bên: kịch trần thì không ai bán,
kịch sàn thì không ai mua. Trước BƯỚC 209 sổ ảo vẫn khớp ở cả hai chiều — lệnh
mua ở giá trần trong 10% khối lượng nến (`vong_doi_lenh` không có nhánh nào cho
nến một giá), và cắt lỗ ở giá sàn (`_gia_ban_that` cố ý không qua mô hình khớp).
Đo 15–16/10/2026 ngoài repo: lệnh PNJ #897 sổ ghi −7,82%, cổ phiếu khoá sàn 4
phiên, bán ở phiên mở khoá thì ước −30,8%.

Mô hình ghim ở `docs/TIEU-CHI-DOC-TRUOC.md` mục ĐO 28 (ký trước, người dùng
duyệt 20/10/2026): khoá biên = nến một giá VÀ |giá ÷ tham chiếu − 1| ≥ 0,9 ×
biên độ của sàn; mua gặp kịch trần → `HUY`; bán gặp kịch sàn → chờ phiên sau,
phiên mở khoá đầu tiên khớp ở min(SL, giá mở cửa) — đường BƯỚC 123.
"""
import pandas as pd
import pytest

import market_filter
import paper_trading as pt
import vong_doi_lenh as vd
from paper_trading import PaperTradingJournal, Status

TIN_HIEU = "2026-09-03"
PHIEN_KHOP = "2026-09-04"
PHIEN_KHOA = "2026-09-07"
PHIEN_MO_KHOA = "2026-09-08"
KHOI_LUONG = 3_000_000.0
GIA_VAO = 30_000.0
BIEN_HOSE = 0.07


def _kq(gia: float = GIA_VAO) -> dict:
    return {"final_score": 70, "recommendation": "MUA", "data_quality": "OK",
            "score_breakdown": {}, "key_reasons": [],
            "analyses": {"risk": {"recommendations": {
                "entry_price": gia, "stop_loss_price": gia * 0.95,
                "take_profit_price": gia * 1.2}}}}


def _nen_thuong(gia_mo: float, tham_chieu: float) -> dict:
    return {"high": gia_mo + 500.0, "low": gia_mo - 500.0, "volume": KHOI_LUONG,
            "tham_chieu": tham_chieu}


def _nen_mot_gia(tham_chieu: float, doi: float) -> dict:
    """Nến cao = thấp = mở = đóng ở `tham_chieu × (1 + doi)`."""
    g = tham_chieu * (1 + doi)
    return {"open": g, "high": g, "low": g, "close": g, "volume": 50_000.0,
            "tham_chieu": tham_chieu}


@pytest.fixture
def moi_truong(monkeypatch):
    monkeypatch.setattr(market_filter, "is_vni_bullish", lambda *a, **k: True)
    monkeypatch.setattr(pt, "CHO_PHEP_MO_LENH_MOI", True)
    monkeypatch.setattr(pt, "MO_PHONG_TRUOT_GIA", True)


def _lenh_cho(so, ma="FPT", san="HOSE"):
    tid = so.consider_entry(ma, TIN_HIEU, _kq(), exchange=san, buy_threshold=50.0)
    if tid is None:
        pytest.fail("TIỀN ĐỀ gãy: consider_entry không mở lệnh chờ")
    return tid


def _vi_the(so, ma="FPT", san="HOSE"):
    _lenh_cho(so, ma, san)
    so.fill_pending(ma, PHIEN_KHOP, GIA_VAO, _nen_thuong(GIA_VAO, GIA_VAO))
    t = so.all_trades()[0]
    if t.status != Status.OPEN:
        pytest.fail(f"TIỀN ĐỀ gãy: lệnh không mở ({t.status})")
    return t


# ─────────────────────────────────────────────────────────────────────
# 1. Hàm thuần `vong_doi_lenh.khoa_bien`
# ─────────────────────────────────────────────────────────────────────

def test_KHOA_BIEN_nhan_dung_KICH_TRAN_va_KICH_SAN():
    assert vd.khoa_bien(_nen_mot_gia(30_000.0, +0.069), BIEN_HOSE) == vd.KICH_TRAN
    assert vd.khoa_bien(_nen_mot_gia(30_000.0, -0.069), BIEN_HOSE) == vd.KICH_SAN


def test_KHOA_BIEN_nen_HAI_gia_khong_phai_khoa_du_sat_bien():
    nen = {"high": 32_100.0, "low": 32_000.0, "tham_chieu": 30_000.0}
    assert vd.khoa_bien(nen, BIEN_HOSE) is None


def test_KHOA_BIEN_nen_mot_gia_KHONG_sat_bien_khong_phai_khoa():
    """108 nến một giá trong cache (VCF 100 cổ phiếu, KOS, DCL) không sát biên."""
    assert vd.khoa_bien(_nen_mot_gia(30_000.0, -0.01), BIEN_HOSE) is None
    assert vd.khoa_bien(_nen_mot_gia(30_000.0, +0.03), BIEN_HOSE) is None
    assert vd.khoa_bien(_nen_mot_gia(30_000.0, 0.0), BIEN_HOSE) is None


def test_KHOA_BIEN_dung_bien_do_CUA_SAN_va_he_so_0_9():
    """+7% một giá: kịch trần ở HOSE (7%), KHÔNG ở HNX (10%)."""
    nen = _nen_mot_gia(30_000.0, +0.07)
    assert vd.khoa_bien(nen, 0.07) == vd.KICH_TRAN
    assert vd.khoa_bien(nen, 0.10) is None
    # biên của hệ số 0,9: 0,9 × 7% = 6,3%
    assert vd.khoa_bien(_nen_mot_gia(30_000.0, +0.0635), 0.07) == vd.KICH_TRAN
    assert vd.khoa_bien(_nen_mot_gia(30_000.0, +0.0625), 0.07) is None
    assert vd.TY_LE_NHAN_KHOA_BIEN == 0.9


def test_KHOA_BIEN_thieu_tham_chieu_thi_khong_phan_duoc():
    nen = _nen_mot_gia(30_000.0, -0.069)
    del nen["tham_chieu"]
    assert vd.khoa_bien(nen, BIEN_HOSE) is None


# ─────────────────────────────────────────────────────────────────────
# 2. Chiều MUA
# ─────────────────────────────────────────────────────────────────────

def test_MUA_o_phien_KICH_TRAN_khong_khop_HUY_voi_ly_do_rieng(moi_truong):
    so = PaperTradingJournal(":memory:")
    _lenh_cho(so)
    n = so.fill_pending("FPT", PHIEN_KHOP, GIA_VAO * 1.069, _nen_mot_gia(GIA_VAO, +0.069))
    t = so.all_trades()[0]
    assert n == 0 and t.status == Status.HUY, (
        f"lệnh mua khớp ở phiên kịch trần một giá (trắng bên bán): {t.status}")
    assert t.entry_price is None
    assert t.exit_reason == pt.LY_DO_KICH_TRAN != pt.LY_DO_TU_CHOI_LENH


def test_MUA_o_phien_KICH_SAN_van_khop(moi_truong):
    """Kịch sàn thì bên bán dư — mua được; mô hình không được chặn chiều này."""
    so = PaperTradingJournal(":memory:")
    _lenh_cho(so)
    nen = _nen_mot_gia(GIA_VAO, -0.069)
    n = so.fill_pending("FPT", PHIEN_KHOP, nen["open"], nen)
    assert n == 1 and so.all_trades()[0].status == Status.OPEN


# ─────────────────────────────────────────────────────────────────────
# 3. Chiều BÁN — cắt lỗ và lệnh chờ bán
# ─────────────────────────────────────────────────────────────────────

def test_CAT_LO_o_phien_KICH_SAN_cho_va_khop_o_gia_MO_CUA_phien_mo_khoa(moi_truong):
    """Hình dạng của PNJ #897: chạm SL ở phiên khoá sàn, phiên mở khoá mở thấp hơn nữa."""
    so = PaperTradingJournal(":memory:")
    t = _vi_the(so)
    sl = float(t.stop_loss)
    khoa = _nen_mot_gia(GIA_VAO, -0.069)
    assert khoa["low"] <= sl, "tiền đề gãy: phiên khoá không chạm SL"
    assert so.evaluate_open("FPT", PHIEN_KHOA, khoa, current_score=70) == []
    assert so.all_trades()[0].status == Status.OPEN, "cắt lỗ khớp được ở phiên trắng bên mua"

    gia_mo = khoa["close"] * 0.95
    mo_khoa = {"open": gia_mo, "high": gia_mo + 300.0, "low": gia_mo - 300.0,
               "close": gia_mo, "volume": KHOI_LUONG, "tham_chieu": khoa["close"]}
    dong = so.evaluate_open("FPT", PHIEN_MO_KHOA, mo_khoa, current_score=70)
    assert len(dong) == 1 and dong[0]["reason"] == pt.ExitReason.STOP_LOSS
    t = so.all_trades()[0]
    assert t.status == Status.CLOSED and str(t.exit_date)[:10] == PHIEN_MO_KHOA
    assert float(t.exit_price) <= gia_mo < sl, (
        f"phiên mở khoá phải khớp ở giá mở cửa {gia_mo:,.0f} (trừ trượt), "
        f"không ở SL {sl:,.0f}: ra {float(t.exit_price):,.0f}")


def test_CAT_LO_o_nen_mot_gia_KHONG_sat_bien_van_dong_nhu_cu(moi_truong):
    so = PaperTradingJournal(":memory:")
    t = _vi_the(so)
    sl = float(t.stop_loss)
    nen = {"open": sl - 100.0, "high": sl - 100.0, "low": sl - 100.0,
           "close": sl - 100.0, "volume": 50_000.0, "tham_chieu": sl + 200.0}
    assert vd.khoa_bien(nen, BIEN_HOSE) is None, "tiền đề gãy: nến này không được là khoá"
    assert len(so.evaluate_open("FPT", PHIEN_KHOA, nen, current_score=70)) == 1


def test_LENH_CHO_BAN_o_phien_KICH_SAN_cho_phien_sau(moi_truong):
    so = PaperTradingJournal(":memory:")
    t = _vi_the(so)
    so.db.execute("UPDATE trades SET status=?, exit_date=?, exit_reason=? WHERE id=?",
                  (Status.CLOSING, PHIEN_KHOP, pt.ExitReason.SIGNAL_REVERSED, t.id))
    so.db.commit()
    khoa = _nen_mot_gia(GIA_VAO, -0.069)
    assert so.fill_closing("FPT", PHIEN_KHOA, khoa["open"], khoa) == 0
    assert so.all_trades()[0].status == Status.CLOSING
    gia_mo = khoa["close"] * 0.97
    assert so.fill_closing("FPT", PHIEN_MO_KHOA, gia_mo,
                           _nen_thuong(gia_mo, khoa["close"])) == 1
    t = so.all_trades()[0]
    assert t.status == Status.CLOSED and str(t.exit_date)[:10] == PHIEN_MO_KHOA


def test_LENH_CHO_BAN_o_phien_KICH_TRAN_van_khop(moi_truong):
    """Kịch trần thì bên mua dư — bán được."""
    so = PaperTradingJournal(":memory:")
    t = _vi_the(so)
    so.db.execute("UPDATE trades SET status=?, exit_date=? WHERE id=?",
                  (Status.CLOSING, PHIEN_KHOP, t.id))
    so.db.commit()
    tran = _nen_mot_gia(GIA_VAO, +0.069)
    assert so.fill_closing("FPT", PHIEN_KHOA, tran["open"], tran) == 1


def test_BIEN_DO_tra_theo_SAN_cua_MA_ma_HNX_khong_khoa_o_7_phan_tram(moi_truong):
    """PVS (HNX, biên 10%): một giá −6,9% chưa sát biên nên cắt lỗ khớp như cũ;
    −9,5% mới là kịch sàn. Ghim cứng biên HOSE thì mã HNX/UPCoM bị giữ oan."""
    so = PaperTradingJournal(":memory:")
    _vi_the(so, "PVS", "HNX")
    assert len(so.evaluate_open("PVS", PHIEN_KHOA, _nen_mot_gia(GIA_VAO, -0.069),
                                current_score=70)) == 1

    so2 = PaperTradingJournal(":memory:")
    _vi_the(so2, "PVS", "HNX")
    assert so2.evaluate_open("PVS", PHIEN_KHOA, _nen_mot_gia(GIA_VAO, -0.095),
                             current_score=70) == []


def test_KICH_SAN_khong_cham_SL_van_dat_lenh_cho_ban_theo_tin_hieu(moi_truong):
    """Phiên khoá sàn chỉ chặn KHỚP, không chặn QUYẾT ĐỊNH: tín hiệu ra (điểm < 45,
    lệnh đang lỗ) vẫn đặt lệnh chờ bán ngay phiên ấy; khớp ở phiên sau qua
    `fill_closing`. Bỏ qua cả lượt xét ở phiên khoá thì lệnh ra trễ một phiên."""
    so = PaperTradingJournal(":memory:")
    t = _vi_the(so)
    khoa = _nen_mot_gia(GIA_VAO * 1.05, -0.069)     # khoá sàn nhưng còn trên SL
    assert vd.khoa_bien(khoa, BIEN_HOSE) == vd.KICH_SAN
    assert khoa["low"] > float(t.stop_loss), "tiền đề gãy: phiên khoá chạm SL"
    so.evaluate_open("FPT", PHIEN_KHOA, khoa, current_score=pt.EXIT_SIGNAL_THRESHOLD - 10)
    assert so.all_trades()[0].status == Status.CLOSING


# ─────────────────────────────────────────────────────────────────────
# 4. Công tắc tầng 2 — tắt thì KHÔNG đổi gì
# ─────────────────────────────────────────────────────────────────────

def test_TAT_TRUOT_GIA_thi_cat_lo_van_khop_o_phien_khoa(moi_truong, monkeypatch):
    """Khoá biên thuộc tầng 2 (vòng đời lệnh), sau cùng công tắc `MO_PHONG_TRUOT_GIA`."""
    so = PaperTradingJournal(":memory:")
    _vi_the(so)
    monkeypatch.setattr(pt, "MO_PHONG_TRUOT_GIA", False)
    dong = so.evaluate_open("FPT", PHIEN_KHOA, _nen_mot_gia(GIA_VAO, -0.069),
                            current_score=70)
    assert len(dong) == 1


# ─────────────────────────────────────────────────────────────────────
# 5. Đường dây — `run_session` phải đưa giá tham chiếu tới `evaluate_open`
# ─────────────────────────────────────────────────────────────────────

def test_RUN_SESSION_dua_THAM_CHIEU_toi_evaluate_open(moi_truong, monkeypatch):
    """Không có tham chiếu thì `khoa_bien` không phân được, và mô hình mới chết
    lặng lẽ trên mọi đường chạy thật lẫn walk-forward."""
    import paper_runner as pr

    so = PaperTradingJournal(":memory:")
    _vi_the(so)
    monkeypatch.setattr(pr, "_analyze", lambda *a, **k: _kq())
    ngay = pd.bdate_range("2026-06-01", PHIEN_KHOA).strftime("%Y-%m-%d")
    dong_cua = [GIA_VAO / 1000.0] * (len(ngay) - 1)
    khoa = round(GIA_VAO / 1000.0 * 0.931, 2)          # −6,9%, đơn vị nghìn đồng
    df = pd.DataFrame({"time": list(ngay), "open": dong_cua + [khoa],
                       "high": dong_cua + [khoa], "low": dong_cua + [khoa],
                       "close": dong_cua + [khoa],
                       "volume": [KHOI_LUONG] * (len(ngay) - 1) + [50_000.0]})
    bar = {"open": khoa, "high": khoa, "low": khoa, "close": khoa, "volume": 50_000.0}
    tk = pr.run_session(so, "FPT", df, bar, PHIEN_KHOA)
    assert tk["closed"] == 0 and so.all_trades()[0].status == Status.OPEN, (
        "run_session đóng lệnh ở phiên khoá sàn — evaluate_open không nhận được "
        "giá tham chiếu, hoặc mô hình khoá biên không chạy trên đường này")
