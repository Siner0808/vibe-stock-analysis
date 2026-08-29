"""Chuông cổng C5: điều kiện dừng đã đạt mà cổng vẫn mở thì làm ĐỎ lượt chạy.

VÌ SAO PHẢI LÀ MỘT WORKFLOW RIÊNG
─────────────────────────────────
`tools/chuong_bao_quet.py` đếm lượt chạy `conclusion == "success"` của
workflow "Quét sổ lệnh" để biết một ngày có được quét hay không. Làm đỏ
workflow đó vì cổng C5 sẽ khiến chuông kia báo "ngày này không có lượt
quét nào" — một báo động giả sinh ra từ một cảnh báo thật, và nó che mất
đúng thứ chuông kia sinh ra để canh. `quet-so-lenh.yml` đã ghi nguyên
văn cảnh báo này cho bước cảnh báo nội phiên; đây là cùng một cái bẫy.

Nên: lượt quét vẫn xanh và vẫn TỰ TẮT mở vị thế mới trong lượt đó (xem
`run_daily.thi_hanh_dieu_kien_dung`), còn chuông C5 đỏ riêng ở đây.
GitHub gửi email cho người sửa cron gần nhất khi một workflow theo lịch
thất bại — đó là đường thông báo, không cần dựng thêm gì.

KÊU KHI NÀO
───────────
Chỉ kêu khi có việc phải làm mà chưa ai làm: **điều kiện đạt VÀ cổng vẫn
mở trong mã nguồn**. Điều kiện đạt mà cổng đã đóng là trạng thái ĐÚNG —
kêu lúc đó là dạy người ta bỏ qua chuông.

KHÔNG NHÌN THẤY GÌ CŨNG LÀ KÊU
──────────────────────────────
Kéo sổ hỏng thì thoát khác 0. Ngược hướng với `cua_doc_bat_buoc.py` —
file đó nhường đường khi không chắc vì nó bảo vệ *quy trình*; file này
bảo vệ *tiền*, nên nó nghiêng về phía dừng. Một cái chuông im lặng vì
không nhìn thấy gì thì tệ hơn không có chuông, vì nó tạo cảm giác đang
được canh.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))


def kiem(trades: list, cong_dang_mo: bool) -> tuple[int, str]:
    """(mã thoát, thông điệp). 0 = không phải làm gì, 1 = phải kêu."""
    from paper_metrics import dieu_kien_dong_lai

    dk = dieu_kien_dong_lai(trades)
    if not dk["dat"]:
        trang_thai = "MỞ" if cong_dang_mo else "ĐÓNG"
        return 0, (f"Cổng C5 đang {trang_thai}. Điều kiện dừng CHƯA đạt: "
                   f"{dk['ly_do']}")
    if not cong_dang_mo:
        return 0, (f"Điều kiện dừng ĐÃ ĐẠT và cổng C5 ĐÃ ĐÓNG — đúng trạng "
                   f"thái, không phải làm gì. {dk['ly_do']}")
    return 1, (f"ĐIỀU KIỆN DỪNG ĐÃ ĐẠT NHƯNG CỔNG C5 VẪN MỞ TRONG MÃ NGUỒN. "
               f"{dk['ly_do']}. Đặt paper_trading.CHO_PHEP_MO_LENH_MOI = "
               f"False rồi merge — lượt quét tự tắt trong từng lượt, nhưng "
               f"cờ đó không sống qua lượt sau.")


def _ep_stdout_utf8() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def main() -> int:
    _ep_stdout_utf8()
    import google_sheets_sync as gs
    import paper_trading as pt
    from paper_trading import PaperTradingJournal

    # Sổ tạm: KHÔNG kéo đè lên `paper_trades.db`. Chuông chỉ đọc.
    tam = Path(tempfile.gettempdir()) / "canh_cong_c5.db"
    if tam.exists():
        tam.unlink()

    try:
        bc = gs.keo_so_co_thu_lai(str(tam))
    except Exception as e:
        print(f"::error::Chuông C5 không kéo được sổ lệnh: "
              f"{type(e).__name__}: {e}")
        return 1
    if bc is None:
        print("::error::Chuông C5: kho ngoài chưa cấu hình — không đọc được "
              "sổ lệnh, nên không canh được gì.")
        return 1

    trades = PaperTradingJournal(str(tam)).all_trades()
    ma, thong_diep = kiem(trades, pt.CHO_PHEP_MO_LENH_MOI)

    print(f"Sổ lệnh: {bc['trades']} lệnh · {bc['decisions']} quyết định")
    print(f"paper_trading.CHO_PHEP_MO_LENH_MOI = {pt.CHO_PHEP_MO_LENH_MOI}")
    print(thong_diep)
    if ma:
        print(f"::error::{thong_diep}")

    tom_tat = os.environ.get("GITHUB_STEP_SUMMARY")
    if tom_tat:
        with open(tom_tat, "a", encoding="utf-8") as f:
            dau = "🔴" if ma else "✅"
            print(f"### {dau} Chuông cổng C5", file=f)
            print("", file=f)
            print(thong_diep, file=f)
    return ma


if __name__ == "__main__":
    sys.exit(main())
