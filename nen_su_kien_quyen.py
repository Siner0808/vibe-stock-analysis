"""Đường tải nến + tập LOẠI sự kiện quyền cho điều kiện dừng (BƯỚC 182, Q14).

VÌ SAO CÓ FILE NÀY
──────────────────
`docs/QUYET-DINH-CHO.md` Q14 (người dùng chốt 10/10/2026, phương án (b)): lệnh ảo
mà sự kiện quyền rơi trong lúc giữ mang lãi/lỗ GIẢ (sổ lưu giá CHƯA điều chỉnh,
nguồn giá điều chỉnh LÙI) nên bị LOẠI khỏi mẫu của điều kiện dừng. `su_kien_quyen`
gắn nhãn (hàm thuần, không mạng); `paper_metrics.dieu_kien_dong_lai(..., loai_tru)`
phán (hàm thuần, không biết nhãn); file này là ĐƯỜNG NỐI DUY NHẤT giữa hai bên và
là chỗ DUY NHẤT tải nến cho việc đó. `run_daily.py` (thi hành trước vòng quét) và
`tools/canh_cong_c5.py` (chuông) cùng gọi `tap_loai`, nên hai nơi KHÔNG THỂ loại
hai tập khác nhau; `tools/soi_su_kien_quyen.py` cũng dùng `tai_nen` và
`loai_tu_nen` ở đây, nên danh sách nó in là danh sách điều kiện dừng loại.

BA LUẬT CỦA FILE NÀY
────────────────────
1. Chỉ lệnh tiến-về-trước ĐÃ ĐÓNG được soi (đúng nhóm mà `dieu_kien_dong_lai` đo)
   — không tải nến cho lệnh mô phỏng hay lệnh còn mở.
2. Tải hỏng (cả lượt, hoặc từng mã) KHÔNG BAO GIỜ làm loại thêm lệnh nào: mã không
   tải được ⇒ lệnh của mã ấy `KHONG_KIEM_DUOC` ⇒ ở lại mẫu. Hàm không ném lỗi; mọi
   thiếu sót nằm trong `KetQuaLoai.canh_bao` để người gọi in thành `::warning::`.
3. Nó KHÔNG sửa sổ, KHÔNG điều chỉnh giá sổ, không đổi ngưỡng nào.

CHIỀU THIÊN LỆCH: sự kiện quyền chỉ làm giá GIẢM, nên mọi lệnh bị loại là lệnh LỖ
GIẢ và loại chúng chỉ có thể làm alpha ĐẸP LÊN (Quy tắc 1). Vì vậy bằng chứng duy
nhất được nhận là nhãn `SU_KIEN_TRONG_LUC_GIU` của máy.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

import su_kien_quyen as skq


@dataclass(frozen=True)
class KetQuaLoai:
    """Kết quả MỘT lượt tính tập loại.

    `loai` {id: lý do} — truyền thẳng cho `loai_tru` của `dieu_kien_dong_lai`.
    `n_xet` — số lệnh tiến-về-trước đã đóng được soi. `thieu` — mã không tải được
    nến (lệnh của chúng ở lại mẫu). `loi` — lỗi chung nếu cả lượt hỏng, "" nếu
    không. `canh_bao` — các dòng cảnh báo đã dựng sẵn (rỗng nếu không có gì).
    """
    loai: dict
    n_xet: int
    thieu: tuple
    loi: str
    canh_bao: tuple


def tai_that(ma: str, tu_ngay: str, den_ngay: str):
    """(trạng thái, bảng OHLCV, hệ số VNĐ) của MỘT mã, qua đường của app."""
    from data_collectors import VNStockCollectorAgent
    from data_quality import price_multiplier
    import san_giao_dich

    kq = VNStockCollectorAgent().collect(
        ma, tu_ngay, den_ngay, exchange=san_giao_dich.san_cua(ma))
    df = kq.get("df")
    return kq.get("status"), df, price_multiplier(df)


def tai_nen(cac_ma: list[str], tu_ngay: str, den_ngay: str,
            tai: Callable = tai_that) -> tuple[dict[str, dict], list[str]]:
    """Nến (mở, thấp, cao) VNĐ của từng mã, MỖI MÃ MỘT LẦN. Trả (nến, mã không tải được)."""
    nen: dict[str, dict] = {}
    thieu: list[str] = []
    for ma in cac_ma:
        try:
            tt, df, he = tai(ma, tu_ngay, den_ngay)
        except Exception:
            thieu.append(ma)
            continue
        if tt != "OK" or df is None or len(df) == 0:
            thieu.append(ma)
            continue
        nen[ma] = skq.dung_nen(df["time"], df["open"], df["low"], df["high"], he)
    return nen, thieu


def lenh_dong_tien_ve_truoc(trades: list) -> list:
    """Lệnh tiến-về-trước ĐÃ ĐÓNG — đúng nhóm mà `dieu_kien_dong_lai` đo."""
    from paper_metrics import lenh_tien_ve_truoc
    return [t for t in lenh_tien_ve_truoc(trades) if t.status == "CLOSED"]


def loai_tu_nen(trades: list, nen_theo_ma: Mapping[str, Mapping[str, Any]]
                ) -> dict:
    """{id: lý do} lệnh tiến-về-trước đã đóng mang nhãn `SU_KIEN_TRONG_LUC_GIU`."""
    return skq.id_su_kien_trong_luc_giu(lenh_dong_tien_ve_truoc(trades),
                                        nen_theo_ma)


def _hom_nay() -> str:
    from data_quality import now_vn
    return now_vn().strftime("%Y-%m-%d")


def tap_loai(trades: list, hom_nay: str | None = None,
             tai: Callable = tai_that) -> KetQuaLoai:
    """Tính tập lệnh bị LOẠI khỏi điều kiện dừng. KHÔNG BAO GIỜ ném lỗi.

    Tải nến MỖI MÃ MỘT LẦN, khoảng [ngày vào sớm nhất − `LUI_NGAY_TAI`, hôm nay]
    (`skq.pham_vi_tai`), chỉ cho mã có lệnh tiến-về-trước đã đóng. Không có lệnh
    nào để soi thì không tải gì. `tai` và `hom_nay` để test tiêm nến giả.
    """
    dong = lenh_dong_tien_ve_truoc(trades)
    try:
        cac_ma, tu_ngay = skq.pham_vi_tai((), dong)
        if tu_ngay is None:
            return KetQuaLoai({}, len(dong), (), "", ())
        nen, thieu = tai_nen(cac_ma, tu_ngay, hom_nay or _hom_nay(), tai)
        loai = skq.id_su_kien_trong_luc_giu(dong, nen)
    except Exception as e:
        loi = f"{type(e).__name__}: {e}"
        return KetQuaLoai({}, len(dong), (), loi, (
            f"Không tính được tập LOẠI sự kiện quyền ({loi}) — điều kiện dừng "
            f"chạy trên MẪU ĐẦY ĐỦ, không loại lệnh nào.",))
    canh_bao = ()
    if thieu:
        canh_bao = (f"Không tải được nến {len(thieu)}/{len(cac_ma)} mã "
                    f"({', '.join(thieu)}): lệnh của chúng KHÔNG kiểm được sự kiện "
                    f"quyền nên ở lại mẫu của điều kiện dừng.",)
    return KetQuaLoai(loai, len(dong), tuple(thieu), "", canh_bao)
