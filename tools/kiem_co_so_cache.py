"""Soát cache giá theo CƠ SỞ ĐIỀU CHỈNH — CHỈ ĐỌC (BƯỚC 180).

Hai việc, đều không ghi file nào:

1. **Quét bậc vượt biên độ sàn** trong từng `<cache>/<MÃ>.csv`: bước đổi
   đóng-cửa liền kề lớn hơn biên độ sàn + 0,5 điểm (HOSE 7% · HNX 10% ·
   UPCoM 15%; sàn tra bằng `san_giao_dich.tra_san`). Mã NGOÀI bảng sàn được
   báo CHƯA KIỂM ĐƯỢC, KHÔNG lùi về HOSE (IDC là mã HNX: ±9,9% là biên bình
   thường, lùi về HOSE 7% sẽ báo nhầm). Mỗi bậc in kèm vùng so với
   `docs/moc_du_lieu_sach.json` (`moc_theo_ma`): trước mốc = vùng NGOÀI MẪU.
2. `--doi-chieu-nguon` (cần mạng, vẫn chỉ ĐỌC): kéo lại từng mã và in nhãn
   `backtest.data.so_co_so` (đúng hàm thuần mà `extend_history` dùng) cùng tỷ
   lệ mới/cũ trên các ngày trùng đã đóng.

    ./.venv/Scripts/python.exe tools/kiem_co_so_cache.py
    ./.venv/Scripts/python.exe tools/kiem_co_so_cache.py --cache backtest/cache
    ./.venv/Scripts/python.exe tools/kiem_co_so_cache.py --doi-chieu-nguon

GIỚI HẠN — đọc trước khi tin một dòng:
  * Phép quét KHÔNG thấy bậc nhỏ hơn biên độ (cổ tức tiền vài %): chuỗi chưa
    điều chỉnh có thể đầy bậc nhỏ mà quét vẫn sạch.
  * Một bậc vượt biên có thể là ngày GDKHQ THẬT trong chuỗi chưa điều chỉnh,
    HOẶC là CHỖ NỐI hai cơ sở giá — công cụ KHÔNG phân biệt được hai ca; cần
    lịch sự kiện doanh nghiệp hoặc `--doi-chieu-nguon`.
  * Mã từng đổi sàn (BSR, VTP rời UPCoM lên HOSE) có thể bị báo theo biên
    của sàn HIỆN TẠI ở giai đoạn cũ (biên UPCoM rộng hơn nên chiều báo
    nhầm là bỏ sót, không phải báo thừa).
  * "Liền kề" là hai dòng kề nhau TRONG FILE; file thiếu phiên làm bước nhảy
    trông lớn hơn thực.
  * `--doi-chieu-nguon` chỉ so phần cache giao với lượt kéo (cửa sổ
    `--so-ngay` ngày trước nến cuối của cache): sự kiện cũ hơn cửa sổ ấy
    không thấy.

Mã thoát: 0 không có bước nào vượt biên · 1 có (kể cả khi chỉ ở vài mã) · 2
không đọc được cache (thư mục vắng / không có CSV đọc được) hoặc
`--doi-chieu-nguon` mà thiếu `vnstock`. Mã CHƯA KIỂM ĐƯỢC được in nhưng KHÔNG
đổi mã thoát — đọc dòng tổng cuối.

KHÔNG nằm trong đường quét hay CI: đọc cache ở máy và (tuỳ chọn) mạng làm
phép đo mất tái lập (bất biến 2).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

for _luong in (sys.stdout, sys.stderr):
    try:
        _luong.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import pandas as pd  # noqa: E402

from san_giao_dich import tra_san  # noqa: E402

#: Biên độ giá ngày theo sàn.
BIEN_DO = {"HOSE": 0.07, "HNX": 0.10, "UPCOM": 0.15}
#: Nới thêm 0,5 điểm phần trăm trước khi gọi một bước đổi là "vượt biên"
#: (làm tròn giá đóng cửa, bước giá).
DEM_BIEN_DO = 0.005
#: Cửa sổ mặc định của `--doi-chieu-nguon`, tính lùi từ nến cuối của cache.
SO_NGAY_DOI_CHIEU = 120
MOC_SACH = GOC / "docs" / "moc_du_lieu_sach.json"


def tim_buoc(df: pd.DataFrame, san: str) -> list[tuple[str, str, float]]:
    """Hàm THUẦN. Bước đổi đóng-cửa liền kề vượt biên độ `san` + `DEM_BIEN_DO`.

    Trả [(ngày, ngày_trước, % đổi)] theo thứ tự thời gian. Phép so viết dạng
    NHÂN (`|c − p| > (biên + đệm) × p`) để biên không dính làm tròn dấu phẩy
    động. Dòng có `close` không phải số dương bị bỏ khỏi chuỗi.
    """
    nguong = BIEN_DO[san] + DEM_BIEN_DO
    d = pd.DataFrame({
        "time": pd.to_datetime(df["time"], errors="coerce").dt.strftime("%Y-%m-%d"),
        "close": pd.to_numeric(df["close"], errors="coerce")})
    d = d.dropna()
    d = d[d["close"] > 0].drop_duplicates("time").sort_values("time")
    ngay, gia = list(d["time"]), list(d["close"])
    out = []
    for k in range(1, len(gia)):
        if abs(gia[k] - gia[k - 1]) > nguong * gia[k - 1]:
            out.append((ngay[k], ngay[k - 1], (gia[k] / gia[k - 1] - 1) * 100))
    return out


def vung(ma: str, ngay: str, moc: dict[str, str]) -> str:
    """'ngoài mẫu' khi `ngay` trước mốc dữ liệu sạch của mã; 'trong mẫu' sau
    đó; 'không có mốc' khi mã vắng trong `moc_theo_ma`."""
    m = moc.get(ma)
    if not m:
        return "không có mốc"
    return "ngoài mẫu" if ngay < m else "trong mẫu"


def doc_moc(duong: Path = MOC_SACH) -> dict[str, str]:
    try:
        return dict(json.loads(duong.read_text(encoding="utf-8"))["moc_theo_ma"])
    except Exception:
        return {}


def doc_cache(thu_muc: Path) -> tuple[dict[str, pd.DataFrame], dict[str, str]]:
    """({mã: df}, {mã: lý do không đọc được}). Chỉ ĐỌC, một tầng thư mục."""
    co: dict[str, pd.DataFrame] = {}
    hong: dict[str, str] = {}
    for f in sorted(thu_muc.glob("*.csv")):
        try:
            df = pd.read_csv(f)
        except Exception as e:
            hong[f.stem] = f"không đọc được CSV ({type(e).__name__})"
            continue
        thieu = {"time", "close"} - set(df.columns)
        if thieu:
            hong[f.stem] = f"thiếu cột {sorted(thieu)}"
        elif len(df) == 0:
            hong[f.stem] = "file rỗng"
        else:
            co[f.stem] = df
    return co, hong


def quet(cache: dict[str, pd.DataFrame], moc: dict[str, str]):
    """Hàm THUẦN. Trả (buoc, chua_kiem).

    buoc       [(mã, sàn, ngày, ngày_trước, %, vùng)]
    chua_kiem  [(mã, lý do)] — mã ngoài bảng sàn
    """
    buoc, chua = [], []
    for ma in sorted(cache):
        san = tra_san(ma)
        if san is None:
            chua.append((ma, "mã NGOÀI bảng sàn `san_giao_dich.BANG_SAN` — "
                             "không lùi về HOSE"))
            continue
        for ngay, truoc, pct in tim_buoc(cache[ma], san):
            buoc.append((ma, san, ngay, truoc, pct, vung(ma, ngay, moc)))
    return buoc, chua


def doi_chieu(cache: dict[str, pd.DataFrame], fetch, bay_gio: datetime,
              so_ngay: int = SO_NGAY_DOI_CHIEU):
    """Kéo lại từng mã bằng `fetch(ma, start, end)` rồi hỏi `so_co_so`.

    Trả {mã: KetQuaCoSo | None}; None = không kéo được. KHÔNG ghi gì.
    """
    from backtest.data import _norm_time, so_co_so

    kq = {}
    end = bay_gio.date().isoformat()
    for ma in sorted(cache):
        cuoi = _norm_time(cache[ma])["time"].max()
        start = (date.fromisoformat(cuoi) - timedelta(days=so_ngay)).isoformat()
        moi = fetch(ma, start, end)
        kq[ma] = (None if moi is None or len(moi) == 0
                  else so_co_so(cache[ma], moi, bay_gio))
    return kq


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cache", default=str(GOC / "backtest" / "cache"),
                    help="thư mục cache (mặc định backtest/cache)")
    ap.add_argument("--doi-chieu-nguon", action="store_true",
                    help="kéo lại từng mã (mạng, chỉ đọc) và in nhãn so cơ sở")
    ap.add_argument("--so-ngay", type=int, default=SO_NGAY_DOI_CHIEU,
                    help="cửa sổ kéo lại, tính lùi từ nến cuối của cache")
    a = ap.parse_args(argv)

    thu_muc = Path(a.cache)
    if not thu_muc.is_dir():
        print(f"KHÔNG ĐỌC ĐƯỢC cache: {thu_muc} không phải thư mục")
        return 2
    cache, hong = doc_cache(thu_muc)
    for ma, ly_do in hong.items():
        print(f"  CHƯA KIỂM ĐƯỢC {ma}: {ly_do}")
    if not cache:
        print(f"KHÔNG ĐỌC ĐƯỢC cache: {thu_muc} không có CSV nào đọc được")
        return 2

    moc = doc_moc()
    buoc, chua = quet(cache, moc)
    print(f"Cache {thu_muc}: {len(cache)} mã đọc được")
    for ma, san, ngay, truoc, pct, v in buoc:
        print(f"  VƯỢT BIÊN  {ma:<7}{san:<6}{ngay} (trước {truoc})  "
              f"{pct:+.2f}%  [{v}]")
    for ma, ly_do in chua:
        print(f"  CHƯA KIỂM ĐƯỢC {ma}: {ly_do}")
    ma_buoc = sorted({b[0] for b in buoc})
    print(f"Tổng: {len(buoc)} bước vượt biên ở {len(ma_buoc)} mã · "
          f"{len(chua) + len(hong)} mã CHƯA KIỂM ĐƯỢC")
    print("Giới hạn: không thấy bậc nhỏ hơn biên; một bước vượt biên có thể "
          "là GDKHQ thật HOẶC chỗ nối hai cơ sở giá — công cụ không phân biệt.")

    if a.doi_chieu_nguon:
        try:
            from backtest.data import fetch_one
            from data_quality import now_vn
        except Exception as e:
            print(f"CHƯA ĐỐI CHIẾU ĐƯỢC NGUỒN ({type(e).__name__}: {e})")
            return 2
        try:
            kq = doi_chieu(cache, fetch_one, now_vn(), a.so_ngay)
        except ImportError as e:
            print(f"CHƯA ĐỐI CHIẾU ĐƯỢC NGUỒN: thiếu thư viện ({e})")
            return 2
        print(f"\nĐỐI CHIẾU NGUỒN (cửa sổ {a.so_ngay} ngày, chỉ đọc):")
        dem: dict[str, int] = {}
        for ma, r in kq.items():
            if r is None:
                print(f"  {ma:<7}KHÔNG KÉO ĐƯỢC")
                dem["KHONG_KEO_DUOC"] = dem.get("KHONG_KEO_DUOC", 0) + 1
                continue
            dem[r.nhan] = dem.get(r.nhan, 0) + 1
            if r.ty_le_min is None:
                print(f"  {ma:<7}{r.nhan}  ({r.ly_do})")
            else:
                print(f"  {ma:<7}{r.nhan}  trùng {r.so_ngay_trung} · lệch "
                      f"{r.so_ngay_lech} · mới/cũ min {r.ty_le_min:.6f} "
                      f"max {r.ty_le_max:.6f}")
        print("Tổng: " + " · ".join(f"{k} {v}" for k, v in sorted(dem.items())))

    return 1 if buoc else 0


if __name__ == "__main__":
    sys.exit(main())
