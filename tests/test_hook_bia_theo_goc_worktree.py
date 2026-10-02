"""Hook chặn bịa số liệu phán một file theo GỐC WORKTREE của chính file đó.

Sự cố 30/09/2026 (đo lúc làm BƯỚC 147). Hook đăng ký ở `~/.claude/settings.json`
bằng đường dẫn TUYỆT ĐỐI của bản checkout chính, nên `GOC_DU_AN` luôn là bản
checkout chính, và mọi file được phán theo đường dẫn tương đối so với nó:

    worktree LỒNG   .claude/worktrees/<tên>/tests/x.py -> không bắt đầu bằng
                    `tests/` -> KHÔNG nhận ra là test -> CHẶN NHẦM R1
    worktree NGOÀI  `relative_to` nổ -> "ngoài dự án" -> hook IM LẶNG; mà mọi
                    phiên song song đều làm việc ở một worktree NGOÀI. Một file
                    có `getattr(o, "ten_sai", 30)` ở đó lọt hoàn toàn.
    cửa Stop        `git diff` chạy ở bản checkout chính, nên không thấy thay
                    đổi nào ở worktree của phiên.

Người dùng chốt 30/09/2026: quét MỌI worktree của CÙNG repo (không quét repo
khác). "Cùng repo" = cùng `git rev-parse --git-common-dir`.

Mọi ca dùng `git worktree add` THẬT trên một repo tạm, không đụng repo thật;
ca ống bơm chạy bản sao của hook đặt trong repo tạm, từ một cwd NGOÀI repo
(lỗi 15: công cụ đúng trong repo có thể sai khi gọi từ nơi khác).

Vài chỗ cố ý:
- worktree ngoài nằm dưới một thư mục tên `scratch` — đúng như thật. Phán theo
  đường dẫn tuyệt đối thì `scratch` ở tổ tiên miễn trừ CẢ worktree.
- các ca ống bơm không bơm cùng (file, nội dung) hai lần trong 5 giây: hook tự
  im lần hai (`da_bao_gan_day`), và ca ấy sẽ đỏ vì lý do không liên quan.
"""
import contextlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(GOC / "tools"))

import chan_bia_so_lieu as hook  # noqa: E402

HOOK_THAT = GOC / "tools" / "chan_bia_so_lieu.py"

#: R1 thật — đúng hình dạng sự cố 12/08/2026. Là chuỗi, không phải mã: chính
#: file test này không được mang mẫu ấy.
BIA = 'def f(o):\n    return getattr(o, "ten_sai", 30)\n'

#: Dataclass có trường `size_pct`; `position_size_pct` ở BIA_R2 là cái tên sai.
LOP = "from dataclasses import dataclass\n\n\n@dataclass\nclass Trade:\n    size_pct: float\n"
BIA_R2 = 'def g(t):\n    return getattr(t, "position_size_pct", None)\n'


def _git(cwd, *args) -> str:
    r = subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t",
         "-c", "commit.gpgsign=false", *args],
        cwd=str(cwd), capture_output=True, text=True, encoding="utf-8",
        errors="replace")
    assert r.returncode == 0, f"git {' '.join(args)} lỗi: {r.stderr}"
    return r.stdout


@pytest.fixture(scope="module")
def kho(tmp_path_factory):
    """Repo tạm + hai worktree thật (lồng và ngoài) + một repo lạ + một thư mục không git."""
    goc = tmp_path_factory.mktemp("kho").resolve()

    main = goc / "main"
    (main / "tools").mkdir(parents=True)
    _git(main, "init", "-q")
    shutil.copy(HOOK_THAT, main / "tools" / "chan_bia_so_lieu.py")
    # Hook nhập `duyet_repo` cùng thư mục (BƯỚC 147): thiếu nó thì bản sao chết
    # ngay khi nạp và mọi ca ống bơm thấy mã thoát 1.
    shutil.copy(GOC / "tools" / "duyet_repo.py", main / "tools" / "duyet_repo.py")
    (main / "README.md").write_text("kho tam\n", encoding="utf-8")
    # Như repo thật: `.claude/worktrees/` nằm trong exclude của bản checkout chính.
    with (main / ".git" / "info" / "exclude").open("a", encoding="utf-8") as f:
        f.write(".claude/worktrees/\n")
    _git(main, "add", "-A")
    _git(main, "commit", "-q", "-m", "khoi tao")

    trong = main / ".claude" / "worktrees" / "trong"
    ngoai = goc / "scratch" / "ngoai"           # `scratch` ở TỔ TIÊN — cố ý
    ngoai.parent.mkdir()
    _git(main, "worktree", "add", "-q", "--detach", str(trong))
    _git(main, "worktree", "add", "-q", "--detach", str(ngoai))

    khac = goc / "khac"                          # một repo KHÁC
    (khac / "tools").mkdir(parents=True)
    (khac / "README.md").write_text("repo la\n", encoding="utf-8")
    _git(khac, "init", "-q")
    _git(khac, "add", "-A")
    _git(khac, "commit", "-q", "-m", "khoi tao")

    khong_git = goc / "khong_git"
    (khong_git / "tools").mkdir(parents=True)
    cwd_ngoai = goc / "cwd_ngoai"                # cwd của hook: NGOÀI mọi repo
    cwd_ngoai.mkdir()

    return SimpleNamespace(
        main=main.resolve(), trong=trong.resolve(), ngoai=ngoai.resolve(),
        khac=khac.resolve(), khong_git=khong_git.resolve(),
        cwd_ngoai=cwd_ngoai.resolve())


@pytest.fixture(autouse=True)
def _hook_nhin_vao_kho(kho, monkeypatch):
    """`GOC_DU_AN` của module = bản checkout chính của repo tạm, như trên máy thật."""
    monkeypatch.setattr(hook, "GOC_DU_AN", kho.main)
    hook.xoa_bo_nho_goc()
    yield
    hook.xoa_bo_nho_goc()


@contextlib.contextmanager
def _viet(duong: Path, ma: str):
    duong.parent.mkdir(parents=True, exist_ok=True)
    duong.write_text(ma, encoding="utf-8")
    try:
        yield duong
    finally:
        duong.unlink(missing_ok=True)


def _ma(phat_hien) -> set:
    return {p.ma for p in phat_hien}


# ── 1. Phán theo gốc của CHÍNH file ──────────────────────────────────

def test_test_trong_worktree_LONG_duoc_mien_nhu_o_checkout_chinh(kho):
    """Đường tương đối so với bản checkout chính là `.claude/worktrees/trong/
    tests/x.py` — không bắt đầu bằng `tests/` nên bị chặn nhầm R1 (đo 30/09)."""
    with _viet(kho.trong / "tests" / "x_test.py", BIA) as f:
        assert hook.trong_pham_vi(f) is True
        assert "R1" not in _ma(hook.kiem_tra(f)), (
            "test ở worktree lồng bị chấm như mã thường")


def test_ma_bia_that_trong_worktree_LONG_van_bi_bat(kho):
    """Đối chứng: nới cho `tests/` không được nới cho phần còn lại."""
    with _viet(kho.trong / "tools" / "bia.py", BIA) as f:
        assert hook.trong_pham_vi(f) is True
        assert "R1" in _ma(hook.kiem_tra(f))


def test_ma_bia_that_o_worktree_NGOAI_repo_bi_bat(kho):
    """Lỗ nặng nhất: worktree ngoài repo là nơi mọi phiên song song làm việc."""
    with _viet(kho.ngoai / "tools" / "bia.py", BIA) as f:
        assert hook.trong_pham_vi(f) is True, (
            "file ở worktree NGOÀI repo bị coi là ngoài dự án -> hook mù")
        assert "R1" in _ma(hook.kiem_tra(f))


def test_test_o_worktree_NGOAI_cung_duoc_mien(kho):
    with _viet(kho.ngoai / "tests" / "x_test.py", BIA) as f:
        assert hook.trong_pham_vi(f) is True
        assert "R1" not in _ma(hook.kiem_tra(f))


def test_ten_thu_muc_TO_TIEN_khong_mien_file_nhung_thu_muc_mien_TRONG_goc_thi_co(kho):
    """Worktree ngoài nằm dưới `scratch/` (đúng như trên máy thật). Miễn trừ
    chỉ tính theo đường dẫn TƯƠNG ĐỐI so với gốc worktree, không theo tổ tiên;
    còn `scratch/` NẰM TRONG worktree thì vẫn được miễn như ở checkout chính."""
    assert "scratch" in kho.ngoai.parts
    with _viet(kho.ngoai / "tools" / "bia.py", BIA) as f:
        assert hook.trong_pham_vi(f) is True
    with _viet(kho.ngoai / "scratch" / "nhap.py", BIA) as f:
        assert hook.trong_pham_vi(f) is False, "scratch/ TRONG worktree phải còn được miễn"
    with _viet(kho.trong / "backtest" / "cache" / "nhap.py", BIA) as f:
        assert hook.trong_pham_vi(f) is False, "backtest/cache TRONG worktree phải còn được miễn"


def test_repo_KHAC_va_thu_muc_khong_git_bi_bo_qua(kho):
    """Phạm vi là CÙNG repo. Repo khác, hay chỗ không có git, vẫn ngoài dự án."""
    with _viet(kho.khac / "tools" / "bia.py", BIA) as f:
        assert hook.trong_pham_vi(f) is False
    with _viet(kho.khong_git / "tools" / "bia.py", BIA) as f:
        assert hook.trong_pham_vi(f) is False


def test_luoc_do_R2_lay_tu_goc_cua_CHINH_file(kho):
    """R2 đối chiếu tên trường với dataclass ở gốc. Worktree có dataclass mà
    bản checkout chính chưa có (nhánh đang thêm nó) thì phải dùng của worktree."""
    with _viet(kho.trong / "mo_hinh_thu.py", LOP), \
            _viet(kho.trong / "tools" / "dung.py", BIA_R2) as f:
        assert "R2" in _ma(hook.kiem_tra(f)), (
            "lược đồ lấy từ bản checkout chính, không phải từ worktree của file")
    with _viet(kho.ngoai / "mo_hinh_thu.py", LOP), \
            _viet(kho.ngoai / "tools" / "dung.py", BIA_R2) as f:
        assert "R2" in _ma(hook.kiem_tra(f))


def test_file_o_GOC_worktree_va_file_sau_nhieu_tang_deu_duoc_nhan(kho):
    """`app.py` ở gốc repo là dạng file phổ biến nhất; tìm gốc phải tính cả
    chính thư mục chứa file, không chỉ tổ tiên của nó."""
    for goc in (kho.trong, kho.ngoai):
        with _viet(goc / "goc_bia.py", BIA) as f:
            assert hook.trong_pham_vi(f) is True
            assert hook.goc_cua_file(f) == goc
            assert "R1" in _ma(hook.kiem_tra(f))
        with _viet(goc / "a" / "b" / "c" / "sau_bia.py", BIA) as f:
            assert hook.goc_cua_file(f) == goc
            assert hook.trong_pham_vi(f) is True


def test_hook_nam_trong_WORKTREE_van_thay_checkout_chinh_va_worktree_kia(kho, monkeypatch):
    """Bản sao hook chạy từ một worktree (`GOC_DU_AN` là worktree): bản checkout
    chính in `--git-common-dir` là đường TƯƠNG ĐỐI `.git`, worktree thì in đường
    tuyệt đối. Hai vế phải quy về cùng một chỗ."""
    monkeypatch.setattr(hook, "GOC_DU_AN", kho.ngoai)
    hook.xoa_bo_nho_goc()
    for goc in (kho.main, kho.trong, kho.ngoai):
        with _viet(goc / "tools" / "bia_cheo.py", BIA) as f:
            assert hook.trong_pham_vi(f) is True, f"không nhận {goc}"
            assert hook.goc_cua_file(f) == goc


def test_khong_hoi_duoc_git_thi_checkout_chinh_van_quet_worktree_thi_im_nhu_cu(kho, monkeypatch):
    """Không suy ra được thì im như trước — không đoán. Nhưng bản checkout chính
    không cần git để biết nó là của dự án; mù cả nó là lùi so với trước."""
    def khong_hoi_duoc(goc):
        return None
    # Fixture huỷ theo thứ tự ngược: `xoa_bo_nho_goc()` chạy khi hàm giả còn gài.
    khong_hoi_duoc.cache_clear = lambda: None
    monkeypatch.setattr(hook, "_thu_muc_git_chung", khong_hoi_duoc)
    with _viet(kho.main / "tools" / "bia.py", BIA) as f:
        assert hook.trong_pham_vi(f) is True
    for goc in (kho.trong, kho.ngoai):
        with _viet(goc / "tools" / "bia.py", BIA) as f:
            assert hook.trong_pham_vi(f) is False


def test_checkout_chinh_KHONG_CO_git_van_duoc_quet(kho, monkeypatch):
    """Bản xuất mã nguồn không kèm `.git`: trước BƯỚC này file dưới `GOC_DU_AN`
    luôn trong phạm vi vì `relative_to` không cần git. BƯỚC 147 bắt được hồi quy
    ở `test_duyet_repo.py::test_CONG_3`; ca này khoá nó ngay trong file của
    chính cơ chế."""
    monkeypatch.setattr(hook, "GOC_DU_AN", kho.khong_git)
    hook.xoa_bo_nho_goc()
    with _viet(kho.khong_git / "tools" / "bia.py", BIA) as f:
        assert hook.trong_pham_vi(f) is True
        assert hook.goc_cua_file(f) == kho.khong_git
        assert "R1" in _ma(hook.kiem_tra(f))


def test_dau_git_hong_ma_git_khong_doc_duoc_thi_khong_duoc_tinh_la_cung_repo(kho, monkeypatch):
    """`None == None` là bẫy: khi CẢ HAI bên chưa hỏi được git thì chúng không
    'giống nhau', chúng đều 'chưa biết'."""
    monkeypatch.setattr(hook, "GOC_DU_AN", kho.khong_git)
    hook.xoa_bo_nho_goc()
    hong = kho.khong_git / "hong"
    (hong / ".git").mkdir(parents=True, exist_ok=True)     # có tên `.git`, git không đọc được
    try:
        with _viet(hong / "tools" / "bia.py", BIA) as f:
            assert hook.trong_pham_vi(f) is False
    finally:
        shutil.rmtree(hong, ignore_errors=True)


def test_git_bao_loi_thi_khong_doc_duoc_dau_ra_du_no_in_ra_mot_duong(kho, monkeypatch):
    """Nhánh `returncode != 0` khác nhánh `stdout rỗng`: git thật khi lỗi in ra
    stderr nên hai nhánh trùng nhau — bỏ kiểm mã thoát thì mọi test dựa vào git
    thật vẫn xanh. Chỉ một `subprocess.run` giả (mã 128 nhưng stdout là một
    đường hợp lệ) phân biệt được chúng."""
    fake = SimpleNamespace(returncode=128, stdout=str(kho.main / ".git") + "\n", stderr="")
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: fake)
    hook.xoa_bo_nho_goc()
    assert hook._thu_muc_git_chung(kho.trong) is None
    with _viet(kho.trong / "tools" / "bia.py", BIA) as f:
        assert hook.trong_pham_vi(f) is False


def test_git_khong_chay_duoc_thi_none_khong_no(kho, monkeypatch):
    """Nhánh `except`: không có git, hết giờ, cwd biến mất."""
    def no(*a, **k):
        raise FileNotFoundError("khong co git")
    monkeypatch.setattr(subprocess, "run", no)
    hook.xoa_bo_nho_goc()
    assert hook._thu_muc_git_chung(kho.trong) is None


def test_thu_muc_khong_doc_duoc_thi_ngoai_pham_vi_khong_no(kho, monkeypatch):
    """Duyệt tổ tiên có thể chạm thư mục không đọc được (EACCES) — hook chết là
    hook không bảo vệ được gì."""
    def no(_):
        raise PermissionError("khong doc duoc")
    monkeypatch.setattr(hook, "_dau_git", no)
    assert hook.goc_cua_thu_muc(kho.trong) is None


def test_cwd_da_bi_xoa_thi_goc_phien_ve_checkout_chinh(kho, monkeypatch):
    def no(cls):
        raise FileNotFoundError("cwd da bi xoa")
    monkeypatch.setattr(Path, "cwd", classmethod(no))
    assert hook.goc_phien() == kho.main


def test_duong_dan_co_cham_cham_duoc_quy_ve_goc_THAT(kho):
    """`ngoai/../../main/tools/x.py` là file của `main`, dù về mặt chữ nó nằm
    dưới `ngoai`. Tìm gốc phải trên đường dẫn đã `resolve`."""
    with _viet(kho.main / "tools" / "bia_cham_cham.py", BIA):
        f = kho.ngoai / ".." / ".." / "main" / "tools" / "bia_cham_cham.py"
        assert hook.goc_cua_file(f) == kho.main
        assert hook.trong_pham_vi(f) is True


def test_cung_mot_thu_muc_chi_di_len_tim_git_MOT_lan(kho, monkeypatch):
    """Hồi quy hiệu năng đo được 30/09/2026: bản đầu `resolve()` hai lần và đi
    `stat` lên tổ tiên cho MỌI file. `--quet-repo` hỏi từng file của cả cây mà
    `.venv` một mình có hàng chục nghìn file — ba file test chạy 154 giây."""
    dem = []
    that = hook._dau_git

    def dem_goi(thu_muc):
        dem.append(thu_muc)
        return that(thu_muc)

    monkeypatch.setattr(hook, "_dau_git", dem_goi)
    ds = [kho.trong / "tools" / f"cung_thu_muc_{i}.py" for i in range(5)]
    for f in ds:
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(BIA, encoding="utf-8")
    try:
        assert all(hook.trong_pham_vi(f) for f in ds)
    finally:
        for f in ds:
            f.unlink(missing_ok=True)
    assert len(dem) == 1, f"đi lên tìm .git {len(dem)} lần cho 5 file cùng một thư mục"


# ── 2. Ống bơm payload thật, từ cwd NGOÀI repo ───────────────────────

def _bom(kho, file_path: Path):
    """Chạy BẢN SAO của hook đặt trong repo tạm — `GOC_DU_AN` của nó là
    `kho.main`, như hook đăng ký toàn cục ở máy thật — từ cwd ngoài mọi repo."""
    r = subprocess.run(
        [sys.executable, str(kho.main / "tools" / "chan_bia_so_lieu.py")],
        input=json.dumps({"tool_input": {"file_path": str(file_path)}}),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(kho.cwd_ngoai),
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"})
    return r.returncode, r.stdout


@pytest.mark.parametrize("nhan,goc,tuong_doi,phai_chan", [
    ("mã bịa ở checkout chính", "main", "tools/bia_bom_1.py", True),
    ("mã bịa ở worktree LỒNG", "trong", "tools/bia_bom_2.py", True),
    ("mã bịa ở worktree NGOÀI", "ngoai", "tools/bia_bom_3.py", True),
    ("test ở checkout chính", "main", "tests/x_bom_4.py", False),
    ("test ở worktree LỒNG", "trong", "tests/x_bom_5.py", False),
    ("test ở worktree NGOÀI", "ngoai", "tests/x_bom_6.py", False),
    ("mã bịa ở repo KHÁC", "khac", "tools/bia_bom_7.py", False),
    ("mã bịa ở chỗ không git", "khong_git", "tools/bia_bom_8.py", False),
])
def test_ong_bom_tu_cwd_ngoai_repo(kho, nhan, goc, tuong_doi, phai_chan):
    with _viet(getattr(kho, goc) / tuong_doi, BIA) as f:
        ma, ra = _bom(kho, f)
    assert ma == 0, "hook không bao giờ được thoát khác 0 ở PostToolUse"
    chan = '"decision": "block"' in ra
    assert chan is phai_chan, f"{nhan}: chặn={chan}, mong đợi {phai_chan}. stdout={ra[:200]!r}"


# ── 3. Cửa Stop: quét thay đổi ở worktree CỦA PHIÊN ──────────────────

def _stop(kho, cwd: Path):
    r = subprocess.run(
        [sys.executable, str(kho.main / "tools" / "chan_bia_so_lieu.py"),
         "--quet-thay-doi"],
        input="", capture_output=True, text=True, encoding="utf-8",
        errors="replace", cwd=str(cwd),
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"})
    return r.returncode, r.stdout


@pytest.mark.parametrize("goc", ["main", "trong", "ngoai"])
def test_cua_STOP_thay_file_bia_o_worktree_cua_phien(kho, goc):
    with _viet(getattr(kho, goc) / "tools" / "bia_stop.py", BIA):
        ma, ra = _stop(kho, getattr(kho, goc))
    assert ma == 1, f"cwd={goc}: Stop không thấy file bịa chưa commit. stdout={ra!r}"
    assert "tools/bia_stop.py" in ra, (
        f"cwd={goc}: phải in đường dẫn TƯƠNG ĐỐI so với gốc worktree. stdout={ra!r}")
    assert "Quét 1 file đã đổi" in ra, (
        f"cwd={goc}: phải là kết quả hỏi git ở đúng worktree, không phải đường "
        f"lùi quét toàn repo. stdout={ra!r}")


def test_cua_STOP_khong_quet_worktree_khac_cua_repo(kho):
    """Phiên ở checkout chính không được bị báo lỗi của worktree người khác —
    ngược với việc quét mọi worktree lúc dừng, sẽ ồn và không phải việc của nó."""
    with _viet(kho.ngoai / "tools" / "bia_stop.py", BIA):
        ma, ra = _stop(kho, kho.main)
    assert ma == 0 and "bia_stop" not in ra, ra


def test_cua_STOP_cay_sach_o_worktree_thi_im(kho):
    """git trả lời "không đổi gì" là SẠCH, không phải "chưa hỏi được"."""
    ma, ra = _stop(kho, kho.ngoai)
    assert ma == 0 and ra.strip() == "", ra


def test_cua_STOP_cwd_ngoai_repo_giu_hanh_vi_cu(kho):
    """Không suy ra được worktree nào từ cwd -> quét bản checkout chính như
    trước BƯỚC này. Không đổi hành vi ở chỗ chưa có yêu cầu đổi."""
    with _viet(kho.main / "tools" / "bia_stop.py", BIA):
        ma, ra = _stop(kho, kho.cwd_ngoai)
    assert ma == 1 and "tools/bia_stop.py" in ra, ra
    # Tiêu đề phân biệt "hỏi git ở bản checkout chính" với đường lùi về quét
    # toàn repo (cả hai đều thấy file bịa ở ca này).
    assert "Quét 1 file đã đổi" in ra, ra


# ── 4. Bộ nhớ lược đồ THEO LƯỢT QUÉT (BƯỚC 152) ──────────────────────
# Đo 01/10/2026: một lượt `quet_repo()` gọi `thu_thap_truong` 243 lần (mỗi file
# một lần, mỗi lần đọc và `ast.parse` mọi `*.py` ở gốc) và dành 90–92% thời gian
# (37,6 s trên 41,8 s; 41,0 s trên 44,4 s) cho việc dựng lại CÙNG MỘT lược đồ.

def _tao_file(goc: Path, ten: str, n: int, ma: str = BIA_R2) -> list[Path]:
    ds = []
    for i in range(n):
        f = goc / "tools" / f"{ten}_{i}.py"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(ma, encoding="utf-8")
        ds.append(f)
    return ds


def _don(ds) -> None:
    for f in ds:
        f.unlink(missing_ok=True)


def _dem_luoc_do(monkeypatch) -> list:
    dem = []
    that = hook.thu_thap_truong

    def dem_goi(goc):
        dem.append(goc)
        return that(goc)

    monkeypatch.setattr(hook, "thu_thap_truong", dem_goi)
    return dem


def test_luot_quet_dung_luoc_do_MOT_lan_cho_MOI_goc(kho, monkeypatch):
    dem = _dem_luoc_do(monkeypatch)
    ds = _tao_file(kho.trong, "q_trong", 3) + _tao_file(kho.ngoai, "q_ngoai", 3)
    try:
        hook._quet(ds, "thu")
    finally:
        _don(ds)
    assert sorted(dem) == sorted([kho.trong, kho.ngoai]), (
        f"mong mỗi gốc đúng một lần, được {len(dem)} lần: {dem}")


def test_goc_KHONG_CO_dataclass_nao_van_chi_dung_luoc_do_MOT_lan(kho, monkeypatch):
    """Lược đồ rỗng `{}` là giá trị HỢP LỆ, không phải 'chưa có': nhớ theo
    `in`, không theo độ thật của giá trị."""
    dem = _dem_luoc_do(monkeypatch)
    ds = _tao_file(kho.ngoai, "r_ngoai", 4)
    try:
        hook._quet(ds, "thu")
    finally:
        _don(ds)
    assert dem == [kho.ngoai], f"gốc không dataclass bị dựng lại {len(dem)} lần"


def test_ket_qua_CO_va_KHONG_bo_nho_giong_het_nhau(kho):
    ds = []
    try:
        with _viet(kho.trong / "mo_hinh_thu.py", LOP):
            ds = (_tao_file(kho.trong, "e_trong", 2) + _tao_file(kho.trong, "e_bia", 1, BIA)
                  + _tao_file(kho.ngoai, "e_ngoai", 2))
            bo_nho: dict = {}
            tat_ca = []
            for f in ds:
                a = [(p.ma, p.dong, p.chan, p.thong_diep) for p in hook.kiem_tra(f)]
                b = [(p.ma, p.dong, p.chan, p.thong_diep) for p in hook.kiem_tra(f, bo_nho)]
                assert a == b, f"{f.name}: có bộ nhớ khác không bộ nhớ"
                tat_ca += a
            assert {m for m, *_ in tat_ca} >= {"R1", "R2"}, (
                f"ca so sánh rỗng ruột — không phát hiện nào để so: {tat_ca}")
    finally:
        _don(ds)


def test_MOI_goc_co_luoc_do_RIENG_trong_cung_mot_luot_quet(kho, capsys):
    """Một bộ nhớ chung cho mọi gốc sẽ trả lược đồ của gốc đầu tiên cho gốc
    thứ hai: R2 ở worktree có dataclass biến mất, hoặc hiện ở nơi không có."""
    trong = kho.trong / "tools" / "dung_trong.py"
    ngoai = kho.ngoai / "tools" / "dung_ngoai.py"
    try:
        with _viet(kho.trong / "mo_hinh_thu.py", LOP):
            for f in (trong, ngoai):
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(BIA_R2, encoding="utf-8")
            hook._quet([ngoai, trong], "thu")           # gốc KHÔNG dataclass đi trước
            ra = capsys.readouterr().out
    finally:
        _don([trong, ngoai])
    assert "[R2/CHẶN] tools/dung_trong.py" in ra, ra
    assert "dung_ngoai" not in ra, ra
