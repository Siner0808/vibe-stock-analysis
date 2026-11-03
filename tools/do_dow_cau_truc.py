"""ĐO 34 — cấu trúc giá theo lý thuyết Dow, CHỈ MUA / ĐỨNG NGOÀI (BƯỚC 251 = Lát 4a của đặc tả Dow).

Tiêu chí ký trước: `docs/TIEU-CHI-DOC-TRUOC.md`, mục *ĐO 34* (commit riêng, TRƯỚC mọi dòng mã). Mọi hằng số,
chuẩn, đối chứng và kết cục ở đây chép từ mục ấy; đổi một con số sau khi nhìn kết quả là vi phạm bất biến 7.

BƯỚC này (Lát 4a) dựng DỤNG CỤ và chạy ĐỐI CHỨNG. Nó KHÔNG đọc, KHÔNG tính, KHÔNG in lợi nhuận của danh mục Dow
so với chuẩn nào, trên dữ liệu thật. Đường ra kết cục chỉ chạy trên dữ liệu TỔNG HỢP trong test; trên dữ liệu thật nó
bị khoá sau `CHO_PHEP_DOC_KET_QUA_THAT` (= False ở Lát 4a) VÀ một cờ gõ nguyên văn (`CAU_XAC_NHAN_LAT_4B`) — Lát 4b
(BƯỚC riêng) lật khoá và chạy MỘT lần.

    ./.venv/Scripts/python.exe tools/do_dow_cau_truc.py doi-chung --cache <thư mục cache> [--ghi X.json]
    ./.venv/Scripts/python.exe tools/do_dow_cau_truc.py cau-hinh-ktc
    ./.venv/Scripts/python.exe tools/do_dow_cau_truc.py ket-qua --cache <thư mục cache> --xac-nhan "<câu>"   (khoá ở 4a)

CHỈ ĐỌC: không mạng, không `import vnstock`, không ghi cache, không đọc sổ lệnh. Chỉ ghi MỘT file JSON kết quả
ở đường dẫn người gọi chọn (`--ghi`).

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
SO_LAP_TIEM = 30                 # đối chứng (iii): 30 lượt lặp (lỗi 99)
NGUONG_BAT_TIEM = 0.80           # ... phải bắt ≥ 80%
HE_SO_NUA_RAO = 0.5              # lợi thế tiêm = nửa rào hoà vốn
PHI_NHAY_PCT = 0.76              # độ nhạy phí: cận trên của dải bán lẻ (CLAUDE.md)
NGUONG_THANG_A_CONG = 0.95       # A⁺: Dow thắng ≥ 95% lượt rút (iv)
SO_SIGMA_DOI_CHUNG_II = 2.0      # đối chứng (ii): trong khoảng 2 sai số chuẩn
CUA_SO_SU_KIEN = 21              # H2: 21 phiên từ mở cửa t+1
BAM_CACHE_KY = "acf6dca1dd38d5157ee397bbccb7f82d662698b318a6dcf6b72617335bf44d6e"
DUONG_BANG_DO_PHU = GOC / "docs" / "san-dau-do-phu.json"
DUONG_MOC_SACH = GOC / "docs" / "moc_du_lieu_sach.json"

#: Khoá lượt chạy trên dữ liệu THẬT. Lát 4a để False; Lát 4b (BƯỚC 252) lật nó trong một commit riêng.
CHO_PHEP_DOC_KET_QUA_THAT = False
CAU_XAC_NHAN_LAT_4B = "DOC KET QUA DO 34 MOT LAN"

KET_CUC_K0, KET_CUC_A, KET_CUC_A_CONG, KET_CUC_B, KET_CUC_C = "K0", "A", "A+", "B", "C"
KET_CUC_KHE = "KHÔNG PHÂN LOẠI ĐƯỢC"          # khe của văn bản ký (xem `ket_cuc`)
KET_CUC_MAU_THUAN = "MÂU THUẪN"                # hai kết cục cùng khớp (không được xảy ra)


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
    """Phân loại K0 / A / A⁺ / B / C đúng chữ của ĐO 34. Ngưỡng SUY RA từ nửa bề rộng KTC của Δ_(i): nhỏ = một nửa,
    lớn = một lần. Mỗi nhãn khớp được tính ĐỘC LẬP; đúng một nhãn → trả nhãn ấy; KHÔNG nhãn nào → `KHE` (văn bản
    ký không phủ hết các trường hợp, xem STATE BƯỚC 251; KHÔNG tự gán); hai nhãn trở lên → `MAU_THUAN`."""
    if not doi_chung_dat:
        return {"ket_cuc": KET_CUC_K0, "khop": [KET_CUC_K0], "nguong_nho": None, "nguong_lon": None}
    nua = (ktc_i[1] - ktc_i[0]) / 2.0
    nho, lon = nua / 2.0, nua
    chua0 = lambda k: k[0] <= 0.0 <= k[1]  # noqa: E731
    khop = []
    if abs(delta_i) <= nho or (chua0(ktc_i) and chua0(ktc_ii) and chua0(ktc_iii)):
        khop.append(KET_CUC_A)
    if nho < delta_i <= lon and not chua0(ktc_i) and thang_iv >= NGUONG_THANG_A_CONG and \
            (not chua0(ktc_ii) or not chua0(ktc_iii)):
        khop.append(KET_CUC_A_CONG)
    if delta_i > lon:
        khop.append(KET_CUC_B)
    if delta_i < -nho and not chua0(ktc_i):
        khop.append(KET_CUC_C)
    nhan = khop[0] if len(khop) == 1 else (KET_CUC_KHE if not khop else KET_CUC_MAU_THUAN)
    return {"ket_cuc": nhan, "khop": khop, "nguong_nho": nho, "nguong_lon": lon}


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
               lan: int = 100, giu_x: bool = False) -> dict:
    """Chuẩn (iv): `so_luot` lượt rút, mỗi lượt một vị thế ngẫu nhiên cho MỌI mã. kieu = "dat" (cùng số khoảng, cùng độ
    dài, ngày bắt đầu ngẫu nhiên), "dich" (dịch vòng ≥ 252) hoặc "hoan" (như "dich" nhưng chuỗi trạng thái của mã j là của
    một mã khác, hoán vị ngẫu nhiên: cắt tương quan giữa thời-gian-trong-thị-trường của mã và độ trôi của mã). Trả trung bình x mỗi lượt (gộp, không phí: `x_tho`) và
    sau phí (`x_phi`), và nếu `giu_x` thì cả chuỗi x_t trung bình qua lượt."""
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
        kq = chay_dong_co(muc.astype(float), M, phi)
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


def doi_chung_ii(M: MaTran, s_dow: np.ndarray, phi: float, so_luot: int = SO_LUOT_NGAU_NHIEN) -> dict:
    """(ii) Hạt ngẫu nhiên: chuẩn (iv) đồng bộ thời gian cho kỳ vọng ≈ lợi nhuận thị trường — trung bình x gộp
    (không phí) trên các lượt phải nằm trong 2 sai số chuẩn của chính nó quanh 0 (x = lợi nhuận danh mục trừ e × rổ).
    Chỉ dùng độ dài các khoảng của Dow, KHÔNG dùng lợi nhuận của Dow."""
    def mot(kieu):
        r = ngau_nhien(M, s_dow, phi, kieu, so_luot)
        tb, se = float(r["x_tho"].mean()), float(r["x_tho"].std(ddof=1) / np.sqrt(len(r["x_tho"])))
        return {"trung_binh_x_tho": tb, "sai_so_chuan": se, "so_sigma": abs(tb) / se if se > 0 else float("inf"),
                "ma_vung_ngan": r["ma_vung_ngan"], "dat": trong_khoang_se(tb, se)}
    ky = mot("dich")          # đúng chữ ĐO 34
    hoan = mot("hoan")        # chẩn đoán: cắt tương quan thời-gian-trong-thị-trường × độ trôi của từng mã
    return {"so_luot": so_luot, **ky, "hoan_vi": hoan, "ky_vong_giai_tich_doc_lap": ky_vong_doc_lap(M, s_dow)}


def ky_vong_doc_lap(M: MaTran, s_dow: np.ndarray) -> float:
    """Kỳ vọng giải tích của x gộp mỗi ngày khi thời điểm vào/ra độc lập với lợi nhuận nhưng MỖI MÃ giữ tỷ lệ
    thời-gian-trong-thị-trường p_j của nó: Σ_j p_j m_j / 71 − (Σ_j p_j / 71) × trung bình(r_rổ). Khác 0 khi p_j và độ trôi
    m_j của mã tương quan (mã xu hướng lên có thủy triều "tăng" lâu hơn). Chỉ đọc p_j (từ trạng thái) và trôi của
    CHUẨN ngẫu nhiên, không phải lợi nhuận của danh mục Dow."""
    v = M.vung
    p = (s_dow * v).sum(axis=0) / np.maximum(v.sum(axis=0), 1)
    m = lai_ro_theo_ma(M).sum(axis=0) / np.maximum(v.sum(axis=0), 1)
    return float((p * m).sum() / SO_MA - p.sum() / SO_MA * ro_trung_binh(M).mean())


NGUONG_IM_TIEM = 0.10    # ô "không tiêm gì" phải IM: tỷ lệ bắt ≤ 10% (lỗi 94; danh nghĩa một phía 2,5%)


def phan_quyet_tiem(ty_le_khong: float, ty_le_nua_rao: float) -> bool:
    """Đạt khi CẢ HAI: ô không tiêm IM (≤ `NGUONG_IM_TIEM`) VÀ ô nửa rào BẮT (≥ `NGUONG_BAT_TIEM`)."""
    return bool(ty_le_khong <= NGUONG_IM_TIEM and ty_le_nua_rao >= NGUONG_BAT_TIEM)


def doi_chung_iii(M: MaTran, s_dow: np.ndarray, phi: float, *, so_lap: int = SO_LAP_TIEM, so_ngan_hang: int = 200,
                  he_so: tuple = (0.0, HE_SO_NUA_RAO, 1.0, 5.0, 10.0, 20.0), hat: int = HAT) -> dict:
    """(iii) Tiêm lợi thế giả (khuôn BƯỚC 113, lỗi 99). Nền = lợi nhuận THẬT với trạng thái Dow DỊCH VÒNG ≥ 252 phiên
    (rời nhãn, giữ tự tương quan — lỗi 94); tiêm `a` = hệ số × rào hoà vốn vào mỗi đơn-vị-đầu-tư-ngày (x += a × e);
    "bắt" = cận dưới KTC có cặp (hàm sân đấu) của mean(x_tiêm) − mean(x_nền) > 0 với x_nền = trung bình mỗi ngày
    của một ngân hàng `so_ngan_hang` lượt dịch vòng độc lập. Phải IM ở hệ số 0 và BẮT ≥ 80% ở nửa rào, trên `so_lap`
    lượt (không phải một lượt). Dịch vòng ≥ 252 nên không lượt nào là trạng thái Dow thật (không đọc Δ của Dow)."""
    rao = rao_hoa_von(M, s_dow, phi)["rao"]
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
        ket[str(h)] = {"he_so_rao": h, "tiem_moi_don_vi_ngay": a_tiem, "bat": bat, "so_lap": so_lap, "ty_le": bat / so_lap}
    dat = phan_quyet_tiem(ket[str(he_so[0])]["ty_le"], ket[str(HE_SO_NUA_RAO)]["ty_le"])
    return {"rao_hoa_von": rao, "o": ket, "dat": dat,
            "ghi_chu": "dat = ty le bat o he so 0 <= 10% (phai im) VA o nua rao >= 80%"}


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
    return {"so_ngay": len(M.ngay), "so_ma": len(M.ma), "x_trung_binh_moi_ngay": float(x_dow.mean()),
            "x_cong_don_diem_phan_tram": float(x_dow.sum() * 100.0), "cot_tho_cong_don_diem_phan_tram":
            float(cot_tho(kq_dow, ro, M)[0].sum() * 100.0), "delta": th, "ngau_nhien": iv, "thang_iv": thang_iv,
            "lech_cau_hinh_ktc": lech, "ket_cuc": kc,
            "so_khoang_giu": int(sum(len(doan_giu(s_dow[np.flatnonzero(M.vung[:, j])[0]:np.flatnonzero(M.vung[:, j])[-1] + 1, j]))
                                     for j in range(len(M.ma))))}


def lenh_ket_qua(a) -> int:
    """Lượt chạy kết cục trên dữ liệu THẬT — KHOÁ ở Lát 4a. Hai khoá độc lập: hằng `CHO_PHEP_DOC_KET_QUA_THAT` (Lát 4b
    lật nó trong commit riêng) và câu xác nhận gõ nguyên văn. Thiếu một trong hai thì thoát 3 TRƯỚC khi nạp bất kỳ
    dữ liệu nào."""
    if not CHO_PHEP_DOC_KET_QUA_THAT or a.xac_nhan != CAU_XAC_NHAN_LAT_4B:
        print("TỪ CHỐI: Lát 4a không đọc kết cục trên dữ liệu thật (ĐO 34: không đọc lợi nhuận trước khi 8.1 xanh trên cache "
              "thật và trước Lát 4b). Khoá: CHO_PHEP_DOC_KET_QUA_THAT + câu xác nhận.")
        return 3
    raise NotImplementedError("Lát 4b nối đường này; Lát 4a không có nhánh chạy dữ liệu thật")


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
    ra(f"(ii) hạt ngẫu nhiên, đúng chữ ĐO 34 (dịch vòng ≥ 252): trung bình x gộp {cii['trung_binh_x_tho']:+.3e} ± "
       f"{cii['sai_so_chuan']:.3e} (SE) = {cii['so_sigma']:.2f} SE, {cii['so_luot']} lượt → {'ĐẠT' if cii['dat'] else 'TRƯỢT'}")
    ra(f"      chẩn đoán (KHÔNG thay điều kiện ký): kỳ vọng giải tích khi thời điểm độc lập nhưng mỗi mã giữ tỷ lệ "
       f"thời-gian-trong-thị-trường của nó = {cii['ky_vong_giai_tich_doc_lap']:+.3e}; bản hoán vị mã (cắt tương quan "
       f"tỷ lệ × độ trôi): {cii['hoan_vi']['trung_binh_x_tho']:+.3e} ± {cii['hoan_vi']['sai_so_chuan']:.3e} = "
       f"{cii['hoan_vi']['so_sigma']:.2f} SE → {'ĐẠT' if cii['hoan_vi']['dat'] else 'TRƯỢT'}")
    kq["ii"] = cii
    ciii = doi_chung_iii(M, s_dow, phi)
    ra(f"(iii) tiêm lợi thế giả: rào hoà vốn {ciii['rao_hoa_von']:.6f} mỗi đơn vị đầu tư-ngày "
       f"(= chi phí mỗi ngày ÷ mức đầu tư mỗi ngày, chỉ đọc chi phí)")
    for k, v in ciii["o"].items():
        ra(f"      hệ số {v['he_so_rao']} × rào (tiêm {v['tiem_moi_don_vi_ngay']:.6f}): bắt {v['bat']}/{v['so_lap']} = "
           f"{100 * v['ty_le']:.1f}%")
    ra(f"      → {'ĐẠT' if ciii['dat'] else 'TRƯỢT'} (im ở 0, bắt ≥ 80% ở nửa rào)")
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


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="lenh", required=True)
    sub.add_parser("cau-hinh-ktc", help="in cấu hình KTC dùng và kết quả so với bản ghi đã khoá")
    d = sub.add_parser("doi-chung", help="đối chứng (i)–(vi) trên cache thật; KHÔNG tính Δ của Dow")
    d.add_argument("--cache", required=True)
    d.add_argument("--ghi", help="đường dẫn JSON kết quả")
    d.add_argument("--so-luot", type=int, default=SO_LUOT_NGAU_NHIEN)
    k = sub.add_parser("ket-qua", help="KHOÁ ở Lát 4a: đọc kết cục trên dữ liệu thật")
    k.add_argument("--cache", required=True)
    k.add_argument("--xac-nhan", default="")
    a = ap.parse_args(argv)
    if a.lenh == "cau-hinh-ktc":
        return lenh_cau_hinh_ktc(a)
    if a.lenh == "doi-chung":
        return lenh_doi_chung(a)
    return lenh_ket_qua(a)


if __name__ == "__main__":
    sys.exit(main())
