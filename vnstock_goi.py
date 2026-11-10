"""vnstock_goi.py — hạng gói vnstock ĐANG CÓ HIỆU LỰC, không phải hạng đã mua.

THẾ HỆ 5 (BƯỚC 260, 10/11/2026) — phần dưới đây tả thế hệ 4; đọc khối này trước
─────────────────────────────────────────────────────────────────────────────
`vnai`, `vnii` và máy chủ `license/verify` KHÔNG còn. Thế hệ 5 có hai hàm công khai:
`vnstock.status()` (hạng do máy chủ cấp, `authenticated`, `active`, `expires_at`) và
`vnstock.usage()` (hạng mà thư viện ĐANG ÁP vào luật quyền, hạn mức, `rule.periods`).
Hai bên đọc cùng một gói nên bất đối xứng cũ — máy chủ nói silver, thư viện chạy như
free vì `ImportError` của `vnii` bị nuốt — không còn đường xảy ra nguyên văn; còn
lại hai cách lệch vẫn đáng bắt: (a) hạng `status()` khác hạng `usage()`; (b) gói
không còn hiệu lực (`active` False). Có khoá mà chưa đăng nhập được thì là CHƯA KIỂM
ĐƯỢC (lý do ghi rõ), và `vnstock_auth.bat_buoc_dang_nhap()` lo phần dừng lượt quét.
Số kỳ BCTC và hạn mức đọc ĐỘNG từ `usage()`: `rule.periods` None = không giới hạn.

VÌ SAO CÓ FILE NÀY
──────────────────
Ngày 22/08/2026, tài khoản đã nâng lên Silver (còn hạn tới 22/11/2026) mà
app vẫn chạy y như gói miễn phí. Không có lỗi nào, không có cảnh báo nào.
Đo được hai hậu quả:

    báo cáo tài chính   8 kỳ   thay vì   34 kỳ
    hạn mức API        60/phút thay vì  300/phút

Gốc nằm ở `vnai/beam/auth.py`:

    def _detect_tier(self):
        tier_from_vnii = self._check_vnii_tier()   # import vnii -> ImportError
        if tier_from_vnii: return tier_from_vnii
        if self._has_api_key(): return "free"      # rơi vào đây, im lặng

Package `vnii` chưa cài, `ImportError` bị nuốt, hàm trả "free". Chính tài
liệu bootstrap của vnstock cũng cảnh báo đúng chỗ đó: *"Do not rely
exclusively on local `vnii` logs as it might not be installed yet and could
incorrectly report 'Community'."*

Đây là **đúng loại hỏng mà dự án này tồn tại để chặn**: một đường sao lưu
báo xanh trong khi thứ nó canh đang đóng. Cùng họ với `market_filter.status()`
từng báo `active=True` trong khi cổng chặn cứng, và với `vnstock_auth.
status_message()` hiện nói "✅ Đã nạp API key" — đúng, nhưng câu đúng đó che
mất việc app đang bị cắt còn 1/4 dữ liệu.

BA TRẠNG THÁI, KHÔNG PHẢI HAI
─────────────────────────────
`KHOP` / `LECH` / `CHUA_KIEM_DUOC`. Trạng thái thứ ba là bắt buộc: mất mạng
mà trả về "khớp" thì phép kiểm này lại trở thành đúng thứ nó sinh ra để bắt.

KHÔNG SỬA HẠNG Ở ĐÂY
────────────────────
Module này CHỈ ĐỌC và SO SÁNH. Nó không ghi `authenticator._cached_tier`,
không vá `PERIOD_LIMITS`, không đụng vào bất cứ phép kiểm giấy phép nào.

Ép cứng hạng thành "silver" sẽ khiến app tiếp tục khẳng định silver sau ngày
hết hạn, rồi cắt dữ liệu sai mà không ai biết — tạo ra đúng lời nói dối âm
thầm mà file này được viết ra để phát hiện. Cách sửa đúng là cài `vnii` và
bốn package đi kèm.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

TTL_GIAY = 1800          # hạng gói đổi rất chậm; 30 phút là quá đủ

KHOP = "KHỚP"
LECH = "LỆCH"
CHUA_KIEM_DUOC = "CHƯA KIỂM ĐƯỢC"

_CACHE: dict[str, tuple[float, "TrangThaiGoi"]] = {}


@dataclass(frozen=True)
class TrangThaiGoi:
    """Ảnh chụp hạng gói. `tinh_trang` là thứ đáng đọc nhất."""

    tinh_trang: str                       # KHOP | LECH | CHUA_KIEM_DUOC
    hang_may_chu: str | None = None       # hạng do máy chủ cấp (`vnstock.status()`)
    hang_cuc_bo: str | None = None        # hạng thư viện ĐANG ÁP (`vnstock.usage()`)
    con_han: bool | None = None
    het_han: str | None = None            # YYYY-MM-DD
    ky_bctc: int | None = None            # số kỳ BCTC được lấy; None = không giới hạn
    han_muc_phut: int | None = None
    ly_do: str = ""                       # vì sao chưa kiểm được / vì sao lệch

    @property
    def dat(self) -> bool:
        """Chỉ True khi ĐÃ kiểm và hạng cục bộ khớp hạng máy chủ."""
        return self.tinh_trang == KHOP

    def dong_log(self) -> str:
        if self.tinh_trang == CHUA_KIEM_DUOC:
            return f"gói vnstock: chưa kiểm được — {self.ly_do}"
        if self.tinh_trang == KHOP:
            han = f", hết hạn {self.het_han}" if self.het_han else ""
            return (f"gói vnstock: {self.hang_may_chu}{han} — thư viện cục bộ "
                    f"nhận đúng hạng, {self._mo_ta_ky()}")
        return (f"gói vnstock: LỆCH — {self.ly_do} "
                f"(máy chủ '{self.hang_may_chu}', thư viện '{self.hang_cuc_bo}'; "
                f"{self._mo_ta_ky()}).")

    def mo_ta_lech(self) -> str:
        """Câu ngắn cho giao diện khi LỆCH."""
        if self.hang_may_chu != self.hang_cuc_bo:
            return f"mua {self.hang_may_chu} · chạy như {self.hang_cuc_bo}"
        return self.ly_do

    def _mo_ta_ky(self) -> str:
        if self.ky_bctc is None:
            return "BCTC không giới hạn số kỳ"
        return f"BCTC {self.ky_bctc} kỳ"


def _doc_may_chu() -> tuple[dict, dict]:
    """(`vnstock.status()`, `vnstock.usage()`). Ném nếu đọc hỏng — người gọi bắt."""
    import vnstock
    return vnstock.status(), vnstock.usage()


def _dang_nhap() -> dict:
    from vnstock_auth import ensure_api_key
    return ensure_api_key()


def kiem_goi(doc=None, dang_nhap=None, dung_cache: bool = True) -> TrangThaiGoi:
    """So hạng máy chủ cấp (`status()`) với hạng thư viện đang áp (`usage()`).

    `doc` (trả `(status, usage)`) và `dang_nhap` (trả dict như
    `vnstock_auth.ensure_api_key()`) tiêm được để test chạy offline. Test gọi mạng
    thì đỏ khi mất mạng và xanh khi máy chủ trả rác — cả hai đều nói sai.

    KHÔNG BAO GIỜ ném, và KHÔNG BAO GIỜ in khoá.
    """
    tiem = doc is not None or dang_nhap is not None
    if dung_cache and not tiem:
        co = _CACHE.get("goi")
        if co and time.time() - co[0] < TTL_GIAY:
            return co[1]

    def _luu(tt: TrangThaiGoi) -> TrangThaiGoi:
        if dung_cache and not tiem:
            _CACHE["goi"] = (time.time(), tt)
        return tt

    def _chiu(ly_do: str, **kw) -> TrangThaiGoi:
        return _luu(TrangThaiGoi(tinh_trang=CHUA_KIEM_DUOC, ly_do=ly_do, **kw))

    try:
        dn = (dang_nhap or _dang_nhap)()
    except Exception as e:
        return _chiu(f"không đăng nhập được vnstock ({type(e).__name__})")
    if not isinstance(dn, dict):
        return _chiu("không đọc được trạng thái đăng nhập")
    if not dn.get("ok"):
        loi = str(dn.get("error") or "")
        if loi.startswith("chưa cấu hình"):
            return _chiu("chưa cấu hình API key")
        return _chiu(f"đăng nhập vnstock thất bại — {loi[:100]}")

    try:
        st, us = (doc or _doc_may_chu)()
    except Exception as e:
        return _chiu(f"{type(e).__name__}: {str(e)[:100]}")
    if not isinstance(st, dict) or not isinstance(us, dict):
        return _chiu("thư viện trả về dữ liệu không đọc được")

    hang_mc = st.get("tier")
    hang_cb = us.get("tier")
    if not hang_mc or not hang_cb:
        return _chiu("không đọc được hạng gói — cấu trúc đã đổi")
    if st.get("authenticated") is not True:
        return _chiu("máy chủ chưa xác nhận khoá (đang ở hạng khách)",
                     hang_may_chu=str(hang_mc), hang_cuc_bo=str(hang_cb))

    het_han = str(st.get("expires_at") or "")[:10] or None
    quy_tac = us.get("rule") if isinstance(us.get("rule"), dict) else {}
    han_muc = us.get("limits") if isinstance(us.get("limits"), dict) else {}
    con_han = bool(st.get("active"))

    ly_do = ""
    if hang_mc != hang_cb:
        ly_do = "hạng máy chủ cấp khác hạng thư viện đang áp"
    elif not con_han:
        ly_do = "máy chủ báo gói không còn hiệu lực"

    return _luu(TrangThaiGoi(
        tinh_trang=LECH if ly_do else KHOP,
        hang_may_chu=str(hang_mc), hang_cuc_bo=str(hang_cb),
        con_han=con_han, het_han=het_han,
        ky_bctc=quy_tac.get("periods"), han_muc_phut=han_muc.get("per_minute"),
        ly_do=ly_do))


def xoa_cache() -> None:
    """Dùng trong test — cache dính giữa các ca test là một nguồn nhiễu."""
    _CACHE.clear()
