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
    return (sorted(GOC.glob("*.py")) + sorted((GOC / "tools").glob("*.py"))
            + sorted((GOC / "tests").glob("*.py")))


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
