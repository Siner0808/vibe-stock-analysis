"""Sổ KẾ HOẠCH VÀO LỆNH ghi lúc quét — lược đồ và dựng dòng (BƯỚC 195, mốc B6 phần 2).

VÌ SAO GHI LÚC QUÉT, KHÔNG TÍNH LẠI SAU
──────────────────────────────────────
`ke_hoach_vao_lenh.lap_ke_hoach` là hàm thuần, nhưng tính lại kế hoạch của một
tín hiệu cũ là tính trên một chuỗi giá KHÁC chuỗi agent đã thấy: giữa hai lượt kéo
`close` lệch thật ở 21,6% nến chung (ĐO 24), và nguồn điều chỉnh lùi sau mỗi sự
kiện quyền (ĐO 26, BƯỚC 193). C7 và mọi phép đo B6 sau này cần phán quyết GHI TẠI
NGÀY t, trước khi biết kết cục (bất biến 7). Người dùng duyệt thiết kế 15/10/2026:
tab MỚI `ke_hoach` (không thêm cột vào tab cũ), MỌI mã có điểm ≥ ngưỡng (kể cả mã
bị cổng của sổ chặn), một tín hiệu ghi MỘT lần.

FILE NÀY CHỈ CÓ LƯỢC ĐỒ VÀ MỘT HÀM THUẦN
───────────────────────────────────────
Nó KHÔNG nhập `ke_hoach_vao_lenh` (đường đo và giao dịch — `paper_trading`,
`sheets_store` — nhập file này để có DDL và cột; chúng không được chạm tới hàm lập
kế hoạch). `dong_tu_ke_hoach` đọc kết quả của `lap_ke_hoach` qua TÊN TRƯỜNG.
Chỉ `run_daily` gọi cả hai.
"""
from __future__ import annotations

import json
from typing import Any

#: Thứ tự cột = hợp đồng với tab `ke_hoach` trên Google Sheets. Đổi thứ tự hay
#: tên là đổi lược đồ: `sheets_store._kiem_tra_header` sẽ báo.
#: `diem` (không phải `score`): `sheets_store` khai kiểu theo TÊN cột cho mọi tab,
#: và `score` ở đó là SỐ NGUYÊN (cột của `decisions`); điểm ở đây là số thực.
COT_KE_HOACH: tuple[str, ...] = (
    "seq", "at", "symbol", "signal_date", "diem", "nguong", "san",
    "phan_quyet", "cat_lo", "vung_day", "vung_tran", "so_phien_cho",
    "rui_ro_pct", "keo_gian_atr", "gia_dong", "atr", "ma20",
    "day_xoay_ngay", "day_xoay_gia", "ly_do", "phien_ban",
)

COT_SO_NGUYEN: frozenset[str] = frozenset({"seq", "so_phien_cho"})
COT_SO_THUC: frozenset[str] = frozenset({
    "at", "diem", "nguong", "cat_lo", "vung_day", "vung_tran", "rui_ro_pct",
    "keo_gian_atr", "gia_dong", "atr", "ma20", "day_xoay_gia",
})
#: Cột chữ được phép rỗng (NULL): kế hoạch `CHUA_LAP_DUOC` không có đáy xoay.
COT_CHU_RONG_DUOC: frozenset[str] = frozenset({"day_xoay_ngay"})


def _kieu_sql(c: str) -> str:
    if c == "seq":
        return "INTEGER PRIMARY KEY AUTOINCREMENT"
    return "INTEGER" if c in COT_SO_NGUYEN else "REAL" if c in COT_SO_THUC else "TEXT"


#: Một tín hiệu = (mã, ngày nến t): ghi MỘT lần. Lượt quét sau (cùng ngày, hay
#: lượt sáng hôm sau xử lý lại nến hôm trước) gặp khoá trùng thì bỏ qua — bản ghi
#: đầu tiên là "lúc agent phán".
DDL_KE_HOACH: str = (
    "CREATE TABLE IF NOT EXISTS ke_hoach ("
    + ", ".join(f"{c} {_kieu_sql(c)}" for c in COT_KE_HOACH)
    + ", UNIQUE(symbol, signal_date))")


def dong_tu_ke_hoach(kh: Any, ma: str, diem: float, nguong: float, san: str,
                     phien_ban: str, luc: float, ngay_nen: str) -> dict:
    """Kết quả `lap_ke_hoach` → một dòng của bảng `ke_hoach` (chưa có `seq`).

    `signal_date` là NGÀY NẾN t của kế hoạch (`kh.ngay`) — nến đã đóng cuối cùng
    mà agent đã thấy; kế hoạch không lập được (`kh.ngay` None) thì lấy `ngay_nen`
    của lượt quét, để khoá (mã, ngày) không bao giờ là NULL (SQLite coi hai NULL
    là khác nhau, khoá duy nhất sẽ không chặn được dòng trùng). Mọi giá giữ nguyên như `KeHoachVaoLenh` (VNĐ, đã làm tròn
    theo bước giá của sàn). Trường không có thì None — không điền 0.
    """
    vung = kh.vung
    return {
        "at": float(luc), "symbol": str(ma), "signal_date": kh.ngay or str(ngay_nen)[:10],
        "diem": float(diem), "nguong": float(nguong), "san": str(san),
        "phan_quyet": str(kh.phan_quyet),
        "cat_lo": kh.cat_lo_cau_truc,
        "vung_day": None if vung is None else vung[0],
        "vung_tran": None if vung is None else vung[1],
        "so_phien_cho": kh.so_phien_cho,
        "rui_ro_pct": kh.rui_ro_pct, "keo_gian_atr": kh.keo_gian_atr,
        "gia_dong": kh.gia_dong, "atr": kh.atr, "ma20": kh.ma20,
        "day_xoay_ngay": kh.day_xoay_ngay, "day_xoay_gia": kh.day_xoay_gia,
        "ly_do": json.dumps(list(kh.ly_do), ensure_ascii=False),
        "phien_ban": str(phien_ban),
    }
