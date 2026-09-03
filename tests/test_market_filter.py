"""Cổng VN-INDEX phải LỘ RA khi nó tự tắt — ô C1.

Sự cố thật, đo ngày 20/08/2026 bằng cách chạy hàm:

    market_filter.status()        = {'active': True, ... → 2026-08-07}
    is_vni_bullish('2026-08-20')  = False
    is_vni_bullish('2030-01-01')  = False

Cache dừng ở 07/08 (close 1768,06 · MA50 1799,29). `is_vni_bullish` lấy
`sub.iloc[-1]` nên với MỌI ngày sau 07/08 nó đọc đúng dòng 07/08 và trả
False vĩnh viễn — trong khi cờ `active` báo XANH vì df nạp được.

14 ngày, 0 lệnh, không ai biết. Chỗ nguy hiểm không phải *mất* dữ liệu:
mất thì fail-open còn nhìn thấy được. Nguy hiểm là **dữ liệu cũ trông
giống dữ liệu mới** — nó fail-closed âm thầm, đúng chiều tệ nhất.

Ô C1 đã chọn: quá hạn ⇒ DỪNG PHIÊN QUÉT, ngưỡng 3 phiên.

Độ cũ đo so với `signal_date` ĐANG CHẤM, không so với hôm nay — nếu không
backtest năm 2024 sẽ nổ oan trên cache chạy tới 2026.

VÀ ĐO BẰNG PHIÊN, KHÔNG BẰNG NGÀY LÀM VIỆC (31/08/2026)
Bản đầu đếm bằng `pd.bdate_range`. Ngày làm việc khác phiên giao dịch:
thị trường Việt Nam nghỉ lễ. Kỳ nghỉ Quốc khánh 31/08 → 02/09/2026 làm bộ
đếm cũ báo trễ 4 phiên vào sáng thứ Năm 03/09 — phiên đầu tiên mở lại —
trong khi dữ liệu chỉ cũ MỘT phiên. Tết cho 8–9. Xem mục cuối file.
"""
import contextlib
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import numpy as np
import pandas as pd

# Nạp một BẢN SAO RIÊNG của market_filter thay vì dùng module dùng chung.
#
# `tests/test_paper_trading.py` ghim `market_filter.is_vni_bullish` thành
# `lambda _: True` ở mức module — hợp lý cho file đó (nó kiểm sổ lệnh, không
# kiểm bộ lọc), nhưng lời ghim đó sống suốt tiến trình. File này kiểm CHÍNH
# bộ lọc, nên nếu dùng module dùng chung thì nó đo cái lambda chứ không đo
# mã thật, và kết quả đổi theo THỨ TỰ chạy — đúng loại ô nhiễm đã làm một
# test đỏ khi chạy cả bộ mà xanh khi chạy riêng.
import importlib.util as _ilu

_spec = _ilu.spec_from_file_location("market_filter_ban_sao", GOC / "market_filter.py")
mf = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(mf)


def _cache_gia(ngay_cuoi: str, n: int = 120, tren_ma: bool = True):
    """Chuỗi VN-INDEX kết thúc ở `ngay_cuoi`, nằm trên hoặc dưới MA50."""
    ngay = pd.bdate_range(end=ngay_cuoi, periods=n).strftime("%Y-%m-%d")
    if tren_ma:
        close = 1000 * np.power(1.002, np.arange(n))      # tăng dần -> trên MA
    else:
        close = 1000 * np.power(0.998, np.arange(n))      # giảm dần -> dưới MA
    return pd.DataFrame({"time": ngay, "close": close})


@contextlib.contextmanager
def _ghim(df):
    """Ghim dữ liệu cho bộ lọc, bỏ qua cache thật trên đĩa.

    Là context manager chứ không phải hàm thường: `mf._btd` là module
    `backtest.data` DÙNG CHUNG cả dự án. Vá nó rồi không trả lại thì mọi
    test chạy sau trong cùng tiến trình đều đọc dữ liệu giả — đúng loại ô
    nhiễm đã làm một test đỏ khi chạy cả bộ mà xanh khi chạy riêng.

    Cũng ghim `fetch_one` để bộ test không đi mạng: runner CI chạy offline.
    """
    goc_load, goc_fetch = mf._btd.load, mf._btd.fetch_one
    mf.get_vni_df.cache_clear()
    mf._btd.load = lambda _ma: df
    mf._btd.fetch_one = lambda *a, **k: None
    try:
        yield
    finally:
        mf._btd.load, mf._btd.fetch_one = goc_load, goc_fetch
        mf.get_vni_df.cache_clear()


def test_cache_qua_han_thi_status_bao_KHONG_hoat_dong():
    with _ghim(_cache_gia("2026-07-01")):
        st = mf.status(hom_nay="2026-08-20")
        assert st["active"] is False, f"cache cũ 7 tuần mà vẫn báo active: {st}"
        assert st.get("tuoi_phien", 0) > 3, f"không báo tuổi dữ liệu: {st}"
        print(f"PASS  cache cũ -> active=False, tuổi {st['tuoi_phien']} phiên")


def test_cache_qua_han_thi_is_vni_bullish_NO_chu_khong_tra_False():
    """Trả False lặng lẽ là chặn hết mà không ai biết — đúng lỗi 14 ngày."""
    with _ghim(_cache_gia("2026-07-01")):
        try:
            mf.is_vni_bullish("2026-08-20")
        except mf.CacheQuaHanError as e:
            assert "2026-07-01" in str(e), f"lỗi không nói dữ liệu tới ngày nào: {e}"
            print("PASS  cache quá hạn -> NỔ, không trả False lặng lẽ")
            return
        raise AssertionError("cache cũ 7 tuần mà vẫn trả về một phán quyết")


def test_cache_tuoi_trong_nguong_thi_chay_binh_thuong():
    with _ghim(_cache_gia("2026-08-18")):
        assert mf.is_vni_bullish("2026-08-20") is True
        assert mf.status(hom_nay="2026-08-20")["active"] is True
        print("PASS  lệch 2 phiên -> vẫn chạy, vẫn active")


def test_backtest_ngay_cu_KHONG_bi_no_oan():
    """Cache chạy tới 2026 mà chấm phiên 2024 thì KHÔNG hề quá hạn."""
    with _ghim(_cache_gia("2026-08-18", n=700)):
        assert mf.is_vni_bullish("2024-03-01") in (True, False)
        print("PASS  chấm ngày trong vùng dữ liệu -> không nổ")


def test_cache_giam_gia_van_tra_False_binh_thuong():
    """Quá hạn khác với xu hướng giảm. Giảm thật thì vẫn phải chặn được."""
    with _ghim(_cache_gia("2026-08-18", tren_ma=False)):
        assert mf.is_vni_bullish("2026-08-19") is False
        print("PASS  VN-INDEX dưới MA50 -> chặn, đúng chức năng")


def test_khong_co_du_lieu_thi_van_fail_open_nhung_LO_RA():
    """Mất dữ liệu thì cho qua — nhưng status phải nói ra."""
    with _ghim(None):
        assert mf.is_vni_bullish("2026-08-20") is True
        st = mf.status(hom_nay="2026-08-20")
        assert st["active"] is False and "KHÔNG" in st["note"].upper()
        print("PASS  mất dữ liệu -> fail-open, nhưng status báo TẮT")


# ─────────────────────────────────────────────────────────────────────
# `chi_so_moi_nhat` — VN-INDEX cho thanh tiêu đề
#
# Đây là ĐƯỜNG KHÁC với `get_vni_df()` ở trên, và khác có chủ ý. Bộ lọc
# phải tất định nên nó ưu tiên cache trên đĩa; thanh tiêu đề phải là phiên
# gần nhất nên nó ưu tiên mạng. Đo 22/08/2026: cache dừng ở 20/08 với
# 1.734,24 trong khi phiên 21/08 đóng 1.768,12 — lệch 1,96%.
#
# Nếu ai đó "dọn dẹp" bằng cách cho hàm này gọi lại `get_vni_df()`, thanh
# tiêu đề sẽ hiện một con số cũ trông y hệt số mới. Các test dưới đây tồn
# tại để chặn đúng lần dọn dẹp đó.
# ─────────────────────────────────────────────────────────────────────

@contextlib.contextmanager
def _ghim_nguon(mang=None, cache=None, mang_no=False):
    goc_load, goc_fetch = mf._btd.load, mf._btd.fetch_one

    def _fetch(*a, **k):
        if mang_no:
            raise ConnectionError("mạng hỏng")
        return mang

    mf._btd.fetch_one = _fetch
    mf._btd.load = lambda _ma: cache
    try:
        yield
    finally:
        mf._btd.load, mf._btd.fetch_one = goc_load, goc_fetch


def _phien(ngay_cuoi, closes):
    ngay = pd.bdate_range(end=ngay_cuoi, periods=len(closes)).strftime("%Y-%m-%d")
    return pd.DataFrame({"time": ngay, "close": list(closes)})


def test_chi_so_uu_tien_mang_hon_cache_cu():
    """Đúng con số đã đo: cache 1.734,24 (20/08) vs mạng 1.768,12 (21/08)."""
    with _ghim_nguon(mang=_phien("2026-08-21", [1734.24, 1768.12]),
                     cache=_phien("2026-08-20", [1726.69, 1734.24])):
        r = mf.chi_so_moi_nhat()
    assert r["dong_cua"] == 1768.12, "lấy phải số cũ trong cache"
    assert r["ngay"] == "2026-08-21"
    assert r["nguon"] == "mạng"
    assert r["phan_tram"] > 1.9


def test_chi_so_luon_kem_ngay_phien():
    """Số không kèm ngày là số không kiểm được — cả hai đường đều phải kèm."""
    with _ghim_nguon(mang=_phien("2026-08-21", [1734.24, 1768.12])):
        assert mf.chi_so_moi_nhat()["ngay"] == "2026-08-21"
    with _ghim_nguon(mang=None, cache=_phien("2026-08-20", [1726.69, 1734.24])):
        assert mf.chi_so_moi_nhat()["ngay"] == "2026-08-20"


def test_chi_so_lui_ve_cache_khi_mang_hong_va_NOI_RA():
    with _ghim_nguon(mang_no=True,
                     cache=_phien("2026-08-20", [1726.69, 1734.24])):
        r = mf.chi_so_moi_nhat()
    assert r["dong_cua"] == 1734.24
    assert r["nguon"] == "cache trên đĩa", "không nói nguồn thì không phân biệt được"
    assert r["loi"] is None


def test_chi_so_mat_ca_hai_nguon_thi_tra_None_chu_khong_nem():
    with _ghim_nguon(mang=None, cache=None):
        r = mf.chi_so_moi_nhat()
    assert r["dong_cua"] is None
    assert r["phan_tram"] is None
    assert r["loi"]


def test_chi_so_mot_phien_thi_khong_bia_ra_muc_khong_phan_tram():
    """Một phiên không đủ để tính thay đổi. Trả 0% là bịa một quan sát."""
    with _ghim_nguon(mang=_phien("2026-08-21", [1768.12])):
        r = mf.chi_so_moi_nhat()
    assert r["phan_tram"] is None
    assert r["dong_cua"] is None
    assert "một phiên" in r["loi"]


def test_chi_so_khong_gay_ra_boi_du_lieu_khong_sap_xep():
    """Nguồn trả ngược thứ tự thì vẫn phải lấy đúng phiên gần nhất."""
    d = _phien("2026-08-21", [1734.24, 1768.12]).iloc[::-1].reset_index(drop=True)
    with _ghim_nguon(mang=d):
        r = mf.chi_so_moi_nhat()
    assert r["dong_cua"] == 1768.12 and r["ngay"] == "2026-08-21"


def test_chi_so_KHONG_dung_lai_duong_cache_cua_bo_loc():
    """Chặn lần "dọn dẹp" gộp hai đường làm một.

    `get_vni_df()` chỉ ra mạng khi cache RỖNG. Nếu `chi_so_moi_nhat()` gọi
    nó, thì với cache cũ nhưng không rỗng, hàm sẽ trả số cũ mà vẫn ghi
    nguồn là gì đó nghe ổn.
    """
    goi = []
    goc = mf.get_vni_df
    mf.get_vni_df = lambda *a, **k: goi.append(1)
    try:
        with _ghim_nguon(mang=_phien("2026-08-21", [1734.24, 1768.12])):
            mf.chi_so_moi_nhat()
    finally:
        mf.get_vni_df = goc
    assert not goi, "chi_so_moi_nhat() đi qua đường cache của bộ lọc"


# ══ ĐẾM TRỄ BẰNG PHIÊN THẬT, KHÔNG BẰNG NGÀY LÀM VIỆC ═══════════════════
#
# `vnstock` không có API lịch giao dịch. Nhưng chuỗi giá CHÍNH LÀ bản ghi
# phiên — thị trường có phiên thì có nến. `run_daily` nạp lịch đó từ rổ
# đang quét; ở đây truyền thẳng vào để phép kiểm không phụ thuộc mạng.
#
# Bốn tình huống, và cả bốn đều phải đúng cùng lúc. Sửa được ba mà hỏng
# cái thứ ba thì là đã gỡ mất ô C1 chứ không phải sửa nó.

#: Lịch phiên thật quanh kỳ nghỉ Quốc khánh 2026: bỏ 31/08, 01/09, 02/09.
_NGHI_LE = ("2026-08-31", "2026-09-01", "2026-09-02")


def _lich_that(dau: str, cuoi: str, nghi=_NGHI_LE) -> list[str]:
    return [d.strftime("%Y-%m-%d") for d in pd.bdate_range(dau, cuoi)
            if d.strftime("%Y-%m-%d") not in nghi]


@contextlib.contextmanager
def _lich_module(ngay):
    """Nạp lịch vào mức module rồi TRẢ LẠI — `_LICH_PHIEN` dùng chung."""
    mf.ghi_nhan_lich_phien(ngay)
    try:
        yield
    finally:
        mf.quen_lich_phien()


def test_nghi_le_KHONG_bi_tinh_la_tre():
    """Ba ngày nghỉ lễ không phải ba phiên bị lỡ."""
    lich = _lich_that("2026-08-01", "2026-09-04")
    assert mf._tre_phien("2026-08-28", "2026-08-28", lich) == 0
    assert mf._tre_phien("2026-08-28", "2026-09-02", lich) == 0
    # Không có lịch quan sát thì rơi xuống lịch CÔNG BỐ — vẫn 0, vì bảng
    # cũng biết ba ngày ấy là nghỉ. Con số ngày làm việc tính TẠI CHỖ để
    # thấy khoảng cách, thay vì ghim nó như thể là hành vi của mã.
    assert mf._tre_phien("2026-08-28", "2026-09-02") == 0
    ngay_lam_viec = len(pd.bdate_range("2026-08-29", "2026-09-02"))
    assert ngay_lam_viec == 3, ngay_lam_viec
    print(f"PASS  nghỉ lễ 3 ngày -> 0 phiên trễ (ngày làm việc {ngay_lam_viec})")


def test_thu_nam_sau_nghi_le_dem_dung_MOT_phien():
    """Đây là ngày ô C1 suýt dừng cả phiên quét vì một phép đếm sai đơn vị."""
    lich = _lich_that("2026-08-01", "2026-09-04")
    ngay_lam_viec = len(pd.bdate_range("2026-08-29", "2026-09-03"))
    assert ngay_lam_viec == 4 and ngay_lam_viec > mf.TRE_TOI_DA_PHIEN

    # CẢ HAI nấc lịch phải cho 1. Sáng 03/09 chưa lượt quét nào chạy nên
    # nấc quan sát còn trống — nếu chỉ nấc ấy đúng thì báo động giả vẫn nổ.
    assert mf._tre_phien("2026-08-28", "2026-09-03", lich) == 1
    assert mf._tre_phien("2026-08-28", "2026-09-03") == 1
    assert 1 <= mf.TRE_TOI_DA_PHIEN
    print(f"PASS  03/09: ngày làm việc {ngay_lam_viec} (vượt ngưỡng) -> phiên 1")


def test_cache_CHET_that_van_bi_bat_nguyen_ven():
    """Sửa đơn vị đếm KHÔNG được làm yếu thứ ô C1 sinh ra để bắt.

    Đây là sự cố 20/08/2026 nguyên bản: cache dừng ở 07/08 trong khi cổ
    phiếu đã tới 20/08. Với lịch phiên thật, con số phải VẪN vượt ngưỡng.
    """
    lich = _lich_that("2026-08-01", "2026-08-20", nghi=())
    tre = mf._tre_phien("2026-08-07", "2026-08-20", lich)
    assert tre > mf.TRE_TOI_DA_PHIEN, f"cache chết 9 phiên mà chỉ đếm {tre}"
    print(f"PASS  cache chết thật -> {tre} phiên, vẫn vượt ngưỡng")


def test_lich_QUAN_SAT_cu_hon_moc_thi_KHONG_duoc_dung_de_dem():
    """Cái bẫy: lịch cũ hơn mốc thì đếm ra 0 và ô C1 tắt lặng lẽ.

    Bản trước chứng minh điều đó bằng con số 4 của ngày làm việc. Con số
    ấy là của ĐƯỜNG LÙI, không phải của cái bẫy — nên khi đường lùi đổi
    sang lịch công bố (03/09/2026) test cũ đỏ dù tính chất nó canh vẫn
    còn nguyên. Nay ghim thẳng tính chất: **không bao giờ ra 0**.
    """
    lich_cu = _lich_that("2026-08-01", "2026-08-28")
    tre = mf._tre_phien("2026-08-28", "2026-09-03", lich_cu)
    assert tre != 0, "lịch cũ được dùng để đếm -> ô C1 tắt lặng lẽ"
    assert tre == 1, tre
    assert mf._nguon_dem("2026-08-28", "2026-09-03",
                         lich_cu) == mf.NGUON_CONG_BO
    assert mf._lich_phu_toi("2026-09-03", lich_cu) is False
    assert mf._lich_phu_toi("2026-08-28", lich_cu) is True
    print("PASS  lịch quan sát cũ -> không dùng để đếm, không tắt lặng lẽ")


def test_NGUON_CHET_qua_ky_nghi_VAN_bi_bat():
    """Đổi đường lùi chỉ được phép bỏ báo động GIẢ, không bỏ báo động thật.

    Đây là phép kiểm cho chiều nguy hiểm của quy tắc số 1: phiên là tập
    con của ngày làm việc, nên thay đổi này chỉ có thể làm con số NHỎ ĐI.
    Ba kịch bản nguồn chết thật, không kịch bản nào được lọt.
    """
    lich_cu = _lich_that("2026-08-01", "2026-08-07")
    # cache chết 07/08 -> 20/08, đúng sự cố nguyên bản
    assert mf._tre_phien("2026-08-07", "2026-08-20", lich_cu) == 9
    # nguồn chết vắt qua Tết (5 ngày nghỉ) — nơi phần bị trừ lớn nhất
    assert mf._tre_phien("2026-02-13", "2026-03-16") == 16
    # và trọn kỳ Quốc khánh cộng vài phiên
    assert mf._tre_phien("2026-08-28", "2026-09-08") > mf.TRE_TOI_DA_PHIEN
    print("PASS  nguồn chết thật vẫn vượt ngưỡng ở cả ba kịch bản")


def test_lich_QUAN_SAT_thang_lich_CONG_BO_khi_hai_ben_lech():
    """Thứ tự nấc là một quyết định, không phải tình cờ.

    Bảng công bố biết trước ngày nghỉ đã hẹn; nó KHÔNG biết một phiên bị
    đóng đột xuất. Chuỗi giá thì biết, vì không có phiên thì không có
    nến. Nên khi lịch quan sát phủ tới mốc, nó phải thắng.
    """
    # bảng công bố nói 03/09 và 04/09 đều có phiên
    assert mf._tre_phien("2026-09-02", "2026-09-04") == 2
    # nhưng quan sát được chỉ một phiên -> quan sát thắng
    lich = ["2026-09-02", "2026-09-04"]
    assert mf._tre_phien("2026-09-02", "2026-09-04", lich) == 1
    assert mf._nguon_dem("2026-09-02", "2026-09-04",
                         lich) == mf.NGUON_QUAN_SAT
    print("PASS  lịch quan sát thắng lịch công bố khi hai bên lệch")


def test_NGOAI_pham_vi_bang_thi_lui_ve_ngay_lam_viec():
    """Bảng phủ một năm. Hết phạm vi phải LỘ RA, không được đoán tiếp."""
    assert mf._nguon_dem("2027-03-01", "2027-03-10") == mf.NGUON_LAM_VIEC
    assert mf._tre_phien("2027-03-01", "2027-03-10") == 7
    assert mf._nguon_dem("2025-12-20", "2026-01-05") == mf.NGUON_LAM_VIEC
    print("PASS  ngoài phạm vi bảng -> lùi về ngày làm việc, có tên nguồn")


def test_KHONG_CO_GI_de_dem_thi_phai_khai_dung_the():
    """Đột biến 10 sống sót vì nó không đổi con số nào — chỉ đổi LỜI KHAI.

    Bỏ nhánh `NGUON_KHONG_CAN` thì mọi phép đếm vẫn ra 0 (tổng rỗng, danh
    sách rỗng, `bdate_range` ngược đầu đều là 0), nên mọi test kiểm giá
    trị đều xanh. Cái đổi là `status()` bắt đầu khai một cuốn lịch nó
    chưa hề mở — đúng thứ thang nấc này sinh ra để chặn.

    Nên gác phải đọc thẳng lời khai, không đọc con số nó kèm theo.
    """
    assert mf._nguon_dem("2026-08-28", "2026-08-28") == mf.NGUON_KHONG_CAN
    assert mf._nguon_dem("2026-08-28", "2026-08-27") == mf.NGUON_KHONG_CAN
    assert mf._tre_phien("2026-08-28", "2026-08-27") == 0

    # Có lịch phủ tới mốc cũng KHÔNG được nhấc nó lên: không có gì để đếm
    # thì không cuốn lịch nào được ghi công.
    lich = _lich_that("2026-08-01", "2026-09-04")
    assert mf._nguon_dem("2026-08-28", "2026-08-28",
                         lich) == mf.NGUON_KHONG_CAN
    print("PASS  không có gì để đếm -> khai đúng thế, không mượn tên lịch")


def test_lich_TRUNG_LAP_khong_lam_phong_do_tre():
    """`run_daily` gom ngày phiên từ cả rổ 71 mã — trùng lặp là mặc định.

    Đếm thẳng trên danh sách thô cho ra độ trễ gấp bội và ô C1 dừng phiên
    quét vì lỗi của phép đếm. Sai theo chiều an toàn, nhưng vẫn là sai.
    """
    tho = ["2026-08-27", "2026-08-28"] * 71
    assert mf._tre_phien("2026-08-26", "2026-08-28", tho) == 2
    print("PASS  ngày phiên trùng lặp không làm phồng độ trễ")


def test_PHEP_DEM_va_TEN_NGUON_khong_the_lech_nhau():
    """Gác HÌNH DẠNG: `_tre_phien` phân nhánh theo `_nguon_dem`, chỉ vậy.

    Nếu hàm đếm tự quyết định lại bằng `_lich_phu_toi` thì có hai phép
    quyết định song song, và ngày chúng trôi khỏi nhau là ngày `status()`
    khai một nguồn trong khi đếm bằng nguồn khác. Kiểm giá trị không bắt
    được — hôm nay hai bên còn cho cùng kết quả.
    """
    import ast
    cay = ast.parse((GOC / "market_filter.py").read_text(encoding="utf-8"))
    ham = [n for n in ast.walk(cay)
           if isinstance(n, ast.FunctionDef) and n.name == "_tre_phien"]
    assert len(ham) == 1
    goi = {n.func.id for n in ast.walk(ham[0])
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert "_nguon_dem" in goi, "không hỏi nguồn, tự quyết định lấy"
    assert "_lich_phu_toi" not in goi, (
        "_tre_phien quyết định lại thang nấc — hai nguồn sự thật song song")
    ten = {n.id for n in ast.walk(ham[0]) if isinstance(n, ast.Name)}
    thieu = {"NGUON_KHONG_CAN", "NGUON_QUAN_SAT", "NGUON_CONG_BO"} - ten
    assert not thieu, f"nhánh không đi qua hằng nguồn: {thieu}"
    print("PASS  một nơi quyết định thang nấc, một nơi duy nhất")


def test_status_NOI_RA_khi_dang_uoc_tinh():
    """Một con số nghỉ lễ trông y hệt một con số cache chết nếu không nói.

    Ba nấc phải phát ra ba tên khác nhau. `uoc_tinh` giữ nghĩa HẸP — chỉ
    nấc ngày làm việc — vì đó là nấc duy nhất thật sự là phỏng đoán; gộp
    "tra bảng công bố" chung một chữ với "đo được trong lượt này" là đúng
    kiểu gộp trạng thái thứ ba vào trạng thái đầu mà dự án đã cấm.
    """
    with _ghim(_cache_gia("2026-08-28")):
        st = mf.status(hom_nay="2026-09-03")
        assert st["nguon_dem"] == mf.NGUON_CONG_BO, st
        assert st["uoc_tinh"] is False, st
        assert st["tuoi_phien"] == 1 and st["active"] is True, st

        st2 = mf.status(hom_nay="2026-09-03",
                        lich=_lich_that("2026-08-01", "2026-09-04"))
        assert st2["nguon_dem"] == mf.NGUON_QUAN_SAT, st2
        assert st2["uoc_tinh"] is False, st2
        assert st2["tuoi_phien"] == 1 and st2["active"] is True, st2

        # Ngoài phạm vi bảng thì mới là ước tính thật.
        st3 = mf.status(hom_nay="2027-01-05")
        assert st3["nguon_dem"] == mf.NGUON_LAM_VIEC, st3
        assert st3["uoc_tinh"] is True, st3
    print("PASS  status() phát ra ba nấc nguồn đếm, không gộp làm hai")


def test_nap_lich_GHI_DE_chu_khong_tich_luy():
    """Bất biến 2: cùng một gói dữ liệu phải cho cùng một kết quả.

    Tích luỹ qua lượt thì lượt thứ hai đếm trên một lịch khác lượt đầu —
    đúng cơ chế `sl_pattern_memory.json` đã làm cùng input ra 47 và 59.
    """
    with _lich_module(["2026-08-27", "2026-08-28"]):
        assert mf._tre_phien("2026-08-26", "2026-08-28") == 2
        mf.ghi_nhan_lich_phien(["2026-08-28"])
        assert mf._tre_phien("2026-08-26", "2026-08-28") == 1
    assert mf._tre_phien("2026-08-26", "2026-08-28") == 2   # lùi về ngày làm việc
    print("PASS  nạp lại là ghi đè, và quên lịch thì về hành vi lùi")


def test_may_quet_THAT_SU_nap_lich_va_doi_chieu_voi_PHIEN_CUOI():
    """Hai dây phải cắm, nếu không phép sửa này chỉ đúng trong test."""
    import ast
    cay = ast.parse((GOC / "run_daily.py").read_text(encoding="utf-8"))
    ham = [n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef)
           and n.name == "execute_daily_scan"][0]

    goi = {n.func.attr for n in ast.walk(ham)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert "ghi_nhan_lich_phien" in goi, "máy quét không nạp lịch phiên"

    st = [n for n in ast.walk(ham) if isinstance(n, ast.Call)
          and isinstance(n.func, ast.Attribute) and n.func.attr == "status"]
    assert any(k.arg == "hom_nay" for n in st for k in n.keywords), (
        "không lời gọi status() nào đối chiếu với phiên cuối của rổ — "
        "đối chiếu với date.today() thì ngày nghỉ lễ thành phiên bị lỡ")
    print("PASS  máy quét nạp lịch và đối chiếu với phiên cuối của rổ")


if __name__ == "__main__":
    for f in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        f()
