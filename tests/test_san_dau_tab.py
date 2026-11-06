"""Gác cho tab "🏟️ Sân đấu" (BƯỚC 257, Lát 4 của C1; `docs/thiet-ke-c1-san-dau.md` mục 10.1 và 11, gác G6).

Tab CHỈ ĐỌC và CHỈ IN: không nút ghi, không đẩy Sheets, không ghi file; mọi KTC là chuỗi do `san_dau.dinh_dang_ktc` ghép
(nơi DUY NHẤT có "95%", luôn kèm độ phủ đo được); biểu ngữ không tắt được. Cộng:
  · đường đọc Sheets MỚI (`sheets_store.doc_quyet_dinh_san_dau`): bản tin bỏ ba cột `components`, `reasons`,
    `data_quality` của tab `decisions`, mà bộ phát lại cần cả ba — thiếu `data_quality` thì cổng chất lượng dữ liệu
    chặn MỌI tín hiệu, nên phải có một đường đọc đủ cột, và nó cũng chỉ gọi `read_rows`;
  · hàm hiển thị thuần (`bang_hien_thi`, `duong_von`) không tính lại số nào.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pandas as pd
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.append(str(GOC / "tools"))

import google_sheets_sync as gss  # noqa: E402
import san_dau as sd  # noqa: E402
import sheets_store as ss  # noqa: E402
import sinh_bang_vang_phien as S  # noqa: E402
from test_san_dau import _sach_cache_phan_tich  # noqa: E402
from test_san_dau_b6 import _bang, _ke_hoach_tu  # noqa: E402

assert _sach_cache_phan_tich

TEN_GHI = {"push", "write_all", "append_rows", "pull", "record_trade", "update_trade", "record_decision",
           "commit", "executemany", "executescript", "ghi_ke_hoach", "open", "write_text", "write_bytes",
           "unlink", "to_csv", "to_json", "dump", "mkdir", "sync_trades_to_google_sheets",
           "restore_journal_from_google_sheets", "keo_so_co_thu_lai"}


def _cay(duong):
    return ast.parse((GOC / duong).read_text(encoding="utf-8"))


def _ham(cay, ten):
    return next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == ten)


def _goi(nut):
    ra = set()
    for n in ast.walk(nut):
        if isinstance(n, ast.Call):
            f = n.func
            ra.add(f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else "")
    return ra


@pytest.fixture(scope="module")
def gia():
    return S.dung_gia()


@pytest.fixture(scope="module")
def bang(gia):
    return _bang(gia, _ke_hoach_tu)


# ── 1. đường đọc Sheets mới ───────────────────────────────────────────────────────────────────
def _sheet_quyet_dinh():
    b = ss.InMemorySheet()
    b.write_all(ss.TAB_DECISIONS, [list(ss.DECISION_COLS),
                                   ["1", "1.7e9", "AAA", "2026-10-01", "70", "MUA", "1", "", '{"a": 1}', '["x"]', "OK"],
                                   ["2", "1.7e9", "BBB", "2026-10-01", "50", "GIỮ", "0", "điểm 50", "{}", "[]", "WARN"]])
    return b


def test_doc_quyet_dinh_san_dau_giu_dung_chin_cot_ma_bo_phat_lai_can():
    ds = ss.doc_quyet_dinh_san_dau(_sheet_quyet_dinh())
    assert [set(d) for d in ds] == [set(ss.COT_QUYET_DINH_SAN_DAU)] * 2
    assert ds[0]["data_quality"] == "OK" and ds[1]["data_quality"] == "WARN"
    assert ds[0]["score"] == 70 and ds[0]["components"] == '{"a": 1}' and ds[0]["reasons"] == '["x"]'
    # bản tin KHÔNG đủ cho bộ phát lại: thiếu data_quality, components, reasons
    assert not ({"data_quality", "components", "reasons"} & set(ss.COT_QUYET_DINH_BAN_TIN))
    assert {"data_quality", "components", "reasons", "seq", "at", "symbol", "signal_date", "score",
            "recommendation"} == set(ss.COT_QUYET_DINH_SAN_DAU)


def test_doc_quyet_dinh_san_dau_chay_duoc_qua_bo_phat_lai_va_giu_cong_chat_luong_du_lieu():
    """Đường đọc đủ cột đưa data_quality vào `ket_qua_tu_dong`: thiếu nó là mọi tín hiệu bị chặn ở cổng chất lượng."""
    qd = ss.doc_quyet_dinh_san_dau(_sheet_quyet_dinh())
    kq = sd.ket_qua_tu_dong(qd[0], "AAA", pd.DataFrame({"time": ["2026-10-01"], "close": [1.0]}), 62)
    assert kq["data_quality"] == "OK" and kq["final_score"] == 70 and kq["score_breakdown"] == {"a": 1}
    assert kq["key_reasons"] == ["x"]


def test_doc_quyet_dinh_san_dau_tab_rong_la_danh_sach_rong_va_tieu_de_lech_thi_NO():
    assert ss.doc_quyet_dinh_san_dau(ss.InMemorySheet()) == []
    xau = _sheet_quyet_dinh()
    hang = xau.read_rows(ss.TAB_DECISIONS)
    hang[0] = ["diem" if c == "score" else c for c in hang[0]]
    xau.write_all(ss.TAB_DECISIONS, hang)
    with pytest.raises(ss.SheetSchemaError):
        ss.doc_quyet_dinh_san_dau(xau)


def test_doc_quyet_dinh_san_dau_CHI_goi_read_rows_va_wrapper_tra_None_khi_chua_cau_hinh(monkeypatch):
    goi = _goi(_ham(_cay("sheets_store.py"), "doc_quyet_dinh_san_dau"))
    assert "_doc_tab" in goi and not (TEN_GHI & goi), sorted(TEN_GHI & goi)
    monkeypatch.setattr(gss._ss, "open_from_secrets", lambda: None)
    assert gss.load_quyet_dinh_san_dau_from_google_sheets() is None
    assert [d["symbol"] for d in gss.load_quyet_dinh_san_dau_from_google_sheets(_sheet_quyet_dinh())] == ["AAA", "BBB"]
    assert not (TEN_GHI & _goi(_ham(_cay("google_sheets_sync.py"), "load_quyet_dinh_san_dau_from_google_sheets")))


# ── 2. hiển thị thuần ─────────────────────────────────────────────────────────────────────────
def test_bang_hien_thi_co_mot_hang_moi_tai_khoan_va_KTC_la_nguyen_chuoi_cua_dinh_dang_ktc(bang):
    cli, b, *_ = bang
    hien = sd.bang_hien_thi(b)
    ten = [r["Tài khoản"] for r in hien["tai_khoan"]]
    assert ten[0].startswith("duong that") and ten[1:4] == ["PB-001", "PB-002", "PB-003"]
    assert ten[4].startswith("Rổ") and len(ten) == 5
    for r, h in zip(hien["tai_khoan"][:4], [b["that"], *b["phuong_an"]]):
        assert r["KTC thước 1"] == h["ktc"]["thuoc1"]["dong"], "KTC phải là chuỗi đã ghép, không tự ghép lại"
    assert [r["Phương án"] for r in hien["so_voi_duong_that"]] == ["PB-001", "PB-002", "PB-003"]
    for r, h in zip(hien["so_voi_duong_that"], b["phuong_an"]):
        assert r["KTC thước 2"] == h["ktc"]["thuoc2"]["dong"]
    assert hien["tai_khoan"][4]["KTC thước 1"].startswith("không có")
    # hai khối nhãn tách riêng: mỗi phương án hai hàng, không hàng "tổng"
    assert [(r["Phương án"], r["Khối"]) for r in hien["khoi"]] == [
        (p, k) for p in ("PB-001", "PB-002", "PB-003") for k in ("đã nhìn", "chưa nhìn")]
    assert any(g.startswith("PB-003") and "kế hoạch B6" in g for g in hien["ghi_chu"])


def test_bang_hien_thi_cua_so_rieng_cua_PB003_hien_ra_o_bang_so_voi_duong_that(bang):
    _, b, *_ = bang
    hien = sd.bang_hien_thi(b)
    cs = {r["Phương án"]: r["Cửa sổ"] for r in hien["so_voi_duong_that"]}
    assert cs["PB-001"] == "chung" and cs["PB-002"] == "chung"
    assert cs["PB-003"].startswith("RIÊNG từ 2026-")


def test_bang_hien_thi_tab_ke_hoach_rong_noi_cua_so_rong(gia):
    _, b, *_ = _bang(gia, lambda qd: [])
    cs = {r["Phương án"]: r["Cửa sổ"] for r in sd.bang_hien_thi(b)["so_voi_duong_that"]}
    assert cs["PB-003"] == "RIÊNG: tab kế hoạch rỗng"


def test_duong_von_cua_moi_tai_khoan_va_cua_so_rieng_cua_PB003(gia):
    tu = S.PHIEN[60]
    _, b, *_ = _bang(gia, lambda qd: _ke_hoach_tu(qd, tu))
    dv = sd.duong_von(b)
    assert dv.columns[0].startswith("duong that")
    assert list(dv.columns[1:]) == ["PB-001", "PB-002", "PB-003", "Rổ đều"]
    assert list(dv.index) == b["phien"]
    for h in [b["that"], *b["phuong_an"]]:
        cot = dv[h["ten"] if h["id"] is None else h["id"]].dropna()
        assert list(cot.index) == h["phien_dung"]
        assert cot.iloc[-1] == pytest.approx(h["cong_don"]) if len(cot) else h["cong_don"] == 0
    pb3 = dv["PB-003"]
    assert pb3[:tu].iloc[:-1].isna().all() and pb3.dropna().index[0] >= tu, "PB-003 chỉ có số từ ngày có kế hoạch"
    assert dv["Rổ đều"].dropna().iloc[-1] == pytest.approx(b["ro"]["cong_don"])


# ── 3. gác G6 và gác của tab trên app ─────────────────────────────────────────────────────────
HAM_APP = ("_nap_san_dau_cli", "_chay_san_dau", "_khoi_san_dau")


def _chuoi_khong_phai_docstring(nut):
    doc = {id(n.body[0].value) for n in ast.walk(nut)
           if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body
           and isinstance(n.body[0], ast.Expr) and isinstance(getattr(n.body[0], "value", None), ast.Constant)}
    return [n.value for n in ast.walk(nut) if isinstance(n, ast.Constant) and isinstance(n.value, str)
            and id(n) not in doc]


def test_G6_95_phan_tram_chi_duoc_ghep_o_dinh_dang_ktc():
    for duong in ("san_dau.py", "tools/san_dau.py"):
        cay = _cay(duong)
        for ham in [n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef)]:
            co = [c for c in _chuoi_khong_phai_docstring(ham) if "95%" in c]
            if ham.name != "dinh_dang_ktc":
                assert not co, (duong, ham.name)
    co = [c for c in _chuoi_khong_phai_docstring(_ham(_cay("san_dau.py"), "dinh_dang_ktc")) if "95%" in c]
    assert co and "độ phủ đo được" in ast.unparse(_ham(_cay("san_dau.py"), "dinh_dang_ktc"))
    cay_app = _cay("app.py")
    for ten in HAM_APP:
        assert not [c for c in _chuoi_khong_phai_docstring(_ham(cay_app, ten)) if "95%" in c], ten


def test_G6_bieu_ngu_dung_chu_cua_dac_ta_va_khong_tat_duoc():
    assert sd.BIEU_NGU == "THĂM DÒ — không bao giờ lên bản"
    ham = _ham(_cay("app.py"), "_khoi_san_dau")
    canh_bao = [n for n in ast.walk(ham) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "warning" and "BIEU_NGU" in ast.unparse(n)]
    assert len(canh_bao) == 1, "biểu ngữ là MỘT st.warning dùng san_dau.BIEU_NGU"
    # nằm trước nút bấm và trước mọi nhánh return: hiện ngay cả khi chưa phát lại
    thu_tu = [n.lineno for n in ast.walk(ham) if isinstance(n, ast.Return)]
    nut = [n for n in ast.walk(ham) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
           and n.func.attr == "button"]
    assert canh_bao[0].lineno < min(thu_tu) and canh_bao[0].lineno < nut[0].lineno


def test_G6_tab_khong_co_nut_ghi__dung_mot_nut_bam_va_khong_goi_ham_ghi():
    cay = _cay("app.py")
    nut_tong = []
    for ten in HAM_APP:
        ham = _ham(cay, ten)
        goi = _goi(ham)
        assert not (TEN_GHI & goi), (ten, sorted(TEN_GHI & goi))
        nut_tong += [n for n in ast.walk(ham) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                     and n.func.attr == "button"]
    assert len(nut_tong) == 1
    khoa = {k.arg: ast.literal_eval(k.value) for k in nut_tong[0].keywords}
    assert khoa == {"key": "san_dau_chay"}


def test_G5_tab_khong_dung_den_ung_vien_nao():
    cay = _cay("app.py")
    van = "\n".join(ast.unparse(_ham(cay, t)) for t in HAM_APP)
    for cam in ("UV-", "ung-vien", "SO_UNG_VIEN", "doc_so_ung_vien", "diem_ung_vien", "cham_bong"):
        assert cam not in van, cam


def test_tab_chi_goi_dung_ba_duong_doc_va_bang_cho_app():
    cay = _cay("app.py")
    goi = _goi(_ham(cay, "_chay_san_dau"))
    assert {"_doc_so_ban_tin", "load_quyet_dinh_san_dau_from_google_sheets", "_doc_ke_hoach",
            "bang_cho_app"} <= goi
    assert "dung_bang" not in goi, "app KHÔNG tự dựng bảng: nó gọi bản chuẩn `bang_cho_app` của tools/san_dau.py"
    hien = _goi(_ham(cay, "_khoi_san_dau"))
    assert {"bang_hien_thi", "duong_von"} <= hien and "ktc_co_nhan" not in hien and "dinh_dang_ktc" not in hien
    nho = [n for n in _ham(cay, "_chay_san_dau").decorator_list]
    assert any("cache_data" in ast.unparse(d) for d in nho), "phát lại tốn vài chục giây: phải có đệm"


def test_tab_nam_trong_danh_sach_tab_cua_app_va_so_bien_bang_so_nhan():
    cay = _cay("app.py")
    gan = next(n for n in ast.walk(cay) if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call)
               and isinstance(n.value.func, ast.Attribute) and n.value.func.attr == "tabs")
    ten = [t.id for t in gan.targets[0].elts]
    nhan = [ast.literal_eval(e) if isinstance(e, ast.Constant) else None for e in gan.value.args[0].elts]
    assert len(ten) == len(nhan) and "t_san_dau" in ten
    assert ten.index("t_san_dau") == ten.index("t_bong") + 1, "tab mới đứng cạnh tab 'bóng' của tầng 3"
    assert nhan[ten.index("t_san_dau")] == "🏟️ Sân đấu"
    khoi = [n for n in ast.walk(cay) if isinstance(n, ast.With)
            and any(isinstance(i.context_expr, ast.Name) and i.context_expr.id == "t_san_dau" for i in n.items)]
    assert len(khoi) == 1 and [ast.unparse(s) for s in khoi[0].body] == ["_khoi_san_dau()"]


def _ghi_lenh(ten):
    def f(self, *a, **k):
        self.log.append((ten, a, k))
    return f


class _St:
    """`streamlit` giả: ghi lại thứ tự lệnh vẽ; `button` trả giá trị đặt sẵn."""

    def __init__(self, bam=False, da_bam=False):
        import contextlib
        self.log, self.session_state, self._bam = [], ({"san_dau_da_bam": True} if da_bam else {}), bam
        self.spinner = lambda *a, **k: contextlib.nullcontext()

    markdown = _ghi_lenh("markdown")
    warning = _ghi_lenh("warning")
    caption = _ghi_lenh("caption")
    info = _ghi_lenh("info")
    dataframe = _ghi_lenh("dataframe")
    line_chart = _ghi_lenh("line_chart")

    def button(self, *a, **k):
        self.log.append(("button", a, k))
        return self._bam


def _chay_khoi(st, kq=None, loi=None):
    """Chạy ĐÚNG mã của `_khoi_san_dau` trong `app.py` với `streamlit` giả và `_chay_san_dau` giả."""
    cay = _cay("app.py")
    ma = ast.unparse(_ham(cay, "_khoi_san_dau"))
    def chay_san_dau():
        if loi:
            raise loi
        return kq
    ns = {"st": st, "pd": pd, "_chay_san_dau": chay_san_dau}
    exec(compile(ma, "app.py::_khoi_san_dau", "exec"), ns)
    ns["_khoi_san_dau"]()


def test_khoi_san_dau_chua_bam_nut_chi_hien_bieu_ngu_va_loi_moi_khong_tinh_gi():
    st = _St()
    _chay_khoi(st)                                              # `kq` None: nếu hàm đụng tới nó thì nổ
    ten = [x[0] for x in st.log]
    assert ten[:3] == ["markdown", "warning", "caption"] and st.log[1][1][0] == "🏟️ " + sd.BIEU_NGU
    assert "button" in ten and "dataframe" not in ten and ten[-1] == "info"


def test_khoi_san_dau_thieu_dau_vao_thi_NOI_thieu_khong_hien_so(bang):
    st = _St(da_bam=True)
    _chay_khoi(st, kq={"loi": "kho ngoài chưa cấu hình"})
    ten = [x[0] for x in st.log]
    assert ten.count("warning") == 2 and "dataframe" not in ten and "line_chart" not in ten
    assert "kho ngoài chưa cấu hình" in st.log[-1][1][0]
    st = _St(da_bam=True)
    _chay_khoi(st, loi=RuntimeError("mạng chết"))
    assert "mạng chết" in st.log[-1][1][0] and "dataframe" not in [x[0] for x in st.log]


def test_khoi_san_dau_da_bam_hien_ba_bang_va_duong_von_va_hai_khoi_nhan(bang):
    _, b, *_ = bang
    st = _St(bam=True)
    _chay_khoi(st, kq={"bang": b, "ghi_chu": ["gia: x"], "ma_thieu_gia": ["ZZZ"]})
    ten = [x[0] for x in st.log]
    assert ten.count("dataframe") == 3 and ten.count("line_chart") == 1
    khung = [x[1][0] for x in st.log if x[0] == "dataframe"]
    assert len(khung[0]) == 5, "năm hàng: đường thật, PB-001, PB-002, PB-003, rổ"
    assert len(khung[2]) == 6, "hai khối nhãn x ba phương án, không hàng tổng"
    assert any("ZZZ" in x[1][0] for x in st.log if x[0] == "caption")


def test_app_nhap_san_dau_la_ngoai_le_G2_da_duoc_mo():
    """G2 (đặc tả mục 11): `app.py` ĐƯỢC nhập `san_dau`; nay nó nhập thật (trong hàm)."""
    van = ast.unparse(_ham(_cay("app.py"), "_khoi_san_dau"))
    assert "import san_dau as _sd" in van
