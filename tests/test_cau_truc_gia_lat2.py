"""Test `cau_truc_gia` Lát 2 — BOS / CHoCH theo cấp, trạng thái Dow, con sóng, chu kỳ 4 giai đoạn
(BƯỚC 249, Dow Lát 2, mốc B5 mượn). Đặc tả: `docs/thiet-ke-dow-cau-truc.md` mục 5.7–5.9, 6, 8.1, 8.4.

VÌ SAO FILE NÀY TỒN TẠI
───────────────────────
Lát 1 gác pivot (`tests/test_cau_truc_gia.py`). Lát 2 thêm ba thứ mà mỗi thứ có một kiểu NHÌN TRỘM riêng:
  * sự kiện phá mốc dùng một pivot chưa biết tại nến phá (mutant 4);
  * trạng thái "biết từ ngày nào" lấy ngày xảy ra thay vì ngày biết;
  * chu kỳ 4 giai đoạn ghi đè Wyckoff bằng thủy triều, hoặc suy Tích luỹ / Phân phối từ thủy triều (12, 13).
Gác chính vẫn là BẤT BIẾN KHI CẮT, nay mở rộng cho sự kiện, con sóng và trạng thái: với MỌI `t`,
mọi thứ tính từ `df[:t+1]` y hệt các dòng đã biết tại `t` của bản đủ.

Đáp số TÍNH TAY: chuỗi `_BOS` (bước ±500 đồng, ATR14 = 500) có đáp số suy ra trên giấy ở mỗi test; các
nhật ký dựng tay (`_P`) cho ca biên (đúng 3/8, đúng 10 phiên, đúng nửa bước giá) mà đường pivot không tạo
được. Đột biến 4, 5 (bản BOS), 7, 8, 10, 11, 12, 13 và phát bổ sung chạy bằng `va_an_toan.dot_bien_bo`;
kết quả ở `docs/STATE.md` BƯỚC 249.
"""
from __future__ import annotations

import pathlib
import re
import sys
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

GOC = pathlib.Path(__file__).resolve().parent.parent
# `tools/` vào CUỐI đường tìm (có hai `cham_xac_nhan.py`; xem chú thích ở test_cau_truc_gia.py).
sys.path.insert(0, str(GOC))
sys.path.append(str(GOC / "tools"))

import cau_truc_gia as C  # noqa: E402
import pha_wyckoff as wy  # noqa: E402

NGAY = pd.bdate_range("2024-01-01", periods=600).strftime("%Y-%m-%d").tolist()


# ── dựng dữ liệu ──────────────────────────────────────────────────────────────────────────
def _df(dong, bat_dau="2024-01-01", vol=1000):
    dong = [float(x) for x in dong]
    return pd.DataFrame({"time": pd.bdate_range(bat_dau, periods=len(dong)),
                         "high": dong, "low": dong, "close": dong, "volume": vol})


def _ngau(n, hat, gia0=30.0):
    rng = np.random.default_rng(hat)
    sigma = np.where((np.arange(n) // 40) % 2 == 0, 0.010, 0.026)
    c = gia0 * np.exp(np.cumsum(rng.normal(0, sigma)))
    c = np.round(c / 0.05) * 0.05
    truoc = np.concatenate([[c[0]], c[:-1]])
    cao = np.maximum(c, truoc) * (1 + np.abs(rng.normal(0, 0.004, n)))
    thap = np.minimum(c, truoc) * (1 - np.abs(rng.normal(0, 0.004, n)))
    vol = rng.integers(0, 3, n) * 100_000
    return pd.DataFrame({"time": pd.bdate_range("2023-01-02", periods=n), "high": cao, "low": thap,
                         "close": c, "volume": vol})


#: Chuỗi dựng tay (mỗi bước 500đ, đơn vị ĐỒNG, he_so_gia=1): lên 20, xuống 8, lên 14, xuống 8, lên 9,
#: xuống 16, lên 4. Đáp số suy ra trên giấy ở `test_CA_DUNG_TAY_su_kien`.
_BOS = ([20000 + 500 * i for i in range(21)] + [30000 - 500 * j for j in range(1, 9)]
        + [26000 + 500 * j for j in range(1, 15)] + [33000 - 500 * j for j in range(1, 9)]
        + [29000 + 500 * j for j in range(1, 10)] + [33500 - 500 * j for j in range(1, 17)]
        + [25500 + 500 * j for j in range(1, 5)])


def _guong(gia):
    """Ảnh gương quanh 50.000: mọi đỉnh thành đáy. Bước giá HOSE vẫn 50 (10.000–49.950) hoặc 100."""
    return [50000.0 - (g - 20000.0) for g in gia]


def _P(cap, loai, xay, biet, gia, nhan=C.CHUA_CO, su_kien=C.XAC_NHAN, thay=None):
    """Một dòng nhật ký pivot dựng TAY."""
    return C.Pivot(cap=cap, loai=loai, su_kien=su_kien, ngay_xay_ra=NGAY[xay], chi_so_xay_ra=xay,
                   ngay_biet=NGAY[biet], chi_so_biet=biet, gia=float(gia), nhan=nhan, khoa_bien=None,
                   khong_giao_dich=False, thay_the_chi_so=thay)


def _N(i, dong, khoa=None):
    return C.Nen(chi_so=i, ngay=NGAY[i], cao=float(dong), thap=float(dong), dong=float(dong), atr=None,
                 khoa_bien=khoa, khong_giao_dich=False)


def _chay_su_kien(pivots_theo_nen, dong_theo_nen, he=1.0, san="HOSE"):
    """Đẩy từng nến qua `cap_nhat_su_kien`; `pivots_theo_nen[i]` là các dòng pivot MỚI của nến i."""
    tsk = C.khoi_tao_su_kien(C.khoi_tao(he_so_gia=he, san=san))
    kq = []
    for i, d in enumerate(dong_theo_nen):
        tsk, sk = C.cap_nhat_su_kien(tsk, _N(i, d), pivots_theo_nen.get(i, []))
        kq.extend(sk)
    return kq


def _tom_tat(e):
    p = e.pivot_bi_pha
    return (e.cap, e.loai, e.chieu, e.chi_so_xay_ra, (p.chi_so_xay_ra, p.chi_so_biet, p.gia))


# ── 1. sự kiện: đáp số tính tay ───────────────────────────────────────────────────────────
def test_CA_DUNG_TAY_su_kien():
    """Suy ra trên giấy. Pivot (xảy ra, biết, giá): nội bộ đỉnh 30.000 (20, 22), đáy 26.000 (28, 30), đỉnh 33.000
    (42, 44), đáy 29.000 (50, 52), đỉnh 33.500 (59, 61); swing: cùng nến xảy ra, biết muộn hơn 2 nến (24, 32, 46, 54, 63).
    Nến 37 đóng 30.500 > 30.000 + 25 (nửa bước 50đ): sự kiện ĐẦU TIÊN của mỗi cấp = KHOI_DAU tăng, phá đỉnh 30.000.
    Nến 59 đóng 33.500 > 33.025: BOS tăng (cùng thiên hướng) phá đỉnh 33.000. Nến 69 đóng 28.500 < 29.000 − 25: CHOCH
    giảm (ngược thiên hướng tăng) phá đáy 29.000 — đáy 29.000, KHÔNG phải đáy 26.000, vì 29.000 là đáy gần nhất chưa phá.
    Nến 75 đóng 25.500 < 26.000 − 25: BOS giảm (cùng thiên hướng giảm vừa đổi) phá đáy 26.000."""
    r = C.doc_cau_truc(_df(_BOS))
    assert len(_BOS) == 80
    assert [_tom_tat(e) for e in r.su_kien] == [
        ("noi_bo", "KHOI_DAU", "tang", 37, (20, 22, 30000.0)),
        ("swing", "KHOI_DAU", "tang", 37, (20, 24, 30000.0)),
        ("noi_bo", "BOS", "tang", 59, (42, 44, 33000.0)),
        ("swing", "BOS", "tang", 59, (42, 46, 33000.0)),
        ("noi_bo", "CHOCH", "giam", 69, (50, 52, 29000.0)),
        ("swing", "CHOCH", "giam", 69, (50, 54, 29000.0)),
        ("noi_bo", "BOS", "giam", 75, (28, 30, 26000.0)),
        ("swing", "BOS", "giam", 75, (28, 32, 26000.0)),
    ]
    for e in r.su_kien:
        assert (e.ngay_xay_ra, e.ngay_biet) == (NGAY[e.chi_so_xay_ra], NGAY[e.chi_so_xay_ra])
        assert e.chi_so_biet == e.chi_so_xay_ra and e.pivot_bi_pha.chi_so_biet < e.chi_so_xay_ra
        assert e.gia_dong == _BOS[e.chi_so_xay_ra] and e.khoa_bien is None


def test_ANH_GUONG_doi_xung_dinh_dao_day_dao_tang_giam_va_BOS_CHOCH_giu_nguyen():
    """Lật giá quanh 50.000: mọi đỉnh thành đáy. Sự kiện xảy ra Ở CÙNG NẾN, chiều đảo, loại giữ nguyên
    (KHOI_DAU → BOS → CHOCH → BOS vẫn là thứ tự đó), pivot bị phá đổi loại."""
    a = C.doc_cau_truc(_df(_BOS)).su_kien
    b = C.doc_cau_truc(_df(_guong(_BOS))).su_kien
    dao = {"tang": "giam", "giam": "tang"}
    assert [(e.cap, e.loai, dao[e.chieu], e.chi_so_xay_ra) for e in a] == \
        [(e.cap, e.loai, e.chieu, e.chi_so_xay_ra) for e in b]
    assert [(e.pivot_bi_pha.chi_so_xay_ra, e.pivot_bi_pha.chi_so_biet) for e in a] == \
        [(e.pivot_bi_pha.chi_so_xay_ra, e.pivot_bi_pha.chi_so_biet) for e in b]
    assert all(x.pivot_bi_pha.loai != y.pivot_bi_pha.loai for x, y in zip(a, b))


def test_chi_pivot_da_biet_TRUOC_nen_pha_duoc_xet__dot_bien_4():
    """Hợp đồng của `cap_nhat_su_kien` (đặc tả 5.7 khoản 1): ở nến `t`, TRƯỚC hết xét phá mốc với pivot đã biết
    trước nến, SAU ĐÓ mới ghi pivot xác nhận ở chính nến `t`. Đường pivot thật không dựng được ca này (pivot xác
    nhận ở nến `t` luôn có đóng cửa `t` còn dưới nó), nên dựng TAY một dòng nhật ký có `chi_so_biet = t` mà đóng cửa
    `t` đã vượt nó: phải KHÔNG có sự kiện ở `t`; sự kiện chỉ đến ở nến sau, với `pivot_bi_pha.chi_so_biet < t'`."""
    y = _P("noi_bo", "dinh", 3, 5, 40000.0)
    ev = _chay_su_kien({5: [y]}, [38000, 38000, 38000, 39000, 39000, 41000, 42000])
    assert [(e.chi_so_xay_ra, e.loai) for e in ev] == [(6, "KHOI_DAU")]      # nến 5 (biết pivot) KHÔNG phá
    assert ev[0].pivot_bi_pha == y and ev[0].pivot_bi_pha.chi_so_biet < ev[0].chi_so_xay_ra


@pytest.mark.parametrize("loai,mốc,cac_dong,so_su_kien", [
    # ĐỈNH 40.000 (HOSE ở 40.000: bước 50, nửa bước 25): bằng, trong nửa bước, ĐÚNG nửa bước chưa phá; hơn nửa bước mới phá
    ("dinh", 40000.0, [40000, 40010, 40025], 0),
    ("dinh", 40000.0, [40026], 1),
    ("dinh", 40000.0, [40050], 1),
    ("day", 40000.0, [40000, 39990, 39975], 0),
    ("day", 40000.0, [39974], 1),
    ("day", 40000.0, [39950], 1),
])
def test_GIA_BANG_o_phep_pha_dong_cua_dung_nua_buoc_chua_phai_pha__dot_bien_5_BOS(loai, mốc, cac_dong, so_su_kien):
    """Mutant 5 bản BOS (Lát 1 hoãn): `>` thành `>=` ở phép phá mốc khiến đóng cửa chạm đúng nửa bước thành phá."""
    p = _P("noi_bo", loai, 3, 5, mốc)
    ev = _chay_su_kien({5: [p]}, [mốc] * 6 + list(cac_dong))
    assert len(ev) == so_su_kien
    if so_su_kien:
        assert ev[0].chieu == ("tang" if loai == "dinh" else "giam") and ev[0].loai == C.KHOI_DAU


def test_dung_sai_nua_buoc_khong_bi_bo_o_phep_pha():
    """Bỏ dung sai (`đóng > mốc` thay cho `đóng > mốc + nửa bước`) sẽ phá ở 40.010 (đỉnh) và 39.990 (đáy)."""
    for loai, d in (("dinh", 40010.0), ("day", 39990.0)):
        assert _chay_su_kien({5: [_P("noi_bo", loai, 3, 5, 40000.0)]}, [40000.0] * 6 + [d]) == []


def test_BOS_hay_CHOCH_theo_thien_huong__dot_bien_7():
    """Hợp đồng dựng tay, suy ra trên giấy. Đỉnh d=44.000 (biết 2), đáy t0=30.000 (4), đỉnh d2=42.000 (6, thấp hơn d),
    đáy t1=36.000 (8, cao hơn t0). Nến 0–8 đóng 38.000. Nến 9 đóng 43.000: đỉnh GẦN NHẤT chưa phá là d2 ⇒ KHOI_DAU tăng
    (d=44.000 chưa bị vượt). Nến 10 đóng 48.000 phá d ⇒ BOS (cùng thiên hướng tăng). Nến 12 đóng 34.000 phá t1 (đáy gần
    nhất) ⇒ CHOCH giảm (ngược thiên hướng), t0 chưa bị vượt. Nến 13 đóng 28.000 phá t0 ⇒ BOS giảm (cùng thiên hướng
    giảm vừa đổi). Nến 14 đóng 20.000 không còn mốc nào."""
    d, t0 = _P("noi_bo", "dinh", 1, 2, 44000.0), _P("noi_bo", "day", 3, 4, 30000.0)
    d2, t1 = _P("noi_bo", "dinh", 5, 6, 42000.0, nhan=C.LH), _P("noi_bo", "day", 7, 8, 36000.0, nhan=C.HL)
    dong = [38000] * 9 + [43000, 48000, 48000, 34000, 28000, 20000]
    ev = _chay_su_kien({2: [d], 4: [t0], 6: [d2], 8: [t1]}, dong)
    assert [(e.chi_so_xay_ra, e.loai, e.chieu, e.pivot_bi_pha.gia) for e in ev] == [
        (9, "KHOI_DAU", "tang", 42000.0), (10, "BOS", "tang", 44000.0),
        (12, "CHOCH", "giam", 36000.0), (13, "BOS", "giam", 30000.0)]


def test_mot_pivot_chi_bi_pha_MOT_LAN__dot_bien_8():
    """Cờ `da_pha`: đóng cửa tiếp tục ở trên mốc thì KHÔNG sinh thêm sự kiện nào cho cùng pivot."""
    p = _P("noi_bo", "dinh", 3, 5, 40000.0)
    ev = _chay_su_kien({5: [p]}, [38000] * 6 + [40500, 40600, 40700, 40800, 40900, 41000])
    assert [(e.chi_so_xay_ra, e.loai) for e in ev] == [(6, "KHOI_DAU")]


def test_hai_dinh_gan_bang_nhau_chi_cho_MOT_su_kien():
    """Hai đỉnh chưa phá trong nửa bước giá (40.000 và 40.010): đóng cửa vượt cả hai ⇒ MỘT sự kiện (phá đỉnh GẦN
    NHẤT, 40.010) và đỉnh 40.000 cũng thành đã phá. Nếu chỉ đánh dấu một đỉnh, nến sau sẽ sinh sự kiện thứ hai
    cho đỉnh còn lại. (Khác chữ nghĩa đặc tả 5.7 khoản 2 — khai ở STATE BƯỚC 249.)"""
    a, b = _P("noi_bo", "dinh", 1, 3, 40000.0), _P("noi_bo", "dinh", 4, 6, 40010.0, nhan=C.BANG)
    ev = _chay_su_kien({3: [a], 6: [b]}, [39000.0] * 7 + [40100.0, 40200.0, 40300.0])
    assert [(e.chi_so_xay_ra, e.loai, e.pivot_bi_pha.gia) for e in ev] == [(7, "KHOI_DAU", 40010.0)]


def test_mot_cu_nhay_qua_nhieu_dao_chi_cho_MOT_su_kien():
    """Đáy cũ 30.000 và đáy mới 36.000 cùng chưa phá; một nến đóng 20.000 vượt cả hai ⇒ MỘT sự kiện (đáy gần nhất 36.000);
    nến sau (19.000) không sinh BOS cho đáy 30.000 vì giá đã đóng dưới nó từ nến trước."""
    ev = _chay_su_kien({4: [_P("noi_bo", "day", 3, 4, 30000.0)], 8: [_P("noi_bo", "day", 7, 8, 36000.0)]},
                       [38000] * 9 + [20000, 19000, 18000])
    assert [(e.chi_so_xay_ra, e.loai, e.chieu, e.pivot_bi_pha.gia) for e in ev] == [(9, "KHOI_DAU", "giam", 36000.0)]


def test_dong_thay_the_cua_fractal_chi_cho_mot_su_kien_voi_pivot_moi():
    """Họ fractal: dòng `thay_the` đè pivot cũ; mốc là pivot MỚI (cao hơn), nến vượt nó cho đúng một sự kiện."""
    cu = _P("noi_bo", "dinh", 1, 3, 40000.0)
    moi = _P("noi_bo", "dinh", 4, 6, 40500.0, su_kien=C.THAY_THE, thay=1)
    ev = _chay_su_kien({3: [cu], 6: [moi]}, [39000.0] * 7 + [40100.0, 40400.0, 40600.0])
    assert [(e.chi_so_xay_ra, e.pivot_bi_pha.gia) for e in ev] == [(9, 40500.0)]


def test_su_kien_lay_co_khoa_bien_cua_nen_pha():
    tsk = C.khoi_tao_su_kien(C.khoi_tao(he_so_gia=1.0))
    tsk, _ = C.cap_nhat_su_kien(tsk, _N(3, 38000), [_P("noi_bo", "dinh", 1, 3, 40000.0)])
    tsk, ev = C.cap_nhat_su_kien(tsk, _N(4, 42000, khoa="KICH_TRAN"), [])
    assert [(e.loai, e.khoa_bien) for e in ev] == [("KHOI_DAU", "KICH_TRAN")]
    tsk, ev = C.cap_nhat_su_kien(tsk, _N(5, 41000), [_P("noi_bo", "day", 4, 5, 30000.0)])
    tsk, ev = C.cap_nhat_su_kien(tsk, _N(6, 20000, khoa="KICH_SAN"), [])
    assert [(e.loai, e.chieu, e.khoa_bien) for e in ev] == [("CHOCH", "giam", "KICH_SAN")]


def test_hai_cap_la_hai_may_doc_lap_o_su_kien():
    """Đỉnh nội bộ 40.000 và đỉnh swing 45.000: nến đóng 42.000 chỉ phá mốc nội bộ."""
    tsk = C.khoi_tao_su_kien(C.khoi_tao(he_so_gia=1.0))
    tsk, _ = C.cap_nhat_su_kien(tsk, _N(3, 38000), [_P("noi_bo", "dinh", 1, 3, 40000.0),
                                                     _P("swing", "dinh", 1, 3, 45000.0)])
    _, ev = C.cap_nhat_su_kien(tsk, _N(4, 42000), [])
    assert [e.cap for e in ev] == ["noi_bo"]


# ── 2. sự kiện: đối chiếu ĐỘC LẬP bằng numpy, trên chuỗi ngẫu nhiên ───────────────────────
def _hieu_luc(nhat_ky, cap):
    ds = []
    for p in nhat_ky:
        if p.cap != cap:
            continue
        ds = [q for q in ds if not (p.su_kien == "thay_the" and q.loai == p.loai
                                    and q.chi_so_xay_ra == p.thay_the_chi_so)] + [p]
    return ds


def _vuot(loai, dong, p, he):
    nua = C.nua_buoc(p.gia, he, "HOSE")
    return (dong - p.gia > nua) if loai == "dinh" else (p.gia - dong > nua)


def _su_kien_tho(df, r, he):
    """Tính lại sự kiện bằng cách THÔ, không trạng thái: ở nến `t`, pivot chưa phá = pivot đã biết ở nến ≤ t−1 mà
    chưa đóng cửa nào từ lúc biết tới t−1 vượt nó; mốc là pivot cuối của loại; phá khi đóng cửa `t` vượt nó."""
    dong = df["close"].to_numpy(float)
    kq = []
    for cap in C.CAPS:
        huong = None
        for t in range(len(dong)):
            biet = _hieu_luc([p for p in r.nhat_ky if p.chi_so_biet <= t - 1], cap)
            for loai, chieu in (("dinh", "tang"), ("day", "giam")):
                chua = [p for p in biet if p.loai == loai
                        and not any(_vuot(loai, x, p, he) for x in dong[p.chi_so_biet:t])]
                if chua and _vuot(loai, dong[t], chua[-1], he):
                    ten = "KHOI_DAU" if huong is None else ("BOS" if chieu == huong else "CHOCH")
                    huong = chieu
                    kq.append((cap, t, ten, chieu, chua[-1]))
    return sorted(kq, key=lambda x: (x[1], C.CAPS.index(x[0])))


@pytest.mark.parametrize("hat", [1, 2, 3, 4])
def test_su_kien_khop_ban_tinh_tho_doc_lap_tren_chuoi_ngau_nhien(hat):
    he = 1000.0
    df = _ngau(260, hat)
    r = C.doc_cau_truc(df, he_so_gia=he)
    tho = _su_kien_tho(df, r, he)
    assert len(tho) >= 8, "chuỗi thử phải có sự kiện, nếu không gác này trống rỗng (lỗi 66)"
    assert [(e.cap, e.chi_so_xay_ra, e.loai, e.chieu, e.pivot_bi_pha) for e in r.su_kien] == tho
    assert {e.loai for e in r.su_kien} >= {"KHOI_DAU", "BOS", "CHOCH"}


@pytest.mark.parametrize("ho,tham_so", [(h, ts) for h in sorted(C.LUOI) for ts in C.LUOI[h]])
def test_su_kien_khop_ban_tinh_tho_moi_o_luoi(ho, tham_so):
    he = 1000.0
    df = _ngau(150, 9)
    r = C.doc_cau_truc(df, he_so_gia=he, ho=ho, tham_so=tham_so)
    assert [(e.cap, e.chi_so_xay_ra, e.loai, e.chieu, e.pivot_bi_pha) for e in r.su_kien] == \
        _su_kien_tho(df, r, he)


def test_hinh_dang_nhat_ky_su_kien():
    df = _ngau(300, 11)
    r = C.doc_cau_truc(df, he_so_gia=1000.0)
    ngay = df["time"].dt.strftime("%Y-%m-%d").tolist()
    biet = [e.chi_so_biet for e in r.su_kien]
    assert biet == sorted(biet) and len(biet) > 8
    for cap in C.CAPS:
        ds = [e for e in r.su_kien if e.cap == cap]
        assert ds[0].loai == "KHOI_DAU" and all(e.loai != "KHOI_DAU" for e in ds[1:]), "KHOI_DAU chỉ ĐẦU TIÊN"
        for truoc, sau in zip(ds, ds[1:]):
            assert sau.loai == ("BOS" if sau.chieu == truoc.chieu else "CHOCH"), (cap, sau.chi_so_xay_ra)
    for e in r.su_kien:
        assert (e.ngay_xay_ra, e.ngay_biet) == (ngay[e.chi_so_xay_ra], ngay[e.chi_so_xay_ra])
        assert e.pivot_bi_pha.chi_so_biet < e.chi_so_xay_ra
        assert e.pivot_bi_pha.cap == e.cap
        assert e.pivot_bi_pha.loai == ("dinh" if e.chieu == "tang" else "day")
    assert len({(e.cap, e.pivot_bi_pha.chi_so_xay_ra, e.pivot_bi_pha.loai, e.pivot_bi_pha.chi_so_biet)
                for e in r.su_kien}) == len(r.su_kien), "mỗi pivot bị phá tối đa MỘT lần"


# ── 3. bất biến khi cắt, mở rộng cho sự kiện, con sóng và trạng thái (đặc tả 8.1) ───────────
def _kiem_cat_lat2(df, **kw):
    day_du = C.doc_cau_truc(df, **kw)
    for t in range(len(df)):
        cat = C.doc_cau_truc(df.iloc[:t + 1], **kw)
        assert list(cat.su_kien) == C.su_kien_tai(day_du.su_kien, t), f"sự kiện lệch khi cắt tại t={t}, {kw}"
        assert list(cat.con_song) == [w for w in day_du.con_song if w.chi_so_biet <= t], f"sóng lệch tại t={t}"
        assert C.trang_thai_dow(cat) == C.trang_thai_dow(day_du, t), f"trạng thái lệch tại t={t}, {kw}"
    return day_du


@pytest.mark.parametrize("hat", [1, 2, 3])
def test_BAT_BIEN_KHI_CAT_su_kien_song_trang_thai_chuoi_ngau_nhien(hat):
    day_du = _kiem_cat_lat2(_ngau(220, hat), he_so_gia=1000.0)
    assert len(day_du.su_kien) >= 6, "chuỗi thử phải có sự kiện (lỗi 66)"


def test_BAT_BIEN_KHI_CAT_chuoi_dung_tay_va_ca_kho_lat2():
    day_du = _kiem_cat_lat2(_df(_BOS))
    assert len(day_du.su_kien) == 8 and len(day_du.con_song) == 1
    _kiem_cat_lat2(_df(_guong(_BOS)))
    gia = list(_BOS[:45])
    df = _df(gia)
    df.loc[10, "volume"] = 0
    gia[20] = gia[19] * 1.07
    df["close"] = df["high"] = df["low"] = gia
    _kiem_cat_lat2(df)
    _kiem_cat_lat2(_df(_BOS[:9]))


@pytest.mark.parametrize("ho", sorted(C.LUOI))
def test_BAT_BIEN_KHI_CAT_lat2_moi_o_luoi(ho):
    for tham_so in C.LUOI[ho]:
        _kiem_cat_lat2(_ngau(110, 7), he_so_gia=1000.0, ho=ho, tham_so=tham_so)


def test_chay_tung_nen_bang_chay_ca_bang_o_su_kien_va_trang_thai_la_gia_tri():
    df = _ngau(200, 5)
    he = 1000.0
    nens = C.chuan_bi_nen(df)
    tt = C.khoi_tao(he_so_gia=he)
    tsk = C.khoi_tao_su_kien(tt)
    log, mong = [], C.doc_cau_truc(df, he_so_gia=he).su_kien
    anh = None
    for i, nen in enumerate(nens):
        tt, moi = C.cap_nhat(tt, nen)
        tsk, sk = C.cap_nhat_su_kien(tsk, nen, moi)
        log.extend(sk)
        if i == 100:
            anh = (tt, tsk, len(log))
    assert tuple(log) == mong
    tt2, tsk2, log2 = anh[0], anh[1], list(mong[:anh[2]])
    for nen in nens[101:]:
        tt2, moi = C.cap_nhat(tt2, nen)
        tsk2, sk = C.cap_nhat_su_kien(tsk2, nen, moi)
        log2.extend(sk)
    assert tuple(log2) == mong


# ── 4. thủy triều, mốc phủ định, cảnh báo (đặc tả 5.8) ────────────────────────────────────
@pytest.mark.parametrize("nhan_dinh,nhan_day,mong", [
    ("HH", "HL", "tang"), ("LH", "LL", "giam"),
    ("HH", "LL", "lan"), ("LH", "HL", "lan"),                    # đỉnh và đáy KHÔNG cùng chiều ⇒ lẫn (đột biến 11)
    ("HH", "bang", "lan"), ("bang", "HL", "lan"), ("bang", "LL", "lan"), ("LH", "bang", "lan"),
    ("HH", "chua_co", "chua_du_bang_chung"), ("chua_co", "HL", "chua_du_bang_chung"),
    ("chua_co", "chua_co", "chua_du_bang_chung"),
    ("HH", None, "chua_du_bang_chung"), (None, "HL", "chua_du_bang_chung"), (None, None, "chua_du_bang_chung"),
])
def test_THUY_TRIEU_can_CA_dinh_VA_day__dot_bien_11(nhan_dinh, nhan_day, mong):
    dong = []
    if nhan_dinh:
        dong.append(_P("swing", "dinh", 10, 13, 100.0, nhan=nhan_dinh))
    if nhan_day:
        dong.append(_P("swing", "day", 20, 23, 60.0, nhan=nhan_day))
    dong.sort(key=lambda p: p.chi_so_biet)
    assert C.trang_thai_tu_nhat_ky(dong, (), (), 50).thuy_trieu == mong


def test_thuy_trieu_doc_cap_SWING_khong_doc_cap_noi_bo():
    dong = [_P("noi_bo", "dinh", 10, 13, 100.0, nhan="HH"), _P("noi_bo", "day", 20, 23, 60.0, nhan="HL")]
    assert C.trang_thai_tu_nhat_ky(dong, (), (), 50).thuy_trieu == "chua_du_bang_chung"


def test_trang_thai_dung_tay_tren_chuoi_BOS():
    """Đáp số suy ra từ các pivot swing của `_BOS`: đỉnh 30.000 (biết 24), đáy 26.000 (32), đỉnh 33.000 HH (46),
    đáy 29.000 HL (54), đỉnh 33.500 HH (63), đáy 25.500 LL (79). Trước nến 54 chưa có hai đáy ⇒ chưa đủ bằng chứng;
    từ 54 (HH + HL) ⇒ TĂNG, "biết từ" nến 54 và GIỮ nguyên khi đỉnh 33.500 (nến 63) đến; mốc phủ định là đáy 29.000
    (xảy ra 50, biết 54). Nến 69: CHOCH swing giảm ⇒ cảnh báo đảo chiều (thủy triều vẫn tăng). Nến 79: đáy LL ⇒ LẪN."""
    r = C.doc_cau_truc(_df(_BOS))
    for t in (45, 46, 53):
        s = C.trang_thai_dow(r, t)
        assert s.thuy_trieu == "chua_du_bang_chung" and s.moc_phu_dinh is None and not s.canh_bao_dao_chieu
    s54 = C.trang_thai_dow(r, 54)
    assert (s54.thuy_trieu, s54.chi_so_biet_thuy_trieu, s54.ngay_biet_thuy_trieu) == ("tang", 54, NGAY[54])
    assert (s54.moc_phu_dinh.gia, s54.moc_phu_dinh.chi_so_xay_ra, s54.moc_phu_dinh.chi_so_biet,
            s54.ngay_biet_moc_phu_dinh) == (29000.0, 50, 54, NGAY[54])
    s63 = C.trang_thai_dow(r, 63)
    assert (s63.thuy_trieu, s63.ngay_biet_thuy_trieu, s63.ngay_biet_moc_phu_dinh) == ("tang", NGAY[54], NGAY[54])
    assert s63.dinh_swing_cuoi.gia == 33500.0 and s63.day_swing_cuoi.gia == 29000.0
    assert not s63.canh_bao_dao_chieu and s63.thien_huong_swing == "tang"
    for t in (69, 75):
        s = C.trang_thai_dow(r, t)
        assert s.thuy_trieu == "tang" and s.thien_huong_swing == "giam"
        assert s.canh_bao_dao_chieu and s.ngay_biet_canh_bao == NGAY[69]
        assert s.moc_phu_dinh.gia == 29000.0                          # nhãn thủy triều KHÔNG đổi theo cảnh báo
    assert C.trang_thai_dow(r, 75).su_kien_cuoi_swing.loai == "BOS"
    assert C.trang_thai_dow(r, 69).su_kien_cuoi_swing.loai == "CHOCH"
    s79 = C.trang_thai_dow(r, 79)
    assert (s79.thuy_trieu, s79.moc_phu_dinh, s79.canh_bao_dao_chieu) == ("lan", None, False)
    assert s79.ngay_biet_thuy_trieu == NGAY[79] and s79.day_swing_cuoi.nhan == "LL"
    assert C.trang_thai_dow(r).chi_so_t == 79                          # mặc định: nến cuối


def test_thuy_trieu_GIAM_o_anh_guong_va_moc_phu_dinh_la_dinh_swing():
    r = C.doc_cau_truc(_df(_guong(_BOS)))
    s = C.trang_thai_dow(r, 54)
    assert (s.thuy_trieu, s.ngay_biet_thuy_trieu) == ("giam", NGAY[54])
    assert (s.moc_phu_dinh.loai, s.moc_phu_dinh.gia, s.moc_phu_dinh.chi_so_xay_ra) == ("dinh", 50000.0 - 9000.0, 50)
    s = C.trang_thai_dow(r, 69)
    assert s.thien_huong_swing == "tang" and s.canh_bao_dao_chieu and s.ngay_biet_canh_bao == NGAY[69]


def test_ngay_biet_la_ngay_doan_hien_tai_bat_dau_khong_phai_ngay_pivot_cuoi():
    """Tide không đổi khi có thêm pivot cùng chiều; mốc phủ định đổi khi đáy mới HL đến — `ngay_biet` đi theo giá trị."""
    dong = [_P("swing", "dinh", 10, 13, 90.0), _P("swing", "day", 20, 23, 60.0),
            _P("swing", "dinh", 30, 33, 100.0, nhan="HH"), _P("swing", "day", 40, 43, 70.0, nhan="HL"),
            _P("swing", "dinh", 50, 53, 110.0, nhan="HH"), _P("swing", "day", 60, 63, 80.0, nhan="HL")]
    s = C.trang_thai_tu_nhat_ky(dong, (), (), 70)
    assert (s.thuy_trieu, s.ngay_biet_thuy_trieu) == ("tang", NGAY[43])        # tăng từ khi đủ HH + HL (nến 43)
    assert (s.moc_phu_dinh.gia, s.ngay_biet_moc_phu_dinh) == (80.0, NGAY[63])  # mốc đổi theo đáy HL mới
    s = C.trang_thai_tu_nhat_ky(dong, (), (), 55)
    assert (s.moc_phu_dinh.gia, s.ngay_biet_moc_phu_dinh) == (70.0, NGAY[43])


def test_trang_thai_chi_dung_dong_da_biet_tai_t():
    dong = [_P("swing", "dinh", 10, 13, 90.0), _P("swing", "day", 20, 23, 60.0),
            _P("swing", "dinh", 30, 33, 100.0, nhan="HH"), _P("swing", "day", 40, 43, 70.0, nhan="HL")]
    assert C.trang_thai_tu_nhat_ky(dong, (), (), 42).thuy_trieu == "chua_du_bang_chung"     # đáy HL chưa biết
    assert C.trang_thai_tu_nhat_ky(dong, (), (), 43).thuy_trieu == "tang"


# ── 5. con sóng (đặc tả 5.8) ──────────────────────────────────────────────────────────────
def _swing_tang():
    return [_P("swing", "day", 0, 3, 50.0), _P("swing", "dinh", 10, 13, 90.0),
            _P("swing", "day", 20, 23, 60.0, nhan="HL"), _P("swing", "dinh", 30, 33, 100.0, nhan="HH")]


def _logs_song(b_gia, thoi_gian):
    """Thủy triều TĂNG (swing: đáy 60 HL, đỉnh 100 HH). Nhịp ngược xuống: đỉnh nội bộ A=100 (xảy ra 30) →
    đáy nội bộ B (xảy ra 30+thoi_gian, giá b_gia). Nhịp chính = 100 − 60 = 40 ⇒ 3/8 = 15."""
    swing = _swing_tang()
    noi = [_P("noi_bo", "dinh", 30, 31, 100.0), _P("noi_bo", "day", 30 + thoi_gian, 32 + thoi_gian, b_gia)]
    return sorted(swing + noi, key=lambda p: (p.chi_so_biet, p.cap != "noi_bo"))


def test_CON_SONG_dung_tay_tren_chuoi_BOS():
    """Duy nhất một nhịp ngược hoàn tất, ở nến 77 (đáy nội bộ 25.500 xảy ra 75): thủy triều khi ấy TĂNG (đáy swing
    25.500 mới biết ở nến 79), nhịp xuống từ đỉnh 33.500 (59). Nhịp chính: đáy swing 29.000 → 33.500 = 4.500; nhịp
    ngược 8.000 ⇒ tỷ lệ 16/9 ≥ 3/8; 16 phiên ≥ 10 ⇒ đủ điều kiện. Các nhịp khác không vào: nhịp xuống 30.000→26.000
    (biết 30) khi chưa có thủy triều, 33.000→29.000 (biết 52) khi mới có HH mà chưa có HL; nhịp lên 29.000→33.500 (biết 61)
    CÙNG chiều thủy triều tăng."""
    r = C.doc_cau_truc(_df(_BOS))
    assert len(r.con_song) == 1
    w = r.con_song[0]
    assert (w.chieu, w.thuy_trieu, w.diem_dau.chi_so_xay_ra, w.diem_cuoi.chi_so_xay_ra, w.chi_so_biet) == \
        ("giam", "tang", 59, 75, 77)
    assert (w.moc_nhip_chinh.gia, w.bien_do, w.bien_do_nhip_chinh, w.so_phien) == (29000.0, 8000.0, 4500.0, 16)
    assert w.ty_le == 8000.0 / 4500.0 and w.du_dieu_kien
    assert (w.ngay_xay_ra, w.ngay_biet) == (NGAY[75], NGAY[77])
    # nhịp đang chạy không vào nhật ký: bảng dừng ở nến 76, một nến trước khi đáy nội bộ được xác nhận (nến 77)
    assert C.doc_cau_truc(_df(_BOS[:77])).con_song == ()
    assert len(C.doc_cau_truc(_df(_BOS[:78])).con_song) == 1


def test_CON_SONG_anh_guong_nhip_nguoc_la_nhip_LEN_khi_thuy_trieu_giam():
    r = C.doc_cau_truc(_df(_guong(_BOS)))
    assert len(r.con_song) == 1
    w = r.con_song[0]
    assert (w.chieu, w.thuy_trieu, w.diem_dau.loai, w.diem_cuoi.loai, w.chi_so_biet) == ("tang", "giam", "day", "dinh", 77)
    assert (w.bien_do, w.bien_do_nhip_chinh) == (8000.0, 4500.0) and w.du_dieu_kien


@pytest.mark.parametrize("b_gia,thoi_gian,mong", [
    (85, 10, True),       # đúng 3/8 (15/40 = 0,375) VÀ đúng 10 phiên: cả hai biên đều bao gồm (≥)
    (85, 9, False),       # đủ biên độ, thiếu 1 phiên
    (86, 10, False),      # 14/40 = 0,35 < 3/8 dù đủ 10 phiên (đột biến 10: VÀ → HOẶC cho True)
    (86, 40, False),      # thời gian dài mấy cũng không bù biên độ thiếu
    (60, 10, True), (50, 25, True),                    # nhịp ngược sâu hơn cả nhịp chính vẫn là nhịp ngược
    (98, 20, False),
])
def test_CON_SONG_mac_dinh_3_8_VA_10_phien__dot_bien_10(b_gia, thoi_gian, mong):
    song = C.con_song_tu_nhat_ky(_logs_song(b_gia, thoi_gian))
    assert len(song) == 1
    assert song[0].du_dieu_kien is mong
    assert C.du_dieu_kien_o(song[0]) is mong


@pytest.mark.parametrize("b_gia,thoi_gian,o,mong", [
    (86, 10, (("nhip_chinh", 1 / 3), 10, "va"), True),       # 0,35 ≥ 1/3
    (86, 10, (("phan_tram", 0.03), 10, "va"), True),         # 14% giá đỉnh ≥ 3%
    (98, 20, (("phan_tram", 0.03), 15, "va"), False),        # 2% < 3%
    (98, 20, (("phan_tram", 0.03), 15, "hoac"), True),       # nhưng 20 ≥ 15 ⇒ HOẶC đủ
    (85, 9, (("nhip_chinh", 3 / 8), 10, "hoac"), True),
    (85, 9, (("nhip_chinh", 3 / 8), 8, "va"), True),         # 9 ≥ 8
    (85, 9, (("nhip_chinh", 3 / 8), 15, "va"), False),
    (86, 8, (("nhip_chinh", 1 / 3), 8, "va"), True),
])
def test_CON_SONG_luoi_18_o(b_gia, thoi_gian, o, mong):
    song = C.con_song_tu_nhat_ky(_logs_song(b_gia, thoi_gian))[0]
    assert C.du_dieu_kien_o(song, *o) is mong


def test_luoi_song_du_18_o_va_hoac_chua_hon_va():
    o = [(b, p, k) for b in C.LUOI_SONG["bien_do"] for p in C.LUOI_SONG["phien"] for k in C.LUOI_SONG["kieu"]]
    assert len(o) == 18 and (C.BIEN_DO_SONG, C.PHIEN_SONG, C.KIEU_SONG) in o
    for b_gia, tg in ((85, 10), (86, 10), (98, 20), (85, 9), (60, 3)):
        song = C.con_song_tu_nhat_ky(_logs_song(b_gia, tg))[0]
        for b in C.LUOI_SONG["bien_do"]:
            for p in C.LUOI_SONG["phien"]:
                assert C.du_dieu_kien_o(song, b, p, "va") <= C.du_dieu_kien_o(song, b, p, "hoac")
    with pytest.raises(ValueError):
        C.du_dieu_kien_o(song, ("lạ", 1), 10, "va")
    with pytest.raises(ValueError):
        C.du_dieu_kien_o(song, C.BIEN_DO_SONG, 10, "xor")


def test_CON_SONG_chi_nhip_NGUOC_chieu_thuy_trieu_va_chi_khi_thuy_trieu_ro():
    # nhịp LÊN trong thủy triều tăng: không phải nhịp ngược
    swing = _swing_tang()
    cung = [_P("noi_bo", "day", 30, 31, 40.0), _P("noi_bo", "dinh", 45, 47, 100.0)]
    assert C.con_song_tu_nhat_ky(sorted(swing + cung, key=lambda p: p.chi_so_biet)) == ()
    # thủy triều lẫn (đáy LL) hoặc chưa đủ: không có nhịp ngược nào
    lan = [replace(p, nhan="LL") if p.cap == "swing" and p.chi_so_xay_ra == 20 else p for p in _logs_song(85, 10)]
    assert C.con_song_tu_nhat_ky(lan) == ()
    assert C.con_song_tu_nhat_ky([p for p in _logs_song(85, 10) if p.cap == "noi_bo"]) == ()


def test_CON_SONG_thuy_trieu_doc_luc_BIET_khong_doc_luc_xay_ra():
    """Đáy nội bộ B biết ở nến 42 nhưng đáy swing HL biết ở nến 43 ⇒ tại 42 chưa có thủy triều tăng ⇒ không có sóng."""
    swing = _swing_tang()
    muon = [replace(p, ngay_biet=NGAY[43], chi_so_biet=43) if p.chi_so_xay_ra == 20 else p for p in swing]
    noi = [_P("noi_bo", "dinh", 30, 31, 100.0), _P("noi_bo", "day", 40, 42, 70.0)]
    assert C.con_song_tu_nhat_ky(sorted(muon + noi, key=lambda p: (p.chi_so_biet, p.cap != "noi_bo"))) == ()
    ok = sorted(swing + noi, key=lambda p: (p.chi_so_biet, p.cap != "noi_bo"))
    assert len(C.con_song_tu_nhat_ky(ok)) == 1


def test_CON_SONG_khong_co_nhip_chinh_thi_khong_du_bien_do_nhung_hoac_van_theo_thoi_gian():
    swing = [_P("swing", "day", 20, 23, 60.0, nhan="HL"), _P("swing", "dinh", 30, 33, 100.0, nhan="HH")]
    # hai swing có mặt nhưng đáy swing nằm SAU đỉnh nội bộ A (xảy ra 25 > 20?) — dùng đáy xảy ra sau A ⇒ không có đáy trước A
    noi = [_P("noi_bo", "dinh", 15, 16, 100.0), _P("noi_bo", "day", 30, 34, 70.0)]
    song = C.con_song_tu_nhat_ky(sorted(swing + noi, key=lambda p: (p.chi_so_biet, p.cap != "noi_bo")))
    assert len(song) == 1 and song[0].moc_nhip_chinh is None and song[0].ty_le is None
    assert song[0].du_dieu_kien is False                                     # VÀ: biên độ không xác minh được
    assert C.du_dieu_kien_o(song[0], C.BIEN_DO_SONG, 10, "hoac") is True      # HOẶC: 15 phiên ≥ 10


# ── 6. chu kỳ 4 giai đoạn (đặc tả 6) ──────────────────────────────────────────────────────
def _khung(closes, vols):
    n = len(closes)
    return pd.DataFrame({"time": pd.date_range("2025-01-01", periods=n, freq="B").strftime("%Y-%m-%d"),
                         "open": list(closes), "close": list(closes),
                         "high": [c * 1.005 for c in closes], "low": [c * 0.995 for c in closes],
                         "volume": list(vols)})


def _doan(tu, den, n):
    if n == 1:
        return [den]
    buoc = (den - tu) / (n - 1)
    return [tu + buoc * i for i in range(n)]


def _tich_luy():
    closes = (_doan(100, 80, 50) + _doan(78, 72, 3) + _doan(73, 78, 6)
              + [76, 75, 74, 76, 77, 75, 74, 76, 77, 76] * 3 + [75])
    vols = ([1000] * 50 + [4000] * 3 + [1500] * 6 + [800] * 31)
    closes, vols = closes[:90], vols[:90]
    closes += [75, 74, 75, 74, 75, 74, 75, 74, 75, 74]
    vols += [800] * 10
    return _khung(closes, vols)


def _phan_phoi():
    closes = (_doan(80, 100, 50) + _doan(102, 108, 3) + _doan(107, 100, 6)
              + [102, 103, 104, 102, 103, 105, 102, 103, 104, 103] * 3 + [103])
    vols = ([1000] * 50 + [4000] * 3 + [1500] * 6 + [800] * 31)
    closes, vols = closes[:90], vols[:90]
    closes += [103, 104, 103, 104, 103, 104, 103, 104, 103, 104]
    vols += [800] * 10
    return _khung(closes, vols)


def _dat(df, i, *, close=None, low=None, high=None, volume=None):
    ra = df.copy()
    if close is not None:
        ra.loc[i, "close"] = close
        ra.loc[i, "open"] = close
    if low is not None:
        ra.loc[i, "low"] = low
    if high is not None:
        ra.loc[i, "high"] = high
    if volume is not None:
        ra.loc[i, "volume"] = volume
    return ra


def _pha(ten):
    """Các `PhaWyckoff` THẬT từ `pha_wyckoff.doc_pha` (không dựng tay đối tượng giả)."""
    if ten == "A":
        return wy.doc_pha(_tich_luy().iloc[:80].reset_index(drop=True))
    if ten == "B":
        return wy.doc_pha(_tich_luy())
    if ten == "C_tich":
        df = _dat(_dat(_tich_luy(), 93, close=74.0, low=70.0, volume=400), 96, close=74.0, low=70.5, volume=300)
        return wy.doc_pha(df)
    if ten == "C_phan":
        return wy.doc_pha(_dat(_phan_phoi(), 93, close=104.0, high=112.0, volume=2500))
    if ten == "D_tich":
        return wy.doc_pha(_dat(_tich_luy(), 95, close=85.0, high=85.5, volume=3000))
    if ten == "E_up":
        df = _tich_luy()
        for i in (97, 98, 99):
            df = _dat(df, i, close=85.0, high=85.5, volume=2000)
        return wy.doc_pha(df)
    if ten == "E_down":
        df = _phan_phoi()
        for i in (97, 98, 99):
            df = _dat(df, i, close=95.0, low=94.5, volume=2000)
        return wy.doc_pha(df)
    if ten == "khong_nen_ngan":
        return wy.doc_pha(_tich_luy().tail(30).reset_index(drop=True))
    if ten == "khong_bien_rong":
        closes = (_doan(100, 80, 50) + _doan(78, 40, 3) + _doan(42, 95, 6) + _doan(95, 60, 31) + _doan(60, 90, 10))
        return wy.doc_pha(_khung(closes, [1000] * 50 + [4000] * 3 + [1500] * 6 + [800] * 41))
    raise KeyError(ten)


def _tt(thuy_trieu, ngay="2025-03-03"):
    return replace(C.TrangThaiDow(), thuy_trieu=thuy_trieu, ngay_biet_thuy_trieu=ngay)


TIDES = (C.TANG, C.GIAM, C.LAN, C.CHUA_DU)


def test_chuoi_Wyckoff_ma_phep_ghep_doc_khop_voi_pha_wyckoff_that():
    """Phép ghép đọc `cau_truc` / `su_kien` bằng CHUỖI; chuỗi gõ lệch một dấu thì mọi nhánh chết im. Đối chiếu với đầu ra
    THẬT của `doc_pha` trên các khung dựng sẵn."""
    assert (_pha("B").pha, _pha("B").cau_truc) == ("B", C._WY_CHUA_PHAN_DINH)
    assert (_pha("C_tich").cau_truc, _pha("C_phan").cau_truc) == (C._WY_TICH_LUY, C._WY_PHAN_PHOI)
    e1, e2 = _pha("E_up"), _pha("E_down")
    assert (e1.pha, e1.su_kien, e2.pha, e2.su_kien) == (C._WY_PHA_RA_VUNG, C._WY_MARKUP, C._WY_PHA_RA_VUNG, C._WY_MARKDOWN)
    assert _pha("A").pha == "A" and _pha("D_tich").pha == "D"
    assert not _pha("khong_nen_ngan").ket_luan_duoc and not _pha("khong_bien_rong").ket_luan_duoc


@pytest.mark.parametrize("ten,tt", [(t, x) for t in ("A", "C_tich", "D_tich") for x in TIDES])
def test_TRONG_VUNG_tich_luy_do_Wyckoff_quyet_khong_do_thuy_trieu__dot_bien_13(ten, tt):
    c = C.ghep_chu_ky(_tt(tt), _pha(ten))
    assert (c.giai_doan, c.nguon, c.mau_thuan) == (C.TICH_LUY, "pha_wyckoff", False)
    assert c.thuy_trieu == tt
    if tt == C.GIAM:
        assert any("thường gặp" in g for g in c.ghi_chu)         # vùng sau xu hướng giảm: hình dạng kinh điển
    else:
        assert not any("thường gặp" in g for g in c.ghi_chu)


@pytest.mark.parametrize("tt", TIDES)
def test_TRONG_VUNG_phan_phoi(tt):
    c = C.ghep_chu_ky(_tt(tt), _pha("C_phan"))
    assert (c.giai_doan, c.nguon, c.mau_thuan) == (C.PHAN_PHOI, "pha_wyckoff", False)
    assert any("thường gặp" in g for g in c.ghi_chu) == (tt == C.TANG)


@pytest.mark.parametrize("tt", TIDES)
def test_pha_B_la_chua_du_bang_chung_du_thuy_trieu_ra_sao(tt):
    c = C.ghep_chu_ky(_tt(tt), _pha("B"))
    assert (c.giai_doan, c.nguon) == ("chưa đủ bằng chứng", "pha_wyckoff")
    assert "chưa phân định tích luỹ hay phân phối" in c.ly_do and not c.mau_thuan


@pytest.mark.parametrize("ten,gd,nguoc", [("E_up", C.MARKUP, C.GIAM), ("E_down", C.MARKDOWN, C.TANG)])
def test_pha_E_MAU_THUAN_thuy_trieu_thi_hien_ca_hai_khong_ghi_de__dot_bien_12(ten, gd, nguoc):
    c = C.ghep_chu_ky(_tt(nguoc), _pha(ten))
    assert c.giai_doan == gd and c.nguon == "pha_wyckoff" and c.mau_thuan                # nhãn KHÔNG đổi
    assert c.ghi_chu[0].startswith("thủy triều swing chưa xác nhận") and C.TEN_THUY_TRIEU[nguoc] in c.ghi_chu[0]
    assert gd in c.ghi_chu[0]                                                           # nêu cả hai phép đọc
    assert c.thuy_trieu == nguoc


@pytest.mark.parametrize("ten,gd,xuoi", [("E_up", C.MARKUP, C.TANG), ("E_down", C.MARKDOWN, C.GIAM)])
@pytest.mark.parametrize("hai", [True, False])
def test_pha_E_khong_mau_thuan_khi_cung_chieu_hoac_thuy_trieu_chua_ro(ten, gd, xuoi, hai):
    tides = (xuoi,) if hai else (C.LAN, C.CHUA_DU)
    for tt in tides:
        c = C.ghep_chu_ky(_tt(tt), _pha(ten))
        assert (c.giai_doan, c.nguon, c.mau_thuan) == (gd, "pha_wyckoff", False)
        assert not c.ghi_chu[0].startswith("thủy triều swing chưa xác nhận")


@pytest.mark.parametrize("ten", ["khong_nen_ngan", "khong_bien_rong"])
def test_NGOAI_VUNG_Wyckoff_khong_ket_luan_thi_thuy_trieu_cho_Markup_Markdown(ten):
    pha = _pha(ten)
    up = C.ghep_chu_ky(_tt(C.TANG), pha)
    assert (up.giai_doan, up.nguon, up.mau_thuan) == (C.MARKUP, "thuy_trieu", False)
    assert C.GHI_CHU_KHONG_CO_VUNG in up.ghi_chu and pha.nhan_day in up.ghi_chu
    down = C.ghep_chu_ky(_tt(C.GIAM), pha)
    assert (down.giai_doan, down.nguon) == (C.MARKDOWN, "thuy_trieu")
    for tt in (C.LAN, C.CHUA_DU):
        c = C.ghep_chu_ky(_tt(tt), pha)
        assert (c.giai_doan, c.nguon) == ("chưa đủ bằng chứng", "thuy_trieu")


def test_tu_thuy_trieu_KHONG_BAO_GIO_suy_ra_tich_luy_hay_phan_phoi__dot_bien_13():
    for ten in ("khong_nen_ngan", "khong_bien_rong"):
        for tt in TIDES:
            assert C.ghep_chu_ky(_tt(tt), _pha(ten)).giai_doan not in (C.TICH_LUY, C.PHAN_PHOI), (ten, tt)
    # và ngược lại: mọi nhánh cho Tích luỹ / Phân phối đều có nguồn pha_wyckoff
    for ten in ("A", "B", "C_tich", "C_phan", "D_tich", "E_up", "E_down", "khong_nen_ngan", "khong_bien_rong"):
        for tt in TIDES:
            c = C.ghep_chu_ky(_tt(tt), _pha(ten))
            if c.giai_doan in (C.TICH_LUY, C.PHAN_PHOI):
                assert c.nguon == "pha_wyckoff", (ten, tt)


def test_giai_doan_chi_nam_trong_nam_gia_tri_va_nguon_nam_trong_hai():
    ok = {C.TICH_LUY, C.MARKUP, C.PHAN_PHOI, C.MARKDOWN, "chưa đủ bằng chứng"}
    for ten in ("A", "B", "C_tich", "C_phan", "D_tich", "E_up", "E_down", "khong_nen_ngan", "khong_bien_rong"):
        for tt in TIDES:
            c = C.ghep_chu_ky(_tt(tt), _pha(ten))
            assert c.giai_doan in ok and c.nguon in ("pha_wyckoff", "thuy_trieu") and c.ly_do
            assert c.thuy_trieu == tt and c.ngay_biet_thuy_trieu == "2025-03-03"


def test_ghep_chu_ky_khong_doan_khi_pha_la_cau_truc_la():
    class Gia:
        ket_luan_duoc = True
        pha, cau_truc, su_kien, nhan_ngan, nhan_day = "C", "LẠ", None, "x", "x"
    with pytest.raises(ValueError):
        C.ghep_chu_ky(_tt(C.TANG), Gia)
    Gia.pha, Gia.su_kien = "E", "Lạ"
    with pytest.raises(ValueError):
        C.ghep_chu_ky(_tt(C.TANG), Gia)


def test_ghep_chu_ky_khong_sua_pha_wyckoff_va_khong_doi_nhan():
    pha = _pha("E_up")
    truoc = repr(pha)
    c = C.ghep_chu_ky(_tt(C.GIAM), pha)
    assert repr(pha) == truoc and c.giai_doan == "Markup"


CAM_LOI = ["sẽ", "dự báo", "tín hiệu mua", "tín hiệu bán", "khuyến nghị", "đáng mua", "đảo chiều chắc chắn",
           "xác nhận xu hướng chính"]


def test_loi_cua_chu_ky_khong_hua_du_bao():
    """Mọi chuỗi mà `ghep_chu_ky` sinh ra, ở mọi nhánh, vắng các từ cấm của đặc tả 7.2 (Lát 3 gác lời của khối giao diện)."""
    chuoi = []
    for ten in ("A", "B", "C_tich", "C_phan", "D_tich", "E_up", "E_down", "khong_nen_ngan", "khong_bien_rong"):
        for tt in TIDES:
            c = C.ghep_chu_ky(_tt(tt), _pha(ten))
            chuoi += [c.giai_doan, c.nguon, c.ly_do, *c.ghi_chu]
    chuoi += [C.GHI_CHU_KHONG_CO_VUNG, *C.TEN_THUY_TRIEU.values()]
    assert len(chuoi) > 100
    for s in chuoi:
        for tu in CAM_LOI:
            assert not re.search(rf"(?<!\w){re.escape(tu)}(?!\w)", s, flags=re.I), (tu, s)


def test_ghep_end_to_end_tren_khung_that_khong_no_va_khop_Wyckoff():
    df = _tich_luy()
    cs = C.doc_cau_truc(df, he_so_gia=1000.0)
    c = C.ghep_chu_ky(C.trang_thai_dow(cs), wy.doc_pha(df, 1000.0))
    assert c.giai_doan == "chưa đủ bằng chứng" and c.nguon == "pha_wyckoff"          # khung này là pha B
    df2 = _tich_luy()
    for i in (97, 98, 99):
        df2 = _dat(df2, i, close=85.0, high=85.5, volume=2000)
    c2 = C.ghep_chu_ky(C.trang_thai_dow(C.doc_cau_truc(df2, he_so_gia=1000.0)), wy.doc_pha(df2, 1000.0))
    assert c2.giai_doan == "Markup" and c2.nguon == "pha_wyckoff"
