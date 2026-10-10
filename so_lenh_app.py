"""Sổ lệnh THẬT cho tab "Vị thế" và "Lịch sử giao dịch" của app (BƯỚC 175).

Sổ thật nằm trên Google Sheets; `paper_trades.db` ở máy đứng yên từ 20/08/2026
(`CLAUDE.md`, mục sổ lệnh giấy). Bản cũ của `app.py` mở tệp ấy nên ở máy hiện vị
thế của sổ CŨ, còn trên Streamlit Cloud (nơi `*.db` bị `.gitignore` chặn) thì báo
"không tìm thấy" — cả hai nơi người dùng đều không thấy vị thế thật.

Module THUẦN, CHỈ ĐỌC: nhận dict `{"quyet_dinh", "lenh", "nhat_ky"}` do
`google_sheets_sync.load_so_ban_tin_from_google_sheets` trả (hoặc `None` nghĩa là
kho ngoài CHƯA cấu hình) và trả một `SoLenhApp` đóng băng. Không mạng, không đĩa,
không đồng hồ, không mở `PaperTradingJournal`, không ghi sổ.

Hai luật đọc (đều khớp cách sổ đang lọc, đọc từ `app.py` cũ, không đoán):
· Vị thế MỞ = `OPEN` · `PENDING` · `CLOSING`.
· Lệnh ĐÓNG cho thống kê = `CLOSED`. `HUY` (lệnh chờ không khớp được) không phải
  một giao dịch nên KHÔNG thuộc nhóm nào (`paper_trading.Status.HUY`).

Kho chưa cấu hình thì `loi` nói đúng điều đó và mọi danh sách rỗng — KHÔNG rơi về
sổ ở máy và KHÔNG dựng danh sách thay thế.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from paper_metrics import Performance, compute
from paper_trading import PaperTradingJournal, Status, Trade

CAU_CHUA_CAU_HINH = ("chưa cấu hình kho ngoài (Google Sheets) — "
                     "không đọc được sổ thật")
CAU_CHUA_CO_LENH_DONG = "sổ chưa có lệnh đã đóng nào"

#: Trạng thái được coi là "đang nắm giữ hoặc đang chờ khớp".
TRANG_THAI_MO = (Status.OPEN, Status.PENDING, Status.CLOSING)
#: Trạng thái của một giao dịch đã xong — đầu vào duy nhất của thống kê.
TRANG_THAI_DONG = (Status.CLOSED,)


@dataclass(frozen=True)
class SoLenhApp:
    """Ảnh chụp sổ lệnh cho app. `loi` chỉ khác None khi KHÔNG đọc được sổ."""
    tat_ca: tuple[Trade, ...]
    vi_the_mo: tuple[Trade, ...]
    lenh_dong: tuple[Trade, ...]
    hieu_qua: Optional[Performance]
    loi: Optional[str]

    @property
    def ly_do_khong_co_thong_ke(self) -> str:
        """Vì sao không có số hiệu quả: không đọc được sổ, hay sổ chưa có lệnh đóng."""
        return self.loi or CAU_CHUA_CO_LENH_DONG


def dung_trade(dong: dict[str, Any]) -> Trade:
    """Một dòng tab `trades` (đã qua `sheets_store._from_cell`) -> `Trade`.

    Dùng đúng hàm đổi của sổ (`PaperTradingJournal._to_trade`) nên cột nào sổ
    đọc thì app đọc y như vậy; thiếu cột bắt buộc thì NỔ `KeyError`, không điền.
    """
    return PaperTradingJournal._to_trade(dong)


def dung_so_lenh(du_lieu: Optional[dict[str, list[dict]]]) -> SoLenhApp:
    """`None` = kho ngoài chưa cấu hình. Ngoài ra đọc `du_lieu["lenh"]`."""
    if du_lieu is None:
        return SoLenhApp((), (), (), None, CAU_CHUA_CAU_HINH)
    tat_ca = tuple(sorted((dung_trade(d) for d in du_lieu["lenh"]),
                          key=lambda t: t.id))
    vi_the_mo = tuple(t for t in tat_ca if t.status in TRANG_THAI_MO)
    lenh_dong = tuple(t for t in tat_ca if t.status in TRANG_THAI_DONG)
    return SoLenhApp(tat_ca, vi_the_mo, lenh_dong, compute(list(lenh_dong)), None)
