"""
sheets_store.py
──────────────────────────────────────────────────────────────────────
Đẩy sổ lệnh giấy ra Google Sheets để nó sống sót trên Streamlit Cloud.

VÌ SAO CẦN
──────────
Ổ đĩa Streamlit Cloud là tạm. App ngủ khi không dùng, redeploy mỗi lần
push, và mọi file app tự ghi ra đều mất. Nghĩa là trên cloud, sổ lệnh chỉ
đọc được bản .db lúc deploy — mọi lệnh ghi sau đó bốc hơi. Không có kho
ngoài thì vòng học không thể chạy trên cloud.

Google Sheets được chọn vì miễn phí, và vì **mở ra soi tay được**: sổ lệnh
là bằng chứng, nên việc người kiểm tra được từng dòng bằng mắt quan trọng
hơn tốc độ.

MÔ HÌNH ĐỒNG BỘ
───────────────
SQLite vẫn là máy chạy. Sheets chỉ là kho bền. Không đồng bộ hai chiều —
hai chiều sinh xung đột, mà xung đột trên sổ lệnh nghĩa là mất bằng chứng.

    decisions  → CHỈ THÊM. Đẩy các dòng có seq lớn hơn seq lớn nhất đã
                 nằm trên sheet. Không bao giờ sửa hay xoá dòng cũ.
    trades     → SOI GƯƠNG TOÀN PHẦN. Lệnh có đổi trạng thái
                 (PENDING → OPEN → CLOSING → CLOSED) và stop_loss được
                 nâng theo trailing, nên phải ghi đè cả bảng. Ghi đè toàn
                 phần cũng làm phép đẩy tự idempotent.

BẤT BIẾN CỦA MODULE NÀY
───────────────────────
1. `pull()` TỪ CHỐI ghi vào sổ đã có dữ liệu, trừ khi gọi kèm
   allow_overwrite=True. Ghi đè sổ thật bằng dữ liệu nơi khác đúng là
   cách 96/113 lệnh biến mất ngày 12/08/2026.
2. Sai lệch cấu trúc cột phải NỔ, không được đoán. Header trên sheet
   chính là lược đồ; lệch một cột là dừng.
3. id và seq được giữ NGUYÊN khi khôi phục. Đánh số lại sẽ làm lần đẩy
   sau nhân đôi dữ liệu.
4. Không có credential thì tính năng TẮT sạch, app chạy như cũ — không
   nuốt lỗi, nhưng cũng không bắt người dùng local phải có Google Cloud.

Xem NGUYEN-TAC-DO-LUONG.md.
"""
from __future__ import annotations

import json
import sqlite3
from typing import Any, Optional, Protocol

# ── Lược đồ: thứ tự cột ở đây LÀ hợp đồng với Google Sheet ───────────
# Đổi thứ tự hoặc đổi tên cột là đổi lược đồ -> pull() sẽ nổ chứ không
# âm thầm đọc sai cột, và đó là hành vi mong muốn.
TRADE_COLS: tuple[str, ...] = (
    "id", "symbol", "exchange", "signal_date", "entry_date", "entry_price",
    "exit_date", "exit_price", "exit_reason", "stop_loss", "take_profit",
    "size_pct", "entry_score", "entry_recommendation", "components",
    "reasons", "status", "created_at",
)

DECISION_COLS: tuple[str, ...] = (
    "seq", "at", "symbol", "signal_date", "score", "recommendation",
    "acted", "skip_reason", "components", "reasons", "data_quality",
)

_INT_COLS = {"id", "seq", "entry_score", "score", "acted"}
_FLOAT_COLS = {"entry_price", "exit_price", "stop_loss", "take_profit",
               "size_pct", "created_at", "at"}

# Ô rỗng trên sheet mang HAI nghĩa khác nhau tuỳ cột, nên phải khai báo rõ
# cột nào được phép NULL. Không khai báo thì buộc phải chọn bừa một nghĩa,
# và vòng đẩy-kéo sẽ mất dữ liệu âm thầm ở nửa còn lại:
#
#   entry_date/exit_date/exit_reason  NULL khi lệnh chưa khớp/chưa đóng
#   skip_reason và cột chữ khác       luôn được ghi, mặc định chuỗi rỗng
#
# Nhờ tách bạch, vòng đẩy-kéo không mất gì — khoá bởi
# test_day_roi_keo_ve_ra_dung_so_cu và test_giu_nguyen_null_cot_chu.
_NULLABLE_TEXT_COLS = {"entry_date", "exit_date", "exit_reason"}

TAB_TRADES = "trades"
TAB_DECISIONS = "decisions"


class SheetError(RuntimeError):
    """Lỗi đồng bộ — luôn ném ra, không bao giờ nuốt."""


class SheetSchemaError(SheetError):
    """Cấu trúc cột trên sheet lệch với lược đồ trong mã."""


# ─────────────────────────────────────────────────────────────────────
# Backend
# ─────────────────────────────────────────────────────────────────────
class SheetBackend(Protocol):
    """Tối giản có chủ ý: đủ để đẩy/kéo, và đủ để dựng bản giả cho test.

    Nhờ lớp này mà toàn bộ logic đồng bộ kiểm thử được offline, không cần
    mạng và không cần credential Google.
    """

    def read_rows(self, tab: str) -> list[list[str]]: ...
    def write_all(self, tab: str, rows: list[list[str]]) -> None: ...
    def append_rows(self, tab: str, rows: list[list[str]]) -> None: ...


class InMemorySheet:
    """Bản giả cho test. Giữ đúng đặc tính khó chịu nhất của Sheets:
    **mọi ô đều là chuỗi**. Nếu chuyển đổi kiểu sai, test sẽ bắt được."""

    def __init__(self) -> None:
        self.tabs: dict[str, list[list[str]]] = {}

    def read_rows(self, tab: str) -> list[list[str]]:
        return [list(r) for r in self.tabs.get(tab, [])]

    def write_all(self, tab: str, rows: list[list[str]]) -> None:
        self.tabs[tab] = [[str(c) for c in r] for r in rows]

    def append_rows(self, tab: str, rows: list[list[str]]) -> None:
        self.tabs.setdefault(tab, [])
        self.tabs[tab].extend([str(c) for c in r] for r in rows)


class GoogleSheet:
    """Backend thật, dùng gspread. Import gspread nằm trong hàm để máy
    local không cài gspread vẫn nạp được module này."""

    def __init__(self, spreadsheet_key: str, credentials: dict) -> None:
        try:
            import gspread
        except ImportError as e:
            raise SheetError(
                "Thiếu gspread. Cài bằng: pip install gspread") from e

        self._gc = gspread.service_account_from_dict(credentials)
        self._sh = self._gc.open_by_key(spreadsheet_key)

    def _tab(self, tab: str):
        try:
            return self._sh.worksheet(tab)
        except Exception:
            return self._sh.add_worksheet(title=tab, rows=1000, cols=30)

    def read_rows(self, tab: str) -> list[list[str]]:
        return self._tab(tab).get_all_values()

    def write_all(self, tab: str, rows: list[list[str]]) -> None:
        """Ghi đè bảng bằng MỘT lệnh gọi duy nhất.

        KHÔNG dùng clear() rồi update(): giữa hai lệnh đó có một khoảng
        thời gian tab rỗng. Mạng đứt đúng lúc ấy là sổ lệnh trên kho ngoài
        mất sạch — đúng kiểu mất bằng chứng mà dự án này đã dính một lần.

        Thay vào đó ghi đè tại chỗ, đệm thêm dòng trống để xoá phần dư của
        lần ghi trước. Thất bại giữa chừng thì cùng lắm là ghi thiếu, chứ
        không có trạng thái trung gian rỗng.
        """
        ws = self._tab(tab)
        if not rows:
            return

        so_dong_cu = len(ws.get_all_values())
        so_cot = max(len(r) for r in rows)
        day_du = [list(r) + [""] * (so_cot - len(r)) for r in rows]
        for _ in range(max(0, so_dong_cu - len(rows))):
            day_du.append([""] * so_cot)

        ws.update(day_du, "A1")

    def append_rows(self, tab: str, rows: list[list[str]]) -> None:
        if rows:
            self._tab(tab).append_rows(rows, value_input_option="RAW")


# ─────────────────────────────────────────────────────────────────────
# Chuyển đổi kiểu
# ─────────────────────────────────────────────────────────────────────
def _to_cell(col: str, value: Any) -> str:
    """SQLite -> ô sheet. Mọi ô là chuỗi."""
    return "" if value is None else str(value)


def _from_cell(col: str, cell: str) -> Any:
    """Ô sheet -> giá trị SQLite. Ô rỗng nghĩa là NULL, trừ các cột chữ
    không-null (ở đó ô rỗng đúng là chuỗi rỗng)."""
    if cell != "":
        if col in _INT_COLS:
            return int(cell)
        if col in _FLOAT_COLS:
            return float(cell)
        return cell
    if col in _INT_COLS or col in _FLOAT_COLS or col in _NULLABLE_TEXT_COLS:
        return None
    return ""


def _kiem_tra_header(tab: str, header: list[str], mong_doi: tuple[str, ...]) -> None:
    if tuple(header) != mong_doi:
        raise SheetSchemaError(
            f"Cấu trúc cột tab '{tab}' lệch với lược đồ trong mã.\n"
            f"  trên sheet: {header}\n"
            f"  mong đợi  : {list(mong_doi)}\n"
            f"Dừng lại thay vì đoán — đọc lệch cột là hỏng sổ lệnh.")


# ─────────────────────────────────────────────────────────────────────
# Đẩy lên
# ─────────────────────────────────────────────────────────────────────
def push(db: sqlite3.Connection, backend: SheetBackend) -> dict:
    """Đẩy sổ lệnh lên sheet.

    trades: ghi đè toàn phần (lệnh có đổi trạng thái).
    decisions: chỉ thêm dòng mới (bảng chỉ-thêm).

    Trả về báo cáo số dòng đã ghi. Gọi hai lần liên tiếp thì lần thứ hai
    thêm 0 decision — phép đẩy là idempotent.
    """
    db.row_factory = sqlite3.Row

    # ── trades: soi gương toàn phần ──────────────────────────────────
    rows = db.execute(
        f"SELECT {', '.join(TRADE_COLS)} FROM trades ORDER BY id").fetchall()
    bang_trades = [list(TRADE_COLS)]
    bang_trades += [[_to_cell(c, r[c]) for c in TRADE_COLS] for r in rows]
    backend.write_all(TAB_TRADES, bang_trades)

    # ── decisions: chỉ thêm phần mới ─────────────────────────────────
    hien_co = backend.read_rows(TAB_DECISIONS)
    seq_lon_nhat = 0
    if hien_co and hien_co[0]:
        _kiem_tra_header(TAB_DECISIONS, hien_co[0], DECISION_COLS)
        for r in hien_co[1:]:
            if r and r[0] != "":
                seq_lon_nhat = max(seq_lon_nhat, int(r[0]))
    else:
        backend.write_all(TAB_DECISIONS, [list(DECISION_COLS)])

    moi = db.execute(
        f"SELECT {', '.join(DECISION_COLS)} FROM decisions"
        f" WHERE seq > ? ORDER BY seq", (seq_lon_nhat,)).fetchall()
    if moi:
        backend.append_rows(
            TAB_DECISIONS,
            [[_to_cell(c, r[c]) for c in DECISION_COLS] for r in moi])

    return {"trades": len(rows), "decisions_moi": len(moi),
            "decisions_da_co": seq_lon_nhat}


# ─────────────────────────────────────────────────────────────────────
# Kéo về
# ─────────────────────────────────────────────────────────────────────
def pull(db: sqlite3.Connection, backend: SheetBackend,
         allow_overwrite: bool = False) -> dict:
    """Dựng lại sổ lệnh từ sheet.

    TỪ CHỐI ghi vào sổ đã có dữ liệu trừ khi allow_overwrite=True. Ghi đè
    sổ thật bằng dữ liệu nơi khác đúng là cách 96/113 lệnh thật biến mất
    ngày 12/08/2026 — mặc định phải là từ chối.

    id và seq giữ nguyên: đánh số lại sẽ làm lần push sau nhân đôi dữ liệu.
    """
    db.row_factory = sqlite3.Row
    dang_co = (db.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
               + db.execute("SELECT COUNT(*) FROM decisions").fetchone()[0])
    if dang_co and not allow_overwrite:
        raise SheetError(
            f"Sổ lệnh đích đang có {dang_co} bản ghi. pull() từ chối ghi đè.\n"
            f"Nếu thật sự muốn thay toàn bộ, gọi pull(..., allow_overwrite=True).")

    bang_trades = backend.read_rows(TAB_TRADES)
    bang_dec = backend.read_rows(TAB_DECISIONS)

    n_trades = n_dec = 0
    db.execute("DELETE FROM trades")
    db.execute("DELETE FROM decisions")

    if bang_trades:
        _kiem_tra_header(TAB_TRADES, bang_trades[0], TRADE_COLS)
        cho = ",".join("?" * len(TRADE_COLS))
        for r in bang_trades[1:]:
            if not r or all(c == "" for c in r):
                continue
            r = list(r) + [""] * (len(TRADE_COLS) - len(r))
            db.execute(
                f"INSERT INTO trades ({', '.join(TRADE_COLS)}) VALUES ({cho})",
                [_from_cell(c, r[i]) for i, c in enumerate(TRADE_COLS)])
            n_trades += 1

    if bang_dec:
        _kiem_tra_header(TAB_DECISIONS, bang_dec[0], DECISION_COLS)
        cho = ",".join("?" * len(DECISION_COLS))
        for r in bang_dec[1:]:
            if not r or all(c == "" for c in r):
                continue
            r = list(r) + [""] * (len(DECISION_COLS) - len(r))
            db.execute(
                f"INSERT INTO decisions ({', '.join(DECISION_COLS)})"
                f" VALUES ({cho})",
                [_from_cell(c, r[i]) for i, c in enumerate(DECISION_COLS)])
            n_dec += 1

    db.commit()
    return {"trades": n_trades, "decisions": n_dec}


# ─────────────────────────────────────────────────────────────────────
# Mở backend thật từ secrets
# ─────────────────────────────────────────────────────────────────────
def open_from_secrets(secrets: Optional[dict] = None) -> Optional[GoogleSheet]:
    """Dựng backend Google từ st.secrets. Trả None nếu chưa cấu hình.

    Không có credential thì tính năng TẮT sạch — người dùng local không
    bắt buộc phải có Google Cloud. Nhưng cấu hình SAI thì phải nổ, vì
    "tưởng đã sao lưu mà thật ra không" là trạng thái tệ nhất.
    """
    if secrets is None:
        try:
            import streamlit as st
            secrets = st.secrets
        except Exception:
            return None

    try:
        key = secrets["GOOGLE_SHEET_KEY"]
        creds = secrets["gcp_service_account"]
    except (KeyError, TypeError):
        return None

    if not key:
        return None

    creds = dict(creds)
    # secrets.toml giữ private_key nhiều dòng bằng \n theo nghĩa đen
    pk = creds.get("private_key", "")
    if "\\n" in pk:
        creds["private_key"] = pk.replace("\\n", "\n")

    return GoogleSheet(str(key), creds)


def trang_thai(backend: Optional[SheetBackend]) -> dict:
    """Kho ngoài có thật sự bật không — cùng tinh thần market_filter.status().

    Một đường sao lưu hỏng âm thầm còn tệ hơn không có đường nào.
    """
    if backend is None:
        return {"bat": False, "ghi_chu": "Chưa cấu hình GOOGLE_SHEET_KEY / "
                                         "gcp_service_account — sổ lệnh chỉ "
                                         "nằm trên ổ đĩa tạm"}
    def _dem(rows: list[list[str]]) -> int:
        # Bỏ header và các dòng trống đệm do write_all() để lại.
        return sum(1 for r in rows[1:] if r and any(c != "" for c in r))

    try:
        return {"bat": True,
                "trades": _dem(backend.read_rows(TAB_TRADES)),
                "decisions": _dem(backend.read_rows(TAB_DECISIONS)),
                "ghi_chu": "Kho ngoài hoạt động"}
    except Exception as e:
        return {"bat": False, "ghi_chu": f"Kho ngoài LỖI: {type(e).__name__}: {e}"}
