"""Cache phải nối được TỚI HIỆN TẠI mà KHÔNG mất lịch sử.

Đo ngày 20/08/2026: chạy `validate_ohlcv` trên 71 mã của rổ cho ra
0% OK · 31% WARN · 69% BLOCK, gần như hoàn toàn vì `STALE` — 49 mã dữ liệu
cũ 13 ngày, 22 mã cũ 9 ngày. Nhưng không công cụ nào trong dự án sửa được:

    download(force=False)   bỏ qua MỌI mã đã có cache      -> không làm mới
    download(force=True)    ghi đè trọn khoảng             -> MẤT lịch sử
    extend_history()        bỏ qua nếu lịch sử đã đủ xa    -> chỉ nối về quá khứ

Hậu quả thật, quan sát được trong ngày: `backtest/cache/VNINDEX.csv` từ
1.724 phiên (2019-09-13 → 2026-08-07) thành 1.655 phiên
(2020-01-02 → 2026-08-20). Nó tươi lên và mất 4 tháng lịch sử — đúng thứ
bất biến 8 cần để có vùng kiểm định ở quá khứ.

`extend_history()` ĐÃ biết hợp nhất giữ bản ghi cũ. Nó chỉ thiếu một điều
kiện: cache cũ ở ĐUÔI thì cũng phải nối, không chỉ khi thiếu ở ĐẦU.
"""
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import pandas as pd

from backtest import data as bt


def _chuoi(tu: str, den: str) -> pd.DataFrame:
    ngay = pd.bdate_range(tu, den).strftime("%Y-%m-%d")
    n = len(ngay)
    return pd.DataFrame({
        "time": ngay,
        "open": [10.0] * n, "high": [11.0] * n,
        "low": [9.0] * n, "close": [10.5] * n,
        "volume": [1_000_000] * n})


def _dung_cache(tmp, sym, df):
    bt.CACHE_DIR = Path(tmp)
    bt.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(bt.cache_path(sym), index=False)


def test_cache_cu_o_duoi_van_duoc_noi_toi_hien_tai():
    """Lịch sử đã đủ xa NHƯNG đuôi cũ 13 ngày — phải nối, không được bỏ qua."""
    import tempfile

    goc_fetch, goc_dir = bt.fetch_one, bt.CACHE_DIR
    with tempfile.TemporaryDirectory() as tmp:
        try:
            _dung_cache(tmp, "TST", _chuoi("2022-01-03", "2026-08-07"))
            bt.fetch_one = lambda s, a, b, **k: _chuoi("2022-01-03", "2026-08-20")

            doi = bt.extend_history(["TST"], "2022-01-01", "2026-08-20")
            assert "TST" in doi, (
                "bỏ qua mã có lịch sử đủ xa nhưng đuôi cũ 13 ngày — "
                "đây đúng là 69% BLOCK vì STALE")

            sau = pd.read_csv(bt.cache_path("TST"))
            cuoi = str(sau["time"].max())[:10]
            assert cuoi >= "2026-08-19", f"nối xong mà đuôi vẫn {cuoi}"
        finally:
            bt.fetch_one, bt.CACHE_DIR = goc_fetch, goc_dir
    print("PASS  cache cũ ở đuôi được nối tới hiện tại")


def test_noi_toi_hien_tai_KHONG_duoc_lam_mat_lich_su():
    """Đúng thứ đã xảy ra với VNINDEX: tươi lên nhưng mất 4 tháng đầu."""
    import tempfile

    goc_fetch, goc_dir = bt.fetch_one, bt.CACHE_DIR
    with tempfile.TemporaryDirectory() as tmp:
        try:
            _dung_cache(tmp, "TST", _chuoi("2022-01-03", "2026-08-07"))
            # Nguồn chỉ trả về khoảng NGẮN hơn — mô phỏng vnstock giới hạn.
            bt.fetch_one = lambda s, a, b, **k: _chuoi("2025-01-01", "2026-08-20")

            bt.extend_history(["TST"], "2022-01-01", "2026-08-20")
            sau = pd.read_csv(bt.cache_path("TST"))
            dau = str(sau["time"].min())[:10]
            assert dau <= "2022-01-05", (
                f"nối xong thì lịch sử bắt đầu từ {dau} — đã MẤT phần trước đó. "
                f"Đây đúng là chuyện đã xảy ra với VNINDEX.csv trong ngày.")
        finally:
            bt.fetch_one, bt.CACHE_DIR = goc_fetch, goc_dir
    print("PASS  nối tới hiện tại mà vẫn giữ nguyên lịch sử cũ")


def test_cache_da_tuoi_thi_van_bo_qua_khong_goi_mang():
    """Chạy lại nhiều lần phải rẻ: đã đủ và đã tươi thì không tải lại."""
    import tempfile

    goc_fetch, goc_dir = bt.fetch_one, bt.CACHE_DIR
    da_goi = []
    with tempfile.TemporaryDirectory() as tmp:
        try:
            _dung_cache(tmp, "TST", _chuoi("2022-01-03", "2026-08-20"))
            bt.fetch_one = lambda s, a, b, **k: da_goi.append(s)

            bt.extend_history(["TST"], "2022-01-01", "2026-08-20")
            assert not da_goi, "cache đã đủ và đã tươi mà vẫn gọi mạng"
        finally:
            bt.fetch_one, bt.CACHE_DIR = goc_fetch, goc_dir
    print("PASS  cache đủ và tươi -> không gọi mạng")


if __name__ == "__main__":
    for f in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        f()
