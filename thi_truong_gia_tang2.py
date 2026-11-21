"""Thị trường giả có lợi thế cài sẵn — Tầng 2, qua đường ống thật (C4, Lát 4, BƯỚC 292).

Đề bài: `docs/thiet-ke-c4-thi-truong-gia.md` mục 4.1 (Tầng 2), 4.2 (thành phần mang = `volume_score`), 4.6 (250
phiên khởi động), 4.8 (hạt), 4.9 (cắm vào bộ máy thật), 6 (hàng P) và 8 ("Lát 4"). Đặc tả là nguồn duy nhất; đừng chép
nó vào đây.

Phần này làm HAI việc, và chỉ hai:

1. `sinh_thi_truong_2` — bộ sinh khung OHLCV đầy đủ. Lợi nhuận, nhân tố ẩn `z` và hạt là CHÍNH `thi_truong_gia._sinh_loi`
   (cùng bộ sinh Tầng 1, không bản sao); phần thêm là cột `open`/`high`/`low` và cột `volume`, trong đó **khối lượng
   mang `z`**: `log(khối lượng) = log(cỡ mã) + C_Z·z(t) + SIGMA·nhiễu`. Chỉ khối lượng đọc được `z` (cộng nhiễu); giá thì
   mang `z` qua kỳ vọng cài sẵn của lợi nhuận (mục 4.2), như Tầng 1. Mọi số ngẫu nhiên THÊM ở đây rút SAU `_sinh_loi` và
   KHÔNG phụ thuộc `kappa`, nên thị trường NULL và thị trường có lợi thế CÙNG hạt có CÙNG khối lượng.
2. `cham_diem_theo_ma` / `cham_diem` — chấm điểm bằng `paper_runner._analyze` THẬT trên lịch sử cắt tới từng phiên
   (như walk-forward) và dựng dòng đúng khuôn bảng `decisions`. KHÔNG có hàm chấm điểm nào khác trong module này.

Hai bẫy đã đo khi dựng (BƯỚC 292), nói ở đây vì chúng nằm đúng chỗ cần cẩn thận:

* `paper_runner._ANALYZE_CACHE` khoá bằng `(mã, số dòng, ngày cuối, ngày phiên)` + dấu vân bộ nhớ — KHÔNG chứa nội dung giá.
  Hai thị trường giả cùng tên mã (`GIA01`…), cùng lịch ngày, khác hạt → CÙNG khoá → thị trường thứ hai nhận điểm của
  thị trường thứ nhất. Nên mọi lượt chấm ở đây xoá cache trước và sau, mỗi mã một lần (kèm test dựng đúng va chạm đó).
* `paper_trading`/`master_agent` gọi `post_mortem_learning.get_learning_engine()`, mà việc dựng engine mặc định ĐỌC
  `sl_pattern_memory.json` nếu file có ở thư mục hiện hành (kể cả khi engine tắt). Nên lượt chấm đặt một engine TẮT trỏ vào
  đường không có file, rồi trả engine cũ.

Phần P2 (BƯỚC 292, phase 2): `chay_that_va_phat_lai` chạy CÙNG một thị trường hai cách — `paper_runner.run_session`
(đường thật, chấm điểm bằng `_analyze` ngay lúc chạy) và `san_dau.phat_lai` (điểm đã ghi từ `cham_diem`) — rồi so bảng
`trades` từng ô của `san_dau.COT_TUONG_DUONG`. Phần P3: `ic_thanh_phan` đo IC (tương quan hạng gộp, cùng `E.rho_hang`) của từng
thành phần điểm với nhãn `E.nhan_vuot_ro`: lợi thế có ĐI QUA agent thật hay không. Nó chỉ dùng nhãn, KHÔNG dùng `z` hay oracle.

Module KHÔNG sửa, KHÔNG nhập ngược từ đường thật (gác G2), không đồng hồ, không mạng, không file, không sổ khác `:memory:`.
"""
from __future__ import annotations

import contextlib
import json
from dataclasses import dataclass

import numpy as np
import pandas as pd

import cham_bong as cb
import experiment_tran_dac_trung as E
import thi_truong_gia as T

# ── dòng thời gian (mục 4.6) ─────────────────────────────────────────────────
SO_PHIEN_KHOI_DONG = 250   # phiên khởi động đứng trước cửa sổ có quyết định; agent cần chúng, không có dòng quyết định
SAN_GIAO_DICH = "HOSE"     # biên ±7% khớp `T.BIEN_NGAY`

# ── mô hình sinh thêm của Tầng 2 — KHAI trước khi chạy bất kỳ thị trường nào, CHƯA hiệu chuẩn vào giá thật ──
# (đặc tả mục 4.2 chỉ chốt "khối lượng mang z"; con số buộc phải có là cái mã cần. Chọn TRƯỚC khi nhìn một điểm nào
# do `_analyze` cho ra; sửa là sửa đặc tả và đổi dòng hạt — bất biến 7.)
HE_SO_Z_KHOI_LUONG = 0.4        # C_Z: hệ số của z trong log khối lượng
SIGMA_KHOI_LUONG = 0.3          # độ lệch chuẩn nhiễu ngày của log khối lượng (độc lập ngày này sang ngày khác)
KHOI_LUONG_TRUNG_VI = 1_000_000  # cỡ khối lượng ngày (cổ phiếu) của một mã trung vị
SIGMA_CO_MA = 0.7               # độ lệch chuẩn của log cỡ khối lượng giữa các mã
BUOC_KHOI_LUONG = 100           # khối lượng làm tròn theo lô 100 như HOSE
SIGMA_GAP = 0.003               # nhảy mở cửa so với đóng cửa hôm trước
TRAN_GAP = 0.02                 # kẹp ±2% (nằm trong biên ±7%)
SIGMA_BIEN_TRONG_NGAY = 0.006   # độ rộng râu nến: |N(0, σ)| ngoài thân nến

#: Cột khung OHLCV, đúng thứ tự `data_quality.REQUIRED_COLUMNS`.
COT_OHLCV = ("time", "open", "high", "low", "close", "volume")


@dataclass(frozen=True, eq=False)
class ThiTruongGia2:
    """MỘT thị trường Tầng 2. Không mang `z` và không mang oracle (gác G4): vòng chấm chỉ thấy khung giá."""
    luong: int
    chi_so: int
    kappa: float
    so_khoi_dong: int
    so_phien: int                      # số phiên CÓ quyết định (không tính khởi động)
    ngay: tuple[str, ...]              # khởi động + có quyết định
    ma: tuple[str, ...]
    gia: dict[str, pd.DataFrame]       # mã → khung OHLCV (nghìn đồng), `time` 10 ký tự tăng nghiêm ngặt

    @property
    def ngay_quyet_dinh(self) -> tuple[str, ...]:
        return self.ngay[self.so_khoi_dong:]


# ── bộ sinh ──────────────────────────────────────────────────────────────────

def _sinh_ohlcv_loi(rng, so_tong: int, kappa: float) -> dict:
    """Lõi sinh Tầng 2: `T._sinh_loi` (lợi nhuận, z) rồi các số ngẫu nhiên THÊM, theo thứ tự cố định,
    KHÔNG phụ thuộc `kappa`. Trả mảng `phiên × mã` cho từng cột và `z` (cho test; KHÔNG vào `ThiTruongGia2`)."""
    n, m = so_tong, T.SO_MA
    loi = T._sinh_loi(rng, n, kappa)
    close, z = loi["close"], loi["z"]
    co_ma = np.exp(np.log(KHOI_LUONG_TRUNG_VI) + SIGMA_CO_MA * rng.standard_normal(m))
    nhieu_kl = rng.standard_normal((n, m))
    gap = np.clip(rng.normal(0.0, SIGMA_GAP, size=(n, m)), -TRAN_GAP, TRAN_GAP)
    rau_tren = np.abs(rng.normal(0.0, SIGMA_BIEN_TRONG_NGAY, size=(n, m)))
    rau_duoi = np.abs(rng.normal(0.0, SIGMA_BIEN_TRONG_NGAY, size=(n, m)))

    tham_chieu = np.empty_like(close)            # đóng cửa hôm trước; phiên đầu lấy chính đóng cửa của nó
    tham_chieu[0] = close[0]
    tham_chieu[1:] = close[:-1]
    mo = tham_chieu * (1.0 + gap)
    than_cao, than_thap = np.maximum(mo, close), np.minimum(mo, close)
    # Kẹp vào biên ±7% RỒI mới bảo đảm cao ≥ thân nến, thấp ≤ thân nến. Thứ tự ấy là cố ý: lợi nhuận kẹp ở đúng
    # `BIEN_NGAY` nên `close/ref` có thể vượt biên 1e-16 (làm tròn của `cumprod`), `np.clip` khi cận dưới > cận trên
    # trả cận trên (< đóng cửa), và `validate_ohlcv` (so chặt) báo OHLC_INCONSISTENT → `data_quality` = WARN.
    # P1 bắt được đúng lỗi này ở lượt chạy đầu tiên (BƯỚC 292).
    cao = np.maximum(np.clip(than_cao * (1.0 + rau_tren), than_cao, tham_chieu * (1.0 + T.BIEN_NGAY)), than_cao)
    thap = np.minimum(np.clip(than_thap * (1.0 - rau_duoi), tham_chieu * (1.0 - T.BIEN_NGAY), than_thap), than_thap)
    log_kl = np.log(co_ma)[None, :] + HE_SO_Z_KHOI_LUONG * z + SIGMA_KHOI_LUONG * nhieu_kl
    khoi_luong = np.maximum(BUOC_KHOI_LUONG, np.rint(np.exp(log_kl) / BUOC_KHOI_LUONG) * BUOC_KHOI_LUONG)
    return {"open": mo, "high": cao, "low": thap, "close": close, "volume": khoi_luong.astype(np.int64), "z": z}


def dong_thoi_gian_2(so_khoi_dong: int = SO_PHIEN_KHOI_DONG) -> dict:
    """Dòng thời gian Tầng 2 (mục 4.6; BƯỚC 293, mục 18 khoản 12a): `T.dong_thoi_gian` với độ lệch lịch bằng số phiên
    khởi động, vì khởi động chiếm `so_khoi_dong` ngày ĐẦU của lịch giả nên đầu tháng dương lịch rơi vào phiên có
    quyết định khác Tầng 1. Mọi chỉ số (`khai`, `doc`, `tong`) là chỉ số PHIÊN CÓ QUYẾT ĐỊNH; không gõ tay."""
    return {**T.dong_thoi_gian(lech=int(so_khoi_dong)), "lech": int(so_khoi_dong)}


def sinh_thi_truong_2(luong: int, chi_so: int, kappa: float, so_phien: int | None = None,
                      so_khoi_dong: int = SO_PHIEN_KHOI_DONG, hat_them: int | None = None) -> ThiTruongGia2:
    """Sinh MỘT thị trường Tầng 2. `so_phien` mặc định = `dong_thoi_gian_2(so_khoi_dong)["tong"]` (phiên có quyết định);
    `so_khoi_dong` phiên khởi động đứng TRƯỚC chúng. Hạt `default_rng([luong, chi_so])` như Tầng 1 (mục 4.8).

    Ngày giả liền một mạch từ `T.NGAY_DAU` (gác G5): khởi động chiếm `so_khoi_dong` phiên đầu, nên phiên có quyết định
    đầu tiên rơi vào ngày thứ `so_khoi_dong + 1` của lịch, không phải ngày `T.NGAY_DAU`.

    `hat_them` (BƯỚC 293): `None` = hạt `[luong, chi_so]` như Tầng 1; một số nguyên thì hạt là `[luong, chi_so, hat_them]`
    — cùng cách dựng hạt của mẫu bảng sự thật Tầng 1, để mẫu bảng sự thật Tầng 2 có hạt RIÊNG mà vẫn qua đúng bộ sinh này."""
    T._kiem_hat(luong, chi_so)
    if kappa < 0:
        raise ValueError("kappa phai >= 0")
    if so_khoi_dong < 0:
        raise ValueError("so_khoi_dong phai >= 0")
    n_qd = dong_thoi_gian_2(so_khoi_dong)["tong"] if so_phien is None else int(so_phien)
    n = so_khoi_dong + n_qd
    hat = [luong, chi_so] if hat_them is None else [luong, chi_so, int(hat_them)]
    mau = _sinh_ohlcv_loi(np.random.default_rng(hat), n, float(kappa))
    ngay, ma = T.lich_phien(n), T._ma_gia()
    gia = {}
    for j, m in enumerate(ma):
        gia[m] = pd.DataFrame({"time": list(ngay), **{c: mau[c][:, j] for c in COT_OHLCV[1:]}})
    return ThiTruongGia2(luong=luong, chi_so=chi_so, kappa=float(kappa), so_khoi_dong=so_khoi_dong,
                         so_phien=n_qd, ngay=ngay, ma=ma, gia=gia)


# ── chấm điểm qua đường ống thật ─────────────────────────────────────────────

#: Đường KHÔNG CÓ FILE: engine tắt trỏ vào đây thì `load_memory` không đọc gì (không đụng `sl_pattern_memory.json`).
_DUONG_BO_NHO_KHONG_CO = ".khong-co-bo-nho-thi-truong-gia.json"


@contextlib.contextmanager
def moi_truong_cham():
    """Đặt môi trường chấm điểm sạch rồi trả lại: engine bộ nhớ hậu nghiệm TẮT trỏ vào đường không có file, và
    `_ANALYZE_CACHE` rỗng. Trả lại engine và cache cũ khi ra (kể cả khi nổ)."""
    import paper_runner as pr
    import post_mortem_learning as pml

    engine_cu, cache_cu = pml._ENGINE_CACHE, dict(pr._ANALYZE_CACHE)
    pml.dat_lai_engine(_DUONG_BO_NHO_KHONG_CO, enabled=False)
    pr._xoa_cache_phan_tich()
    try:
        yield
    finally:
        pr._xoa_cache_phan_tich()
        pr._ANALYZE_CACHE.update(cache_cu)
        pml._ENGINE_CACHE = engine_cu


def _gio_phien(ngay: str) -> float:
    """`at` giả, tất định: 15:35 giờ Việt Nam của `ngay`, tính từ lịch (không đồng hồ). Cùng công thức Tầng 1."""
    import datetime as dt
    return float((dt.date.fromisoformat(ngay).toordinal() - dt.date(1970, 1, 1).toordinal()) * 86400
                 + 15 * 3600 + 35 * 60)


def cham_diem_theo_ma(tt: ThiTruongGia2, ma: str, phien=None, cua_so: int | None = None) -> list[dict]:
    """Chấm MỘT mã ở các phiên có quyết định: mỗi phiên là MỘT lần `paper_runner._analyze` THẬT trên lịch sử cắt
    tới hết phiên ấy (`df.iloc[:t+1]`, gồm cả khởi động). `phien` = chỉ số phiên CÓ quyết định (0 = phiên đầu sau khởi
    động); mặc định mọi phiên. `cua_so` (BƯỚC 293): `None` = lịch sử MỞ RỘNG từ phiên đầu (như cũ); một số nguyên = chỉ
    `cua_so` dòng cuối của lịch sử (cửa sổ trượt), cho mẫu dài mà mỗi lần chấm không thấy nhiều dòng hơn một thị trường
    thật (đường quét thật cũng chỉ giữ ~784 phiên). Trả `[(chỉ số phiên, kết quả `_analyze`)]` đã rút thành dict ghi được:
    `{"phien", "ngay", "final_score", "recommendation", "score_breakdown", "key_reasons", "data_quality"}`."""
    import paper_runner as pr

    df = tt.gia[ma]
    chi_so = range(tt.so_phien) if phien is None else [int(k) for k in phien]
    ra = []
    with moi_truong_cham():
        for k in chi_so:
            if not 0 <= k < tt.so_phien:
                raise ValueError(f"phien {k} ngoai 0..{tt.so_phien - 1}")
            t = tt.so_khoi_dong + k
            dau = 0 if cua_so is None else max(0, t + 1 - int(cua_so))
            res = pr._analyze(ma, df.iloc[dau: t + 1], SAN_GIAO_DICH, tt.ngay[t])
            ra.append({"phien": k, "ngay": tt.ngay[t], "final_score": res["final_score"],
                       "recommendation": res["recommendation"], "score_breakdown": res["score_breakdown"],
                       "key_reasons": res["key_reasons"], "data_quality": res["data_quality"]})
            pr._xoa_cache_phan_tich()          # mỗi nến một khoá riêng, giữ lại chỉ ăn bộ nhớ (xem đầu file)
    return ra


def dong_quyet_dinh(tt: ThiTruongGia2, theo_ma: dict[str, list[dict]]) -> list[dict]:
    """Dòng đúng khuôn tab `decisions` từ kết quả chấm của từng mã: `seq` tăng theo (phiên, thứ tự mã trong `tt.ma`),
    `at` = 15:35 của ngày phiên, `acted` = 0, `skip_reason` rỗng. `score` là `int(final_score)` (cột INT của
    `record_decision`), `components` = `json.dumps(score_breakdown)`, `reasons` = `json.dumps(key_reasons)`."""
    theo_phien: dict[int, list[tuple[str, dict]]] = {}
    for ma in tt.ma:
        for r in theo_ma.get(ma, []):
            theo_phien.setdefault(r["phien"], []).append((ma, r))
    ra, seq = [], 0
    for k in sorted(theo_phien):
        for ma, r in theo_phien[k]:
            seq += 1
            ra.append({"seq": seq, "at": _gio_phien(r["ngay"]), "symbol": ma, "signal_date": r["ngay"],
                       "score": int(r["final_score"]), "recommendation": r["recommendation"], "acted": 0,
                       "skip_reason": "", "components": json.dumps(r["score_breakdown"], ensure_ascii=False),
                       "reasons": json.dumps(r["key_reasons"], ensure_ascii=False),
                       "data_quality": r["data_quality"]})
    return ra


def cham_diem(tt: ThiTruongGia2, ma=None, phien=None) -> list[dict]:
    """Chấm các mã `ma` (mặc định cả 60) ở các phiên `phien` (mặc định mọi phiên) → dòng `decisions`."""
    ds = tt.ma if ma is None else tuple(ma)
    return dong_quyet_dinh(tt, {m: cham_diem_theo_ma(tt, m, phien) for m in ds})


# ── P1 (mục 6, hàng P): dòng do `_analyze` thật sinh đúng khuôn và `data_quality` = OK ────────────────────────

def cot_bang_decisions() -> tuple[str, ...]:
    """Cột của bảng `decisions` THẬT, đọc từ một sổ `:memory:` do chính `PaperTradingJournal` dựng (không gõ tay)."""
    from paper_trading import PaperTradingJournal
    so = PaperTradingJournal(":memory:")
    try:
        return tuple(r[1] for r in so.db.execute("PRAGMA table_info(decisions)").fetchall())
    finally:
        so.db.close()


def kiem_p1(tt: ThiTruongGia2, dong: list[dict], so_ma: int, so_phien: int) -> list[str]:
    """Các vi phạm P1; rỗng = đạt. `so_ma` · `so_phien` là cỡ lượt chấm đã yêu cầu (đòi đủ từng ô, không thiếu không thừa).

    1. cột của mỗi dòng = cột bảng `decisions` thật, và kiểu: `seq` int, `at` float, `score` int (không bool) trong [5, 95];
    2. `components` đọc được và có đủ năm thành phần của `cb.THANH_PHAN`, số hữu hạn trong [0, 100];
    3. `data_quality` = "OK" ở mọi dòng (mức THẬT của `validate_ohlcv`, không phải hằng);
    4. đúng `so_ma × so_phien` dòng, mỗi (mã, ngày) một dòng, ngày thuộc phần CÓ quyết định (không có dòng khởi động);
    5. `cb.doc_quyet_dinh` (cái đọc của bước xác nhận) đọc hết, không bỏ dòng nào."""
    sai: list[str] = []
    cot = cot_bang_decisions()
    ngay_qd = set(tt.ngay_quyet_dinh)
    khoa = set()
    for d in dong:
        if tuple(sorted(d)) != tuple(sorted(cot)):
            sai.append(f"cot lech: {sorted(set(d) ^ set(cot))}")
            break
    for d in dong:
        if not isinstance(d["seq"], int) or isinstance(d["seq"], bool):
            sai.append(f"seq khong phai int: {d['seq']!r}")
        if not isinstance(d["at"], float):
            sai.append(f"at khong phai float: {d['at']!r}")
        if not isinstance(d["score"], int) or isinstance(d["score"], bool) or not 5 <= d["score"] <= 95:
            sai.append(f"score ngoai khuon: {d['score']!r}")
        try:
            tp = json.loads(d["components"])
            vals = [float(tp[k]) for k in cb.THANH_PHAN]
            if not all(np.isfinite(v) and 0.0 <= v <= 100.0 for v in vals):
                sai.append(f"thanh phan ngoai [0,100]: {d['symbol']} {d['signal_date']}")
        except (ValueError, TypeError, KeyError):
            sai.append(f"components hong: {d['symbol']} {d['signal_date']}")
        if d["data_quality"] != "OK":
            sai.append(f"data_quality {d['data_quality']!r}: {d['symbol']} {d['signal_date']}")
        if d["signal_date"] not in ngay_qd:
            sai.append(f"ngay ngoai phan co quyet dinh: {d['signal_date']}")
        k = (d["symbol"], d["signal_date"])
        if k in khoa:
            sai.append(f"trung khoa: {k}")
        khoa.add(k)
    if len(dong) != so_ma * so_phien:
        sai.append(f"so dong {len(dong)} != {so_ma} ma x {so_phien} phien")
    if dong:
        b = cb.doc_quyet_dinh(dong, tu_ngay=min(d["signal_date"] for d in dong))
        if len(b) != len(dong) or b.attrs.get("bo") != 0:
            sai.append(f"doc_quyet_dinh doc {len(b)}/{len(dong)} dong, bo {b.attrs.get('bo')}")
    return sai


# ── P2 (mục 4.9, hàng P): phép thử tương đương của thế giới giả ───────────────────────────────────────────

def vni_gia(tt: ThiTruongGia2) -> pd.DataFrame:
    """VN-INDEX GIẢ: chỉ số bình quân đều của 60 mã, `1000 · TB(giá / giá đầu)`, đủ mọi ngày (cả khởi động, để có MA50
    từ phiên đầu có quyết định). Mục 4.9 nói "chính nhân tố thị trường, cộng dồn"; `_sinh_loi` không trả nhân tố ấy ra
    ngoài và Lát này không sửa `thi_truong_gia.py`, nên dùng chỉ số bình quân đều — cùng hướng đi theo nhân tố thị
    trường nhưng KHÔNG phải nó (ghi chú thi công)."""
    gia = pd.DataFrame({m: df["close"].to_numpy() for m, df in tt.gia.items()})
    chi_so = 1000.0 * (gia / gia.iloc[0]).mean(axis=1)
    return pd.DataFrame({"time": list(tt.ngay), "close": chi_so.to_numpy()})


@contextlib.contextmanager
def vni_tiem_cho_duong_that(khung: pd.DataFrame):
    """Cho ĐƯỜNG THẬT (`run_session` không nhận nguồn) đọc VN-INDEX giả mà không chạm cache toàn cục: nạp MỘT BẢN SAO
    RIÊNG của `market_filter` (mã thật; một test khác có thể đã ghim `market_filter.is_vni_bullish` thành hàm hằng ở mức
    module), trỏ `get_vni_df` của bản sao vào `khung`, rồi đặt `market_filter.is_vni_bullish` = hàm của bản sao trong lúc
    chạy. Trả lại cả hai khi ra."""
    import importlib.util

    import market_filter as mf

    k = khung.copy()
    k["time"] = k["time"].astype(str)
    ban_sao_spec = importlib.util.spec_from_file_location("market_filter_ban_sao_tang2", mf.__file__)
    ban_sao = importlib.util.module_from_spec(ban_sao_spec)
    ban_sao_spec.loader.exec_module(ban_sao)
    k["vni_ma50"] = k["close"].rolling(ban_sao.MA_WINDOW).mean()
    ban_sao.get_vni_df = lambda: k
    cu = (mf.get_vni_df, mf.is_vni_bullish)
    mf.get_vni_df, mf.is_vni_bullish = (lambda: k), ban_sao.is_vni_bullish
    try:
        yield
    finally:
        mf.get_vni_df, mf.is_vni_bullish = cu


@contextlib.contextmanager
def cam_cache_toan_cuc():
    """Trong lúc phát lại, hai cửa đọc VN-INDEX toàn cục của `market_filter` NỔ nếu bị hỏi: phát lại chỉ được dùng nguồn
    TIÊM VÀO (khuôn `tests/test_san_dau.py`)."""
    import market_filter as mf

    def no(*a, **k):
        raise AssertionError("phát lại đã hỏi VN-INDEX toàn cục của market_filter")
    cu = (mf.is_vni_bullish, mf.get_vni_df)
    mf.is_vni_bullish, mf.get_vni_df = no, no
    try:
        yield
    finally:
        mf.is_vni_bullish, mf.get_vni_df = cu


def cau_hinh_mac_dinh():
    """Cấu hình của tài khoản giả: `CauHinhVao.tu_module()` làm cơ sở, ghi đè bằng `dataclasses.replace` (mục 4.9);
    KHÔNG cờ module nào bị gán. Ở Tầng 2 chưa ghi đè gì: ngưỡng, trần vốn, cổng VN-INDEX là của đường thật."""
    import dataclasses

    from paper_trading import CauHinhVao
    return dataclasses.replace(CauHinhVao.tu_module())


def chay_that_va_phat_lai(tt: ThiTruongGia2, ma=None, so_phien: int | None = None, cau_hinh=None,
                          dong_quyet_dinh_san=None) -> dict:
    """Phép thử tương đương MỘT thị trường (mục 4.9): `ma` (mặc định 60 mã) × `so_phien` phiên có quyết định đầu tiên.

    1. Dòng quyết định: `cham_diem` (hay `dong_quyet_dinh_san` nếu người gọi đã chấm) — các dòng mà Tầng 2 sinh.
    2. ĐƯỜNG THẬT: `paper_runner.run_session` từng (phiên, mã) trên lịch sử cắt tới phiên, chấm bằng `_analyze` THẬT ngay lúc
       chạy, sổ `:memory:`; cổng VN-INDEX đọc khung giả qua `vni_tiem_cho_duong_that`.
    3. PHÁT LẠI: `san_dau.phat_lai` từ dòng ở (1), nguồn tiêm `NguonDoRong(co_tu_gia(khung giá), vni=NguonVni(VN-INDEX giả))`,
       trong lúc `cam_cache_toan_cuc`.
    4. So bảng `trades` từng ô của `san_dau.COT_TUONG_DUONG`; kèm: điểm ở sổ `decisions` của đường thật bằng điểm của (1).
    Trả `{"thuc", "phat", "khac", "dem", "quyet_dinh", "diem_lech", "so_diem_so_duoc", "bi_chan_vni"}`; `khac` rỗng nghĩa là
    bằng nhau từng ô; `bi_chan_vni` là số quyết định đủ điểm mua mà cổng VN-INDEX chặn (0 nghĩa là phép thử không canh gì)."""
    import paper_runner as pr
    import san_dau as sd
    from paper_trading import PaperTradingJournal

    ds = tt.ma if ma is None else tuple(ma)
    n = tt.so_phien if so_phien is None else int(so_phien)
    cfg = cau_hinh_mac_dinh() if cau_hinh is None else cau_hinh
    phien = tuple(range(n))
    qd = cham_diem(tt, ma=ds, phien=phien) if dong_quyet_dinh_san is None else list(dong_quyet_dinh_san)
    vni = vni_gia(tt)
    gia = {m: tt.gia[m] for m in ds}

    so = PaperTradingJournal(":memory:")
    with moi_truong_cham(), vni_tiem_cho_duong_that(vni):
        for k in phien:
            t = tt.so_khoi_dong + k
            for m in ds:
                df = tt.gia[m]
                nen = {c: float(df[c].iloc[t]) for c in ("open", "high", "low", "close", "volume")}
                pr.run_session(so, m, df.iloc[: t + 1], nen, tt.ngay[t], SAN_GIAO_DICH, cau_hinh=cfg)
    cot = ", ".join(sd.COT_TUONG_DUONG)
    thuc = [dict(r) for r in so.db.execute(f"SELECT {cot} FROM trades ORDER BY id").fetchall()]
    ds_that = so.decisions()
    diem_that = {(d["symbol"], str(d["signal_date"])[:10]): d["score"] for d in ds_that}
    bi_chan = sum(1 for d in ds_that if str(d["skip_reason"]).startswith("VN-INDEX") and d["score"] >= cfg.buy_threshold)
    so.db.close()

    nguon = sd.NguonDoRong(sd.co_tu_gia(gia), vni=sd.NguonVni(vni))
    with cam_cache_toan_cuc():
        tk = sd.phat_lai(cfg, qd, gia, nguon, san_cua=lambda _m: SAN_GIAO_DICH,
                         ngay_bat_dau=tt.ngay_quyet_dinh[0], ngay_ket_thuc=tt.ngay_quyet_dinh[n - 1])
    phat, dem = tk.lenh(), tk.dem
    tk.dong()
    diem_ghi = {(d["symbol"], d["signal_date"]): d["score"] for d in qd}
    lech = sorted(k for k, v in diem_that.items() if diem_ghi.get(k) != v)
    return {"thuc": thuc, "phat": phat, "khac": sd.so_sanh_lenh(thuc, phat), "dem": dem, "quyet_dinh": qd,
            "diem_lech": lech, "so_diem_so_duoc": len(diem_that), "bi_chan_vni": bi_chan}


# ── P3 (mục 6, hàng P): lợi thế có ĐI QUA agent thật không ────────────────────────────────────────────────

def ic_thanh_phan(tt: ThiTruongGia2, dong: list[dict]) -> dict:
    """IC (tương quan hạng GỘP qua mọi cặp (phiên, mã) có nhãn, cùng `E.rho_hang` của máy đo) của từng thành phần điểm
    và của điểm cuối với nhãn `E.nhan_vuot_ro` (log lợi nhuận 21 phiên vượt rổ đều, vào ở đóng cửa T+1 — mục 3 "Nhãn khai
    thẳng"). Nhãn tính trên giá của MỌI mã của thị trường (rổ = cả 60), dù `dong` chỉ có một phần số mã.
    Trả `{"so_cap": n, "so_cap_khong_nhan": m, "ic": {tên: IC}}` với tên ∈ `cb.THANH_PHAN` ∪ {"score"}. KHÔNG dùng `z`,
    oracle hay `kappa`."""
    if not dong:
        raise ValueError("khong co dong quyet dinh")
    b = cb.doc_quyet_dinh(dong, tu_ngay=min(d["signal_date"] for d in dong))
    kh = {m: pd.DataFrame({"close": df["close"].to_numpy()}) for m, df in tt.gia.items()}
    nhan = E.nhan_vuot_ro(kh, cb.NHIP)
    vi_tri = {d: i for i, d in enumerate(tt.ngay)}
    hang = b["ngay"].map(vi_tri).to_numpy()
    y = np.array([nhan.iloc[h][s] for h, s in zip(hang, b["symbol"])], dtype=float)
    co = ~np.isnan(y)
    if not co.any():
        raise ValueError("khong cap nao co nhan")
    ic = {ten: E.rho_hang(b[ten].to_numpy(float)[co], y[co]) for ten in (*cb.THANH_PHAN, "score")}
    return {"so_cap": int(co.sum()), "so_cap_khong_nhan": int((~co).sum()), "ic": ic}
