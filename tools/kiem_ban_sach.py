"""Chạy bộ test trên một BẢN CHECKOUT SẠCH — giống hệt runner CI.

Vì sao cần: máy phát triển có những thứ mà runner không có —
`.streamlit/secrets.toml`, `paper_trades.db`, `sl_pattern_memory.json`,
`backtest/cache/`. Test đọc phải chúng sẽ xanh ở máy và đỏ trên CI, hoặc
tệ hơn là xanh ở cả hai vì lý do khác nhau.

Ngày 20/08/2026 riêng một phiên đã gặp BA lỗi thuộc loại này:

  1. `test_secrets_toml_ton_tai_nhung_khong_doc_duoc_thi_NO` — streamlit
     cache secrets, nên nhánh đọc-file không bao giờ chạy tới.
  2. `tests/test_market_filter.py` — `test_paper_trading.py` ghim
     `is_vni_bullish` ở mức module và lời ghim đó sống suốt tiến trình.
  3. `test_thieu_key_van_chay_binh_thuong` — không cách ly `st.secrets`,
     nên máy có key thì xanh, runner không có thì đi tiếp tới
     `import vnstock` và nổ ImportError. Đây là lỗi làm CI đỏ.

Cách chạy:  python tools/kiem_ban_sach.py
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent


def main() -> int:
    tam = Path(tempfile.mkdtemp(prefix="kiem_ban_sach_"))
    ban_sao = tam / "sach"
    try:
        print(f"→ clone {GOC.name} @ HEAD vào {ban_sao}")
        r = subprocess.run(["git", "clone", "-q", str(GOC), str(ban_sao)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print("✗ clone thất bại:", r.stderr[-500:])
            return 2

        # Nói ra CHÍNH XÁC cái gì vắng mặt, để không ai tưởng bản sao này
        # giống hệt máy phát triển.
        print("→ bản sạch KHÔNG có:")
        for ten in (".streamlit/secrets.toml", "paper_trades.db",
                    "sl_pattern_memory.json", "backtest/cache"):
            co = (ban_sao / ten).exists()
            print(f"    {'CÓ (?!)' if co else 'không có'}  {ten}")

        print("→ chạy pytest…")
        kq = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-q"],
                            cwd=str(ban_sao))
        if kq.returncode == 0:
            print("\n✓ Bộ test XANH trên bản sạch — CI nhiều khả năng cũng xanh.")
        else:
            print("\n✗ Bộ test ĐỎ trên bản sạch trong khi có thể XANH ở máy bạn.")
            print("  Đó là một test đọc phải thứ chỉ máy phát triển mới có.")
        return kq.returncode
    finally:
        shutil.rmtree(tam, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
