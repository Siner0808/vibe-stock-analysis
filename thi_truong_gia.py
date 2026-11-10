"""Thị trường giả có lợi thế cài sẵn — Tầng 1 (C4, Lát 1, BƯỚC 261).

Đề bài: `docs/thiet-ke-c4-thi-truong-gia.md` mục 4 (đặc tả là nguồn duy nhất; đừng
chép nó vào đây). Module này CHỈ làm phần Lát 1 của mục 8: bộ sinh Tầng 1, thị
trường NULL và oracle. KHÔNG có bước xác nhận, bộ đề xuất, nâng cấp hay vòng nào
(Lát 2–5), không Tầng 2 (`paper_runner._analyze`, `san_dau.phat_lai`).

Một thị trường là MỘT hàm thuần của `(luong, chi_so, kappa)`: `numpy.random.
default_rng([luong, chi_so])` (mục 4.8), không đồng hồ, không mạng, không file, không
sổ. Ngày giả nằm ở dải 2100-01-04 trở đi (mục 4.1 khoản 2).

    nhân tố ẩn z (AR(1))  ──► chỉ `volume_score` đọc z (cộng nhiễu riêng)
    z ở phiên s−2 ──► kỳ vọng cài sẵn của lợi nhuận phiên s = κ·z/21 (mục 4.2)
    ⇒ nhãn của phiên T (log lợi nhuận T+2…T+22, vượt rổ) có kỳ vọng ≈ κ·TB(z quanh T)

`kappa` chỉ đi vào ĐÚNG MỘT chỗ: số hạng kỳ vọng của lợi nhuận. Mọi con số ngẫu nhiên
khác không phụ thuộc nó, nên một thị trường NULL (κ = 0) và một thị trường có lợi thế
CÙNG hạt có CÙNG dòng quyết định và chỉ khác giá — bất biến có test.

ORACLE (mục 4.5): `su_that` tính ΔIC_true của từng spec trên một mẫu dài CÙNG tham số
nhưng hạt riêng, bằng chính `E.rho_hang` và chính `E.nhan_vuot_ro` của máy đo. Nó mang
theo thị trường để (a) đặt κ ở Lát 2, (b) chấm đúng/sai sau khi vòng đã quyết. Nó
KHÔNG BAO GIỜ được gọi từ vòng học (gác G4 ở Lát 3).
"""
from __future__ import annotations

import datetime as _dt
import json
from dataclasses import dataclass

import numpy as np
import pandas as pd

import cham_bong as cb
import experiment_tran_dac_trung as E
import san_dau as sd

# ── dải ngày giả (mục 4.1 khoản 2 · gác G5) ──────────────────────────────────
NGAY_DAU = "2100-01-04"  # thứ Hai; `lich_giao_dich` chỉ phủ 2026 nên mọi ngày giả là "ngoài lịch"

# ── mô hình sinh (mục 4.2) — KHAI trước, sửa là sửa đặc tả và đổi dòng hạt ──
SO_MA = 60                    # ≥ cb.MIN_MA = 40; ít hơn 71 mã thật để bảng không tưởng là bản chép
SO_NGANH = 6
BIEN_NGAY = 0.07              # biên HOSE: lợi nhuận ngày kẹp ±7%
SIGMA_THI_TRUONG = 0.010      # độ lệch chuẩn ngày của nhân tố thị trường — CHƯA hiệu chuẩn vào giá thật
SIGMA_NGANH = 0.007           # ... của mỗi nhân tố ngành — CHƯA hiệu chuẩn
SIGMA_RIENG = 0.015           # ... của phần riêng mã (GARCH-t) — CHƯA hiệu chuẩn
NU_BUOC_T = sd.GARCH_NU       # bậc tự do của bước ngẫu nhiên t của thị trường và ngành (cùng ν đã đo ở BƯỚC 248)
PHI_Z = 0.97                  # hệ số ngày của AR(1) của z (mục 4.2: "φ_z khai ở Lát 1") — KHAI, chưa đo
PHI_THANH_PHAN = 0.90         # hệ số ngày AR(1) của nhiễu riêng từng thành phần (chỉ báo bền theo ngày) — KHAI, chưa đo
HE_SO_Z = 0.5                 # b: phần của z trong tiềm ẩn của thành phần mang (a² + b² = 1)
SIGMA_TRANH_LUAN = 0.45       # nhiễu tranh luận (điểm); kẹp ±TRAN_TRANH_LUAN, đúng cỡ ±0,9 điểm của CLAUDE.md
TRAN_TRANH_LUAN = 0.9
GIA_DAU = (10.0, 50.0)        # nghìn đồng, như nguồn thật (để `price_multiplier` chạy đúng ở Tầng 2)
DIEM_SAN, DIEM_TRAN = 5.0, 95.0  # `master_agent`: pre_debate_score kẹp [5, 95]

THANH_PHAN_MANG = "volume_score"   # chọn TRƯỚC, không chọn theo kết quả (mục 4.2)
#: Bộ trọng số mặc định `master_agent.py` :195, theo thứ tự `cb.THANH_PHAN`.
TRONG_SO_MAC_DINH = {"trend_score": 0.25, "momentum_score": 0.25, "volume_score": 0.20,
                     "sr_score": 0.15, "risk_score": 0.15}
#: Số nấc và biên ĐÃ ĐO của từng thành phần (`MO-XE-KIEN-TRUC.md`, bảng Tầng 2, cửa sổ dài 31/08/2026).
#: Giá trị các nấc là chuỗi ĐỀU từ biên dưới tới biên trên, làm tròn một chữ số thập phân như
#: `score_breakdown`; "đều" là GIẢ ĐỊNH (bảng chỉ cho số nấc và hai biên).
NAC = {"trend_score": (10, 0.0, 100.0), "momentum_score": (17, 4.2, 95.8),
       "volume_score": (13, 25.0, 100.0), "sr_score": (7, 6.2, 100.0),
       "risk_score": (8, 10.0, 45.0)}
#: Tương quan HẠNG giữa các thành phần (`MO-XE-KIEN-TRUC.md`, "Tương quan hạng giữa các cặp"),
#: theo thứ tự trend · momentum · volume · sr · risk.
TUONG_QUAN_HANG = np.array([
    [1.00, 0.76, 0.44, 0.09, 0.00],
    [0.76, 1.00, 0.49, 0.34, 0.02],
    [0.44, 0.49, 1.00, 0.09, 0.07],
    [0.09, 0.34, 0.09, 1.00, -0.08],
    [0.00, 0.02, 0.07, -0.08, 1.00],
])

# ── dòng thời gian (mục 4.6) ─────────────────────────────────────────────────
SO_PHIEN_DA_NHIN = 126        # S: cửa sổ bộ đề xuất được nhìn
SO_PHIEN_TIEN_VE_TRUOC = 126  # F: cửa sổ đo lợi ích sau nâng cấp
SO_UNG_VIEN_KHAI = 3          # ba ứng viên, mỗi tháng dương lịch một (cb.TRAN_MOI_THANG = 1)
DO_TRE_NHAN = cb.NHIP + 1     # nhãn của phiên t cần giá đóng cửa tới t + 22 (E.nhan_vuot_ro: dịch −h−1)

# ── oracle (mục 4.5) ─────────────────────────────────────────────────────────
SO_PHIEN_SU_THAT = 5000
SO_KHOI_SU_THAT = 10          # số khối liền nhau để ước sai số Monte Carlo của ΔIC_true
HAT_SU_THAT = 1               # phần tử thứ ba của hạt oracle: [luong, chi_so, HAT_SU_THAT]
TEN_SPEC_G, TEN_SPEC_Z, TEN_SPEC_H = "mono_volume_score", "doi_cho_trend_sr", "bo_volume_score"


# ── lịch giả ─────────────────────────────────────────────────────────────────

def lich_phien(so_phien: int) -> tuple[str, ...]:
    """`so_phien` ngày làm việc thứ Hai–Sáu liên tiếp từ `NGAY_DAU`, không ngày nghỉ."""
    ra: list[str] = []
    d = _dt.date.fromisoformat(NGAY_DAU)
    while len(ra) < so_phien:
        if d.weekday() < 5:
            ra.append(d.isoformat())
        d += _dt.timedelta(days=1)
    return tuple(ra)


def dong_thoi_gian() -> dict:
    """Dòng thời gian Tầng 1, SUY RA từ lịch và các hằng số — không gõ tay (mục 4.6).

    * Cửa sổ đã nhìn: phiên 0…S−1.
    * Ngày khai thứ i: phiên đầu tiên của tháng dương lịch thứ i kể từ tháng chứa phiên S−1.
    * Ứng viên đọc ở `cb.MOC_DOC` phiên CÓ NHÃN đầu tiên từ ngày khai (`>=`): phiên có nhãn thứ
      252 là `khai + 251`, nhãn của nó cần giá tới `khai + 251 + 22`; đó là phiên đọc.
    * Nâng cấp hiệu lực từ phiên sau phiên đọc; cửa sổ tiến-về-trước F phiên sau đó, mỗi phiên
      cần nhãn nên cần thêm 22 phiên giá. Tổng số phiên tính trên ứng viên khai SAU CÙNG
      (trường hợp dài nhất).
    """
    lich = lich_phien(12 * 21 + SO_PHIEN_DA_NHIN)  # dư xa: ba tháng khai nằm trong 5 tháng đầu sau cửa sổ
    thang = [(_dt.date.fromisoformat(d).year, _dt.date.fromisoformat(d).month) for d in lich]
    nam, th = thang[SO_PHIEN_DA_NHIN - 1]
    khai = []
    for i in range(1, SO_UNG_VIEN_KHAI + 1):
        m0 = th - 1 + i
        muc = (nam + m0 // 12, m0 % 12 + 1)
        khai.append(thang.index(muc))
    doc = [k + (cb.MOC_DOC - 1) + DO_TRE_NHAN for k in khai]
    tong = doc[-1] + SO_PHIEN_TIEN_VE_TRUOC + DO_TRE_NHAN + 1
    return {"S": SO_PHIEN_DA_NHIN, "F": SO_PHIEN_TIEN_VE_TRUOC, "khai": khai,
            "khai_ngay": [lich[k] for k in khai], "doc": doc, "tong": tong}


# ── họ ứng viên đối chứng (mục 4.3) ──────────────────────────────────────────

def _spec(trong_so: dict) -> dict:
    s = {"loai": "trong_so", "trong_so": {k: float(trong_so[k]) for k in cb.THANH_PHAN if k in trong_so}}
    cb.kiem_spec(s)
    return s


def ho_spec_f() -> dict[str, dict]:
    """Họ F = 11 spec: 5 mono, 5 bỏ-một (bộ mặc định bỏ một thành phần, chuẩn hoá về tổng 1), 1 đều."""
    ho = {}
    for c in cb.THANH_PHAN:
        ho[f"mono_{c}"] = _spec({c: 1.0})
    for c in cb.THANH_PHAN:
        con = {k: w for k, w in TRONG_SO_MAC_DINH.items() if k != c}
        tong = sum(con.values())
        ho[f"bo_{c}"] = _spec({k: w / tong for k, w in con.items()})
    ho["deu"] = _spec({c: 0.2 for c in cb.THANH_PHAN})
    return ho


def spec_z() -> dict:
    """Z: đổi chỗ trọng số của hai thành phần KHÔNG mang. Chọn trend ↔ sr, KHÔNG phải trend ↔
    momentum như ví dụ ở mục 4.3: hai thành phần ấy cùng trọng số 0,25 nên đổi chỗ cho đúng bộ
    trọng số mặc định (Δ chỉ còn do `int()`), một đối chứng suy biến. trend và sr có độ phân
    tán gần nhau (nấc 0–100 và 6,2–100) nên đổi chỗ gần như giữ nguyên độ lệch chuẩn của điểm."""
    w = dict(TRONG_SO_MAC_DINH)
    w["trend_score"], w["sr_score"] = w["sr_score"], w["trend_score"]
    return _spec(w)


def ho_spec_oracle() -> dict[str, dict]:
    """Mọi spec oracle chấm: họ F cộng Z."""
    ho = ho_spec_f()
    ho[TEN_SPEC_Z] = spec_z()
    return ho


# ── bộ sinh lõi ──────────────────────────────────────────────────────────────

def _cholesky_tiem_an() -> np.ndarray:
    """Cholesky của ma trận tương quan Pearson của nhiễu RIÊNG năm thành phần.

    Tương quan hạng ρ của hai biến chuẩn đồng thời có Pearson r = 2·sin(πρ/6). Thành phần mang
    pha thêm b·z (độc lập với nhiễu riêng) nên mọi tương quan của nó với thành phần khác bị nhân
    với a = √(1−b²); phần nhiễu riêng được phóng 1/a để tương quan QUAN SÁT được vẫn là bảng
    MO-XE. Nổ nếu ma trận không xác định dương."""
    r = 2.0 * np.sin(np.pi * TUONG_QUAN_HANG / 6.0)
    np.fill_diagonal(r, 1.0)
    i = cb.THANH_PHAN.index(THANH_PHAN_MANG)
    a = float(np.sqrt(1.0 - HE_SO_Z ** 2))
    for j in range(len(r)):
        if j != i:
            r[i, j] = r[j, i] = r[i, j] / a
    return np.linalg.cholesky(r)  # LinAlgError nếu không xác định dương


def _ar1(rng, hinh: tuple, phi: float, n: int) -> np.ndarray:
    """Mảng `hinh + (n,)` các chuỗi AR(1) dừng, phương sai 1, trung bình 0."""
    k = float(np.sqrt(1.0 - phi * phi))
    eps = rng.standard_normal(hinh + (n,))
    ra = np.empty(hinh + (n,))
    ra[..., 0] = eps[..., 0]
    for t in range(1, n):
        ra[..., t] = phi * ra[..., t - 1] + k * eps[..., t]
    return ra


def _roi_rac(tiem_an: np.ndarray, ten: str) -> np.ndarray:
    """Tiềm ẩn chuẩn → giá trị nấc, nấc có xác suất bằng nhau."""
    from statistics import NormalDist
    so, lo, hi = NAC[ten]
    nguong = [NormalDist().inv_cdf(j / so) for j in range(1, so)]
    nac = np.round(np.linspace(lo, hi, so), 1)
    return nac[np.searchsorted(np.array(nguong), tiem_an)]


def _sinh_loi(rng, so_phien: int, kappa: float) -> dict:
    """Lõi sinh. Thứ tự rút số NGẪU NHIÊN cố định và KHÔNG phụ thuộc `kappa`."""
    n, m = so_phien, SO_MA
    heso_t = float(np.sqrt(NU_BUOC_T / (NU_BUOC_T - 2.0)))
    thi_truong = rng.standard_t(NU_BUOC_T, size=n) / heso_t * SIGMA_THI_TRUONG
    nganh = rng.standard_t(NU_BUOC_T, size=(SO_NGANH, n)) / heso_t * SIGMA_NGANH
    rieng = (sd._nhieu_garch(rng, m, n) * SIGMA_RIENG).T             # n × m
    z_ngoai = _ar1(rng, (m,), PHI_Z, n + 2)                           # m × (n+2): cột j là phiên j−2
    nhieu = _ar1(rng, (len(cb.THANH_PHAN), m), PHI_THANH_PHAN, n)     # 5 × m × n
    gia_dau = rng.uniform(*GIA_DAU, size=m)
    tranh_luan = np.clip(rng.normal(0.0, SIGMA_TRANH_LUAN, size=(n, m)), -TRAN_TRANH_LUAN, TRAN_TRANH_LUAN)

    ma_nganh = np.arange(m) * SO_NGANH // m
    ky_vong = kappa * z_ngoai[:, :n].T / cb.NHIP                       # z ở phiên s−2, chia 21 (mục 4.2)
    ln = thi_truong[:, None] + nganh[ma_nganh].T + rieng + ky_vong
    ln = np.clip(ln, -BIEN_NGAY, BIEN_NGAY)
    close = gia_dau[None, :] * np.cumprod(1.0 + ln, axis=0)

    chung = np.einsum("kl,lmt->kmt", _cholesky_tiem_an(), nhieu)       # nhiễu riêng tương quan, 5 × m × n
    a = float(np.sqrt(1.0 - HE_SO_Z ** 2))
    thanh_phan = {}
    for k, ten in enumerate(cb.THANH_PHAN):
        tiem_an = chung[k].T                                           # n × m
        if ten == THANH_PHAN_MANG:
            tiem_an = a * tiem_an + HE_SO_Z * z_ngoai[:, 2:].T         # z ở CHÍNH phiên t
        thanh_phan[ten] = _roi_rac(tiem_an, ten)
    tho = np.zeros((n, m))
    for ten in cb.THANH_PHAN:
        tho = tho + TRONG_SO_MAC_DINH[ten] * thanh_phan[ten]
    diem = np.trunc(np.clip(tho + tranh_luan, DIEM_SAN, DIEM_TRAN)).astype(np.int64)  # `int()` của paper_trading :731
    return {"close": close, "thanh_phan": thanh_phan, "diem": diem, "z": z_ngoai[:, 2:].T}


def _ma_gia(m: int = SO_MA) -> tuple[str, ...]:
    return tuple(f"GIA{i + 1:02d}" for i in range(m))  # không trùng mã thật


def _kiem_hat(luong: int, chi_so: int) -> None:
    for ten, v in (("luong", luong), ("chi_so", chi_so)):
        if not isinstance(v, (int, np.integer)) or isinstance(v, bool) or v < 1:
            raise ValueError(f"{ten} phai la so nguyen >= 1, nhan {v!r}")


# ── oracle ───────────────────────────────────────────────────────────────────

def diem_spec(spec: dict, thanh_phan: dict) -> np.ndarray:
    """Điểm của một spec trên ma trận thành phần: cộng lần lượt theo thứ tự khoá của spec. Cùng
    điểm với `cb.diem_ung_vien` tới sai số làm tròn (≤ 1e-9, có test): `sum()` của Python 3.12+ cộng
    có bù còn bản này cộng thẳng, nên không đòi trùng từng bit."""
    cb.kiem_spec(spec)
    tho = 0.0
    for k, w in spec["trong_so"].items():
        tho = tho + float(w) * thanh_phan[k]
    return tho


def tinh_su_that(luong: int, chi_so: int, kappa: float, so_phien: int = SO_PHIEN_SU_THAT,
                 so_khoi: int = SO_KHOI_SU_THAT) -> dict:
    """Bảng sự thật: ΔIC_true của từng spec so với điểm đã ghi, trên mẫu `so_phien` phiên × `SO_MA`
    mã CÙNG tham số, hạt `[luong, chi_so, HAT_SU_THAT]`. Nhãn là `E.nhan_vuot_ro` của máy đo.

    `se_mc` = độ lệch chuẩn ΔIC giữa `so_khoi` khối phiên liền nhau, chia √so_khoi: sai số
    Monte Carlo của chính mẫu oracle. Khối dài (≥ 400 phiên) hơn nhiều so với đời của z và của
    cửa sổ nhãn (~21 phiên), nên coi các khối là gần độc lập — ĐÂY LÀ ƯỚC LƯỢNG sai số."""
    _kiem_hat(luong, chi_so)
    mau = _sinh_loi(np.random.default_rng([luong, chi_so, HAT_SU_THAT]), so_phien, kappa)
    ma = _ma_gia()
    kh = {m: pd.DataFrame({"close": mau["close"][:, i]}) for i, m in enumerate(ma)}
    nhan = E.nhan_vuot_ro(kh, cb.NHIP).to_numpy()
    co = ~np.isnan(nhan).any(axis=1)
    so_co = int(co.sum())
    assert co[:so_co].all() and not co[so_co:].any(), "nhãn phải có ở đoạn đầu và chỉ thiếu ở đuôi"
    nhan = nhan[:so_co]
    b = mau["diem"][:so_co].astype(float)
    cat = np.array_split(np.arange(so_co), so_khoi)
    ic_b = E.rho_hang(b.ravel(), nhan.ravel())                       # điểm đã ghi: tính MỘT lần
    ic_b_khoi = [E.rho_hang(b[i].ravel(), nhan[i].ravel()) for i in cat]
    ra = {}
    for ten, spec in ho_spec_oracle().items():
        c = diem_spec(spec, {k: v[:so_co] for k, v in mau["thanh_phan"].items()})
        theo_khoi = np.array([E.rho_hang(c[i].ravel(), nhan[i].ravel()) - ic_b_khoi[j]
                              for j, i in enumerate(cat)])
        ra[ten] = {"delta_ic": E.rho_hang(c.ravel(), nhan.ravel()) - ic_b,
                   "se_mc": float(theo_khoi.std(ddof=1) / np.sqrt(so_khoi))}
    return {"kappa": kappa, "so_phien": so_phien, "so_phien_co_nhan": so_co, "so_khoi": so_khoi,
            "hat": [luong, chi_so, HAT_SU_THAT], "spec": ra}


def spec_ngoai_hai_se(su_that: dict, he_so: float = 2.0) -> list[str]:
    """Tên các spec có |ΔIC_true| ≥ `he_so` · sai số MC. Ở NULL phải rỗng (mục 4.5(c))."""
    return sorted(t for t, v in su_that["spec"].items() if abs(v["delta_ic"]) >= he_so * v["se_mc"])


# ── thị trường ───────────────────────────────────────────────────────────────

@dataclass(frozen=True, eq=False)
class ThiTruongGia:
    luong: int
    chi_so: int
    kappa: float
    ngay: tuple[str, ...]
    ma: tuple[str, ...]
    gia: pd.DataFrame                  # ngày × mã, giá đóng cửa (nghìn đồng)
    thanh_phan: dict[str, np.ndarray]  # tên thành phần → ma trận phiên × mã
    diem: np.ndarray                   # phiên × mã, số NGUYÊN (int() như paper_trading :731)
    su_that: dict | None               # bảng sự thật của oracle (4.5); None nếu không dựng

    def dong_quyet_dinh(self) -> list[dict]:
        """Dòng đúng khuôn tab `decisions` mà `cb.doc_quyet_dinh` đọc: `symbol`, `signal_date`,
        `score` NGUYÊN, `components` (JSON năm thành phần), `at`, `seq`. Mọi phiên, mọi mã."""
        goc = _dt.date(1970, 1, 1).toordinal()
        ra, seq = [], 0
        for t, ngay in enumerate(self.ngay):
            at = float((_dt.date.fromisoformat(ngay).toordinal() - goc) * 86400 + 15 * 3600 + 35 * 60)
            for j, ma in enumerate(self.ma):
                seq += 1
                tp = {k: float(self.thanh_phan[k][t, j]) for k in cb.THANH_PHAN}
                ra.append({"symbol": ma, "signal_date": ngay, "score": int(self.diem[t, j]),
                           "components": json.dumps(tp, ensure_ascii=False), "at": at, "seq": seq})
        return ra


def sinh_thi_truong(luong: int, chi_so: int, kappa: float, so_phien: int | None = None,
                    co_su_that: bool = True) -> ThiTruongGia:
    """Sinh MỘT thị trường giả. `so_phien` mặc định = `dong_thoi_gian()["tong"]`.

    `luong` (dòng hạt 1…5 của mục 4.8, hoặc 6, 7… khi sửa đặc tả) và `chi_so` (số thứ tự thị
    trường) đi vào `default_rng([luong, chi_so])`; `kappa` là núm lợi thế (0 = NULL)."""
    _kiem_hat(luong, chi_so)
    if kappa < 0:
        raise ValueError("kappa phai >= 0 (z cung huong voi loi nhuan; dau am la thi truong DAO — khong co o Lat 1)")
    n = dong_thoi_gian()["tong"] if so_phien is None else int(so_phien)
    mau = _sinh_loi(np.random.default_rng([luong, chi_so]), n, float(kappa))
    ngay, ma = lich_phien(n), _ma_gia()
    return ThiTruongGia(
        luong=luong, chi_so=chi_so, kappa=float(kappa), ngay=ngay, ma=ma,
        gia=pd.DataFrame(mau["close"], index=list(ngay), columns=list(ma)),
        thanh_phan=mau["thanh_phan"], diem=mau["diem"],
        su_that=tinh_su_that(luong, chi_so, float(kappa)) if co_su_that else None)


def sinh_null(luong: int, chi_so: int, so_phien: int | None = None, co_su_that: bool = True) -> ThiTruongGia:
    """Thị trường NULL (mục 4.7): cùng bộ sinh, cùng mọi thông số, κ = 0."""
    return sinh_thi_truong(luong, chi_so, 0.0, so_phien, co_su_that)
