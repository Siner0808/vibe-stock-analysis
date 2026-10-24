"""chot_sut_giam.py — chốt sụt giảm của sổ (vốn đã chốt) cho ĐO 33 (BƯỚC 226).

ĐỊNH NGHĨA ĐÃ GHIM TRƯỚC — `docs/TIEU-CHI-DOC-TRUOC.md`, mục "ĐO 33". Đổi một
hằng số ở đây là đổi phép đo sau khi đã ký (bất biến 7); đọc mục ấy trước.

    E(d)    100 × ∏ (1 + r/100 × s/100) trên lệnh CLOSED có ngày ra < d, nhân theo
            thứ tự ngày ra — cùng công thức `paper_metrics.compute`
    phiên   ngày có dòng VNINDEX trong cache
    máy     đỉnh P bắt đầu 100. Không đóng băng: P = max(P, E); (P − E)/P > ngưỡng
            → đóng băng từ phiên ấy. Đóng băng từ d₀: chặn d₀ … d₁₉; ở d₂₀ mở băng,
            P = E(d₂₀), rồi xét lại.

VÌ SAO "< d" CHỨ KHÔNG "≤ d" — trong một phiên, walkforward chạy các mã theo thứ tự
chữ cái và mỗi mã xử lý lệnh thoát của nó TRƯỚC khi xét mở lệnh. Với "≤ d", mã đứng
trước thấy một E, mã đứng sau thấy E khác trong cùng phiên; "< d" cho mọi mã một E,
và dụng cụ dựng lại được từ sổ sau khi chạy.

Số phiên chặn chỉ khai ở MỘT chỗ, `paper_trading.CHOT_SUT_GIAM_PHIEN`; hàm ở đây nhận nó làm đối số.
Đường giao dịch KHÔNG nhập module này trừ khi `paper_trading.CHOT_SUT_GIAM_NGUONG` > 0.
"""
from __future__ import annotations

from bisect import bisect_left
from functools import lru_cache
from pathlib import Path

import pandas as pd

MA_CHI_SO = "VNINDEX"


def he_so_lenh(lenh) -> list[tuple[str, float]]:
    """(ngày ra, 1 + r/100 × s/100) của mọi lệnh CLOSED có lợi nhuận, sắp theo ngày ra."""
    ra = []
    for t in lenh:
        if t.status != "CLOSED":
            continue
        r = t.net_return_pct()
        if r is None or not t.exit_date:
            continue
        ra.append((str(t.exit_date)[:10], 1 + (r / 100) * (t.size_pct / 100)))
    ra.sort(key=lambda x: x[0])
    return ra


def may_trang_thai(phien: list[str], he_so: list[tuple[str, float]], t: str, nguong: float,
                   so_phien: int) -> tuple[float, str] | None:
    """Hàm THUẦN. (mức sụt lúc đóng băng, phiên bắt đầu) nếu sổ ĐANG đóng băng ở phiên cuối ≤ `t`;
    None nếu không. `phien` tăng dần; `he_so` sắp theo ngày ra."""
    von = dinh = 100.0
    j, i0, sut0 = 0, None, 0.0
    for i, d in enumerate(phien):
        if d > t:
            break
        while j < len(he_so) and he_so[j][0] < d:          # đã chốt TRƯỚC phiên d
            von *= he_so[j][1]
            j += 1
        if i0 is not None and i - i0 >= so_phien:
            i0, dinh = None, von                          # mở băng, đặt lại đỉnh
        if i0 is None:
            dinh = max(dinh, von)
            if (dinh - von) / dinh > nguong:
                i0, sut0 = i, (dinh - von) / dinh
    return (sut0, phien[i0]) if i0 is not None else None


def khoi_dong_bang(phien: list[str], he_so: list[tuple[str, float]], nguong: float,
                   so_phien: int) -> list[tuple[str, list[str]]]:
    """Mọi khối đóng băng trên toàn lịch: [(phiên bắt đầu, [các phiên bị chặn])]. Cùng máy trạng thái."""
    khoi: list[tuple[str, list[str]]] = []
    for d in phien:
        tt = may_trang_thai(phien[:bisect_left(phien, d) + 1], he_so, d, nguong, so_phien)
        if tt is None:
            continue
        if not khoi or khoi[-1][0] != tt[1]:
            khoi.append((tt[1], []))
        khoi[-1][1].append(d)
    return khoi


@lru_cache(maxsize=4)
def lich_phien(thu_muc: str) -> tuple[str, ...]:
    """Ngày có dòng VNINDEX trong thư mục cache, tăng dần."""
    d = pd.read_csv(Path(thu_muc) / f"{MA_CHI_SO}.csv", usecols=["time"])
    return tuple(sorted(set(d["time"].astype(str).str[:10])))


def lich_phien_mac_dinh() -> list[str]:
    """Lịch phiên trên thư mục cache mà backtest đang dùng (`backtest.data.CACHE_DIR`)."""
    from backtest.data import CACHE_DIR
    return list(lich_phien(str(CACHE_DIR)))
