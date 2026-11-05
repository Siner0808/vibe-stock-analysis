"""Sơ đồ "Một ngày của agent" trong README: hai tệp SVG phải khớp nguồn sinh.

VÌ SAO CÓ FILE NÀY (BƯỚC 186, 13/10/2026)
──────────────────────────────────────────
Sơ đồ được SINH bởi `tools/ve_so_do_mot_ngay.py` (nhãn đọc từ mã đang chạy:
`run_daily.execute_daily_scan`, `paper_runner.run_session`,
`PaperTradingJournal.consider_entry`). Có hai tệp — nền sáng và nền tối — nên
sửa tay một tệp là cách nhanh nhất để hai bản nói hai điều khác nhau. Nguồn sự
thật là hàm `ve()`; gác này đòi từng byte của tệp trên đĩa bằng đầu ra của nó,
và đòi README trỏ đúng hai tệp qua `<picture>`.
"""
from __future__ import annotations

import ast
import sys
import xml.dom.minidom
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))

import ve_so_do_mot_ngay as vs  # noqa: E402


def test_HAI_TEP_SVG_khop_tung_byte_voi_ham_ve():
    for nen, ten in vs.TEN.items():
        tren_dia = (vs.THU_MUC / ten).read_text(encoding="utf-8")
        assert tren_dia == vs.ve(nen), (
            f"{ten} lệch hàm ve('{nen}') — sửa nhãn trong tools/ve_so_do_mot_ngay.py "
            f"rồi chạy lại nó, đừng sửa SVG tay")


def test_SVG_hop_le_va_co_nhan_cho_nguoi_khong_nhin_duoc():
    for nen in vs.TEN:
        goc = xml.dom.minidom.parseString(vs.ve(nen).encode("utf-8")).documentElement
        assert goc.tagName == "svg"
        assert goc.getAttribute("role") == "img"
        assert "7 cổng" in goc.getAttribute("aria-label")


def test_HAI_BAN_chi_khac_MAU_khong_khac_NOI_DUNG():
    """Bản tối = bản sáng với bảng màu khác — không nhãn nào chỉ có ở một bản."""
    sang, toi = vs.ve("sang"), vs.ve("toi")
    for a, b in zip(vs.MAU["sang"].values(), vs.MAU["toi"].values()):
        sang = sang.replace(a, "#MAU")
        toi = toi.replace(b, "#MAU")
    assert sang == toi


def test_README_tro_dung_hai_tep_qua_picture():
    readme = (GOC / "README.md").read_text(encoding="utf-8")
    assert "<picture>" in readme
    assert f'srcset="docs/hinh/{vs.TEN["toi"]}"' in readme
    assert 'media="(prefers-color-scheme: dark)"' in readme
    assert f'src="docs/hinh/{vs.TEN["sang"]}"' in readme


def _hang_chuoi(duong: Path, ten: str) -> str:
    """Giá trị chuỗi của phép gán cấp module `ten = "..."` — đọc bằng AST. KHÔNG `import sheets_store`:
    `tools/` đứng trước gốc repo trên `sys.path` của file này và có `hau_kiem_loi.py` trùng tên module gốc."""
    cay = ast.parse(duong.read_text(encoding="utf-8"))
    for n in cay.body:
        if (isinstance(n, ast.Assign) and len(n.targets) == 1
                and isinstance(n.targets[0], ast.Name) and n.targets[0].id == ten):
            return ast.literal_eval(n.value)
    raise AssertionError(f"không thấy {ten} ở cấp module của {duong.name}")


def _goi_tab(duong: Path, ten_ham: str, thuoc_tinh: str) -> set[tuple[str, str | None]]:
    """{(tên hằng tab, tên biến đối số thứ hai hoặc None)} của mọi lời gọi
    `<x>.<thuoc_tinh>(TAB_*, ...)` trong hàm `ten_ham` — đọc bằng AST, không bằng `in`."""
    cay = ast.parse(duong.read_text(encoding="utf-8"))
    ham = next(n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == ten_ham)
    ra: set[tuple[str, str | None]] = set()
    for n in ast.walk(ham):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == thuoc_tinh and n.args and isinstance(n.args[0], ast.Name)):
            hai = n.args[1].id if len(n.args) > 1 and isinstance(n.args[1], ast.Name) else None
            ra.add((n.args[0].id, hai))
    return ra


def test_NHAN_day_so_khop_cach_ghi_that_cua_sheets_store():
    """BƯỚC 255: nhãn cũ "chỉ thêm dòng mới" SAI — `trades` và `nhat_ky` soi gương toàn phần
    (`write_all`), chỉ `decisions` và `ke_hoach` thêm dòng (`append_rows`). Đọc `push` bằng AST."""
    ds = GOC / "sheets_store.py"
    ghi_de = _goi_tab(ds, "push", "write_all")
    assert ("TAB_TRADES", "bang_trades") in ghi_de, ghi_de
    assert ("TAB_NHAT_KY", "bang_nk") in ghi_de, ghi_de
    assert ("TAB_DECISIONS", None) in _goi_tab(ds, "push", "append_rows")
    assert any(t == "TAB_KE_HOACH" for t, _ in _goi_tab(ds, "_day_ke_hoach", "append_rows"))
    for nen in vs.TEN:
        van = vs.ve(nen)
        assert "thêm: quyết định, kế hoạch" in van
        assert "soi gương: lệnh, nhật ký" in van
        assert "chỉ thêm dòng mới" not in van


def test_SO_DO_co_hop_hau_kiem_B1_ghi_dung_tab_va_do_workflow_rieng_ghi():
    """BƯỚC 255: hộp B1 gọi tên tab LẤY TỪ `sheets_store.TAB_HAU_KIEM`, và đường ghi thật là
    `sheets_store.them_hau_kiem` gọi từ `tools/hau_kiem_loi.py` (không phải `push`)."""
    for nen in vs.TEN:
        van = vs.ve(nen)
        assert f"tab {_hang_chuoi(GOC / 'sheets_store.py', 'TAB_HAU_KIEM')}" in van
        assert "Hậu kiểm bằng lời" in van
    cay = ast.parse((GOC / "tools" / "hau_kiem_loi.py").read_text(encoding="utf-8"))
    goi = {n.func.attr for n in ast.walk(cay)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert "them_hau_kiem" in goi
    assert not any(t == "TAB_HAU_KIEM" for t, _ in
                   _goi_tab(GOC / "sheets_store.py", "push", "write_all")
                   | _goi_tab(GOC / "sheets_store.py", "push", "append_rows"))
