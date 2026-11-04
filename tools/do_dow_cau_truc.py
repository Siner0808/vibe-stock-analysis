"""ĐO 34 — cấu trúc giá theo lý thuyết Dow, CHỈ MUA / ĐỨNG NGOÀI (BƯỚC 251 = Lát 4a của đặc tả Dow).

Tiêu chí ký trước: `docs/TIEU-CHI-DOC-TRUOC.md`, mục *ĐO 34* (commit riêng, TRƯỚC mọi dòng mã). Mọi hằng số,
chuẩn, đối chứng và kết cục ở đây chép từ mục ấy; đổi một con số sau khi nhìn kết quả là vi phạm bất biến 7.

BƯỚC này (Lát 4a) dựng DỤNG CỤ và chạy ĐỐI CHỨNG. Nó KHÔNG đọc, KHÔNG tính, KHÔNG in lợi nhuận của danh mục Dow
so với chuẩn nào, trên dữ liệu thật. Đường ra kết cục chỉ chạy trên dữ liệu TỔNG HỢP trong test; trên dữ liệu thật nó
bị khoá sau `CHO_PHEP_DOC_KET_QUA_THAT` (= False ở Lát 4a) VÀ một cờ gõ nguyên văn (`CAU_XAC_NHAN_LAT_4B`) — Lát 4b
(BƯỚC 253) lật khoá trong một commit riêng, chạy MỘT lần qua `chay_lat_4b` rồi khoá lại. Phần dưới nói về Lát 4a.

    ./.venv/Scripts/python.exe tools/do_dow_cau_truc.py doi-chung --cache <thư mục cache> [--ghi X.json]
    ./.venv/Scripts/python.exe tools/do_dow_cau_truc.py cau-hinh-ktc
    ./.venv/Scripts/python.exe tools/do_dow_cau_truc.py khoang-cach-ii --cache <thư mục cache>   (BƯỚC 252; KHÔNG tính Δ của Dow)
    ./.venv/Scripts/python.exe tools/do_dow_cau_truc.py ket-qua --cache <thư mục cache> --xac-nhan "<câu>" [--ghi X.json]   (khoá; Lát 4b)

CHỈ ĐỌC: không mạng, không `import vnstock`, không ghi cache, không đọc sổ lệnh. Chỉ ghi MỘT file JSON kết quả
ở đường dẫn người gọi chọn (`--ghi`).

BƯỚC 252 SỬA văn bản ĐO 34 TRƯỚC lượt chạy duy nhất (khối `### SỬA ĐO 34` ở cuối mục, người dùng ĐÃ DUYỆT 03/11/2026): đối chứng (ii) đối
chiếu kỳ vọng giải tích (S1), đối chứng (iii) có lưới, MDE và ô K0 20× rào (S2), bản đồ kết cục toàn phần với lớn = 2H (S3), trọng số
1/71 giữ nguyên (S4), báo kèm bỏ R8/R9 (S5). Các hằng `HE_SO_*`, `SO_LAP_TIEM`, hàm `ket_cuc`, `doi_chung_ii`, `doi_chung_iii` theo khối ấy.

Quy ước khớp (chép từ ĐO 34 + sổ ảo, chọn lúc VIẾT MÃ, TRƯỚC khi có số):
- Trạng thái `s[t]` (thủy triều swing = `tang`, biết tới hết nến `t`) là mục tiêu của phiên `t+1`: vào ở GIÁ MỞ CỬA
  `t+1`, ra ở giá mở cửa phiên sau phiên điều kiện hết. Kịch trần một giá: lệnh mua huỷ, thử lại phiên sau nếu còn
  trạng thái; kịch sàn: lệnh bán chờ, thử lại phiên sau (`vong_doi_lenh.khoa_bien`, qua cờ của `cau_truc_gia`).
- Lợi nhuận một phiên = (1 + w_trước × lợi nhuận qua đêm) × (1 + w_sau × lợi nhuận trong phiên) − 1, với w_trước là
  vị thế TRƯỚC giờ mở cửa và w_sau SAU lệnh khớp ở giờ mở cửa; ngày giữ trọn phiên cho đúng đóng/đóng − 1.
- Phí: nửa `paper_metrics.ROUND_TRIP_COST_PCT` mỗi chiều (+ trượt giá bước giá của `truot_gia.truot_gia`, vốn
  `paper_trading.VON_DANH_MUC_VND / 71` mỗi mã), tính trên giá trị vị thế đổi. Cuối vùng: đóng ở giá đóng cửa.
- Mức đầu tư `e = (w_trước + w_sau) / 2`, x_t = r_danh_mục − e_t × r_rổ; r_rổ = trung bình các mã đang trong vùng
  của lợi nhuận "luôn giữ" (gồm cả ngày đầu: mở→đóng).
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))
sys.path.insert(0, str(GOC))

import cau_truc_gia as C  # noqa: E402
import san_dau as S  # noqa: E402
from data_quality import price_multiplier  # noqa: E402
from san_giao_dich import san_cua  # noqa: E402
from truot_gia import BAN, MUA, khoi_luong_hop_le, truot_gia  # noqa: E402
from vn100_symbols import CUSTOM_WATCHLIST_SYMBOLS  # noqa: E402

# ── hằng số chép từ ĐO 34 ─────────────────────────────────────────────────────────────────
SO_MA = 71                       # trọng số 1/71 mỗi mã đang giữ (ĐO 34, Luật ghim)
HAT = 0                          # hạt giống mọi phép rút của dụng cụ này
SO_LUOT_NGAU_NHIEN = 1000        # chuẩn (iv): 1.000 lượt rút
DICH_TOI_THIEU = 252             # bản đồng bộ thời gian: dịch vòng ≥ 252 phiên
PHIEN_SMA = 200                  # chuẩn (ii)
CUA_SO_TSMOM = (21, 63, 252)     # chuẩn (iii)
SO_LAP_TIEM = 100                # đối chứng (iii), SỬA S2 (BƯỚC 252): 100 lượt lặp mỗi ô (30 ở bản ký; lỗi 99: tỷ lệ chứ không phải một lượt)
NGUONG_BAT_TIEM = 0.80           # ... ô K0 phải bắt ≥ 80%
HE_SO_LUOI_TIEM = (0.0, 0.5, 1.0, 2.0, 5.0, 7.0, 10.0, 14.0, 20.0)   # SỬA S2: lưới hệ số × rào hoà vốn
HE_SO_K0 = 20.0                  # SỬA S2: ô PHẢI bắt được ≥ 80% (20× rào) — trượt nghĩa là máy hỏng, không phải thiếu lực
NGAY_NAM = 252                   # đổi lợi thế mỗi ngày sang mỗi năm
PHI_NHAY_PCT = 0.76              # độ nhạy phí: cận trên của dải bán lẻ (CLAUDE.md)
NGUONG_THANG_A_CONG = 0.95       # A⁺: Dow thắng ≥ 95% lượt rút (iv)
HE_SO_NHO, HE_SO_LON = 0.5, 2.0  # SỬA S3: ngưỡng nhỏ = 0,5 × H, lớn = 2 × H (H = nửa bề rộng KTC của Δ_(i)); bản ký: lớn = 1 × H
SO_SIGMA_DOI_CHUNG_II = 2.0      # đối chứng (ii): trong khoảng 2 sai số chuẩn
CUA_SO_SU_KIEN = 21              # H2: 21 phiên từ mở cửa t+1
BAM_CACHE_KY = "acf6dca1dd38d5157ee397bbccb7f82d662698b318a6dcf6b72617335bf44d6e"
DUONG_BANG_DO_PHU = GOC / "docs" / "san-dau-do-phu.json"
DUONG_MOC_SACH = GOC / "docs" / "moc_du_lieu_sach.json"

#: Khoá lượt chạy trên dữ liệu THẬT. Lát 4a để False; Lát 4b (BƯỚC 252) lật nó trong một commit riêng.
CHO_PHEP_DOC_KET_QUA_THAT = True     # BUOC 253, commit MO KHOA rieng: chi de chay ket-qua MOT LAN; commit sau khoa lai
CAU_XAC_NHAN_LAT_4B = "DOC KET QUA DO 34 MOT LAN"

KET_CUC_K0, KET_CUC_A, KET_CUC_A_CONG, KET_CUC_B, KET_CUC_C = "K0", "A", "A+", "B", "C"
# Bản đồ kết cục sau SỬA S3 (BƯỚC 252) là TOÀN PHẦN: không còn nhãn "không phân loại được" hay "mâu thuẫn".


def phi_nua(phi_pct: float | None = None) -> float:
    """Nửa phí vòng mua–bán, ở dạng tỷ lệ. Mặc định `paper_metrics.ROUND_TRIP_COST_PCT` (nhập lười: kéo theo
    `paper_trading`, không cần khi test hàm thuần)."""
    if phi_pct is None:
        from paper_metrics import ROUND_TRIP_COST_PCT
        phi_pct = ROUND_TRIP_COST_PCT
    return float(phi_pct) / 100.0 / 2.0


# ── dữ liệu một mã → ma trận (ngày toàn cục × mã) ─────────────────────────────────────────
@dataclass
class MaTran:
    """Mọi mảng có hình (T, N): T ngày toàn cục, N mã. `vung` là True trong vùng đọc của từng mã."""
    ngay: list
    ma: list
    qua_dem: np.ndarray        # mở / đóng_trước − 1
    trong_phien: np.ndarray    # đóng / mở − 1
    dong: np.ndarray
    vung: np.ndarray           # bool: ngày thuộc vùng đọc của mã
    cuoi_vung: np.ndarray      # bool: ngày cuối vùng của mã
    khoa_tran: np.ndarray      # bool: nến kịch trần (lệnh mua huỷ)
    khoa_san: np.ndarray       # bool: nến kịch sàn (lệnh bán chờ)
    truot_mua: np.ndarray      # tỷ lệ trượt bất lợi khi mua ở giá mở cửa
    truot_ban: np.ndarray      # ... khi bán


def chon_vung(ngay_ma: np.ndarray, moc: str | None, vung: str) -> np.ndarray:
    """Mặt nạ vùng đọc của một mã: `sach` = các phiên TRƯỚC mốc dữ liệu sạch; `sau_moc` = từ mốc trở đi;
    `tat_ca` = mọi phiên. Mốc rỗng (mã vắng trong `moc_theo_ma`) với `sach` → không phiên nào."""
    if vung == "tat_ca":
        return np.ones(len(ngay_ma), dtype=bool)
    if moc is None:
        return np.zeros(len(ngay_ma), dtype=bool) if vung == "sach" else np.ones(len(ngay_ma), dtype=bool)
    if vung == "sach":
        return ngay_ma < moc
    if vung == "sau_moc":
        return ngay_ma >= moc
    raise ValueError(f"vung khong ro: {vung!r}")


def dung_ma_tran(chuoi: dict, vung_ma: dict, *, truot: bool = True, von_vnd: float | None = None) -> MaTran:
    """Dựng `MaTran` từ `chuoi[ma] = (df, he_so, san)` và `vung_ma[ma]` (mặt nạ bool theo hàng của df).
    Ngày toàn cục = hợp các ngày trong vùng của mọi mã; mã vắng hàng ở một ngày giữa vùng giữ giá (lợi nhuận 0)."""
    if von_vnd is None:
        from paper_trading import VON_DANH_MUC_VND
        von_vnd = VON_DANH_MUC_VND
    ma_ds = [m for m in chuoi if vung_ma[m].any()]
    ngay = sorted({str(t)[:10] for m in ma_ds for t in chuoi[m][0]["time"].to_numpy()[vung_ma[m]]})
    chi_so = {d: i for i, d in enumerate(ngay)}
    T, N = len(ngay), len(ma_ds)
    z = lambda: np.zeros((T, N))  # noqa: E731
    qd, tp, dg = z(), z(), z()
    vg = np.zeros((T, N), dtype=bool)
    cv, kt, ks = np.zeros((T, N), dtype=bool), np.zeros((T, N), dtype=bool), np.zeros((T, N), dtype=bool)
    tm, tb = z(), z()
    for j, m in enumerate(ma_ds):
        df, he, san = chuoi[m]
        mo = pd.to_numeric(df["open"]).to_numpy(float)
        dong = pd.to_numeric(df["close"]).to_numpy(float)
        cao = pd.to_numeric(df["high"]).to_numpy(float)
        thap = pd.to_numeric(df["low"]).to_numpy(float)
        kl = pd.to_numeric(df["volume"]).to_numpy(float) if "volume" in df.columns else np.zeros(len(df))
        nen = C.chuan_bi_nen(df, san)
        hang = np.flatnonzero(vung_ma[m])
        a, b = chi_so[str(df["time"].iloc[hang[0]])[:10]], chi_so[str(df["time"].iloc[hang[-1]])[:10]]
        vg[a:b + 1, j] = True
        cv[b, j] = True
        dg[:, j] = np.nan
        for i in hang:                         # `hang` = các hàng của df trong vùng đọc
            t = chi_so[str(df["time"].iloc[i])[:10]]
            dg[t, j] = dong[i]
            if i > 0:
                qd[t, j] = mo[i] / dong[i - 1] - 1.0
            tp[t, j] = dong[i] / mo[i] - 1.0
            kt[t, j] = nen[i].khoa_bien == "KICH_TRAN"
            ks[t, j] = nen[i].khoa_bien == "KICH_SAN"
            if truot:
                gia = mo[i] * he
                sl = khoi_luong_hop_le(int(von_vnd / SO_MA / gia)) if gia > 0 else 0
                bar = {"high": cao[i] * he, "low": thap[i] * he, "volume": kl[i]}
                tm[t, j] = truot_gia(gia, MUA, bar, sl, san)["truot_pct"] / 100.0
                tb[t, j] = truot_gia(gia, BAN, bar, sl, san)["truot_pct"] / 100.0
        # điền giá đóng cửa cho ngày vắng hàng giữa vùng; ngoài vùng = 0 (không dùng)
        cot = dg[:, j]
        for t in range(a, b + 1):
            if np.isnan(cot[t]):
                cot[t] = cot[t - 1] if t > a else 1.0
        cot[np.isnan(cot)] = 0.0
    return MaTran(ngay=ngay, ma=ma_ds, qua_dem=qd, trong_phien=tp, dong=dg, vung=vg, cuoi_vung=cv,
                  khoa_tran=kt, khoa_san=ks, truot_mua=tm, truot_ban=tb)


# ── động cơ khớp: một chỗ duy nhất tính lợi nhuận, phí và mức đầu tư ───────────────────────
def chay_dong_co(muc_tieu: np.ndarray, M: MaTran, phi: float, *, khoa: bool = True, truot: bool = True) -> dict:
    """Chạy vị thế theo `muc_tieu` (L, T, N) — trọng số mục tiêu biết tới hết nến t, hiệu lực từ mở cửa t+1 — trên MỌI
    làn L cùng lúc (vectơ hoá trên L và N, vòng lặp theo ngày). Trả (L, T) cho `ret` (lợi nhuận gộp, chia 71),
    `chi_phi` (phí + trượt, chia 71) và `phoi` (mức đầu tư e, chia 71)."""
    L, T, N = muc_tieu.shape
    ret = np.zeros((L, T))
    chi_phi = np.zeros((L, T))
    phoi = np.zeros((L, T))
    w = np.zeros((L, N))
    for t in range(T):
        muon = muc_tieu[:, t - 1, :] if t > 0 else np.zeros((L, N))
        muon = muon * M.vung[t][None, :]
        w_truoc = w
        chan = np.zeros((L, N), dtype=bool)
        if khoa:
            chan = ((muon > w_truoc) & M.khoa_tran[t][None, :]) | ((muon < w_truoc) & M.khoa_san[t][None, :])
        w_sau = np.where(chan, w_truoc, muon)
        d = w_sau - w_truoc
        tm = M.truot_mua[t][None, :] if truot else 0.0
        tb = M.truot_ban[t][None, :] if truot else 0.0
        cp = np.abs(d) * (phi + np.where(d > 0, tm, tb))
        lai = (1.0 + w_truoc * M.qua_dem[t][None, :]) * (1.0 + w_sau * M.trong_phien[t][None, :]) - 1.0
        cuoi = M.cuoi_vung[t][None, :]
        cp = cp + np.where(cuoi, w_sau * (phi + (tb if truot else 0.0)), 0.0)
        ret[:, t] = lai.sum(axis=1) / SO_MA
        chi_phi[:, t] = cp.sum(axis=1) / SO_MA
        phoi[:, t] = ((w_truoc + w_sau) / 2.0).sum(axis=1) / SO_MA
        w = np.where(cuoi, 0.0, w_sau)
    return {"ret": ret, "chi_phi": chi_phi, "phoi": phoi}


def lai_ro_theo_ma(M: MaTran) -> np.ndarray:
    """Lợi nhuận "luôn giữ" của TỪNG mã mỗi ngày (T, N), gộp, không phí/trượt/khoá: ngày đầu vùng mở→đóng, sau đó
    đóng/đóng−1 (khớp động cơ với `muc_tieu` = 1). Ngoài vùng = 0."""
    T, N = M.vung.shape
    dau = M.vung & ~np.vstack([np.zeros((1, N), dtype=bool), M.vung[:-1]])
    lai = np.where(dau, M.trong_phien, (1.0 + M.qua_dem) * (1.0 + M.trong_phien) - 1.0)
    return np.where(M.vung, lai, 0.0)


def ro_trung_binh(M: MaTran) -> np.ndarray:
    """r_rổ mỗi ngày: trung bình các mã đang trong vùng của `lai_ro_theo_ma`."""
    lai = lai_ro_theo_ma(M)
    n = M.vung.sum(axis=1)
    return np.where(n > 0, lai.sum(axis=1) / np.maximum(n, 1), 0.0)


def x_tu_dong_co(kq: dict, ro: np.ndarray) -> np.ndarray:
    """x_t = r_danh_mục(sau phí) − e_t × r_rổ, hình (L, T)."""
    return kq["ret"] - kq["chi_phi"] - kq["phoi"] * ro[None, :]


def cot_tho(kq: dict, ro: np.ndarray, M: MaTran) -> np.ndarray:
    """Cột thô r_danh_mục − r_rổ (ở cùng mức đầu tư tối đa 1/71 mỗi mã): r_rổ nhân n_t/71."""
    return (kq["ret"] - kq["chi_phi"]) - (M.vung.sum(axis=1) / SO_MA * ro)[None, :]


# ── trạng thái Dow theo nến, và các chuẩn dạng trạng thái ─────────────────────────────────
def thuy_trieu_chuoi(r) -> list[str]:
    """Thủy triều swing tại MỖI nến, tính nhân quả: nến `t` dùng các dòng pivot swing có `chi_so_biet ≤ t`
    (phát lại theo nhóm `chi_so_biet`, cùng `cau_truc_gia._ap_dong` / `_thuy_trieu_tu_swing`)."""
    dau: dict = {}
    for p in r.nhat_ky:
        if p.cap == C.CAP_SWING:
            dau.setdefault(p.chi_so_biet, []).append(p)
    out = [C.CHUA_DU] * r.so_nen
    sw, hien, bat_dau = [], C.CHUA_DU, 0
    for b in sorted(dau):
        for p in dau[b]:
            sw = C._ap_dong(sw, p)
        moi = C._thuy_trieu_tu_swing(sw)[0]
        if moi != hien:
            out[bat_dau:b] = [hien] * (b - bat_dau)
            hien, bat_dau = moi, b
    out[bat_dau:] = [hien] * (r.so_nen - bat_dau)
    return out


def trang_thai_dow(df: pd.DataFrame, he: float, san: str, ho: str = C.MAC_DINH[0],
                   tham_so: tuple | None = None) -> np.ndarray:
    """Bool (n,): thủy triều swing = `tang`, biết tới hết nến t."""
    ts = C.MAC_DINH[1] if tham_so is None else tham_so
    r = C.doc_cau_truc(df, he_so_gia=he, san=san, ho=ho, tham_so=ts)
    return np.array([x == C.TANG for x in thuy_trieu_chuoi(r)], dtype=bool)


def trang_thai_sma200(dong: np.ndarray, phien: int = PHIEN_SMA) -> np.ndarray:
    """Chuẩn (ii): đóng cửa > SMA200 của chính nó, biết tới hết t. Chưa đủ 200 phiên → False."""
    s = pd.Series(dong).rolling(phien, min_periods=phien).mean().to_numpy()
    return np.where(np.isnan(s), False, dong > s)


def trong_so_tsmom(dong: np.ndarray, cua_so: tuple = CUA_SO_TSMOM) -> np.ndarray:
    """Chuẩn (iii): trung bình dấu lợi nhuận 21, 63, 252 phiên, cắt về [0, 1] (dạng long-only của tín hiệu
    1/3/12 tháng). Chưa đủ lịch sử cho một cửa sổ thì cửa sổ ấy đóng góp 0 (không đoán)."""
    n = len(dong)
    tong = np.zeros(n)
    for k in cua_so:
        if n > k:
            lai = np.full(n, np.nan)
            lai[k:] = dong[k:] / dong[:-k] - 1.0
            tong += np.where(np.isnan(lai), 0.0, np.sign(lai))
    return np.clip(tong / len(cua_so), 0.0, 1.0)


def doan_giu(s: np.ndarray) -> list[int]:
    """Độ dài các đoạn liên tiếp True của `s` (chuẩn (iv): cùng số khoảng nắm giữ, cùng độ dài)."""
    kq, dem = [], 0
    for x in s:
        if x:
            dem += 1
        elif dem:
            kq.append(dem)
            dem = 0
    if dem:
        kq.append(dem)
    return kq


def dat_ngau_nhien(do_dai: list[int], n: int, rng) -> np.ndarray:
    """Đặt các đoạn `do_dai` (theo thứ tự) vào `n` vị trí ở ngày bắt đầu ngẫu nhiên, không chồng, cách nhau ≥ 1:
    phần trống được chia ngẫu nhiên đều (sao và vạch) vào k+1 khe, k−1 khe giữa bắt buộc ≥ 1."""
    s = np.zeros(n, dtype=bool)
    k = len(do_dai)
    if k == 0:
        return s
    tu_do = n - sum(do_dai) - (k - 1)
    if tu_do < 0:
        raise ValueError("cac doan khong vua trong vung (can cach nhau >= 1)")
    vach = np.sort(rng.choice(tu_do + k, size=k, replace=False))
    khe = np.diff(np.concatenate([[-1], vach])) - 1          # k khe trước mỗi đoạn, ≥ 0
    vi_tri = 0
    for i, dd in enumerate(do_dai):
        vi_tri += int(khe[i]) + (1 if i > 0 else 0)
        s[vi_tri:vi_tri + dd] = True
        vi_tri += dd
    return s


def dich_vong(s: np.ndarray, rng, toi_thieu: int = DICH_TOI_THIEU) -> np.ndarray:
    """Bản đồng bộ thời gian: dịch vòng chuỗi trạng thái đi k phiên ngẫu nhiên, k ≥ `toi_thieu`. Vùng ngắn hơn
    `toi_thieu + 1` không đủ chỗ: dùng k trong [1, n−1] (người gọi đếm các mã này)."""
    n = len(s)
    if n < 2:
        return s.copy()
    lo = toi_thieu if n > toi_thieu else 1
    return np.roll(s, int(rng.integers(lo, n)))


# ── thống kê, KTC của sân đấu, đối chiếu cấu hình khoá ───────────────────────────────────
def doc_bang_do_phu() -> dict:
    return json.loads(DUONG_BANG_DO_PHU.read_text(encoding="utf-8"))


def ktc_cap(a, b, bang: dict | None = None) -> dict:
    """KTC của mean(a) − mean(b) bằng HÀM DUY NHẤT của sân đấu (`san_dau.ktc_co_nhan`, dạng "cap"), kèm nhãn độ phủ.
    KHÔNG viết bản sao thứ hai của hàm KTC (ĐO 34, Luật ghim)."""
    bang = doc_bang_do_phu() if bang is None else bang
    return S.ktc_co_nhan(np.asarray(a, float), np.asarray(b, float), "cap", bang)


def khop_cau_hinh(ktc: dict | None) -> list[str]:
    """Rỗng = cấu hình KTC của lượt tính KHỚP bản ghi `cau_hinh_khoa` (khác rỗng = K0, ĐO 34)."""
    if ktc is None:
        return ["KTC khong duoc tinh (n qua ngan hoac chua co bang do phu)"]
    return S.khop_cau_hinh_khoa(ktc, doc_bang_do_phu()["cau_hinh_khoa"])


def in_cau_hinh_ktc(ktc: dict, ra=None) -> list[str]:
    """In cấu hình KTC lượt tính đã dùng, bản ghi đã khoá và kết quả so (rỗng = KHỚP)."""
    ra = ra or print
    ban_ghi = doc_bang_do_phu()["cau_hinh_khoa"]
    lech = S.khop_cau_hinh_khoa(ktc, ban_ghi)
    ra(f"cấu hình KTC dùng : độ dài khối {ktc['do_dai_yeu_cau']!r} (giải ra {ktc['do_dai']}), vòng {ktc['vong']}, "
       f"hạt {ktc['hat']}, phân vị {ktc['phan_vi']}")
    ra(f"cấu hình đã khoá  : độ dài khối {ban_ghi['do_dai_khoi']!r}, vòng {ban_ghi['vong']}, "
       f"hạt {ban_ghi['hat_bootstrap']}, phân vị {ban_ghi['phan_vi']} (BƯỚC {ban_ghi['buoc']})")
    ra("khop_cau_hinh_khoa: " + ("KHỚP" if not lech else "LỆCH → K0: " + "; ".join(lech)))
    return lech


def tom_tat_x(x_dow: np.ndarray, x_chuan: np.ndarray, bang: dict | None = None) -> dict:
    """Δ = mean(x_dow) − mean(x_chuan) kèm KTC có cặp và nhãn độ phủ."""
    k = ktc_cap(x_dow, x_chuan, bang)
    ktc = k["ktc"]
    return {"delta": float(np.mean(x_dow) - np.mean(x_chuan)), "ktc": ktc, "dong": k["dong"], "n": k["n"],
            "chua_0": None if ktc is None else bool(ktc["can_duoi"] <= 0 <= ktc["can_tren"]),
            "nua_be_rong": None if ktc is None else (ktc["can_tren"] - ktc["can_duoi"]) / 2.0}


# ── kết cục (ký trước, ĐO 34) — hàm thuần, chạy được trên dữ liệu tổng hợp ───────────────────
def ket_cuc(*, delta_i: float, ktc_i: tuple, ktc_ii: tuple, ktc_iii: tuple, thang_iv: float,
            doi_chung_dat: bool) -> dict:
    """Phân loại K0 / B / C / A⁺ / A theo bản ĐO 34 đã SỬA S3 (BƯỚC 252). H = nửa bề rộng KTC của Δ_(i); ngưỡng SUY RA:
    nhỏ = `HE_SO_NHO` × H, lớn = `HE_SO_LON` × H. Xét THEO THỨ TỰ, nhãn đầu khớp thắng, nên bản đồ TOÀN PHẦN (không có nhãn
    thứ sáu): K0 → B (Δ > lớn) → C (Δ < −nhỏ VÀ cận trên KTC < 0) → A⁺ (nhỏ < Δ ≤ lớn, cận dưới KTC(i) > 0, Dow thắng
    ≥ 95%, cận dưới KTC(ii) > 0 hoặc KTC(iii) > 0) → A (mọi thứ còn lại, kèm `ly_do_A`)."""
    if not doi_chung_dat:
        return {"ket_cuc": KET_CUC_K0, "khop": [KET_CUC_K0], "nguong_nho": None, "nguong_lon": None, "ly_do_A": None}
    nua = (ktc_i[1] - ktc_i[0]) / 2.0
    nho, lon = HE_SO_NHO * nua, HE_SO_LON * nua
    ly_do = None
    if delta_i > lon:
        nhan = KET_CUC_B
    elif delta_i < -nho and ktc_i[1] < 0.0:
        nhan = KET_CUC_C
    elif nho < delta_i <= lon and ktc_i[0] > 0.0 and thang_iv >= NGUONG_THANG_A_CONG and \
            (ktc_ii[0] > 0.0 or ktc_iii[0] > 0.0):
        nhan = KET_CUC_A_CONG
    else:
        nhan = KET_CUC_A
        if ktc_i[0] <= 0.0 <= ktc_i[1]:
            ly_do = "a: KTC của Δ_(i) chứa 0"
        elif abs(delta_i) <= nho:
            ly_do = "b: |Δ| ≤ nhỏ"
        elif delta_i > nho:
            ly_do = "c: Δ > nhỏ, KTC loại 0 nhưng thiếu điều kiện của A⁺ (thắng ngẫu nhiên / hơn SMA200 hoặc TSMOM)"
        else:
            ly_do = "d: Δ < −nhỏ mà KTC loại 0 về phía dương (KTC lệch dấu với Δ)"
    return {"ket_cuc": nhan, "khop": [nhan], "nguong_nho": nho, "nguong_lon": lon, "ly_do_A": ly_do}


# ── đối chứng của máy đo ──────────────────────────────────────────────────────────────────
def doi_chung_i(M: MaTran, phi: float) -> dict:
    """(i) Luật "luôn giữ" = cầm rổ trừ đúng MỘT vòng phí mỗi mã: đồng nhất thức trên giá. Với từng mã chạy MỘT làn qua
    CHÍNH động cơ (muc_tieu = 1, không trượt, không khoá): lợi nhuận gộp ghép của làn phải bằng đóng_cuối / (đóng_ngày_vào ÷
    (1 + mở→đóng ngày vào)) − 1, tức đóng cuối / mở cửa ngày vào, và chi phí phải bằng đúng 2 × nửa phí. (Ngày đầu của
    ma trận không vào được vì không có mục tiêu biết từ ngày trước: ngày vào là ngày đầu tiên có mức đầu tư > 0.)"""
    T, N = M.vung.shape
    lech_gia, lech_phi = 0.0, 0.0
    for j in range(N):
        cot = np.zeros((1, T, N))
        cot[0, :, j] = 1.0
        kq = chay_dong_co(cot, M, phi, khoa=False, truot=False)
        b = int(np.flatnonzero(M.vung[:, j])[-1])
        h = int(np.flatnonzero(kq["phoi"][0] > 0)[0])               # ngày vào
        gop = float(np.prod(1.0 + kq["ret"][0, h:b + 1] * SO_MA) - 1.0)
        mo_vao = M.dong[h, j] / (1.0 + M.trong_phien[h, j])
        dung = float(M.dong[b, j] / mo_vao - 1.0)
        lech_gia = max(lech_gia, abs(gop - dung))
        lech_phi = max(lech_phi, abs(kq["chi_phi"].sum() * SO_MA - 2 * phi))
    return {"lech_gia_toi_da": lech_gia, "lech_phi_toi_da": lech_phi, "so_ma": N,
            "dat": lech_gia < 1e-9 and lech_phi < 1e-12}


def rao_hoa_von(M: MaTran, s_dow: np.ndarray, phi: float) -> dict:
    """Rào hoà vốn của luật đang đo = chi phí mỗi ngày ÷ mức đầu tư mỗi ngày (lợi thế mỗi-đơn-vị-đầu-tư-ngày làm
    luật hoà vốn so với rổ). CHỈ ĐỌC CHI PHÍ: lợi nhuận bị đặt bằng 0 trước khi chạy động cơ nên đường này không thể
    rò lợi nhuận (đường không-rò, ĐO 34: không đọc lợi nhuận trước Lát 4b)."""
    khong = MaTran(**{**M.__dict__, "qua_dem": np.zeros_like(M.qua_dem), "trong_phien": np.zeros_like(M.trong_phien)})
    kq = chay_dong_co(s_dow[None].astype(float), khong, phi)
    e = float(kq["phoi"].mean())
    return {"chi_phi_moi_ngay": float(kq["chi_phi"].mean()), "phoi_trung_binh": e,
            "rao": float(kq["chi_phi"].mean() / e) if e > 0 else float("nan")}


def chia_lan(tong: int, co: int):
    d = 0
    while d < tong:
        yield d, min(co, tong - d)
        d += co


def ngau_nhien(M: MaTran, s_dow: np.ndarray, phi: float, kieu: str, so_luot: int, *, hat: int = HAT,
               lan: int = 100, giu_x: bool = False, khoa: bool = True, truot: bool = True, dong_co=None) -> dict:
    """Chuẩn (iv): `so_luot` lượt rút, mỗi lượt một vị thế ngẫu nhiên cho MỌI mã. kieu = "dat" (cùng số khoảng, cùng độ
    dài, ngày bắt đầu ngẫu nhiên), "dich" (dịch vòng ≥ 252) hoặc "hoan" (như "dich" nhưng chuỗi trạng thái của mã j là của
    một mã khác, hoán vị ngẫu nhiên: cắt tương quan giữa thời-gian-trong-thị-trường của mã và độ trôi của mã). Trả trung bình x mỗi lượt (gộp, không phí: `x_tho`) và
    sau phí (`x_phi`), và nếu `giu_x` thì cả chuỗi x_t trung bình qua lượt. `khoa`/`truot` tắt khoá biên / trượt giá của động cơ
    (đối chứng (ii) chạy tắt cả hai); `dong_co` thay động cơ khớp (chỉ để GÀI LỖI vào, xem `LOI_CAY`)."""
    dong_co = chay_dong_co if dong_co is None else dong_co
    rng = np.random.default_rng(hat)
    T, N = s_dow.shape
    ro = ro_trung_binh(M)
    vi_tri = [np.flatnonzero(M.vung[:, j]) for j in range(N)]
    doan = [doan_giu(s_dow[v[0]:v[-1] + 1, j]) for j, v in enumerate(vi_tri)]
    tb_phi, tb_tho, tong_x = [], [], np.zeros(T)
    ngan = 0
    for _, co in chia_lan(so_luot, lan):
        muc = np.zeros((co, T, N), dtype=np.float32)
        hoan = [rng.permutation(N) for _ in range(co)] if kieu == "hoan" else None
        for k in range(co):
            for j in range(N):
                a, b = vi_tri[j][0], vi_tri[j][-1] + 1
                if kieu == "dat":
                    muc[k, a:b, j] = dat_ngau_nhien(doan[j], b - a, rng)
                elif kieu == "hoan":
                    muc[k, a:b, j] = dich_vong(s_dow[a:b, hoan[k][j]], rng)
                else:
                    if b - a <= DICH_TOI_THIEU:
                        ngan += 1
                    muc[k, a:b, j] = dich_vong(s_dow[a:b, j], rng)
        kq = dong_co(muc.astype(float), M, phi, khoa=khoa, truot=truot)
        x = x_tu_dong_co(kq, ro)
        tb_phi.extend(x.mean(axis=1))
        tb_tho.extend((kq["ret"] - kq["phoi"] * ro[None, :]).mean(axis=1))
        tong_x += x.sum(axis=0)
    out = {"x_phi": np.array(tb_phi), "x_tho": np.array(tb_tho), "ma_vung_ngan": ngan}
    if giu_x:
        out["x_t"] = tong_x / so_luot
    return out


def trong_khoang_se(trung_binh: float, sai_so_chuan: float, so_se: float = SO_SIGMA_DOI_CHUNG_II) -> bool:
    """|trung bình| ≤ `so_se` sai số chuẩn (biên đóng). Đối chứng (ii)."""
    return bool(abs(trung_binh) <= so_se * sai_so_chuan)


def doi_chung_ii(M: MaTran, s_dow: np.ndarray, phi: float, so_luot: int = SO_LUOT_NGAU_NHIEN, dong_co=None) -> dict:
    """(ii) SỬA S1 (BƯỚC 252). Hạt ngẫu nhiên đối chiếu với kỳ vọng GIẢI TÍCH: trung bình x gộp (không phí) của chuẩn (iv)
    bản dịch vòng, động cơ chạy KHÔNG khoá biên và KHÔNG trượt, phải nằm trong 2 sai số chuẩn của chính nó quanh
    `ky_vong_dich_giai_tich` (viết lại thẳng từ định nghĩa, độc lập với động cơ). Chỉ dùng độ dài các khoảng và mức đầu tư
    của Dow, KHÔNG dùng lợi nhuận của Dow. Bản có khoá biên + trượt, cùng lượt rút (có cặp), báo kèm. `dong_co` để gài lỗi."""
    r = ngau_nhien(M, s_dow, phi, "dich", so_luot, khoa=False, truot=False, dong_co=dong_co)
    x = r["x_tho"]
    tb, se = float(x.mean()), float(x.std(ddof=1) / np.sqrt(len(x)))
    e_gt = ky_vong_dich_giai_tich(M, s_dow)
    r2 = ngau_nhien(M, s_dow, phi, "dich", so_luot, khoa=True, truot=True, dong_co=dong_co)
    d = r2["x_tho"] - x
    return {"so_luot": so_luot, "trung_binh_x_tho": tb, "sai_so_chuan": se, "ky_vong_giai_tich": e_gt, "lech": tb - e_gt,
            "so_sigma": abs(tb - e_gt) / se if se > 0 else float("inf"), "ma_vung_ngan": r["ma_vung_ngan"],
            "dat": trong_khoang_se(tb - e_gt, se),
            "khoa_truot_chenh_cap": {"trung_binh": float(d.mean()), "sai_so_chuan": float(d.std(ddof=1) / np.sqrt(len(d)))}}


def ky_vong_dich_giai_tich(M: MaTran, s_dow: np.ndarray, *, dich_toi_thieu: int = DICH_TOI_THIEU,
                           nua_ngay: bool = True) -> float:
    """E_gt (SỬA S1): kỳ vọng của x̄ gộp (không phí, trượt, khoá) của chuẩn dịch vòng, tính BẰNG LIỆT KÊ mọi dịch chuyển k của
    từng mã (k nguyên trong [`dich_toi_thieu`, n_j − 1], hoặc [1, n_j − 1] nếu n_j ≤ `dich_toi_thieu`, đúng phân bố của
    `dich_vong`): w_sau(t) = trạng thái dịch ở t−1, w_trước(t) = ở t−2, lợi nhuận một phiên (1 + w_trước·qua đêm)(1 + w_sau·trong
    phiên) − 1, mức đầu tư (w_trước + w_sau)/2, trừ e × r_rổ, trọng số 1/71. Các mã độc lập nên kỳ vọng là tổng kỳ vọng từng mã.
    KHÔNG gọi `chay_dong_co`. `nua_ngay=False`: bỏ quy ước nửa ngày (cả ngày vào/ra ăn trọn lợi nhuận đóng/đóng−1, e = w_sau) —
    chỉ để phân rã khoảng cách (ứng viên đã bị bác ở STATE BƯỚC 252)."""
    T, N = s_dow.shape
    ro = ro_trung_binh(M)
    lai_ngay = lai_ro_theo_ma(M)
    tong = np.zeros(T)
    for j in range(N):
        v = np.flatnonzero(M.vung[:, j])
        a, b = v[0], v[-1] + 1
        n = b - a
        base = np.asarray(s_dow[a:b, j], dtype=float)
        ks = np.array([0]) if n < 2 else np.arange(dich_toi_thieu if n > dich_toi_thieu else 1, n)
        m = base[(np.arange(n)[None, :] - ks[:, None]) % n]            # (số dịch chuyển, n)
        w_sau, w_truoc, tich = np.zeros(n), np.zeros(n), np.zeros(n)
        if n > 1:
            w_sau[1:] = m[:, :-1].mean(axis=0)
        if n > 2:
            w_truoc[2:] = m[:, :-2].mean(axis=0)
            tich[2:] = (m[:, :-2] * m[:, 1:-1]).mean(axis=0)
        if nua_ngay:
            lai = w_truoc * M.qua_dem[a:b, j] + w_sau * M.trong_phien[a:b, j] + tich * M.qua_dem[a:b, j] * M.trong_phien[a:b, j]
            e = (w_sau + w_truoc) / 2.0
        else:
            lai, e = w_sau * lai_ngay[a:b, j], w_sau
        tong[a:b] += (lai - e * ro[a:b]) / SO_MA
    return float(tong.mean())


def ky_vong_xap_xi_cu(M: MaTran, s_dow: np.ndarray, *, trong_so_hien_dien: bool = False) -> float:
    """Công thức XẤP XỈ dùng ở BƯỚC 251 (đã bị `ky_vong_dich_giai_tich` thay; giữ để phân rã khoảng cách, STATE BƯỚC 252):
    Σ_j p_j m_j / 71 − (Σ_j p_j / 71) × trung bình(r_rổ) với p_j = tỷ lệ thời gian trong thị trường, m_j = trôi của mã.
    `trong_so_hien_dien=True` thêm hai yếu tố nó thiếu: trọng số số-ngày hiện diện n_j/T và r_rổ lấy trên cửa sổ của từng mã."""
    v = M.vung
    T = v.shape[0]
    nj = np.maximum(v.sum(axis=0), 1)
    p = (s_dow * v).sum(axis=0) / nj
    m = lai_ro_theo_ma(M).sum(axis=0) / nj
    ro = ro_trung_binh(M)
    if not trong_so_hien_dien:
        return float((p * m).sum() / SO_MA - p.sum() / SO_MA * ro.mean())
    ro_rieng = np.array([ro[v[:, j]].mean() for j in range(v.shape[1])])
    return float((p * (nj / T) * (m - ro_rieng)).sum() / SO_MA)


def phan_ra_khoang_cach_ii(M: MaTran, s_dow: np.ndarray) -> list[tuple[str, float]]:
    """Từng bước đi từ công thức xấp xỉ BƯỚC 251 tới E_gt (lệnh `khoang-cach-ii`)."""
    return [("xấp xỉ BƯỚC 251", ky_vong_xap_xi_cu(M, s_dow)),
            ("+ trọng số số-ngày hiện diện, r_rổ theo cửa sổ từng mã", ky_vong_xap_xi_cu(M, s_dow, trong_so_hien_dien=True)),
            ("liệt kê, dịch đều [0, n), bỏ quy ước nửa ngày", ky_vong_dich_giai_tich(M, s_dow, dich_toi_thieu=0, nua_ngay=False)),
            ("liệt kê, dịch ≥ 252, bỏ quy ước nửa ngày", ky_vong_dich_giai_tich(M, s_dow, nua_ngay=False)),
            ("liệt kê, dịch ≥ 252, nửa ngày (= E_gt)", ky_vong_dich_giai_tich(M, s_dow))]


def _cay_cong(delta: float):
    """Gài lỗi: cộng `delta` × mức đầu tư vào lợi nhuận gộp mỗi ngày (một độ lệch HỆ THỐNG theo ngày-mã giữ)."""
    def f(muc, M, phi, **kw):
        kq = chay_dong_co(muc, M, phi, **kw)
        return {**kq, "ret": kq["ret"] + delta * kq["phoi"]}
    return f


def _cay_nhan(he: float):
    """Gài lỗi: nhân lợi nhuận gộp với `he` (sai thước đo lợi nhuận)."""
    def f(muc, M, phi, **kw):
        kq = chay_dong_co(muc, M, phi, **kw)
        return {**kq, "ret": kq["ret"] * he}
    return f


#: Lỗi gài để chứng minh đối chứng (ii) CÓ THỂ trượt (BƯỚC 252). Tên → động cơ đã gài.
LOI_CAY = {"cong_0.15bp": _cay_cong(1.5e-5), "cong_0.5bp": _cay_cong(5e-5), "cong_1bp": _cay_cong(1e-4),
           "nhan_1.01": _cay_nhan(1.01), "nhan_1.05": _cay_nhan(1.05)}


NGUONG_IM_TIEM = 0.10    # ô "không tiêm gì" phải IM: tỷ lệ bắt ≤ 10% (lỗi 94; danh nghĩa một phía 2,5%)


def phan_quyet_tiem(ty_le_khong: float, ty_le_k0: float) -> bool:
    """Đạt khi CẢ HAI (SỬA S2): ô không tiêm IM (≤ `NGUONG_IM_TIEM`) VÀ ô `HE_SO_K0` × rào BẮT (≥ `NGUONG_BAT_TIEM`)."""
    return bool(ty_le_khong <= NGUONG_IM_TIEM and ty_le_k0 >= NGUONG_BAT_TIEM)


def khoang_wilson(bat: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Khoảng Wilson của một tỷ lệ bắt `bat`/`n` (đường cong lực phải kèm khoảng, không chỉ điểm)."""
    if n <= 0:
        return (0.0, 1.0)
    p = bat / n
    mau = 1.0 + z * z / n
    tam = (p + z * z / (2.0 * n)) / mau
    nua = z * np.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n)) / mau
    return (float(max(0.0, tam - nua)), float(min(1.0, tam + nua)))


def mde_80(o: dict) -> float | None:
    """MDE₈₀ (SỬA S2): hệ số h NHỎ NHẤT của lưới có tỷ lệ bắt ≥ `NGUONG_BAT_TIEM`; None nếu không ô nào. Cận TRÊN của MDE thật
    (lưới thô), nên không khoe phép đo mạnh hơn nó."""
    ok = sorted(v["he_so_rao"] for v in o.values() if v["ty_le"] >= NGUONG_BAT_TIEM)
    return ok[0] if ok else None


def doi_chung_iii(M: MaTran, s_dow: np.ndarray, phi: float, *, so_lap: int = SO_LAP_TIEM, so_ngan_hang: int = 200,
                  he_so: tuple = HE_SO_LUOI_TIEM, hat: int = HAT) -> dict:
    """(iii) Tiêm lợi thế giả — công suất (khuôn BƯỚC 113, lỗi 99; SỬA S2, BƯỚC 252). Nền = lợi nhuận THẬT với trạng thái Dow
    DỊCH VÒNG ≥ 252 phiên (rời nhãn, giữ tự tương quan — lỗi 94); tiêm `a` = hệ số × rào hoà vốn vào mỗi đơn-vị-đầu-tư-ngày
    (x += a × e); "bắt" = cận dưới KTC có cặp (hàm sân đấu) của mean(x_tiêm) − mean(x_nền) > 0 với x_nền = trung bình mỗi ngày
    của một ngân hàng `so_ngan_hang` lượt dịch vòng độc lập. K0 chỉ khi ô 0 KÊU (> 10%) hoặc ô `HE_SO_K0` × rào KHÔNG bắt
    được ≥ 80%, trên `so_lap` lượt (không phải một lượt). Báo đủ đường cong lực kèm khoảng Wilson và MDE₈₀ (cận trên, lưới
    thô) đổi sang điểm phần trăm mỗi năm. Dịch vòng ≥ 252 nên không lượt nào là trạng thái Dow thật (không đọc Δ của Dow)."""
    if 0.0 not in he_so or HE_SO_K0 not in he_so:
        raise ValueError(f"luoi he so phai co 0 va {HE_SO_K0}: {he_so}")
    rh = rao_hoa_von(M, s_dow, phi)
    rao = rh["rao"]
    ro = ro_trung_binh(M)
    nen = ngau_nhien(M, s_dow, phi, "dich", so_ngan_hang, hat=hat + 1, giu_x=True)["x_t"]
    bang = doc_bang_do_phu()
    rng = np.random.default_rng(hat + 2)
    T, N = s_dow.shape
    vi_tri = [np.flatnonzero(M.vung[:, j]) for j in range(N)]
    muc = np.zeros((so_lap, T, N), dtype=np.float32)
    for k in range(so_lap):
        for j in range(N):
            a, b = vi_tri[j][0], vi_tri[j][-1] + 1
            muc[k, a:b, j] = dich_vong(s_dow[a:b, j], rng)
    kq = chay_dong_co(muc.astype(float), M, phi)
    x0 = x_tu_dong_co(kq, ro)
    ket = {}
    for h in he_so:
        a_tiem = h * rao
        bat, lech = 0, []
        for k in range(so_lap):
            x = x0[k] + a_tiem * kq["phoi"][k]
            t = tom_tat_x(x, nen, bang)
            lech += khop_cau_hinh(t["ktc"]) if k == 0 else []
            bat += int(t["ktc"] is not None and t["ktc"]["can_duoi"] > 0)
        w_lo, w_hi = khoang_wilson(bat, so_lap)
        ket[str(h)] = {"he_so_rao": h, "tiem_moi_don_vi_ngay": a_tiem, "bat": bat, "so_lap": so_lap, "ty_le": bat / so_lap,
                       "wilson": [w_lo, w_hi]}
    dat = phan_quyet_tiem(ket["0.0"]["ty_le"], ket[str(HE_SO_K0)]["ty_le"])
    e = rh["phoi_trung_binh"]
    h80 = mde_80(ket)
    mde = None if h80 is None else {
        "he_so_rao": h80, "tiem_moi_don_vi_ngay": h80 * rao,
        "diem_pt_von_moi_nam": h80 * rao * e * NGAY_NAM * 100.0,
        "diem_pt_dang_dau_tu_moi_nam": h80 * rao * NGAY_NAM * 100.0}
    return {"rao_hoa_von": rao, "phoi_trung_binh": e, "o": ket, "dat": dat, "mde_80": mde,
            "ghi_chu": f"dat = ty le bat o he so 0 <= 10% (phai im) VA o {HE_SO_K0}x rao >= 80%; mde_80 = he so nho nhat >= 80%"}


def dung_lai_thu_cong(df: pd.DataFrame, he: float, san: str, tham_so: tuple = C.MAC_DINH[1], so_pivot: int = 3) -> dict:
    """(iv) Ca thật đã biết, phần TÁI DỰNG ĐỘC LẬP: máy trạng thái ATR viết lại thẳng từ luật trong đặc tả 5.3 trên
    bảng giá thô (không gọi `cau_truc_gia`), cho cấp swing; so TỪNG DÒNG `so_pivot` pivot đầu với nhật ký của mô-đun
    (ngày xảy ra, ngày biết, giá). Trả cả dòng thô của các nến quanh pivot để người đọc đối chiếu bằng mắt."""
    k = tham_so[1]
    c = pd.to_numeric(df["close"]).to_numpy(float)
    h = pd.to_numeric(df["high"]).to_numpy(float)
    lo = pd.to_numeric(df["low"]).to_numpy(float)
    ngay = [str(t)[:10] for t in df["time"]]
    n = len(c)
    ref = np.concatenate([[np.nan], c[:-1]])
    tr = np.maximum.reduce([h - lo, np.abs(h - ref), np.abs(lo - ref)])
    tr[0] = h[0] - lo[0]
    atr = np.full(n, np.nan)
    for t in range(13, n):
        atr[t] = tr[t - 13:t + 1].mean()
    atr[:13] = np.nan
    # nến đầu (chỉ số 0) không bao giờ là pivot; theo dõi cực trị chờ cả hai phía
    pivots, huong = [], None
    cd, ct = 0, 0             # chỉ số đỉnh chờ, đáy chờ
    for t in range(1, n):
        if c[t] > c[cd] + 1e-12:
            cd = t
        if c[t] < c[ct] - 1e-12:
            ct = t
        if np.isnan(atr[t]) or atr[t] <= 0:
            continue
        if huong in (None, "len") and c[t] <= c[cd] - k * atr[t] and cd > 0:
            pivots.append(("dinh", cd, t))
            huong, ct = "xuong", t
            for u in range(cd + 1, t + 1):
                if c[u] < c[ct]:
                    ct = u
            cd = t
        elif huong in (None, "xuong") and c[t] >= c[ct] + k * atr[t] and ct > 0:
            pivots.append(("day", ct, t))
            huong, cd = "len", t
            for u in range(ct + 1, t + 1):
                if c[u] > c[cd]:
                    cd = u
            ct = t
        if len(pivots) >= so_pivot + 6:
            break
    r = C.doc_cau_truc(df, he_so_gia=he, san=san, ho="atr", tham_so=tham_so)
    mo_dun = [p for p in r.nhat_ky if p.cap == C.CAP_SWING and p.su_kien == C.XAC_NHAN][:so_pivot]
    tay = pivots[:so_pivot]
    dong_so = []
    khop = len(tay) == len(mo_dun) == so_pivot
    for a, b in zip(tay, mo_dun):
        ok = (a[0] == b.loai and ngay[a[1]] == b.ngay_xay_ra and ngay[a[2]] == b.ngay_biet and abs(c[a[1]] - b.gia) < 1e-9)
        khop = khop and ok
        dong_so.append({"tay": [a[0], ngay[a[1]], ngay[a[2]], float(c[a[1]])],
                        "mo_dun": [b.loai, b.ngay_xay_ra, b.ngay_biet, b.gia], "khop": bool(ok)})
    return {"khop": bool(khop), "so_pivot_tay": len(tay), "so_pivot_mo_dun": len(mo_dun), "dong": dong_so}


# ── H2 (sự kiện CHoCH), H3 (VN-INDEX), mô tả lật lại ────────────────────────────────────
def loi_nhuan_cua_so(mo: np.ndarray, dong: np.ndarray, t: int, do_dai: int = CUA_SO_SU_KIEN) -> float | None:
    """Lợi nhuận từ MỞ CỬA phiên t+1 tới ĐÓNG CỬA phiên t+do_dai (do_dai phiên). None khi thiếu nến."""
    if t + do_dai >= len(dong):
        return None
    return float(dong[t + do_dai] / mo[t + 1] - 1.0)


def su_kien_h2(df: pd.DataFrame, he: float, san: str, thang: np.ndarray, rng, so_luot: int = SO_LUOT_NGAU_NHIEN,
               tham_so: tuple | None = None) -> list[dict]:
    """H2 cho MỘT mã: mỗi CHoCH cấp swing tại nến t cho lợi nhuận cửa sổ 21 phiên (từ mở cửa t+1), trừ lợi nhuận rổ
    (`thang` = lợi nhuận cửa sổ của rổ tại từng t, tính ở người gọi) và trừ trung bình `so_luot` ngày ngẫu nhiên
    CÙNG MÃ, CÙNG THÁNG LỊCH (kiểm soát chế độ thị trường). Trả danh sách sự kiện kèm hiệu."""
    ts = C.MAC_DINH[1] if tham_so is None else tham_so
    r = C.doc_cau_truc(df, he_so_gia=he, san=san, ho="atr", tham_so=ts)
    mo = pd.to_numeric(df["open"]).to_numpy(float)
    dong = pd.to_numeric(df["close"]).to_numpy(float)
    thang_lich = pd.to_datetime(df["time"]).dt.to_period("M").to_numpy()
    kq = []
    for e in r.su_kien:
        if e.cap != C.CAP_SWING or e.loai != C.CHOCH:
            continue
        t = e.chi_so_xay_ra
        lai = loi_nhuan_cua_so(mo, dong, t)
        if lai is None or np.isnan(thang[t]):
            continue
        cung = [u for u in range(len(dong)) if thang_lich[u] == thang_lich[t] and u != t
                and loi_nhuan_cua_so(mo, dong, u) is not None and not np.isnan(thang[u])]
        if not cung:
            continue
        pick = rng.choice(cung, size=so_luot, replace=True)
        nen = np.array([loi_nhuan_cua_so(mo, dong, int(u)) - thang[int(u)] for u in set(pick.tolist())])
        dem = np.bincount(pick, minlength=len(dong))[sorted(set(pick.tolist()))]
        chuan = float((nen * dem).sum() / dem.sum())
        kq.append({"ngay": e.ngay_xay_ra, "chieu": e.chieu, "khoa_bien": e.khoa_bien,
                   "du": float(lai - thang[t] - chuan)})
    return kq


def h3_chi_so(df: pd.DataFrame, he: float, san: str) -> dict:
    """H3 (mô tả, KHÔNG suy diễn): đếm sự kiện cấp swing của MỘT chuỗi và độ trễ biết của pivot swing."""
    r = C.doc_cau_truc(df, he_so_gia=he, san=san)
    sk = [e for e in r.su_kien if e.cap == C.CAP_SWING]
    tre = [p.chi_so_biet - p.chi_so_xay_ra for p in r.nhat_ky if p.cap == C.CAP_SWING and p.su_kien == C.XAC_NHAN]
    return {"so_phien": r.so_nen, "su_kien": {k: sum(1 for e in sk if e.loai == k) for k in (C.BOS, C.CHOCH, C.KHOI_DAU)},
            "tre_trung_vi": float(np.median(tre)) if tre else None,
            "tre_p90": float(np.percentile(tre, 90)) if tre else None}


def lat_lai_hai_dinh_nghia(df: pd.DataFrame, r) -> dict:
    """"Lật lại trong 3 phiên", ĐẶT TÊN RÕ HAI ĐỊNH NGHĨA (người dùng 02/11: *"Báo cả hai, đặt tên rõ"*):
    `lat_lai_sau_su_kien_nguoc` = sự kiện kế tiếp CÙNG cấp ngược chiều, cách ≤ 3 phiên;
    `lat_lai_dong_cua_qua_moc` = trong 3 phiên sau nến sự kiện có một nến đóng cửa ở phía bên kia mốc bị phá."""
    import mo_ta_cau_truc_gia as MT
    kq = {}
    for k, v in MT.lat_lai(df, r).items():
        n = v.get("n", 0)
        kq[k] = {"n": n, "lat_lai_sau_su_kien_nguoc": v.get("su_kien_nguoc", 0),
                 "lat_lai_dong_cua_qua_moc": v.get("dong_cua_quay_lai", 0)}
    return kq


# ── lượt chạy dữ liệu THẬT: khoá ───────────────────────────────────────────────────────────
def nap_cache(cache: Path, ma_ds=None, moc: dict | None = None, vung: str = "sach"):
    """(chuoi, vung_ma, s_dow) cho các mã của rổ: bảng, hệ số giá, sàn, mặt nạ vùng đọc và trạng thái Dow mặc định."""
    ma_ds = list(CUSTOM_WATCHLIST_SYMBOLS) if ma_ds is None else ma_ds
    if moc is None:
        moc = json.loads(DUONG_MOC_SACH.read_text(encoding="utf-8"))["moc_theo_ma"]
    chuoi, vung_ma, s = {}, {}, {}
    for m in ma_ds:
        df = pd.read_csv(Path(cache) / f"{m}.csv").sort_values("time").reset_index(drop=True)
        he, san = float(price_multiplier(df)), san_cua(m)
        chuoi[m] = (df, he, san)
        ngay = np.array([str(t)[:10] for t in df["time"]])
        vung_ma[m] = chon_vung(ngay, moc.get(m), vung)
        s[m] = trang_thai_dow(df, he, san)
    return chuoi, vung_ma, s


def s_matran(M: MaTran, chuoi: dict, s: dict) -> np.ndarray:
    """Trạng thái Dow theo (ngày toàn cục × mã): hàng của từng mã đặt đúng ngày của nó; ngày vắng hàng giữ giá trị trước."""
    chi_so = {d: i for i, d in enumerate(M.ngay)}
    out = np.zeros((len(M.ngay), len(M.ma)))
    for j, m in enumerate(M.ma):
        df = chuoi[m][0]
        co_hang = np.zeros(len(M.ngay), dtype=bool)
        for i, t in enumerate(df["time"]):
            d = str(t)[:10]
            if d in chi_so:
                out[chi_so[d], j] = float(s[m][i])
                co_hang[chi_so[d]] = True
        v = np.flatnonzero(M.vung[:, j])
        for t in range(v[0] + 1, v[-1] + 1):
            if not co_hang[t]:                      # ngày vắng hàng của mã giữa vùng: giữ trạng thái ngày trước
                out[t, j] = out[t - 1, j]
    return out


def chuan_i(M: MaTran, phi: float, ro: np.ndarray) -> np.ndarray:
    """Chuẩn (i): rổ đều trọng số, không phí ngoài một vòng mua đầu và bán cuối (không trượt, không khoá biên). Phần
    gộp của rổ trừ chính nó là 0 theo ĐỊNH NGHĨA (x của rổ so với rổ), nên x_(i) chỉ còn là −chi phí của đúng hai chuyến;
    tính qua động cơ để chi phí và ngày vào/ra là của động cơ, không gõ tay. `ro` giữ trong chữ ký cho khớp các chuẩn khác."""
    del ro
    return -chay_dong_co(np.ones((1,) + M.vung.shape), M, phi, khoa=False, truot=False)["chi_phi"][0]


def thang_tong_hop(iv: dict) -> float:
    """Tỷ lệ Dow thắng ở chuẩn (iv) dùng cho A⁺: giá trị NHỎ HƠN trong hai bản (đặt ngẫu nhiên, đồng bộ thời gian)."""
    return min(iv["dat"]["thang"], iv["dich"]["thang"])


def chay_ket_qua(M: MaTran, s_dow: np.ndarray, s_sma: np.ndarray, w_tsmom: np.ndarray, phi: float, *,
                 doi_chung_dat: bool, so_luot: int = SO_LUOT_NGAU_NHIEN, bang: dict | None = None,
                 hat: int = HAT) -> dict:
    """ĐƯỜNG RA KẾT CỤC (H1). Chỉ test (dữ liệu TỔNG HỢP) và `lenh_ket_qua` (khoá) gọi nó: nó là chỗ DUY NHẤT tính Δ của
    danh mục Dow so với chuẩn (i)–(iv). Trả mọi thống kê của "Thống kê chính" kèm KTC, nhãn độ phủ, đối chiếu cấu hình
    KTC khoá, cột thô, và kết cục."""
    bang = doc_bang_do_phu() if bang is None else bang
    ro = ro_trung_binh(M)
    x_dow = x_tu_dong_co(chay_dong_co(s_dow[None].astype(float), M, phi), ro)[0]
    kq_dow = chay_dong_co(s_dow[None].astype(float), M, phi)
    x_i = chuan_i(M, phi, ro)
    x_ii = x_tu_dong_co(chay_dong_co(s_sma[None].astype(float), M, phi), ro)[0]
    x_iii = x_tu_dong_co(chay_dong_co(w_tsmom[None], M, phi), ro)[0]
    th = {"i": tom_tat_x(x_dow, x_i, bang), "ii": tom_tat_x(x_dow, x_ii, bang), "iii": tom_tat_x(x_dow, x_iii, bang)}
    lech = [m for t in th.values() for m in khop_cau_hinh(t["ktc"])]
    rd = {k: ngau_nhien(M, s_dow, phi, k, so_luot, hat=hat, giu_x=True) for k in ("dat", "dich")}
    iv = {k: {"thang": float((v["x_phi"] < x_dow.mean()).mean()), "tb_ngau_nhien": float(v["x_phi"].mean()),
              "delta": float(x_dow.mean() - v["x_phi"].mean())} for k, v in rd.items()}
    thang_iv = thang_tong_hop(iv)
    ok = doi_chung_dat and not lech and all(t["ktc"] is not None for t in th.values())
    kc = ket_cuc(delta_i=th["i"]["delta"], ktc_i=(th["i"]["ktc"]["can_duoi"], th["i"]["ktc"]["can_tren"]),
                 ktc_ii=(th["ii"]["ktc"]["can_duoi"], th["ii"]["ktc"]["can_tren"]),
                 ktc_iii=(th["iii"]["ktc"]["can_duoi"], th["iii"]["ktc"]["can_tren"]), thang_iv=thang_iv,
                 doi_chung_dat=bool(ok)) if all(t["ktc"] is not None for t in th.values()) else \
        {"ket_cuc": KET_CUC_K0, "khop": [KET_CUC_K0], "nguong_nho": None, "nguong_lon": None}
    nua_h = th["i"]["nua_be_rong"]
    e_dow = float(kq_dow["phoi"].mean())
    nam = {"nua_be_rong_ktc_i": nua_h, "phoi_trung_binh": e_dow,
           "diem_pt_von_moi_nam": None if nua_h is None else nua_h * NGAY_NAM * 100.0,
           "diem_pt_dang_dau_tu_moi_nam": None if nua_h is None or e_dow <= 0 else nua_h / e_dow * NGAY_NAM * 100.0}
    return {"so_ngay": len(M.ngay), "so_ma": len(M.ma), "x_trung_binh_moi_ngay": float(x_dow.mean()), "nua_h_quy_nam": nam,
            "x_cong_don_diem_phan_tram": float(x_dow.sum() * 100.0), "cot_tho_cong_don_diem_phan_tram":
            float(cot_tho(kq_dow, ro, M)[0].sum() * 100.0), "delta": th, "ngau_nhien": iv, "thang_iv": thang_iv,
            "lech_cau_hinh_ktc": lech, "ket_cuc": kc,
            "so_khoang_giu": int(sum(len(doan_giu(s_dow[np.flatnonzero(M.vung[:, j])[0]:np.flatnonzero(M.vung[:, j])[-1] + 1, j]))
                                     for j in range(len(M.ma))))}


# ── Lát 4b (BƯỚC 253): lượt chạy DUY NHẤT dưới văn bản ĐO 34 đã sửa ──────────────────────────
def chuan_ii_iii(M: MaTran, chuoi: dict) -> tuple[np.ndarray, np.ndarray]:
    """Trạng thái SMA200 (chuẩn (ii)) và trọng số TSMOM (chuẩn (iii)) theo (ngày toàn cục × mã), xếp hàng cùng cách với
    `s_matran` (ngày vắng hàng giữa vùng giữ giá trị trước). Chưa đủ lịch sử: SMA → không giữ; cửa sổ TSMOM → đóng góp 0 (S7)."""
    dong = {m: pd.to_numeric(chuoi[m][0]["close"]).to_numpy(float) for m in M.ma}
    return (s_matran(M, chuoi, {m: trang_thai_sma200(dong[m]) for m in M.ma}).astype(float),
            s_matran(M, chuoi, {m: trong_so_tsmom(dong[m]) for m in M.ma}))


def _json_mac_dinh(o):
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, np.generic):
        return o.item()
    return str(o)


def _an_toan(ten: str, ra, f):
    """Một mục BÁO KÈM hỏng không được làm mất kết cục đã in (lượt chạy là DUY NHẤT): ghi lỗi to ra và vào JSON."""
    try:
        return f()
    except Exception as e:  # noqa: BLE001
        import traceback
        ra(f"[BÁO KÈM LỖI] {ten}: {e!r}")
        return {"loi": repr(e), "vet": traceback.format_exc()}


def thang_cua_so_ro(M: MaTran, do_dai: int = CUA_SO_SU_KIEN) -> np.ndarray:
    """Lợi nhuận của rổ trong cửa sổ `do_dai` phiên (từ MỞ CỬA t+1 tới ĐÓNG CỬA t+do_dai) tại mỗi ngày toàn cục t: trung bình
    các mã đang trong vùng ở CẢ HAI đầu cửa sổ. NaN khi không mã nào đủ. (H2: chuẩn trừ là rổ cùng cửa sổ.)"""
    T = M.vung.shape[0]
    mo = np.where(M.vung, M.dong / (1.0 + M.trong_phien), np.nan)
    out = np.full(T, np.nan)
    for t in range(T - do_dai):
        ok = M.vung[t + 1] & M.vung[t + do_dai]
        if ok.any():
            out[t] = float(np.mean(M.dong[t + do_dai][ok] / mo[t + 1][ok] - 1.0))
    return out


def cat_vung_sach(df: pd.DataFrame, vung: np.ndarray) -> pd.DataFrame:
    """Bảng của một mã cắt tới nến cuối của vùng đọc (nhân quả: nhật ký đến đó giống hệt bản đầy đủ — bất biến khi cắt)."""
    return df.iloc[:int(np.flatnonzero(vung)[-1]) + 1].reset_index(drop=True)


def luoi_h1(M: MaTran, chuoi: dict, phi: float, ro: np.ndarray, x_i: np.ndarray, bang: dict) -> list[dict]:
    """Toàn lưới 10 ô × H1 (S5): CHỈ Δ_(i) kèm KTC và nhãn độ phủ, KHÔNG nhãn kết cục. Ô tốt nhất không phải một kết quả."""
    kq = []
    for ho in sorted(C.LUOI):
        for ts in C.LUOI[ho]:
            s = {m: trang_thai_dow(chuoi[m][0], chuoi[m][1], chuoi[m][2], ho, ts) for m in M.ma}
            x = x_tu_dong_co(chay_dong_co(s_matran(M, chuoi, s)[None].astype(float), M, phi), ro)[0]
            t = tom_tat_x(x, x_i, bang)
            kq.append({"ho": ho, "tham_so": list(ts), "mac_dinh": (ho, ts) == C.MAC_DINH, "delta": t["delta"],
                       "ktc": t["ktc"], "dong": t["dong"], "chua_0": t["chua_0"]})
    return kq


def mo_ta_bao_kem(chuoi: dict, vung_ma: dict) -> dict:
    """Số MÔ TẢ ở ô mặc định, vùng sạch (S5): số sự kiện mỗi mã mỗi năm, độ trễ `chi_so_biet − chi_so_xay_ra` (trung vị, p90) mỗi cấp,
    HAI định nghĩa "lật lại trong 3 phiên". Không đọc lợi nhuận."""
    dem = {c: {} for c in C.CAPS}
    tre = {c: [] for c in C.CAPS}
    lat: dict = {}
    so_nam = 0.0
    for m in chuoi:
        if not vung_ma[m].any():
            continue
        df = cat_vung_sach(chuoi[m][0], vung_ma[m])
        r = C.doc_cau_truc(df, he_so_gia=chuoi[m][1], san=chuoi[m][2])
        so_nam += int(vung_ma[m].sum()) / 252.0
        for e in r.su_kien:
            for k in (e.loai, f"{e.loai}/{e.chieu}"):
                dem[e.cap][k] = dem[e.cap].get(k, 0) + 1
        for p in r.nhat_ky:
            tre[p.cap].append(p.chi_so_biet - p.chi_so_xay_ra)
        for k, v in lat_lai_hai_dinh_nghia(df, r).items():
            o = lat.setdefault(k, {"n": 0, "lat_lai_sau_su_kien_nguoc": 0, "lat_lai_dong_cua_qua_moc": 0})
            for kk in o:
                o[kk] += v[kk]
    return {"so_nam_ma": so_nam,
            "su_kien_moi_ma_moi_nam": {c: {k: v / so_nam for k, v in sorted(dem[c].items())} for c in C.CAPS},
            "su_kien_dem": dem,
            "do_tre_trung_vi": {c: float(np.median(tre[c])) if tre[c] else None for c in C.CAPS},
            "do_tre_p90": {c: float(np.percentile(tre[c], 90)) if tre[c] else None for c in C.CAPS},
            "lat_lai_3_phien": {k: {**v, "ty_le_su_kien_nguoc": v["lat_lai_sau_su_kien_nguoc"] / v["n"] if v["n"] else None,
                                    "ty_le_dong_cua_qua_moc": v["lat_lai_dong_cua_qua_moc"] / v["n"] if v["n"] else None}
                                for k, v in sorted(lat.items())}}


def h2_mo_ta(M: MaTran, chuoi: dict, vung_ma: dict, hat: int = HAT) -> dict:
    """H2 ở dạng MÔ TẢ (S5): số sự kiện CHoCH cấp swing và trung bình / trung vị của (lợi nhuận 21 phiên trừ rổ trừ ngày ngẫu
    nhiên cùng mã cùng tháng) theo hướng. KHÔNG KTC, KHÔNG vào kết cục. Chuẩn trừ của rổ: `thang_cua_so_ro`."""
    thang = thang_cua_so_ro(M)
    chi_so = {d: i for i, d in enumerate(M.ngay)}
    rng = np.random.default_rng(hat + 3)
    ds = []
    for m in M.ma:
        df = cat_vung_sach(chuoi[m][0], vung_ma[m])
        thang_ma = np.full(len(df), np.nan)
        for i, t in enumerate(df["time"]):
            if vung_ma[m][i]:
                thang_ma[i] = thang[chi_so[str(t)[:10]]]
        ds += su_kien_h2(df, chuoi[m][1], chuoi[m][2], thang_ma, rng)
    kq = {"so_su_kien": len(ds)}
    for chieu in (C.TANG, C.GIAM):
        du = np.array([e["du"] for e in ds if e["chieu"] == chieu], float)
        kq[chieu] = {"n": int(len(du)), "trung_binh": float(du.mean()) if len(du) else None,
                     "trung_vi": float(np.median(du)) if len(du) else None,
                     "n_khoa_bien": int(sum(1 for e in ds if e["chieu"] == chieu and e["khoa_bien"]))}
    return kq


def h3_vnindex(cache: Path) -> dict:
    """H3 (mô tả, KHÔNG suy diễn): VN-INDEX như MỘT chuỗi, toàn bảng của cache."""
    import mo_ta_cau_truc_gia as MT
    df, he, san = MT.cau_hinh(Path(cache), "VNINDEX")
    return h3_chi_so(df, he, san)


def _dong_delta(t: dict) -> str:
    ktc = t["ktc"]
    if ktc is None:
        return f"Δ {t['delta']:+.4e}, KTC không tính được"
    return (f"Δ {t['delta']:+.4e} mỗi ngày, KTC [{ktc['can_duoi']:+.4e} ; {ktc['can_tren']:+.4e}] "
            f"({'chứa 0' if t['chua_0'] else 'LOẠI 0'}); {t['dong']}")


def in_ket_qua(kq: dict, ra=print) -> None:
    """In kết cục và các số của `chay_ket_qua` (mọi con số ở đây được tính trong lượt chạy này)."""
    kc = kq["ket_cuc"]
    nam = kq["nua_h_quy_nam"]
    ra(f"quần thể: {kq['so_ma']} mã, {kq['so_ngay']} ngày toàn cục, {kq['so_khoang_giu']} khoảng nắm giữ của Dow")
    ra(f"x trung bình mỗi ngày của Dow (sau phí, trừ rổ): {kq['x_trung_binh_moi_ngay']:+.4e}; cộng dồn {kq['x_cong_don_diem_phan_tram']:+.2f} điểm %; "
       f"cột thô cộng dồn {kq['cot_tho_cong_don_diem_phan_tram']:+.2f} điểm %")
    for k, ten in (("i", "(i) rổ"), ("ii", "(ii) SMA200"), ("iii", "(iii) TSMOM")):
        ra(f"Δ_{ten}: {_dong_delta(kq['delta'][k])}")
    for k, ten in (("dat", "đặt ngẫu nhiên"), ("dich", "đồng bộ thời gian (dịch vòng ≥ 252)")):
        v = kq["ngau_nhien"][k]
        ra(f"(iv) {ten}: Dow thắng {100 * v['thang']:.1f}% lượt rút, x̄ ngẫu nhiên {v['tb_ngau_nhien']:+.4e}, Δ {v['delta']:+.4e}")
    ra(f"(iv) tỷ lệ dùng cho A⁺ (số nhỏ hơn trong hai bản): {100 * kq['thang_iv']:.1f}%")
    if nam["nua_be_rong_ktc_i"] is not None:
        ra(f"H = nửa bề rộng KTC của Δ_(i) = {nam['nua_be_rong_ktc_i']:.4e} mỗi ngày = {nam['diem_pt_von_moi_nam']:.2f} điểm % vốn (71 ô) mỗi năm = "
           f"{nam['diem_pt_dang_dau_tu_moi_nam']:.1f} điểm % trên vốn đang đầu tư mỗi năm (mức đầu tư trung bình {nam['phoi_trung_binh']:.4f})")
    if kc["nguong_nho"] is not None:
        ra(f"ngưỡng nhỏ = H/2 = {kc['nguong_nho']:.4e}; ngưỡng lớn = 2H = {kc['nguong_lon']:.4e}")
    ra("cấu hình KTC đã dùng ở Δ_(i): " + ("; ".join(kq["lech_cau_hinh_ktc"]) if kq["lech_cau_hinh_ktc"] else "KHỚP bản đã khoá (BƯỚC 248)"))
    ra(f"KẾT CỤC: {kc['ket_cuc']}" + (f"  (dạng A — {kc['ly_do_A']})" if kc.get("ly_do_A") else ""))


def chay_lat_4b(cache: Path, ra=print, *, so_luot: int = SO_LUOT_NGAU_NHIEN, ma_ds=None, moc: dict | None = None,
                bam_ky: str = BAM_CACHE_KY, ghi: str | Path | None = None, bang: dict | None = None) -> dict:
    """LƯỢT CHẠY DUY NHẤT của ĐO 34 (Lát 4b, BƯỚC 253) dưới văn bản đã sửa: băm cache → đối chứng (i)–(vi) → kết cục (H1) trên vùng
    sạch (in ngay) → báo kèm (lưới 10 ô, bản không khoá biên, độ nhạy phí 0,76%, mô tả, H2 mô tả, H3, vùng sau mốc, KHÔNG vào kết
    cục) → băm cache sau. Chỉ `lenh_ket_qua` (sau hai khoá) gọi hàm này. Băm trước lệch băm đã ký, hoặc băm sau lệch băm trước,
    thì kết cục cuối là K0. `ma_ds`/`moc`/`bam_ky` chỉ để test trên cache tổng hợp."""
    import mo_ta_cau_truc_gia as MT
    bang = doc_bang_do_phu() if bang is None else bang
    out: dict = {"hat": HAT, "so_luot": so_luot, "bam_ky": bam_ky}

    def luu():
        if ghi:
            Path(ghi).write_text(json.dumps(out, ensure_ascii=False, indent=1, default=_json_mac_dinh), encoding="utf-8")

    truoc = MT.bam_cache(cache)
    out["bam_truoc_chay"] = truoc
    khop_ky = truoc["sha256"] == bam_ky
    ra(f"băm cache TRƯỚC lượt chạy: {truoc['sha256']} ({truoc['so_file']} file) — băm đã ký {'KHỚP' if khop_ky else 'LỆCH → K0'}")
    ra("== ĐỐI CHỨNG (i)–(vi), cùng lượt chạy ==")
    dc = doi_chung_tat_ca(cache, ra=ra, so_luot=so_luot)
    out["doi_chung"] = dc
    dat_dc = bool(dc["tat_ca_dat"]) and khop_ky
    ra("== H1: KẾT CỤC trên vùng sạch ==")
    chuoi, vung_ma, s = nap_cache(cache, ma_ds, moc, vung="sach")
    M = dung_ma_tran(chuoi, vung_ma)
    s_dow = s_matran(M, chuoi, s)
    s_sma, w_ts = chuan_ii_iii(M, chuoi)
    phi = phi_nua()
    ra(f"vùng sạch: {len(M.ma)} mã, {len(M.ngay)} ngày toàn cục ({M.ngay[0]} → {M.ngay[-1]}), {int(M.vung.sum())} ngày-mã")
    kq = chay_ket_qua(M, s_dow, s_sma, w_ts, phi, doi_chung_dat=dat_dc, so_luot=so_luot, bang=bang, hat=HAT)
    out["ket_qua"] = kq
    in_ket_qua(kq, ra)
    k_ban_dau = kq["ket_cuc"]["ket_cuc"]
    out["ket_cuc_truoc_bam_sau"] = k_ban_dau
    luu()

    ro = ro_trung_binh(M)
    x_i = chuan_i(M, phi, ro)
    ra("== BÁO KÈM (không quyết định kết cục) ==")
    out["bao_kem"] = bk = {}
    bk["luoi_10_o"] = _an_toan("lưới 10 ô", ra, lambda: luoi_h1(M, chuoi, phi, ro, x_i, bang))
    if isinstance(bk["luoi_10_o"], list):
        ra("lưới 10 ô × H1 (CHỈ Δ_(i); ô tốt nhất không phải một kết quả):")
        for o in bk["luoi_10_o"]:
            ra(f"  {o['ho']:8s} {str(o['tham_so']):12s}{' [mặc định]' if o['mac_dinh'] else '            '} Δ {o['delta']:+.4e}  "
               f"KTC {'không tính được' if o['ktc'] is None else '[%+.4e ; %+.4e]' % (o['ktc']['can_duoi'], o['ktc']['can_tren'])}")

    def khong_khoa():
        x = x_tu_dong_co(chay_dong_co(s_dow[None].astype(float), M, phi, khoa=False), ro)[0]
        return tom_tat_x(x, x_i, bang)
    bk["khong_khoa_bien"] = _an_toan("bản không khoá biên", ra, khong_khoa)
    if "delta" in bk["khong_khoa_bien"]:
        ra("bản không có sự kiện nến khoá biên (động cơ khoa=False: lệnh không bị huỷ / chặn ở nến kịch trần / sàn): "
           + _dong_delta(bk["khong_khoa_bien"]))

    def nhay_phi():
        k = chay_ket_qua(M, s_dow, s_sma, w_ts, phi_nua(PHI_NHAY_PCT), doi_chung_dat=dat_dc, so_luot=so_luot, bang=bang, hat=HAT)
        return {"phi_pct": PHI_NHAY_PCT, "delta_i": k["delta"]["i"], "ket_cuc": k["ket_cuc"], "thang_iv": k["thang_iv"]}
    bk["nhay_phi_0_76"] = _an_toan("độ nhạy phí 0,76%", ra, nhay_phi)
    if "delta_i" in bk["nhay_phi_0_76"]:
        v = bk["nhay_phi_0_76"]
        ra(f"độ nhạy phí {PHI_NHAY_PCT}% một vòng: {_dong_delta(v['delta_i'])}; nhãn tính được {v['ket_cuc']['ket_cuc']} (KHÔNG đổi nhãn chính)")
    bk["mo_ta"] = _an_toan("mô tả sự kiện", ra, lambda: mo_ta_bao_kem(chuoi, vung_ma))
    if "su_kien_dem" in bk["mo_ta"]:
        ra("sự kiện mỗi mã mỗi năm (loại, ô mặc định, vùng sạch): " + json.dumps(bk["mo_ta"]["su_kien_moi_ma_moi_nam"], ensure_ascii=False))
        ra(f"độ trễ chi_so_biet − chi_so_xay_ra: trung vị {bk['mo_ta']['do_tre_trung_vi']}, p90 {bk['mo_ta']['do_tre_p90']}")
        ra("lật lại trong 3 phiên (HAI định nghĩa): " + json.dumps(bk["mo_ta"]["lat_lai_3_phien"], ensure_ascii=False))
    bk["h2_mo_ta"] = _an_toan("H2 mô tả", ra, lambda: h2_mo_ta(M, chuoi, vung_ma))
    ra("H2 (MÔ TẢ, không KTC, không vào kết cục): " + json.dumps(bk["h2_mo_ta"], ensure_ascii=False))
    bk["h3_vnindex"] = _an_toan("H3 VN-INDEX", ra, lambda: h3_vnindex(cache))
    ra("H3 (mô tả, VN-INDEX): " + json.dumps(bk["h3_vnindex"], ensure_ascii=False))
    luu()

    def sau_moc():
        chuoi2, vung2, s2 = nap_cache(cache, ma_ds, moc, vung="sau_moc")
        M2 = dung_ma_tran(chuoi2, vung2)
        sd2 = s_matran(M2, chuoi2, s2)
        sm2, ts2 = chuan_ii_iii(M2, chuoi2)
        k = chay_ket_qua(M2, sd2, sm2, ts2, phi, doi_chung_dat=dat_dc, so_luot=so_luot, bang=bang, hat=HAT)
        k["ghi_chu"] = "vùng SAU mốc dữ liệu sạch: đã nhìn bởi các vòng tối ưu khác; báo RIÊNG, không phải kết cục chính"
        return k
    bk["vung_sau_moc"] = _an_toan("vùng sau mốc", ra, sau_moc)
    if "delta" in bk["vung_sau_moc"]:
        v = bk["vung_sau_moc"]
        ra(f"vùng SAU mốc (đã nhìn bởi các vòng tối ưu khác; báo RIÊNG; không phải kết cục): {v['so_ma']} mã, {v['so_ngay']} ngày; "
           f"{_dong_delta(v['delta']['i'])}; nhãn máy tính {v['ket_cuc']['ket_cuc']}")
    luu()

    sau = MT.bam_cache(cache)
    out["bam_sau_chay"] = sau
    khop = sau["sha256"] == truoc["sha256"]
    ra(f"băm cache SAU lượt chạy: {sau['sha256']} → {'KHỚP băm trước' if khop else 'LỆCH → K0'}")
    nhan = k_ban_dau if (khop and khop_ky) else KET_CUC_K0
    out["ket_cuc_cuoi"] = {**kq["ket_cuc"], "ket_cuc": nhan}
    ra(f"KẾT CỤC CUỐI (sau băm cache): {nhan}")
    luu()
    return out


def lenh_ket_qua(a) -> int:
    """Lượt chạy kết cục trên dữ liệu THẬT. Hai khoá độc lập: hằng `CHO_PHEP_DOC_KET_QUA_THAT` (Lát 4b lật nó trong commit riêng, rồi
    khoá lại sau lượt chạy) và câu xác nhận gõ nguyên văn. Thiếu một trong hai thì thoát 3 TRƯỚC khi nạp bất kỳ dữ liệu nào."""
    if not CHO_PHEP_DOC_KET_QUA_THAT or a.xac_nhan != CAU_XAC_NHAN_LAT_4B:
        print("TỪ CHỐI: lượt đọc kết cục trên dữ liệu thật bị khoá (ĐO 34: chạy MỘT lần, ở Lát 4b). "
              "Khoá: CHO_PHEP_DOC_KET_QUA_THAT + câu xác nhận.")
        return 3
    chay_lat_4b(Path(a.cache), ghi=a.ghi)
    return 0


def doi_chung_tat_ca(cache: Path, ra=print, so_luot: int = SO_LUOT_NGAU_NHIEN) -> dict:
    """Chạy đối chứng (i)–(vi) trên cache THẬT, vùng sạch. KHÔNG tính Δ của Dow so với chuẩn nào: (i) là đồng nhất thức
    trên giá, (ii) chỉ dùng độ dài khoảng của Dow, (iii) dịch vòng ≥ 252 phiên và chỉ in tỷ lệ bắt, rào hoà vốn chỉ đọc
    chi phí, (iv) so với bản dựng độc lập, (v) bất biến khi cắt, (vi) băm cache."""
    import mo_ta_cau_truc_gia as MT
    kq = {}
    truoc = MT.bam_cache(cache)
    ra(f"(vi) băm cache TRƯỚC: {truoc['sha256']} ({truoc['so_file']} file)")
    kq["bam_truoc"] = truoc
    if truoc["sha256"] != BAM_CACHE_KY:
        ra(f"CẢNH BÁO: băm khác băm đã ký {BAM_CACHE_KY[:16]}…")
    ktc_mau = S.ktc_khoi_co_cap(np.random.default_rng(0).normal(size=300), np.zeros(300))
    lech_ktc = in_cau_hinh_ktc(ktc_mau, ra)
    kq["khop_cau_hinh_ktc"] = {"lech": lech_ktc}
    phi = phi_nua()
    chuoi, vung_ma, s = nap_cache(cache, vung="sach")
    M = dung_ma_tran(chuoi, vung_ma)
    s_dow = s_matran(M, chuoi, s)
    ra(f"vùng sạch: {len(M.ma)} mã có phiên trước mốc, {len(M.ngay)} ngày toàn cục "
       f"({M.ngay[0]} → {M.ngay[-1]}), {int(M.vung.sum())} ngày-mã")
    kq["quan_the"] = {"so_ma": len(M.ma), "so_ngay": len(M.ngay), "tu": M.ngay[0], "den": M.ngay[-1]}
    ci = doi_chung_i(M, phi)
    ra(f"(i)  luôn giữ = rổ trừ một vòng phí: lệch giá tối đa {ci['lech_gia_toi_da']:.2e}, lệch phí tối đa "
       f"{ci['lech_phi_toi_da']:.2e} trên {ci['so_ma']} mã → {'ĐẠT' if ci['dat'] else 'TRƯỢT'}")
    kq["i"] = ci
    cii = doi_chung_ii(M, s_dow, phi, so_luot)
    ra(f"(ii) hạt ngẫu nhiên đối chiếu kỳ vọng giải tích (SỬA S1): x̄ đo (dịch vòng ≥ 252, không khoá, không trượt) "
       f"{cii['trung_binh_x_tho']:+.4e} ± {cii['sai_so_chuan']:.3e} (SE) · E_gt {cii['ky_vong_giai_tich']:+.4e} · lệch "
       f"{cii['lech']:+.3e} = {cii['so_sigma']:.2f} SE, {cii['so_luot']} lượt, {cii['ma_vung_ngan']} mã vùng ≤ 252 → "
       f"{'ĐẠT' if cii['dat'] else 'TRƯỢT'}")
    ra(f"      báo kèm (không quyết định): bản có khoá biên + trượt trừ bản không (cùng lượt rút) "
       f"{cii['khoa_truot_chenh_cap']['trung_binh']:+.3e} ± {cii['khoa_truot_chenh_cap']['sai_so_chuan']:.1e}")
    kq["ii"] = cii
    ciii = doi_chung_iii(M, s_dow, phi)
    ra(f"(iii) tiêm lợi thế giả: rào hoà vốn {ciii['rao_hoa_von']:.6f} mỗi đơn vị đầu tư-ngày "
       f"(= chi phí mỗi ngày ÷ mức đầu tư mỗi ngày, chỉ đọc chi phí); mức đầu tư trung bình {ciii['phoi_trung_binh']:.4f}")
    for k, v in ciii["o"].items():
        ra(f"      hệ số {v['he_so_rao']} × rào (tiêm {v['tiem_moi_don_vi_ngay']:.6f}): bắt {v['bat']}/{v['so_lap']} = "
           f"{100 * v['ty_le']:.1f}%  Wilson [{100 * v['wilson'][0]:.1f} ; {100 * v['wilson'][1]:.1f}]")
    m = ciii["mde_80"]
    ra("      MDE₈₀ (cận trên, lưới thô): " + ("không ô nào đạt 80%" if m is None else
       f"{m['he_so_rao']}× rào = {m['tiem_moi_don_vi_ngay']:.3e} mỗi đơn-vị-đầu-tư-ngày = {m['diem_pt_von_moi_nam']:.2f} điểm % vốn "
       f"(71 ô) mỗi năm = {m['diem_pt_dang_dau_tu_moi_nam']:.1f} điểm % trên vốn đang đầu tư mỗi năm"))
    ra(f"      → {'ĐẠT' if ciii['dat'] else 'TRƯỢT'} (ô 0 im ≤ 10%, ô {HE_SO_K0}× rào bắt ≥ 80%)")
    kq["iii"] = ciii
    ma_tay = next((m for m in CUSTOM_WATCHLIST_SYMBOLS
                   if dung_lai_thu_cong(*chuoi[m][:1], chuoi[m][1], chuoi[m][2])["so_pivot_tay"] >= 3), None)
    civ = dung_lai_thu_cong(chuoi[ma_tay][0], chuoi[ma_tay][1], chuoi[ma_tay][2]) if ma_tay else {"khop": False}
    ra(f"(iv) ca thật đã biết, mã {ma_tay}: dựng độc lập 3 pivot swing đầu → {'KHỚP' if civ['khop'] else 'LỆCH'}")
    for d in civ.get("dong", []):
        ra(f"      tay {d['tay']}  mô-đun {d['mo_dun']}  {'khớp' if d['khop'] else 'LỆCH'}")
    kq["iv"] = civ
    cat_ma, cat_dong = 0, 0
    import io
    from contextlib import redirect_stdout
    buf = io.StringIO()
    with redirect_stdout(buf):
        ma_cat = MT.lenh_kiem_cat(argparse.Namespace(cache=str(cache), so_diem=40, hat=0, o_luoi=False,
                                                      so_diem_luoi=6, so_ma_luoi=12))
    dong_cuoi = [x for x in buf.getvalue().splitlines() if x.startswith("tổng")]
    ra(f"(v)  bất biến khi cắt trên cache thật, 71 mã + VN-INDEX, ô mặc định: mã thoát {ma_cat}; {dong_cuoi[-1] if dong_cuoi else ''}")
    kq["v"] = {"ma_thoat": ma_cat, "dong_tong": dong_cuoi[-1] if dong_cuoi else None, "dat": ma_cat == 0}
    sau = MT.bam_cache(cache)
    ra(f"(vi) băm cache SAU:   {sau['sha256']} → {'KHỚP' if sau['sha256'] == truoc['sha256'] else 'LỆCH'}")
    kq["vi"] = {"bam_sau": sau, "dat": sau["sha256"] == truoc["sha256"]}
    kq["tat_ca_dat"] = bool(ci["dat"] and cii["dat"] and ciii["dat"] and civ["khop"] and kq["v"]["dat"] and kq["vi"]["dat"]
                            and not lech_ktc)
    ra("TẤT CẢ ĐỐI CHỨNG: " + ("ĐẠT" if kq["tat_ca_dat"] else "CÓ ĐỐI CHỨNG TRƯỢT → K0 nếu chạy kết cục"))
    return kq


def lenh_doi_chung(a) -> int:
    kq = doi_chung_tat_ca(Path(a.cache), so_luot=a.so_luot)
    if a.ghi:
        Path(a.ghi).write_text(json.dumps(kq, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return 0 if kq["tat_ca_dat"] else 1


def lenh_cau_hinh_ktc(_a) -> int:
    ktc = S.ktc_khoi_co_cap(np.random.default_rng(0).normal(size=300), np.zeros(300))
    return 0 if not in_cau_hinh_ktc(ktc) else 1


def lenh_khoang_cach_ii(a) -> int:
    """Phân rã khoảng cách (ii) từng bước và thử gài lỗi (BƯỚC 252). CHỈ dùng trạng thái, độ dài khoảng và lợi nhuận của mã /
    của chuẩn ngẫu nhiên; KHÔNG tính Δ của danh mục Dow."""
    chuoi, vung_ma, s = nap_cache(Path(a.cache), vung="sach")
    M = dung_ma_tran(chuoi, vung_ma)
    s_dow = s_matran(M, chuoi, s)
    phi = phi_nua()
    print(f"vùng sạch: {len(M.ma)} mã, {len(M.ngay)} ngày toàn cục ({M.ngay[0]} → {M.ngay[-1]})")
    for ten, v in phan_ra_khoang_cach_ii(M, s_dow):
        print(f"  {ten:62s} {v:+.4e}")
    sach = doi_chung_ii(M, s_dow, phi, a.so_luot)
    print(f"  động cơ KHÔNG gài lỗi: x̄ {sach['trung_binh_x_tho']:+.4e} ± {sach['sai_so_chuan']:.2e}, lệch so E_gt "
          f"{sach['lech']:+.2e} = {sach['so_sigma']:.2f} SE → {'ĐẠT' if sach['dat'] else 'TRƯỢT'}")
    sd = float(ngau_nhien(M, s_dow, phi, "dich", a.so_luot)["x_phi"].std(ddof=1))
    rh = rao_hoa_von(M, s_dow, phi)
    print(f"  độ lệch chuẩn của x̄ mỗi lượt rút (dịch vòng, sau phí): {sd:.4e}; 1,96 × = {1.96 * sd:.4e}; tiêm 20× rào × e = "
          f"{HE_SO_K0 * rh['rao'] * rh['phoi_trung_binh']:.4e} ({HE_SO_K0 * rh['rao'] * rh['phoi_trung_binh'] / (1.96 * sd):.2f} lần nửa bề rộng một lượt)")
    print(f"  2 SE của (ii) = {2 * sach['sai_so_chuan']:.3e} = {2 * sach['sai_so_chuan'] / rh['phoi_trung_binh'] * 1e4:.3f} bp mỗi đơn-vị-đầu-tư-ngày")
    for ten, dc in LOI_CAY.items():
        r = doi_chung_ii(M, s_dow, phi, a.so_luot, dong_co=dc)
        print(f"  gài lỗi {ten:12s}: lệch so E_gt {r['lech']:+.2e} = {r['so_sigma']:.2f} SE → {'ĐẠT (KHÔNG bắt)' if r['dat'] else 'TRƯỢT (bắt)'}")
    return 0


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="lenh", required=True)
    sub.add_parser("cau-hinh-ktc", help="in cấu hình KTC dùng và kết quả so với bản ghi đã khoá")
    g = sub.add_parser("khoang-cach-ii", help="phân rã khoảng cách của đối chứng (ii) và thử gài lỗi; KHÔNG tính Δ của Dow")
    g.add_argument("--cache", required=True)
    g.add_argument("--so-luot", type=int, default=SO_LUOT_NGAU_NHIEN)
    d = sub.add_parser("doi-chung", help="đối chứng (i)–(vi) trên cache thật; KHÔNG tính Δ của Dow")
    d.add_argument("--cache", required=True)
    d.add_argument("--ghi", help="đường dẫn JSON kết quả")
    d.add_argument("--so-luot", type=int, default=SO_LUOT_NGAU_NHIEN)
    k = sub.add_parser("ket-qua", help="KHOÁ (hằng + câu xác nhận): lượt đọc kết cục DUY NHẤT trên dữ liệu thật (Lát 4b)")
    k.add_argument("--cache", required=True)
    k.add_argument("--xac-nhan", default="")
    k.add_argument("--ghi", help="đường dẫn JSON kết quả (ghi sau kết cục, sau báo kèm, và cuối lượt)")
    a = ap.parse_args(argv)
    if a.lenh == "cau-hinh-ktc":
        return lenh_cau_hinh_ktc(a)
    if a.lenh == "doi-chung":
        return lenh_doi_chung(a)
    if a.lenh == "khoang-cach-ii":
        return lenh_khoang_cach_ii(a)
    return lenh_ket_qua(a)


if __name__ == "__main__":
    sys.exit(main())
