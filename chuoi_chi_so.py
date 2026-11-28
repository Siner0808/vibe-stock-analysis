"""Dữ liệu sạch cho ba chuỗi chỉ số VN30 · VNMidcap · VN100 (BƯỚC 307, Dow phần 2 Lát 1, mốc B7).

CHỈ ĐỂ ĐỌC, KHÔNG CHẤM ĐIỂM. Đặc tả: `vibe_logs_dow2/DAC-TA-DOW2.md` mục 2 (dữ liệu) và mục 6 hàng "1"; số đo nguồn:
`vibe_logs_dow2/BAO-CAO.md`. Mô-đun này CHỈ chuẩn bị bảng giá sạch cho `cau_truc_gia` ở chế độ chỉ số
(`la_chi_so=True`); nó KHÔNG nhập `cau_truc_gia` nên không có đường nào từ đây tới đếm swing hay lật (bức tường ĐO 39,
tới khi một lượt chạy chính thức ở Lát 3).

Hợp đồng
────────
THUẦN: không mạng, không đĩa, không đồng hồ. Mạng đi qua `http(url, accept) -> dict` do NGƯỜI GỌI truyền vào (bắt buộc,
không giá trị mặc định); giờ hiện tại do người gọi truyền vào (`bay_gio`). Nguồn và thứ tự thử là
`nguon_gia_cong_khai.CHUOI_CHI_SO` (VNDirect → iBoard → VPS). MỘT chuỗi luôn từ MỘT nguồn: nguồn nào hỏng thì loại CẢ chuỗi
của nguồn ấy rồi thử nguồn kế ("thà thiếu còn hơn sai"), không vá từng nến.

Quy tắc làm sạch (đặc tả §2; mỗi quy tắc một test ở `tests/test_chuoi_chi_so.py`):
  1. thang iBoard ×0,001: `HE_SO_THANG[("iboard", "VNMIDCAP")] = 1000` KÈM cổng độ lớn `kiem_do_lon` — trung vị
     `close` của chuỗi / `close` của chuỗi tham chiếu (VN30) phải nằm trong `DAI_DO_LON` = [0,2 ; 5]; một cổng cho MỌI nguồn,
     nên nếu iBoard sửa thang thì chuỗi bị LOẠI thay vì nhân nhầm;
  2. VPS có ngày trùng và `close` = 0: loại cả chuỗi (đã làm bởi `nguon_gia_cong_khai.dung_khung`), không khử trùng;
  3. tên mã khác nhau theo nguồn: bảng `MA_THEO_NGUON`; không sửa `CHI_SO_HO_TRO` của repo;
  4. `volume` của chỉ số: bảng ra KHÔNG có cột `volume` (phần 1 coi `volume` = 0 là phiên không giao dịch);
  5. (ở `cau_truc_gia`) chế độ `la_chi_so=True`;
  6. chỉ số không điều chỉnh quyền: `HE_SO_GIA` = 1.
Thêm vào đặc tả: lịch căn theo GIAO các ngày (`can_theo_giao`); ngày cuối lệch → đọc tới ngày chung muộn nhất và ghi
"X có thêm n phiên chưa dùng"; nến cuối chưa đóng thì BỎ (`data_quality.nen_cuoi_dang_do`).

Quy tắc dữ liệu BỔ SUNG SAU KHI KÝ ĐO 39 (chỉ đường dự phòng; quyết định của leader 28/11/2026, không phải của người dùng):
nguồn có tỷ lệ nến `high == low == close` > `NGUONG_NEN_MOT_GIA` = 0,5% bị loại cho chuỗi ấy, vì nguồn không trả
high/low thật thì ATR sai. Ngưỡng này chọn SAU KHI thấy dữ liệu (VNDirect 0/2.311 hàng; iBoard VNMidcap 94/1.983 =
4,74%): nó là ngưỡng LÀM SẠCH dữ liệu, không phải ngưỡng đo. Hệ quả: chuỗi VNMidcap thực tế chỉ còn VNDirect (VPS đã bị loại
theo quy tắc 2).

Chưa làm ở Lát này: "chuỗi trễ >= 2 phiên so với lịch" (đặc tả §2, `lich_giao_dich.NGUON_DUNG`) — thuộc ô trên app.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

import pandas as pd

import nguon_gia_cong_khai as ng
from data_quality import nen_cuoi_dang_do

#: Cửa sổ GHIM: ngày sớm nhất mà nguồn sạch dài nhất chung cho cả ba chuỗi có (giới hạn của VNDirect, không phải ngày
#: ra đời của chỉ số). Tới nến đã đóng gần nhất.
TU_NGAY = date(2017, 8, 24)
CHUOI = ("VN30", "VNMidcap", "VN100")
CHUOI_GOC = "VN30"                      # chuỗi tham chiếu của cổng độ lớn; bản thân nó không có tham chiếu
CAC_COT = ("time", "open", "high", "low", "close")      # KHÔNG có `volume` (quy tắc 4)
HE_SO_GIA = 1.0                         # quy tắc 6
TOI_THIEU_PHIEN = 20                    # = nguon_gia_cong_khai.TOI_THIEU_PHIEN

#: Tên mã của từng chuỗi ở từng nguồn (quy tắc 3). Khoá: (chuỗi, tên nguồn của `CHUOI_CHI_SO`).
MA_THEO_NGUON = {
    ("VN30", "vndirect"): "VN30", ("VN30", "iboard"): "VN30", ("VN30", "vps"): "VN30",
    ("VNMidcap", "vndirect"): "VNMID", ("VNMidcap", "iboard"): "VNMIDCAP", ("VNMidcap", "vps"): "VNMID",
    ("VN100", "vndirect"): "VN100", ("VN100", "iboard"): "VN100", ("VN100", "vps"): "VN100",
}
#: Hệ số nhân giá, khoá (tên nguồn, mã trên nguồn) — gõ rõ tên, không suy ra (quy tắc 1). iBoard trả VNMidcap ×0,001.
HE_SO_THANG = {("iboard", "VNMIDCAP"): 1000}
#: Cổng độ lớn (quy tắc 1): trung vị close_A / close_B nằm trong dải đóng này. Rộng cỡ một bậc độ lớn để bắt lỗi THANG,
#: không để tinh chỉnh (VNMID/VN30 trên VNDirect: 0,949–1,572; iBoard×1000/VNDirect: 0,9913–1,0098).
DAI_DO_LON = (0.2, 5.0)
#: Quy tắc bổ sung sau khi ký ĐO 39: tỷ lệ nến high == low == close TỐI ĐA của một nguồn (loại khi VƯỢT). Chọn SAU KHI
#: thấy dữ liệu; là ngưỡng làm sạch, không phải ngưỡng đo.
NGUONG_NEN_MOT_GIA = 0.005
#: Chuỗi bắt đầu muộn hơn `TU_NGAY` quá số ngày lịch này thì gắn nhãn "lịch sử ngắn hơn".
DUNG_SAI_NGAY_DAU = 7
TEN_HIEN = {"vndirect": "VNDirect", "iboard": "iBoard", "vps": "VPS"}


def _pct(x: float) -> str:
    return f"{x * 100:.2f}%".replace(".", ",")


@dataclass(frozen=True, eq=False)
class KetQuaChuoi:
    """Một chuỗi sau làm sạch. `df is None` = không đọc được (`thong_bao()` nói lý do từng nguồn)."""
    chuoi: str
    nguon: str | None                          # tên nguồn đã phục vụ cả chuỗi (khoá trong `TEN_HIEN`)
    ma: str | None                             # mã trên nguồn ấy
    df: pd.DataFrame | None                    # cột `CAC_COT`, ngày tăng ngặt, không `volume`
    da_thu: tuple = ()                         # ((tên nguồn, lý do), ...) các nguồn hỏng trước nó
    he_so_gia: float = HE_SO_GIA
    lich_su_ngan_hon: bool = False
    bo_nen_cuoi_dang_do: bool = False
    ly_do_chung: str = ""                      # lý do khi không thử nguồn nào (thiếu chuỗi tham chiếu)

    def thong_bao(self) -> str:
        if self.df is not None:
            return ""
        if self.ly_do_chung:
            return f"Không đọc được: {self.chuoi} — {self.ly_do_chung}"
        chi_tiet = ", ".join(f"{TEN_HIEN[n] if n in TEN_HIEN else n} ({ly})" for n, ly in self.da_thu)
        return f"Không đọc được: {self.chuoi} — đã thử {chi_tiet}"


@dataclass(frozen=True, eq=False)
class CapDaCan:
    """Hai chuỗi căn theo GIAO các ngày. `thua[tên]` = số phiên của chuỗi ấy nằm SAU ngày chung muộn nhất."""
    chuoi_a: str
    chuoi_b: str
    df_a: pd.DataFrame
    df_b: pd.DataFrame
    so_hang: int
    ngay_cuoi_chung: date
    thua: dict
    ghi_chu: str


def ty_le_nen_mot_gia(df: pd.DataFrame) -> float:
    """Tỷ lệ hàng có high == low == close (nguồn không trả high/low thật cho hàng ấy)."""
    if len(df) == 0:
        return 0.0
    return float(((df["high"] == df["low"]) & (df["low"] == df["close"])).mean())


def _kiem_nen_mot_gia(df: pd.DataFrame) -> str | None:
    ty = ty_le_nen_mot_gia(df)
    if ty > NGUONG_NEN_MOT_GIA:
        return (f"{_pct(ty)} nến có high = low = close, vượt ngưỡng {_pct(NGUONG_NEN_MOT_GIA)} "
                "— nguồn không trả high/low thật")
    return None


def kiem_do_lon(a: pd.Series, b: pd.Series) -> str | None:
    """Cổng độ lớn: trung vị `a / b` trên các ngày chung phải nằm trong `DAI_DO_LON` (đóng cả hai đầu).
    `a`, `b` là chuỗi `close` đánh chỉ số theo ngày. Trả `None` khi qua; không thì trả lý do."""
    chung = a.index.intersection(b.index)
    if len(chung) == 0:
        return "không có ngày chung với chuỗi tham chiếu để kiểm độ lớn"
    ty = float((a.loc[chung] / b.loc[chung]).median())
    thap, cao = DAI_DO_LON
    if thap <= ty <= cao:
        return None
    return f"độ lớn lệch: trung vị close gấp {ty:.4g} lần chuỗi tham chiếu, ngoài dải [{thap} ; {cao}]"


def lay_chuoi(chuoi: str, den: date, bay_gio: datetime, *, http, tham_chieu: pd.Series | None = None,
              ngu=None, nghi: float | None = None, dong_ho=None) -> KetQuaChuoi:
    """Một chuỗi chỉ số sạch, từ nguồn đầu tiên dùng được. `http(url, accept) -> dict` do người gọi truyền vào.

    `tham_chieu` = `close` của chuỗi tham chiếu (đánh chỉ số theo ngày) cho cổng độ lớn; `None` chỉ dành cho chính
    chuỗi gốc `CHUOI_GOC` (không có thứ để so)."""
    if chuoi not in CHUOI:
        raise ValueError(f"chuỗi {chuoi!r} không có trong {CHUOI}")
    da_thu: list[tuple[str, str]] = []
    for nguon in ng.CHUOI_CHI_SO:
        ma = MA_THEO_NGUON[(chuoi, nguon.ten)]
        try:
            kq = ng.lay_ohlcv(ma, TU_NGAY, den, toi_thieu=TOI_THIEU_PHIEN, kiem_them=_kiem_nen_mot_gia,
                              chuoi=(nguon,), nghi=nghi, http=http, ngu=ngu, dong_ho=dong_ho)
        except ng.NguonGiaHetNguon as e:
            da_thu.append((nguon.ten, e.da_thu[0][1]))
            continue
        df = kq.df
        bo_cuoi = bool(len(df)) and nen_cuoi_dang_do(df["time"].iloc[-1], bay_gio)
        if bo_cuoi:
            df = df.iloc[:-1]
        if (nguon.ten, ma) in HE_SO_THANG:
            he = HE_SO_THANG[(nguon.ten, ma)]
            df = df.assign(open=df["open"] * he, high=df["high"] * he, low=df["low"] * he, close=df["close"] * he)
        df = df[list(CAC_COT)].reset_index(drop=True)
        if tham_chieu is not None:
            ly = kiem_do_lon(df.set_index("time")["close"], tham_chieu)
            if ly:
                da_thu.append((nguon.ten, ly))
                continue
        ngan = df["time"].iloc[0].date() > TU_NGAY + timedelta(days=DUNG_SAI_NGAY_DAU)
        return KetQuaChuoi(chuoi=chuoi, nguon=nguon.ten, ma=ma, df=df, da_thu=tuple(da_thu),
                           lich_su_ngan_hon=bool(ngan), bo_nen_cuoi_dang_do=bo_cuoi)
    return KetQuaChuoi(chuoi=chuoi, nguon=None, ma=None, df=None, da_thu=tuple(da_thu))


def lay_ba_chuoi(den: date, bay_gio: datetime, *, http, ngu=None, nghi: float | None = None,
                 dong_ho=None) -> dict[str, KetQuaChuoi]:
    """VN30, VNMidcap, VN100. VN30 đi trước làm chuỗi tham chiếu của cổng độ lớn cho hai chuỗi kia; không đọc được VN30 thì
    hai chuỗi kia cũng không đọc được (không có gì để kiểm thang) — thà thiếu còn hơn sai."""
    kw = dict(http=http, ngu=ngu, nghi=nghi, dong_ho=dong_ho)
    goc = lay_chuoi(CHUOI_GOC, den, bay_gio, **kw)
    kq = {CHUOI_GOC: goc}
    tham_chieu = None if goc.df is None else goc.df.set_index("time")["close"]
    for ten in CHUOI:
        if ten == CHUOI_GOC:
            continue
        if tham_chieu is None:
            kq[ten] = KetQuaChuoi(chuoi=ten, nguon=None, ma=None, df=None,
                                  ly_do_chung=f"không đọc được {CHUOI_GOC}, nên không kiểm được độ lớn")
        else:
            kq[ten] = lay_chuoi(ten, den, bay_gio, tham_chieu=tham_chieu, **kw)
    return {ten: kq[ten] for ten in CHUOI}


def can_theo_giao(a: KetQuaChuoi, b: KetQuaChuoi) -> CapDaCan:
    """Căn hai chuỗi theo GIAO các ngày (không HỢP: hợp để lại lỗ), đọc tới ngày chung muộn nhất."""
    for r in (a, b):
        if r.df is None:
            raise ValueError(f"chuỗi {r.chuoi} không đọc được — không căn")
    chung = pd.Index(a.df["time"]).intersection(pd.Index(b.df["time"]))
    if len(chung) == 0:
        raise ValueError(f"{a.chuoi} và {b.chuoi} không có ngày chung")
    df_a = a.df[a.df["time"].isin(chung)].reset_index(drop=True)
    df_b = b.df[b.df["time"].isin(chung)].reset_index(drop=True)
    cuoi = chung.max()
    thua = {r.chuoi: int((r.df["time"] > cuoi).sum()) for r in (a, b)}
    ghi_chu = "; ".join(f"{ten} có thêm {n} phiên chưa dùng" for ten, n in thua.items() if n)
    return CapDaCan(chuoi_a=a.chuoi, chuoi_b=b.chuoi, df_a=df_a, df_b=df_b, so_hang=len(chung),
                    ngay_cuoi_chung=cuoi.date(), thua=thua, ghi_chu=ghi_chu)


def dong_du_kien(ket_qua: dict[str, KetQuaChuoi]) -> list[str]:
    """Các dòng DỮ KIỆN (không trạng thái): nguồn, mã, số hàng, ngày đầu/cuối, và tỷ số trung vị close của hai chuỗi."""
    dong = []
    for ten in CHUOI:
        r = ket_qua[ten]
        if r.df is None:
            dong.append(r.thong_bao())
            continue
        d = (f"{ten}: nguồn {r.nguon}, mã {r.ma}, {len(r.df)} hàng, {r.df['time'].iloc[0]:%Y-%m-%d} đến "
             f"{r.df['time'].iloc[-1]:%Y-%m-%d}")
        if r.lich_su_ngan_hon:
            d += "; lịch sử ngắn hơn cửa sổ"
        if r.bo_nen_cuoi_dang_do:
            d += "; đã bỏ nến cuối chưa đóng"
        dong.append(d)
    goc = ket_qua[CHUOI_GOC]
    for ten in CHUOI:
        r = ket_qua[ten]
        if ten == CHUOI_GOC or r.df is None or goc.df is None:
            continue
        cap = can_theo_giao(r, goc)
        ty = f"{float((cap.df_a['close'] / cap.df_b['close']).median()):.4f}".replace(".", ",")
        dong.append(f"{ten}/{CHUOI_GOC}: trung vị close {ty} trên {cap.so_hang} ngày chung")
        if cap.ghi_chu:
            dong.append(f"{ten}/{CHUOI_GOC}: {cap.ghi_chu}")
    return dong
