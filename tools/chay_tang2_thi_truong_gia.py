"""`chay-tang2` — chấm MỘT thị trường giả Tầng 2 qua `paper_runner._analyze` THẬT, kiểm P1, ĐO chi phí (C4 Lát 4, BƯỚC 292).

Đề bài: `docs/thiet-ke-c4-thi-truong-gia.md` mục 4.1 (Tầng 2), 4.6, 4.8, 4.9, 6 (hàng P), 9 (chi phí) và 8 ("Lát 4").
Đặc tả là nguồn duy nhất; đừng chép nó vào đây.

MỘT thị trường, một tiến trình: sinh khung OHLCV (khối lượng mang `z`) → chấm từng (mã, phiên) bằng `_analyze` thật →
dòng đúng khuôn `decisions` → P1. In thời gian từng giai đoạn và chi phí một lần chấm. KHÔNG có tỷ lệ nào, KHÔNG phán
đạt/trượt của một tiêu chí nào (đó là Lát 5); P1 là kiểm khuôn, tất định.

DÒNG HẠT. Dùng lại cửa `kiem_luong` của `chay_vong_thi_truong_gia`: chỉ dòng 1 và 9001 (dòng thử). Dòng 2, 3, 4 (lượt
chính, Lát 5) và 5 (chẩn đoán sau khi nhìn kết quả) bị chặn: không sinh, không chạy, không đọc. Mọi hàm gọi bộ sinh đều
gọi `kiem_luong` TRƯỚC (gác AST ở test).

KHÔNG mạng, KHÔNG file chung: không đọc/ghi `backtest/cache*`, `sl_pattern_memory.json`, `paper_trades.db`, Sheets,
`~/.vnstock`. Công cụ này không ghi file nào; muốn lưu kết quả thì chuyển hướng đầu ra.

CHẠY
    ./.venv/Scripts/python.exe -X utf8 tools/chay_tang2_thi_truong_gia.py --luong 9001 --chi-so 1 --muc 2
    ./.venv/Scripts/python.exe -X utf8 tools/chay_tang2_thi_truong_gia.py --luong 9001 --chi-so 1 --muc 2 --so-ma-cham 6 --so-phien 40

`--muc` lấy κ của bốn mức 0× · 0,5× · 1× · 2× MDE₈₀ từ `docs/thi-truong-gia-hieu-chuan.json` (Lát 2); `--kappa` đặt thẳng.
Mã thoát: 0 chạy xong và P1 đạt · 1 P1 có vi phạm · 2 lỗi cấu hình (dòng hạt cấm, đối số sai).
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import sys
import time
from pathlib import Path

for _luong_ra in (sys.stdout, sys.stderr):   # BƯỚC 129
    try:
        _luong_ra.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.append(str(Path(__file__).resolve().parent))

import thi_truong_gia as T  # noqa: E402
import thi_truong_gia_tang2 as G  # noqa: E402
from chay_vong_thi_truong_gia import LUONG_TEST, doc_kappa_muc, kiem_luong  # noqa: E402


def chay_mot_thi_truong(luong: int, chi_so: int, kappa: float, so_ma_cham: int | None = None,
                        so_phien: int | None = None, so_khoi_dong: int = G.SO_PHIEN_KHOI_DONG,
                        tien_do=None) -> dict:
    """Sinh (qua `kiem_luong`), chấm và kiểm P1 MỘT thị trường Tầng 2. Trả số đo, KHÔNG phán."""
    kiem_luong(luong)
    t0 = time.perf_counter()
    tt = G.sinh_thi_truong_2(luong, chi_so, float(kappa), so_phien=so_phien, so_khoi_dong=so_khoi_dong)
    giay_sinh = time.perf_counter() - t0
    ma = tt.ma if so_ma_cham is None else tt.ma[: int(so_ma_cham)]
    theo_ma, giay_ma = {}, {}
    cpu0 = time.process_time()
    t1 = time.perf_counter()
    for i, m in enumerate(ma, 1):
        t = time.perf_counter()
        theo_ma[m] = G.cham_diem_theo_ma(tt, m)
        giay_ma[m] = time.perf_counter() - t
        if tien_do is not None:
            tien_do(i, len(ma), time.perf_counter() - t1)
    giay_cham = time.perf_counter() - t1
    cpu_cham = time.process_time() - cpu0
    dong = G.dong_quyet_dinh(tt, theo_ma)
    sai_p1 = G.kiem_p1(tt, dong, len(ma), tt.so_phien)
    ic = G.ic_thanh_phan(tt, dong)          # P3: chỉ nhãn và dòng quyết định, không z, không oracle
    so_lan = len(dong)
    return {"thi_truong": {"luong": int(luong), "chi_so": int(chi_so), "kappa": float(kappa), "so_ma": len(ma),
                           "so_phien": tt.so_phien, "so_khoi_dong": tt.so_khoi_dong, "ngay_dau": tt.ngay[0],
                           "ngay_dau_quyet_dinh": tt.ngay_quyet_dinh[0], "ngay_cuoi": tt.ngay[-1]},
            "so_lan_cham": so_lan, "giay_sinh": giay_sinh, "giay_cham": giay_cham, "giay_cpu_cham": cpu_cham,
            "giay_moi_ma": giay_ma, "p1": sai_p1, "ic": ic, "dong": dong}


def mo_ta_phan_phoi(dong: list[dict]) -> dict:
    """Mô tả (không phán) phân phối điểm `_analyze` cho ra trên dữ liệu giả: số giá trị khác nhau và biên của điểm cuối
    và của năm thành phần, tỷ lệ điểm ≥ ngưỡng mua. Để so với bảng Tầng 2 của `MO-XE-KIEN-TRUC.md`."""
    import json

    import cham_bong as cb
    import paper_trading as pt
    diem = [d["score"] for d in dong]
    ra = {"so_dong": len(dong), "diem": {"khac_nhau": len(set(diem)), "min": min(diem), "max": max(diem)},
          "ty_le_tren_nguong_mua": sum(1 for x in diem if x >= pt.BUY_THRESHOLD) / len(diem),
          "nguong_mua": pt.BUY_THRESHOLD, "thanh_phan": {}}
    tp = [json.loads(d["components"]) for d in dong]
    for k in cb.THANH_PHAN:
        v = [x[k] for x in tp]
        ra["thanh_phan"][k] = {"khac_nhau": len(set(v)), "min": min(v), "max": max(v)}
    return ra


def bien_ban(kq: dict, pp: dict | None = None) -> list[str]:
    tt = kq["thi_truong"]
    g = list(kq["giay_moi_ma"].values())
    n_ma = max(tt["so_ma"], 1)
    ms = kq["giay_cham"] / kq["so_lan_cham"] * 1000 if kq["so_lan_cham"] else float("nan")
    ra = [f"THỊ TRƯỜNG GIẢ TẦNG 2 — dòng hạt {tt['luong']}, chỉ số {tt['chi_so']}, κ = {tt['kappa']:.6f}",
          f"  {tt['so_ma']} mã · {tt['so_khoi_dong']} phiên khởi động + {tt['so_phien']} phiên có quyết định "
          f"({tt['ngay_dau']} → {tt['ngay_cuoi']}; quyết định từ {tt['ngay_dau_quyet_dinh']})",
          f"  Python {platform.python_version()} · {os.cpu_count()} lõi logic · một tiến trình",
          "",
          "CHI PHÍ (đo; một tiến trình)",
          f"  sinh khung OHLCV     : {kq['giay_sinh']:.2f} s",
          f"  chấm điểm            : {kq['giay_cham']:.1f} s tường · {kq['giay_cpu_cham']:.1f} s CPU, "
          f"{kq['so_lan_cham']} lần `_analyze` → {ms:.2f} ms một lần",
          f"  mỗi mã (s)           : min {min(g):.1f} · trung vị {statistics.median(g):.1f} · max {max(g):.1f}",
          f"  quy ra {T.SO_MA} mã        : {kq['giay_cham'] / n_ma * T.SO_MA / 60:.1f} phút (chỉ phần chấm điểm)",
          "",
          "P1 — dòng do `_analyze` thật sinh đúng khuôn, `data_quality` = OK: "
          + ("ĐẠT, 0 vi phạm" if not kq["p1"] else f"CÓ {len(kq['p1'])} VI PHẠM")]
    for s in kq["p1"][:10]:
        ra.append(f"    - {s}")
    if pp is not None:
        ra += ["", "PHÂN PHỐI điểm `_analyze` trên dữ liệu giả (mô tả, không phán):",
               f"  điểm cuối: {pp['diem']['khac_nhau']} giá trị khác nhau, {pp['diem']['min']}…{pp['diem']['max']}; "
               f"tỷ lệ ≥ ngưỡng mua {pp['nguong_mua']}: {pp['ty_le_tren_nguong_mua']:.3f}"]
        for k, v in pp["thanh_phan"].items():
            ra.append(f"  {k:<15}: {v['khac_nhau']:>3} giá trị khác nhau, {v['min']}…{v['max']}")
    ic = kq["ic"]
    ra += ["", f"P3 — IC (tương quan hạng gộp) của từng thành phần với nhãn, {ic['so_cap']} cặp (phiên, mã) có nhãn "
               f"(mô tả MỘT thị trường, không phán; tiêu chí ≥ 90/100 là của Lát 5):"]
    for k, v in ic["ic"].items():
        ra.append(f"  {k:<15}: {v:+.4f}")
    return ra


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--luong", type=int, default=LUONG_TEST, help="dòng hạt: chỉ 1 hoặc 9001")
    ap.add_argument("--chi-so", type=int, default=1)
    nhom = ap.add_mutually_exclusive_group()
    nhom.add_argument("--muc", type=float, default=None, help="hệ số MDE₈₀ của file hiệu chuẩn: 0 · 0.5 · 1 · 2")
    nhom.add_argument("--kappa", type=float, default=None)
    ap.add_argument("--so-ma-cham", type=int, default=None, help="chỉ chấm N mã đầu (mặc định cả 60)")
    ap.add_argument("--so-phien", type=int, default=None,
                    help="số phiên CÓ quyết định (mặc định: dòng thời gian của đặc tả)")
    ap.add_argument("--so-khoi-dong", type=int, default=G.SO_PHIEN_KHOI_DONG)
    ap.add_argument("--tien-do", action="store_true", help="in một dòng sau mỗi mã (ra stderr)")
    ap.add_argument("--json", action="store_true", help="in thêm MỘT dòng `KET_QUA_JSON {...}` (thị trường, thời gian, P1, IC)")
    a = ap.parse_args(argv)
    try:
        kiem_luong(a.luong)
        kappa = a.kappa if a.kappa is not None else doc_kappa_muc(2.0 if a.muc is None else a.muc)
        td = (lambda i, n, s: print(f"  mã {i}/{n} xong sau {s:.0f} s", file=sys.stderr, flush=True)) if a.tien_do else None
        kq = chay_mot_thi_truong(a.luong, a.chi_so, kappa, a.so_ma_cham, a.so_phien, a.so_khoi_dong, td)
    except ValueError as e:
        print(f"LỖI: {e}", file=sys.stderr)
        return 2
    print("\n".join(bien_ban(kq, mo_ta_phan_phoi(kq["dong"]))))
    if a.json:
        print("KET_QUA_JSON " + json.dumps({k: kq[k] for k in ("thi_truong", "so_lan_cham", "giay_sinh", "giay_cham",
                                                                  "giay_cpu_cham", "p1", "ic")}, ensure_ascii=False))
    return 1 if kq["p1"] else 0


if __name__ == "__main__":
    sys.exit(main())
