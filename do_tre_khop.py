"""
do_tre_khop.py
Độ trễ khớp lệnh — đo bằng LỊCH PHIÊN, không bằng ngày lịch.

VÌ SAO PHẢI CÓ FILE NÀY
───────────────────────
`run_daily.py` lấy `row = df.iloc[-1]` — nến **mới nhất** — rồi truyền
ngày của nó làm `session_date` cho `fill_pending()`. Chốt duy nhất của
`fill_pending` là `session_date <= signal_date` thì bỏ qua. Hệ quả:

    phiên khớp là phiên mà lượt quét TÌNH CỜ chạy, không phải T+1.

Nhịp cron GitHub đo được ngày 03/09/2026 là 33,9%, và ba chuông ở khung
09:00–10:00 UTC trễ trung vị 4–4,7 giờ. Một ngày mà mọi nhịp đều rơi thì
lệnh chờ khớp ở giá mở cửa của phiên SAU, và sổ ghi ngày ấy mà không có
gì kêu.

Cả `signal_date` lẫn `entry_date` đều đã được lưu, nên độ trễ **suy ra
được từ lâu**. Cái thiếu không phải dữ liệu — cái thiếu là một dụng cụ
đọc nó. Cùng hạng với việc `created_at` của 113 lệnh nằm gọn trong 258
giây suốt nhiều tháng trước khi có người đếm.

BA QUYẾT ĐỊNH ĐÃ CHỌN, GHI RA ĐỂ KHÔNG AI SỬA NGƯỢC
───────────────────────────────────────────────────
**1. KHÔNG đổi cách khớp.** `fill_pending()` giữ nguyên. Khớp muộn không
sai về mặt mô phỏng: không ai đặt lệnh ngày đó thì không có giao dịch
ngày đó, và `paper_metrics` so mỗi lệnh với rổ chuẩn trong đúng khoảng
nắm giữ của chính nó nên alpha không lệch vì vào muộn. Sửa cơ chế khớp
là đổi con số mà không có phép đo nào bảo phải đổi — đúng hình dạng
quy tắc số 1.

**2. KHÔNG lưu độ trễ thành cột.** Nó là hàm của hai cột đã có. Một giá
trị suy ra được mà đem lưu thì sẽ có ngày lệch khỏi nguồn của nó, và khi
lệch thì không ai biết bên nào đúng.

**3. KHÔNG lọc lệnh trễ ra khỏi phép đo.** Viết ra ĐÚNG LÚC NÀY, khi mới
có 4 lệnh tiến-về-trước và 0 kết quả đã đóng — tức trước khi nhìn thấy
lệnh trễ nào lãi hay lỗ. Lọc sau khi đã thấy số là bất biến 7 đổi hướng.
Dụng cụ này chỉ ĐO và NÓI RA; nó không được cầm quyền loại bỏ.
Khoá bởi `tests/test_do_tre_khop.py::test_phep_do_KHONG_duoc_loc_lenh_tre`.

KHÔNG CÓ KHỐI `__main__` — CỐ Ý
──────────────────────────────
Sổ THẬT nằm trên Google Sheets; `paper_trades.db` ở máy đứng yên từ
20/08/2026. Một CLI ở đây sẽ đọc bản sao chết ấy và trả lời rất tự tin —
đúng cái bẫy đã sập một lần ngày 28/08/2026. Dụng cụ này chỉ nhận danh
sách lệnh từ người gọi, và hai người gọi (`paper_metrics.report`,
`run_daily`) đều đã kéo sổ từ nguồn đúng.
"""
from __future__ import annotations

import lich_giao_dich as _lgd

#: Cần bao nhiêu lệnh trễ mới được phép nói "đồng đều". Với 1–2 lệnh
#: thì mọi tập đều "đồng đều" một cách tầm thường, và một kết luận tầm
#: thường phát ra như một phát hiện là cách nhanh nhất để lần sau không
#: ai đọc nó nữa.
TOI_THIEU_DE_NOI_DONG_DEU = 3

#: Bao nhiêu PHIÊN từ tín hiệu tới khớp là ĐÚNG HẠN. Bất biến 1 nói vào
#: lệnh ở giá mở cửa phiên T+1, nên con số này là 1 — không phải một
#: tham số để nới. Nới lên 2 là hợp thức hoá đúng thứ dụng cụ này sinh ra
#: để bắt; `tests/test_do_tre_khop.py` ghim nó.
TRE_CHUAN_PHIEN = 1

# Năm trạng thái. Ba trong số đó là "chưa kết luận được", và chúng KHÁC
# NHAU — gộp lại là mất đúng thông tin cần để biết phải làm gì tiếp:
#
#   CHUA_KHOP  -> bình thường, lệnh còn PENDING, không phải việc phải sửa
#   NGOAI_LICH -> lịch phiên không phủ tới đó, phải cập nhật BẢNG
#   MAU_THUAN  -> sổ nói điều `fill_pending` không thể sinh ra, phải sửa SỔ
#
# Cùng quy ước với `lich_giao_dich.chan_doan` và `vnstock_goi.kiem_goi`.
DUNG_HAN = "DUNG_HAN"
TRE = "TRE"
CHUA_KHOP = "CHUA_KHOP"
NGOAI_LICH = "NGOAI_LICH"
MAU_THUAN = "MAU_THUAN"

#: Thứ tự để in bảng đếm — cố định, để hai lượt chạy cho ra cùng một
#: bảng và mắt người quen chỗ.
CAC_TRANG_THAI = (DUNG_HAN, TRE, CHUA_KHOP, NGOAI_LICH, MAU_THUAN)

#: Nhãn ngắn cho ô trong bảng. Bảng nào cũng dùng chung một bộ này —
#: hai bảng tự đặt nhãn riêng là hai bảng sẽ nói khác nhau về cùng
#: một lệnh.
_NHAN = {
    CHUA_KHOP: "—",
    NGOAI_LICH: "?",
    MAU_THUAN: "!",
}

#: Dòng chú giải đi kèm mọi bảng có cột trễ. Không có nó thì "?" và "!"
#: là hai ký tự không ai đọc được.
CHU_GIAI = ("Cột TRỄ: T+n = n phiên từ tín hiệu tới khớp (T+1 là đúng "
            "hạn) · — chưa khớp · ? lịch phiên không phủ · ! sổ mâu thuẫn")


def _ngay(x) -> str:
    """Chuỗi ngày, hoặc rỗng. `None` phải ra rỗng chứ KHÔNG ra 'None'."""
    if x is None:
        return ""
    return str(x)[:10].strip()


def trang_thai_khop(signal_date, entry_date) -> tuple[str, int | None]:
    """(trạng thái, số phiên) của một lệnh.

    Số phiên là `None` khi không đếm được — và khi ấy trạng thái nói rõ
    vì sao không đếm được, chứ không trả 0. Số 0 là một con số, và một
    con số bịa ra ở chỗ này sẽ đi thẳng vào bảng thống kê.
    """
    ky = _ngay(entry_date)
    if not ky:
        return CHUA_KHOP, None

    tin = _ngay(signal_date)
    if not tin:
        # Có ngày khớp mà không có ngày tín hiệu: `consider_entry` luôn
        # ghi `signal_date` nên trạng thái này không thể sinh ra từ
        # đường chạy thật. Nó tồn tại vì sổ còn có đường khác — khôi
        # phục từ Sheets, nạp lại từ backtest — và một bản ghi hỏng thì
        # phải kêu chứ không được đếm nhầm sang "đúng hạn".
        return MAU_THUAN, None

    n = _lgd.so_phien_giua(tin, ky)
    if n is None:
        return NGOAI_LICH, None
    if n <= 0:
        # `fill_pending` bỏ qua khi `session_date <= signal_date`, nên
        # ngày khớp luôn LỚN HƠN ngày tín hiệu. Đếm ra 0 phiên nghĩa là
        # ngày khớp rơi vào ngày mà BẢNG LỊCH gọi là nghỉ — cùng hình
        # dạng với `lich_giao_dich.BANG_SAI`: dữ liệu canh bảng, không
        # chỉ bảng canh dữ liệu.
        return MAU_THUAN, n
    if n > TRE_CHUAN_PHIEN:
        return TRE, n
    return DUNG_HAN, n


def nhan_tre(trang_thai: str, so_phien: int | None) -> str:
    """Ô 'TRỄ' trong bảng — ngắn, và giống nhau ở mọi bảng."""
    if so_phien is None:
        return _NHAN.get(trang_thai, "?")
    if trang_thai == MAU_THUAN:
        return _NHAN[MAU_THUAN]
    return f"T+{so_phien}"


def do_mot_lenh(t) -> dict:
    """{id, symbol, signal_date, entry_date, trang_thai, so_phien, nhan}"""
    tt, n = trang_thai_khop(
        getattr(t, "signal_date", None), getattr(t, "entry_date", None))
    return {
        "id": getattr(t, "id", None),
        "symbol": getattr(t, "symbol", None),
        "signal_date": _ngay(getattr(t, "signal_date", None)),
        "entry_date": _ngay(getattr(t, "entry_date", None)),
        "trang_thai": tt,
        "so_phien": n,
        "nhan": nhan_tre(tt, n),
    }


def tom_tat(trades) -> dict:
    """{dem, tre, mau_thuan, tre_lon_nhat, so_lenh}

    `tre` và `mau_thuan` là danh sách bản ghi đầy đủ chứ không chỉ số
    đếm: một con số "3 lệnh trễ" không cho biết phải đi xem lệnh nào.
    """
    dem = {k: 0 for k in CAC_TRANG_THAI}
    tre: list[dict] = []
    mau_thuan: list[dict] = []

    for t in trades:
        d = do_mot_lenh(t)
        dem[d["trang_thai"]] = dem.get(d["trang_thai"], 0) + 1
        if d["trang_thai"] == TRE:
            tre.append(d)
        elif d["trang_thai"] == MAU_THUAN:
            mau_thuan.append(d)

    tre.sort(key=lambda d: (-(d["so_phien"] or 0), str(d["symbol"])))

    # ĐỒNG ĐỀU hay RẢI RÁC — phân biệt này tách hai nguyên nhân trông
    # giống hệt nhau từ bảng đếm. Đo ngày 04/09/2026 trên sổ thật:
    # 43/43 lệnh trễ đều ĐÚNG T+2, không lệch một cái. Nhịp cron rơi
    # ngẫu nhiên không thể cho ra một hằng số như thế; một bước nhảy cố
    # định trong vòng lặp mô phỏng thì có.
    muc = {d["so_phien"] for d in tre}
    dong_deu = (None if len(tre) < TOI_THIEU_DE_NOI_DONG_DEU
                else len(muc) == 1)

    return {
        "dem": dem,
        "tre": tre,
        "mau_thuan": mau_thuan,
        "tre_lon_nhat": tre[0]["so_phien"] if tre else None,
        "tre_dong_deu": dong_deu,
        "cac_muc_tre": sorted(muc),
        "so_lenh": sum(dem.values()),
    }


def dong_bao_cao(tt: dict) -> list[str]:
    """Các dòng báo cáo. Rỗng khi không có gì đáng nói.

    Trả danh sách dòng thay vì in: hai nơi gọi (`paper_metrics.report`
    dạng văn bản, `run_daily` dạng markdown) phải nói **cùng một câu**,
    và cách duy nhất bảo đảm điều đó là chỉ có một chỗ viết câu ấy.
    """
    ra: list[str] = []
    dem = tt["dem"]

    if dem.get(MAU_THUAN):
        ra.append(f"🚨 {dem[MAU_THUAN]} lệnh có ngày khớp mà `fill_pending` "
                  f"không thể sinh ra")
        for d in tt["mau_thuan"][:5]:
            ra.append(f"   {d['symbol']}: tín hiệu {d['signal_date'] or '—'} "
                      f"→ khớp {d['entry_date'] or '—'}")
        ra.append("   Sổ hoặc bảng lịch sai. Đừng tin số nào khác cho tới "
                  "khi biết bên nào.")

    if dem.get(TRE):
        ra.append(f"⚠️ {dem[TRE]} lệnh khớp MUỘN hơn T+1 "
                  f"(muộn nhất: T+{tt['tre_lon_nhat']})")
        for d in tt["tre"][:5]:
            ra.append(f"   {d['symbol']}: tín hiệu {d['signal_date']} → khớp "
                      f"{d['entry_date']}  ({d['nhan']})")
        # KHÔNG đoán nguyên nhân. Bản đầu của dụng cụ này khẳng định
        # thẳng "do cron GitHub rơi nhịp" — và số liệu thật ngày
        # 04/09/2026 bác sạch: 43/43 lệnh trễ đúng T+2 vì
        # `walkforward._mo_phong(stride=2)` không ghé phiên t+1. Một
        # thông điệp nêu sai nguyên nhân dẫn người đọc đi sai hướng
        # chắc chắn hơn là không có thông điệp nào.
        if tt.get("tre_dong_deu") is True:
            ra.append(f"   ĐỒNG ĐỀU: cả {dem[TRE]} lệnh đều trễ đúng "
                      f"T+{tt['tre_lon_nhat']}, không lệch cái nào.")
            ra.append("   Nhịp quét rơi ngẫu nhiên KHÔNG cho ra hằng số. Đi")
            ra.append("   xem bước nhảy của vòng mô phỏng trước:")
            ra.append("   `walkforward._mo_phong(stride=…)` — stride=2 thì")
            ra.append("   phiên t+1 không bao giờ được ghé, và `run_session`")
            ra.append("   gọi `fill_pending` TRƯỚC `consider_entry`.")
        elif tt.get("tre_dong_deu") is False:
            ra.append(f"   RẢI RÁC: các mức trễ là {tt['cac_muc_tre']}. Hợp")
            ra.append("   với việc rơi nhịp quét — lệnh chờ khớp ở giá mở cửa")
            ra.append("   của phiên mà lượt quét chạy được, nên một ngày cron")
            ra.append("   GitHub rơi hết nhịp là một phiên trượt.")
        else:
            ra.append(f"   Chưa đủ {TOI_THIEU_DE_NOI_DONG_DEU} lệnh để nói "
                      f"đồng đều hay rải rác — CHƯA phân biệt được nguyên")
            ra.append("   nhân là bước nhảy mô phỏng hay nhịp quét rơi.")
        ra.append("   Những lệnh này VẪN được tính vào mọi con số ở trên —")
        ra.append("   loại chúng ra sau khi đã thấy kết quả là bất biến 7.")

    if dem.get(NGOAI_LICH):
        ra.append(f"ℹ️ {dem[NGOAI_LICH]} lệnh nằm ngoài phạm vi lịch phiên "
                  f"({_lgd.PHU_TU} → {_lgd.PHU_TOI}) — CHƯA BIẾT trễ bao nhiêu")

    return ra
