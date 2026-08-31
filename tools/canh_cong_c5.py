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


def ro_chuan(trades: list):
    """Rổ đối chiếu VN-INDEX cho nhóm lệnh này, hoặc None kèm lý do in ra.

    Điều kiện dừng đo ALPHA khớp từng lệnh, nên chuông cũng cần rổ chuẩn.
    Không dựng được thì `kiem()` sẽ báo "không đo được" — và đó là một
    trạng thái đáng kêu, không phải một trạng thái im lặng.
    """
    try:
        import market_filter
        from paper_metrics import ro_chuan_tu_chuoi_gia

        df = market_filter.get_vni_df()
        if df is None or len(df) == 0:
            print("Không có chuỗi VN-INDEX — không dựng được rổ đối chiếu.")
            return None
        gia = dict(zip(df["time"].astype(str), df["close"].astype(float)))
        return ro_chuan_tu_chuoi_gia(trades, gia) or None
    except Exception as e:
        print(f"Không dựng được rổ đối chiếu: {type(e).__name__}: {e}")
        return None


def kiem(trades: list, cong_dang_mo: bool, benchmark=None) -> tuple[int, str]:
    """(mã thoát, thông điệp). 0 = không phải làm gì, 1 = phải kêu."""
    from paper_metrics import dieu_kien_dong_lai

    dk = dieu_kien_dong_lai(trades, benchmark)
    if not dk.get("do_duoc"):
        # Không đo được KHÔNG phải "không sao". Chuông sinh ra để canh;
        # một cái chuông im lặng vì không nhìn thấy gì thì tệ hơn không có
        # chuông, vì nó tạo cảm giác đang được canh.
        return 1, f"CHUÔNG C5 KHÔNG ĐO ĐƯỢC — {dk['ly_do']}"
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


def kiem_ro_ri(quyet_dinh, cong_dang_mo: bool,
               moc: float, ngay_dong: str) -> tuple[int, str]:
    """Cổng đóng mà vẫn mở được vị thế thì cổng đó chỉ là một dòng chữ.

    `kiem()` phía trên hỏi "điều kiện đã đạt chưa, và cổng còn mở không" —
    cả hai vế đều đọc từ MÃ NGUỒN. Hàm này hỏi một câu khác hẳn, và chỉ
    trả lời được từ DỮ LIỆU: kể từ lúc đóng, có vị thế mới nào được mở
    không. Đó là khác biệt giữa "đã khai là chặn" và "đã chặn".

    Vì sao `acted = 1` là dấu hiệu đúng: `record_decision` chỉ được gọi từ
    `consider_entry`, và `acted = True` chỉ ở nhánh mở vị thế mới
    (`paper_trading.py:612`). `fill_pending` KHÔNG ghi quyết định — nên
    bốn lệnh chờ khớp sau khi đóng cổng không làm chuông này kêu, đúng
    như thiết kế: **đóng cổng không huỷ lệnh chờ**.

    Cổng đang mở thì không có gì để đối chiếu — im lặng ở đó là đúng,
    không phải bỏ sót.
    """
    if cong_dang_mo:
        return 0, "Cổng C5 đang MỞ — không có ràng buộc nào để đối chiếu."
    ro_ri = [q for q in quyet_dinh
             if int(q.get("acted") or 0) == 1
             and float(q.get("at") or 0.0) >= moc]
    if not ro_ri:
        return 0, (f"Cổng C5 ĐÓNG từ {ngay_dong} — 0 quyết định vào lệnh kể "
                   f"từ mốc đó trên {len(quyet_dinh)} quyết định. Cổng chặn "
                   f"THẬT, không chỉ khai trong mã nguồn.")
    ma = sorted({str(q.get("symbol")) for q in ro_ri})
    return 1, (f"CỔNG C5 RÒ RỈ: {len(ro_ri)} quyết định VÀO LỆNH kể từ "
               f"{ngay_dong} trong khi cờ đang ĐÓNG — "
               f"{', '.join(ma[:8])}. Cờ trong mã nguồn nói một đằng, sổ "
               f"lệnh ghi một nẻo; tin sổ lệnh.")


def moc_dong_cong(ngay_dong: str) -> float:
    """Mốc epoch của 00:00 giờ VN ngày đóng cổng.

    `decisions.at` ghi bằng `now_vn().timestamp()`, nên mốc so sánh phải
    cùng múi giờ — lệch 7 tiếng là đủ để một quyết định sáng sớm rơi sai
    phía của mốc.
    """
    import pandas as pd

    from data_quality import now_vn

    return pd.Timestamp(ngay_dong, tz=now_vn().tzinfo).timestamp()


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

    so = PaperTradingJournal(str(tam))
    trades = so.all_trades()
    ma, thong_diep = kiem(trades, pt.CHO_PHEP_MO_LENH_MOI, ro_chuan(trades))

    # Phép đối chiếu THỨ HAI, độc lập với phép trên: cổng đã đóng thì
    # sổ lệnh phải chứng minh được là nó chặn.
    ma_rr, td_rr = kiem_ro_ri(so.decisions(), pt.CHO_PHEP_MO_LENH_MOI,
                              moc_dong_cong(pt.NGAY_DONG_CONG_C5),
                              pt.NGAY_DONG_CONG_C5)

    print(f"Sổ lệnh: {bc['trades']} lệnh · {bc['decisions']} quyết định")
    print(f"paper_trading.CHO_PHEP_MO_LENH_MOI = {pt.CHO_PHEP_MO_LENH_MOI}")
    print(thong_diep)
    print(td_rr)
    if ma:
        print(f"::error::{thong_diep}")
    if ma_rr:
        print(f"::error::{td_rr}")

    tom_tat = os.environ.get("GITHUB_STEP_SUMMARY")
    if tom_tat:
        with open(tom_tat, "a", encoding="utf-8") as f:
            dau = "🔴" if (ma or ma_rr) else "✅"
            print(f"### {dau} Chuông cổng C5", file=f)
            print("", file=f)
            print(thong_diep, file=f)
            print("", file=f)
            print(td_rr, file=f)
    return 1 if (ma or ma_rr) else 0


if __name__ == "__main__":
    sys.exit(main())
