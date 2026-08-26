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
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Optional

from data_quality import now_vn

DB_PATH = "paper_trades.db"


class ProtectedLedgerError(RuntimeError):
    """Có thứ gì đó định ghi đè sổ lệnh thật bằng kết quả backtest."""


def guard_not_real_ledger(path: str, *, caller: str) -> None:
    """Chặn script tối ưu ghi đè `paper_trades.db`.

    Đã xảy ra ngày 12/08/2026: ba script tối ưu kết thúc bằng
    `os.remove("paper_trades.db")` rồi seed lại bằng vòng lãi cao nhất
    trong 20 vòng chạy trên cùng dữ liệu. Kết quả: 96/113 lệnh thật biến
    mất, vị thế ACB đang mở bị xoá, và bằng chứng duy nhất chưa bị tối ưu
    chạm vào bị thay bằng chính thứ nó phải dùng để kiểm chứng.

    Sổ lệnh thật là dữ liệu quan sát, không phải nơi chứa đầu ra của
    backtest. Kết quả in-sample phải đi vào file scratch riêng.

    Xem NGUYEN-TAC-DO-LUONG.md, bất biến 7.
    """
    import os as _os

    if _os.path.basename(str(path)) == _os.path.basename(DB_PATH):
        raise ProtectedLedgerError(
            f"{caller} định ghi vào sổ lệnh thật ({DB_PATH}). Bị chặn.\n"
            f"Sổ lệnh thật chỉ được ghi bởi paper_runner.py và run_daily.py.\n"
            f"Kết quả tối ưu phải ghi ra file scratch riêng.")


# ── Quy tắc mặc định ────────────────────────────────────────────────
BUY_THRESHOLD = 62          # khớp ngưỡng MUA của MasterConsensusAgent

#: Chốt lời cứng — TẮT, và tắt là hành vi đang chạy từ trước.
#:
#: Công tắc này KHÔNG dựng ra để bật lại. Nó dựng ra để câu hỏi "gỡ
#: chốt lời cứng đi là đúng hay sai" trở thành một câu hỏi ĐO ĐƯỢC:
#: chạy walk-forward hai lần trên đúng cùng dữ liệu, mỗi lần một bên.
#:
#: Vì sao cần: đo ngày 23/08/2026, 19/112 lệnh đã đóng trong sổ vẫn
#: mang `exit_reason = TAKE_PROFIT` — di sản của luật cũ — và toàn bộ
#: kỳ vọng dương của sổ (+0,792%) nằm ở đúng 19 dòng ấy. Nhưng xoá 19
#: dòng rồi tính lại KHÔNG mô phỏng được luật mới: dưới luật mới những
#: lệnh đó chạy tiếp và thoát bằng trailing stop. Chỉ có chạy lại cả
#: hai bên mới trả lời được.
#:
#: ĐÃ CHẠY (23/08/2026), hai lượt walk-forward đầy đủ:
#:   ngoai mau  TAT +0,616%/lenh · BAT +0,426%   chenh KTC chua 0
#:   alpha      TAT -0,008%      · BAT -0,006%   hai luat GIONG NHAU
#:   sigma      TAT  10,18%      · BAT   7,72%   TP giam phuong sai 24%
#: Gỡ chốt lời cứng không làm hỏng gì; phần kỳ vọng dôi ra là do giữ
#: lâu hơn 17% (20,3 so với 17,4 ngày), tức beta chứ không phải alpha.
#: Chi tiết: `docs/STATE.md`, mục 23/08/2026.
#:
#: Thứ tự kiểm giữ nguyên bất biến 3: SL kiểm TRƯỚC, nên khi cả hai
#: cùng chạm trong một phiên thì vẫn LẤY SL. `elif` là thứ bảo đảm
#: điều đó, không phải quy ước.
CHOT_LOI_CUNG = False

# ── Ô C5 — NGƯỠNG MUA ĐỂ TRỐNG ──────────────────────────────────────
# Mặc định TẮT: hệ thống vẫn quét, vẫn chấm điểm, vẫn ghi quyết định, vẫn
# theo dõi và đóng các vị thế đang mở — nhưng KHÔNG mở vị thế mới.
#
# Vì sao không phải 50,0 và cũng không phải 62. Đo ngày 20/08/2026 trên 8
# trong 20 sổ còn sót của chính lần chạy sinh ra +636,11%:
#
#   win rate toàn dải ngưỡng 48→59   28,2% → 30,7%   (chênh 2,5 điểm)
#   tương quan ngưỡng ↔ số lệnh      −0,999
#   tương quan số lệnh ↔ vốn đỉnh    +0,990
#   ngưỡng 50 hơn ngưỡng 48          1,57/636 = 0,25%
#
# Ngưỡng KHÔNG cải thiện chất lượng chọn mã — win rate phẳng chứng minh
# điều đó, và nó còn cao hơn ở ngưỡng 58–59. Thứ ngưỡng điều khiển là số
# lệnh, và số lệnh điều khiển đòn bẩy. "Quán quân" chỉ là vòng ôm nhiều vị
# thế cùng lúc nhất. Thêm nữa: alpha in-sample +0,090% (KTC chứa 0) và
# alpha ngoài mẫu 07/08 là −0,63% (cũng chứa 0).
#
# Bật lại khi Phase 5D sinh ra một ngưỡng chọn trên khoảng A và đo trên
# khoảng B, A ∩ B = ∅. Không sớm hơn.
#
# Backtest và test PHẢI bật công tắc này — chúng tồn tại để đo chính logic
# vào lệnh. `cmd_seed` bật nó trong suốt lượt chạy.
CHO_PHEP_MO_LENH_MOI = False

#: Muc chat luong du lieu con DUNG DUOC de vao lenh.
#:
#: "OK" la sach; "WARN" la co dau hieu la nhung van dung duoc (sau khi noi
#: lai cache ngay 20/08, ca 71 ma cua ro deu 0% BLOCK va 11,3% WARN, toan
#: bo la PRICE_JUMP). Moi muc KHAC deu chan -- ke ca mot chuoi la khong
#: nam trong bang Severity, vi "khong biet muc nay la gi" phai nghieng ve
#: phia chan chu khong phai phia cho qua.
#:
#: Ban cu chan moi thu khac "OK", tuc gop WARN vao cung BLOCK. Ban truoc do
#: nua thi nhanh nay la CODE CHET vi packet luon mang "OK" cung.
MUC_CHAT_LUONG_DUNG_DUOC = frozenset({"OK", "WARN"})

LY_DO_C5 = ("ngưỡng mua ĐỂ TRỐNG (ô C5) — đủ điều kiện vào lệnh nhưng hệ "
            "thống dừng mở vị thế mới cho tới khi Phase 5D chọn được ngưỡng "
            "bằng walk-forward hợp lệ")
#: Trần vốn cam kết cùng lúc, tính theo % tài khoản.
#:
#: Bất biến 7b: đường vốn nhân dồn từng lệnh vào TOÀN BỘ vốn hiện có.
#: Phép nhân đó chỉ đúng khi mỗi thời điểm có một lệnh mở. Nhiều lệnh
#: chồng lên nhau thì tổng vốn cam kết vượt 100% và con số cộng dồn
#: trở thành lợi nhuận của một tài khoản VAY ĐƯỢC.
#:
#: Trước 24/08/2026 KHÔNG có gì chặn — `Performance.avg_capital_deployed_pct`
#: chỉ BÁO CÁO sau khi việc đã rồi. Đo được:
#:     so lenh that      29% trung binh · 208% DINH
#:     walk-forward OOS 145% trung binh · 524% dinh
#: Đó đúng là cơ chế sinh ra +636,11% ngày 12/08/2026.
#:
#: Trần theo VỐN chứ không theo SỐ vị thế: `size_pct` chạy từ 5% tới
#: 33,3% tuỳ khoảng cách stop, nên đếm vị thế không ràng buộc được
#: thứ cần ràng buộc. Ở mức trung bình 18,8% thì 100% ≈ 5,3 vị thế.
TRAN_VON_CAM_KET_PCT = 100.0

LY_DO_TRAN_VON = ("vốn cam kết đã chạm trần — mở thêm là dùng đòn bẩy "
                  "(bất biến 7b)")

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


def _lay_cot(r: Any, ten: str):
    """Đọc một cột có thể KHÔNG tồn tại trong hàng.

    `sqlite3.Row` ném `IndexError` chứ không trả None khi thiếu cột,
    và sổ cũ hơn schema hiện tại thì thiếu thật. Trả None ở đây là
    trung thực — "không biết" — chứ không phải nuốt lỗi: hàm gọi
    (`lo_ghi_hang_loat`) coi None là không kết luận được.
    """
    try:
        return r[ten]
    except (IndexError, KeyError):
        return None


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
    #: Dấu thời gian LÚC GHI VÀO ĐĨA (epoch giây) — khác hẳn
    #: `signal_date` là ngày mô phỏng. Chênh lệch giữa hai thứ này
    #: là thứ duy nhất phân biệt một sổ tích luỹ tiến về phía trước
    #: với một sổ sinh ra từ một lượt mô phỏng. Xem
    #: `paper_metrics.lo_ghi_hang_loat()`.
    created_at: Optional[float] = None

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

    def __init__(self, path: str = DB_PATH, *,
                 cho_phep_so_that: bool = False) -> None:
        """Mở sổ. Mở `paper_trades.db` phải khai báo `cho_phep_so_that=True`.

        Mặc định TỪ CHỐI. Bản cũ đặt gác ở phía người gọi —
        `guard_not_real_ledger(SCRATCH_DB, ...)` — nên nó chỉ được gọi ở
        3/7 script tối ưu, và mỗi lần đều truyền hằng số tên file scratch,
        tức không bao giờ có thể kích hoạt. Gác ở phía người gọi là lời tự
        khai; gác ở đây là cái cửa, và script viết sau này cũng phải đi qua.
        """
        if not cho_phep_so_that:
            import sys as _sys
            try:
                nguoi_goi = Path(_sys._getframe(1).f_code.co_filename).name
            except Exception:
                nguoi_goi = "?"
            guard_not_real_ledger(path, caller=nguoi_goi)
        self.duong_dan = str(path)
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA synchronous = OFF;")
        self.db.execute("PRAGMA journal_mode = MEMORY;")
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
    def von_dang_cam_ket(self) -> float:
        """Tổng `size_pct` của các lệnh ĐANG MỞ **và ĐANG CHỜ KHỚP**.

        Phải gồm cả PENDING. Lệnh chờ sẽ khớp ở phiên sau và cam kết
        vốn thật; bỏ nó ra thì xếp bao nhiêu lệnh chờ cũng lọt, rồi
        sáng hôm sau tất cả cùng khớp một lượt — trần thành vô hiệu
        đúng vào phiên nó cần chặn nhất.
        """
        r = self.db.execute(
            "SELECT COALESCE(SUM(size_pct), 0) FROM trades WHERE status IN (?,?)",
            (Status.OPEN, Status.PENDING)).fetchone()
        return float(r[0] or 0.0)

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
        # KHONG bat Exception o day nua. Ban cu nuot MOI loi thanh
        # `vni_ok = True`, tuc "hoi cong that bai" bien thanh "cong cho qua".
        # Cong VN-INDEX qua han nay nem CacheQuaHanError va no PHAI di ra
        # ngoai de dung ca phien quet -- do la o C1.
        from market_filter import is_vni_bullish
        vni_ok = is_vni_bullish(signal_date)

        if not vni_ok:
            skip = "VN-INDEX nằm dưới MA50 (Downtrend/Điều chỉnh - Giữ 100% tiền mặt)"
        elif str(quality).upper() not in MUC_CHAT_LUONG_DUNG_DUOC:
            # CHAN theo muc BLOCK, khong chan ca WARN. Ban cu chan moi thu
            # khac "OK" -- gop hai muc lam mot la mat thong tin: WARN nghia
            # la "co dau hieu la, van dung duoc", BLOCK nghia la "khong dung
            # duoc". Sau khi noi lai cache ngay 20/08, ro 71 ma con 0% BLOCK
            # va 11,3% WARN (deu la PRICE_JUMP).
            skip = f"chất lượng dữ liệu {quality!r} — không dùng được"
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

        # Chốt cuối cùng, ĐẶT SAU mọi cổng khác có chủ đích: lý do ghi vào sổ
        # khi đó cho biết lệnh này LẼ RA đã mở. Đặt trước thì cổng VN-INDEX và
        # cổng chất lượng dữ liệu không còn thống kê được nữa.
        if skip is None and not CHO_PHEP_MO_LENH_MOI:
            skip = LY_DO_C5

        if skip:
            self.record_decision(symbol, signal_date, result, False, skip)
            return None

        risk = result["analyses"]["risk"]["recommendations"]
        
        # Ý TƯỞNG C & E: Phân bổ cỡ vị thế theo Volatility (Fixed Fractional Risk)
        # Fixed Risk = 1.0% tài khoản trên mỗi lệnh
        account_risk_pct = 1.0
        
        entry_price = float(risk["entry_price"])
        stop_loss = float(risk["stop_loss_price"])
        
        # Khoảng cách Stop Loss tính bằng %
        sl_pct_dist = (entry_price - stop_loss) / entry_price if entry_price > stop_loss else 0.05
        
        # Capping khoảng cách tối thiểu 3% để tránh chia cho số quá nhỏ dẫn đến all-in
        sl_pct_dist = max(0.03, sl_pct_dist)
        
        # Tính kích cỡ lệnh: (Rủi ro % / Khoảng cách SL %)
        size = account_risk_pct / sl_pct_dist
        
        # Giới hạn kích cỡ: Tối thiểu 5%, tối đa 33.3% (Tránh dồn vốn vào 1 mã)
        size = round(max(5.0, min(33.3, size)), 1)

        # Trần vốn — chốt cuối cùng, và bắt buộc nằm ở ĐÂY chứ không
        # nằm cùng chỗ với các cổng trên: nó cần `size`, mà `size` chỉ
        # tính được sau khi đã có stop-loss. Lý do ghi vào sổ vì thế
        # cho biết lệnh này đã qua MỌI cổng khác và chỉ dừng ở trần.
        dang_cam_ket = self.von_dang_cam_ket()
        if dang_cam_ket + size > TRAN_VON_CAM_KET_PCT:
            self.record_decision(
                symbol, signal_date, result, False,
                f"{LY_DO_TRAN_VON}: đang cam kết {dang_cam_ket:.1f}% "
                f"+ {size:.1f}% > {TRAN_VON_CAM_KET_PCT:.0f}%")
            return None

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

        Mặc định `CHOT_LOI_CUNG = False`, nên **không có lối thoát bằng
        chốt lời** — lệnh chỉ đóng bằng cắt lỗ, đảo tín hiệu, hoặc trần
        thời gian nắm giữ. Docstring bản trước hứa một nhánh TP mà thân
        hàm đã gỡ; đọc nó rồi tin là hiểu sai hệ thống đang chạy.

        Khi bật công tắc: thứ tự ưu tiên lúc cả SL và TP cùng chạm trong
        một phiên là LẤY SL. Nến ngày không cho biết cái nào chạm trước,
        nên chọn giả định bất lợi — giả định có lợi sẽ thổi phồng kết quả
        một cách có hệ thống (bất biến 3).
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

            entry_p = float(r["entry_price"]) if r["entry_price"] else None

            # SL là lệnh chờ đặt sẵn ở sàn -> khớp NGAY trong phiên.
            #
            # `elif` chứ không phải `if` thứ hai: cả hai cùng chạm thì
            # LẤY SL (bất biến 3). Đổi sang hai `if` rời là để TP ghi đè
            # SL — đúng cái giả định có lợi bị cấm.
            if low <= sl:
                reason, price = ExitReason.STOP_LOSS, sl
            elif CHOT_LOI_CUNG and high >= tp:
                reason, price = ExitReason.TAKE_PROFIT, tp

            # TRAILING STOP & BREAK-EVEN: CHỈ CÓ HIỆU LỰC TỪ PHIÊN SAU.
            close_p = float(bar["close"])
            if reason is None and entry_p:
                new_sl = sl
                # 1. Dời stop về hoà vốn khi giá đạt +5%
                if high >= entry_p * 1.05 and sl < entry_p:
                    new_sl = entry_p
                
                # 2. Trailing Stop 7% (Cho phép giá rung lắc 7% từ đỉnh gần nhất)
                trail_sl = close_p * 0.93
                if trail_sl > new_sl:
                    new_sl = trail_sl
                
                # Chỉ cập nhật database nếu SL được nâng lên
                if new_sl > sl:
                    self.db.execute("UPDATE trades SET stop_loss=? WHERE id=?",
                                    (new_sl, r["id"]))
                    # Commit NGAY. Bản cũ chỉ commit khi có lệnh ĐÓNG, nên
                    # phiên nào chỉ nâng stop mà không đóng lệnh thì lần
                    # nâng đó biến mất lúc đóng kết nối. Đo được: stop
                    # 100,0 trong phiên -> 90,0 sau khi đóng. Nặng hơn:
                    # run_daily.py gọi push() TRƯỚC db.close(), nên Sheets
                    # nhận stop mới còn DB local rollback về stop cũ, và
                    # pull() từ chối ghi đè sổ không rỗng -> hai kho lệch
                    # nhau vĩnh viễn.
                    self.db.commit()

            if reason:
                if reason == ExitReason.STOP_LOSS:
                    try:
                        from post_mortem_learning import get_learning_engine
                        engine = get_learning_engine()
                        if engine.enabled:
                            breakdown = json.loads(r["components"]) if r["components"] else {}
                            reasons = json.loads(r["reasons"]) if r["reasons"] else []
                            # signal_date, KHÔNG phải session_date: mẫu hình thuộc về
                            # thời điểm sinh tín hiệu, và đó là mốc dùng để so sánh
                            # thời gian ở get_penalty_for_pattern.
                            engine.record_sl_trade(
                                symbol, int(r["entry_score"] or 0), breakdown,
                                reasons, signal_date=r["signal_date"],
                                trade_id=r["id"], nguon=self.duong_dan,
                                # phien_hoc = phien LENH DONG, khac
                                # signal_date la phien sinh tin hieu. Day la
                                # truc thoi gian thu hai.
                                phien_hoc=session_date)

                            # CHI SO THAT moi duoc boi vao bo nho tren dia.
                            #
                            # Ba script optimize dat POST_MORTEM_ENABLED=1.
                            # Neu save_memory() chay cho ca so scratch thi moi
                            # lan backtest lai boi them mau vao bo nho that --
                            # dung co che da de ra khoi 6.327 mau, trong do
                            # 99,1% khong ung voi mot lenh that nao.
                            #
                            # Day la mat kia cua guard_not_real_ledger(): o do
                            # so that duoc bao ve khoi backtest GHI VAO; o day
                            # bo nho that duoc bao ve khoi backtest BOI THEM.
                            if Path(self.duong_dan).name == Path(DB_PATH).name:
                                engine.save_memory()
                    except Exception:
                        pass

                self.db.execute(
                    "UPDATE trades SET exit_date=?, exit_price=?, exit_reason=?,"
                    " status=? WHERE id=?",
                    (session_date, price, reason, Status.CLOSED, r["id"]))
                closed.append({"id": r["id"], "symbol": symbol,
                               "reason": reason, "exit_price": price})
                continue

            # Ý TƯỞNG A & D: Khai thác đuôi béo (Fat-Tail Exploitation)
            # Tắt đảo chiều bằng điểm số cho lệnh đang LÃI (unrealized_profit > 0).
            # Khi lệnh đã có lãi, để Trailing Stop & Stop-Loss quản trị việc thoát lệnh,
            # KHÔNG để biến động điểm số ngắn hạn ép chốt non cắt đuôi lãi chạy!
            close_p = float(bar["close"])
            is_profitable = entry_p is not None and close_p > entry_p

            if current_score is not None and current_score < EXIT_SIGNAL_THRESHOLD and not is_profitable:
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
            # bia-ok: ngày không đọc được -> coi như vừa vào lệnh, để một bản
            # ghi hỏng không làm sập cả phiên quét. Đánh đổi có chủ ý và cần
            # biết: lệnh đó sẽ KHÔNG bao giờ chạm MAX_HOLD.
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
            entry_score=r["entry_score"], status=r["status"],
            created_at=_lay_cot(r, "created_at"))
