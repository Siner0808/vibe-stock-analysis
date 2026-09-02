"""Chuông nguồn đứng: có phiên mà không có nến mới thì làm ĐỎ lượt chạy.

CÁI HỎNG NÓ CANH
────────────────
Ngày 02/09/2026, bốn lệnh chờ không khớp suốt ba ngày. Nguyên nhân là thị
trường nghỉ Quốc khánh — vô hại. Nhưng **một nguồn dữ liệu chết sẽ có đúng
chữ ký ấy**, và chữ ký ấy im lặng hoàn toàn với mọi dụng cụ đang có:

- `chuong_bao_quet.py` đếm lượt quét THÀNH CÔNG. Ba ngày nghỉ đều thành
  công, chuông im — đúng chức năng của nó.
- `run_daily.bao_cua_so_du_lieu()` so SỐ phiên nhận được với kỳ vọng, mà
  kỳ vọng lấy từ chính chuỗi đó. Nguồn đứng thì hai vế cùng đứng.
- `market_filter.is_vni_bullish()` đo độ cũ so với NGÀY ĐANG CHẤM, mà ngày
  ấy chính là nến mới nhất — độ trễ bằng 0 theo định nghĩa.

Cả ba đều đo dữ liệu bằng chính dữ liệu đó. Chuông này đối chiếu với
`lich_giao_dich` — một lịch công bố trước, đến từ ngoài chuỗi giá.

KÉO THẲNG TỪ MẠNG, KHÔNG QUA CACHE
──────────────────────────────────
Dùng `fetch_one` chứ không `get_vni_df()`. Hàm kia ưu tiên cache trên đĩa
— đúng cho backtest (phải tất định), nhưng ở đây cache CHÍNH LÀ thứ có thể
đang che mất việc nguồn đã chết. Một cái chuông đọc bản sao thì nó canh
bản sao.

KHÔNG THẤY GÌ CŨNG LÀ KÊU
─────────────────────────
Kéo hỏng, hoặc lịch hết hạn, đều thoát khác 0. Cùng tinh thần
`canh_cong_c5.py`: một cái chuông im vì không nhìn thấy gì thì tệ hơn
không có chuông, vì nó tạo cảm giác đang được canh.

KHÔNG PHỤ THUỘC SỔ LỆNH
───────────────────────
Chuông chỉ cần chuỗi giá và lịch. Không mở `paper_trades.db`, không cần
credential Google Sheets — nên nó vẫn kêu được đúng vào lúc những thứ kia
hỏng, và đó là lúc cần nó nhất.
"""
from __future__ import annotations

import datetime as _dt
import os
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

import lich_giao_dich as lg   # noqa: E402

#: Múi giờ Việt Nam, khai tại chỗ. Không nhập từ module sổ lệnh: chuông
#: phải chạy được cả khi module đó hỏng.
VN = _dt.timezone(_dt.timedelta(hours=7))

#: Trạng thái nào làm đỏ lượt chạy. `CHUA_BIET` NẰM TRONG DANH SÁCH NÀY —
#: lịch hết hạn là việc phải làm, không phải tin vui.
TRANG_THAI_KEU = (lg.NGUON_DUNG, lg.BANG_SAI, lg.CHUA_BIET)


def ma_thoat(trang_thai: str) -> int:
    """0 nếu yên, 1 nếu phải kêu. Tách riêng để kiểm được không cần mạng."""
    return 1 if trang_thai in TRANG_THAI_KEU else 0


def nen_moi_nhat_tu_mang() -> str | None:
    """Ngày nến VN-INDEX mới nhất mà MẠNG trả về, hoặc None kèm lý do in ra."""
    try:
        import market_filter as mf
        df = mf._btd.fetch_one(
            "VNINDEX", (_dt.datetime.now(VN).date()
                        - _dt.timedelta(days=60)).isoformat(),
            _dt.datetime.now(VN).date().isoformat())
    except Exception as e:
        print(f"::error::Không kéo được VN-INDEX: {type(e).__name__}: {e}")
        return None
    if df is None or len(df) == 0:
        print("::error::Chuỗi VN-INDEX rỗng — không đối chiếu được.")
        return None
    return max(str(t)[:10] for t in df["time"])


def _bao_cao(dong: str) -> None:
    tom_tat = os.environ.get("GITHUB_STEP_SUMMARY")
    if tom_tat:
        with open(tom_tat, "a", encoding="utf-8") as f:
            print(dong, file=f)


def main() -> int:
    hom_nay = _dt.datetime.now(VN).date().isoformat()
    nen = nen_moi_nhat_tu_mang()
    if nen is None:
        _bao_cao("### 🔴 CHUÔNG NGUỒN ĐỨNG: không kéo được VN-INDEX")
        return 1

    trang_thai, thong_diep = lg.chan_doan(nen, hom_nay)
    ma = ma_thoat(trang_thai)

    print(f"Hôm nay {hom_nay} · nến VN-INDEX mới nhất (mạng) {nen}")
    print(f"[{trang_thai}] {thong_diep}")

    if ma:
        print(f"::error::{trang_thai}: {thong_diep}")
        _bao_cao(f"### 🔴 CHUÔNG NGUỒN ĐỨNG — {trang_thai}\n\n{thong_diep}")
    else:
        _bao_cao(f"### ✅ Nguồn dữ liệu theo kịp lịch\n\n{thong_diep}")
    return ma


if __name__ == "__main__":
    raise SystemExit(main())
