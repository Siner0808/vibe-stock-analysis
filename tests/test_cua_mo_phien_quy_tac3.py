"""Bản tin mở phiên nói đúng LUẬT MỚI — BƯỚC 164 (giai đoạn A3, đột biến lô B).

`tools/cua_mo_phien.py` in ra, mỗi lần mở phiên, ai còn nợ sổ tay và nhịp soát. Sau
khi Quy tắc 3 thu hẹp (người dùng "Đồng ý" 08/10/2026) nó phải nói luật MỚI chứ không
nhắc "mỗi BƯỚC phải HỎI". Phần mới thêm ở BƯỚC 164 không có gác nào: tám đột biến lô B
(đọc sai khoá mốc, đảo nhánh, đổi `>=` thành `>`, gõ cứng 164…) cùng sống sót. Các ca
dưới đây ép từng chỗ ấy.

Mỗi ca thay các hàm đọc đĩa bằng giá trị cho trước (`monkeypatch`), nên chúng không
phụ thuộc trạng thái thật của sổ hôm nay — chỉ phụ thuộc cách `ban_tin()` ráp câu.
"""
import datetime as dt
import json
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))

import cua_mo_phien as mp  # noqa: E402
import moc_lo_trinh  # noqa: E402

HOM_NAY = dt.date(2026, 10, 20)


@pytest.fixture
def ban(monkeypatch):
    """Dựng `ban_tin()` trên đầu vào cho trước; trả hàm `(**ghi_de) -> list[str]` dòng."""
    mac_dinh = dict(
        ten_skill=lambda: ["quy-trinh-lam-viec"],
        trang_thai_cua=lambda: "CUA: 7/7 song",
        dong_moc_lo_trinh=lambda: "MỐC: dong mau",
        buoc_chua_khai_soat=lambda: [],
        ngay_tu_lan_soat_quy_trinh=lambda hom_nay=None: 0,
        chuoi_khong_soat=lambda so=None: [],
        moc_bat_buoc_hoi=lambda: 108,
        moc_chi_hoi_khi_doi_luat=lambda: 164,
        moc_ngay_con_chan=lambda hom_nay=None: [],
    )

    def dung(**ghi_de):
        for ten, f in {**mac_dinh, **ghi_de}.items():
            monkeypatch.setattr(mp, ten, f)
        return mp.ban_tin(HOM_NAY).splitlines()
    return dung


# ── đọc mốc thu hẹp từ sổ ────────────────────────────────────────────────────

def _so_tam(tmp_path, monkeypatch, noi_dung):
    p = tmp_path / "soat.json"
    p.write_text(json.dumps(noi_dung), encoding="utf-8")
    monkeypatch.setattr(mp, "SO_SOAT", p)


def test_MOC_THU_HEP_doc_dung_khoa_va_khong_nham_voi_moc_cu(tmp_path, monkeypatch):
    _so_tam(tmp_path, monkeypatch, {"_moc_chi_hoi_khi_doi_luat": 164, "_moc_bat_buoc_hoi": 108})
    assert mp.moc_chi_hoi_khi_doi_luat() == 164
    assert mp.moc_bat_buoc_hoi() == 108


@pytest.mark.parametrize("gia_tri", [True, "164", 164.0, None])
def test_MOC_THU_HEP_khong_phai_so_nguyen_thi_NONE_khong_doan(tmp_path, monkeypatch, gia_tri):
    """`True` là một `int` của Python: không lọc nó thì mốc thành 1 và luật áp từ BƯỚC 1."""
    _so_tam(tmp_path, monkeypatch, {"_moc_chi_hoi_khi_doi_luat": gia_tri})
    assert mp.moc_chi_hoi_khi_doi_luat() is None


def test_MOC_THU_HEP_so_vang_hay_hong_thi_NONE_chu_khong_no(tmp_path, monkeypatch):
    monkeypatch.setattr(mp, "SO_SOAT", tmp_path / "khong_co.json")
    assert mp.moc_chi_hoi_khi_doi_luat() is None
    _so_tam(tmp_path, monkeypatch, {"khoa_khac": 1})
    assert mp.moc_chi_hoi_khi_doi_luat() is None


# ── dòng nhắc Mốc ────────────────────────────────────────────────────────────

def test_DONG_MOC_doc_so_BUOC_tu_moc_lo_trinh_khong_go_cung(monkeypatch):
    monkeypatch.setattr(moc_lo_trinh, "TU_BUOC", 777)
    dong = mp.dong_moc_lo_trinh()
    assert dong and "777" in dong and "164" not in dong, dong
    assert "**Mốc:**" in dong and "docs/LO-TRINH.md" in dong


def test_BAN_TIN_co_dong_Moc_khi_doc_duoc_va_khong_co_khi_khong(ban):
    assert any("MỐC: dong mau" in d for d in ban())
    assert not any("MỐC" in d for d in ban(dong_moc_lo_trinh=lambda: None))


# ── ba nhánh của lời nhắc nợ sổ tay ──────────────────────────────────────────

NO = lambda: ["BƯỚC 170", "BƯỚC 171"]  # noqa: E731


def test_NO_SO_TAY_khi_co_ca_hai_moc_noi_LUAT_MOI(ban):
    van = "\n".join(ban(buoc_chua_khai_soat=NO))
    assert "SOÁT CHÉO còn nợ 2: BƯỚC 170 · BƯỚC 171" in van
    assert "BƯỚC >= 164 chạm file luật → phải HỎI thật" in van
    assert "khong_bat_buoc_vi" in van and "tools/buoc_cham_luat.py" in van
    assert "BƯỚC 108..163: vẫn mỗi BƯỚC phải HỎI" in van      # hep - 1, không phải hep
    assert "PHÁT HIỆN, không" not in van


def test_NO_SO_TAY_thieu_moc_thu_hep_thi_noi_luat_CU(ban):
    van = "\n".join(ban(buoc_chua_khai_soat=NO, moc_chi_hoi_khi_doi_luat=lambda: None))
    assert "từ BƯỚC 108 mỗi BƯỚC phải HỎI (quy tắc 3)" in van
    assert "khong_bat_buoc_vi" not in van and "BƯỚC >=" not in van


def test_NO_SO_TAY_thieu_ca_hai_moc_thi_noi_chung(ban):
    van = "\n".join(ban(buoc_chua_khai_soat=NO, moc_bat_buoc_hoi=lambda: None,
                        moc_chi_hoi_khi_doi_luat=lambda: 164))
    assert "phát hiện, hoặc lý do" in van
    assert "khong_bat_buoc_vi" not in van


def test_KHONG_no_thi_khong_co_dong_SOAT_CHEO(ban):
    assert not any("SOÁT CHÉO" in d for d in ban())


# ── nhịp soát: đúng ranh giới ────────────────────────────────────────────────

def test_NHAC_SOAT_QUY_TRINH_tu_dung_NHIP_tro_di(ban):
    nhip = mp.NHIP_SOAT_NGAY
    van = "\n".join(ban(ngay_tu_lan_soat_quy_trinh=lambda hom_nay=None: nhip))
    assert f"SOÁT QUY TRÌNH: lần gần nhất {nhip} ngày trước (nhịp {nhip} ngày)" in van
    assert "soat-tuan" in van
    van = "\n".join(ban(ngay_tu_lan_soat_quy_trinh=lambda hom_nay=None: nhip - 1))
    assert "SOÁT QUY TRÌNH" not in van


def test_CHUA_doc_duoc_lan_soat_thi_im_lang_khong_bao_vua_soat(ban):
    assert not any("SOÁT QUY TRÌNH" in d for d in
                   ban(ngay_tu_lan_soat_quy_trinh=lambda hom_nay=None: None))
