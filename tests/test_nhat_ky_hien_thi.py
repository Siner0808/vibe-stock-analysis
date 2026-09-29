"""Gác của P2d — HIỆN nhật ký "vì sao" trên app (BƯỚC 141).

Ba điều, mỗi điều một lỗi đã từng có hình dạng ấy trong dự án:

1. TRẠNG THÁI đọc từ SỔ LỆNH, không suy từ ô trống của nhật ký. Nửa ĐÓNG
   chỉ được điền ở lượt `hoan_tat_nhat_ky` kế tiếp; trong khoảng giữa, một
   lệnh ĐÃ ĐÓNG có nửa ĐÓNG rỗng — suy từ ô trống sẽ gọi nó là "đang mở".
2. Ô thiếu thì HIỆN LÀ THIẾU — không số mặc định (dự án chặn bịa số).
3. App đọc thẳng HAI tab (`nhat_ky` + cột trạng thái của `trades`), không kéo
   cả bảng quyết định mỗi lần mở trang; và CHỈ ĐỌC — không tạo tab nào.
"""
import ast
import json
from pathlib import Path

import pandas as pd
import pytest

import google_sheets_sync as gs
import market_filter
import nhat_ky_vi_sao as nk
import paper_trading as pt
import sheets_store as ss
from paper_trading import PaperTradingJournal, Status

GOC = Path(__file__).resolve().parent.parent

_ngay = pd.bdate_range("2026-07-01", "2026-09-30")
VNI = pd.DataFrame({"time": _ngay.strftime("%Y-%m-%d"),
                    "close": [1600.0 + i for i in range(len(_ngay))],
                    "vni_ma50": [1550.0] * len(_ngay)})
GIA_VNI = dict(zip(VNI["time"], VNI["close"]))


def _kq(diem=70):
    return {"final_score": diem, "recommendation": "MUA", "data_quality": "OK",
            "score_breakdown": {"trend_score": 80.0, "volume_score": 70.0},
            "key_reasons": ["xu hướng tăng"],
            "analyses": {"risk": {"recommendations": {"entry_price": 100.0,
                                                      "stop_loss_price": 95.0,
                                                      "take_profit_price": 120.0}}}}


@pytest.fixture
def moi_truong(monkeypatch):
    monkeypatch.setattr(market_filter, "is_vni_bullish", lambda *a, **k: True)
    monkeypatch.setattr(market_filter, "get_vni_df", lambda: VNI)
    monkeypatch.setattr(pt, "CHO_PHEP_MO_LENH_MOI", True)
    monkeypatch.setattr(pt, "MO_PHONG_TRUOT_GIA", False)


def _so_ba_trang_thai():
    """FPT đã đóng (chưa hoàn tất nửa ĐÓNG) · HPG đang mở · VNM chờ khớp."""
    j = PaperTradingJournal(":memory:", cho_phep_so_that=True)
    j.consider_entry("FPT", "2026-09-01", _kq())
    j.fill_pending("FPT", "2026-09-03", 100.0)
    j.evaluate_open("FPT", "2026-09-04", {"open": 94, "high": 95, "low": 90, "close": 92})
    j.consider_entry("HPG", "2026-09-01", _kq(65))
    j.fill_pending("HPG", "2026-09-03", 100.0)
    j.consider_entry("VNM", "2026-09-07", _kq(62))
    return j


# ── 1. trạng thái từ sổ lệnh ─────────────────────────────────────────────

def test_TRANG_THAI_doc_tu_SO_LENH_khong_suy_tu_o_trong(moi_truong):
    j = _so_ba_trang_thai()
    sheet = ss.InMemorySheet()
    ss.push(j.db, sheet)                      # CHƯA hoàn tất nửa ĐÓNG của FPT
    dong = {d["symbol"]: d for d in ss.doc_nhat_ky(sheet)}
    assert dong["FPT"]["exit_date"] is None, "phép kiểm cần nửa ĐÓNG còn rỗng"
    h = {k: nk.dong_hien_thi(v, v["trang_thai_lenh"])["Trạng thái"] for k, v in dong.items()}
    assert h == {"FPT": "Đã đóng", "HPG": "Đang mở", "VNM": "Chờ khớp"}


@pytest.mark.parametrize("st_lenh, nhan", [
    (Status.PENDING, "Chờ khớp"), (Status.OPEN, "Đang mở"),
    (Status.CLOSING, "Chờ thoát"), (Status.CLOSED, "Đã đóng"), (None, "?"),
])
def test_moi_trang_thai_so_lenh_co_NHAN(st_lenh, nhan):
    d = {c: None for c in nk.COT_NHAT_KY}
    assert nk.dong_hien_thi(d, st_lenh)["Trạng thái"] == nhan


def test_moi_trang_thai_cua_Status_deu_co_nhan():
    ten = {v for k, v in vars(Status).items() if not k.startswith("_") and isinstance(v, str)}
    thieu = ten - set(nk.NHAN_TRANG_THAI)
    assert not thieu, f"trạng thái sổ lệnh chưa có nhãn hiện: {thieu}"


# ── 2. ô thiếu hiện là thiếu ─────────────────────────────────────────────

def test_o_THIEU_hien_la_None_khong_so_mac_dinh():
    d = {c: None for c in nk.COT_NHAT_KY}
    d.update(trade_id=9, symbol="VNM", signal_date="2026-09-07")
    h = nk.dong_hien_thi(d, Status.PENDING)
    for c in ("Giá vào", "Cắt lỗ ban đầu", "Rủi ro %", "Điểm", "VN-INDEX so MA50 %",
              "Lãi ròng %", "R", "Alpha"):
        assert h[c] is None, c


def test_so_lieu_DI_THANG_khong_tinh_lai(moi_truong):
    j = _so_ba_trang_thai()
    j.hoan_tat_nhat_ky(GIA_VNI)
    sheet = ss.InMemorySheet()
    ss.push(j.db, sheet)
    d = next(x for x in ss.doc_nhat_ky(sheet) if x["symbol"] == "FPT")
    h = nk.dong_hien_thi(d, d["trang_thai_lenh"])
    assert h["R"] == d["ket_qua_R"] and h["Alpha"] == d["alpha_pct"]
    assert h["Lãi ròng %"] == d["loi_nhuan_rong_pct"]
    assert h["Cắt lỗ ban đầu"] == d["stop_loss_ban_dau"] == 95.0
    assert h["VN-INDEX so MA50 %"] == pytest.approx(
        json.loads(d["boi_canh"])["vni_pct_tren_ma50"])


def test_chi_tiet_giai_JSON_va_boi_canh_RONG_la_rong():
    d = {c: None for c in nk.COT_NHAT_KY}
    d.update(diem_agent='{"trend_score": 80.0}', ly_do='["a", "b"]', boi_canh=None)
    ct = nk.chi_tiet(d)
    assert ct == {"diem_agent": {"trend_score": 80.0}, "ly_do": ["a", "b"], "boi_canh": {}}


def test_chi_tiet_xep_boi_canh_theo_THU_TU_CO_NGHIA_khong_theo_chu_cai():
    """Nhật ký lưu JSON với `sort_keys` nên đọc ra theo CHỮ CÁI (`atr_pct`
    đứng đầu). Thứ tự để đọc là `KHOA_BOI_CANH`: điểm → VN-INDEX → rủi ro →
    khối lượng. Thấy trên app thật 29/09/2026."""
    bc = {k: 1.0 for k in nk.KHOA_BOI_CANH}
    d = {c: None for c in nk.COT_NHAT_KY}
    d["boi_canh"] = json.dumps(bc, sort_keys=True)
    assert list(nk.chi_tiet(d)["boi_canh"]) == list(nk.KHOA_BOI_CANH)


def test_moi_khoa_boi_canh_co_NHAN():
    assert set(nk.NHAN_BOI_CANH) == set(nk.KHOA_BOI_CANH)


# ── 3. đọc thẳng hai tab, CHỈ ĐỌC ────────────────────────────────────────

class GhiLai(ss.InMemorySheet):
    def __init__(self):
        super().__init__()
        self.doc, self.ghi = [], []

    def read_rows(self, tab):
        self.doc.append(tab)
        return super().read_rows(tab)

    def write_all(self, tab, rows):
        self.ghi.append(tab)
        super().write_all(tab, rows)

    def append_rows(self, tab, rows):
        self.ghi.append(tab)
        super().append_rows(tab, rows)


def test_DOC_nhat_ky_chi_doc_HAI_tab_va_KHONG_ghi_gi(moi_truong):
    j = _so_ba_trang_thai()
    sheet = GhiLai()
    ss.push(j.db, sheet)
    sheet.doc.clear(); sheet.ghi.clear()
    ra = ss.doc_nhat_ky(sheet)
    assert [d["trade_id"] for d in ra] == sorted((d["trade_id"] for d in ra), reverse=True)
    assert set(sheet.doc) == {ss.TAB_NHAT_KY, ss.TAB_TRADES}, sheet.doc
    assert sheet.ghi == []


def test_DOC_nhat_ky_tab_RONG_kieu_gspread_thi_rong():
    class Rong(ss.InMemorySheet):
        def read_rows(self, tab):
            return super().read_rows(tab) or [[]]
    assert ss.doc_nhat_ky(Rong()) == []


def test_DOC_nhat_ky_tieu_de_LECH_thi_NO():
    sheet = ss.InMemorySheet()
    sheet.write_all(ss.TAB_NHAT_KY, [["trade_id", "sai"], ["1", "x"]])
    with pytest.raises(ss.SheetSchemaError):
        ss.doc_nhat_ky(sheet)


def test_CHUA_CAU_HINH_la_None_khac_voi_RONG(monkeypatch):
    monkeypatch.setattr(ss, "open_from_secrets", lambda *a, **k: None)
    assert gs.load_nhat_ky_from_google_sheets() is None
    assert gs.load_nhat_ky_from_google_sheets(backend=ss.InMemorySheet()) == []


# ── 4. app: đi qua hàm thuần, không tự tính lại ──────────────────────────

def _ham_app(ten):
    cay = ast.parse((GOC / "app.py").read_text(encoding="utf-8"))
    for n in ast.walk(cay):
        if isinstance(n, ast.FunctionDef) and n.name == ten:
            return n
    raise AssertionError(f"app.py không có hàm {ten}")


def test_app_HIEN_qua_dong_hien_thi_va_KHONG_tu_tinh_so():
    f = _ham_app("_bang_nhat_ky")
    goi = {getattr(c.func, "attr", getattr(c.func, "id", "")) for c in ast.walk(f)
           if isinstance(c, ast.Call)}
    assert "dong_hien_thi" in goi
    tinh = [n for n in ast.walk(f) if isinstance(n, ast.BinOp)
            and isinstance(n.op, (ast.Sub, ast.Div, ast.Mult))]
    assert not tinh, "bảng nhật ký tự tính số — phải đọc số nhật ký đã ghi"


def test_app_doc_nhat_ky_qua_DUONG_CHI_DOC():
    f = _ham_app("_doc_nhat_ky")
    goi = {getattr(c.func, "attr", getattr(c.func, "id", "")) for c in ast.walk(f)
           if isinstance(c, ast.Call)}
    assert "load_nhat_ky_from_google_sheets" in goi
    assert not goi & {"pull", "push", "restore_journal_from_google_sheets"}
