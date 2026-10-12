"""ĐO 25 — kế hoạch vào lệnh B6 có hơn "mua mọi tín hiệu ở giá mở cửa phiên sau" không?

Tiêu chí ký trước: `docs/TIEU-CHI-DOC-TRUOC.md`, mục *ĐO 25* (commit riêng, TRƯỚC file này).
Mọi hằng số, ngưỡng và kết cục ở đây là chép từ mục ấy; đổi một con số sau khi nhìn kết quả là
vi phạm bất biến 7 — muốn đổi phải khai ĐO mới.

CHỈ ĐỌC: không mạng, không `import vnstock`, không ghi cache, không ghi sổ lệnh, không mở
`paper_trades.db`. Chỉ ghi MỘT file JSON kết quả ở đường dẫn người gọi chọn (`--ghi`).

    ./.venv/Scripts/python.exe tools/do25_ke_hoach_vao_lenh.py doi-chung
    ./.venv/Scripts/python.exe tools/do25_ke_hoach_vao_lenh.py chay \
        --cache backtest/cache --ghi <đường dẫn JSON> [--tu YYYY-MM-DD] [--den YYYY-MM-DD]

MÁY CHẤM: tái dùng NGUYÊN các hàm của `walkforward.py` ở chế độ "theo ngày", độ trễ khớp 1:
vùng ngoài mẫu (`nap_moc_sach` + `chia_vung`), lịch phiên (`lich_theo_ngay`), bộ nhớ
(`_dung_bo_nho`), và điểm của `paper_runner._analyze` — không viết lại công thức điểm. Mặc định
`stride`, `min_history`, `che_do_hoc` ĐỌC từ chữ ký của `walkforward.chay`, không gõ lại.

Hai chính sách, cùng khung H = 20 phiên, cùng chi phí vòng `paper_metrics.ROUND_TRIP_COST_PCT`
(đi qua `Trade.net_return_pct`), KHÔNG mô phỏng trượt giá cho bên nào.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import inspect
import json
import os
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pandas as pd

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(GOC / "tools"))

import ke_hoach_vao_lenh as KH  # noqa: E402
import paper_metrics as PM  # noqa: E402
import paper_runner as PR  # noqa: E402
import paper_trading as PT  # noqa: E402
import san_giao_dich  # noqa: E402
import truot_gia  # noqa: E402
import walkforward as WF  # noqa: E402
from data_quality import price_multiplier  # noqa: E402

# ── Hằng số đã KÝ TRƯỚC (docs/TIEU-CHI-DOC-TRUOC.md, ĐO 25) ─────────────────────────────────────
#: Khung nắm giữ chung của cả hai chính sách: ra ở giá đóng cửa phiên t + H.
KHUNG_H = 20
SO_LUOT_BOOTSTRAP = 10_000
HAT_BOOTSTRAP = 20261010
#: Ngưỡng mua đã ký. Dụng cụ NHẬP `paper_trading.BUY_THRESHOLD` (một ngưỡng, một chỗ) rồi DỪNG
#: nếu nó không còn là số này — đổi ngưỡng thì quần thể đổi, tức là một ĐO khác.
NGUONG_DA_KY = 62
#: Commit merge mà `ke_hoach_vao_lenh.py` phải còn ĐÚNG như thế (PR #219).
COMMIT_KE_HOACH = "d44cc87"
#: Δ trung bình lớn hơn mức này (điểm %/tín hiệu) → soát lỗi TRƯỚC khi đọc (Quy tắc 1).
NGUONG_QUY_TAC_1 = 2.0
HAT_DOI_CHUNG = 25
#: Mức ngoài khoảng KTC dưới/trên theo percentile của bootstrap (KTC 95%).
PHAN_VI_KTC = (2.5, 97.5)

#: Giờ giả định "sau giờ đóng cửa ngày t" khi gọi `lap_ke_hoach` (nến ngày t đã đóng).
GIO_SAU_DONG_CUA = datetime.time(23, 0)

KET_CUC_CHUA_DU = "CHƯA ĐỦ"
KET_CUC_A = "A — triển vọng"
KET_CUC_B = "B — chưa phân biệt được"
KET_CUC_C = "C — kém hơn"

_CHUA_LAP = KH.CHUA_LAP_DUOC


# ── nạp dữ liệu (CHỈ ĐỌC) ──────────────────────────────────────────────────────────────────────
@contextmanager
def dat_cache(thu_muc):
    """Trỏ `backtest.data.CACHE_DIR` sang `thu_muc` trong một khối, rồi trả lại.

    Dùng đúng `load` của backtest (sắp xếp theo `time`, kiểm đủ cột) thay vì viết bộ đọc thứ hai.
    """
    import backtest.data as BD
    cu = BD.CACHE_DIR
    BD.CACHE_DIR = Path(thu_muc)
    try:
        yield BD
    finally:
        BD.CACHE_DIR = cu


def bam_thu_muc(thu_muc) -> dict:
    """M0 — băm SHA-256 theo (tên file, nội dung) của mọi `*.csv`, cùng mtime nhỏ nhất/lớn nhất."""
    files = sorted(Path(thu_muc).glob("*.csv"))
    h = hashlib.sha256()
    mt = []
    for f in files:
        h.update(f.name.encode("utf-8"))
        h.update(b"\0")
        h.update(f.read_bytes())
        h.update(b"\0")
        mt.append(f.stat().st_mtime)
    iso = (lambda x: datetime.datetime.fromtimestamp(x, datetime.timezone.utc).isoformat())
    return {"so_file": len(files), "sha256": h.hexdigest(),
            "mtime_nho_nhat": iso(min(mt)) if mt else None,
            "mtime_lon_nhat": iso(max(mt)) if mt else None}


def kiem_ma_ke_hoach(goc=GOC, commit: str = COMMIT_KE_HOACH) -> str:
    """`khop` · `lech` · `chua_kiem_duoc` — `ke_hoach_vao_lenh.py` còn ĐÚNG như ở `commit` không.

    Dùng `git diff --quiet <commit> -- ke_hoach_vao_lenh.py` (chuẩn hoá xuống dòng giúp git lo).
    Không có git / không có commit đó (repo nông) → `chua_kiem_duoc`, KHÔNG trả `khop`.
    """

    def git(*args):
        return subprocess.run(["git", *args], cwd=str(goc), capture_output=True).returncode

    try:
        # Ngoài một repo, `git diff` chạy ở chế độ --no-index và trả 1 ("lệch") cho bất cứ gì:
        # phải xác nhận có repo VÀ có commit trước khi tin mã thoát của diff.
        if git("rev-parse", "--git-dir") != 0 or git("cat-file", "-e", f"{commit}^{{commit}}") != 0:
            return "chua_kiem_duoc"
        ma = git("diff", "--quiet", commit, "--", "ke_hoach_vao_lenh.py")
    except OSError:
        return "chua_kiem_duoc"
    return {0: "khop", 1: "lech"}.get(ma, "chua_kiem_duoc")


def mac_dinh_walkforward() -> dict:
    """`stride` · `min_history` · `che_do_hoc` mặc định của `walkforward.chay` — ĐỌC, không gõ lại."""
    tham = inspect.signature(WF.chay).parameters
    return {k: tham[k].default for k in ("stride", "min_history", "che_do_hoc")}


def dung_vung_oos(tat_ca: dict, moc: dict, min_history: int) -> dict:
    """Vùng ngoài mẫu, ĐÚNG phép dựng trong `walkforward.chay`: mã có mốc, phần < mốc, đủ dài."""
    vung = {}
    for sym, df in tat_ca.items():
        if sym not in moc:
            continue
        o, _ = WF.chia_vung(df, moc[sym])
        if len(o) > min_history:
            vung[sym] = o.reset_index(drop=True)
    return vung


@contextmanager
def moi_truong_cham_diem(che_do_hoc: str):
    """Bộ nhớ post-mortem + biến môi trường như `walkforward.chay` dựng, rồi trả lại như cũ."""
    cu = os.environ.get("POST_MORTEM_ENABLED")
    os.environ["POST_MORTEM_ENABLED"] = "0" if che_do_hoc == "tat" else "1"
    try:
        yield WF._dung_bo_nho(che_do_hoc, None)
    finally:
        os.environ.pop("POST_MORTEM_ENABLED", None)
        if cu is not None:
            os.environ["POST_MORTEM_ENABLED"] = cu
        from post_mortem_learning import MEMORY_FILE, dat_lai_engine
        dat_lai_engine(MEMORY_FILE)
        PR._xoa_cache_phan_tich()


def cham_diem_that(sym: str, lich_su: pd.DataFrame, ngay: str) -> float:
    """Điểm cuối của MỘT phiên — đúng lời gọi `walkforward._chay_mot_phien` → `run_session` thực hiện."""
    return float(PR._analyze(sym, lich_su, "HOSE", ngay)["final_score"])


# ── mô phỏng khớp ──────────────────────────────────────────────────────────────────────────────
def tim_khop(df: pd.DataFrame, t: int, tran_vnd: float, san: str, he_so: float,
             cham: bool = False):
    """Lệnh giới hạn mua ở `tran_vnd`, hiệu lực `SO_PHIEN_CHO` phiên từ t+1.

    Khớp ở phiên d đầu tiên có low(d) ≤ trần − MỘT bước giá (`cham=True`: low(d) ≤ trần);
    giá khớp = min(open(d), trần). Trả `(d, giá khớp VNĐ)` hoặc `None` (lỡ).
    Bước giá lấy ở MỨC GIÁ CỦA TRẦN vùng, `truot_gia.buoc_gia(trần, sàn)`.
    """
    nguong = tran_vnd if cham else tran_vnd - truot_gia.buoc_gia(tran_vnd, san)
    cuoi = min(t + KH.SO_PHIEN_CHO, len(df) - 1)
    for d in range(t + 1, cuoi + 1):
        if round(float(df["low"].iloc[d]) * he_so, 6) <= nguong:
            mo = round(float(df["open"].iloc[d]) * he_so, 6)
            return d, min(mo, float(tran_vnd))
    return None


def dung_lenh(ma: str, ngay_t: str, diem: float, ngay_vao: str, gia_vao: float,
              ngay_ra: str, gia_ra: float) -> PT.Trade:
    """Một lệnh đã đóng, chỉ để `Trade.net_return_pct()` và `build_benchmark` đọc."""
    return PT.Trade(id=0, symbol=ma, signal_date=ngay_t, entry_date=ngay_vao,
                    entry_price=gia_vao, exit_date=ngay_ra, exit_price=gia_ra,
                    exit_reason=None, stop_loss=0.0, take_profit=0.0, size_pct=0.0,
                    entry_score=int(diem), status=PT.Status.CLOSED)


def lap_ke_hoach_cho_tin_hieu(df: pd.DataFrame, t: int, diem: float, san: str):
    """Kế hoạch B6 của tín hiệu tại hàng `t`: CHỈ nhìn các nến ≤ t, sau giờ đóng cửa ngày t."""
    lich_su = df.iloc[: t + 1]
    ngay = datetime.date.fromisoformat(str(df["time"].iloc[t])[:10])
    bay_gio = datetime.datetime.combine(ngay, GIO_SAU_DONG_CUA)
    return KH.lap_ke_hoach(lich_su, price_multiplier(lich_su), diem, NGUONG_DA_KY, bay_gio, san)


def ban_ghi_tin_hieu(ma: str, df: pd.DataFrame, t: int, diem: float, san: str, ke_hoach):
    """Các lệnh giả định của MỘT tín hiệu. `None` nếu không đủ `KHUNG_H` phiên về sau.

    Nền: mua ở giá MỞ CỬA t+1. B6: `MUA_NGAY` = nền; `CHO_VUNG` = khớp lệnh giới hạn (`tim_khop`),
    lỡ thì không nắm giữ; mọi phán quyết khác không nắm giữ. Hai biến thể của `CHO_VUNG`: khớp
    nghiêm (đã ký) và "chạm là khớp" (báo kèm).
    """
    if t + KHUNG_H > len(df) - 1:
        return None
    he = price_multiplier(df.iloc[: t + 1])
    ngay_t = str(df["time"].iloc[t])[:10]
    ngay_ra = str(df["time"].iloc[t + KHUNG_H])[:10]
    gia_ra = round(float(df["close"].iloc[t + KHUNG_H]) * he, 6)
    nen = dung_lenh(ma, ngay_t, diem, str(df["time"].iloc[t + 1])[:10],
                    round(float(df["open"].iloc[t + 1]) * he, 6), ngay_ra, gia_ra)
    khop = cham = None
    if ke_hoach.phan_quyet == KH.CHO_VUNG:
        if not ke_hoach.vung:
            raise ValueError(f"{ma} {ngay_t}: CHO_VUNG mà không có vùng — dữ liệu hỏng, không đoán")
        tran = float(ke_hoach.vung[1])

        def lenh(cham_la_khop):
            k = tim_khop(df, t, tran, san, he, cham=cham_la_khop)
            if k is None:
                return None
            d, gia = k
            return dung_lenh(ma, ngay_t, diem, str(df["time"].iloc[d])[:10], gia, ngay_ra, gia_ra)

        khop, cham = lenh(False), lenh(True)
    return {"ma": ma, "ngay": ngay_t, "diem": float(diem), "phan_quyet": ke_hoach.phan_quyet,
            "lenh_nen": nen, "lenh_khop": khop, "lenh_cham": cham}


# ── alpha và chênh lệch ────────────────────────────────────────────────────────────────────────
def alpha_cua_lenh(lenh, chuan: dict):
    """alpha khớp từng lệnh = lợi nhuận SAU CHI PHÍ − lợi nhuận chuẩn cùng khoảng giữ (`vs_benchmark`).

    `None` khi rổ chuẩn không có cặp ngày (chuẩn bị bỏ, được ĐẾM bởi người gọi).
    """
    khoa = (str(lenh.entry_date)[:10], str(lenh.exit_date)[:10])
    if khoa not in chuan:
        return None
    return lenh.net_return_pct() - chuan[khoa]


def gan_alpha(ban_ghi: list[dict], tap_du_lieu: dict) -> tuple[list[dict], int]:
    """Gắn `ret_*`/`alpha_*` cho từng bản ghi. Trả `(bản ghi giữ lại, số tín hiệu bỏ vì thiếu chuẩn)`.

    Một tín hiệu mà alpha của NỀN không dựng được bị bỏ khỏi CẢ HAI chính sách (không bỏ một bên).
    """
    lenh = [b[k] for b in ban_ghi for k in ("lenh_nen", "lenh_khop", "lenh_cham") if b[k] is not None]
    chuan = PR.build_benchmark(lenh, tap_du_lieu)
    giu, bo = [], 0
    for b in ban_ghi:
        ra = dict(b)
        ok = True
        for ten in ("nen", "khop", "cham"):
            ld = b[f"lenh_{ten}"]
            if ld is None:
                ra[f"ret_{ten}"] = ra[f"alpha_{ten}"] = None
                continue
            a = alpha_cua_lenh(ld, chuan)
            if a is None:
                ok = False
                break
            ra[f"ret_{ten}"], ra[f"alpha_{ten}"] = ld.net_return_pct(), a
        if ok:
            giu.append(ra)
        else:
            bo += 1
    return giu, bo


def khu_trung(ban_ghi: list[dict]) -> tuple[list[dict], int]:
    """Khử trùng theo (mã, ngày t): giữ bản đầu. Trả `(bản ghi, số bản bị bỏ)`."""
    thay, ra = set(), []
    for b in ban_ghi:
        khoa = (b["ma"], b["ngay"])
        if khoa in thay:
            continue
        thay.add(khoa)
        ra.append(b)
    return ra, len(ban_ghi) - len(ra)


def ket_qua_chinh_sach(b: dict, ep: str | None = None, cham: bool = False):
    """`(lợi nhuận, alpha)` của chính sách B6 cho bản ghi `b`. Không nắm giữ → `(0.0, 0.0)`.

    `ep` ép phán quyết (đối chứng): `MUA_NGAY` hoặc `BO_QUA`. Không ép thì dùng phán quyết thật.
    """
    v = ep or b["phan_quyet"]
    if v == KH.MUA_NGAY:
        return b["ret_nen"], b["alpha_nen"]
    if v == KH.CHO_VUNG:
        ten = "cham" if cham else "khop"
        if b[f"lenh_{ten}"] is not None:
            return b[f"ret_{ten}"], b[f"alpha_{ten}"]
    return 0.0, 0.0


def chenh(ban_ghi: list[dict], ep: str | None = None, cham: bool = False) -> dict:
    """Mảng Δ_i = alpha_P − alpha_B, cùng mảng chênh lợi nhuận, mảng ngày (khối bootstrap)."""
    d_alpha, d_ret, ngay = [], [], []
    for b in ban_ghi:
        rp, ap = ket_qua_chinh_sach(b, ep, cham)
        d_alpha.append(ap - b["alpha_nen"])
        d_ret.append(rp - b["ret_nen"])
        ngay.append(b["ngay"])
    return {"d_alpha": d_alpha, "d_ret": d_ret, "ngay": ngay}


def bootstrap_khoi_ngay(gia_tri, ngay, so_luot: int = SO_LUOT_BOOTSTRAP, hat: int = HAT_BOOTSTRAP):
    """KTC 95% của trung bình, bootstrap theo KHỐI NGÀY tín hiệu (rút lại cả ngày, không rút dòng).

    Mỗi lượt rút lại D ngày có hoàn lại; trung bình của lượt = tổng Δ / tổng số tín hiệu của các
    ngày được rút. Trả `(cận dưới, cận trên)`.
    """
    gia_tri = np.asarray(gia_tri, dtype=float)
    ngay_duy_nhat = sorted(set(ngay))
    chi_so = {d: i for i, d in enumerate(ngay_duy_nhat)}
    nhom = np.fromiter((chi_so[d] for d in ngay), dtype=np.int64, count=len(ngay))
    D = len(ngay_duy_nhat)
    tong = np.bincount(nhom, weights=gia_tri, minlength=D)
    dem = np.bincount(nhom, minlength=D).astype(float)
    rng = np.random.default_rng(hat)
    tb = np.empty(so_luot)
    cho = 1000
    for dau in range(0, so_luot, cho):
        n = min(cho, so_luot - dau)
        rut = rng.integers(0, D, size=(n, D))
        tb[dau:dau + n] = tong[rut].sum(axis=1) / dem[rut].sum(axis=1)
    lo, hi = np.percentile(tb, PHAN_VI_KTC)
    return float(lo), float(hi)


def ket_cuc(n: int, lo: float, hi: float) -> str:
    """Kết cục ĐÃ KÝ. Dưới `PM.N_TOI_THIEU` tín hiệu duy nhất → chưa đủ, KHÔNG đọc dấu."""
    if n < PM.N_TOI_THIEU:
        return KET_CUC_CHUA_DU
    if lo > 0:
        return KET_CUC_A
    if hi < 0:
        return KET_CUC_C
    return KET_CUC_B


def thong_ke(ban_ghi: list[dict], ep: str | None = None, cham: bool = False) -> dict:
    """Thống kê chính: Δ alpha trung bình mỗi tín hiệu duy nhất + KTC 95% theo khối ngày."""
    n = len(ban_ghi)
    if n == 0:
        return {"n": 0, "delta_alpha": None, "ktc": None, "delta_ret": None,
                "ket_cuc": KET_CUC_CHUA_DU, "so_ngay": 0}
    c = chenh(ban_ghi, ep, cham)
    lo, hi = bootstrap_khoi_ngay(c["d_alpha"], c["ngay"])
    tb = float(np.mean(c["d_alpha"]))
    return {"n": n, "so_ngay": len(set(c["ngay"])), "delta_alpha": tb, "ktc": [lo, hi],
            "delta_ret": float(np.mean(c["d_ret"])),
            "ket_cuc": ket_cuc(n, lo, hi),
            "quy_tac_1": tb > NGUONG_QUY_TAC_1}


# ── báo kèm ────────────────────────────────────────────────────────────────────────────────────
def bao_kem(ban_ghi: list[dict]) -> dict:
    """Mọi thứ ĐO 25 cho báo kèm, không quyết định kết cục."""
    n = len(ban_ghi)
    dem = {}
    for b in ban_ghi:
        dem[b["phan_quyet"]] = dem.get(b["phan_quyet"], 0) + 1
    cho = [b for b in ban_ghi if b["phan_quyet"] == KH.CHO_VUNG]
    khop = [b for b in cho if b["lenh_khop"] is not None]
    lo = [b for b in cho if b["lenh_khop"] is None]
    tb = lambda xs, k: float(np.mean([x[k] for x in xs])) if xs else None  # noqa: E731
    tach = {}
    for v in sorted(dem):
        nho = [b for b in ban_ghi if b["phan_quyet"] == v]
        tach[v] = {"n": len(nho),
                   "delta_alpha": float(np.mean(chenh(nho)["d_alpha"]))}
    return {
        "ty_le_phan_quyet": {v: {"n": k, "ty_le": k / n if n else None} for v, k in sorted(dem.items())},
        "cho_vung": {"n": len(cho), "khop": len(khop), "lo": len(lo),
                     "ty_le_khop": len(khop) / len(cho) if cho else None,
                     "ret_nen_nhom_khop": tb(khop, "ret_nen"),
                     "ret_nen_nhom_lo": tb(lo, "ret_nen"),
                     "alpha_nen_nhom_khop": tb(khop, "alpha_nen"),
                     "alpha_nen_nhom_lo": tb(lo, "alpha_nen")},
        "delta_theo_phan_quyet": tach,
        "bien_the_cham_la_khop": thong_ke(ban_ghi, cham=True),
    }


def vni_tren_ma50(vni: pd.DataFrame | None, ngay: str):
    """`True`/`False`/`None` — VN-INDEX tại `ngay` có trên MA50 không (cùng phép so `>=` của bộ lọc).

    Chỉ dùng dữ liệu ≤ ngày. `None` khi không có dữ liệu hoặc chưa đủ 50 phiên (không bịa nhãn).
    """
    if vni is None or len(vni) == 0:
        return None
    d = vni.sort_values("time")
    d = d[d["time"].astype(str).str.slice(0, 10) <= ngay]
    if len(d) < 50:
        return None
    ma = d["close"].astype(float).rolling(50).mean().iloc[-1]
    if pd.isna(ma):
        return None
    return bool(float(d["close"].iloc[-1]) >= float(ma))


def nhom_vni(ban_ghi: list[dict], vni: pd.DataFrame | None) -> dict:
    """Δ theo nhóm VN-INDEX trên/dưới MA50 tại t — chỉ báo kèm."""
    nhom = {"tren_ma50": [], "duoi_ma50": [], "khong_xac_dinh": []}
    for b in ban_ghi:
        v = vni_tren_ma50(vni, b["ngay"])
        nhom["khong_xac_dinh" if v is None else "tren_ma50" if v else "duoi_ma50"].append(b)
    return {k: {"n": len(xs),
                "delta_alpha": float(np.mean(chenh(xs)["d_alpha"])) if xs else None}
            for k, xs in nhom.items()}


# ── đối chứng của máy đo ───────────────────────────────────────────────────────────────────────
def doi_chung_ep(ban_ghi: list[dict]) -> dict:
    """(i) ép luôn MUA_NGAY → Δ ≡ 0 ; (ii) ép luôn BO_QUA → Δ = −alpha nền, từng tín hiệu."""
    if not ban_ghi:
        return {"i": {"dat": False, "ly_do": "không có tín hiệu nào"},
                "ii": {"dat": False, "ly_do": "không có tín hiệu nào"}}
    ci = chenh(ban_ghi, ep=KH.MUA_NGAY)["d_alpha"]
    cii = chenh(ban_ghi, ep=KH.BO_QUA)["d_alpha"]
    alpha_nen = [b["alpha_nen"] for b in ban_ghi]
    i_dat = all(x == 0.0 for x in ci)
    ii_dat = all(x == -a for x, a in zip(cii, alpha_nen))
    # Một đối chứng chỉ có nghĩa khi alpha nền KHÔNG toàn 0 — nếu không (ii) đúng một cách rỗng.
    co_nghia = any(a != 0.0 for a in alpha_nen)
    return {"i": {"dat": i_dat, "delta_alpha_tb": float(np.mean(ci))},
            "ii": {"dat": ii_dat and co_nghia, "co_nghia": co_nghia,
                   "delta_alpha_tb": float(np.mean(cii)),
                   "tru_alpha_nen_tb": -float(np.mean(alpha_nen))}}


def doi_chung_xao_tuong_lai(tin_hieu: list[dict], hat: int = HAT_DOI_CHUNG) -> dict:
    """(iii) xáo các nến SAU t → phán quyết không đổi.

    `tin_hieu`: các dict có `ma`, `df`, `t`, `diem`, `san`, `ke_hoach` (phán quyết đã lập từ df ≤ t).
    Lập LẠI phán quyết qua CHÍNH `lap_ke_hoach_cho_tin_hieu` trên bảng đã xáo phần sau t.
    """
    rng = np.random.default_rng(hat)
    lech, khac_tuong_lai, da_xao = 0, 0, 0
    for s in tin_hieu:
        df, t = s["df"], s["t"]
        if len(df) - (t + 1) < 2:
            continue
        da_xao += 1
        # Xáo giá-khối lượng của các nến sau t, GIỮ NGUYÊN cột ngày (lịch vẫn tăng dần).
        cot = [df.columns.get_loc(c) for c in df.columns if c != "time"]
        goc_gia = df.iloc[t + 1:, cot].to_numpy()
        gia_xao = goc_gia[rng.permutation(len(goc_gia))]
        df2 = df.copy()
        df2.iloc[t + 1:, cot] = gia_xao
        if not np.array_equal(gia_xao, goc_gia):
            khac_tuong_lai += 1
        if lap_ke_hoach_cho_tin_hieu(df2, t, s["diem"], s["san"]) != s["ke_hoach"]:
            lech += 1
    dat = lech == 0 and khac_tuong_lai > 0
    return {"dat": dat, "so_tin_hieu": da_xao, "so_lech": lech,
            "so_lan_tuong_lai_that_su_doi": khac_tuong_lai}


# ── chạy ───────────────────────────────────────────────────────────────────────────────────────
def thu_thap_tin_hieu(vung_oos: dict, cham_diem, stride: int, min_history: int,
                      tu: str | None = None, den: str | None = None):
    """Quét lịch "theo ngày", độ trễ khớp 1, chỉ các phiên QUYẾT ĐỊNH (bỏ phiên chỉ-khớp).

    Trả `(tin_hieu, thong_ke_quan_sat)`: mỗi tín hiệu là dict có `ma`, `df`, `t`, `diem`, `san`,
    `ke_hoach`. Tín hiệu = điểm ≥ ngưỡng đã ký. `tu`/`den` lọc theo ngày t (gồm hai đầu).
    """
    tin_hieu, so_cham = [], 0
    for ngay, ma, t, chi_khop in WF.lich_theo_ngay(vung_oos, min_history, stride, 1):
        if chi_khop or (tu and ngay < tu) or (den and ngay > den):
            continue
        df = vung_oos[ma]
        diem = cham_diem(ma, df.iloc[: t + 1], ngay)
        so_cham += 1
        if diem < NGUONG_DA_KY:
            continue
        san = san_giao_dich.san_cua(ma)
        tin_hieu.append({"ma": ma, "df": df, "t": t, "diem": diem, "san": san,
                         "ke_hoach": lap_ke_hoach_cho_tin_hieu(df, t, diem, san)})
    return tin_hieu, {"so_phien_cham": so_cham}


def do_tin_hieu(tin_hieu: list[dict], tap_du_lieu: dict, vni: pd.DataFrame | None = None) -> dict:
    """Từ danh sách tín hiệu tới bảng kết quả: ban ghi → khử trùng → alpha → thống kê → đối chứng."""
    tho, bo_tuong_lai = [], 0
    for s in tin_hieu:
        b = ban_ghi_tin_hieu(s["ma"], s["df"], s["t"], s["diem"], s["san"], s["ke_hoach"])
        if b is None:
            bo_tuong_lai += 1
        else:
            tho.append(b)
    tho, so_trung = khu_trung(tho)
    ban_ghi, bo_chuan = gan_alpha(tho, tap_du_lieu)
    chinh = thong_ke(ban_ghi)
    return {
        "so_tin_hieu_dat_nguong": len(tin_hieu),
        "bo_vi_thieu_tuong_lai": bo_tuong_lai,
        "bo_vi_trung": so_trung,
        "bo_vi_thieu_chuan": bo_chuan,
        "chinh": chinh,
        "bao_kem": bao_kem(ban_ghi) if ban_ghi else None,
        "vni": nhom_vni(ban_ghi, vni) if ban_ghi else None,
        "doi_chung": {"ep": doi_chung_ep(ban_ghi),
                      "xao_tuong_lai": doi_chung_xao_tuong_lai(tin_hieu)},
    }


def doi_chung_dat(kq: dict) -> bool:
    dc = kq["doi_chung"]
    return bool(dc["ep"]["i"]["dat"] and dc["ep"]["ii"]["dat"] and dc["xao_tuong_lai"]["dat"])


# ── in bảng ────────────────────────────────────────────────────────────────────────────────────
def _so(x, nd=2, dau=True):
    return "—" if x is None else (f"{x:+.{nd}f}" if dau else f"{x:.{nd}f}")


def dong_bao_cao(kq: dict, m0: dict | None = None) -> list[str]:
    """Bảng kết cục ĐÚNG khuôn ĐO 25 — chỉ in số đã tính, không diễn giải thêm."""
    d = []
    if m0:
        d += ["── M0 ───────────────────────────────────────────────────────────────",
              f"  cache: {m0['cache']['so_file']} file · sha256 {m0['cache']['sha256'][:16]}…"
              f" · mtime {m0['cache']['mtime_nho_nhat']} → {m0['cache']['mtime_lon_nhat']}",
              f"  ke_hoach_vao_lenh.py so với {COMMIT_KE_HOACH}: {m0['ma_ke_hoach']}",
              f"  ngưỡng mua {m0['nguong_mua']} (đã ký {NGUONG_DA_KY}) · chế độ học {m0['che_do_hoc']}"
              f" ({m0.get('mau_bo_nho')} mẫu) · stride {m0['stride']} · min_history {m0['min_history']}"]
    c = kq["chinh"]
    d += ["── QUẦN THỂ ─────────────────────────────────────────────────────────",
          f"  tín hiệu đạt ngưỡng: {kq['so_tin_hieu_dat_nguong']}"
          f" · bỏ vì thiếu {KHUNG_H} phiên về sau: {kq['bo_vi_thieu_tuong_lai']}"
          f" · bỏ vì trùng (mã, t): {kq['bo_vi_trung']} · bỏ vì thiếu chuẩn: {kq['bo_vi_thieu_chuan']}",
          f"  N duy nhất: {c['n']} trong {c['so_ngay']} ngày (tối thiểu {PM.N_TOI_THIEU})"]
    if c["n"] == 0:
        return d + ["  KẾT CỤC: " + KET_CUC_CHUA_DU]
    d += ["── THỐNG KÊ CHÍNH ─────────────────────────────────────────────────",
          f"  Δ alpha trung bình mỗi tín hiệu (B6 − nền): {_so(c['delta_alpha'])} điểm %"
          f"   KTC 95% [{_so(c['ktc'][0])} ; {_so(c['ktc'][1])}]"
          f"   (bootstrap khối ngày, {SO_LUOT_BOOTSTRAP} lượt, hạt {HAT_BOOTSTRAP})",
          f"  KẾT CỤC KÝ TRƯỚC: {c['ket_cuc']}"]
    if c.get("quy_tac_1"):
        d.append(f"  ⚠️ QUY TẮC 1: Δ trung bình > +{NGUONG_QUY_TAC_1:g} điểm — soát nhìn trộm (df ≤ t), "
                 f"giá khớp, chi phí, khử trùng, đơn vị giá TRƯỚC khi đọc kết cục.")
    bk = kq.get("bao_kem")
    if bk:
        d.append("── BÁO KÈM (không quyết định kết cục) ───────────────────────────────")
        d.append(f"  chênh lợi nhuận sau chi phí, chưa trừ chuẩn: {_so(c['delta_ret'])} điểm %/tín hiệu")
        d.append("  tỷ lệ phán quyết: " + " · ".join(
            f"{v} {x['n']} ({x['ty_le'] * 100:.1f}%)" for v, x in bk["ty_le_phan_quyet"].items()))
        cv = bk["cho_vung"]
        d.append(f"  CHO_VUNG: {cv['n']} tín hiệu, khớp {cv['khop']} ({_so(None if cv['ty_le_khop'] is None else cv['ty_le_khop'] * 100, 1, False)}%), lỡ {cv['lo']}")
        d.append(f"  r nền trung bình, nhóm CHO_VUNG KHỚP {_so(cv['ret_nen_nhom_khop'])}% · nhóm LỠ {_so(cv['ret_nen_nhom_lo'])}%"
                 f"   (alpha nền: {_so(cv['alpha_nen_nhom_khop'])} · {_so(cv['alpha_nen_nhom_lo'])})")
        d.append("  Δ theo phán quyết: " + " · ".join(
            f"{v} n={x['n']} {_so(x['delta_alpha'])}" for v, x in bk["delta_theo_phan_quyet"].items()))
        ch = bk["bien_the_cham_la_khop"]
        d.append(f"  biến thể chạm-là-khớp: Δ {_so(ch['delta_alpha'])}   KTC [{_so(ch['ktc'][0])} ; {_so(ch['ktc'][1])}]")
    if kq.get("vni"):
        d.append("  nhóm VN-INDEX tại t: " + " · ".join(
            f"{k} n={x['n']} Δ {_so(x['delta_alpha'])}" for k, x in kq["vni"].items()))
    dc = kq["doi_chung"]
    d += ["── ĐỐI CHỨNG CỦA MÁY ĐO (cùng lượt) ────────────────────────────────",
          f"  (i)   ép luôn MUA_NGAY → Δ ≡ 0: {'ĐẠT' if dc['ep']['i']['dat'] else 'TRƯỢT'}",
          f"  (ii)  ép luôn BO_QUA → Δ = −alpha nền: {'ĐẠT' if dc['ep']['ii']['dat'] else 'TRƯỢT'}"
          f" (Δ tb {_so(dc['ep']['ii'].get('delta_alpha_tb'))} so với −alpha nền tb {_so(dc['ep']['ii'].get('tru_alpha_nen_tb'))})",
          f"  (iii) xáo nến sau t → phán quyết không đổi: {'ĐẠT' if dc['xao_tuong_lai']['dat'] else 'TRƯỢT'}"
          f" ({dc['xao_tuong_lai']['so_lech']} lệch / {dc['xao_tuong_lai']['so_tin_hieu']} tín hiệu)"]
    if not doi_chung_dat(kq):
        d.append("  ⛔ ĐỐI CHỨNG TRƯỢT — máy đo hỏng, KHÔNG đọc kết cục ở trên.")
    return d


# ── dữ liệu tổng hợp cho `doi-chung` ───────────────────────────────────────────────────────────
def chuoi_tong_hop(n: int = 220, gia0: float = 30.0, hat: int = 1) -> pd.DataFrame:
    """Bảng OHLCV tổng hợp xác định (hạt cố định) — chỉ để chạy đối chứng, KHÔNG phải dữ liệu thật."""
    rng = np.random.default_rng(hat)
    dong = gia0 * np.exp(np.cumsum(rng.normal(0.0004, 0.014, n)))
    mo = np.concatenate([[gia0], dong[:-1]]) * (1 + rng.normal(0, 0.004, n))
    cao = np.maximum(mo, dong) * (1 + np.abs(rng.normal(0, 0.006, n)))
    thap = np.minimum(mo, dong) * (1 - np.abs(rng.normal(0, 0.006, n)))
    ngay = pd.bdate_range("2022-01-03", periods=n).strftime("%Y-%m-%d")
    return pd.DataFrame({"time": ngay, "open": np.round(mo, 2), "high": np.round(cao, 2),
                         "low": np.round(thap, 2), "close": np.round(dong, 2),
                         "volume": rng.integers(100_000, 900_000, n).astype(float)})


def doi_chung_tong_hop(so_ma: int = 6, stride: int = 2, min_history: int = 60) -> dict:
    """Chạy cả ba đối chứng trên dữ liệu tổng hợp, qua CHÍNH `thu_thap_tin_hieu` + `do_tin_hieu`.

    Điểm giả: 70 cho mọi phiên (≥ ngưỡng) — đối chứng kiểm máy đo, không kiểm máy chấm điểm.
    """
    vung = {f"S{i}": chuoi_tong_hop(hat=i + 1, gia0=20.0 + 7 * i) for i in range(so_ma)}
    tin_hieu, _ = thu_thap_tin_hieu(vung, lambda ma, ls, ngay: 70.0, stride, min_history)
    kq = do_tin_hieu(tin_hieu, vung)
    kq["tong_hop"] = {"so_ma": so_ma, "stride": stride, "min_history": min_history}
    return kq


# ── dòng lệnh ──────────────────────────────────────────────────────────────────────────────────
def lenh_doi_chung(a) -> int:
    kq = doi_chung_tong_hop()
    print("── ĐỐI CHỨNG TRÊN DỮ LIỆU TỔNG HỢP (không phải dữ liệu thật) ────────")
    for dong in dong_bao_cao(kq):
        print(dong)
    pq = kq["bao_kem"]["ty_le_phan_quyet"] if kq.get("bao_kem") else {}
    ten = ", ".join(k + "=" + str(v["n"]) for k, v in pq.items())
    print("  phán quyết trong bộ tổng hợp: " + ten)
    return 0 if doi_chung_dat(kq) else 1


def lenh_chay(a) -> int:
    mac_dinh = mac_dinh_walkforward()
    stride = a.stride or mac_dinh["stride"]
    min_history = a.min_history or mac_dinh["min_history"]
    che_do_hoc = a.che_do_hoc or mac_dinh["che_do_hoc"]
    if PT.BUY_THRESHOLD != NGUONG_DA_KY:
        print(f"DỪNG: paper_trading.BUY_THRESHOLD = {PT.BUY_THRESHOLD}, ĐO 25 ký {NGUONG_DA_KY}.", file=sys.stderr)
        return 1
    ma_kh = kiem_ma_ke_hoach()
    if ma_kh != "khop":
        print(f"DỪNG: ke_hoach_vao_lenh.py so với {COMMIT_KE_HOACH} = {ma_kh} "
              f"(ĐO 25 đo ĐÚNG mã ở commit ấy).", file=sys.stderr)
        return 1 if ma_kh == "lech" else 2
    cache = Path(a.cache)
    bam = bam_thu_muc(cache)
    if bam["so_file"] == 0:
        print(f"DỪNG: {cache} không có file csv nào.", file=sys.stderr)
        return 2
    if a.bam_mong_doi and a.bam_mong_doi != bam["sha256"]:
        print(f"DỪNG (M0): băm cache {bam['sha256']} ≠ băm mong đợi {a.bam_mong_doi}.", file=sys.stderr)
        return 1
    from vn100_symbols import CUSTOM_WATCHLIST_SYMBOLS
    symbols = a.symbols.split(",") if a.symbols else CUSTOM_WATCHLIST_SYMBOLS
    with dat_cache(cache) as BD:
        tat_ca = BD.load_all(symbols)
        vni = BD.load("VNINDEX")
    vung_oos = dung_vung_oos(tat_ca, WF.nap_moc_sach(), min_history)
    with moi_truong_cham_diem(che_do_hoc) as may:
        mau = len(may.sl_patterns)
        tin_hieu, quan_sat = thu_thap_tin_hieu(vung_oos, cham_diem_that, stride, min_history,
                                               a.tu, a.den)
    kq = do_tin_hieu(tin_hieu, vung_oos, vni)
    m0 = {"cache": bam, "ma_ke_hoach": ma_kh, "nguong_mua": PT.BUY_THRESHOLD,
          "che_do_hoc": che_do_hoc, "mau_bo_nho": mau, "stride": stride,
          "min_history": min_history, "so_ma_oos": len(vung_oos), **quan_sat}
    for dong in dong_bao_cao(kq, m0):
        print(dong)
    ra = {"m0": m0, "ket_qua": kq,
          "ghi_chu": "ĐO 25 — số tính trong phiên này; đọc theo bảng đã ký ở docs/TIEU-CHI-DOC-TRUOC.md"}
    Path(a.ghi).write_text(json.dumps(ra, ensure_ascii=False, indent=2, default=str) + "\n",
                           encoding="utf-8")
    print(f"đã ghi {a.ghi}")
    return 0 if doi_chung_dat(kq) else 1


def main(argv=None) -> int:
    for luong in (sys.stdout, sys.stderr):
        try:
            luong.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="lenh", required=True)
    sub.add_parser("doi-chung", help="ba đối chứng của máy đo trên dữ liệu tổng hợp")
    c = sub.add_parser("chay", help="đo thật trên cache")
    c.add_argument("--cache", required=True, help="thư mục cache giá (backtest/cache)")
    c.add_argument("--ghi", required=True, help="đường dẫn JSON kết quả (người gọi chọn)")
    c.add_argument("--tu", help="chỉ tín hiệu có ngày t >= YYYY-MM-DD")
    c.add_argument("--den", help="chỉ tín hiệu có ngày t <= YYYY-MM-DD")
    c.add_argument("--symbols", help="danh sách mã, cách nhau bằng dấu phẩy (mặc định: rổ của walkforward)")
    c.add_argument("--stride", type=int, help="mặc định = walkforward.chay")
    c.add_argument("--min-history", type=int, dest="min_history", help="mặc định = walkforward.chay")
    c.add_argument("--che-do-hoc", choices=("tat", "co_san"), dest="che_do_hoc",
                   help="mặc định = walkforward.chay")
    c.add_argument("--bam-mong-doi", dest="bam_mong_doi",
                   help="sha256 cache đã ghi ở lượt trước; lệch thì DỪNG (M0)")
    a = ap.parse_args(argv)
    return lenh_doi_chung(a) if a.lenh == "doi-chung" else lenh_chay(a)


if __name__ == "__main__":
    sys.exit(main())
