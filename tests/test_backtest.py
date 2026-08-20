"""Test cho engine backtest.

Test quan trọng nhất: KHÔNG LOOK-AHEAD.
Một backtest bị rò rỉ tương lai sẽ cho kết quả tuyệt vời và hoàn toàn vô
nghĩa — và không có cách nào phát hiện bằng mắt. Phải test.

Chạy offline:  python3 tests/test_backtest.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd

from backtest import engine, report


def make_df(close: np.ndarray) -> pd.DataFrame:
    n = len(close)
    return pd.DataFrame({
        "time": pd.date_range("2024-01-01", periods=n, freq="B").strftime("%Y-%m-%d"),
        "open": close * 0.999,
        "high": close * 1.005,
        "low": close * 0.995,
        "close": close,
        "volume": np.full(n, 2_000_000),
    })


def trending(n: int, step: float, start: float = 50_000.0) -> np.ndarray:
    return start * np.power(step, np.arange(n))


# ─────────────────────────────────────────────────────────────────────
# 1. BẤT BIẾN SỐ MỘT — không look-ahead
# ─────────────────────────────────────────────────────────────────────
def test_khong_co_look_ahead():
    """Sửa dữ liệu SAU ngày T không được làm đổi điểm TẠI ngày T.

    Cách test: chạy 2 lần trên cùng lịch sử, chỉ khác phần tương lai.
    Nếu điểm khác nhau => engine đang rò rỉ dữ liệu tương lai.
    """
    n, min_hist, h = 200, 60, 20
    base = trending(n, 1.002)

    df_a = make_df(base.copy())

    # Bản B: giống hệt tới phiên 120, sau đó SỤP 50%
    alt = base.copy()
    alt[121:] = alt[121:] * 0.5
    df_b = make_df(alt)

    obs_a = engine.run_symbol("T", df_a, horizons=(h,), min_history=min_hist, stride=1)
    obs_b = engine.run_symbol("T", df_b, horizons=(h,), min_history=min_hist, stride=1)

    a_by_date = {o.date: o for o in obs_a}
    b_by_date = {o.date: o for o in obs_b}

    # Với mọi ngày T <= 120, điểm phải GIỐNG HỆT nhau
    checked = 0
    for date, oa in a_by_date.items():
        ob = b_by_date.get(date)
        if ob is None:
            continue
        idx = list(df_a["time"]).index(date)
        if idx > 120:
            continue
        assert oa.score == ob.score, (
            f"RÒ RỈ TƯƠNG LAI tại {date}: điểm {oa.score} vs {ob.score}. "
            "Engine đang nhìn thấy dữ liệu sau ngày T.")
        assert oa.recommendation == ob.recommendation
        checked += 1

    assert checked >= 30, f"chỉ so được {checked} ngày, chưa đủ tin cậy"
    print(f"PASS  không look-ahead: {checked} ngày cho điểm giống hệt "
          "dù tương lai khác hẳn")


def test_luong_du_lieu_dua_vao_pipeline_bi_cat_dung():
    """Kiểm tra trực tiếp: packet nhận được chỉ chứa dữ liệu đến ngày T."""
    seen = []

    class SpyAgent:
        def run(self, packet):
            seen.append((len(packet.ohlcv_df),
                         packet.ohlcv_df["time"].iloc[-1]))
            return {"final_score": 50, "recommendation": "NẮM GIỮ 👀"}

    df = make_df(trending(150, 1.001))
    engine.run_symbol("T", df, horizons=(20,), min_history=60, stride=10,
                      agent=SpyAgent())

    assert seen, "pipeline chưa từng được gọi"
    for length, last_date in seen:
        # độ dài lịch sử = chỉ số ngày T + 1, và ngày cuối phải đúng là ngày T
        assert df["time"].iloc[length - 1] == last_date
        assert length <= len(df) - 20, "packet chứa dữ liệu vượt quá vùng cho phép"
    print(f"PASS  packet luôn bị cắt đúng đến ngày T ({len(seen)} lần gọi)")


# ─────────────────────────────────────────────────────────────────────
# 2. Tính đúng của phép đo
# ─────────────────────────────────────────────────────────────────────
def test_loi_nhuan_tuong_lai_tinh_dung():
    """Chuỗi tăng đều 0.2%/phiên: lợi nhuận 20 phiên phải ≈ 1.002^20 - 1."""
    step, h = 1.002, 20
    df = make_df(trending(200, step))
    obs = engine.run_symbol("T", df, horizons=(h,), min_history=60, stride=10)

    expected = (step ** h - 1) * 100
    for o in obs:
        assert abs(o.fwd_return[h] - expected) < 1e-6, (o.fwd_return[h], expected)
    print(f"PASS  lợi nhuận {h} phiên = {expected:.2f}% đúng như tính tay "
          f"({len(obs)} quan sát)")


def test_loi_nhuan_vuot_thi_truong_triet_tieu_xu_huong_chung():
    """Hai mã tăng y hệt nhau => excess return của cả hai phải ≈ 0.

    Đây là điểm mấu chốt: nếu cả thị trường tăng 10%, một mã tăng 10%
    KHÔNG phải là thành tích.
    """
    data = {
        "A": make_df(trending(200, 1.002)),
        "B": make_df(trending(200, 1.002, start=80_000.0)),
    }
    obs = engine.run_universe(data, horizons=(20,), min_history=60,
                              stride=10, progress=False)
    assert obs
    for o in obs:
        assert abs(o.excess_return[20]) < 1e-9, o.excess_return[20]
    print(f"PASS  hai mã đi giống nhau -> excess return = 0 ({len(obs)} quan sát)")


def test_excess_return_bat_duoc_ma_vuot_troi():
    """Mã tăng mạnh hơn phải có excess return dương, mã yếu hơn phải âm."""
    data = {
        "MANH": make_df(trending(200, 1.004)),
        "YEU": make_df(trending(200, 1.000)),
    }
    obs = engine.run_universe(data, horizons=(20,), min_history=60,
                              stride=10, progress=False)
    manh = [o.excess_return[20] for o in obs if o.symbol == "MANH"]
    yeu = [o.excess_return[20] for o in obs if o.symbol == "YEU"]
    assert manh and yeu
    assert all(x > 0 for x in manh), manh[:3]
    assert all(x < 0 for x in yeu), yeu[:3]
    print(f"PASS  excess return phân biệt mạnh/yếu: "
          f"{np.mean(manh):+.2f}% vs {np.mean(yeu):+.2f}%")


# ─────────────────────────────────────────────────────────────────────
# 3. Kiểm định thống kê không tự lừa mình
# ─────────────────────────────────────────────────────────────────────
def test_bootstrap_khong_ket_luan_bua_tren_du_lieu_ngau_nhien():
    """Hai nhóm rút từ cùng phân phối => phải báo 'chưa đủ bằng chứng'."""
    rng = np.random.default_rng(42)
    a = rng.normal(0, 5, 300).tolist()
    b = rng.normal(0, 5, 300).tolist()
    r = report.bootstrap_diff(a, b)
    assert not r["significant"], r
    assert "CHƯA" in r["verdict"]
    print(f"PASS  bootstrap không kết luận bừa: {r['diff']:+.2f}% "
          f"[{r['ci'][0]:+.2f}, {r['ci'][1]:+.2f}]")


def test_bootstrap_phat_hien_khac_biet_that():
    rng = np.random.default_rng(42)
    a = rng.normal(5, 5, 300).tolist()
    b = rng.normal(0, 5, 300).tolist()
    r = report.bootstrap_diff(a, b)
    assert r["significant"] and r["diff"] > 3
    print(f"PASS  bootstrap phát hiện khác biệt thật: {r['diff']:+.2f}% "
          f"[{r['ci'][0]:+.2f}, {r['ci'][1]:+.2f}]")


def test_co_so_ngau_nhien_khong_bi_danh_bai_boi_nhan_ngau_nhien():
    """Gán nhãn ngẫu nhiên => p-value không được nhỏ (không có kỹ năng)."""
    rng = np.random.default_rng(7)
    n = 400
    df = pd.DataFrame({
        "ret_20d": rng.normal(1.0, 6, n),
        "excess_20d": rng.normal(0.0, 6, n),
        "bucket": rng.choice(["MUA", "NẮM GIỮ", "BÁN"], n),
        "symbol": "X", "date": "2025-01-01", "score": 50,
    })
    rb = report.random_baseline(df, 20, "ret")
    assert not rb["beats_random"], rb
    print(f"PASS  nhãn ngẫu nhiên KHÔNG đánh bại cơ sở ngẫu nhiên "
          f"(p={rb['p_value']:.3f})")


def test_khong_tim_ra_tin_hieu_trong_nhieu_thuan_tuy():
    """PHÉP THỬ NULL: chạy trên random walk => KHÔNG được có sức dự báo.

    Nếu test này fail, nghĩa là engine đang rò rỉ tương lai hoặc phép đo
    có lỗi — vì trên nhiễu thuần tuý thì không thể có tín hiệu thật.
    Đây là hàng rào cuối chống việc tự lừa mình bằng backtest đẹp.
    """
    rng = np.random.default_rng(11)
    data = {}
    for i, sym in enumerate(["N1", "N2", "N3", "N4", "N5", "N6"]):
        ret = rng.normal(0.0003, 0.017, 400)
        data[sym] = make_df(50_000 * np.exp(np.cumsum(ret)))

    obs = engine.run_universe(data, horizons=(20,), min_history=60,
                              stride=10, progress=False)
    df = engine.to_frame(obs, (20,))
    sub = df[["score", "excess_20d"]].dropna()
    assert len(sub) >= 100, len(sub)

    sc = report.spearman_ci(sub["score"].tolist(), sub["excess_20d"].tolist())
    assert not sc["significant"], (
        f"Tìm ra 'tín hiệu' rho={sc['rho']:+.3f} trên dữ liệu NGẪU NHIÊN — "
        "engine hoặc phép đo có lỗi (nghi ngờ look-ahead)")
    print(f"PASS  phép thử null: rho={sc['rho']:+.3f} "
          f"[{sc['ci'][0]:+.3f}, {sc['ci'][1]:+.3f}] — không có tín hiệu giả")


def test_bao_cao_chay_duoc_va_neu_han_che():
    rng = np.random.default_rng(1)
    n = 200
    df = pd.DataFrame({
        "symbol": rng.choice(["A", "B"], n),
        "date": "2025-06-02",
        "score": rng.integers(20, 90, n),
        "bucket": rng.choice(["MUA MẠNH", "MUA", "NẮM GIỮ", "BÁN"], n),
        "recommendation": "x",
        "ret_20d": rng.normal(1, 5, n),
        "excess_20d": rng.normal(0, 5, n),
    })
    text = report.summarize(df, (20,))
    assert "LỢI NHUẬN VƯỢT THỊ TRƯỜNG" in text
    assert "Chưa trừ phí giao dịch" in text
    assert "KHÔNG chứng minh hệ thống tốt" in text
    assert "NGŨ PHÂN VỊ ĐIỂM" in text
    assert "Tương quan hạng" in text
    print("PASS  báo cáo chạy được và có nêu rõ hạn chế")


def test_canh_bao_khi_mot_phia_vang_mat():
    """Thiếu nhóm MUA phải được cảnh báo to, không im lặng trả NaN."""
    rng = np.random.default_rng(3)
    n = 150
    df = pd.DataFrame({
        "symbol": "A", "date": "2025-06-02",
        "score": rng.integers(35, 60, n),
        "bucket": rng.choice(["NẮM GIỮ", "BÁN"], n),   # không có MUA
        "recommendation": "x",
        "ret_20d": rng.normal(1, 5, n),
        "excess_20d": rng.normal(0, 5, n),
    })
    text = report.summarize(df, (20,))
    assert "KHÔNG THỂ SO SÁNH MUA vs BÁN" in text
    assert "tv_bonus = 0" in text
    assert "nan" not in text.lower(), "không được để lọt giá trị NaN vào báo cáo"
    print("PASS  cảnh báo rõ khi thiếu một phía, không lọt NaN")



def test_ghi_lai_diem_tung_thanh_phan():
    """Backtest phải lưu điểm từng agent, không chỉ điểm tổng.

    Điểm tổng cho một con số; nếu nó bằng 0 thì không biết vì sao. Phân rã
    theo thành phần mới chỉ ra được cái nào mang tín hiệu, cái nào là nhiễu.
    """
    df = make_df(trending(200, 1.002))
    obs = engine.run_symbol("T", df, horizons=(20,), min_history=60, stride=20)
    assert obs, "không có quan sát nào"
    assert obs[0].components, "không ghi lại điểm thành phần"
    for key in ("trend_score", "momentum_score", "volume_score"):
        assert key in obs[0].components, f"thiếu {key}"

    frame = engine.to_frame(obs, (20,))
    assert "trend_score" in frame.columns
    print(f"PASS  ghi {len(obs[0].components)} điểm thành phần vào mỗi quan sát")


def test_bang_phan_ra_khong_ket_luan_bua():
    """Trên nhiễu thuần tuý, không thành phần nào được báo là 'CÓ tín hiệu'."""
    rng = np.random.default_rng(5)
    n = 300
    data = {
        "score": rng.integers(30, 70, n),
        "trend_score": rng.integers(20, 80, n),
        "momentum_score": rng.integers(20, 80, n),
        "excess_20d": rng.normal(0, 6, n),
    }
    frame = pd.DataFrame(data)
    table = report.component_table(frame, 20, "excess")
    assert not table.empty
    assert "CÓ tín hiệu" not in table["Kết luận"].tolist(), table.to_string()
    print(f"PASS  phân rã trên nhiễu -> {len(table)} thành phần, "
          "không cái nào bị kết luận có tín hiệu")


def test_bang_phan_ra_bat_duoc_tin_hieu_that():
    """Thành phần thực sự tương quan phải được nhận ra."""
    rng = np.random.default_rng(6)
    n = 300
    signal = rng.normal(50, 15, n)
    frame = pd.DataFrame({
        "score": rng.integers(30, 70, n),
        "trend_score": signal,
        "excess_20d": signal * 0.3 + rng.normal(0, 4, n),   # tương quan thật
    })
    table = report.component_table(frame, 20, "excess")
    row = table[table["Thành phần"] == "Xu hướng"].iloc[0]
    assert row["Kết luận"] == "CÓ tín hiệu", table.to_string()
    print(f"PASS  phân rã bắt được tín hiệu thật (rho={row['rho']})")


def test_thanh_phan_khong_bien_thien_khong_bao_NaN():
    """Thành phần hằng số phải báo 'không đủ biến thiên', không để lọt NaN."""
    rng = np.random.default_rng(7)
    n = 200
    frame = pd.DataFrame({
        "score": rng.integers(30, 70, n),
        "news_score": [50.0] * n,              # hằng số
        "excess_20d": rng.normal(0, 5, n),
    })
    table = report.component_table(frame, 20, "excess")
    row = table[table["Thành phần"] == "Tin tức"].iloc[0]
    assert row["rho"] == "—" and "không đủ biến thiên" in row["Kết luận"]
    assert "nan" not in table.to_string().lower()
    print("PASS  thành phần hằng số báo rõ, không lọt NaN")


# ─────────────────────────────────────────────────────────────────────
# Nối dài lịch sử — chỗ hai kiểu dữ liệu gặp nhau
# ─────────────────────────────────────────────────────────────────────
def test_ghep_cache_cu_voi_du_lieu_moi_khac_kieu_ngay():
    """Cache CSV cho `time` kiểu chuỗi, vnstock trả Timestamp.

    Ghép thẳng hai thứ đó rồi sắp xếp thì pandas ném
    "'<' not supported between instances of 'Timestamp' and 'str'".
    Lỗi chỉ xuất hiện khi có cache CŨ — chạy trên máy trắng sẽ không thấy.
    """
    import tempfile
    from pathlib import Path

    from backtest import data as bt

    old = pd.DataFrame({                       # như đọc từ CSV: chuỗi
        "time": ["2025-07-17", "2025-07-18"],
        "open": [10.0, 11.0], "high": [11.0, 12.0],
        "low": [9.0, 10.0], "close": [10.5, 11.5],
        "volume": [1000, 1100]})
    fresh = pd.DataFrame({                     # như vnstock trả: Timestamp
        "time": pd.to_datetime(["2022-01-04", "2022-01-05", "2025-07-17"]),
        "open": [5.0, 5.1, 99.0], "high": [5.5, 5.6, 99.0],
        "low": [4.9, 5.0, 99.0], "close": [5.2, 5.3, 99.0],
        "volume": [500, 510, 520]})

    tmp = Path(tempfile.mkdtemp())
    saved_dir, saved_fetch = bt.CACHE_DIR, bt.fetch_one
    try:
        bt.CACHE_DIR = tmp
        old.to_csv(tmp / "TST.csv", index=False)
        bt.fetch_one = lambda *a, **k: fresh

        changed = bt.extend_history(["TST"], "2022-01-01", "2026-01-01")
        assert "TST" in changed, "không nối được lịch sử"

        merged = pd.read_csv(tmp / "TST.csv")
        assert list(merged["time"]) == ["2022-01-04", "2022-01-05",
                                        "2025-07-17", "2025-07-18"]
        # Trùng ngày -> giữ bản GHI CŨ (10.5), không lấy bản mới (99.0)
        row = merged[merged["time"] == "2025-07-17"].iloc[0]
        assert float(row["close"]) == 10.5, (
            "bản ghi cũ bị ghi đè — kết quả trước đó sẽ không tái dựng được")
        print(f"PASS  ghép cache chuỗi + dữ liệu Timestamp -> "
              f"{len(merged)} phiên, giữ bản ghi cũ khi trùng ngày")
    finally:
        bt.CACHE_DIR, bt.fetch_one = saved_dir, saved_fetch


def test_bo_qua_ma_da_du_lich_su():
    """Chạy lại nhiều lần phải an toàn và không gọi mạng thừa."""
    import tempfile
    from pathlib import Path

    from backtest import data as bt

    tmp = Path(tempfile.mkdtemp())
    called = []
    saved_dir, saved_fetch = bt.CACHE_DIR, bt.fetch_one
    try:
        bt.CACHE_DIR = tmp
        # Fixture phải PHỦ THẬT khoảng được yêu cầu. Bản cũ chỉ có 2 phiên
        # tháng 1/2022 trong khi `end` là 2026-01-01 — tức đuôi cũ 4 NĂM mà
        # vẫn bị coi là "đã đủ lịch sử". Nó khoá đúng cái lỗ hổng đã làm 69%
        # rổ bị BLOCK vì STALE mà không công cụ nào sửa được: extend_history
        # chỉ hỏi "lịch sử đã đủ xa chưa", không hỏi "đuôi còn tươi không".
        # Trường hợp đuôi cũ nay do tests/test_cache_tuoi.py khoá riêng.
        _ngay = pd.bdate_range("2022-01-04", "2026-01-01").strftime("%Y-%m-%d")
        _n = len(_ngay)
        pd.DataFrame({"time": _ngay,
                      "open": [1.0] * _n, "high": [1.0] * _n,
                      "low": [1.0] * _n, "close": [1.0] * _n,
                      "volume": [1] * _n}).to_csv(tmp / "TST.csv", index=False)
        bt.fetch_one = lambda *a, **k: called.append(1) or None

        changed = bt.extend_history(["TST"], "2022-01-01", "2026-01-01")
        assert changed == {} and called == [], "gọi mạng dù đã đủ lịch sử"
        print("PASS  mã đã đủ lịch sử -> bỏ qua, không gọi mạng")
    finally:
        bt.CACHE_DIR, bt.fetch_one = saved_dir, saved_fetch


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
