"""Nguồn giá NGÀY công khai, không khoá — đường lấy giá TẠM thay `vnstock` (BƯỚC 267).

Vì sao có file này. `vnstock` 4.x/5.x bị hãng gỡ ngày 10/11/2026 (chỉ mục trả
HTTP 410; bản 4.0.9 đã cài bị cắt giữa lượt quét), còn `vnstock` 6 đòi khoá môi
giới SSI mà người dùng chưa có (BƯỚC 265, đường CHÍNH THỨC sẽ chuyển sang sau).
Trong lúc chờ, đọc thẳng bốn điểm cuối biểu đồ công khai mà trang web của các
công ty chứng khoán tự dùng:

    cổ phiếu : DNSE Entrade -> VNDirect dchart -> VPS
    chỉ số   : VNDirect dchart -> SSI iBoard -> VPS      (VN-Index)

THỨ TỰ DO ĐO, KHÔNG DO ĐOÁN (11/11/2026, 71 mã + VN-Index, cửa sổ quét 22/10/2023 ->
21/10/2026 so với cache 4.0.9 trên đĩa; bảng đầy đủ ở PR và `docs/STATE.md` BƯỚC 267):
SSI iBoard sai giá ở mã UPCoM (ACV · MSR · OIL, cùng VTP · HHP: 481 ngày lệch lợi suất
> 0,5% so với cache, 87 ngày > 2%) và cộng thêm khối lượng thoả thuận ở HNX/UPCoM (SHS: 9,1
triệu cổ phiếu ngày 29/02/2024), nên KHÔNG đứng trong chuỗi cổ phiếu. Entrade khớp cache nhất
nhưng có nến trùng ngày ở lịch sử trước 2023 — với cửa sổ dài nó bị loại LỚN TIẾNG và chuỗi
rơi sang nguồn kế. VPS thiếu 17 ngày-mã và khối lượng khác cache ở 71% số ngày (lệch > 1% ở 0,73%).

LUẬT CỦA MODULE
  1. Một chuỗi giá LUÔN đến từ MỘT nguồn. Không bao giờ vá nửa chuỗi từ nguồn
     này với nửa từ nguồn khác (hai nguồn là hai hệ số điều chỉnh khác nhau —
     `backtest/data.py::fetch_one`). Nguồn đầu hỏng hay không qua kiểm thì bỏ
     CẢ chuỗi và thử nguồn kế; nguồn đã phục vụ được ghi lại và trả ra.
  2. Khung trả về đúng dạng người gọi vẫn nhận từ vnstock 4.0.9: cột
     `time` (datetime64[ns], KHÔNG múi giờ), `open` `high` `low` `close`
     (float64, nghìn đồng với cổ phiếu, điểm với chỉ số), `volume` (int64).
  3. Kiểm lành mạnh và NỔ TO: ngày không tăng ngặt, giá không/âm/NaN, khối
     lượng NaN hay âm, ít hơn `toi_thieu` phiên -> `NguonGiaLoi` cho nguồn đó,
     không bao giờ sửa hay lấp số. Hết nguồn thì `NguonGiaHetNguon` kể từng lý do.
  4. Lịch sự: User-Agent THẬT nêu tên dự án (không bao giờ là chuỗi trình
     duyệt), timeout 30 giây, thử lại 2 lần có lùi, nghỉ giữa hai lần gọi mạng.
  5. Không đọc/ghi đĩa, không đọc khoá, không dùng `vnstock`.

Các điểm cuối là API riêng của web các công ty chứng khoán, không có điều khoản
công bố, có thể đổi hoặc chặn bất cứ lúc nào (TCBS đã gỡ cùng cách đó). Đây là
đường tạm; đường chính thức là BƯỚC 265.

Nến cuối của ngày đang giao dịch được các nguồn trả về như một nến "dở". Module
KHÔNG tự cắt nó — người gọi phải dùng `data_quality.nen_cuoi_dang_do`.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Callable, Iterable

import pandas as pd

#: Tên dự án, không bao giờ là chuỗi trình duyệt. ASCII thuần (tiêu đề HTTP).
USER_AGENT = ("vibe-preview/1.0 (+https://github.com/Siner0808/vibe-stock-analysis; "
              "doc gia ngay cong khai, khong khoa, khong phai trinh duyet)")
TIMEOUT_GIAY = 30
SO_LAN_THU = 3                      # 1 lần đầu + 2 lần thử lại
LUI_GIAY = (2.0, 5.0)               # nghỉ trước lần thử lại thứ 1 và thứ 2
NGHI_GIUA_LAN_GOI_GIAY = 0.3        # tối thiểu giữa hai lần gọi mạng liên tiếp
TOI_THIEU_PHIEN = 20                # = data_quality.SO_PHIEN_TOI_THIEU (test khoá bằng nhau)
GIO_VN = timezone(timedelta(hours=7))

CHI_SO_HO_TRO = ("VNINDEX",)
COT = ("time", "open", "high", "low", "close", "volume")


class NguonGiaLoi(RuntimeError):
    """MỘT nguồn không cho được chuỗi dùng được (mạng, định dạng, kiểm lành mạnh)."""


class NguonGiaHetNguon(NguonGiaLoi):
    """Mọi nguồn trong chuỗi đều hỏng. `da_thu` = [(tên nguồn, lý do)]."""

    def __init__(self, ma: str, da_thu: list[tuple[str, str]]):
        self.ma = ma
        self.da_thu = list(da_thu)
        chi_tiet = " | ".join(f"{t}: {ly}" for t, ly in self.da_thu) or "không có nguồn nào"
        super().__init__(f"không nguồn công khai nào cho được giá {ma} — {chi_tiet}")


@dataclass
class KetQuaGia:
    df: pd.DataFrame
    nguon: str                                   # nguồn ĐÃ phục vụ cả chuỗi
    da_thu: list[tuple[str, str]] = field(default_factory=list)  # nguồn hỏng trước nó


# ──────────────────────────── Định nghĩa nguồn ────────────────────────────

def _cot_tu_dict(j: dict) -> tuple:
    for k in ("t", "o", "h", "l", "c", "v"):
        if k not in j:
            raise NguonGiaLoi(f"phản hồi thiếu mảng '{k}'")
    return tuple(list(j[k]) for k in ("t", "o", "h", "l", "c", "v"))


def _doc_iboard(j: dict) -> tuple:
    if not isinstance(j, dict) or j.get("code") != "SUCCESS":
        raise NguonGiaLoi(f"iBoard trả code={j.get('code') if isinstance(j, dict) else type(j).__name__}")
    return _cot_tu_dict(j.get("data") or {})


def _doc_phang(j: dict) -> tuple:
    """Entrade / VPS / VNDirect: mảng ở gốc; `s` = 'no_data' nghĩa là rỗng."""
    if not isinstance(j, dict):
        raise NguonGiaLoi(f"phản hồi không phải đối tượng ({type(j).__name__})")
    if j.get("s") not in (None, "ok"):
        if j.get("s") == "no_data":
            return [], [], [], [], [], []
        raise NguonGiaLoi(f"s={j.get('s')!r}")
    return _cot_tu_dict(j)


@dataclass(frozen=True)
class Nguon:
    ten: str
    url: Callable[[str, str, int, int], str]     # (loai, ma, tu_ts, den_ts)
    doc: Callable[[dict], tuple]
    accept: str = "*/*"          # VNDirect trả 406 nếu xin 'application/json' (đo 11/11/2026)


def _url_iboard(loai, ma, tu, den):
    return ("https://iboard-api.ssi.com.vn/statistics/charts/history"
            f"?symbol={ma}&resolution=1D&from={tu}&to={den}")


def _url_entrade(loai, ma, tu, den):
    lop = "index" if loai == "chi_so" else "stock"
    return (f"https://services.entrade.com.vn/chart-api/v2/ohlcs/{lop}"
            f"?symbol={ma}&resolution=1D&from={tu}&to={den}")


def _url_vndirect(loai, ma, tu, den):
    return ("https://dchart-api.vndirect.com.vn/dchart/history"
            f"?symbol={ma}&resolution=D&from={tu}&to={den}")


def _url_vps(loai, ma, tu, den):
    return ("https://histdatafeed.vps.com.vn/tradingview/history"
            f"?symbol={ma}&resolution=D&from={tu}&to={den}")


NGUON_IBOARD = Nguon("iboard", _url_iboard, _doc_iboard)
NGUON_ENTRADE = Nguon("entrade", _url_entrade, _doc_phang)
NGUON_VNDIRECT = Nguon("vndirect", _url_vndirect, _doc_phang)
NGUON_VPS = Nguon("vps", _url_vps, _doc_phang)

#: Thứ tự thử (lý do ở docstring đầu file). Chỉ số KHÔNG có Entrade: nguồn ấy thiếu phiên
#: ở chỉ số (1.677 so với 1.711 phiên từ 2020-01-01) và khối lượng chỉ số lệch xa cache.
CHUOI_CO_PHIEU = (NGUON_ENTRADE, NGUON_VNDIRECT, NGUON_VPS)
CHUOI_CHI_SO = (NGUON_VNDIRECT, NGUON_IBOARD, NGUON_VPS)


def loai_ma(ma: str) -> str:
    return "chi_so" if str(ma).upper() in CHI_SO_HO_TRO else "co_phieu"


def chuoi_nguon(ma: str) -> tuple[Nguon, ...]:
    return CHUOI_CHI_SO if loai_ma(ma) == "chi_so" else CHUOI_CO_PHIEU


def ten_cac_nguon(ma: str) -> tuple[str, ...]:
    return tuple(n.ten for n in chuoi_nguon(ma))


def ly_do_khong_co_nguon(cho: str) -> str:
    """Câu "không có nguồn" cho thứ điểm cuối công khai KHÔNG phục vụ được (BƯỚC 267).

    Bảng giá (trần/sàn/tham chiếu), BCTC/chỉ số `ratio`, giao dịch khối ngoại, nến nội phiên:
    chỉ `vnstock` đọc được, mà `vnstock` bị hãng gỡ 10/11/2026 và không còn cài trên
    Cloud/Actions. Người gọi hiện câu này NGUYÊN VĂN và tụt xuống đường lui của nó; không
    bao giờ điền số thay thế (không suy trần từ phần trăm).
    """
    return (f"không có nguồn: {cho} chỉ đọc được từ vnstock, mà vnstock đã bị hãng gỡ "
            f"10/11/2026 — nguồn công khai không khoá chỉ có giá ngày; chờ BƯỚC 265")


def vnstock_vang() -> bool:
    """`vnstock` không nạp được ở đây (không cài, hoặc bị chặn). Không nạp nó."""
    import importlib.util
    try:
        return importlib.util.find_spec("vnstock") is None
    except (ImportError, ValueError):
        return True


# ──────────────────────────── Mạng (thay được khi test) ────────────────────────────

_lan_goi_cuoi = [0.0]


def _http_json(url: str, accept: str = "*/*") -> dict:
    """GET một URL, trả JSON. Lỗi tạm thời (mạng, 429, 5xx) ném `_LoiTam`; lỗi khác `NguonGiaLoi`."""
    import requests                       # bên trong hàm: module nhập được khi chưa có `requests`
    try:
        r = requests.get(url, timeout=TIMEOUT_GIAY,
                         headers={"User-Agent": USER_AGENT, "Accept": accept})
    except requests.exceptions.RequestException as e:
        raise _LoiTam(f"{type(e).__name__}") from e
    if r.status_code == 429 or r.status_code >= 500:
        raise _LoiTam(f"HTTP {r.status_code}")
    if r.status_code != 200:
        raise NguonGiaLoi(f"HTTP {r.status_code}")
    try:
        return r.json()
    except ValueError as e:
        raise NguonGiaLoi("phản hồi không phải JSON") from e


class _LoiTam(NguonGiaLoi):
    """Đáng thử lại."""


def _goi_co_thu_lai(url: str, accept: str, http, ngu, dong_ho,
                    nghi_toi_thieu: float = NGHI_GIUA_LAN_GOI_GIAY) -> dict:
    ly_do = ""
    for lan in range(SO_LAN_THU):
        cho = nghi_toi_thieu - (dong_ho() - _lan_goi_cuoi[0])
        if cho > 0:
            ngu(cho)
        try:
            return http(url, accept)
        except _LoiTam as e:
            ly_do = str(e)
            if lan < SO_LAN_THU - 1:
                ngu(LUI_GIAY[min(lan, len(LUI_GIAY) - 1)])
        finally:
            _lan_goi_cuoi[0] = dong_ho()
    raise NguonGiaLoi(f"{ly_do} sau {SO_LAN_THU} lần thử")


# ──────────────────────────── Dựng khung và kiểm ────────────────────────────

def _ngay(x, ten: str) -> date:
    if isinstance(x, datetime):
        return x.date()
    if isinstance(x, date):
        return x
    try:
        return pd.Timestamp(str(x)[:10]).date()
    except Exception as e:
        raise ValueError(f"{ten} không đọc được: {x!r}") from e


def dung_khung(cot: tuple, tu: date, den: date) -> pd.DataFrame:
    """(t,o,h,l,c,v) thô -> khung đúng dạng vnstock 4.0.9, cắt vào [tu, den].

    Kiểm ở ĐÂY mọi thứ thuộc về dữ liệu thô: độ dài các mảng, ngày tăng NGẶT,
    ô thiếu. Không sửa, không lấp.
    """
    t, o, h, l, c, v = cot
    if not (len(t) == len(o) == len(h) == len(l) == len(c) == len(v)):
        raise NguonGiaLoi("các mảng t/o/h/l/c/v khác độ dài")
    if len(t) == 0:
        raise NguonGiaLoi("0 phiên")
    ts = pd.to_numeric(pd.Series(t), errors="coerce")
    if ts.isna().any():
        raise NguonGiaLoi("có mốc thời gian không đọc được")
    if not (ts.diff().dropna() > 0).all():
        raise NguonGiaLoi("mốc thời gian không tăng ngặt (trùng hoặc đảo thứ tự)")
    # Mọi nguồn đặt mốc trong khoảng 00:00 UTC–09:00 ICT của đúng ngày phiên, nên
    # đổi sang giờ VN rồi cắt về ngày cho ra ngày phiên.
    ngay = (pd.to_datetime(ts.astype("int64"), unit="s") + pd.Timedelta(hours=7)).dt.normalize()
    ngay = ngay.astype("datetime64[ns]")
    if not ngay.is_monotonic_increasing or ngay.duplicated().any():
        raise NguonGiaLoi("hai nến rơi vào cùng một ngày phiên")
    num = {k: pd.to_numeric(pd.Series(x), errors="coerce")
           for k, x in (("open", o), ("high", h), ("low", l), ("close", c), ("volume", v))}
    for k, s in num.items():
        if s.isna().any():
            raise NguonGiaLoi(f"{int(s.isna().sum())} ô '{k}' thiếu")
    for k in ("open", "high", "low", "close"):
        if (num[k] <= 0).any():
            raise NguonGiaLoi(f"{int((num[k] <= 0).sum())} ô '{k}' ≤ 0")
    if (num["volume"] < 0).any():
        raise NguonGiaLoi("khối lượng âm")
    df = pd.DataFrame({
        "time": ngay,
        "open": num["open"].astype("float64"),
        "high": num["high"].astype("float64"),
        "low": num["low"].astype("float64"),
        "close": num["close"].astype("float64"),
        "volume": num["volume"].round().astype("int64"),
    })
    loc = (df["time"] >= pd.Timestamp(tu)) & (df["time"] <= pd.Timestamp(den))
    return df.loc[loc].reset_index(drop=True)


def toi_thieu_mac_dinh(d_tu: date, d_den: date) -> int:
    """Số phiên tối thiểu khi người gọi không nêu: `TOI_THIEU_PHIEN` (20), hoặc NỬA số ngày làm việc
    của cửa sổ nếu cửa sổ ngắn (ô VN-Index ở topbar chỉ xin vài ngày), ít nhất 2 để còn tính được thay đổi.

    Cố ý KHÔNG đòi một TỶ LỆ cho cửa sổ dài: một mã mới niêm yết (VPL: 362 phiên trên cửa sổ 1.095
    ngày) hợp lệ, và nguồn cắt lịch sử đã có `run_daily.bao_cua_so_du_lieu` canh theo VN-Index.
    """
    ngay_lam_viec = len(pd.bdate_range(d_tu, d_den)) if d_den >= d_tu else 0
    return max(2, min(TOI_THIEU_PHIEN, ngay_lam_viec // 2))


def kiem_so_phien(df: pd.DataFrame, toi_thieu: int) -> None:
    if len(df) < toi_thieu:
        raise NguonGiaLoi(f"chỉ {len(df)} phiên < tối thiểu {toi_thieu}")


# ──────────────────────────── Hàm công khai ────────────────────────────

def lay_ohlcv(ma: str, tu, den, *,
              toi_thieu: int | None = None,
              kiem_them: Callable[[pd.DataFrame], str | None] | None = None,
              chuoi: Iterable[Nguon] | None = None,
              nghi: float | None = None,
              http=None, ngu=None, dong_ho=None) -> KetQuaGia:
    """Giá ngày của `ma` (cổ phiếu hoặc VN-Index) từ `tu` tới `den`, cả hai đầu tính.

    `kiem_them(df)` trả chuỗi lý do để BỎ nguồn này và thử nguồn kế (người gọi
    nối `data_quality.validate_ohlcv` vào đây — thà thiếu còn hơn sai). Trả
    `KetQuaGia`; không nguồn nào được thì ném `NguonGiaHetNguon`.
    """
    nghi_toi_thieu = NGHI_GIUA_LAN_GOI_GIAY if nghi is None else float(nghi)
    http = http or _http_json
    ngu = ngu or time.sleep
    dong_ho = dong_ho or time.monotonic
    ma_chuan = str(ma).strip().upper()
    d_tu, d_den = _ngay(tu, "tu"), _ngay(den, "den")
    if toi_thieu is None:
        toi_thieu = toi_thieu_mac_dinh(d_tu, d_den)
    loai = loai_ma(ma_chuan)
    # Xin RỘNG HƠN một ngày ở hai đầu: có nguồn (VPS) bỏ nến đúng mốc `from`.
    # Cắt lại chính xác ở `dung_khung`.
    ts_tu = int(datetime(d_tu.year, d_tu.month, d_tu.day, tzinfo=timezone.utc).timestamp()) - 86400
    ts_den = int(datetime(d_den.year, d_den.month, d_den.day, tzinfo=timezone.utc).timestamp()) + 86400
    da_thu: list[tuple[str, str]] = []
    for ng in (tuple(chuoi) if chuoi is not None else chuoi_nguon(ma_chuan)):
        try:
            j = _goi_co_thu_lai(ng.url(loai, ma_chuan, ts_tu, ts_den), ng.accept,
                                http, ngu, dong_ho, nghi_toi_thieu)
            df = dung_khung(ng.doc(j), d_tu, d_den)
            kiem_so_phien(df, toi_thieu)
            if kiem_them is not None:
                ly = kiem_them(df)
                if ly:
                    raise NguonGiaLoi(ly)
        except NguonGiaLoi as e:
            da_thu.append((ng.ten, str(e)))
            continue
        df.attrs["nguon"] = ng.ten
        return KetQuaGia(df=df, nguon=ng.ten, da_thu=da_thu)
    raise NguonGiaHetNguon(ma_chuan, da_thu)


def lay_khung(ma: str, tu, den, **kw) -> pd.DataFrame:
    """Như `lay_ohlcv` nhưng chỉ trả khung (nguồn nằm ở `df.attrs['nguon']`)."""
    return lay_ohlcv(ma, tu, den, **kw).df
