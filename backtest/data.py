"""Tải và cache dữ liệu OHLCV lịch sử để backtest chạy lặp lại được.

Nguyên tắc: tải MỘT LẦN xuống đĩa, mọi lần backtest sau đọc từ cache.
Backtest phải tất định — cùng dữ liệu vào, cùng kết quả ra.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd

# Ngưỡng độ tươi lấy TRỰC TIẾP từ data_quality để hai bên không thể lệch
# nhau. Một cache mà extend_history() coi là "đã tươi" nhưng validate_ohlcv()
# lại gắn STALE thì không công cụ nào sửa được nó — đúng tình trạng ngày
# 20/08/2026: 69% rổ bị BLOCK vì STALE mà không có đường nào làm mới.
from data_quality import STALE_WARN_DAYS, nen_cuoi_dang_do, now_vn

_CACHE_MAC_DINH = Path(__file__).parent / "cache"

# Trỏ cache sang chỗ khác bằng BIẾN MÔI TRƯỜNG, đọc lúc import.
#
# VÌ SAO CẦN, và vì sao là biến môi trường chứ không phải tham số:
# `tools/do1_chi_phi_thuc_thi.py` chạy mỗi lượt trong MỘT TIẾN TRÌNH
# RIÊNG. Gán một biến toàn cục ở tiến trình cha không đi theo sang con;
# biến môi trường thì có.
#
# Thêm 11/09/2026 cho ĐO 4. Người dùng chốt: kéo cache về 2018 vào một
# thư mục RIÊNG, giữ `backtest/cache/` nguyên vẹn làm bản neo tái lập
# cho mọi số ĐO 1/2/3 đã công bố. Lý do không hợp nhất vào cache cũ:
# nguồn đã đổi hệ số điều chỉnh (đo được tới −1,2% trên 1.172/1.217
# phiên của VNM), nên hợp nhất sẽ để vùng phải mang hệ số cũ và vùng
# trái mang hệ số hôm nay — một VẾT SẸO ở chỗ nối. Xem lỗi 31.
#
# KHÔNG đặt biến thì đường dẫn y hệt trước, tới từng ký tự — khoá bởi
# `tests/test_cache_tro_duoc.py`. Đây là thay đổi DỤNG CỤ, không phải
# thay đổi số liệu.
CACHE_DIR = Path(os.environ.get("VIBE_CACHE_DIR", "") or _CACHE_MAC_DINH)

# Ảnh chụp rổ VN30 (cập nhật 08/2026). Rổ VN30 được HOSE cơ cấu định kỳ,
# nên đây là danh sách tham chiếu — dùng --symbols để chỉ định rổ khác.
#
# CẢNH BÁO SURVIVORSHIP BIAS: backtest trên rổ VN30 HIỆN TẠI sẽ cho kết quả
# lạc quan hơn thực tế, vì các mã bị loại khỏi rổ (thường do kém) không có
# mặt. Đây là hạn chế đã biết, xem README.md.
VN30_SNAPSHOT = [
    "ACB", "BCM", "BID", "BVH", "CTG", "FPT", "GAS", "GVR", "HDB", "HPG",
    "MBB", "MSN", "MWG", "PLX", "POW", "SAB", "SHB", "SSB", "SSI", "STB",
    "TCB", "TPB", "VCB", "VHM", "VIB", "VIC", "VJC", "VNM", "VPB", "VRE",
]


def cache_path(symbol: str) -> Path:
    return CACHE_DIR / f"{symbol.upper()}.csv"


NGUON_MAC_DINH = ("kbs", "tcbs", "vci", "dnse")


def fetch_one(symbol: str, start: str, end: str, pause: float = 0.4,
              nguon: str | tuple[str, ...] | None = None) -> pd.DataFrame | None:
    """Tải OHLCV từ vnstock. Trả None nếu không lấy được (KHÔNG sinh dữ liệu giả).

    `nguon` GHIM nguồn. Mặc định `None` giữ nguyên hành vi cũ: thử lần
    lượt `kbs → tcbs → vci → dnse`, lấy cái đầu tiên có dữ liệu.

    VÌ SAO CẦN GHIM ĐƯỢC (đo 11/09/2026)
    ────────────────────────────────────
    Cách rơi-sang-nguồn-khác **không ghi lại nguồn nào đã trả lời**, mà
    hai nguồn là **hai hệ số điều chỉnh**. Lượt kéo `backtest/cache_2018/`
    ngày 11/09 có 123 mã từ `kbs` và **2 mã từ `vci`** (HT1, TCH) —
    không vì `kbs` thiếu dữ liệu, mà vì một lần hỏng tạm thời. Hỏi lại
    sau đó: `kbs` trả đủ 1.995 phiên cho cả hai.

    Giá hai nguồn KHÔNG bằng nhau. Đo trên chính ba mã ấy:

        TCH  1988/1995 dòng lệch · tỷ lệ vci/kbs TB 0,9971
        HT1   116/1995 dòng lệch · TB 0,99998
        FPT  1499/1995 dòng lệch · TB 0,99966

    Phần lớn là một hệ số gần đều nên **triệt tiêu trong lợi nhuận**,
    nhưng nó không đều tuyệt đối. Một rổ trộn hai nguồn là một rổ trộn
    hai hệ số, và **không ai biết** vì hàm này im lặng.

    Cùng họ với lỗi 30: thứ gây hại không phải việc rơi nguồn, mà việc
    rơi nguồn KHÔNG ĐƯỢC HỎI.
    """
    from vnstock import Quote

    # Nạp API key từ cấu hình NGOÀI mã nguồn (biến môi trường hoặc
    # .streamlit/secrets.toml). Idempotent, không in key ra đâu cả.
    try:
        from vnstock_auth import ensure_api_key
        ensure_api_key()
    except Exception:
        pass

    if nguon is None:
        danh_sach = NGUON_MAC_DINH
    elif isinstance(nguon, str):
        danh_sach = (nguon,)
    else:
        danh_sach = tuple(nguon)

    for src in danh_sach:
        try:
            df = Quote(symbol=symbol, source=src).history(start=start, end=end)
            if df is not None and not df.empty:
                time.sleep(1.0)          # lịch sự với API, tăng lên 1.0s để tránh block
                return df
        except Exception:
            continue
    return None


def bo_nen_dang_do(df: pd.DataFrame, bay_gio: datetime) -> pd.DataFrame:
    """Bỏ khỏi `df` mọi nến NGÀY chưa đóng (BƯỚC 180). HÀM THUẦN.

    `bay_gio` do NGƯỜI GỌI lấy MỘT lần mỗi lượt chạy (giờ VN) rồi truyền
    xuống; hàm này không hỏi đồng hồ. Luật "đã đóng hay chưa" là của
    `data_quality.nen_cuoi_dang_do`, không viết lại ở đây.

    Vì sao cache KHÔNG được chứa nến dở: lượt kéo ngày 03/09/2026 chạy lúc
    ~09:40 sáng, trong giờ giao dịch, nên dòng cuối của 72 mã là giá TẠM
    (ACB: cache 22,30, nguồn 22,20 sau khi đóng cửa — số do leader đo ở máy,
    đám mây không tái lập được). Cộng với việc `extend_history` giữ dòng CŨ
    khi trùng ngày, nến dở ấy nằm lại mãi (lỗi 163).

    Giữ nguyên dạng cột `time` của đầu vào (Timestamp hay chuỗi) để đường
    `download()` ghi ra đúng định dạng nó vẫn ghi. Lặp tới khi nến cuối đã
    đóng (một nến "tương lai" và một nến hôm nay chưa đóng cùng có mặt thì
    bỏ cả hai), nên áp hai lần cho kết quả như một lần.
    """
    if df is None or len(df) == 0 or "time" not in df.columns:
        return df
    ngay = pd.to_datetime(df["time"], errors="coerce").dt.strftime("%Y-%m-%d")
    con = sorted(set(ngay.dropna()))
    bo: set[str] = set()
    while con and nen_cuoi_dang_do(con[-1], bay_gio):
        bo.add(con.pop())
    if not bo:
        return df
    return df.loc[~ngay.isin(bo)].reset_index(drop=True)


def download(symbols: list[str], start: str, end: str,
             force: bool = False,
             bay_gio: datetime | None = None) -> dict[str, int]:
    """Tải và ghi cache. Trả về {symbol: số phiên}. Bỏ qua mã đã có cache.

    Không ghi nến chưa đóng (`bo_nen_dang_do`); `bay_gio` lấy MỘT lần cho cả lượt.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    bay_gio = bay_gio or now_vn()
    result: dict[str, int] = {}
    for i, sym in enumerate(symbols, 1):
        path = cache_path(sym)
        if path.exists() and not force:
            result[sym] = len(pd.read_csv(path))
            print(f"[{i}/{len(symbols)}] {sym}: đã có cache ({result[sym]} phiên)")
            continue
        df = fetch_one(sym, start, end)
        if df is None or df.empty:
            print(f"[{i}/{len(symbols)}] {sym}: ❌ không tải được — BỎ QUA")
            continue
        df = bo_nen_dang_do(df, bay_gio)
        if df.empty:
            print(f"[{i}/{len(symbols)}] {sym}: ❌ chỉ có nến chưa đóng — BỎ QUA")
            continue
        df.to_csv(path, index=False)
        result[sym] = len(df)
        print(f"[{i}/{len(symbols)}] {sym}: ✅ {len(df)} phiên")
    return result


#: Cache bắt đầu muộn hơn mốc yêu cầu tối đa ngần này ngày thì vẫn coi là đủ.
#: Đủ rộng để nuốt Tết Nguyên đán, quãng nghỉ dài nhất của thị trường VN.
SKIP_TOLERANCE_DAYS = 14


def _within_days(have_from: str, want_from: str, tol: int) -> bool:
    """`have_from` có sớm hơn, hoặc muộn hơn `want_from` không quá `tol` ngày?"""
    try:
        a = pd.Timestamp(have_from)
        b = pd.Timestamp(want_from)
    except Exception:
        return False
    return (a - b).days <= tol


def _norm_time(df: pd.DataFrame) -> pd.DataFrame:
    """Quy cột `time` về chuỗi YYYY-MM-DD.

    Cache trên đĩa là CSV nên `time` đọc ra là chuỗi; vnstock trả về
    Timestamp. Trộn hai loại trong cùng một cột làm mọi phép so sánh và sắp
    xếp ném TypeError. Chuẩn hoá ngay tại chỗ ghép là nơi duy nhất cần biết
    về khác biệt này.
    """
    df = df.copy()
    df["time"] = pd.to_datetime(df["time"], errors="coerce").dt.strftime("%Y-%m-%d")
    return df.dropna(subset=["time"])


# ───────────────── So cơ sở giá trước khi nối cache (BƯỚC 180) ─────────────────
#
# Nguồn giá ĐIỀU CHỈNH LÙI cả lịch sử sau mỗi sự kiện quyền (chia/thưởng cổ
# phiếu, cổ tức tiền). Cache cũ nằm ở cơ sở CŨ; lượt kéo mới nằm ở cơ sở MỚI.
# Hợp nhất giữ-dòng-cũ-khi-trùng-ngày nối hai cơ sở thành MỘT chuỗi có bậc
# giả ngay chỗ nối (HDB: −23% ở một ngày không có sự kiện nào). Nên trước
# khi hợp nhất phải SO hai bên trên các ngày TRÙNG đã đóng.

CUNG_CO_SO = "CUNG_CO_SO"
LECH_CO_SO = "LECH_CO_SO"
KHONG_SO_DUOC = "KHONG_SO_DUOC"

#: Hai bên lệch quá ngần này (|mới/cũ − 1|) ở một ngày trùng thì ngày ấy tính
#: là LỆCH. ĐỀ XUẤT, hiệu chỉnh bằng số đo leader 12/10/2026 (125 mã, đo ở
#: máy; đám mây không tái lập được): nguồn sửa số lẻ một ngày cho tỷ lệ tối
#: đa 1,0002–1,0008 (SAB, PLX, CTG, DPM, VJC) — NHỎ HƠN 0,1%; đoạn điều chỉnh
#: LÙI nhỏ nhất đo được (leader, `--doi-chieu-nguon` 12/10/2026, ≥ 5 ngày lệch)
#: là IDC 54/83 ngày ở 0,99865 (−0,13%), rồi HHV 0,99812, OCB 0,99791 — LỚN
#: HƠN 0,1%. (Đề bài từng dẫn VNM 0,9949 làm mốc: sai, VNM lệch MỘT ngày — lỗi
#: 168.) 0,1%
#: nằm giữa hai cụm, sát cụm nhiễu về phía an toàn (nghi quá thì không nối,
#: không phải nối nhầm). Viết dạng NHÂN (`|mới − cũ| > ngưỡng × cũ`), không
#: chia, để biên không phụ thuộc làm tròn dấu phẩy động.
NGUONG_LECH_CO_SO = 0.001

#: Số ngày trùng lệch tối thiểu để phán LECH_CO_SO. Một ngày lẻ là sửa số;
#: đổi cơ sở thì lệch CẢ ĐOẠN (mọi ngày trước mốc sự kiện), nên luôn ≥ 2 ngày
#: liền nhau và điều kiện "≥ 2 ngày" đã bao luôn "một đoạn liền ≥ 2 ngày".
#: ĐỀ XUẤT, cùng nguồn số đo với ngưỡng trên.
SO_NGAY_LECH_TOI_THIEU = 2


@dataclass(frozen=True)
class KetQuaCoSo:
    """Phán quyết của `so_co_so`. `ty_le_*` là mới/cũ trên các ngày trùng."""

    nhan: str
    so_ngay_trung: int = 0
    so_ngay_lech: int = 0
    ty_le_min: float | None = None
    ty_le_max: float | None = None
    ngay_lech_dau: str | None = None
    ngay_lech_cuoi: str | None = None
    ly_do: str = ""


def so_co_so(cu: pd.DataFrame | None, moi: pd.DataFrame | None,
             bay_gio: datetime) -> KetQuaCoSo:
    """Hai chuỗi giá có CÙNG cơ sở điều chỉnh không? HÀM THUẦN (BƯỚC 180).

    Không mạng, không đồng hồ, không đĩa; `bay_gio` do người gọi đưa vào.
    So `close` trên các ngày TRÙNG ĐÃ ĐÓNG: bỏ ngày CUỐI của `cu` (có thể là
    nến chưa đóng của một lượt kéo giữa phiên) và bỏ nến chưa đóng của `moi`
    (`bo_nen_dang_do`).

    Ba nhãn:
      CUNG_CO_SO     ít hơn `SO_NGAY_LECH_TOI_THIEU` ngày lệch quá
                     `NGUONG_LECH_CO_SO` — nguồn chỉ sửa số lẻ.
      LECH_CO_SO     từ `SO_NGAY_LECH_TOI_THIEU` ngày trở lên lệch — nguồn đã
                     điều chỉnh lùi (sự kiện quyền) hoặc đổi nguồn.
      KHONG_SO_DUOC  thiếu cột, rỗng, hoặc không có ngày trùng đã đóng nào.
                     Không so được thì KHÔNG được coi là "cùng cơ sở".

    GIỚI HẠN: chỉ thấy bậc lệch ≥ `NGUONG_LECH_CO_SO` ở ≥ 2 ngày trùng; chỉ
    có MỘT ngày trùng lệch thì vẫn CUNG_CO_SO (bằng chứng yếu — `so_ngay_trung`
    cho người gọi thấy); sự kiện quyền xảy ra SAU ngày cuối của cache nhưng
    nằm TRONG lượt kéo mới thì vẫn bắt được (mọi ngày cũ lệch).
    """
    if cu is None or moi is None or len(cu) == 0 or len(moi) == 0:
        return KetQuaCoSo(KHONG_SO_DUOC, ly_do="một bên rỗng")
    for ten, d in (("cache cũ", cu), ("lượt mới", moi)):
        thieu = {"time", "close"} - set(d.columns)
        if thieu:
            return KetQuaCoSo(KHONG_SO_DUOC,
                              ly_do=f"{ten} thiếu cột {sorted(thieu)}")

    c = _norm_time(cu)
    m = _norm_time(bo_nen_dang_do(moi, bay_gio))
    if len(c) == 0 or len(m) == 0:
        return KetQuaCoSo(KHONG_SO_DUOC, ly_do="một bên không có ngày hợp lệ")
    c = c[c["time"] != c["time"].max()]
    gia_c = (c.assign(close=pd.to_numeric(c["close"], errors="coerce"))
              .drop_duplicates("time").set_index("time")["close"])
    gia_m = (m.assign(close=pd.to_numeric(m["close"], errors="coerce"))
              .drop_duplicates("time").set_index("time")["close"])
    chung = sorted(gia_c.index.intersection(gia_m.index))
    pares = [(d, float(gia_c[d]), float(gia_m[d])) for d in chung
             if gia_c[d] > 0 and gia_m[d] > 0]      # NaN và ≤ 0 đều rớt
    if not pares:
        return KetQuaCoSo(KHONG_SO_DUOC,
                          ly_do="không có ngày trùng đã đóng nào so được")

    ty_le = [mo / co for _, co, mo in pares]
    lech = [d for d, co, mo in pares if abs(mo - co) > NGUONG_LECH_CO_SO * co]
    nhan = LECH_CO_SO if len(lech) >= SO_NGAY_LECH_TOI_THIEU else CUNG_CO_SO
    return KetQuaCoSo(
        nhan=nhan, so_ngay_trung=len(pares), so_ngay_lech=len(lech),
        ty_le_min=min(ty_le), ty_le_max=max(ty_le),
        ngay_lech_dau=lech[0] if lech else None,
        ngay_lech_cuoi=lech[-1] if lech else None,
        ly_do=(f"{len(lech)}/{len(pares)} ngày trùng đã đóng lệch "
               f"> {NGUONG_LECH_CO_SO:.1%}"))


def hop_nhat(cu: pd.DataFrame, moi: pd.DataFrame) -> pd.DataFrame:
    """Hợp nhất cache cũ với lượt mới. HÀM THUẦN. CHỈ gọi sau `CUNG_CO_SO`.

    Trùng ngày -> giữ bản ghi CŨ: dữ liệu cũ đã dùng để sinh các lệnh trong
    sổ, thay nó thì các kết quả trước đó không tái dựng được. NGOẠI LỆ duy
    nhất: ngày CUỐI của cache cũ lấy bản MỚI nếu lượt mới có ngày ấy, vì
    lượt kéo cũ có thể đã chạy giữa phiên và ghi giá tạm (lỗi 163).
    """
    c, m = _norm_time(cu), _norm_time(moi)
    if len(c):
        cuoi = c["time"].max()
        if (m["time"] == cuoi).any():
            c = c[c["time"] != cuoi]
    gop = pd.concat([c, m], ignore_index=True)
    return (gop.drop_duplicates(subset="time", keep="first")
               .sort_values("time").reset_index(drop=True))


def extend_history(symbols: list[str], start: str, end: str,
                   pause: float = 0.4, *,
                   thay_ca_chuoi: bool = False,
                   bay_gio: datetime | None = None,
                   bao_cao: dict[str, KetQuaCoSo] | None = None,
                   ) -> dict[str, tuple[str, str, int]]:
    """Nối dài cache VỀ QUÁ KHỨ cho những mã chưa có đủ lịch sử.

    `download()` bỏ qua mọi mã đã có file cache. Hợp lý khi chỉ cần dữ liệu
    mới, nhưng nó khiến một mã tải lần đầu với 13 tháng sẽ MÃI MÃI chỉ có 13
    tháng. Đó là lý do rổ 50 mã hiện tại có 28 mã bắt đầu từ 2025-07 trong
    khi 13 mã khác có từ 2023-11 — và vì thế giai đoạn 2024 chỉ được đại diện
    bởi một nhóm nhỏ, làm mọi kết quả nghiêng về giai đoạn gần nhất.

    Hàm này tải lại trọn khoảng rồi HỢP NHẤT với cache cũ (giữ bản ghi cũ khi
    trùng ngày), nên chạy nhiều lần vẫn an toàn.

    BƯỚC 180 — hai hàng rào trước khi ghi:
      1. **Không trộn hai cơ sở giá.** `so_co_so` so lượt mới với cache cũ
         trên các ngày trùng đã đóng; `LECH_CO_SO` hoặc `KHONG_SO_DUOC` thì
         mã ấy KHÔNG được hợp nhất, file cũ giữ nguyên từng byte. Phán quyết
         của từng mã không hợp nhất được ghi vào `bao_cao` (nếu truyền) để
         người gọi đếm. `thay_ca_chuoi=True` là lối đi CÓ CHỦ ĐÍCH: ghi đè
         trọn mã bằng MỘT lượt kéo mới (một cơ sở), kết quả đo cũ trên mã đó
         không tái lập được nữa. Mặc định False.
      2. **Không ghi nến chưa đóng** (`bo_nen_dang_do`). `bay_gio` lấy MỘT
         lần mỗi lượt chạy (giờ VN).

    Trả về {symbol: (ngày_đầu, ngày_cuối, số_phiên)} cho các mã có thay đổi.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    bay_gio = bay_gio or now_vn()
    changed: dict[str, tuple[str, str, int]] = {}

    for i, sym in enumerate(symbols, 1):
        path = cache_path(sym)
        old = pd.read_csv(path) if path.exists() else None
        if old is not None and len(old) == 0:
            old = None

        if old is not None and "time" in old.columns:
            have_from = str(old["time"].min())[:10]
            have_to = str(old["time"].max())[:10]

            # Dung sai vài ngày: mốc yêu cầu thường rơi vào ngày nghỉ hoặc
            # cuối tuần, nên phiên đầu tiên có thật luôn muộn hơn một chút.
            # So bằng dấu <= sẽ khiến những mã đó bị tải lại MỖI LẦN chạy.
            du_lich_su = _within_days(have_from, start, SKIP_TOLERANCE_DAYS)

            # Bản cũ CHỈ hỏi "lịch sử đã đủ xa chưa" nên một mã có lịch sử
            # từ 2022 mà đuôi dừng ở 2026-08-07 vẫn bị bỏ qua mãi mãi. Cộng
            # với `download()` bỏ qua mọi mã đã có cache, dự án không còn
            # đường nào đưa cache tới hiện tại — đo ngày 20/08/2026: 69% rổ
            # bị BLOCK vì STALE mà không có đường nào làm mới. Đường duy nhất
            # còn lại là `download(force=True)`, mà nó ghi đè trọn khoảng nên
            # LÀM MẤT lịch sử: VNINDEX.csv đã đi từ 1.724 phiên (2019-09-13)
            # xuống 1.655 phiên (2020-01-02) đúng theo cách đó.
            da_tuoi = _within_days(end, have_to, STALE_WARN_DAYS)

            # `thay_ca_chuoi` là lệnh kéo lại CÓ CHỦ ĐÍCH: không bỏ qua mã
            # "đã đủ và đã tươi" (đúng loại mã mà bậc điều chỉnh nằm lẫn).
            if du_lich_su and da_tuoi and not thay_ca_chuoi:
                print(f"[{i}/{len(symbols)}] {sym}: đã có {have_from} → "
                      f"{have_to} — bỏ qua")
                continue
            if du_lich_su and not thay_ca_chuoi:
                print(f"[{i}/{len(symbols)}] {sym}: lịch sử đủ nhưng đuôi cũ "
                      f"({have_to}) — nối tới {end}")
        else:
            have_from = None

        fresh = fetch_one(sym, start, end, pause=pause)
        if fresh is None or fresh.empty:
            print(f"[{i}/{len(symbols)}] {sym}: ❌ không tải được — giữ nguyên cache")
            continue

        # Cache đọc từ CSV có `time` là CHUỖI, vnstock trả về Timestamp. Nối
        # hai loại lại rồi sắp xếp thì pandas ném
        # "'<' not supported between instances of 'Timestamp' and 'str'".
        # Quy cả hai về chuỗi YYYY-MM-DD trước khi ghép.
        fresh = bo_nen_dang_do(_norm_time(fresh), bay_gio)
        if fresh.empty:
            print(f"[{i}/{len(symbols)}] {sym}: ❌ lượt mới chỉ có nến chưa "
                  f"đóng — giữ nguyên cache")
            continue

        if old is None:
            merged = fresh
        elif thay_ca_chuoi:
            mat = 0
            if "time" in old.columns:
                mat = int((_norm_time(old)["time"] < fresh["time"].min()).sum())
            ghi_mat = f" (MẤT {mat} phiên đầu của cache cũ)" if mat else ""
            print(f"[{i}/{len(symbols)}] {sym}: ⚠️ THAY CẢ CHUỖI — cache cũ "
                  f"{len(old)} phiên bị thay bằng lượt mới {len(fresh)} phiên"
                  f"{ghi_mat}; kết quả đo cũ trên mã này KHÔNG tái lập được nữa")
            merged = fresh
        else:
            kq = so_co_so(old, fresh, bay_gio)
            if bao_cao is not None:
                bao_cao[sym] = kq
            if kq.nhan == LECH_CO_SO:
                print(f"[{i}/{len(symbols)}] {sym}: ⚠️ LECH_CO_SO — "
                      f"{kq.so_ngay_lech}/{kq.so_ngay_trung} ngày trùng đã "
                      f"đóng lệch > {NGUONG_LECH_CO_SO:.1%}, tỷ lệ mới/cũ "
                      f"min {kq.ty_le_min:.6f} max {kq.ty_le_max:.6f} "
                      f"({kq.ngay_lech_dau} → {kq.ngay_lech_cuoi}) — KHÔNG "
                      f"hợp nhất, giữ nguyên cache (muốn thay cả chuỗi: "
                      f"--thay-ca-chuoi)")
                continue
            if kq.nhan != CUNG_CO_SO:
                print(f"[{i}/{len(symbols)}] {sym}: ⚠️ KHONG_SO_DUOC "
                      f"({kq.ly_do}) — KHÔNG hợp nhất, giữ nguyên cache")
                continue
            merged = hop_nhat(old, fresh)
        merged = bo_nen_dang_do(merged, bay_gio)
        merged.to_csv(path, index=False)

        d0, d1 = str(merged["time"].iloc[0])[:10], str(merged["time"].iloc[-1])[:10]
        changed[sym] = (d0, d1, len(merged))
        was = f"{have_from} → " if have_from else "(mới) "
        print(f"[{i}/{len(symbols)}] {sym}: ✅ {was}{d0}  ({len(merged)} phiên)")

    return changed


def coverage(symbols: list[str]) -> pd.DataFrame:
    """Bảng độ phủ dữ liệu: mỗi mã có từ ngày nào tới ngày nào, bao nhiêu phiên.

    Nhìn bảng này TRƯỚC khi diễn giải bất kỳ kết quả backtest nào. Một rổ mà
    nửa số mã chỉ có dữ liệu năm gần nhất sẽ cho ra con số nói về năm đó,
    không phải về cả giai đoạn ghi trên tiêu đề.
    """
    rows = []
    for sym in symbols:
        df = load(sym)
        if df is None or df.empty:
            rows.append({"symbol": sym, "from": None, "to": None, "sessions": 0})
            continue
        rows.append({"symbol": sym,
                     "from": str(df["time"].iloc[0])[:10],
                     "to": str(df["time"].iloc[-1])[:10],
                     "sessions": len(df)})
    return pd.DataFrame(rows).sort_values("from", na_position="first")


def load(symbol: str) -> pd.DataFrame | None:
    """Đọc từ cache, chuẩn hoá cột và sắp xếp theo thời gian tăng dần."""
    path = cache_path(symbol)
    if not path.exists():
        return None
    df = pd.read_csv(path)
    required = {"time", "open", "high", "low", "close", "volume"}
    if not required.issubset(df.columns):
        return None
    df = df.sort_values("time").reset_index(drop=True)
    return df


def load_all(symbols: list[str] | None = None) -> dict[str, pd.DataFrame]:
    symbols = symbols or VN30_SNAPSHOT
    out = {}
    for sym in symbols:
        df = load(sym)
        if df is not None and len(df) > 0:
            out[sym] = df
    return out
