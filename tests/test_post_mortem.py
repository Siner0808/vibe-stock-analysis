"""Test bộ nhớ mẫu hình cắt lỗ.

Cơ chế này từng làm hỏng mọi kết quả đo được của dự án theo hai đường:

  1. Nhìn trộm tương lai — mô phỏng chạy từng mã một, nên khi chấm phiên
     tháng 1/2024 của mã B, bộ nhớ đã chứa lệnh cắt lỗ năm 2026 của mã A.
  2. Không tái lập — file bộ nhớ bị ghi đè trong lúc chạy, cùng một lát dữ
     liệu cho ra điểm khác nhau tuỳ vào việc trước đó đã chạy gì.

Bốn test dưới đây khoá cả hai đường lại.

Chạy offline:  python3 tests/test_post_mortem.py
"""
import itertools
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from post_mortem_learning import PENALTY, PostMortemLearningEngine

BD = {"trend_score": 70, "momentum_score": 60, "volume_score": 55}


def new_engine(enabled=True):
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    os.remove(path)
    return PostMortemLearningEngine(memory_file=path, enabled=enabled), path


#: Đếm để mỗi mẫu gieo có một trade_id riêng.
_dem_seed = itertools.count(1)


def seed(eng, signal_date):
    """Gieo một mẫu hình cắt lỗ KÈM NGUỒN GỐC.

    `record_sl_trade` từ chối mẫu không khai `trade_id` + `nguon` — đó là
    thứ ngăn bộ nhớ thoái hoá về đúng trạng thái file cũ: 6.327 mẫu mà chỉ
    56 (0,89%) truy được về một lệnh thật.
    """
    eng.record_sl_trade("AAA", 70, BD, ["lý do"], signal_date=signal_date,
                        trade_id=next(_dem_seed), nguon="test")


# ─────────────────────────────────────────────────────────────────────
# 1. Không nhìn trộm tương lai — bất biến quan trọng nhất
# ─────────────────────────────────────────────────────────────────────
def test_khong_phat_dua_tren_lenh_lo_xay_ra_sau_do():
    """Mẫu hình ghi ngày 2026 không được ảnh hưởng tới phiên chấm năm 2024."""
    eng, path = new_engine()
    try:
        seed(eng, "2026-05-20")
        assert eng.get_penalty_for_pattern(BD, as_of="2024-01-15") == 0.0, (
            "phiên 2024 bị phạt vì khoản lỗ năm 2026 — nhìn trộm tương lai")
        assert eng.get_penalty_for_pattern(BD, as_of="2026-06-01") == PENALTY
        print("PASS  mẫu hình 2026 không phạt phiên 2024, có phạt phiên 2026-06")
    finally:
        os.path.exists(path) and os.remove(path)


def test_cung_ngay_cung_khong_duoc_tinh():
    """Lệnh cắt lỗ ngày T không thể biết được vào lúc chấm phiên T."""
    eng, path = new_engine()
    try:
        seed(eng, "2026-05-20")
        assert eng.get_penalty_for_pattern(BD, as_of="2026-05-20") == 0.0
        print("PASS  mẫu hình cùng ngày không được tính")
    finally:
        os.path.exists(path) and os.remove(path)


def test_thieu_as_of_thi_khong_co_diem_phat():
    """Không có mốc thời gian thì không so sánh được -> không phạt.

    Đây là hàng rào cuối: quên truyền `as_of` sẽ làm cơ chế im lặng, chứ
    không làm nó lặng lẽ nhìn trộm.
    """
    eng, path = new_engine()
    try:
        seed(eng, "2020-01-01")
        assert eng.get_penalty_for_pattern(BD) == 0.0
        assert eng.get_penalty_for_pattern(BD, as_of=None) == 0.0
        assert eng.get_penalty_for_pattern(BD, as_of="2026-01-01") == PENALTY
        print("PASS  thiếu as_of -> im lặng, không phạt")
    finally:
        os.path.exists(path) and os.remove(path)


# ─────────────────────────────────────────────────────────────────────
# 2. Mặc định tắt cho tới khi có bằng chứng ngoài mẫu
# ─────────────────────────────────────────────────────────────────────
def test_mac_dinh_tat_va_khong_ghi_gi():
    eng, path = new_engine(enabled=False)
    try:
        assert eng.record_sl_trade("AAA", 70, BD, [], signal_date="2020-01-01") is False
        assert eng.sl_patterns == []
        assert not os.path.exists(path), "đang tắt mà vẫn ghi ra file"
        assert eng.get_penalty_for_pattern(BD, as_of="2026-01-01") == 0.0
        print("PASS  khi tắt: không ghi file, không phạt")
    finally:
        os.path.exists(path) and os.remove(path)


def test_bien_moi_truong_quyet_dinh_trang_thai_mac_dinh():
    old = os.environ.get("POST_MORTEM_ENABLED")
    try:
        os.environ.pop("POST_MORTEM_ENABLED", None)
        assert PostMortemLearningEngine(memory_file="/tmp/_x.json").enabled is False
        os.environ["POST_MORTEM_ENABLED"] = "1"
        assert PostMortemLearningEngine(memory_file="/tmp/_x.json").enabled is True
        print("PASS  mặc định TẮT, bật bằng POST_MORTEM_ENABLED=1")
    finally:
        os.environ.pop("POST_MORTEM_ENABLED", None)
        if old is not None:
            os.environ["POST_MORTEM_ENABLED"] = old


# ─────────────────────────────────────────────────────────────────────
# 3. Tái lập — cùng input, cùng kết quả
# ─────────────────────────────────────────────────────────────────────
def test_cham_diem_khong_doi_khi_chay_lai():
    """Chấm cùng một gói dữ liệu hai lần phải cho cùng một điểm.

    Bản trước không đạt: bộ nhớ phình ra giữa hai lần chạy nên lần thứ hai
    dính điểm phạt mà lần đầu không có. Đo được 47 và 59 trên cùng input.
    """
    import numpy as np
    import pandas as pd

    from data_collectors import MarketDataPacket
    from master_agent import MasterConsensusAgent

    n = 140
    close = 50_000 * np.power(1.002, np.arange(n))
    df = pd.DataFrame({
        "time": pd.bdate_range("2026-01-01", periods=n).strftime("%Y-%m-%d"),
        "open": close * 0.998, "high": close * 1.006,
        "low": close * 0.994, "close": close,
        "volume": np.full(n, 2_000_000)})

    agent = MasterConsensusAgent()
    scores = []
    for _ in range(3):
        p = MarketDataPacket(symbol="TST", exchange="HOSE", ohlcv_df=df.copy())
        scores.append(agent.run(p)["final_score"])

    assert len(set(scores)) == 1, f"cùng input cho ra {scores} — không tái lập"
    print(f"PASS  chấm 3 lần cùng một gói dữ liệu -> đều {scores[0]} điểm")


def test_tai_lap_qua_HAI_TIEN_TRINH_voi_post_mortem_BAT():
    """Gate 5A — bất biến 2. Cùng input, post-mortem BẬT, hai TIẾN TRÌNH.

    `test_cham_diem_khong_doi_khi_chay_lai` ở trên chạy ba lần trong CÙNG
    một tiến trình với post-mortem TẮT. Cả hai điều đó làm nó không thể
    bắt được sự cố 47-vs-59:

      • Bất biến 2 nói về trạng thái trên ĐĨA. Trong một tiến trình,
        `_ENGINE_CACHE` ở mức module giữ nguyên bộ nhớ đã nạp, nên file có
        đổi cũng không ai thấy.
      • Post-mortem TẮT nghĩa là cơ chế gây ra sự cố bị tắt ngay trong
        chính test khoá nó.

    Test này khẳng định HAI điều, và điều thứ hai quan trọng ngang điều
    thứ nhất:
      1. hai tiến trình riêng biệt cho cùng một điểm
      2. bộ nhớ THẬT SỰ có tác dụng — điểm khi BẬT phải KHÁC điểm khi TẮT

    Thiếu (2) thì test vẫn xanh khi post-mortem âm thầm không chạy, tức
    lại đúng mẫu "test đúng nhưng dây chưa cắm" mà Phase 0 đã đo được.

    `post_mortem_learning.MEMORY_FILE` là đường dẫn TƯƠNG ĐỐI nên thư mục
    làm việc của tiến trình con quyết định đọc bộ nhớ nào. Nhờ đó test
    không chạm vào `sl_pattern_memory.json` thật.
    """
    import json
    import subprocess
    import sys
    import tempfile
    from pathlib import Path

    goc = Path(__file__).resolve().parent.parent
    kich_ban = goc / "tests" / "_cham_diem_mot_lan.py"

    # Lưới bước 10 với dung sai 5 phủ kín 0..100 trên cả ba chiều, nên mọi
    # breakdown đều khớp và điểm phạt là tất định — không phụ thuộc agent
    # hôm nay tình cờ cho ra con số nào.
    # Mỗi mẫu phải khai nguồn, nếu không load_memory() bỏ hết và test này
    # xanh vì lý do sai: bộ nhớ rỗng thì BẬT và TẮT cho cùng điểm.
    hat_giong = [{"symbol": "SEED", "entry_score": 60,
                  "trend_score": t, "momentum_score": m, "volume_score": v,
                  "key_reasons": [], "signal_date": "2020-01-01",
                  "nguon": "test", "trade_id": i}
                 for i, (t, m, v) in enumerate(
                     ((t, m, v) for t in range(0, 101, 10)
                      for m in range(0, 101, 10)
                      for v in range(0, 101, 10)), 1)]

    def chay(thu_muc, bat):
        moi_truong = dict(os.environ)
        moi_truong["POST_MORTEM_ENABLED"] = "1" if bat else "0"
        moi_truong["PYTHONPATH"] = str(goc)
        moi_truong["PYTHONIOENCODING"] = "utf-8"
        kq = subprocess.run(
            [sys.executable, str(kich_ban)], cwd=str(thu_muc),
            env=moi_truong, capture_output=True, text=True, timeout=600)
        assert kq.returncode == 0, ("tiến trình con lỗi: " + kq.stderr[-2000:])
        return json.loads(kq.stdout.strip().splitlines()[-1])

    with tempfile.TemporaryDirectory() as d:
        Path(d, "sl_pattern_memory.json").write_text(
            json.dumps(hat_giong), encoding="utf-8")
        mot = chay(d, True)
        hai = chay(d, True)
        tat = chay(d, False)

    assert mot["post_mortem_bat"] and hai["post_mortem_bat"],         "post-mortem phải BẬT trong tiến trình con, nếu không test vô nghĩa"
    assert mot["so_mau_doc_duoc"] == len(hat_giong),         f"tiến trình con đọc {mot['so_mau_doc_duoc']} mẫu, chờ {len(hat_giong)}"

    assert mot["final_score"] == hai["final_score"], (
        f"cùng input, post-mortem BẬT, hai tiến trình cho "
        f"{mot['final_score']} và {hai['final_score']} — bất biến 2 vỡ")

    assert mot["final_score"] != tat["final_score"], (
        f"BẬT và TẮT cho cùng {mot['final_score']} điểm — bộ nhớ không hề "
        f"tác động, nên test này không đo được thứ nó tuyên bố đo")

    print(f"PASS  hai tiến trình cùng {mot['final_score']} điểm; "
          f"tắt post-mortem thì {tat['final_score']} -> bộ nhớ có cắn "
          f"{mot['final_score'] - tat['final_score']:+d} điểm")


def test_master_agent_lay_dung_ngay_phien_cuoi():
    import numpy as np
    import pandas as pd

    from data_collectors import MarketDataPacket
    from master_agent import MasterConsensusAgent

    df = pd.DataFrame({
        "time": pd.bdate_range("2026-01-01", periods=40).strftime("%Y-%m-%d"),
        "open": np.full(40, 50_000.0), "high": np.full(40, 50_500.0),
        "low": np.full(40, 49_500.0), "close": np.full(40, 50_000.0),
        "volume": np.full(40, 1_000_000)})
    p = MarketDataPacket(symbol="TST", exchange="HOSE", ohlcv_df=df)
    assert MasterConsensusAgent._session_date(p) == str(df["time"].iloc[-1])

    empty = MarketDataPacket(symbol="TST", exchange="HOSE", ohlcv_df=None)
    assert MasterConsensusAgent._session_date(empty) is None
    print("PASS  mốc thời gian lấy đúng phiên cuối, thiếu dữ liệu -> None")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
        except Exception as e:
            failed += 1
            print(f"FAIL  {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n===== {len(fns) - failed}/{len(fns)} test PASS =====")
    sys.exit(1 if failed else 0)
