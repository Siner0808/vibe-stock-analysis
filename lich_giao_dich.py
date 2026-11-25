"""
lich_giao_dich.py
Lịch phiên giao dịch CÔNG BỐ TRƯỚC — nguồn độc lập với chuỗi giá.

VÌ SAO PHẢI CÓ FILE NÀY
───────────────────────
Ngày 02/09/2026 dự án mất nửa ngày để trả lời câu "vì sao bốn lệnh chờ
không khớp". Câu trả lời là "thị trường nghỉ Quốc khánh", và **không dụng
cụ nào trong dự án nói được điều đó**:

- `chuong_bao_quet.py` đếm lượt quét THÀNH CÔNG. Ba ngày nghỉ đều có lượt
  quét thành công, nên chuông im. Đúng chức năng của nó.
- `run_daily.bao_cua_so_du_lieu()` so SỐ phiên nhận được với kỳ vọng, mà
  kỳ vọng lại lấy từ chính chuỗi VN-INDEX đó. Nguồn đứng thì cả hai vế
  cùng đứng và tỷ lệ vẫn ~100%.
- `market_filter.is_vni_bullish()` đo độ cũ so với NGÀY ĐANG CHẤM, mà ngày
  đang chấm chính là nến mới nhất — nên độ trễ bằng 0 theo định nghĩa.

Ba dụng cụ, không cái nào sai, và cùng nhau vẫn để lọt. Vấn đề chung: tất
cả đều đo dữ liệu **bằng chính dữ liệu đó**. Một nguồn đứng và một thị
trường nghỉ cho ra chữ ký giống hệt nhau, và không thể tách bằng nội tại.

Thứ tách được chúng là một lịch **công bố trước, từ bên ngoài**. Sở công
bố lịch nghỉ giao dịch từng năm; đó là dữ liệu ít, đổi mỗi năm một lần, và
biết trước.

BẢNG NÀY ĐÃ ĐƯỢC DỮ LIỆU KIỂM, KHÔNG PHẢI CHÉP TỪ BÁO RỒI TIN
─────────────────────────────────────────────────────────────
Bản chép từ bài báo lần đầu SAI: nó ghi 02/01/2026 có phiên. Đối chiếu với
chuỗi VN-INDEX thật thì ngày đó không có nến — Sở nghỉ cả 01 và 02/01, thứ
Sáu 02/01 hoán đổi sang thứ Bảy 10/01. Sửa xong mới khớp.

Phép đối chiếu (02/09/2026), toàn bộ vùng có dữ liệu:

    chuỗi VN-INDEX 2026-01-05 → 2026-08-28 : 162 phiên
    bảng này dự kiến                        : 162 phiên
    bảng nói CÓ mà không có nến             : 0
    có nến mà bảng nói NGHỈ                 : 0

`tests/test_lich_giao_dich.py` ghim đúng con số 162 đó, nên bảng không
trôi đi được mà không ai biết.

LẦN KIỂM THỨ HAI (25/11/2026, BƯỚC 298) — LẦN KIỂM CŨ CHỈ TỚI 28/08
────────────────────────────────────────────────────────────────────
Lần kiểm ở trên dừng ở nến 28/08/2026; từ 29/08 trở đi bảng KHÔNG được
dữ liệu kiểm lần nào, và có một ngày sai: 24/11/2026 (thứ Ba) HOSE (thông
báo 11/11) và HNX (thông báo 10/11) nghỉ giao dịch, "Ngày Văn hóa Việt
Nam" (Nghị quyết 28/2026/QH16, hiệu lực 01/7/2026). Bảng chưa có ngày đó
nên chuông `chuong-nguon-dung` kêu oan lúc 03:38 ICT 25/11. Đo lại, cùng
phương pháp, tới hôm nay:

    nguon_gia_cong_khai.lay_ohlcv("VNINDEX", "2026-08-24", "2026-11-25")
    nến VN-INDEX 2026-08-29 → 2026-11-24 : 58 phiên (03/09 → 23/11)
    bảng CŨ dự kiến                       : 59 phiên
    bảng nói CÓ mà không có nến           : 1   (2026-11-24)
    có nến mà bảng nói NGHỈ               : 0
    bảng MỚI (có 24/11) dự kiến           : 58 phiên, lệch 0 ở cả hai chiều

Cổ phiếu FPT và SSI (Entrade) cũng không có nến 24/11. Ngày 25/11 chưa
được đối chiếu (nến chưa đóng lúc đo). `tests/test_lich_giao_dich.py` ghim
danh sách 58 phiên thật đó (mục 9). Bảng này chỉ được coi là kiểm tới
24/11/2026; từ 25/11 tới hết năm nó là LỊCH CÔNG BỐ chưa có nến đối chiếu.
Báo chí chưa thấy thông báo nghỉ toàn thị trường nào khác tới 31/12/2026
(đợt chuyển cổ phiếu HNX sang HOSE tạm ngừng 24–25/12 là chuyện TỪNG MÃ,
không phải ngày nghỉ của thị trường, nên không vào bảng này).

NGÀY LÀM BÙ KHÔNG GIAO DỊCH
───────────────────────────
Năm 2026 có hai ngày làm bù rơi vào thứ Bảy: 10/01 (bù cho 02/01) và 22/08
(bù cho 31/08). **Cả hai đều KHÔNG giao dịch** — HOSE thông báo rõ, và
chuỗi giá xác nhận: 0 phiên thứ Bảy trong toàn bộ 162 phiên đo được.

Vì thế `NGAY_NGHI` chỉ chứa ngày TRONG TUẦN. Thêm một thứ Bảy vào đó là
thêm một dòng không có tác dụng — cuối tuần đã bị loại từ trước — mà lại
trông như một luật. Nếu năm nào Sở MỞ CỬA vào ngày làm bù thì đó là ngoại
lệ ngược, và phải khai ở `PHIEN_CUOI_TUAN`, không phải ở đây.
"""
from __future__ import annotations

import datetime as _dt

#: Ngày TRONG TUẦN mà Sở công bố KHÔNG giao dịch.
#: Nguồn: thông báo HOSE/HNX, đối chiếu qua báo chí tài chính 02/09/2026
#: (các ngày tới 02/09) và 25/11/2026 (ngày 24/11). Mỗi kỳ nghỉ ghi kèm lý
#: do — một ngày không có lý do là một ngày không kiểm lại được.
NGAY_NGHI: frozenset[str] = frozenset({
    "2026-01-01", "2026-01-02",                 # Tết Dương lịch (02/01 hoán đổi)
    "2026-02-16", "2026-02-17", "2026-02-18",   # Tết Nguyên đán
    "2026-02-19", "2026-02-20",
    "2026-04-27",                               # Giỗ tổ Hùng Vương
    "2026-04-30", "2026-05-01",                 # Thống nhất · Quốc tế Lao động
    "2026-08-31", "2026-09-01", "2026-09-02",   # Quốc khánh
    # Ngày Văn hóa Việt Nam, thứ Ba. Nguồn: HOSE thông báo 11/11/2026 (bổ
    # sung lịch nghỉ 2026 của 2294/TB-SGDHCM), HNX thông báo 10/11/2026;
    # căn cứ Nghị quyết 28/2026/QH16. Không có nến VN-INDEX ngày này.
    "2026-11-24",
})

#: Ngoại lệ NGƯỢC: thứ Bảy/Chủ nhật mà Sở VẪN mở cửa. Năm 2026 không có.
#: Để rỗng chứ không bỏ hẳn: ngày nào có thì chỗ khai đã sẵn, khỏi phải
#: sửa cấu trúc lúc đang vội.
PHIEN_CUOI_TUAN: frozenset[str] = frozenset()

#: BẢNG CHỈ PHỦ TỪNG NÀY. Ngoài khoảng này mọi câu trả lời là "chưa biết",
#: KHÔNG phải "ổn". Lịch năm sau chỉ có khi Sở công bố, thường cuối năm
#: trước — nên bảng hết hạn là chuyện bình thường và phải nói ra được.
PHU_TU = "2026-01-01"
PHU_TOI = "2026-12-31"

#: Trễ bao nhiêu PHIÊN thì kêu. Vì sao 2 chứ không phải 1: trong một phiên
#: đang diễn ra, nến ngày hôm đó chưa đóng, nên trễ 1 phiên là trạng thái
#: BÌNH THƯỜNG của mọi lượt quét chạy trước giờ đóng cửa. Trễ 2 nghĩa là
#: phiên liền trước đã đóng hẳn mà nến của nó vẫn chưa về — đó không phải
#: chậm, đó là thiếu.
TRE_BAO_DONG_PHIEN = 2

# Ba trạng thái chẩn đoán. "Chưa biết" là một trạng thái THẬT, không phải
# một cách nói giảm của "ổn" — xem `chan_doan`.
OK = "OK"
NGUON_DUNG = "NGUON_DUNG"
BANG_SAI = "BANG_SAI"
CHUA_BIET = "CHUA_BIET"


def _ngay(x) -> str:
    return str(x)[:10]


def trong_pham_vi(ngay) -> bool:
    """Bảng có phát biểu được về ngày này không."""
    return PHU_TU <= _ngay(ngay) <= PHU_TOI


def co_phien(ngay) -> bool | None:
    """Ngày này có phiên giao dịch không. `None` = NGOÀI phạm vi bảng.

    Trả `None` chứ không đoán, kể cả khi đoán rất dễ (thứ Ba giữa tháng
    Sáu năm sau gần chắc là có phiên). Một bảng lịch mà tự suy ra ngày
    ngoài phạm vi thì nó không còn là lịch công bố, nó là phỏng đoán đội
    lốt lịch — và cái nó bỏ sót đúng là ngày nghỉ lễ, tức đúng thứ nó sinh
    ra để biết.
    """
    d = _ngay(ngay)
    if not trong_pham_vi(d):
        return None
    if d in PHIEN_CUOI_TUAN:
        return True
    if _dt.date.fromisoformat(d).weekday() >= 5:
        return False
    return d not in NGAY_NGHI


def cac_phien(sau, toi) -> list[str] | None:
    """Các phiên nằm trong khoảng `(sau, toi]`. `None` nếu ngoài phạm vi.

    Mở ở đầu, đóng ở cuối — cùng quy ước với `market_filter._tre_phien`,
    vì hai bên đếm cùng một thứ và lệch quy ước là lệch đúng một phiên.
    """
    a, b = _ngay(sau), _ngay(toi)
    if not (trong_pham_vi(a) and trong_pham_vi(b)):
        return None
    if b <= a:
        return []
    ra, n = [], _dt.date.fromisoformat(a) + _dt.timedelta(days=1)
    het = _dt.date.fromisoformat(b)
    while n <= het:
        if co_phien(n.isoformat()):
            ra.append(n.isoformat())
        n += _dt.timedelta(days=1)
    return ra


def so_phien_giua(sau, toi) -> int | None:
    """Đếm phiên trong `(sau, toi]`. `None` nếu bảng không phủ."""
    ds = cac_phien(sau, toi)
    return None if ds is None else len(ds)


def chan_doan(nen_moi_nhat, hom_nay) -> tuple[str, str]:
    """(trạng thái, thông điệp) — nguồn dữ liệu đứng hay thị trường nghỉ.

    Đây là câu hỏi mà mọi dụng cụ cũ của dự án KHÔNG trả lời được, vì
    chúng đo dữ liệu bằng chính dữ liệu đó. Hàm này đối chiếu nến mới nhất
    với một lịch đến từ BÊN NGOÀI chuỗi giá.

    Bốn trạng thái, và trạng thái thứ tư là bắt buộc:

    - `OK`         — số phiên đáng lẽ đã có kể từ nến cuối còn dưới ngưỡng.
    - `NGUON_DUNG` — đã qua ≥ `TRE_BAO_DONG_PHIEN` phiên mà không có nến mới.
    - `BANG_SAI`   — có nến vào đúng ngày bảng gọi là NGHỈ. Chiều ngược
      lại của phép kiểm: dữ liệu canh bảng, không chỉ bảng canh dữ liệu.
      Bảng sai thì mọi phán quyết còn lại đều vô giá trị, nên nó phải là
      một trạng thái riêng chứ không được lặng lẽ đi tiếp.
    - `CHUA_BIET`  — ngoài phạm vi bảng. KHÔNG được gộp vào `OK`. Một cái
      chuông hết hạn mà báo "ổn" thì tệ hơn không có chuông: nó biến việc
      "không ai cập nhật lịch năm nay" thành ba tháng im lặng.
    """
    nen, moc = _ngay(nen_moi_nhat), _ngay(hom_nay)

    if not (trong_pham_vi(nen) and trong_pham_vi(moc)):
        return CHUA_BIET, (
            f"Lịch chỉ phủ {PHU_TU} → {PHU_TOI}; đang hỏi về nến {nen} và "
            f"mốc {moc}. CHƯA BIẾT nguồn có đứng hay không — cập nhật "
            f"`lich_giao_dich.NGAY_NGHI` theo thông báo của Sở.")

    if co_phien(nen) is False:
        return BANG_SAI, (
            f"Có nến ngày {nen} nhưng bảng lịch gọi đó là ngày NGHỈ. Bảng "
            f"sai, không phải dữ liệu — sửa `NGAY_NGHI` trước khi tin bất "
            f"kỳ phán quyết nào khác của module này.")

    tre = so_phien_giua(nen, moc)
    if tre >= TRE_BAO_DONG_PHIEN:
        bo_qua = cac_phien(nen, moc)
        return NGUON_DUNG, (
            f"NGUỒN DỮ LIỆU ĐỨNG: nến mới nhất là {nen}, nhưng theo lịch "
            f"công bố đã có {tre} phiên kể từ đó ({', '.join(bo_qua)}) tính "
            f"tới {moc}. Kết luận này đến từ bảng lịch trong repo "
            f"(`lich_giao_dich.NGAY_NGHI`), không phải từ thông báo của Sở. "
            f"Cách giải thích khác cần kiểm trước khi kết luận nguồn hỏng: Sở "
            f"thêm ngày nghỉ sau khi bảng được viết (24/11/2026 đã xảy ra) — "
            f"đối chiếu thông báo nghỉ giao dịch của HOSE/HNX cho các ngày "
            f"trên.")

    return OK, (f"Nến mới nhất {nen}, trễ {tre} phiên so với {moc} "
                f"(ngưỡng {TRE_BAO_DONG_PHIEN}). Khớp lịch công bố.")
