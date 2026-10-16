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

FILE NÀY CHỈ CÓ LƯỢC ĐỒ VÀ HÀM THUẦN
───────────────────────────────────
Nó KHÔNG nhập `ke_hoach_vao_lenh` (đường đo và giao dịch — `paper_trading`,
`sheets_store` — nhập file này để có DDL và cột; chúng không được chạm tới hàm lập
kế hoạch). `dong_tu_ke_hoach` đọc kết quả của `lap_ke_hoach` qua TÊN TRƯỜNG.
Chỉ `run_daily` gọi cả hai.

Các hàm HIỆN (BƯỚC 198) — `dong_hien_thi`, `noi_lenh`, `noi_quyet_dinh`,
`khoa_tin_hieu` — cho app
đọc lại dòng ĐÃ GHI: không tính lại số nào, ô thiếu giữ None. App hiện bản GHI
tại ngày nến, không bao giờ lập lại kế hoạch của một tín hiệu cũ.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

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


#: Giờ Việt Nam: UTC+7 cố định, không có giờ mùa hè. `at` ghi bằng
#: `bay_gio.timestamp()` (giây epoch), nên đọc lại phải đặt đúng múi giờ này —
#: múi giờ của máy chạy app (Streamlit Cloud chạy UTC) cho giờ lệch 7 tiếng.
GIO_VN = timezone(timedelta(hours=7))


def ly_do_tu_o(o: Any) -> list[str]:
    """Ô `ly_do` (chuỗi JSON một danh sách) → list chữ. Ô rỗng → `[]`.

    Ô không đọc được thành danh sách thì trả NGUYÊN chữ trong ô thành một mục —
    bản ghi là bằng chứng, không được nuốt.
    """
    if o is None or o == "":
        return []
    try:
        ds = json.loads(o) if isinstance(o, str) else o
    except ValueError:
        return [str(o)]
    if isinstance(ds, list):
        return [str(x) for x in ds]
    return [str(o)]


def khoa_tin_hieu(ma: Any, ngay: Any) -> tuple[str, str]:
    """(mã, ngày nến 10 ký tự). Sổ lệnh có hai định dạng thời gian
    (`docs/HANDOFF.md` mục 3, ràng buộc 1) — so chuỗi đầy đủ là mất dòng."""
    return (str(ma), str(ngay)[:10])


def noi_lenh(lenh: Iterable[Any]) -> dict[tuple[str, str], Any]:
    """Lệnh sổ ảo (`Trade`) theo khoá tín hiệu (mã, ngày nến).

    Lệnh không có `signal_date` bị bỏ. Nhiều lệnh cùng một tín hiệu thì giữ lệnh
    có `id` LỚN nhất (ghi sau cùng).
    """
    ra: dict[tuple[str, str], Any] = {}
    for t in lenh:
        if not t.signal_date:
            continue
        k = khoa_tin_hieu(t.symbol, t.signal_date)
        cu = ra.get(k)
        if cu is None or (t.id is not None and (cu.id is None or t.id > cu.id)):
            ra[k] = t
    return ra


def noi_quyet_dinh(quyet_dinh: Iterable[dict]) -> dict[tuple[str, str], dict]:
    """Dòng tab `decisions` theo khoá tín hiệu (mã, ngày nến).

    Một tín hiệu có thể có nhiều dòng (mỗi lượt quét xử lý lại nến đã đóng ghi một
    dòng): giữ dòng có `seq` LỚN nhất — lượt sau cùng. Dòng thiếu `signal_date` bị bỏ.
    """
    ra: dict[tuple[str, str], dict] = {}
    for q in quyet_dinh:
        if not q.get("signal_date"):
            continue
        k = khoa_tin_hieu(q.get("symbol"), q["signal_date"])
        cu = ra.get(k)
        if cu is None or (q.get("seq") is not None
                          and (cu.get("seq") is None or q["seq"] > cu["seq"])):
            ra[k] = q
    return ra


def o_so_ao(lenh: Any = None, quyet_dinh: dict | None = None) -> str | None:
    """Sổ ảo đã làm gì với tín hiệu: lệnh nó mở, hoặc lý do nó KHÔNG mở (ghi
    nguyên văn từ bảng quyết định). Không có cả hai thì None — không đoán lý do."""
    if lenh is not None:
        return f"#{lenh.id} {lenh.status}"
    if quyet_dinh is not None and quyet_dinh.get("skip_reason"):
        return f"không mở — {quyet_dinh['skip_reason']}"
    return None


def dong_hien_thi(d: dict, lenh: Any = None, quyet_dinh: dict | None = None) -> dict:
    """Một dòng tab `ke_hoach` (đã đổi kiểu qua `sheets_store`) → dict để hiện.

    KHÔNG tính lại gì: mọi số là số ĐÃ GHI lúc quét; ô thiếu là None (app hiện
    dấu gạch), không điền 0. `lenh`: lệnh sổ ảo cùng tín hiệu (từ `noi_lenh`);
    `quyet_dinh`: dòng quyết định cùng tín hiệu (từ `noi_quyet_dinh`) — cột
    "Sổ ảo" đi qua `o_so_ao`.
    """
    day, tran = d.get("vung_day"), d.get("vung_tran")
    at = d.get("at")
    return {
        "Ngày nến": d.get("signal_date"),
        "Mã": d.get("symbol"),
        "Điểm": d.get("diem"),
        "Phán quyết": d.get("phan_quyet"),
        "Vùng chờ": None if day is None or tran is None else (day, tran),
        "Cắt lỗ cấu trúc": d.get("cat_lo"),
        "Rủi ro %": d.get("rui_ro_pct"),
        "Kéo giãn ATR": d.get("keo_gian_atr"),
        "Giá đóng": d.get("gia_dong"),
        "Hiệu lực (phiên)": d.get("so_phien_cho"),
        "Sổ ảo": o_so_ao(lenh, quyet_dinh),
        "Ghi lúc": (None if at is None
                    else datetime.fromtimestamp(at, GIO_VN).strftime("%d/%m %H:%M")),
        "Phiên bản": d.get("phien_ban"),
        "Lý do": ly_do_tu_o(d.get("ly_do")),
    }
