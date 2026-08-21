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
import time
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
        j = PaperTradingJournal(DB_PATH, cho_phep_so_that=True)
        return j.db, j
    if isinstance(nguon, PaperTradingJournal):
        return nguon.db, None
    if isinstance(nguon, sqlite3.Connection):
        return nguon, None
    j = PaperTradingJournal(str(nguon), cho_phep_so_that=True)
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
    j = PaperTradingJournal(db_path, cho_phep_so_that=True)
    try:
        return _ss.pull(j.db, b, allow_overwrite=allow_overwrite)
    finally:
        j.db.close()


# ─────────────────────────────────────────────────────────────────────
# Kéo sổ có thử lại — cho nhịp quét tự động trên GitHub Actions
# ─────────────────────────────────────────────────────────────────────
#
# VÌ SAO CẦN. 2/35 nhịp quét (18/08 và 19/08/2026) chết ở đúng bước kéo
# sổ, sau 2 giây, và hai bước sau bị "skipped" — nhịp đó không quét gì
# cả. Không nhịp nào để lại annotation "::error::" của chính script, tức
# là chúng chết vì NGOẠI LỆ chưa bắt chứ không phải nhánh "chưa cấu
# hình". Chết sau 2 giây ngay khi gọi mạng là dấu hiệu trục trặc nhất
# thời — thứ đáng thử lại.
#
# THỬ LẠI CÓ AN TOÀN KHÔNG. Có, và lý do nằm ở THỨ TỰ trong
# sheets_store.pull(): hai lời gọi mạng read_rows() chạy TRƯỚC mọi lệnh
# DELETE, còn commit() nằm ở cuối cùng. Hỏng mạng thì chưa có gì bị xoá;
# hỏng giữa vòng INSERT thì connection đóng lúc chưa commit nên SQLite
# rollback. Đó là suy luận đọc từ mã, nên nó được KHOÁ bằng
# tests/test_keo_so_thu_lai.py chứ không để nằm làm giả định. Thiếu tính
# chất này thì thử lại còn tệ hơn không thử: lần 1 xoá dở sổ, lần 2 gặp
# sổ đã có dữ liệu và bị chính gác chống ghi đè từ chối.
#
# KHÔNG thử lại khi hàm trả None. None nghĩa là "kho ngoài chưa cấu
# hình" — thử thêm 100 lần vẫn None, chỉ tổ làm chậm nhịp quét.
#
# HẾT SỐ LẦN THÌ NỔ, không trả None và không trả sổ rỗng. Trả None sẽ
# lẫn với "chưa cấu hình", mà hai thứ đó cần hai câu báo lỗi khác nhau.
# Cả hai đều phải DỪNG phiên quét: quét tiếp trên sổ rỗng rồi đẩy lên là
# đúng cơ chế đã làm mất 96/113 lệnh ngày 12/08/2026.

CHO_GIUA_HAI_LAN = (5, 20)   # giây, giãn dần


class KeoSoThatBai(RuntimeError):
    """Kéo sổ hỏng sau khi đã thử hết số lần cho phép."""


def keo_so_co_thu_lai(db_path: str = DB_PATH, so_lan: int = 3,
                      cho: tuple = CHO_GIUA_HAI_LAN,
                      backend: Any = None,
                      nghi=time.sleep, ghi=print) -> Optional[dict]:
    """Kéo sổ lệnh từ Sheets, thử lại khi gặp ngoại lệ.

    Trả về {"trades": n, "decisions": n} khi kéo được, None khi kho
    ngoài chưa cấu hình. Ném KeoSoThatBai khi đã thử hết số lần.

    `nghi` và `ghi` tách thành tham số để test chạy được mà không phải
    ngủ thật và không phải bắt stdout.
    """
    if so_lan < 1:
        raise ValueError(f"so_lan phải >= 1, nhận {so_lan}")

    loi_cuoi: Optional[BaseException] = None
    for lan in range(1, so_lan + 1):
        try:
            return restore_journal_from_google_sheets(db_path, backend=backend)
        except Exception as e:
            loi_cuoi = e
            ghi(f"Kéo sổ lần {lan}/{so_lan} hỏng — {type(e).__name__}: {e}")
            if lan < so_lan:
                giay = cho[min(lan - 1, len(cho) - 1)] if cho else 0
                ghi(f"Chờ {giay}s rồi thử lại.")
                nghi(giay)

    raise KeoSoThatBai(
        f"Kéo sổ hỏng cả {so_lan} lần. Lỗi cuối cùng: "
        f"{type(loi_cuoi).__name__}: {loi_cuoi}") from loi_cuoi
