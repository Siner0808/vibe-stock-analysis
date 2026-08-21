"""
post_mortem_learning.py
──────────────────────────────────────────────────────────────────────
Bộ nhớ mẫu hình lệnh dính cắt lỗ.

Ý tưởng: nếu một tổ hợp chỉ báo đã từng dẫn tới cắt lỗ, lần sau gặp lại
tổ hợp đó thì hạ điểm. Nghe hợp lý — nhưng bản cài đặt trước đó có hai
lỗi khiến mọi kết quả đo được đều vô giá trị:

  1. NHÌN TRỘM TƯƠNG LAI. Mô phỏng chạy từng mã một: hết ACB (2023→2026)
     rồi mới tới BCM (2023→2026). Tới lúc chấm phiên BCM tháng 1/2024,
     bộ nhớ đã chứa các lệnh cắt lỗ của ACB năm 2026. Agent bị phạt vì
     một khoản lỗ CHƯA XẢY RA.

  2. KHÔNG TÁI LẬP. File bộ nhớ bị ghi đè trong lúc chạy, nên cùng một
     lát dữ liệu cho ra điểm khác nhau tùy vào việc trước đó đã chạy gì.
     Đo được 47 và 59 trên cùng một input.

Hai luật chống lỗi đó, cài ngay trong thiết kế:

  • `get_penalty_for_pattern` BẮT BUỘC nhận `as_of` (ngày của phiên đang
    chấm) và chỉ dùng mẫu hình có `signal_date` NHỎ HƠN `as_of`. Không
    truyền `as_of` thì trả 0 — không có đường nào lọt.
  • Mặc định TẮT. Cơ chế này chưa từng được kiểm định ngoài mẫu, nên nó
    không được phép tác động vào điểm số cho tới khi walk-forward chứng
    minh nó có ích. Bật bằng biến môi trường POST_MORTEM_ENABLED=1.

`sl_pattern_memory.json` là trạng thái chạy, không phải mã nguồn —
nó nằm trong .gitignore.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

MEMORY_FILE = "sl_pattern_memory.json"

#: Chênh lệch tối đa trên mỗi chỉ báo để coi là "cùng mẫu hình".
MATCH_TOLERANCE = 5.0

#: Điểm trừ khi khớp mẫu hình đã từng cắt lỗ.
PENALTY = -12.0

#: Trường BẮT BUỘC để một mẫu được vào bộ nhớ.
#:
#: Đo ngày 20/08/2026 trên file cũ: 6.327 mẫu, 100 mã, KHÔNG trường nào nói
#: vòng nào hay dữ liệu nào sinh ra chúng — và chỉ 56/6.327 (0,89%) ứng với
#: một lệnh thật trong sổ. 99,1% là dư lượng của các vòng seed/tối ưu
#: in-sample, gồm cả những vòng đã bị bất biến 7 tuyên bố vô hiệu.
#:
#: Không sửa được bằng cách bổ sung provenance sau: các vòng sinh ra chúng
#: đã bị `os.remove()` xoá, nên thông tin để truy nguồn KHÔNG TỒN TẠI.
#:
#: Hai trường này là thứ ngăn bộ nhớ mới thoái hoá về đúng trạng thái đó.
TRUONG_NGUON = ("nguon", "trade_id")


def _now_iso() -> str:
    from datetime import datetime, timedelta, timezone
    return datetime.now(timezone(timedelta(hours=7))).isoformat(timespec="seconds")


def _enabled_by_default() -> bool:
    return os.environ.get("POST_MORTEM_ENABLED", "").strip() == "1"


_ENGINE_CACHE = None

def get_learning_engine(memory_file: str = MEMORY_FILE, enabled: Optional[bool] = None):
    global _ENGINE_CACHE
    if _ENGINE_CACHE is None or _ENGINE_CACHE.memory_file != memory_file:
        _ENGINE_CACHE = PostMortemLearningEngine(memory_file, enabled)
    return _ENGINE_CACHE

class PostMortemLearningEngine:
    """Bộ nhớ mẫu hình cắt lỗ, có ràng buộc thời gian và mặc định tắt."""

    def __init__(self, memory_file: str = MEMORY_FILE,
                 enabled: Optional[bool] = None):
        self.memory_file = memory_file
        self.enabled = _enabled_by_default() if enabled is None else bool(enabled)
        self.sl_patterns: List[Dict[str, Any]] = self.load_memory()
        self._dirty = False

    # ─────────────────────────── Lưu / đọc ──────────────────────────
    def load_memory(self) -> List[Dict[str, Any]]:
        """Nạp bộ nhớ, BỎ mọi mẫu không khai nguồn gốc — và nói ra.

        Im lặng bỏ thì không phân biệt được với "file rỗng"; im lặng nạp
        thì bộ nhớ bịa lại tiếp tục trừ điểm. Cả hai đều đã xảy ra.
        """
        if not os.path.exists(self.memory_file):
            return []
        try:
            with open(self.memory_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"⚠️  Không đọc được {self.memory_file}: "
                  f"{type(e).__name__}: {e}")
            return []
        if not isinstance(data, list):
            return []

        hop_le = [p for p in data
                  if isinstance(p, dict) and all(k in p for k in TRUONG_NGUON)]
        bo = len(data) - len(hop_le)
        if bo:
            print(f"⚠️  Bỏ {bo}/{len(data)} mẫu trong {self.memory_file} vì "
                  f"KHÔNG khai nguồn gốc (thiếu {'/'.join(TRUONG_NGUON)}). "
                  f"Một mẫu không truy được về lệnh nào thì không dùng để "
                  f"trừ điểm ai được. Dựng lại bằng "
                  f"tools/dung_lai_bo_nho.py.")
        return hop_le

    def save_memory(self, force: bool = False) -> None:
        if not self._dirty and not force:
            return
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self.sl_patterns, f, ensure_ascii=False, indent=2)
            self._dirty = False
        except Exception:
            pass

    # ─────────────────────────── Ghi nhận ───────────────────────────
    def record_sl_trade(self, symbol: str, entry_score: int,
                        score_breakdown: dict, key_reasons: list,
                        signal_date: Optional[str] = None,
                        trade_id: Optional[int] = None,
                        nguon: Optional[str] = None,
                        phien_hoc: Optional[str] = None) -> bool:
        """Ghi một mẫu hình cắt lỗ. TỪ CHỐI nếu không khai nguồn gốc.

        `trade_id` và `nguon` là bắt buộc: chúng cho phép truy ngược một
        mẫu về đúng lệnh đã sinh ra nó. Thiếu chúng thì mẫu này y hệt
        6.271 mẫu không truy nguồn được trong file cũ.
        """
        if not self.enabled or not signal_date:
            return False
        if trade_id is None or not nguon:
            return False
        self.sl_patterns.append({
            "symbol": symbol,
            "signal_date": str(signal_date),
            "entry_score": entry_score,
            "trend_score": score_breakdown.get("trend_score", 50),
            "momentum_score": score_breakdown.get("momentum_score", 50),
            "volume_score": score_breakdown.get("volume_score", 50),
            "reasons": key_reasons[:3] if key_reasons else [],
            # ── provenance ──
            "nguon": str(nguon),
            "trade_id": int(trade_id),
            "ghi_luc": _now_iso(),
            # Trục thời gian THỨ HAI: phiên mà mẫu này trở nên biết được,
            # tức phiên lệnh đóng. Khác `signal_date` (phiên sinh tín hiệu).
            "phien_hoc": str(phien_hoc or "")[:10],
        })
        self._dirty = True
        return True

    # ─────────────────────────── Tra cứu ────────────────────────────
    def get_penalty_for_pattern(self, current_breakdown: dict,
                                as_of: Optional[str] = None,
                                phien_hien_tai: Optional[str] = None) -> float:
        """Điểm phạt nếu tín hiệu hiện tại trùng mẫu hình đã từng cắt lỗ.

        HAI hàng rào, hai mục đích khác nhau:

        `as_of` — ngày của phiên đang chấm. Chỉ mẫu có `signal_date` NHỎ HƠN
        `as_of` mới được tính. Đây là hàng rào chống NHÌN TRỘM TƯƠNG LAI, và
        nó không có đường vòng: không có `as_of` thì không có điểm phạt.

        `phien_hien_tai` — chỉ mẫu có `phien_hoc` NHỎ HƠN nó mới được tính.
        Đây là hàng rào giữ TÍNH TÁI LẬP, và một mình `as_of` không làm được
        việc đó. Xét một lệnh tín hiệu 2026-01-05 đóng bằng cắt lỗ ngày
        2026-08-20: `signal_date` của nó nhỏ hơn `as_of`, nên nó LỌT hàng rào
        thứ nhất — dù mẫu đó chỉ tồn tại từ 20/08. Trong chính phiên quét
        20/08, mã A đóng bằng cắt lỗ sẽ làm lệch điểm mã B, và cùng một input
        cho hai kết quả tuỳ thứ tự quét. Đó là sự cố 47-vs-59.

        Cùng hình dạng với bất biến 3: dời stop về hoà vốn chỉ có hiệu lực từ
        phiên sau, vì lệnh dời stop chỉ đặt được sau khi đã thấy giá chạm mốc.

        Không truyền `phien_hien_tai` thì giữ nguyên hành vi cũ, để chỗ gọi
        chưa cập nhật không im lặng đổi kết quả.
        """
        if not self.enabled or not self.sl_patterns or not as_of:
            return 0.0

        as_of = str(as_of)
        c_trend = current_breakdown.get("trend_score", 50)
        c_mom = current_breakdown.get("momentum_score", 50)
        c_vol = current_breakdown.get("volume_score", 50)

        for p in self.sl_patterns:
            past = p.get("signal_date")
            if not past or str(past) >= as_of:
                continue                      # cùng ngày hoặc tương lai -> bỏ

            if phien_hien_tai is not None:
                hoc = p.get("phien_hoc")
                # Không biết học lúc nào thì KHÔNG dùng. Fail-closed: một mẫu
                # không xác định được thời điểm thì không chứng minh được nó
                # đã tồn tại trước phiên này.
                if not hoc or str(hoc)[:10] >= str(phien_hien_tai)[:10]:
                    continue
            if (abs(c_trend - p["trend_score"]) <= MATCH_TOLERANCE and
                    abs(c_mom - p["momentum_score"]) <= MATCH_TOLERANCE and
                    abs(c_vol - p["volume_score"]) <= MATCH_TOLERANCE):
                return PENALTY

        return 0.0
