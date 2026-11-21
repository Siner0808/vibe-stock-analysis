"""`chay-vong-tang2` — chạy vòng học (`vong_hoc_gia.chay_vong`) trên MỘT thị trường Tầng 2 và ĐO chi phí của nó (C4, BƯỚC 293, việc (b)).

Đề bài: `docs/thiet-ke-c4-thi-truong-gia.md` mục 18 khoản 12b (chi phí của vòng trên Tầng 2 chưa đo) và mục 19. Đặc tả là nguồn duy nhất.

MỘT thị trường Tầng 2, dòng hạt 1 hay 9001 (qua cửa `kiem_luong`): sinh khung OHLCV (605 phiên có quyết định + 250 khởi động) →
chấm 60 mã bằng `paper_runner._analyze` thật (`thi_truong_gia_tang2.cham_diem_theo_ma`, song song theo mã) → dòng đúng khuôn
`decisions` (`dong_quyet_dinh`) và bảng giá đóng cửa theo NGÀY CÓ QUYẾT ĐỊNH → `vong_hoc_gia.chay_vong` (bộ đề xuất, ba lần
`cham_xac_nhan.cham` 2.000 hoán vị, kiểm tiến-về-trước) và đo thời gian từng phần.

BỘ NỐI (adapter) là hai dòng: `dong` = dòng của `dong_quyet_dinh`, `gia` = bảng `close` của các phiên có quyết định (bỏ khởi động).
KHÔNG đổi nghĩa nào của vòng: nó vốn chỉ nhận `dong` và `gia` (gác G4) và suy lịch khai/đọc từ ngày của dữ liệu, nên chạy nguyên trên
dữ liệu Tầng 2; test (`tests/test_chuan_bi_lat5_thi_truong_gia.py`) kiểm các phiên khai/đọc ra ĐÚNG 139 · 160 · 183 / 412 · 433 · 456.

HAI LƯỢT ĐO: (1) vòng ĐÚNG như Lát 3 (bộ đề xuất cơ sở, dừng ở lần nâng cấp đầu); (2) cận trên: ba ứng viên ép sẵn (G, H, `deu`)
nên cả ba lần `cham` đều chạy nếu không ai `QUA` (vòng dừng ngay sau một lần nâng cấp, nên lượt (1) có thể chỉ đọc 1–2 lần).
`--song-song N` chạy N bản của vòng cùng lúc trong N tiến trình để thấy độ co giãn (cùng đầu vào; chỉ đo thời gian).

KHÔNG CÓ TỶ LỆ, KHÔNG PHÁN ĐẠT/TRƯỢT. Công cụ không ghi file nào.

CHẠY
    ./.venv/Scripts/python.exe -X utf8 tools/chay_vong_tang2_thi_truong_gia.py --luong 9001 --chi-so 1 --muc 2 --so-tien-trinh 12 --song-song 12
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import platform
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd

for _luong_ra in (sys.stdout, sys.stderr):   # BƯỚC 129
    try:
        _luong_ra.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.append(str(Path(__file__).resolve().parent))

import cham_xac_nhan as cx  # noqa: E402
import thi_truong_gia as T  # noqa: E402
import thi_truong_gia_tang2 as G  # noqa: E402
import vong_hoc_gia as V  # noqa: E402
from chay_vong_thi_truong_gia import LUONG_TEST, doc_kappa_muc, kiem_luong  # noqa: E402


def _viec_cham_ma(a):
    tt, ma = a
    return ma, G.cham_diem_theo_ma(tt, ma)


def cham_ba_muoi(tt, pool=None) -> dict:
    """Chấm cả 60 mã, mỗi mã một việc; kết quả theo ĐÚNG thứ tự mã, bất kể số tiến trình."""
    viec = [(dataclasses.replace(tt, gia={m: tt.gia[m]}), m) for m in tt.ma]
    kq = [_viec_cham_ma(a) for a in viec] if pool is None else list(pool.map(_viec_cham_ma, viec, chunksize=1))
    return dict(kq)


def noi_dong_va_gia(tt, theo_ma: dict) -> tuple[list[dict], pd.DataFrame]:
    """Bộ nối Tầng 2 → vòng: dòng `decisions` và bảng giá đóng cửa của các phiên CÓ quyết định (bỏ khởi động)."""
    dong = G.dong_quyet_dinh(tt, theo_ma)
    gia = pd.DataFrame({m: tt.gia[m]["close"].to_numpy()[tt.so_khoi_dong:] for m in tt.ma}, index=list(tt.ngay_quyet_dinh))
    return dong, gia


def bo_ba_ep(dong, gia) -> list[dict]:
    """Ba ứng viên ép sẵn (G, H, `deu`) để cả ba lần `cham` đều chạy: cận trên chi phí. Δ giả = 1 (chỉ để qua `chon_khai`)."""
    ho = T.ho_spec_f()
    return [{"ten": t, "spec": ho[t], "delta": 1.0 - 0.1 * i} for i, t in enumerate(("mono_volume_score", "bo_volume_score", "deu"))]


def do_vong(dong, gia, de_xuat_fn=None, so_hoan_vi: int = cx.SO_HOAN_VI) -> dict:
    """Chạy `vong_hoc_gia.chay_vong` và đo: tổng, bộ đề xuất, từng lần `cham`, kiểm tiến-về-trước. Trả số đo + biên bản tóm tắt.
    Đo bằng cách bọc TẠM `cx.cham`, `V.de_xuat`, `V.kiem_tien_ve_truoc` rồi trả lại (kể cả khi nổ)."""
    gio = {"de_xuat": 0.0, "cham": [], "tien_ve_truoc": 0.0}
    cu = (cx.cham, V.de_xuat, V.kiem_tien_ve_truoc)

    def boc_cham(*a, **k):
        t = time.perf_counter()
        r = cu[0](*a, **k)
        gio["cham"].append(time.perf_counter() - t)
        return r

    def boc_de_xuat(*a, **k):
        t = time.perf_counter()
        r = cu[1](*a, **k)
        gio["de_xuat"] += time.perf_counter() - t
        return r

    def boc_tien(*a, **k):
        t = time.perf_counter()
        r = cu[2](*a, **k)
        gio["tien_ve_truoc"] += time.perf_counter() - t
        return r
    cx.cham, V.de_xuat, V.kiem_tien_ve_truoc = boc_cham, boc_de_xuat, boc_tien
    try:
        t0 = time.perf_counter()
        v = V.chay_vong(dong, gia, de_xuat_fn=de_xuat_fn, so_hoan_vi=so_hoan_vi)
        tong = time.perf_counter() - t0
    finally:
        cx.cham, V.de_xuat, V.kiem_tien_ve_truoc = cu
    return {"giay_tong": tong, "giay_de_xuat": gio["de_xuat"], "giay_cham": gio["cham"], "giay_tien_ve_truoc": gio["tien_ve_truoc"],
            "so_lan_cham": len(gio["cham"]), "ket_cuc": v["ket_cuc"], "khai": [r["ten"] for r in v["lich"]],
            "phien_khai": [r["khai_phien"] for r in v["lich"]], "phien_doc": [r["doc_phien"] for r in v["lich"]],
            "trang_thai": v["trang_thai"], "so_phien": v["so_phien"]}


def _viec_vong(a):
    dong, gia, ep = a
    return do_vong(dong, gia, bo_ba_ep if ep else None)


def chay(luong: int, chi_so: int, kappa: float, so_tien_trinh: int = 1, song_song: int = 0, so_ma=None) -> dict:
    kiem_luong(luong)
    t0 = time.perf_counter()
    tt = G.sinh_thi_truong_2(luong, chi_so, float(kappa))
    giay_sinh = time.perf_counter() - t0
    if so_ma is not None:
        tt = dataclasses.replace(tt, ma=tt.ma[: int(so_ma)], gia={m: tt.gia[m] for m in tt.ma[: int(so_ma)]})
    t1 = time.perf_counter()
    if so_tien_trinh > 1:
        with ProcessPoolExecutor(max_workers=so_tien_trinh) as pool:
            theo_ma = cham_ba_muoi(tt, pool)
    else:
        theo_ma = cham_ba_muoi(tt)
    giay_cham = time.perf_counter() - t1
    t2 = time.perf_counter()
    dong, gia = noi_dong_va_gia(tt, theo_ma)
    giay_noi = time.perf_counter() - t2
    ra = {"thi_truong": {"luong": int(luong), "chi_so": int(chi_so), "kappa": float(kappa), "so_ma": len(tt.ma),
                         "so_phien": tt.so_phien, "so_khoi_dong": tt.so_khoi_dong},
          "giay_sinh": giay_sinh, "giay_cham_diem": giay_cham, "giay_noi": giay_noi, "so_dong": len(dong),
          "so_lan_analyze": len(dong), "vong": do_vong(dong, gia), "vong_ep_ba": do_vong(dong, gia, bo_ba_ep)}
    if song_song > 1:
        t3 = time.perf_counter()
        with ProcessPoolExecutor(max_workers=song_song) as pool:
            kq = list(pool.map(_viec_vong, [(dong, gia, True)] * song_song))
        ra["song_song"] = {"n": song_song, "giay_tuong": time.perf_counter() - t3, "giay_tong_moi_ban": [k["giay_tong"] for k in kq],
                             "khai_moi_ban": [k["khai"] for k in kq]}
    return ra


def bien_ban(r: dict) -> list[str]:
    tt = r["thi_truong"]
    ra = [f"VÒNG HỌC TRÊN THỊ TRƯỜNG TẦNG 2 — dòng hạt {tt['luong']}, chỉ số {tt['chi_so']}, κ = {tt['kappa']:.6f}; "
          f"{tt['so_ma']} mã × {tt['so_phien']} phiên có quyết định (+{tt['so_khoi_dong']} khởi động); Python {platform.python_version()}",
          f"  sinh khung OHLCV     : {r['giay_sinh']:.2f} s",
          f"  chấm điểm            : {r['giay_cham_diem']:.1f} s tường ({r['so_lan_analyze']} lần `_analyze`)",
          f"  bộ nối dòng + giá    : {r['giay_noi']:.2f} s ({r['so_dong']} dòng)"]
    for nhan, k in (("VÒNG LÁT 3 (bộ đề xuất cơ sở)", "vong"), ("VÒNG ÉP BA ỨNG VIÊN (cận trên)", "vong_ep_ba")):
        v = r[k]
        ra += ["", f"{nhan}: kết cục {v['ket_cuc']}; khai {v['khai']} ở phiên {v['phien_khai']}, đọc ở {v['phien_doc']}; trạng thái {v['trang_thai']}",
               f"  tổng                 : {v['giay_tong']:.2f} s",
               f"  bộ đề xuất           : {v['giay_de_xuat']:.2f} s",
               f"  `cham` ({v['so_lan_cham']} lần, 2.000 hoán vị): " + " · ".join(f"{g:.2f} s" for g in v["giay_cham"]),
               f"  kiểm tiến-về-trước   : {v['giay_tien_ve_truoc']:.2f} s"]
    if "song_song" in r:
        s = r["song_song"]
        ra += ["", f"{s['n']} BẢN CÙNG LÚC (vòng ép ba ứng viên): {s['giay_tuong']:.2f} s tường; mỗi bản "
               f"{min(s['giay_tong_moi_ban']):.2f}–{max(s['giay_tong_moi_ban']):.2f} s"]
    return ra


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--luong", type=int, default=LUONG_TEST, help="dòng hạt: chỉ 1 hoặc 9001")
    ap.add_argument("--chi-so", type=int, default=1)
    nhom = ap.add_mutually_exclusive_group()
    nhom.add_argument("--muc", type=float, default=None, help="hệ số MDE₈₀ của file hiệu chuẩn: 0 · 0.5 · 1 · 2")
    nhom.add_argument("--kappa", type=float, default=None)
    ap.add_argument("--so-tien-trinh", type=int, default=1, help="số tiến trình chấm điểm")
    ap.add_argument("--song-song", type=int, default=0, help="chạy N bản của vòng cùng lúc để đo độ co giãn")
    ap.add_argument("--so-ma", type=int, default=None, help="chỉ lấy N mã đầu (thử nhỏ)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        kiem_luong(a.luong)
        kappa = a.kappa if a.kappa is not None else doc_kappa_muc(2.0 if a.muc is None else a.muc)
        r = chay(a.luong, a.chi_so, kappa, a.so_tien_trinh, a.song_song, a.so_ma)
    except ValueError as e:
        print(f"LỖI: {e}", file=sys.stderr)
        return 2
    print("\n".join(bien_ban(r)))
    if a.json:
        print("KET_QUA_JSON " + json.dumps(r, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
