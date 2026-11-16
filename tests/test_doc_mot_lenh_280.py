"""BƯỚC 280, phần A — app đọc năm tab Google Sheets bằng MỘT lệnh `values_batch_get`, dữ liệu y hệt.

Khoá bốn điều (đột biến ở `docs/STATE.md` BƯỚC 280):

1. **Cùng dòng**: đường một-lệnh (`read_rows_nhieu`) trả ĐÚNG thứ mà đường từng-tab cũ
   (`get_all_values`, BƯỚC 275) trả, trên dữ liệu có dòng ngắn (API cắt ô rỗng ở cuối dòng), ô rỗng
   ở giữa (NULL khác chuỗi rỗng), tab rỗng, tab chỉ có tiêu đề — và các bộ đọc `doc_*` cho ra cùng
   danh sách dict (kiểu, NULL, tiêu đề).
2. **Một lệnh**: năm tab có mặt thì đúng MỘT `values_batch_get`, không `worksheets()`, không `get_all_values()`.
3. **Lỗi vẫn hiện**: tab chưa có (API trả 400) rơi về đường cũ và ra `[]`; lỗi khác là giá trị của mọi tab.
4. **Chỉ đọc**: không đường ghi nào được chạm.

Bản giả mô phỏng API: một tab là lưới chuỗi; `values_batch_get` trả dòng đã bị cắt ô rỗng cuối dòng và
bỏ dòng rỗng cuối bảng; tab rỗng thì vùng KHÔNG có khoá `values`. Đường cũ dùng phép đệm VIẾT RIÊNG ở
đây (không phải `fill_gaps` của gspread) để phép so không tự kiểm chính nó.
"""
import ast
import pathlib

import pytest
from gspread.exceptions import APIError

import google_sheets_sync as gss
import sheets_store as ss

GOC = pathlib.Path(__file__).resolve().parent.parent


def _dong(cols, **kv):
    return [str(kv.get(c, "")) for c in cols]


def _luoi_mau() -> dict:
    """Năm tab, có đủ hình dạng khó: ô rỗng giữa dòng, dòng ngắn, NULL và chuỗi rỗng."""
    return {
        ss.TAB_TRADES: [list(ss.TRADE_COLS),
                        _dong(ss.TRADE_COLS, id=1, symbol="HPG", status="CLOSED", entry_date="2026-10-01",
                              exit_date="2026-10-09", exit_reason="STOP_LOSS", size_pct="2.5"),
                        _dong(ss.TRADE_COLS, id=2, symbol="FPT", status="OPEN", entry_date="2026-11-02")],
        ss.TAB_NHAT_KY: [list(ss.NHAT_KY_COLS),
                         _dong(ss.NHAT_KY_COLS, trade_id=1, symbol="HPG", signal_date="2026-10-01"),
                         _dong(ss.NHAT_KY_COLS, trade_id=2, symbol="FPT", signal_date="2026-11-02")],
        ss.TAB_DECISIONS: [list(ss.DECISION_COLS),
                           _dong(ss.DECISION_COLS, seq=1, at="1.7e9", symbol="HPG", signal_date="2026-10-01",
                                 score="70", recommendation="BUY", acted="1", components="{}"),
                           _dong(ss.DECISION_COLS, seq=2, symbol="FPT", signal_date="2026-11-02", score="",
                                 skip_reason="điểm dưới ngưỡng"),
                           _dong(ss.DECISION_COLS, seq=3, symbol="VNM", signal_date="2026-11-02", score="40",
                                 acted="0", skip_reason="", data_quality="{\"x\": 1}")],
        ss.TAB_HAU_KIEM: [list(ss.HAU_KIEM_COLS)],
        ss.TAB_KE_HOACH: [list(ss.KE_HOACH_COLS),
                          _dong(ss.KE_HOACH_COLS, seq=5, symbol="HPG", signal_date="2026-11-02")],
    }


def _cat_nhu_api(rows: list) -> list:
    """Hình dạng API trả: bỏ ô rỗng CUỐI mỗi dòng, bỏ dòng rỗng CUỐI bảng."""
    ra = []
    for r in rows:
        r = list(r)
        while r and r[-1] == "":
            r.pop()
        ra.append(r)
    while ra and not ra[-1]:
        ra.pop()
    return ra


def _dem_deu(values: list) -> list:
    """Đệm VIẾT RIÊNG (không phải `fill_gaps`): mọi dòng dài bằng dòng dài nhất."""
    if not values:
        return [[]]
    n = max(len(r) for r in values)
    return [list(r) + [""] * (n - len(r)) for r in values]


def _loi_api(ma: int) -> APIError:
    class _Tl:
        status_code = ma
        text = "x"

        def json(self):
            return {"error": {"code": ma, "message": "Unable to parse range", "status": "X"}}
    return APIError(_Tl())


class _Ws:
    def __init__(self, ten, luoi, nhat):
        self.title, self._luoi, self._nhat = ten, luoi, nhat

    def get_all_values(self):
        self._nhat.append(("get_all_values", self.title))
        return _dem_deu(_cat_nhu_api(self._luoi))

    def update(self, *a, **k):
        raise AssertionError("GHI")


class _Sh:
    """Spreadsheet giả. Mọi lệnh gọi được ghi vào `nhat`; mọi đường ghi nổ."""

    def __init__(self, luoi, loi_batch=None):
        self.luoi, self.nhat, self.loi_batch = luoi, [], loi_batch

    def values_batch_get(self, ranges, params=None):
        self.nhat.append(("values_batch_get", tuple(ranges)))
        if self.loi_batch is not None:
            raise self.loi_batch
        ra = []
        for r in ranges:
            ten = r[1:-1].replace("''", "'")
            if ten not in self.luoi:
                raise _loi_api(400)
            v = _cat_nhu_api(self.luoi[ten])
            ra.append({"range": r, "majorDimension": "ROWS", **({"values": v} if v else {})})
        return {"spreadsheetId": "x", "valueRanges": ra}

    def worksheets(self):
        self.nhat.append(("worksheets",))
        return [_Ws(t, g, self.nhat) for t, g in self.luoi.items()]

    def worksheet(self, t):
        raise AssertionError("không được hỏi từng tab")

    def add_worksheet(self, **k):
        raise AssertionError("TẠO tab")

    def batch_update(self, *a, **k):
        raise AssertionError("GHI")


def _google_gia(luoi, loi_batch=None) -> ss.GoogleSheet:
    g = object.__new__(ss.GoogleSheet)
    g._sh = _Sh(luoi, loi_batch)
    return g


# ── 1. cùng dòng ────────────────────────────────────────────────────────────
def test_mot_lenh_va_tung_tab_tra_cung_dong_tren_du_lieu_kho():
    g = _google_gia(_luoi_mau())
    mot = g.read_rows_nhieu(gss.TAB_APP_DOC)
    cu = g._doc_tung_tab(gss.TAB_APP_DOC)
    assert mot == cu
    assert set(mot) == set(gss.TAB_APP_DOC)
    # dữ liệu có dòng ngắn thật: ô cuối rỗng bị API cắt rồi đệm lại thành chuỗi rỗng, KHÔNG bị mất cột
    assert all(len(r) == len(ss.DECISION_COLS) for r in mot[ss.TAB_DECISIONS])
    assert mot[ss.TAB_DECISIONS][2][ss.DECISION_COLS.index("score")] == ""


def test_tab_rong_va_tab_chi_tieu_de_giong_nhau_hai_duong():
    luoi = _luoi_mau()
    luoi[ss.TAB_KE_HOACH] = []
    luoi[ss.TAB_HAU_KIEM] = [[]]
    g = _google_gia(luoi)
    mot, cu = g.read_rows_nhieu(gss.TAB_APP_DOC), g._doc_tung_tab(gss.TAB_APP_DOC)
    assert mot == cu
    assert mot[ss.TAB_KE_HOACH] == [[]] and mot[ss.TAB_HAU_KIEM] == [[]]


def _doc_het(b):
    return {
        "ban_tin": ss.doc_so_ban_tin(b),
        "nhat_ky": ss.doc_nhat_ky(b),
        "ke_hoach": ss.doc_ke_hoach(b),
        "hau_kiem": ss.doc_hau_kiem(b),
        "san_dau": ss.doc_quyet_dinh_san_dau(b),
    }


def test_cac_bo_doc_cho_cung_dict_NULL_khac_chuoi_rong_va_kieu():
    luoi = _luoi_mau()
    g = _google_gia(luoi)
    moi = _doc_het(gss.BackendDocChung(g))
    # đường tham chiếu: bản InMemorySheet cùng lưới (đọc nguyên lưới, không cắt, không đệm)
    ref = ss.InMemorySheet()
    ref.tabs = {t: [list(r) for r in v] for t, v in luoi.items()}
    cu = _doc_het(ref)
    assert moi == cu
    qd = moi["ban_tin"]["quyet_dinh"]
    assert qd[1]["score"] is None                    # ô rỗng của cột số = NULL
    assert qd[2]["skip_reason"] == ""                # ô rỗng của cột chữ không-null = chuỗi rỗng
    assert qd[0]["score"] == 70 and isinstance(qd[0]["score"], int)


def test_vung_dung_thu_tu_tab_va_xu_ly_dau_nhay_don():
    g = _google_gia({"a'b": [["x", "y"], ["1", ""]], "c": [["z"]]})
    ra = g.read_rows_nhieu(["c", "a'b"])
    assert g._sh.nhat == [("values_batch_get", ("'c'", "'a''b'"))]
    assert ra == {"c": [["z"]], "a'b": [["x", "y"], ["1", ""]]}


# ── 2. một lệnh ─────────────────────────────────────────────────────────────
def test_nam_tab_co_mat_thi_dung_MOT_values_batch_get_khong_hoi_gi_them():
    g = _google_gia(_luoi_mau())
    g.read_rows_nhieu(gss.TAB_APP_DOC)
    assert g._sh.nhat == [("values_batch_get", tuple(f"'{t}'" for t in gss.TAB_APP_DOC))]


def test_backend_doc_chung_that_doc_mot_lan_trong_han():
    g = _google_gia(_luoi_mau())
    d = gss.BackendDocChung(g)
    _doc_het(d)
    assert d.so_lan_doc == 1
    assert [n[0] for n in g._sh.nhat] == ["values_batch_get"]          # năm bộ đọc, MỘT lệnh gọi mạng


# ── 3. lỗi vẫn hiện ─────────────────────────────────────────────────────────
def test_tab_chua_co_roi_ve_duong_cu_va_ra_rong_khong_tao_tab():
    luoi = _luoi_mau()
    del luoi[ss.TAB_HAU_KIEM]
    g = _google_gia(luoi)
    ra = g.read_rows_nhieu(gss.TAB_APP_DOC)
    goi = [n[0] for n in g._sh.nhat if n[0] != "get_all_values"]
    assert goi == ["values_batch_get", "worksheets"]
    assert ra[ss.TAB_HAU_KIEM] == []
    assert ra[ss.TAB_TRADES] == g._doc_tung_tab([ss.TAB_TRADES])[ss.TAB_TRADES]


def test_loi_khac_400_la_gia_tri_cua_moi_tab_khong_hoi_lai():
    loi = _loi_api(429)
    g = _google_gia(_luoi_mau(), loi_batch=loi)
    ra = g.read_rows_nhieu(gss.TAB_APP_DOC)
    assert all(v is loi for v in ra.values()) and set(ra) == set(gss.TAB_APP_DOC)
    assert [n[0] for n in g._sh.nhat] == ["values_batch_get"]          # KHÔNG gọi lại, KHÔNG đổi đường


def test_so_vung_tra_ve_lech_thi_no():
    g = _google_gia(_luoi_mau())
    g._sh.values_batch_get = lambda ranges, params=None: {"valueRanges": []}
    with pytest.raises(ss.SheetError):
        g.read_rows_nhieu(gss.TAB_APP_DOC)


def test_tab_doc_loi_thi_bo_doc_can_no_NO_nguyen_loi():
    """Qua BackendDocChung: lượt đọc cả bộ hỏng thì không tab nào được nhớ, bộ đọc đọc thẳng và nổ đúng lỗi."""
    loi = ConnectionError("mạng đứt")
    g = _google_gia(_luoi_mau(), loi_batch=loi)
    g.read_rows = lambda tab: (_ for _ in ()).throw(loi)
    d = gss.BackendDocChung(g)
    with pytest.raises(ConnectionError, match="mạng đứt"):
        ss.doc_nhat_ky(d)


# ── 4. chỉ đọc ──────────────────────────────────────────────────────────────
def test_AST_ba_ham_doc_khong_co_lenh_ghi_va_chi_goi_lenh_doc():
    TEN_GHI = {"write_all", "append_rows", "add_worksheet", "update", "append_row", "clear",
               "delete_rows", "batch_update", "values_update", "values_batch_update", "values_append",
               "values_clear", "values_batch_clear"}
    cay = ast.parse((GOC / "sheets_store.py").read_text(encoding="utf-8"))
    ten_goi = set()
    for ten in ("read_rows_nhieu", "_doc_tung_tab", "_nhu_get_all_values"):
        ham = next(n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == ten)
        ten_goi |= {getattr(n.func, "attr", getattr(n.func, "id", "")) for n in ast.walk(ham)
                    if isinstance(n, ast.Call)}
    assert not ten_goi & TEN_GHI
    assert "values_batch_get" in ten_goi


def test_AST_read_rows_nhieu_dung_dung_mot_cho_goi_values_batch_get():
    cay = ast.parse((GOC / "sheets_store.py").read_text(encoding="utf-8"))
    ham = next(n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == "read_rows_nhieu")
    goi = [n for n in ast.walk(ham) if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "values_batch_get"]
    assert len(goi) == 1
    # và nó đi MỘT lần, ngoài mọi vòng lặp (lặp theo tab là quay về 5 lượt hỏi)
    for vong in (n for n in ast.walk(ham) if isinstance(n, (ast.For, ast.While, ast.ListComp, ast.DictComp))):
        assert not [n for n in ast.walk(vong) if isinstance(n, ast.Call)
                    and getattr(n.func, "attr", "") == "values_batch_get"]
