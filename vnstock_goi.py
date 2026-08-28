"""vnstock_goi.py — hạng gói vnstock ĐANG CÓ HIỆU LỰC, không phải hạng đã mua.

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

DUONG_DAN_XAC_MINH = "https://vnstocks.com/api/vnstock/license/verify"
TTL_GIAY = 1800          # hạng gói đổi rất chậm; 30 phút là quá đủ
CHO_TOI_DA = 10          # giây — chờ lâu hơn thì thà báo "chưa kiểm được"

KHOP = "KHỚP"
LECH = "LỆCH"
CHUA_KIEM_DUOC = "CHƯA KIỂM ĐƯỢC"

#: Số kỳ báo cáo tài chính mỗi hạng được lấy. Chép từ
#: `vnai.beam.fundamental.PERIOD_LIMITS`; None nghĩa là không giới hạn.
#: Đọc động khi có thể, bảng này chỉ là đường lui khi vnai đổi cấu trúc.
KY_BCTC_THEO_HANG = {"guest": 4, "free": 8, "bronze": None,
                     "silver": None, "golden": None, "diamond": None}

_CACHE: dict[str, tuple[float, "TrangThaiGoi"]] = {}


@dataclass(frozen=True)
class TrangThaiGoi:
    """Ảnh chụp hạng gói. `tinh_trang` là thứ đáng đọc nhất."""

    tinh_trang: str                       # KHOP | LECH | CHUA_KIEM_DUOC
    hang_may_chu: str | None = None       # hạng thật, do máy chủ trả
    hang_cuc_bo: str | None = None        # hạng vnai đang tự nhận
    con_han: bool | None = None
    het_han: str | None = None            # YYYY-MM-DD
    goi_duoc_dung: tuple[str, ...] = ()   # package thuê bao cho phép
    goi_thieu: tuple[str, ...] = ()       # trong số đó, chưa cài cái nào
    ky_bctc: int | None = None            # số kỳ BCTC đang thật sự lấy được
    ky_bctc_neu_dung_hang: int | None = None
    han_muc_phut: int | None = None
    ly_do: str = ""                       # vì sao chưa kiểm được

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
        thieu = (f" Chưa cài: {', '.join(self.goi_thieu)}."
                 if self.goi_thieu else "")
        return (f"gói vnstock: máy chủ nói '{self.hang_may_chu}' nhưng thư "
                f"viện cục bộ chạy như '{self.hang_cuc_bo}' — đang bị giới hạn "
                f"như gói thấp hơn ({self._mo_ta_ky()}).{thieu}")

    def _mo_ta_ky(self) -> str:
        if self.ky_bctc is None:
            return "BCTC không giới hạn số kỳ"
        neu = self.ky_bctc_neu_dung_hang
        if neu is None and self.tinh_trang == LECH:
            return f"BCTC {self.ky_bctc} kỳ thay vì không giới hạn"
        return f"BCTC {self.ky_bctc} kỳ"


def _hang_cuc_bo() -> tuple[str | None, int | None, int | None]:
    """(hạng vnai tự nhận, số kỳ BCTC đang áp, hạn mức/phút). None nếu đọc hỏng.

    Đọc ĐỘNG từ vnai chứ không chép cứng, vì con số đang có hiệu lực mới là
    thứ cần biết — chép cứng thì bảng ở đây và hành vi thật có thể lệch nhau
    mà không ai thấy.
    """
    hang = ky = phut = None
    try:
        from vnai.beam.auth import authenticator
        hang = authenticator.get_tier()
        phut = authenticator.get_limits(hang).get("min")
    except Exception:
        pass
    try:
        from vnai.beam import fundamental
        ky = fundamental.get_max_periods()
    except Exception:
        if hang is not None:
            ky = KY_BCTC_THEO_HANG.get(hang)
    return hang, ky, phut


def _goi_da_cai(ten: str) -> bool:
    import importlib.util
    try:
        return importlib.util.find_spec(ten) is not None
    except Exception:
        return False


def _hoi_may_chu(khoa: str, ma_may: str, tai_ve) -> dict:
    return tai_ve(DUONG_DAN_XAC_MINH,
                  {"api_key": khoa, "device_id": ma_may}, CHO_TOI_DA)


def _tai_ve_that(url: str, tham_so: dict, cho: int) -> dict:
    import requests
    r = requests.get(url, params=tham_so, timeout=cho)
    r.raise_for_status()
    return r.json()


def _ma_may() -> str:
    """Mã máy vnai đã đăng ký. Sai mã thì máy chủ báo 'chưa đăng ký' oan.

    Đã bị chính cái bẫy này ngày 22/08/2026: truyền chuỗi ví dụ 'vibe-setup'
    trong tài liệu làm mã máy, máy chủ trả `deviceRegistered: false`, suýt
    kết luận nhầm là máy chưa đăng ký.
    """
    import json
    import pathlib
    p = pathlib.Path.home() / ".vnstock" / "id" / "hw_info.json"
    try:
        return str(json.loads(p.read_text(encoding="utf-8"))["device_id"])
    except Exception:
        return ""


def kiem_goi(tai_ve=None, lay_khoa=None, dung_cache: bool = True) -> TrangThaiGoi:
    """So hạng máy chủ với hạng thư viện cục bộ đang áp dụng.

    `tai_ve` và `lay_khoa` tiêm được để test chạy offline. Test gọi mạng thì
    đỏ khi mất mạng và xanh khi máy chủ trả rác — cả hai đều nói sai.

    KHÔNG BAO GIỜ ném, và KHÔNG BAO GIỜ in khoá.
    """
    if dung_cache and tai_ve is None:
        co = _CACHE.get("goi")
        if co and time.time() - co[0] < TTL_GIAY:
            return co[1]

    hang_cb, ky, phut = _hang_cuc_bo()

    def _chiu(ly_do: str) -> TrangThaiGoi:
        tt = TrangThaiGoi(tinh_trang=CHUA_KIEM_DUOC, hang_cuc_bo=hang_cb,
                          ky_bctc=ky, han_muc_phut=phut, ly_do=ly_do)
        if dung_cache and tai_ve is None:
            _CACHE["goi"] = (time.time(), tt)
        return tt

    try:
        if lay_khoa is not None:
            khoa = lay_khoa()
        else:
            from vnstock_auth import ensure_api_key
            ensure_api_key()
            import vnai
            khoa = vnai.get_api_key()
    except Exception as e:
        return _chiu(f"không đọc được API key ({type(e).__name__})")
    if not khoa:
        return _chiu("chưa cấu hình API key")

    try:
        d = _hoi_may_chu(khoa, _ma_may(), tai_ve or _tai_ve_that)
    except Exception as e:
        return _chiu(f"{type(e).__name__}: {str(e)[:100]}")
    if not isinstance(d, dict):
        return _chiu("máy chủ trả về dữ liệu không đọc được")

    tb = d.get("subscription") or {}
    hang_mc = tb.get("tier") or ("free" if d.get("userType") else None)
    if not hang_mc:
        return _chiu("máy chủ không trả về hạng gói — cấu trúc đã đổi")

    duoc_dung = tuple(d.get("availablePackages") or ())
    thieu = tuple(g for g in duoc_dung if not _goi_da_cai(g))
    het_han = str(tb.get("endDate") or "")[:10] or None

    tt = TrangThaiGoi(
        tinh_trang=KHOP if hang_mc == hang_cb else LECH,
        hang_may_chu=hang_mc, hang_cuc_bo=hang_cb,
        con_han=bool(tb.get("isActive")), het_han=het_han,
        goi_duoc_dung=duoc_dung, goi_thieu=thieu,
        ky_bctc=ky, ky_bctc_neu_dung_hang=KY_BCTC_THEO_HANG.get(hang_mc),
        han_muc_phut=phut)
    if dung_cache and tai_ve is None:
        _CACHE["goi"] = (time.time(), tt)
    return tt


def xoa_cache() -> None:
    """Dùng trong test — cache dính giữa các ca test là một nguồn nhiễu."""
    _CACHE.clear()
