"""
khung_thoi_gian.py
Nến TUẦN · THÁNG gộp từ nến NGÀY — CHỈ ĐỂ HIỆN (BƯỚC 171, mốc B5).

VÌ SAO FILE NÀY TỒN TẠI
───────────────────────
App chỉ vẽ nến ngày, nên người xem không có cái nhìn từ vi mô lên vĩ mô
bằng phương pháp kỹ thuật (người dùng 09/10/2026). Module này gộp chuỗi ngày
đã qua cổng kiểm định thành nến tuần và tháng để app vẽ ba khung D-W-M.

VÌ SAO CHỈ ĐỂ HIỆN, KHÔNG CHẤM ĐIỂM
────────────────────────────────────
Nến tuần/tháng gộp từ CHÍNH chuỗi giá ngày, nên chúng không phải dữ liệu độc
lập. `CLAUDE.md` mục "Trạng thái đo được": điểm cuối không dự báo lợi nhuận
và thêm tầng vào một hệ có rho ≈ 0 không cải thiện được gì. Dùng xu hướng
tuần/tháng làm bộ lọc lệnh ảo là một ứng viên tầng 3 riêng, phải khai trước —
KHÔNG thuộc bài này. Hệ quả cứng: chỉ `app.py` được nhập module này
(`tests/test_khung_thoi_gian.py`).

QUY TẮC NẾN ĐÃ ĐÓNG — vì sao không dùng `resample` mặc định
────────────────────────────────────────────────────────────
`resample("W")`/`resample("ME")` gắn nhãn mỗi nến bằng NGÀY CUỐI TUẦN/THÁNG
THEO LỊCH, và giữ cả kỳ đang dở. Hai thứ đó cùng là nhìn trộm: một nến tuần
mang nhãn Chủ nhật 11/10 trong khi dữ liệu mới tới thứ Tư 07/10 nói rằng nó
có mặt từ trước phiên thứ Năm; một nến tháng đang dở trông như một tháng.
Ở đây:

- Nhãn mỗi nến = ngày của PHIÊN CUỐI THẬT SỰ có trong nhóm.
- Nến ngày cuối còn đang dở (`data_quality.nen_cuoi_dang_do`) bị bỏ TRƯỚC khi
  gộp.
- Kỳ cuối của dữ liệu chỉ được giữ khi lịch phiên CÔNG BỐ của dự án
  (`lich_giao_dich`) chứng minh sau ngày cuối của nó không còn phiên nào trong
  kỳ. Lịch không phủ → "chưa kiểm được" → coi như đang dở. Không gõ ngày nghỉ
  lễ ở đây.
- Mọi kỳ TRƯỚC kỳ cuối là đã đóng: dữ liệu có phiên ở kỳ sau chứng minh điều
  đó, không cần lịch.
- Kỳ đầu bị cửa sổ tải cắt ngang (kỳ bắt đầu trước `tu_ngay`) bị bỏ: nến của
  nó thiếu phiên nên open/high/low/volume sai im lặng.

Hệ quả kiểm được (`tests/test_khung_thoi_gian.py`, gác chống nhìn trộm):
gộp rồi lọc theo ngày t = lọc rồi gộp.

KHÔNG làm ở đây: không nhân `price_multiplier` (app nhân lúc vẽ như nến ngày),
`volume` không bao giờ nhân; không điều chỉnh giá theo sự kiện quyền (mốc D2
chưa làm) nên trên khung tháng nhiều năm có thể có bậc giá giả.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Mapping

import pandas as pd

import data_quality
import lich_giao_dich

#: Các khung hiển thị. D là chính chuỗi ngày (đã bỏ nến dở), W/M do `gop_nen` dựng.
KHUNG = ("D", "W", "M")
KHUNG_GOP = ("W", "M")

#: Chu kỳ hai đường trung bình trên chart nến — MỘT nơi khai, `app.py` đọc từ đây
#: cho cả ba khung để khung D và khung W/M không thể lệch nhau.
CHU_KY_MA_NGAN = 20
CHU_KY_MA_DAI = 50
CHU_KY_DAI_NHAT = max(CHU_KY_MA_NGAN, CHU_KY_MA_DAI)

#: Hai kỳ đệm cho chuỗi tháng: kỳ đầu bị cửa sổ cắt ngang (bị bỏ) và kỳ cuối
#: đang dở (bị bỏ). Thiếu hai kỳ này thì MA dài nhất luôn thiếu đúng 2 nến.
SO_KY_DEM = 2
#: Số nến THÁNG cần để chỉ báo dài nhất (MA50) có giá trị ở nến cuối.
SO_NEN_THANG_CAN = CHU_KY_DAI_NHAT + SO_KY_DEM
#: Ngày lịch trung bình một tháng (năm Gregorian / 12).
NGAY_LICH_MOT_THANG = 365.25 / 12


def ngay_lich_cho_nen_thang(so_nen: int) -> int:
    """Đổi số nến tháng sang số NGÀY LỊCH phải xin nguồn (làm tròn lên)."""
    return math.ceil(so_nen * NGAY_LICH_MOT_THANG)


#: Cửa sổ tải cho khung W/M: suy từ chu kỳ chỉ báo dài nhất, không gõ số ngày.
NGAY_LICH_CHO_KHUNG_THANG = ngay_lich_cho_nen_thang(SO_NEN_THANG_CAN)

_CAC_COT = ("time", "open", "high", "low", "close", "volume")


def _rong() -> pd.DataFrame:
    return pd.DataFrame({c: [] for c in _CAC_COT})


def _chuan_ngay(df: pd.DataFrame | None) -> pd.DataFrame:
    """Bản sao sắp tăng dần, bỏ ngày không đọc được/trùng, thêm cột `_ngay`."""
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return _rong().assign(_ngay=pd.Series(dtype="datetime64[ns]"))
    thieu = [c for c in _CAC_COT if c not in df.columns]
    if thieu:
        raise ValueError(f"thiếu cột: {', '.join(thieu)}")
    out = df.copy()
    t = pd.to_datetime(out["time"], errors="coerce")
    if getattr(t.dt, "tz", None) is not None:
        t = t.dt.tz_localize(None)
    out["_ngay"] = t.dt.normalize()
    out = (out.dropna(subset=["_ngay"])
              .drop_duplicates(subset=["_ngay"], keep="last")
              .sort_values("_ngay")
              .reset_index(drop=True))
    return out


def _iso(ts: pd.Timestamp) -> str:
    return ts.strftime("%Y-%m-%d")


def _bo_nen_cuoi_dang_do(d: pd.DataFrame, bay_gio: datetime) -> pd.DataFrame:
    if len(d) and data_quality.nen_cuoi_dang_do(d["_ngay"].iloc[-1], bay_gio):
        return d.iloc[:-1].reset_index(drop=True)
    return d


def nen_ngay_da_dong(df: pd.DataFrame | None, bay_gio: datetime) -> pd.DataFrame:
    """Chuỗi ngày sau khi bỏ nến cuối nếu nó chưa đóng (`nen_cuoi_dang_do`).

    `bay_gio` do người gọi đưa vào — hàm thuần, không hỏi đồng hồ.
    """
    d = _bo_nen_cuoi_dang_do(_chuan_ngay(df), bay_gio)
    if d.empty:
        return _rong()
    d["time"] = d["_ngay"].dt.strftime("%Y-%m-%d")
    return d[list(_CAC_COT)]


def _ky_cuoi_da_dong(ngay_cuoi: pd.Timestamp, het_ky: pd.Timestamp) -> bool:
    """Sau `ngay_cuoi` còn phiên nào trong kỳ (tới `het_ky`) không?

    Chỉ trả True khi lịch CÔNG BỐ phủ cả hai đầu và nói "không còn". Lịch
    không phủ → False (chưa kiểm được, coi như đang dở).
    """
    con = lich_giao_dich.cac_phien(_iso(ngay_cuoi), _iso(het_ky))
    return con is not None and len(con) == 0


def gop_nen(df_ngay: pd.DataFrame | None, khung: str, bay_gio: datetime,
            tu_ngay: str | None = None) -> pd.DataFrame:
    """Nến tuần ("W", thứ Hai → Chủ nhật) hoặc tháng ("M") — CHỈ nến ĐÃ ĐÓNG.

    Cột ra: time (ngày PHIÊN CUỐI thật có trong nhóm, "YYYY-MM-DD"), open (phiên
    đầu), high (max), low (min), close (phiên cuối), volume (tổng). Giá giữ đơn
    vị của đầu vào.

    `tu_ngay`: ngày SỚM NHẤT mà dữ liệu thật sự phủ tới (người gọi đọc từ chính
    bảng nó đã tải — KHÔNG phải ngày nó đã xin: nguồn có thể cắt ngắn hơn). Kỳ
    bắt đầu TRƯỚC ngày này bị cửa sổ cắt ngang nên bị bỏ, vì nến của nó thiếu
    phiên. `None` = người gọi khẳng định dữ liệu không bị cắt.
    """
    if khung not in KHUNG_GOP:
        raise ValueError(f"khung phải là một trong {KHUNG_GOP}, nhận {khung!r}")
    d = _bo_nen_cuoi_dang_do(_chuan_ngay(df_ngay), bay_gio)
    if d.empty:
        return _rong()

    ma_ky = "W-SUN" if khung == "W" else "M"
    d["_ky"] = d["_ngay"].dt.to_period(ma_ky)
    nhom = d.groupby("_ky", sort=True)
    nen = pd.DataFrame({
        "time": nhom["_ngay"].max(),
        "open": nhom["open"].first(),
        "high": nhom["high"].max(),
        "low": nhom["low"].min(),
        "close": nhom["close"].last(),
        "volume": nhom["volume"].sum(),
    })
    nen["_dau_ky"] = [p.start_time.normalize() for p in nen.index]
    nen["_het_ky"] = [p.end_time.normalize() for p in nen.index]

    giu = pd.Series(True, index=nen.index)
    # Kỳ cuối: giữ khi lịch chứng minh nó đã đóng.
    giu.iloc[-1] = _ky_cuoi_da_dong(nen["time"].iloc[-1], nen["_het_ky"].iloc[-1])
    # Kỳ đầu bị cửa sổ cắt ngang.
    if tu_ngay is not None:
        giu &= nen["_dau_ky"] >= pd.Timestamp(str(tu_ngay)[:10])

    nen = nen[giu].reset_index(drop=True)
    nen["time"] = nen["time"].dt.strftime("%Y-%m-%d")
    return nen[list(_CAC_COT)]


# ─────────────────────────── Nhãn đồng pha ───────────────────────────
TREN, DUOI, BANG, CHUA_DU = "trên", "dưới", "bằng", "chưa đủ"


def vi_tri_so_voi_ma(nen: pd.DataFrame | None,
                     chu_ky: int = CHU_KY_MA_NGAN) -> tuple[str, str]:
    """(trạng thái, mô tả) — giá đóng cửa cuối so với MA của CHÍNH khung ấy.

    Thiếu nến cho MA thì `CHUA_DU` và mô tả "chưa đủ n nến" — không đoán.
    """
    n = 0 if nen is None else len(nen)
    if nen is None or n < chu_ky:
        return CHUA_DU, f"chưa đủ {chu_ky} nến (có {n})"
    close = pd.to_numeric(nen["close"], errors="coerce")
    ma = close.rolling(window=chu_ky).mean().iloc[-1]
    cuoi = close.iloc[-1]
    if pd.isna(ma) or pd.isna(cuoi):
        return CHUA_DU, f"chưa đủ {chu_ky} nến hợp lệ (có {n})"
    if cuoi > ma:
        return TREN, TREN
    if cuoi < ma:
        return DUOI, DUOI
    return BANG, BANG


@dataclass(frozen=True)
class DongPha:
    dong: str            # "D: trên · W: dưới · M: trên — lệch pha"
    ket_luan: str        # "đồng pha" · "lệch pha" · "chưa đủ …"
    trang_thai: dict     # {"D": "trên", ...} — trạng thái thô từng khung


def doc_dong_pha(nen_theo_khung: Mapping[str, pd.DataFrame | None],
                 chu_ky: int = CHU_KY_MA_NGAN) -> DongPha:
    """Một dòng nói ba khung có cùng đứng trên/dưới MA của chính nó không."""
    trang_thai, phan = {}, []
    for k in KHUNG:
        tt, mo_ta = vi_tri_so_voi_ma(nen_theo_khung.get(k), chu_ky)
        trang_thai[k] = tt
        phan.append(f"{k}: {mo_ta}")
    biet = {tt for tt in trang_thai.values() if tt != CHUA_DU}
    if len(biet) >= 2:
        ket_luan = "lệch pha"
    elif len(biet) == 1 and CHUA_DU not in trang_thai.values():
        ket_luan = "đồng pha"
    else:
        ket_luan = "chưa đủ nến ở mọi khung để kết luận đồng pha"
    return DongPha(" · ".join(phan) + f" — {ket_luan}", ket_luan, trang_thai)
