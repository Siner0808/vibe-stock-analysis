"""ĐO 24 — lệch `close` giữa hai cache giá: có DẠNG điều chỉnh không?

Tiêu chí ký trước: `docs/TIEU-CHI-DOC-TRUOC.md`, mục *ĐO 24* (commit 427f126, sửa
dung sai đoạn ở 421975e, cả hai TRƯỚC file này). Mọi ngưỡng ở đây là chép từ đó.

CHỈ ĐỌC: không mạng, không `import vnstock`, không ghi cache, không tính điểm
hay IC, không SELECT cột điểm của sổ. Giá cắt `< MOC_DA_NHIN` lúc nạp.

    ./.venv/Scripts/python.exe tools/do24_lech_gia.py chay \
        --cache <A> --cache-khac <B> --cache-goc <bản sao A> \
        --db <paper_trades.db> --db <paper_trades_seeded_insample.db> [--ghi docs/do24-lech-gia.json]
    ./.venv/Scripts/python.exe tools/do24_lech_gia.py doi-chung --cache-khac <B>
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(GOC / "tools"))

import experiment_tran_dac_trung as E  # noqa: E402
import sang_ung_vien as SV  # noqa: E402

MOC_DA_NHIN = SV.MOC_DA_NHIN
#: Giá làm tròn 2 chữ số: hai lượt kéo cùng một giá thật vẫn có thể khác ≤ 0,01.
LAM_TRON = 0.0101
#: Sai số làm tròn của `ℓ` ở mỗi nến ≤ 0,0101/c; hiệu hai nến liền nhau ≤ 0,0202/c.
DUNG_SAI_BUOC = 0.0202
#: Đoạn: |ℓ − ln k̂| ≤ 0,0202/c (sai số của ℓ cộng sai số của trung vị k̂).
DUNG_SAI_DOAN = 0.0202
TOI_DA_DIEM_DOI = 3
TOI_THIEU_DOAN = 5
NGUONG_K1 = 0.90
NGUONG_K2 = 0.50
NGUONG_DEP_QUA = 0.99
NGUONG_NHOM = 5.0
NHIP = 21
NGUONG_E = (0.5, 2.0)
NGUONG_GHEP = 0.01
DUNG_SAI_M0 = 1e-6
M0_NEN_CHUNG, M0_NEN_KHAC, M0_MA_LECH = 80018, 27219, 45
CHOT_BAN_NEO = "2026-09-11"
HAT_DOI_CHUNG = 24
HE_SO_TIEM = 0.97
NHIEU_DOI_CHUNG = 0.005
NEN_LAC_HE_SO = 1.05
_RE_2_SO = re.compile(r"^\d+(\.\d{1,2})?$")


# ── đọc giá ─────────────────────────────────────────────────────────────────
def doc_close(f: Path) -> pd.Series | None:
    """`close` theo ngày (10 ký tự đầu của `time`), đã cắt < mốc; None nếu hỏng khuôn."""
    df = pd.read_csv(f, usecols=lambda c: c in ("time", "close"))
    if "time" not in df.columns or "close" not in df.columns:
        return None
    ngay = df["time"].astype(str).str.slice(0, 10)
    s = (pd.Series(df["close"].to_numpy(float), index=ngay.to_numpy())
         .loc[lambda x: ~x.index.duplicated()].sort_index())
    s = s[s.index < MOC_DA_NHIN]
    return s if len(s) else None


def dinh_dang_time(f: Path) -> str:
    """`ngay` hay `ngay-gio`, theo ô `time` đầu tiên."""
    d = pd.read_csv(f, usecols=["time"], nrows=1)
    return "ngay-gio" if len(str(d["time"].iloc[0])) > 10 else "ngay"


def nap_p2(a: Path, b: Path) -> dict:
    """{mã: (close_A, close_B)} trên mọi mã có file ở CẢ HAI thư mục, nến chung."""
    ra = {}
    for f in sorted(a.glob("*.csv")):
        g = b / f.name
        if not g.exists():
            continue
        sa, sb = doc_close(f), doc_close(g)
        if sa is None or sb is None:
            continue
        j = sa.index.intersection(sb.index)
        if len(j):
            ra[f.stem] = (sa[j], sb[j])
    return ra


def nap_p1(a: Path, b: Path) -> dict:
    """{mã: (close_A, close_B)} trên rổ `E.nap_gia`, nến chung, cắt < mốc."""
    ga, gb = SV.nap_gia(a), SV.nap_gia(b)
    ra = {}
    for ma in sorted(set(ga) & set(gb)):
        sa, sb = ga[ma]["close"].astype(float), gb[ma]["close"].astype(float)
        j = sa.index.intersection(sb.index)
        ra[ma] = (sa[j], sb[j])
    return ra


# ── M0 ──────────────────────────────────────────────────────────────────────
def m0a(p1: dict) -> dict:
    chung = lech = 0
    ma_lech = 0
    for sa, sb in p1.values():
        k = int(((sa - sb).abs() > DUNG_SAI_M0).sum())
        chung, lech, ma_lech = chung + len(sa), lech + k, ma_lech + (k > 0)
    ok = (chung, lech, ma_lech) == (M0_NEN_CHUNG, M0_NEN_KHAC, M0_MA_LECH)
    return {"n_nen_chung": chung, "n_nen_khac": lech, "n_ma_co_nen_khac": ma_lech,
            "tai_lap_ODO23": ok}


def m0b(a: Path, b: Path) -> dict:
    """Tỷ lệ ô OHLC có ≤ 2 chữ số thập phân, ở từng thư mục (đọc chuỗi thô)."""
    ra = {}
    for ten, d in (("A", a), ("B", b)):
        tong = tot = 0
        for f in sorted(d.glob("*.csv")):
            df = pd.read_csv(f, dtype=str, usecols=lambda c: c in ("open", "high", "low", "close"))
            v = df.to_numpy().ravel()
            tong += len(v)
            tot += sum(1 for x in v if isinstance(x, str) and _RE_2_SO.match(x.strip()))
        ra[ten] = tot / tong if tong else 0.0
    ra["dat"] = ra["A"] >= 0.999 and ra["B"] >= 0.999
    return ra


def _bam(f: Path) -> str:
    return hashlib.sha256(f.read_bytes()).hexdigest()


def m0c(a: Path, goc: Path) -> dict:
    moc_t = datetime.datetime.strptime(CHOT_BAN_NEO, "%Y-%m-%d").timestamp()
    files = sorted(a.glob("*.csv"))
    sau = [f.name for f in files if f.stat().st_mtime > moc_t + 86400]
    khac, thieu = [], []
    for f in files:
        g = goc / f.name
        if not g.exists():
            thieu.append(f.name)
        elif _bam(f) != _bam(g):
            khac.append(f.name)
    return {"n_file_A": len(files), "mtime_sau_chot": len(sau),
            "khac_bam_so_voi_ban_sao": len(khac), "thieu_trong_ban_sao": len(thieu),
            "ten_file_khac": khac[:10]}


# ── M1–M2: phân loại ────────────────────────────────────────────────────────
def phan_loai(a: pd.Series, b: pd.Series) -> dict:
    """Phân loại một mã theo M2. `a`, `b` đã khớp chỉ số (nến chung)."""
    A, B = a.to_numpy(float), b.to_numpy(float)
    if len(A) == 0 or (A <= 0).any() or (B <= 0).any():
        raise ValueError("close <= 0 hoac rong")
    n = len(A)
    n_lech = int((np.abs(A - B) > LAM_TRON).sum())
    if n_lech == 0:
        return {"loai": "KHOP", "n": n, "n_lech_that": 0, "doan": []}
    ln = np.log(A / B)
    c4 = np.minimum.reduce([A[1:], B[1:], A[:-1], B[:-1]])
    doi = np.flatnonzero(np.abs(np.diff(ln)) > DUNG_SAI_BUOC / c4) + 1
    bien = [0, *doi.tolist(), n]
    doan = []
    for s, e in zip(bien[:-1], bien[1:]):
        khat = float(np.exp(np.median(ln[s:e])))
        tol = DUNG_SAI_DOAN / np.minimum(A[s:e], B[s:e])
        doan.append({"tu": s, "den": e, "dai": e - s, "khat": khat,
                     "mot_he_so": bool(np.all(np.abs(ln[s:e] - np.log(khat)) <= tol))})
    dang = (len(doi) <= TOI_DA_DIEM_DOI and all(d["dai"] >= TOI_THIEU_DOAN for d in doan)
            and all(d["mot_he_so"] for d in doan))
    return {"loai": "DANG DIEU CHINH" if dang else "KHONG DANG DIEU CHINH", "n": n,
            "n_lech_that": n_lech, "n_diem_doi": int(len(doi)), "doan": doan}


def ket_cuc_q1(p_adj: float, m0_dat: bool, m3_dat: bool) -> str:
    if not (m0_dat and m3_dat):
        return "K0"
    if p_adj >= NGUONG_K1:
        return "K1"
    if p_adj <= NGUONG_K2:
        return "K2"
    return "K3"


def m2(p1: dict) -> dict:
    pl = {ma: phan_loai(sa, sb) for ma, (sa, sb) in p1.items()}
    tong = sum(v["n_lech_that"] for v in pl.values())
    dang = sum(v["n_lech_that"] for v in pl.values() if v["loai"] == "DANG DIEU CHINH")
    dem = {k: sum(1 for v in pl.values() if v["loai"] == k)
           for k in ("KHOP", "DANG DIEU CHINH", "KHONG DANG DIEU CHINH")}
    return {"pl": pl, "n_lech_that": tong, "n_lech_trong_ma_dang": dang,
            "P_adj": dang / tong if tong else None, "so_ma": dem}


# ── M3: đối chứng ───────────────────────────────────────────────────────────
def doi_chung(sb: pd.Series, hat: int = HAT_DOI_CHUNG) -> dict:
    """Bốn ô đối chứng dựng từ `close` của B. Mỗi ô trả (loại thu được, đạt?)."""
    rng = np.random.default_rng(hat)
    B = sb.to_numpy(float)
    n = len(B)
    d = n // 2
    idx = sb.index
    ra = {}

    def lam(x):
        return pd.Series(np.round(x, 2), index=idx)

    ra["1_khong_tiem"] = phan_loai(lam(B), sb)
    tiem = B.copy()
    tiem[:d] = tiem[:d] * HE_SO_TIEM
    r2 = phan_loai(lam(tiem), sb)
    r2["diem_doi_dung_o_D"] = (r2.get("n_diem_doi") == 1 and len(r2["doan"]) == 2
                               and r2["doan"][1]["tu"] == d)
    ra["2_dieu_chinh_tiem"] = r2
    nhieu = B * (1 + rng.uniform(-NHIEU_DOI_CHUNG, NHIEU_DOI_CHUNG, n))
    ra["3_nhieu_hang_ngay"] = phan_loai(lam(nhieu), sb)
    lac = B.copy()
    lac[d] = lac[d] * NEN_LAC_HE_SO
    ra["4_nen_lac"] = phan_loai(lam(lac), sb)
    ky_vong = {"1_khong_tiem": "KHOP", "2_dieu_chinh_tiem": "DANG DIEU CHINH",
               "3_nhieu_hang_ngay": "KHONG DANG DIEU CHINH",
               "4_nen_lac": "KHONG DANG DIEU CHINH"}
    out = {}
    for k, v in ra.items():
        dat = v["loai"] == ky_vong[k]
        if k == "2_dieu_chinh_tiem":
            dat = dat and v["diem_doi_dung_o_D"]
        out[k] = {"loai": v["loai"], "ky_vong": ky_vong[k], "dat": bool(dat),
                  "n_lech_that": v["n_lech_that"], "n_diem_doi": v.get("n_diem_doi", 0)}
    out["dat_ca_bon"] = all(v["dat"] for v in out.values())
    return out


def chon_ma_doi_chung(p1: dict) -> str:
    """Mã có nhiều nến chung nhất (hoà thì tên theo thứ tự chữ) — chọn theo ĐỘ DÀI, không theo kết quả."""
    return sorted(p1, key=lambda m: (-len(p1[m][0]), m))[0]


# ── M4–M9 ───────────────────────────────────────────────────────────────────
def ty_le(lech: int, tong: int):
    return lech / tong if tong else None


def m4(p2: dict, a: Path) -> dict:
    nhom = {"dinh_dang_time": {}, "nhom_mtime": {}, "nam": {}}

    def cong(loai, khoa, tong, lech):
        t = nhom[loai].setdefault(khoa, [0, 0])
        t[0] += tong
        t[1] += lech

    for ma, (sa, sb) in p2.items():
        f = a / f"{ma}.csv"
        lech = (sa - sb).abs() > LAM_TRON
        dd = dinh_dang_time(f)
        md = datetime.date.fromtimestamp(f.stat().st_mtime)
        mt = "06-08/08" if (md.month == 8) else md.isoformat()
        cong("dinh_dang_time", dd, len(sa), int(lech.sum()))
        cong("nhom_mtime", mt, len(sa), int(lech.sum()))
        for nam, g in lech.groupby(sa.index.str.slice(0, 4)):
            cong("nam", nam, len(g), int(g.sum()))
    out = {k: {n: {"nen": t[0], "lech_that": t[1], "ty_le": ty_le(t[1], t[0])}
               for n, t in sorted(v.items())} for k, v in nhom.items()}
    for k in ("dinh_dang_time", "nhom_mtime"):
        r = [v["ty_le"] for v in out[k].values() if v["ty_le"] is not None]
        out[k]["_gap_5_lan"] = bool(len(r) >= 2 and min(r) > 0 and max(r) / min(r) >= NGUONG_NHOM) \
            or bool(len(r) >= 2 and min(r) == 0 and max(r) > 0)
    return out


def m5(pl: dict) -> dict:
    ks = [d["khat"] for v in pl.values() for d in v["doan"]]
    if not ks:
        return {"n_doan": 0}
    ln = np.abs(np.log(ks))
    return {"n_doan": len(ks), "trung_vi_abs_ln_khat": float(np.median(ln)),
            "max_abs_ln_khat": float(ln.max()), "khat_lon_hon_1": int(sum(k > 1 + 1e-9 for k in ks)),
            "khat_nho_hon_1": int(sum(k < 1 - 1e-9 for k in ks)),
            "doan_moi_ma_trung_vi": float(np.median([len(v["doan"]) for v in pl.values() if v["doan"]]))}


def m6(p1: dict) -> dict:
    es, ma_cham = [], set()
    for ma, (sa, sb) in p1.items():
        ln = np.log(sa.to_numpy(float) / sb.to_numpy(float))
        if len(ln) <= NHIP + 1:
            continue
        e = np.abs(ln[1:len(ln) - NHIP] - ln[NHIP + 1:]) * 100
        es.append(e)
        if (e > NGUONG_E[0]).any():
            ma_cham.add(ma)
    e = np.concatenate(es) if es else np.array([])
    return {"n_cua_so": int(len(e)),
            **{f"ty_le_e_gt_{x}": float((e > x).mean()) for x in NGUONG_E},
            "e_max": float(e.max()) if len(e) else None, "n_ma_cham_0_5": len(ma_cham),
            "ghep_khong_chap_nhan": bool(len(e) and (e > NGUONG_E[0]).mean() >= NGUONG_GHEP)}


def m7(p1: dict) -> dict:
    ka = {m: pd.DataFrame({"close": sa}) for m, (sa, _) in p1.items()}
    kb = {m: pd.DataFrame({"close": sb}) for m, (_, sb) in p1.items()}
    la, lb = E.nhan_vuot_ro(ka, NHIP), E.nhan_vuot_ro(kb, NHIP)
    ok = la.notna() & lb.notna()
    x, y = la.where(ok).stack(), lb.where(ok).stack()
    if len(x) < 2:
        return {"n_o": int(len(x))}
    return {"n_o": int(len(x)), "spearman_gop": float(x.corr(y, method="spearman")),
            "ty_le_chenh_gt_0_5": float(((x - y).abs() > 0.5).mean()),
            "chenh_max": float((x - y).abs().max())}


def m9(p1: dict, pl: dict, moc_theo_ma: dict) -> dict:
    lech_nen = []
    ty_ma = {}
    for ma, (sa, sb) in p1.items():
        d = (sa - sb).abs()
        m = d > LAM_TRON
        ty_ma[ma] = float(m.mean())
        lech_nen.append((sa / sb - 1).abs()[m] * 100)
    ln = pd.concat(lech_nen) if lech_nen else pd.Series(dtype=float)
    ra = {"co_lech_pct": {"trung_vi": float(ln.median()) if len(ln) else None,
                          "p90": float(ln.quantile(0.9)) if len(ln) else None,
                          "max": float(ln.max()) if len(ln) else None},
          "ty_le_theo_ma": {"trung_vi": float(np.median(list(ty_ma.values()))),
                            "p90": float(np.quantile(list(ty_ma.values()), 0.9)),
                            "n_ma_tren_50": int(sum(v > 0.5 for v in ty_ma.values()))}}
    oos = {}
    for ma, (sa, sb) in p1.items():
        moc = moc_theo_ma.get(ma)
        if moc is None:
            continue
        mask = sa.index.to_numpy() < str(moc)[:10]
        if not mask.any():
            continue
        d = (sa - sb).abs()
        oos[ma] = {"n_oos": int(mask.sum()), "trung_vi_toan": float(d.median()),
                   "trung_vi_oos": float(d[mask].median()),
                   "lech_that_oos": int((d[mask] > LAM_TRON).sum()),
                   "lech_that_ngoai_oos": int((d[~mask] > LAM_TRON).sum()),
                   "n_ngoai_oos": int((~mask).sum())}
    tong_oos = sum(v["n_oos"] for v in oos.values())
    lech_oos = sum(v["lech_that_oos"] for v in oos.values())
    ra["dung_lai_DO5b"] = {
        "n_ma_co_oos": len(oos),
        "n_ma_trung_vi_toan_bang_0": sum(v["trung_vi_toan"] <= 5e-7 for v in oos.values()),
        "n_ma_trung_vi_oos_bang_0": sum(v["trung_vi_oos"] <= 5e-7 for v in oos.values()),
        "nen_oos": tong_oos, "lech_that_oos": lech_oos,
        "ty_le_lech_that_oos": ty_le(lech_oos, tong_oos),
        "ty_le_lech_that_ngoai_oos": ty_le(sum(v["lech_that_ngoai_oos"] for v in oos.values()),
                                           sum(v["n_ngoai_oos"] for v in oos.values()))}
    return ra


def m8(db: Path) -> dict:
    """Chỉ COUNT — không SELECT cột điểm."""
    con = sqlite3.connect(f"file:{Path(db).as_posix()}?mode=ro", uri=True)
    try:
        q = ("select count(*), count(distinct symbol||'|'||substr(signal_date,1,10)) "
             "from decisions where substr(signal_date,1,10) {} ?")
        tr = con.execute(q.format("<"), (MOC_DA_NHIN,)).fetchone()
        sau = con.execute(q.format(">="), (MOC_DA_NHIN,)).fetchone()
        thang = con.execute("select substr(signal_date,1,7), count(*) from decisions "
                            "group by 1 order by 1").fetchall()
    finally:
        con.close()
    return {"truoc_moc": {"dong": tr[0], "mot_lan_ma_phien": tr[1]},
            "tu_moc": {"dong": sau[0], "mot_lan_ma_phien": sau[1]},
            "tong_dong": tr[0] + sau[0], "theo_thang": dict(thang)}


# ── chạy ────────────────────────────────────────────────────────────────────
def _in(ten, v):
    print(f"\n[{ten}]")
    print(json.dumps(v, ensure_ascii=False, indent=1, default=str))


def _lenh_chay(a) -> int:
    ca, cb = Path(a.cache), Path(a.cache_khac)
    p1 = nap_p1(ca, cb)
    r = {"M0a": m0a(p1), "M0b": m0b(ca, cb)}
    _in("M0a", r["M0a"])
    _in("M0b", r["M0b"])
    if a.cache_goc:
        r["M0c"] = m0c(ca, Path(a.cache_goc))
        _in("M0c", r["M0c"])
    m0_dat = r["M0a"]["tai_lap_ODO23"] and r["M0b"]["dat"]
    ma_dc = chon_ma_doi_chung(p1)
    dc = doi_chung(p1[ma_dc][1])
    r["M3"] = {"ma": ma_dc, **dc}
    _in("M3", r["M3"])
    q = m2(p1)
    pl = q.pop("pl")
    q["ket_cuc"] = ket_cuc_q1(q["P_adj"] or 0.0, m0_dat, dc["dat_ca_bon"])
    r["M2"] = q
    _in("M2", q)
    if q["P_adj"] is not None and q["P_adj"] >= NGUONG_DEP_QUA and not dc["dat_ca_bon"]:
        print("CHAN: P_adj >= 0,99 ma M3 chua qua ca bon o - khong viet K1.")
    nlech = sum(v["n_lech_that"] for v in pl.values())
    nlt = sum(len(s) for s, _ in p1.values())
    nlam = sum(int((((sa - sb).abs() > DUNG_SAI_M0) & ((sa - sb).abs() <= LAM_TRON)).sum())
               for sa, sb in p1.values())
    r["M1"] = {"nen_chung": nlt, "lech_that": nlech, "chi_lam_tron": nlam}
    _in("M1", r["M1"])
    p2 = nap_p2(ca, cb)
    r["M4"] = {"so_ma_P2": len(p2), **m4(p2, ca)}
    _in("M4", r["M4"])
    r["M5"] = m5(pl)
    _in("M5", r["M5"])
    r["M6"] = m6(p1)
    _in("M6", r["M6"])
    r["M7"] = m7(p1)
    _in("M7", r["M7"])
    moc = json.loads(E.FILE_MOC.read_text(encoding="utf-8"))["moc_theo_ma"]
    r["M9"] = m9(p1, pl, moc)
    _in("M9", r["M9"])
    r["M8"] = {Path(d).name: m8(Path(d)) for d in a.db}
    _in("M8", r["M8"])
    if a.ghi:
        Path(a.ghi).write_text(json.dumps(r, ensure_ascii=False, indent=1, default=str) + "\n",
                               encoding="utf-8")
        print(f"\nda ghi {a.ghi}")
    return 0 if q["ket_cuc"] != "K0" else 1


def ly_do_khong(v: dict) -> list[str]:
    """Vì sao một mã có nến lệch thật mà KHÔNG đạt DẠNG ĐIỀU CHỈNH (chẩn đoán, không quyết định)."""
    if v["loai"] != "KHONG DANG DIEU CHINH":
        return []
    ra = []
    if v["n_diem_doi"] > TOI_DA_DIEM_DOI:
        ra.append("qua_nhieu_diem_doi")
    if any(d["dai"] < TOI_THIEU_DOAN for d in v["doan"]):
        ra.append("doan_ngan")
    if not all(d["mot_he_so"] for d in v["doan"]):
        ra.append("troi_trong_doan")
    return ra


def p_adj_do_nhay(pl: dict, tran_diem_doi: int, doan_toi_thieu: int) -> float | None:
    """P_adj nếu nới trần điểm đổi / độ dài đoạn tối thiểu — CHỈ để đọc độ nhạy của kết cục đã ký."""
    tong = dang = 0
    for v in pl.values():
        if v["n_lech_that"] == 0:
            continue
        tong += v["n_lech_that"]
        if (v["n_diem_doi"] <= tran_diem_doi and all(d["dai"] >= doan_toi_thieu for d in v["doan"])
                and all(d["mot_he_so"] for d in v["doan"])):
            dang += v["n_lech_that"]
    return dang / tong if tong else None


def p_doan_tot(p1: dict, pl: dict) -> float | None:
    """Tỷ lệ nến lệch thật nằm trong đoạn dài >= 5 nến đạt một-hệ-số, BẤT KỂ mã có nến lạc ở rìa.

    CHẨN ĐOÁN SAU kết cục đã ký (mã-hoá-tất-cả-hoặc-không của M2 để một nến lạc ở đuôi kéo
    cả mã 1.200 nến xuống KHÔNG) — không thay thế `P_adj`.
    """
    tong = tot = 0
    for ma, (sa, sb) in p1.items():
        v = pl[ma]
        if v["n_lech_that"] == 0:
            continue
        lech = ((sa - sb).abs() > LAM_TRON).to_numpy()
        tong += int(lech.sum())
        for d in v["doan"]:
            if d["dai"] >= TOI_THIEU_DOAN and d["mot_he_so"]:
                tot += int(lech[d["tu"]:d["den"]].sum())
    return tot / tong if tong else None


def theo_nen_co_gio(a_dir: Path, p1: dict, pl: dict) -> dict:
    """Cột `time` của A lẫn HAI định dạng TRONG MỘT file: so tỷ lệ lệch theo từng nến, và so
    ngày dòng đầu mang giờ (`J`) với các điểm đổi bậc đã phân đoạn."""
    co = {"nen_co_gio": [0, 0], "nen_khong_gio": [0, 0]}
    ma_co_gio = j_la_diem_doi = diem_doi_tong = diem_doi_tai_j = 0
    for ma, (sa, sb) in p1.items():
        raw = pd.read_csv(a_dir / f"{ma}.csv", usecols=["time"], dtype=str)["time"]
        ngay = raw.str.slice(0, 10)
        gio = pd.Series((raw.str.len() > 10).to_numpy(), index=ngay.to_numpy())
        gio = gio.loc[~gio.index.duplicated()].reindex(sa.index).fillna(False).to_numpy(bool)
        lech = ((sa - sb).abs() > LAM_TRON).to_numpy()
        for k, m in (("nen_co_gio", gio), ("nen_khong_gio", ~gio)):
            co[k][0] += int(m.sum())
            co[k][1] += int(lech[m].sum())
        bd = [d["tu"] for d in pl[ma]["doan"][1:]]
        diem_doi_tong += len(bd)
        if gio.any():
            ma_co_gio += 1
            j = int(np.argmax(gio))
            diem_doi_tai_j += sum(abs(x - j) <= 1 for x in bd)
            j_la_diem_doi += any(abs(x - j) <= 1 for x in bd)
    return {"nen_co_gio": {"nen": co["nen_co_gio"][0], "lech_that": co["nen_co_gio"][1],
                           "ty_le": ty_le(co["nen_co_gio"][1], co["nen_co_gio"][0])},
            "nen_khong_gio": {"nen": co["nen_khong_gio"][0], "lech_that": co["nen_khong_gio"][1],
                              "ty_le": ty_le(co["nen_khong_gio"][1], co["nen_khong_gio"][0])},
            "ma_co_nen_co_gio": ma_co_gio, "ma_co_gio_co_diem_doi_tai_J": j_la_diem_doi,
            "diem_doi_tong": diem_doi_tong, "diem_doi_tai_J": diem_doi_tai_j}


def _lenh_chan_doan(a) -> int:
    p1 = nap_p1(Path(a.cache), Path(a.cache_khac))
    pl = m2(p1)["pl"]
    print(f"P_adj ky = {m2(p1)['P_adj']:.4f} · ty le nen lech trong doan dai>=5 dat mot-he-so "
          f"(bat ke nen lac o rim) = {p_doan_tot(p1, pl):.4f}")
    print("theo nen co gio:", json.dumps(theo_nen_co_gio(Path(a.cache), p1, pl), ensure_ascii=False))
    print("độ nhạy của P_adj (kết cục đã ký dùng trần 3 điểm đổi, đoạn >= 5):")
    for tran, dai in ((3, 5), (6, 5), (10, 5), (10_000, 5), (3, 1), (10_000, 1)):
        print(f"  trần {tran:>6} · đoạn >= {dai}: {p_adj_do_nhay(pl, tran, dai):.4f}")
    dem = {}
    for v in pl.values():
        dem[tuple(ly_do_khong(v))] = dem.get(tuple(ly_do_khong(v)), 0) + 1
    print("mã KHÔNG DẠNG ĐIỀU CHỈNH theo lý do:", {"+".join(k) or "-": n for k, n in sorted(dem.items())})
    print("mã | loại | nến lệch thật | điểm đổi | số đoạn | khat các đoạn")
    for ma, v in sorted(pl.items(), key=lambda t: -t[1]["n_lech_that"]):
        if v["n_lech_that"]:
            print(f"{ma} | {v['loai'][:5]} | {v['n_lech_that']} | {v['n_diem_doi']} | {len(v['doan'])} | "
                  + " ".join(f"{d['khat']:.4f}x{d['dai']}" for d in v["doan"][:6]))
    return 0


def _lenh_doi_chung(a) -> int:
    ga = SV.nap_gia(Path(a.cache_khac))
    p = {m: (d["close"].astype(float),) * 2 for m, d in ga.items()}
    ma = chon_ma_doi_chung(p)
    _in("M3", {"ma": ma, **doi_chung(p[ma][1])})
    return 0


def main(argv=None) -> int:
    for lg in (sys.stdout, sys.stderr):
        try:
            lg.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sp = ap.add_subparsers(dest="lenh", required=True)
    c = sp.add_parser("chay")
    c.add_argument("--cache", required=True)
    c.add_argument("--cache-khac", required=True)
    c.add_argument("--cache-goc", default=None)
    c.add_argument("--db", action="append", default=[])
    c.add_argument("--ghi", default=None)
    d = sp.add_parser("doi-chung")
    d.add_argument("--cache-khac", required=True)
    g = sp.add_parser("chan-doan")
    g.add_argument("--cache", required=True)
    g.add_argument("--cache-khac", required=True)
    a = ap.parse_args(argv)
    return {"chay": _lenh_chay, "doi-chung": _lenh_doi_chung,
            "chan-doan": _lenh_chan_doan}[a.lenh](a)


if __name__ == "__main__":
    raise SystemExit(main())
