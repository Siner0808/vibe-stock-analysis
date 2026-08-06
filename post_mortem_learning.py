"""
post_mortem_learning.py
──────────────────────────────────────────────────────────────────────
Hệ thống Học hỏi từ Nhật ký Thua lỗ (Post-Mortem SL Learning Engine).
Lưu giữ mẫu hình các lệnh dính Stop-Loss (SL) và tạo Điểm Phạt Phản Xạ
để Agent KHÔNG BAO GIỜ lặp lại sai lầm ở các phiên tiếp theo.
"""
import json
import os
from typing import Dict, List, Any

MEMORY_FILE = "sl_pattern_memory.json"

class PostMortemLearningEngine:
    def __init__(self, memory_file: str = MEMORY_FILE):
        self.memory_file = memory_file
        self.sl_patterns: List[Dict[str, Any]] = self.load_memory()

    def load_memory(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def save_memory(self):
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self.sl_patterns, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def record_sl_trade(self, symbol: str, entry_score: int, score_breakdown: dict, key_reasons: list):
        """Ghi nhận đặc trưng kỹ thuật của một lệnh bị dính Cắt lỗ (SL)."""
        pattern = {
            "symbol": symbol,
            "entry_score": entry_score,
            "trend_score": score_breakdown.get("trend_score", 50),
            "momentum_score": score_breakdown.get("momentum_score", 50),
            "volume_score": score_breakdown.get("volume_score", 50),
            "reasons": key_reasons[:3] if key_reasons else []
        }
        self.sl_patterns.append(pattern)
        self.save_memory()

    def get_penalty_for_pattern(self, current_breakdown: dict) -> float:
        """Kiểm tra xem tín hiệu hiện tại có trùng với mẫu hình từng gây SL hay không.
        
        Nếu trùng mẫu hình đã từng dính SL -> Trả về Điểm Phạt Phản Xạ (-12.0 điểm).
        """
        if not self.sl_patterns:
            return 0.0

        c_trend = current_breakdown.get("trend_score", 50)
        c_mom = current_breakdown.get("momentum_score", 50)
        c_vol = current_breakdown.get("volume_score", 50)

        for p in self.sl_patterns:
            # Nếu chênh lệch các chỉ số kỹ thuật < 5% so với mẫu hình đã dính SL
            if (abs(c_trend - p["trend_score"]) <= 5 and
                abs(c_mom - p["momentum_score"]) <= 5 and
                abs(c_vol - p["volume_score"]) <= 5):
                return -12.0  # Điểm phạt nặng phản xạ chống lặp lại sai lầm SL

        return 0.0
