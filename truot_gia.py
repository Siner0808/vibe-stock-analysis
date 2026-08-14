"""
truot_gia.py
──────────────────────────────────────────────────────────────────────
Mô hình trượt giá — khoảng cách giữa giá mình muốn và giá thật sự khớp.

VÌ SAO CẦN
──────────
Sổ lệnh giấy hiện ghi rõ ở cuối mỗi báo cáo: *"Sổ này chỉ đo TÍN HIỆU.
Giao dịch thật còn có trượt giá, khớp một phần và tâm lý — kết quả thực tế
sẽ thấp hơn."* Câu đó đúng, nhưng nó là lời cảnh báo chứ không phải phép
đo. Module này biến nó thành con số.

Hệ quả cần chuẩn bị tinh thần: **mọi chỉ số sẽ xấu đi sau khi bật trượt
giá.** Đó là dấu hiệu tốt — nó có nghĩa con số đang tiến gần thực tế, chứ
không phải chiến lược vừa tệ đi.

HAI THÀNH PHẦN
──────────────
1. VƯỢT CHÊNH LỆCH MUA-BÁN. Muốn khớp ngay thì phải trả giá bên kia. Sàn
   dưới là MỘT bước giá — không thể ít hơn, vì giá chỉ tồn tại trên lưới
   bước giá.

2. TÁC ĐỘNG THỊ TRƯỜNG. Lệnh càng lớn so với thanh khoản thì càng đẩy giá.
   Dùng quy luật căn bậc hai, chuẩn trong tài liệu vi cấu trúc thị trường:

       tác_động = biên_độ_nến × √(khối_lượng_lệnh / khối_lượng_nến)

   Thang đo lấy từ BIÊN ĐỘ NẾN THẬT, không phải hằng số. Đây là điểm mấu
   chốt: một hằng số kiểu `0.001` trông như đo đạc nhưng thực ra là bịa.
   Biên độ nến thì đọc từ dữ liệu, và nó tự co giãn theo mã và theo phiên —
   phiên biến động mạnh thì trượt nhiều, đúng như thực tế.

   Điều kiện biên kiểm tra được: nuốt trọn cả nến (tỷ trọng = 1) thì tác
   động đúng bằng biên độ nến. Hợp lý, và bắt được nếu công thức sai.

ĐÂY LÀ MÔ HÌNH, KHÔNG PHẢI SỐ ĐO
────────────────────────────────
`he_so_tac_dong` là GIẢ ĐỊNH cho tới khi đối chiếu với lệnh khớp thật.
Mặc định 1,0 nghĩa là "tin hoàn toàn vào quy luật căn bậc hai". Chưa ai
kiểm định con số này trên thị trường Việt Nam.

Vì vậy `truot_gia()` trả về BẢNG TÁCH KHOẢN chứ không phải một con số:
người đọc phải thấy được phần nào do chênh lệch mua-bán, phần nào do tác
động, và tỷ trọng khối lượng là bao nhiêu. Một con số duy nhất sẽ nhanh
chóng bị dùng như thể nó là sự thật.

Xem NGUYEN-TAC-DO-LUONG.md.
"""
from __future__ import annotations

import math

MUA = "MUA"
BAN = "BAN"

# Bước giá HOSE cho cổ phiếu: (ngưỡng giá trên, bước giá).
# Đối chiếu với giá khớp thật ngày 13/08/2026:
#   ACB ~22.550đ → 100% chia hết 50đ, chỉ 49% chia hết 100đ
#   SHB ~12.500đ → 100% chia hết 50đ
#   VNM ~57.900đ → 92,9% chia hết 100đ
BUOC_GIA = {
    "HOSE": ((10_000, 10), (50_000, 50), (float("inf"), 100)),
    "HNX": ((float("inf"), 100),),
    "UPCOM": ((float("inf"), 100),),
}

LO_CHAN = 100          # lô chẵn HOSE


def buoc_gia(gia: float, san: str = "HOSE") -> int:
    """Bước giá áp dụng cho một mức giá."""
    bang = BUOC_GIA.get(san.upper(), BUOC_GIA["HOSE"])
    for nguong, buoc in bang:
        if gia < nguong:
            return buoc
    return bang[-1][1]


def lam_tron_bat_loi(gia: float, huong: str, san: str = "HOSE") -> float:
    """Làm tròn về lưới bước giá, LUÔN theo chiều bất lợi.

    Mua thì làm tròn LÊN, bán thì làm tròn XUỐNG. Đây là bất biến 3 của dự
    án — giả định bất lợi khi không phân định được. Làm tròn về gần nhất
    sẽ cho kết quả đẹp hơn thực tế một cách có hệ thống.
    """
    b = buoc_gia(gia, san)
    return float(math.ceil(gia / b) * b) if huong == MUA else float(math.floor(gia / b) * b)


def truot_gia(gia_muc_tieu: float, huong: str, nen: dict,
              khoi_luong_lenh: int, san: str = "HOSE",
              he_so_tac_dong: float = 1.0) -> dict:
    """Giá khớp thực tế sau trượt, kèm bảng tách khoản.

    nen: {"high": ..., "low": ..., "volume": ...} — nến mà lệnh khớp trong đó.

    Trả dict để người đọc thấy được cấu thành, không phải một con số trần
    trụi dễ bị hiểu là sự thật đã đo.
    """
    if huong not in (MUA, BAN):
        raise ValueError(f"huong phải là {MUA!r} hoặc {BAN!r}, nhận {huong!r}")
    if gia_muc_tieu <= 0:
        raise ValueError(f"giá mục tiêu phải dương, nhận {gia_muc_tieu}")

    tick = buoc_gia(gia_muc_tieu, san)

    kl_nen = float(nen.get("volume") or 0)
    bien_do = float(nen.get("high") or 0) - float(nen.get("low") or 0)

    # Nến không có thanh khoản: không mô hình hoá được tác động. Tính phần
    # chênh lệch mua-bán thôi và NÓI RA, thay vì im lặng coi tác động = 0.
    if kl_nen <= 0:
        ty_trong = 0.0
        tac_dong = 0.0
        ghi_chu = "nến không có khối lượng — chỉ tính chênh lệch mua-bán"
    else:
        ty_trong = min(khoi_luong_lenh / kl_nen, 1.0)
        tac_dong = max(bien_do, 0.0) * math.sqrt(ty_trong) * he_so_tac_dong
        ghi_chu = "OK"

    # Cộng tác động RỒI làm tròn bất lợi. Chính phép làm tròn đó là chi phí
    # vượt chênh lệch mua-bán: giá không tồn tại giữa hai bước, nên muốn
    # khớp ngay là phải trả tới bước kế tiếp.
    #
    # Bản đầu cộng thêm một bước giá TRƯỚC khi làm tròn — thành ra tính hai
    # lần, và một lệnh 1 cổ phiếu phải trả 100đ thay vì 50đ. Với cổ phiếu
    # 22.500đ thì sai số đó là 0,22% mỗi lệnh, cùng độ lớn với toàn bộ lợi
    # thế đang đo (+0,79%/lệnh). Bi quan quá mức cũng là đo sai.
    gia_tho = gia_muc_tieu + tac_dong if huong == MUA else gia_muc_tieu - tac_dong
    gia_khop = lam_tron_bat_loi(gia_tho, huong, san)

    # Tác động quá nhỏ để đẩy qua bước kế tiếp thì vẫn phải vượt chênh lệch:
    # không ai khớp ngay ở đúng giá mình muốn.
    if gia_khop == gia_muc_tieu:
        gia_khop = gia_muc_tieu + tick if huong == MUA else gia_muc_tieu - tick

    thuc_te = abs(gia_khop - gia_muc_tieu)
    return {
        "gia_khop": float(gia_khop),
        "gia_muc_tieu": float(gia_muc_tieu),
        "truot_vnd": thuc_te,
        "truot_pct": 100.0 * thuc_te / gia_muc_tieu,
        "phan_chenh_lech": float(min(tick, thuc_te)),
        "phan_tac_dong": round(tac_dong, 2),
        "ty_trong_kl": round(ty_trong, 6),
        "buoc_gia": tick,
        "ghi_chu": ghi_chu,
    }


def khoi_luong_hop_le(so_luong: int) -> int:
    """Làm tròn XUỐNG bội số lô chẵn. Dưới một lô thì không đặt được."""
    return max(0, int(so_luong) // LO_CHAN * LO_CHAN)
