"""Tầng 3 — BỘ KÉO bảng giá MỘT lượt cho máy chấm xác nhận (P3d, BƯỚC 162).

Ra đúng định dạng `cham_xac_nhan.dinh_dang_bang_gia`: CSV dài
`symbol,date,close,nguon,keo_luc`, MỘT `keo_luc` cho cả bảng, `nguon` MỖI MÃ. Bảng
này là thứ `cham_xac_nhan.doc_bang_gia` đọc; người dùng chốt 06/10/2026 *"Một bảng tải
một lần"* (BƯỚC 159, ĐO 24: `close` lệch thật giữa hai lượt kéo ở 21,6% nến chung).

CHẠY THẬT là việc của MÁY người dùng (gói vnstock, mạng giá). Module này không nhập
`vnstock` ở mức module; hàm lấy dữ liệu là THAM SỐ (`lay`) để test bằng hàm giả. Mặc
định `lay_mac_dinh` uỷ cho `VNStockCollectorAgent.collect` — nguồn `vci` rồi `kbs`,
cùng họ nguồn với agent sống — và nhập `data_collectors` NGAY TRONG HÀM.

Bốn điều bộ kéo không được làm, mỗi điều chặn một cách bảng giá tự khen mình:

1. **Không nhận `SYNTHETIC` / `FAILED`.** `collect` có đường lui sinh bước đi ngẫu
   nhiên (`_generate_fallback_df`) mang một DataFrame ĐỦ DÒNG — kiểm "df có rỗng
   không" bỏ lọt nó. Chỉ `status == "OK"` kèm `source` thuộc `vci`/`kbs` được vào.
2. **Không điền.** Mã kéo hỏng, thiếu nến, giá không dương, trùng ngày: BÁO TÊN mã (và
   phiên), không điền, không bỏ mã để bảng "sạch". Còn một mã hỏng thì KHÔNG có văn bản
   bảng nào được ra: rổ chuẩn của nhãn là trung bình các mã của bảng, bỏ một mã là
   đổi rổ lặng lẽ.
3. **Không kéo trên nến dở.** `keo_luc` là giờ của lời gọi ĐẦU TIÊN (mọi giá kéo
   SAU nó), và nến cuối phải đã đóng lúc ấy (`data_quality.nen_cuoi_dang_do`).
4. **Không nối.** Một lần chạy là một lượt; không có đường nạp thêm vào bảng cũ.

Trước khi trả văn bản, bộ kéo cho nó đi qua CHÍNH `cham_xac_nhan.phan_tich_bang_gia`
và `kiem_lich` — thứ nó ghi ra phải là thứ máy chấm nhận.
"""
from __future__ import annotations

import datetime
import re
import time

import numpy as np
import pandas as pd

import cham_xac_nhan as cx
import data_quality as dq
import san_giao_dich as sg

#: Giãn nhịp giữa hai mã (giây). Hạng free: 60 lời gọi/phút; `collect` có thể gọi tới
#: HAI nguồn cho một mã (`vci` rồi `kbs`) nên 2,0 s/mã giữ trần ≤ 60 lời gọi/phút ngay
#: cả khi mọi mã phải rơi sang nguồn thứ hai. Đây là SUY LUẬN từ trần ghi ở
#: `CLAUDE.md`, chưa đo trên mạng thật.
NGHI_GIAY = 2.0
_RE_MA = re.compile(r"^[A-Z0-9]{1,10}$")
_RE_NGAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
#: Số mục (mã, phiên) in tối đa trong một thông báo; tổng số luôn in đủ.
TOI_DA_IN = cx.TOI_DA_IN


class KeoLoi(ValueError):
    """Không kéo được cả lượt (thiếu gói, tham số sai, nến cuối còn dở)."""


def lay_mac_dinh(ma: str, tu: str, den: str) -> dict:
    """Kéo MỘT mã bằng `VNStockCollectorAgent.collect` (`vci` rồi `kbs`).

    Nhập `data_collectors` ở đây chứ không ở đầu file: `collect` tự nhập `vnstock`, và
    gói ấy chỉ có trên máy người dùng. Sàn truyền cho kiểm định lấy theo MÃ từ bảng chụp
    (`san_giao_dich`), như `run_daily`.
    """
    from data_collectors import VNStockCollectorAgent
    return VNStockCollectorAgent().collect(ma, tu, den, exchange=sg.san_cua(ma))


def _gom(muc, toi_da: int = TOI_DA_IN) -> str:
    return cx._gom(muc, toi_da)


def _chuoi_gia(ma: str, kq: dict, tu: str, den: str):
    """Kết quả `collect` của MỘT mã → (chuỗi `close` theo ngày, nguồn) hoặc (None, lý do).

    Không điền, không sửa giá: chỉ NHẬN hay TỪ CHỐI.
    """
    if not isinstance(kq, dict):
        return None, f"ket qua khong phai dict: {type(kq).__name__}"
    st = kq.get("status")
    if st != "OK":
        return None, (f"status {st!r} (chi nhan 'OK'; SYNTHETIC la du lieu mo phong "
                      f"ngau nhien, FAILED la khong qua kiem dinh)")
    nguon = kq.get("source")
    if nguon not in cx.NGUON_HOP_LE:
        return None, f"nguon {nguon!r} ngoai {list(cx.NGUON_HOP_LE)}"
    df = kq.get("df")
    if df is None or len(df) == 0:
        return None, "bang rong"
    if not {"time", "close"} <= set(df.columns):
        return None, f"thieu cot time/close, co {list(df.columns)}"
    ngay = pd.to_datetime(df["time"], errors="coerce")
    if ngay.isna().any():
        return None, f"{int(ngay.isna().sum())} dong co `time` khong doc duoc"
    ngay = ngay.dt.strftime("%Y-%m-%d")
    gia = pd.to_numeric(df["close"], errors="coerce")
    s = pd.Series(gia.to_numpy(float), index=ngay.to_numpy())
    s = s[(s.index >= tu) & (s.index <= den)]
    if s.empty:
        return None, f"khong co nen nao trong [{tu}, {den}]"
    trung = sorted(set(s.index[s.index.duplicated()]))
    if trung:
        return None, f"{len(trung)} ngay trung: {_gom(trung)}"
    xau = s.index[~(np.isfinite(s.to_numpy()) & (s.to_numpy() > 0))]
    if len(xau):
        return None, (f"{len(xau)} gia khong phai so duong huu han tai "
                      f"{_gom(sorted(xau))}")
    return s.sort_index(), nguon


def keo(ma_list, tu: str, den: str, lay=None, nghi_giay: float = NGHI_GIAY,
        bay_gio=None, ngu=time.sleep) -> dict:
    """Kéo MỘT bảng giá cho `ma_list` trong [`tu`, `den`] (YYYY-MM-DD, giờ VN).

    `lay(ma, tu, den)` trả đúng dạng `VNStockCollectorAgent.collect`
    (`{"status", "df", "source", …}`); mặc định `lay_mac_dinh`. `bay_gio()` trả một
    `datetime` CÓ múi giờ (mặc định `data_quality.now_vn`); `ngu(giây)` là hàm nghỉ
    (mặc định `time.sleep`) — cả hai tiêm được để test không đợi và không hỏi đồng hồ.

    Chỉ nghỉ GIỮA các lời gọi (không nghỉ trước lời gọi đầu). Một `ImportError` của
    `lay` (thiếu gói) dừng cả lượt ngay — kéo tiếp 70 mã để nhận 70 lỗi giống nhau là
    vô ích; lỗi khác của một mã chỉ làm mã ấy `hong`.

    Trả `{"gia", "nguon", "keo_luc", "hong", "cuoi", "van_ban"}`. `hong` = {mã: lý do};
    còn `hong` thì `van_ban` là `None` (bảng không đủ mã thì không được ghi ra).
    Không `hong` mà nến cuối còn dở hoặc bảng không qua `cham_xac_nhan` thì NỔ
    (`KeoLoi` / `cham_xac_nhan.BangGiaLoi`), không trả văn bản.
    """
    ma = []
    for m in ma_list:
        m2 = str(m).strip().upper()
        if not _RE_MA.match(m2):
            raise KeoLoi(f"ma khong hop le: {m!r} (chi chu hoa va so)")
        if m2 not in ma:
            ma.append(m2)
    if not ma:
        raise KeoLoi("khong co ma nao de keo")
    for ten, v in (("tu", tu), ("den", den)):
        if not _RE_NGAY.match(str(v)):
            raise KeoLoi(f"{ten} phai la YYYY-MM-DD: {v!r}")
        datetime.date.fromisoformat(v)
    if tu > den:
        raise KeoLoi(f"tu {tu} sau den {den}")
    if nghi_giay < 0:
        raise KeoLoi("nghi_giay am")

    lay = lay or lay_mac_dinh
    bay = (bay_gio or dq.now_vn)()
    if bay.tzinfo is None:
        raise KeoLoi("bay_gio phai co mui gio")
    bay = bay.astimezone(dq.VN_TZ)            # một múi giờ cho `keo_luc` và cho phép kiểm nến dở
    keo_luc = bay.isoformat(timespec="seconds")

    chuoi, nguon, hong = {}, {}, {}
    for i, m in enumerate(ma):
        if i:
            ngu(nghi_giay)
        try:
            kq = lay(m, tu, den)
        except ImportError as e:
            raise KeoLoi(f"khong nhap duoc goi keo gia ({e}); keo that chay tren may "
                         f"co vnstock") from e
        except Exception as e:                                 # noqa: BLE001 — mạng, nguồn
            hong[m] = f"loi khi keo: {type(e).__name__}: {e}"
            continue
        s, v = _chuoi_gia(m, kq, tu, den)
        if s is None:
            hong[m] = v
        else:
            chuoi[m], nguon[m] = s, v

    cuoi = None
    if chuoi:
        cuoi_ma = {m: s.index.max() for m, s in chuoi.items()}
        dem = pd.Series(list(cuoi_ma.values())).value_counts()
        cuoi = max(dem[dem == dem.max()].index)         # nến cuối CHUNG: ngày đa số, hoà thì muộn hơn
        for m, c in cuoi_ma.items():
            if c != cuoi:
                hong[m] = f"nen cuoi {c} khac nen cuoi chung {cuoi}"
    ok = [m for m in ma if m in chuoi and m not in hong]
    # Lịch chung = hợp ngày của các mã CÒN LẠI (mã lệch nến cuối đã bị gọi tên, ngày thừa
    # của nó không được làm cả bảng "thiếu phiên"). Mỗi mã phải có MỌI phiên của lịch ấy.
    gia = pd.DataFrame({m: chuoi[m] for m in ok}).sort_index()
    for m in ok:
        thieu = list(gia.index[gia[m].isna()])
        if thieu:
            hong[m] = (f"thieu {len(thieu)} phien so voi lich chung cua bang: "
                       f"{_gom(thieu)}")
    ket = {"gia": gia, "nguon": nguon, "keo_luc": keo_luc, "hong": hong,
           "cuoi": cuoi, "van_ban": None}
    if hong:
        return ket
    if dq.nen_cuoi_dang_do(cuoi, bay):
        raise KeoLoi(f"nen cuoi {cuoi} co the con DO luc keo ({keo_luc}, truoc gio dong "
                     f"{dq.GIO_NEN_DA_DONG}): keo lai SAU gio dong cua")
    van = cx.dinh_dang_bang_gia(gia, keo_luc, nguon)
    cx.kiem_lich(cx.phan_tich_bang_gia(van)["gia"])      # máy chấm phải nhận thứ này
    ket["van_ban"] = van
    return ket
