"""Test `cau_truc_gia` — lõi pivot (BƯỚC 247, Dow Lát 1, mốc B5 mượn).

VÌ SAO FILE NÀY TỒN TẠI
───────────────────────
Mô-đun trả đỉnh/đáy kèm HAI thời điểm (`ngay_xay_ra`, `ngay_biet`). Lỗi nặng nhất của loại này
là NHÌN TRỘM: một pivot được gán vào ngày nó xảy ra thay vì ngày máy biết nó (hoặc dùng nến sau),
khiến mọi phép đo xu hướng đọc tương lai. Gác chính (đặc tả 8.1) là BẤT BIẾN KHI CẮT: nhật ký của
`df[:t+1]` phải y hệt các dòng có `chi_so_biet <= t` của nhật ký đủ — với MỌI `t`.

Bảy đột biến thuộc Lát 1 (đặc tả 8.4: 1, 2, 3, 5, 6, 9, 14) chạy bằng `va_an_toan.dot_bien` lên
`cau_truc_gia.py` với file này làm gác; kết quả ghi ở `docs/STATE.md` BƯỚC 247.

Đáp số TÍNH TAY (không dựng lại công thức của mã): các chuỗi dựng tay bên dưới có bước ±500 đồng
nên ATR14 = 500 đúng từ nến thứ 15 (true range nến đầu = 0, nên nến thứ 14 là 464,29).
"""
from __future__ import annotations

import ast
import pathlib
import sys

import numpy as np
import pandas as pd
import pytest

GOC = pathlib.Path(__file__).resolve().parent.parent
# `tools/` vào CUỐI đường tìm: có hai `cham_xac_nhan.py` (gốc và tools/); chèn `tools/` lên đầu ở đây
# (tên file xếp trước `test_cham_xac_nhan`) làm bốn mươi tám test của file kia nhập nhầm bản thứ hai.
sys.path.insert(0, str(GOC))
sys.path.append(str(GOC / "tools"))

import cau_truc_gia as C  # noqa: E402
import duyet_repo  # noqa: E402

NGUON = GOC / "cau_truc_gia.py"


# ── dựng dữ liệu ──────────────────────────────────────────────────────────────────────────
def _df(dong, cao=None, thap=None, vol=1000, bat_dau="2024-01-01"):
    dong = [float(x) for x in dong]
    return pd.DataFrame({
        "time": pd.bdate_range(bat_dau, periods=len(dong)),
        "high": dong if cao is None else cao, "low": dong if thap is None else thap,
        "close": dong, "volume": vol})


def _ngau(n, hat, gia0=30.0):
    """Bước ngẫu nhiên hạt giống cố định, CÓ cụm biến động, giá đóng cửa trên lưới 50đ (đơn vị nghìn)."""
    rng = np.random.default_rng(hat)
    sigma = np.where((np.arange(n) // 40) % 2 == 0, 0.010, 0.026)
    c = gia0 * np.exp(np.cumsum(rng.normal(0, sigma)))
    c = np.round(c / 0.05) * 0.05
    truoc = np.concatenate([[c[0]], c[:-1]])
    cao = np.maximum(c, truoc) * (1 + np.abs(rng.normal(0, 0.004, n)))
    thap = np.minimum(c, truoc) * (1 - np.abs(rng.normal(0, 0.004, n)))
    vol = rng.integers(0, 3, n) * 100_000     # có phiên volume = 0
    return pd.DataFrame({"time": pd.bdate_range("2023-01-02", periods=n), "high": cao, "low": thap,
                         "close": c, "volume": vol})


#: Chuỗi dựng tay: lên 20 bước, xuống 12, lên 15, xuống 9 (mỗi bước 500đ; đơn vị ĐỒNG, he_so_gia=1).
_TAY = ([20000 + 500 * i for i in range(21)] + [30000 - 500 * j for j in range(1, 13)]
        + [24000 + 500 * j for j in range(1, 16)] + [31500 - 500 * j for j in range(1, 10)])


def _hang(r):
    return [(p.cap, p.loai, p.chi_so_xay_ra, p.chi_so_biet, p.gia, p.nhan) for p in r.nhat_ky]


# ── 1. đáp số tính tay ────────────────────────────────────────────────────────────────────
def test_CA_DUNG_TAY_atr_hai_cap():
    """ATR=500 ⇒ nội bộ (k=2) xác nhận sau khi lùi 1.000đ, swing (k=4) sau 2.000đ.
    Đỉnh 30.000 (nến 20): nội bộ biết ở nến 22 (29.000), swing ở nến 24 (28.000).
    Đáy 24.000 (nến 32): nội bộ nến 34 (25.000), swing nến 36 (26.000).
    Đỉnh 31.500 (nến 47): nội bộ nến 49 (30.500); swing nến 51 = 29.500 = 31.500 − 4×500 ĐÚNG BẰNG
    ngưỡng (điều kiện là `<=`). Cả hai cao hơn đỉnh trước 1.500đ (> nửa bước 25đ) ⇒ HH.
    Đáy 27.000 ở nến 56 mới là CHỜ (chưa ai lùi ngược lên 1.000đ) ⇒ KHÔNG có trong nhật ký.
    Đáy ở nến 0 (20.000) không bao giờ là pivot: nó là chỗ cửa sổ bắt đầu."""
    r = C.doc_cau_truc(_df(_TAY))
    assert _hang(r) == [
        ("noi_bo", "dinh", 20, 22, 30000.0, "chua_co"),
        ("swing", "dinh", 20, 24, 30000.0, "chua_co"),
        ("noi_bo", "day", 32, 34, 24000.0, "chua_co"),
        ("swing", "day", 32, 36, 24000.0, "chua_co"),
        ("noi_bo", "dinh", 47, 49, 31500.0, "HH"),
        ("swing", "dinh", 47, 51, 31500.0, "HH"),
    ]
    assert all(p.su_kien == "xac_nhan" and p.thay_the_chi_so is None for p in r.nhat_ky)
    d = pd.bdate_range("2024-01-01", periods=len(_TAY))
    p = r.nhat_ky[0]
    assert (p.ngay_xay_ra, p.ngay_biet) == (d[20].strftime("%Y-%m-%d"), d[22].strftime("%Y-%m-%d"))


def test_pivot_CHO_khong_vao_nhat_ky():
    """Chuỗi kết thúc giữa một nhịp lên: đỉnh chờ ở nến cuối KHÔNG được ghi (đột biến 9)."""
    r = C.doc_cau_truc(_df(_TAY[:48]))                 # cắt ngay tại đỉnh 31.500 (chưa ai lùi)
    assert [p.chi_so_xay_ra for p in r.nhat_ky] == [20, 20, 32, 32]
    r2 = C.doc_cau_truc(_df(_TAY[:57]))                # kết thúc ở đáy 27.000 chờ
    assert 56 not in {p.chi_so_xay_ra for p in r2.nhat_ky}
    assert not any(p.chi_so_xay_ra >= 47 and p.chi_so_biet >= 57 for p in r2.nhat_ky)


def test_ATR_bang_0_khong_xac_nhan_gi_va_hai_pivot_cung_nen_xac_nhan_theo_thu_tu_xay_ra():
    # 6 nến lên rồi 25 nến đứng yên ở đỉnh: khi cửa sổ 14 nến toàn đứng yên, ATR = 0 và `close <= đỉnh − k×0`
    # sẽ "xác nhận" một đỉnh mà giá không lùi tick nào
    dung_yen = [30000 + 500 * i for i in range(6)] + [32500.0] * 25
    assert C.doc_cau_truc(_df(dung_yen)).nhat_ky == ()
    # ca đặc biệt: nến đầu tiên có ATR (nến 13) xác nhận được CẢ đỉnh nến 1 lẫn đáy nến 2.
    # ATR = (5.000 + 10.000 + 10×500 + 0)/14 = 1.428,57 ⇒ nội bộ k=2: ngưỡng 2.857,14.
    gia = [30000, 35000, 25000] + [25500 + 500 * j for j in range(10)] + [30000]
    assert len(gia) == 14
    r = C.doc_cau_truc(_df(gia), tham_so=(2, 4))
    assert _hang(r) == [("noi_bo", "dinh", 1, 13, 35000.0, "chua_co"),
                        ("noi_bo", "day", 2, 13, 25000.0, "chua_co")]      # cái XẢY RA SỚM ghi trước


def test_nen_dau_bang_khong_la_pivot_va_chuoi_ngan_khong_co_gi():
    d = _df([20000 + 500 * i for i in range(21)])      # chỉ tăng: đáy duy nhất là nến 0
    assert C.doc_cau_truc(d).nhat_ky == ()
    assert C.doc_cau_truc(_df([20000, 21000, 19000, 22000, 18000])).nhat_ky == ()   # < khởi động ATR
    assert C.doc_cau_truc(_df([])).nhat_ky == ()
    assert C.doc_cau_truc(_df([30000.0] * 40)).nhat_ky == ()                        # ATR = 0


# ── 2. bất biến khi cắt: gác chính (đặc tả 8.1) ───────────────────────────────────────────
def _kiem_cat(df, **kw):
    """Với MỖI t: nhật ký của df[:t+1] == các dòng đã biết tại t của nhật ký đủ."""
    day_du = C.doc_cau_truc(df, **kw)
    for t in range(len(df)):
        cat = C.doc_cau_truc(df.iloc[:t + 1], **kw)
        assert list(cat.nhat_ky) == C.nhat_ky_tai(day_du.nhat_ky, t), f"lệch khi cắt tại t={t}, {kw}"
    return day_du


@pytest.mark.parametrize("hat", [1, 2, 3])
def test_BAT_BIEN_KHI_CAT_chuoi_ngau_nhien_mac_dinh(hat):
    day_du = _kiem_cat(_ngau(220, hat), he_so_gia=1000.0)
    assert len(day_du.nhat_ky) >= 6, "chuỗi thử phải có pivot, nếu không gác này trống rỗng (lỗi 66)"


def test_BAT_BIEN_KHI_CAT_chuoi_dung_tay_va_ca_kho():
    _kiem_cat(_df(_TAY))
    # ca khó: phiên volume=0, khoá trần, giá bằng nhau, chuỗi ngắn hơn khởi động
    gia = list(_TAY[:30])
    df = _df(gia)
    df.loc[10, "volume"] = 0
    gia[20] = gia[19] * 1.07
    df["close"] = gia
    df["high"] = gia
    df["low"] = gia
    _kiem_cat(df)
    _kiem_cat(_df(_TAY[:9]))


@pytest.mark.parametrize("ho", sorted(C.LUOI))
def test_BAT_BIEN_KHI_CAT_moi_o_luoi(ho):
    for tham_so in C.LUOI[ho]:
        df = _ngau(130, 7)
        _kiem_cat(df, he_so_gia=1000.0, ho=ho, tham_so=tham_so)


def test_BAT_BIEN_KHI_CAT_dac_trung_nen_chi_phu_thuoc_tien_to():
    """Chặn tận gốc: nến thứ i của bảng cắt == nến thứ i của bảng đủ (ATR, cờ, ngày)."""
    df = _ngau(120, 4)
    day_du = C.chuan_bi_nen(df)
    for t in range(len(df)):
        assert C.chuan_bi_nen(df.iloc[:t + 1]) == day_du[:t + 1], t


def test_chay_tung_nen_bang_chay_ca_bang_va_trang_thai_la_gia_tri():
    df = _ngau(200, 5)
    he = 1000.0
    nens = C.chuan_bi_nen(df)
    tt = C.khoi_tao(he_so_gia=he)
    log, mong = [], C.doc_cau_truc(df, he_so_gia=he).nhat_ky
    anh_chup = None
    for i, nen in enumerate(nens):
        tt, moi = C.cap_nhat(tt, nen)
        log.extend(moi)
        if i == 100:
            anh_chup = (tt, len(log))
    assert tuple(log) == mong
    # trạng thái là giá trị: chạy tiếp từ ảnh chụp ở nến 100 cho cùng kết quả
    tt2, log2 = anh_chup[0], list(mong[:anh_chup[1]])
    for nen in nens[101:]:
        tt2, moi = C.cap_nhat(tt2, nen)
        log2.extend(moi)
    assert tuple(log2) == mong


# ── 3. bất biến cấu trúc của nhật ký ──────────────────────────────────────────────────────
def _hieu_luc(nhat_ky, cap):
    """Danh sách pivot HIỆU LỰC sau khi áp các dòng `thay_the`."""
    ds = []
    for p in nhat_ky:
        if p.cap != cap:
            continue
        if p.su_kien == "thay_the":
            assert ds and ds[-1].loai == p.loai and ds[-1].chi_so_xay_ra == p.thay_the_chi_so
            ds[-1] = p
        else:
            ds.append(p)
    return ds


@pytest.mark.parametrize("ho,tham_so", [(h, ts) for h in sorted(C.LUOI) for ts in C.LUOI[h]])
def test_nhat_ky_dung_hinh_dang_moi_o_luoi(ho, tham_so):
    df = _ngau(300, 11)
    he = 1000.0
    r = C.doc_cau_truc(df, he_so_gia=he, ho=ho, tham_so=tham_so)
    ngay = df["time"].dt.strftime("%Y-%m-%d").tolist()
    biet = [p.chi_so_biet for p in r.nhat_ky]
    assert biet == sorted(biet), "nhật ký phải theo thứ tự biết"
    for p in r.nhat_ky:
        assert p.chi_so_biet > p.chi_so_xay_ra
        assert (p.ngay_xay_ra, p.ngay_biet) == (ngay[p.chi_so_xay_ra], ngay[p.chi_so_biet])
        assert p.gia == df["close"].iloc[p.chi_so_xay_ra]
        assert p.cap in C.CAPS and p.loai in (C.DINH, C.DAY)
        assert p.chi_so_xay_ra > 0
    for cap in C.CAPS:
        ds = _hieu_luc(r.nhat_ky, cap)
        assert all(a.loai != b.loai for a, b in zip(ds, ds[1:])), f"không xen kẽ ở {cap}"
        for i, p in enumerate(ds):
            truoc = next((q for q in reversed(ds[:i]) if q.loai == p.loai), None)
            if truoc is None:
                assert p.nhan == C.CHUA_CO
                continue
            nua = C.nua_buoc(p.gia, he, "HOSE")
            d = p.gia - truoc.gia
            mong = (C.BANG if abs(d) <= nua else
                    (C.HH if d > 0 else C.LH) if p.loai == C.DINH else (C.HL if d > 0 else C.LL))
            assert p.nhan == mong, (cap, i)


def test_atr_moi_dong_thoa_nguong_xac_nhan_va_cuc_tri_la_cuc_tri():
    """Đối chiếu ĐỘC LẬP bằng pandas: tại nến biết, đóng cửa lùi ≥ k×ATR14 so với pivot, và không
    nến nào trong (xảy ra, biết] vượt pivot quá nửa bước. Pivot chờ không thoả → không có trong sổ."""
    df = _ngau(400, 21)
    he = 1000.0
    c = df["close"].astype(float)
    tr = pd.concat([df["high"] - df["low"], (df["high"] - c.shift(1)).abs(),
                    (df["low"] - c.shift(1)).abs()], axis=1).max(axis=1)
    tr = tr.where(df["volume"] != 0, 0.0)
    atr = tr.rolling(14).mean()
    r = C.doc_cau_truc(df, he_so_gia=he, tham_so=(2, 4))
    assert len(r.nhat_ky) > 10
    for p in r.nhat_ky:
        k = 2 if p.cap == "noi_bo" else 4
        cb = c.iloc[p.chi_so_biet]
        nua = C.nua_buoc(p.gia, he, "HOSE")
        sau = c.iloc[p.chi_so_xay_ra + 1:p.chi_so_biet + 1]
        if p.loai == C.DINH:
            assert cb <= p.gia - k * atr.iloc[p.chi_so_biet]
            assert (sau - p.gia).max() <= nua
        else:
            assert cb >= p.gia + k * atr.iloc[p.chi_so_biet]
            assert (p.gia - sau).max() <= nua


def test_hai_cap_la_hai_bo_do_doc_lap():
    df = _ngau(300, 31)
    r2 = C.doc_cau_truc(df, he_so_gia=1000.0, tham_so=(2, 4))
    r3 = C.doc_cau_truc(df, he_so_gia=1000.0, tham_so=(2, 3))
    noi = lambda r: [p for p in r.nhat_ky if p.cap == "noi_bo"]  # noqa: E731
    assert noi(r2) == noi(r3)                        # đổi k của swing không chạm nội bộ
    assert [p for p in r2.nhat_ky if p.cap == "swing"] != [p for p in r3.nhat_ky if p.cap == "swing"]


# ── 4. giá bằng nhau trên lưới bước giá (đột biến 5 và 6) ─────────────────────────────────
def _dinh_gan_bang(gia_21):
    """Lên 30.000→40.000 (bước 500), nến 21 đóng ở `gia_21`, rồi rơi 38.900. HOSE ở 40.000: bước 50,
    nửa bước 25 (he_so_gia=1)."""
    gia = [30000 + 500 * i for i in range(21)] + [gia_21, 38900.0]
    return C.doc_cau_truc(_df(gia), he_so_gia=1.0, tham_so=(2, 4))


def test_GIA_BANG_trong_nua_buoc_khong_thay_dinh_cu():
    p = _dinh_gan_bang(40010.0).nhat_ky[0]
    assert (p.loai, p.chi_so_xay_ra, p.chi_so_biet, p.gia) == ("dinh", 20, 22, 40000.0)


def test_GIA_BANG_dung_nua_buoc_van_la_bang_cuc_tri_chi_thay_khi_vuot_NGHIEM_NGAT():
    p = _dinh_gan_bang(40025.0).nhat_ky[0]           # chênh ĐÚNG 25 = nửa bước ⇒ vẫn bằng ⇒ giữ nến 20
    assert (p.chi_so_xay_ra, p.gia) == (20, 40000.0)
    p = _dinh_gan_bang(40050.0).nhat_ky[0]           # chênh 50 = một bước ⇒ đỉnh mới thay
    assert (p.chi_so_xay_ra, p.gia) == (21, 40050.0)
    p = _dinh_gan_bang(40000.0).nhat_ky[0]           # bằng hệt: giữ nến SỚM
    assert p.chi_so_xay_ra == 20


def test_GIA_BANG_doi_xung_o_day_va_o_fractal():
    """Cùng luật nửa bước cho ĐÁY (đột biến 5b) và cho họ fractal (5c): chênh ĐÚNG nửa bước = bằng."""
    def day(gia_20):
        gia = [49500 - 500 * i for i in range(20)] + [gia_20, 41100.0]     # đáy 40.000 ở nến 19
        return C.doc_cau_truc(_df(gia), he_so_gia=1.0, tham_so=(2, 4)).nhat_ky[0]
    for g in (39990.0, 39975.0, 40000.0):
        assert (day(g).loai, day(g).chi_so_xay_ra, day(g).gia) == ("day", 19, 40000.0), g
    assert (day(39950.0).chi_so_xay_ra, day(39950.0).gia) == (20, 39950.0)

    def fractal(gia):
        return C.doc_cau_truc(_df(gia), he_so_gia=1.0, ho="fractal", tham_so=(3, 8)).nhat_ky
    # nến 4 cao hơn nến 3 ĐÚNG 25 = nửa bước: không nến nào cao hơn NGHIÊM NGẶT ⇒ không có đỉnh
    assert fractal([38000, 38500, 39000, 40000, 40025, 39000, 38500, 38000, 37500, 37000]) == ()
    assert fractal([42000, 41500, 41000, 40000, 39975, 41000, 41500, 42000, 42500, 43000]) == ()
    # chênh 50 = một bước ⇒ có đỉnh / đáy
    assert [(p.loai, p.chi_so_xay_ra) for p in fractal(
        [38000, 38500, 39000, 40000, 40050, 39000, 38500, 38000, 37500, 37000])] == [("dinh", 4)]
    assert [(p.loai, p.chi_so_xay_ra) for p in fractal(
        [42000, 41500, 41000, 40000, 39950, 41000, 41500, 42000, 42500, 43000])] == [("day", 4)]


def test_NHAN_bang_khi_hai_dinh_lien_ke_trong_nua_buoc():
    def hai_dinh(gia_dinh_2):
        gia = ([30000 + 500 * i for i in range(21)]                 # đỉnh 40.000 (20)
               + [40000 - 500 * j for j in range(1, 17)]            # đáy 32.000 (36)
               + [32000 + 500 * j for j in range(1, 16)] + [gia_dinh_2]   # đỉnh 2 (52)
               + [gia_dinh_2 - 1000, gia_dinh_2 - 2000, gia_dinh_2 - 3000])
        return [p for p in C.doc_cau_truc(_df(gia), he_so_gia=1.0).nhat_ky
                if p.cap == "noi_bo" and p.loai == "dinh"]
    assert [p.nhan for p in hai_dinh(40010.0)] == ["chua_co", "bang"]
    assert [p.nhan for p in hai_dinh(40025.0)] == ["chua_co", "bang"]      # ĐÚNG nửa bước vẫn là bằng
    assert [p.nhan for p in hai_dinh(39975.0)] == ["chua_co", "bang"]
    assert [p.nhan for p in hai_dinh(40050.0)] == ["chua_co", "HH"]
    assert [p.nhan for p in hai_dinh(39950.0)] == ["chua_co", "LH"]


# ── 5. cờ nến (đột biến 14) ───────────────────────────────────────────────────────────────
def _khoa(huong):
    """Lên (hoặc xuống) 500đ mỗi nến 15 nến; nến 15 là nến MỘT GIÁ ở trần (sàn) HOSE ±7% so với
    nến trước; rồi quay đầu."""
    dau = 33000.0 if huong > 0 else 47000.0
    gia = [dau + huong * 500 * i for i in range(15)]
    cuc = gia[-1] * (1 + 0.07 * huong)
    gia += [cuc, cuc - huong * 800, cuc - huong * 2300, cuc - huong * 3800, cuc - huong * 5300]
    return gia


def test_KHOA_BIEN_gan_len_pivot_o_nen_mot_gia_sat_bien():
    for huong, nhan_khoa, loai in ((1, "KICH_TRAN", "dinh"), (-1, "KICH_SAN", "day")):
        gia = _khoa(huong)
        r = C.doc_cau_truc(_df(gia), he_so_gia=1.0, san="HOSE")
        p = next(x for x in r.nhat_ky if x.chi_so_xay_ra == 15)
        assert p.loai == loai and p.khoa_bien == nhan_khoa
        assert all(x.khoa_bien is None for x in r.nhat_ky if x.chi_so_xay_ra != 15)
    # cùng nến nhưng sàn HNX (biên 10%): +7% KHÔNG sát biên ⇒ không khoá
    r = C.doc_cau_truc(_df(_khoa(1)), he_so_gia=1.0, san="HNX")
    assert all(x.khoa_bien is None for x in r.nhat_ky)


def test_KHONG_GIAO_DICH_gan_len_pivot_va_true_range_bang_0():
    gia = list(_TAY)
    df = _df(gia)
    df.loc[20, "volume"] = 0
    r = C.doc_cau_truc(df)
    assert [(p.chi_so_xay_ra, p.khong_giao_dich) for p in r.nhat_ky if p.chi_so_xay_ra == 20] == \
        [(20, True), (20, True)]
    assert all(not p.khong_giao_dich for p in r.nhat_ky if p.chi_so_xay_ra != 20)
    # true range của nến volume=0 là 0 dù nến có biên độ: ATR14 tại nến 33 = (13×500 + 0)/14
    df2 = _df(gia)
    df2["high"] = [g + 300 for g in gia]
    df2["volume"] = 1000
    df2.loc[30, "volume"] = 0
    a = C.chuan_bi_nen(df2)[33].atr
    b = C.chuan_bi_nen(df2.assign(volume=1000))[33].atr
    assert a < b


def test_dau_vao_xau_thi_no_khong_doan():
    with pytest.raises(ValueError):
        C.doc_cau_truc(_df(_TAY), san="HSX")
    with pytest.raises(ValueError):
        C.doc_cau_truc(_df(_TAY), ho="elliott")
    with pytest.raises(ValueError):
        C.doc_cau_truc(_df(_TAY), tham_so=(4, 2))
    with pytest.raises(ValueError):
        C.doc_cau_truc(_df(_TAY), he_so_gia=0)
    with pytest.raises(ValueError):
        C.doc_cau_truc(_df(_TAY).iloc[::-1])             # thời gian giảm
    xau = _df(_TAY)
    xau.loc[5, "close"] = float("nan")
    with pytest.raises(ValueError):
        C.doc_cau_truc(xau)
    with pytest.raises(ValueError):
        C.doc_cau_truc(_df(_TAY).drop(columns=["low"]))


# ── 6. họ fractal và zigzag: ca dựng tay ──────────────────────────────────────────────────
_FR = [1000, 1020, 1040, 1100, 1060, 1040, 1020, 1010, 1010, 1030, 1050, 1070]


def test_FRACTAL_dung_tay_ngay_biet_la_n_nen_sau():
    gia = [1000, 1020, 1040, 1100, 1060, 1040, 1020, 1010, 1030, 1050, 1070, 1090, 1080, 1060, 1040]
    r = C.doc_cau_truc(_df(gia), he_so_gia=1.0, ho="fractal", tham_so=(3, 8))
    assert [(p.cap, p.loai, p.chi_so_xay_ra, p.chi_so_biet, p.gia, p.nhan) for p in r.nhat_ky] == [
        ("noi_bo", "dinh", 3, 6, 1100.0, "chua_co"),
        ("noi_bo", "day", 7, 10, 1010.0, "chua_co"),
        ("noi_bo", "dinh", 11, 14, 1090.0, "LH"),
    ]


def test_FRACTAL_xen_ke_hai_dinh_lien_nhau_thi_giu_cuc_tri_hon():
    # đáy giữa là CAO NGANG (1010, 1010): không nến nào thấp hơn NGHIÊM NGẶT ⇒ không có đáy ⇒ hai đỉnh liền nhau
    gia_cao = _FR + [1120, 1090, 1070, 1050]
    r = C.doc_cau_truc(_df(gia_cao), he_so_gia=1.0, ho="fractal", tham_so=(3, 8))
    assert [(p.su_kien, p.chi_so_xay_ra, p.chi_so_biet, p.gia, p.thay_the_chi_so, p.nhan) for p in r.nhat_ky] == [
        ("xac_nhan", 3, 6, 1100.0, None, "chua_co"),
        ("thay_the", 12, 15, 1120.0, 3, "chua_co"),
    ]
    thap = C.doc_cau_truc(_df(_FR + [1090, 1070, 1050, 1030]), he_so_gia=1.0, ho="fractal", tham_so=(3, 8))
    assert [(p.su_kien, p.chi_so_xay_ra) for p in thap.nhat_ky] == [("xac_nhan", 3)]    # đỉnh thấp hơn bị bỏ
    bang = C.doc_cau_truc(_df(_FR + [1100, 1070, 1050, 1030]), he_so_gia=1.0, ho="fractal", tham_so=(3, 8))
    assert [(p.su_kien, p.chi_so_xay_ra) for p in bang.nhat_ky] == [("xac_nhan", 3)]    # bằng nhau: giữ cái sớm
    assert [p.chi_so_xay_ra for p in _hieu_luc(r.nhat_ky, "noi_bo")] == [12]


def test_ZIGZAG_dung_tay_nguong_ty_le_theo_cuc_tri():
    gia = [100 + 2 * i for i in range(11)] + [117, 113, 110, 107, 104, 100]   # đỉnh 120 ở nến 10
    r = C.doc_cau_truc(_df(gia), he_so_gia=1000.0, ho="zigzag", tham_so=(0.05, 0.10))
    assert [(p.cap, p.loai, p.chi_so_xay_ra, p.chi_so_biet, p.gia) for p in r.nhat_ky] == [
        ("noi_bo", "dinh", 10, 12, 120.0),     # 113 ≤ 120 × 0,95 = 114
        ("swing", "dinh", 10, 14, 120.0),      # 107 ≤ 120 × 0,90 = 108
    ]


def test_luoi_du_muoi_o_va_mac_dinh():
    assert sum(len(v) for v in C.LUOI.values()) == 10
    assert C.MAC_DINH == ("atr", (2, 4)) and (2, 4) in C.LUOI["atr"]
    assert C.CHU_KY_ATR == 14


# ── 7. gác AST: không cửa sổ căn giữa, không nhìn tới (đặc tả 8.2) ────────────────────────
CAM_GOI = {"roll", "argrelextrema", "find_peaks", "argrelmax", "argrelmin"}


def _am(n):
    return (isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub)) or \
        (isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and n.value < 0)


def vi_pham_nhin_toi(src: str) -> tuple[list[str], int]:
    """(các vi phạm, số nút AST đã duyệt). Đọc AST, không đọc chuỗi: chú thích và docstring không lọt."""
    cay = ast.parse(src)
    nut = list(ast.walk(cay))
    bien_vong = set()
    for n in nut:
        if isinstance(n, (ast.For, ast.comprehension)):
            bien_vong |= {x.id for x in ast.walk(n.target) if isinstance(x, ast.Name)}
    loi = []
    for n in nut:
        if isinstance(n, ast.Call):
            ten = n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", "")
            if ten in CAM_GOI:
                loi.append(f"gọi {ten} (nhìn hai phía)")
            for kw in n.keywords:
                if kw.arg == "center" and not (isinstance(kw.value, ast.Constant) and kw.value.value is False):
                    loi.append("center=… (cửa sổ căn giữa)")
                if kw.arg == "periods" and _am(kw.value) and ten == "shift":
                    loi.append("shift(periods âm)")
            if ten == "shift" and n.args and _am(n.args[0]):
                loi.append("shift(đối số âm)")
        if isinstance(n, ast.Subscript):
            for x in ast.walk(n.slice):
                if isinstance(x, ast.BinOp) and isinstance(x.op, ast.Add) and any(
                        isinstance(y, ast.Name) and y.id in bien_vong for y in ast.walk(x)):
                    loi.append("chỉ số dạng …[biến_vòng + k]")
                    break
    return loi, len(nut)


def test_GAC_AST_mo_dun_khong_nhin_toi():
    loi, so_nut = vi_pham_nhin_toi(NGUON.read_text(encoding="utf-8"))
    assert so_nut > 500, "quần thể gác phải khác rỗng (lỗi 66)"
    assert loi == [], loi


@pytest.mark.parametrize("ma,mong", [
    ("x = s.rolling(14, center=True).mean()", "center"),
    ("x = s.shift(-1)", "shift"),
    ("x = s.shift(periods=-3)", "shift"),
    ("x = s.shift(-(n // 2))", "shift"),
    ("for t in range(9):\n    y = a[t + 1]", "chỉ số"),
    ("y = [a[i + 2] for i in range(5)]", "chỉ số"),
    ("import numpy as np\nx = np.roll(a, -1)", "roll"),
    ("x = find_peaks(a)", "find_peaks"),
    ("x = signal.argrelextrema(a, np.greater)", "argrelextrema"),
])
def test_gac_AST_bat_duoc_kieu_nhin_toi_da_thay_ngoai_doi(ma, mong):
    loi, _ = vi_pham_nhin_toi(ma)
    assert loi and any(mong in x for x in loi), (ma, loi)


@pytest.mark.parametrize("ma", [
    "x = s.shift(1)", "x = s.rolling(14, min_periods=14).mean()", "x = s.rolling(14, center=False).mean()",
    "for t in range(9):\n    y = a[t - 1]", "y = a[-(2 * n + 1):]",
    "# s.shift(-1)\nx = 'center=True'\n\"\"\"find_peaks\"\"\"",
])
def test_gac_AST_khong_bat_nham_kieu_nhin_lui_va_chu_thich(ma):
    assert vi_pham_nhin_toi(ma)[0] == []


# ── 8. gác nhập (đặc tả 8.3, phần mô-đun) ─────────────────────────────────────────────────
def _nhap_va_goi(duong: pathlib.Path):
    cay = ast.parse(duong.read_text(encoding="utf-8"))
    nhap, goi = set(), set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            nhap |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            nhap.add(n.module.split(".")[0])
        elif isinstance(n, ast.Call):
            f = n.func
            goi.add(f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else "")
    return nhap, goi


def _file_ma_nguon():
    bo = {"tests", ".venv", ".git", "node_modules", "__pycache__"}
    return [p for p in duyet_repo.duyet(GOC, "*.py") if not (set(p.relative_to(GOC).parts) & bo)]


#: Người được nhập: đặc tả 8.3 (`app.py` ở Lát 3, `tools/do_dow_cau_truc.py` ở Lát 4) và dụng cụ MÔ TẢ
#: của Lát 1. Danh sách ĐÓNG: file mới nào nhập mô-đun đều đỏ.
#: BƯỚC 307 (Dow phần 2, Lát 1; người dùng "duyệt" 25/11/2026, khuyến nghị 5): thêm đúng MỘT dòng, tên mô-đun
#: của Lát 2. Chưa file nào nhập nó ở Lát 1, nên dòng này chưa có phát đột biến nào canh được.
CHO_PHEP_NHAP = {"app.py", "tools/do_dow_cau_truc.py", "tools/mo_ta_cau_truc_gia.py", "dow_hai_chi_so.py"}
#: Đường chấm điểm, sổ lệnh và đo: CẤM nhập (đặc tả 8.3).
CAM_NHAP = ["paper_trading.py", "paper_runner.py", "paper_metrics.py", "master_agent.py",
            "analysis_agents.py", "debate_agents.py", "news_sentiment_agent.py", "fundamental_agent.py",
            "data_collectors.py", "walkforward.py", "sheets_store.py", "run_daily.py",
            "ke_hoach_vao_lenh.py", "muc_fibonacci.py", "san_dau.py", "cham_bong.py", "hau_kiem_loi.py",
            "ban_tin.py"]


def test_chi_nguoi_trong_danh_sach_dong_duoc_nhap_cau_truc_gia():
    nguoi = {p.relative_to(GOC).as_posix() for p in _file_ma_nguon()
             if "cau_truc_gia" in _nhap_va_goi(p)[0]}
    assert nguoi <= CHO_PHEP_NHAP, f"cau_truc_gia CHỈ ĐỂ ĐỌC; đang có người lạ: {sorted(nguoi - CHO_PHEP_NHAP)}"
    assert "tools/mo_ta_cau_truc_gia.py" in nguoi, "quần thể phải khác rỗng: dụng cụ mô tả phải nhập nó"


@pytest.mark.parametrize("ten", CAM_NHAP)
def test_duong_cham_diem_va_giao_dich_KHONG_nhap(ten):
    duong = GOC / ten
    assert duong.exists(), f"{ten} biến mất — sửa danh sách cấm, đừng bỏ qua"
    assert "cau_truc_gia" not in _nhap_va_goi(duong)[0], ten


def test_khong_file_nao_duoi_backtest_nhap_cau_truc_gia():
    ds = duyet_repo.duyet(GOC / "backtest", "*.py")
    assert ds, "quần thể rỗng"
    assert not [p for p in ds if "cau_truc_gia" in _nhap_va_goi(p)[0]]


def test_mo_dun_chi_nhap_thu_trung_tinh_va_khong_dong_ho_khong_mang():
    nhap, goi = _nhap_va_goi(NGUON)
    assert nhap <= {"__future__", "dataclasses", "pandas", "numpy", "math", "data_quality", "truot_gia",
                    "vong_doi_lenh", "san_giao_dich", "pha_wyckoff"}, nhap
    assert not ({"now", "today", "now_vn", "today_vn", "utcnow", "time", "read_csv", "get", "request",
                 "urlopen", "open", "to_csv", "to_json", "write_text", "read_text"} & goi), goi
    assert "khoa_bien" in " ".join(goi) or "_khoa_bien" in goi


# ══ BƯỚC 307 (Dow phần 2, Lát 1): chế độ chỉ số `la_chi_so` ═══════════════════════════════════════════════
# Đặc tả `vibe_logs_dow2/DAC-TA-DOW2.md` mục 2 khoản 5: phần 1 đọc giá như cổ phiếu, nên với một chỉ số 1.788 điểm
# "bằng nhau" là chênh <= 5 điểm (nửa bước giá HOSE 10 của mức giá ấy) — vô nghĩa. `la_chi_so=True` đặt dung sai
# 0,005 điểm (nửa của hai chữ số thập phân nguồn trả), bỏ cờ `khoa_bien`, bỏ cờ `khong_giao_dich`.
# `la_chi_so=False` (mặc định) PHẢI cho cổ phiếu đúng từng byte như trước BƯỚC 307.
import hashlib  # noqa: E402


def _bang_vang():
    """Bảng cổ phiếu dựng TAY (số hữu hạn, không `np.exp`: hàm siêu việt có thể lệch bit giữa hệ điều hành)."""
    t1 = _df(_TAY)
    t1.loc[20, "volume"] = 0                                       # phiên không giao dịch ở đỉnh
    t4 = _df([30000.0 + 500 * i for i in range(21)] + [40010.0, 38900.0])
    hai = ([30000 + 500 * i for i in range(21)] + [40000 - 500 * j for j in range(1, 17)]
           + [32000 + 500 * j for j in range(1, 16)] + [40010.0, 39010.0, 38010.0, 37010.0])
    return [(t1, {}), (_df(_khoa(1)), {}), (_df(_khoa(-1)), {}), (t4, {"tham_so": (2, 4)}),
            (_df(hai), {}), (_df(_TAY), {"ho": "fractal", "tham_so": (3, 8)})]


def _dau_van_tay(cac_bang, **them):
    """sha256 của nhật ký + sự kiện + con sóng (KHÔNG gồm `trang_thai`: nó có thêm trường `la_chi_so`)."""
    h, so_dong = hashlib.sha256(), 0
    for df, kw in cac_bang:
        r = C.doc_cau_truc(df, he_so_gia=1.0, **kw, **them)
        h.update(repr((r.nhat_ky, r.su_kien, r.con_song)).encode("utf-8"))
        so_dong += len(r.nhat_ky) + len(r.su_kien) + len(r.con_song)
    return h.hexdigest(), so_dong


#: Tính trên bản `main` TRƯỚC khi sửa `cau_truc_gia.py` (9dc7672), lệnh ở `docs/STATE.md` BƯỚC 307.
DAU_VAN_TAY_CO_PHIEU = "85ac9f4135b9c93e0ce836cdb70ff404e4a200311c4ad528e292f5a54bd50f69"


def test_CO_PHIEU_la_chi_so_False_dung_tung_byte_nhu_truoc_BUOC_307():
    """Mặc định và `la_chi_so=False` cho cùng nhật ký/sự kiện/con sóng, và cả hai khớp dấu vân tay tính trên mã
    TRƯỚC khi sửa. Sáu bảng có phiên volume=0, nến khoá trần/sàn, đỉnh gần bằng nhau, họ fractal."""
    mac_dinh = _dau_van_tay(_bang_vang())
    ro_rang = _dau_van_tay(_bang_vang(), la_chi_so=False)
    assert mac_dinh == ro_rang
    assert mac_dinh[1] >= 25, "bảng thử phải có nhiều dòng, nếu không dấu vân tay gác không được gì (lỗi 66)"
    assert mac_dinh[0] == DAU_VAN_TAY_CO_PHIEU


def test_CO_PHIEU_van_mang_co_nen_khi_la_chi_so_False():
    r = C.doc_cau_truc(_df(_khoa(1)), he_so_gia=1.0, san="HOSE", la_chi_so=False)
    assert any(p.khoa_bien == "KICH_TRAN" for p in r.nhat_ky)
    df = _df(_TAY)
    df.loc[20, "volume"] = 0
    assert any(p.khong_giao_dich for p in C.doc_cau_truc(df, la_chi_so=False).nhat_ky)


# Chuỗi CHỈ SỐ dựng tay: bước ±20 điểm (ATR14 = 20 từ nến thứ 15), cùng hình dạng `_TAY`, giá 1.500–1.960.
_CS = ([1500.0 + 20 * i for i in range(21)] + [1900.0 - 20 * j for j in range(1, 13)]
       + [1660.0 + 20 * j for j in range(1, 16)] + [1960.0 - 20 * j for j in range(1, 10)])


def test_CHI_SO_dung_sai_la_0_005_diem_va_hang_so_co_ten():
    assert C.NUA_BUOC_CHI_SO == 0.005
    # `nua_buoc` (cổ phiếu) KHÔNG đổi: một chỉ số 1.788 điểm có nửa bước giá HOSE = 5 điểm
    assert C.nua_buoc(1788.51, 1.0, "HOSE") == 5.0
    assert C.khoi_tao(la_chi_so=True).la_chi_so is True
    assert C.khoi_tao().la_chi_so is False
    assert C.doc_cau_truc(_df(_CS), la_chi_so=True).trang_thai.la_chi_so is True
    assert C.khoi_tao_su_kien(C.khoi_tao(la_chi_so=True)).la_chi_so is True
    assert C.khoi_tao_su_kien(C.khoi_tao()).la_chi_so is False


def _hai_dinh(gia_dinh_2, **kw):
    """Đỉnh 1 = 1.900 (nến 20); đỉnh 2 = `gia_dinh_2`. Trả `nhan` các đỉnh nội bộ (đường `_nhan`)."""
    gia = ([1500.0 + 20 * i for i in range(21)] + [1900.0 - 20 * j for j in range(1, 17)]
           + [1580.0 + 20 * j for j in range(1, 15)] + [gia_dinh_2, gia_dinh_2 - 40, gia_dinh_2 - 80,
                                                         gia_dinh_2 - 120])
    r = C.doc_cau_truc(_df(gia), he_so_gia=1.0, san="HOSE", **kw)
    return [p.nhan for p in r.nhat_ky if p.cap == "noi_bo" and p.loai == "dinh"]


def test_CHI_SO_buoc_4_diem_KHONG_bi_coi_la_bang_o_nhan_dinh():
    """Đỉnh 2 hơn đỉnh 1 đúng 4 điểm. Cổ phiếu (nửa bước 5): "bang". Chỉ số: "HH". Và 0,004 điểm vẫn là bằng,
    0,006 điểm thì không (dung sai 0,005): bắt cả `0.005`→`5`/`0.5`/`0.05` lẫn `0.005`→`0.001`/`0`."""
    assert _hai_dinh(1904.0) == ["chua_co", "bang"]
    assert _hai_dinh(1904.0, la_chi_so=False) == ["chua_co", "bang"]
    assert _hai_dinh(1904.0, la_chi_so=True) == ["chua_co", "HH"]
    assert _hai_dinh(1896.0, la_chi_so=True) == ["chua_co", "LH"]
    assert _hai_dinh(1900.004, la_chi_so=True) == ["chua_co", "bang"]
    assert _hai_dinh(1899.996, la_chi_so=True) == ["chua_co", "bang"]
    assert _hai_dinh(1900.006, la_chi_so=True) == ["chua_co", "HH"]
    assert _hai_dinh(1899.994, la_chi_so=True) == ["chua_co", "LH"]
    assert _hai_dinh(1900.006) == ["chua_co", "bang"]                    # cổ phiếu: vẫn bằng


def _dinh_chi_so(gia_21, **kw):
    gia = [1500.0 + 20 * i for i in range(21)] + [gia_21, 1840.0]       # đỉnh 1.900 ở nến 20, nến 21 = `gia_21`
    return C.doc_cau_truc(_df(gia), he_so_gia=1.0, san="HOSE", tham_so=(2, 4), **kw).nhat_ky[0]


def test_CHI_SO_cuc_tri_cho_thay_khi_vuot_0_005_diem_chu_khong_phai_nua_buoc_gia():
    """Đường `_cuc_tri`: nến 21 cao hơn đỉnh chờ 4 điểm. Cổ phiếu giữ nến 20; chỉ số chuyển sang nến 21."""
    p = _dinh_chi_so(1904.0)
    assert (p.chi_so_xay_ra, p.gia) == (20, 1900.0)
    p = _dinh_chi_so(1904.0, la_chi_so=True)
    assert (p.chi_so_xay_ra, p.gia) == (21, 1904.0)
    assert _dinh_chi_so(1900.004, la_chi_so=True).chi_so_xay_ra == 20
    assert _dinh_chi_so(1900.006, la_chi_so=True).chi_so_xay_ra == 21
    assert _dinh_chi_so(1900.0, la_chi_so=True).chi_so_xay_ra == 20      # bằng hệt: giữ nến SỚM


def test_CHI_SO_cuc_tri_day_doi_xung():
    def day(gia_20, **kw):
        gia = [2400.0 - 20 * i for i in range(20)] + [gia_20, 2080.0]         # đáy 2.020 ở nến 19
        return C.doc_cau_truc(_df(gia), he_so_gia=1.0, san="HOSE", tham_so=(2, 4), **kw).nhat_ky[0]
    assert day(2016.0).chi_so_xay_ra == 19
    assert day(2016.0, la_chi_so=True).chi_so_xay_ra == 20
    assert day(2019.996, la_chi_so=True).chi_so_xay_ra == 19
    assert day(2019.994, la_chi_so=True).chi_so_xay_ra == 20


def test_CHI_SO_fractal_dinh_cao_hon_4_diem_la_dinh():
    def fractal(gia, **kw):
        return [(p.loai, p.chi_so_xay_ra) for p in C.doc_cau_truc(
            _df(gia), he_so_gia=1.0, ho="fractal", tham_so=(3, 8), **kw).nhat_ky]
    dinh = [1700, 1720, 1740, 1900, 1904, 1740, 1720, 1700, 1680, 1660]
    day = [2100, 2080, 2060, 1900, 1896, 2060, 2080, 2100, 2120, 2140]
    assert fractal(dinh) == [] and fractal(day) == []                           # cổ phiếu: 4 điểm < nửa bước 5
    assert fractal(dinh, la_chi_so=True) == [("dinh", 4)]
    assert fractal(day, la_chi_so=True) == [("day", 4)]
    near_d = [1700, 1720, 1740, 1900, 1900.004, 1740, 1720, 1700, 1680, 1660]
    assert fractal(near_d, la_chi_so=True) == []
    xa_d = [1700, 1720, 1740, 1900, 1900.006, 1740, 1720, 1700, 1680, 1660]
    assert fractal(xa_d, la_chi_so=True) == [("dinh", 4)]


def _pivot_tay(loai, gia):
    return C.Pivot(cap="noi_bo", loai=loai, su_kien=C.XAC_NHAN, ngay_xay_ra="2024-01-04", chi_so_xay_ra=3,
                   ngay_biet="2024-01-08", chi_so_biet=5, gia=float(gia), nhan=C.CHUA_CO, khoa_bien=None,
                   khong_giao_dich=False)


def _nen_tay(i, dong):
    return C.Nen(chi_so=i, ngay=f"2024-02-{i + 1:02d}", cao=float(dong), thap=float(dong), dong=float(dong),
                 atr=None, khoa_bien=None, khong_giao_dich=False)


def _su_kien_tay(loai, moc, dong, **kw):
    tsk = C.khoi_tao_su_kien(C.khoi_tao(he_so_gia=1.0, san="HOSE", **kw))
    ra = []
    for i, d in enumerate([moc] * 6 + [dong]):
        tsk, sk = C.cap_nhat_su_kien(tsk, _nen_tay(i, d), [_pivot_tay(loai, moc)] if i == 5 else [])
        ra.extend(sk)
    return ra


def test_CHI_SO_phep_pha_moc_dung_dung_sai_0_005_diem():
    """Đường `_vuot_moc`: đóng cửa vượt mốc 1.900 đúng 4 điểm. Cổ phiếu chưa phá (nửa bước 5); chỉ số phá."""
    for loai, vuot, bang in (("dinh", 1904.0, 1900.004), ("day", 1896.0, 1899.996)):
        assert _su_kien_tay(loai, 1900.0, vuot) == []
        assert len(_su_kien_tay(loai, 1900.0, vuot, la_chi_so=True)) == 1
        assert _su_kien_tay(loai, 1900.0, bang, la_chi_so=True) == []
    assert len(_su_kien_tay("dinh", 1900.0, 1900.006, la_chi_so=True)) == 1
    assert len(_su_kien_tay("day", 1900.0, 1899.994, la_chi_so=True)) == 1


def test_CHI_SO_khong_co_co_khoa_bien_khong_giao_dich_o_pivot_va_su_kien():
    """Hai cờ nến của cổ phiếu (khoá biên, volume=0) KHÔNG áp cho chỉ số: chỉ số không có trần/sàn của mã và
    `volume` = 0 ở chỉ số là thiếu dữ liệu, không phải phiên đứng giá."""
    df = _df(_khoa(1))
    r = C.doc_cau_truc(df, he_so_gia=1.0, san="HOSE")
    assert any(p.khoa_bien == "KICH_TRAN" for p in r.nhat_ky)                 # đối chứng: cùng bảng, cổ phiếu CÓ cờ
    r = C.doc_cau_truc(df, he_so_gia=1.0, san="HOSE", la_chi_so=True)
    assert r.nhat_ky and all(p.khoa_bien is None for p in r.nhat_ky)
    assert all(e.khoa_bien is None for e in r.su_kien)
    df = _df(_CS)
    df.loc[20, "volume"] = 0
    assert any(p.khong_giao_dich for p in C.doc_cau_truc(df).nhat_ky)         # đối chứng
    r = C.doc_cau_truc(df, la_chi_so=True)
    assert r.nhat_ky and all(not p.khong_giao_dich for p in r.nhat_ky)
    assert r.su_kien and all(not e.khong_giao_dich for e in r.su_kien)


def test_CHI_SO_volume_0_khong_dua_true_range_ve_0():
    """Cổ phiếu: nến volume=0 có true range 0 (ATR thấp hơn). Chỉ số: bỏ quy tắc ấy, ATR y hệt khi không có
    cột `volume` (chuỗi chỉ số của Lát 1 không mang cột này)."""
    gia = list(_CS)
    df2 = _df(gia)
    df2["high"] = [g + 30 for g in gia]
    df2.loc[30, "volume"] = 0
    co_phieu = C.chuan_bi_nen(df2)[33].atr
    chi_so = C.chuan_bi_nen(df2, la_chi_so=True)[33].atr
    khong_cot = C.chuan_bi_nen(df2.drop(columns=["volume"]), la_chi_so=True)[33].atr
    assert co_phieu < chi_so == khong_cot


def test_CHI_SO_bat_bien_khi_cat_va_bang_khong_cot_volume_van_doc_duoc():
    df = _df(_CS).drop(columns=["volume"])
    day_du = _kiem_cat(df, la_chi_so=True)
    assert len(day_du.nhat_ky) >= 4, "bảng thử phải có pivot, nếu không gác này trống rỗng (lỗi 66)"
    assert [(p.cap, p.loai, p.chi_so_xay_ra, p.gia) for p in day_du.nhat_ky][:2] == [
        ("noi_bo", "dinh", 20, 1900.0), ("swing", "dinh", 20, 1900.0)]
