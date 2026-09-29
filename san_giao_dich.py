"""Sàn giao dịch của từng mã trong rổ — BẢNG CHỤP có ngày và nguồn (BƯỚC 143).

Vì sao có file này. Bước giá và biên độ khác nhau theo sàn (HOSE 10/50/100đ
tuỳ mức giá, HNX và UPCoM 100đ mọi mức), mà `run_daily` từng ghim cứng
`"HOSE"` cho mọi mã, nên 4 mã HNX và 3 mã UPCoM của rổ bị làm tròn giá theo
lưới HOSE — có giá không thể tồn tại trên sàn thật, và trượt giá bị tính
THẤP (chiều làm số đẹp lên). Đo và phương án: `docs/STATE.md` BƯỚC 143.

Vì sao là BẢNG CHỤP trong repo chứ không tra `Listing` lúc chạy. Mạng nằm
trong đường quyết định thì backtest hết tái lập (bất biến 2), và hai nguồn
gọi cùng một sàn bằng hai nhãn khác nhau (VCI `HSX`, KBS `HOSE`). Đổi lại
bảng có thể cũ đi khi một mã chuyển sàn — `tools/kiem_san_giao_dich.py` so lại
với hai nguồn và nói ra từng mã lệch (mã thoát 2 khi mất mạng).

Rổ không được rơi im lặng về HOSE: bảng phải có ĐỦ mọi mã của rổ, kể cả 64
mã HOSE, và `tests/test_san_giao_dich.py` bắt điều đó. `san_cua()` trả `HOSE`
cho mã NGOÀI bảng — hành vi cũ, cần cho test và công cụ dòng lệnh — nên nhánh
ấy chỉ được phép chạm mã ngoài rổ; `tra_san()` trả `None` để người gọi phân
biệt được.
"""
from __future__ import annotations

NGAY_CHUP = "2026-09-29"
NGUON = ("Listing(source='vci').symbols_by_exchange() = "
         "Listing(source='kbs').symbols_by_exchange(), khớp từng mã của rổ "
         "sau khi chuẩn hoá nhãn (HSX -> HOSE)")

SAN_HOP_LE = ("HOSE", "HNX", "UPCOM")
SAN_MAC_DINH = "HOSE"

# Nhãn của từng nguồn -> tên sàn của dự án. Nhãn KHÔNG có ở đây (DELISTED,
# BOND, XHNF, NAN…) cho None: một mã không xác định được sàn phải hiện ra là
# chưa biết, không được lặng lẽ thành HOSE.
NHAN_NGUON = {"HSX": "HOSE", "HOSE": "HOSE", "HNX": "HNX", "UPCOM": "UPCOM"}

# 71 mã của `vn100_symbols.CUSTOM_WATCHLIST_SYMBOLS`, đo 2026-09-29.
BANG_SAN: dict[str, str] = {
    "AAA": "HOSE", "ACB": "HOSE", "ACV": "UPCOM", "BAF": "HOSE",
    "BCM": "HOSE", "BID": "HOSE", "BSR": "HOSE", "CII": "HOSE",
    "CTG": "HOSE", "DCL": "HOSE", "DCM": "HOSE", "DHG": "HOSE",
    "DIG": "HOSE", "DPM": "HOSE", "DXG": "HOSE", "FPT": "HOSE",
    "FRT": "HOSE", "GAS": "HOSE", "GEL": "HOSE", "GEX": "HOSE",
    "GIL": "HOSE", "GVR": "HOSE", "HAG": "HOSE", "HAX": "HOSE",
    "HCM": "HOSE", "HDB": "HOSE", "HHP": "HOSE", "HHV": "HOSE",
    "HPG": "HOSE", "HSG": "HOSE", "HUT": "HNX", "HVN": "HOSE",
    "KDH": "HOSE", "LPB": "HOSE", "MBB": "HOSE", "MBS": "HNX",
    "MSN": "HOSE", "MSR": "UPCOM", "MWG": "HOSE", "NAF": "HOSE",
    "NKG": "HOSE", "NLG": "HOSE", "NVL": "HOSE", "OIL": "UPCOM",
    "PC1": "HOSE", "PDR": "HOSE", "PLX": "HOSE", "PNJ": "HOSE",
    "POW": "HOSE", "PVD": "HOSE", "PVS": "HNX", "PVT": "HOSE",
    "SHB": "HOSE", "SHS": "HNX", "SSI": "HOSE", "STB": "HOSE",
    "TCB": "HOSE", "VCB": "HOSE", "VCG": "HOSE", "VCI": "HOSE",
    "VCK": "HOSE", "VHM": "HOSE", "VIC": "HOSE", "VIX": "HOSE",
    "VJC": "HOSE", "VND": "HOSE", "VNM": "HOSE", "VPL": "HOSE",
    "VRE": "HOSE", "VSC": "HOSE", "VTP": "HOSE",
}


def chuan_hoa_nhan(nhan: object) -> str | None:
    """Nhãn sàn của một nguồn -> HOSE | HNX | UPCOM, hoặc None nếu lạ."""
    return NHAN_NGUON.get(str(nhan).strip().upper())


def tra_san(ma: str) -> str | None:
    """Sàn của `ma` theo bảng chụp; None nếu mã không có trong bảng."""
    return BANG_SAN.get(str(ma).strip().upper())


def san_cua(ma: str) -> str:
    """Sàn của `ma`; mã NGOÀI bảng trả `SAN_MAC_DINH` (hành vi trước BƯỚC 143).

    Rổ luôn nằm trong bảng (có gác), nên nhánh mặc định chỉ chạm mã ngoài
    rổ. Cần biết mã có trong bảng không thì dùng `tra_san`.
    """
    return tra_san(ma) or SAN_MAC_DINH
