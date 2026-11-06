"""Gác cho Lát 4 của C1 (BƯỚC 257): luật VÀO theo kế hoạch B6 (PB-003) trong sân đấu — `LuatKhopKeHoach`,
`PaperTradingJournal.fill_pending(luat_khop=…)`, `san_dau.phat_lai(ke_hoach=…)` và hàng PB-003 của
`tools/san_dau.py bang` (`docs/thiet-ke-c1-san-dau.md` mục 7, 10.2, 12).

Năm nhánh `phan_quyet` mà đặc tả đòi, MỖI nhánh một test riêng: mua ngay · chờ vùng khớp · chờ vùng hết hạn · bỏ qua
· thiếu kế hoạch. Cộng:
  · PHÉP THỬ TƯƠNG ĐƯƠNG vẫn đúng ở nhánh mới: mọi tín hiệu `MUA_NGAY` thì lệnh phát lại bằng ĐÚNG lệnh của luật mở
    cửa (cả kịch bản mười mã × 95 phiên);
  · bộ phát lại đi từng phiên (`khop_mot_phien`) khớp với dụng cụ ĐO 25 đi cả cửa sổ (`tim_khop`) ở mọi mẫu ngẫu nhiên;
  · lệnh KHÔNG BAO GIỜ ĐƯỢC ĐẶT (`BO_QUA`, `CHUA_LAP_DUOC`, thiếu kế hoạch) không giữ vốn cho mã khác cùng phiên;
  · cửa sổ RIÊNG của PB-003 (quyết định 4b): so với đường thật và rổ chỉ trên các tín hiệu và phiên từ ngày có
    dòng `ke_hoach` đầu tiên.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.append(str(GOC / "tools"))

import khop_gioi_han as KG  # noqa: E402
import paper_trading as pt  # noqa: E402
import san_dau as sd  # noqa: E402
import sinh_bang_vang_phien as S  # noqa: E402
from test_san_dau import (_cfg, _chay_that, _khung_vni, _lenh, _nap_cli,  # noqa: E402
                          _NguonKichBan, _qd, _sach_cache_phan_tich)
from test_san_dau_bang import _dung  # noqa: E402

assert _sach_cache_phan_tich  # fixture autouse nhập từ test_san_dau, giữ trong module này

B6 = "KE_HOACH_B6"
D0 = S.PHIEN[40]          # ngày tín hiệu của các ca một mã; FPT đóng 67,5 nghìn, mở phiên sau 67,5


@pytest.fixture(scope="module")
def gia():
    return S.dung_gia()


def _kh(ma, ngay, phan_quyet, *, tran=None, so=5, seq=1, gia_dong=67500.0):
    """Một dòng `ke_hoach`. `gia_dong` mặc định 67.500 = đóng cửa FPT ngày `D0` ở khung tổng hợp (đúng thang)."""
    return {"seq": seq, "symbol": ma, "signal_date": ngay, "phan_quyet": phan_quyet,
            "vung_day": None if tran is None else tran - 500.0, "vung_tran": tran, "gia_dong": gia_dong,
            "so_phien_cho": so if phan_quyet == "CHO_VUNG" else None}


def _chay(gia, qd, ke_hoach, *, cfg=None, ma=("FPT",), sua_gia=None, bat_dau=D0, ket_thuc=None):
    g = {m: gia[m].copy() for m in ma}
    for (m, i), (cot, v) in (sua_gia or {}).items():
        g[m].loc[i, cot] = v
    return sd.phat_lai(cfg or _cfg(luat_vao=B6), qd, g, _NguonKichBan(), ke_hoach=ke_hoach,
                       ngay_bat_dau=bat_dau, ngay_ket_thuc=ket_thuc)


def _mot(tk):
    ds = tk.lenh()
    assert len(ds) == 1, ds
    return ds[0]


# ── 1. năm nhánh phan_quyet ───────────────────────────────────────────────────────────────────
def test_NHANH_mua_ngay_vao_o_mo_cua_phien_sau_nhu_duong_that(gia):
    qd = [_qd("FPT", D0, 90, at=1.0, seq=1)]
    tk0 = sd.phat_lai(_cfg(), qd, {"FPT": gia["FPT"]}, _NguonKichBan(), ngay_bat_dau=D0)
    tk = _chay(gia, qd, [_kh("FPT", D0, "MUA_NGAY")])
    try:
        assert sd.so_sanh_lenh(tk0.lenh(), tk.lenh()) == []
        t = _mot(tk)
        assert t["entry_date"] == S.PHIEN[41] and t["status"] != "PENDING"
        assert tk.luat.ghi == {("FPT", D0): "MUA_NGAY"}
    finally:
        tk0.dong()
        tk.dong()


def test_NHANH_cho_vung_khop_o_phien_thu_ba_o_gia_TRAN_khong_phai_gia_mo_cua(gia):
    """Trần 67.300 (HOSE trên 50k, bước 100) → ngưỡng 67.200. Thấp 67.300 (hàng 41) và 67.600 (hàng 42) KHÔNG khớp;
    hàng 43 hạ xuống 67.000 → khớp, mở cửa 68.200 nên giá khớp cơ sở = trần 67.300."""
    qd = [_qd("FPT", D0, 90, at=1.0, seq=1)]
    tk = _chay(gia, qd, [_kh("FPT", D0, "CHO_VUNG", tran=67300.0)], sua_gia={("FPT", 43): ("low", 67.0)})
    try:
        t = _mot(tk)
        assert t["entry_date"] == S.PHIEN[43], t
        assert 67300.0 <= t["entry_price"] <= 67300.0 * 1.005, "giá vào = trần 67.300 (+ trượt giá nhỏ), không phải mở cửa 68.200"
        assert t["status"] in ("OPEN", "CLOSED")
        assert tk.luat.ghi == {("FPT", D0): "CHO_VUNG"}
    finally:
        tk.dong()


def test_khop_o_gia_duoi_cat_lo_ban_dau_duoc_DEM_khong_bi_giau(gia):
    """Trần 63.000 thấp hơn cắt lỗ ban đầu (~5% dưới 67.500): vào lệnh là vào dưới SL. Phát lại không giấu: nó ĐẾM
    (`khop_duoi_cat_lo`). Việc bộ máy làm gì với một lệnh như thế là của bộ máy (đặc tả mục 7: chỉ đổi luật VÀO)."""
    qd = [_qd("FPT", D0, 90, at=1.0, seq=1)]
    tk = _chay(gia, qd, [_kh("FPT", D0, "CHO_VUNG", tran=63000.0)], sua_gia={("FPT", 42): ("low", 62.0)})
    try:
        t = _mot(tk)
        assert t["entry_date"] == S.PHIEN[42] and t["entry_price"] <= 63000.0 * 1.005
        assert t["stop_loss"] > 63000.0, "giả định của ca: cắt lỗ ban đầu phải nằm TRÊN giá khớp"
        assert tk.luat.khop_duoi_cat_lo == {("FPT", D0)}
    finally:
        tk.dong()
    tk = _chay(gia, qd, [_kh("FPT", D0, "MUA_NGAY")])
    try:
        assert tk.luat.khop_duoi_cat_lo == set(), "mua ngay ở 67.500 không thủng SL"
    finally:
        tk.dong()


def test_NHANH_cho_vung_khop_o_phien_thu_NAM_nhung_khong_o_phien_thu_SAU(gia):
    qd = [_qd("FPT", D0, 90, at=1.0, seq=1)]
    kh = [_kh("FPT", D0, "CHO_VUNG", tran=67300.0)]
    tk = _chay(gia, qd, kh, sua_gia={("FPT", 45): ("low", 67.0)})          # t + 5: còn trong cửa sổ
    try:
        assert _mot(tk)["entry_date"] == S.PHIEN[45]
    finally:
        tk.dong()
    tk = _chay(gia, qd, kh, sua_gia={("FPT", 46): ("low", 67.0)})          # t + 6: đã hết hạn ở hàng 45
    try:
        t = _mot(tk)
        assert t["status"] == sd.TRANG_THAI_HET_HAN and t["entry_date"] is None
        assert t["exit_date"] == S.PHIEN[45] and t["exit_reason"] == sd.LY_DO_HET_HAN
        assert sd.dem_lenh(tk.lenh())["het_han"] == 1
    finally:
        tk.dong()


def test_NHANH_cho_vung_het_han_giai_phong_von_va_ma_vao_lai_duoc(gia):
    """Lệnh hết hạn ở hàng 45 phải thôi giữ vốn VÀ thôi chặn mã: tín hiệu mới ở hàng 46 vào được."""
    qd = [_qd("FPT", D0, 90, at=1.0, seq=1), _qd("FPT", S.PHIEN[46], 90, at=2.0, seq=2)]
    kh = [_kh("FPT", D0, "CHO_VUNG", tran=67300.0, seq=1), _kh("FPT", S.PHIEN[46], "MUA_NGAY", seq=2)]
    tk = _chay(gia, qd, kh, ket_thuc=S.PHIEN[47])
    try:
        ds = tk.lenh()
        assert [(t["signal_date"], t["status"]) for t in ds][0] == (D0, sd.TRANG_THAI_HET_HAN)
        assert ds[1]["signal_date"] == S.PHIEN[46] and ds[1]["entry_date"] == S.PHIEN[47]
    finally:
        tk.dong()


@pytest.mark.parametrize("phan_quyet", ["BO_QUA", "CHUA_LAP_DUOC"])
def test_NHANH_bo_qua_va_chua_lap_duoc_khong_vao_lenh_va_duoc_dem(gia, phan_quyet):
    qd = [_qd("FPT", D0, 90, at=1.0, seq=1)]
    tk = _chay(gia, qd, [_kh("FPT", D0, phan_quyet)])
    try:
        assert tk.lenh() == []
        assert tk.luat.ghi == {("FPT", D0): phan_quyet}
    finally:
        tk.dong()


def test_NHANH_cho_vung_lech_thang_gia_KHONG_khop_gia_va_duoc_dem_RIENG(gia):
    """Vùng chờ là giá tuyệt đối ở thang LÚC QUÉT; khung giá tải hôm nay có thể đã điều chỉnh quyền (TCB 06/11/2026:
    lệch đúng 33,3%). Lệch quá `DUNG_SAI_THANG_GIA` thì không khớp được và KHÔNG vào lệnh — nếu không, giá mở cửa
    đã điều chỉnh thấp hơn vùng cả một phần ba và lệnh chờ 'khớp' ngay phiên đầu, ở giá mở cửa."""
    qd = [_qd("FPT", D0, 90, at=1.0, seq=1)]
    # vùng chờ ở thang chưa điều chỉnh (×1,5): đóng cửa khung giá 67.500, gia_dong đã ghi 101.250
    kh = [_kh("FPT", D0, "CHO_VUNG", tran=100000.0, gia_dong=101250.0)]
    tk = _chay(gia, qd, kh)
    try:
        assert tk.lenh() == [] and tk.luat.ghi == {("FPT", D0): sd.LECH_THANG_GIA}
    finally:
        tk.dong()
    # cùng ca, thang ĐÚNG: lệnh chờ ở lại và (mở cửa 67.500 <= trần 100.000, thấp 67.300 <= 99.900) khớp ngay phiên đầu
    tk = _chay(gia, qd, [_kh("FPT", D0, "CHO_VUNG", tran=100000.0, gia_dong=67500.0)])
    try:
        assert _mot(tk)["entry_date"] == S.PHIEN[41] and tk.luat.ghi == {("FPT", D0): "CHO_VUNG"}
    finally:
        tk.dong()


def test_lech_thang_gia_bien_o_DUNG_SAI(gia):
    assert sd.DUNG_SAI_THANG_GIA == 0.005
    qd = [_qd("FPT", D0, 90, at=1.0, seq=1)]
    for gia_dong, mong in [(67500.0 / 1.0049, "CHO_VUNG"), (67500.0 * 1.0049, "CHO_VUNG"),
                           (67500.0 / 1.0051, sd.LECH_THANG_GIA), (67500.0 * 0.9949, sd.LECH_THANG_GIA)]:
        tk = _chay(gia, qd, [_kh("FPT", D0, "CHO_VUNG", tran=67300.0, gia_dong=gia_dong)])
        try:
            assert tk.luat.ghi == {("FPT", D0): mong}, gia_dong
        finally:
            tk.dong()


def test_NHANH_thieu_ke_hoach_khong_vao_lenh_va_duoc_dem_RIENG(gia):
    qd = [_qd("FPT", D0, 90, at=1.0, seq=1)]
    tk = _chay(gia, qd, [_kh("FPT", S.PHIEN[39], "MUA_NGAY")])             # có kế hoạch, nhưng của NGÀY khác
    try:
        assert tk.lenh() == []
        assert tk.luat.ghi == {("FPT", D0): sd.THIEU_KE_HOACH}
    finally:
        tk.dong()


def test_tin_hieu_duoi_nguong_khong_di_qua_luat_va_khong_bi_dem_thieu(gia):
    qd = [_qd("FPT", D0, 50, at=1.0, seq=1)]
    tk = _chay(gia, qd, [])
    try:
        assert tk.lenh() == [] and tk.luat.ghi == {}, "chỉ đếm tín hiệu mà BỘ MÁY đã mở lệnh"
    finally:
        tk.dong()


# ── 2. lệnh không được đặt không giữ vốn ──────────────────────────────────────────────────────
def test_lenh_KHONG_DUOC_DAT_khong_giu_von_cho_ma_khac_cung_phien(gia):
    """Trần vốn chỉ chừa chỗ cho MỘT lệnh. FPT (xử lý trước) mà MUA_NGAY thì VCB bị chặn; FPT mà BO_QUA thì dòng
    PENDING của nó bị xoá NGAY, VCB vào được — nếu giữ tới phiên sau thì VCB bị chặn oan bởi lệnh không tồn tại."""
    qd = [_qd("FPT", D0, 80, at=1.0, seq=1), _qd("VCB", D0, 80, at=2.0, seq=2)]
    tk0 = sd.phat_lai(_cfg(), qd, {m: gia[m] for m in ("FPT", "VCB")}, _NguonKichBan(),
                      ngay_bat_dau=D0, ngay_ket_thuc=D0)
    co = {r["symbol"]: r["size_pct"] for r in tk0.lenh()}
    tk0.dong()
    assert set(co) == {"FPT", "VCB"}
    tran = max(co.values()) + 0.01
    assert tran < sum(co.values())
    cfg = _cfg(luat_vao=B6, tran_von_cam_ket_pct=tran)
    for fpt, vcb, mong in [("MUA_NGAY", "MUA_NGAY", ["FPT"]), ("BO_QUA", "MUA_NGAY", ["VCB"]),
                           ("CHUA_LAP_DUOC", "MUA_NGAY", ["VCB"]), ("CHO_VUNG", "MUA_NGAY", ["FPT"])]:
        kh = [_kh("FPT", D0, fpt, tran=60000.0, seq=1), _kh("VCB", D0, vcb, seq=2, gia_dong=None)]
        tk = _chay(gia, qd, kh, cfg=cfg, ma=("FPT", "VCB"), ket_thuc=D0)
        try:
            assert [r["symbol"] for r in tk.lenh()] == mong, (fpt, vcb)
        finally:
            tk.dong()
    # thiếu kế hoạch cũng vậy
    tk = _chay(gia, qd, [_kh("VCB", D0, "MUA_NGAY", seq=2)], cfg=cfg, ma=("FPT", "VCB"), ket_thuc=D0)
    try:
        assert [r["symbol"] for r in tk.lenh()] == ["VCB"]
        assert tk.luat.ghi[("FPT", D0)] == sd.THIEU_KE_HOACH
    finally:
        tk.dong()


# ── 3. phép thử tương đương vẫn đúng ở nhánh mới ─────────────────────────────────────────────
@pytest.fixture(scope="module")
def kich_ban(gia):
    so, qd = _chay_that(_cfg(), gia, vni_df=_khung_vni(gia))
    thuc = _lenh(so)
    so.db.close()
    return thuc, qd


def test_TANG_A_moi_tin_hieu_MUA_NGAY_thi_B6_ra_DUNG_cac_lenh_cua_duong_that(gia, kich_ban):
    thuc, qd = kich_ban
    vni = _khung_vni(gia)
    kh = [_kh(r["symbol"], r["signal_date"], "MUA_NGAY", seq=i) for i, r in enumerate(qd, 1)]
    tk = sd.phat_lai(_cfg(luat_vao=B6), qd, gia, sd.NguonVni(vni), ke_hoach=kh, ngay_bat_dau=S.PHIEN[0])
    tk0 = sd.phat_lai(_cfg(), qd, gia, sd.NguonVni(vni), ngay_bat_dau=S.PHIEN[0])
    try:
        assert sd.so_sanh_lenh(thuc, tk.lenh()) == []
        assert sd.so_sanh_lenh(tk0.lenh(), tk.lenh()) == []
        assert len(thuc) >= 5 and tk.dem == tk0.dem
        assert set(tk.luat.ghi.values()) == {"MUA_NGAY"}
    finally:
        tk.dong()
        tk0.dong()


def test_TANG_A_B6_that_su_khac_duong_that_khi_ke_hoach_bao_bo_qua_va_cho_vung(gia, kich_ban):
    """Kịch bản phải CANH luật: nếu hai tài khoản ra cùng lệnh thì cờ không có tác dụng và gác trống."""
    thuc, qd = kich_ban
    vni = _khung_vni(gia)
    loai = ["MUA_NGAY", "BO_QUA", "CHO_VUNG", "CHUA_LAP_DUOC"]
    kh = []
    for i, r in enumerate(qd, 1):
        # vùng chờ nằm dưới thị trường 3% : phần lớn lệnh lỡ, vài lệnh khớp ở phiên giá rơi
        g = gia[r["symbol"]]
        dong = g[g["time"] == r["signal_date"]]
        tran = float(dong["close"].iloc[0]) * 1000.0 * 0.995 if len(dong) else None
        kh.append(_kh(r["symbol"], r["signal_date"], loai[i % 4], tran=tran, seq=i,
                      gia_dong=None if tran is None else tran / 0.995))
    tk = sd.phat_lai(_cfg(luat_vao=B6), qd, gia, sd.NguonVni(vni), ke_hoach=kh, ngay_bat_dau=S.PHIEN[0])
    try:
        assert sd.so_sanh_lenh(thuc, tk.lenh()), "B6 không khác đường thật: kịch bản không canh luật vào"
        assert {"BO_QUA", "CHO_VUNG", "CHUA_LAP_DUOC"} <= set(tk.luat.ghi.values())
        assert all(t["status"] != "PENDING" or t["signal_date"] >= S.PHIEN[-6] for t in tk.lenh())
    finally:
        tk.dong()


# ── 4. bộ phát lại đi từng phiên = dụng cụ ĐO 25 đi cả cửa sổ ─────────────────────────────────
def test_luat_xet_tung_phien_ra_dung_tim_khop_ca_cua_so__mau_ngau_nhien(gia):
    rng = np.random.default_rng(2570)
    ngay = [f"2026-10-{d:02d}" for d in range(1, 29)]
    da_khop = da_lo = 0
    for _ in range(200):
        mo = np.round(rng.uniform(20, 70, 28), 1)
        thap = np.round(mo - rng.uniform(0, 1.5, 28), 1)
        df = pd.DataFrame({"time": ngay, "open": mo, "high": mo + 1, "low": thap, "close": mo, "volume": 1.0})
        khung = sd._chuan_hoa_gia({"AAA": df})
        t = int(rng.integers(0, 15))
        tran = float(np.round(rng.uniform(20, 70), 1) * 1000)
        so = int(rng.integers(1, 8))
        san = str(rng.choice(["HOSE", "HNX", "UPCOM"]))
        luat = sd.LuatKhopKeHoach([_kh("AAA", ngay[t], "CHO_VUNG", tran=tran, so=so)], khung, lambda m, s=san: s)
        luat.ghi[("AAA", ngay[t])] = "CHO_VUNG"
        mong = KG.tim_khop(df, t, tran, san, 1000.0, so_phien_cho=so)
        kq = None
        for d in range(t + 1, len(df)):
            khop, gia_co_so, het_han = luat.xet({"symbol": "AAA", "signal_date": ngay[t]}, ngay[d],
                                                {"open": mo[d] * 1000.0, "low": thap[d] * 1000.0})
            if khop:
                kq = (d, gia_co_so)
                break
            if het_han:
                break
        assert kq == mong, (t, so, tran, san)
        da_khop += kq is not None
        da_lo += kq is None
    assert da_khop >= 20 and da_lo >= 20, "mẫu phải có cả ca khớp lẫn ca lỡ, nếu không phép so không canh gì"


def test_luat_het_han_dung_o_phien_cuoi_cua_cua_so_khong_som_khong_muon(gia):
    ngay = [f"2026-10-{d:02d}" for d in range(1, 15)]
    df = pd.DataFrame({"time": ngay, "open": 30.0, "high": 31.0, "low": 30.0, "close": 30.0, "volume": 1.0})
    khung = sd._chuan_hoa_gia({"AAA": df})
    luat = sd.LuatKhopKeHoach([_kh("AAA", ngay[2], "CHO_VUNG", tran=30000.0, so=3)], khung, lambda m: "HOSE")
    luat.ghi[("AAA", ngay[2])] = "CHO_VUNG"
    lenh = {"symbol": "AAA", "signal_date": ngay[2]}
    nen = {"open": 30000.0, "low": 30000.0}
    assert luat.xet(lenh, ngay[3], nen) == (False, None, False)       # t + 1
    assert luat.xet(lenh, ngay[4], nen) == (False, None, False)       # t + 2
    assert luat.xet(lenh, ngay[5], nen) == (False, None, True)        # t + 3 = phiên cuối: hết hạn
    assert luat.xet(lenh, ngay[6], nen) == (False, None, True)        # quá hạn: vẫn hết hạn, không khớp
    assert luat.xet(lenh, ngay[6], {"open": 29000.0, "low": 28000.0}) == (False, None, True), "quá hạn không được khớp"


def test_dem_b6_dem_dung_phan_quyet_ket_cuc_lenh_gioi_han_va_khop_duoi_cat_lo(gia):
    """`tools/san_dau._dem_b6` là nơi MỘT dòng của bảng nói PB-003 đã làm gì: sai ở đây thì bảng nói sai mà vẫn
    trông hợp lý. Mỗi ca dựng bằng bộ phát lại thật rồi đếm bằng tay."""
    cli = _nap_cli()
    qd = [_qd("FPT", D0, 90, at=1.0, seq=1)]

    def dem(kh, sua_gia=None, tu=D0, loai=frozenset()):
        tk = _chay(gia, qd, kh, sua_gia=sua_gia)
        try:
            return cli._dem_b6(tk, tu, set(loai))
        finally:
            tk.dong()

    khop_duoi = dem([_kh("FPT", D0, "CHO_VUNG", tran=63000.0)], {("FPT", 42): ("low", 62.0)})
    assert khop_duoi == {"tu": D0, "ke_hoach_dong": 1, "dat": {"CHO_VUNG": 1},
                         "cho_vung": {"khop": 1, "het_han": 0, "cho": 0, "huy": 0}, "khop_duoi_cat_lo": 1}
    het_han = dem([_kh("FPT", D0, "CHO_VUNG", tran=67300.0)], {("FPT", 46): ("low", 67.0)})
    assert het_han["cho_vung"] == {"khop": 0, "het_han": 1, "cho": 0, "huy": 0} and het_han["khop_duoi_cat_lo"] == 0
    cho = dem([_kh("FPT", D0, "CHO_VUNG", tran=67300.0)])          # 5 phiên không rơi tới trần; kịch bản dài hơn 5 phiên
    assert cho["cho_vung"]["het_han"] == 1                          # hết hạn thật (cửa sổ t+1..t+5 đã qua trong kịch bản)
    mot = dem([_kh("FPT", D0, "MUA_NGAY")])
    assert mot["dat"] == {"MUA_NGAY": 1} and mot["cho_vung"] == {"khop": 0, "het_han": 0, "cho": 0, "huy": 0}
    bo = dem([_kh("FPT", D0, "BO_QUA")])
    assert bo["dat"] == {"BO_QUA": 1} and bo["ke_hoach_dong"] == 1
    truoc = dem([_kh("FPT", D0, "BO_QUA")], tu=S.PHIEN[41])
    assert truoc["dat"] == {} and truoc["ke_hoach_dong"] == 0, "tín hiệu trước ngày bắt đầu của cửa sổ không đếm"
    ngoai = dem([_kh("FPT", D0, "BO_QUA")], loai={D0})
    assert ngoai["dat"] == {} and ngoai["ke_hoach_dong"] == 0, "ngày bị LOẠI không đếm"


def test_luat_xet_o_chinh_ngay_tin_hieu_khong_khop_va_khong_het_han(gia):
    ngay = [f"2026-10-{d:02d}" for d in range(1, 10)]
    df = pd.DataFrame({"time": ngay, "open": 20.0, "high": 31.0, "low": 20.0, "close": 30.0, "volume": 1.0})
    luat = sd.LuatKhopKeHoach([_kh("AAA", ngay[2], "CHO_VUNG", tran=30000.0, so=3)], sd._chuan_hoa_gia({"AAA": df}),
                              lambda m: "HOSE")
    luat.ghi[("AAA", ngay[2])] = "CHO_VUNG"
    assert luat.xet({"symbol": "AAA", "signal_date": ngay[2]}, ngay[2], {"open": 20000.0, "low": 20000.0}) == (
        False, None, False)


def test_so_phuong_an_that_co_PB003_dung_khuon_va_dung_cau_hinh():
    import json
    import phuong_an_bong as pab
    so = json.loads((GOC / "docs" / "phuong-an-bong.json").read_text(encoding="utf-8"))
    assert pab.vi_pham_so(so) == []
    pb = so["phuong_an"]["PB-003"]
    assert pb["lop"] == "tham_do" and pb["bo_co"] == {"luat_vao": B6}
    cfg = sd.cau_hinh_tu_phuong_an(_cfg(), pb)
    assert cfg.luat_vao == B6 and cfg == _cfg(luat_vao=B6), "PB-003 chỉ đổi luật vào, không cờ nào khác"


def test_luat_dong_het_han_chi_dong_lenh_dang_PENDING(gia):
    so = pt.PaperTradingJournal(":memory:")
    try:
        for tt in ("PENDING", "OPEN"):
            so.db.execute("INSERT INTO trades (symbol, exchange, signal_date, size_pct, status, created_at)"
                          " VALUES ('FPT', 'HOSE', '2026-09-03', 10.0, ?, 0)", (tt,))
        luat = sd.LuatKhopKeHoach([], {}, lambda m: "HOSE")
        luat.dong_het_han(so.db, 1, "2026-09-10 00:00:00")
        luat.dong_het_han(so.db, 2, "2026-09-10")
        r = [dict(x) for x in so.db.execute("SELECT status, exit_date, exit_reason FROM trades ORDER BY id")]
        assert r == [{"status": sd.TRANG_THAI_HET_HAN, "exit_date": "2026-09-10", "exit_reason": sd.LY_DO_HET_HAN},
                     {"status": "OPEN", "exit_date": None, "exit_reason": None}]
    finally:
        so.db.close()


# ── 5. đầu vào xấu thì NỔ, không đoán ─────────────────────────────────────────────────────────
def test_phat_lai_B6_can_ke_hoach__luat_mo_cua_cam_ke_hoach(gia):
    qd = [_qd("FPT", D0, 90, at=1.0, seq=1)]
    with pytest.raises(ValueError):
        sd.phat_lai(_cfg(luat_vao=B6), qd, {"FPT": gia["FPT"]}, _NguonKichBan(), ngay_bat_dau=D0)
    with pytest.raises(ValueError):
        sd.phat_lai(_cfg(), qd, {"FPT": gia["FPT"]}, _NguonKichBan(), ke_hoach=[], ngay_bat_dau=D0)
    tk = sd.phat_lai(_cfg(luat_vao=B6), qd, {"FPT": gia["FPT"]}, _NguonKichBan(), ke_hoach=[], ngay_bat_dau=D0)
    tk.dong()                                                    # danh sách RỖNG hợp lệ (khác None)


def test_ke_hoach_phan_quyet_la_hoac_cho_vung_thieu_vung_thi_NO(gia):
    with pytest.raises(ValueError):
        sd.LuatKhopKeHoach([_kh("FPT", D0, "MUA_VAO_DAY")], {}, lambda m: "HOSE")
    qd = [_qd("FPT", D0, 90, at=1.0, seq=1)]
    for hong in (_kh("FPT", D0, "CHO_VUNG", tran=None), _kh("FPT", D0, "CHO_VUNG", tran=0.0),
                 dict(_kh("FPT", D0, "CHO_VUNG", tran=67300.0), so_phien_cho=None),
                 _kh("FPT", D0, "CHO_VUNG", tran=67300.0, gia_dong=None),
                 _kh("FPT", D0, "CHO_VUNG", tran=67300.0, gia_dong=0.0)):
        with pytest.raises(ValueError):
            _chay(gia, qd, [hong])


def test_dong_ke_hoach_trung_khoa_giu_dong_seq_NHO_nhat(gia):
    luat = sd.LuatKhopKeHoach([_kh("FPT", D0, "BO_QUA", seq=9), _kh("FPT", D0 + " 00:00:00", "MUA_NGAY", seq=3),
                               _kh("FPT", D0, "CHUA_LAP_DUOC", seq=5)], {}, lambda m: "HOSE")
    assert luat.ke_hoach[("FPT", D0)]["phan_quyet"] == "MUA_NGAY"


def test_xet_lenh_khong_do_luat_dat_thi_NO(gia):
    luat = sd.LuatKhopKeHoach([], {}, lambda m: "HOSE")
    with pytest.raises(ValueError):
        luat.xet({"symbol": "FPT", "signal_date": D0}, S.PHIEN[41], {"open": 1.0, "low": 1.0})


# ── 6. bảng: hàng PB-003 và cửa sổ riêng ──────────────────────────────────────────────────────
PB3 = {"PB-003": {"lop": "tham_do", "bo_co": {"luat_vao": B6}, "khai_ngay": S.PHIEN[48], "commit": None,
                  "mo_ta": "x", "ly_do": "y"}}


def _ke_hoach_tu(qd, tu=None, phan_quyet="MUA_NGAY"):
    return [_kh(r["symbol"], r["signal_date"], phan_quyet, seq=i)
            for i, r in enumerate(qd, 1) if tu is None or r["signal_date"] >= tu]


def _bang(gia, ke_hoach_cua):
    mp = pytest.MonkeyPatch()
    try:
        cli = _nap_cli()
        vni = _khung_vni(gia)
        so, qd = _chay_that(_cfg(), gia, vni_df=vni)
        so.db.close()
        return _dung(gia, mp, them=PB3, ke_hoach=ke_hoach_cua(qd))
    finally:
        mp.undo()


def _hang(b, ma="PB-003"):
    return next(h for h in b["phuong_an"] if h["id"] == ma)


def test_bang_PB003_moi_tin_hieu_MUA_NGAY_thi_cung_lenh_va_thuoc_2_bang_khong_tren_cua_so_rieng(gia):
    cli, b, lenh, qd, pa = _bang(gia, _ke_hoach_tu)
    h = _hang(b)
    assert h["cua_so_rieng"] == min(r["signal_date"] for r in qd)
    assert h["khac_lenh"] == {"chi_duong_that": [], "chi_phuong_an": []}
    assert h["thuoc2"]["cong_don"] == pytest.approx(0.0, abs=1e-9)
    assert h["bao_toan"]["vi_pham"] == [] and cli.ma_thoat_bang(b) == cli.MA_BANG_NHAU
    assert h["b6"]["dat"] == {"MUA_NGAY": sum(h["lenh"].values())} and h["b6"]["khop_duoi_cat_lo"] >= 0


def test_bang_PB003_cua_so_rieng_bat_dau_o_tin_hieu_co_ke_hoach_dau_tien__truoc_do_khong_tinh(gia):
    tu = S.PHIEN[60]
    cli, b, lenh, qd, pa = _bang(gia, lambda qd: _ke_hoach_tu(qd, tu))
    h = _hang(b)
    that = b["that"]
    assert h["cua_so_rieng"] == tu
    assert h["phien_dung"] and min(h["phien_dung"]) >= tu and len(h["phien_dung"]) < len(that["phien_dung"])
    # mọi lệnh của PB-003 trong bảng có ngày tín hiệu từ `tu`; đường thật bị cắt cùng cửa sổ khi so (khac_lenh rỗng)
    assert h["khac_lenh"] == {"chi_duong_that": [], "chi_phuong_an": []}, \
        "hai tài khoản bắt đầu CÙNG vị thế mang sang nên chỉ khác ở luật; mọi tín hiệu MUA_NGAY thì không khác gì"
    assert h["thuoc2"]["n_phien"] == len(h["phien_dung"]) and h["thuoc2"]["cong_don"] == pytest.approx(0.0, abs=1e-9)
    assert h["b6"]["tu"] == tu and sd.THIEU_KE_HOACH not in h["b6"]["dat"], "tín hiệu trước `tu` không bị đếm là thiếu"
    # tổng lệnh đã nằm trong cửa sổ: ít hơn đường thật cả kỳ
    assert sum(h["lenh"].values()) < sum(that["lenh"].values())
    assert h["that_cua_so"]["lenh"] == h["lenh"], "đường thật của cửa sổ riêng cùng lệnh khi mọi tín hiệu MUA_NGAY"


def test_bang_PB003_tab_ke_hoach_RONG_thi_cua_so_rong_va_khong_so_nao(gia):
    cli, b, lenh, qd, pa = _bang(gia, lambda qd: [])
    h = _hang(b)
    assert h["cua_so_rieng"] == cli.NGAY_VO_CUC and h["phien_dung"] == []
    assert sum(h["lenh"].values()) == 0 and h["thuoc2"]["n_phien"] == 0 and h["b6"]["dat"] == {}
    assert h["ktc"]["thuoc1"]["dong"].startswith(sd.NHAN_MAU_QUA_NGAN) or "ngắn" in h["ktc"]["thuoc1"]["dong"]


def test_bang_PB003_khac_duong_that_khi_ke_hoach_bo_qua_mot_nua(gia):
    def kh(qd):
        return [_kh(r["symbol"], r["signal_date"], "BO_QUA" if i % 2 else "MUA_NGAY", seq=i)
                for i, r in enumerate(qd, 1)]
    cli, b, lenh, qd, pa = _bang(gia, kh)
    h = _hang(b)
    assert h["khac_lenh"]["chi_duong_that"], "BO_QUA phải làm PB-003 thiếu lệnh so với đường thật"
    assert h["b6"]["dat"].get("BO_QUA", 0) > 0 and h["b6"]["dat"].get("MUA_NGAY", 0) > 0
    assert h["bao_toan"]["vi_pham"] == []


def test_dung_bang_ke_hoach_None_voi_phuong_an_B6_thi_NO(gia):
    mp = pytest.MonkeyPatch()
    try:
        with pytest.raises(ValueError):
            _dung(gia, mp, them=PB3)
    finally:
        mp.undo()


def test_in_bang_in_cua_so_rieng_va_dem_ke_hoach(gia):
    cli, b, *_ = _bang(gia, _ke_hoach_tu)
    dong = []
    cli.in_bang(b, ghi=dong.append)
    van = "\n".join(dong)
    assert "CUA SO RIENG" in van and "ke hoach B6" in van and "lenh gioi han CHO_VUNG" in van
    assert "het han" in van
