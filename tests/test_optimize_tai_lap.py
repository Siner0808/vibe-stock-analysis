"""Bất biến 7 — chạy lại cùng một phép tối ưu phải ra cùng một bảng.

Kế hoạch sửa chữa, mục 5C. Vấn đề KHÔNG phải "20 vòng cho ra 20 kết quả
khác nhau" — đó là điều mong muốn. Vấn đề là **20 vòng đó không độc lập**,
nên "quán quân" thực chất là cực đại của 20 lần thử đã xáo trộn chéo và
phụ thuộc thứ tự luồng. Chạy lại ra bảng khác.

Cơ chế, đọc từ mã:

  paper_runner._ANALYZE_CACHE   khoá (symbol, len(history), last_time)
  master_agent.run()            cộng sl_penalty lấy từ bộ nhớ post-mortem
  post_mortem_learning._ENGINE_CACHE   ở mức module, sl_patterns dùng chung
  optimize_20loops_...py:115    ThreadPoolExecutor(max_workers=8), MỘT tiến trình

`_analyze` ghi nhớ một giá trị KHÔNG phải hàm thuần của khoá: cùng khoá,
bộ nhớ khác thì điểm khác. Vòng 3 đóng một lệnh bằng cắt lỗ, bộ nhớ phình
thêm; vòng 11 gọi `_analyze` cho cùng lát cắt và nhận lại điểm mà vòng 3
đã tính TRƯỚC khi bộ nhớ đổi.
"""
import os
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import numpy as np
import pandas as pd

import paper_runner as pr
from post_mortem_learning import get_learning_engine


def _lich_su(n: int = 140) -> pd.DataFrame:
    close = 50_000 * np.power(1.002, np.arange(n))
    return pd.DataFrame({
        "time": pd.bdate_range("2026-01-01", periods=n).strftime("%Y-%m-%d"),
        "open": close * 0.998, "high": close * 1.006,
        "low": close * 0.994, "close": close,
        "volume": np.full(n, 2_000_000)})


def _luoi_phu_kin() -> list:
    """Mẫu hình phủ kín 0..100 trên cả ba chiều với dung sai 5."""
    return [{"symbol": "SEED", "entry_score": 60,
             "trend_score": t, "momentum_score": m, "volume_score": v,
             "key_reasons": [], "signal_date": "2020-01-01"}
            for t in range(0, 101, 10)
            for m in range(0, 101, 10)
            for v in range(0, 101, 10)]


def test_analyze_khong_tra_diem_cu_khi_bo_nho_da_doi():
    """Cùng lát cắt, bộ nhớ khác nhau, PHẢI cho điểm khác nhau.

    Test này KHÔNG chạm `sl_pattern_memory.json` trên đĩa: nó chỉ đổi
    `sl_patterns` trong RAM và không gọi `save_memory()` lần nào.
    """
    df = _lich_su()
    may = get_learning_engine()

    bat_cu = os.environ.get("POST_MORTEM_ENABLED")
    bo_nho_cu = may.sl_patterns
    da_bat_cu = may.enabled
    cache_cu = pr._ANALYZE_CACHE

    try:
        os.environ["POST_MORTEM_ENABLED"] = "1"
        may.enabled = True
        pr._ANALYZE_CACHE = {}

        # (a) bộ nhớ RỖNG
        may.sl_patterns = []
        diem_rong = pr._analyze("TST", df)["final_score"]

        # (b) CÙNG lát cắt, bộ nhớ đã phình — đúng thứ xảy ra giữa hai vòng
        may.sl_patterns = _luoi_phu_kin()
        diem_day = pr._analyze("TST", df)["final_score"]
    finally:
        pr._ANALYZE_CACHE = cache_cu
        may.sl_patterns = bo_nho_cu
        may.enabled = da_bat_cu
        os.environ.pop("POST_MORTEM_ENABLED", None)
        if bat_cu is not None:
            os.environ["POST_MORTEM_ENABLED"] = bat_cu

    assert diem_rong != diem_day, (
        f"cùng lát cắt cho cùng {diem_rong} điểm dù bộ nhớ đã đổi từ 0 lên "
        f"{len(_luoi_phu_kin())} mẫu — _ANALYZE_CACHE đang trả điểm tính ở "
        f"một trạng thái bộ nhớ KHÁC. Đây là đường mà vòng 3 làm lệch vòng 11.")
    print(f"PASS  bộ nhớ rỗng {diem_rong} điểm · bộ nhớ đầy {diem_day} điểm")


if __name__ == "__main__":
    test_analyze_khong_tra_diem_cu_khi_bo_nho_da_doi()


# ── Nhãn khoảng thời gian phải nói đúng thứ đã chạy ──────────────────
def test_cat_khoang_ton_trong_start_end():
    """`cmd_seed` phải TÔN TRỌNG start/end, hoặc nhãn "18 tháng" là bịa.

    optimize_20loops_custom71_18m.py:67 dựng Namespace(start=..., end=...)
    và in "📅 Khoảng thời gian: ... (18 Tháng gần nhất)". Nhưng subcommand
    `seed` KHÔNG có --start/--end, và `cmd_seed` không đọc hai trường đó:
    nó gọi `load_all()` rồi duyệt trọn file cache. Độ phủ thật lên tới
    ~4,8 năm với 34 mã.
    """
    import pandas as pd

    df = pd.DataFrame({
        "time": ["2021-06-01", "2024-03-01 07:00:00", "2025-07-15",
                 "2026-01-20 07:00:00", "2026-08-01"],
        "close": [1.0, 2.0, 3.0, 4.0, 5.0]})

    het = pr._cat_khoang(df, "2025-01-01", "2026-06-30")
    assert list(het["close"]) == [3.0, 4.0], f"cắt sai: {list(het['close'])}"

    # Cache có HAI định dạng cột time — hàm phải chịu được cả hai.
    assert "2026-01-20 07:00:00" in list(het["time"]), "bỏ mất dòng có hậu tố giờ"

    # Không truyền gì thì giữ nguyên, không được im lặng cắt bớt.
    assert len(pr._cat_khoang(df, None, None)) == len(df)
    assert len(pr._cat_khoang(df, "", "")) == len(df)
    print("PASS  _cat_khoang tôn trọng start/end và chịu được hai định dạng ngày")
