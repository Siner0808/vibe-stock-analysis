"""
ke_hoach_vao_lenh.py
Kế hoạch vào lệnh: agent phán quyết ĐIỂM VÀO — CHỈ ĐỂ HIỆN (BƯỚC 173, mốc B6).

VÌ SAO FILE NÀY TỒN TẠI
───────────────────────
Người dùng 09/10/2026 (Q12): *"Hãy giao việc phán quyết cho Agent, không phải
cứ điểm cao là mua (đôi khi đạt đủ điểm chưa chắc đã đúng điểm vào lệnh)"*.

Đường thật hiện tại: điểm ≥ `paper_trading.BUY_THRESHOLD` → lệnh PENDING →
khớp ở GIÁ MỞ CỬA phiên sau. Không chỗ nào xét giá đang đứng ở đâu so với hỗ
trợ, đã chạy xa MA20 bao nhiêu, hay cắt lỗ cấu trúc cách bao xa. App thì in
"MUA 30%" cho mọi điểm qua ngưỡng. B6 tách hai việc:

  · CHỌN mã   — điểm (giữ nguyên, không đụng tới);
  · ĐIỂM VÀO  — module này: lập kế hoạch và PHÁN QUYẾT kèm lý do.

VÌ SAO CHỈ ĐỂ HIỆN, KHÔNG VÀO SỔ (đừng đổi điều này trong cùng bài)
───────────────────────────────────────────────────────────────────
Phán quyết CHƯA ĐO. Đổi cách khớp của sổ giữa chừng phá phép đo tiến về phía
trước (`NGUYEN-TAC-DO-LUONG.md`, bất biến 7). Hệ quả cứng: chỉ `app.py` được
nhập module này (`tests/test_ke_hoach_vao_lenh.py`).

Thứ tự đã duyệt: B6 (hiện) → một phép đo thăm dò KHAI TIÊU CHÍ TRƯỚC → C7 chạy
bóng → sớm nhất 11/2026 mới bàn tới đường thật. Ba bẫy đã biết:
  1. Lệnh giới hạn TỰ CHỌN LỆNH THUA (chỉ khớp khi giá đang rơi) → phải đo theo
     MỖI TÍN HIỆU, kể cả lệnh lỡ.
  2. Ít lệnh hơn → điều kiện dừng (`N_TOI_THIEU`) đến chậm hơn.
  3. Không đổi đường thật giữa chừng.

HÀM THUẦN
─────────
Không mạng, không đồng hồ (`bay_gio` là tham số), chỉ dùng các dòng của `df`
đưa vào — để phép đo thăm dò sau này chạy lại ĐÚNG hàm này trên cache lịch sử.
`nguong` BẮT BUỘC, không có mặc định: một ngưỡng mua, một chỗ (app truyền
`BUY_THRESHOLD`).

MỌI HẰNG SỐ DƯỚI ĐÂY LÀ "ĐỀ XUẤT, CHƯA ĐO"
──────────────────────────────────────────
Phép đo thăm dò trước C7 khai tiêu chí TRƯỚC rồi mới đo; chỉnh hằng số sau khi
nhìn số là vi phạm bất biến 7. Riêng hai biên rủi ro NHẬP từ `muc_fibonacci`
(`SL_HEP_NHAT`, `SL_RONG_NHAT`) — đúng biên mà SL theo ATR của sổ đang kẹp vào.

NGHĨA CỦA `CHO_VUNG` — phép đo sau phải dùng ĐÚNG định nghĩa này
─────────────────────────────────────────────────────────────────
  · lệnh giới hạn đặt ở TRẦN của `vung`, hiệu lực `SO_PHIEN_CHO` phiên kể từ
    phiên SAU ngày t (ngày nến đã đóng cuối cùng);
  · khớp ở phiên đầu tiên có low ≤ trần vùng, giá khớp = min(open, trần vùng);
  · hết hạn mà không khớp = LỠ — một kết cục được ĐẾM, không bị bỏ.
Module này KHÔNG viết hàm khớp: nó chỉ nêu định nghĩa.

`MUA_NGAY` nghĩa là khớp ở giá mở cửa phiên sau, đúng như sổ đang làm.

ĐƠN VỊ: tính trên giá thô của `df`, nhân `he_so_gia` ở ĐẦU RA (như
`muc_fibonacci`). `keo_gian_atr` và `rui_ro_pct` không có đơn vị giá.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime

import pandas as pd

import data_quality
import pha_wyckoff
from muc_fibonacci import SL_HEP_NHAT, SL_RONG_NHAT

# ── Hằng số — ĐỀ XUẤT, CHƯA ĐO (xem docstring) ────────────────────────
#: ATR 14 = trung bình trượt đơn của true range, CÙNG định nghĩa với
#: `data_collectors.DataOrchestrator._compute_local_indicators`.
CHU_KY_ATR = 14
#: MA của giá đóng cửa. Khớp `khung_thoi_gian.CHU_KY_MA_NGAN` (test giữ).
CHU_KY_MA = 20
#: Cắt lỗ cấu trúc đặt dưới đáy của ngần này phiên gần nhất (gồm ngày t).
CUA_SO_DAY = 20
#: ...trừ thêm ngần này ATR làm đệm.
HE_SO_DEM_ATR = 0.5
#: Giá đã chạy xa MA20 hơn ngần này ATR thì không đuổi theo.
KEO_GIAN_TOI_DA_ATR = 2.0
#: Hiệu lực của vùng chờ, tính bằng phiên kể từ phiên sau ngày t.
SO_PHIEN_CHO = 5
#: Số nến đã đóng tối thiểu — SUY từ các chu kỳ trên, không gõ số.
#: ATR cần CHU_KY_ATR true range mà true range đầu tiên không có giá đóng
#: trước, nên +1.
SO_NEN_TOI_THIEU = max(CHU_KY_MA, CHU_KY_ATR + 1, CUA_SO_DAY)

# ── Phán quyết ────────────────────────────────────────────────────────
KHONG_XET = "KHONG_XET"          # điểm dưới ngưỡng — chưa phải ứng viên
CHUA_LAP_DUOC = "CHUA_LAP_DUOC"  # thiếu dữ liệu — không đoán
BO_QUA = "BO_QUA"
MUA_NGAY = "MUA_NGAY"
CHO_VUNG = "CHO_VUNG"

#: Nhãn hiện trên app và lớp màu CSS (`pos` / `neu` / `neg`).
HIEN_THI = {
    KHONG_XET: ("THEO DÕI", "neu"),
    MUA_NGAY: ("MUA NGAY", "pos"),
    CHO_VUNG: ("CHỜ VÙNG", "neu"),
    BO_QUA: ("BỎ QUA", "neg"),
    CHUA_LAP_DUOC: ("CHƯA LẬP ĐƯỢC", "neu"),
}

_COT_GIA = ("open", "high", "low", "close")
_COT_BAT_BUOC = ("time", *_COT_GIA)


@dataclass(frozen=True)
class KeHoachVaoLenh:
    """Kết quả. Mọi giá đã nhân `he_so_gia` (VNĐ khi app truyền `mult`).

    Trường nào không tính được thì là `None`, không phải 0.
    """

    phan_quyet: str
    ly_do: tuple[str, ...]
    ngay: str | None                 # ngày nến t (nến đã đóng cuối cùng)
    gia_dong: float | None
    atr: float | None
    ma20: float | None
    keo_gian_atr: float | None       # (close − MA20) / ATR
    cat_lo_cau_truc: float | None
    rui_ro_pct: float | None         # (close − cắt lỗ) / close × 100
    vung: tuple[float, float] | None  # (đáy, trần) vùng chờ — chỉ khi CHO_VUNG
    so_phien_cho: int | None
    nhan: str


def _ket(phan_quyet: str, ly_do, nhan: str, **truong) -> KeHoachVaoLenh:
    mac_dinh = dict(ngay=None, gia_dong=None, atr=None, ma20=None,
                    keo_gian_atr=None, cat_lo_cau_truc=None, rui_ro_pct=None,
                    vung=None, so_phien_cho=None)
    mac_dinh.update(truong)
    return KeHoachVaoLenh(phan_quyet=phan_quyet, ly_do=tuple(ly_do),
                          nhan=nhan, **mac_dinh)


def _chua_lap(ly_do: str, **truong) -> KeHoachVaoLenh:
    """Không lập được — nói rõ vì sao, không trả một kế hoạch trung tính."""
    return _ket(CHUA_LAP_DUOC, [ly_do], f"Chưa lập được — {ly_do}", **truong)


def _la_so(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) \
        and not math.isnan(x)


def _lam_sach(df: pd.DataFrame) -> pd.DataFrame:
    """Bản sao có giá là số, bỏ dòng hỏng. KHÔNG sửa `df` của người gọi."""
    d = df.copy()
    for c in _COT_GIA:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.dropna(subset=["time", *_COT_GIA]).reset_index(drop=True)


def lap_ke_hoach(df: pd.DataFrame | None, he_so_gia: float, diem: float,
                 nguong: float, bay_gio: datetime) -> KeHoachVaoLenh:
    """Lập kế hoạch vào lệnh cho nến đã đóng cuối cùng của `df`.

    `df`: nến ngày tăng dần, cột time/open/high/low/close/volume.
    `diem`: điểm cuối của mã. `nguong`: ngưỡng mua (BẮT BUỘC, không mặc định).
    `bay_gio`: do người gọi đưa vào; nến cuối bị bỏ nếu chưa đóng.
    """
    # ── 2. Ngưỡng. Điểm BẰNG ngưỡng thì được xét, như `consider_entry`. ──
    if not _la_so(diem):
        return _chua_lap("điểm không đọc được")
    if diem < nguong:
        ly = f"điểm {diem:g} dưới ngưỡng {nguong:g} — chưa phải ứng viên"
        return _ket(KHONG_XET, [ly], ly)

    thieu = [c for c in (*_COT_BAT_BUOC, "volume")
             if df is None or c not in getattr(df, "columns", [])]
    if thieu:
        return _chua_lap(f"thiếu cột {', '.join(thieu)}")

    # ── 1. Nến dở. Bỏ trước khi đọc BẤT KỲ giá nào. ──
    d = _lam_sach(df)
    if len(d) and data_quality.nen_cuoi_dang_do(d["time"].iloc[-1], bay_gio):
        d = d.iloc[:-1].reset_index(drop=True)

    # ── 3. Đủ dữ liệu. ──
    if len(d) < SO_NEN_TOI_THIEU:
        return _chua_lap(f"chỉ có {len(d)} nến đã đóng, cần ít nhất "
                         f"{SO_NEN_TOI_THIEU}")

    # ── 4. Các đại lượng trên nến đã đóng cuối cùng (ngày t). ──
    ngay = str(d["time"].iloc[-1])[:10]
    close, high, low = d["close"], d["high"], d["low"]
    tr = pd.concat([high - low,
                    (high - close.shift()).abs(),
                    (low - close.shift()).abs()], axis=1).max(axis=1)
    atr = float(tr.rolling(CHU_KY_ATR).mean().iloc[-1])
    ma20 = float(close.rolling(CHU_KY_MA).mean().iloc[-1])
    gia = float(close.iloc[-1])
    day = float(low.tail(CUA_SO_DAY).min())
    if not all(_la_so(x) for x in (atr, ma20, gia, day)) or atr <= 0 or gia <= 0:
        return _chua_lap("ATR hoặc giá không dương/không đọc được", ngay=ngay)

    keo_gian = (gia - ma20) / atr
    cat_lo = day - HE_SO_DEM_ATR * atr
    if cat_lo <= 0:
        return _chua_lap("cắt lỗ cấu trúc không dương", ngay=ngay)
    rui_ro = (gia - cat_lo) / gia

    # Vùng GIÁ vừa ngân sách rủi ro: (p − s)/p ∈ [SL_HEP_NHAT, SL_RONG_NHAT].
    # Rủi ro tăng theo giá, nên biên hẹp là ĐÁY vùng, biên rộng là TRẦN vùng.
    day_ngan_sach = cat_lo / (1.0 - SL_HEP_NHAT)
    tran_ngan_sach = cat_lo / (1.0 - SL_RONG_NHAT)
    tran_keo_gian = ma20 + KEO_GIAN_TOI_DA_ATR * atr

    he = he_so_gia
    chung = dict(ngay=ngay, gia_dong=gia * he, atr=atr * he, ma20=ma20 * he,
                 keo_gian_atr=keo_gian, cat_lo_cau_truc=cat_lo * he,
                 rui_ro_pct=rui_ro * 100.0)

    # ── 5. Phán quyết. Giữ MỌI lý do áp dụng, không chỉ lý do đầu. ──
    pha = pha_wyckoff.doc_pha(d, he_so_gia)
    wy_giam = pha.ket_luan_duoc and pha.huong == pha_wyckoff.GIAM
    ly_wy = ([f"cấu trúc Wyckoff hướng giảm: {pha.nhan_ngan}"]
             if wy_giam else [])

    vuot_rui_ro = gia > tran_ngan_sach
    vuot_keo_gian = keo_gian > KEO_GIAN_TOI_DA_ATR

    if not vuot_rui_ro and not vuot_keo_gian:
        if wy_giam:
            return _ket(BO_QUA, ly_wy, f"Bỏ qua — {ly_wy[0]}", **chung)
        ly_mua = [f"rủi ro tới cắt lỗ cấu trúc {rui_ro * 100:.1f}% (không quá "
                  f"{SL_RONG_NHAT * 100:.1f}%) và giá cách MA{CHU_KY_MA} "
                  f"{keo_gian:.1f} ATR (không quá {KEO_GIAN_TOI_DA_ATR:g})"]
        if rui_ro < SL_HEP_NHAT:
            ly_mua.append("cắt lỗ cấu trúc sát hơn biên dưới ngân sách rủi ro "
                          f"({SL_HEP_NHAT * 100:.1f}%)")
        return _ket(MUA_NGAY, ly_mua,
                    f"Mua ngay (khớp giá mở cửa phiên sau) · rủi ro "
                    f"{rui_ro * 100:.1f}% · kéo giãn {keo_gian:.1f} ATR",
                    **chung)

    # Giá đóng không vào được ngay: nêu ĐÚNG điều kiện đã trượt.
    ly_truot = []
    if vuot_rui_ro:
        ly_truot.append(f"rủi ro {rui_ro * 100:.1f}% vượt "
                        f"{SL_RONG_NHAT * 100:.1f}% nếu vào ở giá đóng")
    if vuot_keo_gian:
        ly_truot.append(f"giá cách MA{CHU_KY_MA} {keo_gian:.1f} ATR, vượt "
                        f"{KEO_GIAN_TOI_DA_ATR:g} ATR")

    tran_vung = min(tran_ngan_sach, tran_keo_gian)
    if tran_vung < day_ngan_sach:
        ly = ly_wy + ly_truot + [
            "không có giá nào vừa cả ngân sách rủi ro lẫn độ kéo giãn"]
        return _ket(BO_QUA, ly, f"Bỏ qua — {ly[0]}", **chung)
    if wy_giam:
        ly = ly_wy + ly_truot
        return _ket(BO_QUA, ly, f"Bỏ qua — {ly[0]}", **chung)

    vung = (day_ngan_sach * he, tran_vung * he)
    return _ket(CHO_VUNG, ly_truot,
                f"Chờ giá về {vung[0]:,.0f} – {vung[1]:,.0f} trong "
                f"{SO_PHIEN_CHO} phiên", vung=vung,
                so_phien_cho=SO_PHIEN_CHO, **chung)
