"""Chú thích lỗ GIẢ do sự kiện quyền ở app (BƯỚC 271) — CHỈ CHỮ, không đổi số.

Người dùng chốt 12/11/2026 (nguyên văn): *"Thêm chú thích, cùng BƯỚC thiết kế (Recommended)"*;
chữ họ thấy: một dòng nhỏ "gồm 2 lệnh lỗ giả do sự kiện quyền" cạnh ô Sổ lệnh (net) và cạnh lời
B1 của hai lệnh; KHÔNG in số +7,95% (số đẹp lên, không phải số đã sửa).

Bốn gác:
  1. Hàm thuần: có mặt đủ hai lệnh thì "gồm 2 …"; thiếu một thì "gồm 1 …"; không có thì None;
     khớp theo CẢ id, mã VÀ lý do thoát (sổ đánh số lại không gắn nhầm).
  2. Không số "đã loại": mọi chuỗi của ba hằng chú thích không có số thập phân, không có phần trăm,
     không có chữ "đã loại"/"without"; và ba hàm `chu_thich_*` KHÔNG đụng vào thước đo
     (`compute` · `Performance` · `total_net_pct` · `net_return_pct`) — AST, không đọc `in`.
  3. Nối vào app (AST): ô topbar "Sổ lệnh (net)" mang `_chu_thich_so_lenh_html`; khối hậu kiểm gọi
     `chu_thich_hau_kiem` và hiện kết quả TRƯỚC `import hau_kiem_loi`.
  4. Nguyên nhân viết từ mã: câu nói tới `low <= sl` ở `paper_trading._lenh_dat_san` có thật.
"""
from __future__ import annotations

import ast
import pathlib
import re
import sys

GOC = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import paper_trading as pt  # noqa: E402
import so_lenh_app as sla  # noqa: E402


def _lenh(i: int, ma: str, ly_do: str = "STOP_LOSS") -> pt.Trade:
    return pt.PaperTradingJournal._to_trade({
        "id": i, "symbol": ma, "exchange": "HOSE", "signal_date": "2026-10-01",
        "entry_date": "2026-10-02", "entry_price": 100.0, "exit_date": "2026-10-09",
        "exit_price": 80.0, "exit_reason": ly_do, "stop_loss": 90.0, "take_profit": 120.0,
        "size_pct": 10.0, "entry_score": 65, "entry_recommendation": "BUY",
        "components": "{}", "reasons": "[]", "status": "CLOSED", "created_at": 0.0})


def test_HAM_dem_dung_so_lenh_co_mat_trong_so():
    ca_hai = (_lenh(122, "HDB"), _lenh(128, "TCB"), _lenh(5, "ACB"))
    assert sla.chu_thich_o_so_lenh(ca_hai) == "gồm 2 lệnh lỗ giả do sự kiện quyền"
    mot = (_lenh(128, "TCB"), _lenh(5, "ACB"))
    assert sla.chu_thich_o_so_lenh(mot) == "gồm 1 lệnh lỗ giả do sự kiện quyền"
    assert sla.chu_thich_o_so_lenh((_lenh(5, "ACB"),)) is None
    assert sla.chu_thich_o_so_lenh(()) is None


def test_HAM_khop_CA_id_ma_va_ly_do_thoat():
    # đúng id nhưng khác mã, hoặc đúng cả hai nhưng không phải cắt lỗ → không gắn
    assert sla.chu_thich_o_so_lenh((_lenh(122, "TCB"),)) is None
    assert sla.chu_thich_o_so_lenh((_lenh(122, "HDB", "SIGNAL_REVERSED"),)) is None
    assert sla.chu_thich_o_so_lenh((_lenh(999, "HDB"),)) is None


def test_CAU_hau_kiem_chi_hien_cho_dung_lenh():
    lenh = (_lenh(122, "HDB"), _lenh(128, "TCB"), _lenh(5, "ACB"))
    assert sla.chu_thich_hau_kiem(122, lenh) == sla.CHU_THICH_HAU_KIEM
    assert sla.chu_thich_hau_kiem("128", lenh) == sla.CHU_THICH_HAU_KIEM   # sheet trả chuỗi
    assert sla.chu_thich_hau_kiem(5, lenh) is None
    assert sla.chu_thich_hau_kiem(None, lenh) is None
    assert sla.chu_thich_hau_kiem(122, ()) is None


def test_CHU_THICH_khong_in_so_da_loai():
    chu = [sla.CHU_THICH_O_SO_LENH, sla.CHU_THICH_HAU_KIEM,
           sla.chu_thich_o_so_lenh((_lenh(122, "HDB"), _lenh(128, "TCB"))) or ""]
    for c in chu:
        assert not re.search(r"\d+[.,]\d+", c), f"có số thập phân: {c!r}"
        assert "%" not in c, f"có phần trăm: {c!r}"
        for cam in ("7,95", "7.95", "đã loại", "without", "không có hai lệnh"):
            assert cam not in c.lower(), f"{cam!r} trong {c!r}"
    # ba hằng và hàm không đọc được thước đo: AST
    nguon = ast.parse((GOC / "so_lenh_app.py").read_text(encoding="utf-8"))
    ham = {n.name: n for n in nguon.body if isinstance(n, ast.FunctionDef)
           and n.name in ("lenh_lo_gia_trong_so", "chu_thich_o_so_lenh", "chu_thich_hau_kiem")}
    assert set(ham) == {"lenh_lo_gia_trong_so", "chu_thich_o_so_lenh", "chu_thich_hau_kiem"}
    cam_ten = {"compute", "Performance", "total_net_pct", "net_return_pct", "hieu_qua"}
    for ten, f in ham.items():
        dung = {n.id for n in ast.walk(f) if isinstance(n, ast.Name)} | \
               {n.attr for n in ast.walk(f) if isinstance(n, ast.Attribute)}
        assert not (dung & cam_ten), f"{ten} đụng vào thước đo: {dung & cam_ten}"


def _app() -> ast.Module:
    return ast.parse((GOC / "app.py").read_text(encoding="utf-8"))


def test_TOPBAR_o_so_lenh_net_mang_chu_thich():
    cay = _app()
    # (a) lời gọi tồn tại ở mức module
    goi = [n for n in ast.walk(cay) if isinstance(n, ast.Call)
           and isinstance(n.func, ast.Attribute) and n.func.attr == "chu_thich_o_so_lenh"]
    assert goi, "app.py không gọi chu_thich_o_so_lenh"
    # (b) chuỗi f nối ngầm của topbar gộp thành MỘT JoinedStr: tên chú thích phải có mặt trong nó
    topbar = [j for j in ast.walk(cay) if isinstance(j, ast.JoinedStr)
              and any(isinstance(v, ast.Constant) and isinstance(v.value, str)
                      and "Sổ lệnh (net)" in v.value for v in j.values)]
    assert topbar, "không tìm thấy ô Sổ lệnh (net)"
    ten = {n.id for j in topbar for n in ast.walk(j) if isinstance(n, ast.Name)}
    assert "_chu_thich_so_lenh_html" in ten, f"ô Sổ lệnh (net) không mang chú thích: {sorted(ten)}"


def test_KHOI_hau_kiem_hien_chu_thich_truoc_loi_B1():
    nguon = (GOC / "app.py").read_text(encoding="utf-8")
    cay = ast.parse(nguon)
    goi = [n for n in ast.walk(cay) if isinstance(n, ast.Call)
           and isinstance(n.func, ast.Attribute) and n.func.attr == "chu_thich_hau_kiem"]
    assert len(goi) == 1, "app.py phải gọi chu_thich_hau_kiem đúng một lần"
    # kết quả được HIỆN: có khối `if _ct_lo_gia:` mà thân gọi st.warning(_ct_lo_gia)
    hien = [n for n in ast.walk(cay) if isinstance(n, ast.If)
            and isinstance(n.test, ast.Name) and n.test.id == "_ct_lo_gia"
            and any(isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
                    and c.func.attr in ("warning", "caption", "info")
                    and any(isinstance(a, ast.Name) and a.id == "_ct_lo_gia" for a in c.args)
                    for s in n.body for c in ast.walk(s))]
    assert hien, "chú thích không được hiện bằng st.warning/caption/info"
    # đứng TRƯỚC lời B1: dòng của lời gọi < dòng `import hau_kiem_loi as _hkl_mod`
    dong_nhap = [n.lineno for n in ast.walk(cay) if isinstance(n, ast.Import)
                 and any(a.name == "hau_kiem_loi" for a in n.names)]
    assert dong_nhap and goi[0].lineno < min(dong_nhap), "chú thích phải đứng trước lời B1"


def test_NGUYEN_NHAN_viet_tu_ma_la_co_that():
    """Câu nói tới phép so `low <= sl` ở `_lenh_dat_san`: nó phải CÓ trong hàm ấy (AST)."""
    cay = ast.parse((GOC / "paper_trading.py").read_text(encoding="utf-8"))
    ham = next(n for n in ast.walk(cay)
               if isinstance(n, ast.FunctionDef) and n.name == "_lenh_dat_san")
    so = [c for c in ast.walk(ham) if isinstance(c, ast.Compare)
          and isinstance(c.left, ast.Name) and c.left.id == "low"
          and isinstance(c.ops[0], ast.LtE)
          and isinstance(c.comparators[0], ast.Name) and c.comparators[0].id == "sl"]
    assert so, "`low <= sl` không còn trong _lenh_dat_san — sửa câu chú thích cho khớp mã"
    assert "low <= sl" in (GOC / "so_lenh_app.py").read_text(encoding="utf-8")
