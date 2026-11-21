"""Bảng sự thật (oracle) của Tầng 2 — ΔIC_true chấm bằng `paper_runner._analyze` THẬT (C4, BƯỚC 293, mục 19).

Đề bài: `docs/thiet-ke-c4-thi-truong-gia.md` mục 4.5 (oracle Tầng 1), 18 khoản 10 và 12c (vì sao cần bản Tầng 2) và
mục 19. Đặc tả là nguồn duy nhất; đừng chép nó vào đây.

CÂU HỎI. Ở Tầng 1 oracle chấm ΔIC_true của từng spec bằng các thành phần SINH THẲNG (`thi_truong_gia.tinh_su_that`). Ở
Tầng 2 điểm và thành phần do agent thật tính từ khung OHLCV, mà kỳ vọng cài sẵn `κ·z/21` nằm trong GIÁ (khoản 10 của
mục 18: `trend` và `sr` đọc được nó). Vậy ΔIC_true của G · Z · H, và của mọi spec trong họ F, ở Tầng 2 là bao nhiêu?

CÁCH ĐO (đối xứng với oracle Tầng 1, chỉ khác phần chấm điểm)
  * MỘT mẫu dài CÙNG tham số, hạt RIÊNG `[luong, chi_so, HAT_ORACLE_2]` (Tầng 1: `[luong, chi_so, 1]`; phần tử thứ ba
    khác nên không trùng mẫu oracle Tầng 1 nào), qua `thi_truong_gia_tang2.sinh_thi_truong_2` (cùng bộ sinh khung OHLCV).
  * Chấm bằng `thi_truong_gia_tang2.cham_diem_theo_ma` — CHÍNH đường `cham_diem` dùng (`paper_runner._analyze` thật, lịch
    sử cắt tới từng phiên) — kèm CỬA SỔ TRƯỢT `CUA_SO_CHAM` dòng (= 250 khởi động + dòng thời gian Tầng 2 = lịch sử dài
    nhất một thị trường thật của Tầng 2 từng thấy): đường quét thật cũng chỉ giữ ~784 phiên, và chi phí một lần chấm tăng
    theo độ dài lịch sử (đo ở STATE BƯỚC 293). Trong `CUA_SO_CHAM − 250` phiên đầu cửa sổ là lịch sử MỞ RỘNG y như thị trường.
  * Điểm đã ghi = `int(final_score)` (đúng cột `score` của `dong_quyet_dinh`); thành phần = `score_breakdown`.
  * ΔIC_true của mọi spec của `thi_truong_gia.ho_spec_oracle` (11 spec của F + Z) so với điểm đã ghi, bằng `E.rho_hang`
    và `E.nhan_vuot_ro`; sai số Monte Carlo = độ lệch chuẩn giữa `so_khoi` khối phiên liền nhau / √so_khoi, ĐÚNG công thức
    của `tinh_su_that` (ước lượng; có test so từng số với `tinh_su_that` trên cùng một mẫu Tầng 1).
  * Thêm: IC của từng thành phần VÀ của điểm cuối, mỗi cái đứng riêng, với nhãn (cùng sai số khối).
  * Nhiều mẫu độc lập → `gop_mau`: ΔIC trung bình, sai số = √(Σ se²)/k (các mẫu độc lập).

CHỈ DÒNG HẠT 1 VÀ 9001, qua cửa `kiem_luong` của `chay_vong_thi_truong_gia` (dòng 2 · 3 · 4 · 5 bị chặn). Dòng 9001 là
dòng thử: số đo ở đây dùng để THIẾT KẾ, không phải kết quả T6. Công cụ KHÔNG ghi file nào; muốn lưu thì chuyển hướng đầu ra.

CHẠY
    ./.venv/Scripts/python.exe -X utf8 tools/oracle_tang2_thi_truong_gia.py --luong 9001 --muc 2 --so-phien 5000 --so-mau 2 --chi-so-dau 101 --so-tien-trinh 12
    ./.venv/Scripts/python.exe -X utf8 tools/oracle_tang2_thi_truong_gia.py --luong 9001 --muc 0 --so-phien 300 --so-ma-cham 6   # lát nhỏ

`--muc` lấy κ của mức 0× · 0,5× · 1× · 2× MDE₈₀ từ `docs/thi-truong-gia-hieu-chuan.json` (Lát 2, đo ở Tầng 1); `--kappa` đặt thẳng.
Mã thoát: 0 chạy xong · 2 lỗi cấu hình (dòng hạt cấm, đối số sai). KHÔNG phán đạt/trượt tiêu chí nào của mục 6.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import platform
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

for _luong_ra in (sys.stdout, sys.stderr):   # BƯỚC 129
    try:
        _luong_ra.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

GOC = Path(__file__).resolve().parent.parent
DUONG_CONG_CU = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))
sys.path.append(str(DUONG_CONG_CU))

import cham_bong as cb  # noqa: E402
import experiment_tran_dac_trung as E  # noqa: E402
import thi_truong_gia as T  # noqa: E402
import thi_truong_gia_tang2 as G  # noqa: E402
from chay_vong_thi_truong_gia import LUONG_TEST, doc_kappa_muc, kiem_luong  # noqa: E402

#: Phần tử thứ ba của hạt mẫu bảng sự thật Tầng 2: `[luong, chi_so, HAT_ORACLE_2]`. Tầng 1 dùng `T.HAT_SU_THAT` (= 1); KHÁC.
HAT_ORACLE_2 = 2
SO_PHIEN_MAC_DINH = T.SO_PHIEN_SU_THAT          # 5.000 phiên có quyết định mỗi mẫu, như Tầng 1
#: Cửa sổ trượt của lượt chấm: lịch sử dài nhất mà một thị trường Tầng 2 (khởi động + dòng thời gian) từng đưa cho `_analyze`.
CUA_SO_CHAM = G.SO_PHIEN_KHOI_DONG + G.dong_thoi_gian_2()["tong"]
TEN_BO_BA = {"G": T.TEN_SPEC_G, "Z": T.TEN_SPEC_Z, "H": T.TEN_SPEC_H}


# ── chấm một mã (việc của một tiến trình) ────────────────────────────────────

def _viec_cham_ma(a):
    """`(tt một mã, mã, cửa sổ)` → `(mã, điểm nguyên, thành phần, số dòng data_quality ≠ OK)`. Đi qua `cham_diem_theo_ma`."""
    tt, ma, cua_so = a
    kq = G.cham_diem_theo_ma(tt, ma, cua_so=cua_so)
    diem = np.array([int(r["final_score"]) for r in kq], dtype=np.int64)    # `int()` như cột `score` của `dong_quyet_dinh`
    tp = {k: np.array([float(r["score_breakdown"][k]) for r in kq]) for k in cb.THANH_PHAN}
    return ma, diem, tp, sum(1 for r in kq if r["data_quality"] != "OK")


def _map(pool, ham, ds: list) -> list:
    """Theo ĐÚNG thứ tự đầu vào, bất kể số tiến trình."""
    if pool is None:
        return [ham(a) for a in ds]
    return list(pool.map(ham, ds, chunksize=1))


def sinh_mau(luong: int, chi_so: int, kappa: float, so_phien: int, so_khoi_dong: int = G.SO_PHIEN_KHOI_DONG):
    """Mẫu Tầng 2 của bảng sự thật: hạt `[luong, chi_so, HAT_ORACLE_2]`. Qua `kiem_luong` TRƯỚC khi sinh."""
    kiem_luong(luong)
    return G.sinh_thi_truong_2(luong, chi_so, float(kappa), so_phien=int(so_phien), so_khoi_dong=so_khoi_dong,
                               hat_them=HAT_ORACLE_2)


def cham_mau(tt, ma=None, cua_so: int | None = CUA_SO_CHAM, pool=None) -> dict:
    """Chấm các mã `ma` (mặc định cả 60) của mẫu `tt`, mỗi mã một việc. Trả `diem` (phiên × mã, nguyên),
    `thanh_phan` (tên → phiên × mã), `ma`, `khong_ok` (số dòng `data_quality` ≠ OK)."""
    ds = tt.ma if ma is None else tuple(ma)
    viec = [(dataclasses.replace(tt, gia={m: tt.gia[m]}), m, cua_so) for m in ds]
    return _gop_ket_qua(ds, _map(pool, _viec_cham_ma, viec))


def _gop_ket_qua(ds, ket_qua: list) -> dict:
    theo_ma = {m: (d, tp, k) for m, d, tp, k in ket_qua}
    return {"ma": tuple(ds), "diem": np.stack([theo_ma[m][0] for m in ds], axis=1),
            "thanh_phan": {k: np.stack([theo_ma[m][1][k] for m in ds], axis=1) for k in cb.THANH_PHAN},
            "khong_ok": int(sum(theo_ma[m][2] for m in ds))}


# ── ΔIC_true (cùng công thức với `thi_truong_gia.tinh_su_that`) ──────────────

def nhan_cua_mau(tt) -> np.ndarray:
    """Nhãn `E.nhan_vuot_ro` trên GIÁ của mọi mã của mẫu (rổ = mọi mã), cắt bỏ phần khởi động: hàng k ↔ phiên có quyết định k."""
    kh = {m: pd.DataFrame({"close": df["close"].to_numpy()}) for m, df in tt.gia.items()}
    return E.nhan_vuot_ro(kh, cb.NHIP).to_numpy()[tt.so_khoi_dong:]


def bang_su_that(thanh_phan: dict, diem: np.ndarray, nhan: np.ndarray, so_khoi: int = T.SO_KHOI_SU_THAT) -> dict:
    """ΔIC_true của từng spec của `T.ho_spec_oracle()` so với `diem`, và IC đứng riêng của từng thành phần + điểm cuối.
    Đầu vào đã căn hàng (hàng k = phiên có quyết định k). `T.tinh_su_that` làm CÙNG phép tính trên thành phần sinh thẳng;
    hàm này khác nó đúng ở chỗ đầu vào, và (ngoài `spec`) thêm `ic_rieng`."""
    co = ~np.isnan(nhan).any(axis=1)
    so_co = int(co.sum())
    assert co[:so_co].all() and not co[so_co:].any(), "nhãn phải có ở đoạn đầu và chỉ thiếu ở đuôi"
    nhan = nhan[:so_co]
    b = diem[:so_co].astype(float)
    cat = np.array_split(np.arange(so_co), so_khoi)
    ic_b = E.rho_hang(b.ravel(), nhan.ravel())
    ic_b_khoi = [E.rho_hang(b[i].ravel(), nhan[i].ravel()) for i in cat]
    spec = {}
    for ten, sp in T.ho_spec_oracle().items():
        c = T.diem_spec(sp, {k: v[:so_co] for k, v in thanh_phan.items()})
        theo_khoi = np.array([E.rho_hang(c[i].ravel(), nhan[i].ravel()) - ic_b_khoi[j] for j, i in enumerate(cat)])
        spec[ten] = {"delta_ic": E.rho_hang(c.ravel(), nhan.ravel()) - ic_b,
                     "se_mc": float(theo_khoi.std(ddof=1) / np.sqrt(so_khoi))}
    ic_rieng = {}
    for ten in (*cb.THANH_PHAN, "score"):
        x = b if ten == "score" else thanh_phan[ten][:so_co].astype(float)
        theo_khoi = np.array([E.rho_hang(x[i].ravel(), nhan[i].ravel()) for i in cat])
        ic_rieng[ten] = {"ic": E.rho_hang(x.ravel(), nhan.ravel()),
                         "se_mc": float(theo_khoi.std(ddof=1) / np.sqrt(so_khoi))}
    return {"so_phien_co_nhan": so_co, "so_khoi": so_khoi, "spec": spec, "ic_rieng": ic_rieng}


def gop_mau(mau: list[dict]) -> dict:
    """Gộp k mẫu độc lập của CÙNG mức: trung bình, sai số = √(Σ se²)/k (độc lập); `sd_giua_mau` (k ≥ 2) là độ lệch chuẩn
    thực giữa các mẫu / √k, để so với sai số khối. Trả `{spec: {delta_ic, se, sd_giua_mau}, ic_rieng: {...}}`."""
    k = len(mau)

    def tong_hop(lay):
        x = np.array([lay(m) for m in mau])
        return x

    ra = {"so_mau": k, "spec": {}, "ic_rieng": {}}
    for ten in mau[0]["spec"]:
        d = tong_hop(lambda m: m["spec"][ten]["delta_ic"])
        s = tong_hop(lambda m: m["spec"][ten]["se_mc"])
        ra["spec"][ten] = {"delta_ic": float(d.mean()), "se": float(np.sqrt((s ** 2).sum()) / k),
                           "sd_giua_mau": float(d.std(ddof=1) / np.sqrt(k)) if k >= 2 else None}
    for ten in mau[0]["ic_rieng"]:
        d = tong_hop(lambda m: m["ic_rieng"][ten]["ic"])
        s = tong_hop(lambda m: m["ic_rieng"][ten]["se_mc"])
        ra["ic_rieng"][ten] = {"ic": float(d.mean()), "se": float(np.sqrt((s ** 2).sum()) / k),
                               "sd_giua_mau": float(d.std(ddof=1) / np.sqrt(k)) if k >= 2 else None}
    return ra


def spec_ngoai_hai_se_gop(gop: dict, he_so: float = 2.0) -> list[str]:
    """Tên spec có |ΔIC_true| ≥ `he_so` · sai số của mẫu gộp. Ở NULL, mục 4.5(c) đòi rỗng (xem mục 15 khoản 8 về tỷ lệ báo nhầm)."""
    return sorted(t for t, v in gop["spec"].items() if abs(v["delta_ic"]) >= he_so * v["se"])


# ── nhiều mẫu cùng một lúc (cân tải tốt hơn) ─────────────────────────────────

def tinh_nhieu_mau(luong: int, chi_so_ds: list[int], kappa: float, so_phien: int, ma=None,
                   cua_so: int | None = CUA_SO_CHAM, pool=None, so_khoi: int = T.SO_KHOI_SU_THAT, tien_do=None) -> list[dict]:
    """k mẫu độc lập (mỗi `chi_so` một mẫu) cùng một mức κ; mọi việc (mã × mẫu) dồn vào MỘT hàng đợi để các tiến trình không rỗi.
    Kết quả KHÔNG phụ thuộc số tiến trình (có test)."""
    t0 = time.perf_counter()
    mau = [sinh_mau(luong, c, kappa, so_phien) for c in chi_so_ds]
    ds = mau[0].ma if ma is None else tuple(ma)
    viec = [(dataclasses.replace(tt, gia={m: tt.gia[m]}), m, cua_so) for tt in mau for m in ds]
    if pool is None:
        kq = []
        for i, a in enumerate(viec, 1):
            kq.append(_viec_cham_ma(a))
            if tien_do:
                tien_do(i, len(viec), time.perf_counter() - t0)
    else:
        kq = []
        for i, r in enumerate(pool.map(_viec_cham_ma, viec, chunksize=1), 1):
            kq.append(r)
            if tien_do:
                tien_do(i, len(viec), time.perf_counter() - t0)
    ra = []
    for j, (c, tt) in enumerate(zip(chi_so_ds, mau)):
        cham = _gop_ket_qua(ds, kq[j * len(ds):(j + 1) * len(ds)])
        nhan = nhan_cua_mau(tt)
        cot = [tt.ma.index(m) for m in cham["ma"]]
        r = bang_su_that(cham["thanh_phan"], cham["diem"], nhan[:, cot], so_khoi)
        r.update({"kappa": float(kappa), "so_phien": int(so_phien), "so_ma": len(ds), "so_lan_cham": int(cham["diem"].size),
                  "khong_ok": cham["khong_ok"], "cua_so": cua_so, "hat": [int(luong), int(c), HAT_ORACLE_2]})
        ra.append(r)
    return ra


# ── in ───────────────────────────────────────────────────────────────────────

def bien_ban(gop: dict, kappa: float, muc: float | None, luong: int, chi_so_ds: list[int], giay: float, so_lan: int,
             so_tien_trinh: int, so_phien: int, so_ma: int) -> list[str]:
    ra = [f"BẢNG SỰ THẬT TẦNG 2 — dòng hạt {luong}, chỉ số {chi_so_ds}, hạt thứ ba {HAT_ORACLE_2}, κ = {kappa:.6f}"
          + ("" if muc is None else f" (mức {muc}× MDE₈₀ của Tầng 1)"),
          f"  {gop['so_mau']} mẫu × {so_phien} phiên × {so_ma} mã, cửa sổ chấm {CUA_SO_CHAM} dòng; {so_lan} lần `_analyze` "
          f"trong {giay:.0f} s ({giay / max(so_lan, 1) * 1000 * max(so_tien_trinh, 1):.1f} ms CPU-tường mỗi lần ở {so_tien_trinh} tiến trình); "
          f"Python {platform.python_version()}, {os.cpu_count()} lõi logic",
          "", "ΔIC_true so với điểm đã ghi (sai số Monte Carlo = khối):"]
    for ten, v in gop["spec"].items():
        gan = " ".join(k for k, t in TEN_BO_BA.items() if t == ten)
        ra.append(f"  {ten:<20} {v['delta_ic']:+.4f} ± {v['se']:.4f}   {gan}")
    ra += ["", "IC đứng riêng với nhãn:"]
    for ten, v in gop["ic_rieng"].items():
        ra.append(f"  {ten:<20} {v['ic']:+.4f} ± {v['se']:.4f}")
    return ra


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--luong", type=int, default=LUONG_TEST, help="dòng hạt: chỉ 1 hoặc 9001")
    nhom = ap.add_mutually_exclusive_group()
    nhom.add_argument("--muc", type=float, default=None, help="hệ số MDE₈₀ của file hiệu chuẩn: 0 · 0.5 · 1 · 2")
    nhom.add_argument("--kappa", type=float, default=None)
    ap.add_argument("--so-phien", type=int, default=SO_PHIEN_MAC_DINH, help="số phiên có quyết định mỗi mẫu")
    ap.add_argument("--so-mau", type=int, default=1)
    ap.add_argument("--chi-so-dau", type=int, default=1, help="chỉ số của mẫu đầu; mẫu j dùng chi_so_dau + j")
    ap.add_argument("--so-ma-cham", type=int, default=None, help="chỉ chấm N mã đầu (lát nhỏ; mặc định cả 60)")
    ap.add_argument("--cua-so", type=int, default=CUA_SO_CHAM, help="số dòng lịch sử cuối cùng đưa cho `_analyze`; 0 = mở rộng")
    ap.add_argument("--so-tien-trinh", type=int, default=1)
    ap.add_argument("--tien-do", action="store_true")
    ap.add_argument("--json", action="store_true", help="in thêm MỘT dòng `KET_QUA_JSON {...}`")
    a = ap.parse_args(argv)
    try:
        kiem_luong(a.luong)
        if a.so_mau < 1 or a.so_phien < 100 or a.so_tien_trinh < 1:
            raise ValueError("so_mau >= 1, so_phien >= 100, so_tien_trinh >= 1")
        kappa = a.kappa if a.kappa is not None else doc_kappa_muc(2.0 if a.muc is None else a.muc)
        chi_so_ds = [a.chi_so_dau + j for j in range(a.so_mau)]
        ma = None if a.so_ma_cham is None else T._ma_gia()[: a.so_ma_cham]
        cua_so = None if a.cua_so == 0 else a.cua_so
        td = (lambda i, n, s: print(f"  {i}/{n} việc xong sau {s:.0f} s", file=sys.stderr, flush=True) if i % 10 == 0 or i == n else None) \
            if a.tien_do else None
        t0 = time.perf_counter()
        if a.so_tien_trinh > 1:
            with ProcessPoolExecutor(max_workers=a.so_tien_trinh) as pool:
                mau = tinh_nhieu_mau(a.luong, chi_so_ds, kappa, a.so_phien, ma, cua_so, pool, tien_do=td)
        else:
            mau = tinh_nhieu_mau(a.luong, chi_so_ds, kappa, a.so_phien, ma, cua_so, None, tien_do=td)
        giay = time.perf_counter() - t0
    except ValueError as e:
        print(f"LỖI: {e}", file=sys.stderr)
        return 2
    gop = gop_mau(mau)
    so_lan = sum(m["so_lan_cham"] for m in mau)
    print("\n".join(bien_ban(gop, kappa, a.muc, a.luong, chi_so_ds, giay, so_lan, a.so_tien_trinh, a.so_phien, mau[0]["so_ma"])))
    print(f"  data_quality ≠ OK: {sum(m['khong_ok'] for m in mau)} dòng")
    ngoai = spec_ngoai_hai_se_gop(gop)
    print(f"  spec có |ΔIC_true| ≥ 2 sai số (mẫu gộp): {ngoai or 'không có'}")
    if a.json:
        print("KET_QUA_JSON " + json.dumps({"luong": a.luong, "chi_so": chi_so_ds, "muc": a.muc, "kappa": kappa,
              "so_phien": a.so_phien, "so_ma": mau[0]["so_ma"], "cua_so": cua_so, "so_tien_trinh": a.so_tien_trinh,
              "giay": giay, "so_lan_cham": so_lan, "khong_ok": sum(m["khong_ok"] for m in mau), "gop": gop,
              "tung_mau": [{k: v for k, v in m.items()} for m in mau]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
