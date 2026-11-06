"""Mô hình khớp lệnh GIỚI HẠN MUA của kế hoạch vào lệnh B6 — hàm THUẦN dùng chung (BƯỚC 257, Lát 4 của C1).

`docs/thiet-ke-c1-san-dau.md` mục 7: mô hình khớp của ĐO 25 (`tools/do25_ke_hoach_vao_lenh.py`, kết cục B, BƯỚC 179)
được chuyển ra đây để sân đấu (PB-003) và phép đo thăm dò dùng CHUNG một định nghĩa "khớp nghiêm":

  · lệnh giới hạn mua ở `tran_vnd` (trần của vùng chờ), hiệu lực `so_phien_cho` phiên kể từ phiên SAU ngày tín hiệu;
  · khớp ở phiên đầu tiên có `low` ≤ trần TRỪ MỘT bước giá (`cham=True`: `low` ≤ trần — biến thể "chạm là khớp"
    của ĐO 25, chỉ để báo kèm);
  · giá khớp cơ sở = `min(open, trần)`; bước giá lấy ở MỨC GIÁ CỦA TRẦN, `truot_gia.buoc_gia(trần, sàn)`.

KHÔNG nhập `ke_hoach_vao_lenh`: module ấy CHỈ ĐỂ HIỆN và chỉ ba nơi được nhập nó (`tests/test_ke_hoach_vao_lenh.py`,
`CHO_PHEP_NHAP`). Vì thế `so_phien_cho` là THAM SỐ, không đọc `SO_PHIEN_CHO` ở đây: dụng cụ ĐO 25 truyền
`ke_hoach_vao_lenh.SO_PHIEN_CHO`, sân đấu truyền cột `so_phien_cho` của dòng `ke_hoach` đã ghi lúc quét.

Hàm thuần: không mạng, không đĩa, không đồng hồ. Mọi giá đưa vào là VNĐ.
"""
from __future__ import annotations

from typing import Optional

import truot_gia

#: Bốn phán quyết của kế hoạch vào lệnh (`ke_hoach_vao_lenh.MUA_NGAY` … — một test giữ cho chúng bằng nhau).
MUA_NGAY = "MUA_NGAY"
CHO_VUNG = "CHO_VUNG"
BO_QUA = "BO_QUA"
CHUA_LAP_DUOC = "CHUA_LAP_DUOC"
PHAN_QUYET = (MUA_NGAY, CHO_VUNG, BO_QUA, CHUA_LAP_DUOC)


def khop_mot_phien(mo_vnd: float, thap_vnd: float, tran_vnd: float, san: str,
                   cham: bool = False) -> tuple[bool, Optional[float]]:
    """Lệnh giới hạn mua ở `tran_vnd` có khớp trong MỘT phiên (mở `mo_vnd`, thấp nhất `thap_vnd`) không.

    Trả `(True, giá khớp cơ sở)` hay `(False, None)`. So sánh sau khi làm tròn 6 chữ số: `16,1 × 1000` ra
    `16100,000000000002` trong số thực, và so thẳng thì một phiên chạm đúng ngưỡng bị coi là lỡ.
    """
    nguong = tran_vnd if cham else tran_vnd - truot_gia.buoc_gia(tran_vnd, san)
    if round(float(thap_vnd), 6) <= nguong:
        return True, min(round(float(mo_vnd), 6), float(tran_vnd))
    return False, None


def tim_khop(df, t: int, tran_vnd: float, san: str, he_so: float, *, so_phien_cho: int,
             cham: bool = False):
    """Khớp ở phiên d ∈ [t + 1, t + `so_phien_cho`] đầu tiên (`df` có cột `open`, `low`; `he_so` quy về VNĐ).

    Trả `(d, giá khớp VNĐ)` hoặc `None` (lỡ). Cửa sổ KHÔNG gồm hàng t và bị cắt ở hàng cuối của `df`.
    """
    cuoi = min(t + so_phien_cho, len(df) - 1)
    for d in range(t + 1, cuoi + 1):
        khop, gia = khop_mot_phien(float(df["open"].iloc[d]) * he_so, float(df["low"].iloc[d]) * he_so,
                                   tran_vnd, san, cham)
        if khop:
            return d, gia
    return None
