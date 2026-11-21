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

Module KHÔNG sửa, KHÔNG nhập ngược từ đường thật (gác G2), không đồng hồ, không mạng, không file, không sổ khác `:memory:`.
"""
from __future__ import annotations

import contextlib
import json
from dataclasses import dataclass

import numpy as np
import pandas as pd

import cham_bong as cb
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


def sinh_thi_truong_2(luong: int, chi_so: int, kappa: float, so_phien: int | None = None,
                      so_khoi_dong: int = SO_PHIEN_KHOI_DONG) -> ThiTruongGia2:
    """Sinh MỘT thị trường Tầng 2. `so_phien` mặc định = `T.dong_thoi_gian()["tong"]` (phiên có quyết định);
    `so_khoi_dong` phiên khởi động đứng TRƯỚC chúng. Hạt `default_rng([luong, chi_so])` như Tầng 1 (mục 4.8).

    Ngày giả liền một mạch từ `T.NGAY_DAU` (gác G5): khởi động chiếm `so_khoi_dong` phiên đầu, nên phiên có quyết định
    đầu tiên rơi vào ngày thứ `so_khoi_dong + 1` của lịch, không phải ngày `T.NGAY_DAU`."""
    T._kiem_hat(luong, chi_so)
    if kappa < 0:
        raise ValueError("kappa phai >= 0")
    if so_khoi_dong < 0:
        raise ValueError("so_khoi_dong phai >= 0")
    n_qd = T.dong_thoi_gian()["tong"] if so_phien is None else int(so_phien)
    n = so_khoi_dong + n_qd
    mau = _sinh_ohlcv_loi(np.random.default_rng([luong, chi_so]), n, float(kappa))
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


def cham_diem_theo_ma(tt: ThiTruongGia2, ma: str, phien=None) -> list[dict]:
    """Chấm MỘT mã ở các phiên có quyết định: mỗi phiên là MỘT lần `paper_runner._analyze` THẬT trên lịch sử cắt
    tới hết phiên ấy (`df.iloc[:t+1]`, gồm cả khởi động). `phien` = chỉ số phiên CÓ quyết định (0 = phiên đầu sau khởi
    động); mặc định mọi phiên. Trả `[(chỉ số phiên, kết quả `_analyze`)]` đã rút thành dict ghi được:
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
            res = pr._analyze(ma, df.iloc[: t + 1], SAN_GIAO_DICH, tt.ngay[t])
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
