"""Gác BẢNG VÀNG của một phiên giao dịch giấy (BƯỚC 239, Lát 1 của C1).

Lát 1 đổi CÁCH bộ máy nhận cờ (tham số/cấu hình thay vì biến module) và gom thứ tự bốn bước
của một phiên về MỘT hàm — mà hành vi phải giữ NGUYÊN TỪNG BIT. Test này là bằng chứng:
nó chạy lại đúng kịch bản của `tools/sinh_bang_vang_phien.py` (mười mã, 95 phiên, mười bốn
cấu hình cờ, toàn bộ bộ máy thật: khớp, trượt giá, bước giá, lô chẵn, khoá biên, trần vốn,
cắt lỗ, trailing) và đòi từng ô khớp với `tests/du_lieu/bang_vang_phien.json`.

File JSON được sinh bằng mã TRƯỚC khi sửa (`main` `09f7980`); lệnh sinh ở docstring của
`tools/sinh_bang_vang_phien.py`. Đừng sinh lại để làm test xanh: một ô đổi là hành vi đổi.

Hai đường vào, cùng một bảng:
  • "module"   — cờ đặt bằng GÁN BIẾN MODULE (như `tools/do30_nghi_sau_lo.py`…): khoá việc ĐỌC
                CỜ LÚC GỌI;
  • "cau_hinh" — module giữ mặc định, cờ đi qua `CauHinhVao` truyền vào `run_session`: khoá
                việc KHÔNG CÒN ĐỌC cờ module ở chỗ nào bên trong bộ máy.
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
# `tools` ở CUỐI đường tìm: `tools/cham_xac_nhan.py` cùng tên với module gốc, đứng trước là
# làm test nạp sau (test_keo_bang_gia) nhập nhầm dụng cụ thay vì module.
sys.path.append(str(GOC / "tools"))

import sinh_bang_vang_phien as S  # noqa: E402

BANG = json.loads((Path(__file__).resolve().parent / "du_lieu" / "bang_vang_phien.json")
                   .read_text(encoding="utf-8"))
TEN = sorted(BANG["kich_ban"])


@pytest.fixture(scope="module")
def gia():
    return S.dung_gia()


def _sai_khac(ten: str, kq: dict, ky_vong: dict) -> str | None:
    """Mô tả ô ĐẦU TIÊN khác nhau, hoặc None nếu bằng nhau."""
    for khoa in ("lenh", "quyet_dinh_khac_diem_thap", "buoc"):
        a, b = kq[khoa], ky_vong[khoa]
        for i in range(max(len(a), len(b))):
            x = a[i] if i < len(a) else "<hết>"
            y = b[i] if i < len(b) else "<hết>"
            if x != y:
                return f"{ten}/{khoa}[{i}]: chạy ra {x} · bảng vàng {y}"
    for khoa in ("so_quyet_dinh", "bam_quyet_dinh"):
        if kq[khoa] != ky_vong[khoa]:
            return f"{ten}/{khoa}: chạy ra {kq[khoa]} · bảng vàng {ky_vong[khoa]}"
    return None


def test_bang_vang_co_du_kich_ban():
    assert TEN == sorted(S.KICH_BAN), "kịch bản của công cụ lệch bảng vàng"
    assert len(TEN) >= 14


@pytest.mark.parametrize("ten", TEN)
def test_duong_MODULE_khop_bang_vang(ten, gia):
    kq = S.chay_kich_ban(ten, "module", gia)
    sai = _sai_khac(ten, kq, BANG["kich_ban"][ten])
    assert sai is None, sai


def _gan_trong_nguon(ten: str):
    cay = ast.parse((GOC / "paper_trading.py").read_text(encoding="utf-8"))
    return [n.value.value for n in cay.body if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == ten for t in n.targets)]


def test_MAC_DINH_trong_NGUON_khop_bang_vang():
    """Đọc NGUỒN bằng AST (test khác có thể đã đặt cờ lúc chạy): mỗi cờ gán MỘT lần ở mức
    module, bằng đúng giá trị bảng vàng ghi lúc sinh. Đổi một mặc định → ĐỎ."""
    sai = {}
    for co, gia_tri in BANG["co_mac_dinh"].items():
        gan = _gan_trong_nguon(co)
        if gan != [gia_tri] or type(gan[0]) is not type(gia_tri):
            sai[co] = (gan, gia_tri)
    assert not sai, f"mặc định trong nguồn lệch bảng vàng: {sai}"
    assert sorted(BANG["co_mac_dinh"]) == sorted(S.CO)


def test_bang_vang_CHAM_du_cac_nhanh_can_canh():
    """Bảng không rỗng ở chỗ nó định canh: một kịch bản không chạm nhánh nào thì không canh nhánh đó."""
    dem = S.phu(BANG["kich_ban"])
    for ly_do in ("VN-INDEX nằm dưới", "chất lượng dữ", "chốt sụt giảm", "lọc IMOM nhóm",
                  "nghỉ sau lệnh", "thiếu stop-loss/take-profit", "độ rộng thị", "ô C5 ĐÓNG",
                  "vốn cam kết"):
        assert dem["ly_do_bo"].get(ly_do), f"bảng vàng không có lệnh nào bị chặn bởi {ly_do!r}"
    for ly_do_ra in ("STOP_LOSS", "SIGNAL_REVERSED", "MAX_HOLD", "TAKE_PROFIT"):
        assert dem["ly_do_ra"].get(ly_do_ra), f"bảng vàng không có lệnh nào ra bằng {ly_do_ra}"
    assert dem["trang_thai"].get("HUY"), "bảng vàng không có lệnh chờ bị huỷ (kịch trần một giá)"
    mac_dinh = BANG["kich_ban"]["mac_dinh"]
    assert len(mac_dinh["lenh"]) >= 10
    lenh_dong_c5 = BANG["kich_ban"]["dong_cong_c5"]["lenh"]
    assert lenh_dong_c5 == [], "ô C5 đóng mà vẫn có lệnh"
