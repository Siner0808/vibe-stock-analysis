"""ĐO 35 — chỉnh thang giá của lệnh đang mở lúc xét: dụng cụ PHÁT LẠI 20 lệnh tiến-về-trước (BƯỚC 272).

Tiêu chí KÝ TRƯỚC ở `docs/TIEU-CHI-DOC-TRUOC.md`, mục `## ĐO 35` (commit ký `d81ddbe`, trước khi file
này tồn tại). Mã được đo: `chinh_thang_gia.py`. CHỈ ĐỌC: sổ thật kéo MỘT lần từ Sheets vào DB tạm ngoài
repo (bước `--keo-so` chạy ở repo chính vì cần `.streamlit/secrets.toml`; bước còn lại mở DB ấy bằng
`mode=ro`); nến tải MỖI MÃ MỘT LẦN rồi ghi ra đĩa; lịch VCI chỉ để đối chứng C6, KHÔNG nằm trong
đường chạy thật.

    <py chính> tools/do35_chinh_thang_gia.py tai-nen   --thu-muc <log>   # nến + băm
    <py chính> tools/do35_chinh_thang_gia.py doi-chung --thu-muc <log>   # CHỈ bản cơ sở (i)-(iii), chưa chạy bản sửa
    <py chính> tools/do35_chinh_thang_gia.py chay      --thu-muc <log> [--pytest]   # đối chứng + C1–C11 (MỘT lần)

Chỗ bản ký CHƯA nói (chọn khi viết, TRƯỚC mọi lượt đọc, khai ở `docs/STATE.md` BƯỚC 272):
- Cắt lỗ KHỞI ĐẦU của phát lại = `nhat_ky.stop_loss_ban_dau` nếu lệnh có dòng nhật ký (từ #118), không
  thì `stop_loss` của dòng sổ. Cột `trades.stop_loss` của lệnh đã đóng là cắt lỗ CUỐI (đã nâng trailing);
  dựng lệnh từ nó làm cây thủng cắt lỗ xảy ra sớm hơn thật.
- Phát lại chỉ xét ngày CÓ dòng quyết định của (mã, nến) — ngày đường quét thật từng xử lý.
- Biên của C11 nới `NOI_BIEN` theo cùng dạng nhân với `su_kien_quyen.kiem_lenh`:
  thấp_nhỏ_nhất × (1 − NOI_BIEN) ≤ giá ra ≤ cao_lớn_nhất × (1 + NOI_BIEN).
- C2 đi qua tham số `nhan_f` của `chinh_thang_mot_ma` (chia cho f × 0,98 / × 1,02).
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import math
import os
import pickle
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Optional

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))
sys.path.insert(0, str(GOC))

for _luong in (sys.stdout, sys.stderr):
    try:
        _luong.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import pandas as pd  # noqa: E402

import chinh_thang_gia as ct  # noqa: E402
import do26_nguong_su_kien_quyen as do26  # noqa: E402
import su_kien_quyen as skq  # noqa: E402
from data_quality import price_multiplier  # noqa: E402
from paper_trading import PaperTradingJournal, Status  # noqa: E402

#: Hết cửa sổ dữ liệu của lượt đo (bản ký: "12/11/2026").
NGAY_CUOI = "2026-11-12"
#: Ca dương đã biết (bản ký, đối chứng (i)) và cửa sổ XỬ LÝ (C1) đọc từ bản ký.
CA_DUONG = {122: {"ma": "HDB", "cua_so_den": "2026-10-09", "ra": ("STOP_LOSS", "2026-10-09", 21600.0)},
            128: {"ma": "TCB", "cua_so_den": "2026-10-29", "ra": ("STOP_LOSS", "2026-10-28", 22450.0)}}
#: Lịch VCI — cùng URL với BƯỚC 268/270; MÁY KHÁCH là `requests` + User-Agent tên dự án (không vnstock).
URL_LICH = "https://iq.vietcap.com.vn/api/iq-insight-service/v1/events"
TU_LICH, DEN_LICH = "20260801", "20261227"
GIO_VN = datetime.timezone(datetime.timedelta(hours=7))
CAC_O_SO_SANH = ("status", "entry_price", "stop_loss", "take_profit", "exit_date", "exit_price",
                 "exit_reason", "size_pct")


def bam(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True,
                                     default=str).encode("utf-8")).hexdigest()


def bam_tep(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def bam_khung(df: pd.DataFrame) -> str:
    return hashlib.sha256(df.to_csv(index=False).encode("utf-8")).hexdigest()


def mo_so(duong_dan: Path) -> sqlite3.Connection:
    c = sqlite3.connect(f"file:{duong_dan.as_posix()}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    return c


# ─────────────────────────── quần thể ───────────────────────────
def quan_the(c: sqlite3.Connection) -> list[dict]:
    """20 lệnh tiến-về-trước đã đóng, theo ĐÚNG hàm của sản phẩm (`paper_metrics.lenh_tien_ve_truoc`)."""
    from paper_metrics import lenh_tien_ve_truoc
    trades = [PaperTradingJournal._to_trade(r) for r in c.execute("SELECT * FROM trades ORDER BY id")]
    ids = [t.id for t in lenh_tien_ve_truoc(trades) if t.status == Status.CLOSED]
    ra = []
    for i in ids:
        d = dict(c.execute("SELECT * FROM trades WHERE id=?", (i,)).fetchone())
        nk = c.execute("SELECT * FROM nhat_ky WHERE trade_id=?", (i,)).fetchone()
        d["nhat_ky"] = dict(nk) if nk else None
        ra.append(d)
    return ra


def ngay10(x: Any) -> str:
    return str(x or "")[:10]


def luot_cuoi_xu_ly_nen(c: sqlite3.Connection, ma: str, ngay_nen: str) -> Optional[str]:
    """Ngày (giờ VN) của lượt quét CUỐI đã ghi dòng quyết định cho nến `ngay_nen` (BƯỚC 270 mục E)."""
    r = c.execute("SELECT MAX(at) FROM decisions WHERE symbol=? AND substr(signal_date,1,10)=?",
                  (ma, ngay_nen)).fetchone()
    if r is None or r[0] is None:
        return None
    return datetime.datetime.fromtimestamp(r[0], GIO_VN).date().isoformat()


def diem_theo_ngay(c: sqlite3.Connection, ma: str) -> dict[str, Optional[float]]:
    """{ngày nến: điểm} từ dòng quyết định có `seq` LỚN NHẤT của (mã, nến) (bản ký)."""
    ra: dict[str, Optional[float]] = {}
    for r in c.execute("SELECT substr(signal_date,1,10) AS d, score FROM decisions"
                       " WHERE symbol=? ORDER BY seq", (ma,)):
        ra[r["d"]] = r["score"]
    return ra


# ─────────────────────────── nến ───────────────────────────
def tai_khung(ma: str, tu: str) -> tuple[pd.DataFrame, str]:
    """Khung giá của lượt đo, qua ĐÚNG đường của lượt quét (`VNStockCollectorAgent.collect`).
    Trạng thái khác OK (kể cả SYNTHETIC — dữ liệu ngẫu nhiên) thì NÉM: không dùng giá bịa."""
    from data_collectors import VNStockCollectorAgent
    from san_giao_dich import san_cua
    ngay_cuoi = datetime.date.fromisoformat(NGAY_CUOI)
    start = (ngay_cuoi - datetime.timedelta(days=ct_ngay_lich_su())).isoformat()
    kq = VNStockCollectorAgent().collect(ma, start, NGAY_CUOI, exchange=san_cua(ma))
    if kq.get("status") != "OK" or kq.get("df") is None or len(kq["df"]) == 0:
        raise RuntimeError(f"{ma}: không tải được nến thật ({kq.get('status')}: {str(kq.get('note'))[:80]})")
    df = kq["df"].copy()
    df["ngay"] = pd.to_datetime(df["time"]).dt.strftime("%Y-%m-%d")
    df = df[df["ngay"] <= NGAY_CUOI].reset_index(drop=True)
    df = df[df["ngay"] >= tu].reset_index(drop=True)
    return df, str(kq.get("source") or "?")


def ct_ngay_lich_su() -> int:
    import run_daily
    return int(run_daily.NGAY_LICH_SU)


def tai_nen(thu_muc: Path) -> dict:
    """MỘT lần cho mỗi mã; ghi `nen_do35.pkl` và in băm từng khung."""
    c = mo_so(thu_muc / "so_that_272.db")
    qt = quan_the(c)
    theo_ma: dict[str, list[dict]] = {}
    for t in qt:
        theo_ma.setdefault(t["symbol"], []).append(t)
    kho: dict[str, dict] = {}
    for ma, ds in sorted(theo_ma.items()):
        som_nhat = min(ngay10(t["entry_date"]) for t in ds)
        tu = (datetime.date.fromisoformat(som_nhat) - datetime.timedelta(days=5)).isoformat()
        df, nguon = tai_khung(ma, tu)
        kho[ma] = {"df": df, "nguon": nguon, "tu": tu, "bam": bam_khung(df)}
        print(f"{ma:<4} {len(df):>4} nến {df['ngay'].iloc[0]} → {df['ngay'].iloc[-1]} nguồn {nguon} "
              f"băm {kho[ma]['bam'][:16]}", flush=True)
    with open(thu_muc / "nen_do35.pkl", "wb") as f:
        pickle.dump(kho, f)
    return kho


def doc_nen(thu_muc: Path) -> dict:
    with open(thu_muc / "nen_do35.pkl", "rb") as f:
        return pickle.load(f)


# ─────────────────────────── lịch VCI (CHỈ đối chứng C6) ───────────────────────────
def tai_lich(ma: str, tien_trinh=None) -> list[dict]:
    import requests
    from nguon_gia_cong_khai import USER_AGENT
    dong: list[dict] = []
    for trang in range(do26.TRAN_TRANG):
        last = None
        for lan in range(3):
            try:
                r = requests.get(URL_LICH, params={"ticker": ma, "fromDate": TU_LICH, "toDate": DEN_LICH,
                                                    "eventCode": "DIV,ISS", "page": trang,
                                                    "size": do26.CO_TRANG},
                                 headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
                                 timeout=30)
                r.raise_for_status()
                j = r.json()
                if not j.get("successful"):
                    raise RuntimeError(f"{j.get('msg')} {j.get('exception')}")
                lo = (j.get("data") or {}).get("content", [])
                last = None
                break
            except Exception as e:                      # noqa: BLE001
                last = e
                time.sleep(2.0)
        if last is not None:
            raise last
        dong.extend(lo)
        time.sleep(0.4)
        if len(lo) < do26.CO_TRANG:
            return dong
    raise RuntimeError(f"{ma}: quá {do26.TRAN_TRANG} trang sự kiện")


# ─────────────────────────── phát lại ───────────────────────────
def _bam_phan_con_lai(db, trade_id: int) -> dict[str, str]:
    """Băm từng bảng TRỪ dòng của lệnh đang phát lại — cho C8 (băm từng dòng trước/sau)."""
    ra = {}
    for bang, cot in (("trades", "id"), ("nhat_ky", "trade_id")):
        rows = [tuple(r) for r in db.execute(f"SELECT * FROM {bang} WHERE {cot}<>? ORDER BY {cot}",
                                              (trade_id,))]
        ra[bang] = bam(rows)
    for bang in ("decisions", "ke_hoach"):
        rows = [tuple(r) for r in db.execute(f"SELECT * FROM {bang}")]
        ra[bang] = bam(rows)
    return ra


def phat_lai(so: Path, t: dict, kho: dict, diem: dict, *, sua: bool, nhan_f: float = 1.0,
             den: str = NGAY_CUOI, dong_cuoi: bool = False) -> dict:
    """Phát lại MỘT lệnh bằng CHÍNH `fill_closing` / `evaluate_open` của repo trên sổ `:memory:`
    (bản sao TOÀN BỘ sổ thật, lệnh được đặt lại `OPEN`), từng nến từ ngày vào + 1.

    Mỗi nến, giống `paper_runner.buoc_phien`: [bộ chỉnh nếu `sua`] → `fill_closing` → `evaluate_open`.
    """
    ma, ngay_vao = t["symbol"], ngay10(t["entry_date"])
    df = kho[ma]["df"]
    nguon = kho[ma]["nguon"]
    j = PaperTradingJournal(":memory:")
    goc = mo_so(so)
    goc.backup(j.db)
    goc.close()
    sl0 = (t["nhat_ky"] or {}).get("stop_loss_ban_dau") or t["stop_loss"]
    j.db.execute("UPDATE trades SET status='OPEN', exit_date=NULL, exit_price=NULL, exit_reason=NULL,"
                 " stop_loss=? WHERE id=?", (sl0, t["id"]))
    j.db.commit()
    nk_truoc = j.db.execute("SELECT * FROM nhat_ky WHERE trade_id=?", (t["id"],)).fetchone()
    nk_truoc = tuple(nk_truoc) if nk_truoc else None
    bam_truoc = _bam_phan_con_lai(j.db, t["id"])
    buoc, canh_bao, su_kien = [], [], []
    dem_chinh = 0
    san = None
    from san_giao_dich import san_cua
    san = san_cua(ma)
    ngay_cac_nen = [d for d in df["ngay"] if ngay_vao < d <= den]
    for d in ngay_cac_nen:
        if d not in diem:
            continue
        sub = df[df["ngay"] <= d]
        row = j.db.execute("SELECT status FROM trades WHERE id=?", (t["id"],)).fetchone()
        if row["status"] not in (Status.OPEN, Status.CLOSING):
            break
        if sua:
            ev = ct.chinh_thang_mot_ma(j, ma, sub, d, nguon=nguon, san=san,
                                       ghi=lambda s: canh_bao.append(s) if s.startswith("##[warning]") else None,
                                       nhan_f=nhan_f)
            for e in ev:
                su_kien.append(dict(e, ngay_nen=d))
                if e["trang_thai"] == ct.CHINH:
                    dem_chinh += 1
        mult = price_multiplier(sub)
        nen_tho = sub.iloc[-1]
        bar = {k: float(nen_tho[k]) * mult for k in ("open", "high", "low", "close")}
        bar["volume"] = float(nen_tho["volume"]) if "volume" in sub.columns else 0.0
        _nen = None
        if len(sub) >= 2:
            _nen = {"high": bar["high"], "low": bar["low"], "volume": bar["volume"],
                    "tham_chieu": float(sub["close"].iloc[-2]) * mult}
        j.fill_closing(ma, d, bar["open"], _nen)
        r = j.db.execute("SELECT * FROM trades WHERE id=?", (t["id"],)).fetchone()
        if r["status"] == Status.OPEN:
            _bar = dict(bar, tham_chieu=_nen["tham_chieu"]) if _nen else bar
            sl_truoc = float(r["stop_loss"])
            j.evaluate_open(ma, d, _bar, current_score=int(diem[d]) if diem[d] is not None else None)
            buoc.append({"ngay": d, "thap": bar["low"], "cao": bar["high"], "dong": bar["close"],
                         "sl_truoc": sl_truoc, "bien": (bar["low"] - sl_truoc) / bar["low"]})
        elif r["status"] == Status.CLOSED:
            break
    bam_sau = _bam_phan_con_lai(j.db, t["id"])
    r = dict(j.db.execute("SELECT * FROM trades WHERE id=?", (t["id"],)).fetchone())
    nk_sau = j.db.execute("SELECT * FROM nhat_ky WHERE trade_id=?", (t["id"],)).fetchone()
    nk_sau = dict(nk_sau) if nk_sau else None
    ra_gia = False
    if dong_cuoi and r["status"] == Status.OPEN:
        sub = df[df["ngay"] <= den]
        mult = price_multiplier(sub)
        j.dong_so_sach(ma, str(sub["ngay"].iloc[-1]), float(sub["close"].iloc[-1]) * mult)
        r = dict(j.db.execute("SELECT * FROM trades WHERE id=?", (t["id"],)).fetchone())
        ra_gia = True
    return {"id": t["id"], "ma": ma, "sua": sua, "nhan_f": nhan_f, "row": r, "nhat_ky_truoc": nk_truoc,
            "nhat_ky_sau": nk_sau, "buoc": buoc, "su_kien": su_kien, "canh_bao": canh_bao,
            "dem_chinh": dem_chinh, "bam_truoc": bam_truoc, "bam_sau": bam_sau,
            "ban_giu_nguyen_ngoai_lenh": bam_truoc == bam_sau, "ra_gia": ra_gia}


def so_o(a: dict, b: dict, cac_o=CAC_O_SO_SANH) -> list[str]:
    """Các ô khác nhau giữa hai dòng `trades` (ngày so 10 ký tự, các ô khác so từng chữ số)."""
    khac = []
    for o in cac_o:
        x, y = a.get(o), b.get(o)
        if o == "exit_date":
            x, y = ngay10(x), ngay10(y)
        if x != y:
            khac.append(f"{o}: {x!r} ≠ {y!r}")
    return khac


# ─────────────────────────── đối chứng ───────────────────────────
def doi_chung(so: Path, qt: list[dict], kho: dict, c: sqlite3.Connection) -> dict:
    """(i)–(iv) của bản ký, chỉ cần bản CƠ SỞ (+ phép đo f). Trả dict và in dữ liệu thô."""
    kq: dict[str, Any] = {"co_so": {}, "chi_tiet": []}
    diem = {t["symbol"]: diem_theo_ngay(c, t["symbol"]) for t in qt}
    chay1 = {t["id"]: phat_lai(so, t, kho, diem[t["symbol"]], sua=False) for t in qt}
    chay2 = {t["id"]: phat_lai(so, t, kho, diem[t["symbol"]], sua=False) for t in qt}
    kq["co_so"], kq["_diem"] = chay1, diem
    # (iii) hai lượt cơ sở liên tiếp cho cùng kết quả
    giong = all(so_o(chay1[i]["row"], chay2[i]["row"]) == [] and chay1[i]["buoc"] == chay2[i]["buoc"]
                for i in chay1)
    kq["iii_hai_luot_co_so_giong"] = giong
    # (i) ca dương
    i_ket = {}
    for i, ca in CA_DUONG.items():
        r = chay1[i]["row"]
        ly_do, ngay, gia = ca["ra"]
        i_ket[i] = (r["exit_reason"] == ly_do and ngay10(r["exit_date"]) == ngay and r["exit_price"] == gia,
                    {"exit_reason": r["exit_reason"], "exit_date": ngay10(r["exit_date"]),
                     "exit_price": r["exit_price"], "ky_vong": ca["ra"]})
    kq["i_ca_duong"] = i_ket
    # (ii) 18 lệnh còn lại tái lập đúng từng chữ số ngày ra, lý do và giá ra của dòng sổ
    ii = {}
    for t in qt:
        if t["id"] in CA_DUONG:
            continue
        r = chay1[t["id"]]["row"]
        khac = so_o(r, t, ("exit_date", "exit_reason", "exit_price"))
        ii[t["id"]] = khac
    kq["ii_khac"] = ii
    # tất cả các ô cho mọi lệnh (dữ liệu thô)
    for t in qt:
        r = chay1[t["id"]]["row"]
        kq["chi_tiet"].append({"id": t["id"], "ma": t["symbol"], "so_vs_co_so": so_o(r, t),
                               "ra_so": (ngay10(t["exit_date"]), t["exit_reason"], t["exit_price"]),
                               "ra_co_so": (ngay10(r["exit_date"]), r["exit_reason"], r["exit_price"])})
    return kq


def in_doi_chung(kq: dict) -> None:
    print("\n=== ĐỐI CHỨNG (i)–(iii): bản CƠ SỞ ===")
    for d in kq["chi_tiet"]:
        print(f" #{d['id']:<3} {d['ma']:<4} sổ {d['ra_so']} · cơ sở {d['ra_co_so']} · "
              f"ô khác sổ: {d['so_vs_co_so'] or 'không'}")
    print("(i) ca dương:", {i: v[0] for i, v in kq["i_ca_duong"].items()},
          {i: v[1] for i, v in kq["i_ca_duong"].items()})
    loai = sorted(i for i, k in kq["ii_khac"].items() if k)
    print(f"(ii) lệnh KHÔNG tái lập (ngày ra · lý do · giá ra): {loai}  (loại quá 2 ⇒ K0)")
    print(f"(iii) hai lượt cơ sở liên tiếp giống nhau: {kq['iii_hai_luot_co_so_giong']}")


# ─────────────────────────── chạy đầy đủ ───────────────────────────
def p95(xs: list[float]) -> Optional[float]:
    return do26.p95(xs)


def chay(thu_muc: Path, ca_pytest: bool) -> int:
    t0 = time.time()
    so = thu_muc / "so_that_272.db"
    kho = doc_nen(thu_muc)
    bam_so_truoc = bam_tep(so)
    bam_khung_truoc = {m: bam_khung(v["df"]) for m, v in kho.items()}
    c = mo_so(so)
    qt = quan_the(c)
    print(f"sổ {so.name} sha256 {bam_so_truoc}")
    print(f"quần thể tiến-về-trước đã đóng: {len(qt)} lệnh, id {[t['id'] for t in qt]}")
    mo_hien = [tuple(r) for r in c.execute("SELECT status, COUNT(*) FROM trades GROUP BY status")]
    print(f"trạng thái sổ: {mo_hien}")
    kq_dc = doi_chung(so, qt, kho, c)
    in_doi_chung(kq_dc)
    co_so, diem = kq_dc["co_so"], kq_dc["_diem"]

    # (iv) f đo được cho CẢ 20 lệnh
    nen_theo_ma = {m: skq.dung_nen(v["df"]["time"], v["df"]["open"], v["df"]["low"], v["df"]["high"],
                                   price_multiplier(v["df"])) for m, v in kho.items()}
    f_do = {}
    for t in qt:
        f_do[t["id"]] = ct.do_he_so(t["entry_price"], t["entry_date"], nen_theo_ma[t["symbol"]])
    iv_thieu = [i for i, k in f_do.items() if k["f"] is None]
    print("\n(iv) f đo được cho mọi lệnh:", "ĐỦ 20/20" if not iv_thieu else f"THIẾU {iv_thieu}")
    for t in qt:
        k = f_do[t["id"]]
        print(f"  #{t['id']:<3} {t['symbol']:<4} vào {ngay10(t['entry_date'])} giá vào {t['entry_price']:>10,.1f}"
              f" f = {k['f'] if k['f'] is None else round(k['f'], 6)} → {k['trang_thai']}")

    # (v) lịch VCI cho HDB và TCB (và mọi mã, cho danh sách tiền mặt ở C5)
    lich: dict[str, list] = {}
    loi_lich: dict[str, str] = {}
    for ma in sorted(kho):
        try:
            lich[ma] = do26.chuan_hoa(ma, tai_lich(ma))
        except Exception as e:                          # noqa: BLE001
            loi_lich[ma] = f"{type(e).__name__}: {e}"
    print("\n(v) lịch VCI đọc được:", sorted(lich), "· lỗi:", loi_lich)
    v_ok = {i: (CA_DUONG[i]["ma"] in lich) for i in CA_DUONG}

    # K0 từ đối chứng?
    k0 = []
    if not all(v_ok.values()):
        k0.append(f"(v) lịch VCI không đọc được cho {sorted(i for i, v in v_ok.items() if not v)}: C6 là K0")
    if not all(v[0] for v in kq_dc["i_ca_duong"].values()):
        k0.append("(i) ca dương không tái lập")
    loai_c3 = sorted(i for i, k in kq_dc["ii_khac"].items() if k)
    if len(loai_c3) > 2:
        k0.append(f"(ii) loại {len(loai_c3)} > 2 lệnh: {loai_c3}")
    if not kq_dc["iii_hai_luot_co_so_giong"]:
        k0.append("(iii) hai lượt cơ sở khác nhau")
    if bam_tep(so) != bam_so_truoc:
        k0.append("(iii) băm sổ đổi")
    if iv_thieu:
        k0.append(f"(iv) thiếu f cho {iv_thieu}")
    print("\nK0 từ đối chứng:", k0 or "không")

    # bản SỬA, và C1/C2/C3/C4/C8/C9/C11
    sua = {t["id"]: phat_lai(so, t, kho, diem[t["symbol"]], sua=True) for t in qt}
    sua098 = {i: phat_lai(so, next(t for t in qt if t["id"] == i), kho, diem[CA_DUONG[i]["ma"]], sua=True,
                          nhan_f=0.98) for i in CA_DUONG}
    sua102 = {i: phat_lai(so, next(t for t in qt if t["id"] == i), kho, diem[CA_DUONG[i]["ma"]], sua=True,
                          nhan_f=1.02) for i in CA_DUONG}
    sua_c11 = phat_lai(so, next(t for t in qt if t["id"] == 128), kho, diem["TCB"], sua=True, dong_cuoi=True)

    ket: dict[str, Any] = {}
    print("\n=== C1 · C2: hai ca dương không còn cắt lỗ GIẢ ===")
    for i, ca in CA_DUONG.items():
        den_cs = ca["cua_so_den"]
        t = next(x for x in qt if x["id"] == i)
        lc = luot_cuoi_xu_ly_nen(c, ca["ma"], ngay10(t["exit_date"]))
        print(f" #{i} {ca['ma']}: cửa sổ xử lý đọc từ bản ký đến {den_cs}; lượt cuối xử lý nến ra ghi trong sổ: {lc}")
        for nhan, ch in (("f đo", sua[i]), ("f×0,98", sua098[i]), ("f×1,02", sua102[i])):
            r = ch["row"]
            trong = [b for b in ch["buoc"] if b["ngay"] <= den_cs]
            bien = min((b["bien"] for b in trong), default=None)
            cat_gia = (r["exit_reason"] == "STOP_LOSS" and ngay10(r["exit_date"]) <= den_cs)
            print(f"   [{nhan}] kết cục {r['status']} · ra {ngay10(r['exit_date'])} · {r['exit_reason']} · "
                  f"giá ra {r['exit_price']} · cắt lỗ GIẢ trong cửa sổ: {cat_gia} · "
                  f"biên an toàn nhỏ nhất (thấp − SL)/thấp = {bien if bien is None else round(bien, 6)} "
                  f"· số lần chỉnh {ch['dem_chinh']}")
            ket[f"C1C2_{i}_{nhan}"] = {"cat_lo_gia": cat_gia, "bien_an_toan": bien, "row": r}
    ket["C1"] = all(not ket[f"C1C2_{i}_f đo"]["cat_lo_gia"] for i in CA_DUONG)
    ket["C2"] = all(not ket[f"C1C2_{i}_f×0,98"]["cat_lo_gia"] for i in CA_DUONG)

    print("\n=== C3 · C4: 18 lệnh còn lại ===")
    c3_sai, c4_max, c4_kich = [], [], []
    for t in qt:
        if t["id"] in CA_DUONG:
            continue
        s = sua[t["id"]]
        khac = so_o(s["row"], co_so[t["id"]]["row"])
        nk_khac = s["nhat_ky_sau"] != co_so[t["id"]]["nhat_ky_sau"]
        if t["id"] in loai_c3:
            print(f" #{t['id']} LOẠI khỏi C3 (không tái lập ở bước (ii))")
            continue
        if khac or nk_khac or s["dem_chinh"]:
            c3_sai.append((t["id"], khac, nk_khac, s["dem_chinh"]))
        c4_max.append(abs(f_do[t["id"]]["f"] - 1))
        if f_do[t["id"]]["trang_thai"] == ct.CHINH:
            c4_kich.append(t["id"])
    ket["C3"] = not c3_sai
    print(" C3 ô khác / nhật ký khác / số lần chỉnh:", c3_sai or "KHÔNG có ô nào đổi")
    ket["C4_kich_hoat"] = sorted(i for i, k in f_do.items() if k["trang_thai"] == ct.CHINH)
    ket["C4_max_f_1"] = max(c4_max) if c4_max else None
    ket["C4"] = (ket["C4_kich_hoat"] == sorted(CA_DUONG) and ket["C4_max_f_1"] is not None
                 and ket["C4_max_f_1"] <= ct.NGUONG_LECH / 2)
    print(f" C4: kích hoạt ở {ket['C4_kich_hoat']} (cần đúng {sorted(CA_DUONG)}) · max |f−1| của 18 lệnh = "
          f"{ket['C4_max_f_1']} (≤ {ct.NGUONG_LECH / 2})")

    print("\n=== C6: f_vào ÷ F (lịch VCI) ===")
    c6 = {}
    for i, ca in CA_DUONG.items():
        t = next(x for x in qt if x["id"] == i)
        if ca["ma"] not in lich:
            c6[i] = None
            print(f" #{i}: lịch không đọc được — C6 là K0 cho ca này")
            continue
        sk = do26.trong_khoang(lich[ca["ma"]], ngay10(t["entry_date"]), ca["cua_so_den"])
        F = do26.he_so(sk, t["entry_price"], "M_CK")
        f = f_do[i]["f"]
        sai = None if F is None else abs(f / F - 1)
        c6[i] = {"F": F, "f": f, "sai": sai, "su_kien": [(s.ngay, s.loai, s.ty_le) for s in sk]}
        print(f" #{i} {ca['ma']}: f_vào = {f:.6f} · F = {F} · |f/F − 1| = {sai} (≤ {ct.NOI_BIEN}) · {c6[i]['su_kien']}")
    ket["C6"] = (None if any(v is None for v in c6.values())
                 else all(v["sai"] is not None and v["sai"] <= ct.NOI_BIEN for v in c6.values()))
    ket["C6_chi_tiet"] = c6

    print("\n=== C5 (nhật): sự kiện TIỀN MẶT của lịch VCI ở cửa sổ 20 lệnh (kỳ vọng 0) ===")
    tm = []
    for t in qt:
        ma = t["symbol"]
        if ma not in lich:
            continue
        den_cs = CA_DUONG[t["id"]]["cua_so_den"] if t["id"] in CA_DUONG else (
            luot_cuoi_xu_ly_nen(c, ma, ngay10(t["exit_date"])) or ngay10(t["exit_date"]))
        for s in do26.trong_khoang(lich[ma], ngay10(t["entry_date"]), den_cs):
            if s.loai == do26.TM:
                tm.append((t["id"], ma, s.ngay, s.ty_le, s.tien))
    print(" sự kiện tiền mặt:", tm or "KHÔNG có")
    ket["C5_tien_mat"] = tm
    print(" (lịch lỗi:", loi_lich or "không", ")")

    print("\n=== C8 (thật): băm từng bảng/dòng ngoài lệnh phát lại, trước/sau mỗi lượt sửa ===")
    c8_sai = [i for i, s in sua.items() if not s["ban_giu_nguyen_ngoai_lenh"]]
    c8_sai += [("0,98", i) for i, s in sua098.items() if not s["ban_giu_nguyen_ngoai_lenh"]]
    ket["C8_thuc"] = not c8_sai
    print(" lượt phát lại làm đổi dòng ngoài lệnh của nó:", c8_sai or "KHÔNG")

    print("\n=== C9 (thật): máy dò chưa-điều-chỉnh trên nến THẬT từ ngày vào tới ngày ra ===")
    c9 = []
    for t in qt:
        df = kho[t["symbol"]]["df"]
        from san_giao_dich import san_cua
        mult = price_multiplier(df)
        den_r = ngay10(t["exit_date"])
        c9 += [(t["id"], t["symbol"], x) for x in ct.may_do_chua_dieu_chinh(
            df, mult, san_cua(t["symbol"]), ngay10(t["entry_date"]), den_r)]
    ket["C9_thuc"] = not c9
    print(" cảnh báo trên nến thật:", c9 or "0")
    n_canh_bao_sua = sum(len(s["canh_bao"]) for s in sua.values())
    print(f" `##[warning]` bản sửa sinh ra trên 20 lệnh (cả cửa sổ tới 12/11): {n_canh_bao_sua}")
    for i, s in sua.items():
        for w in s["canh_bao"]:
            print("   ", i, w)

    print("\n=== C11 (thật): #128 theo tới lối ra ===")
    r = sua_c11["row"]
    t128 = next(x for x in qt if x["id"] == 128)
    df = kho["TCB"]["df"]
    mult = price_multiplier(df)
    vao = r["entry_price"]
    ngay_ra = ngay10(r["exit_date"])
    seg = df[(df["ngay"] >= ngay10(t128["entry_date"])) & (df["ngay"] <= (ngay_ra or NGAY_CUOI))]
    thap, cao = float(seg["low"].min()) * mult, float(seg["high"].max()) * mult
    lo = thap * (1 - ct.NOI_BIEN) / vao - 1
    hi = cao * (1 + ct.NOI_BIEN) / vao - 1
    ret = r["exit_price"] / vao - 1
    ret_cu = r["exit_price"] / t128["entry_price"] - 1
    nk = sua_c11["nhat_ky_sau"]
    c11_trong = lo <= ret <= hi
    c11_doi_chung = not (lo <= ret_cu <= hi)
    ket["C11_thuc"] = c11_trong and c11_doi_chung
    print(f" kết cục {r['status']} · ra {ngay_ra} · {r['exit_reason']} · giá ra {r['exit_price']} · "
          f"ra GIẢ cuối dữ liệu: {sua_c11['ra_gia']}")
    print(f" entry_price ĐÃ CHỈNH {vao:.4f} · ret = {ret:+.4%} ∈ [{lo:+.4%} ; {hi:+.4%}]: {c11_trong}")
    print(f" đối chứng entry CHƯA chỉnh {t128['entry_price']}: ret = {ret_cu:+.4%} VƯỢT biên: {c11_doi_chung}")
    if nk:
        print(f" nhat_ky #128: entry_price {nk['entry_price']} · stop_loss_ban_dau {nk['stop_loss_ban_dau']} "
              f"(thang mới) · dieu_chinh_thang trong boi_canh: "
              f"{json.loads(nk['boi_canh']).get(ct.KHOA_NHAT_KY) if nk['boi_canh'] else None}")

    print("\n=== Ba đại lượng nhiễu f của nhóm sạch (N, max, p95; max cũ 0,0038 ĐO 26 · 0,0070 ĐO 27) ===")
    sach = [abs(f_do[t["id"]]["f"] - 1) for t in qt if t["id"] not in CA_DUONG]
    print(f" N = {len(sach)} · max = {max(sach):.6f} · p95 = {p95(sach):.6f}")
    ket["nhieu"] = {"N": len(sach), "max": max(sach), "p95": p95(sach)}

    # kết cục SAU cửa sổ của hai ca (báo kèm)
    print("\n=== Báo kèm: kết cục SAU cửa sổ của #122 và #128 (bản sửa, f đo) ===")
    for i in CA_DUONG:
        r = sua[i]["row"]
        print(f" #{i}: status {r['status']} · ra {ngay10(r['exit_date'])} · {r['exit_reason']} · giá ra "
              f"{r['exit_price']} · giá vào đã chỉnh {r['entry_price']:.2f} · cắt lỗ cuối {r['stop_loss']:.2f}")
        if r["status"] != "CLOSED":
            print("     → còn mở tới 12/11/2026 (không gọi lãi/lỗ)")
        elif r["exit_price"] and r["entry_price"]:
            print(f"     → net_return của dòng phát lại: {(r['exit_price']/r['entry_price']-1)*100:+.2f}% (chưa trừ phí)")
    tong = 0.0
    ok_tong = True
    for i in CA_DUONG:
        r = sua[i]["row"]
        if r["status"] == "CLOSED" and r["exit_price"] and r["entry_price"]:
            tong += (r["exit_price"] / r["entry_price"] - 1) * 100
        else:
            ok_tong = False
    print(f" Quy tắc 1: tổng lợi nhuận gộp sau sửa #122+#128 (hai lệnh đã đóng?) = {tong:+.2f}% (cả hai đóng: {ok_tong})")

    ket["bam"] = {"so_truoc": bam_so_truoc, "so_sau": bam_tep(so),
                  "khung_truoc": bam_khung_truoc,
                  "khung_sau": {m: bam_khung(v["df"]) for m, v in kho.items()}}
    m0 = (ket["bam"]["so_truoc"] == ket["bam"]["so_sau"] and
          ket["bam"]["khung_truoc"] == ket["bam"]["khung_sau"])
    print(f"\n(iii) M0 băm sổ và khung giá trước = sau: {m0}")
    if not m0:
        k0.append("(iii) M0")

    pyt: dict[str, Any] = {}
    if ca_pytest:
        print("\n=== Phần TỔNG HỢP (pytest, dựng tay): C5 · C7 · C8 · C9 · C10 · C11 ===")
        for ten, loc in (("C5", "test_C5_"), ("C7", "test_C7"), ("C8", "test_C8_"),
                         ("C9", "test_C9_"), ("C10", "test_C10"), ("C11", "test_C11_")):
            lenh = [sys.executable, "-m", "pytest", "tests/test_chinh_thang_gia.py", "-q", "-k", loc,
                    "-p", "no:cacheprovider"]
            p = subprocess.run(lenh, cwd=GOC, capture_output=True, text=True, encoding="utf-8",
                               errors="replace")
            cuoi = (p.stdout.strip().splitlines() or ["?"])[-1]
            pyt[ten] = {"ma_thoat": p.returncode, "dong_cuoi": cuoi}
            print(f" {ten}: mã thoát {p.returncode} · {cuoi}")
        lenh = [sys.executable, "-m", "pytest", "tests/test_sheets_store.py", "-q", "-p", "no:cacheprovider"]
        p = subprocess.run(lenh, cwd=GOC, capture_output=True, text=True, encoding="utf-8", errors="replace")
        pyt["sheets_store"] = {"ma_thoat": p.returncode, "dong_cuoi": (p.stdout.strip().splitlines() or ["?"])[-1]}
        print(f" test_sheets_store: mã thoát {p.returncode} · {pyt['sheets_store']['dong_cuoi']}")
    ket["pytest"] = pyt

    # ── PHÁN KẾT CỤC (đúng văn bản đã ký) ──
    def ok(k):
        return None if k not in pyt else pyt[k]["ma_thoat"] == 0
    C = {
        "C1": ket["C1"], "C2": ket["C2"], "C3": ket["C3"], "C4": ket["C4"],
        "C5": (ok("C5")), "C6": ket["C6"],
        "C7": ok("C7"),
        "C8": (None if ok("C8") is None else (ok("C8") and ket["C8_thuc"] and ok("sheets_store"))),
        "C9": (None if ok("C9") is None else (ok("C9") and ket["C9_thuc"])),
        "C11": (None if ok("C11") is None else (ok("C11") and ket["C11_thuc"])),
    }
    print("\n=== PHÁN QUYẾT TỪNG TIÊU CHÍ ===")
    for k in ("C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C11"):
        print(f" {k}: {'ĐẠT' if C[k] else ('CHƯA CHẠY' if C[k] is None else 'TRƯỢT')}")
    if k0:
        ketcuc = "K0"
    else:
        b = [k for k in ("C3", "C4", "C5", "C7", "C8") if C[k] is False]
        cc = [k for k in ("C1", "C2", "C6", "C9", "C11") if C[k] is False or C[k] is None and k == "C6"]
        if b:
            ketcuc = "B" + (" (đồng thời C)" if cc else "")
        elif cc:
            ketcuc = "C"
        elif any(v is None for v in C.values()):
            ketcuc = "CHƯA ĐỦ DỮ LIỆU ĐỂ PHÁN (thiếu pytest)"
        else:
            ketcuc = "A"
    print(f"\n>>> KẾT CỤC ĐO 35: {ketcuc}   (K0: {k0})")
    print(f"thời gian chạy {time.time() - t0:.0f} s")

    def gon(o):
        if isinstance(o, dict):
            return {str(k): gon(v) for k, v in o.items() if k not in ("df",)}
        if isinstance(o, (list, tuple)):
            return [gon(x) for x in o]
        return o
    with open(thu_muc / "ket_qua_do35.json", "w", encoding="utf-8") as f:
        json.dump(gon({"ketcuc": ketcuc, "k0": k0, "C": C, "ket": ket, "f_do": f_do,
                       "doi_chung_i": kq_dc["i_ca_duong"], "doi_chung_ii": kq_dc["ii_khac"]}),
                  f, ensure_ascii=False, indent=1, default=str)
    return 0 if ketcuc == "A" else 1


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("lenh", choices=["tai-nen", "doi-chung", "chay"])
    ap.add_argument("--thu-muc", required=True)
    ap.add_argument("--pytest", action="store_true")
    a = ap.parse_args(argv)
    os.environ["POST_MORTEM_ENABLED"] = "0"   # phát lại không được ghi bộ nhớ mẫu hình cắt lỗ (chỉ khi chạy CLI)
    thu_muc = Path(a.thu_muc)
    if a.lenh == "tai-nen":
        tai_nen(thu_muc)
        return 0
    if a.lenh == "doi-chung":
        so = thu_muc / "so_that_272.db"
        kho = doc_nen(thu_muc)
        c = mo_so(so)
        qt = quan_the(c)
        kq = doi_chung(so, qt, kho, c)
        in_doi_chung(kq)
        return 0
    return chay(thu_muc, a.pytest)


if __name__ == "__main__":
    sys.exit(main())
