"""Gác ĐO 29 (BƯỚC 212): walk-forward xét LỆNH ĐẶT SẴN (cắt lỗ) ở MỌI phiên.

Walk-forward chấm cách `stride` (2) phiên và ghé thêm phiên CHỈ-KHỚP ở giữa để
lệnh vào khớp đúng T+1 (ĐO 2). Trước BƯỚC 212 phiên chỉ-khớp trả về TRƯỚC
`evaluate_open`, nên một cây thủng cắt lỗ ở phiên ấy vô hình tới phiên chấm sau
và lệnh khớp ở giá phiên sau. Ca thật (BƯỚC 209): GIL phiên mở khoá 21/12/2022 mở
13,59 dưới SL 18,139 xa; 21/12 là phiên chỉ-khớp nên lệnh ra 22/12 ở 16.200.

Mô hình ghim ở `docs/TIEU-CHI-DOC-TRUOC.md` mục ĐO 29 (ký `c4d01ed`, người dùng
duyệt 20/10/2026): ở phiên chỉ-khớp, SAU `fill_pending` và `fill_closing`, xét
lệnh đặt sẵn ĐÚNG như nhánh cắt lỗ của `evaluate_open` — một bản mã, không chép;
nâng stop, thoát theo tín hiệu, trần thời gian vẫn chỉ ở phiên chấm.
"""
import ast
from pathlib import Path

import pandas as pd
import pytest

import market_filter
import paper_runner as pr
import paper_trading as pt
from paper_trading import PaperTradingJournal, Status

GOC = Path(__file__).resolve().parent.parent
TIN_HIEU = "2026-09-03"
PHIEN_KHOP = "2026-09-04"
PHIEN_CHI_KHOP = "2026-09-07"
PHIEN_SAU = "2026-09-08"
GIA_VAO = 30_000.0
KHOI_LUONG = 3_000_000.0


def _kq(gia: float = GIA_VAO) -> dict:
    return {"final_score": 70, "recommendation": "MUA", "data_quality": "OK",
            "score_breakdown": {}, "key_reasons": [],
            "analyses": {"risk": {"recommendations": {
                "entry_price": gia, "stop_loss_price": gia * 0.95,
                "take_profit_price": gia * 1.2}}}}


@pytest.fixture
def moi_truong(monkeypatch):
    monkeypatch.setattr(market_filter, "is_vni_bullish", lambda *a, **k: True)
    monkeypatch.setattr(pt, "CHO_PHEP_MO_LENH_MOI", True)
    monkeypatch.setattr(pt, "MO_PHONG_TRUOT_GIA", True)

    def _khong_cham(*a, **k):
        pytest.fail("phiên chỉ-khớp gọi `_analyze` — nó không được chấm điểm")
    monkeypatch.setattr(pr, "_analyze", _khong_cham)


def _lenh_cho(so):
    tid = so.consider_entry("FPT", TIN_HIEU, _kq(), exchange="HOSE", buy_threshold=50.0)
    if tid is None:
        pytest.fail("TIỀN ĐỀ gãy: consider_entry không mở lệnh chờ")
    return tid


def _vi_the(so):
    _lenh_cho(so)
    so.fill_pending("FPT", PHIEN_KHOP, GIA_VAO,
                    {"high": GIA_VAO + 500.0, "low": GIA_VAO - 500.0,
                     "volume": KHOI_LUONG, "tham_chieu": GIA_VAO})
    t = so.all_trades()[0]
    if t.status != Status.OPEN:
        pytest.fail(f"TIỀN ĐỀ gãy: lệnh không mở ({t.status})")
    return t


def _phien(so, ngay: str, mo: float, cao: float, thap: float, dong: float,
           chi_khop: bool = True, khoi_luong: float = KHOI_LUONG) -> dict:
    """`run_session` một phiên, giá theo NGHÌN ĐỒNG như cache; các phiên trước
    đứng ở `GIA_VAO` (tham chiếu = giá đóng cửa phiên trước)."""
    ngay_cu = pd.bdate_range("2026-06-01", ngay).strftime("%Y-%m-%d")
    nen = [GIA_VAO / 1000.0] * (len(ngay_cu) - 1)
    df = pd.DataFrame({"time": list(ngay_cu), "open": nen + [mo], "high": nen + [cao],
                       "low": nen + [thap], "close": nen + [dong],
                       "volume": [KHOI_LUONG] * (len(ngay_cu) - 1) + [khoi_luong]})
    bar = {"open": mo, "high": cao, "low": thap, "close": dong, "volume": khoi_luong}
    return pr.run_session(so, "FPT", df, bar, ngay, chi_khop=chi_khop)


# ─────────────────────────────────────────────────────────────────────
# 1. Phiên chỉ-khớp XÉT cắt lỗ, khớp ở min(SL, giá mở cửa)
# ─────────────────────────────────────────────────────────────────────

def test_PHIEN_CHI_KHOP_cat_lo_KHOP_o_min_SL_gia_mo_cua(moi_truong):
    """Hình dạng của GIL 21/12/2022: phiên chỉ-khớp mở hẳn dưới SL."""
    so = PaperTradingJournal(":memory:")
    sl = float(_vi_the(so).stop_loss)
    mo = sl / 1000.0 * 0.90                      # mở 10% dưới SL (nghìn đồng)
    tk = _phien(so, PHIEN_CHI_KHOP, mo, mo + 0.3, mo - 0.3, mo + 0.2)
    t = so.all_trades()[0]
    assert t.status == Status.CLOSED, (
        "phiên chỉ-khớp không xét cắt lỗ — cây thủng SL vô hình tới phiên chấm sau "
        "(đúng lỗi ĐO 29 sửa)")
    assert t.exit_reason == pt.ExitReason.STOP_LOSS and str(t.exit_date)[:10] == PHIEN_CHI_KHOP
    assert float(t.exit_price) <= mo * 1000.0 < sl, (
        f"phải khớp ở giá mở cửa {mo * 1000:,.0f} (trừ trượt), không ở SL {sl:,.0f}: "
        f"ra {float(t.exit_price):,.0f}")
    assert tk["closed"] == 1 and tk["final_score"] is None


def test_PHIEN_CHI_KHOP_cham_SL_trong_phien_khop_o_SL(moi_truong):
    """Mở trên SL, đáy chạm SL → khớp ở SL (trừ trượt), như nhánh của `evaluate_open`."""
    so = PaperTradingJournal(":memory:")
    sl = float(_vi_the(so).stop_loss)
    mo = sl / 1000.0 * 1.02
    _phien(so, PHIEN_CHI_KHOP, mo, mo + 0.2, sl / 1000.0 * 0.99, mo)
    t = so.all_trades()[0]
    assert t.status == Status.CLOSED and float(t.exit_price) <= sl


def test_PHIEN_CHI_KHOP_khong_cham_SL_thi_khong_dong(moi_truong):
    so = PaperTradingJournal(":memory:")
    sl = float(_vi_the(so).stop_loss)
    g = sl / 1000.0 * 1.02
    assert _phien(so, PHIEN_CHI_KHOP, g, g + 0.2, g - 0.1, g)["closed"] == 0
    assert so.all_trades()[0].status == Status.OPEN


# ─────────────────────────────────────────────────────────────────────
# 2. Những việc CẦN CHẤM vẫn chỉ ở phiên chấm
# ─────────────────────────────────────────────────────────────────────

def test_PHIEN_CHI_KHOP_KHONG_nang_stop(moi_truong):
    """Nâng stop (hoà vốn, trailing) là việc của lượt chấm — phiên chỉ-khớp để nguyên."""
    so = PaperTradingJournal(":memory:")
    sl = float(_vi_the(so).stop_loss)
    cao = GIA_VAO / 1000.0 * 1.10
    _phien(so, PHIEN_CHI_KHOP, GIA_VAO / 1000.0, cao, GIA_VAO / 1000.0, cao)
    assert float(so.all_trades()[0].stop_loss) == sl, "phiên chỉ-khớp đã nâng stop"

    doi_chung = PaperTradingJournal(":memory:")
    _vi_the(doi_chung)
    doi_chung.evaluate_open("FPT", PHIEN_CHI_KHOP,
                            {"open": GIA_VAO, "high": cao * 1000.0, "low": GIA_VAO,
                             "close": cao * 1000.0}, current_score=70)
    assert float(doi_chung.all_trades()[0].stop_loss) > sl, (
        "TIỀN ĐỀ gãy: nến này không làm `evaluate_open` nâng stop, nên phép thử trên vô nghĩa")


def test_PHIEN_CHI_KHOP_KHONG_thoat_theo_TRAN_THOI_GIAN(moi_truong):
    so = PaperTradingJournal(":memory:")
    t = _vi_the(so)
    so.db.execute("UPDATE trades SET entry_date=? WHERE id=?", ("2025-01-02", t.id))
    so.db.commit()
    g = GIA_VAO / 1000.0
    _phien(so, PHIEN_CHI_KHOP, g, g + 0.1, g - 0.1, g)
    assert so.all_trades()[0].status == Status.OPEN, "phiên chỉ-khớp đặt lệnh thoát theo thời gian"

    assert so.evaluate_open("FPT", PHIEN_CHI_KHOP,
                            {"open": GIA_VAO, "high": GIA_VAO + 100, "low": GIA_VAO - 100,
                             "close": GIA_VAO}, current_score=70), (
        "TIỀN ĐỀ gãy: lệnh này không chạm trần thời gian ở phiên chấm")


def test_PHIEN_CHI_KHOP_khong_xet_o_CHINH_phien_vao(moi_truong):
    """Lệnh chờ khớp ở phiên chỉ-khớp rồi giá lủng SL cùng phiên: không đóng ngay
    trong phiên vào, như `evaluate_open` (nến ngày không cho biết thứ tự)."""
    so = PaperTradingJournal(":memory:")
    _lenh_cho(so)
    g = GIA_VAO / 1000.0
    _phien(so, PHIEN_KHOP, g, g + 0.2, g * 0.90, g * 0.92)
    t = so.all_trades()[0]
    assert t.status == Status.OPEN and str(t.entry_date)[:10] == PHIEN_KHOP


# ─────────────────────────────────────────────────────────────────────
# 3. Kịch sàn một giá: chờ phiên mở khoá (ĐO 28) — cả ở phiên chỉ-khớp
# ─────────────────────────────────────────────────────────────────────

def test_PHIEN_CHI_KHOP_KICH_SAN_cho_roi_khop_o_phien_mo_khoa(moi_truong):
    """Cần giá tham chiếu tới hàm xét: thiếu nó thì `khoa_bien` không phân được và
    cắt lỗ khớp ở phiên trắng bên mua."""
    so = PaperTradingJournal(":memory:")
    sl = float(_vi_the(so).stop_loss)
    khoa = round(GIA_VAO / 1000.0 * 0.931, 2)       # −6,9%, một giá
    assert khoa * 1000.0 <= sl, "tiền đề gãy: phiên khoá không chạm SL"
    assert _phien(so, PHIEN_CHI_KHOP, khoa, khoa, khoa, khoa, khoi_luong=50_000.0)["closed"] == 0
    assert so.all_trades()[0].status == Status.OPEN, "cắt lỗ khớp được ở phiên kịch sàn"


def test_CHOT_LOI_CUNG_bat_thi_TP_cung_khop_o_phien_chi_khop(moi_truong, monkeypatch):
    monkeypatch.setattr(pt, "CHOT_LOI_CUNG", True)
    so = PaperTradingJournal(":memory:")
    tp = float(_vi_the(so).take_profit)
    g = GIA_VAO / 1000.0
    _phien(so, PHIEN_CHI_KHOP, g, tp / 1000.0 * 1.01, g, g)
    t = so.all_trades()[0]
    assert t.status == Status.CLOSED and t.exit_reason == pt.ExitReason.TAKE_PROFIT


# ─────────────────────────────────────────────────────────────────────
# 4. MỘT bản mã cho hai đường; đường chạy thật không đổi
# ─────────────────────────────────────────────────────────────────────

def _ham(cay: ast.AST, ten: str) -> ast.FunctionDef:
    for n in ast.walk(cay):
        if isinstance(n, ast.FunctionDef) and n.name == ten:
            return n
    pytest.fail(f"không thấy hàm {ten}")


def _goi_self(ham: ast.FunctionDef) -> set[str]:
    return {n.func.attr for n in ast.walk(ham)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and isinstance(n.func.value, ast.Name) and n.func.value.id == "self"}


def _thuoc_tinh(ham: ast.FunctionDef) -> set[str]:
    return {n.attr for n in ast.walk(ham) if isinstance(n, ast.Attribute)}


def test_MOT_BAN_MA_nhanh_lenh_dat_san_cho_HAI_duong():
    """`evaluate_open` và `xet_lenh_dat_san` đi qua `_lenh_dat_san`; không hàm nào
    tự dựng lại phép khớp cắt lỗ (hai bản sao là chỗ hai đường trôi khỏi nhau)."""
    cay = ast.parse((GOC / "paper_trading.py").read_text(encoding="utf-8"))
    chung = _ham(cay, "_lenh_dat_san")
    assert {"STOP_LOSS", "TAKE_PROFIT"} <= _thuoc_tinh(chung)
    assert "_gia_ban_that" in _goi_self(chung)
    for ten in ("evaluate_open", "xet_lenh_dat_san"):
        h = _ham(cay, ten)
        assert "_lenh_dat_san" in _goi_self(h), f"{ten} không đi qua `_lenh_dat_san`"
        assert not {"STOP_LOSS", "TAKE_PROFIT"} & _thuoc_tinh(h), (
            f"{ten} tự dựng nhánh cắt lỗ/chốt lời — bản sao thứ hai")
        assert "_gia_ban_that" not in _goi_self(h)


def test_RUN_SESSION_phien_chi_khop_goi_xet_lenh_dat_san_TRUOC_khi_tra_ve():
    cay = ast.parse((GOC / "paper_runner.py").read_text(encoding="utf-8"))
    rs = _ham(cay, "run_session")
    nhanh = [n for n in ast.walk(rs) if isinstance(n, ast.If)
             and isinstance(n.test, ast.Name) and n.test.id == "chi_khop"]
    assert len(nhanh) == 1, "không thấy đúng một nhánh `if chi_khop:`"
    goi = {n.func.attr for n in ast.walk(nhanh[0])
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert "xet_lenh_dat_san" in goi
    assert not {"evaluate_open", "consider_entry"} & goi, (
        "phiên chỉ-khớp gọi đường cần CHẤM")


def test_DUONG_CHAY_THAT_khong_co_phien_chi_khop():
    """`run_daily` chấm mọi phiên: không lời gọi `run_session` nào truyền `chi_khop`,
    nên sổ thật không đổi vì ĐO 29."""
    cay = ast.parse((GOC / "run_daily.py").read_text(encoding="utf-8"))
    goi = [n for n in ast.walk(cay) if isinstance(n, ast.Call)
           and getattr(n.func, "id", getattr(n.func, "attr", None)) == "run_session"]
    assert goi, "TIỀN ĐỀ gãy: run_daily không gọi run_session"
    assert all(k.arg != "chi_khop" for g in goi for k in g.keywords)
