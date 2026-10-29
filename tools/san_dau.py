"""Dụng cụ I/O của sân đấu C1 (BƯỚC 240, Lát 2) — CHỈ ĐỌC với sổ và Google Sheets.

    python tools/san_dau.py tuong-duong                       # Tầng B: phát lại sổ THẬT, so từng ô
    python tools/san_dau.py tuong-duong --tu-ngay 2026-09-25  # đổi ngày bắt đầu của cửa sổ
    python tools/san_dau.py tuong-duong --so-tam <file.db>    # đọc DB tạm đã kéo sẵn (sqlite, chỉ đọc)
    python tools/san_dau.py tuong-duong --nguon-gia mang      # giá tải trực tiếp (bộ thu thập của run_daily)

PHẦN THUẦN ở module gốc `san_dau.py` (đặc tả `docs/thiet-ke-c1-san-dau.md`, mục 6 và 10.2). File này làm
phần có I/O: kéo sổ thật vào DB TẠM bằng đường của `tools/doc_so_that.py` (`keo_ve_so_tam`), đọc giá từ cache
lịch sử cục bộ (`backtest.data.load`, chỉ đọc) hoặc tải thẳng (không ghi cache), rồi gọi phần thuần và IN.
KHÔNG `push`, KHÔNG `pull` vào sổ nào khác, KHÔNG ghi `*.db` ở gốc repo, KHÔNG ghi Sheets. Gác AST ở
`tests/test_san_dau.py` (G1).

TẦNG B — định nghĩa (đặc tả mục 6). Phát lại cấu hình mặc định (`CauHinhVao.tu_module()`) từ `--tu-ngay`, rồi
so với các lệnh THẬT có `signal_date` trong cửa sổ: cùng tập khoá `(mã, ngày tín hiệu)`, mười hai cột bằng nhau
từng ô (không dung sai), số phiên-mã thiếu điểm = 0, số phiên-mã thiếu nến = 0. Khác một ô → ĐỎ, in từng sai
khác. Dụng cụ KHÔNG chỉnh gì để cho khớp.

GIỚI HẠN KHAI THẲNG (đặc tả mục 6): bộ máy thật đổi ở BƯỚC 209 (khoá biên kịch trần/sàn, vào `main` ngày
`NGAY_BO_MAY_HIEN_HANH`) và thêm cờ ở BƯỚC 221–226. Lệnh có đời nằm trước ngày ấy chạy dưới bộ máy cũ nên có thể
khác khi phát lại mà KHÔNG phải lỗi của phát lại; dụng cụ in cả hai ngày và đếm riêng lệnh có tín hiệu từ ngày đó.

MÃ THOÁT: 0 bằng nhau từng ô và không thiếu điểm/nến · 1 có khác biệt hay có phiên-mã thiếu · 2 không đọc được.
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
import time
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
# `tools/` có file cùng tên với module gốc `san_dau.py` (khuôn `tools/hau_kiem_loi.py`): GOC đứng TRƯỚC để
# `import san_dau` ra module thuần. Chạy như script thì `tools/` là sys.path[0]; ở đây GOC chen lên trước nó.
sys.path.insert(0, str(GOC))

for _luong in (sys.stdout, sys.stderr):
    try:
        _luong.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import san_dau as sd  # noqa: E402

MA_BANG_NHAU = 0
MA_KHAC = 1
MA_KHONG_DOC_DUOC = 2

#: Ngày `khoa_bien` (BƯỚC 209, ĐO 28) vào `main` — từ ngày này bộ máy thật là bộ máy hiện hành về khớp lệnh
#: kịch trần/sàn. Lệnh thật có tín hiệu từ ngày này mới có CẢ ĐỜI nằm dưới bộ máy hiện hành. Lấy bằng:
#:     git log --first-parent --format='%h %cI %s' origin/main | grep 'khop-kich-tran-san-209'
#: -> `ed9a9ab` 2026-10-21T08:28:53+07:00 (PR #255). Bước 212 (cắt lỗ phiên chỉ-khớp) chỉ đổi walk-forward;
#: BƯỚC 221–226 chỉ thêm cờ mặc định tắt. Đổi ngày này là một quyết định về cách đọc: nó nằm ở đây, kèm lệnh.
NGAY_BO_MAY_HIEN_HANH = "2026-10-21"

#: Số ngày lịch lùi lại khi tải giá trực tiếp: đủ để cửa sổ chỉ báo (MA50, ATR14) và biên rủi ro của mọi phiên.
NGAY_LUI_GIA = 400

#: Cột của lệnh mà dụng cụ đọc từ sổ (đủ cho phần thuần).
_COT_LENH = ("id", "symbol", "exchange", "signal_date", "entry_date", "entry_price", "exit_date",
             "exit_price", "exit_reason", "stop_loss", "take_profit", "size_pct", "entry_score", "status")


# ── đọc ───────────────────────────────────────────────────────────────────────────────────────
def doc_so_tam(duong: str) -> tuple[list[dict], list[dict]]:
    """(lệnh, quyết định) từ một DB tạm đã kéo sẵn — mở CHỈ ĐỌC (`mode=ro`)."""
    db = sqlite3.connect(f"file:{Path(duong).as_posix()}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    try:
        lenh = [dict(r) for r in db.execute("SELECT * FROM trades ORDER BY id")]
        qd = [dict(r) for r in db.execute("SELECT * FROM decisions ORDER BY seq")]
    finally:
        db.close()
    return lenh, qd


def keo_so_that() -> tuple[list[dict], list[dict]] | None:
    """Kéo sổ thật từ Google Sheets vào DB TẠM (đường của `tools/doc_so_that.py`), đọc rồi đóng.
    None khi kho ngoài chưa cấu hình."""
    sys.path.append(str(GOC / "tools"))
    import doc_so_that as dst
    ra = dst.keo_ve_so_tam()
    if ra is None:
        return None
    so, _ = ra
    try:
        lenh = [dict(r) for r in so.db.execute("SELECT * FROM trades ORDER BY id")]
        qd = [dict(r) for r in so.db.execute("SELECT * FROM decisions ORDER BY seq")]
    finally:
        so.db.close()
    return lenh, qd


def doc_gia_cache(ma_list: list[str]) -> dict:
    """{mã: khung OHLCV} từ cache lịch sử cục bộ (`backtest.data.load`, chỉ đọc). Mã không có cache bị bỏ."""
    from backtest import data as bt_data
    ra = {}
    for ma in ma_list:
        df = bt_data.load(ma)
        if df is not None and len(df):
            ra[ma] = df
    return ra


def tai_gia_mang(ma_list: list[str], den_ngay: str, ghi=print) -> dict:
    """{mã: khung OHLCV} tải THẲNG bằng bộ thu thập mà `run_daily` dùng; không ghi cache. Mã hỏng bị bỏ."""
    os.environ.setdefault("VNSTOCK_TELEMETRY", "off")
    import pandas as pd
    from data_collectors import VNStockCollectorAgent
    bat_dau = (pd.Timestamp(den_ngay) - pd.Timedelta(days=NGAY_LUI_GIA)).strftime("%Y-%m-%d")
    thu = VNStockCollectorAgent()
    ra = {}
    for i, ma in enumerate(ma_list, 1):
        kq = thu.collect(ma, bat_dau, den_ngay)
        if kq.get("status") == "OK" and kq["df"] is not None and len(kq["df"]):
            ra[ma] = kq["df"]
        else:
            ghi(f"  không tải được {ma}: {kq.get('status')}")
        time.sleep(0.3)
    return ra


def tai_vni_mang(den_ngay: str):
    """VN-INDEX tải THẲNG đúng như `market_filter.get_vni_df` khi cache rỗng (đường của runner Actions):
    `backtest.data.fetch_one("VNINDEX", "2020-01-01", ...)`, không ghi cache. Cột `time` của nguồn mang hậu
    tố giờ (`2026-09-30 07:00:00`), nên phép so CHUỖI `time <= ngày tín hiệu` của cổng loại nến CỦA CHÍNH
    NGÀY TÍN HIỆU — cổng chạy thật thấy VN-INDEX trễ MỘT phiên; cache CSV (`2026-09-30`) thì không (BƯỚC 240)."""
    os.environ.setdefault("VNSTOCK_TELEMETRY", "off")
    from backtest import data as bt_data
    return bt_data.fetch_one("VNINDEX", "2020-01-01", den_ngay)


# ── phần tính (thuần theo đầu vào; kiểm được offline) ─────────────────────────────────────────
def _cat_theo_ngay_cuoi(t: dict, ket_thuc: str) -> tuple[dict, frozenset]:
    """Trạng thái của một lệnh THẬT tính tới hết `ket_thuc` (sổ chỉ giữ trạng thái cuối), và các cột KHÔNG so
    được vì chúng đã đổi sau ngày ấy: lệnh chưa khớp tới `ket_thuc` mất cả `stop_loss` lẫn `size_pct` (cỡ lúc
    khớp ≠ cỡ lúc đặt); lệnh đang mở mất `stop_loss` (trailing nâng dần), và — khi nó thoát theo tín hiệu hay
    trần thời gian — cả `status`, `exit_date`, `exit_reason` (sổ chỉ ghi NGÀY KHỚP RA, nên không phân được
    OPEN với CLOSING lúc ấy; ở CLOSING, `exit_date` là ngày TÍN HIỆU ra)."""
    ngay_vao = sd.ngay10(t["entry_date"]) if t["entry_date"] else None
    ngay_ra = sd.ngay10(t["exit_date"]) if t["exit_date"] else None
    if t["status"] == "HUY" and ngay_ra is not None and ngay_ra <= ket_thuc:
        return dict(t), frozenset()              # lệnh chờ đã bị huỷ: kết thúc, không có giá vào
    if ngay_vao is None or ngay_vao > ket_thuc:
        moi = dict(t, entry_date=None, entry_price=None, exit_date=None, exit_price=None,
                   exit_reason=None, status="PENDING")
        return moi, frozenset({"stop_loss", "size_pct"})
    if ngay_ra is None or ngay_ra > ket_thuc or t["status"] in ("OPEN", "CLOSING"):
        moi = dict(t, exit_date=None, exit_price=None, exit_reason=None, status="OPEN")
        theo_tin_hieu = t["exit_reason"] in ("SIGNAL_REVERSED", "MAX_HOLD")
        return moi, frozenset({"stop_loss", "status", "exit_date", "exit_reason"} if theo_tin_hieu
                              else {"stop_loss"})
    return dict(t), frozenset()


def so_tuong_duong(lenh_thuc: list[dict], quyet_dinh: list[dict], gia: dict, vni_df, *,
                   tu_ngay: str = sd.NGAY_MO_CONG, den_ngay: str | None = None,
                   cau_hinh=None) -> dict:
    """Tầng B: phát lại cấu hình (mặc định `tu_module()`) rồi so với lệnh thật. Trả báo cáo dạng dict; không
    in, không đọc đĩa. Chỉ lệnh có `signal_date` trong `[tu_ngay, ngày cuối]` được so — lệnh có tín hiệu
    trước `tu_ngay` còn sống ở đó được CHÉP vào sổ phát lại (vị thế mang sang) chứ không so."""
    import paper_trading as pt

    cau_hinh = cau_hinh if cau_hinh is not None else pt.CauHinhVao.tu_module()
    nguon = sd.NguonVni(vni_df)
    mang = sd.vi_the_mang_sang(lenh_thuc, tu_ngay)
    tk = sd.phat_lai(cau_hinh, quyet_dinh, gia, nguon, ngay_bat_dau=tu_ngay, ngay_ket_thuc=den_ngay,
                     vi_the_mang_sang=mang)
    try:
        cuoi = tk.ngay_ket_thuc
        trong = [t for t in lenh_thuc if tu_ngay <= sd.ngay10(t["signal_date"]) <= cuoi]
        sau_cua_so = [t for t in lenh_thuc if sd.ngay10(t["signal_date"]) > cuoi]
        phat = [r for r in tk.lenh() if tu_ngay <= sd.ngay10(r["signal_date"]) <= cuoi]
        khac: list[dict] = []
        cat = {}
        for t in trong:
            moi, bo = _cat_theo_ngay_cuoi(t, cuoi)
            cat[(str(t["symbol"]), sd.ngay10(t["signal_date"]))] = (moi, bo)
        thuc_cat = [m for m, _ in cat.values()]
        for k in sd.so_sanh_lenh(thuc_cat, phat, sd.COT_TUONG_DUONG):
            if k["loai"] == "khac_o" and k["cot"] in cat[k["khoa"]][1]:
                continue
            khac.append(k)
        khoa_khac = {k["khoa"] for k in khac}
        khoa_thuc = set(cat)
        bao_cao = {
            "tu_ngay": tu_ngay, "ngay_cuoi": cuoi, "ngay_mo_cong": sd.NGAY_MO_CONG,
            "ngay_bo_may_hien_hanh": NGAY_BO_MAY_HIEN_HANH,
            "lenh_thuc_trong_cua_so": len(trong), "lenh_thuc_sau_ngay_cuoi": len(sau_cua_so),
            "lenh_phat_lai_trong_cua_so": len(phat),
            "khop_tung_o": len(khoa_thuc - khoa_khac), "khac": khac, "so_khoa_khac": len(khoa_khac),
            "tin_hieu_tu_may_hien_hanh": sum(1 for t in trong
                                             if sd.ngay10(t["signal_date"]) >= NGAY_BO_MAY_HIEN_HANH),
            "mang_sang": [(m["symbol"], m["status"]) for m in mang],
            "dem": dict(tk.dem), "vni_thieu": sorted(nguon.ngay_thieu),
            "thieu_diem": list(tk.ds_thieu_diem), "thieu_nen": list(tk.ds_thieu_nen),
            "nhan": _dem_nhan(trong),
            "cot_khong_so_duoc": sorted({(k, c) for k, (_, bo) in cat.items() for c in bo}),
        }
    finally:
        tk.dong()
    return bao_cao


def _dem_nhan(lenh: list[dict]) -> dict:
    dem: dict = {}
    for t in lenh:
        n = sd.nhan_du_lieu(t["signal_date"])
        dem[n] = dem.get(n, 0) + 1
    return dem


def ma_thoat(bao_cao: dict) -> int:
    d = bao_cao["dem"]
    if bao_cao["khac"] or d["thieu_diem"] or d["thieu_nen"] or bao_cao["vni_thieu"]:
        return MA_KHAC
    return MA_BANG_NHAU


def in_bao_cao(b: dict, ghi=print) -> None:
    d = b["dem"]
    ghi("=" * 70)
    ghi("SAN DAU / TUONG DUONG (Tang B) -- phat lai cau hinh mac dinh, so voi so THAT")
    ghi("=" * 70)
    ghi(f"NGAY_MO_CONG                 : {b['ngay_mo_cong']}")
    ghi(f"NGAY_BO_MAY_HIEN_HANH        : {b['ngay_bo_may_hien_hanh']}  (khoa_bien, BUOC 209, vao main)")
    ghi(f"Cua so phat lai              : {b['tu_ngay']} .. {b['ngay_cuoi']}  ({d['phien']} phien, "
        f"{d['buoc']} phien-ma)")
    ghi(f"Vi the mang sang dau cua so  : {len(b['mang_sang'])}  {b['mang_sang']}")
    ghi(f"Lenh THAT trong cua so       : {b['lenh_thuc_trong_cua_so']}  "
        f"(sau ngay cuoi, khong so: {b['lenh_thuc_sau_ngay_cuoi']})")
    ghi(f"Lenh phat lai trong cua so   : {b['lenh_phat_lai_trong_cua_so']}")
    ghi(f"Khop TUNG O (12 cot)         : {b['khop_tung_o']} / {b['lenh_thuc_trong_cua_so']}")
    ghi(f"Khac                         : {b['so_khoa_khac']} lenh, {len(b['khac'])} sai khac")
    ghi(f"Tin hieu >= may hien hanh    : {b['tin_hieu_tu_may_hien_hanh']} lenh trong cua so")
    ghi(f"Phien-ma thieu DIEM          : {d['thieu_diem']}   (chay chi-khop, KHONG xet vao/thoat theo diem)")
    ghi(f"Phien-ma thieu NEN           : {d['thieu_nen']}   (co quyet dinh, khong co nen)")
    for ten, ds in (("thieu diem", b["thieu_diem"]), ("thieu nen", b["thieu_nen"])):
        if ds:
            ghi(f"  {ten}: " + ", ".join(f"{m}@{n[5:]}" for m, n in ds))
    ghi(f"Quyet dinh ngoai cua so      : {d['quyet_dinh_ngoai_cua_so']}")
    ghi(f"Ngay VN-INDEX thieu          : {len(b['vni_thieu'])} {b['vni_thieu']}")
    ghi(f"Nhan du lieu (lenh that)     : {b['nhan']}")
    if b["cot_khong_so_duoc"]:
        ghi(f"Cot khong so duoc (doi qua ngay cuoi): {b['cot_khong_so_duoc']}")
    for k in b["khac"]:
        if k["loai"] == "khac_o":
            ghi(f"  KHAC  {k['khoa'][0]:6s} tin hieu {k['khoa'][1]}  cot {k['cot']:12s} "
                f"that={k['thuc']!r}  phat lai={k['phat_lai']!r}")
        else:
            ghi(f"  {k['loai'].upper():20s} {k['khoa']}")
    ghi("")
    ghi("Khong co dung sai, khong chinh gi cho khop (Quy tac 1). Ket qua nay khong dung de doi nguong/diem.")


# ── dòng lệnh ─────────────────────────────────────────────────────────────────────────────────
def lenh_tuong_duong(a) -> int:
    ra = doc_so_tam(a.so_tam) if a.so_tam else keo_so_that()
    if ra is None:
        print("CHUA DOC DUOC -- kho ngoai chua cau hinh. Khong doan gi ca.", file=sys.stderr)
        return MA_KHONG_DOC_DUOC
    lenh, qd = ra
    ma_list = sorted({str(r["symbol"]) for r in qd if sd.ngay10(r["signal_date"]) >= a.tu_ngay})
    if not ma_list:
        print(f"CHUA DOC DUOC -- khong co quyet dinh nao tu {a.tu_ngay}.", file=sys.stderr)
        return MA_KHONG_DOC_DUOC
    cuoi_qd = max(sd.ngay10(r["signal_date"]) for r in qd)
    if a.nguon_gia == "cache":
        gia = doc_gia_cache(ma_list)
        vni = doc_gia_cache(["VNINDEX"]).get("VNINDEX")
    else:
        gia = tai_gia_mang(ma_list, cuoi_qd)
        vni = tai_vni_mang(cuoi_qd)
    if not gia:
        print("CHUA DOC DUOC -- khong co chuoi gia nao.", file=sys.stderr)
        return MA_KHONG_DOC_DUOC
    print(f"gia: {len(gia)}/{len(ma_list)} ma ({a.nguon_gia}); "
          f"VN-INDEX: {'co' if vni is not None else 'KHONG co'}; "
          f"quyet dinh toi {cuoi_qd}")
    b = so_tuong_duong(lenh, qd, gia, vni, tu_ngay=a.tu_ngay, den_ngay=a.den_ngay)
    in_bao_cao(b)
    return ma_thoat(b)


def dung_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    con = ap.add_subparsers(dest="lenh", required=True)
    td = con.add_parser("tuong-duong", help="Tầng B: phát lại sổ thật, so từng ô")
    td.add_argument("--tu-ngay", default=sd.NGAY_MO_CONG, help="ngày bắt đầu của cửa sổ (mặc định NGAY_MO_CONG)")
    td.add_argument("--den-ngay", default=None, help="ngày cuối (mặc định: ngày cuối của giá)")
    td.add_argument("--so-tam", default=None, help="DB tạm đã kéo sẵn (mở chỉ đọc); không có thì kéo từ Sheets")
    td.add_argument("--nguon-gia", choices=("cache", "mang"), default="cache")
    td.set_defaults(ham=lenh_tuong_duong)
    return ap


def main(argv=None) -> int:
    a = dung_parser().parse_args(argv)
    return a.ham(a)


if __name__ == "__main__":
    sys.exit(main())
