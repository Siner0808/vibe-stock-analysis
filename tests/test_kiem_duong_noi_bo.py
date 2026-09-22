"""Gác cho phép dò đường giao dịch nội bộ.

Phép dò này kết luận một điều PHỦ ĐỊNH — *"đường này không trả dữ liệu"* —
và một kết luận phủ định chỉ đọc được khi phép đo CÓ KHẢ NĂNG cho kết quả
dương (lỗi 66). Nên thứ phải khoá chặt nhất ở đây là **ô đối chứng**: bỏ
nó đi thì *"nguồn không có dữ liệu"* và *"tôi không có quyền truy cập"*
trông y hệt nhau.

Không phép kiểm nào ở đây chạm mạng.
"""
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))

import kiem_duong_noi_bo as K  # noqa: E402


def _dc(so_co: int) -> dict:
    """Đối chứng: `so_co` endpoint khác CÓ dữ liệu."""
    return {t: {"so_dong": (5 if i < so_co else 0), "loi": ""}
            for i, t in enumerate(K.DOI_CHUNG)}


def _ro(co: int, tong: int = 71) -> dict:
    return {"co": co, "rong": tong - co, "hong": 0, "tong": tong}


# ── Ô ĐỐI CHỨNG: vế khiến một kết luận PHỦ ĐỊNH đọc được ──────────────

def test_DOI_CHUNG_AM_thi_CHUA_KIEM_DUOC_chu_KHONG_phai_KHONG_CO_DU_LIEU():
    """Đây là ca nguy hiểm nhất, và nó có tiền lệ thật.

    `vnstock_pipeline` từng bị KHOÁ ở hạng silver trong khi
    `license/verify` vẫn liệt kê nó. Một đường bị khoá trả về đúng cùng
    hình dạng với một đường không có dữ liệu. Không tách được thì con số
    0 nói về QUYỀN TRUY CẬP chứ không nói về DỮ LIỆU.
    """
    ma, cau = K.phan_dinh(_ro(0), _dc(0))
    assert ma == 2, cau
    assert "CHUA KIEM DUOC" in cau
    assert "QUYEN TRUY CAP" in cau


def test_DOI_CHUNG_DUONG_dat_thi_con_so_0_MOI_doc_duoc():
    ma, cau = K.phan_dinh(_ro(0), _dc(3))
    assert ma == 1, cau
    assert "KHONG TRA DU LIEU" in cau and "DOC DUOC" in cau


def test_MOT_endpoint_doi_chung_la_DU_de_doc_duoc():
    """Ngưỡng là 'có ít nhất một', không phải 'tất cả'."""
    ma, _ = K.phan_dinh(_ro(0), _dc(1))
    assert ma == 1


def test_CO_DU_LIEU_thi_bao_CO_du_doi_chung_the_nao():
    for so_dc in (0, 2, 4):
        ma, cau = K.phan_dinh(_ro(5), _dc(so_dc))
        assert ma == 0, (so_dc, cau)
        assert "CO TRA DU LIEU" in cau


# ── `_so_dong`: 0 và "không đếm được" là hai kết luận NGƯỢC nhau ──────

def test_KHONG_DEM_DUOC_phai_la_None_chu_khong_phai_0():
    assert K._so_dong(None) is None
    assert K._so_dong(object()) is None
    assert K._so_dong([]) == 0
    assert K._so_dong([1, 2]) == 2


# ── Quần thể nguồn và đối chứng: suy ra, đừng gõ ──────────────────────

def test_HOI_HET_BON_NGUON_chu_khong_doan_nguon_nao_co():
    """Đoán một nguồn rồi kết luận về cả API là đọc rộng hơn phạm vi."""
    assert set(K.NGUON) == {"VCI", "KBS", "ASEAN", "CAFEF"}


def test_DOI_CHUNG_khong_duoc_RONG():
    """Một danh sách đối chứng rỗng làm mọi kết quả 0 thành 'chưa kiểm được'
    — nghe thì an toàn, nhưng nó giết luôn khả năng kết luận."""
    assert len(K.DOI_CHUNG) >= 2
    assert K.DICH not in K.DOI_CHUNG, "doi chung khong duoc la CHINH dich"


def test_PHAN_DINH_khong_gop_HAI_trang_thai_cuoi():
    """Ba mã thoát phải THẬT SỰ khác nhau trên ba ca khác nhau."""
    ma = {K.phan_dinh(_ro(5), _dc(4))[0],
          K.phan_dinh(_ro(0), _dc(4))[0],
          K.phan_dinh(_ro(0), _dc(0))[0]}
    assert ma == {0, 1, 2}, ma
