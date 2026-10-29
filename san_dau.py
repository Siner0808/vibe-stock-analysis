"""Sân đấu C1 — bộ PHÁT LẠI thuần (BƯỚC 240, Lát 2 của `docs/thiet-ke-c1-san-dau.md`).

BƯỚC 242 (Lát 3a) thêm: nguồn độ rộng tiêm được cho PB-002 (`NguonDoRong`), cấu hình từ dòng sổ phương án
(`cau_hinh_tu_phuong_an`), chuỗi lợi nhuận mỗi phiên + gác bảo toàn, rổ, và hai thước ở dạng GIÁ TRỊ ĐIỂM
(khoảng tin cậy và độ phủ đến ở BƯỚC 243).

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
            "tho_tb": _trung_binh(list(tho.values())), "tho_cong_don": sum(tho.values())}


def thuoc_2(r_pa: dict, r_that: dict, phien: list[str]) -> dict:
    """THƯỚC 2 (đặc tả mục 8.2), GIÁ TRỊ ĐIỂM: `d_t = r_t(phương án) − r_t(đường thật phát lại)` trên
    các phiên của cửa sổ CHUNG `phien`."""
    ds = [d for d in phien if d in r_pa and d in r_that]
    d_t = [r_pa[d] - r_that[d] for d in ds]
    return {"n_phien": len(ds), "tb": _trung_binh(d_t), "cong_don": sum(d_t)}


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
