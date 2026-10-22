"""BƯỚC 217 — mã nguồn không gọi Streamlit bằng tham số đã bị khai tử.

`requirements.txt` khai `streamlit` KHÔNG ghim, nên Streamlit Cloud và CI luôn
cài bản mới nhất, còn máy cài một lần rồi đứng yên. Từ bản đang chạy ở máy
(1.64.0), mỗi lời gọi `use_container_width=` in một lời cảnh báo *"will be
removed after 2025-12-31"* — ngày ấy đã qua; ngày Streamlit gỡ tham số này, app
trên Cloud nổ `TypeError` ngay ở thanh bên. Thay bằng `width="stretch"` (cùng
nghĩa với `use_container_width=True` cho `dataframe` · `button` · `plotly_chart`).

Ba gác, cả ba đọc AST:
1. không lời gọi nào trong mã nguồn mang từ khoá `use_container_width`;
2. `width=` là chuỗi thì chỉ là `"stretch"` hoặc `"content"` (gõ sai thì
   Streamlit nổ lúc chạy, không phải lúc nạp);
3. mọi hàm `st.<tên>` được gọi với `width=` trong `app.py` thật sự nhận tham số
   `width` ở bản Streamlit đang cài — trên CI đó là bản mới nhất, nên gác này
   đỏ ngay khi Streamlit đổi chữ ký.
"""
from __future__ import annotations

import ast
import inspect
import pathlib
import sys

GOC = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))

import duyet_repo  # noqa: E402

THAM_SO_CU = "use_container_width"
GIA_TRI_WIDTH = {"stretch", "content"}


def _file_ma_nguon():
    bo = {"tests", ".venv", ".git", "node_modules", "__pycache__"}
    return [p for p in duyet_repo.duyet(GOC, "*.py")
            if not (set(p.relative_to(GOC).parts) & bo)]


def _goi_st(cay):
    """Mọi lời gọi `st.<tên>(...)` hoặc `st.<x>.<tên>(...)`: (tên, nút gọi)."""
    for n in ast.walk(cay):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)):
            continue
        goc = n.func.value
        while isinstance(goc, ast.Attribute):
            goc = goc.value
        if isinstance(goc, ast.Name) and goc.id == "st":
            yield n.func.attr, n


def _cay_app():
    return ast.parse((GOC / "app.py").read_text(encoding="utf-8"))


def test_quan_the_khac_rong_va_co_app_py():
    tep = _file_ma_nguon()
    assert GOC / "app.py" in tep, "quần thể phải chứa app.py — đường duyệt hỏng"
    assert len(tep) > 20


def test_KHONG_loi_goi_nao_mang_use_container_width():
    pham = []
    for p in _file_ma_nguon():
        cay = ast.parse(p.read_text(encoding="utf-8"))
        for n in ast.walk(cay):
            if isinstance(n, ast.keyword) and n.arg == THAM_SO_CU:
                pham.append(f"{p.relative_to(GOC)}:{n.value.lineno}")
    assert not pham, (
        f"`{THAM_SO_CU}=` đã bị Streamlit khai tử — dùng `width=\"stretch\"` "
        f"(True) hoặc `width=\"content\"` (False): {pham}")


def test_width_chuoi_chi_la_stretch_hoac_content():
    sai = []
    for ten, goi in _goi_st(_cay_app()):
        for k in goi.keywords:
            if (k.arg == "width" and isinstance(k.value, ast.Constant)
                    and isinstance(k.value.value, str)
                    and k.value.value not in GIA_TRI_WIDTH):
                sai.append(f"st.{ten} dòng {goi.lineno}: {k.value.value!r}")
    assert not sai, sai


def test_moi_ham_goi_voi_width_deu_NHAN_width():
    import streamlit as st

    goi_width = [(ten, goi.lineno) for ten, goi in _goi_st(_cay_app())
                 if any(k.arg == "width" for k in goi.keywords)]
    assert goi_width, "không thấy lời gọi `st.*(width=…)` nào — đường duyệt AST hỏng?"
    khong_nhan = sorted({f"st.{ten} (dòng {dong})" for ten, dong in goi_width
                         if "width" not in inspect.signature(getattr(st, ten)).parameters})
    assert not khong_nhan, (
        f"streamlit {st.__version__} không nhận `width` ở: {khong_nhan}")
