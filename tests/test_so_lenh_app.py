"""App đọc sổ THẬT trên Google Sheets cho tab "Vị thế" và "Lịch sử giao dịch"
(BƯỚC 175).

Lỗi gốc (10/10/2026): `app.py` mở `paper_trades.db` ở gốc repo — tệp đứng yên từ
20/08/2026 — rồi dựng vị thế và thống kê từ nó. Ở máy hiện sổ CŨ, trên Streamlit
Cloud báo "không tìm thấy", và ở cả hai nơi người dùng không thấy vị thế thật.

Ba lớp gác:
  1. `so_lenh_app` (hàm thuần) — SỐ TÍNH TAY: dòng `lenh` nhiều trạng thái -> đúng
     số vị thế mở, số lệnh đóng; kho chưa cấu hình -> câu nói thẳng, không danh sách
     giả. Đi qua đường THẬT: ô chuỗi của sheet giả -> `load_so_ban_tin_from_google_sheets`
     -> `dung_so_lenh`.
  2. AST `app.py` — không còn mở `paper_trades.db`, không gọi `PaperTradingJournal`;
     danh sách vị thế đến từ loader Sheets (HÌNH DẠNG biểu thức, không đọc `in`).
  3. AST `so_lenh_app.py` — thuần: không đĩa, không SQLite, không ghi.
"""
from __future__ import annotations

import ast
import pathlib
import sys

import pytest

GOC = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import google_sheets_sync as gss  # noqa: E402
import paper_trading as pt  # noqa: E402
import sheets_store as ss  # noqa: E402
import so_lenh_app as sla  # noqa: E402
from paper_trading import Status  # noqa: E402


# ─────────────────────────────────────────────────────────────────────
# Dựng sheet giả (mọi ô là chuỗi, như Sheets thật)
# ─────────────────────────────────────────────────────────────────────
def _lenh(id, ma, tt, vao=None, gia_vao=None, ra=None, gia_ra=None, ly_do=None,
          size=10.0, tao=None):
    d = {c: None for c in ss.TRADE_COLS}
    d.update(id=id, symbol=ma, exchange="HOSE", signal_date="2026-09-01",
             entry_date=vao, entry_price=gia_vao, exit_date=ra, exit_price=gia_ra,
             exit_reason=ly_do, stop_loss=90.0, take_profit=120.0, size_pct=size,
             entry_score=70, entry_recommendation="BUY", components="{}",
             reasons="[]", status=tt, created_at=tao)
    return d


def _sheet(lenh):
    s = ss.InMemorySheet()
    s.tabs[ss.TAB_DECISIONS] = [list(ss.DECISION_COLS)]
    s.tabs[ss.TAB_TRADES] = [list(ss.TRADE_COLS)] + [
        [ss._to_cell(c, d[c]) for c in ss.TRADE_COLS] for d in lenh]
    s.tabs[ss.TAB_NHAT_KY] = [list(ss.NHAT_KY_COLS)]
    return s


# Sáu lệnh dựng tay:
#   1 AAA OPEN · 2 BBB PENDING · 3 CCC CLOSING  -> vị thế MỞ = 3
#   4 DDD CLOSED mua 100 bán 110 (gộp +10%) · 5 EEE CLOSED mua 100 bán 95 (gộp -5%)
#                                               -> lệnh ĐÓNG = 2
#   6 FFF HUY (lệnh chờ không khớp được)        -> KHÔNG mở, KHÔNG đóng
# Phí một vòng = 0,46% (paper_metrics.ROUND_TRIP_COST_PCT) nên ròng = +9,54% và -5,46%:
#   kỳ vọng = (9,54 - 5,46) / 2 = 2,04% · tỷ lệ thắng = 1/2.
LENH = [
    _lenh(3, "CCC", Status.CLOSING, vao="2026-09-02", gia_vao=100.0),
    _lenh(1, "AAA", Status.OPEN, vao="2026-09-02", gia_vao=100.0),
    _lenh(2, "BBB", Status.PENDING),
    _lenh(4, "DDD", Status.CLOSED, vao="2026-09-02", gia_vao=100.0, ra="2026-09-10",
          gia_ra=110.0, ly_do="TAKE_PROFIT", tao=1.7e9),
    _lenh(5, "EEE", Status.CLOSED, vao="2026-09-02", gia_vao=100.0, ra="2026-09-12",
          gia_ra=95.0, ly_do="STOP_LOSS", tao=1.7e9 + 5),
    _lenh(6, "FFF", Status.HUY, ra="2026-09-03", ly_do=pt.LY_DO_TU_CHOI_LENH),
]


def _so():
    return sla.dung_so_lenh(gss.load_so_ban_tin_from_google_sheets(_sheet(LENH)))


# ─────────────────────────────────────────────────────────────────────
# 1. Số tính tay
# ─────────────────────────────────────────────────────────────────────
def test_vi_the_mo_la_OPEN_PENDING_CLOSING_xep_theo_id():
    so = _so()
    assert [t.symbol for t in so.vi_the_mo] == ["AAA", "BBB", "CCC"]
    assert [t.id for t in so.tat_ca] == [1, 2, 3, 4, 5, 6]          # đưa vào id 3,1,2,...


def test_CLOSING_la_vi_the_mo():
    """Lệnh đã có tín hiệu ra nhưng CHƯA khớp vẫn đang nắm giữ."""
    assert "CCC" in [t.symbol for t in _so().vi_the_mo]
    assert len(_so().vi_the_mo) == 3


def test_lenh_dong_chi_la_CLOSED_va_HUY_khong_thuoc_nhom_nao():
    so = _so()
    assert [t.symbol for t in so.lenh_dong] == ["DDD", "EEE"]
    assert "FFF" not in [t.symbol for t in so.vi_the_mo]
    assert "FFF" not in [t.symbol for t in so.lenh_dong]
    assert len(so.tat_ca) == 6


def test_thong_ke_tren_hai_lenh_dong_dung_so_tinh_tay():
    p = _so().hieu_qua
    assert p.n_trades == 2
    assert p.win_rate == 0.5
    assert p.expectancy == pytest.approx(2.04, abs=1e-9)      # (9,54 - 5,46) / 2
    assert p.avg_win == pytest.approx(9.54, abs=1e-9)
    assert p.avg_loss == pytest.approx(-5.46, abs=1e-9)


def test_o_chuoi_cua_sheet_thanh_dung_kieu():
    t = {x.symbol: x for x in _so().tat_ca}
    assert t["DDD"].entry_price == 100.0 and isinstance(t["DDD"].entry_price, float)
    assert t["DDD"].entry_score == 70 and t["DDD"].created_at == 1.7e9
    assert t["BBB"].entry_price is None and t["BBB"].exit_date is None   # ô rỗng = NULL


def test_chua_co_lenh_dong_nao_thi_hieu_qua_None_va_noi_ro_khong_phai_loi_doc():
    so = sla.dung_so_lenh(gss.load_so_ban_tin_from_google_sheets(
        _sheet([_lenh(1, "AAA", Status.OPEN, vao="2026-09-02", gia_vao=100.0)])))
    assert len(so.vi_the_mo) == 1 and so.hieu_qua is None and so.loi is None
    assert so.ly_do_khong_co_thong_ke == sla.CAU_CHUA_CO_LENH_DONG


def test_tab_trades_rong_la_so_rong_khong_phai_chua_cau_hinh():
    so = sla.dung_so_lenh(gss.load_so_ban_tin_from_google_sheets(_sheet([])))
    assert so.tat_ca == () and so.loi is None


def test_kho_chua_cau_hinh_noi_thang_va_khong_dung_danh_sach_gia():
    so = sla.dung_so_lenh(None)
    assert so.loi == ("chưa cấu hình kho ngoài (Google Sheets) — "
                      "không đọc được sổ thật")
    assert so.tat_ca == () and so.vi_the_mo == () and so.lenh_dong == ()
    assert so.hieu_qua is None
    assert so.ly_do_khong_co_thong_ke == so.loi


def test_dung_so_lenh_khong_doi_dau_vao():
    du_lieu = gss.load_so_ban_tin_from_google_sheets(_sheet(LENH))
    truoc = [dict(d) for d in du_lieu["lenh"]]
    sla.dung_so_lenh(du_lieu)
    assert du_lieu["lenh"] == truoc


# ─────────────────────────────────────────────────────────────────────
# 2. AST app.py
# ─────────────────────────────────────────────────────────────────────
def _app():
    return ast.parse((GOC / "app.py").read_text(encoding="utf-8"))


def test_app_khong_con_mo_so_o_may():
    """Không `PaperTradingJournal`, không `all_trades`, không chuỗi nhắc tới
    `paper_trades` — ở BẤT KỲ đâu trong cây (lời gọi, tên, thuộc tính, chuỗi)."""
    cay = _app()
    ten = ({n.id for n in ast.walk(cay) if isinstance(n, ast.Name)}
           | {n.attr for n in ast.walk(cay) if isinstance(n, ast.Attribute)}
           | {a.name for n in ast.walk(cay) if isinstance(n, ast.ImportFrom)
              for a in n.names}
           | {n.value for n in ast.walk(cay) if isinstance(n, ast.Constant)
              and isinstance(n.value, str)})
    cam = ("PaperTradingJournal", "all_trades", "paper_trades", "_PJ", "_db_path")
    thay = sorted(x for x in ten if any(c in x for c in cam))
    assert not thay, thay


def _gan_module(cay, ten):
    """Phép gán `ten = ...` ở MỨC MODULE, kể cả nằm trong `try`."""
    ra = []
    def duyet(than):
        for n in than:
            if isinstance(n, ast.Assign) and any(
                    isinstance(t, ast.Name) and t.id == ten for t in n.targets):
                ra.append(ast.unparse(n.value))
            elif isinstance(n, ast.Try):
                duyet(n.body)
    duyet(cay.body)
    return ra


def test_danh_sach_vi_the_den_tu_loader_Sheets_qua_dung_so_lenh():
    cay = _app()
    assert _gan_module(cay, "_so_lenh")[0] == "_dung_so_lenh(_doc_so_ban_tin())"
    assert _gan_module(cay, "real_open_trades") == ["list(_so_lenh.vi_the_mo)"]
    assert _gan_module(cay, "so_lenh_perf") == ["_so_lenh.hieu_qua"]
    assert _gan_module(cay, "so_lenh_dong") == ["len(_so_lenh.lenh_dong)"]
    assert _gan_module(cay, "so_lenh_tat_ca") == ["list(_so_lenh.tat_ca)"]
    nhap = {a.asname or a.name: n.module for n in ast.walk(cay)
            if isinstance(n, ast.ImportFrom) and n.module == "so_lenh_app"
            for a in n.names}
    assert nhap.get("_dung_so_lenh") == "so_lenh_app"


def test_doc_so_ban_tin_la_ham_cache_va_la_NOI_DUY_NHAT_goi_loader_cua_sheets():
    cay = _app()
    ham = next(n for n in cay.body if isinstance(n, ast.FunctionDef)
               and n.name == "_doc_so_ban_tin")
    assert any("st.cache_data" in ast.unparse(d) for d in ham.decorator_list)
    cuoc = [n for n in ast.walk(cay) if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr == "load_so_ban_tin_from_google_sheets"]
    assert len(cuoc) == 1 and cuoc[0].lineno >= ham.lineno      # một đường đọc, không đường thứ hai
    # và vị thế không đọc bằng đường Sheets nào khác (`sync_*`, `restore_*`, `load_nhat_ky`)
    ten_khac = {n.func.attr for n in ast.walk(cay) if isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute)
                and n.func.attr.endswith("_google_sheets")} - {
                    "load_so_ban_tin_from_google_sheets",
                    "load_nhat_ky_from_google_sheets"}
    assert not ten_khac, ten_khac


def test_khoi_so_lenh_chay_SAU_dinh_nghia_loader_va_TRUOC_moi_lan_dung():
    cay = _app()
    dong_ham = next(n.lineno for n in cay.body if isinstance(n, ast.FunctionDef)
                    and n.name == "_doc_so_ban_tin")
    dong_gan = min(n.lineno for n in cay.body if isinstance(n, ast.Try)
                   and "_dung_so_lenh" in ast.unparse(n))
    dung = [n.lineno for n in ast.walk(cay) if isinstance(n, ast.Name)
            and n.id in ("real_open_trades", "so_lenh_perf", "so_lenh_dong")
            and isinstance(n.ctx, ast.Load)]
    assert dong_ham < dong_gan < min(dung)


# ─────────────────────────────────────────────────────────────────────
# 3. AST so_lenh_app.py — thuần
# ─────────────────────────────────────────────────────────────────────
def test_so_lenh_app_thuan_khong_dia_khong_sqlite_khong_ghi_khong_mo_so():
    cay = ast.parse((GOC / "so_lenh_app.py").read_text(encoding="utf-8"))
    nhap = set()
    goi = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            nhap |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            nhap.add((n.module or "").split(".")[0])
        elif isinstance(n, ast.Call):
            f = n.func
            goi.add(f.id if isinstance(f, ast.Name) else getattr(f, "attr", ""))
    assert not ({"sqlite3", "os", "pathlib", "requests", "gspread", "sheets_store",
                 "google_sheets_sync", "streamlit", "market_filter"} & nhap), nhap
    ghi = {"open", "write_text", "write_bytes", "commit", "execute", "push", "pull",
           "record_trade", "update_trade", "record_decision", "now", "today",
           "PaperTradingJournal"}
    assert not (ghi & goi), sorted(ghi & goi)        # chỉ dùng `_to_trade`, không MỞ sổ


def _bo_ba(cay, ten):
    n = next(n for n in cay.body if isinstance(n, ast.Assign)
             and isinstance(n.targets[0], ast.Name) and n.targets[0].id == ten)
    return [ast.unparse(e) for e in n.value.elts]


def test_hai_nhom_trang_thai_la_hang_so_cua_Status_khong_chuoi_go_tay():
    cay = ast.parse((GOC / "so_lenh_app.py").read_text(encoding="utf-8"))
    assert _bo_ba(cay, "TRANG_THAI_MO") == ["Status.OPEN", "Status.PENDING",
                                            "Status.CLOSING"]
    assert _bo_ba(cay, "TRANG_THAI_DONG") == ["Status.CLOSED"]
