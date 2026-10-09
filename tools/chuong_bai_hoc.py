"""Chuông tiêu chí ra khỏi giai đoạn B: "100% lệnh đóng có bài học trong vòng 1 phiên".

`docs/LO-TRINH.md` giai đoạn B ra khi mọi lệnh ảo đã đóng có bài học (sổ bài học,
`so_bai_hoc.py`) trong vòng một phiên. BƯỚC 167 dựng sổ bài học và đếm lệnh còn
chờ nửa ĐÓNG ngay trên app, nhưng không ai nhìn app mỗi ngày — chuông này nhìn
thay. Nửa ĐÓNG của nhật ký điền ở `run_daily.py` (`hoan_tat_nhat_ky`), và có thể
thiếu rổ chuẩn khi lượt quét không đọc được VN-INDEX; lượt sau thử lại. Chuông kêu
khi một lệnh đã QUÁ HẠN một phiên mà vẫn chưa có bài học.

ĐO GÌ
─────
Định nghĩa nằm ở `so_bai_hoc.do_phu_bai_hoc` (hàm thuần, có test) — file này chỉ
kéo sổ và in:

  • Quần thể: lệnh tiến-về-trước đã ĐÓNG, mở TỪ `NGAY_NHAT_KY_BAT_DAU` trở đi. Lệnh
    mở trước ngày đó không có dòng nhật ký nào và KHÔNG được điền bù (lý do vào
    lệnh phải ghi lúc vào) — đếm riêng, in ra, không làm đỏ. Đếm chúng thì chuông
    đỏ vĩnh viễn ngay từ ngày đầu, và chuông như thế không ai đọc.
  • "Có bài học": dòng nhật ký có nửa ĐÓNG và có rổ chuẩn (phân rã được).
  • "Trong một phiên": hạn là HẾT phiên kế tiếp sau ngày đóng, đếm theo lịch phiên
    của dự án (`lich_giao_dich`), không theo ngày lịch.

MÃ THOÁT — ba nấc, không gộp
────────────────────────────
  0  xanh: không lệnh nào quá hạn (kể cả khi chưa có lệnh nào để đo)
  1  VI PHẠM: có lệnh đóng quá hạn một phiên mà chưa có bài học
  2  CHƯA KIỂM ĐƯỢC: Sheets không đọc được, kho ngoài chưa cấu hình, lịch phiên
     không phủ tới hạn của một lệnh, hoặc lỗi bất ngờ
Chưa kiểm được KHÔNG phải xanh — cùng triết lý `canh_cong_c5.py`: một chuông im
lặng vì không nhìn thấy gì tệ hơn không có chuông. Mã 1 thắng mã 2 khi có cả hai.
Một ngoại lệ chưa bắt thoát mã 1 theo mặc định của Python và lẫn với "vi phạm",
nên `main` bắt hết và trả 2.

CHỈ ĐỌC. Chuông kéo sổ về một file tạm rồi xoá; không đẩy gì lên Sheets, không
ghi vào sổ nào, không in lãi lỗ của lệnh nào (chỉ mã, mã lệnh, ngày ra, lý do).
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

MA_XANH = 0
MA_VI_PHAM = 1
MA_CHUA_KIEM_DUOC = 2


def _ep_stdout_utf8() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def dong_in_ra(kq: dict) -> list[str]:
    """Các dòng báo cáo từ kết quả `do_phu_bai_hoc`. KHÔNG có lãi lỗ."""
    import so_bai_hoc as sbh

    ra = [sbh.cau_tieu_chi_b(kq)]

    def liet_ke(nhan: str, ds: list) -> None:
        if not ds:
            return
        ra.append(f"{nhan}: {len(ds)}")
        for m in ds:
            han = f" · hạn hết {m['han']}" if m.get("han") else ""
            ra.append(f"  - {m.get('symbol')} · lệnh #{m.get('trade_id')} · ra "
                      f"{m.get('exit_date') or '?'}{han} — {m.get('ly_do')}")

    liet_ke("QUÁ HẠN, chưa có bài học", kq["vi_pham"])
    liet_ke("CHƯA KIỂM ĐƯỢC", kq["khong_kiem_duoc"])
    liet_ke("Đang trong hạn (chưa có bài học)", kq["trong_han"])
    if kq["lech_trang_thai"]:
        ra.append(f"Lệch trạng thái (chỉ để biết, không vào kết luận): nhật ký có "
                  f"nửa ĐÓNG nhưng bảng trades không nói CLOSED — lệnh "
                  f"{', '.join(kq['lech_trang_thai'])}")
    return ra


def kiem(trades: list, dong_nk: list, hom_nay: str,
         lich=None) -> tuple[int, list[str], dict]:
    """(mã thoát, các dòng báo cáo, kết quả đo). Hàm thuần — test không cần Sheets."""
    import so_bai_hoc as sbh

    kq = sbh.do_phu_bai_hoc(sbh.lenh_dong_tu_trades(trades), dong_nk, hom_nay, lich)
    ma = {sbh.TT_XANH: MA_XANH, sbh.TT_VI_PHAM: MA_VI_PHAM,
          sbh.TT_CHUA_KIEM_DUOC: MA_CHUA_KIEM_DUOC}[kq["trang_thai"]]
    return ma, dong_in_ra(kq), kq


def doc_so(db_path: str, backend=None):
    """Kéo sổ từ Sheets về `db_path` rồi đọc `(báo cáo kéo, trades, dòng nhật ký)`.

    Báo cáo kéo là None khi kho ngoài chưa cấu hình. Ném `KeoSoThatBai` khi kéo hỏng
    sau số lần thử lại. Đường kéo là `keo_so_co_thu_lai` — cùng đường `canh_cong_c5`
    và lượt quét dùng: mọi lời gọi mạng chạy TRƯỚC mọi lệnh xoá, và đọc không tạo tab.
    """
    import google_sheets_sync as gs
    from nhat_ky_vi_sao import COT_NHAT_KY
    from paper_trading import PaperTradingJournal

    bc = gs.keo_so_co_thu_lai(db_path, backend=backend)
    if bc is None:
        return None, [], []
    so = PaperTradingJournal(db_path)
    try:
        trades = so.all_trades()
        dong_nk = [dict(zip(COT_NHAT_KY, r)) for r in so.db.execute(
            f"SELECT {', '.join(COT_NHAT_KY)} FROM nhat_ky ORDER BY trade_id").fetchall()]
    finally:
        so.db.close()
    return bc, trades, dong_nk


def main(backend=None, hom_nay: str | None = None, lich=None) -> int:
    _ep_stdout_utf8()
    try:
        if hom_nay is None:
            from data_quality import now_vn

            hom_nay = now_vn().strftime("%Y-%m-%d")
        with tempfile.TemporaryDirectory() as tam:
            bc, trades, dong_nk = doc_so(os.path.join(tam, "chuong_bai_hoc.db"), backend)
        if bc is None:
            print("::error::Chuông bài học: kho ngoài (Google Sheets) chưa cấu hình — "
                  "không đọc được sổ lệnh, nên không canh được gì.")
            return MA_CHUA_KIEM_DUOC
        ma, dong, kq = kiem(trades, dong_nk, hom_nay, lich)
    except Exception as e:
        print(f"::error::Chuông bài học KHÔNG KIỂM ĐƯỢC — {type(e).__name__}: {e}")
        return MA_CHUA_KIEM_DUOC

    print(f"Sổ lệnh: {len(trades)} lệnh · {len(dong_nk)} dòng nhật ký · đo ngày {hom_nay}")
    for d in dong:
        print(d)
    if ma == MA_VI_PHAM:
        print(f"::error::{dong[0]}")
    elif ma == MA_CHUA_KIEM_DUOC:
        print(f"::error::Chuông bài học CHƯA KIỂM ĐƯỢC — {dong[0]}")

    tom_tat = os.environ.get("GITHUB_STEP_SUMMARY")
    if tom_tat:
        with open(tom_tat, "a", encoding="utf-8") as f:
            dau = {MA_XANH: "✅", MA_VI_PHAM: "🔴", MA_CHUA_KIEM_DUOC: "🟠"}[ma]
            print(f"### {dau} Chuông bài học (tiêu chí giai đoạn B)", file=f)
            print("", file=f)
            for d in dong:
                print(d, file=f)
    return ma


if __name__ == "__main__":
    sys.exit(main())
