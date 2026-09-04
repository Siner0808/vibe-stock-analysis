"""
run_daily.py
─────────────
Script tự động quét danh mục VN100 và cập nhật Sổ Lệnh Giấy paper_trades.db.
Được lên lịch chạy tự động tại các khung giờ: 09:30, 12:00, 15:15 (Thứ 2 đến Thứ 6).
"""
import os
import sys
import pandas as pd

os.environ["POST_MORTEM_ENABLED"] = "1"
sys.stdout.reconfigure(encoding="utf-8")

from vn100_symbols import CUSTOM_WATCHLIST_SYMBOLS, SECTOR_WATCHLIST
from paper_trading import BUY_THRESHOLD, PaperTradingJournal
from paper_metrics import (dieu_kien_dong_lai, report,
                           ro_chuan_tu_chuoi_gia)
from paper_runner import run_session
from data_collectors import VNStockCollectorAgent
from data_quality import now_vn
import market_filter
import do_tre_khop

DB_PATH = "paper_trades.db"

# NGƯỠNG MUA nhập từ `paper_trading`, KHÔNG khai lại ở đây.
#
# Bản trước cầm 50,0 chạy song song với `paper_trading.BUY_THRESHOLD =
# 62`. Hai con số chưa bao giờ gặp nhau vì cổng C5 đang đóng — mở cổng
# ra thì hệ thống chạy ở 50 trong khi mọi phép đo ngoài mẫu đều đo ở
# 62, và không có gì đỏ.
#
# 62 là con số `walkforward.chay()` chọn theo luật nêu trước (≥30 lệnh
# trên IS, rồi kỳ vọng cao nhất), trên vùng chưa thể đã nhìn. 50,0 là
# 'quán quân' của 20 vòng tối ưu chạy trên CÙNG một bộ dữ liệu — đúng
# thứ bất biến 7 cấm.

def canh_bao_nguon(quet_duoc: int, bo_qua: dict, tong_ma: int) -> str:
    """Chuỗi cảnh báo cho dòng "Số mã quét được" trong báo cáo phiên.

    Hàm thuần, tách ra khỏi thân `execute_daily_scan` để kiểm được không
    cần mạng. "0 lệnh" phải nói được VÌ SAO: một ngày cả rổ mất nguồn cho
    ra đúng cùng một con số với một ngày không có tín hiệu nào.

    Ngưỡng một nửa: quét được dưới nửa rổ thì phiên đó không kết luận được
    gì về thị trường — nó chỉ kết luận được rằng nguồn dữ liệu đang hỏng.
    """
    ra = ""
    if bo_qua:
        chi_tiet = " · ".join(f"{k}: {v}" for k, v in sorted(bo_qua.items()))
        ra = f" — bỏ qua {sum(bo_qua.values())} mã ({chi_tiet})"
    if tong_ma and quet_duoc * 2 < tong_ma:
        ra += (f" · ⛔ CHỈ QUÉT ĐƯỢC {quet_duoc}/{tong_ma} MÃ — phiên này "
               f"không kết luận được gì về thị trường")
    return ra


#: Cửa sổ dữ liệu của MỘT lượt quét, tính bằng ngày lịch.
#:
#: Bản cũ: 60 ngày = **44 phiên**. Đó không phải một lựa chọn có cân nhắc,
#: và nó là thứ có ảnh hưởng lớn nhất tới việc mã nào được mua.
#:
#: Đo ngày 29/08/2026, cả 71 mã, hai lượt độc lập cho cùng kết quả
#: (`docs/STATE.md` — "BƯỚC 2 — ĐO CHỖ TỐI"):
#:
#:     44 -> 288 phiên : |lệch| 5,51 điểm · 29/68 mã lệch ≥5 · ĐỔI 6/68
#:    288 -> 747 phiên : |lệch| 1,97 điểm · 10/68 mã lệch ≥5 · ĐỔI 1/68
#:
#: Cơ chế: `_compute_local_indicators()` trả None cho SMA50 dưới 50 phiên
#: và SMA200 dưới 200 phiên. Thiếu chúng thì các luật dài hạn của agent xu
#: hướng bị bỏ qua và `trend_score` kẹt trong 35/50/65 — không bao giờ
#: chạm 100 hay 15.
#:
#: Vì sao 1095 chứ không phải 420: ngưỡng 62 do Phase 5D chọn bằng
#: walk-forward, mà `walkforward.py` truyền `df.iloc[: t + 1]` — cửa sổ MỞ
#: RỘNG, hàng trăm phiên. Ngưỡng và điểm phải cùng một phân phối. 1095
#: ngày ≈ 747 phiên là mức gần nhất với walk-forward mà vẫn chạy lọt hạn
#: mức thời gian của Actions.
#:
#: GIÁ PHẢI TRẢ, đo thật ngày 29/08/2026 (tải + chấm, 8 mã):
#:     420 ngày  → 2,35 s/mã → 71 mã ≈  4,0 phút
#:    1095 ngày  → 8,88 s/mã → 71 mã ≈ 11,7 phút
#: Vì thế `quet-so-lenh.yml` nới `timeout-minutes` từ 25 lên 40. Đổi hằng
#: số này lên nữa mà không nới thời gian là tự tạo một phiên quét chết
#: giữa chừng — `tests/test_cua_so_du_lieu_quet.py` khoá cặp đó lại.
NGAY_LICH_SU = 1095

#: Tỷ lệ tối thiểu giữa TRUNG VỊ số phiên nhận được và số phiên VN-INDEX có
#: trong cùng cửa sổ. Dưới mức này là dấu hiệu nguồn đang cắt lịch sử.
#:
#: Ngưỡng này KHÔNG tinh tế, và đó là chủ ý: khoảng cần phân biệt là 6%
#: (44 trên 747 phiên — cấu hình trước 29/08/2026) so với ~100%. Mọi giá
#: trị trong dải 0,5–0,9 cho cùng một kết luận. Chọn 0,80 để chừa chỗ cho
#: nghỉ lễ và mã tạm ngừng giao dịch.
TY_LE_PHIEN_TOI_THIEU = 0.80


def phien_ky_vong(start_date: str, end_date: str) -> tuple[int | None, str]:
    """Số phiên VN-INDEX nằm trong cửa sổ — kỳ vọng ĐO ĐƯỢC, không gõ tay.

    Vì sao lấy từ chỉ số chứ không tính bằng "52 tuần × 5 ngày trừ lễ":
    một con số gõ tay không biết runner hôm nay thấy được gì. Chuỗi
    VN-INDEX kéo trên CHÍNH máy đang quét, cùng gói, cùng lúc — nên nó là
    thước đo tại chỗ, và nó tự đúng lại khi lịch nghỉ đổi.

    Trả `(None, lý do)` khi không dựng được. Không đoán một con số thay thế:
    một kỳ vọng bịa ra sẽ đẻ ra cảnh báo giả hoặc im lặng giả, mà cả hai
    đều tệ hơn việc nói thẳng là chưa đo được.
    """
    try:
        df = market_filter.get_vni_df()
        if df is None or len(df) == 0:
            return None, "không có chuỗi VN-INDEX"
        ngay = df["time"].astype(str).str[:10]
        trong_cua_so = ngay[(ngay >= start_date) & (ngay <= end_date)]
        return int(len(trong_cua_so)), str(ngay.iloc[-1])
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def bao_cua_so_du_lieu(phien_nhan, ky_vong, ngay_ro) -> tuple[str, str]:
    """(dòng luôn in, dòng cảnh báo hoặc rỗng) về cửa sổ dữ liệu thật nhận.

    HỎI 1095 NGÀY KHÔNG CÓ NGHĨA LÀ NHẬN ĐỦ. Ngày 29/08/2026 đã đo được
    rằng cửa sổ dữ liệu — chứ không phải gói vnstock hay TradingView — là
    thứ lật 6/71 quyết định: dưới 50 phiên thì SMA50/SMA200 trả None và
    agent xu hướng kẹt ở ba nấc. Ngưỡng mua do walk-forward chọn trên phân
    phối điểm của cửa sổ DÀI, nên chạy nó trên cửa sổ ngắn là áp một
    ngưỡng lên một phân phối khác.

    Cửa sổ ở máy local đã đo được. Cửa sổ mà GÓI MIỄN PHÍ trên runner
    thật sự trả về thì CHƯA — `CLAUDE.md` ghi thẳng đó là chỗ chưa đo.
    Hàm này biến mỗi lượt quét thành một phép đo của chính nó.
    """
    if not phien_nhan:
        return "CỬA SỔ DỮ LIỆU: không mã nào chấm được — không đo được.", ""
    xep = sorted(phien_nhan)
    trung_vi = xep[len(xep) // 2]
    duoi_50 = sum(1 for x in xep if x < 50)
    dong = (f"CỬA SỔ DỮ LIỆU: {len(xep)} mã · trung vị {trung_vi} phiên "
            f"(ít nhất {xep[0]} · nhiều nhất {xep[-1]}) · {duoi_50} mã dưới "
            f"50 phiên — mốc SMA50/SMA200 trả None")
    if ky_vong is None:
        return f"{dong} · chưa so được với kỳ vọng ({ngay_ro})", ""
    dong += f" · kỳ vọng {ky_vong} phiên theo VN-INDEX tới {ngay_ro}"
    if ky_vong <= 0:
        return dong, ""
    ty_le = trung_vi / ky_vong
    if ty_le >= TY_LE_PHIEN_TOI_THIEU:
        return dong, ""
    return dong, (
        f"CỬA SỔ DỮ LIỆU BỊ CẮT: trung vị {trung_vi} phiên trên kỳ vọng "
        f"{ky_vong} ({ty_le:.0%}). Ngưỡng {BUY_THRESHOLD} được walk-forward "
        f"hiệu chuẩn trên cửa sổ dài; điểm của cửa sổ ngắn là một phân phối "
        f'KHÁC. Xem docs/STATE.md, mục "BƯỚC 2 — ĐO CHỖ TỐI".')


def thi_hanh_dieu_kien_dung(trades, dat_co,
                            benchmark=None) -> tuple[bool, str]:
    """Điều kiện dừng phải ĐỔI TRẠNG THÁI, không chỉ in ra một câu.

    Đây là chỗ vá nguyên nhân 4 trong `docs/STATE.md` — "GỐC RỄ CỦA CỔNG
    C5". Trước hàm này, `dieu_kien_dong_lai()` chỉ được gọi bên trong
    `paper_metrics.report()`, một hàm nối chuỗi: khi điều kiện đạt, nó
    thêm một CÂU VĂN nhờ con người đi sửa mã nguồn, và câu văn đó đi vào
    một tệp zip lưu 14 ngày. Kể cả nếu điều kiện có lực phát hiện 100%,
    nó vẫn không đóng được cổng.

    `benchmark` — rổ đối chiếu VN-INDEX ({(ngày vào, ngày ra): %}). Điều
    kiện đo ALPHA khớp từng lệnh (bất biến 6), nên THIẾU rổ này thì nó
    KHÔNG kết luận gì — và nói ra điều đó, không lặng lẽ quay về kỳ vọng.

    `dat_co(gia_tri)` — hàm đặt `paper_trading.CHO_PHEP_MO_LENH_MOI`.
    Truyền vào chứ không gán thẳng trong đây, để test chứng minh được
    trạng thái ĐÃ đổi mà không phải vá module rồi dọn.

    Trả `(đã_đóng, thông_điệp)`.

    BỐN THỨ HÀM NÀY KHÔNG LÀM — phải biết, vì một hàng rào mà người ta
    tưởng nhầm phạm vi thì tệ hơn không có hàng rào:

    1. **Không huỷ lệnh PENDING.** `fill_pending()` khớp bằng giá mở cửa
       phiên sau và không đọc cờ này. Lệnh đã cam kết vẫn vào.
    2. **Không đóng vị thế đang mở.** Dừng MỞ THÊM khác với thoát hàng.
    3. **Không phải chốt một cửa.** Cờ đặt ở đây chỉ sống trong tiến
       trình này; lượt sau tính lại từ đầu. Chốt bền duy nhất hiện có là
       `CHO_PHEP_MO_LENH_MOI = False` trong MÃ NGUỒN, do người sửa, khoá
       bởi `tests/test_c5_noi_that.py`. Kho ngoài chỉ có hai bảng
       `trades` và `decisions`, không có chỗ nào ghi được một lá cờ sống
       qua nhiều lượt chạy trên nhiều runner.
    4. **Không làm đỏ lượt quét.** `tools/chuong_bao_quet.py` đếm lượt
       `conclusion == "success"` của workflow "Quét sổ lệnh" để biết một
       ngày có được quét không; làm đỏ nó ở đây sẽ sinh ra báo động giả
       "ngày này không có lượt quét nào" và che mất đúng thứ chuông sinh
       ra để canh. Chuông riêng cho C5 nằm ở `tools/canh_cong_c5.py`.
    """
    dk = dieu_kien_dong_lai(trades, benchmark)
    if not dk["dat"]:
        dau = "" if dk.get("do_duoc") else "⚠️ "
        return False, f"{dau}Cổng C5 (mở vị thế mới): {dk['ly_do']}"
    dat_co(False)
    return True, (
        "ĐIỀU KIỆN DỪNG ĐÃ ĐẠT — đã TẮT mở vị thế mới cho lượt quét này. "
        f"{dk['ly_do']}. Đặt paper_trading.CHO_PHEP_MO_LENH_MOI = False "
        "trong mã nguồn để nó sống qua lượt sau.")


def trang_thai_c5(cho_phep: bool, nguong: float) -> tuple[str, str]:
    """(dòng trạng thái, khối giải thích) cho báo cáo phiên — SUY RA từ cờ.

    Bản cũ viết CỨNG hai chỗ này trong template: "⛔ DỪNG mở vị thế mới
    (ô C5)" và một khối dài giải thích vì sao 0 lệnh. Đúng lúc viết
    (20/08/2026), SAI từ 24/08 khi cổng mở — và lượt quét 28/08/2026
    21:13 MỞ 4 LỆNH trong khi chính báo cáo của nó nói đang dừng mở vị
    thế mới. Suốt 5 ngày không ai đọc ra điều đó từ báo cáo.

    Cùng lỗi với dòng post-mortem trong `execute_daily_scan`: một câu
    khẳng định về hành vi mà không đọc hành vi thì chỉ đúng cho tới lần
    sửa sau.

    Tách ra mức module vì một chuỗi nằm giữa hàm quét 300 dòng cần cả
    mạng lẫn sổ lệnh mới chạm tới được — tức là không test được, tức là
    lại một câu chữ không ai canh.
    """
    if cho_phep:
        return (f"✅ CHO PHÉP mở vị thế mới — ô C5 MỞ, ngưỡng {nguong:.1f}",
                "> ✅ **Ô C5 đang MỞ.** Mã đạt ngưỡng SẼ được vào lệnh. Điều "
                "kiện đóng lại nằm ở `paper_metrics.dieu_kien_dong_lai()`; "
                "trạng thái của nó in ở mục 5 bên dưới.")
    return ("⛔ DỪNG mở vị thế mới — ô C5 ĐÓNG",
            "> ⛔ **Vì sao 0 lệnh mới, kể cả khi có mã vượt ngưỡng.** Ô C5 "
            "đóng ngày 29/08/2026. Điều kiện dừng cũ đo bằng KỲ VỌNG chứ "
            "không phải alpha khớp từng lệnh, hiệu chuẩn cho mức −2,5%/lệnh "
            "trong khi mức bất lợi đo được là −0,927%, và KHÔNG CÓ GÌ thi "
            "hành nó khi đạt. Mở lại khi điều kiện được viết lại theo alpha "
            "VÀ có nơi hành động. Xem `docs/STATE.md`, mục \"GỐC RỄ CỦA "
            "CỔNG C5\".")


def _ro_chuan_vnindex(trades):
    """Rổ đối chiếu VN-INDEX cho báo cáo phiên — bất biến 6.

    Trước đây `report(trades)` được gọi KHÔNG có tham số benchmark, nên
    `vs_benchmark` có test nhưng chưa bao giờ chạy trên đường tự động:
    đúng mẫu "test đúng nhưng dây chưa cắm". Mọi báo cáo phiên đều in
    "Chưa có đối chiếu chuẩn", tức lợi nhuận cộng dồn không nói lên được
    gì vì không biết thị trường chung đi thế nào cùng kỳ.

    Không dựng được thì trả None và NÓI RA lý do; báo cáo khi đó vẫn in
    cảnh báo thiếu đối chiếu như cũ. Lệnh nào không tìm được cặp ngày sẽ
    được `vs_benchmark` đếm vào `bo_qua` và báo cáo in ra con số đó —
    cache VN-INDEX đóng băng ở 2026-08-07 nên các lệnh đóng sau ngày đó
    chắc chắn rơi vào nhóm này, và điều đó phải nhìn thấy được.
    """
    try:
        import market_filter
        df = market_filter.get_vni_df()
        if df is None or len(df) == 0:
            print("⚠️  Không có chuỗi VN-INDEX — báo cáo phiên sẽ thiếu đối chiếu chuẩn.")
            return None
        gia = dict(zip(df["time"].astype(str), df["close"].astype(float)))
        ro = ro_chuan_tu_chuoi_gia(trades, gia)
        if not ro:
            print("⚠️  Rổ đối chiếu VN-INDEX rỗng — không lệnh nào khớp cặp ngày.")
            return None
        return ro
    except Exception as e:
        print(f"⚠️  Không dựng được rổ đối chiếu VN-INDEX: {type(e).__name__}: {e}")
        return None


def execute_daily_scan():
    import time as _time
    moc_bat_dau = _time.time()
    now_time = now_vn()
    session_name = "SÁNG (09:30)" if now_time.hour < 11 else ("TRƯA (12:00)" if now_time.hour < 14 else "CHIỀU ATC (15:15)")
    print("=" * 80)
    print(f"🚀 KÍCH HOẠT QUÉT THỊ TRƯỜNG DỰ BÁO VIBE CODING - PHIÊN {session_name}")
    print(f"⏰ Thời gian: {now_time:%Y-%m-%d %H:%M:%S}")
    print(f"📌 Rổ chứng khoán Theo dõi: Danh mục Tùy chỉnh 16 Ngành ({len(CUSTOM_WATCHLIST_SYMBOLS)} mã)")
    print(f"📌 Ngưỡng điểm mua: {BUY_THRESHOLD} điểm (Tối ưu từ 20 Vòng lặp)")
    # "Self-Improving AI (Post-Mortem Memory Loop ACTIVE)" la mot khang dinh
    # sai o hai muc. Mot: bo nho cu la 6.327 mau dư luong in-sample, chi
    # 56 (0,89%) truy duoc ve mot lenh that -- no khong hoc, no lap lai ket
    # qua cua chinh cac vong toi uu. Hai: `save_memory()` khong duoc goi o
    # BAT KY dau, nen no khong tich luy gi ca. Noi dung thu dang chay.
    from post_mortem_learning import get_learning_engine as _may
    _pm = _may()
    # Dòng này SUY RA từ trạng thái, không khẳng định một hằng số. Bản cũ
    # viết cứng "CHƯA tích luỹ (save_memory chưa được gọi ở đâu)" — đúng lúc
    # viết, sai từ 21/08/2026 khi save_memory() được bật cho sổ thật, và nó
    # vẫn được in ra mỗi phiên quét trong suốt thời gian đó. Một câu khẳng
    # định về hành vi mà không đọc hành vi thì chỉ đúng cho tới lần sửa sau.
    _ghi = _pm.enabled and not getattr(_pm, "chi_doc", False)
    # Tính chuỗi RA NGOÀI f-string. Bản đầu đặt biểu thức điều kiện xuống
    # dòng ngay trong ô thay thế — cú pháp đó là PEP 701, chỉ có từ Python
    # 3.12. Máy phát triển chạy 3.13 nên nó nạp bình thường; CI chạy 3.11
    # nên `ast.parse` nổ ở đúng dòng này và hai test đỏ.
    _cach = ("CÓ tích luỹ — mỗi lệnh cắt lỗ ghi thêm một mẫu" if _ghi
             else "chỉ đọc, không ghi thêm")
    print(f"📌 Post-mortem: {'BẬT' if _pm.enabled else 'TẮT'}"
          f" · {len(_pm.sl_patterns)} mẫu, đều từ lệnh thật đã đóng"
          f" · {_cach}")
    if _ghi:
        print("   ↳ đo 21/08/2026: cơ chế này CHƯA cho bằng chứng nó giúp gì"
              " — xem docs/ket-qua-bo-nho-rieng-20260821.md")
    # Bat bien: bao cao nao noi "da loc theo xu huong thi truong" deu phai
    # goi status() truoc. Ban cu KHONG he nhac toi bo loc -- grep
    # "market_filter|status()" run_daily.py tra ve 0 -- nen suot 14 ngay
    # khong ai biet cong da dong cung.
    #: Nguồn nào đếm ra con số "trễ N phiên" — ba nấc, ba câu khác nhau.
    #: Bản trước chỉ có một câu "(ước tính theo ngày làm việc)" gắn với một
    #: cờ hai trạng thái, nên khi có thêm nấc giữa thì câu đó thành sai.
    _NHAN_NGUON_DEM = {
        market_filter.NGUON_QUAN_SAT: " (lịch phiên đo được trong lượt này)",
        market_filter.NGUON_CONG_BO: " (theo lịch công bố — chưa nạp lịch quét)",
        market_filter.NGUON_LAM_VIEC: " (ƯỚC TÍNH theo ngày làm việc — "
                                      "không có lịch nào phủ)",
    }
    _cong = market_filter.status()
    print(f"📌 Cổng VN-INDEX: {'BẬT' if _cong.get('active') else 'TẮT'}"
          f" · dữ liệu tới {_cong.get('ngay_cuoi', '?')}"
          f" · trễ {_cong.get('tuoi_phien', '?')} phiên"
          f"{_NHAN_NGUON_DEM.get(_cong.get('nguon_dem'), '')}")
    print("=" * 80)

    # ── KÉO SỔ LỆNH TỪ KHO NGOÀI TRƯỚC KHI QUÉT ──────────────────────
    # Bắt buộc khi có nhiều nơi cùng quét (máy này + GitHub Actions).
    #
    # Không kéo trước thì mỗi nơi đánh số `seq` theo sổ riêng của nó. Ví dụ
    # thật ngày 14/08: sheet ở seq 9.282, sổ máy ở 9.142. Máy quét xong sẽ
    # sinh seq 9.143–9.212, mà push() chỉ đẩy dòng có seq > 9.282 — nên 70
    # quyết định vừa ghi bị BỎ QUA lặng lẽ. Không nổ, không log, chỉ mất.
    #
    # Kéo trước thì cả hai nơi cùng nối tiếp dãy seq của sheet, không đụng
    # nhau. Điều kiện còn lại là đừng chạy trùng giờ.
    _da_keo = False
    try:
        import sheets_store as _ss
        if _ss.open_from_secrets() is not None:
            import google_sheets_sync as _gs
            _bc = _gs.restore_journal_from_google_sheets(
                DB_PATH, allow_overwrite=True)
            _da_keo = True
            print(f"⬇️ Đã kéo sổ lệnh từ kho ngoài: {_bc['trades']} lệnh, "
                  f"{_bc['decisions']} quyết định.")
        else:
            print("ℹ️ Kho ngoài chưa cấu hình — quét trên sổ lệnh của máy này.")
    except Exception as _e:
        # Kho ngoài CÓ cấu hình nhưng kéo hỏng: DỪNG. Quét tiếp trên sổ cũ
        # rồi đẩy lên sẽ làm mất lặng lẽ đúng như mô tả ở trên.
        print(f"🚨 KÉO SỔ LỆNH THẤT BẠI: {type(_e).__name__}: {_e}")
        print("   Dừng phiên quét để không ghi đè lên dữ liệu mới hơn trên kho ngoài.")
        raise

    journal = PaperTradingJournal(DB_PATH, cho_phep_so_that=True)

    # ── THI HÀNH ĐIỀU KIỆN DỪNG — TRƯỚC vòng quét, không phải sau ────
    # Đặt sau vòng quét thì lượt này đã kịp mở lệnh rồi mới đóng cổng:
    # muộn đúng một phiên, và phiên đó là phiên đáng lẽ không được có.
    #
    # Đọc/ghi cờ qua thuộc tính module chứ không qua `from ... import`:
    # bản sao lấy lúc nạp thì gán vào không ai thấy.
    import paper_trading as _pt
    _so_truoc_quet = journal.all_trades()
    _c5_da_dong, _c5_thong_diep = thi_hanh_dieu_kien_dung(
        _so_truoc_quet,
        lambda v: setattr(_pt, "CHO_PHEP_MO_LENH_MOI", v),
        _ro_chuan_vnindex(_so_truoc_quet))
    print(f"🚦 {_c5_thong_diep}")
    if _c5_da_dong:
        # Annotation đọc được qua API công khai; nhật ký chạy và artifact
        # thì đòi đăng nhập. Đó là khác biệt giữa chẩn đoán được từ xa và
        # phải đoán.
        print(f"::error::{_c5_thong_diep}")
        _tom_tat = os.environ.get("GITHUB_STEP_SUMMARY")
        if _tom_tat:
            with open(_tom_tat, "a", encoding="utf-8") as _f:
                print("### 🔴 CỔNG C5 TỰ ĐÓNG TRONG LƯỢT NÀY", file=_f)
                print("", file=_f)
                print(_c5_thong_diep, file=_f)
    start_date = (now_time - pd.Timedelta(days=NGAY_LICH_SU)).strftime("%Y-%m-%d")
    end_date = now_time.strftime("%Y-%m-%d")

    opened_count = 0
    closed_count = 0
    pending_count = 0

    scan_details = []
    # Đếm mã bị BỎ QUA và vì sao. Trước 24/08/2026 nhánh `break` bên dưới
    # im lặng hoàn toàn: một ngày mà cả 71 mã trả SYNTHETIC (mất nguồn) ra
    # đúng cùng một báo cáo với một ngày không có tín hiệu nào — '0 lệnh'.
    # Cổng C5 đóng thì hai thứ đó như nhau; cổng mở rồi thì chúng khác hẳn.
    bo_qua = {}
    quet_duoc = 0
    _da_nap_lich = False
    # Số phiên nến THẬT SỰ nhận được cho từng mã đã chấm được điểm.
    phien_nhan = []
    collector = VNStockCollectorAgent()

    import time
    for idx, sym in enumerate(CUSTOM_WATCHLIST_SYMBOLS, 1):
        retry = 0
        while retry < 3:
            try:
                res = collector.collect(sym, start_date, end_date, exchange="HOSE")
                if res.get("status") != "OK":
                    note = str(res.get("note", ""))
                    if "Rate limit" in note or "GIỚI HẠN API" in note:
                        print(f"  ⏳ {sym}: Dính Rate Limit API (60 req/min). Tự động chờ 40 giây...")
                        time.sleep(40)
                        retry += 1
                        continue
                    ly_do = str(res.get("status", "?"))
                    bo_qua[ly_do] = bo_qua.get(ly_do, 0) + 1
                    print(f"  ⚠️ {sym}: bỏ qua — {ly_do} · {note[:60]}")
                    break
                
                df = res["df"]
                # Nạp lịch phiên THẬT cho ô C1, một lần, từ mã đầu
                # tiên tải được. Thị trường có phiên thì có nến — đó
                # là lịch giao dịch duy nhất lấy được, vì `vnstock`
                # không có API lịch. Nạp TRƯỚC `run_session` để mã
                # đầu tiên cũng được chấm với cùng lịch như mã cuối.
                if not _da_nap_lich and df is not None and len(df):
                    _n = market_filter.ghi_nhan_lich_phien(df["time"])
                    _da_nap_lich = True
                    print(f"📅 Lịch phiên cho ô C1: {_n} phiên từ {sym}")
                if df is None or df.empty or len(df) < 20:
                    n = 0 if df is None else len(df)
                    bo_qua["thiếu nến"] = bo_qua.get("thiếu nến", 0) + 1
                    print(f"  ⚠️ {sym}: bỏ qua — chỉ {n} nến, cần ≥20")
                    break
                
                row = df.iloc[-1]
                bar = {
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    # Khối lượng cho mô hình trượt giá. KHÔNG nhân hệ số giá.
                    "volume": float(row["volume"]) if "volume" in row else 0.0,
                }
                s = run_session(journal, sym, df, bar, str(row["time"]), "HOSE", BUY_THRESHOLD)
                quet_duoc += 1
                phien_nhan.append(len(df))
                opened_count += s["opened"]
                closed_count += s["closed"]
                pending_count += s["filled_in"]

                # Thu thập thông tin phân tích cho báo cáo
                last_score = s["final_score"]
                raw_close = float(row["close"])
                close_vnd = raw_close * (1000.0 if raw_close < 500.0 else 1.0)
                scan_details.append({
                    "symbol": sym,
                    "ngay": str(row["time"])[:10],
                    "close": close_vnd,
                    "score": last_score,
                    "opened": s["opened"] > 0,
                    "filled": s["filled_in"] > 0
                })
                break
            except market_filter.CacheQuaHanError:
                # O C1: qua han thi DUNG CA PHIEN, khong bo qua tung ma.
                # Bat o day roi di tiep se thanh 71 dong canh bao va mot
                # phien quet chay tren cong da chet -- dung thu da xay ra.
                raise
            except Exception as e:
                err_msg = str(e)
                if "Rate limit" in err_msg or "429" in err_msg:
                    print(f"  ⏳ {sym}: Dính Rate Limit API. Tự động chờ 40 giây...")
                    time.sleep(40)
                    retry += 1
                else:
                    print(f"⚠️ Lỗi xử lý {sym}: {e}")
                    break

        time.sleep(1.0) # Tạm dừng 1.0s giữa các request

    # ── CỬA SỔ DỮ LIỆU THẬT SỰ NHẬN ĐƯỢC ─────────────────────────────
    # Đi bằng `::notice::` vì annotation đọc được qua API công khai,
    # còn nhật ký chạy và artifact thì đòi đăng nhập — cùng lý do đã
    # ghi ở khối thi hành điều kiện dừng phía trên.
    _ky_vong, _ngay_ro = phien_ky_vong(start_date, end_date)
    _dong_do, _dong_canh = bao_cua_so_du_lieu(phien_nhan, _ky_vong, _ngay_ro)
    print(f"📏 {_dong_do}")
    print(f"::notice::{_dong_do}")
    if _dong_canh:
        print(f"⚠️ {_dong_canh}")
        # `::warning::` chứ KHÔNG phải mã thoát: làm đỏ lượt quét sẽ
        # khiến `tools/chuong_bao_quet.py` báo giả 'ngày này không có
        # lượt quét nào' và che mất đúng thứ chuông kia sinh ra để canh.
        print(f"::warning::{_dong_canh}")

    trades = journal.all_trades()
    rep = report(trades, benchmark=_ro_chuan_vnindex(trades))

    # Vi sao dem theo `at` chu khong theo signal_date: cac ma co ngay phien
    # cuoi khac nhau, con `at` la moc GHI nen no khoanh dung mot luot quet.
    # Mốc đối chiếu là PHIÊN CUỐI của rổ, không phải `date.today()`:
    # ngày nghỉ lễ không phải một phiên bị lỡ. Không quét được mã nào
    # thì không có mốc, và `status()` lùi về ước tính — nó tự nói ra.
    _phien_cuoi = max((d["ngay"] for d in scan_details if d.get("ngay")),
                      default=None)
    _cong_sau = market_filter.status(hom_nay=_phien_cuoi)
    try:
        _bi_chan = journal.db.execute(
            "select skip_reason, count(*) from decisions "
            "where at >= ? and acted = 0 group by skip_reason "
            "order by count(*) desc", (moc_bat_dau,)).fetchall()
    except Exception as _e:
        _bi_chan = []
        print(f"⚠️  Không đếm được quyết định bị chặn: {type(_e).__name__}: {_e}")

    dong_cong = [
        "",
        "### 🚦 CỔNG CHẶN — TRẠNG THÁI THẬT",
        "",
        f"- **Cổng VN-INDEX:** {'BẬT' if _cong_sau.get('active') else '⛔ TẮT'}"
        f" · dữ liệu tới `{_cong_sau.get('ngay_cuoi', '?')}`"
        f" · trễ **{_cong_sau.get('tuoi_phien', '?')}** phiên"
        f" (ngưỡng {market_filter.TRE_TOI_DA_PHIEN})",
    ]
    if _bi_chan:
        dong_cong.append("- **Quyết định KHÔNG vào lệnh trong phiên này:**")
        for _ly_do, _n in _bi_chan:
            dong_cong.append(f"    - `{_n}` — {_ly_do or '(không ghi lý do)'}")
    else:
        dong_cong.append("- **Quyết định KHÔNG vào lệnh trong phiên này:** không có dòng nào")
    khoi_cong = chr(10).join(dong_cong)

    # ── TẠO BÁO CÁO PHÂN TÍCH CHUYÊN SÂU KHI HOÀN THÀNH ──────────────
    # '0 lệnh' phải nói được vì sao. Quét được dưới một nửa rổ nghĩa là
    # phiên này KHÔNG kết luận được gì về thị trường, chỉ kết luận được
    # rằng nguồn dữ liệu đang hỏng.
    _tong_ma = len(CUSTOM_WATCHLIST_SYMBOLS)
    _canh_bao_nguon = canh_bao_nguon(quet_duoc, bo_qua, _tong_ma)
    if _canh_bao_nguon:
        print("")
        print(f"⚠️ Quét được {quet_duoc}/{_tong_ma} mã{_canh_bao_nguon}")

    scan_details.sort(key=lambda x: -x["score"])
    top_candidates = [x for x in scan_details if x["score"] >= BUY_THRESHOLD]

    open_trades = [t for t in trades if t.status in ("OPEN", "PENDING", "CLOSING")]

    # Phân loại theo Ngành
    sector_summary = {}
    for sec_name, sec_syms in SECTOR_WATCHLIST.items():
        matched = [x for x in scan_details if x["symbol"] in sec_syms]
        if matched:
            avg_score = sum(x["score"] for x in matched) / len(matched)
            sector_summary[sec_name] = {
                "count": len(matched),
                "avg_score": avg_score,
                "top_stock": sorted(matched, key=lambda x: -x["score"])[0]
            }

    sorted_sectors = sorted(sector_summary.items(), key=lambda x: -x[1]["avg_score"])

    # `_pt` đã nạp ở khối thi hành điều kiện dừng phía trên. Đọc thuộc
    # tính module chứ không `from ... import` giá trị: backtest và test
    # bật cờ này lúc chạy, còn bản sao lấy lúc nạp thì không thấy.
    _trang_thai_c5, _giai_thich_c5 = trang_thai_c5(
        _pt.CHO_PHEP_MO_LENH_MOI, BUY_THRESHOLD)

    # Dựng báo cáo dạng Markdown
    report_md = f"""# 📊 BÁO CÁO PHÂN TÍCH THỊ TRƯỜNG DỰ BÁO VIBE CODING
**Khung giờ thực thi:** Phiên {session_name} lúc {now_time:%d/%m/%Y %H:%M:%S}  
**Rổ chứng khoán theo dõi:** {len(CUSTOM_WATCHLIST_SYMBOLS)} mã thuộc 16 Ngành Tùy chỉnh  
**Ngưỡng LỌC THEO DÕI:** {BUY_THRESHOLD:.1f} điểm — **KHÔNG phải ngưỡng mua**
**Trạng thái vào lệnh:** {_trang_thai_c5}

---

### 🚀 1. TỔNG QUAN PHIÊN QUÉT MULTI-AGENT
- **Số mã quét được:** `{quet_duoc}`/`{len(CUSTOM_WATCHLIST_SYMBOLS)}`{_canh_bao_nguon}
- **Số lệnh mới phát hiện mở mua:** `{opened_count}` lệnh
- **Số lệnh chờ đã khớp mua:** `{pending_count}` lệnh
- **Số lệnh đã chốt lời / cắt lỗ:** `{closed_count}` lệnh
- **Số cổ phiếu vượt ngưỡng lọc theo dõi (Score ≥ {BUY_THRESHOLD:.1f}):** `{len(top_candidates)}/{len(scan_details)}` mã

{_giai_thich_c5}
{khoi_cong}

---

### ⭐ 2. CỔ PHIẾU ĐIỂM CAO NHẤT PHIÊN (SCORE ≥ {BUY_THRESHOLD:.1f}) — CHỈ THEO DÕI

"""
    if top_candidates:
        report_md += "| STT | Mã CK | Giá Đóng Cửa (VNĐ) | Điểm Multi-Agent | Trạng Thái Lệnh |\n"
        report_md += "| :---: | :---: | :---: | :---: | :---: |\n"
        for i, item in enumerate(top_candidates[:10], 1):
            stt_str = "🟢 MUA MỚI" if item["opened"] else ("🔵 ĐÃ KHỚP" if item["filled"] else "👀 THEO DÕI")
            report_md += f"| {i} | **{item['symbol']}** | {item['close']:,.0f} | **{item['score']:.1f}/100** | {stt_str} |\n"
    else:
        report_md += f"ℹ️ *Phiên này không có cổ phiếu nào vượt ngưỡng mua {BUY_THRESHOLD:.1f} điểm. Hệ thống duy trì trạng thái kiên nhẫn đứng ngoài an toàn.*\n"

    report_md += """
---

### 🏗️ 3. XẾP HẠNG TÍN HIỆU THEO 16 NGÀNH HÀNG (SECTOR RANKING)

| Xếp hạng | Tên Ngành Hàng | Số Mã Quét | Điểm Trung Bình | Mã Dẫn Đầu Ngành (Top Stock) |
| :---: | :--- | :---: | :---: | :--- |\n"""
    for i, (sec_name, sec_info) in enumerate(sorted_sectors, 1):
        top_s = sec_info['top_stock']
        report_md += f"| {i} | **{sec_name}** | {sec_info['count']} mã | **{sec_info['avg_score']:.1f}đ** | {top_s['symbol']} ({top_s['score']:.1f}đ) |\n"

    report_md += """
---

### 📌 4. DANH SÁCH VỊ THẾ ĐANG MỞ & QUẢN TRỊ RỦI RO (ACTIVE POSITIONS)

"""
    if open_trades:
        # Ngày tín hiệu và ngày khớp là HAI cột. Gộp chúng lại
        # (`entry_date or signal_date`) là che đúng độ trễ mà cột "Trễ"
        # bên cạnh sinh ra để hiện — xem `do_tre_khop.py`.
        report_md += ("| Mã CK | Trạng Thái | Ngày Tín Hiệu | Ngày Khớp | Trễ "
                      "| Giá Vào (VNĐ) | Cắt Lỗ (SL) | Chốt Lời (TP) "
                      "| Tỷ Trọng Vốn |\n")
        report_md += ("| :---: | :---: | :---: | :---: | :---: | :---: "
                      "| :---: | :---: | :---: |\n")
        for t in open_trades:
            sl_str = f"{t.stop_loss:,.0f} VNĐ" if t.stop_loss else "—"
            tp_str = f"{t.take_profit:,.0f} VNĐ" if t.take_profit else "—"
            entry_p = f"{t.entry_price:,.0f} VNĐ" if t.entry_price else "Chờ khớp phiên tới"
            size_pct = f"{t.size_pct:.0f}%"
            _d = do_tre_khop.do_mot_lenh(t)
            report_md += (f"| **{t.symbol}** | `{t.status}` "
                          f"| {_d['signal_date'] or '—'} "
                          f"| {_d['entry_date'] or '—'} | {_d['nhan']} "
                          f"| {entry_p} | {sl_str} | {tp_str} | {size_pct} |\n")
        report_md += f"\n_{do_tre_khop.CHU_GIAI}_\n"
        for _d in do_tre_khop.dong_bao_cao(do_tre_khop.tom_tat(open_trades)):
            report_md += f"\n{_d}\n"
    else:
        report_md += "ℹ️ **Hiện tại không có lệnh nào đang mở.** Tất cả vị thế đã được chốt lời / cắt lỗ an toàn.\n"

    report_md += f"""
---

### 📈 5. KẾT QUẢ TỔNG THỂ SỔ LỆNH GIẤY (PAPER JOURNAL SUMMARY)

```text
{rep}
```
"""

    print("\n" + "=" * 80)
    print("📊 BÁO CÁO PHÂN TÍCH CHUYÊN SÂU PHIÊN " + session_name)
    print("=" * 80)
    print(report_md)

    # ── Đẩy sổ lệnh ra kho ngoài ─────────────────────────────────────
    # PHẢI làm trước khi đóng kết nối. Trên Streamlit Cloud ổ đĩa là tạm,
    # nên nếu không đẩy ra ngoài thì mọi lệnh vừa ghi sẽ mất khi app ngủ
    # hoặc redeploy.
    #
    # Lỗi đẩy KHÔNG được làm hỏng phiên quét — dữ liệu đã nằm an toàn
    # trong .db local rồi. Nhưng phải kêu to: "tưởng đã sao lưu mà thật
    # ra không" là trạng thái tệ nhất.
    try:
        import sheets_store as _ss
        _backend = _ss.open_from_secrets()
        if _backend is None:
            print("\nℹ️ Kho ngoài chưa cấu hình — sổ lệnh chỉ nằm trên ổ đĩa này.")
        else:
            _bc = _ss.push(journal.db, _backend)
            print(f"\n☁️ Đã đẩy sổ lệnh ra Google Sheets: "
                  f"{_bc['trades']} lệnh · thêm {_bc['decisions_moi']} quyết định mới")
    except Exception as _e:
        print(f"\n🚨 ĐẨY KHO NGOÀI THẤT BẠI: {type(_e).__name__}: {_e}")
        print("   Sổ lệnh local vẫn nguyên. Nhưng trên cloud, dữ liệu phiên "
              "này SẼ MẤT nếu không đẩy lại được.")

    journal.db.close()

    # 1. Ghi log ngắn ra daily_execution_log.txt
    log_file = "daily_execution_log.txt"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n\n==================== [ {now_time:%Y-%m-%d %H:%M:%S} - PHIÊN {session_name} ] ====================\n")
        f.write(rep)

    # 2. Ghi báo cáo phân tích chi tiết ra latest_daily_report.md
    with open("latest_daily_report.md", "w", encoding="utf-8") as f:
        f.write(report_md)

    # 3. Lưu lịch sử báo cáo vào thư mục reports/
    os.makedirs("reports", exist_ok=True)
    report_hist_file = f"reports/daily_report_{now_time:%Y%m%d_%H%M}.md"
    with open(report_hist_file, "w", encoding="utf-8") as f:
        f.write(report_md)

    print(f"\n✅ Đã lưu Báo cáo Phân tích Chuyên sâu vào file 'latest_daily_report.md' và '{report_hist_file}'")

if __name__ == "__main__":
    try:
        execute_daily_scan()
    except market_filter.CacheQuaHanError as e:
        print()
        print("=" * 78)
        print("DUNG PHIEN QUET — CONG VN-INDEX QUA HAN")
        print("=" * 78)
        print(str(e))
        print()
        print("O C1 da chon: qua han thi dung, khong am tham cho qua va cung")
        print("khong am tham chan het. Khong quet tiep tren mot cong da chet.")
        sys.exit(1)
