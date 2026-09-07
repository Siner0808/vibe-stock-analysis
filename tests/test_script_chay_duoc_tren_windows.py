"""Mọi script có `print` phải đặt lại mã hoá stdout — gác toàn repo.

Cùng một lỗi đã xảy ra BA lần, mỗi lần trên một file khác:

    22/08/2026  tools/kiem_ban_sach.py       — cổng kiểm bản sạch
    23/08/2026  experiment_fundamentals.py   — script quyết TRONG_SO_CO_BAN
    24/08/2026  extend_history.py            — lệnh CLAUDE.md bảo nên chạy

Cả ba chết ở `print` đầu tiên vì console Windows mặc định cp1258, TRƯỚC khi
làm được việc gì. Không lần nào có test đỏ, vì test import module chứ không
chạy nó như một script.

Một công cụ kiểm tra không chạy được cũng là một cổng xanh giả: nó không
bao giờ báo lỗi, và sự im lặng đó đọc y hệt "sạch".

Vá từng file là cách sửa ba lần đầu. Đây là cách sửa lần thứ tư.
"""
import ast
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: Thư mục quét. `tests/` không cần — pytest tự bắt stdout.
THU_MUC = ("", "tools")


def _script_co_print(duong_dan: str) -> bool:
    """File này có chạy được như script VÀ có in ra màn hình không."""
    try:
        cay = ast.parse(open(duong_dan, encoding="utf-8").read())
    except (SyntaxError, UnicodeDecodeError):
        return False
    la_script = any(
        isinstance(n, ast.If) and isinstance(n.test, ast.Compare)
        and isinstance(n.test.left, ast.Name) and n.test.left.id == "__name__"
        for n in cay.body)
    if not la_script:
        return False
    return any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
               and n.func.id == "print" for n in ast.walk(cay))


def _co_reconfigure(duong_dan: str) -> bool:
    """Đọc AST, không đọc chuỗi — chú thích nhắc tên hàm sẽ khớp phải."""
    cay = ast.parse(open(duong_dan, encoding="utf-8").read())
    return any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
               and n.func.attr == "reconfigure" for n in ast.walk(cay))


def _liet_ke():
    ra = []
    for tm in THU_MUC:
        d = os.path.join(ROOT, tm) if tm else ROOT
        if not os.path.isdir(d):
            continue
        for ten in sorted(os.listdir(d)):
            if not ten.endswith(".py"):
                continue
            p = os.path.join(d, ten)
            if os.path.isfile(p) and _script_co_print(p):
                ra.append(p)
    return ra


def test_moi_script_co_print_phai_dat_lai_ma_hoa():
    scripts = _liet_ke()
    assert scripts, "không tìm thấy script nào — gác này đang quét nhầm chỗ"
    thieu = [os.path.relpath(p, ROOT).replace("\\", "/")
             for p in scripts if not _co_reconfigure(p)]
    assert not thieu, (
        "script có print nhưng thiếu sys.stdout.reconfigure(encoding='utf-8') "
        f"— sẽ chết ở dòng print đầu tiên trên console cp1258: {thieu}")
    print(f"PASS  {len(scripts)} script đều đặt lại mã hoá stdout")


def test_gac_nay_nhin_thay_du_so_script():
    """Nếu bộ lọc hỏng và trả về 2 file, test trên xanh mà chẳng gác gì.

    Con số dưới đây là sàn, không phải mốc cố định — thêm script mới không
    làm nó đỏ, nhưng một bộ lọc bị hỏng thì có.
    """
    n = len(_liet_ke())
    assert n >= 12, (   # đo được 15 ngày 24/08/2026
        f"chỉ thấy {n} script — bộ lọc hỏng, gác ở trên thành vô nghĩa")
    print(f"PASS  gác nhìn thấy {n} script")


# ══════════════════════════════════════════════════════════════════════
# Chiều NGƯỢC LẠI của cùng một bất đối xứng: máy Windows ↔ runner Linux
# ══════════════════════════════════════════════════════════════════════
#
# Phần trên canh "chạy được trên Windows". Phần dưới canh "chạy được trên
# LINUX", và nó cũng đã hỏng ba lần:
#
#     31/08/2026  kiem_cu_phap_311.DUONG_DOAN thiếu `sys.executable`
#     31/08/2026  test_skill_quy_trinh kiểm `exists()` — máy có, CI không
#     07/09/2026  va_an_toan + test_cua_quy_trinh ghim
#                 `.venv/Scripts/python.exe` — đường WINDOWS, CI là Linux
#
# Lần thứ ba xanh cả bốn cổng ở máy rồi đỏ CI ngay bước đầu, và bài học
# đã nằm sẵn trong docstring của `tests/test_hang_rao_tu_dong.py` từ
# 31/08. Vá từng file là cách sửa ba lần đầu.

THU_MUC_QUET = ("", "tools", "tests")


def _bien_ghim_venv(cay: ast.Module) -> set:
    """Tên biến ở mức module được gán một đường dẫn có chứa `.venv`."""
    ra = set()
    for cau in cay.body:
        if not isinstance(cau, ast.Assign):
            continue
        co = any(isinstance(n, ast.Constant) and isinstance(n.value, str)
                 and ".venv" in n.value for n in ast.walk(cau.value))
        if co:
            ra |= {t.id for t in cau.targets if isinstance(t, ast.Name)}
    return ra


def _trinh_thong_dich_ghim_cung(duong_dan: str) -> list:
    """PHÉP PHÁN. Lời gọi subprocess lấy trình thông dịch từ `.venv` ghim cứng.

    Chỉ soi ĐỐI SỐ ĐẦU TIÊN của `subprocess.run/Popen/check_*`, tức chỗ
    thật sự quyết định chạy bằng cái gì. Một chuỗi `.venv` nằm ở chỗ khác
    — ví dụ mẫu lệnh trong `tests/test_cua_quy_trinh.py::XAU`, hay danh
    sách thư mục bỏ qua — KHÔNG phải lỗi, và một gác kêu oan ở đó sẽ bị
    tắt (`docs/STATE.md` BƯỚC 31).
    """
    try:
        src = open(duong_dan, encoding="utf-8").read()
        cay = ast.parse(src)
    except (SyntaxError, UnicodeDecodeError, OSError):
        return []

    ghim = _bien_ghim_venv(cay)
    ra = []
    for n in ast.walk(cay):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr in ("run", "Popen", "check_output", "call",
                                    "check_call")
                and isinstance(n.func.value, ast.Name)
                and n.func.value.id == "subprocess"):
            continue
        if not n.args:
            continue
        dau = n.args[0]
        if isinstance(dau, ast.List) and dau.elts:
            dau = dau.elts[0]
        elif isinstance(dau, ast.BinOp) and isinstance(dau.left, ast.List) \
                and dau.left.elts:
            dau = dau.left.elts[0]
        for x in ast.walk(dau):
            if isinstance(x, ast.Constant) and isinstance(x.value, str) \
                    and ".venv" in x.value:
                ra.append(n.lineno)
            elif isinstance(x, ast.Name) and x.id in ghim:
                ra.append(n.lineno)
    return sorted(set(ra))


def _liet_ke_py():
    ra = []
    for tm in THU_MUC_QUET:
        d = os.path.join(ROOT, tm) if tm else ROOT
        if not os.path.isdir(d):
            continue
        for ten in sorted(os.listdir(d)):
            p = os.path.join(d, ten)
            if ten.endswith(".py") and os.path.isfile(p):
                ra.append(p)
    return ra


def test_khong_file_nao_ghim_cung_trinh_thong_dich_venv():
    ds = _liet_ke_py()
    assert ds, "không thấy file .py nào — gác này đang quét nhầm chỗ"
    pham = []
    for p in ds:
        for dong in _trinh_thong_dich_ghim_cung(p):
            pham.append(f"{os.path.relpath(p, ROOT).replace(os.sep, '/')}:{dong}")
    assert not pham, (
        "chạy subprocess bằng đường dẫn `.venv` ghim cứng — đó là đường "
        "WINDOWS, runner CI là Linux nên nó sẽ FileNotFoundError:\n  "
        + "\n  ".join(pham)
        + "\n\nDùng `sys.executable`, như `tools/kiem_test_chay_rieng.py`.")
    print(f"PASS  {len(ds)} file .py, 0 chỗ ghim cứng trình thông dịch")


_XAU_VENV = [
    ("chuỗi thẳng trong lời gọi",
     "import subprocess\n"
     "subprocess.run(['.venv/Scripts/python.exe', '-c', 'pass'])\n"),
    ("qua biến mức module",
     "import subprocess\n"
     "PY = '.venv/Scripts/python.exe'\n"
     "subprocess.run([PY, '-c', 'pass'])\n"),
    ("biến dựng bằng phép nối đường dẫn",
     "import subprocess\n"
     "from pathlib import Path\n"
     "PY = str(Path('x') / '.venv' / 'Scripts' / 'python.exe')\n"
     "subprocess.run([PY, '-m', 'pytest'])\n"),
    ("danh sách cộng thêm",
     "import subprocess\n"
     "PY = '.venv/Scripts/python.exe'\n"
     "subprocess.run([PY] + ['-q'])\n"),
    ("Popen chứ không phải run",
     "import subprocess\n"
     "subprocess.Popen(['.venv/Scripts/python.exe'])\n"),
]

_TOT_VENV = [
    ("sys.executable",
     "import subprocess, sys\n"
     "subprocess.run([sys.executable, '-c', 'pass'])\n"),
    (".venv chỉ là mẫu lệnh trong dữ liệu, không phải chỗ chạy",
     "import subprocess, sys\n"
     "MAU = ['./.venv/Scripts/python.exe -m pytest | tail -5']\n"
     "subprocess.run([sys.executable, '-c', 'pass'])\n"),
    (".venv trong danh sách thư mục bỏ qua",
     "BO_QUA = {'.venv', '.git'}\n"),
    (".venv nằm ở đối số SAU, không phải trình thông dịch",
     "import subprocess, sys\n"
     "subprocess.run([sys.executable, 'tools/x.py', '--goc', '.venv'])\n"),
]


def test_MAY_DO_venv_tu_chung_minh_no_bat_duoc(tmp_path):
    """5 mẫu xấu, 4 mẫu tốt, cùng một cửa.

    Mẫu tốt thứ hai là mẫu quan trọng: `tests/test_cua_quy_trinh.py` CÓ
    chuỗi `.venv` thật, trong danh sách lệnh mẫu để thử cửa Bash. Gác này
    phải tha nó, nếu không nó kêu oan ngay ngày đầu.
    """
    for ten, src in _XAU_VENV:
        f = tmp_path / "x.py"
        f.write_text(src, encoding="utf-8")
        assert _trinh_thong_dich_ghim_cung(str(f)), f"BỎ SÓT mẫu xấu: {ten}"
    for ten, src in _TOT_VENV:
        f = tmp_path / "y.py"
        f.write_text(src, encoding="utf-8")
        assert not _trinh_thong_dich_ghim_cung(str(f)), f"KÊU OAN mẫu tốt: {ten}"
    print(f"PASS  bắt {len(_XAU_VENV)}/{len(_XAU_VENV)} xấu, "
          f"tha {len(_TOT_VENV)}/{len(_TOT_VENV)} tốt")
