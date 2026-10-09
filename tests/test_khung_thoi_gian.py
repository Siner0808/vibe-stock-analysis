"""Test nến tuần/tháng gộp từ nến ngày — `khung_thoi_gian` (BƯỚC 171, mốc B5).

VÌ SAO FILE NÀY TỒN TẠI
───────────────────────
Module chỉ để hiện, nhưng một nến tuần/tháng SAI NGẦM thì trông y như đúng.
Lỗi đặc trưng của việc gộp nến là NHÌN TRỘM: `resample` mặc định gắn nhãn
bằng ngày cuối tuần/tháng THEO LỊCH và giữ cả kỳ đang dở. Nên gác chính ở
đây là một tính chất, không phải vài ca: với MỌI ngày cắt t,
    gộp(dữ liệu tới t)  ==  các nến đã đóng tại t lấy từ gộp(toàn bộ).
Vế phải được dựng bằng đếm phiên của lịch (`lich_giao_dich.co_phien`) từng
ngày một, độc lập với cách module quyết định kỳ đã đóng.

Mọi test offline, dữ liệu giả. Không cần vnstock.
"""
from __future__ import annotations

import ast
import pathlib
import sys
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
import pytest

GOC = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(GOC / "tools"))

import duyet_repo  # noqa: E402
import khung_thoi_gian as kt  # noqa: E402
import lich_giao_dich  # noqa: E402

XA = datetime(2027, 6, 1, 20, 0)          # sau mọi dữ liệu giả: nến ngày nào cũng đã đóng


# ─────────────────────────────────────────────────────────────────────
# Dựng dữ liệu giả
# ─────────────────────────────────────────────────────────────────────

def _la_phien(d: date) -> bool:
    """Phiên giao dịch: năm lịch phủ thì hỏi lịch, năm khác thì ngày làm việc."""
    c = lich_giao_dich.co_phien(d.isoformat())
    return (d.weekday() < 5) if c is None else c


def _ngay(tu: str, den: str) -> list[str]:
    ds = pd.date_range(tu, den, freq="D")
    return [d.strftime("%Y-%m-%d") for d in ds if _la_phien(d.date())]


def _khung(ngays: list[str], seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n = len(ngays)
    mo = 50 + rng.normal(0, 1, n).cumsum()
    dong = mo + rng.normal(0, 0.5, n)
    return pd.DataFrame({
        "time": ngays,
        "open": mo,
        "high": np.maximum(mo, dong) + rng.uniform(0.1, 1.0, n),
        "low": np.minimum(mo, dong) - rng.uniform(0.1, 1.0, n),
        "close": dong,
        "volume": rng.integers(1_000, 9_000, n).astype(float),
    })


def _tuan_5_phien() -> pd.DataFrame:
    """Đúng một tuần đầy đủ, 5 phiên, số tay: 2026-03-02 (T2) → 2026-03-06 (T6)."""
    return pd.DataFrame({
        "time": ["2026-03-02", "2026-03-03", "2026-03-04",
                 "2026-03-05", "2026-03-06"],
        "open": [10.0, 11.0, 12.0, 11.5, 12.5],
        "high": [11.5, 12.5, 13.0, 12.8, 14.0],
        "low": [9.5, 10.5, 11.0, 10.8, 12.0],
        "close": [11.0, 12.0, 11.5, 12.5, 13.5],
        "volume": [100.0, 200.0, 300.0, 400.0, 500.0],
    })


# ─────────────────────────────────────────────────────────────────────
# Khớp số: nến dựng tay
# ─────────────────────────────────────────────────────────────────────

def test_NEN_TUAN_dung_tay_tu_5_phien():
    # Thêm tuần sau để tuần đầu chắc chắn đã đóng cả theo "có phiên sau".
    d = pd.concat([_tuan_5_phien(), pd.DataFrame({
        "time": ["2026-03-09"], "open": [13.5], "high": [14.5],
        "low": [13.0], "close": [14.0], "volume": [50.0]})], ignore_index=True)
    w = kt.gop_nen(d, "W", XA)
    assert list(w.columns) == ["time", "open", "high", "low", "close", "volume"]
    t = w.iloc[0]
    assert t["time"] == "2026-03-06"
    assert t["open"] == 10.0          # phiên ĐẦU
    assert t["high"] == 14.0          # max
    assert t["low"] == 9.5            # min
    assert t["close"] == 13.5         # phiên CUỐI
    assert t["volume"] == 1500.0      # TỔNG


def test_NEN_THANG_dung_tay():
    d = _khung(_ngay("2026-03-02", "2026-04-15"))
    t = kt.gop_nen(d, "M", XA).iloc[0]
    thang3 = d[d.time.str.startswith("2026-03")]
    assert t["time"] == thang3.time.iloc[-1]
    assert t["open"] == thang3.open.iloc[0]
    assert t["close"] == thang3.close.iloc[-1]
    assert t["high"] == thang3.high.max()
    assert t["low"] == thang3.low.min()
    assert t["volume"] == thang3.volume.sum()


def test_gop_nen_KHONG_nhan_price_multiplier_va_khong_doi_volume():
    d = _tuan_5_phien()
    d.loc[len(d)] = ["2026-03-09", 13.5, 14.5, 13.0, 14.0, 50.0]
    w = kt.gop_nen(d, "W", XA)
    assert w["high"].max() == 14.0 and w["volume"].iloc[0] == 1500.0


# ─────────────────────────────────────────────────────────────────────
# Nhãn = phiên cuối THẬT, không phải ngày cuối kỳ theo lịch
# ─────────────────────────────────────────────────────────────────────

def test_NHAN_tuan_la_phien_cuoi_that_khong_phai_Chu_nhat_hay_thu_Sau():
    # Tuần 27/04–03/05/2026: 27/04 (Giỗ Tổ), 30/04 và 01/05 nghỉ → chỉ còn 28, 29/04.
    d = _khung(_ngay("2026-04-20", "2026-05-12"))
    w = kt.gop_nen(d, "W", XA)
    assert "2026-04-29" in set(w.time)
    assert not (set(w.time) & {"2026-05-03", "2026-05-01", "2026-04-30"})
    tuan = w[w.time == "2026-04-29"].iloc[0]
    phien = d[(d.time >= "2026-04-27") & (d.time <= "2026-05-03")]
    assert len(phien) == 2
    assert tuan["volume"] == phien.volume.sum()


def test_NHAN_thang_la_phien_cuoi_that_khi_ngay_cuoi_thang_la_ngay_nghi():
    # 31/08/2026 nghỉ (Quốc khánh) → tháng 8 mang nhãn 28/08, không phải 31/08.
    d = _khung(_ngay("2026-07-01", "2026-09-15"))
    m = kt.gop_nen(d, "M", XA)
    assert "2026-08-28" in set(m.time) and "2026-08-31" not in set(m.time)


def test_KHONG_nen_nao_mang_ngay_sau_du_lieu_cua_no():
    d = _khung(_ngay("2026-01-05", "2026-08-28"))
    co = set(d.time)
    for k in kt.KHUNG_GOP:
        assert set(kt.gop_nen(d, k, XA).time) <= co, k


# ─────────────────────────────────────────────────────────────────────
# Kỳ đang dở, nến ngày đang dở, lịch không phủ
# ─────────────────────────────────────────────────────────────────────

def test_KY_DANG_DO_bi_bo():
    # Dữ liệu dừng ở thứ Tư 2026-10-07: tuần 05–11/10 còn T5, T6.
    d = _khung(_ngay("2026-09-21", "2026-10-07"))
    w = kt.gop_nen(d, "W", XA)
    assert w.time.max() == "2026-10-02"          # tuần dở KHÔNG có mặt
    assert "2026-10-07" not in set(w.time)
    m = kt.gop_nen(d, "M", XA)
    assert list(m.time) == ["2026-09-30"]        # tháng 10 dở bị bỏ


def test_KY_vua_dong_o_phien_cuoi_cua_ky_thi_GIU():
    d = _khung(_ngay("2026-09-21", "2026-10-02"))
    assert kt.gop_nen(d, "W", XA).time.max() == "2026-10-02"


def test_TUAN_co_ngay_le_giua_tuan_van_dong_o_phien_cuoi_that():
    # Tết 2026: 16–20/02 nghỉ cả tuần. Tuần 09–15/02 giao dịch đủ T2–T6;
    # tuần 16–22/02 không có phiên nào nên không có nến; tuần 23–27/02 đủ lại.
    d = _khung(_ngay("2026-02-02", "2026-03-06"))
    w = kt.gop_nen(d, "W", XA)
    assert "2026-02-13" in set(w.time)
    assert not any("2026-02-16" <= t <= "2026-02-22" for t in w.time)   # tuần nghỉ cả tuần: không nến
    assert "2026-02-27" in set(w.time)


def test_NEN_NGAY_CUOI_dang_do_bi_bo_truoc_khi_gop():
    d = _khung(_ngay("2026-09-21", "2026-10-02"))
    # Bây giờ là 10:00 sáng 02/10: nến ngày 02/10 chưa đóng → tuần chưa thể đóng.
    gio_phien = datetime(2026, 10, 2, 10, 0)
    w = kt.gop_nen(d, "W", gio_phien)
    assert w.time.max() == "2026-09-25"
    # Sau 15:30 cùng ngày thì tuần đóng và gồm cả nến 02/10.
    w2 = kt.gop_nen(d, "W", datetime(2026, 10, 2, 16, 0))
    assert w2.time.max() == "2026-10-02"
    assert w2.iloc[-1]["volume"] == d[(d.time >= "2026-09-28")].volume.sum()


def test_NAM_LICH_KHONG_PHU_thi_ky_cuoi_la_CHUA_KIEM_DUOC_va_bi_bo():
    # 2025 ngoài `lich_giao_dich` (phủ từ 2026-01-01): kỳ cuối coi như đang dở.
    d = _khung(_ngay("2025-09-01", "2025-10-31"))
    assert lich_giao_dich.co_phien("2025-10-31") is None
    m = kt.gop_nen(d, "M", XA)
    assert list(m.time) == ["2025-09-30"]        # tháng 9 đã đóng nhờ có phiên tháng 10
    # Tuần cuối cũng chưa kiểm được.
    w = kt.gop_nen(d, "W", XA)
    assert w.time.max() < "2025-10-31"
    # Nhưng mọi kỳ TRƯỚC kỳ cuối vẫn còn: không vứt cả lịch sử vì lịch không phủ.
    assert len(w) >= 8


def test_KY_CUOI_vuot_bien_lich_PHU_TOI_la_chua_kiem_duoc__ky_gon_trong_lich_thi_giu():
    d = _khung(_ngay("2026-12-01", "2026-12-31"))
    assert lich_giao_dich.PHU_TOI == "2026-12-31"
    # Tháng 12 kết thúc đúng 31/12 — nằm trong lịch, phiên cuối là 31/12 → đóng.
    assert kt.gop_nen(d, "M", XA).time.max() == "2026-12-31"
    # Tuần 28/12–03/01/2027 vượt biên lịch: không chứng minh được → bỏ.
    assert kt.gop_nen(d, "W", XA).time.max() == "2026-12-25"


def test_CUA_SO_cat_ngang_ky_dau_thi_BO_nen_dau():
    d = _khung(_ngay("2026-03-04", "2026-05-29"))      # bắt đầu giữa tháng/giữa tuần
    m = kt.gop_nen(d, "M", XA, tu_ngay="2026-03-04")
    assert m.time.iloc[0] == "2026-04-29"              # tháng 3 bị cắt (bắt đầu 04/03); 30/04 nghỉ
    w = kt.gop_nen(d, "W", XA, tu_ngay="2026-03-04")   # 04/03 là thứ Tư
    assert w.time.iloc[0] == "2026-03-13"              # tuần 02–08/03 bị cắt, bỏ
    # Không khai tu_ngay thì không bỏ (người gọi tự nhận trách nhiệm).
    assert kt.gop_nen(d, "W", XA).time.iloc[0] == "2026-03-06"


def test_DAU_VAO_rong_hoac_sai():
    assert kt.gop_nen(None, "W", XA).empty
    assert kt.gop_nen(pd.DataFrame(), "M", XA).empty
    with pytest.raises(ValueError):
        kt.gop_nen(pd.DataFrame({"time": ["2026-03-02"]}), "W", XA)
    with pytest.raises(ValueError):
        kt.gop_nen(_tuan_5_phien(), "D", XA)


def test_GOP_khong_phu_thuoc_thu_tu_va_ngay_trung():
    d = _khung(_ngay("2026-03-02", "2026-05-15"))
    xao = pd.concat([d, d.iloc[10:20]]).sample(frac=1, random_state=3)
    for k in kt.KHUNG_GOP:
        pd.testing.assert_frame_equal(kt.gop_nen(d, k, XA), kt.gop_nen(xao, k, XA))


# ─────────────────────────────────────────────────────────────────────
# GÁC CHÍNH — chống nhìn trộm: gộp rồi lọc == lọc rồi gộp
# ─────────────────────────────────────────────────────────────────────

def _cac_phien_cua_ky(nhan: str, khung: str) -> list[str]:
    """Mọi phiên theo LỊCH trong kỳ chứa `nhan`, đếm từng ngày — độc lập với module."""
    d = pd.Timestamp(nhan)
    if khung == "W":
        dau = d - timedelta(days=d.weekday())
        cuoi = dau + timedelta(days=6)
    else:
        dau = d.replace(day=1)
        cuoi = (dau + pd.offsets.MonthEnd(0))
    return [x.strftime("%Y-%m-%d") for x in pd.date_range(dau, cuoi)
            if lich_giao_dich.co_phien(x.strftime("%Y-%m-%d"))]


def _mong_doi(day_du: pd.DataFrame, khung: str, t: str) -> pd.DataFrame:
    """Các nến của `gop_nen(toàn bộ)` mà MỌI phiên theo lịch của kỳ đều <= t."""
    dong = pd.Series([max(_cac_phien_cua_ky(x, khung)) <= t for x in day_du.time],
                     index=day_du.index, dtype=bool)
    return day_du[dong].reset_index(drop=True)


@pytest.mark.parametrize("khung", kt.KHUNG_GOP)
def test_CHONG_NHIN_TROM__gop_roi_loc_bang_loc_roi_gop(khung):
    df = _khung(_ngay("2026-01-01", "2026-12-31"))
    day_du = kt.gop_nen(df, khung, XA)
    so_ngay_cat = 0
    for t in df.time:
        cat = kt.gop_nen(df[df.time <= t], khung, XA)
        pd.testing.assert_frame_equal(cat.reset_index(drop=True),
                                      _mong_doi(day_du, khung, t),
                                      obj=f"{khung} cắt tại {t}")
        so_ngay_cat += 1
    assert so_ngay_cat == len(df) > 200


@pytest.mark.parametrize("khung", kt.KHUNG_GOP)
def test_CHONG_NHIN_TROM__voi_cua_so_cat_dau(khung):
    df = _khung(_ngay("2026-01-07", "2026-09-30"))
    tu = "2026-01-07"
    day_du = kt.gop_nen(df, khung, XA, tu_ngay=tu)
    for t in df.time[::3]:
        cat = kt.gop_nen(df[df.time <= t], khung, XA, tu_ngay=tu)
        pd.testing.assert_frame_equal(cat.reset_index(drop=True),
                                      _mong_doi(day_du, khung, t))


@pytest.mark.parametrize("khung", kt.KHUNG_GOP)
def test_CHONG_NHIN_TROM__nen_ngay_dang_do_nhu_chua_tung_ton_tai(khung):
    """Ở 10:00 ngày t, nến ngày t chưa đóng: kết quả == dữ liệu tới t-1 sau giờ đóng."""
    df = _khung(_ngay("2026-02-02", "2026-06-30"))
    for t in df.time[::4]:
        sang = kt.gop_nen(df[df.time <= t], khung,
                          datetime.fromisoformat(t + "T10:00:00"))
        truoc = kt.gop_nen(df[df.time < t], khung, XA)
        pd.testing.assert_frame_equal(sang.reset_index(drop=True),
                                      truoc.reset_index(drop=True))


def test_KHONG_dung_resample_mac_dinh_la_cho_sinh_ra_nhin_trom():
    """Dựng lại kiểu nhìn trộm: nhãn ngày cuối tuần THEO LỊCH và giữ kỳ dở."""
    d = _khung(_ngay("2026-09-21", "2026-10-07")).set_index(
        pd.to_datetime(_khung(_ngay("2026-09-21", "2026-10-07")).time))
    tro = d["close"].resample("W").last()
    # Bản resample mang nhãn Chủ nhật 11/10/2026 khi dữ liệu mới tới 07/10.
    assert tro.index.max() > pd.Timestamp("2026-10-07")
    ta = kt.gop_nen(d.reset_index(drop=True), "W", XA)
    assert pd.Timestamp(ta.time.max()) <= pd.Timestamp("2026-10-07")


# ─────────────────────────────────────────────────────────────────────
# Cửa sổ dữ liệu cho W/M — suy từ chu kỳ chỉ báo dài nhất
# ─────────────────────────────────────────────────────────────────────

def _so_nen_thang_dong(den: date, so_ngay: int) -> int:
    tu = den - timedelta(days=so_ngay)
    d = _khung(_ngay(tu.isoformat(), den.isoformat()))
    return len(kt.gop_nen(d, "M", XA, tu_ngay=d.time.iloc[0]))


def _cac_ngay_ket_thuc():
    """Mỗi 5 ngày suốt 2026 — kỳ cuối lúc đóng lúc dở, kỳ đầu bị cắt ở mọi vị trí."""
    d0 = date(2026, 1, 5)
    return [d for d in (d0 + timedelta(days=i) for i in range(0, 360, 5))
            if _la_phien(d)]


def test_CUA_SO_THANG_luon_du_nen_cho_MA_dai_nhat__moi_ngay_ket_thuc():
    """Tải `NGAY_LICH_CHO_KHUNG_THANG` ngày → LUÔN đủ `CHU_KY_DAI_NHAT` nến tháng ĐÃ ĐÓNG."""
    ngay = _cac_ngay_ket_thuc()
    assert len(ngay) > 40
    thap_nhat = min(_so_nen_thang_dong(d, kt.NGAY_LICH_CHO_KHUNG_THANG) for d in ngay)
    assert thap_nhat >= kt.CHU_KY_DAI_NHAT


def test_CUA_SO_THANG_thieu_hai_ky_dem_thi_DO():
    """Cùng phép quét nhưng cửa sổ KHÔNG có hai kỳ đệm (kỳ đầu bị cắt, kỳ cuối dở)
    phải có ngày kết thúc cho ra thiếu nến — nếu không hằng số đệm là thừa."""
    ngay = _cac_ngay_ket_thuc()
    so_ngay_it = kt.ngay_lich_cho_nen_thang(kt.CHU_KY_DAI_NHAT)
    thap_nhat = min(_so_nen_thang_dong(d, so_ngay_it) for d in ngay)
    assert thap_nhat < kt.CHU_KY_DAI_NHAT


def _gan_hang(cay: ast.Module, ten: str) -> ast.expr:
    for n in cay.body:
        if isinstance(n, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == ten for t in n.targets):
            return n.value
    raise AssertionError(f"không thấy phép gán {ten}")


def _ten_trong(bt: ast.AST) -> set[str]:
    return {n.id for n in ast.walk(bt) if isinstance(n, ast.Name)}


def test_HANG_SO_cua_so_la_phep_SUY_RA__kiem_hinh_dang_bang_AST():
    cay = ast.parse((GOC / "khung_thoi_gian.py").read_text(encoding="utf-8"))
    # Dài nhất = max của hai chu kỳ MA, không gõ số.
    dn = _gan_hang(cay, "CHU_KY_DAI_NHAT")
    assert isinstance(dn, ast.Call) and dn.func.id == "max"
    assert _ten_trong(dn) == {"max", "CHU_KY_MA_NGAN", "CHU_KY_MA_DAI"}
    # Số nến tháng cần = chu kỳ dài nhất + kỳ đệm.
    nc = _gan_hang(cay, "SO_NEN_THANG_CAN")
    assert isinstance(nc, ast.BinOp) and isinstance(nc.op, ast.Add)
    assert _ten_trong(nc) == {"CHU_KY_DAI_NHAT", "SO_KY_DEM"}
    # Ngày lịch = phép tính CÓ TÊN trên số nến cần, không phải con số.
    ng = _gan_hang(cay, "NGAY_LICH_CHO_KHUNG_THANG")
    assert isinstance(ng, ast.Call) and ng.func.id == "ngay_lich_cho_nen_thang"
    assert _ten_trong(ng) == {"ngay_lich_cho_nen_thang", "SO_NEN_THANG_CAN"}
    # Tháng = năm / 12: không gõ 30,44 hay 30.
    tm = _gan_hang(cay, "NGAY_LICH_MOT_THANG")
    assert isinstance(tm, ast.BinOp) and isinstance(tm.op, ast.Div)


# ─────────────────────────────────────────────────────────────────────
# Nhãn đồng pha
# ─────────────────────────────────────────────────────────────────────

def _chuoi_close(cuoi_so_voi_ma: str, n: int = 30) -> pd.DataFrame:
    """n nến, 29 nến đầu close=100, nến cuối cao/thấp/bằng MA20."""
    close = [100.0] * (n - 1)
    close.append({"tren": 130.0, "duoi": 70.0}.get(cuoi_so_voi_ma, 100.0))
    return pd.DataFrame({"close": close})


def test_VI_TRI_tren_duoi_bang_va_chua_du():
    assert kt.vi_tri_so_voi_ma(_chuoi_close("tren"))[0] == kt.TREN
    assert kt.vi_tri_so_voi_ma(_chuoi_close("duoi"))[0] == kt.DUOI
    assert kt.vi_tri_so_voi_ma(_chuoi_close("bang"))[0] == kt.BANG
    tt, mo_ta = kt.vi_tri_so_voi_ma(_chuoi_close("tren", n=12))
    assert tt == kt.CHUA_DU and f"chưa đủ {kt.CHU_KY_MA_NGAN} nến (có 12)" == mo_ta
    # Đúng biên: thiếu MỘT nến vẫn là thiếu; đủ chu kỳ nến thì có kết luận.
    c = kt.CHU_KY_MA_NGAN
    assert kt.vi_tri_so_voi_ma(_chuoi_close("tren", n=c - 1)) == (
        kt.CHUA_DU, f"chưa đủ {c} nến (có {c - 1})")
    assert kt.vi_tri_so_voi_ma(_chuoi_close("tren", n=c))[0] == kt.TREN
    assert kt.vi_tri_so_voi_ma(None)[0] == kt.CHUA_DU


def test_VI_TRI_dung_chu_ky_MA_cua_chinh_khung():
    """Đúng MA20: 19 nến 100 + nến cuối 120 → MA20 = 101, 120 > 101 (không phải MA toàn chuỗi)."""
    d = pd.DataFrame({"close": [50.0] * 40 + [100.0] * 19 + [120.0]})
    ma20 = d.close.tail(20).mean()
    assert ma20 == 101.0 and kt.vi_tri_so_voi_ma(d)[0] == kt.TREN
    d2 = pd.DataFrame({"close": [200.0] * 40 + [100.0] * 19 + [99.0]})
    assert kt.vi_tri_so_voi_ma(d2)[0] == kt.DUOI


def test_DONG_PHA_lech_pha_dong_pha_va_chua_du():
    t, d = _chuoi_close("tren"), _chuoi_close("duoi")
    r = kt.doc_dong_pha({"D": t, "W": d, "M": t})
    assert r.dong == "D: trên · W: dưới · M: trên — lệch pha"
    assert r.ket_luan == "lệch pha"
    r = kt.doc_dong_pha({"D": t, "W": t, "M": t})
    assert r.ket_luan == "đồng pha" and "lệch" not in r.dong
    r = kt.doc_dong_pha({"D": t, "W": t, "M": _chuoi_close("tren", n=10)})
    assert "chưa đủ 20 nến (có 10)" in r.dong
    assert r.ket_luan.startswith("chưa đủ") and r.trang_thai["M"] == kt.CHUA_DU
    # Hai khung đủ nến mà khác nhau → vẫn nói được "lệch pha" dù khung thứ ba thiếu.
    r = kt.doc_dong_pha({"D": t, "W": d, "M": None})
    assert r.ket_luan == "lệch pha"
    assert kt.doc_dong_pha({}).ket_luan.startswith("chưa đủ")


# ─────────────────────────────────────────────────────────────────────
# Gác AST — CHỈ ĐỂ HIỆN: ai được nhập, app gọi gì
# ─────────────────────────────────────────────────────────────────────

def _nhap_va_goi(duong: pathlib.Path) -> tuple[set[str], set[str]]:
    cay = ast.parse(duong.read_text(encoding="utf-8"))
    nhap, goi = set(), set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            nhap |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            nhap.add(n.module.split(".")[0])
        elif isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name):
                goi.add(f.id)
            elif isinstance(f, ast.Attribute):
                goi.add(f.attr)
    return nhap, goi


def _file_ma_nguon() -> list[pathlib.Path]:
    bo = {"tests", ".venv", ".git", "node_modules", "__pycache__"}
    return [p for p in duyet_repo.duyet(GOC, "*.py")
            if not (set(p.relative_to(GOC).parts) & bo)]


def test_CHI_app_py_duoc_nhap_khung_thoi_gian():
    """Danh sách cấm cụ thể dễ bị quên khi có file mới → cho phép đúng MỘT nơi."""
    nguoi_nhap = {p.relative_to(GOC).as_posix() for p in _file_ma_nguon()
                  if "khung_thoi_gian" in _nhap_va_goi(p)[0]}
    assert nguoi_nhap == {"app.py"}, (
        f"khung_thoi_gian CHỈ ĐỂ HIỆN, chỉ app.py được nhập; đang có: {sorted(nguoi_nhap)}")


@pytest.mark.parametrize("ten", [
    "run_daily.py", "paper_trading.py", "master_agent.py", "analysis_agents.py",
    "debate_agents.py", "news_sentiment_agent.py", "fundamental_agent.py",
    "walkforward.py", "paper_runner.py", "paper_metrics.py"])
def test_duong_giao_dich_va_cham_diem_KHONG_nhap(ten):
    duong = GOC / ten
    if duong.exists():
        assert "khung_thoi_gian" not in _nhap_va_goi(duong)[0], ten
    assert not [p for p in duyet_repo.duyet(GOC / "backtest", "*.py")
                if "khung_thoi_gian" in _nhap_va_goi(p)[0]]


def test_module_chi_nhap_thu_trung_tinh():
    """Chính nó không được kéo đường giao dịch vào: chỉ pandas + hai module dữ liệu/lịch."""
    nhap, goi = _nhap_va_goi(GOC / "khung_thoi_gian.py")
    assert nhap <= {"__future__", "math", "dataclasses", "datetime", "typing",
                    "pandas", "data_quality", "lich_giao_dich"}, nhap
    assert "resample" not in goi, "resample mặc định = nhãn theo lịch + giữ kỳ dở (nhìn trộm)"
    assert "nen_cuoi_dang_do" in goi and "cac_phien" in goi


def test_APP_goi_dung_gop_nen_va_calculate_rsi_va_khong_viet_lai_chi_bao():
    duong = GOC / "app.py"
    nhap, goi = _nhap_va_goi(duong)
    assert "khung_thoi_gian" in nhap
    assert "gop_nen" in goi and "calculate_rsi" in goi
    assert "doc_dong_pha" in goi
    cay = ast.parse(duong.read_text(encoding="utf-8"))
    # calculate_rsi chỉ được ĐỊNH NGHĨA một lần: không bản RSI thứ hai cho W/M.
    dinh_nghia = [n.name for n in ast.walk(cay) if isinstance(n, ast.FunctionDef)
                  and "rsi" in n.name.lower()]
    assert dinh_nghia == ["calculate_rsi"], dinh_nghia
    # Chu kỳ MA lấy từ hằng số của module, không gõ lại 20/50 trong app.
    cung = [(k.value.value, n.lineno) for n in ast.walk(cay)
            if isinstance(n, ast.Call) for k in n.keywords
            if k.arg == "window" and isinstance(k.value, ast.Constant)
            and k.value.value in (kt.CHU_KY_MA_NGAN, kt.CHU_KY_MA_DAI)]
    assert not cung, f"app.py gõ cứng chu kỳ MA: {cung}"
    # Mọi lời gọi gop_nen trong app phải khai kỳ đầu bị cắt (tu_ngay) — thiếu thì
    # nến đầu của chuỗi thiếu phiên mà vẫn được vẽ như nến thật.
    loi_goi = [n for n in ast.walk(cay) if isinstance(n, ast.Call)
               and isinstance(n.func, ast.Attribute) and n.func.attr == "gop_nen"]
    assert len(loi_goi) >= 2
    for n in loi_goi:
        assert "tu_ngay" in {k.arg for k in n.keywords}, f"dòng {n.lineno}: thiếu tu_ngay"
    # Nạp giá W/M đi qua load_stock_data (cổng kiểm định), không thêm đường tải thứ hai.
    assert not ({"Quote", "fetch_one"} & goi), "app.py không được tải giá ngoài load_stock_data"
