"""ĐO 21 — vòng XÁC NHẬN của tầng 3: bao nhiêu phiên dữ liệu chưa nhìn thì
bắt được một ứng viên có lợi thế BẰNG RÀO HOÀ VỐN?

Tiêu chí ký trước: `docs/TIEU-CHI-DOC-TRUOC.md` mục ĐO 21.

CÂU HỎI
Tầng 3 (`docs/STATE.md` BƯỚC 122) hứa: sàng tối đa 5 ứng viên mỗi tuần trên
dữ liệu đã nhìn, rồi xác nhận tối đa 1 mỗi tháng trên dữ liệu CHƯA nhìn, ngưỡng
hiệu chỉnh theo tổng số ứng viên đã sàng. Trước khi dựng vòng ấy phải biết nó
CÓ LỰC không: một tháng dữ liệu mới — khoảng 70 mã × 21 phiên, đo trên tab
`decisions` thật ngày 29/09/2026 — bắt được thứ gì?

KHÔNG ĐO một ứng viên thật nào. Mọi ứng viên ở đây là ứng viên GIẢ, dựng bằng
cách tiêm một mức tương quan BIẾT TRƯỚC với nhãn — đúng phép tiêm của ĐO 15/16.

BỘ MÁY NHẬP LẠI, KHÔNG DỰNG LẠI
    E.nhan_vuot_ro   nhãn log lợi nhuận h phiên VƯỢT RỔ, vào ở T+1
    E.rho_hang       tương quan hạng — phép tính IC duy nhất
    E.rao_hoa_von    rào hoà vốn (chi phí CŨ 0,43 — in để so ĐO 15/16)
    E.san_nhieu      null DỊCH VÒNG — chỉ dùng ĐỂ ĐỐI CHIẾU null mới
    D.nguong_im      số lượt 'không có gì' được phép kêu, suy từ nhị thức
    D.R_TOI_THIEU    dưới số lượt này không phán lực (lỗi 99)

HAI THỨ MỚI, VÀ VÌ SAO
1. Null HOÁN VỊ MÃ. `E.san_nhieu` dịch vòng nhãn trong từng mã một khoảng
   > h, nên nó cần mỗi mã có hơn 2(h+1) quan sát — cửa sổ 21 phiên ở h=21 thì
   không dịch được gì, null thành một điểm. Hoán vị mã gán chuỗi nhãn của mã
   này cho chuỗi điểm của mã khác, GIỮ NGUYÊN mọi tự tương quan theo thời gian
   của cả hai và cấu trúc chéo của nhãn, chỉ phá liên kết điểm–nhãn. Nó chưa
   ai kiểm, nên ĐO này đối chiếu nó với `E.san_nhieu` ở cửa sổ dài, nơi cả hai
   chạy được (tiền lệ BƯỚC 9).
2. Rào HIỆN HÀNH. `E.rao_hoa_von` dùng trượt giá 0,43 đo ngày 24/08; chi phí
   thực thi hiện hành là 0,76 điểm mỗi lệnh (ĐO 20, dòng theo ngày). Tiêm
   bằng rào hiện hành; rào cũ chỉ in ra để so.

NỀN CỦA PHÉP TIÊM: HAI CỘT, ĐỂ KẸP
Đo 29/09/2026 trên 2.430 dòng quyết định tiến-về-trước (34 phiên, không
chạm lợi nhuận): ACF của ĐIỂM CUỐI thật là +0,45 · +0,32 · −0,02 ở độ trễ
1 · 2 · 5. `px_sma50` bền hơn ở độ trễ ngắn (+0,80 · +0,58 · 0,00), `stoch_kd`
kém bền hơn (+0,34 · −0,14 · −0,25). Điểm thật nằm GIỮA — nên đo cả hai và
đọc kết luận ở cột BẤT LỢI cho kết luận ấy.

CHẠY
    ./.venv/Scripts/python.exe tools/do21_luc_vong_xac_nhan.py --doi-chieu
    ./.venv/Scripts/python.exe tools/do21_luc_vong_xac_nhan.py

Mã thoát: 0 đọc được · 2 chưa kiểm được / máy đo không qua đối chiếu.
CHỈ ĐỌC `backtest/cache_2018/`, không chạm mạng, không ghi file nào.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

for _luong in (sys.stdout, sys.stderr):   # stderr: BƯỚC 129
    try:
        _luong.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import experiment_tran_dac_trung as E  # noqa: E402
import experiment_khoi_ngoai_nhip_dai as D  # noqa: E402
from paper_metrics import ROUND_TRIP_COST_PCT  # noqa: E402

#: Giá của tập DÀI nhất trong máy (2018-09 → 2026-09), cùng thư mục ĐO 16.
CACHE_GIA = GOC / "backtest" / "cache_2018"

#: Hai nhịp, cả hai trong `E.NHIP_DA_DOI_CHIEU`. 21 ≈ thời gian giữ lệnh
#: trung bình (20,3 phiên, CLAUDE.md); 5 là nhịp lực cao nhất đã đối chiếu.
NHIP = (5, 21)

#: Độ dài dữ liệu chưa nhìn, tính bằng PHIÊN: 1 · 3 · 6 · 12 tháng.
CUA_SO = (21, 63, 126, 252)

#: Tổng số ứng viên đã sàng K — ngưỡng Bonferroni 0,05/K, HAI PHÍA. 1 = một
#: ứng viên đơn lẻ · 20 = trần sàng một tháng (5/tuần) · 260 = trần một năm.
SO_UNG_VIEN = (1, 20, 260)
ALPHA = 0.05

#: Nền của phép tiêm — xem docstring đầu file.
NEN = ("px_sma50", "stoch_kd")

#: Mức tiêm, tính theo RÀO HIỆN HÀNH. 0 là ô 'không có gì' — nó phải im.
HE_SO_TIEM = (0.0, 1.0, 2.0)

#: Chi phí thực thi hiện hành LÚC ĐO 21, điểm % mỗi lệnh: ĐO 20, dòng 2 (theo ngày).
#: Không phải hằng số của mô hình — là kết quả đo, nên ghi nguồn. ĐO 22 (30/09/2026)
#: nay đo 0,96; ĐO 21 đã ký và chạy với 0,76 nên hằng số KHÔNG đổi theo.
CHI_PHI_THUC_THI_HIEN_HANH = 0.76

#: Số lượt mỗi ô, và số hoán vị mỗi lượt.
R_TIEM = 30
SO_HOAN_VI = 2000

#: Một cửa sổ cần ít nhất chừng này mã ĐỦ dữ liệu suốt cửa sổ; rổ quét thật
#: có ~70 mã (tab `decisions`, 29/09/2026).
MIN_MA = 40

#: Lực tối thiểu để gọi là BẮT ĐƯỢC — cùng quy ước ĐO 16.
LUC_TOI_THIEU = D.LUC_TOI_THIEU

#: Hai null lệch nhau quá tỷ lệ này ở cửa sổ dài thì máy đo KHÔNG qua.
LECH_NULL_TOI_DA = 0.25

HAT_GIONG = 20260929

_ND = NormalDist()


# ── dữ liệu ──────────────────────────────────────────────────────────────

def bang_rong(kh: dict, h: int, ten_nen: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(nhãn, nền) dạng RỘNG: ngày × mã, cắt `E.MIN_HIST` phiên đầu mỗi mã.

    Cắt đúng như `E._bang`: dưới mốc ấy SMA50/SMA200 trả None nên đặc trưng
    NGHÈO, và trộn hai chế độ là trộn hai phân phối (BƯỚC 2).
    """
    nhan = E.nhan_vuot_ro(kh, h)
    Y, X = {}, {}
    for ma, d in kh.items():
        dt = E.dac_trung(d)[ten_nen].iloc[E.MIN_HIST:]
        Y[ma] = nhan[ma].reindex(dt.index)
        X[ma] = dt
    Yw = pd.DataFrame(Y).sort_index()
    Xw = pd.DataFrame(X).reindex(Yw.index)
    return Yw, Xw


def cua_so(Yw: pd.DataFrame, Xw: pd.DataFrame, i0: int, W: int,
           min_ma: int = MIN_MA):
    """Ma trận W × M của cửa sổ bắt đầu ở hàng `i0`; chỉ giữ mã ĐỦ cả W phiên.

    Trả None khi không đủ `min_ma` mã — cửa sổ ấy không được rút.
    """
    y = Yw.iloc[i0:i0 + W]
    x = Xw.iloc[i0:i0 + W]
    if len(y) < W:
        return None
    du = y.notna().all() & x.notna().all()
    if int(du.sum()) < min_ma:
        return None
    cot = du[du].index
    return (x[cot].to_numpy(float), y[cot].to_numpy(float),
            str(y.index[0]), str(y.index[-1]), list(cot))


def diem_bat_dau(Yw: pd.DataFrame, Xw: pd.DataFrame, W: int,
                 min_ma: int = MIN_MA) -> list[int]:
    """Mọi hàng bắt đầu một cửa sổ W phiên có đủ `min_ma` mã đầy đủ."""
    ok_y = Yw.notna().astype(int)
    ok_x = Xw.notna().astype(int)
    du = (ok_y * ok_x).rolling(W).min().shift(-(W - 1))
    dem = (du == 1).sum(axis=1)
    return [i for i in range(len(Yw) - W + 1) if int(dem.iloc[i]) >= min_ma]


# ── thống kê ─────────────────────────────────────────────────────────────

def ic_gop(X: np.ndarray, Y: np.ndarray) -> float:
    """IC GỘP của cửa sổ — đi qua `E.rho_hang`, không tính lại."""
    return E.rho_hang(X.ravel(), Y.ravel())


def _hang_giua(A: np.ndarray) -> np.ndarray:
    """Hạng GỘP của cả ma trận, trừ trung bình — đúng cách `E.rho_hang` xếp."""
    r = pd.Series(A.ravel()).rank().to_numpy()
    return (r - r.mean()).reshape(A.shape)


def null_hoan_vi_ma(X: np.ndarray, Y: np.ndarray, rng,
                    so: int = SO_HOAN_VI) -> np.ndarray:
    """IC gộp dưới null: cột nhãn của mã j gán cho mã π(j).

    Hạng GỘP không đổi khi hoán vị cột (cùng một tập giá trị), nên
    Σ_t Σ_j RX[t,j]·RY[t,π(j)] = Σ_j C[j, π(j)] với C = RXᵀ RY — mỗi hoán vị
    chỉ còn M phép lấy phần tử. Hoán vị đồng nhất cho LẠI ĐÚNG `ic_gop`
    (có test khoá).
    """
    RX, RY = _hang_giua(X), _hang_giua(Y)
    mau = float(np.sqrt((RX * RX).sum() * (RY * RY).sum()))
    if not mau:
        return np.zeros(so)
    C = RX.T @ RY
    M = C.shape[0]
    hang = np.arange(M)
    out = np.empty(so)
    for i in range(so):
        out[i] = C[hang, rng.permutation(M)].sum() / mau
    return out


def tri_so_p_z(ic: float, null: np.ndarray) -> float:
    """p HAI PHÍA theo xấp xỉ chuẩn của null: z = (ic − TB) / SD.

    Không đếm đuôi thực nghiệm: ở K = 260 ngưỡng là 0,0002, và 2.000 hoán
    vị không chạm tới đó — `(1 + k)/(1 + n)` sẽ không bao giờ xuống dưới
    0,0005. Xấp xỉ chuẩn phải CHỨNG MINH được bằng ô 'không có gì' ở K = 1:
    nếu nó kêu quá `D.nguong_im` thì cả phép đo không đọc được.
    """
    sd = float(np.std(null))
    if sd == 0.0:
        return 1.0
    z = (ic - float(np.mean(null))) / sd
    return 2.0 * (1.0 - _ND.cdf(abs(z)))


def rao_hien_hanh(sigma: float, p: float = 0.05) -> float:
    """Rào hoà vốn với chi phí HIỆN HÀNH — cùng công thức `E.rao_hoa_von`."""
    return (ROUND_TRIP_COST_PCT + CHI_PHI_THUC_THI_HIEN_HANH) / (
        sigma * E.e_z_tren(p))


def _chuan(A: np.ndarray) -> np.ndarray:
    s = float(A.std())
    return (A - A.mean()) / s if s else A - A.mean()


def tiem(X: np.ndarray, Y: np.ndarray, muc: float, rng) -> np.ndarray:
    """Ứng viên GIẢ: tương quan `muc` với nhãn + nền RỜI nhãn.

    Nền là cột thật của mã KHÁC (hoán vị cột không điểm cố định), nên nó giữ
    nguyên tự tương quan của đặc trưng thật mà không mang một chút liên kết
    nào của chính mã ấy với nhãn của nó — bản 3 của `K.chung_cu_duong_kn`,
    đổi phép dịch vòng thành phép hoán vị mã vì cửa sổ ngắn không dịch được.
    """
    M = X.shape[1]
    while True:
        pi = rng.permutation(M)
        if not np.any(pi == np.arange(M)):
            break
    nen = _chuan(X[:, pi])
    return muc * _chuan(Y) + np.sqrt(max(1.0 - muc ** 2, 0.0)) * nen


def mot_luot(Yw, Xw, W: int, muc: float, bat_dau: list[int], rng,
             so: int = SO_HOAN_VI) -> dict:
    """MỘT ứng viên giả trên MỘT cửa sổ rút ngẫu nhiên."""
    i0 = bat_dau[int(rng.integers(len(bat_dau)))]
    X, Y, d0, d1, _ = cua_so(Yw, Xw, i0, W)
    G = tiem(X, Y, muc, rng)
    ic = ic_gop(G, Y)
    null = null_hoan_vi_ma(G, Y, rng, so)
    return {"ic": ic, "p": tri_so_p_z(ic, null), "tu": d0, "den": d1,
            "so_ma": X.shape[1]}


def dem_bat(luot: list[dict], alpha: float) -> int:
    return sum(1 for v in luot if v["p"] < alpha)


def doc_o(k_bat: int, r: int, k_im: int, alpha_k1: float) -> str:
    """Một ô (nền, h, W, K): BẮT / KHÔNG, hoặc KHÔNG ĐỌC khi máy đo hỏng.

    Ô 'không có gì' ở K = 1 phải im theo `D.nguong_im` — đó là phép kiểm
    xấp xỉ chuẩn của `tri_so_p_z`. Dưới `D.R_TOI_THIEU` lượt thì không phán.
    """
    if r < D.R_TOI_THIEU or k_im > D.nguong_im(r, alpha_k1):
        return "KHONG DOC"
    return "BAT" if k_bat / r >= LUC_TOI_THIEU else "KHONG"


def cua_so_nho_nhat(bang: dict, nen: str, h: int, K: int) -> int | None:
    """W nhỏ nhất mà ô (nen, h, W, K) BẮT ở mức 1× rào; None nếu không có."""
    for W in CUA_SO:
        if bang.get((nen, h, W, K)) == "BAT":
            return W
    return None


def phan_dinh(bang: dict, doi_chieu_qua: bool) -> tuple[int, str]:
    """Đọc theo ĐÚNG bảng kết cục đã ký (ĐO 21). Ô chuẩn: h = 21, K = 20.

    Đọc ở cột nền BẤT LỢI cho kết luận: W nhỏ nhất lấy MAX qua hai nền —
    nền nào cần nhiều phiên hơn thì kết luận theo nền ấy. Một nền không
    bắt được ở cửa sổ nào là đủ để kết luận không bắt được.
    """
    if not doi_chieu_qua:
        return 2, "KHONG DOC — null hoan vi ma khong qua doi chieu"
    o = [bang.get((n, 21, W, 20)) for n in NEN for W in CUA_SO]
    if any(v in (None, "KHONG DOC") for v in o):
        return 2, "KHONG DOC — co o thieu hoac o 'khong co gi' keu"
    w = [cua_so_nho_nhat(bang, n, 21, 20) for n in NEN]
    if any(v is None for v in w):
        return 0, "KET CUC C — 252 phien chua nhin van KHONG bat duoc 1x rao"
    w_max = max(w)
    if w_max <= 21:
        return 0, "KET CUC A — mot thang (21 phien) du bat 1x rao"
    return 0, f"KET CUC B — can {w_max} phien chua nhin de bat 1x rao"


# ── đối chiếu null mới với null đã kiểm ──────────────────────────────────

def doi_chieu_null(Yw, Xw, h: int, W: int, rng, so: int = 400) -> dict:
    """Ngưỡng 95% hai phía của null HOÁN VỊ MÃ so với null DỊCH VÒNG.

    Cùng cửa sổ, cùng nền (cột thật của mã khác — rời nhãn), cùng IC. Cửa sổ
    `W` phải đủ dài để `E.san_nhieu` dịch được mọi mã (W > 2(h+1)).
    """
    bat_dau = diem_bat_dau(Yw, Xw, W)
    i0 = bat_dau[int(rng.integers(len(bat_dau)))]
    X, Y, d0, d1, _ = cua_so(Yw, Xw, i0, W)
    G = tiem(X, Y, 0.0, rng)
    m = X.shape[1]
    # trải theo MÃ: mỗi mã một khối liền để E.san_nhieu dịch trong từng mã
    g, y = G.T.ravel(), Y.T.ravel()
    chi_so = {j: np.arange(j * W, (j + 1) * W) for j in range(m)}
    dv = E.san_nhieu(lambda yp, _g=g: E.rho_hang(_g, yp), y, chi_so, h, rng,
                     so=so)
    hv = null_hoan_vi_ma(G, Y, rng, so)
    n_dv = float(np.quantile(np.abs(dv), 0.95))
    n_hv = float(np.quantile(np.abs(hv), 0.95))
    return {"h": h, "W": W, "tu": d0, "den": d1, "so_ma": m,
            "nguong_dich_vong": n_dv, "nguong_hoan_vi_ma": n_hv,
            "ty_le": n_hv / n_dv if n_dv else float("inf")}


def qua_doi_chieu(ds: list[dict]) -> bool:
    """Mọi cặp lệch không quá `LECH_NULL_TOI_DA` theo tỷ lệ; rỗng thì False."""
    if not ds:
        return False
    return all(abs(d["ty_le"] - 1.0) <= LECH_NULL_TOI_DA for d in ds)


# ── chạy ─────────────────────────────────────────────────────────────────

def _chay_doi_chieu(kh: dict, rng) -> list[dict]:
    ra = []
    print("\n== DOI CHIEU NULL: hoan vi ma vs dich vong (E.san_nhieu) ==")
    for nen in NEN:
        for h in NHIP:
            Yw, Xw = bang_rong(kh, h, nen)
            d = doi_chieu_null(Yw, Xw, h, 252, rng)
            d["nen"] = nen
            ra.append(d)
            print(f"  nen {nen:>9} h={h:>2} W=252 {d['tu']}->{d['den']}"
                  f" {d['so_ma']} ma · 95% dich vong {d['nguong_dich_vong']:.4f}"
                  f" · hoan vi ma {d['nguong_hoan_vi_ma']:.4f}"
                  f" · ty le {d['ty_le']:.3f}")
    ok = qua_doi_chieu(ra)
    print(f"  -> {'QUA' if ok else 'KHONG QUA'} (lech toi da"
          f" {LECH_NULL_TOI_DA:.0%})")
    return ra


def main(tham_so: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="DO 21 — luc vong xac nhan")
    ap.add_argument("--doi-chieu", action="store_true",
                    help="chi doi chieu hai null, khong do luc")
    ap.add_argument("--r", type=int, default=R_TIEM)
    ap.add_argument("--hoan-vi", type=int, default=SO_HOAN_VI)
    ap.add_argument("--hat", type=int, default=HAT_GIONG)
    a = ap.parse_args(tham_so)

    kh = E.nap_gia(CACHE_GIA)
    if len(kh) < MIN_MA:
        print(f"CHUA KIEM DUOC — {len(kh)} ma trong {CACHE_GIA}")
        return 2
    rng = np.random.default_rng(a.hat)
    print(f"DO 21 · {CACHE_GIA.name} · {len(kh)} ma · R={a.r} ·"
          f" {a.hoan_vi} hoan vi · hat {a.hat}")

    dc = _chay_doi_chieu(kh, rng)
    if a.doi_chieu:
        return 0 if qua_doi_chieu(dc) else 2

    bang: dict = {}
    for nen in NEN:
        for h in NHIP:
            Yw, Xw = bang_rong(kh, h, nen)
            sigma = float(np.nanstd(Yw.to_numpy()))
            rao = rao_hien_hanh(sigma)
            print(f"\n== nen {nen} · h = {h} · sigma nhan {sigma:.3f}% ·"
                  f" rao hien hanh {rao:.4f} (rao cu E: {E.rao_hoa_von(sigma):.4f}) ==")
            for W in CUA_SO:
                bd = diem_bat_dau(Yw, Xw, W)
                if not bd:
                    print(f"  W={W}: KHONG co cua so nao du {MIN_MA} ma")
                    continue
                luot = {hs: [mot_luot(Yw, Xw, W, hs * rao, bd, rng, a.hoan_vi)
                             for _ in range(a.r)] for hs in HE_SO_TIEM}
                k_im = dem_bat(luot[0.0], ALPHA)
                print(f"  W={W:>3} ({len(bd)} diem bat dau)")
                for hs in HE_SO_TIEM:
                    ic = np.array([v["ic"] for v in luot[hs]])
                    dong = " · ".join(
                        f"K={K}: {dem_bat(luot[hs], ALPHA / K)}/{a.r}"
                        for K in SO_UNG_VIEN)
                    print(f"    tiem {hs:.0f}x rao ({hs * rao:.4f}): IC TB"
                          f" {ic.mean():+.4f} SD {ic.std():.4f} | {dong}")
                    print("      p: " + " ".join(
                        f"{v['p']:.4f}" for v in sorted(luot[hs],
                                                        key=lambda v: v["p"])))
                for K in SO_UNG_VIEN:
                    bang[(nen, h, W, K)] = doc_o(
                        dem_bat(luot[1.0], ALPHA / K), a.r, k_im, ALPHA)
                print("    doc o 1x rao: " + " · ".join(
                    f"K={K} {bang[(nen, h, W, K)]}" for K in SO_UNG_VIEN)
                    + f"   (o 'khong co gi' K=1 keu {k_im}/{a.r},"
                    f" nguong im {D.nguong_im(a.r, ALPHA)})")

    ma, cau = phan_dinh(bang, qua_doi_chieu(dc))
    print(f"\n== PHAN DINH (o chuan h=21, K=20) ==\n  {cau}")
    for nen in NEN:
        for h in NHIP:
            print(f"  nen {nen:>9} h={h:>2}: W nho nhat bat 1x rao —"
                  + " · ".join(f" K={K}: {cua_so_nho_nhat(bang, nen, h, K)}"
                               for K in SO_UNG_VIEN))
    return ma


if __name__ == "__main__":
    sys.exit(main())
