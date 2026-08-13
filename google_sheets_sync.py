"""
google_sheets_sync.py
──────────────────────────────────────────────────────────────────────
Lớp gọi gọn cho kho ngoài Google Sheets.

Đây là VỎ. Toàn bộ ruột nằm ở `sheets_store.py` — một lược đồ, một đường
đã kiểm thử. Module này chỉ để gọi cho ngắn:

    import google_sheets_sync as gs
    gs.sync_trades_to_google_sheets()        # đẩy sổ mặc định lên Sheets
    gs.load_trades_from_google_sheets()      # đọc lệnh từ Sheets

VÌ SAO KHÔNG TỰ GHI SHEET Ở ĐÂY
───────────────────────────────
Bản đầu của file này tự nói chuyện với gspread bằng lược đồ 14 cột riêng.
Nó đọc `t.position_size_pct`, nhưng lớp `Trade` tên trường là `size_pct` —
`getattr` không bao giờ tìm thấy nên **ghi hằng số 30 cho mọi lệnh**, trong
khi tỷ trọng thật là 15,4 / 25,0 / 26,0… Ba trường `components`, `reasons`,
`created_at` cũng không có trên `Trade` nên luôn ghi rỗng.

Bịa 30% vào sổ lệnh không phải lỗi nhỏ: 30% × số lệnh chồng lấn đúng là
phép tính đã đẻ ra "+636,11%" ngày 12/08/2026. Một con số bịa, lấy từ
Google Sheets, sẽ trông đáng tin hơn hẳn.

Bài học không phải "viết cẩn thận hơn" mà là **chữ ký hàm sai**: nhận vào
`list[Trade]` thì dữ liệu cần thiết không có ở đó, nên buộc phải bịa. Vì
vậy các hàm dưới đây nhận NGUỒN SỔ LỆNH (journal / connection / đường dẫn),
không nhận list.

Xem NGUYEN-TAC-DO-LUONG.md và sheets_store.py.
"""
from __future__ import annotations

import sqlite3
from typing import Any, Optional

import sheets_store as _ss
from paper_trading import DB_PATH, PaperTradingJournal, Trade


class ChuKySaiError(TypeError):
    """Gọi theo kiểu cũ — truyền list[Trade] vào chỗ cần nguồn sổ lệnh."""


def _mo_db(nguon: Any) -> tuple[sqlite3.Connection, Optional[PaperTradingJournal]]:
    """Nhận journal / connection / đường dẫn / None -> (connection, journal_tam).

    journal_tam khác None nghĩa là hàm gọi phải tự đóng nó.
    """
    if isinstance(nguon, list):
        raise ChuKySaiError(
            "Hàm này nhận NGUỒN SỔ LỆNH, không nhận list[Trade].\n"
            "Lớp Trade không mang components/reasons/created_at/exchange, nên "
            "đẩy từ list buộc phải bịa giá trị — đúng lỗi đã khiến mọi lệnh "
            "bị ghi size_pct = 30.\n"
            "Gọi: sync_trades_to_google_sheets()            # sổ mặc định\n"
            "hoặc: sync_trades_to_google_sheets(journal)     # hoặc đường dẫn .db")

    if nguon is None:
        j = PaperTradingJournal(DB_PATH)
        return j.db, j
    if isinstance(nguon, PaperTradingJournal):
        return nguon.db, None
    if isinstance(nguon, sqlite3.Connection):
        return nguon, None
    j = PaperTradingJournal(str(nguon))
    return j.db, j


def get_backend(backend: Any = None) -> Optional[_ss.GoogleSheet]:
    """Backend Sheets từ st.secrets. None nghĩa là chưa cấu hình."""
    return backend if backend is not None else _ss.open_from_secrets()


def is_google_sheets_enabled(backend: Any = None) -> bool:
    """Kho ngoài có dùng được không.

    Chỉ kiểm cấu hình, KHÔNG gọi mạng — dùng `trang_thai()` nếu cần biết
    kho có thật sự trả lời hay không.
    """
    try:
        return get_backend(backend) is not None
    except Exception:
        return False


def trang_thai(backend: Any = None) -> dict:
    """Kho ngoài sống hay chết, có gọi mạng. Xem sheets_store.trang_thai."""
    try:
        return _ss.trang_thai(get_backend(backend))
    except Exception as e:
        return {"bat": False, "ghi_chu": f"Kho ngoài LỖI: {type(e).__name__}: {e}"}


def get_gspread_client(backend: Any = None):
    """Client gspread thô — CỬA THOÁT HIỂM để soi lỗi bằng tay.

    Đừng ghi Sheet qua đây. Ghi thẳng bằng client là bỏ qua kiểm tra lược
    đồ và bỏ qua phép ghi-một-lệnh, tức là mở lại đúng hai lỗ hổng đã vá.
    """
    b = get_backend(backend)
    if b is None:
        raise _ss.SheetError("Chưa cấu hình GOOGLE_SHEET_KEY / gcp_service_account")
    return b._gc


def sync_trades_to_google_sheets(nguon: Any = None, backend: Any = None
                                 ) -> Optional[dict]:
    """Đẩy sổ lệnh lên Google Sheets.

    Đẩy CẢ `trades` lẫn `decisions`. Đẩy riêng trades sẽ làm mất bảng quyết
    định — mà chỉ ghi lệnh đã mở thì chính sổ đã có thiên lệch chọn mẫu.

    nguon: None (sổ mặc định) | PaperTradingJournal | connection | đường dẫn

    Trả None nếu chưa cấu hình (tính năng tắt, không phải lỗi).
    Trả dict báo cáo nếu đẩy xong.
    NÉM ngoại lệ nếu đẩy thất bại — "tưởng đã sao lưu mà thật ra không" là
    trạng thái tệ nhất, nên tuyệt đối không nuốt lỗi ở đây.
    """
    b = get_backend(backend)
    if b is None:
        return None

    db, tam = _mo_db(nguon)
    try:
        return _ss.push(db, b)
    finally:
        if tam is not None:
            tam.db.close()


def load_trades_from_google_sheets(backend: Any = None) -> list[Trade]:
    """Đọc lệnh từ Sheets về dạng `Trade`, KHÔNG đụng sổ trên đĩa.

    Trả list rỗng nếu chưa cấu hình. Dùng để xem/đối chiếu; muốn dựng lại
    sổ thật thì gọi `restore_journal_from_google_sheets()`.
    """
    b = get_backend(backend)
    if b is None:
        return []
    tam = PaperTradingJournal(":memory:")
    try:
        _ss.pull(tam.db, b)
        return tam.all_trades()
    finally:
        tam.db.close()


def restore_journal_from_google_sheets(db_path: str = DB_PATH,
                                       allow_overwrite: bool = False,
                                       backend: Any = None) -> Optional[dict]:
    """Dựng lại sổ lệnh trên đĩa từ Sheets — đường dùng trên Streamlit Cloud.

    TỪ CHỐI ghi vào sổ đang có dữ liệu trừ khi allow_overwrite=True. Ghi đè
    sổ thật bằng dữ liệu nơi khác đúng là cách 96/113 lệnh biến mất
    ngày 12/08/2026.
    """
    b = get_backend(backend)
    if b is None:
        return None
    j = PaperTradingJournal(db_path)
    try:
        return _ss.pull(j.db, b, allow_overwrite=allow_overwrite)
    finally:
        j.db.close()
