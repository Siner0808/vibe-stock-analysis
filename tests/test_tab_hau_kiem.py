"""Tab Sheets `hau_kiem` của B1 (BƯỚC 204) — CHỈ THÊM, khoá (`trade_id`, `lan`).

`sheets_store.them_hau_kiem` / `doc_hau_kiem` trên `InMemorySheet` (mọi ô là chuỗi):
tiêu đề ghi khi tab rỗng, vòng ghi–đọc giữ đúng kiểu, khoá trùng thì từ chối và KHÔNG
ghi gì, tiêu đề lệch thì nổ như mọi tab khác.
"""
from __future__ import annotations

import pytest

import hau_kiem_loi as hk
import sheets_store as ss


def _dong(**doi) -> dict:
    d = {c: None for c in hk.COT_HAU_KIEM}
    d.update({"trade_id": 125, "lan": 1, "symbol": "HPG", "exit_date": "2026-10-09",
              "trang_thai": hk.TT_DAT, "ke_lai": "Lệnh HPG lỗ 5,21%.",
              "khong_chung_minh": "Một lệnh chưa chứng minh được gì.",
              "theo_doi": "Chưa kiểm: gap.", "kien_thuc": "Gap là …",
              "model_yeu_cau": hk.MODEL, "model_phuc_vu": hk.MODEL, "effort": hk.EFFORT,
              "bam_loi_dan": "abc", "bam_du_kien": "def", "token_vao": 2000,
              "token_ra": 1500, "chi_phi_usd_uoc": 0.0475, "stop_reason": "end_turn",
              "viet_luc": "2026-10-26T18:20:00"})
    d.update(doi)
    return d


def test_LUOC_DO_tab_suy_tu_module_thuan():
    assert ss.HAU_KIEM_COLS == hk.COT_HAU_KIEM
    assert ss.TAB_HAU_KIEM == "hau_kiem"


def test_THEM_ghi_tieu_de_khi_tab_rong_va_doc_lai_dung_kieu():
    b = ss.InMemorySheet()
    assert ss.doc_hau_kiem(b) == []
    assert ss.them_hau_kiem(b, [_dong(), _dong(lan=2, trang_thai=hk.TT_BI_BAC, ly_do_bac="x",
                                               ke_lai=None)]) == 2
    assert b.tabs[ss.TAB_HAU_KIEM][0] == list(hk.COT_HAU_KIEM)
    doc = ss.doc_hau_kiem(b)
    assert doc[0] == _dong()
    assert doc[1]["ke_lai"] is None and doc[1]["lan"] == 2
    assert isinstance(doc[0]["token_vao"], int) and isinstance(doc[0]["chi_phi_usd_uoc"], float)


def test_KHOA_TRUNG_tren_tab_hay_trong_lo_thi_TU_CHOI_va_khong_ghi_gi():
    b = ss.InMemorySheet()
    ss.them_hau_kiem(b, [_dong()])
    truoc = [list(r) for r in b.tabs[ss.TAB_HAU_KIEM]]
    with pytest.raises(ss.SheetError):
        ss.them_hau_kiem(b, [_dong(lan=2), _dong(lan=1)])
    with pytest.raises(ss.SheetError):
        ss.them_hau_kiem(b, [_dong(lan=3), _dong(lan=3)])
    assert b.tabs[ss.TAB_HAU_KIEM] == truoc


def test_TIEU_DE_LECH_thi_NO():
    b = ss.InMemorySheet()
    b.write_all(ss.TAB_HAU_KIEM, [list(hk.COT_HAU_KIEM[::-1])])
    with pytest.raises(ss.SheetSchemaError):
        ss.them_hau_kiem(b, [_dong()])
    with pytest.raises(ss.SheetSchemaError):
        ss.doc_hau_kiem(b)


def test_THEM_rong_khong_cham_tab():
    b = ss.InMemorySheet()
    assert ss.them_hau_kiem(b, []) == 0
    assert ss.TAB_HAU_KIEM not in b.tabs
