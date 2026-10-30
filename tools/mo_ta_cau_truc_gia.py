"""Dụng cụ MÔ TẢ của `cau_truc_gia` trên cache giá (BƯỚC 247, Dow Lát 1). CHỈ ĐỌC.

Chỉ in số MÔ TẢ (độ trễ biết, số pivot, giá bằng nhau, cờ nến) và chạy phép thử bất biến khi cắt
trên dữ liệu thật (Tầng B). KHÔNG đọc lợi nhuận, KHÔNG tính alpha — lợi nhuận của luật này chỉ
được đọc ở Lát 4 theo `ĐO 34` (bất biến 7). Không mạng, không ghi cache; chỉ ghi MỘT file JSON
kết quả ở đường dẫn người gọi chọn (`--ghi`).

    ./.venv/Scripts/python.exe tools/mo_ta_cau_truc_gia.py mo-ta --cache <thư mục cache> [--ghi X.json]
    ./.venv/Scripts/python.exe tools/mo_ta_cau_truc_gia.py kiem-cat --cache <thư mục cache> [--so-diem 40]

Rổ: `vn100_symbols.CUSTOM_WATCHLIST_SYMBOLS` (71 mã). Hệ số giá tính MỘT lần trên cả chuỗi rồi
truyền cho mọi lượt cắt (xem docstring `cau_truc_gia`). Băm cache bằng
`tools/do25_ke_hoach_vao_lenh.py::bam_thu_muc` trước và sau; hai băm phải bằng nhau.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))
sys.path.insert(0, str(GOC))

import cau_truc_gia as C  # noqa: E402
from data_quality import price_multiplier  # noqa: E402
from san_giao_dich import san_cua  # noqa: E402
from truot_gia import buoc_gia  # noqa: E402
from vn100_symbols import CUSTOM_WATCHLIST_SYMBOLS  # noqa: E402

PHIEN_MOI_NAM = 252
#: Chuỗi chỉ số: KHÔNG có lưới bước giá. Coi 1.500 điểm là 1.500.000đ (bước 100đ, nửa bước 0,05 điểm)
#: để dung sai bằng-nhau thành không đáng kể.
HE_SO_CHI_SO = 1000.0


def bam_cache(thu_muc) -> dict:
    import do25_ke_hoach_vao_lenh as D25     # nhập lười: kéo theo module đo, không cần khi chỉ mô tả
    return D25.bam_thu_muc(thu_muc)


def nap(cache: Path, ma: str) -> pd.DataFrame:
    df = pd.read_csv(cache / f"{ma}.csv")
    return df.sort_values("time").reset_index(drop=True)


def cau_hinh(cache: Path, ma: str):
    """(df, he_so_gia, sàn) — cùng đường tính cho mọi lượt cắt của một mã."""
    df = nap(cache, ma)
    if ma == "VNINDEX":
        return df, HE_SO_CHI_SO, "HOSE"
    return df, float(price_multiplier(df)), san_cua(ma)


def phan_vi(x, q):
    return float(np.percentile(x, q)) if len(x) else None


def luoi_o():
    return [(ho, ts) for ho in sorted(C.LUOI) for ts in C.LUOI[ho]]


# ── mô tả ─────────────────────────────────────────────────────────────────────────────────
def mo_ta_o_luoi(cache: Path, rổ: list[str], ho: str, tham_so: tuple) -> dict:
    tre = {c: [] for c in C.CAPS}
    so_dong = Counter()
    thay = 0
    so_nam = 0.0
    theo_nam = {c: Counter() for c in C.CAPS}
    for ma in rổ:
        df, he, san = cau_hinh(cache, ma)
        r = C.doc_cau_truc(df, he_so_gia=he, san=san, ho=ho, tham_so=tham_so)
        so_nam += len(df) / PHIEN_MOI_NAM
        for p in r.nhat_ky:
            so_dong[p.cap] += 1
            thay += p.su_kien == C.THAY_THE
            tre[p.cap].append(p.chi_so_biet - p.chi_so_xay_ra)
            theo_nam[p.cap][p.ngay_biet[:4]] += 1
    return {
        "ho": ho, "tham_so": list(tham_so),
        "so_dong": {c: so_dong[c] for c in C.CAPS},
        "dong_moi_ma_moi_nam": {c: round(so_dong[c] / so_nam, 2) for c in C.CAPS},
        "do_tre_phien_trung_vi": {c: phan_vi(tre[c], 50) for c in C.CAPS},
        "do_tre_phien_p90": {c: phan_vi(tre[c], 90) for c in C.CAPS},
        "do_tre_phien_max": {c: (max(tre[c]) if tre[c] else None) for c in C.CAPS},
        "ty_le_thay_the": round(thay / max(1, sum(so_dong.values())), 4),
        "theo_nam_biet": {c: dict(sorted(theo_nam[c].items())) for c in C.CAPS},
    }


def hieu_luc(nhat_ky, cap):
    ds = []
    for p in nhat_ky:
        if p.cap != cap:
            continue
        if p.su_kien == C.THAY_THE:
            ds[-1] = p
        else:
            ds.append(p)
    return ds


def gia_bang_nhau(cache: Path, rổ: list[str]) -> dict:
    """Ô lưới mặc định: chênh (theo số bước giá) giữa hai pivot hiệu lực CÙNG LOẠI liền kề, mỗi cấp;
    tỷ lệ đóng cửa nằm trên lưới theo năm; tác động của dung sai nửa bước lên nhật ký."""
    kho = {c: Counter() for c in C.CAPS}
    nhan = {c: Counter() for c in C.CAPS}
    tren_luoi, so_nen_nam = Counter(), Counter()
    bang_gia_truoc = 0
    ma_khac_0, ma_khac_1 = [], []
    dong_khac_0 = dong_khac_1 = 0
    goc = C.nua_buoc
    for ma in rổ:
        df, he, san = cau_hinh(cache, ma)
        r = C.doc_cau_truc(df, he_so_gia=he, san=san)
        nam = pd.to_datetime(df["time"]).dt.year.astype(str).to_numpy()
        gia = df["close"].to_numpy(dtype=float) * he
        buoc = np.array([buoc_gia(g, san) for g in gia])
        du = np.abs(gia / buoc - np.round(gia / buoc))
        for y, ok in zip(nam, du < 1e-6):
            so_nen_nam[y] += 1
            tren_luoi[y] += bool(ok)
        bang_gia_truoc += int((df["close"].diff() == 0).sum())
        for cap in C.CAPS:
            ds = hieu_luc(r.nhat_ky, cap)
            for p in ds:
                nhan[cap][p.nhan] += 1
            for loai in (C.DINH, C.DAY):
                xs = [p for p in ds if p.loai == loai]
                for a, b in zip(xs, xs[1:]):
                    t = abs(b.gia - a.gia) * he / buoc_gia(b.gia * he, san)
                    kho[cap]["=0"] += t < 1e-9
                    kho[cap]["(0,0.5]"] += 1e-9 <= t <= 0.5
                    kho[cap]["(0.5,1)"] += 0.5 < t < 1
                    kho[cap]["[1,2]"] += 1 <= t <= 2
                    kho[cap]["tong_cap"] += 1
        # nhạy cảm với dung sai: 0 (so nghiêm ngặt) và một bước đầy đủ
        for ten, ham in (("0", lambda g, h, s: 0.0), ("1", lambda g, h, s: buoc_gia(g * h, s) / h)):
            C.nua_buoc = ham
            try:
                alt = C.doc_cau_truc(df, he_so_gia=he, san=san)
            finally:
                C.nua_buoc = goc
            a, b = set(r.nhat_ky), set(alt.nhat_ky)
            if a != b:
                (ma_khac_0 if ten == "0" else ma_khac_1).append(ma)
                if ten == "0":
                    dong_khac_0 += len(a ^ b)
                else:
                    dong_khac_1 += len(a ^ b)
    return {
        "chenh_theo_buoc_giua_hai_pivot_cung_loai_lien_ke": {c: dict(kho[c]) for c in C.CAPS},
        "nhan_pivot_hieu_luc": {c: dict(nhan[c]) for c in C.CAPS},
        "ty_le_dong_cua_tren_luoi_theo_nam": {y: round(tren_luoi[y] / so_nen_nam[y], 4) for y in sorted(so_nen_nam)},
        "so_nen_dong_cua_bang_nen_truoc": bang_gia_truoc,
        "nhat_ky_doi_neu_dung_sai_bang_0": {"so_ma": len(ma_khac_0), "so_dong_khac": dong_khac_0, "ma": ma_khac_0[:15]},
        "nhat_ky_doi_neu_dung_sai_bang_1_buoc": {"so_ma": len(ma_khac_1), "so_dong_khac": dong_khac_1, "ma": ma_khac_1[:15]},
    }


def co_nen(cache: Path, rổ: list[str]) -> dict:
    """Số nến khoá biên / không giao dịch / đứng yên, và số pivot mặc định mang cờ."""
    nen_tong = 0
    kb = Counter()
    kgd = phang = 0
    piv_kb, piv_kgd, piv_tong = Counter(), 0, 0
    tran_la_dinh = san_la_day = 0
    for ma in rổ:
        df, he, san = cau_hinh(cache, ma)
        nens = C.chuan_bi_nen(df, san)
        nen_tong += len(nens)
        dong = df["close"].to_numpy(dtype=float)
        for n in nens:
            kb[n.khoa_bien] += 1
            kgd += n.khong_giao_dich
            cua_so = dong[max(0, n.chi_so - 5):n.chi_so + 6]    # chỉ để ĐẾM: kiểm máy đo, không vào mô-đun
            tran_la_dinh += n.khoa_bien == "KICH_TRAN" and dong[n.chi_so] >= cua_so.max()
            san_la_day += n.khoa_bien == "KICH_SAN" and dong[n.chi_so] <= cua_so.min()
        c = df["close"]
        phang += int(((df["high"] == df["low"]) & (df["low"] == c) & (c == c.shift(1))).sum())
        r = C.doc_cau_truc(df, he_so_gia=he, san=san)
        for p in r.nhat_ky:
            piv_tong += 1
            piv_kb[p.khoa_bien] += 1
            piv_kgd += p.khong_giao_dich
    return {"so_nen": nen_tong,
            "khoa_bien": {str(k): v for k, v in kb.items()},
            "kich_tran_la_dong_cua_cao_nhat_cua_so_pm5": int(tran_la_dinh),
            "kich_san_la_dong_cua_thap_nhat_cua_so_pm5": int(san_la_day),
            "khong_giao_dich_volume_0": kgd,
            "nen_dung_yen_cao_thap_dong_bang_dong_truoc": phang,
            "pivot_mac_dinh_tong": piv_tong,
            "pivot_mac_dinh_khoa_bien": {str(k): v for k, v in piv_kb.items()},
            "pivot_mac_dinh_khong_giao_dich": piv_kgd}


def ca_da_biet(cache: Path) -> dict:
    """Ca thật: tra đỉnh đóng cửa VN-INDEX trong 03–06/2022 bằng lệnh trên cache (không gõ ngày)."""
    df, he, san = cau_hinh(cache, "VNINDEX")
    gio = pd.to_datetime(df["time"])
    vung = df[(gio >= "2022-03-01") & (gio <= "2022-06-30")]
    i = int(vung["close"].idxmax())
    r = C.doc_cau_truc(df, he_so_gia=he, san=san)
    gan = [p for p in r.nhat_ky if p.loai == C.DINH and abs(p.chi_so_xay_ra - i) <= 15]
    return {"dinh_dong_cua_trong_vung": {"chi_so": i, "ngay": str(df['time'].iloc[i]), "dong": float(df['close'].iloc[i])},
            "pivot_dinh_trong_15_phien": [
                {"cap": p.cap, "xay_ra": p.ngay_xay_ra, "biet": p.ngay_biet, "gia": p.gia,
                 "tre_phien": p.chi_so_biet - p.chi_so_xay_ra, "nhan": p.nhan} for p in gan]}


def lenh_mo_ta(a) -> int:
    cache = Path(a.cache)
    bam_truoc = bam_cache(cache)
    kq = {"cache": bam_truoc, "so_ma": len(CUSTOM_WATCHLIST_SYMBOLS)}
    print(f"cache {bam_truoc['sha256'][:16]}… · {bam_truoc['so_file']} file · {kq['so_ma']} mã")
    kq["luoi"] = []
    for ho, ts in luoi_o():
        o = mo_ta_o_luoi(cache, CUSTOM_WATCHLIST_SYMBOLS, ho, ts)
        kq["luoi"].append(o)
        print(f"  {ho:7s}{str(ts):14s} dòng/mã/năm {o['dong_moi_ma_moi_nam']}  trễ trung vị {o['do_tre_phien_trung_vi']}"
              f"  p90 {o['do_tre_phien_p90']}  max {o['do_tre_phien_max']}  thay_thế {o['ty_le_thay_the']}")
    kq["gia_bang_nhau"] = gia_bang_nhau(cache, CUSTOM_WATCHLIST_SYMBOLS)
    print(json.dumps(kq["gia_bang_nhau"], ensure_ascii=False, indent=1))
    kq["co_nen"] = co_nen(cache, CUSTOM_WATCHLIST_SYMBOLS)
    print(json.dumps(kq["co_nen"], ensure_ascii=False, indent=1))
    kq["ca_da_biet_vnindex"] = ca_da_biet(cache)
    print(json.dumps(kq["ca_da_biet_vnindex"], ensure_ascii=False, indent=1))
    bam_sau = bam_cache(cache)
    kq["bam_sau"] = bam_sau
    print("băm cache sau:", "KHỚP" if bam_sau["sha256"] == bam_truoc["sha256"] else "LỆCH", bam_sau["sha256"][:16])
    if a.ghi:
        Path(a.ghi).write_text(json.dumps(kq, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0 if bam_sau["sha256"] == bam_truoc["sha256"] else 1


# ── Tầng B: bất biến khi cắt trên cache thật ──────────────────────────────────────────────
def diem_cat(n: int, so_diem: int, hat: int) -> list[int]:
    dau = list(range(0, min(n, 40), 3))
    ngau = random.Random(hat).sample(range(40, n), min(so_diem, max(0, n - 40))) if n > 40 else []
    return sorted(set(dau + ngau + [max(0, n - 2), n - 1]))


def kiem_cat_ma(df, he, san, ho, tham_so, so_diem, hat):
    day_du = C.doc_cau_truc(df, he_so_gia=he, san=san, ho=ho, tham_so=tham_so)
    # chạy tăng dần == cả bảng
    tt, log = C.khoi_tao(ho, tham_so, san, he), []
    for nen in C.chuan_bi_nen(df, san):
        tt, moi = C.cap_nhat(tt, nen)
        log.extend(moi)
    loi = [] if tuple(log) == day_du.nhat_ky else ["tang_dan != ca_bang"]
    for t in diem_cat(len(df), so_diem, hat):
        cat = C.doc_cau_truc(df.iloc[:t + 1], he_so_gia=he, san=san, ho=ho, tham_so=tham_so)
        if list(cat.nhat_ky) != C.nhat_ky_tai(day_du.nhat_ky, t):
            loi.append(f"t={t}")
    return loi, len(day_du.nhat_ky)


def lenh_kiem_cat(a) -> int:
    cache = Path(a.cache)
    truoc = bam_cache(cache)
    print(f"băm cache TRƯỚC: {truoc['sha256']} ({truoc['so_file']} file)")
    ma_ds = list(CUSTOM_WATCHLIST_SYMBOLS) + ["VNINDEX"]
    hong, tong_cat, tong_dong = [], 0, 0
    o = [("atr", (2, 4))] if not a.o_luoi else luoi_o()
    for ho, ts in o:
        so_diem = a.so_diem if (ho, ts) == ("atr", (2, 4)) else a.so_diem_luoi
        ma_dung = ma_ds if (ho, ts) == ("atr", (2, 4)) else ma_ds[:a.so_ma_luoi]
        cat_o = dong_o = 0
        for ma in ma_dung:
            df, he, san = cau_hinh(cache, ma)
            loi, so_dong = kiem_cat_ma(df, he, san, ho, ts, so_diem, a.hat)
            cat_o += len(diem_cat(len(df), so_diem, a.hat)) + 1
            dong_o += so_dong
            if loi:
                hong.append((ho, ts, ma, loi[:5]))
        tong_cat += cat_o
        tong_dong += dong_o
        print(f"  {ho:7s}{str(ts):14s} {len(ma_dung)} mã · {cat_o} phép so · {dong_o} dòng nhật ký")
    sau = bam_cache(cache)
    print(f"băm cache SAU:   {sau['sha256']}  {'KHỚP' if sau['sha256'] == truoc['sha256'] else 'LỆCH'}")
    print(f"tổng {tong_cat} phép so, {tong_dong} dòng nhật ký, {len(hong)} ca LỆCH")
    for h in hong[:20]:
        print("  LỆCH", h)
    return 0 if not hong and sau["sha256"] == truoc["sha256"] else 1


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="lenh", required=True)
    m = sub.add_parser("mo-ta", help="số mô tả trên cache (độ trễ, đếm, giá bằng, cờ)")
    m.add_argument("--cache", required=True)
    m.add_argument("--ghi", help="đường dẫn JSON kết quả")
    k = sub.add_parser("kiem-cat", help="Tầng B: bất biến khi cắt trên cache thật")
    k.add_argument("--cache", required=True)
    k.add_argument("--so-diem", type=int, default=40)
    k.add_argument("--hat", type=int, default=0)
    k.add_argument("--o-luoi", action="store_true", help="kiểm cả 10 ô lưới (ít điểm cắt hơn, ít mã hơn)")
    k.add_argument("--so-diem-luoi", type=int, default=6)
    k.add_argument("--so-ma-luoi", type=int, default=12)
    a = ap.parse_args(argv)
    return lenh_mo_ta(a) if a.lenh == "mo-ta" else lenh_kiem_cat(a)


if __name__ == "__main__":
    sys.exit(main())
