"""BƯỚC 286 — mọi đường còn nhắc tới `vnstock` phải sống sót khi vnstock VẮNG (Cloud/Actions).

VÌ SAO CÓ FILE NÀY
──────────────────
Từ BƯỚC 267 (11/11/2026) `requirements.txt` không còn `vnstock`/`vnai`, nhưng máy local còn cài
`vnstock 4.0.9` nên mọi lượt chạy ở máy che mất chỗ hỏng. Lượt đo 20/11/2026 chạy từng đường bằng
một bộ chặn `sys.meta_path` (không gỡ gì khỏi `.venv`): không đường sản xuất nào sập, nhưng ba chỗ
nói SAI nguyên nhân (đổ cho khoá API khi gói vắng) và một script tay (`fetch_fundamentals.py`)
ném traceback. Người dùng 20/11/2026: *"Đổi chữ, giữ ô (Recommended)"* — hộp "🎫 Gói vnstock" ở app
ở lại, XÁM, ghi "vnstock không còn cài ở đây".

NĂM GÁC
  1. bộ chặn thật: mỗi đường đã duyệt, chạy dưới bộ chặn, ra đúng câu "vnstock không còn cài/không
     có nguồn" và KHÔNG ném;
  2. hộp "Gói vnstock" XÁM trong CHÍNH biểu thức của `app.py` (chạy khối AST của app, không dựng
     Streamlit): không cam, không `?`, không dòng cảnh báo;
  3. gác AST: mọi nhập gói hãng ngoài `tests/` nằm trong `try` bắt ImportError, MỌI nơi, trừ một
     danh sách cho phép TƯỜNG MINH (script đo lịch sử) — danh sách cũng phải KHỚP (không thừa);
  4. không nhập gói hãng ở MỨC MODULE ở đâu cả;
  5. không workflow nào `pip install vnstock|vnai`.
Chạy được Ở CẢ HAI môi trường (có và không có vnstock): bộ chặn tự gỡ bản đã nạp.
"""
from __future__ import annotations

import ast
import importlib
import importlib.abc
import re
import sys
import types
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
# `tools/` có file cùng tên với module gốc (`suc_khoe`, `ban_tin`): GOC phải đứng TRƯỚC `tools/`.
sys.path.insert(0, str(GOC / "tools"))
sys.path.insert(0, str(GOC))

CHAN = ("vnstock", "vnstock_data", "vnai", "vnstock_ta", "vnstock_news", "vnstock_pipeline",
        "vnstock_ezchart", "vnii")
GOI_HANG = frozenset(CHAN)


class _BoChan(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name.split(".")[0] in CHAN:
            raise ModuleNotFoundError(f"No module named {name!r} (bộ chặn BƯỚC 286)", name=name)
        return None


@pytest.fixture
def vang(monkeypatch):
    """Giả lập Cloud/Actions: gói hãng KHÔNG nạp được, không có khoá, không nhớ lượt trước."""
    for ten in list(sys.modules):
        if ten.split(".")[0] in CHAN:
            monkeypatch.delitem(sys.modules, ten, raising=False)
    monkeypatch.setattr(sys, "meta_path", [_BoChan(), *sys.meta_path])
    import vnstock_auth
    import vnstock_goi
    monkeypatch.setattr(vnstock_auth, "_read_key", lambda: (None, ""))
    monkeypatch.setattr(vnstock_auth, "_STATE",
                        {"done": False, "ok": False, "source": "", "error": ""})
    vnstock_goi.xoa_cache()
    yield
    vnstock_goi.xoa_cache()


# ══ 1. BỘ CHẶN THẬT — từng đường đã duyệt ═══════════════════════════════════

def test_bo_chan_chan_that():
    """Đối chứng: không có nó thì các gác dưới đo nhầm máy có vnstock."""
    for ten in list(sys.modules):
        if ten.split(".")[0] in CHAN:
            sys.modules.pop(ten, None)
    sys.meta_path.insert(0, _BoChan())
    try:
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("vnstock")
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("vnai.beam")
    finally:
        sys.meta_path.pop(0)


def test_vnstock_auth_goi_dung_ten_nguyen_nhan_khi_vang(vang, monkeypatch):
    import vnstock_auth as va
    monkeypatch.setattr(va, "_read_key", lambda: ("khoa-gia-cua-test", "test"))
    s = va.ensure_api_key(force=True)
    assert s["ok"] is False and s["error"] == va.LOI_VANG, s
    msg = va.status_message()
    assert "không còn cài" in msg and "khoá-gia" not in msg and "khoa-gia" not in msg
    assert "ModuleNotFoundError" not in msg, msg


def test_vnstock_auth_khong_khoa_van_noi_chua_cau_hinh(vang):
    import vnstock_auth as va
    s = va.ensure_api_key(force=True)
    assert s["ok"] is False and s["error"].startswith("chưa cấu hình"), s


def test_kiem_goi_that_noi_vang_chu_khong_do_cho_khoa(vang):
    import vnstock_goi as vg
    tt = vg.kiem_goi(dung_cache=False)
    assert tt.tinh_trang == vg.CHUA_KIEM_DUOC and tt.dat is False
    assert tt.goi_vang is True, tt
    assert vg.CHU_O_VANG in tt.ly_do and "API key" not in tt.ly_do, tt.ly_do
    assert vg.CHU_O_VANG in tt.dong_log()


def test_kiem_goi_thieu_module_KHAC_khong_bi_gan_nhan_vang(vang, monkeypatch):
    """Chỉ `vnai`/`vnstock` vắng mới là "gói vắng"; thiếu module khác là lỗi thật, phải còn nói ra."""
    import vnstock_auth
    import vnstock_goi as vg

    def _no(*a, **k):
        raise ModuleNotFoundError("No module named 'mot_goi_khac'", name="mot_goi_khac")
    monkeypatch.setattr(vnstock_auth, "ensure_api_key", _no)
    tt = vg.kiem_goi(dung_cache=False)
    assert tt.goi_vang is False and tt.tinh_trang == vg.CHUA_KIEM_DUOC
    assert "không đọc được API key (ModuleNotFoundError)" in tt.ly_do, tt.ly_do


def test_kiem_goi_vang_khong_ghi_cache_de_xuyen_test_khac(vang):
    import vnstock_goi as vg
    vg.kiem_goi()                    # dung_cache=True: đường app dùng
    assert vg.kiem_goi().goi_vang is True


def test_kiem_goi_tiem_ham_gia_KHONG_di_qua_nhanh_vang(vang):
    """Test cũ tiêm `lay_khoa`: nhánh vắng chỉ dành cho đường THẬT, không nuốt bản tiêm."""
    import vnstock_goi as vg
    tt = vg.kiem_goi(tai_ve=lambda u, p, c: {"subscription": {"tier": "silver", "isActive": True},
                                              "userType": "paid"},
                     lay_khoa=lambda: "khoa-gia", dung_cache=False)
    assert tt.goi_vang is False and tt.tinh_trang != vg.CHUA_KIEM_DUOC, tt


def test_hang_hop_app_vang_la_xam_khong_cam_khong_hoi(vang):
    import vnstock_goi as vg
    chu, nhan, lop, canh_bao = vg.hang_hop_app(vg.kiem_goi(dung_cache=False))
    assert (chu, lop, canh_bao) == ("vnstock không còn cài ở đây", "xam", "")
    assert "?" not in nhan and lop != "wn"


@pytest.mark.parametrize("tt, lop, nhan", [
    ("khop", "ac", "● ĐÚNG"), ("lech", "wn", "● LỆCH"), ("chua", "wn", "● ?")])
def test_hang_hop_app_ba_trang_thai_cu_giu_nguyen(tt, lop, nhan):
    import vnstock_goi as vg
    mau = {"khop": vg.TrangThaiGoi(tinh_trang=vg.KHOP, hang_may_chu="silver", hang_cuc_bo="silver",
                                   het_han="2026-11-22"),
           "lech": vg.TrangThaiGoi(tinh_trang=vg.LECH, hang_may_chu="silver", hang_cuc_bo="free"),
           "chua": vg.TrangThaiGoi(tinh_trang=vg.CHUA_KIEM_DUOC, ly_do="mất mạng")}[tt]
    chu, n, l, canh_bao = vg.hang_hop_app(mau)
    assert (l, n) == (lop, nhan)
    assert bool(canh_bao) == (tt != "khop")        # ĐÚNG thì không cảnh báo; hai cái kia thì có


def test_suc_khoe_kiem_goi_noi_vang_va_van_xam(vang):
    import suc_khoe as sk
    trang_thai, ly_do, _ = sk._chay_kiem_goi()
    assert trang_thai == sk.CHUA_KIEM_DUOC
    assert "vnstock không còn cài ở đây" in ly_do, ly_do


def test_fetch_fundamentals_vang_thi_noi_mot_lan_va_thoat_ma_2(vang, monkeypatch, tmp_path, capsys):
    ff = importlib.import_module("fetch_fundamentals")
    monkeypatch.setattr(ff, "OUT", tmp_path)
    monkeypatch.setattr(ff, "SO_TAY", tmp_path / "_hang_da_tai.json")
    monkeypatch.setattr(ff, "VN100_SYMBOLS", ["AAA", "BBB", "CCC"])
    monkeypatch.setattr(ff.time, "sleep", lambda *_: None)
    with pytest.raises(ff.VangVnstock):
        ff.fetch_symbol("AAA")
    for argv in (["x"], ["x", "--schema"]):
        monkeypatch.setattr(sys, "argv", argv)
        assert ff.main() == 2
    ra = capsys.readouterr().out
    assert ra.count("CHƯA KIỂM ĐƯỢC — vnstock không còn cài ở đây") == 2, ra   # MỘT lần mỗi lượt
    assert "Traceback" not in ra
    assert not list(tmp_path.glob("*.csv")), "không được ghi gì xuống đĩa"


def test_fetch_khoi_ngoai_va_hai_script_kiem_thoat_ma_2(vang, capsys):
    import fetch_khoi_ngoai
    import kiem_duong_noi_bo
    import kiem_san_giao_dich
    assert fetch_khoi_ngoai.main(["--so-ma", "1"]) == 2
    assert kiem_duong_noi_bo.main([]) == 2
    assert kiem_san_giao_dich.main() == 2
    assert capsys.readouterr().out.count("CHUA KIEM DUOC") + 0 >= 2


# — Ba đường BƯỚC 267 đã hạ: khoá lại bằng bộ chặn thật, để không ai "sửa" quay về gọi vnstock —

def test_bang_gia_vang_thi_khong_co_nguon(vang):
    import mau_bang_gia
    r = mau_bang_gia.doc_bang_gia("SSI")
    assert r["loi"].startswith("không có nguồn:") and r["tran"] is None, r


def test_noi_phien_vang_thi_IntradayError_khong_co_nguon(vang):
    import intraday_data
    with pytest.raises(intraday_data.IntradayError, match="không có nguồn"):
        intraday_data.tai("SSI", "2026-11-17", "2026-11-17", "30m", dung_cache=False)


def test_chi_so_co_ban_vang_thi_khong_co_nguon(vang):
    import fundamental_agent as fa
    fa.xoa_cache()
    c = fa.doc_chi_so("ZZZ286")
    assert c.co_du_lieu is False and c.ly_do.startswith("không có nguồn:"), c.ly_do


def test_financial_collector_vang_ba_ham_deu_khong_co_nguon(vang):
    import financial_collector as fc
    k = fc.FinancialDataCollector()
    ket = [k.get_company_overview("ZZZ286"), k.get_financial_statements("ZZZ286"),
           k.get_foreign_trading_history("ZZZ286")]
    for r in ket:
        assert r["available"] is False and "không có nguồn" in r["note"], r["note"]


# ══ 2. HỘP "GÓI VNSTOCK" CỦA APP — chạy CHÍNH biểu thức của app.py ═══════════

def _app_cay() -> ast.Module:
    return ast.parse((GOC / "app.py").read_text(encoding="utf-8"))


def _khoi_hop_goi(cay: ast.Module):
    """(hàm `_hang`, khối `try` gán `_row_goi`) của app.py — đúng mã, không chép lại."""
    ham = next(n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == "_hang")
    kho = [n for n in ast.walk(cay) if isinstance(n, ast.Try) and any(
        isinstance(s, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "_row_goi"
                                          for t in s.targets)
        for s in ast.walk(ast.Module(n.body, [])))]
    assert len(kho) == 1, f"khối gán _row_goi: {len(kho)}"
    return ham, kho[0]


def _chay_hop_app() -> dict:
    ham, kho = _khoi_hop_goi(_app_cay())
    ns: dict = {}
    mod = ast.Module([ham, kho], [])
    ast.fix_missing_locations(mod)
    exec(compile(mod, "app.py(hop_goi)", "exec"), ns)
    return ns


def test_hop_goi_trong_app_xam_khi_vang(vang):
    ns = _chay_hop_app()
    html = ns["_row_goi"]
    assert 'class="a-st xam"' in html, html
    assert "vnstock không còn cài ở đây" in html, html
    assert "● —" in html and "● ?" not in html and 'a-st wn' not in html, html
    assert ns["_goi_canh_bao"] == "", "ô gói vắng không được kèm dòng cảnh báo cam"


def test_hop_goi_trong_app_loi_bat_ngo_van_cam_khong_do_cha(vang, monkeypatch):
    import vnstock_goi as vg
    monkeypatch.setattr(vg, "kiem_goi", lambda *a, **k: 1 / 0)
    ns = _chay_hop_app()
    assert "không kiểm được" in ns["_row_goi"] and 'a-st wn' in ns["_row_goi"]
    assert ns["_goi_canh_bao"] == ""


def test_app_dong_canh_bao_cam_di_theo_bien_canh_bao_va_css_co_lop_xam():
    cay = _app_cay()
    co = [n for n in ast.walk(cay) if isinstance(n, ast.IfExp)
          and isinstance(n.test, ast.Name) and n.test.id == "_goi_canh_bao"]
    assert co, "dòng cảnh báo cam không còn đi theo `_goi_canh_bao` (đã quay về `not _goi.dat`?)"
    css = [c.value for c in ast.walk(cay) if isinstance(c, ast.Constant) and isinstance(c.value, str)
           and ".a-st.ok" in c.value]
    assert css and re.search(r"\.a-st\.xam\s*\{\s*color:\s*#919191\s*;", css[0]), css


def test_chu_thich_agent_co_ban_khong_con_ghi_vnstock_la_nguon():
    chuoi = " ".join(c.value for c in ast.walk(_app_cay())
                     if isinstance(c, ast.Constant) and isinstance(c.value, str))
    assert "Agent Cơ Bản đọc BCTC năm gần nhất (vnstock)" not in chuoi
    assert "hiện KHÔNG có" in chuoi


# ══ 3 + 4. GÁC AST — nhập gói hãng ═════════════════════════════════════════

#: Script đo LỊCH SỬ, chạy tay, đã đo xong, không chạy lại được khi vnstock vắng (người dùng giữ
#: nguyên, BƯỚC 286). (tệp, hàm) -> số chỗ nhập chưa bọc. Danh sách PHẢI khớp (thừa cũng đỏ).
CHO_PHEP_KHONG_BOC = {
    ("tools/do10_nang_vnstock.py", "do_A"): 1,
    ("tools/do10_nang_vnstock.py", "do_B"): 1,
    ("tools/do10_nang_vnstock.py", "do_C"): 1,
    ("tools/do13_nang_urllib3.py", "_keo_mot_luot"): 1,
    ("tools/do22_buoc_gia_theo_san.py", "san_theo_nguon"): 1,
    ("tools/do26_nguong_su_kien_quyen.py", "tai_lich_that"): 1,
    ("tools/kiem_duong_noi_bo.py", "goi"): 1,      # chỉ được gọi sau khi `main` đã bọc nhập
    ("tools/kiem_san_giao_dich.py", "_tai_nguon"): 1,  # chỉ được gọi trong try của `main`
}

_BO_QUA = ("tests/", ".venv/", ".tam_test/", "backtest/cache/", ".git/", "node_modules/")


def _tep_nguon() -> list[Path]:
    ra = []
    for p in sorted(GOC.rglob("*.py")):
        r = p.relative_to(GOC).as_posix()
        if r.startswith(_BO_QUA) or "/.venv/" in r or "/site-packages/" in r:
            continue
        ra.append(p)
    assert len(ra) > 60, f"quần thể quá nhỏ ({len(ra)}): duyệt sai thư mục?"
    return ra


def _la_nhap_hang(nut) -> bool:
    if isinstance(nut, ast.Import):
        return any(a.name.split(".")[0] in GOI_HANG for a in nut.names)
    if isinstance(nut, ast.ImportFrom):
        return nut.level == 0 and (nut.module or "").split(".")[0] in GOI_HANG
    if isinstance(nut, ast.Call):       # importlib.import_module("vnstock…") / __import__("vnstock…")
        f = nut.func
        ten = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
        return (ten in ("import_module", "__import__") and nut.args
                and isinstance(nut.args[0], ast.Constant) and isinstance(nut.args[0].value, str)
                and nut.args[0].value.split(".")[0] in GOI_HANG)
    return False


def _bat_import_error(t: ast.Try) -> bool:
    for h in t.handlers:
        if h.type is None:
            return True
        ten = list(h.type.elts) if isinstance(h.type, ast.Tuple) else [h.type]
        if any(isinstance(x, ast.Name) and x.id in ("Exception", "BaseException", "ImportError",
                                                    "ModuleNotFoundError") for x in ten):
            return True
    return False


def _nhap_hang(cay: ast.Module) -> list[tuple[ast.AST, bool, str]]:
    """[(nút nhập, có `try` bắt ImportError che trong THÂN, tên hàm gần nhất hoặc '<module>')]."""
    ra = []

    def duyet(nut, tt):
        for con in ast.iter_child_nodes(nut):
            if _la_nhap_hang(con):
                che = any(isinstance(a, ast.Try) and _bat_import_error(a)
                          and (tt + [nut, con])[i + 1] in a.body
                          for i, a in enumerate(tt + [nut]) if i + 1 < len(tt + [nut, con]))
                ham = next((a.name for a in reversed(tt + [nut])
                            if isinstance(a, (ast.FunctionDef, ast.AsyncFunctionDef))), "<module>")
                ra.append((con, che, ham))
            duyet(con, tt + [nut])

    duyet(cay, [])
    return ra


def _quet() -> list[tuple[str, int, bool, str]]:
    ra = []
    for p in _tep_nguon():
        try:
            cay = ast.parse(p.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for nut, che, ham in _nhap_hang(cay):
            ra.append((p.relative_to(GOC).as_posix(), nut.lineno, che, ham))
    return ra


def test_AST_moi_nhap_goi_hang_duoc_boc_try_tru_danh_sach_cho_phep_tuong_minh():
    tat_ca = _quet()
    assert len(tat_ca) >= 20, f"chỉ thấy {len(tat_ca)} chỗ nhập gói hãng — bộ duyệt hỏng?"
    chua_boc: dict[tuple[str, str], int] = {}
    for tep, _dong, che, ham in tat_ca:
        if not che:
            chua_boc[(tep, ham)] = chua_boc.get((tep, ham), 0) + 1
    moi = {k: v for k, v in chua_boc.items() if CHO_PHEP_KHONG_BOC.get(k) != v}
    thua = {k: v for k, v in CHO_PHEP_KHONG_BOC.items() if chua_boc.get(k) != v}
    assert not moi, ("nhập gói hãng KHÔNG bọc try bắt ImportError (Cloud/Actions vắng vnstock sẽ "
                     f"sập): {moi}. Bọc `try`/nói 'không có nguồn', đừng thêm vào danh sách cho phép.")
    assert not thua, f"danh sách cho phép có mục không còn đúng (xoá/sửa mục): {thua}"


def test_AST_khong_nhap_goi_hang_o_muc_module_o_dau_ca():
    mod = [(t, d) for t, d, _che, ham in _quet() if ham == "<module>"]
    assert not mod, f"nhập gói hãng ở MỨC MODULE (CLAUDE.md cấm): {mod}"


def test_AST_bo_duyet_bat_duoc_ca_nhap_khong_boc_va_nhap_trong_try():
    """Máy đo cũng bị nghi ngờ: bộ duyệt phải THẤY cả hai loại trên mã mẫu."""
    mau = ast.parse(
        "import vnstock\n"
        "def a():\n    from vnstock import Quote\n"
        "def b():\n    try:\n        import vnstock_data\n    except ImportError:\n        pass\n"
        "def c():\n    try:\n        pass\n    except ImportError:\n        import vnai\n"
        "def d():\n    import importlib\n    importlib.import_module('vnstock.core')\n")
    got = [(ham, che) for _n, che, ham in _nhap_hang(mau)]
    assert got == [("<module>", False), ("a", False), ("b", True), ("c", False), ("d", False)], got


def test_workflow_khong_pip_install_vnstock_hay_vnai():
    xau = []
    for p in sorted((GOC / ".github" / "workflows").glob("*.yml")):
        for i, dong in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if dong.lstrip().startswith("#"):
                continue
            if re.search(r"pip\s+install[^\n]*\b(vnstock\w*|vnai)\b", dong):
                xau.append(f"{p.name}:{i}")
    assert not xau, f"workflow cài vnstock/vnai: {xau}"
