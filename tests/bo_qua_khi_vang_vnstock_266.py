"""BƯỚC 266 — ngoại lệ TẠM: bỏ qua test CẦN `vnstock` đang cài khi `vnstock` không nạp được.

VÌ SAO CÓ FILE NÀY
──────────────────
Từ 10/11/2026 kho hãng `vnstocks.com/api/simple` trả HTTP 410 cho `vnstock` và
`vnai`, nên `pip install -r requirements.txt` chết ở `vnstock==4.0.9` và mọi PR
đỏ ở `kiem-dinh`. Người dùng chọn 11/11/2026 *"Bỏ tạm vnstock khỏi CI
(Recommended)"*: `kiem-dinh.yml` cài mọi thư viện trừ các dòng vnstock/vnai, và
các test cần vnstock đang cài bỏ qua CÓ LÝ DO GHI RÕ, CÓ HẠN GỠ. Ở máy vẫn chạy đủ.

NGOẠI LỆ NÀY KHÔNG ĐƯỢC SỐNG LÂU HƠN NGUYÊN NHÂN CỦA NÓ
────────────────────────────────────────────────────────
Gác `tests/test_bo_qua_khi_vang_vnstock_266.py` giữ ba điều, đều bằng máy:
  1. `DANH_SACH_BO_QUA` khớp ĐÚNG tập test mang dấu `can_vnstock_dang_cai` (AST);
  2. điều kiện bỏ qua CHỈ là "vnstock không nạp được" (AST của dòng dưới);
  3. ĐỎ khi `requirements.txt` không còn ghim `GHIM_NGOAI_LE` mà danh sách còn
     phần tử — tức BƯỚC 265 (vnstock 6) đã vào, ngoại lệ phải gỡ CÙNG LÚC.

Chỉ dùng dấu này làm decorator của hàm test ở mức module. KHÔNG `pytestmark`,
KHÔNG gán sang tên khác: gác (1) báo mọi chỗ dùng lạ.
"""
import importlib.util

import pytest

#: Lý do hiện ở `pytest -rs`. Phải nêu BƯỚC 266 và hạn gỡ (gác kiểm hai cụm ấy).
LY_DO = ("BƯỚC 266: vnstock không cài được trên CI (kho hãng đóng 10/11/2026) — "
         "test này cần vnstock/vnai đang cài; gỡ khi BƯỚC 265 vào")

#: Bản ghim mà ngoại lệ này sinh ra để chịu. Đổi ghim (BƯỚC 265) thì gác ĐỎ.
GHIM_NGOAI_LE = "vnstock==4.0.9"

#: Mọi test mang dấu bên dưới, dạng `tests/<file>::<hàm>`. Thêm dấu mà không khai ở đây
#: (hoặc ngược lại) thì gác ĐỎ.
#: BƯỚC 267 (11/11/2026): RỖNG. `requirements.txt` không còn `vnstock==4.0.9` (hãng gỡ gói), ba test cần
#: vnstock/vnai đang cài đã bị XOÁ (một ở `test_requirements.py`, hai ở `test_no_fabricated_data.py` và
#: `test_vnstock_goi.py`), nên không còn test nào mang dấu. Gác `test_bo_qua_khi_vang_vnstock_266.py` xanh vì
#: danh sách rỗng VÀ không test nào mang dấu — không phải vì nó bị tắt. Dấu và gác giữ lại cho BƯỚC 265.
DANH_SACH_BO_QUA = frozenset()

can_vnstock_dang_cai = pytest.mark.skipif(importlib.util.find_spec("vnstock") is None, reason=LY_DO)
