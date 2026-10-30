"""Sân đấu C1 — bộ PHÁT LẠI thuần (BƯỚC 240, Lát 2 của `docs/thiet-ke-c1-san-dau.md`).

BƯỚC 242 (Lát 3a) thêm: nguồn độ rộng tiêm được cho PB-002 (`NguonDoRong`), cấu hình từ dòng sổ phương án
(`cau_hinh_tu_phuong_an`), chuỗi lợi nhuận mỗi phiên + gác bảo toàn, rổ, và hai thước ở dạng GIÁ TRỊ ĐIỂM
(khoảng tin cậy và độ phủ đến ở BƯỚC 243).

BƯỚC 243 (Lát 3b) thêm: KTC bootstrap khối vòng CÓ CẶP (`ktc_khoi_co_cap`), phép thử độ phủ ở n = 40, 113, 252
(`mo_phong_do_phu`), và nhãn độ phủ (`dinh_dang_ktc`, nơi duy nhất ghép chuỗi KTC danh nghĩa).

Phát lại những QUYẾT ĐỊNH ĐÃ GHI (tab `decisions`) trên một chuỗi giá, bằng bộ máy sổ lệnh THẬT
(`paper_runner.buoc_phien` — CHỖ DUY NHẤT giữ thứ tự bốn bước), trên một `PaperTradingJournal` đặt trong
bộ nhớ. Không nạp mạng, không đĩa, không đồng hồ: dữ liệu đi vào bằng tham số, kết quả đi ra bằng giá trị.
Khuôn B1: module thuần ở gốc repo + dụng cụ I/O cùng tên ở `tools/san_dau.py`.

ĐIỂM LÀ ĐIỂM ĐÃ GHI (quy ước 1 của `cham_bong.py`). Module KHÔNG chấm lại điểm: nó đọc `score`,
`recommendation`, `data_quality`, `components`, `reasons` của dòng quyết định đã giữ. Cái bộ máy cần mà sổ
không ghi — giá vào, cắt lỗ, chốt lời — là hàm THUẦN của giá (ATR); `dung_lai_rui_ro` dựng lại ĐÚNG phần
rủi ro ấy, chỉ bằng agent rủi ro, trên lịch sử cắt tới hết ngày tín hiệu. Việc dựng lại được CHỨNG MINH bằng
phép thử tương đương (`tests/test_san_dau.py`, Tầng A; `tools/san_dau.py tuong-duong`, Tầng B).

Mỗi (mã, ngày) có thể có NHIỀU dòng quyết định (quét nhiều lần một ngày): giữ dòng ghi SAU CÙNG theo
`(at, seq)` (quy ước 2). Thứ tự xử lý các mã trong một phiên là thứ tự `(at, seq)` ấy — trần vốn phụ thuộc
thứ tự mở lệnh trong phiên. Phiên-mã KHÔNG có dòng quyết định chạy ở chế độ chỉ-khớp (khớp vào/ra và lệnh đặt
sẵn, không chấm, không xét vào) và bị ĐẾM; phiên-mã có quyết định mà thiếu nến cũng bị đếm, không đoán.
"""
from __future__ import annotations

import dataclasses
import json
from typing import Any, Callable, Iterable, Optional

import numpy as np
import pandas as pd

#: Cổng mở lệnh mở từ ngày này (`docs/STATE.md` BƯỚC 138; đặc tả mục 4 khoản 7, quyết định 3).
NGAY_MO_CONG = "2026-09-28"

#: Pha tiến-về-trước của sổ bắt đầu ở tín hiệu ≥ ngày này (`tools/doc_so_that.py`, cờ `--moc-tin-hieu`).
NGAY_TIEN_VE_TRUOC = "2026-08-28"

#: Mười hai cột mà phép thử tương đương đòi bằng nhau từng ô (đặc tả mục 6).
COT_TUONG_DUONG = ("symbol", "signal_date", "entry_date", "entry_price", "exit_date", "exit_price",
                   "exit_reason", "stop_loss", "take_profit", "size_pct", "entry_score", "status")

#: Ba cột ngày: so mười ký tự đầu (hậu tố giờ do nguồn đổi, `buoc_phien` cũng cắt về mười ký tự).
_COT_NGAY = ("signal_date", "entry_date", "exit_date")

#: Cột của bảng `trades` mà một vị thế mang sang ghi lại nguyên văn.
_COT_MANG_SANG = ("symbol", "exchange", "signal_date", "entry_date", "entry_price", "exit_date",
                  "exit_price", "exit_reason", "stop_loss", "take_profit", "size_pct", "entry_score",
                  "status")

#: Nhãn dữ liệu (đặc tả mục 4 khoản 7): độc lập với cửa sổ kế toán.
NHAN_MO_PHONG = "MO_PHONG"          # tín hiệu < NGAY_TIEN_VE_TRUOC: lượt mô phỏng lịch sử
NHAN_DA_NHIN = "DA_NHIN"            # NGAY_TIEN_VE_TRUOC ≤ tín hiệu < khai_ngay của phương án
NHAN_CHUA_NHIN = "CHUA_NHIN"        # tín hiệu ≥ khai_ngay của phương án
NHAN_TIEN_VE_TRUOC = "TIEN_VE_TRUOC"  # tài khoản không có khai_ngay (đường thật phát lại, rổ)


def ngay10(x: Any) -> str:
    """Ngày phiên, mười ký tự đầu (nguồn trả `2026-09-25` hay `2026-09-25 00:00:00`)."""
    return str(x)[:10]


def nhan_du_lieu(ngay_tin_hieu: Any, khai_ngay: Optional[str] = None) -> str:
    """Nhãn của một tín hiệu: mô phỏng lịch sử · đã nhìn · chưa nhìn (hay tiến-về-trước thuần khi
    tài khoản không có `khai_ngay`)."""
    n = ngay10(ngay_tin_hieu)
    if n < NGAY_TIEN_VE_TRUOC:
        return NHAN_MO_PHONG
    if khai_ngay is None:
        return NHAN_TIEN_VE_TRUOC
    return NHAN_DA_NHIN if n < ngay10(khai_ngay) else NHAN_CHUA_NHIN


def _thu_tu(dong: dict) -> tuple:
    """`(at, seq)` của một dòng quyết định; thiếu thì xếp TRƯỚC mọi dòng có giá trị."""
    at, seq = dong["at"], dong["seq"]
    return (float("-inf") if at is None else float(at),
            float("-inf") if seq is None else float(seq))


def chon_quyet_dinh(quyet_dinh: Iterable[dict]) -> dict:
    """{(mã, ngày 10 ký tự): (thứ tự `(at, seq)`, dòng)} — mỗi (mã, ngày) giữ dòng ghi SAU CÙNG.

    Cùng cách `cham_bong.doc_quyet_dinh` (quy ước 2): lượt quét sau trong ngày thắng lượt trước.
    """
    giu: dict = {}
    for dong in quyet_dinh:
        khoa = (str(dong["symbol"]), ngay10(dong["signal_date"]))
        tt = _thu_tu(dong)
        cu = giu.get(khoa)
        if cu is None or tt >= cu[0]:
            giu[khoa] = (tt, dong)
    return giu


# ── nguồn thị trường tiêm được ────────────────────────────────────────────────────────────────
class NguonVni:
    """`NguonThiTruong` cho cổng VN-INDEX: CÙNG phép so với `market_filter.is_vni_bullish` — lấy dòng
    cuối có ngày (10 ký tự đầu của `time`) `<=` ngày tín hiệu, đóng cửa ≥ MA50 của chính chuỗi. Cả hai dạng
    cột `time` (cache CSV `2026-09-30`, nguồn mạng `2026-09-30 07:00:00`) đọc CÙNG nến — nguồn thật sửa ở
    BƯỚC 241 (lỗi 195); trước đó nó so chuỗi nguyên và dạng kèm giờ lùi một phiên.

    Khác nguồn thật ở đúng MỘT chỗ, và nó là chỗ cố ý: nguồn thật ném `CacheQuaHanError` khi cache cũ
    hơn ngưỡng và trả "cho qua" khi thiếu; ở đây ngày nào VN-INDEX KHÔNG có nến đúng ngày ấy (thiếu hẳn,
    hay chuỗi dừng trước ngày đó) vẫn trả như nguồn thật nhưng bị GHI VÀO `ngay_thieu` — thiếu dữ liệu
    đầu vào không được phép lặng lẽ thành "không chặn" mà không ai đếm.

    `do_rong` CHƯA có (Lát 3): nổ chứ không trả "không chặn" — đúng cái bẫy của đặc tả mục 4 khoản 4.
    """

    def __init__(self, vni_df: Optional[pd.DataFrame]) -> None:
        from market_filter import MA_WINDOW
        self.ngay_thieu: set = set()
        if vni_df is None or len(vni_df) == 0:
            self._df = None
            return
        df = vni_df.copy()
        df["time"] = df["time"].astype(str).str[:10]
        df = df.sort_values("time").reset_index(drop=True)
        df["vni_ma50"] = df["close"].rolling(MA_WINDOW).mean()
        self._df = df

    def thieu(self, ngay: str) -> bool:
        """VN-INDEX KHÔNG có nến đúng ngày này (thiếu hẳn, ngày trước chuỗi, hay chuỗi dừng trước ngày).
        Không ghi gì — để đếm độ phủ cổng trên MỌI phiên chứ không chỉ phiên bị hỏi."""
        n = ngay10(ngay)
        if self._df is None:
            return True
        return bool((self._df["time"] <= n).sum() == 0 or ngay10(self._df["time"].iloc[-1]) < n)

    def vni_tren_ma50(self, ngay: str) -> bool:
        n = ngay10(ngay)
        if self.thieu(n):
            self.ngay_thieu.add(n)
        if self._df is None:
            return True
        sub = self._df[self._df["time"] <= n]
        if sub.empty:
            return True
        dong = sub.iloc[-1]
        if pd.notna(dong["vni_ma50"]):
            return float(dong["close"]) >= float(dong["vni_ma50"])
        return True

    def do_rong(self, ngay: str) -> Optional[float]:
        raise NotImplementedError("NguonVni không có độ rộng: dùng NguonDoRong (đặc tả mục 4 khoản 4)")


class NguonDoRong:
    """`NguonThiTruong` cho PB-002 (BƯỚC 242, Lát 3a): độ rộng thị trường TIÊM ĐƯỢC.

    `bang_co` — {mã: chuỗi cờ "đóng cửa ≥ MA50 của chính nó"} của `do_rong.co_tren_ma` (bảng của cache 71 mã
    như `do_rong.BangDoRong.bang_co`, hay `co_tu_gia` trên giá đã tải). Độ rộng tại ngày t = `do_rong.do_rong`
    (CÙNG hàm mà đường thật gọi): tỉ lệ mã trên MA50, THIẾU khi N(t) < `do_rong.N_TOI_THIEU`.

    Khác hàm gốc ở hai chỗ, cả hai cố ý (đặc tả mục 4 khoản 4): (1) hàm gốc lấy "dòng cuối có ngày ≤ t" nên
    khi giá dừng trước t nó lặng lẽ dùng độ rộng CŨ; ở đây ngày t mà ít hơn `N_TOI_THIEU` mã còn nến tới t cũng
    là THIẾU. (2) Bộ máy hiểu độ rộng None là "không chặn" — đúng cái bẫy mà đặc tả cấm — nên ngày THIẾU trả
    0,0: mọi ngưỡng > 0 CHẶN, tức PB-002 không mở lệnh nào ở ngày ấy. Ngày thiếu được ghi vào
    `ngay_thieu_rong`; người gọi LOẠI phiên ấy khỏi cửa sổ so sánh của MỌI tài khoản (`phien_thieu`) và
    lệnh có ngày tín hiệu ở đó khỏi mọi tổng. Giá trị 0,0 chỉ là cách để bộ máy chặn, không phải một độ rộng.

    `vni` — nguồn VN-INDEX (`NguonVni`) nếu cấu hình còn cổng VN-INDEX; thiếu mà bị hỏi thì NỔ.
    """
    co_do_rong = True

    def __init__(self, bang_co: dict, vni: Any = None) -> None:
        self.bang_co = bang_co
        self.vni = vni
        self.ngay_thieu_rong: set = set()
        self._cuoi = sorted(co.index[-1] for co in bang_co.values() if len(co))

    def thieu(self, ngay: str) -> bool:
        """True nếu ngày này KHÔNG có độ rộng đáng tin. Không ghi gì."""
        import do_rong as dr
        t = pd.Timestamp(ngay10(ngay))
        con_nen = sum(1 for c in self._cuoi if c >= t)
        return con_nen < dr.N_TOI_THIEU or dr.do_rong(self.bang_co, t) is None

    def do_rong(self, ngay: str) -> Optional[float]:
        import do_rong as dr
        n = ngay10(ngay)
        if self.thieu(n):
            self.ngay_thieu_rong.add(n)
            return 0.0
        return dr.do_rong(self.bang_co, pd.Timestamp(n))

    def vni_tren_ma50(self, ngay: str) -> bool:
        if self.vni is None:
            raise RuntimeError("cổng VN-INDEX bật mà nguồn độ rộng không có nguồn VN-INDEX")
        return self.vni.vni_tren_ma50(ngay)

    def phien_thieu(self, phien: Iterable[str]) -> list[str]:
        """Các phiên của `phien` mà độ rộng THIẾU — những phiên bị loại khỏi cửa sổ thống kê."""
        return [d for d in phien if self.thieu(d)]


def co_tu_gia(gia: dict) -> dict:
    """{mã: chuỗi cờ "trên MA50"} dựng từ khung giá đã tải (khi không có thư mục cache để đọc). Cùng cách
    `do_rong.gia_dong_cua` đọc một tệp: ngày 10 ký tự, bỏ dòng trùng, sắp theo ngày; VNINDEX không vào."""
    import do_rong as dr
    ra: dict = {}
    for ma, df in gia.items():
        if df is None or len(df) == 0 or ma == dr.MA_CHI_SO:
            continue
        d = df[["time", "close"]].dropna().copy()
        d["time"] = pd.to_datetime(d["time"].astype(str).str[:10])
        ra[ma] = dr.co_tren_ma(d.drop_duplicates("time").sort_values("time").set_index("time")["close"])
    return ra


def cau_hinh_tu_phuong_an(co_so: Any, phuong_an: dict) -> Any:
    """`CauHinhVao` của một phương án bóng = cấu hình đường thật `co_so` ghi đè bởi `bo_co` của dòng sổ.
    Dòng sổ không hợp lệ (khoá lạ, sai kiểu, cờ chưa có nguồn tiêm) thì NỔ."""
    import phuong_an_bong as pab
    loi = pab.vi_pham_bo_co(phuong_an.get("bo_co"))
    if loi:
        raise ValueError("; ".join(loi))
    return dataclasses.replace(co_so, **phuong_an["bo_co"])


# ── dựng lại phần rủi ro từ giá ───────────────────────────────────────────────────────────────
def dung_lai_rui_ro(ma: str, lich_su: pd.DataFrame) -> dict:
    """`recommendations` của agent rủi ro trên lịch sử cắt tới hết ngày tín hiệu: giá vào, cắt lỗ,
    chốt lời — hàm thuần của giá. Cùng `DataOrchestrator._compute_local_indicators` và cùng
    `RiskManagementAgent` mà đường chấm điểm thật dùng; không agent nào khác được dựng."""
    from analysis_agents import RiskManagementAgent
    from data_collectors import DataOrchestrator, MarketDataPacket

    goi = MarketDataPacket(symbol=ma, exchange="HOSE", ohlcv_df=lich_su.reset_index(drop=True))
    if len(goi.ohlcv_df) >= 20:
        cuc_bo = DataOrchestrator(ma, "", "")._compute_local_indicators(goi.ohlcv_df)
        goi.tv_indicators.update({k: v for k, v in cuc_bo.items() if v is not None})
    return RiskManagementAgent().analyze(goi)["recommendations"]


def _json_danh_sach(van: Any) -> list:
    return json.loads(van) if van else []


def _json_tu_dien(van: Any) -> dict:
    return json.loads(van) if van else {}


def ket_qua_tu_dong(dong: dict, ma: str, lich_su: pd.DataFrame, nguong_mua: float) -> dict:
    """`result` mà `consider_entry` / `evaluate_open` đọc, dựng từ dòng quyết định ĐÃ GHI + phần rủi ro
    dựng lại. KHÔNG chấm điểm: `final_score` là cột `score`.

    Phần rủi ro CHỈ được dựng khi `score >= nguong_mua`: dưới ngưỡng, `consider_entry` bỏ lệnh ở cổng điểm
    TRƯỚC khi đọc `analyses` (và `evaluate_open` không đọc nó), nên dựng lại chỉ tốn ~8 ms một lần mà không
    đổi gì. Giả định ấy về thứ tự cổng được CANH bởi phép thử tương đương (`tests/test_san_dau.py`): đổi
    thứ tự thì lệnh phát lại khác lệnh thật."""
    rui_ro = dung_lai_rui_ro(ma, lich_su) if dong["score"] >= nguong_mua else None
    return {"final_score": dong["score"], "recommendation": dong["recommendation"],
            "data_quality": dong["data_quality"],
            "score_breakdown": _json_tu_dien(dong["components"]),
            "key_reasons": _json_danh_sach(dong["reasons"]),
            "analyses": {} if rui_ro is None else {"risk": {"recommendations": rui_ro}}}


# ── tài khoản ─────────────────────────────────────────────────────────────────────────────────
@dataclasses.dataclass
class TaiKhoan:
    """Một tài khoản ảo: một sổ trong bộ nhớ + các số đếm của lượt phát lại.

    `dem` — `phien` số phiên đã chạy · `buoc` số phiên-mã đã chạy qua `buoc_phien` · `thieu_diem` số
    phiên-mã CÓ nến mà KHÔNG có dòng quyết định (chạy chỉ-khớp) · `thieu_nen` số phiên-mã CÓ quyết định
    mà KHÔNG có nến (bỏ qua) · `quyet_dinh_ngoai_cua_so` số (mã, ngày) có quyết định nằm ngoài cửa sổ
    phát lại · `mang_sang` số vị thế chép từ sổ thật lúc bắt đầu.
    """
    nhat_ky: Any
    ngay_bat_dau: str
    ngay_ket_thuc: str
    dem: dict
    #: Từng phiên-mã bị đếm vào `dem["thieu_diem"]` / `dem["thieu_nen"]`, dạng `(mã, ngày)`.
    ds_thieu_diem: list = dataclasses.field(default_factory=list)
    ds_thieu_nen: list = dataclasses.field(default_factory=list)

    def lenh(self) -> list[dict]:
        """Bảng `trades` của tài khoản (mười hai cột `COT_TUONG_DUONG`), theo thứ tự `id`."""
        cot = ", ".join(COT_TUONG_DUONG)
        return [dict(r) for r in self.nhat_ky.db.execute(
            f"SELECT {cot} FROM trades ORDER BY id").fetchall()]

    def dong(self) -> None:
        self.nhat_ky.db.close()


def _kiem_cau_hinh_ho_tro(cau_hinh: Any, nguon: Any = None) -> None:
    """Từ chối cấu hình mà CHƯA có đầu vào cho: phát lại lặng lẽ bỏ qua là phát lại sai. Cổng độ rộng chỉ
    chạy được khi `nguon` tự khai có độ rộng (`co_do_rong`, như `NguonDoRong`)."""
    import paper_trading as pt
    if cau_hinh.luat_vao != "MO_CUA_SAU":
        raise NotImplementedError(f"luat_vao={cau_hinh.luat_vao!r}: chưa có — Lát 4 của C1")
    if cau_hinh.do_rong_nguong > 0 and not getattr(nguon, "co_do_rong", False):
        raise NotImplementedError("cổng độ rộng: nguồn không có độ rộng (cần NguonDoRong)")
    if cau_hinh.loc_imom_phan_vi > 0 or cau_hinh.chot_sut_giam_nguong > 0:
        raise ValueError("IMOM và chốt sụt giảm chưa tiêm được (đặc tả mục 5 khoản 4): "
                         "phát lại sẽ đọc cache toàn cục")
    if pt.DUNG_MUC_FIBONACCI:
        raise ValueError("DUNG_MUC_FIBONACCI đang bật: phần rủi ro không còn là hàm của ATR để dựng lại")


def _san_mac_dinh(ma: str) -> str:
    from san_giao_dich import san_cua
    return san_cua(ma)


def _chuan_hoa_gia(gia: dict) -> dict:
    """{mã: (khung giá sắp theo thời gian, danh sách ngày 10 ký tự, {ngày: vị trí})}."""
    ra: dict = {}
    for ma, df in gia.items():
        if df is None or len(df) == 0:
            continue
        khung = df.reset_index(drop=True)
        ngay = [ngay10(t) for t in khung["time"]]
        if any(a >= b for a, b in zip(ngay, ngay[1:])):
            raise ValueError(f"{ma}: chuỗi giá phải tăng nghiêm ngặt theo ngày")
        ra[ma] = (khung, ngay, {n: i for i, n in enumerate(ngay)})
    return ra


def _gieo_mang_sang(nhat_ky: Any, vi_the: Iterable[dict], san_cua: Callable[[str], str]) -> int:
    """Chép các vị thế mang sang vào sổ nguyên văn (id mới, các cột của `_COT_MANG_SANG`)."""
    n = 0
    for v in vi_the:
        dong = {c: v[c] for c in _COT_MANG_SANG if c in v}
        if dong.get("exchange") is None:
            dong["exchange"] = san_cua(dong["symbol"])
        cot = list(dong)
        nhat_ky.db.execute(
            f"INSERT INTO trades ({', '.join(cot)}) VALUES ({','.join('?' * len(cot))})",
            [dong[c] for c in cot])
        n += 1
    nhat_ky.db.commit()
    return n


def phat_lai(cau_hinh: Any, quyet_dinh: Iterable[dict], gia: dict, nguon: Any, *,
             san_cua: Optional[Callable[[str], str]] = None,
             ngay_bat_dau: Optional[str] = None, ngay_ket_thuc: Optional[str] = None,
             vi_the_mang_sang: Iterable[dict] = ()) -> TaiKhoan:
    """Phát lại `quyet_dinh` đã ghi trên `gia` với `cau_hinh`, qua `paper_runner.buoc_phien`.

    `gia` — {mã: khung OHLCV theo đơn vị của nguồn (nghìn đồng cũng được), cột `time` tăng dần}.
    `nguon` — `NguonThiTruong` cho cổng VN-INDEX (`NguonVni`). Cửa sổ là các phiên có nến trong
    `[ngay_bat_dau, ngay_ket_thuc]` (mặc định: phiên đầu và cuối của `gia`). Trả `TaiKhoan` (sổ còn mở,
    gọi `.dong()` khi xong).

    Mỗi phiên, mỗi mã có quyết định: MỘT lần `buoc_phien` theo thứ tự `(at, seq)`; mỗi mã có nến mà không
    có quyết định: một lần chỉ-khớp, sau các mã có quyết định, theo tên mã.
    """
    from paper_runner import buoc_phien
    from paper_trading import PaperTradingJournal

    _kiem_cau_hinh_ho_tro(cau_hinh, nguon)
    if nguon is None and cau_hinh.cong_vni_bat:
        raise ValueError("cổng VN-INDEX bật mà không có nguồn: bộ máy sẽ đọc cache toàn cục")
    san_cua = san_cua if san_cua is not None else _san_mac_dinh
    khung = _chuan_hoa_gia(gia)
    giu = chon_quyet_dinh(quyet_dinh)

    lich = sorted({n for _, ngay, _ in khung.values() for n in ngay})
    if not lich:
        raise ValueError("không có nến nào để phát lại")
    bat_dau = ngay10(ngay_bat_dau) if ngay_bat_dau is not None else lich[0]
    ket_thuc = ngay10(ngay_ket_thuc) if ngay_ket_thuc is not None else lich[-1]
    phien = [n for n in lich if bat_dau <= n <= ket_thuc]

    trong_cua_so = {k for k in giu if bat_dau <= k[1] <= ket_thuc}
    ma_co_diem = sorted({ma for ma, _ in trong_cua_so})

    nhat_ky = PaperTradingJournal(":memory:")
    dem = {"phien": 0, "buoc": 0, "thieu_diem": 0, "thieu_nen": 0,
           "quyet_dinh_ngoai_cua_so": len(giu) - len(trong_cua_so), "mang_sang": 0}
    dem["mang_sang"] = _gieo_mang_sang(nhat_ky, vi_the_mang_sang, san_cua)
    ds_thieu_diem: list = []
    ds_thieu_nen: list = []

    for d in phien:
        dem["phien"] += 1
        co_diem = sorted((giu[(ma, d)][0], ma) for ma in ma_co_diem if (ma, d) in giu)
        khong_diem = [ma for ma in ma_co_diem if (ma, d) not in giu]
        for ma in [m for _, m in co_diem] + khong_diem:
            dong_qd = giu[(ma, d)][1] if (ma, d) in giu else None
            moc = khung.get(ma)
            if moc is None or d not in moc[2]:
                if dong_qd is not None:
                    dem["thieu_nen"] += 1
                    ds_thieu_nen.append((ma, d))
                continue
            df, _, vi_tri = moc
            lich_su = df.iloc[: vi_tri[d] + 1]
            nen = {c: float(df[c].iloc[vi_tri[d]]) for c in ("open", "high", "low", "close", "volume")}
            if dong_qd is None:
                dem["thieu_diem"] += 1
                ds_thieu_diem.append((ma, d))
            dem["buoc"] += 1
            buoc_phien(nhat_ky, ma, lich_su, nen, d, san_cua(ma), cau_hinh,
                       (lambda m=ma, q=dong_qd, h=lich_su: ket_qua_tu_dong(q, m, h,
                                                                           cau_hinh.buy_threshold)),
                       chi_khop=dong_qd is None, nguon=nguon)
    return TaiKhoan(nhat_ky=nhat_ky, ngay_bat_dau=bat_dau, ngay_ket_thuc=ket_thuc, dem=dem,
                    ds_thieu_diem=ds_thieu_diem, ds_thieu_nen=ds_thieu_nen)


# ── vị thế mang sang NGAY_MO_CONG ─────────────────────────────────────────────────────────────
def vi_the_mang_sang(lenh: Iterable[dict], ngay: str = NGAY_MO_CONG) -> list[dict]:
    """Các lệnh của sổ thật còn SỐNG ở đầu phiên `ngay`: tín hiệu trước `ngay` và chưa kết thúc (đóng hay
    huỷ) trước `ngay`. Trả mỗi lệnh ở TRẠNG THÁI ĐẦU PHIÊN — chưa khớp trước `ngay` thì PENDING, không có
    giá vào/ra; đã khớp thì OPEN, không có giá ra — với các cột còn lại chép NGUYÊN VĂN từ sổ.

    GIỚI HẠN KHAI THẲNG: sổ thật chỉ giữ trạng thái CUỐI. `stop_loss` (nâng dần theo trailing) và `size_pct`
    (chỉnh theo lô chẵn lúc khớp) là giá trị lúc lệnh KẾT THÚC, không phải lúc `ngay`; một lệnh đang chờ
    thoát (CLOSING) ở đầu phiên cũng chỉ còn trạng thái cuối. Bộ phát lại chép chúng đúng như thế.
    """
    n = ngay10(ngay)
    ra = []
    for t in lenh:
        if ngay10(t["signal_date"]) >= n:
            continue
        xong = t["status"] in ("CLOSED", "HUY") and t["exit_date"] and ngay10(t["exit_date"]) < n
        if xong:
            continue
        da_khop = bool(t["entry_date"]) and ngay10(t["entry_date"]) < n
        moi = {c: t[c] for c in _COT_MANG_SANG if c in t}
        moi.update(exit_date=None, exit_price=None, exit_reason=None,
                   status="OPEN" if da_khop else "PENDING")
        if not da_khop:
            moi.update(entry_date=None, entry_price=None)
        ra.append(moi)
    return ra


# ── phép thử tương đương ──────────────────────────────────────────────────────────────────────
def _chuan_o(cot: str, v: Any) -> Any:
    if cot in _COT_NGAY and v is not None:
        return ngay10(v)
    return v


def so_sanh_lenh(thuc: Iterable[dict], phat_lai_: Iterable[dict],
                 cot: Iterable[str] = COT_TUONG_DUONG) -> list[dict]:
    """Mọi khác biệt giữa hai bảng lệnh, khoá bằng `(mã, ngày tín hiệu)`; rỗng nghĩa là bằng nhau TỪNG Ô.

    Không có dung sai: số so bằng `==`; ba cột ngày so mười ký tự đầu (hậu tố giờ là định dạng của nguồn,
    không phải luật). Mỗi khác biệt là một dict: `loai` ∈ {`chi_co_o_thuc`, `chi_co_o_phat_lai`,
    `khac_o`, `lenh_trung_khoa`}, `khoa`, và với `khac_o` thêm `cot`, `thuc`, `phat_lai`.
    """
    cot = tuple(cot)

    def gom(bang: Iterable[dict]) -> tuple[dict, list]:
        theo: dict = {}
        trung = []
        for r in bang:
            k = (str(r["symbol"]), ngay10(r["signal_date"]))
            if k in theo:
                trung.append(k)
            theo[k] = r
        return theo, trung

    a, trung_a = gom(thuc)
    b, trung_b = gom(phat_lai_)
    khac = [{"loai": "lenh_trung_khoa", "khoa": k} for k in sorted(set(trung_a) | set(trung_b))]
    for k in sorted(set(a) - set(b)):
        khac.append({"loai": "chi_co_o_thuc", "khoa": k})
    for k in sorted(set(b) - set(a)):
        khac.append({"loai": "chi_co_o_phat_lai", "khoa": k})
    for k in sorted(set(a) & set(b)):
        for c in cot:
            x, y = _chuan_o(c, a[k][c]), _chuan_o(c, b[k][c])
            if x != y:
                khac.append({"loai": "khac_o", "khoa": k, "cot": c, "thuc": x, "phat_lai": y})
    return khac


# ── chuỗi lợi nhuận mỗi phiên, rổ, bảo toàn, hai thước (BƯỚC 242, Lát 3a; đặc tả mục 8) ─────────
#: Trạng thái lệnh có đóng góp vào đường vốn: đã khớp vào. CLOSING (chờ khớp ra) vẫn đang giữ.
TRANG_THAI_CO_DONG_GOP = ("OPEN", "CLOSING", "CLOSED")

#: Dưới ngưỡng này một mức cam kết coi như 0 ("phiên không giữ").
_E_KHONG = 1e-12


def phien_cua_so(gia: dict, bat_dau: str, ket_thuc: str) -> list[str]:
    """Các phiên có nến (của BẤT KỲ mã nào) trong `[bat_dau, ket_thuc]` — đúng tập mà `phat_lai` chạy."""
    khung = _chuan_hoa_gia(gia)
    lich = sorted({n for _, ngay, _ in khung.values() for n in ngay})
    return [n for n in lich if ngay10(bat_dau) <= n <= ngay10(ket_thuc)]


def _dong_cua_vnd(moc: tuple) -> tuple[list[str], list[float]]:
    """(ngày, đóng cửa quy về VNĐ) của một mã — cùng hệ số đơn vị mà bộ máy dùng khi ghi giá vào sổ."""
    from data_quality import price_multiplier
    khung, ngay, _ = moc
    he_so = price_multiplier(khung)
    return ngay, [float(c) * he_so for c in khung["close"]]


def dong_gop_lenh(lenh: dict, moc: tuple, bat_dau: str, ket_thuc: str) -> dict[str, float]:
    """Đóng góp của MỘT lệnh vào đường vốn, theo phiên: {ngày: điểm phần trăm vốn}.

    Lệnh giữ SỐ CỔ PHIẾU cố định (không tái đầu tư: `size_pct` là phần trăm vốn ban đầu, vào ở giá
    `entry_price`), nên lãi lỗ một phiên là `w × Δgiá / entry_price`:
      - phiên khớp vào: từ giá vào tới đóng cửa · phiên giữ: đóng cửa trước → đóng cửa · phiên khớp ra:
        từ đóng cửa trước tới giá ra · cả ba cộng lại THU GỌN (telescoping) về `w × (ra − vào) / vào`;
      - phí khứ hồi `paper_metrics.ROUND_TRIP_COST_PCT` trừ ở phiên khớp ra (`w` × phí).
    Chỉ các phiên trong `[bat_dau, ket_thuc]` được trả. Lệnh chưa khớp, đã huỷ: rỗng.

    LỆCH ĐẶC TẢ, khai thẳng: mục 8.1 viết `w × (đóng cửa_t / đóng cửa_{t-1} − 1)` và đồng thời đòi
    tổng qua các phiên = `w × net_return_pct`. Hai thứ ấy KHÔNG đi cùng nhau (tổng các lợi nhuận đơn mỗi
    phiên khác lợi nhuận đơn cả kỳ: +10% rồi −10% cộng 0, nhân −1%). Giữ gác bảo toàn thì phải chia cho
    GIÁ VÀO, không cho đóng cửa hôm trước — và đó cũng là lãi lỗ thật của một lệnh giữ số cổ phiếu cố định.
    """
    from paper_metrics import ROUND_TRIP_COST_PCT

    if lenh["status"] not in TRANG_THAI_CO_DONG_GOP or not lenh["entry_date"] or lenh["entry_price"] is None:
        return {}
    ngay, dong = _dong_cua_vnd(moc)
    vao_gia = float(lenh["entry_price"])
    w = float(lenh["size_pct"]) / 100.0
    vao = ngay10(lenh["entry_date"])
    ra = ngay10(lenh["exit_date"]) if lenh["status"] == "CLOSED" and lenh["exit_date"] else None
    bd, kt = ngay10(bat_dau), ngay10(ket_thuc)
    out: dict[str, float] = {}
    for i, d in enumerate(ngay):
        if d < vao:
            continue
        if d > kt or (ra is not None and d > ra):
            break
        if d == vao:
            dau = vao_gia
        elif i == 0:
            continue
        else:
            dau = dong[i - 1]
        cuoi = float(lenh["exit_price"]) if d == ra else dong[i]
        v = w * (cuoi - dau) / vao_gia * 100.0
        if d == ra:
            v -= w * ROUND_TRIP_COST_PCT
        if d >= bd:
            out[d] = v
    return out


@dataclasses.dataclass
class ChuoiTaiKhoan:
    """Chuỗi đo của một tài khoản trên một cửa sổ: `r` {ngày: điểm phần trăm vốn} · `e` {ngày: tỷ lệ vốn
    cam kết, tức tổng `size_pct/100` của các lệnh có đóng góp ở phiên ấy} · `thieu_gia` các lệnh không có
    chuỗi giá (bị bỏ khỏi chuỗi)."""
    r: dict
    e: dict
    thieu_gia: list = dataclasses.field(default_factory=list)


def chuoi_tai_khoan(lenh: Iterable[dict], gia: dict, phien: list[str], *,
                    loc: Optional[Callable[[dict], bool]] = None) -> ChuoiTaiKhoan:
    """Chuỗi `r`, `e` của một tài khoản trên `phien` (đã sắp). `loc` chọn một phần các lệnh (nhãn dữ liệu)."""
    khung = _chuan_hoa_gia(gia)
    r = {d: 0.0 for d in phien}
    e = {d: 0.0 for d in phien}
    thieu: list = []
    if not phien:
        return ChuoiTaiKhoan(r, e, thieu)
    for t in lenh:
        if loc is not None and not loc(t):
            continue
        if t["status"] not in TRANG_THAI_CO_DONG_GOP or not t["entry_date"]:
            continue
        moc = khung.get(str(t["symbol"]))
        if moc is None:
            thieu.append((t["symbol"], ngay10(t["signal_date"])))
            continue
        for d, v in dong_gop_lenh(t, moc, phien[0], phien[-1]).items():
            if d in r:
                r[d] += v
                e[d] += float(t["size_pct"]) / 100.0
    return ChuoiTaiKhoan(r, e, thieu)


def loi_nhuan_ro(gia: dict, phien: list[str]) -> tuple[dict, list[str]]:
    """Rổ ĐỀU trọng số theo phiên (đặc tả mục 8.1): lợi nhuận một phiên = trung bình lợi nhuận một phiên
    (điểm phần trăm) của các mã đủ nến hai phiên LIỀN (phiên trước = phiên trước trong lịch chung của `gia`).
    Cùng phép tính với `paper_runner.build_benchmark` áp cho khoá (phiên trước, phiên) — test đối chiếu.
    Rổ luôn đầu tư 100% và KHÔNG trả phí (không đảo danh mục). Trả ({ngày: lợi nhuận}, phiên không dựng được)."""
    khung = _chuan_hoa_gia(gia)
    lich = sorted({n for _, ngay, _ in khung.values() for n in ngay})
    vi_tri = {d: i for i, d in enumerate(lich)}
    dong = {ma: {d: float(c) for d, c in zip(ngay, kh["close"])} for ma, (kh, ngay, _) in khung.items()}
    ro: dict = {}
    thieu: list = []
    for d in phien:
        i = vi_tri.get(d)
        if i is None or i == 0:
            thieu.append(d)
            continue
        truoc = lich[i - 1]
        loi = [(c[d] - c[truoc]) / c[truoc] * 100.0 for c in dong.values()
               if d in c and truoc in c and c[truoc] > 0]
        if not loi:
            thieu.append(d)
            continue
        ro[d] = sum(loi) / len(loi)
    return ro, thieu


def kiem_bao_toan(lenh: Iterable[dict], gia: dict, bat_dau: str, ket_thuc: str, *,
                  dung_sai: float = 1e-8) -> dict:
    """GÁC BẢO TOÀN (đặc tả mục 8.1): với MỖI lệnh đã khớp vào, tổng đóng góp qua các phiên của cửa sổ
    phải bằng đại lượng viết theo CÔNG THỨC ĐÓNG (đầu mút), không qua vòng lặp từng phiên:
        w × (giá cuối − giá đầu) / giá vào  −  w × phí (nếu ra trong cửa sổ)
    với giá đầu = giá vào (vào trong cửa sổ) hay đóng cửa phiên cuối TRƯỚC cửa sổ; giá cuối = giá ra (ra trong
    cửa sổ) hay đóng cửa phiên cuối của cửa sổ. Lệnh ĐÃ ĐÓNG nằm trọn trong cửa sổ còn phải bằng
    `size_pct/100 × Trade.net_return_pct()` — công thức lợi nhuận ròng của chính sổ lệnh. Trả
    {`da_kiem`, `dong_trong_cua_so`, `vi_pham`: [{lenh, thuc, ky_vong, loai}]}."""
    from paper_metrics import ROUND_TRIP_COST_PCT
    from paper_trading import Trade

    khung = _chuan_hoa_gia(gia)
    bd, kt = ngay10(bat_dau), ngay10(ket_thuc)
    vi_pham: list = []
    da_kiem = dong_trong = 0
    for t in lenh:
        if t["status"] not in TRANG_THAI_CO_DONG_GOP or not t["entry_date"] or t["entry_price"] is None:
            continue
        khoa = (t["symbol"], ngay10(t["signal_date"]))
        moc = khung.get(str(t["symbol"]))
        if moc is None:
            vi_pham.append({"lenh": khoa, "loai": "thieu_gia", "thuc": None, "ky_vong": None})
            continue
        ngay, dong = _dong_cua_vnd(moc)
        gia_ngay = dict(zip(ngay, dong))
        w = float(t["size_pct"]) / 100.0
        vao = ngay10(t["entry_date"])
        ra = ngay10(t["exit_date"]) if t["status"] == "CLOSED" and t["exit_date"] else None
        thuc = sum(dong_gop_lenh(t, moc, bd, kt).values())
        da_kiem += 1
        if (ra is not None and ra < bd) or vao > kt:
            ky_vong = 0.0
        else:
            truoc = [d for d in ngay if d < bd]
            sau = [d for d in ngay if d <= kt]
            if vao < bd and not truoc:
                vi_pham.append({"lenh": khoa, "loai": "thieu_gia_dau", "thuc": thuc, "ky_vong": None})
                continue
            dau = float(t["entry_price"]) if vao >= bd else gia_ngay[truoc[-1]]
            ra_trong = ra is not None and ra <= kt
            cuoi = float(t["exit_price"]) if ra_trong else gia_ngay[sau[-1]]
            ky_vong = w * (cuoi - dau) / float(t["entry_price"]) * 100.0
            if ra_trong:
                ky_vong -= w * ROUND_TRIP_COST_PCT
        if abs(thuc - ky_vong) > dung_sai * (1.0 + abs(ky_vong)):
            vi_pham.append({"lenh": khoa, "loai": "dong", "thuc": thuc, "ky_vong": ky_vong})
        if t["status"] == "CLOSED" and ra is not None and vao >= bd and ra <= kt:
            dong_trong += 1
            sach = Trade(id=0, symbol=t["symbol"], signal_date=t["signal_date"], entry_date=t["entry_date"],
                         entry_price=t["entry_price"], exit_date=t["exit_date"], exit_price=t["exit_price"],
                         exit_reason=t["exit_reason"], stop_loss=t["stop_loss"], take_profit=t["take_profit"],
                         size_pct=t["size_pct"], entry_score=t["entry_score"], status=t["status"])
            tu_so = w * sach.net_return_pct()
            if abs(thuc - tu_so) > dung_sai * (1.0 + abs(tu_so)):
                vi_pham.append({"lenh": khoa, "loai": "net_return_pct", "thuc": thuc, "ky_vong": tu_so})
    return {"da_kiem": da_kiem, "dong_trong_cua_so": dong_trong, "vi_pham": vi_pham}


def _trung_binh(xs: list) -> Optional[float]:
    return sum(xs) / len(xs) if xs else None


def thuoc_1(r: dict, e: dict, ro: dict, phien: list[str]) -> dict:
    """THƯỚC 1 (đặc tả mục 8.2), GIÁ TRỊ ĐIỂM: `x_t = r_t − e_t × rổ_t`, `e_t` = tổng `size_pct/100` đang
    cam kết ở phiên t. Cột thô `r_t − rổ_t` in CẠNH, không thay. Trung bình `x` tính trên các phiên CÓ GIỮ
    (`e_t > 0`); phiên không giữ cho `x_t = 0`, được ĐẾM riêng và không làm tăng n. Cộng dồn = tổng trên cửa
    sổ. Thô: trung bình và cộng dồn trên MỌI phiên của cửa sổ (tiền mặt nằm ngoài là một phần của nó)."""
    ds = [d for d in phien if d in ro]
    x = {d: r[d] - e[d] * ro[d] for d in ds}
    tho = {d: r[d] - ro[d] for d in ds}
    giu = [d for d in ds if e[d] > _E_KHONG]
    return {"n_phien": len(ds), "n_giu": len(giu), "n_khong_giu": len(ds) - len(giu),
            "x_tb_giu": _trung_binh([x[d] for d in giu]), "x_cong_don": sum(x.values()),
            "tho_tb": _trung_binh(list(tho.values())), "tho_cong_don": sum(tho.values()),
            "x_chuoi": [x[d] for d in ds], "tho_chuoi": [tho[d] for d in ds]}


def thuoc_2(r_pa: dict, r_that: dict, phien: list[str]) -> dict:
    """THƯỚC 2 (đặc tả mục 8.2), GIÁ TRỊ ĐIỂM: `d_t = r_t(phương án) − r_t(đường thật phát lại)` trên
    các phiên của cửa sổ CHUNG `phien`."""
    ds = [d for d in phien if d in r_pa and d in r_that]
    d_t = [r_pa[d] - r_that[d] for d in ds]
    return {"n_phien": len(ds), "tb": _trung_binh(d_t), "cong_don": sum(d_t),
            "a_chuoi": [r_pa[d] for d in ds], "b_chuoi": [r_that[d] for d in ds]}


def sut_giam_toi_da(r: dict, phien: list[str]) -> float:
    """Sụt giảm tối đa của đường vốn cộng dồn (điểm phần trăm vốn), đỉnh khởi đầu = 0."""
    cum = dinh = toi_da = 0.0
    for d in phien:
        cum += r.get(d, 0.0)
        dinh = max(dinh, cum)
        toi_da = max(toi_da, dinh - cum)
    return toi_da


def dem_lenh(lenh: Iterable[dict]) -> dict:
    """{`dong`, `mo` (OPEN + CLOSING), `cho` (PENDING), `huy`} — số lệnh theo trạng thái."""
    ra = {"dong": 0, "mo": 0, "cho": 0, "huy": 0}
    anh_xa = {"CLOSED": "dong", "OPEN": "mo", "CLOSING": "mo", "PENDING": "cho", "HUY": "huy"}
    for t in lenh:
        ra[anh_xa[t["status"]]] += 1
    return ra


def dem_theo_nhan(lenh: Iterable[dict], khai_ngay: Optional[str] = None) -> dict:
    """{nhãn: số lệnh} theo `nhan_du_lieu(ngày tín hiệu, khai_ngay)`."""
    ra: dict = {}
    for t in lenh:
        n = nhan_du_lieu(t["signal_date"], khai_ngay)
        ra[n] = ra.get(n, 0) + 1
    return ra


def alpha_tung_lenh(tk: TaiKhoan, gia: dict, *, bo_tin_hieu: Iterable[str] = ()) -> dict:
    """Alpha từng lệnh của `paper_metrics.vs_benchmark` (đặc tả mục 8.2, ĐỐI TƯỢNG KHÁC với hai thước):
    `{n, alpha}` — alpha None khi n < 10. Khoảng tin cậy của nó KHÔNG được in ở đây. Lệnh có ngày tín hiệu
    trong `bo_tin_hieu` (phiên bị loại khỏi cửa sổ) không vào."""
    import paper_metrics as pm
    from paper_runner import build_benchmark

    bo = {ngay10(d) for d in bo_tin_hieu}
    lenh = [t for t in tk.nhat_ky.all_trades() if ngay10(t.signal_date) not in bo]
    kq = pm.vs_benchmark(lenh, build_benchmark(lenh, gia))
    return {"n": kq["n"], "alpha": kq.get("alpha"), "bo_qua": kq["bo_qua"]}

# ── BƯỚC 243 (Lát 3b): KTC bootstrap khối CÓ CẶP, phép thử độ phủ, nhãn độ phủ ─────────────────
#: Đặc tả mục 8.3. `L` = 10 phiên được ghim TRƯỚC khi thấy dữ liệu thật (người dùng 28/10/2026); {5, 21} chỉ là
#: bảng nhạy cảm, không dùng để chọn `L`.
DO_DAI_KHOI = 10
DO_DAI_KHOI_NHAY = (5, 21)
#: Cùng `VONG` với `paper_metrics.vs_benchmark`; hạt giống cố định 0; khoảng phân vị 2,5–97,5.
VONG_KTC = 5000
HAT_KTC = 0
PHAN_VI_KTC = (2.5, 97.5)

#: Đặc tả mục 8.4: lưới n, số lần lặp, hạt giống, mô hình sinh — CỐ ĐỊNH trước khi chạy; sửa là sửa đặc tả.
LUOI_N = (40, 113, 252)
SO_LAN_LAP_DO_PHU = 2000
HAT_DO_PHU = 0
#: Độ phủ đo được dưới ngưỡng này thì nhãn "mẫu quá ngắn: độ phủ đo được dưới 90%" (người dùng duyệt).
NGUONG_DO_PHU = 0.90
#: Ba dạng chuỗi được in, mỗi dạng một cột độ phủ riêng:
#:   `cap`       KTC của mean(A) − mean(B), MỘT bộ khối cho cả hai chuỗi (thước 2: phương án − đường thật);
#:   `mot_chuoi` KTC của mean(x) khi x có đoạn KHÔNG GIỮ (e_t = 0 cho x_t = 0; thước 1: r − e×rổ);
#:   `tho`       KTC của mean(x) khi x KHÔNG có đoạn không giữ (cột thô r − rổ; rổ luôn đầu tư 100%).
DANG_KTC = ("cap", "mot_chuoi", "tho")

#: Mô hình sinh của phép thử độ phủ (mục 8.4): đuôi dày t 4 bậc tự do · tự tương quan do vị thế chồng nhau =
#: trung bình trượt `CUA_SO_VI_THE` phiên của nhiễu · thành phần chung `TY_TRONG_CHUNG` giữa A và B ·
#: đoạn không giữ = chuỗi Markov hai trạng thái, vào giữ với xác suất `P_VAO_GIU` mỗi phiên, đoạn giữ dài
#: trung bình `TB_DOAN_GIU` phiên. Trung bình thật của mọi chuỗi bằng 0 (nhiễu đối xứng, độc lập với mặt nạ).
BAC_TU_DO_T = 4
CUA_SO_VI_THE = 20
TY_TRONG_CHUNG = 0.5
P_VAO_GIU = 0.1
TB_DOAN_GIU = 15

NHAN_MAU_QUA_NGAN = "mẫu quá ngắn"
NHAN_DO_PHU_THAP = "mẫu quá ngắn: độ phủ đo được dưới 90%"


def _trung_binh_khoi(x: np.ndarray, dau: np.ndarray, do_dai: int, du: int) -> np.ndarray:
    """Trung bình của mỗi lần rút bootstrap khối VÒNG. `dau` (vong × số khối): chỉ số bắt đầu mỗi khối; mỗi lần
    rút ghép `số khối` khối dài `do_dai` rồi CẮT về n (khối cuối chỉ lấy `du` phiên đầu). Tính bằng tổng cộng dồn
    của chuỗi nhân đôi (khối vòng) nên không dựng ma trận vong × n; test đối chiếu với bản dựng chỉ số tường minh."""
    n = x.size
    p = np.concatenate([[0.0], np.cumsum(np.concatenate([x, x]))])
    s = np.arange(n)
    day = p[s + do_dai] - p[s]
    cuoi = p[s + du] - p[s]
    return (day[dau[:, :-1]].sum(axis=1) + cuoi[dau[:, -1]]) / n


# ── BƯỚC 248: độ dài khối có thể là SỐ CỐ ĐỊNH hay một QUY TẮC tính từ chính chuỗi (đặc tả mục 8.4b) ─────────────
QUY_TAC_PW = "PW"        # Politis–White (2004) + Patton–Politis–White (2009), dạng khối vòng
QUY_TAC_N13 = "N13"      # ⌈n^(1/3)⌉
QUY_TAC_KHOI = (QUY_TAC_PW, QUY_TAC_N13)


def nhan_do_dai(do_dai: Any) -> str:
    """Nhãn của một cấu hình độ dài khối ở khoá của `docs/san-dau-do-phu.json`: "L10" cho số, tên quy tắc cho quy tắc."""
    return f"L{int(do_dai)}" if isinstance(do_dai, (int, np.integer)) and not isinstance(do_dai, bool) else str(do_dai)


def do_dai_politis_white(x: Any) -> int:
    """Độ dài khối vòng tối ưu theo Politis–White (2004) có hiệu chỉnh Patton–Politis–White (2009), tính từ CHÍNH
    chuỗi `x` (đặc tả mục 8.4b, ứng viên 4): K_N = max(5, ⌈log10 n⌉); m_max = ⌈√n⌉ + K_N; m̂ = m nhỏ nhất có
    |ρ̂(m+j)| < 2·√(log10 n / n) với mọi j = 1..K_N (không có thì m_max); M = 2·max(m̂, 1); cửa sổ phẳng
    λ(s) = 1 (|s| ≤ ½), 2(1−|s|) (½ < |s| ≤ 1); ĝ = Σ λ(k/M)·R̂(k), Ĝ = Σ λ(k/M)·|k|·R̂(k) (k = −M..M, R̂ chia n);
    b = (1,5·(Ĝ/ĝ)²)^(1/3)·n^(1/3) [= (2Ĝ²/((4/3)ĝ²))^(1/3)·n^(1/3)]. ĝ ≤ 0 hay chuỗi hằng → 1; ngược lại
    làm tròn (nửa lên) của min(b, ⌈min(3√n, n/3)⌉), tối thiểu 1."""
    x = np.asarray(x, dtype=float)
    n = int(x.size)
    d = x - x.mean() if n else x
    if n < 4 or not np.any(d):
        return 1
    k_n = max(5, int(np.ceil(np.log10(n))))
    m_max = int(np.ceil(np.sqrt(n))) + k_n
    so_tre = min(m_max + k_n, n - 1)
    r = np.array([float((d[k:] * d[:n - k]).sum()) / n for k in range(0, so_tre + 1)])
    rho = r / r[0]
    nguong = 2.0 * np.sqrt(np.log10(n) / n)

    def tre(k: int) -> float:
        return abs(float(rho[k])) if k <= so_tre else 0.0

    m_hat = m_max
    for m in range(0, m_max + 1):
        if all(tre(m + j) < nguong for j in range(1, k_n + 1)):
            m_hat = m
            break
    big_m = min(2 * max(m_hat, 1), so_tre)
    ks = np.arange(0, big_m + 1)
    lam = np.where(ks / big_m <= 0.5, 1.0, 2.0 * (1.0 - ks / big_m))
    g = float(r[0] + 2.0 * (lam[1:] * r[1:big_m + 1]).sum())
    gg = float(2.0 * (lam[1:] * ks[1:] * r[1:big_m + 1]).sum())
    if g <= 0.0:
        return 1
    b = (1.5 * (gg / g) ** 2) ** (1.0 / 3.0) * n ** (1.0 / 3.0)
    tran = float(np.ceil(min(3.0 * np.sqrt(n), n / 3.0)))
    return max(1, int(np.floor(min(b, tran) + 0.5)))


def do_dai_theo_quy_tac(quy_tac: str, x: Any) -> int:
    """Độ dài khối cho `quy_tac` ∈ `QUY_TAC_KHOI` trên chuỗi `x` (thống kê là trung bình của `x`)."""
    n = int(np.asarray(x).size)
    if quy_tac == QUY_TAC_PW:
        return do_dai_politis_white(x)
    if quy_tac == QUY_TAC_N13:
        return int(np.ceil(n ** (1.0 / 3.0)))      # đo: n ** (1/3) không vượt số nguyên với mọi lập phương m³, m < 3000
    raise ValueError(f"quy tac do dai khoi khong ro: {quy_tac!r}")


def ktc_khoi_co_cap(a: Any, b: Any = None, *, do_dai: Any = DO_DAI_KHOI, vong: int = VONG_KTC,
                    hat: int = HAT_KTC) -> dict:
    """Khoảng tin cậy phân vị của `mean(a) − mean(b)` (hay `mean(a)` khi không có `b`) bằng bootstrap khối vòng
    CÓ CẶP (đặc tả mục 8.3): MỘT bộ chỉ số khối được rút và áp cho MỌI chuỗi (cặp), nên phần chung của hai chuỗi
    triệt tiêu như nó triệt tiêu trong số liệu. Khối cố định `do_dai`, rút ceil(n/do_dai) khối, cắt về n; `vong`
    lần rút; hạt giống `hat`. Đây là HÀM DUY NHẤT tính KTC của sân đấu: phép thử độ phủ gọi chính nó."""
    a = np.asarray(a, dtype=float)
    n = int(a.size)
    if b is not None:
        b = np.asarray(b, dtype=float)
        if b.size != n:
            raise ValueError(f"hai chuoi phai cung do dai ({n} != {b.size})")
    yeu_cau = do_dai
    if isinstance(do_dai, str):
        do_dai = do_dai_theo_quy_tac(do_dai, a if b is None else a - b)
    if n < 1 or not 1 <= do_dai <= n:
        raise ValueError(f"do dai khoi {do_dai} khong hop le voi n = {n}")
    so_khoi = -(-n // do_dai)
    du = n - (so_khoi - 1) * do_dai
    dau = np.random.default_rng(hat).integers(0, n, size=(vong, so_khoi))
    boot = _trung_binh_khoi(a, dau, do_dai, du)
    tb = float(a.mean())
    if b is not None:
        boot = boot - _trung_binh_khoi(b, dau, do_dai, du)
        tb -= float(b.mean())
    can_duoi, can_tren = np.percentile(boot, PHAN_VI_KTC)
    return {"n": n, "do_dai": do_dai, "do_dai_yeu_cau": yeu_cau, "so_khoi": so_khoi, "tb": tb,
            "can_duoi": float(can_duoi), "can_tren": float(can_tren), "vong": vong, "hat": hat}


def _nhieu_chong_vi_the(rng: Any, so_lan: int, n: int) -> np.ndarray:
    """Nhiễu t đuôi dày, tự tương quan do trung bình trượt `CUA_SO_VI_THE` phiên (vị thế chồng nhau), phương sai ~1."""
    z = rng.standard_t(BAC_TU_DO_T, size=(so_lan, n + CUA_SO_VI_THE - 1))
    p = np.concatenate([np.zeros((so_lan, 1)), np.cumsum(z, axis=1)], axis=1)
    return (p[:, CUA_SO_VI_THE:] - p[:, :-CUA_SO_VI_THE]) / np.sqrt(CUA_SO_VI_THE)


def _mat_na_giu(rng: Any, so_lan: int, n: int) -> np.ndarray:
    """Mặt nạ GIỮ / KHÔNG GIỮ (True = đang giữ), chuỗi Markov hai trạng thái ở phân phối dừng."""
    p_ra = 1.0 / TB_DOAN_GIU
    dung = P_VAO_GIU / (P_VAO_GIU + p_ra)
    u = rng.random((so_lan, n))
    s = rng.random(so_lan) < dung
    ra = np.empty((so_lan, n), dtype=bool)
    for t in range(n):
        s = np.where(s, u[:, t] >= p_ra, u[:, t] < P_VAO_GIU)
        ra[:, t] = s
    return ra


def sinh_chuoi_do_phu(n: int, so_lan: int, hat: int = HAT_DO_PHU) -> tuple:
    """(A, B, A_tho), mỗi mảng so_lan × n, trung bình thật bằng 0. A và B chung thành phần (cặp) và chung mặt
    nạ không giữ; A_tho là A không mặt nạ. Hạt giống phụ thuộc (hat, n) nên cùng một bộ chuỗi được dùng cho mọi `L`."""
    rng = np.random.default_rng([hat, n])
    chung = _nhieu_chong_vi_the(rng, so_lan, n)
    ia = _nhieu_chong_vi_the(rng, so_lan, n)
    ib = _nhieu_chong_vi_the(rng, so_lan, n)
    giu = _mat_na_giu(rng, so_lan, n)
    w = float(np.sqrt(TY_TRONG_CHUNG))
    v = float(np.sqrt(1.0 - TY_TRONG_CHUNG))
    a_tho = w * chung + v * ia
    b_tho = w * chung + v * ib
    return a_tho * giu, b_tho * giu, a_tho


# ── BƯỚC 248: kiểm mô hình sinh với chuỗi THẬT, rồi mô hình mới ─────────────────────────────────
#: Mô hình sinh của BƯỚC 243 (trung bình trượt `CUA_SO_VI_THE` phiên của nhiễu) cho tự tương quan bậc 1 cỡ 0,86–0,94
#: và hệ số phương sai 9–17; chuỗi THẬT (tài khoản vào lệnh ngẫu nhiên trên cache, `tools/san_dau.py kiem-mo-hinh`)
#: cho 0,04 và 0,94–1,09. Trung bình trượt của nhiễu mô tả lợi nhuận của một cửa sổ 20 phiên, KHÔNG mô tả đóng góp
#: MỖI PHIÊN của một sổ vị thế (trọng số biết trước, lợi nhuận phiên không tự tương quan). Mô hình mới: nhiễu
#: GARCH(1,1) đuôi t, KHÔNG tự tương quan ở mức, có phương sai theo cụm. Ba số dưới là KHỚP CHUNG (hợp lý cực đại, 30
#: tài khoản ngẫu nhiên, `kiem-mo-hinh --hop-garch`) làm tròn: lượt thử đầu (300 tài khoản, mầm 20261030) 0,137 · 0,809 ·
#: 7,54; lượt của dụng cụ (100 tài khoản) 0,149 · 0,794 · 7,43; mỗi tài khoản một mình 0,10–0,17 · 0,75–0,86 · 5,4–8,6.
#: KHÔNG chọn theo độ phủ (khi chốt chúng chưa có độ phủ nào của mô hình mới).
GARCH_ALPHA = 0.14
GARCH_BETA = 0.81
GARCH_NU = 7.5
#: Dư để GARCH về phân phối dừng trước khi lấy mẫu.
GARCH_DU = 200
#: Hệ số tự hồi quy bậc 1 của mô hình CĂNG THẲNG (báo cáo, không phải tiêu chí chọn): cao hơn mọi số đo được
#: (rổ đều 0,09 · trung vị mã 0,06 · tài khoản ngẫu nhiên 0,04).
PHI_CANG_THANG = 0.15


def _nhieu_garch(rng: Any, so_lan: int, n: int, phi: float = 0.0) -> np.ndarray:
    """Nhiễu GARCH(1,1) đuôi t (`GARCH_NU` bậc tự do, chuẩn hoá phương sai 1), phương sai vô điều kiện 1 (ω = 1 − α − β).
    `phi` ≠ 0 thêm tự hồi quy bậc 1 giữ phương sai 1: y_t = φ·y_(t−1) + √(1−φ²)·a_t."""
    t_tong = n + GARCH_DU
    z = rng.standard_t(GARCH_NU, size=(so_lan, t_tong)) / np.sqrt(GARCH_NU / (GARCH_NU - 2.0))
    omega = 1.0 - GARCH_ALPHA - GARCH_BETA
    a = np.empty((so_lan, t_tong))
    h = np.ones(so_lan)
    for t in range(t_tong):
        a[:, t] = np.sqrt(h) * z[:, t]
        h = omega + GARCH_ALPHA * a[:, t] ** 2 + GARCH_BETA * h
    if phi == 0.0:
        return a[:, GARCH_DU:]
    y = np.empty_like(a)
    y[:, 0] = a[:, 0]
    k = float(np.sqrt(1.0 - phi * phi))
    for t in range(1, t_tong):
        y[:, t] = phi * y[:, t - 1] + k * a[:, t]
    return y[:, GARCH_DU:]


def sinh_chuoi_mo_hinh_moi(n: int, so_lan: int, hat: int = HAT_DO_PHU, phi: float = 0.0) -> tuple:
    """(A, B, A_tho) như `sinh_chuoi_do_phu` nhưng nhiễu là `_nhieu_garch` (BƯỚC 248). Cùng thành phần chung, cùng mặt
    nạ không giữ, cùng cách đặt hạt giống (hat, n); trung bình thật bằng 0."""
    rng = np.random.default_rng([hat, n])
    chung = _nhieu_garch(rng, so_lan, n, phi)
    ia = _nhieu_garch(rng, so_lan, n, phi)
    ib = _nhieu_garch(rng, so_lan, n, phi)
    giu = _mat_na_giu(rng, so_lan, n)
    w = float(np.sqrt(TY_TRONG_CHUNG))
    v = float(np.sqrt(1.0 - TY_TRONG_CHUNG))
    a_tho = w * chung + v * ia
    b_tho = w * chung + v * ib
    return a_tho * giu, b_tho * giu, a_tho


# Thống kê MÔ TẢ chuỗi (không so sánh chiến lược): dùng để kiểm mô hình sinh với chuỗi thật.
SO_TRE_MO_TA = 60
TRE_IN = (1, 2, 5, 10, 20, 30, 40, 60)


def acf_mau(y: Any, so_tre: int = SO_TRE_MO_TA) -> np.ndarray:
    """Tự tương quan mẫu bậc 1..so_tre (bỏ NaN, trừ trung bình mẫu, chia cho tổng bình phương)."""
    y = np.asarray(y, dtype=float)
    y = y[~np.isnan(y)]
    y = y - y.mean()
    mau = float((y * y).sum())
    return np.array([float((y[k:] * y[:-k]).sum()) / mau for k in range(1, so_tre + 1)])


def he_so_phuong_sai(rho: Any, n: int) -> float:
    """1 + 2·Σ (1 − k/n)·ρ_k: tỷ số giữa phương sai của TRUNG BÌNH mẫu và phương sai nếu các phiên độc lập."""
    rho = np.asarray(rho, dtype=float)
    k = np.arange(1, rho.size + 1)
    return 1.0 + 2.0 * float((np.clip(1.0 - k / n, 0.0, None) * rho).sum())


def kurt_thua(y: Any) -> float:
    """Độ nhọn thừa (m4/m2² − 3) của chuỗi, bỏ NaN."""
    y = np.asarray(y, dtype=float)
    y = y[~np.isnan(y)]
    d = y - y.mean()
    return float((d ** 4).mean() / (d ** 2).mean() ** 2 - 3.0)


def mo_ta_chuoi(m: Any) -> dict:
    """Trung bình theo hàng của ACF(y), ACF(|y|), hệ số phương sai và độ nhọn thừa, trên ma trận m (số chuỗi × n).
    Chỉ các bậc `TRE_IN` được trả về."""
    m = np.atleast_2d(np.asarray(m, dtype=float))
    ac = np.array([acf_mau(r) for r in m]).mean(axis=0)
    aa = np.array([acf_mau(np.abs(r)) for r in m]).mean(axis=0)
    return {"so_chuoi": int(m.shape[0]), "n": int(m.shape[1]),
            "acf": {str(k): round(float(ac[k - 1]), 3) for k in TRE_IN},
            "acf_tuyet_doi": {str(k): round(float(aa[k - 1]), 3) for k in TRE_IN},
            "he_so_phuong_sai": round(float(np.mean([he_so_phuong_sai(acf_mau(r), m.shape[1]) for r in m])), 3),
            "kurt_thua": round(float(np.mean([kurt_thua(r) for r in m])), 2)}


def tai_khoan_ngau_nhien(gia: Any, ro: Any, rng: Any, *, so_phien_giu: int, xac_suat_vao: float,
                         ty_trong: float) -> tuple[np.ndarray, np.ndarray]:
    """MỘT tài khoản vào lệnh NGẪU NHIÊN trên ma trận giá đóng cửa `gia` (phiên × mã, NaN = thiếu) để đo cấu trúc
    phụ thuộc của x_t = r_t − e_t·rổ_t mà KHÔNG dùng lệnh hay lãi nào của sổ thật: mỗi phiên, xác suất `xac_suat_vao`
    mở một vị thế ở một mã ngẫu nhiên, cỡ `ty_trong` vốn, giữ `so_phien_giu` phiên (cắt ở chỗ mất nến); đóng góp mỗi
    phiên = ty_trong × Δgiá / giá vào (đặc tả mục 8.1). Trả (x_t, e_t); `ro[t]` NaN coi là 0."""
    gia = np.asarray(gia, dtype=float)
    n_phien, n_ma = gia.shape
    dong_gop = np.zeros(n_phien)
    e = np.zeros(n_phien)
    for s in range(n_phien - 1):
        if rng.random() >= xac_suat_vao:
            continue
        j = int(rng.integers(0, n_ma))
        doan = gia[s: min(n_phien - 1, s + so_phien_giu) + 1, j]
        if np.isnan(doan).any():      # cắt ở chỗ mất nến; mất ngay giá vào thì còn 0 phiên và bị bỏ ở dưới
            doan = doan[: int(np.argmax(np.isnan(doan)))]
        if doan.size < 2:
            continue
        dong_gop[s + 1: s + doan.size] += (doan[1:] - doan[:-1]) / doan[0] * 100.0 * ty_trong
        e[s + 1: s + doan.size] += ty_trong
    return dong_gop - e * np.nan_to_num(np.asarray(ro, dtype=float)), e


def do_phu_mot_o(n: int, do_dai: Any, dang: str, *, so_lan: int = SO_LAN_LAP_DO_PHU, hat: int = HAT_DO_PHU,
                 vong: int = VONG_KTC, chuoi: Optional[tuple] = None) -> Optional[float]:
    """Tỷ lệ KTC (do `ktc_khoi_co_cap` tính, cùng mã với thứ được in) chứa 0 trên `so_lan` bộ chuỗi có trung bình
    thật bằng 0, ở n, `do_dai` (số hay quy tắc) và dạng `dang` đã cho. `chuoi` = kết quả `sinh_chuoi_do_phu` (để
    dùng chung). Khối CỐ ĐỊNH dài hơn n thì phương pháp KHÔNG XÁC ĐỊNH ở n ấy: trả None (ô không đạt, đặc tả 8.4b)."""
    if dang not in DANG_KTC:
        raise ValueError(f"dang KTC khong ro: {dang!r}")
    if isinstance(do_dai, (int, np.integer)) and not isinstance(do_dai, bool) and do_dai > n:
        return None
    a, b, a_tho = chuoi if chuoi is not None else sinh_chuoi_do_phu(n, so_lan, hat)
    chua = 0
    for i in range(so_lan):
        if dang == "cap":
            k = ktc_khoi_co_cap(a[i], b[i], do_dai=do_dai, vong=vong)
        elif dang == "mot_chuoi":
            k = ktc_khoi_co_cap(a[i], do_dai=do_dai, vong=vong)
        else:
            k = ktc_khoi_co_cap(a_tho[i], do_dai=do_dai, vong=vong)
        if k["can_duoi"] <= 0.0 <= k["can_tren"]:
            chua += 1
    return chua / so_lan


def mo_phong_do_phu(*, luoi_n: Iterable[int] = LUOI_N,
                    do_dai: Iterable[Any] = (DO_DAI_KHOI, *DO_DAI_KHOI_NHAY),
                    so_lan: int = SO_LAN_LAP_DO_PHU, hat: int = HAT_DO_PHU, vong: int = VONG_KTC,
                    sinh: Optional[Callable[[int, int, int], tuple]] = None) -> dict:
    """Độ phủ đo được: {nhãn: {"<n>": {dạng: tỷ lệ | None}}} với nhãn = `nhan_do_dai(do_dai)`. Mỗi n sinh MỘT lần bộ
    chuỗi (bằng `sinh(n, so_lan, hat)`, mặc định `sinh_chuoi_do_phu`) dùng cho mọi cấu hình độ dài khối."""
    sinh = sinh or sinh_chuoi_do_phu
    ra: dict = {}
    for n in luoi_n:
        chuoi = sinh(n, so_lan, hat)
        for ld in do_dai:
            o = ra.setdefault(nhan_do_dai(ld), {}).setdefault(str(n), {})
            for dang in DANG_KTC:
                o[dang] = do_phu_mot_o(n, ld, dang, so_lan=so_lan, hat=hat, vong=vong, chuoi=chuoi)
    return ra


#: Danh sách ứng viên THEO THỨ TỰ khai ở đặc tả mục 8.4b (BƯỚC 248), khai TRƯỚC khi chạy độ phủ của ứng viên nào.
UNG_VIEN_KTC = (42, 63, 21, QUY_TAC_PW, 10, QUY_TAC_N13, 5)
#: Mô phỏng dùng để CHỌN (mục 8.4b khoản 2): số lần lặp mỗi ô; hạt 0.
SO_LAN_CHON = 10_000


def o_dat(p: Optional[float]) -> bool:
    """Một ô ĐẠT khi đã đo được (không phải None) và độ phủ ≥ `NGUONG_DO_PHU` (so ước lượng điểm, không dung sai)."""
    return p is not None and p >= NGUONG_DO_PHU


def ung_vien_dat(bang_ung_vien: dict, *, luoi_n: Iterable[int] = LUOI_N) -> bool:
    """Cả `len(luoi_n) × 3` ô (3 dạng × mỗi n) của MỘT ứng viên đều ĐẠT (mục 8.4b khoản 3)."""
    return all(o_dat((bang_ung_vien.get(str(n)) or {}).get(d)) for n in luoi_n for d in DANG_KTC)


def chon_ung_vien(*, ung_vien: Optional[Iterable[Any]] = None, luoi_n: Iterable[int] = LUOI_N,
                  so_lan: int = SO_LAN_CHON, hat: int = HAT_DO_PHU, vong: int = VONG_KTC,
                  sinh: Optional[Callable[[int, int, int], tuple]] = None, ghi: Optional[Callable] = None) -> dict:
    """Chạy ứng viên THEO THỨ TỰ và DỪNG ở ứng viên ĐẦU TIÊN đạt (không thử ứng viên nào sau nó để chọn):
    {"da_thu": [(nhãn, bảng độ phủ của n × dạng)], "chot": nhãn | None}. `ghi` nhận mỗi ứng viên vừa đo xong."""
    luoi_n = tuple(luoi_n)
    da_thu: list = []
    for uv in (UNG_VIEN_KTC if ung_vien is None else ung_vien):
        bang = mo_phong_do_phu(luoi_n=luoi_n, do_dai=(uv,), so_lan=so_lan, hat=hat, vong=vong, sinh=sinh)[nhan_do_dai(uv)]
        dat = ung_vien_dat(bang, luoi_n=luoi_n)
        da_thu.append((nhan_do_dai(uv), bang))
        if ghi is not None:
            ghi(nhan_do_dai(uv), bang, dat)
        if dat:
            return {"da_thu": da_thu, "chot": nhan_do_dai(uv)}
    return {"da_thu": da_thu, "chot": None}


def dung_bang_do_phu(do_phu: dict, *, luoi_n: Iterable[int] = LUOI_N,
                     do_dai: Iterable[int] = (DO_DAI_KHOI, *DO_DAI_KHOI_NHAY),
                     so_lan: int = SO_LAN_LAP_DO_PHU, hat: int = HAT_DO_PHU, vong: int = VONG_KTC) -> dict:
    """Nội dung `docs/san-dau-do-phu.json`: tham số cố định, mô hình sinh (suy ra từ hằng số, không gõ tay) và độ
    phủ đo được. Sai số Monte Carlo lớn nhất (căn p(1−p)/số lần lặp) in kèm để biết ô nào là nhiễu."""
    sai_so = max((float(np.sqrt(p * (1.0 - p) / so_lan)) for l_ in do_phu.values() for o in l_.values()
                  for p in o.values()), default=0.0)
    return {
        "_ghi_chu": ("Do phu cua khoang tin cay bootstrap khoi (BUOC 243, Lat 3b; docs/thiet-ke-c1-san-dau.md muc 8.4). "
                     "Tai lap: ./.venv/Scripts/python.exe tools/san_dau.py do-phu --kiem (so sanh voi file nay) hoac "
                     "do-phu --json (in lai). App/bang CHI DOC file nay; sua tham so o dac ta TRUOC khi chay lai."),
        "lenh": "./.venv/Scripts/python.exe tools/san_dau.py do-phu --json",
        "tham_so": {"hat": hat, "so_lan_lap": so_lan, "vong_bootstrap": vong, "hat_bootstrap": HAT_KTC,
                    "phan_vi": list(PHAN_VI_KTC), "luoi_n": list(luoi_n), "do_dai_khoi": list(do_dai),
                    "do_dai_khoi_chinh": DO_DAI_KHOI, "nguong_do_phu": NGUONG_DO_PHU},
        "mo_hinh": {"bac_tu_do_t": BAC_TU_DO_T, "cua_so_vi_the": CUA_SO_VI_THE, "ty_trong_chung": TY_TRONG_CHUNG,
                    "p_vao_giu": P_VAO_GIU, "tb_doan_giu": TB_DOAN_GIU,
                    "dang": {"cap": "mean(A) - mean(B), mot bo khoi cho ca hai chuoi (thuoc 2)",
                             "mot_chuoi": "mean(x), x co doan KHONG GIU bang 0 (thuoc 1)",
                             "tho": "mean(x), x khong co doan khong giu (cot tho r - ro)"}},
        "do_phu": do_phu,
        "sai_so_monte_carlo_toi_da": sai_so,
    }


def vi_pham_bang_do_phu(bang: Any) -> list[str]:
    """Lỗi cấu trúc của `docs/san-dau-do-phu.json` (rỗng = hợp lệ): khoá, kiểu, p ∈ [0, 1], đủ ô của lưới, và
    tham số phải KHỚP hằng số hiện hành của module — sửa mô hình hay lưới mà không chạy lại thì file cũ bị bắt."""
    if not isinstance(bang, dict):
        return ["khong phai tu dien"]
    loi: list = []
    ts = bang.get("tham_so") or {}
    mong = {"hat": HAT_DO_PHU, "so_lan_lap": SO_LAN_LAP_DO_PHU, "vong_bootstrap": VONG_KTC,
            "hat_bootstrap": HAT_KTC, "phan_vi": list(PHAN_VI_KTC), "luoi_n": list(LUOI_N),
            "do_dai_khoi": [DO_DAI_KHOI, *DO_DAI_KHOI_NHAY], "do_dai_khoi_chinh": DO_DAI_KHOI,
            "nguong_do_phu": NGUONG_DO_PHU}
    for k, v in mong.items():
        if ts.get(k) != v:
            loi.append(f"tham_so.{k} = {ts.get(k)!r}, hang so hien hanh = {v!r}")
    mh = bang.get("mo_hinh") or {}
    for k, v in (("bac_tu_do_t", BAC_TU_DO_T), ("cua_so_vi_the", CUA_SO_VI_THE), ("ty_trong_chung", TY_TRONG_CHUNG),
                 ("p_vao_giu", P_VAO_GIU), ("tb_doan_giu", TB_DOAN_GIU)):
        if mh.get(k) != v:
            loi.append(f"mo_hinh.{k} = {mh.get(k)!r}, hang so hien hanh = {v!r}")
    dp = bang.get("do_phu")
    if not isinstance(dp, dict):
        return loi + ["thieu muc do_phu"]
    for ld in (DO_DAI_KHOI, *DO_DAI_KHOI_NHAY):
        for n in LUOI_N:
            o = (dp.get(f"L{ld}") or {}).get(str(n))
            if not isinstance(o, dict):
                loi.append(f"thieu o L{ld} n={n}")
                continue
            for dang in DANG_KTC:
                p = o.get(dang)
                if isinstance(p, bool) or not isinstance(p, (int, float)) or not 0.0 <= p <= 1.0:
                    loi.append(f"o L{ld} n={n} dang {dang}: {p!r} khong phai ty le")
    return loi


def n_luoi_cua(n: int, luoi_n: Iterable[int] = LUOI_N) -> Optional[int]:
    """Điểm lưới LỚN NHẤT ≤ n (đặc tả mục 8.4); None khi n nhỏ hơn mọi điểm lưới."""
    ok = [g for g in luoi_n if g <= n]
    return max(ok) if ok else None


def dinh_dang_ktc(n: int, dang: str, ktc: Optional[dict], bang_do_phu: Optional[dict],
                  do_dai: int = DO_DAI_KHOI) -> str:
    """NƠI DUY NHẤT ghép chuỗi KTC danh nghĩa và LUÔN kèm độ phủ đã đo (gác G6): không có độ phủ đo thì không
    in con số 95. n nhỏ hơn mọi điểm lưới → "mẫu quá ngắn", không in KTC; n không có trên lưới → dùng điểm lưới
    lớn nhất ≤ n; độ phủ đo được < `NGUONG_DO_PHU` → thêm nhãn "mẫu quá ngắn: độ phủ đo được dưới 90%"."""
    luoi = (bang_do_phu or {}).get("tham_so", {}).get("luoi_n", LUOI_N)
    g = n_luoi_cua(n, luoi)
    if g is None:
        return f"{NHAN_MAU_QUA_NGAN} (n={n} < {min(luoi)}): không in KTC"
    if bang_do_phu is None:
        return f"chưa có bảng độ phủ đo (docs/san-dau-do-phu.json): không in KTC (n={n})"
    p = ((bang_do_phu.get("do_phu") or {}).get(f"L{do_dai}") or {}).get(str(g), {}).get(dang)
    if p is None or ktc is None:
        return f"chưa đo độ phủ ở n={g}, L={do_dai}, dạng {dang}: không in KTC (n={n})"
    s = (f"KTC danh nghĩa 95% [{ktc['can_duoi']:+.3f} ; {ktc['can_tren']:+.3f}] — "
         f"độ phủ đo được {100.0 * p:.1f}% (n={g}, L={do_dai})")
    if p < NGUONG_DO_PHU:
        s += f" — {NHAN_DO_PHU_THAP}"
    return s


def ktc_co_nhan(a: Any, b: Any, dang: str, bang_do_phu: Optional[dict], *, do_dai: int = DO_DAI_KHOI) -> dict:
    """KTC của một chuỗi (hay một cặp) KÈM nhãn độ phủ: {n, ktc | None, dong}. Chỉ tính KTC khi sẽ được in
    (n đủ lớn và đã có bảng độ phủ); `dong` là chuỗi in được, ghép bởi `dinh_dang_ktc`."""
    n = len(a)
    luoi = (bang_do_phu or {}).get("tham_so", {}).get("luoi_n", LUOI_N)
    ktc = ktc_khoi_co_cap(a, b, do_dai=do_dai) if (bang_do_phu is not None and n_luoi_cua(n, luoi) is not None
                                                  and n >= do_dai) else None
    return {"n": n, "dang": dang, "ktc": ktc, "dong": dinh_dang_ktc(n, dang, ktc, bang_do_phu, do_dai)}
