"""Gác lỗi 187 (BƯỚC 214): dụng cụ ĐO (`tools/doN_*.py`) phải từ chối cờ lạ TRƯỚC khi
kéo nguồn nào.

21/10/2026, lúc mở ngày, leader gõ `tools/do27_su_kien_quyen_chieu_tien.py --help 2>&1
| head -30` để xem cách dùng. Dụng cụ đọc `sys.argv` bằng tay, chỉ nhận `--json`, nên
bỏ qua `--help` và chạy THẬT phép đọc đã hẹn của ĐO 27: kéo sổ thật, nến, lịch VCI.
`head` nuốt mọi dòng kết quả. Một phép đọc ký "kéo mỗi nguồn MỘT lần" bị kéo hai lần.

Hai lớp chặn: dụng cụ dùng `argparse` (gác dưới), và cửa Bash chặn dụng cụ đo chạy
qua ống (`dung-cu-do-qua-ong`, `tests/test_cua_quy_trinh.py`).
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))
sys.path.insert(0, str(GOC))

DUNG_CU_DO = sorted(p for p in (GOC / "tools").glob("do*.py") if re.match(r"do\d+", p.name))


def _co_main(cay: ast.AST) -> bool:
    return any(isinstance(n, ast.If) and "__main__" in ast.unparse(n.test) for n in ast.walk(cay))


def test_QUAN_THE_khong_rong_va_co_ca_that():
    ten = {p.name for p in DUNG_CU_DO}
    assert len(ten) >= 20, ten
    assert "do27_su_kien_quyen_chieu_tien.py" in ten


@pytest.mark.parametrize("p", DUNG_CU_DO, ids=lambda p: p.name)
def test_MOI_DUNG_CU_DO_chay_duoc_deu_doc_co_bang_ARGPARSE(p):
    """Dụng cụ đọc `sys.argv` bằng tay thì một cờ gõ nhầm bị bỏ qua và phép đo chạy thật."""
    cay = ast.parse(p.read_text(encoding="utf-8"))
    if not _co_main(cay):
        return
    nhap = {a.name for n in ast.walk(cay) if isinstance(n, ast.Import) for a in n.names}
    goi = {n.func.attr for n in ast.walk(cay)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert "argparse" in nhap and "parse_args" in goi, (
        f"{p.name} có `__main__` mà không đọc cờ bằng argparse — `--help` sẽ chạy thật")


def _khong_duoc_keo():
    pytest.fail("dụng cụ KÉO NGUỒN trước khi đọc xong cờ")


@pytest.mark.parametrize("ten", ["do26_nguong_su_kien_quyen", "do27_su_kien_quyen_chieu_tien"])
def test_HELP_in_cach_dung_va_thoat_KHONG_keo_nguon(ten, capsys):
    """Dựng lại nguyên văn lỗi 187."""
    import importlib
    m = importlib.import_module(ten)
    with pytest.raises(SystemExit) as e:
        m.main(["--help"], keo=_khong_duoc_keo)
    assert e.value.code == 0
    assert "--json" in capsys.readouterr().out


@pytest.mark.parametrize("ten", ["do26_nguong_su_kien_quyen", "do27_su_kien_quyen_chieu_tien"])
def test_CO_LA_thi_thoat_2_KHONG_keo_nguon(ten):
    import importlib
    m = importlib.import_module(ten)
    with pytest.raises(SystemExit) as e:
        m.main(["--jsno", "x.json"], keo=_khong_duoc_keo)
    assert e.value.code == 2
