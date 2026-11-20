"""Hiệu chuẩn MDE₈₀ và đường cong lực trên thị trường giả (C4 Lát 2, BƯỚC 289).

Đề bài: `docs/thiet-ke-c4-thi-truong-gia.md` mục 4.4 (MDE₈₀), 4.8 (hạt), 6 (tiêu chí),
7 (gác) và 8 ("Lát 2"). Đặc tả là nguồn duy nhất; đừng chép nó vào đây.

CÂU HỎI. Bước xác nhận THẬT (`cham_xac_nhan.cham` → `cham_bong.phan_quyet`, K = 3,
W = `cham_bong.MOC_DOC` = 252 phiên có nhãn, M = `thi_truong_gia.SO_MA` = 60 mã, ngưỡng
0,05/3 hai phía, 2000 hoán vị) trả `QUA` cho ứng viên G ở ΔIC_true nào, và bao nhiêu phần
trăm thị trường? MDE₈₀ = ΔIC_true nhỏ nhất của G mà ở đó ≥ 80% thị trường trả `QUA`.

CÁC BƯỚC (mọi bước là hàm THUẦN của `cau_hinh`; tái lập bằng `--kiem`)
  1. Oracle: ΔIC_true(G) theo κ trên lưới (trung bình `n_oracle_tim` mẫu oracle độc lập).
  2. Lưới lực: R thị trường mỗi κ của lưới, mỗi thị trường chạy BỘ BA G · Z · H khai tay ở
     ba tháng liên tiếp (mục 6) qua `cham_xac_nhan.cham`; đếm G = `QUA`.
  3. Khớp probit P(QUA) = Φ(a + b·ΔIC_true) → MDE₈₀ (kèm sai số bootstrap tham số).
  4. Bốn mức 0× · 0,5× · 1× · 2× MDE₈₀: dò nhị phân κ cho ΔIC_true(G) khớp mục tiêu trên
     mẫu oracle THỨ NHẤT, rồi ĐỐI CHIẾU trên mẫu oracle THỨ HAI độc lập (độ lệch ±10%).
  5. Lực thật ở từng mức (R thị trường mới) và bảng "ΔIC_true → tỷ lệ bắt".
  6. NULL smoke (κ = 0): số thị trường có ≥ 1 báo động, so với ngưỡng B1 (7,5%).

CHỈ DÒNG HẠT 1. Dòng 2, 3, 4 dành cho lượt chạy chính của Lát 5 sau khi tiêu chí được ký
(bất biến 7). Công cụ này KHÔNG có đối số `--luong`, mọi đường vào bộ sinh đi qua
`kiem_luong` (nổ với mọi dòng khác 1), và bản khai `cau_hinh` đọc từ file cũng bị kiểm.
Không có thị trường nào của dòng 2–4 được sinh, chạy hay đọc ở đây.

CHẠY
    ./.venv/Scripts/python.exe tools/hieu_chuan_thi_truong_gia.py --chay     # ghi docs/thi-truong-gia-hieu-chuan.json
    ./.venv/Scripts/python.exe tools/hieu_chuan_thi_truong_gia.py --kiem     # chạy lại, so với file đã ghi
    ./.venv/Scripts/python.exe tools/hieu_chuan_thi_truong_gia.py --tham-do --kappa 0.01 0.02 --so-thi-truong 8

Mã thoát: 0 đạt · 1 lệch (`--kiem`) hoặc độ lệch ±10% / NULL smoke trượt · 2 lỗi cấu hình.
KHÔNG chạm Sheets, `*.db`, sổ ứng viên thật; chỉ ghi `docs/thi-truong-gia-hieu-chuan.json`
(bằng `va_an_toan.ghi`) khi `--chay`.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as _dt
import importlib.util
import json
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from statistics import NormalDist

import numpy as np

for _luong_ra in (sys.stdout, sys.stderr):   # BƯỚC 129
    try:
        _luong_ra.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import cham_bong as cb  # noqa: E402
import cham_xac_nhan as cx  # noqa: E402
import thi_truong_gia as T  # noqa: E402

DUONG_KET_QUA = GOC / "docs" / "thi-truong-gia-hieu-chuan.json"
DUONG_CONG_CU = Path(__file__).resolve().parent

# ── hạt: CHỈ dòng 1 ──────────────────────────────────────────────────────────
LUONG = 1
LUONG_DUOC_PHEP = (1,)
#: Phần tử thứ 2–3 của hạt bootstrap `[LUONG, HAT_BOOTSTRAP, 7]`: ba phần tử như hạt oracle
#: nhưng phần tử cuối khác `T.HAT_SU_THAT` (= 1), nên không trùng hạt oracle nào.
HAT_BOOTSTRAP = 289

#: Chỉ số thị trường chia theo VAI TRÒ để các tập không bao giờ chạm nhau (mỗi tập một khối
#: 100.000; trong khối, điểm j của lưới chiếm 10.000 số). Hạt thị trường là `[LUONG, chi_so]`.
CHI_SO_GOC = {"luoi": 0, "muc": 100_000, "null": 200_000, "or_tim": 300_000,
              "or_kiem": 400_000, "tham_do": 900_000}
BUOC_DIEM = 10_000
TOI_DA_MOI_DIEM = BUOC_DIEM - 1

TEN_BO_BA = ("G", "Z", "H")
TEN_SPEC_BO_BA = {"G": T.TEN_SPEC_G, "Z": T.TEN_SPEC_Z, "H": T.TEN_SPEC_H}
NGUONG_B1 = 0.075                            # mục 6, tiêu chí B1: ≤ 7,5% thị trường NULL có ≥ 1 báo động
DUNG_SAI_MUC = 0.10                          # mục 8 Lát 2: κ khớp mục tiêu ±10%
LUC_MUC_TIEU = 0.80
DAI_TIN = 0.99                               # dải 99% quanh 80% của mục 6 "Báo cáo, không phán"
KHOA_BO_QUA_SO_SANH = ("moi_truong", "lenh", "thoi_gian_chay_giay")

#: Cấu hình CHÍNH THỨC của lượt chạy ghi vào `docs/thi-truong-gia-hieu-chuan.json`. Lưới κ chọn
#: SAU một lượt thăm dò nhỏ (`--tham-do`, vai trò `tham_do`, không vào bảng; 32 thị trường mỗi κ ở
#: 0 · 0,01 · 0,02 · 0,03 cho lực 0/32 · 9/32 · 30/32 · 32/32; 224 thị trường ở 0,016 cho 119/224): ghi ở STATE BƯỚC 289.
CAU_HINH_MAC_DINH = {
    "luong": LUONG,
    "luoi_kappa": [0.010, 0.012, 0.014, 0.016, 0.018, 0.020, 0.022, 0.024],
    "so_thi_truong_luoi": 500,
    "so_thi_truong_muc": 400,
    "so_thi_truong_null": 500,
    "he_so_muc": [0.5, 1.0, 2.0],
    "so_phien_oracle": T.SO_PHIEN_SU_THAT,
    "so_oracle_tim": 24,
    "so_oracle_kiem": 24,
    "tol_nhi_phan": 0.02,
    "toi_da_vong_nhi_phan": 24,
    "so_bootstrap": 500,
    "so_hoan_vi": cx.SO_HOAN_VI,
}


def kiem_luong(luong) -> None:
    """Cửa DUY NHẤT tới bộ sinh: chỉ dòng hạt 1. Nổ với 2, 3, 4, 5, 6… và với kiểu lạ."""
    if isinstance(luong, bool) or not isinstance(luong, (int, np.integer)) or int(luong) not in LUONG_DUOC_PHEP:
        raise ValueError(
            f"hieu chuan chi dung dong hat {LUONG_DUOC_PHEP}; nhan {luong!r}. Dong 2, 3, 4 danh cho luot "
            f"chay chinh cua Lat 5 sau khi tieu chi duoc ky (bat bien 7) — khong sinh, khong chay, khong doc.")


def chi_so_thi_truong(vai_tro: str, diem: int, thu_tu: int) -> int:
    """Chỉ số thị trường thứ `thu_tu` (từ 1) của điểm `diem` (từ 0) ở vai trò `vai_tro`."""
    if vai_tro not in CHI_SO_GOC:
        raise ValueError(f"vai tro la: {vai_tro!r}")
    if not (1 <= thu_tu <= TOI_DA_MOI_DIEM) or diem < 0:
        raise ValueError(f"thu_tu {thu_tu} / diem {diem} ngoai khoi")
    return CHI_SO_GOC[vai_tro] + diem * BUOC_DIEM + thu_tu


# ── một thị trường qua bước xác nhận THẬT ────────────────────────────────────

def _sinh(luong: int, chi_so: int, kappa: float):
    kiem_luong(luong)
    return T.sinh_thi_truong(luong, chi_so, float(kappa), co_su_that=False)


def keo_luc_gia(ngay_cuoi: str) -> str:
    """Giờ kéo giá của bảng giả: nửa đêm giờ VN của NGÀY SAU nến cuối. `phan_tich_bang_gia` đòi giờ kéo
    không sớm hơn nến cuối và nến cuối không còn dở — dải ngày giả trải tới 2102 (594 phiên từ 2100-01-04),
    nên một hằng số gõ tay cho "năm 2100" sẽ bị bảng giá thật từ chối."""
    return (_dt.date.fromisoformat(ngay_cuoi) + _dt.timedelta(days=1)).isoformat() + "T00:00:00+07:00"


def so_ung_vien_bo_ba() -> dict:
    """Sổ ứng viên GIẢ (một dict trong bộ nhớ, cùng khuôn sổ thật): G · Z · H khai ở ba tháng
    liên tiếp của `thi_truong_gia.dong_thoi_gian()`; đi qua `cham_bong.kiem_so_ung_vien`."""
    ngay = T.dong_thoi_gian()["khai_ngay"]
    ho = T.ho_spec_oracle()
    so = {"ung_vien": {ten: {"khai_ngay": ngay[i], "mo_ta": f"bo ba {ten}", "ly_do": f"bo ba {ten}",
                             "qua_sang": None, "spec": ho[TEN_SPEC_BO_BA[ten]]}
                       for i, ten in enumerate(TEN_BO_BA)}}
    cb.kiem_so_ung_vien(so)
    return so


def cham_mot_thi_truong(chi_so: int, kappa: float, luong: int = LUONG, so_hoan_vi: int = cx.SO_HOAN_VI) -> dict:
    """Sinh một thị trường (κ cho trước) và chấm bộ ba qua `cham_xac_nhan.cham`. Hạt hoán vị là
    mặc định thật `cx.HAT_RNG`. Trả số thuần (JSON được): trạng thái, p, Δ của từng ứng viên."""
    kiem_luong(luong)
    tt = _sinh(luong, chi_so, kappa)
    bang_gia = {"gia": tt.gia, "keo_luc": keo_luc_gia(tt.ngay[-1]), "nguon": {m: "vci" for m in tt.ma}}
    so = so_ung_vien_bo_ba()
    r = cx.cham(tt.dong_quyet_dinh(), so, bang_gia, cx.HAT_RNG, so_hoan_vi)
    ra = {"chi_so": int(chi_so), "kappa": float(kappa), "K": int(r["K"]), "nguong": float(r["nguong"])}
    for ten in TEN_BO_BA:
        c = r["chi_tiet"][ten]
        ra[ten] = {"trang_thai": c["trang_thai"], "n_phien": int(c["n_phien"]), "n_ma": int(c["n_ma"]),
                   "delta": float(c["delta"]), "p": float(c["p"])}
    return ra


def oracle_mot_mau(chi_so: int, kappa: float, so_phien: int, luong: int = LUONG) -> dict:
    """ΔIC_true của G · Z · H trên MỘT mẫu oracle `so_phien` phiên (hạt `[luong, chi_so, 1]`)."""
    kiem_luong(luong)
    s = T.tinh_su_that(luong, chi_so, float(kappa), so_phien)["spec"]
    return {ten: float(s[TEN_SPEC_BO_BA[ten]]["delta_ic"]) for ten in TEN_BO_BA}


def _viec_cham(a):
    return cham_mot_thi_truong(*a)


def _viec_oracle(a):
    return oracle_mot_mau(*a)


# ── chạy song song, kết quả KHÔNG phụ thuộc số tiến trình ─────────────────────

@contextlib.contextmanager
def tao_pool(so_tien_trinh: int):
    """`None` khi 1 tiến trình (chạy tuần tự). Tiến trình con kế thừa `sys.path` của cha lúc
    sinh (spawn), nên thư mục công cụ phải nằm trong đó suốt vòng đời của pool."""
    if so_tien_trinh <= 1:
        yield None
        return
    duong = str(DUONG_CONG_CU)
    them = duong not in sys.path
    if them:
        sys.path.insert(0, duong)
    try:
        with ProcessPoolExecutor(max_workers=so_tien_trinh) as pool:
            yield pool
    finally:
        if them and duong in sys.path:
            sys.path.remove(duong)


def _map(pool, ham, danh_sach: list) -> list:
    """Kết quả theo ĐÚNG thứ tự đầu vào, bất kể số tiến trình."""
    if pool is None:
        return [ham(a) for a in danh_sach]
    return list(pool.map(ham, danh_sach, chunksize=max(1, len(danh_sach) // 64)))


# ── thống kê thuần ────────────────────────────────────────────────────────────

_ND = NormalDist()


def wilson(k: int, n: int, do_tin: float = 0.95) -> tuple[float, float]:
    z = _ND.inv_cdf(0.5 + do_tin / 2.0)
    p = k / n
    mau = 1.0 + z * z / n
    tam = (p + z * z / (2 * n)) / mau
    nua = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / mau
    return tam - nua, tam + nua


def nhi_thuc_cdf(k: int, n: int, p: float) -> float:
    """P(X ≤ k), X ~ Nhị thức(n, p), cộng chính xác (không scipy)."""
    if k < 0:
        return 0.0
    return min(1.0, math.fsum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(0, min(k, n) + 1)))


def nhi_thuc_ppf(q: float, n: int, p: float) -> int:
    """k nhỏ nhất có P(X ≤ k) ≥ q."""
    t = 0.0
    for k in range(n + 1):
        t += math.comb(n, k) * p ** k * (1 - p) ** (n - k)
        if t >= q - 1e-12:
            return k
    return n


def dai_khop(n: int, p: float = LUC_MUC_TIEU, do_tin: float = DAI_TIN) -> tuple[int, int]:
    """Dải [thấp ; cao] số lần bắt được trong n thị trường nếu tỷ lệ thật là p (đối xứng đuôi)."""
    d = (1.0 - do_tin) / 2.0
    return nhi_thuc_ppf(d, n, p), nhi_thuc_ppf(1.0 - d, n, p)


def _phi(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def khop_probit(x, n, k) -> tuple[float, float]:
    """MLE của P = Φ(a + b·x) trên dữ liệu nhị thức nhóm (điểm cho điểm; Fisher scoring).
    Nổ nếu không hội tụ hoặc b ≤ 0 (lực không tăng theo lợi thế: máy đo hỏng)."""
    x, n, k = (np.asarray(v, float) for v in (x, n, k))
    p0 = np.clip((k + 0.5) / (n + 1.0), 1e-6, 1 - 1e-6)
    y = np.array([_ND.inv_cdf(float(v)) for v in p0])
    b, a = np.polyfit(x, y, 1)
    for _ in range(200):
        eta = a + b * x
        pp = np.clip(np.array([_ND.cdf(float(e)) for e in eta]), 1e-12, 1 - 1e-12)
        ph = np.array([_phi(float(e)) for e in eta])
        r = (k - n * pp) * ph / (pp * (1 - pp))
        w = n * ph * ph / (pp * (1 - pp))
        info = np.array([[w.sum(), (w * x).sum()], [(w * x).sum(), (w * x * x).sum()]])
        buoc = np.linalg.solve(info, np.array([r.sum(), (r * x).sum()]))
        a, b = a + buoc[0], b + buoc[1]
        if float(np.max(np.abs(buoc))) < 1e-11:
            break
    else:
        raise RuntimeError("probit khong hoi tu")
    if not (np.isfinite(a) and np.isfinite(b)) or b <= 0:
        raise RuntimeError(f"probit cho b = {b!r} (luc khong tang theo loi the)")
    return float(a), float(b)


def mde_tu_probit(a: float, b: float, luc: float = LUC_MUC_TIEU) -> float:
    return (_ND.inv_cdf(luc) - a) / b


def bootstrap_mde(x, n, k, so_lan: int) -> dict:
    """Sai số của MDE₈₀ do R hữu hạn: rút lại số lần bắt ~ Nhị thức(n, P đã khớp) rồi khớp lại.
    Hạt `[LUONG, HAT_BOOTSTRAP, 7]`. Lần không hội tụ bị ĐẾM, không bỏ lặng lẽ."""
    a0, b0 = khop_probit(x, n, k)
    p = np.array([_ND.cdf(a0 + b0 * float(v)) for v in x])
    rng = np.random.default_rng([LUONG, HAT_BOOTSTRAP, 7])
    mde, hong = [], 0
    for _ in range(so_lan):
        kk = rng.binomial(np.asarray(n, int), p)
        try:
            mde.append(mde_tu_probit(*khop_probit(x, n, kk)))
        except (RuntimeError, np.linalg.LinAlgError):
            hong += 1
    m = np.array(mde)
    return {"so_lan": so_lan, "so_lan_hong": hong, "se": float(m.std(ddof=1)),
            "khoang_95": [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))]}


def nhi_phan(f, muc_tieu: float, lo: float, hi: float, tol_tuong_doi: float, toi_da: int) -> tuple[float, float, list]:
    """Dò nhị phân κ ∈ [lo, hi] sao cho f(κ) khớp `muc_tieu` trong ±tol (tương đối); f đơn điệu tăng.
    Trả (κ, f(κ), vết). Nổ nếu khoảng không bao được mục tiêu hoặc không hội tụ sau `toi_da` vòng."""
    vet = []
    f_lo, f_hi = f(lo), f(hi)
    vet += [{"kappa": lo, "f": f_lo}, {"kappa": hi, "f": f_hi}]
    if not (f_lo <= muc_tieu <= f_hi):
        raise RuntimeError(f"khoang [{lo}, {hi}] khong bao muc tieu {muc_tieu}: f = [{f_lo}, {f_hi}]")
    for _ in range(toi_da):
        mid = 0.5 * (lo + hi)
        f_mid = f(mid)
        vet.append({"kappa": mid, "f": f_mid})
        if abs(f_mid - muc_tieu) <= tol_tuong_doi * abs(muc_tieu):
            return mid, f_mid, vet
        if f_mid < muc_tieu:
            lo = mid
        else:
            hi = mid
    raise RuntimeError(f"khong hoi tu sau {toi_da} vong (muc tieu {muc_tieu})")


# ── oracle trung bình ─────────────────────────────────────────────────────────

def oracle_trung_binh(pool, kappa: float, vai_tro: str, so_mau: int, so_phien: int) -> dict:
    """Trung bình ΔIC_true của G · Z · H trên `so_mau` mẫu oracle độc lập của `vai_tro`
    (`or_tim` hoặc `or_kiem`), cùng một tập hạt cho mọi κ (đường κ → ΔIC đơn điệu, trơn).
    `se` = độ lệch chuẩn giữa các mẫu / √số mẫu."""
    viec = [(chi_so_thi_truong(vai_tro, 0, i + 1), float(kappa), so_phien) for i in range(so_mau)]
    kq = _map(pool, _viec_oracle, viec)
    ra = {"kappa": float(kappa), "so_mau": so_mau}
    for ten in TEN_BO_BA:
        v = np.array([r[ten] for r in kq])
        ra[ten] = {"delta_ic": float(v.mean()), "se": float(v.std(ddof=1) / math.sqrt(so_mau))}
    return ra


def _dem(kq: list[dict]) -> dict:
    """Đếm từ kết quả của R thị trường."""
    n = len(kq)
    alpha = kq[0]["nguong"]
    d = {"R": n, "n_QUA_G": 0, "n_THUA_G": 0, "n_QUA_H": 0, "n_THUA_H": 0, "n_bao_dong_Z": 0,
         "n_co_bao_dong": 0, "n_co_QUA": 0}
    for r in kq:
        bd = {t: r[t]["p"] < alpha for t in TEN_BO_BA}
        d["n_QUA_G"] += r["G"]["trang_thai"] == "QUA"
        d["n_THUA_G"] += r["G"]["trang_thai"] == "THUA"
        d["n_QUA_H"] += r["H"]["trang_thai"] == "QUA"
        d["n_THUA_H"] += r["H"]["trang_thai"] == "THUA"
        d["n_bao_dong_Z"] += bd["Z"]
        d["n_co_bao_dong"] += any(bd.values())
        d["n_co_QUA"] += any(r[t]["trang_thai"] == "QUA" for t in TEN_BO_BA)
    d["nguong_p"] = alpha
    d["delta_do_G"] = float(np.mean([r["G"]["delta"] for r in kq]))
    d["se_delta_do_G"] = float(np.std([r["G"]["delta"] for r in kq], ddof=1) / math.sqrt(n))
    d["ty_le_bat_G"] = d["n_QUA_G"] / n
    d["khoang_wilson_95"] = list(wilson(d["n_QUA_G"], n))
    return d


def chay_thi_truong(pool, vai_tro: str, diem: int, kappa: float, so_thi_truong: int, so_hoan_vi: int) -> dict:
    viec = [(chi_so_thi_truong(vai_tro, diem, i + 1), float(kappa), LUONG, so_hoan_vi) for i in range(so_thi_truong)]
    return _dem(_map(pool, _viec_cham, viec))


# ── toàn bộ hiệu chuẩn ────────────────────────────────────────────────────────

def kiem_cau_hinh(ch: dict) -> None:
    kiem_luong(ch["luong"])
    thieu = [k for k in CAU_HINH_MAC_DINH if k not in ch]
    if thieu:
        raise ValueError(f"cau_hinh thieu khoa: {thieu}")
    for k in ("so_thi_truong_luoi", "so_thi_truong_muc", "so_thi_truong_null"):
        if not (2 <= ch[k] <= TOI_DA_MOI_DIEM):
            raise ValueError(f"{k} ngoai [2, {TOI_DA_MOI_DIEM}]")
    for k in ("so_oracle_tim", "so_oracle_kiem"):
        if not (2 <= ch[k] <= TOI_DA_MOI_DIEM):
            raise ValueError(f"{k} ngoai [2, {TOI_DA_MOI_DIEM}]")
    if len(ch["luoi_kappa"]) < 3 or sorted(ch["luoi_kappa"]) != list(ch["luoi_kappa"]) or ch["luoi_kappa"][0] <= 0:
        raise ValueError("luoi_kappa phai tang dan, > 0, it nhat 3 diem")
    if len(ch["luoi_kappa"]) > BUOC_DIEM // 100:   # số điểm lưới không được tràn sang khối khác
        raise ValueError("luoi_kappa qua dai")
    if 1.0 not in ch["he_so_muc"] or sorted(ch["he_so_muc"]) != list(ch["he_so_muc"]):
        raise ValueError("he_so_muc phai tang dan va co 1.0")


def chay(ch: dict, so_tien_trinh: int = 1, in_tien_do: bool = False) -> dict:
    """Toàn bộ hiệu chuẩn; hàm THUẦN của `ch`. `so_tien_trinh` chỉ đổi tốc độ, không đổi kết quả."""
    kiem_cau_hinh(ch)
    t0 = time.time()

    def bao(s):
        if in_tien_do:
            print(f"[{time.time() - t0:7.1f}s] {s}", flush=True)

    so = so_ung_vien_bo_ba()
    thong_so = {"K": cb.so_da_sang(so), "W": cb.MOC_DOC, "M": T.SO_MA, "alpha_k": cb.nguong(so),
                "so_hoan_vi": ch["so_hoan_vi"], "hat_hoan_vi": cx.HAT_RNG, "ung_vien": list(TEN_BO_BA),
                "spec": {t: TEN_SPEC_BO_BA[t] for t in TEN_BO_BA}, "khai_ngay": T.dong_thoi_gian()["khai_ngay"]}
    sp = ch["so_phien_oracle"]
    with tao_pool(so_tien_trinh) as pool:
        # 1 + 2 + 3: lưới lực
        luoi = []
        for j, kappa in enumerate(ch["luoi_kappa"]):
            orc = oracle_trung_binh(pool, kappa, "or_tim", ch["so_oracle_tim"], sp)
            lu = chay_thi_truong(pool, "luoi", j, kappa, ch["so_thi_truong_luoi"], ch["so_hoan_vi"])
            luoi.append({"kappa": kappa, "oracle": orc, **lu})
            bao(f"luoi {j + 1}/{len(ch['luoi_kappa'])} kappa={kappa}: dIC_true(G)={orc['G']['delta_ic']:.4f} "
                f"bat {lu['n_QUA_G']}/{lu['R']}")
        x = [r["oracle"]["G"]["delta_ic"] for r in luoi]
        n = [r["R"] for r in luoi]
        k = [r["n_QUA_G"] for r in luoi]
        a, b = khop_probit(x, n, k)
        mde = mde_tu_probit(a, b)
        boot = bootstrap_mde(x, n, k, ch["so_bootstrap"])
        bao(f"probit a={a:.4f} b={b:.3f} MDE80={mde:.4f} (bootstrap se {boot['se']:.4f})")

        # độ dốc đường κ → ΔIC (bình phương tối thiểu qua gốc) để chọn khoảng dò
        kap = np.array(ch["luoi_kappa"], float)
        doc = float((kap * np.array(x)).sum() / (kap * kap).sum())

        def f_tim(kappa: float) -> float:
            return oracle_trung_binh(pool, kappa, "or_tim", ch["so_oracle_tim"], sp)["G"]["delta_ic"]

        # 4 + 5: bốn mức
        muc = []
        for h, he in enumerate([0.0] + list(ch["he_so_muc"])):
            muc_tieu = he * mde
            if he == 0.0:
                kappa, vet = 0.0, []
            else:
                lo, hi = 0.0, 2.0 * muc_tieu / doc
                for _ in range(10):
                    if f_tim(hi) >= muc_tieu:
                        break
                    hi *= 1.5
                kappa, _, vet = nhi_phan(f_tim, muc_tieu, lo, hi, ch["tol_nhi_phan"], ch["toi_da_vong_nhi_phan"])
            tim = oracle_trung_binh(pool, kappa, "or_tim", ch["so_oracle_tim"], sp)
            kiem = oracle_trung_binh(pool, kappa, "or_kiem", ch["so_oracle_kiem"], sp)
            lech = None if he == 0.0 else (kiem["G"]["delta_ic"] - muc_tieu) / muc_tieu
            if he == 0.0:
                dat = abs(kiem["G"]["delta_ic"]) < 2.0 * kiem["G"]["se"]
            else:
                dat = abs(lech) <= DUNG_SAI_MUC
            lu = chay_thi_truong(pool, "muc", h, kappa, ch["so_thi_truong_muc"], ch["so_hoan_vi"]) if he > 0 else None
            muc.append({"he_so": he, "muc_tieu_delta_ic": muc_tieu, "kappa": kappa, "vet_nhi_phan": vet,
                        "oracle_tim": tim, "oracle_kiem": kiem, "lech_tuong_doi_tren_mau_kiem": lech,
                        "dat_dung_sai_10pct": bool(dat), "luc": lu})
            bao(f"muc {he}x: kappa={kappa:.5f} muc_tieu={muc_tieu:.4f} kiem={kiem['G']['delta_ic']:.4f} "
                f"lech={'-' if lech is None else format(lech, '+.1%')}"
                + ("" if lu is None else f" bat {lu['n_QUA_G']}/{lu['R']}"))

        # 6: NULL smoke
        nl = chay_thi_truong(pool, "null", 0, 0.0, ch["so_thi_truong_null"], ch["so_hoan_vi"])
        bao(f"NULL: {nl['n_co_bao_dong']}/{nl['R']} thi truong co >= 1 bao dong")

    R_null = nl["R"]
    toi_da = int(math.floor(NGUONG_B1 * R_null + 1e-9))
    p0 = 1.0 - (1.0 - thong_so["alpha_k"]) ** len(TEN_BO_BA)   # mức danh nghĩa nếu ba phép thử độc lập
    null_smoke = {**nl, "nguong_B1": NGUONG_B1, "toi_da_cho_phep": toi_da,
                  "dat": bool(nl["n_co_bao_dong"] <= toi_da), "ty_le_bao_dong": nl["n_co_bao_dong"] / R_null,
                  "muc_danh_nghia_neu_doc_lap": p0, "ky_vong_bao_dong": p0 * R_null,
                  "p_nhi_thuc_tu_so_do_tro_len": 1.0 - nhi_thuc_cdf(nl["n_co_bao_dong"] - 1, R_null, p0)}

    # bảng "ΔIC_true → tỷ lệ bắt": mọi điểm đã đo, theo ΔIC_true tăng. Điểm của lưới dùng ΔIC_true
    # của mẫu `or_tim`; điểm của bốn mức dùng mẫu `or_kiem` (độc lập với việc dò κ).
    bang = [{"nguon": "luoi", "kappa": r["kappa"], "delta_ic_true": r["oracle"]["G"]["delta_ic"],
             "se_delta_ic_true": r["oracle"]["G"]["se"], "R": r["R"], "n_QUA_G": r["n_QUA_G"],
             "ty_le_bat_G": r["ty_le_bat_G"], "khoang_wilson_95": r["khoang_wilson_95"],
             "n_QUA_H": r["n_QUA_H"], "n_bao_dong_Z": r["n_bao_dong_Z"], "delta_do_G": r["delta_do_G"]}
            for r in luoi]
    for m in muc:
        if m["luc"] is None:
            continue
        lu = m["luc"]
        bang.append({"nguon": f"muc {m['he_so']}x", "kappa": m["kappa"],
                     "delta_ic_true": m["oracle_kiem"]["G"]["delta_ic"], "se_delta_ic_true": m["oracle_kiem"]["G"]["se"],
                     "R": lu["R"], "n_QUA_G": lu["n_QUA_G"], "ty_le_bat_G": lu["ty_le_bat_G"],
                     "khoang_wilson_95": lu["khoang_wilson_95"], "n_QUA_H": lu["n_QUA_H"],
                     "n_bao_dong_Z": lu["n_bao_dong_Z"], "delta_do_G": lu["delta_do_G"]})
    bang.sort(key=lambda r: (r["delta_ic_true"], r["nguon"]))

    m1 = next(m for m in muc if m["he_so"] == 1.0)
    thap, cao = dai_khop(m1["luc"]["R"])
    kiem_1x = {"R": m1["luc"]["R"], "n_QUA_G": m1["luc"]["n_QUA_G"], "dai_99_quanh_80": [thap, cao],
               "trong_dai": bool(thap <= m1["luc"]["n_QUA_G"] <= cao)}
    return {
        "buoc": 289, "muc_tieu": "C4 Lat 2 — hieu chuan MDE80 va duong cong luc (dong hat 1)",
        "cau_hinh": ch, "thong_so_vong": thong_so,
        "mde80": {"delta_ic_true": mde, "probit": {"a": a, "b": b}, "bootstrap": boot,
                  "do_doc_kappa_delta_ic": doc,
                  "kappa_tuong_ung": next(m["kappa"] for m in muc if m["he_so"] == 1.0)},
        "luoi": luoi, "muc": muc, "bang_ic_true_ty_le_bat": bang,
        "kiem_1x_trong_dai_99": kiem_1x, "null_smoke": null_smoke,
        "dat_dung_sai_10pct_ca_bon_muc": all(m["dat_dung_sai_10pct"] for m in muc),
        "moi_truong": {"python": sys.version.split()[0], "numpy": np.__version__, "so_tien_trinh": so_tien_trinh},
        "thoi_gian_chay_giay": round(time.time() - t0, 1),
    }


# ── ghi và kiểm lại ──────────────────────────────────────────────────────────

def _nap_va_an_toan():
    s = importlib.util.spec_from_file_location("va_an_toan_hieu_chuan", DUONG_CONG_CU / "va_an_toan.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def ghi_ket_qua(ket: dict, duong: Path = DUONG_KET_QUA) -> None:
    _nap_va_an_toan().ghi(duong, json.dumps(ket, ensure_ascii=False, indent=1) + "\n")


def doc_ket_qua(duong: Path = DUONG_KET_QUA) -> dict:
    ket = json.loads(Path(duong).read_text(encoding="utf-8"))
    kiem_luong(ket["cau_hinh"]["luong"])   # file bị sửa sang dòng khác thì nổ TRƯỚC khi chạy gì
    return ket


def so_sanh(cu, moi, duong: str = "", rel: float = 1e-6, ab: float = 1e-9) -> list[str]:
    """Danh sách chỗ lệch. Số nguyên, chuỗi, bool phải BẰNG; số thực lệch trong dung sai là bằng
    (`sum()` của Python 3.12+ cộng có bù, 3.11 thì không — `docs/thiet-ke-c4-thi-truong-gia.md` mục 15 khoản 9)."""
    lech: list[str] = []
    if isinstance(cu, dict) and isinstance(moi, dict):
        for k in sorted(set(cu) | set(moi)):
            if duong == "" and k in KHOA_BO_QUA_SO_SANH:
                continue
            if k not in cu or k not in moi:
                lech.append(f"{duong}/{k}: chi co o mot ben")
            else:
                lech += so_sanh(cu[k], moi[k], f"{duong}/{k}", rel, ab)
    elif isinstance(cu, list) and isinstance(moi, list):
        if len(cu) != len(moi):
            lech.append(f"{duong}: dai {len(cu)} != {len(moi)}")
        else:
            for i, (a, b) in enumerate(zip(cu, moi)):
                lech += so_sanh(a, b, f"{duong}[{i}]", rel, ab)
    elif isinstance(cu, float) or isinstance(moi, float):
        if not (isinstance(cu, (int, float)) and isinstance(moi, (int, float))
                and not isinstance(cu, bool) and not isinstance(moi, bool)
                and math.isclose(cu, moi, rel_tol=rel, abs_tol=ab)):
            lech.append(f"{duong}: {cu!r} != {moi!r}")
    elif type(cu) is not type(moi) or cu != moi:
        lech.append(f"{duong}: {cu!r} != {moi!r}")
    return lech


def pearson_chi2(ket: dict) -> tuple[float, int]:
    """χ² Pearson của mọi điểm đã đo (lưới và ba mức) so với đường probit đã khớp, và số bậc tự do
    (số điểm trừ hai tham số). Chỉ đọc số đếm đã ghi."""
    a, b = ket["mde80"]["probit"]["a"], ket["mde80"]["probit"]["b"]
    t = 0.0
    for r in ket["bang_ic_true_ty_le_bat"]:
        p = min(max(_ND.cdf(a + b * r["delta_ic_true"]), 1e-12), 1.0 - 1e-12)
        t += (r["n_QUA_G"] - r["R"] * p) ** 2 / (r["R"] * p * (1.0 - p))
    return t, len(ket["bang_ic_true_ty_le_bat"]) - 2


def tong_hop_Z_H(ket: dict) -> dict:
    """Báo động của Z và số lần H được `QUA` ở MỌI thị trường có lợi thế (lưới + ba mức)."""
    co = list(ket["luoi"]) + [m["luc"] for m in ket["muc"] if m["luc"] is not None]
    n = sum(r["R"] for r in co)
    z = sum(r["n_bao_dong_Z"] for r in co)
    return {"R": n, "n_bao_dong_Z": z, "ty_le_bao_dong_Z": z / n, "n_QUA_H": sum(r["n_QUA_H"] for r in co),
            "danh_nghia_moi_ung_vien": ket["thong_so_vong"]["alpha_k"]}


def in_bang(ket: dict) -> None:
    print("ΔIC_true(G)   κ         R    bắt G   tỷ lệ  [Wilson 95%]        nguồn")
    for r in ket["bang_ic_true_ty_le_bat"]:
        lo, hi = r["khoang_wilson_95"]
        print(f"{r['delta_ic_true']:+.4f}±{r['se_delta_ic_true']:.4f}  {r['kappa']:.5f}  {r['R']:4d}  "
              f"{r['n_QUA_G']:4d}  {r['ty_le_bat_G']:6.1%}  [{lo:5.1%} ; {hi:5.1%}]  {r['nguon']}")
    m = ket["mde80"]
    print(f"MDE80 = {m['delta_ic_true']:.4f} (bootstrap se {m['bootstrap']['se']:.4f}, "
          f"95% {m['bootstrap']['khoang_95'][0]:.4f}…{m['bootstrap']['khoang_95'][1]:.4f})")
    for mc in ket["muc"]:
        lech = mc["lech_tuong_doi_tren_mau_kiem"]
        print(f"  {mc['he_so']}x: kappa={mc['kappa']:.5f} muc tieu {mc['muc_tieu_delta_ic']:.4f} · mau kiem "
              f"{mc['oracle_kiem']['G']['delta_ic']:.4f}±{mc['oracle_kiem']['G']['se']:.4f} · lech "
              f"{'-' if lech is None else format(lech, '+.1%')} · {'ĐẠT' if mc['dat_dung_sai_10pct'] else 'TRƯỢT'}")
    ns = ket["null_smoke"]
    print(f"NULL smoke: {ns['n_co_bao_dong']}/{ns['R']} có ≥ 1 báo động ({ns['ty_le_bao_dong']:.1%}); "
          f"cho phép ≤ {ns['toi_da_cho_phep']} ({NGUONG_B1:.1%}) → {'ĐẠT' if ns['dat'] else 'TRƯỢT'}")
    chi2, bac = pearson_chi2(ket)
    zh = tong_hop_Z_H(ket)
    print(f"khớp probit: Pearson χ² = {chi2:.2f} trên ~{bac} bậc tự do")
    print(f"Z báo động {zh['n_bao_dong_Z']}/{zh['R']} = {zh['ty_le_bao_dong_Z']:.2%} (danh nghĩa mỗi ứng viên "
          f"{zh['danh_nghia_moi_ung_vien']:.2%}); H được QUA {zh['n_QUA_H']}/{zh['R']} thị trường có lợi thế")
    k1 = ket["kiem_1x_trong_dai_99"]
    print(f"1x: bắt {k1['n_QUA_G']}/{k1['R']}, dải 99% quanh 80% = {k1['dai_99_quanh_80']} → "
          f"{'trong dải' if k1['trong_dai'] else 'NGOÀI dải'}")


def tham_do(kappas: list[float], so_thi_truong: int, so_tien_trinh: int) -> int:
    """Thăm dò NHỎ để chọn lưới κ: vai trò `tham_do`, không vào bảng, không ghi file."""
    with tao_pool(so_tien_trinh) as pool:
        for j, kappa in enumerate(kappas):
            t0 = time.time()
            orc = oracle_trung_binh(pool, kappa, "or_tim", 4, T.SO_PHIEN_SU_THAT)
            lu = chay_thi_truong(pool, "tham_do", j, kappa, so_thi_truong, cx.SO_HOAN_VI)
            print(f"kappa={kappa}: dIC_true(G)={orc['G']['delta_ic']:.4f}±{orc['G']['se']:.4f}  bat G "
                  f"{lu['n_QUA_G']}/{lu['R']}  H QUA {lu['n_QUA_H']}  Z bao dong {lu['n_bao_dong_Z']}  "
                  f"do={lu['delta_do_G']:.4f}  [{time.time() - t0:.0f}s]", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    nhom = ap.add_mutually_exclusive_group(required=True)
    nhom.add_argument("--chay", action="store_true", help="chạy và ghi file kết quả hiệu chuẩn")
    nhom.add_argument("--kiem", action="store_true", help="chạy lại theo cau_hinh trong file, so với file")
    nhom.add_argument("--in-bang", action="store_true", help="in bảng đã ghi (không chạy lại thị trường nào)")
    nhom.add_argument("--tham-do", action="store_true", help="thăm dò nhỏ để chọn lưới κ (không ghi file)")
    ap.add_argument("--tien-trinh", type=int, default=max(1, os.cpu_count() - 2))
    ap.add_argument("--kappa", type=float, nargs="*", default=[0.01, 0.02])
    ap.add_argument("--so-thi-truong", type=int, default=8)
    a = ap.parse_args(argv)
    if a.in_bang:
        in_bang(doc_ket_qua())
        return 0
    if a.tham_do:
        return tham_do(a.kappa, a.so_thi_truong, a.tien_trinh)
    if a.chay:
        ket = chay(dict(CAU_HINH_MAC_DINH), a.tien_trinh, in_tien_do=True)
        ket["lenh"] = "./.venv/Scripts/python.exe tools/hieu_chuan_thi_truong_gia.py --chay"
        ghi_ket_qua(ket)
        in_bang(ket)
        print(f"đã ghi {DUONG_KET_QUA.relative_to(GOC).as_posix()} ({ket['thoi_gian_chay_giay']} s)")
        return 0 if ket["dat_dung_sai_10pct_ca_bon_muc"] and ket["null_smoke"]["dat"] else 1
    cu = doc_ket_qua()
    moi = chay(cu["cau_hinh"], a.tien_trinh, in_tien_do=True)
    lech = so_sanh(cu, moi)
    if lech:
        print(f"LỆCH {len(lech)} chỗ, ví dụ:")
        for s in lech[:20]:
            print("  ", s)
        return 1
    print(f"OK — chạy lại cho đúng bảng đã ghi ({moi['thoi_gian_chay_giay']} s, {a.tien_trinh} tiến trình)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
