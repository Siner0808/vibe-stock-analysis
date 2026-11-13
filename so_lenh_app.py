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


# ── Chú thích lỗ GIẢ do sự kiện quyền (BƯỚC 271) ─────────────────────────────
#: Hai lệnh đã đóng mà sổ ghi một cú cắt lỗ GIẢ vì lệch thang giá: sổ lưu giá vào và
#: cắt lỗ ở thang CHƯA điều chỉnh, nguồn giá điều chỉnh lùi sau ngày giao dịch không
#: hưởng quyền, nên `paper_trading._lenh_dat_san` so hai thang khác nhau (`low <= sl`).
#: {id lệnh: mã}. Nguồn của danh sách: `docs/STATE.md` BƯỚC 269 (nguyên nhân) và 270
#: (kiểm kê); ĐO 27 (BƯỚC 268) khai đúng hai lệnh này ở `tap_loai`. Người dùng chốt
#: 12/11/2026 giữ nguyên sổ, nên đây là danh sách TĨNH của hai dòng đã đóng — KHÔNG phải
#: nhãn tính lúc chạy (nhãn tính cần tải giá, app chỉ làm khi người dùng bấm nút).
#: Khớp theo CẢ id, mã VÀ lý do thoát: sổ dựng lại hay đánh số lại thì chú thích
#: không gắn nhầm sang một lệnh khác.
LENH_LO_GIA_GDKHQ: dict[int, str] = {122: "HDB", 128: "TCB"}

#: Mẫu câu cạnh ô "Sổ lệnh (net)" ở topbar. `{n}` là số lệnh THẬT SỰ có mặt trong sổ đang
#: đọc. KHÔNG in một con số "đã loại hai lệnh": số ấy đẹp lên, nó không phải số đã sửa
#: (giá trị đúng của hai lệnh trên thang đúng chưa ai chạy; `docs/STATE.md` BƯỚC 270 ô "Cách đọc").
CHU_THICH_O_SO_LENH = "gồm {n} lệnh lỗ giả do sự kiện quyền"

#: Câu cạnh lời hậu kiểm (máy và B1) của một trong hai lệnh. Nguyên nhân viết từ mã:
#: `paper_trading._lenh_dat_san` (`low <= sl`) đọc nến thang MỚI với cắt lỗ thang CŨ.
CHU_THICH_HAU_KIEM = (
    "Lệnh này mang lỗ GIẢ do sự kiện quyền: sổ lưu giá vào và cắt lỗ ở thang chưa điều "
    "chỉnh, nguồn giá đã điều chỉnh lùi, nên máy so hai thang khác nhau và ghi một cú "
    "cắt lỗ không có thật (docs/STATE.md BƯỚC 269–270). Nhãn \"gap/trượt giá\", phần "
    "\"riêng mã\" và lời B1 bên dưới đọc cú rơi cơ học ấy như biến động thị trường — "
    "đừng theo dõi nó như một hiện tượng gap.")


def lenh_lo_gia_trong_so(lenh_dong: "tuple[Trade, ...] | list[Trade]") -> tuple[Trade, ...]:
    """Các lệnh ĐÃ ĐÓNG trong sổ đang đọc khớp `LENH_LO_GIA_GDKHQ` (id, mã VÀ cắt lỗ)."""
    return tuple(t for t in lenh_dong
                 if LENH_LO_GIA_GDKHQ.get(t.id) == t.symbol
                 and t.exit_reason == "STOP_LOSS")


def chu_thich_o_so_lenh(lenh_dong: "tuple[Trade, ...] | list[Trade]") -> Optional[str]:
    """Câu một dòng cạnh ô "Sổ lệnh (net)", hoặc None khi sổ không có lệnh nào trong số đó."""
    n = len(lenh_lo_gia_trong_so(lenh_dong))
    return CHU_THICH_O_SO_LENH.format(n=n) if n else None


def chu_thich_hau_kiem(trade_id: Any, lenh_dong: "tuple[Trade, ...] | list[Trade]") -> Optional[str]:
    """Câu cạnh lời hậu kiểm của lệnh `trade_id`, hoặc None nếu không phải lệnh lỗ giả trong sổ."""
    for t in lenh_lo_gia_trong_so(lenh_dong):
        if str(t.id) == str(trade_id):
            return CHU_THICH_HAU_KIEM
    return None
