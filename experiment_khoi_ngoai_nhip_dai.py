"""ĐO 16 — nhịp 21 phiên: tín hiệu khối ngoại của ĐO 15 có LẶP LẠI ngoài mẫu?

Tiêu chí ký trước: `docs/TIEU-CHI-DOC-TRUOC.md` mục ĐO 16.

CÂU HỎI
ĐO 15 (`docs/STATE.md` BƯỚC 113) đo TRONG MẪU và thấy ở h=21 `kn_z_20` cho
IC **+0,0557**, cao hơn rào hoà vốn 0,0488 — rồi xếp nhịp ấy vào kết cục 4
(THIẾU LỰC). ĐO 16 hỏi đúng một câu: **dự báo ấy, GIỮ NGUYÊN, có đứng được
trên dữ liệu mà năm đặc trưng khối ngoại CHƯA TỪNG NHÌN không?**

HAI TẬP, TÁCH THEO KHOÁ
    tap HUAN LUYEN   bang DO 15 (`backtest/cache/`)  -- da nhin
    tap KIEM         bang cache_2018 TRU bang DO 15, theo khoa (ma, ngay)
Tách theo KHOÁ, không theo một mốc ngày: bảng ĐO 15 bắt đầu ở mỗi mã một
ngày khác, nên một mốc chung sẽ hoặc bỏ sót phiên chưa nhìn, hoặc lẫn phiên
đã nhìn. KHÔNG chạm mạng — kéo lại khối ngoại trước 29/09/2026 là đọc sớm
phép kiểm point-in-time đã hẹn (`docs/HANDOFF.md` mục 5).

DỰ BÁO: `kn_z_20`, DẤU +, KHÔNG KHỚP LẠI — KIỂM HAI PHÍA
Không tham số nào được chọn trên tập kiểm. Hướng dấu đã biết từ ĐO 15, nhưng
phép kiểm vẫn HAI PHÍA, theo tiền lệ BƯỚC 13 (*"hai phía, cố ý, dù giả
thuyết có hướng"*). Bản thiết kế lúc người dùng duyệt là một phía; nó đổi về
hai phía khi lực hai phía trên tập kiểm đo được 41/50 — tức lý do duy nhất
để chọn một phía, "cho đủ lực", không còn. Một IC có ý nghĩa mà NGƯỢC dấu
thì là KHÔNG LẶP LẠI. Cách gộp tuyến tính khớp trên tập huấn luyện được in
như SỐ PHỤ — không vào phán quyết.

PHÁN QUYẾT "ĐỌC ĐƯỢC": NHIỀU LƯỢT, KHÔNG PHẢI MỘT ĐỒNG XU
Lặp lại chính phép tiêm của ĐO 15 ba mươi lần trên cửa sổ ĐO 15:

    h=21   khong co gi   bat  0/30    dung bang rao  bat 21/30
    h=5    khong co gi   bat  0/30    dung bang rao  bat 30/30

Ở h=21 một lượt rút đơn lẻ là một đồng xu nghiêng 70/30 (lỗi 99). Nên ở
đây: đọc TỶ LỆ bắt qua `R_TIEM` lượt, và dưới `R_TOI_THIEU` lượt thì không
được phán gì cả. Tái lập hai dòng trên:

    --do-luc --cua-so-do15 --r 30 --alpha 0.01 --hat 20260945
    --do-luc --cua-so-do15 --r 30 --alpha 0.01 --hat 20260929 --nhip 5

CHẠY
    ./.venv/Scripts/python.exe experiment_khoi_ngoai_nhip_dai.py --tai-lap-do15
    ./.venv/Scripts/python.exe experiment_khoi_ngoai_nhip_dai.py --do-luc
    ./.venv/Scripts/python.exe experiment_khoi_ngoai_nhip_dai.py
"""
from __future__ import annotations

import argparse
import json
import sys
from math import comb
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))

import experiment_tran_dac_trung as E  # noqa: E402
import experiment_khoi_ngoai as K  # noqa: E402

#: Thư mục giá của tập GỘP. KHÔNG phải `E.CACHE` — đó là cửa sổ ĐO 15.
CACHE_GIA = GOC / "backtest" / "cache_2018"

#: Nhịp duy nhất. Nằm trong `E.NHIP_DA_DOI_CHIEU` (BƯỚC 9).
NHIP = 21

#: Dự báo được kiểm, và hướng dấu khai TRƯỚC — từ ĐO 15, không từ tập kiểm.
DU_BAO = "kn_z_20"
DAU = +1

#: Mốc đầu cửa sổ ĐO 15, chép từ tiêu chí ĐO 15. Chỉ để IN cơ cấu tập kiểm
#: — tập kiểm tách theo khoá, không theo mốc này.
MOC_DO15 = "2021-10-14"

#: HAI PHÍA, theo tiền lệ BƯỚC 13 — xem docstring đầu file.
ALPHA = 0.05

#: Mã có ít hơn chừng này quan sát trong tập kiểm thì bỏ — đúng ngưỡng 60
#: của `K._bang_kn`. Mã quá ngắn thì `E.san_nhieu` để nguyên không dịch, và
#: phép tiêm cũng không dịch được nền, tức ô 'không có gì' ở mã ấy đo lại
#: chính cột thật — bản 2 hỏng của ĐO 15, thu nhỏ.
MIN_QUAN_SAT_MA = 60

#: Lực tối thiểu để một kết quả null đọc được: 80%, chuẩn quy ước.
LUC_TOI_THIEU = 0.80

#: Số lượt tiêm, và số vòng null mỗi lượt (bằng mặc định của ĐO 15).
R_TIEM = 50
SO_VONG_TIEM = 400

#: Dưới số lượt này thì KHÔNG được phán đọc-được, dù tỷ lệ đẹp đến đâu.
#: Đây là chính lỗi 99: một lượt rút là một đồng xu 70/30 ở h=21. Với 30
#: lượt, sai số chuẩn của tỷ lệ quanh 80% là sqrt(0,8 x 0,2 / 30) = 0,073.
R_TOI_THIEU = 30

#: Số hoán vị cho null của DỰ BÁO, như ĐO 15.
SO_HOAN_VI = 2000

#: Hai hạt giống RIÊNG: phép tiêm dùng hạt của nó, nên `--do-luc` và lượt
#: chính cho ĐÚNG cùng một bảng lực — lượt chính chỉ ĐO LẠI, không rút lại.
HAT_GIONG = 20260924
HAT_GIONG_LUC = 20260925

#: Ba con số ĐO 15 đã ghi ở h=21 (BƯỚC 113), làm tròn bốn chữ số. Tập huấn
#: luyện phải tái lập ĐÚNG chúng trước khi được dùng làm tập huấn luyện.
DO15_H21 = {"rao": 0.0488, "kn_z_20": 0.0557, "can_tren": 0.0851}


def nguong_im(r: int, alpha: float, muc: float = 0.05) -> int:
    """Số lượt 'không có gì' bị bắt NHIỀU NHẤT mà vẫn coi là im.

    Dưới giả thuyết null, số lượt bắt ~ Binom(r, alpha). Trả `m` nhỏ nhất
    sao cho P(X > m) < `muc`. Suy ra, không gõ tay: đổi `R_TIEM` hay
    `ALPHA` thì ngưỡng tự đi theo.
    """
    duoi = 0.0
    for m in range(r + 1):
        duoi += comb(r, m) * alpha ** m * (1 - alpha) ** (r - m)
        if 1.0 - duoi < muc:
            return m
    return r


def tri_so_p_mot_phia(ic: float, null: np.ndarray, dau: int = DAU) -> float:
    """p MỘT PHÍA theo hướng `dau`, dạng có hiệu chỉnh — không bao giờ 0.

    KHÔNG phải luật của ĐO 16 (luật là hai phía). Giữ lại để TÁI LẬP con số
    lực một phía đã viết vào tiêu chí, bằng `--mot-phia`. Đếm null ở ĐÚNG
    phía đã khai: một IC ngược dấu thì p gần 1.
    """
    k = int(np.sum(dau * np.asarray(null) >= dau * ic))
    return (1.0 + k) / (1.0 + len(null))


def tach_chua_nhin(khoa_da_nhin, khoa) -> np.ndarray:
    """Mặt nạ các dòng có khoá KHÔNG nằm trong tập đã nhìn."""
    da = set(khoa_da_nhin)
    return np.array([k not in da for k in khoa], dtype=bool)


def tap_kiem(kh_gop: dict, kh_do15: dict, kn: dict, h: int) -> dict:
    """Tập KIỂM = bảng gộp trừ bảng ĐO 15 theo khoá; bỏ mã quá ngắn.

    Trả cả tập HUẤN LUYỆN, vì cách gộp số phụ khớp trên nó.
    """
    X15, y15, _, k15 = K._bang_kn_khoa(kh_do15, kn, h)
    Xg, yg, _, kg = K._bang_kn_khoa(kh_gop, kn, h)
    if Xg is None or X15 is None:
        return {}
    moi = tach_chua_nhin(k15, kg)
    ma = np.array([k[0] for k in kg])
    ngay = np.array([k[1] for k in kg])
    dem = pd.Series(ma[moi]).value_counts()
    giu = moi & np.isin(ma, dem[dem >= MIN_QUAN_SAT_MA].index.to_numpy())
    ma_k = ma[giu]
    chi_so = {m: np.flatnonzero(ma_k == m) for m in np.unique(ma_k)}
    ngay_k = ngay[giu]
    return {"X": Xg[giu], "y": yg[giu], "chi_so": chi_so,
            "X_huan_luyen": X15, "y_huan_luyen": y15,
            "n_do15": len(k15), "n_gop": len(kg), "n_chua_nhin": int(moi.sum()),
            "n_kiem": int(giu.sum()),
            "ma_bo": sorted(dem[dem < MIN_QUAN_SAT_MA].index.tolist()),
            "n_truoc_moc": int(np.sum(ngay_k < MOC_DO15)),
            "ngay_dau": str(min(ngay_k)) if len(ngay_k) else None,
            "ngay_cuoi": str(max(ngay_k)) if len(ngay_k) else None}


def mot_luot_tiem(X, y, chi_so, h: int, rng, he_so: float,
                  so_vong: int = SO_VONG_TIEM, alpha: float = ALPHA,
                  mot_phia: bool = False):
    """MỘT lượt tiêm, đúng công thức bản 3 của `K.chung_cu_duong_kn`.

    Nền = cột `kn_z_20` THẬT, dịch vòng trong từng mã một khoảng ≫ h: giữ
    nguyên tự tương quan, RỜI khỏi nhãn. Bản 2 của ĐO 15 dùng chính cột
    thật không dịch, và ô 'không tiêm gì' khi ấy đo lại chính `kn_z_20` —
    tự kiểm thứ nó đi kiểm. p mặc định HAI PHÍA, như ĐO 15 và như phép kiểm
    thật của ĐO 16; `mot_phia=True` chỉ để tái lập con số một phía.
    """
    sigma = float(np.std(y))
    rao = E.rao_hoa_von(sigma)
    nen = X[:, K.TEN_DAC_TRUNG.index(DU_BAO)].copy()
    for _, idx in chi_so.items():
        n = len(idx)
        if n > 2 * (h + 1):
            k = int(rng.integers(h + 1, n - h - 1))
            nen[idx] = np.roll(nen[idx], k)
    nen = (nen - nen.mean()) / (nen.std() or 1.0)
    muc = rao * he_so
    gia_dt = muc * (y / sigma) + np.sqrt(max(1 - muc ** 2, 0.0)) * nen
    r = E.rho_hang(gia_dt, y)
    null = E.san_nhieu(lambda yp, _x=gia_dt: E.rho_hang(_x, yp),
                       y, chi_so, h, rng, so=so_vong)
    p = tri_so_p_mot_phia(r, null) if mot_phia else K.tri_so_p(r, null)
    return {"muc": muc, "ic": r, "p": p, "bat": bool(p < alpha)}


def luc_phat_hien(X, y, chi_so, h: int, rng, r_tiem: int = R_TIEM,
                  so_vong: int = SO_VONG_TIEM, alpha: float = ALPHA,
                  mot_phia: bool = False) -> dict:
    """R lượt tiêm ở hai mức, đếm tỷ lệ bắt. In DỮ LIỆU THÔ dưới con số."""
    ra = {"R": r_tiem, "alpha": alpha}
    print(f"\n-- LUC PHAT HIEN · h = {h} · {r_tiem} luot · {so_vong} vong"
          f" null moi luot · alpha {alpha}"
          f" {'MOT PHIA' if mot_phia else 'HAI PHIA'} --")
    for he_so, ten in ((0.0, "khong co gi"), (1.0, "dung bang rao")):
        luot = [mot_luot_tiem(X, y, chi_so, h, rng, he_so, so_vong, alpha,
                              mot_phia) for _ in range(r_tiem)]
        bat = sum(v["bat"] for v in luot)
        ic = np.array([v["ic"] for v in luot])
        ra[ten] = bat
        ra[f"p_{ten}"] = [round(v["p"], 4) for v in luot]
        print(f"  {ten:>14}  muc tiem {luot[0]['muc']:.4f}  IC do: TB"
              f" {ic.mean():+.4f} SD {ic.std():.4f}   BAT {bat}/{r_tiem}")
        print(f"  {'':>14}  p: " + " ".join(
            f"{v:.3f}" for v in sorted(ra[f"p_{ten}"])))
    im = nguong_im(r_tiem, alpha)
    print(f"  -> doc duoc khi: 'dung bang rao' bat >= {LUC_TOI_THIEU:.0%}"
          f" VA 'khong co gi' bat <= {im}")
    return ra


def doc_duoc_nhieu_luot(luc: dict | None) -> bool:
    """Hai vế, cả hai bắt buộc; thiếu khoá thì False — fail closed.

    Vế 'im' KHÔNG đòi 0/R: dưới null đúng, một phép kiểm ở mức `alpha` tự
    kêu khoảng `alpha` số lượt. Đòi 0 là đòi một máy đo tốt hơn máy đo
    đúng — nên ngưỡng lấy từ phân phối nhị thức, không gõ tay.
    """
    if not luc:
        return False
    try:
        r = int(luc["R"])
        k0 = int(luc["khong co gi"])
        k1 = int(luc["dung bang rao"])
        alpha = float(luc["alpha"])
    except (KeyError, TypeError, ValueError):
        return False
    if r < R_TOI_THIEU:
        return False
    return k1 / r >= LUC_TOI_THIEU and k0 <= nguong_im(r, alpha)


def phan_dinh_lap_lai(ket: dict | None, rao: float | None,
                      doc_duoc: bool | None,
                      alpha: float = ALPHA) -> tuple[int, str]:
    """Đọc theo ĐÚNG bảng kết cục đã ký ở tiêu chí ĐO 16.

    Mã thoát: 0 câu hỏi ĐÓNG · 1 KHÔNG đóng được · 2 không đọc được.

    `ket["p"]` là p HAI PHÍA. Một IC có ý nghĩa mà ngược dấu đã khai là
    KHÔNG LẶP LẠI — phép kiểm hai phía không được đọc nó thành "có tín hiệu".

    `bien` = z(1 - alpha/2) lần độ lệch chuẩn null của CHÍNH dự báo: nó
    tách 'dưới rào CHẮC' khỏi 'dưới rào trong biên nhiễu'. ĐO 15 đọc được
    điểm ước lượng vì khoảng cách là 2,66 LẦN, không phải vì luật cho phép.
    """
    if doc_duoc is None or not ket or rao is None:
        return 2, "CHUA KIEM DUOC — thieu du bao, rao, hoac phep do luc"
    try:
        ic = float(ket["ic"])
        p = float(ket["p"])
        sd = float(ket["null_sd"])
    except (KeyError, TypeError, ValueError):
        return 2, "CHUA KIEM DUOC — du bao thieu ic / p / null_sd"
    if not doc_duoc:
        return 2, ("KET CUC 4 — THIEU LUC: phep tiem khong dat, ket qua"
                   " KHONG doc duoc du no dep hay xau")
    if p >= alpha:
        return 0, (f"KET CUC 3 — KHONG LAP LAI: {DU_BAO} IC {ic:+.4f}"
                   f" (p hai phia {p:.4f}). Nhip 21 DONG")
    if DAU * ic <= 0:
        return 0, (f"KET CUC 3 — KHONG LAP LAI, NGUOC DAU: {DU_BAO} IC"
                   f" {ic:+.4f} co y nghia nhung trai huong da khai."
                   f" Nhip 21 DONG")
    bien = NormalDist().inv_cdf(1 - alpha / 2) * sd
    if ic > rao:
        return 1, (f"KET CUC 1 — LAP LAI VA VUOT RAO: IC {ic:+.4f} > rao"
                   f" {rao:.4f}. QUY TAC 1 truoc khi tin. KHONG bat gi")
    if ic + bien < rao:
        return 0, (f"KET CUC 2 — LAP LAI, DUOI RAO CHAC: {ic:+.4f} + bien"
                   f" {bien:.4f} < rao {rao:.4f}. Nhip 21 DONG ve kinh te")
    return 1, (f"KET CUC 2b — LAP LAI, SAT RAO: {ic:+.4f} duoi rao {rao:.4f}"
               f" nhung trong bien nhieu {bien:.4f}. KHONG dong duoc")


def ic_theo_khoa(kh_gop: dict, kh_do15: dict, kn: dict, h: int) -> dict:
    """IC của `DU_BAO` trên BẢNG GỘP, tách theo khoá — CHẨN ĐOÁN SAU KHI ĐỌC.

    Thêm 24/09/2026 SAU khi lượt chính ra kết cục 3. Không vào phán quyết
    nào — phán quyết đã ký và đã đọc. Nó trả lời một câu về DỤNG CỤ:

        phan DA NHIN, tinh lai tren bang GOP   phai ~ +0,0557 cua DO 15

    Đường ống gộp (giá `cache_2018`, rổ chuẩn khác) mà không dựng lại được
    IC trong mẫu trên chính phần đã nhìn thì một IC ngoài mẫu ≈ 0 nói về
    đường ống, không nói về tín hiệu. Đây là "bắt máy đo đi qua một ca THẬT
    đã biết trước" (`SKILL.md` Bước 3), làm cho một kết quả XẤU.

    Kèm IC tập kiểm tách trước/sau `MOC_DO15` — MÔ TẢ, chọn sau khi thấy
    số, nên không được dùng để kể chuyện "tín hiệu chỉ chết ở giai đoạn X".
    """
    _, _, _, k15 = K._bang_kn_khoa(kh_do15, kn, h)
    Xg, yg, _, kg = K._bang_kn_khoa(kh_gop, kn, h)
    da = ~tach_chua_nhin(k15, kg)
    x = Xg[:, K.TEN_DAC_TRUNG.index(DU_BAO)]
    ngay = np.array([k[1] for k in kg])
    moi = ~da
    truoc = moi & (ngay < MOC_DO15)
    sau = moi & (ngay >= MOC_DO15)
    ra = {}
    for ten, m in (("da_nhin", da), ("chua_nhin_truoc_moc", truoc),
                   ("chua_nhin_sau_moc", sau)):
        ra[ten] = {"n": int(m.sum()),
                   "ic": E.rho_hang(x[m], yg[m]) if m.sum() else None}
    return ra


def tai_lap_do15(so_hoan_vi: int = 20) -> int:
    """Tiền kiểm dụng cụ: ba con số ĐO 15 phải ra ĐÚNG trên `E.CACHE`.

    Cả ba là đại lượng TẤT ĐỊNH (không phụ thuộc hạt giống), nên số vòng
    hoán vị ở đây chỉ để hàm chạy — không ảnh hưởng thứ được so.
    """
    kh = E.nap_gia()
    kn = K.nap_khoi_ngoai()
    d = K.chay_mot_nhip(kh, kn, NHIP, np.random.default_rng(20260922),
                        so_hoan_vi)
    thay = {"rao": d["rao"], "kn_z_20": d["dac_trung"]["kn_z_20"]["ic"],
            "can_tren": d["can_tren"]["rho"]}
    print(f"\nTAI LAP DO 15 · h = {NHIP} · {E.CACHE.name}")
    lech = 0
    for k, v in DO15_H21.items():
        ok = round(thay[k], 4) == v
        lech += not ok
        print(f"  {k:<9} ghi {v:+.4f}  do {thay[k]:+.4f}  "
              f"{'KHOP' if ok else 'LECH'}")
    return 0 if lech == 0 else 1


def _in_tap(t: dict) -> None:
    print(f"bang DO 15 {t['n_do15']:,} · bang gop {t['n_gop']:,} · chua nhin"
          f" {t['n_chua_nhin']:,} · TAP KIEM {t['n_kiem']:,}"
          f" (truoc {MOC_DO15}: {t['n_truoc_moc']:,}) · {len(t['chi_so'])} ma"
          f" · {t['ngay_dau']} -> {t['ngay_cuoi']}")
    if t["ma_bo"]:
        print(f"  ma bo vi duoi {MIN_QUAN_SAT_MA} quan sat kiem: {t['ma_bo']}")


def do_luc(cua_so_do15: bool = False, mot_phia: bool = False,
           r_tiem: int = R_TIEM, alpha: float = ALPHA,
           hat: int = HAT_GIONG_LUC, nhip: int = NHIP) -> int:
    """Lực TRƯỚC khi ký — không tính một IC thật nào.

    Mặc định là ĐÚNG luật đã ký: tập kiểm, hai phía, `R_TIEM` lượt,
    `ALPHA`. Các tuỳ chọn còn lại tồn tại để TÁI LẬP những con số lực đã
    viết vào tiêu chí — kể cả con số đo theo luật của ĐO 15 (hai phía,
    Bonferroni 0,01, 30 lượt) và con số một phía của bản thiết kế đầu.
    """
    kn = K.nap_khoi_ngoai()
    if cua_so_do15:
        X, y, chi_so = K._bang_kn(E.nap_gia(), kn, nhip)
        t = {"X": X, "y": y, "chi_so": chi_so}
        print(f"CUA SO DO 15 · {E.CACHE.name} · h = {nhip} ·"
              f" {len(y):,} quan sat · {len(chi_so)} ma")
    else:
        t = tap_kiem(E.nap_gia(CACHE_GIA), E.nap_gia(), kn, nhip)
        if not t:
            print("CHUA KIEM DUOC — khong gop duoc bang nao")
            return 2
        _in_tap(t)
    sigma = float(np.std(t["y"]))
    rao = E.rao_hoa_von(sigma)
    print(f"  sigma nhan {sigma:.3f}% · rao {rao:.4f}")
    luc = luc_phat_hien(t["X"], t["y"], t["chi_so"], nhip,
                        np.random.default_rng(hat), r_tiem=r_tiem,
                        alpha=alpha, mot_phia=mot_phia)
    dd = doc_duoc_nhieu_luot(luc)
    # null cua CHINH du bao: hoan vi nhan pha lien ket, nen KHONG lo IC that
    x = t["X"][:, K.TEN_DAC_TRUNG.index(DU_BAO)]
    null = E.san_nhieu(lambda yp, _x=x: E.rho_hang(_x, yp), t["y"],
                       t["chi_so"], nhip, np.random.default_rng(hat + 1),
                       so=SO_VONG_TIEM)
    z = NormalDist().inv_cdf(1 - ALPHA / 2)
    san = float(np.quantile(np.abs(null), 1 - ALPHA))
    sd = float(np.std(null))
    print(f"\n  null {DU_BAO} ({SO_VONG_TIEM} vong, UOC LUONG truoc): SD"
          f" {sd:.4f} · san hai phia |IC| > {san:.4f}")
    print(f"  ket cuc 2 CHAC doi IC < rao - {z:.2f} x SD = {rao - z * sd:+.4f},"
          f" trong khi vuot san doi IC > {san:+.4f}  ->"
          f" {'VO NGHIEM' if rao - z * sd <= san else 'co nghiem'}")
    print(f"\n  -> {'DOC DUOC' if dd else 'KHONG doc duoc'}")
    return 0 if dd else 2


def main(tham_so: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="DO 16 — lap lai ngoai mau h=21")
    ap.add_argument("--tai-lap-do15", action="store_true",
                    help="tien kiem: ba con so DO 15 phai ra dung")
    ap.add_argument("--do-luc", action="store_true",
                    help="luc tren tap kiem, KHONG tinh IC that nao")
    ap.add_argument("--cua-so-do15", action="store_true",
                    help="--do-luc tren cua so DO 15 (tai lap)")
    ap.add_argument("--mot-phia", action="store_true",
                    help="--do-luc theo p MOT phia (tai lap ban thiet ke dau)")
    ap.add_argument("--r", type=int, default=R_TIEM)
    ap.add_argument("--alpha", type=float, default=ALPHA)
    ap.add_argument("--hat", type=int, default=HAT_GIONG_LUC)
    ap.add_argument("--nhip", type=int, default=NHIP)
    ap.add_argument("--sau-khi-doc", action="store_true",
                    help="chan doan SAU khi doc -- khong vao phan quyet")
    ap.add_argument("--hoan-vi", type=int, default=SO_HOAN_VI)
    ap.add_argument("--ra", default="")
    a = ap.parse_args(tham_so)

    if a.tai_lap_do15:
        return tai_lap_do15()
    if a.sau_khi_doc:
        ra = ic_theo_khoa(E.nap_gia(CACHE_GIA), E.nap_gia(),
                          K.nap_khoi_ngoai(), NHIP)
        print(f"CHAN DOAN SAU KHI DOC · {DU_BAO} · h = {NHIP} · bang gop")
        for ten, v in ra.items():
            ic = "-" if v["ic"] is None else f"{v['ic']:+.4f}"
            print(f"  {ten:<22} {v['n']:>7,} quan sat   IC {ic}")
        print(f"  (DO 15 trong mau ghi {DO15_H21['kn_z_20']:+.4f}"
              f" -- tren bang CUA NO, ro chuan cua no)")
        return 0
    if a.do_luc:
        return do_luc(a.cua_so_do15, a.mot_phia, a.r, a.alpha, a.hat, a.nhip)

    kn = K.nap_khoi_ngoai()
    kh_gop = E.nap_gia(CACHE_GIA)
    print(f"gia: {len(kh_gop)} ma tu {CACHE_GIA.name} · khoi ngoai: {len(kn)} ma")
    if not kh_gop or not kn:
        print("CHUA KIEM DUOC — thieu cache gia hoac khoi ngoai")
        return 2
    t = tap_kiem(kh_gop, E.nap_gia(), kn, NHIP)
    if not t:
        return 2
    _in_tap(t)
    X, y, chi_so = t["X"], t["y"], t["chi_so"]
    sigma = float(np.std(y))
    rao = E.rao_hoa_von(sigma)
    print(f"sigma nhan {sigma:.3f}% · rao {rao:.4f}")

    # ── PHEP KIEM CHINH: du bao giu nguyen, HAI phia ─────────────────
    rng = np.random.default_rng(HAT_GIONG)
    x = X[:, K.TEN_DAC_TRUNG.index(DU_BAO)]
    ic = E.rho_hang(x, y)
    null = E.san_nhieu(lambda yp, _x=x: E.rho_hang(_x, yp), y, chi_so, NHIP,
                       rng, so=a.hoan_vi)
    ket = {"ic": ic, "p": K.tri_so_p(ic, null),
           "null_sd": float(np.std(null)),
           "san": float(np.quantile(np.abs(null), 1 - ALPHA))}
    print(f"\nDU BAO {DU_BAO} (dau {DAU:+d} da khai, giu nguyen tu DO 15):")
    print(f"  IC {ic:+.4f}   p hai phia {ket['p']:.4f}   san |IC| >"
          f" {ket['san']:.4f}   SD null {ket['null_sd']:.4f}   rao {rao:.4f}")

    # ── SO PHU: khong vao phan quyet ─────────────────────────────────
    print("\nSO PHU — KHONG vao phan quyet:")
    for i, ten in enumerate(K.TEN_DAC_TRUNG):
        print(f"  {ten:<16} IC {E.rho_hang(X[:, i], y):+.4f}")
    Xh = t["X_huan_luyen"]
    tb, sd = Xh.mean(0), np.where(Xh.std(0) == 0, 1.0, Xh.std(0))
    Ah = np.column_stack([np.ones(len(Xh)), (Xh - tb) / sd])
    beta = np.linalg.lstsq(Ah, t["y_huan_luyen"], rcond=None)[0]
    Ak = np.column_stack([np.ones(len(X)), (X - tb) / sd])
    print(f"  cach gop KHOP tren tap huan luyen, ap nguyen len tap kiem:"
          f" rho {E.rho_hang(Ak @ beta, y):+.4f}")
    xd = X[:, K.TEN_DAC_TRUNG.index(K.O_DOI_CHUNG)]
    null_dc = E.san_nhieu(lambda yp, _x=xd: E.rho_hang(_x, yp), y, chi_so,
                          NHIP, rng, so=SO_VONG_TIEM)
    p_dc = K.tri_so_p(E.rho_hang(xd, y), null_dc)
    print(f"  o doi chung {K.O_DOI_CHUNG}: p hai phia {p_dc:.4f}"
          + ("   ⚠️  VUOT — nghi RO RI truoc khi tin" if p_dc < ALPHA else ""))

    luc = luc_phat_hien(X, y, chi_so, NHIP,
                        np.random.default_rng(HAT_GIONG_LUC))
    dd = doc_duoc_nhieu_luot(luc)

    print(f"\n{'=' * 66}\nPHAN DINH THEO BANG DA KY (alpha {ALPHA} HAI phia)"
          f"\n{'=' * 66}")
    m, cau = phan_dinh_lap_lai(ket, rao, dd)
    print(f"  h={NHIP}  {cau}")

    if a.ra:
        goi = {"ngay_chay": pd.Timestamp.today().strftime("%Y-%m-%d"),
               "tap": {k: v for k, v in t.items()
                       if not k.startswith(("X", "y", "chi_so"))},
               "du_bao": ket, "rao": rao, "o_doi_chung_p": p_dc,
               "luc": luc, "doc_duoc": dd, "ket_cuc": cau, "ma": m}
        Path(a.ra).write_text(json.dumps(goi, ensure_ascii=False, indent=2,
                                         default=float), encoding="utf-8")
        print(f"\n  ghi: {a.ra}")
    return m


if __name__ == "__main__":
    sys.exit(main())
