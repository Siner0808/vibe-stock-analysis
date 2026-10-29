"""Dụng cụ I/O của sân đấu C1 (BƯỚC 240, Lát 2) — CHỈ ĐỌC với sổ và Google Sheets.

    python tools/san_dau.py tuong-duong                       # Tầng B: phát lại sổ THẬT, so từng ô
    python tools/san_dau.py tuong-duong --tu-ngay 2026-09-25  # đổi ngày bắt đầu của cửa sổ
    python tools/san_dau.py tuong-duong --so-tam <file.db>    # đọc DB tạm đã kéo sẵn (sqlite, chỉ đọc)
    python tools/san_dau.py tuong-duong --nguon-gia mang      # giá tải trực tiếp (bộ thu thập của run_daily)
    python tools/san_dau.py bang [--so-tam <file.db>] [--nguon-gia cache|mang]   # BƯỚC 242: bảng, GIÁ TRỊ ĐIỂM

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

LỆNH `bang` (BƯỚC 242, Lát 3a; đặc tả mục 8 và 10.1): phát lại đường thật, PB-001, PB-002 (từ `docs/phuong-an-bong.json`)
và dựng rổ; in MỘT hàng mỗi tài khoản với các cột mà đặc tả mục 10.1 nêu và có thể tính KHÔNG cần khoảng tin cậy —
số lệnh, lãi/lỗ cộng dồn, thước 1 (r − e×rổ, kèm cột thô r − rổ), thước 2 (phương án − đường thật), alpha từng lệnh,
sụt giảm tối đa, số phiên, nhãn "đã nhìn"/"chưa nhìn", độ phủ cổng. KTC và độ phủ KTC đến ở BƯỚC 243; mỗi hàng nói
thẳng điều đó. Mã thoát 0 khi gác bảo toàn xanh ở mọi tài khoản, 1 khi không, 2 khi không đọc được.
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


# ── lệnh `bang` (BƯỚC 242, Lát 3a): một hàng mỗi tài khoản, GIÁ TRỊ ĐIỂM, chưa có KTC ────────────
SO_PHUONG_AN = GOC / "docs" / "phuong-an-bong.json"

#: Dòng in kèm MỖI hàng: khoảng tin cậy và độ phủ chưa có ở BƯỚC này.
GHI_CHU_CHUA_CO_KTC = "KTC va do phu: den o BUOC 243 (chua co o BUOC 242, day chi la GIA TRI DIEM)"


def doc_so_phuong_an(duong=None) -> dict:
    """{id: dòng} của sổ phương án bóng; NỔ nếu một dòng không hợp lệ (luật (f) của `phuong_an_bong`)."""
    import json
    import phuong_an_bong as pab
    so = json.loads(Path(duong if duong is not None else SO_PHUONG_AN).read_text(encoding="utf-8"))
    loi = pab.vi_pham_so(so)
    if loi:
        raise ValueError("so phuong an khong hop le: " + "; ".join(loi))
    return so["phuong_an"]


def doc_bang_co_cache() -> dict:
    """Bảng cờ "trên MA50" của cache lịch sử cục bộ — CHÍNH `do_rong.BangDoRong` mà đường thật dùng
    (thư mục `backtest.data.CACHE_DIR`, nên `VIBE_CACHE_DIR` đổi được). Chỉ đọc."""
    from backtest import data as bt_data
    from do_rong import BangDoRong
    return BangDoRong(Path(bt_data.CACHE_DIR)).bang_co


def _dem_chan(tk, nguong_mua: float) -> dict:
    """{cổng: (số dòng quyết định bị cổng ấy chặn, số trong đó ĐỦ điểm mua)} của lượt phát lại. Để biết một
    phương án có THẬT SỰ khác đường thật trong cửa sổ hay chỉ khác trên giấy: thước 2 bằng 0 vì cổng của nó
    chưa chặn tín hiệu nào là một kết quả khác hẳn thước 2 bằng 0 vì hai đường vốn trùng nhau."""
    import paper_trading as pt
    dong = tk.nhat_ky.decisions()
    ra = {}
    for ten, tien_to in (("vni", pt.LY_DO_VNI), ("nghi_sau_lo", pt.LY_DO_NGHI_SAU_LO),
                         ("do_rong", pt.LY_DO_DO_RONG)):
        ds = [d for d in dong if str(d["skip_reason"]).startswith(tien_to)]
        ra[ten] = (len(ds), sum(1 for d in ds if d["score"] >= nguong_mua))
    return ra


def _khoi(tk, tk_that, gia, phien, phien_dung, ro, nhan, khai_ngay) -> dict:
    """Số đo của MỘT khối nhãn dữ liệu (đã nhìn / chưa nhìn) của một phương án, và của đường thật CHỌN
    THEO CÙNG NHÃN (nhãn theo NGÀY TÍN HIỆU của từng lệnh, đặc tả mục 4 khoản 7, nên tách theo lệnh; hai
    khối KHÔNG cộng vào nhau)."""
    def chon(t):
        return sd.nhan_du_lieu(t["signal_date"], khai_ngay) == nhan

    lenh = [t for t in tk.lenh() if chon(t)]
    ch = sd.chuoi_tai_khoan(lenh, gia, phien)
    ch_that = sd.chuoi_tai_khoan([t for t in tk_that.lenh() if chon(t)], gia, phien)
    return {"n_lenh": len(lenh), "lenh": sd.dem_lenh(lenh),
            "thuoc1": sd.thuoc_1(ch.r, ch.e, ro, phien_dung),
            "cong_don": sum(ch.r[d] for d in phien_dung),
            "thuoc2": sd.thuoc_2(ch.r, ch_that.r, phien_dung)}


def dung_bang(lenh_thuc: list[dict], quyet_dinh: list[dict], gia: dict, vni_df, bang_co: dict,
              phuong_an: dict, *, tu_ngay: str = sd.NGAY_MO_CONG, den_ngay: str | None = None,
              cau_hinh=None) -> dict:
    """Dựng bảng sân đấu: đường thật phát lại, mỗi phương án bóng của `phuong_an`, và rổ. Không in, không
    đọc đĩa. Cửa sổ kế toán bắt đầu `tu_ngay` (mặc định `NGAY_MO_CONG`); vị thế mang sang chép vào MỌI tài
    khoản. Phương án có cổng độ rộng LOẠI khỏi cửa sổ của nó các phiên thiếu độ rộng; thước 2 chỉ tính trên
    cửa sổ chung của cặp (đặc tả mục 8.2)."""
    import paper_trading as pt

    co_so = cau_hinh if cau_hinh is not None else pt.CauHinhVao.tu_module()
    mang = sd.vi_the_mang_sang(lenh_thuc, tu_ngay)
    tk_ds: list = []

    def chay(cfg, nguon):
        tk = sd.phat_lai(cfg, quyet_dinh, gia, nguon, ngay_bat_dau=tu_ngay, ngay_ket_thuc=den_ngay,
                         vi_the_mang_sang=mang)
        tk_ds.append(tk)
        return tk

    try:
        vni_that = sd.NguonVni(vni_df)
        tk_that = chay(co_so, vni_that)
        phien = sd.phien_cua_so(gia, tu_ngay, tk_that.ngay_ket_thuc)
        ro, ro_thieu = sd.loi_nhuan_ro(gia, phien)
        phien_ro = [d for d in phien if d in ro]

        def hang(ten, ma, tk, cfg_tk, nguon, vni, pa, that, phien_dung):
            khai = pa["khai_ngay"] if pa is not None else None
            lenh = tk.lenh()
            ch = sd.chuoi_tai_khoan(
                lenh, gia, phien, loc=lambda t: sd.nhan_du_lieu(t["signal_date"], khai) != sd.NHAN_MO_PHONG)
            h = {"ten": ten, "id": ma, "khai_ngay": khai, "lenh": sd.dem_lenh(lenh),
                 "nhan": sd.dem_theo_nhan(lenh, khai), "phien_dung": phien_dung, "n_phien_cua_so": len(phien),
                 "thuoc1": sd.thuoc_1(ch.r, ch.e, ro, phien_dung), "cong_don": sum(ch.r[d] for d in phien_dung),
                 "sut_giam": sd.sut_giam_toi_da(ch.r, phien_dung), "alpha_lenh": sd.alpha_tung_lenh(tk, gia),
                 "vni_thieu": [d for d in phien if vni.thieu(d)] if vni is not None else None,
                 "rong_thieu": sorted(nguon.ngay_thieu_rong) if hasattr(nguon, "ngay_thieu_rong") else None,
                 "rong_loai": [d for d in phien if d not in set(phien_dung)],
                 "dem": dict(tk.dem), "thieu_gia": ch.thieu_gia, "r": ch.r,
                 "chan": _dem_chan(tk, cfg_tk.buy_threshold),
                 "bao_toan": sd.kiem_bao_toan(lenh, gia, phien[0], phien[-1]),
                 "ds_thieu_diem": list(tk.ds_thieu_diem), "ds_thieu_nen": list(tk.ds_thieu_nen)}
            if that is not None:
                h["thuoc2"] = sd.thuoc_2(ch.r, that["r"], phien_dung)
                h["khoi"] = {nhan: _khoi(tk, tk_that, gia, phien, phien_dung, ro, nhan, khai)
                             for nhan in (sd.NHAN_DA_NHIN, sd.NHAN_CHUA_NHIN)}
            return h

        that = hang("duong that phat lai", None, tk_that, co_so, vni_that, vni_that, None, None, phien)
        ra_pa = []
        for ma, pa in sorted(phuong_an.items()):
            cfg = sd.cau_hinh_tu_phuong_an(co_so, pa)
            vni = sd.NguonVni(vni_df) if cfg.cong_vni_bat else None
            if cfg.do_rong_nguong > 0:
                nguon = sd.NguonDoRong(bang_co, vni=vni)
                thieu = set(nguon.phien_thieu(phien))
                phien_dung = [d for d in phien if d not in thieu]
            else:
                nguon = vni
                phien_dung = phien
            tk = chay(cfg, nguon)
            ra_pa.append(hang(ma, ma, tk, cfg, nguon, vni, pa, that, phien_dung))
        r_ro = {d: ro[d] for d in phien_ro}
        ro_hang = {"ten": "ro deu (mua-giu, khong phi)", "n_ma": len(gia), "phien": phien_ro,
                   "thieu": ro_thieu, "cong_don": sum(r_ro.values()),
                   "sut_giam": sd.sut_giam_toi_da(r_ro, phien_ro)}
        return {"tu_ngay": tu_ngay, "ngay_cuoi": tk_that.ngay_ket_thuc, "phien": phien,
                "mang_sang": len(mang), "that": that, "phuong_an": ra_pa, "ro": ro_hang}
    finally:
        for tk in tk_ds:
            tk.dong()


def _s(x, nd: int = 2, dau: bool = True) -> str:
    if x is None:
        return "n/a"
    return f"{x:+.{nd}f}" if dau else f"{x:.{nd}f}"


def _in_thuoc1(t1: dict, ghi, lui: str = "   ") -> None:
    ghi(f"{lui}thuoc 1 (r - e*ro): trung binh/phien GIU = {_s(t1['x_tb_giu'], 3)} diem%  "
        f"cong don = {_s(t1['x_cong_don'])}   [{t1['n_giu']} phien giu, {t1['n_khong_giu']} phien KHONG giu]")
    ghi(f"{lui}tho   (r - ro)   : trung binh/phien = {_s(t1['tho_tb'], 3)} diem%  "
        f"cong don = {_s(t1['tho_cong_don'])}   [{t1['n_phien']} phien]")


def _in_tai_khoan(h: dict, ghi) -> None:
    n = h["lenh"]
    ghi(f"   lenh dong/mo/cho/huy : {n['dong']}/{n['mo']}/{n['cho']}/{n['huy']}   nhan: {h['nhan']}")
    ghi(f"   lai/lo cong don      : {_s(h['cong_don'])} diem%   sut giam toi da = "
        f"{_s(h['sut_giam'], 2, False)}   so phien = {len(h['phien_dung'])}")
    _in_thuoc1(h["thuoc1"], ghi)
    a = h["alpha_lenh"]
    if a["alpha"] is None:
        ghi(f"   alpha tung lenh      : chua du (n={a['n']}; vs_benchmark, doi tuong KHAC hai thuoc)")
    else:
        ghi(f"   alpha tung lenh      : n={a['n']} alpha={_s(a['alpha'])} bo_qua={a['bo_qua']} "
            "(vs_benchmark, doi tuong KHAC hai thuoc)")
    if h["vni_thieu"] is not None:
        ghi(f"   do phu cong VN-INDEX : thieu {len(h['vni_thieu'])}/{h['n_phien_cua_so']} phien {h['vni_thieu']}")
    if h["rong_thieu"] is not None:
        ghi(f"   do phu cong DO RONG  : {len(h['rong_loai'])}/{h['n_phien_cua_so']} phien THIEU -> LOAI khoi cua so "
            f"cua phuong an nay {h['rong_loai']}; ngay bi hoi ma thieu: {h['rong_thieu']}")
    c = h["chan"]
    ghi(f"   tin hieu bi cong chan : (tong/du diem mua) VN-INDEX {c['vni'][0]}/{c['vni'][1]}, "
        f"nghi sau lo {c['nghi_sau_lo'][0]}/{c['nghi_sau_lo'][1]}, do rong {c['do_rong'][0]}/{c['do_rong'][1]}")
    d = h["dem"]
    ghi(f"   thieu diem/nen       : {d['thieu_diem']}/{d['thieu_nen']} phien-ma   "
        f"thieu gia: {len(h['thieu_gia'])} lenh")
    bt = h["bao_toan"]
    ghi(f"   bao toan (8.1)       : {bt['da_kiem']} lenh kiem, {bt['dong_trong_cua_so']} dong tron cua so "
        f"(+ net_return_pct), {len(bt['vi_pham'])} VI PHAM")
    for v in bt["vi_pham"][:5]:
        ghi(f"      VI PHAM bao toan {v}")


def in_bang(b: dict, ghi=print) -> None:
    ghi("=" * 74)
    ghi("SAN DAU / BANG (BUOC 242, Lat 3a) -- GIA TRI DIEM, chua co KTC / do phu (BUOC 243)")
    ghi("=" * 74)
    ghi("THAM DO -- khong bao gio len ban. Don vi: diem phan tram von (size_pct la % von ban dau).")
    ghi(f"Cua so ke toan : {b['tu_ngay']} .. {b['ngay_cuoi']}  ({len(b['phien'])} phien); "
        f"vi the mang sang tu so that, chep vao MOI tai khoan: {b['mang_sang']}")
    ghi(f"Nhan du lieu   : tin hieu < {sd.NGAY_TIEN_VE_TRUOC} = MO PHONG (loai khoi thong ke); "
        f"[{sd.NGAY_TIEN_VE_TRUOC}, khai_ngay) = DA NHIN; >= khai_ngay = CHUA NHIN (hai khoi, KHONG cong)")
    ghi("")
    t = b["that"]
    ghi(f"[1] {t['ten'].upper()}  (cau hinh = tu_module; bo may HIEN HANH replay, KHONG phai ban sao so that)")
    _in_tai_khoan(t, ghi)
    ghi(f"   {GHI_CHU_CHUA_CO_KTC}")
    for i, p in enumerate(b["phuong_an"], 2):
        ghi("")
        ghi(f"[{i}] {p['ten']}  khai_ngay {p['khai_ngay']}")
        _in_tai_khoan(p, ghi)
        t2 = p["thuoc2"]
        ghi(f"   thuoc 2 (PB - duong that): trung binh/phien = {_s(t2['tb'], 3)} diem%  cong don = "
            f"{_s(t2['cong_don'])}   [{t2['n_phien']} phien cua cua so CHUNG]")
        for nhan in (sd.NHAN_DA_NHIN, sd.NHAN_CHUA_NHIN):
            k = p["khoi"][nhan]
            ghi(f"   khoi {nhan:9s}: {k['n_lenh']} lenh {k['lenh']}  lai/lo cong don = {_s(k['cong_don'])}")
            if k["n_lenh"]:
                _in_thuoc1(k["thuoc1"], ghi, "      ")
                ghi(f"      thuoc 2: trung binh/phien = {_s(k['thuoc2']['tb'], 3)}  "
                    f"cong don = {_s(k['thuoc2']['cong_don'])}")
        ghi(f"   {GHI_CHU_CHUA_CO_KTC}")
    ro = b["ro"]
    ghi("")
    ghi(f"[{len(b['phuong_an']) + 2}] {ro['ten'].upper()}  ({ro['n_ma']} ma, luon dau tu 100%)")
    ghi(f"   phien: {len(ro['phien'])} (khong dung duoc: {len(ro['thieu'])} {ro['thieu']})")
    ghi(f"   lai/lo cong don = {_s(ro['cong_don'])} diem%   sut giam toi da = {_s(ro['sut_giam'], 2, False)}")
    ghi(f"   {GHI_CHU_CHUA_CO_KTC}")


def ma_thoat_bang(b: dict) -> int:
    """0 nếu gác bảo toàn xanh ở mọi tài khoản và không lệnh nào thiếu giá; 1 nếu không."""
    if any(h["bao_toan"]["vi_pham"] or h["thieu_gia"] for h in [b["that"], *b["phuong_an"]]):
        return MA_KHAC
    return MA_BANG_NHAU


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


def lenh_bang(a) -> int:
    ra = doc_so_tam(a.so_tam) if a.so_tam else keo_so_that()
    if ra is None:
        print("CHUA DOC DUOC -- kho ngoai chua cau hinh. Khong doan gi ca.", file=sys.stderr)
        return MA_KHONG_DOC_DUOC
    lenh, qd = ra
    phuong_an = doc_so_phuong_an(a.so_phuong_an)
    mang = sd.vi_the_mang_sang(lenh, a.tu_ngay)
    ma_list = sorted({str(r["symbol"]) for r in qd if sd.ngay10(r["signal_date"]) >= a.tu_ngay}
                     | {str(m["symbol"]) for m in mang})
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
    # Độ rộng LUÔN đọc từ cache (CHÍNH bảng mà đường thật dùng, mọi mã của thư mục), kể cả khi giá tải trực tiếp:
    # cache dừng trước ngày nào thì ngày ấy THIẾU độ rộng (không dùng độ rộng cũ) và phiên bị LOẠI khỏi PB-002.
    bang_co = doc_bang_co_cache()
    nguon_rong = f"cache {len(bang_co)} ma (do_rong.BangDoRong, nhu duong that)"
    if not bang_co:
        bang_co = sd.co_tu_gia(gia)
        nguon_rong = f"CACHE RONG -> dung {len(bang_co)} ma da tai (KHAC dinh nghia cua duong that)"
    if not gia:
        print("CHUA DOC DUOC -- khong co chuoi gia nao.", file=sys.stderr)
        return MA_KHONG_DOC_DUOC
    cuoi_gia = max(sd.ngay10(df["time"].iloc[-1]) for df in gia.values())
    print(f"gia: {len(gia)}/{len(ma_list)} ma ({a.nguon_gia}), nen cuoi {cuoi_gia}; "
          f"VN-INDEX: {'co' if vni is not None else 'KHONG co'}; quyet dinh toi {cuoi_qd}; do rong: {nguon_rong}")
    if cuoi_gia < cuoi_qd:
        print(f"CANH BAO: gia dung truoc quyet dinh cuoi ({cuoi_gia} < {cuoi_qd}); quyet dinh sau do bi bo")
    # đường thật phát lại vs sổ THẬT: nói thẳng chỗ khác (lỗi 195/196 đã sửa ở BƯỚC 241, lịch sử sổ không viết lại)
    tt = so_tuong_duong(lenh, qd, gia, vni, tu_ngay=a.tu_ngay, den_ngay=a.den_ngay)
    print(f"duong that phat lai vs so THAT (12 cot): khop tung o {tt['khop_tung_o']}/{tt['lenh_thuc_trong_cua_so']}"
          f" lenh trong cua so, khac {tt['so_khoa_khac']} lenh -- xem `tuong-duong`")
    b = dung_bang(lenh, qd, gia, vni, bang_co, phuong_an, tu_ngay=a.tu_ngay, den_ngay=a.den_ngay)
    in_bang(b)
    return ma_thoat_bang(b)


def dung_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    con = ap.add_subparsers(dest="lenh", required=True)
    bg = con.add_parser("bang", help="bảng sân đấu: giá trị điểm, chưa có KTC (BƯỚC 242)")
    bg.add_argument("--tu-ngay", default=sd.NGAY_MO_CONG, help="ngày bắt đầu cửa sổ (mặc định NGAY_MO_CONG)")
    bg.add_argument("--den-ngay", default=None, help="ngày cuối (mặc định: ngày cuối của giá)")
    bg.add_argument("--so-tam", default=None, help="DB tạm đã kéo sẵn (mở chỉ đọc); không có thì kéo từ Sheets")
    bg.add_argument("--nguon-gia", choices=("cache", "mang"), default="cache")
    bg.add_argument("--so-phuong-an", default=None, help="đường tới sổ phương án (mặc định docs/phuong-an-bong.json)")
    bg.set_defaults(ham=lenh_bang)
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
