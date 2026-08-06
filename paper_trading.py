"""
paper_trading.py
──────────────────────────────────────────────────────────────────────
Sổ lệnh GIẤY của agent — ghi lại mọi quyết định để kiểm chứng hiệu quả.

KHÔNG ĐẶT LỆNH THẬT
───────────────────
Module này không kết nối tới bất kỳ công ty chứng khoán nào và không thực
hiện giao dịch. Nó chỉ ghi chép. Nếu sau này có tính năng giao dịch thật,
ranh giới phải là: agent chuẩn bị lệnh → người xác nhận → người đặt.

VÌ SAO SỔ GIẤY ĐỦ (VÀ TỐT HƠN) ĐỂ ĐO HIỆU QUẢ
──────────────────────────────────────────────
Tiền thật không thêm thông tin nào về chất lượng tín hiệu — tín hiệu y hệt,
chỉ hậu quả khác. Ngược lại nó thêm nhiễu (trượt giá, khớp một phần, người
dùng tự can thiệp) khiến không tách được "tín hiệu sai" khỏi "thực thi kém".
Sổ giấy còn chạy song song cả rổ nên tích luỹ mẫu nhanh hơn nhiều lần.

QUAN HỆ VỚI BACKTEST
────────────────────
Backtest = đánh giấy trong QUÁ KHỨ: có ngay kết quả, nhưng dính hindsight
bias, survivorship bias và nguy cơ rò rỉ tương lai.
Sổ này = ghi tiến về phía TRƯỚC: miễn nhiễm với cả ba, đổi lại phải chờ.
Hai thứ bổ sung cho nhau.

BỐN NGUYÊN TẮC GHI CHÉP
───────────────────────
1. Bất biến — quyết định đã ghi thì không sửa. Sửa được thì nó thành câu
   chuyện tự kể, không phải bằng chứng.
2. Không nhìn trộm — tín hiệu sinh sau phiên T thì vào lệnh ở giá MỞ CỬA
   phiên T+1, không phải giá đóng cửa T.
3. Có phí — phí môi giới hai chiều + thuế bán. Bỏ qua thì mọi con số lạc quan.
4. Ghi CẢ quyết định không vào lệnh — nếu chỉ ghi lệnh đã mở thì chính sổ
   của bạn đã có thiên lệch chọn mẫu.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Any, Optional

from data_quality import now_vn

DB_PATH = "paper_trades.db"

# ── Quy tắc mặc định ────────────────────────────────────────────────
BUY_THRESHOLD = 62          # khớp ngưỡng MUA của MasterConsensusAgent
EXIT_SIGNAL_THRESHOLD = 45  # điểm rơi xuống dưới mức này -> đóng theo nguyên tắc
MAX_HOLD_SESSIONS = 60      # trần thời gian nắm giữ

# Chi phí thị trường VN (điều chỉnh theo công ty chứng khoán của bạn)
BROKER_FEE_PCT = 0.0015     # 0,15% mỗi chiều
SELL_TAX_PCT = 0.001        # 0,1% thuế trên giá trị bán


class Status:
    PENDING = "PENDING"     # đã có tín hiệu vào, chờ giá mở cửa phiên sau
    OPEN = "OPEN"
    CLOSING = "CLOSING"     # đã có tín hiệu ra, chờ giá mở cửa phiên sau
    CLOSED = "CLOSED"


class ExitReason:
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"
    SIGNAL_REVERSED = "SIGNAL_REVERSED"
    MAX_HOLD = "MAX_HOLD"


@dataclass
class Trade:
    id: int
    symbol: str
    signal_date: str
    entry_date: Optional[str]
    entry_price: Optional[float]
    exit_date: Optional[str]
    exit_price: Optional[float]
    exit_reason: Optional[str]
    stop_loss: float
    take_profit: float
    size_pct: float
    entry_score: int
    status: str

    def gross_return_pct(self) -> Optional[float]:
        if self.entry_price and self.exit_price:
            return (self.exit_price - self.entry_price) / self.entry_price * 100
        return None

    def net_return_pct(self) -> Optional[float]:
        """Lợi nhuận sau phí — con số duy nhất đáng tin."""
        g = self.gross_return_pct()
        if g is None:
            return None
        cost = (BROKER_FEE_PCT * 2 + SELL_TAX_PCT) * 100
        return g - cost


class PaperTradingJournal:
    """Sổ lệnh giấy, lưu SQLite. Bảng quyết định chỉ-thêm."""

    def __init__(self, path: str = DB_PATH) -> None:
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS decisions (
              seq INTEGER PRIMARY KEY AUTOINCREMENT,
              at REAL, symbol TEXT, signal_date TEXT,
              score INT, recommendation TEXT, acted INT,
              skip_reason TEXT, components TEXT, reasons TEXT,
              data_quality TEXT
            );
            CREATE TABLE IF NOT EXISTS trades (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              symbol TEXT, exchange TEXT,
              signal_date TEXT, entry_date TEXT, entry_price REAL,
              exit_date TEXT, exit_price REAL, exit_reason TEXT,
              stop_loss REAL, take_profit REAL, size_pct REAL,
              entry_score INT, entry_recommendation TEXT,
              components TEXT, reasons TEXT,
              status TEXT, created_at REAL
            );
            CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol, status);
        """)
        self.db.commit()

    # ─────────────────── Ghi quyết định (kể cả không vào lệnh) ────────
    def record_decision(self, symbol: str, signal_date: str, result: dict,
                        acted: bool, skip_reason: str = "") -> None:
        self.db.execute(
            "INSERT INTO decisions (at, symbol, signal_date, score, recommendation,"
            " acted, skip_reason, components, reasons, data_quality)"
            " VALUES (?,?,?,?,?,?,?,?,?,?)",
            (now_vn().timestamp(), symbol, signal_date,
             int(result.get("final_score", 0)), result.get("recommendation", ""),
             1 if acted else 0, skip_reason,
             json.dumps(result.get("score_breakdown", {}), ensure_ascii=False),
             json.dumps(result.get("key_reasons", []), ensure_ascii=False),
             result.get("data_quality", "")))
        self.db.commit()

    # ─────────────────── Mở lệnh ──────────────────────────────────────
    def consider_entry(self, symbol: str, signal_date: str, result: dict,
                       exchange: str = "HOSE",
                       buy_threshold: float | None = None) -> Optional[int]:
        """Xét mở lệnh theo ngưỡng. Trả id lệnh, hoặc None kèm lý do đã ghi sổ.

        Lệnh ở trạng thái PENDING: giá vào lấy ở phiên SAU, không phải phiên
        có tín hiệu — nếu không thì đã nhìn trộm tương lai.
        """
        score = int(result.get("final_score", 0))
        quality = result.get("data_quality", "")
        threshold = BUY_THRESHOLD if buy_threshold is None else buy_threshold

        skip = None
        try:
            from market_filter import is_vni_bullish
            vni_ok = is_vni_bullish(signal_date)
        except Exception:
            vni_ok = True

        if not vni_ok:
            skip = "VN-INDEX nằm dưới MA50 (Downtrend/Điều chỉnh - Giữ 100% tiền mặt)"
        elif quality != "OK":
            skip = f"chất lượng dữ liệu {quality!r}"
        elif score < threshold:
            skip = f"điểm {score} dưới ngưỡng {threshold:g}"
        elif self.open_position(symbol) is not None:
            skip = "đã có vị thế đang mở"
        else:
            risk = (result.get("analyses", {}).get("risk", {})
                    .get("recommendations", {}))
            sl, tp = risk.get("stop_loss_price"), risk.get("take_profit_price")
            if not sl or not tp:
                skip = "thiếu stop-loss/take-profit"

        if skip:
            self.record_decision(symbol, signal_date, result, False, skip)
            return None

        risk = result["analyses"]["risk"]["recommendations"]
        size = float(result.get("safety", {}).get("safe_position_size")
                     or risk.get("suggested_position_size_pct", 10.0))
        cur = self.db.execute(
            "INSERT INTO trades (symbol, exchange, signal_date, entry_date,"
            " entry_price, exit_date, exit_price, exit_reason, stop_loss,"
            " take_profit, size_pct, entry_score, entry_recommendation,"
            " components, reasons, status, created_at)"
            " VALUES (?,?,?,NULL,NULL,NULL,NULL,NULL,?,?,?,?,?,?,?,?,?)",
            (symbol, exchange, signal_date,
             float(risk["stop_loss_price"]), float(risk["take_profit_price"]),
             size, int(result["final_score"]), result.get("recommendation", ""),
             json.dumps(result.get("score_breakdown", {}), ensure_ascii=False),
             json.dumps(result.get("key_reasons", []), ensure_ascii=False),
             Status.PENDING, now_vn().timestamp()))
        self.db.commit()
        self.record_decision(symbol, signal_date, result, True)
        return int(cur.lastrowid)

    def fill_pending(self, symbol: str, session_date: str,
                     open_price: float) -> int:
        """Khớp các lệnh PENDING bằng giá MỞ CỬA của phiên sau ngày tín hiệu."""
        rows = self.db.execute(
            "SELECT id, signal_date FROM trades WHERE symbol=? AND status=?",
            (symbol, Status.PENDING)).fetchall()
        filled = 0
        for r in rows:
            if session_date <= r["signal_date"]:
                continue                      # chưa tới phiên sau -> chưa khớp
            self.db.execute(
                "UPDATE trades SET entry_date=?, entry_price=?, status=?"
                " WHERE id=?",
                (session_date, float(open_price), Status.OPEN, r["id"]))
            filled += 1
        self.db.commit()
        return filled

    # ─────────────────── Đóng lệnh ────────────────────────────────────
    def evaluate_open(self, symbol: str, session_date: str, bar: dict,
                      current_score: Optional[int] = None) -> list[dict]:
        """Xét đóng các lệnh đang mở theo quy tắc, dựa trên nến phiên hiện tại.

        Thứ tự ưu tiên khi cả SL và TP cùng chạm trong một phiên: LẤY SL.
        Nến ngày không cho biết cái nào chạm trước, nên chọn giả định bất lợi —
        giả định có lợi sẽ thổi phồng kết quả một cách có hệ thống.
        """
        closed = []
        rows = self.db.execute(
            "SELECT * FROM trades WHERE symbol=? AND status=?",
            (symbol, Status.OPEN)).fetchall()

        for r in rows:
            if session_date <= (r["entry_date"] or ""):
                continue                      # không đóng ngay trong phiên vào
            low, high = float(bar["low"]), float(bar["high"])
            sl, tp = float(r["stop_loss"]), float(r["take_profit"])
            reason = price = None

            # SL/TP là lệnh chờ đặt sẵn ở sàn -> khớp NGAY trong phiên.
            if low <= sl:
                reason, price = ExitReason.STOP_LOSS, sl
            elif high >= tp:
                reason, price = ExitReason.TAKE_PROFIT, tp

            if reason:
                self.db.execute(
                    "UPDATE trades SET exit_date=?, exit_price=?, exit_reason=?,"
                    " status=? WHERE id=?",
                    (session_date, price, reason, Status.CLOSED, r["id"]))
                closed.append({"id": r["id"], "symbol": symbol,
                               "reason": reason, "exit_price": price})
                continue

            # Thoát theo TÍN HIỆU hoặc HẾT HẠN: chỉ biết được sau khi phiên
            # đóng cửa, nên không thể bán ở chính giá đóng cửa đó. Đánh dấu
            # CLOSING và khớp ở giá mở cửa phiên sau — đối xứng với lúc vào.
            if current_score is not None and current_score < EXIT_SIGNAL_THRESHOLD:
                reason = ExitReason.SIGNAL_REVERSED
            elif self._sessions_held(r["entry_date"], session_date) >= MAX_HOLD_SESSIONS:
                reason = ExitReason.MAX_HOLD

            if reason:
                self.db.execute(
                    "UPDATE trades SET exit_reason=?, status=? WHERE id=?",
                    (reason, Status.CLOSING, r["id"]))
                closed.append({"id": r["id"], "symbol": symbol,
                               "reason": reason, "exit_price": None,
                               "pending": True})
        if closed:
            self.db.commit()
        return closed

    def fill_closing(self, symbol: str, session_date: str,
                     open_price: float) -> int:
        """Khớp các lệnh CLOSING ở giá mở cửa phiên sau khi có tín hiệu ra."""
        rows = self.db.execute(
            "SELECT id, entry_date FROM trades WHERE symbol=? AND status=?",
            (symbol, Status.CLOSING)).fetchall()
        filled = 0
        for r in rows:
            self.db.execute(
                "UPDATE trades SET exit_date=?, exit_price=?, status=?"
                " WHERE id=?",
                (session_date, float(open_price), Status.CLOSED, r["id"]))
            filled += 1
        self.db.commit()
        return filled

    @staticmethod
    def _sessions_held(entry_date: str, session_date: str) -> int:
        """Xấp xỉ số phiên nắm giữ từ khoảng cách ngày lịch (5/7 là ngày giao dịch)."""
        import datetime as _dt
        try:
            a = _dt.date.fromisoformat(entry_date[:10])
            b = _dt.date.fromisoformat(session_date[:10])
        except Exception:
            return 0
        return int((b - a).days * 5 / 7)

    # ─────────────────── Truy vấn ─────────────────────────────────────
    def open_position(self, symbol: str) -> Optional[Trade]:
        r = self.db.execute(
            "SELECT * FROM trades WHERE symbol=? AND status IN (?,?,?) LIMIT 1",
            (symbol, Status.OPEN, Status.PENDING, Status.CLOSING)).fetchone()
        return self._to_trade(r) if r else None

    def all_trades(self, status: str | None = None) -> list[Trade]:
        sql = "SELECT * FROM trades"
        args: list = []
        if status:
            sql += " WHERE status=?"
            args.append(status)
        sql += " ORDER BY id"
        return [self._to_trade(r) for r in self.db.execute(sql, args).fetchall()]

    def decisions(self, acted: bool | None = None) -> list[dict]:
        sql = "SELECT * FROM decisions"
        args: list = []
        if acted is not None:
            sql += " WHERE acted=?"
            args.append(1 if acted else 0)
        return [dict(r) for r in self.db.execute(sql + " ORDER BY seq", args)]

    @staticmethod
    def _to_trade(r: Any) -> Trade:
        return Trade(
            id=r["id"], symbol=r["symbol"], signal_date=r["signal_date"],
            entry_date=r["entry_date"], entry_price=r["entry_price"],
            exit_date=r["exit_date"], exit_price=r["exit_price"],
            exit_reason=r["exit_reason"], stop_loss=r["stop_loss"],
            take_profit=r["take_profit"], size_pct=r["size_pct"],
            entry_score=r["entry_score"], status=r["status"])
