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
