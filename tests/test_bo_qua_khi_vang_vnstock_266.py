"""BƯỚC 266 — gác ngoại lệ TẠM "CI không có vnstock" (nguồn: `tests/bo_qua_khi_vang_vnstock_266.py`).

VÌ SAO CÓ FILE NÀY
──────────────────
Từ 10/11/2026 kho hãng đóng, `pip install` không lấy được `vnstock`/`vnai`, nên
`kiem-dinh.yml` cài mọi thứ TRỪ chúng và vài test cần vnstock đang cài bỏ qua có lý do.
Người dùng 11/11/2026: *"Bỏ tạm vnstock khỏi CI (Recommended)"*. Một ngoại lệ "tạm" mà chỉ
nhớ bằng trí nhớ thì thành vĩnh viễn, và một `skip` rộng thì nuốt luôn test không liên quan.
Năm gác dưới đây bắt ba kiểu hỏng:

  1. dấu bỏ qua lan sang test không khai (hoặc khai mà không còn dấu)  -> ĐỎ
  2. điều kiện bỏ qua rộng hơn "vnstock không nạp được"                  -> ĐỎ
  3. BƯỚC 265 vào (`requirements.txt` hết ghim `vnstock==4.0.9`) mà danh sách còn -> ĐỎ
  4. một `pytest.skip` lén về vnstock/vnai ngoài danh sách              -> ĐỎ
  5. `kiem-dinh.yml` không còn lọc đúng ba loại dòng (hoặc lọc thừa)    -> ĐỎ

Mọi phép kiểm hình dạng đọc AST, không đọc `in` trên văn bản (CLAUDE.md, "Gác phải đọc AST").
Các gác này chạy được Ở CẢ HAI môi trường (có và không có vnstock): chúng không import vnstock.
"""
import ast
import importlib.util
import re
from pathlib import Path

import bo_qua_khi_vang_vnstock_266 as bq

GOC = Path(__file__).resolve().parent.parent
TESTS = GOC / "tests"
TEN_DAU = "can_vnstock_dang_cai"
TEN_FILE_HELPER = "bo_qua_khi_vang_vnstock_266.py"
TEN_FILE_GAC = Path(__file__).name
MODULE_HELPER = TEN_FILE_HELPER[:-3]


def _cay(p: Path) -> ast.Module:
    return ast.parse(p.read_text(encoding="utf-8"))


def _file_test() -> list[Path]:
    """Mọi `tests/test_*.py`, trừ chính file gác này (nó nhắc tên dấu trong chuỗi)."""
    ra = [p for p in sorted(TESTS.glob("test_*.py")) if p.name != TEN_FILE_GAC]
    assert len(ra) > 100, f"quần thể file test quá nhỏ ({len(ra)}) — duyệt sai thư mục?"
    return ra


def _la_dau(nut: ast.expr) -> bool:
    return isinstance(nut, ast.Name) and nut.id == TEN_DAU


def _ham_mang_dau() -> tuple[set[str], list[str]]:
    """({`tests/<file>::<hàm>` của hàm MỨC MODULE mang dấu}, [chỗ dùng dấu KHÔNG phải decorator mức module])."""
    co: set[str] = set()
    la: list[str] = []
    for p in _file_test():
        cay = _cay(p)
        hop_le: set[int] = set()
        for nut in cay.body:
            if isinstance(nut, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for d in nut.decorator_list:
                    if _la_dau(d):
                        co.add(f"tests/{p.name}::{nut.name}")
                        hop_le.add(id(d))
        for nut in ast.walk(cay):
            if _la_dau(nut) and id(nut) not in hop_le:
                la.append(f"tests/{p.name}:{nut.lineno}")
    return co, la


# ── 1. Danh sách khớp đúng tập test mang dấu ─────────────────────────

def test_DANH_SACH_khop_DUNG_tap_test_mang_dau_va_khong_co_cho_dung_la():
    co, la = _ham_mang_dau()
    assert not la, (
        f"dấu `{TEN_DAU}` dùng ở chỗ KHÔNG phải decorator của hàm test mức module "
        f"(pytestmark / gán lại / lớp): {la}")
    khai = set(bq.DANH_SACH_BO_QUA)
    thua = sorted(co - khai)
    thieu = sorted(khai - co)
    assert not thua, f"test mang dấu bỏ qua mà CHƯA khai ở DANH_SACH_BO_QUA: {thua}"
    assert not thieu, f"DANH_SACH_BO_QUA khai test không còn mang dấu (hoặc không tồn tại): {thieu}"


def test_QUAN_THE_gac_danh_sach_khong_rong_khi_ngoai_le_con_song():
    """Danh sách rỗng mà ghim còn thì vòng kiểm trên xanh vì chẳng canh gì."""
    if not bq.DANH_SACH_BO_QUA:
        return                      # đã gỡ: gác 3 chịu trách nhiệm phần còn lại
    co, _ = _ham_mang_dau()
    assert co, "danh sách khai có test nhưng quét AST không thấy hàm nào mang dấu — bộ quét hỏng?"


# ── 2. Điều kiện bỏ qua CHỈ là "vnstock không nạp được" ──────────────

#: Hình dạng DUY NHẤT được phép. Viết thành mã rồi `ast.dump` — không so chuỗi.
_DIEU_KIEN_DUNG = ast.dump(
    ast.parse("importlib.util.find_spec('vnstock') is None", mode="eval").body)
_CAC_TEN_BO_QUA = {"skip", "skipif", "xfail", "importorskip"}


def _ten_cuoi(f: ast.expr) -> str:
    return f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")


def test_DIEU_KIEN_bo_qua_CHI_la_find_spec_vnstock_is_None_AST():
    cay = _cay(TESTS / TEN_FILE_HELPER)
    goi = [n for n in ast.walk(cay)
           if isinstance(n, ast.Call) and _ten_cuoi(n.func) in _CAC_TEN_BO_QUA]
    assert len(goi) == 1, (
        f"{TEN_FILE_HELPER} phải có ĐÚNG MỘT lời gọi skip/skipif/xfail/importorskip, thấy "
        f"{[ast.unparse(g) for g in goi]}")
    g = goi[0]
    assert ast.unparse(g.func) == "pytest.mark.skipif", ast.unparse(g.func)
    assert len(g.args) == 1, "điều kiện phải là đối số vị trí DUY NHẤT"
    assert ast.dump(g.args[0]) == _DIEU_KIEN_DUNG, (
        "điều kiện bỏ qua phải đúng hình `importlib.util.find_spec('vnstock') is None`; "
        f"thấy `{ast.unparse(g.args[0])}`")
    assert [k.arg for k in g.keywords] == ["reason"], [k.arg for k in g.keywords]
    assert isinstance(g.keywords[0].value, ast.Name) and g.keywords[0].value.id == "LY_DO"


def test_DAU_o_LUC_CHAY_dung_la_skipif_khi_vnstock_vang_va_mang_LY_DO():
    """Đo lúc chạy (bổ sung cho AST): `args` là giá trị đã ĐÁNH GIÁ, nên cặp này đỏ nếu
    điều kiện bị đổi thành hằng (True/False) dù AST bị lách."""
    m = bq.can_vnstock_dang_cai.mark
    assert m.name == "skipif"
    assert m.args == ((importlib.util.find_spec("vnstock") is None),)
    assert m.kwargs == {"reason": bq.LY_DO}


def test_LY_DO_nhac_BUOC_266_va_han_go_BUOC_265():
    assert "BƯỚC 266" in bq.LY_DO, bq.LY_DO
    assert "gỡ khi BƯỚC 265 vào" in bq.LY_DO, bq.LY_DO


# ── 3. Hết hạn: BƯỚC 265 vào thì ngoại lệ phải đi cùng ───────────────

def _dong_requirements() -> list[str]:
    ra = []
    for d in (GOC / "requirements.txt").read_text(encoding="utf-8").splitlines():
        d = d.split("#")[0].strip()
        if d:
            ra.append(d)
    return ra


def test_NGOAI_LE_tu_het_han_khi_requirements_het_ghim_vnstock_cu():
    """Đỏ khi `requirements.txt` không còn dòng `vnstock==4.0.9` (BƯỚC 265 đã vào) mà
    `DANH_SACH_BO_QUA` còn phần tử. Cách gỡ: xoá danh sách, các dấu `can_vnstock_dang_cai`,
    khối lọc ở `kiem-dinh.yml`, và hai file `bo_qua_khi_vang_vnstock_266.py` + file này —
    CÙNG LÚC với đổi ghim."""
    dong = _dong_requirements()
    con_ghim_cu = bq.GHIM_NGOAI_LE in dong
    assert not (bq.DANH_SACH_BO_QUA and not con_ghim_cu), (
        f"requirements.txt không còn ghim `{bq.GHIM_NGOAI_LE}` (BƯỚC 265 đã vào?) nhưng "
        f"ngoại lệ BƯỚC 266 còn {len(bq.DANH_SACH_BO_QUA)} test bị bỏ qua — gỡ ngoại lệ: "
        f"{sorted(bq.DANH_SACH_BO_QUA)}")


def test_GHIM_NGOAI_LE_la_mot_dong_vnstock_dung_dang():
    """Nếu hằng ghim bị gõ sai thì gác hết hạn ở trên luôn đỏ/xanh nhầm."""
    assert re.fullmatch(r"vnstock==[0-9][0-9.]*", bq.GHIM_NGOAI_LE), bq.GHIM_NGOAI_LE


# ── 4. Không `pytest.skip` lén về vnstock/vnai ngoài danh sách ───────

def _skip_lang_ve_vnstock() -> list[str]:
    """Lời gọi `pytest.skip` / `pytest.importorskip` có chuỗi nhắc vnstock/vnai nằm NGOÀI
    hàm đã khai ở danh sách."""
    khai = {c.split("::")[1] for c in bq.DANH_SACH_BO_QUA}
    xau: list[str] = []
    for p in _file_test():
        for nut in _cay(p).body:
            ten_ham = nut.name if isinstance(nut, (ast.FunctionDef, ast.AsyncFunctionDef)) else None
            for n in ast.walk(nut):
                if not (isinstance(n, ast.Call) and _ten_cuoi(n.func) in {"skip", "importorskip"}):
                    continue
                chu = " ".join(str(c.value) for c in ast.walk(n)
                               if isinstance(c, ast.Constant) and isinstance(c.value, str))
                if re.search(r"vnstock|vnai", chu, re.I) and ten_ham not in khai:
                    xau.append(f"tests/{p.name}:{n.lineno}")
    return xau


def test_KHONG_co_pytest_skip_ve_vnstock_vnai_ngoai_danh_sach():
    xau = _skip_lang_ve_vnstock()
    assert not xau, (
        "skip ngầm về vnstock/vnai ngoài `DANH_SACH_BO_QUA` — ngoại lệ phải TƯỜNG MINH và có hạn "
        f"(dùng `{TEN_DAU}`): {xau}")


# ── 5. kiem-dinh.yml lọc ĐÚNG ba loại dòng, không hơn ────────────────

_YML = GOC / ".github" / "workflows" / "kiem-dinh.yml"
_LOC = re.compile(r"""grep\s+-vE\s+'([^']+)'\s+requirements\.txt\s*>\s*(\S+)""")


def _dong_hieu_luc_yml() -> list[str]:
    return [d.strip() for d in _YML.read_text(encoding="utf-8").splitlines()
            if d.strip() and not d.strip().startswith("#")]


def _bo_loc() -> tuple[str, str]:
    kq = [_LOC.search(d) for d in _dong_hieu_luc_yml()]
    kq = [k for k in kq if k]
    assert len(kq) == 1, f"kiem-dinh.yml phải có ĐÚNG MỘT dòng lọc requirements.txt, thấy {len(kq)}"
    return kq[0].group(1), kq[0].group(2)


def test_kiem_dinh_yml_cai_BAN_LOC_chu_khong_cai_thang_requirements_txt():
    mau, dich = _bo_loc()
    cai = [d for d in _dong_hieu_luc_yml() if d.startswith("pip install")]
    assert "pip install -r " + dich in cai, f"không có lệnh cài từ bản lọc `{dich}`: {cai}"
    assert not [d for d in cai if re.search(r"-r\s+requirements\.txt\b", d)], (
        f"kiem-dinh.yml còn cài thẳng requirements.txt (gồm vnstock): {cai}")


def test_BO_LOC_giu_het_dong_khac_va_bo_DUNG_dong_vnstock_vnai_kho_hang():
    """Chạy chính mẫu ra khỏi workflow lên `requirements.txt` THẬT: phần bị bỏ phải đúng là các
    dòng bắt đầu bằng `vnstock` / `vnai` / `--extra-index-url`; phần còn lại giữ nguyên."""
    mau, _ = _bo_loc()
    re_loc = re.compile(mau)
    dong = [d for d in (GOC / "requirements.txt").read_text(encoding="utf-8").splitlines()]
    bi_bo = [d for d in dong if re_loc.search(d)]
    giu = [d for d in dong if not re_loc.search(d)]
    # 1. không dòng thật nào dính vnstock*/vnai* còn sót (kể cả vnstock_ezchart: nó đòi vnstock)
    sot = [d for d in giu if re.match(r"\s*(vnstock|vnai|--extra-index-url)", d)]
    assert not sot, f"bộ lọc để sót dòng vnstock/vnai/kho hãng: {sot}"
    # 2. không bỏ thừa: mọi dòng bị bỏ phải thuộc ba loại trên
    thua = [d for d in bi_bo if not re.match(r"(vnstock|vnai|--extra-index-url)", d)]
    assert not thua, f"bộ lọc bỏ THỪA dòng: {thua}"
    # 3. các thư viện khác vẫn còn
    con_lai = {re.split(r"[<>=!~\[ ;@]", d)[0].strip().lower() for d in giu if d.strip()
               and not d.lstrip().startswith("#")}
    for goi in ("streamlit", "pandas", "numpy", "plotly", "requests", "gspread", "toml"):
        assert goi in con_lai, f"bộ lọc làm mất `{goi}`: {sorted(con_lai)}"
    # 4. mẫu thật sự bắt được cả ba loại trong `requirements.txt` hiện hành (không rỗng)
    loai = {m.group(1) for d in bi_bo if (m := re.match(r"(vnstock|vnai|--extra-index-url)", d))}
    if bq.GHIM_NGOAI_LE in [d.split("#")[0].strip() for d in dong]:
        assert loai == {"vnstock", "vnai", "--extra-index-url"}, loai
