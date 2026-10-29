"""Sân đấu C1 — bộ PHÁT LẠI thuần (BƯỚC 240, Lát 2 của `docs/thiet-ke-c1-san-dau.md`).

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

    def vni_tren_ma50(self, ngay: str) -> bool:
        n = ngay10(ngay)
        if self._df is None:
            self.ngay_thieu.add(n)
            return True
        sub = self._df[self._df["time"] <= n]
        if sub.empty or ngay10(self._df["time"].iloc[-1]) < n:
            self.ngay_thieu.add(n)
        if sub.empty:
            return True
        dong = sub.iloc[-1]
        if pd.notna(dong["vni_ma50"]):
            return float(dong["close"]) >= float(dong["vni_ma50"])
        return True

    def do_rong(self, ngay: str) -> Optional[float]:
        raise NotImplementedError("nguồn độ rộng chưa có — Lát 3 của C1 (đặc tả mục 4 khoản 4)")


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


def _kiem_cau_hinh_ho_tro(cau_hinh: Any) -> None:
    """Từ chối cấu hình mà Lát 2 CHƯA có đầu vào cho: phát lại lặng lẽ bỏ qua là phát lại sai."""
    import paper_trading as pt
    if cau_hinh.luat_vao != "MO_CUA_SAU":
        raise NotImplementedError(f"luat_vao={cau_hinh.luat_vao!r}: chưa có — Lát 4 của C1")
    if cau_hinh.do_rong_nguong > 0:
        raise NotImplementedError("cổng độ rộng: chưa có nguồn độ rộng — Lát 3 của C1")
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

    _kiem_cau_hinh_ho_tro(cau_hinh)
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
