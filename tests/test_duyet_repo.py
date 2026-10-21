"""Máy quét toàn repo phải BỎ QUA worktree LỒNG bên trong repo.

VÌ SAO CÓ FILE NÀY
──────────────────
Ứng dụng Claude desktop tạo worktree cho mỗi phiên ở
`<repo>/.claude/worktrees/<tên>/` — NẰM TRONG thư mục repo. Ngày 30/09/2026,
khi `.claude/worktrees/angry-keller-8c2bd9` tồn tại, năm cổng chạy từ bản
checkout chính cho ĐỎ GIẢ ở bốn cổng — cả bốn vì `Path.rglob` đi xuống bản
sao lồng. git không thấy thư mục ấy (ứng dụng ghi `.claude/worktrees/` vào
`.git/info/exclude`), nhưng `rglob` không hỏi git. `docs/STATE.md` BƯỚC 147.

Ba lớp gác:
  1. HÀM PHÁN `duyet_repo.la_worktree_long` và bộ duyệt `duyet_repo.duyet`
     — dựng cây giả VÀ một worktree git THẬT (ca đã biết trước).
  2. Hai CỔNG đã đỏ giả (cổng 2, cổng 3) — chạy đúng hàm của chúng trên cây
     có worktree lồng.
  3. SỔ ĐĂNG KÝ: mọi lượt duyệt đệ quy trong `tools/`, `tests/` và gốc repo
     phải đi qua `duyet_repo.duyet`, hoặc khai miễn trừ kèm lý do. Một máy
     quét mới viết `goc.rglob(...)` là ĐỎ — lớp lỗi này quét cả lớp, không
     sửa từng chỗ (ràng buộc 5, `docs/HANDOFF.md`).
"""
from __future__ import annotations

import ast
import fnmatch
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(GOC / "tools"))

import duyet_repo  # noqa: E402


def _tao(goc: Path, *tuong_doi: str) -> None:
    for t in tuong_doi:
        p = goc / t
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x = 1\n", encoding="utf-8")


def _ten(goc: Path, ds) -> list[str]:
    return sorted(p.relative_to(goc).as_posix() for p in ds)


# ── 1. Hàm phán ──────────────────────────────────────────────────────
def test_WORKTREE_CUA_APP_bi_bo_qua_KE_CA_KHI_da_mat_git(tmp_path):
    """Luật 1 không cần `.git`: gỡ worktree trên Windows hay để lại thư mục
    khi có file đang bị khoá, và bản sao mồ côi ấy vẫn làm cổng đỏ giả."""
    _tao(tmp_path, "a.py", "tools/b.py", ".claude/worktrees/w/tools/c.py",
         ".claude/worktrees/w/d.py")
    assert _ten(tmp_path, duyet_repo.duyet(tmp_path, "*.py")) == [
        "a.py", "tools/b.py"]


def test_THU_MUC_CON_mang_git_TEP_la_worktree_khac(tmp_path):
    """Luật 2, dạng worktree: `.git` là một TỆP `gitdir: …`."""
    _tao(tmp_path, "a.py", "ngoai/wt/e.py", "ngoai/f.py")
    (tmp_path / "ngoai" / "wt" / ".git").write_text(
        "gitdir: C:/x/.git/worktrees/wt\n", encoding="utf-8")
    assert _ten(tmp_path, duyet_repo.duyet(tmp_path, "*.py")) == [
        "a.py", "ngoai/f.py"]


def test_THU_MUC_CON_mang_git_THU_MUC_la_ban_clone_long(tmp_path):
    """Luật 2, dạng clone lồng: `.git` là một THƯ MỤC."""
    _tao(tmp_path, "a.py", "clone/g.py")
    (tmp_path / "clone" / ".git").mkdir()
    assert _ten(tmp_path, duyet_repo.duyet(tmp_path, "*.py")) == ["a.py"]


def test_GOC_mang_git_thi_KHONG_bi_bo_qua(tmp_path):
    """Gốc repo nào cũng có `.git`. Xét cả gốc thì mọi file bị loại và máy
    quét báo sạch trên 0 file — đúng hình dạng lỗi 'lọc theo đường tuyệt
    đối' đã cắn `kiem_cu_phap_311` và `test_chi_dan_chay_duoc`."""
    _tao(tmp_path, "a.py", "tools/b.py")
    (tmp_path / ".git").mkdir()
    assert _ten(tmp_path, duyet_repo.duyet(tmp_path, "*.py")) == [
        "a.py", "tools/b.py"]


def test_PHAN_CON_LAI_cua_claude_VAN_duoc_quet(tmp_path):
    """Chỉ `.claude/worktrees/`, không phải cả `.claude/`: `SKILL.md` và
    `references/` nằm dưới `.claude/skills/`, và `test_chi_dan_chay_duoc`
    quét `*.md` ở đó."""
    _tao(tmp_path, ".claude/skills/q/SKILL.md", ".claude/worktrees/w/SKILL.md")
    assert _ten(tmp_path, duyet_repo.duyet(tmp_path, "*.md")) == [
        ".claude/skills/q/SKILL.md"]


def test_ten_GAN_GIONG_worktrees_KHONG_bi_bo_qua(tmp_path):
    """So theo PHẦN đường dẫn, không theo tiền tố chuỗi."""
    _tao(tmp_path, ".claude/worktrees_cu/h.py", "docs/.claude/worktrees/i.py")
    assert _ten(tmp_path, duyet_repo.duyet(tmp_path, "*.py")) == [
        ".claude/worktrees_cu/h.py", "docs/.claude/worktrees/i.py"]


def _git(cwd: Path, *lenh: str) -> None:
    r = subprocess.run(["git", "-C", str(cwd), *lenh], capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0, f"git {' '.join(lenh)}: {r.stderr.strip()}"


def test_WORKTREE_GIT_THAT_do_git_worktree_add_tao_ra(tmp_path):
    """Ca THẬT đã biết trước, không phải đồ giả: đúng lệnh ứng dụng dùng.

    Hai vị trí: dưới `.claude/worktrees/` (luật 1) và một thư mục thường
    (chỉ luật 2 bắt được — cột `.git` là tệp `gitdir:` do git viết).
    """
    _git(tmp_path, "init", "-q")
    _tao(tmp_path, "a.py", "tools/b.py")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "-c", "user.name=t", "-c", "user.email=t@t",
         "commit", "-q", "-m", "goc")
    _git(tmp_path, "worktree", "add", "-q", "--detach",
         str(tmp_path / ".claude" / "worktrees" / "_thu"))
    _git(tmp_path, "worktree", "add", "-q", "--detach",
         str(tmp_path / "wt_thuong"))
    assert (tmp_path / "wt_thuong" / ".git").is_file()
    tat_ca = _ten(tmp_path, tmp_path.rglob("*.py"))
    assert len(tat_ca) == 6, f"cay thu sai hinh dang: {tat_ca}"
    assert _ten(tmp_path, duyet_repo.duyet(tmp_path, "*.py")) == [
        "a.py", "tools/b.py"]


# ── 2. Hai cổng đã đỏ giả ngày 30/09/2026 ─────────────────────────────
def _nap(ten: str):
    spec = importlib.util.spec_from_file_location(
        f"_{ten}_thu", GOC / "tools" / f"{ten}.py")
    mo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mo)
    return mo


def test_CONG_2_cac_file_bo_qua_worktree_long(tmp_path):
    k = _nap("kiem_cu_phap_311")
    _tao(tmp_path, "a.py", "tools/b.py", ".claude/worktrees/w/c.py")
    assert _ten(tmp_path, k.cac_file(tmp_path)) == ["a.py", "tools/b.py"]


def test_CONG_3_quet_repo_bo_qua_worktree_long(tmp_path, monkeypatch):
    """Dựng lại NGUYÊN VĂN lỗi thật: `getattr(..., "lineno", 0)` là một trong
    năm dòng CHẶN đọc được ở bản sao lồng ngày 30/09.

    Đối chứng dương đi CÙNG cây: cùng dòng ấy ở một file thường phải bị bắt,
    nếu không một `quet_repo` trả 0 vì không quét gì cũng qua được."""
    h = _nap("chan_bia_so_lieu")
    monkeypatch.setattr(h, "GOC_DU_AN", tmp_path)
    xau = 'n = getattr(nut, "lineno", 0)\n'
    p = tmp_path / ".claude" / "worktrees" / "w" / "x.py"
    p.parent.mkdir(parents=True)
    p.write_text(xau, encoding="utf-8")
    assert h.quet_repo() == 0, "quet_repo doc vao worktree long"
    (tmp_path / "y.py").write_text(xau, encoding="utf-8")
    assert h.quet_repo() == 1, "doi chung duong: quet_repo khong bat mau CHAN"


# ── 3. Sổ đăng ký: không lượt duyệt đệ quy nào đi vòng ────────────────
#: (file, hàm) -> lý do. Lượt duyệt đệ quy ở đây KHÔNG phải quét toàn repo.
MIEN_TRU = {
    ("tools/duyet_repo.py", "duyet"):
        "chinh bo duyet; noi DUY NHAT duoc goi rglob tren goc repo",
    ("tests/test_doi_chung_ngoai_venv.py", "_py_sau_trong_tools"):
        "duyet `tools/` chu khong duyet goc; worktree cua app nam o .claude/",
    ("tests/test_duyet_repo.py", "test_WORKTREE_GIT_THAT_do_git_worktree_add_tao_ra"):
        "dem cay thu CO worktree long de chung minh cay dung hinh dang",
}


def _file_quan_the() -> list[Path]:
    return (duyet_repo.liet_ke(GOC, ".", "*.py") + duyet_repo.liet_ke(GOC, "tools", "*.py")
            + duyet_repo.liet_ke(GOC, "tests", "*.py"))


def _duyet_de_quy(cay: ast.AST) -> list[tuple[str, int]]:
    """[(hàm bao quanh, dòng)] của mọi lời gọi duyệt ĐỆ QUY trong một file.

    Ba hình dạng: `.rglob(...)`, `os.walk(...)`, và `glob(..., recursive=True)`
    hay `.glob("**…")` — dạng sau là `rglob` viết cách khác.
    """
    ra = []

    def tham(nut, ham):
        for con in ast.iter_child_nodes(nut):
            ten = ham
            if isinstance(con, (ast.FunctionDef, ast.AsyncFunctionDef)):
                ten = con.name
            if isinstance(con, ast.Call):
                f = con.func
                la = False
                if isinstance(f, ast.Attribute) and f.attr == "rglob":
                    la = True
                elif (isinstance(f, ast.Attribute) and f.attr == "walk"
                      and isinstance(f.value, ast.Name) and f.value.id == "os"):
                    la = True
                elif isinstance(f, ast.Attribute) and f.attr in ("glob", "iglob"):
                    if any(k.arg == "recursive" for k in con.keywords):
                        la = True
                    if (con.args and isinstance(con.args[0], ast.Constant)
                            and isinstance(con.args[0].value, str)
                            and "**" in con.args[0].value):
                        la = True
                if la:
                    ra.append((ham, con.lineno))
            tham(con, ten)

    tham(cay, "<module>")
    return ra


def test_SO_DANG_KY_moi_luot_duyet_de_quy_deu_qua_duyet_repo():
    """Thêm một máy quét toàn repo mà viết `goc.rglob(...)` thì đỏ ở đây.

    Sửa: dùng `duyet_repo.duyet(goc, mau)`. Nếu lượt duyệt ấy thật sự không
    phải quét toàn repo, khai vào `MIEN_TRU` kèm lý do.
    """
    vi_pham, thay = [], set()
    for f in _file_quan_the():
        rel = f.relative_to(GOC).as_posix()
        cay = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
        for ham, dong in _duyet_de_quy(cay):
            thay.add((rel, ham))
            if (rel, ham) not in MIEN_TRU:
                vi_pham.append(f"{rel}:{dong} (ham {ham})")
    assert not vi_pham, (
        "luot duyet DE QUY khong qua duyet_repo.duyet — se doc vao worktree "
        "long .claude/worktrees/:\n  " + "\n  ".join(vi_pham))
    chet = set(MIEN_TRU) - thay
    assert not chet, f"mien tru khong con ai dung, go di: {sorted(chet)}"


def test_SO_DANG_KY_KHONG_MU_bat_duoc_moi_hinh_dang_da_khai():
    """Máy đo cũng bị nghi như gác (SKILL.md Bước 3, điều 4): bắt nó đi qua
    đúng mọi hình dạng nó khai, và KHÔNG bắt `glob` một tầng."""
    src = (
        "import os, glob\n"
        "def a(g):\n    return list(g.rglob('*.py'))\n"
        "def b(g):\n    return list(os.walk(g))\n"
        "def c(g):\n    return glob.glob(g + '/**/*.py', recursive=True)\n"
        "def d(g):\n    return list(g.glob('**/*.md'))\n"
        "def e(g):\n    return list(g.glob('*.py'))\n"
    )
    assert [h for h, _ in _duyet_de_quy(ast.parse(src))] == ["a", "b", "c", "d"]


def test_SO_DANG_KY_KHONG_MU_thay_du_cac_may_quet_that():
    """Đối chứng dương trên CÂY THẬT: đếm lời gọi `duyet(...)`. Chín máy quét
    đã chuyển sang nó ngày 30/09; sổ đăng ký thấy ít hơn thì nó đang mù (một
    quần thể rỗng cũng cho 'không vi phạm')."""
    goi = []
    for f in _file_quan_the():
        cay = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
        for n in ast.walk(cay):
            if not isinstance(n, ast.Call):
                continue
            fn = n.func
            if ((isinstance(fn, ast.Attribute) and fn.attr == "duyet"
                 and isinstance(fn.value, ast.Name) and fn.value.id == "duyet_repo")
                    or (isinstance(fn, ast.Name) and fn.id == "duyet")):
                goi.append(f.relative_to(GOC).as_posix())
    may_quet = {f for f in goi if f != "tests/test_duyet_repo.py"}
    assert len(may_quet) >= 9, f"chi thay {sorted(may_quet)}"


# ── BƯỚC 201: luật 3 — `.tam_test/` ở gốc ───────────────────────────────

def test_TAM_TEST_o_GOC_bi_bo_qua_nhung_ten_giong_o_noi_khac_thi_khong(tmp_path):
    from duyet_repo import THU_MUC_TAM_TEST
    (tmp_path / THU_MUC_TAM_TEST / "tmpab12").mkdir(parents=True)
    (tmp_path / THU_MUC_TAM_TEST / "tmpab12" / "thu.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "tools" / THU_MUC_TAM_TEST).mkdir(parents=True)
    (tmp_path / "tools" / THU_MUC_TAM_TEST / "giu.py").write_text("x = 2\n", encoding="utf-8")
    (tmp_path / ".tam_test_khac").mkdir()
    (tmp_path / ".tam_test_khac" / "giu2.py").write_text("x = 3\n", encoding="utf-8")
    (tmp_path / "a.py").write_text("x = 4\n", encoding="utf-8")
    thay = sorted(p.relative_to(tmp_path).as_posix() for p in duyet_repo.duyet(tmp_path, "*.py"))
    assert thay == [".tam_test_khac/giu2.py", "a.py", "tools/.tam_test/giu.py"]


def test_KHONG_TEST_NAO_tao_thu_muc_tam_o_GOC_repo():
    """Nguồn đỏ giả khi chạy song song (BƯỚC 201): `TemporaryDirectory(dir=str(GOC))`.
    File tạm TRONG repo phải đi qua `.tam_test/` (tools/duyet_repo.py, luật 3)."""
    import ast
    vi_pham = []
    for f in sorted((GOC / "tests").glob("test_*.py")):
        cay = ast.parse(f.read_text(encoding="utf-8"))
        for n in ast.walk(cay):
            if isinstance(n, ast.Call):
                for kw in n.keywords:
                    if kw.arg == "dir" and ast.unparse(kw.value) in ("GOC", "str(GOC)", "ROOT", "str(ROOT)"):
                        vi_pham.append(f"{f.name}:{n.lineno} {ast.unparse(n)[:80]}")
    assert not vi_pham, vi_pham


# ── BƯỚC 211: luật 4 — tệp tạm `tests/__tam_*` của một test KHÁC ──────────

def _cuoc_dua(monkeypatch, ten_ham: str = "rglob") -> list:
    """Giả lập TẤT ĐỊNH cuộc đua 20/10/2026 (PR #255, cổng 4, 12 file song song):
    lượt liệt kê thấy `tests/__tam_*` của một test KHÁC, rồi test ấy xoá tệp TRƯỚC
    khi máy quét đọc tới. Bọc `Path.<ten_ham>`: liệt kê thật xong thì xoá mọi
    `tests/__tam_*` trong danh sách. Trả tên các tệp đã xoá — đối chứng rằng phép
    giả lập có chạy (một giả lập không xoá gì thì mọi máy quét đều "chịu được")."""
    goc_ham = getattr(Path, ten_ham)
    da_xoa: list = []

    def ham_mat(self, *a, **k):
        ds = list(goc_ham(self, *a, **k))
        for p in ds:
            if p.parent.name == "tests" and p.name.startswith("__tam_") and p.is_file():
                p.unlink()
                da_xoa.append(p.name)
        return iter(ds)

    monkeypatch.setattr(Path, ten_ham, ham_mat)
    return da_xoa


def test_CUOC_DUA_20_10_tep_tam_bien_mat_giua_LIET_KE_va_DOC(tmp_path, monkeypatch):
    """Dựng lại NGUYÊN VĂN lỗi thật: `test_KHONG_FILE_NAO_trong_repo_co_CAU_LENH_CHET`
    đỏ `FileNotFoundError: … tests/__tam_kiem_tra_mien_tru.py` — `duyet` trả tệp tạm mà
    `tests/test_chan_bia_so_lieu.py` (tiến trình khác) vừa xoá. Mọi máy quét đọc tệp
    sau `duyet` cùng hình dạng, nên sửa ở bộ duyệt, một chỗ."""
    _tao(tmp_path, "a.py", "tests/test_b.py", "tests/__tam_kiem_tra_mien_tru.py")
    da_xoa = _cuoc_dua(monkeypatch)
    doc = {p.relative_to(tmp_path).as_posix(): p.read_text(encoding="utf-8")
           for p in duyet_repo.duyet(tmp_path, "*.py")}
    assert da_xoa == ["__tam_kiem_tra_mien_tru.py"], "phep gia lap cuoc dua khong chay"
    assert sorted(doc) == ["a.py", "tests/test_b.py"]


def test_LUAT_4_chi_bo_tep_tam_NGAY_DUOI_tests_cua_GOC(tmp_path):
    """Bỏ đúng phần đường THỨ HAI mang tiền tố `__tam_` dưới `tests/` của gốc (tệp hay
    thư mục). `__tam_` ở nơi khác, `tests/` lồng, tên gần giống thì VẪN quét: phép bỏ
    qua rộng hơn quy ước là nới thứ máy quét kiểm."""
    _tao(tmp_path, "tests/__tam_x.py", "tests/__tam_d/y.py", "tests/test_a.py",
         "tests/con/__tam_z.py", "tools/tests/__tam_w.py", "docs/__tam_v.py",
         "__tam_goc.py", "tests_cu/__tam_u.py", "tests/tam_t.py")
    assert _ten(tmp_path, duyet_repo.duyet(tmp_path, "*.py")) == [
        "__tam_goc.py", "docs/__tam_v.py", "tests/con/__tam_z.py", "tests/tam_t.py",
        "tests/test_a.py", "tests_cu/__tam_u.py", "tools/tests/__tam_w.py"]


def test_LIET_KE_MOT_TANG_cung_bo_tep_tam_ke_ca_khi_no_bien_mat(tmp_path, monkeypatch):
    """`(GOC / "tests").glob("*.py")` rồi đọc là cùng cuộc đua, một tầng: sáu máy quét
    trong `tests/` làm đúng thế (BƯỚC 211). `liet_ke` là bản một tầng của `duyet`."""
    _tao(tmp_path, "tests/test_a.py", "tests/_ho_tro.py", "tests/__tam_kiem_tra_r6.py",
         "a.py", "__tam_goc.py")
    da_xoa = _cuoc_dua(monkeypatch, "glob")
    doc = {p.name: p.read_text(encoding="utf-8")
           for p in duyet_repo.liet_ke(tmp_path, "tests", "*.py")}
    assert da_xoa == ["__tam_kiem_tra_r6.py"], "phep gia lap cuoc dua khong chay"
    assert sorted(doc) == ["_ho_tro.py", "test_a.py"]
    assert _ten(tmp_path, duyet_repo.liet_ke(tmp_path, ".", "*.py")) == [
        "__tam_goc.py", "a.py"]


def test_TEP_TAM_TRONG_TESTS_ten_DUY_NHAT_moi_luot_va_may_quet_khong_thay(tmp_path):
    """Đo 21/10/2026: hai tiến trình chạy lặp hai test của `tests/test_chan_bia_so_lieu.py`
    (mỗi test MỘT tên tệp cố định) → 6/1600 lượt đỏ `PermissionError`/`FileNotFoundError`
    — tiến trình này xoá tệp tiến trình kia đang đọc. Cổng 1 và cổng 4 chạy file ấy cùng
    lúc. Tên duy nhất mỗi lượt thì không ai xoá tệp của ai."""
    (tmp_path / "tests").mkdir()
    with duyet_repo.tep_tam_trong_tests(tmp_path, "kiem_tra") as a, \
            duyet_repo.tep_tam_trong_tests(tmp_path, "kiem_tra") as b:
        assert a != b
        for p in (a, b):
            assert p.parent == tmp_path / "tests" and p.is_file()
            assert p.name.startswith("__tam_kiem_tra_") and p.suffix == ".py"
            assert duyet_repo.la_tep_tam_cua_test(tmp_path, p)
        assert list(duyet_repo.duyet(tmp_path, "*.py")) == []
        assert list(duyet_repo.liet_ke(tmp_path, "tests", "*.py")) == []
    assert not a.exists() and not b.exists()
    with pytest.raises(RuntimeError):
        with duyet_repo.tep_tam_trong_tests(tmp_path, "loi") as c:
            raise RuntimeError("giua chung")
    assert not c.exists(), "tep tam con lai sau mot test no"


# ── Sổ đăng ký MỘT TẦNG: lượt liệt kê một tầng nào có thể thấy `tests/__tam_*` ──
#: Một tên tệp tạm luật 4. Mẫu glob không khớp nó (`test_*.py`, `*.csv`…) thì lượt liệt
#: kê ấy không thể trả tệp tạm và không phải khai.
_TEN_TEP_TAM_MAU = "__tam_x.py"
#: Hằng mức module trỏ GỐC repo trong dự án. Liệt kê một tầng ở gốc, ở `<gốc> / "<khác
#: tests>"`, hay dưới `tmp_path` thì không thấy `tests/`.
_NHAN_GOC = {"GOC", "ROOT", "GOC_DU_AN"}

#: (file, hàm) -> lý do. Lượt liệt kê ở đây KHÔNG liệt kê `tests/` của repo.
MIEN_TRU_MOT_TANG = {
    ("tools/duyet_repo.py", "liet_ke"):
        "chinh bo liet ke mot tang; noi loc tep tam luat 4",
    ("tools/chan_bia_so_lieu.py", "thu_thap_truong"):
        "goi voi goc worktree (luoc do dataclass); mot tang o goc, khong co tests/",
    ("tests/test_chup_cache.py", "_anh"):
        "kho la thu muc tam cua test (tmp_path qua fixture)",
    ("tests/test_chup_cache.py", "test_ban_chep_lech_bam_thi_no_va_KHONG_ghi"):
        "kho la thu muc tam cua test (tmp_path qua fixture)",
    ("tests/test_no_fabricated_data.py", "test_khong_co_key_trong_ma_nguon"):
        "bo moi duong co /tests/ TRUOC khi mo; `*` cua glob khong khop .tam_test",
    ("tests/test_tai_lieu_khop_ten_ma.py", "_cac_module"):
        "THU_MUC = goc, tools/, backtest/ — khong co tests/",
}


def _mau_cua(nut) -> str | None:
    """Mẫu glob đọc được tĩnh; phần biến của f-string thành `*`. Không đọc được: None."""
    if isinstance(nut, ast.Constant) and isinstance(nut.value, str):
        return nut.value
    if isinstance(nut, ast.JoinedStr):
        return "".join(v.value if isinstance(v, ast.Constant) else "*" for v in nut.values)
    return None


def _nhan_khong_phai_tests(nut) -> bool:
    """Bên nhận CHẮC CHẮN không phải `tests/`: `GOC`, `Path(GOC)`, `GOC / "<khác tests>"`,
    hay bắt đầu bằng `tmp_path`. Không chứng minh được thì coi là có thể."""
    if ast.unparse(nut).startswith("tmp_path"):
        return True
    if isinstance(nut, ast.Name) and nut.id in _NHAN_GOC:
        return True
    if (isinstance(nut, ast.Call) and len(nut.args) == 1 and isinstance(nut.args[0], ast.Name)
            and nut.args[0].id in _NHAN_GOC and ast.unparse(nut.func).endswith("Path")):
        return True
    return (isinstance(nut, ast.BinOp) and isinstance(nut.op, ast.Div)
            and isinstance(nut.left, ast.Name) and nut.left.id in _NHAN_GOC
            and isinstance(nut.right, ast.Constant) and nut.right.value != "tests")


def _liet_ke_mot_tang(cay: ast.AST) -> list[tuple[str, int, str]]:
    """[(hàm bao quanh, dòng, mã)] của mọi lượt liệt kê MỘT TẦNG có thể trả `tests/__tam_*`.

    Năm hình dạng: `.glob(...)`/`.iglob(...)` không `**`, `.iterdir()`, `os.listdir(...)`,
    `os.scandir(...)`, `glob.glob(...)` không `recursive`. Dạng đệ quy thuộc sổ đăng ký
    trên. Bỏ qua khi mẫu không khớp `_TEN_TEP_TAM_MAU` hoặc bên nhận chắc chắn không
    phải `tests/` (`_nhan_khong_phai_tests`).
    """
    ra = []

    def tham(nut, ham):
        for con in ast.iter_child_nodes(nut):
            ten = con.name if isinstance(con, (ast.FunctionDef, ast.AsyncFunctionDef)) else ham
            if isinstance(con, ast.Call) and isinstance(con.func, ast.Attribute):
                f, nhan, mau, la = con.func, con.func.value, None, False
                if (isinstance(nhan, ast.Name) and nhan.id == "os"
                        and f.attr in ("listdir", "scandir")):
                    la, nhan = True, (con.args[0] if con.args else None)
                elif isinstance(nhan, ast.Name) and nhan.id == "glob" and f.attr in ("glob", "iglob"):
                    la = not any(k.arg == "recursive" for k in con.keywords)
                    mau, nhan = (_mau_cua(con.args[0]) if con.args else None), None
                elif f.attr in ("glob", "iglob"):
                    mau = _mau_cua(con.args[0]) if con.args else None
                    la = not (mau is not None and "**" in mau)
                elif f.attr == "iterdir":
                    la = True
                if (la and not (mau is not None and not fnmatch.fnmatchcase(_TEN_TEP_TAM_MAU, mau))
                        and not (nhan is not None and _nhan_khong_phai_tests(nhan))):
                    ra.append((ham, con.lineno, ast.unparse(con)[:90]))
            tham(con, ten)

    tham(cay, "<module>")
    return ra


def test_SO_DANG_KY_MOT_TANG_moi_luot_liet_ke_co_the_thay_tep_tam_deu_qua_liet_ke():
    """Thêm `(GOC / "tests").glob("*.py")` rồi đọc thì đỏ ở đây: lượt liệt kê ấy trả tệp
    tạm của một test khác đang chạy song song (BƯỚC 211). Sửa: `duyet_repo.liet_ke(GOC,
    "tests", "*.py")`. Nếu nó thật sự không liệt kê `tests/`, khai `MIEN_TRU_MOT_TANG`."""
    vi_pham, thay = [], set()
    for f in _file_quan_the():
        rel = f.relative_to(GOC).as_posix()
        cay = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
        for ham, dong, ma in _liet_ke_mot_tang(cay):
            thay.add((rel, ham))
            if (rel, ham) not in MIEN_TRU_MOT_TANG:
                vi_pham.append(f"{rel}:{dong} (ham {ham}) {ma}")
    assert not vi_pham, (
        "luot liet ke MOT TANG co the tra tep tam tests/__tam_* cua test khac — dung "
        "duyet_repo.liet_ke:\n  " + "\n  ".join(vi_pham))
    chet = set(MIEN_TRU_MOT_TANG) - thay
    assert not chet, f"mien tru khong con ai dung, go di: {sorted(chet)}"


def test_SO_DANG_KY_MOT_TANG_KHONG_MU_bat_duoc_moi_hinh_dang_da_khai():
    """Máy đo cũng bị nghi như gác: đi qua đúng từng hình dạng nó khai, và KHÔNG bắt mẫu
    không khớp tệp tạm, bên nhận là gốc / `<gốc> / "tools"` / `tmp_path`, dạng đệ quy,
    f-string đuôi khác, hay chính `liet_ke`."""
    src = (
        "import os, glob\n"
        "def a(t):\n    return list(t.glob('*.py'))\n"
        "def b(t):\n    return os.listdir(t)\n"
        "def c(t):\n    return list(t.iterdir())\n"
        "def d():\n    return glob.glob(os.path.join(R, '*.py'))\n"
        "def e(t):\n    return list(os.scandir(t))\n"
        "def f(t):\n    return list(t.glob('test_*.py'))\n"
        "def g():\n    return list(GOC.glob('*.py'))\n"
        "def h():\n    return list((GOC / 'tools').glob('*.py'))\n"
        "def i():\n    return list((GOC / 'tests').glob('*.py'))\n"
        "def j(tmp_path):\n    return list((tmp_path / 'x').iterdir())\n"
        "def k(t):\n    return list(t.glob('**/*.py'))\n"
        "def l(t, b):\n    return list(t.glob(f'*_{b}.csv'))\n"
        "def m():\n    return duyet_repo.liet_ke(GOC, 'tests', '*.py')\n"
        "def n():\n    return list(Path(GOC).glob('*.py'))\n"
        "def o(t):\n    return list(t.iglob('*'))\n"
    )
    assert [h for h, _, _ in _liet_ke_mot_tang(ast.parse(src))] == [
        "a", "b", "c", "d", "e", "i", "o"]


def test_SO_DANG_KY_MOT_TANG_KHONG_MU_thay_du_cac_may_quet_that():
    """Đối chứng dương trên CÂY THẬT: sáu tệp đọc `tests/` một tầng đã chuyển sang
    `liet_ke` ngày 21/10/2026; thấy ít hơn thì phép đếm đang mù."""
    goi = set()
    for f in _file_quan_the():
        cay = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
        for n in ast.walk(cay):
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                    and n.func.attr == "liet_ke"):
                goi.add(f.relative_to(GOC).as_posix())
    assert len(goi - {"tests/test_duyet_repo.py"}) >= 6, f"chi thay {sorted(goi)}"


def test_CONG_2_khong_doc_tep_tam_cua_test_KHAC(tmp_path, monkeypatch):
    """Cổng 2 biên dịch bằng 3.11 mọi tệp `cac_file` trả: tệp đã mất ra dòng `khong doc
    duoc` → cổng ĐỎ giả. (Cổng 3 hỏi `exists()` trước khi đọc nên đã chịu được phần lớn
    cửa sổ; nó cũng đi qua `duyet` nên cùng được sửa.)"""
    k = _nap("kiem_cu_phap_311")
    _tao(tmp_path, "a.py", "tests/test_b.py", "tests/__tam_kiem_tra_mien_tru.py")
    _cuoc_dua(monkeypatch)
    assert _ten(tmp_path, k.cac_file(tmp_path)) == ["a.py", "tests/test_b.py"]

