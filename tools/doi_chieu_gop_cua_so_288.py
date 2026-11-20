"""Đối chiếu nến của ĐƯỜNG BIỂU ĐỒ trên app (một lượt tải 1.583 ngày, Entrade khử trùng, rồi cắt) với nến mà
`run_daily` chấm điểm (BƯỚC 288). CHỈ ĐỌC; không `run_daily`, không sổ, không Sheets, không khoá.

Với mỗi mã, từng cửa sổ:
  - cửa sổ quét 1.095 ngày: nến `run_daily` dùng = `VNStockCollectorAgent().collect(mã, hôm nay − 1.095 ngày, hôm nay)`
    (chuỗi mặc định) so với nến app cho ô Dow (cắt từ lượt tải 1.583 ngày bằng `gia_mot_lan.tai_mot_lan`);
  - cửa sổ biểu đồ ngày 180 ngày: nến app so với `collect` mặc định cho cửa sổ 180 ngày.
"Giống" = `DataFrame.equals` VÀ cùng dtype từng cột (từng byte), sau khi bỏ nến của NGÀY `den` (nến đang giao dịch bị
nguồn trả dở và đổi theo giờ, nên hai lượt tải cách nhau vài phút có thể khác nhau ở đúng nến ấy).

Chạy mạng thật (tuần tự, nghỉ giữa lượt; ~1 s mỗi mã):
    ./.venv/Scripts/python.exe tools/doi_chieu_gop_cua_so_288.py               # cả 71 mã trong `san_giao_dich`
    ./.venv/Scripts/python.exe tools/doi_chieu_gop_cua_so_288.py ACB DHG AAA   # vài mã
Mã thoát: 0 mọi mã giống · 1 có mã LỆCH · 2 chưa kiểm được (không tải được).

Bản phát lại ngoại tuyến cho CI: `tests/test_gop_cua_so_288.py` chạy CHÍNH hàm `doi_chieu_mot_ma` này trên JSON thô đã
chụp (`tests/du_lieu/entrade_khu_trung_288.json.gz`).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

#: = `run_daily.NGAY_LICH_SU` (không nhập `run_daily` ở đây: nó kéo cả sổ lệnh; test khoá hai số bằng nhau).
NGAY_QUET = 1095
NGAY_BIEU_DO = 180                 # = `days_back` của app.py (test khoá)
#: = `khung_thoi_gian.NGAY_LICH_CHO_KHUNG_THANG`; không nhập module ấy ở đây vì `tests/test_khung_thoi_gian.py` đòi
#: CHỈ `app.py` nhập nó (test của BƯỚC 288 khoá hai số bằng nhau).
NGAY_RONG = 1583


@dataclass
class KetQuaMotMa:
    ma: str
    nguon_cua_so_rong: str = ""
    quet_giong: bool = False
    bieu_do_giong: bool = False
    so_nen_quet: int = 0
    so_nen_bieu_do: int = 0
    so_hang_lech_quet: int = 0
    ghi_chu: list = field(default_factory=list)

    @property
    def giong(self) -> bool:
        return self.quet_giong and self.bieu_do_giong


def _bo_nen_ngay(df: pd.DataFrame, den: str) -> pd.DataFrame:
    return df[df["time"] != pd.Timestamp(den)].reset_index(drop=True)


def _giong_tung_byte(a: pd.DataFrame, b: pd.DataFrame) -> tuple[bool, int]:
    """(giống từng byte?, số hàng khác ≥ 1 cột — chỉ đếm được khi cùng hình dạng)."""
    if a.shape != b.shape or list(a.columns) != list(b.columns):
        return False, -1
    khac = (a.reset_index(drop=True) != b.reset_index(drop=True)).any(axis=1)
    return bool(a.equals(b)) and list(a.dtypes) == list(b.dtypes), int(khac.sum())


def doi_chieu_mot_ma(ma: str, den: str) -> KetQuaMotMa:
    """Đối chiếu MỘT mã tới ngày `den` (chuỗi YYYY-MM-DD). Gọi mạng qua `nguon_gia_cong_khai` (thay được khi test)."""
    import gia_mot_lan as g1l
    import nguon_gia_cong_khai as ngk
    import san_giao_dich as sgd
    from data_collectors import VNStockCollectorAgent

    san = sgd.san_cua(ma)

    def tu(n: int) -> str:
        return (pd.Timestamp(den) - pd.Timedelta(days=n)).strftime("%Y-%m-%d")

    def tai(tk, s, e, x):                                      # = `app.load_stock_data`
        r = VNStockCollectorAgent().collect(tk, s, e, exchange=x)
        q = r.get("quality")
        return r.get("df"), r.get("status"), [i.message for i in q.warnings] if q is not None else []

    bo_nho: dict = {}

    def tai_nguon(tk, s, e, x):                                # = `app.load_stock_data_nguon` (+ đệm thay `st.cache_data`)
        khoa = (tk, s, e, x)
        if khoa not in bo_nho:
            r = VNStockCollectorAgent().collect(tk, s, e, exchange=x, chuoi=ngk.chuoi_cho_app(tk))
            q = r.get("quality")
            bo_nho[khoa] = (r.get("df"), r.get("status"),
                            [i.message for i in q.warnings] if q is not None else [], r.get("source", ""))
        return bo_nho[khoa]

    ngay_rong = max(NGAY_BIEU_DO, NGAY_QUET, NGAY_RONG)
    kq = KetQuaMotMa(ma=ma)
    # nến `run_daily` chấm: chuỗi MẶC ĐỊNH, cửa sổ 1.095 ngày
    quet = tai(ma, tu(NGAY_QUET), den, san)
    bieu_do_cu = tai(ma, tu(NGAY_BIEU_DO), den, san)
    # nến app: một lượt tải rộng, cắt
    dow = g1l.tai_mot_lan(tai_nguon, tai, ma, tu(NGAY_QUET), den, san, ngay_rong)
    bieu_do = g1l.tai_mot_lan(tai_nguon, tai, ma, tu(NGAY_BIEU_DO), den, san, ngay_rong)
    rong = tai_nguon(ma, tu(ngay_rong), den, san)
    kq.nguon_cua_so_rong = rong[3] if rong[1] == "OK" else f"khong tai duoc ({rong[1]})"
    for ten, x in (("quet", quet), ("bieu_do_cu", bieu_do_cu), ("dow_app", dow), ("bieu_do_app", bieu_do)):
        if x[1] != "OK" or x[0] is None or x[0].empty:
            kq.ghi_chu.append(f"{ten}: trang thai {x[1]}")
            return kq
    a, b = _bo_nen_ngay(quet[0], den), _bo_nen_ngay(dow[0], den)
    kq.quet_giong, kq.so_hang_lech_quet = _giong_tung_byte(a, b)
    kq.so_nen_quet = len(a)
    c, d = _bo_nen_ngay(bieu_do_cu[0], den), _bo_nen_ngay(bieu_do[0], den)
    kq.bieu_do_giong, _ = _giong_tung_byte(c, d)
    kq.so_nen_bieu_do = len(c)
    return kq


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    import time

    import san_giao_dich as sgd
    from data_quality import now_vn

    mas = [m.upper() for m in argv] or list(sgd.BANG_SAN)
    den = now_vn().strftime("%Y-%m-%d")
    print(f"Doi chieu den {den} (bo nen ngay {den}, dang do): {len(mas)} ma")
    dem_giong = dem_lech = dem_loi = 0
    for ma in mas:
        try:
            r = doi_chieu_mot_ma(ma, den)
        except Exception as e:                                 # mạng hỏng, không phải kết luận
            dem_loi += 1
            print(f"{ma}: CHUA KIEM DUOC ({type(e).__name__}: {str(e)[:100]})", flush=True)
            continue
        if r.ghi_chu:
            dem_loi += 1
        elif r.giong:
            dem_giong += 1
        else:
            dem_lech += 1
        print(f"{ma}: {'GIONG' if r.giong and not r.ghi_chu else 'LECH' if not r.ghi_chu else 'CHUA KIEM DUOC'} "
              f"| quet {r.so_nen_quet} nen {r.quet_giong} (hang lech {r.so_hang_lech_quet}) "
              f"| bieu do {r.so_nen_bieu_do} nen {r.bieu_do_giong} | nguon cua so rong {r.nguon_cua_so_rong} {r.ghi_chu or ''}",
              flush=True)
        time.sleep(0.4)
    print(f"TONG: {dem_giong} giong · {dem_lech} lech · {dem_loi} chua kiem duoc / {len(mas)}")
    return 1 if dem_lech else 2 if dem_loi else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
