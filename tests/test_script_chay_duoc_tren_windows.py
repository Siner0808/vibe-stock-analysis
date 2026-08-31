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
