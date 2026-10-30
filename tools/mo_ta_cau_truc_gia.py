"""Dụng cụ MÔ TẢ của `cau_truc_gia` trên cache giá (BƯỚC 247 Lát 1, BƯỚC 249 Lát 2). CHỈ ĐỌC.

Chỉ in số MÔ TẢ (độ trễ biết, số pivot, giá bằng nhau, cờ nến; số sự kiện, tỷ lệ lật lại, con sóng, phân bố chu kỳ 4
giai đoạn) và chạy phép thử bất biến khi cắt trên dữ liệu thật (Tầng B, nay phủ cả sự kiện, con sóng và trạng thái).
KHÔNG đọc lợi nhuận, KHÔNG tính alpha — lợi nhuận của luật này chỉ được đọc ở Lát 4 theo `ĐO 34` (bất biến 7).
Không mạng, không ghi cache; chỉ ghi MỘT file JSON kết quả ở đường dẫn người gọi chọn (`--ghi`).

    ./.venv/Scripts/python.exe tools/mo_ta_cau_truc_gia.py mo-ta --cache <thư mục cache> [--ghi X.json]
    ./.venv/Scripts/python.exe tools/mo_ta_cau_truc_gia.py kiem-cat --cache <thư mục cache> [--so-diem 40]
    ./.venv/Scripts/python.exe tools/mo_ta_cau_truc_gia.py su-kien --cache <thư mục cache> [--ghi X.json]

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
    tsk, sk_log, tt2 = C.khoi_tao_su_kien(C.khoi_tao(ho, tham_so, san, he)), [], C.khoi_tao(ho, tham_so, san, he)
    for nen in C.chuan_bi_nen(df, san):
        tt2, moi = C.cap_nhat(tt2, nen)
        tsk, sk = C.cap_nhat_su_kien(tsk, nen, moi)
        sk_log.extend(sk)
    if tuple(sk_log) != day_du.su_kien:
        loi.append("su_kien_tang_dan != ca_bang")
    for t in diem_cat(len(df), so_diem, hat):
        cat = C.doc_cau_truc(df.iloc[:t + 1], he_so_gia=he, san=san, ho=ho, tham_so=tham_so)
        if list(cat.nhat_ky) != C.nhat_ky_tai(day_du.nhat_ky, t):
            loi.append(f"t={t}")
        if list(cat.su_kien) != C.su_kien_tai(day_du.su_kien, t):
            loi.append(f"su_kien t={t}")
        if list(cat.con_song) != [w for w in day_du.con_song if w.chi_so_biet <= t]:
            loi.append(f"con_song t={t}")
        if C.trang_thai_dow(cat) != C.trang_thai_dow(day_du, t):
            loi.append(f"trang_thai t={t}")
    return loi, len(day_du.nhat_ky), len(day_du.su_kien), len(day_du.con_song)


def lenh_kiem_cat(a) -> int:
    cache = Path(a.cache)
    truoc = bam_cache(cache)
    print(f"băm cache TRƯỚC: {truoc['sha256']} ({truoc['so_file']} file)")
    ma_ds = list(CUSTOM_WATCHLIST_SYMBOLS) + ["VNINDEX"]
    hong, tong_cat, tong_dong, tong_sk, tong_song = [], 0, 0, 0, 0
    o = [("atr", (2, 4))] if not a.o_luoi else luoi_o()
    for ho, ts in o:
        so_diem = a.so_diem if (ho, ts) == ("atr", (2, 4)) else a.so_diem_luoi
        ma_dung = ma_ds if (ho, ts) == ("atr", (2, 4)) else ma_ds[:a.so_ma_luoi]
        cat_o = dong_o = sk_o = song_o = 0
        for ma in ma_dung:
            df, he, san = cau_hinh(cache, ma)
            loi, so_dong, so_sk, so_song = kiem_cat_ma(df, he, san, ho, ts, so_diem, a.hat)
            cat_o += len(diem_cat(len(df), so_diem, a.hat)) + 1
            dong_o += so_dong
            sk_o += so_sk
            song_o += so_song
            if loi:
                hong.append((ho, ts, ma, loi[:5]))
        tong_cat += cat_o
        tong_dong += dong_o
        tong_sk += sk_o
        tong_song += song_o
        print(f"  {ho:7s}{str(ts):14s} {len(ma_dung)} mã · {cat_o} phép so · {dong_o} dòng pivot · {sk_o} sự kiện · {song_o} con sóng")
    sau = bam_cache(cache)
    print(f"băm cache SAU:   {sau['sha256']}  {'KHỚP' if sau['sha256'] == truoc['sha256'] else 'LỆCH'}")
    print(f"tổng {tong_cat} phép so, {tong_dong} dòng pivot, {tong_sk} sự kiện, {tong_song} con sóng, {len(hong)} ca LỆCH")
    for h in hong[:20]:
        print("  LỆCH", h)
    return 0 if not hong and sau["sha256"] == truoc["sha256"] else 1


# ── Lát 2: sự kiện, trạng thái, con sóng, chu kỳ (BƯỚC 249) ─────────────────────────────
CUA_SO_LAT_LAI = 3          # "lật lại trong 3 phiên" (đặc tả 9.2, TR §7 mục 3–4)
BUOC_MAU_CHU_KY = 21        # lấy mẫu chu kỳ mỗi 21 phiên, từ phiên 120 (đủ cho `pha_wyckoff`)
NAM_CA_THAT = ("2022-03-01", "2022-08-31")


def doc_lap_su_kien(df, r, he, san) -> dict:
    """Kiểm ĐỘC LẬP mọi sự kiện của `r` bằng bảng giá thô (không gọi lại `cap_nhat_su_kien`), nghi ngờ máy đo như gác:
    (a) đóng cửa ở nến sự kiện vượt pivot bị phá quá nửa bước (nửa bước tính lại thẳng từ `truot_gia.buoc_gia`);
    (b) không đóng cửa nào từ lúc BIẾT pivot tới trước nến sự kiện đã vượt nó (phá ở nến đầu tiên có thể);
    (c) `pivot_bi_pha.chi_so_biet < chi_so_xay_ra` và ngày khớp bảng; (d) KHOI_DAU chỉ đầu tiên, BOS/CHOCH theo chiều
    sự kiện trước cùng cấp; (e) ĐẦY ĐỦ: mọi pivot hiệu lực có một nến đóng cửa vượt nó kể từ nến sau khi biết thì có
    một sự kiện cùng cấp, cùng chiều Ở ĐÚNG nến đầu tiên đó."""
    dong = df["close"].to_numpy(dtype=float)
    ngay = pd.to_datetime(df["time"]).dt.strftime("%Y-%m-%d").tolist()
    loi = Counter()
    kiem = Counter()
    for e in r.su_kien:
        p = e.pivot_bi_pha
        nua = buoc_gia(p.gia * he, san) / 2.0 / he
        sgn = 1.0 if e.chieu == C.TANG else -1.0
        kiem["su_kien"] += 1
        loi["a_khong_vuot_nua_buoc"] += not sgn * (dong[e.chi_so_xay_ra] - p.gia) > nua
        loi["b_da_bi_vuot_truoc"] += bool((sgn * (dong[p.chi_so_biet:e.chi_so_xay_ra] - p.gia) > nua).any())
        loi["c_biet_khong_truoc_nen_pha"] += not p.chi_so_biet < e.chi_so_xay_ra
        loi["c_ngay_lech"] += ngay[e.chi_so_xay_ra] != e.ngay_xay_ra or e.ngay_biet != e.ngay_xay_ra
        loi["c_chieu_loai_pivot_sai"] += p.loai != (C.DINH if e.chieu == C.TANG else C.DAY)
    for cap in C.CAPS:
        ds = [e for e in r.su_kien if e.cap == cap]
        for i, e in enumerate(ds):
            if i == 0:
                loi["d_khoi_dau_sai"] += e.loai != C.KHOI_DAU
            else:
                mong = C.BOS if e.chieu == ds[i - 1].chieu else C.CHOCH
                loi["d_khoi_dau_sai"] += e.loai != mong
        co_su_kien = {(e.chi_so_xay_ra, e.chieu) for e in ds}
        for p in hieu_luc(r.nhat_ky, cap):
            nua = buoc_gia(p.gia * he, san) / 2.0 / he
            sgn = 1.0 if p.loai == C.DINH else -1.0
            sau = sgn * (dong[p.chi_so_biet + 1:] - p.gia) > nua
            if sau.any():
                f = p.chi_so_biet + 1 + int(np.argmax(sau))
                kiem["pivot_co_nen_vuot"] += 1
                loi["e_thieu_su_kien"] += (f, C.TANG if p.loai == C.DINH else C.GIAM) not in co_su_kien
    return {"da_kiem": dict(kiem), "vi_pham": {k: int(v) for k, v in loi.items() if v}, "tong_vi_pham": int(sum(loi.values()))}


def lat_lai(df, r) -> dict:
    """Tỷ lệ sự kiện "lật lại trong 3 phiên", MỖI cấp × loại. Hai định nghĩa (mô tả, không phải lợi nhuận):
    `su_kien_nguoc` = sự kiện kế tiếp CÙNG cấp là chiều ngược và cách ≤ 3 phiên; `dong_cua_quay_lai` = trong 3 phiên sau
    nến sự kiện có một nến đóng cửa ở phía bên kia mốc bị phá (đỉnh bị phá: đóng ≤ giá đỉnh; đáy: đóng ≥ giá đáy).
    Loại các sự kiện cách nến cuối < 3 phiên (cắt phải)."""
    dong = df["close"].to_numpy(dtype=float)
    n = len(dong)
    d = {}
    for cap in C.CAPS:
        ds = [e for e in r.su_kien if e.cap == cap]
        for i, e in enumerate(ds):
            if e.chi_so_xay_ra + CUA_SO_LAT_LAI > n - 1:
                continue
            for k in (e.loai, "tat_ca"):
                o = d.setdefault(f"{cap}/{k}", Counter())
                o["n"] += 1
                if i + 1 < len(ds) and ds[i + 1].chieu != e.chieu and \
                        ds[i + 1].chi_so_xay_ra - e.chi_so_xay_ra <= CUA_SO_LAT_LAI:
                    o["su_kien_nguoc"] += 1
                sau = dong[e.chi_so_xay_ra + 1:e.chi_so_xay_ra + 1 + CUA_SO_LAT_LAI]
                p = e.pivot_bi_pha
                if (e.chieu == C.TANG and (sau <= p.gia).any()) or (e.chieu == C.GIAM and (sau >= p.gia).any()):
                    o["dong_cua_quay_lai"] += 1
    return {k: dict(v) for k, v in d.items()}


def mo_ta_su_kien(cache: Path, rổ: list[str], toi_da_ma: int | None = None) -> dict:
    """Số MÔ TẢ của sự kiện / con sóng / thủy triều ở ô mặc định (KHÔNG đọc lợi nhuận)."""
    ds_ma = rổ if toi_da_ma is None else rổ[:toi_da_ma]
    so_nam = 0.0
    dem = {c: Counter() for c in C.CAPS}
    theo_nam = {c: Counter() for c in C.CAPS}
    lat = {}
    kiem_dl, loi_dl = Counter(), Counter()
    song_tong = Counter()
    song_o = Counter()
    ty_le_song = []
    nam_song = Counter()
    gio_thuy_trieu = Counter()
    tong_phien_thuy_trieu = 0
    tre_biet_trang_thai = []
    for ma in ds_ma:
        df, he, san = cau_hinh(cache, ma)
        r = C.doc_cau_truc(df, he_so_gia=he, san=san)
        so_nam += len(df) / PHIEN_MOI_NAM
        for e in r.su_kien:
            dem[e.cap][e.loai] += 1
            dem[e.cap][e.loai + "/" + e.chieu] += 1
            theo_nam[e.cap][e.ngay_biet[:4]] += 1
        for k, v in lat_lai(df, r).items():
            lat.setdefault(k, Counter()).update(v)
        dl = doc_lap_su_kien(df, r, he, san)
        kiem_dl.update(dl["da_kiem"])
        loi_dl.update(dl["vi_pham"])
        for w in r.con_song:
            song_tong["tong"] += 1
            song_tong["du_dieu_kien_mac_dinh"] += w.du_dieu_kien
            song_tong["khong_co_nhip_chinh"] += w.ty_le is None
            nam_song[w.ngay_biet[:4]] += 1
            if w.ty_le is not None:
                ty_le_song.append(w.ty_le)
            for b in C.LUOI_SONG["bien_do"]:
                for p in C.LUOI_SONG["phien"]:
                    for k in C.LUOI_SONG["kieu"]:
                        song_o[f"{b[0]}={b[1]:.4g}|{p}|{k}"] += C.du_dieu_kien_o(w, b, p, k)
        # thời gian ở mỗi thủy triều: theo từng nến, tính từ nhật ký đã biết tại nến ấy
        tt_theo_nen = thuy_trieu_theo_nen(r)
        gio_thuy_trieu.update(tt_theo_nen)
        tong_phien_thuy_trieu += len(df)
        tre_biet_trang_thai.append(trang_thai_cuoi_tre(r))
    out = {
        "so_ma": len(ds_ma), "so_nam_ma": round(so_nam, 2),
        "su_kien_moi_ma_moi_nam": {c: {k: round(v / so_nam, 3) for k, v in sorted(dem[c].items()) if "/" not in k}
                                    for c in C.CAPS},
        "su_kien_dem": {c: dict(sorted(dem[c].items())) for c in C.CAPS},
        "su_kien_theo_nam_biet": {c: dict(sorted(theo_nam[c].items())) for c in C.CAPS},
        "lat_lai_trong_3_phien": {k: {**dict(v), "ty_le_su_kien_nguoc": round(v["su_kien_nguoc"] / v["n"], 4),
                                      "ty_le_dong_cua_quay_lai": round(v["dong_cua_quay_lai"] / v["n"], 4)}
                                   for k, v in sorted(lat.items())},
        "doc_lap": {"da_kiem": dict(kiem_dl), "vi_pham": dict(loi_dl), "tong_vi_pham": int(sum(loi_dl.values()))},
        "con_song": {"tong": song_tong["tong"], "moi_ma_moi_nam": round(song_tong["tong"] / so_nam, 3),
                     "du_dieu_kien_mac_dinh": song_tong["du_dieu_kien_mac_dinh"],
                     "khong_co_nhip_chinh": song_tong["khong_co_nhip_chinh"],
                     "ty_le_trung_vi": phan_vi(ty_le_song, 50), "ty_le_p90": phan_vi(ty_le_song, 90),
                     "theo_nam_biet": dict(sorted(nam_song.items())),
                     "luoi_18_o_so_song_du_dieu_kien": dict(sorted(song_o.items()))},
        "thuy_trieu_ty_le_nen": {k: round(v / tong_phien_thuy_trieu, 4) for k, v in sorted(gio_thuy_trieu.items())},
    }
    return out


def thuy_trieu_theo_nen(r) -> Counter:
    """Số nến ở mỗi giá trị thủy triều, tính nhân quả: nến `t` dùng trạng thái đã biết tại `t` (đường lui = phát lại từng
    nhóm `chi_so_biet`, không gọi `trang_thai_dow` n lần)."""
    dau = {}
    for p in r.nhat_ky:
        if p.cap == C.CAP_SWING:
            dau.setdefault(p.chi_so_biet, []).append(p)
    sw, hien, bat_dau, kq = [], C.CHUA_DU, 0, Counter()
    for b in sorted(dau):
        for p in dau[b]:
            sw = C._ap_dong(sw, p)
        moi = C._thuy_trieu_tu_swing(sw)[0]
        if moi != hien:
            kq[hien] += b - bat_dau
            hien, bat_dau = moi, b
    kq[hien] += r.so_nen - bat_dau
    return kq


def trang_thai_cuoi_tre(r) -> int | None:
    s = C.trang_thai_dow(r)
    return None if s.chi_so_biet_thuy_trieu is None else s.chi_so_t - s.chi_so_biet_thuy_trieu


def chu_ky_phan_bo(cache: Path, rổ: list[str], toi_da_ma: int | None = None) -> dict:
    """Phân bố chu kỳ 4 giai đoạn: mỗi mã lấy mẫu mỗi `BUOC_MAU_CHU_KY` phiên từ phiên 120 + nến cuối; ở mỗi mẫu
    `pha_wyckoff.doc_pha` trên `df[:t+1]` và `trang_thai_dow` ĐÃ BIẾT tại `t` (đọc từ nhật ký đủ, hợp lệ nhờ bất biến khi
    cắt — Tầng B kiểm riêng). Mô tả, không phải lợi nhuận."""
    import pha_wyckoff as W
    ds_ma = rổ if toi_da_ma is None else rổ[:toi_da_ma]
    giai_doan, chi_tiet, tide, pha_dem, cheo = Counter(), Counter(), Counter(), Counter(), Counter()
    mau_thuan = Counter()
    so_mau = 0
    for ma in ds_ma:
        df, he, san = cau_hinh(cache, ma)
        r = C.doc_cau_truc(df, he_so_gia=he, san=san)
        n = len(df)
        for t in sorted(set(range(120, n, BUOC_MAU_CHU_KY)) | {n - 1}):
            pha = W.doc_pha(df.iloc[:t + 1], he)
            s = C.trang_thai_dow(r, t)
            c = C.ghep_chu_ky(s, pha)
            so_mau += 1
            giai_doan[c.giai_doan] += 1
            chi_tiet[f"{c.giai_doan}|{c.nguon}"] += 1
            tide[s.thuy_trieu] += 1
            pha_dem[f"{pha.pha}/{pha.cau_truc}"] += 1
            cheo[f"{s.thuy_trieu}|{c.giai_doan}"] += 1
            mau_thuan[c.mau_thuan] += 1
    return {"so_mau": so_mau, "so_ma": len(ds_ma), "giai_doan": dict(giai_doan.most_common()),
            "giai_doan_nguon": dict(chi_tiet.most_common()),
            "ty_le_giai_doan": {k: round(v / so_mau, 4) for k, v in giai_doan.most_common()},
            "thuy_trieu": dict(tide.most_common()), "pha_wyckoff": dict(pha_dem.most_common()),
            "thuy_trieu_x_giai_doan": dict(sorted(cheo.items())), "mau_thuan": {str(k): v for k, v in mau_thuan.items()}}


def ca_that_vnindex(cache: Path) -> dict:
    """Ca thật đã biết: sự kiện của VN-INDEX 03–08/2022 kèm giá thô để đối chiếu bằng mắt với bảng giá (không gõ ngày)."""
    df, he, san = cau_hinh(cache, "VNINDEX")
    r = C.doc_cau_truc(df, he_so_gia=he, san=san)
    gio = pd.to_datetime(df["time"])
    tu, den = NAM_CA_THAT
    ds = []
    for e in r.su_kien:
        if tu <= e.ngay_xay_ra <= den:
            p = e.pivot_bi_pha
            ds.append({"cap": e.cap, "loai": e.loai, "chieu": e.chieu, "ngay": e.ngay_xay_ra, "dong_cua": float(df["close"].iloc[e.chi_so_xay_ra]),
                       "pivot": {"loai": p.loai, "gia": p.gia, "xay_ra": p.ngay_xay_ra, "biet": p.ngay_biet, "nhan": p.nhan},
                       "gia_dong_cua_pivot_theo_bang": float(df["close"].iloc[p.chi_so_xay_ra])})
    cuoi = df[(gio >= tu) & (gio <= den)]
    t_cuoi = int(cuoi.index[-1])
    s = C.trang_thai_dow(r, t_cuoi)
    return {"su_kien": ds,
            "trang_thai_cuoi_vung": {"ngay": str(df["time"].iloc[t_cuoi]), "thuy_trieu": s.thuy_trieu,
                                     "ngay_biet": s.ngay_biet_thuy_trieu, "moc_phu_dinh": None if s.moc_phu_dinh is None else
                                     {"gia": s.moc_phu_dinh.gia, "xay_ra": s.moc_phu_dinh.ngay_xay_ra, "biet": s.moc_phu_dinh.ngay_biet},
                                     "canh_bao": s.canh_bao_dao_chieu, "huong_swing": s.thien_huong_swing}}


def lenh_su_kien(a) -> int:
    cache = Path(a.cache)
    bam_truoc = bam_cache(cache)
    print(f"cache {bam_truoc['sha256'][:16]}… · {bam_truoc['so_file']} file")
    kq = {"cache": bam_truoc}
    kq["mo_ta"] = mo_ta_su_kien(cache, CUSTOM_WATCHLIST_SYMBOLS, a.toi_da_ma)
    print(json.dumps(kq["mo_ta"], ensure_ascii=False, indent=1))
    kq["chu_ky"] = chu_ky_phan_bo(cache, CUSTOM_WATCHLIST_SYMBOLS, a.toi_da_ma)
    print(json.dumps(kq["chu_ky"], ensure_ascii=False, indent=1))
    kq["ca_that_vnindex"] = ca_that_vnindex(cache)
    print(json.dumps(kq["ca_that_vnindex"], ensure_ascii=False, indent=1))
    bam_sau = bam_cache(cache)
    kq["bam_sau"] = bam_sau
    print("băm cache sau:", "KHỚP" if bam_sau["sha256"] == bam_truoc["sha256"] else "LỆCH", bam_sau["sha256"][:16])
    if a.ghi:
        Path(a.ghi).write_text(json.dumps(kq, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0 if bam_sau["sha256"] == bam_truoc["sha256"] and kq["mo_ta"]["doc_lap"]["tong_vi_pham"] == 0 else 1


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
    s = sub.add_parser("su-kien", help="Lát 2: số mô tả sự kiện / con sóng / chu kỳ + ca thật VN-INDEX")
    s.add_argument("--cache", required=True)
    s.add_argument("--ghi", help="đường dẫn JSON kết quả")
    s.add_argument("--toi-da-ma", type=int, default=None, help="chỉ để chạy thử nhanh; bỏ trống = cả 71 mã")
    a = ap.parse_args(argv)
    if a.lenh == "mo-ta":
        return lenh_mo_ta(a)
    return lenh_su_kien(a) if a.lenh == "su-kien" else lenh_kiem_cat(a)


if __name__ == "__main__":
    sys.exit(main())
