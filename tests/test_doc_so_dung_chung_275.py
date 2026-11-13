"""BƯỚC 275, lát 2 — app đọc Google Sheets ÍT lượt hơn mà KHÔNG đổi một ô, và vẫn CHỈ ĐỌC.

Khoá năm điều (mỗi điều có đột biến ở STATE BƯỚC 275, mục D):

1. **Cùng dữ liệu**: ba bộ đọc đi qua backend dùng chung trả đúng thứ mà đường cũ
   (`load_*_from_google_sheets(backend=…)` không bọc) trả.
2. **Một kết nối, mỗi tab một lần**: `backend_doc_chung` gọi `get_backend` đúng một lần cho cả ba
   bộ đọc; năm tab đọc đúng một lượt; backend thật đi qua `read_rows_nhieu` (một lần hỏi danh sách tab).
3. **Hạn và làm mới**: trong hạn không đọc lại; quá hạn hoặc bấm "Đọc lại sổ" thì đọc lại; có dấu giờ.
4. **Lỗi vẫn hiện**: tab lỗi đọc thì bộ đọc cần nó nổ NGUYÊN lỗi ấy (không rỗng giả, không số mặc
   định), không bị nhớ; tiêu đề lệch của một tab chỉ làm hỏng bộ đọc của tab ấy.
5. **Không bao giờ ghi**: `BackendDocChung` và `read_rows_nhieu` không có đường ghi (chạy + AST), và
   đường quét không nhắc tới các tên mới.
"""
import ast
import pathlib
import types

import pytest

import google_sheets_sync as gss
import sheets_store as ss

GOC = pathlib.Path(__file__).resolve().parent.parent
TEN_GHI = {"write_all", "append_rows", "add_worksheet", "update", "append_row", "push", "pull",
           "clear", "delete_rows", "batch_update", "restore_journal_from_google_sheets",
           "sync_trades_to_google_sheets"}


def _dong(cols, **kv):
    return [str(kv.get(c, "")) for c in cols]


def _so_mau() -> ss.InMemorySheet:
    s = ss.InMemorySheet()
    s.tabs[ss.TAB_TRADES] = [list(ss.TRADE_COLS),
                             _dong(ss.TRADE_COLS, id=1, symbol="HPG", status="CLOSED", entry_date="2026-10-01", exit_date="2026-10-09"),
                             _dong(ss.TRADE_COLS, id=2, symbol="FPT", status="OPEN", entry_date="2026-11-02")]
    s.tabs[ss.TAB_NHAT_KY] = [list(ss.NHAT_KY_COLS),
                              _dong(ss.NHAT_KY_COLS, trade_id=1), _dong(ss.NHAT_KY_COLS, trade_id=2)]
    s.tabs[ss.TAB_DECISIONS] = [list(ss.DECISION_COLS),
                                _dong(ss.DECISION_COLS, seq=1, symbol="HPG", signal_date="2026-10-01", score="70"),
                                _dong(ss.DECISION_COLS, seq=2, symbol="FPT", signal_date="2026-11-02", score="64")]
    s.tabs[ss.TAB_HAU_KIEM] = [list(ss.HAU_KIEM_COLS)]
    s.tabs[ss.TAB_KE_HOACH] = [list(ss.KE_HOACH_COLS),
                               _dong(ss.KE_HOACH_COLS, seq=5, symbol="HPG", signal_date="2026-11-02")]
    return s


class _Dem(ss.InMemorySheet):
    """InMemorySheet có đếm lượt `read_rows` theo tab; mọi đường ghi nổ."""

    def __init__(self, goc):
        super().__init__()
        self.tabs = goc.tabs
        self.doc = []

    def read_rows(self, tab):
        self.doc.append(tab)
        return super().read_rows(tab)

    def write_all(self, *a, **k):
        raise AssertionError("ghi")

    def append_rows(self, *a, **k):
        raise AssertionError("ghi")


@pytest.fixture(autouse=True)
def _sach(monkeypatch):
    monkeypatch.setattr(gss, "_DUNG_CHUNG", None)
    yield
    monkeypatch.setattr(gss, "_DUNG_CHUNG", None)


def _gan_backend(monkeypatch, b):
    goi = []
    def get():
        goi.append(1)
        return b
    monkeypatch.setattr(gss, "get_backend", lambda backend=None: get() if backend is None else backend)
    return goi


def _ba_bo_doc(b=None):
    return (gss.load_nhat_ky_from_google_sheets(b), gss.load_so_ban_tin_from_google_sheets(b),
            gss.load_ke_hoach_from_google_sheets(b))


# ── 1. cùng dữ liệu ─────────────────────────────────────────────────────────
def test_ba_bo_doc_qua_backend_chung_ra_dung_thu_duong_cu_ra(monkeypatch):
    mau = _so_mau()
    cu = _ba_bo_doc(_Dem(mau))
    _gan_backend(monkeypatch, _Dem(mau))
    moi = _ba_bo_doc(gss.backend_doc_chung())
    assert moi == cu
    assert len(moi[0]) == 2 and len(moi[1]["lenh"]) == 2 and len(moi[1]["quyet_dinh"]) == 2 and len(moi[2]) == 1


# ── 2. một kết nối, mỗi tab một lần ─────────────────────────────────────────
def test_mot_ket_noi_va_moi_tab_mot_lan_cho_ca_ba_bo_doc(monkeypatch):
    b = _Dem(_so_mau())
    goi = _gan_backend(monkeypatch, b)
    _ba_bo_doc(gss.backend_doc_chung())
    _ba_bo_doc(gss.backend_doc_chung())
    assert len(goi) == 1, "mỗi bộ đọc tự xác thực = 6 lượt gọi mạng ở bản cũ"
    assert sorted(b.doc) == sorted(gss.TAB_APP_DOC) and len(b.doc) == 5


def test_duong_cu_doc_bay_luot_cho_nam_tab_de_so_sanh(monkeypatch):
    """Phép đo đối chứng: đường CŨ (không dùng chung) đọc `trades` 2 lần, `nhat_ky` 2 lần (7 lượt cho 5 tab)."""
    b = _Dem(_so_mau())
    _ba_bo_doc(b)
    assert b.doc.count(ss.TAB_TRADES) == 2 and b.doc.count(ss.TAB_NHAT_KY) == 2 and len(b.doc) == 7


def test_backend_that_di_qua_read_rows_nhieu_mot_lan(monkeypatch):
    class That(_Dem):
        def __init__(self, goc):
            super().__init__(goc)
            self.nhieu = []

        def read_rows_nhieu(self, tabs):
            self.nhieu.append(tuple(tabs))
            return {t: ss.InMemorySheet.read_rows(self, t) for t in tabs}
    b = That(_so_mau())
    _gan_backend(monkeypatch, b)
    _ba_bo_doc(gss.backend_doc_chung())
    assert b.nhieu == [gss.TAB_APP_DOC] and b.doc == []


class _Ws:
    def __init__(self, title, rows, loi=None, nhat=None):
        self.title, self._rows, self._loi, self._nhat = title, rows, loi, nhat

    def get_all_values(self):
        self._nhat.append(self.title)
        if self._loi:
            raise self._loi
        return self._rows

    def update(self, *a, **k):
        raise AssertionError("ghi")


class _Sh:
    def __init__(self, ws, nhat):
        self._ws, self.nhat = ws, nhat
        self.hoi_ds = 0

    def worksheets(self):
        self.hoi_ds += 1
        return self._ws

    def worksheet(self, t):
        raise AssertionError("read_rows_nhieu không được hỏi từng tab")

    def add_worksheet(self, **k):
        raise AssertionError("TẠO tab")


def _google_gia(ws):
    g = object.__new__(ss.GoogleSheet)
    nhat = []
    g._sh = _Sh([_Ws(t, r, l, nhat) for t, r, l in ws], nhat)
    return g


def test_GoogleSheet_read_rows_nhieu_mot_lan_hoi_danh_sach_tab_khong_tao_khong_ghi():
    loi = RuntimeError("429 quota")
    g = _google_gia([("trades", [["a"]], None), ("nhat_ky", [["b"]], None), ("decisions", None, loi)])
    ra = g.read_rows_nhieu(["trades", "nhat_ky", "decisions", "hau_kiem"])
    assert g._sh.hoi_ds == 1
    assert ra["trades"] == [["a"]] and ra["nhat_ky"] == [["b"]]
    assert ra["decisions"] is loi                 # lỗi của MỘT tab là giá trị của tab ấy
    assert ra["hau_kiem"] == []                   # tab chưa có -> rỗng, KHÔNG tạo (add_worksheet sẽ nổ)
    assert g._sh.nhat == ["trades", "nhat_ky", "decisions"]


# ── 3. hạn và làm mới ───────────────────────────────────────────────────────
def test_trong_han_khong_doc_lai_qua_han_hoac_bam_nut_thi_doc_lai():
    gio = [100.0]
    b = _Dem(_so_mau())
    d = gss.BackendDocChung(b, ttl=60, bay_gio=lambda: gio[0])
    d.read_rows(ss.TAB_TRADES)
    gio[0] += 59
    d.read_rows(ss.TAB_NHAT_KY)
    assert d.so_lan_doc == 1 and len(b.doc) == 5
    gio[0] += 2
    d.read_rows(ss.TAB_TRADES)
    assert d.so_lan_doc == 2 and len(b.doc) == 10
    d.lam_moi()
    d.read_rows(ss.TAB_KE_HOACH)
    assert d.so_lan_doc == 3


def test_co_dau_gio_doc_va_lam_moi_doc_cua_ca_tien_trinh(monkeypatch):
    b = _Dem(_so_mau())
    _gan_backend(monkeypatch, b)
    assert gss.doc_luc_gan_nhat() is None
    gss.load_nhat_ky_from_google_sheets(gss.backend_doc_chung())
    luc = gss.doc_luc_gan_nhat()
    assert luc is not None and luc.tzinfo is not None
    n = len(b.doc)
    gss.lam_moi_doc()
    gss.load_so_ban_tin_from_google_sheets(gss.backend_doc_chung())
    assert len(b.doc) == 2 * n


def test_chua_cau_hinh_thi_none_va_khong_nho(monkeypatch):
    _gan_backend(monkeypatch, None)
    assert gss.backend_doc_chung() is None and gss.doc_luc_gan_nhat() is None
    assert gss.load_nhat_ky_from_google_sheets(gss.backend_doc_chung()) is None


def test_hang_so_han_la_lua_chon_da_khai():
    assert gss.TTL_DOC_APP == 30 * 60 and gss.TTL_DOC_APP > 5 * 60


def test_dong_tra_ve_la_ban_sao_khong_lam_ban_doc_chung_hong():
    d = gss.BackendDocChung(_Dem(_so_mau()))
    a = d.read_rows(ss.TAB_TRADES)
    a[0][0] = "HONG"
    a.append(["them"])
    assert d.read_rows(ss.TAB_TRADES)[0][0] == ss.TRADE_COLS[0] and len(d.read_rows(ss.TAB_TRADES)) == 3


# ── 4. lỗi vẫn hiện ─────────────────────────────────────────────────────────
def test_tab_doc_loi_thi_bo_doc_can_no_NO_nguyen_loi_va_khong_bi_nho():
    class Hong(_Dem):
        so_lan_hong = 0

        def read_rows(self, tab):
            if tab == ss.TAB_KE_HOACH and Hong.so_lan_hong < 1000:
                Hong.so_lan_hong += 1
                self.doc.append(tab)
                raise ConnectionError("mạng đứt")
            return super().read_rows(tab)
    b = Hong(_so_mau())
    d = gss.BackendDocChung(b)
    assert gss.load_nhat_ky_from_google_sheets(d)              # tab khác vẫn dùng được
    with pytest.raises(ConnectionError, match="mạng đứt"):
        gss.load_ke_hoach_from_google_sheets(d)
    n1 = Hong.so_lan_hong
    with pytest.raises(ConnectionError):
        gss.load_ke_hoach_from_google_sheets(d)
    assert Hong.so_lan_hong == n1 + 1, "lỗi KHÔNG được nhớ: lượt sau đọc lại"


def test_ke_hoach_lech_tieu_de_chi_hong_bo_doc_cua_ke_hoach():
    mau = _so_mau()
    mau.tabs[ss.TAB_KE_HOACH][0] = ["cot_la"] + list(ss.KE_HOACH_COLS)[1:]
    d = gss.BackendDocChung(_Dem(mau))
    with pytest.raises(ss.SheetError):
        gss.load_ke_hoach_from_google_sheets(d)
    assert len(gss.load_nhat_ky_from_google_sheets(d)) == 2
    assert len(gss.load_so_ban_tin_from_google_sheets(d)["lenh"]) == 2


def test_tab_chua_co_la_rong_that_khong_phai_none():
    mau = _so_mau()
    del mau.tabs[ss.TAB_KE_HOACH]
    kq = gss.load_ke_hoach_from_google_sheets(gss.BackendDocChung(_Dem(mau)))
    assert kq == []                                           # đã cấu hình, chưa có dòng -> [] (khác None)


# ── 5. không bao giờ ghi ────────────────────────────────────────────────────
def test_backend_chung_nem_khi_bi_goi_ghi():
    d = gss.BackendDocChung(_Dem(_so_mau()))
    with pytest.raises(ss.SheetError):
        d.write_all("trades", [["x"]])
    with pytest.raises(ss.SheetError):
        d.append_rows("trades", [["x"]])


def _ham(cay, ten):
    return next(n for n in ast.walk(cay) if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == ten)


def _ten_goi(nut):
    return {getattr(n.func, "attr", getattr(n.func, "id", "")) for n in ast.walk(nut) if isinstance(n, ast.Call)}


def test_AST_doc_chung_khong_goi_ham_ghi_nao():
    gcay = ast.parse((GOC / "google_sheets_sync.py").read_text(encoding="utf-8"))
    for ten in ("BackendDocChung", "backend_doc_chung", "lam_moi_doc", "doc_luc_gan_nhat"):
        da = _ten_goi(_ham(gcay, ten))
        assert not da & (TEN_GHI - {"write_all", "append_rows"}), (ten, da & TEN_GHI)
    # hai phương thức ghi của lớp bọc chỉ NỔ, không gọi gì
    lop = _ham(gcay, "BackendDocChung")
    for pt in (n for n in lop.body if isinstance(n, ast.FunctionDef) and n.name in ("write_all", "append_rows")):
        assert isinstance(pt.body[-1], ast.Raise) and not _ten_goi(pt) - {"SheetError"}
    scay = ast.parse((GOC / "sheets_store.py").read_text(encoding="utf-8"))
    nh = _ten_goi(_ham(scay, "read_rows_nhieu"))
    assert not nh & TEN_GHI and nh <= {"worksheets", "get_all_values", "get"}, nh


def test_AST_app_ba_bo_doc_di_qua_backend_chung_va_giu_dem_va_han():
    cay = ast.parse((GOC / "app.py").read_text(encoding="utf-8"))
    for ten, load in (("_doc_nhat_ky", "load_nhat_ky_from_google_sheets"),
                      ("_doc_so_ban_tin", "load_so_ban_tin_from_google_sheets"),
                      ("_doc_ke_hoach", "load_ke_hoach_from_google_sheets")):
        f = _ham(cay, ten)
        dec = [ast.unparse(d) for d in f.decorator_list]
        assert any("st.cache_data" in d and "TTL_DOC_APP" in d for d in dec), (ten, dec)
        goi = [n for n in ast.walk(f) if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == load]
        assert len(goi) == 1 and "backend_doc_chung" in ast.unparse(goi[0]), ten


def test_AST_nut_doc_lai_so_xoa_ca_ba_dem_va_ban_doc_chung_va_co_dau_gio():
    cay = ast.parse((GOC / "app.py").read_text(encoding="utf-8"))
    f = _ham(cay, "_lam_moi_so")
    src = ast.unparse(f)
    for t in ("lam_moi_doc()", "_doc_nhat_ky.clear()", "_doc_so_ban_tin.clear()", "_doc_ke_hoach.clear()"):
        assert t in src, t
    # nút: một `if st.button(..., key="doc_lai_so")` mà THÂN gọi `_lam_moi_so()` rồi `st.rerun()`
    nut = [n for n in ast.walk(cay) if isinstance(n, ast.If) and isinstance(n.test, ast.Call)
           and ast.unparse(n.test.func) == "st.button"
           and any(k.arg == "key" and isinstance(k.value, ast.Constant) and k.value.value == "doc_lai_so"
                   for k in n.test.keywords)]
    assert len(nut) == 1
    assert [ast.unparse(s) for s in nut[0].body] == ["_lam_moi_so()", "st.rerun()"]
    # dấu giờ: giờ của lượt đọc thật (`doc_luc_gan_nhat()`) đi vào chuỗi f định dạng %H:%M
    gan = [n for n in ast.walk(cay) if isinstance(n, ast.Assign) and ast.unparse(n.value) == "_gss_doc.doc_luc_gan_nhat()"]
    assert len(gan) == 1 and ast.unparse(gan[0].targets[0]) == "_gio_doc_so"
    dung = [n for n in ast.walk(cay) if isinstance(n, ast.FormattedValue) and isinstance(n.value, ast.Name)
            and n.value.id == "_gio_doc_so" and n.format_spec is not None and "%H:%M" in ast.unparse(n.format_spec)]
    assert len(dung) == 1


def test_duong_quet_khong_nhac_ten_moi_cua_app():
    cam = {"backend_doc_chung", "BackendDocChung", "read_rows_nhieu", "lam_moi_doc", "doc_luc_gan_nhat", "TAB_APP_DOC"}
    for p in [GOC / f for f in ("run_daily.py", "paper_runner.py", "san_dau.py", "paper_trading.py")] + \
             sorted((GOC / "backtest").glob("*.py")):
        if not p.exists():
            continue
        for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if isinstance(n, ast.Attribute):
                ten = n.attr
            elif isinstance(n, ast.Name):
                ten = n.id
            elif isinstance(n, ast.alias):
                ten = n.name
            else:
                continue
            assert ten not in cam, f"{p.name}:{n.lineno if hasattr(n, 'lineno') else '?'} nhắc {ten}"
