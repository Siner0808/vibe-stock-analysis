"""Gác của P2b-2 — nối nhật ký "vì sao" vào sổ lệnh (BƯỚC 134).

Ba chỗ nối, mỗi chỗ một lý do:

    consider_entry   mở dòng nhật ký LÚC TÍN HIỆU, chụp bối cảnh — chỉ ở đó
                     có `result`; VN-INDEX qua `market_filter.get_vni_df()`
    fill_pending     điền nửa VÀO NGAY LÚC KHỚP — trước mọi lần trailing nâng
                     `stop_loss` (`evaluate_open` ghi đè nó trong sổ lệnh)
    hoan_tat_nhat_ky điền nửa ĐÓNG cho lệnh đã đóng, kèm rổ VN-INDEX; làm lại
                     được, nên rổ tới muộn thì lượt sau điền nốt

Dòng mở từ lúc tín hiệu vì lệnh chờ khớp đi QUA Google Sheets: tín hiệu ở
lượt quét hôm nay, khớp ở lượt quét phiên sau trên một runner sạch vừa kéo
sổ về. Bối cảnh không nằm trong một dòng sổ thì nó không sống qua đêm.

Người dùng chốt 27/09/2026: CHỈ sổ THẬT ghi nhật ký (`cho_phep_so_that`).
Phép kiểm thứ hai dưới đây là điều kiện để không phép đo nào đổi.
"""
import ast
import json
from pathlib import Path

import pandas as pd
import pytest

import market_filter
import nhat_ky_vi_sao as nk
import paper_trading as pt
import sheets_store as ss
from paper_trading import ExitReason, PaperTradingJournal, Status

GOC = Path(__file__).resolve().parent.parent

TIN_HIEU = "2026-09-01"
KHOP = "2026-09-03"

_ngay = pd.bdate_range("2026-07-01", "2026-09-30")
VNI = pd.DataFrame({
    "time": _ngay.strftime("%Y-%m-%d"),
    "close": [1600.0 + i for i in range(len(_ngay))],
    "vni_ma50": [1550.0] * len(_ngay),
})
GIA_VNI = dict(zip(VNI["time"], VNI["close"]))


def _kq(diem=70, sl=95.0, tp=120.0, vao=100.0) -> dict:
    return {
        "final_score": diem, "recommendation": "MUA 📈", "data_quality": "OK",
        "score_breakdown": {"trend_score": 80.0, "momentum_score": 60.0,
                            "volume_score": 70.0, "news_score": 50.0},
        "key_reasons": ["xu hướng tăng"],
        "analyses": {
            "risk": {"recommendations": {"entry_price": vao, "stop_loss_price": sl,
                                         "take_profit_price": tp},
                     "metrics": {"volatility_annual": 30.0, "max_drawdown": -20.0,
                                 "sharpe_ratio": 1.1, "atr_pct": 2.5}},
            "volume": {"stats": {"last_volume": 1.0e6, "avg_vol_20": 8.0e5,
                                 "vol_ratio_vs_ma20": 1.25}},
        },
    }


def _nen(o, h, l, c):
    return {"open": o, "high": h, "low": l, "close": c}


@pytest.fixture
def moi_truong(monkeypatch):
    monkeypatch.setattr(market_filter, "is_vni_bullish", lambda *a, **k: True)
    monkeypatch.setattr(market_filter, "get_vni_df", lambda: VNI)
    monkeypatch.setattr(pt, "CHO_PHEP_MO_LENH_MOI", True)
    monkeypatch.setattr(pt, "MO_PHONG_TRUOT_GIA", False)


@pytest.fixture
def so_that(moi_truong):
    j = PaperTradingJournal(":memory:", cho_phep_so_that=True)
    yield j
    j.db.close()


def _dong_nk(j, tid) -> dict:
    r = j.db.execute("SELECT * FROM nhat_ky WHERE trade_id=?", (tid,)).fetchone()
    return dict(r) if r else None


def _so_dong_nk(j) -> int:
    return j.db.execute("SELECT COUNT(*) FROM nhat_ky").fetchone()[0]


def _vong_doi_trailing(j):
    """Vào 100 (SL 95) · phiên sau trailing nâng SL · phiên sau nữa cắt lỗ."""
    tid = j.consider_entry("FPT", TIN_HIEU, _kq())
    assert j.fill_pending("FPT", KHOP, 100.0) == 1
    j.evaluate_open("FPT", "2026-09-04", _nen(101, 110, 100, 108))
    nang = j.open_position("FPT").stop_loss
    assert nang > 100.0, "trailing phải NÂNG stop — không thì phép kiểm rỗng"
    j.evaluate_open("FPT", "2026-09-07", _nen(101, 102, 99, 100))
    assert j.all_trades(Status.CLOSED), "lệnh phải đóng bằng stop đã nâng"
    return tid, nang


# ── chỗ nối 1: consider_entry ────────────────────────────────────────────

def test_SO_THAT_mo_dong_nhat_ky_tu_luc_TIN_HIEU_voi_boi_canh_cua_phien_ay(so_that):
    tid = so_that.consider_entry("FPT", TIN_HIEU, _kq())
    d = _dong_nk(so_that, tid)
    assert d is not None, "sổ thật phải mở dòng nhật ký ngay lúc tín hiệu"
    assert (d["symbol"], d["signal_date"], d["entry_date"]) == ("FPT", TIN_HIEU, None)
    ky_vong = nk.boi_canh_luc_tin_hieu(_kq(), TIN_HIEU, VNI, pt.BUY_THRESHOLD)
    assert json.loads(d["boi_canh"]) == ky_vong
    assert json.loads(d["boi_canh"])["vni_close"] == GIA_VNI[TIN_HIEU]


def test_KHONG_phai_so_that_thi_KHONG_ghi_va_KHONG_goi_get_vni_df(moi_truong, monkeypatch):
    """Backtest/walkforward mở sổ KHÔNG cờ — không một dòng, không một lời gọi."""
    def cam():
        raise AssertionError("đường không-sổ-thật đã gọi get_vni_df")
    monkeypatch.setattr(market_filter, "get_vni_df", cam)
    j = PaperTradingJournal(":memory:")
    _vong_doi_trailing(j)
    assert j.hoan_tat_nhat_ky(GIA_VNI) == 0
    assert _so_dong_nk(j) == 0


def test_bo_qua_tin_hieu_thi_KHONG_mo_dong(so_that):
    assert so_that.consider_entry("FPT", TIN_HIEU, _kq(diem=10)) is None
    assert _so_dong_nk(so_that) == 0


# ── chỗ nối 2: fill_pending ──────────────────────────────────────────────

def test_nua_VAO_ghi_LUC_KHOP_va_giu_SL_BAN_DAU_sau_khi_trailing_NANG_stop(so_that):
    tid, nang = _vong_doi_trailing(so_that)
    d = _dong_nk(so_that, tid)
    assert d["entry_date"] == KHOP and d["entry_price"] == 100.0
    assert d["stop_loss_ban_dau"] == 95.0, (
        f"nhật ký phải giữ SL LÚC KHỚP (95), không phải SL đã nâng ({nang})")
    assert d["rui_ro_pct"] == pytest.approx(5.0)
    assert json.loads(d["diem_agent"]) == {"momentum_score": 60.0, "news_score": 50.0,
                                           "trend_score": 80.0, "volume_score": 70.0}
    assert json.loads(d["ly_do"]) == ["xu hướng tăng"]
    # Nửa VÀO không đụng bối cảnh chụp lúc tín hiệu.
    assert json.loads(d["boi_canh"])["vni_close"] == GIA_VNI[TIN_HIEU]


def test_lenh_KHONG_KHOP_bi_xoa_thi_dong_nhat_ky_cung_xoa(so_that, monkeypatch):
    monkeypatch.setattr(pt, "MO_PHONG_TRUOT_GIA", True)
    so_that.consider_entry("FPT", TIN_HIEU, _kq())
    assert _so_dong_nk(so_that) == 1
    # Mở cửa 100 trên tham chiếu 80: +25%, ngoài biên độ ±7% -> sàn từ chối.
    nen = {"high": 100.0, "low": 100.0, "volume": 1.0e9, "tham_chieu": 80.0}
    assert so_that.fill_pending("FPT", KHOP, 100.0, nen) == 0
    assert so_that.all_trades() == []
    assert _so_dong_nk(so_that) == 0, "lệnh không tồn tại thì nhật ký của nó cũng không"


def test_lenh_CHO_tu_truoc_khi_co_nhat_ky_van_ghi_nua_VAO_voi_boi_canh_RONG(so_that):
    tid = so_that.consider_entry("FPT", TIN_HIEU, _kq())
    so_that.db.execute("DELETE FROM nhat_ky")          # lệnh chờ đời trước P2b
    so_that.fill_pending("FPT", KHOP, 100.0)
    d = _dong_nk(so_that, tid)
    assert d["stop_loss_ban_dau"] == 95.0
    assert d["boi_canh"] is None, "không chụp được thì ô RỖNG, không phải chuỗi 'null'"


# ── chỗ nối 3: hoan_tat_nhat_ky ──────────────────────────────────────────

def test_HOAN_TAT_dien_nua_DONG_R_tren_SL_BAN_DAU(so_that):
    tid, _ = _vong_doi_trailing(so_that)
    assert so_that.hoan_tat_nhat_ky(GIA_VNI) == 1
    d = _dong_nk(so_that, tid)
    t = so_that.all_trades(Status.CLOSED)[0]
    assert d["exit_reason"] == ExitReason.STOP_LOSS
    assert d["loi_nhuan_rong_pct"] == pytest.approx(t.net_return_pct())
    assert d["ket_qua_R"] == pytest.approx(t.net_return_pct() / 5.0)
    ro = (GIA_VNI[t.exit_date[:10]] - GIA_VNI[KHOP]) / GIA_VNI[KHOP] * 100.0
    assert d["ro_chuan_pct"] == pytest.approx(ro)
    assert d["alpha_pct"] == pytest.approx(t.net_return_pct() - ro)
    assert "ĐÃ NÂNG" in d["hau_kiem_may"]


def test_HOAN_TAT_lam_lai_khi_ro_chuan_toi_MUON_roi_THOI(so_that):
    tid, _ = _vong_doi_trailing(so_that)
    thieu = {k: v for k, v in GIA_VNI.items() if k != "2026-09-07"}
    assert so_that.hoan_tat_nhat_ky(thieu) == 1
    d = _dong_nk(so_that, tid)
    assert d["exit_date"] == "2026-09-07" and d["ro_chuan_pct"] is None
    assert "chưa có rổ chuẩn" in d["hau_kiem_may"]
    assert so_that.hoan_tat_nhat_ky(thieu) == 0, "rổ vẫn thiếu: không có gì ĐỔI"
    assert so_that.hoan_tat_nhat_ky(GIA_VNI) == 1, "rổ tới muộn thì lượt sau điền nốt"
    assert _dong_nk(so_that, tid)["alpha_pct"] is not None
    assert so_that.hoan_tat_nhat_ky(GIA_VNI) == 0, "đủ rồi thì không ghi lại"


def test_HOAN_TAT_khong_dung_lenh_CHUA_DONG_va_dong_THIEU_nua_VAO(so_that):
    # Lệnh ĐÃ ĐÓNG mà dòng nhật ký thiếu nửa VÀO (khớp ở một đường không ghi
    # nhật ký): không có cắt lỗ ban đầu thì không dựng nửa ĐÓNG — không nổ,
    # không đoán.
    tid, _ = _vong_doi_trailing(so_that)
    so_that.db.execute(
        "UPDATE nhat_ky SET entry_date=NULL, entry_price=NULL, stop_loss_ban_dau=NULL,"
        " rui_ro_pct=NULL, entry_score=NULL, diem_agent=NULL, ly_do=NULL"
        " WHERE trade_id=?", (tid,))
    so_that.consider_entry("HPG", TIN_HIEU, _kq())
    so_that.fill_pending("HPG", KHOP, 100.0)           # đang mở
    so_that.consider_entry("VNM", TIN_HIEU, _kq())     # còn chờ khớp
    truoc = [dict(r) for r in so_that.db.execute("SELECT * FROM nhat_ky ORDER BY trade_id")]
    assert so_that.hoan_tat_nhat_ky(GIA_VNI) == 0
    sau = [dict(r) for r in so_that.db.execute("SELECT * FROM nhat_ky ORDER BY trade_id")]
    assert sau == truoc


# ── Google Sheets: dòng mở hôm nay phải sống tới phiên khớp ──────────────

def _so_ba_trang_thai():
    j = PaperTradingJournal(":memory:", cho_phep_so_that=True)
    _vong_doi_trailing(j)                              # FPT: đã đóng
    j.hoan_tat_nhat_ky(GIA_VNI)
    j.consider_entry("HPG", TIN_HIEU, _kq())           # HPG: đã khớp
    j.fill_pending("HPG", KHOP, 100.0)
    j.consider_entry("VNM", "2026-09-07", _kq())        # VNM: mới có tín hiệu
    return j


def _anh(j):
    return [tuple(r) for r in j.db.execute("SELECT * FROM nhat_ky ORDER BY trade_id")]


def test_DAY_KEO_giu_nguyen_tung_o_nhat_ky_ca_o_RONG(moi_truong):
    j = _so_ba_trang_thai()
    sheet = ss.InMemorySheet()
    ss.push(j.db, sheet)
    assert sheet.read_rows(ss.TAB_NHAT_KY)[0] == list(nk.COT_NHAT_KY)
    moi = PaperTradingJournal(":memory:")
    ss.pull(moi.db, sheet)
    assert _anh(moi) == _anh(j)
    assert len(_anh(moi)) == 3


def test_lenh_CHO_qua_dem_van_ghi_nua_VAO_voi_boi_canh_luc_tin_hieu(moi_truong):
    """Tín hiệu ở runner hôm nay; khớp ở runner phiên sau, sổ kéo từ Sheets."""
    hom_nay = PaperTradingJournal(":memory:", cho_phep_so_that=True)
    tid = hom_nay.consider_entry("FPT", TIN_HIEU, _kq())
    sheet = ss.InMemorySheet()
    ss.push(hom_nay.db, sheet)
    mai = PaperTradingJournal(":memory:", cho_phep_so_that=True)
    ss.pull(mai.db, sheet)
    mai.fill_pending("FPT", KHOP, 100.0)
    d = _dong_nk(mai, tid)
    assert d["stop_loss_ban_dau"] == 95.0
    assert json.loads(d["boi_canh"])["vni_close"] == GIA_VNI[TIN_HIEU]


def test_DAY_tu_choi_khi_nhat_ky_local_IT_HON_sheet(moi_truong):
    j = _so_ba_trang_thai()
    sheet = ss.InMemorySheet()
    ss.push(j.db, sheet)
    truoc = sheet.read_rows(ss.TAB_NHAT_KY)
    j.db.execute("DELETE FROM nhat_ky WHERE symbol='VNM'")
    with pytest.raises(ss.SheetError, match="nhật ký"):
        ss.push(j.db, sheet)
    assert sheet.read_rows(ss.TAB_NHAT_KY) == truoc


def test_KEO_doc_tab_nhat_ky_TRUOC_moi_lenh_xoa(moi_truong):
    """Hỏng mạng ở tab thứ ba thì sổ đích chưa bị xoá gì — điều kiện để
    `keo_so_co_thu_lai` thử lại an toàn.

    Đo THỨ TỰ ngay lúc lời gọi mạng xảy ra, không đo sổ sau khi hỏng: sau
    khi hỏng thì rollback cũng trả sổ về như cũ, nên phép đo sau che mất
    một `pull()` xoá TRƯỚC rồi mới đọc (đục thử 28/09 sống sót đúng chỗ ấy).
    """
    j = _so_ba_trang_thai()
    sheet = ss.InMemorySheet()
    ss.push(j.db, sheet)
    dich = _so_ba_trang_thai()
    luc_doc = []

    class HongNhatKy(ss.InMemorySheet):
        def read_rows(self, tab):
            if tab == ss.TAB_NHAT_KY:
                luc_doc.append((len(dich.all_trades()), len(_anh(dich))))
                raise ConnectionError("mạng đứt")
            return super().read_rows(tab)

    hong = HongNhatKy()
    hong.tabs = sheet.tabs
    truoc = (_anh(dich), len(dich.all_trades()))
    with pytest.raises(ConnectionError):
        ss.pull(dich.db, hong, allow_overwrite=True)
    assert luc_doc == [(3, 3)], f"pull() đã xoá sổ TRƯỚC khi đọc tab nhật ký: {luc_doc}"
    dich.db.rollback()
    assert (_anh(dich), len(dich.all_trades())) == truoc


def test_KEO_tu_choi_khi_so_dich_CHI_co_nhat_ky(moi_truong):
    j = _so_ba_trang_thai()
    sheet = ss.InMemorySheet()
    ss.push(j.db, sheet)
    dich = PaperTradingJournal(":memory:")
    dich.db.execute("INSERT INTO nhat_ky (trade_id, symbol, signal_date) VALUES (99, 'X', '2026-01-01')")
    with pytest.raises(ss.SheetError):
        ss.pull(dich.db, sheet)


# ── lược đồ: một chỗ khai, hai nơi suy ───────────────────────────────────

def test_bang_SQLite_va_tab_Sheets_cung_suy_tu_COT_NHAT_KY():
    assert nk.COT_SO_NGUYEN | nk.COT_SO_THUC <= set(nk.COT_NHAT_KY)
    assert not nk.COT_SO_NGUYEN & nk.COT_SO_THUC
    j = PaperTradingJournal(":memory:")
    cot = [(r[1], r[2]) for r in j.db.execute("PRAGMA table_info(nhat_ky)")]
    assert [c for c, _ in cot] == list(nk.COT_NHAT_KY)
    for c, kieu in cot:
        mong = ("INTEGER" if c in nk.COT_SO_NGUYEN
                else "REAL" if c in nk.COT_SO_THUC else "TEXT")
        assert kieu == mong, (c, kieu)
    assert ss.NHAT_KY_COLS is nk.COT_NHAT_KY


# ── gác AST: đường VN-INDEX và thứ tự ở run_daily ────────────────────────

def _ham(tep: str, ten: str) -> ast.FunctionDef:
    cay = ast.parse((GOC / tep).read_text(encoding="utf-8"))
    for n in ast.walk(cay):
        if isinstance(n, ast.FunctionDef) and n.name == ten:
            return n
    raise AssertionError(f"không thấy {ten} trong {tep}")


def _ten_goi(n: ast.AST) -> list[tuple[int, str]]:
    ra = []
    for c in ast.walk(n):
        if isinstance(c, ast.Call):
            f = c.func
            ten = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
            ra.append((c.lineno, ten))
    return sorted(ra)


def test_boi_canh_di_duong_BO_LOC_get_vni_df_KHONG_duong_topbar():
    goi = {t for _, t in _ten_goi(_ham("paper_trading.py", "consider_entry"))}
    assert "get_vni_df" in goi and "boi_canh_luc_tin_hieu" in goi
    assert "chi_so_moi_nhat" not in goi, "đường topbar ưu tiên MẠNG — CLAUDE.md"


def test_run_daily_HOAN_TAT_nhat_ky_TRUOC_khi_DAY_len_Sheets():
    goi = _ten_goi(_ham("run_daily.py", "execute_daily_scan"))
    hoan_tat = [d for d, t in goi if t == "hoan_tat_nhat_ky"]
    day = [d for d, t in goi if t == "push"]
    assert hoan_tat, "run_daily chưa bao giờ điền nửa ĐÓNG"
    assert day and max(hoan_tat) < min(day), "điền sau khi đẩy thì Sheets luôn chậm một lượt"
