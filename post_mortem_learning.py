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


def _enabled_by_default() -> bool:
    return os.environ.get("POST_MORTEM_ENABLED", "").strip() == "1"


class PostMortemLearningEngine:
    """Bộ nhớ mẫu hình cắt lỗ, có ràng buộc thời gian và mặc định tắt.

    Tham số
    ───────
    memory_file : đường dẫn file bộ nhớ.
    enabled     : None -> lấy theo biến môi trường POST_MORTEM_ENABLED.
                  Đặt True/False để ép trong test.
    """

    def __init__(self, memory_file: str = MEMORY_FILE,
                 enabled: Optional[bool] = None):
        self.memory_file = memory_file
        self.enabled = _enabled_by_default() if enabled is None else bool(enabled)
        self.sl_patterns: List[Dict[str, Any]] = self.load_memory()

    # ─────────────────────────── Lưu / đọc ──────────────────────────
    def load_memory(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.memory_file):
            return []
        try:
            with open(self.memory_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def save_memory(self) -> None:
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self.sl_patterns, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # ─────────────────────────── Ghi nhận ───────────────────────────
    def record_sl_trade(self, symbol: str, entry_score: int,
                        score_breakdown: dict, key_reasons: list,
                        signal_date: Optional[str] = None) -> bool:
        """Ghi mẫu hình của một lệnh vừa dính cắt lỗ.

        `signal_date` là ngày sinh tín hiệu vào lệnh. Thiếu nó thì mẫu hình
        không dùng được (vì không so sánh thời gian được), nên bỏ qua luôn
        thay vì ghi một bản ghi vô dụng.

        Trả về True nếu có ghi.
        """
        if not self.enabled or not signal_date:
            return False
        self.sl_patterns.append({
            "symbol": symbol,
            "signal_date": str(signal_date),
            "entry_score": entry_score,
            "trend_score": score_breakdown.get("trend_score", 50),
            "momentum_score": score_breakdown.get("momentum_score", 50),
            "volume_score": score_breakdown.get("volume_score", 50),
            "reasons": key_reasons[:3] if key_reasons else [],
        })
        self.save_memory()
        return True

    # ─────────────────────────── Tra cứu ────────────────────────────
    def get_penalty_for_pattern(self, current_breakdown: dict,
                                as_of: Optional[str] = None) -> float:
        """Điểm phạt nếu tín hiệu hiện tại trùng mẫu hình đã từng cắt lỗ.

        `as_of` là ngày của phiên đang chấm. Chỉ những mẫu hình có
        `signal_date` NHỎ HƠN `as_of` mới được tính — đây là hàng rào chống
        nhìn trộm tương lai, và nó không có đường vòng: không có `as_of`
        thì không có điểm phạt.
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
            if (abs(c_trend - p["trend_score"]) <= MATCH_TOLERANCE and
                    abs(c_mom - p["momentum_score"]) <= MATCH_TOLERANCE and
                    abs(c_vol - p["volume_score"]) <= MATCH_TOLERANCE):
                return PENALTY

        return 0.0
