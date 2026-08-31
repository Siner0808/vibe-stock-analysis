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
    # Tien trinh con (pytest) ghi thang ra stdout, con print() cua ta bi
    # dem khi output di qua pipe -> thu tu doc bi dao, canh bao quan trong
    # nhat lai hien sau cung. Mot cong cu chan doan doc sai thu tu thi vo
    # dung.
    # Them encoding: thieu no thi console cp1258 cua Windows lam cong cu
    # NO ngay dong print dau tien co dau mui ten. Mot cong cu kiem tra ma
    # khong chay duoc thi khong kiem gi ca -- do la mot cong xanh gia.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace",
                               line_buffering=True)
    except Exception:
        pass

    # `git clone` lay HEAD, KHONG lay cay lam viec. Neu con thay doi chua
    # commit thi bao cao "xanh" o duoi noi ve ban CU -- dung loai dam bao
    # gia ma du an nay hay dinh. Noi ra truoc khi chay.
    ban = subprocess.run(["git", "status", "--porcelain"], cwd=str(GOC),
                         capture_output=True, text=True)
    ban_do = [d for d in ban.stdout.splitlines() if d.strip()]
    if ban_do:
        print("!" * 70)
        print(f"CANH BAO: cay lam viec con {len(ban_do)} muc chua commit.")
        print("Cong cu nay chay tren HEAD, nen ket qua duoi day KHONG noi ve")
        print("nhung thay doi do. Commit truoc roi chay lai.")
        for d in ban_do[:8]:
            print("   ", d)
        if len(ban_do) > 8:
            print(f"    ... va {len(ban_do) - 8} muc nua")
        print("!" * 70)
        print()

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
