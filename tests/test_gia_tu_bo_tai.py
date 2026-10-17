"""Vòng tải giá DÙNG CHUNG của sổ bài học (`so_bai_hoc.gia_tu_bo_tai`, BƯỚC 204).

App (nút "📥 Tải giá…") và phần chạy B1 (`tools/hau_kiem_loi.py`) cùng đi qua một vòng,
chỉ khác bộ tải — không có đường giá thứ hai (đặc tả B1 mục 4, bước 2).
"""
from __future__ import annotations

import ast
import pathlib

import pandas as pd

import so_bai_hoc

GOC = pathlib.Path(__file__).resolve().parent.parent


def test_GOM_GIA_nhan_he_so_va_ghi_ma_thieu():
    df = pd.DataFrame({"time": ["2026-10-01", "2026-10-02"], "close": [27.45, 27.6]})
    bang = {"HPG": (df, "OK"), "HSG": (None, "FAILED"), "NKG": (df.iloc[0:0], "OK"),
            "MSR": (df, "FAILED")}
    gia, thieu = so_bai_hoc.gia_tu_bo_tai(list(bang), lambda m: bang[m])
    assert gia == {"HPG": {"2026-10-01": 27450.0, "2026-10-02": 27600.0}}
    assert thieu == ["HSG", "NKG", "MSR"]


def test_APP_di_qua_vong_chung_khong_tu_lap():
    cay = ast.parse((GOC / "app.py").read_text(encoding="utf-8"))
    f = next(n for n in ast.walk(cay)
             if isinstance(n, ast.FunctionDef) and n.name == "_gia_cho_so_bai_hoc")
    goi = {n.func.attr for n in ast.walk(f)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert "gia_tu_bo_tai" in goi
    assert not [n for n in ast.walk(f) if isinstance(n, (ast.For, ast.While))]
