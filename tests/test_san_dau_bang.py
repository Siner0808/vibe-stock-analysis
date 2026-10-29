"""Gác cho Lát 3a của C1 (BƯỚC 242): nguồn độ rộng, cấu hình từ sổ phương án, chuỗi lợi nhuận mỗi phiên, rổ,
GÁC BẢO TOÀN, hai thước ở dạng giá trị điểm, và lệnh `tools/san_dau.py bang` (`docs/thiet-ke-c1-san-dau.md`
mục 4, 8.1, 8.2, 10.1, 10.2, 11).

MÁY ĐO cũng bị nghi ngờ như gác (skill, Bước 3 điều 4): đường vốn sai thì mọi khoảng tin cậy phía sau đều sai
mà vẫn trông hợp lý. Nên có BỐN lớp:
  1. số viết tay (đóng góp từng phiên của MỘT lệnh, thước 1, thước 2, sụt giảm);
  2. gác bảo toàn chạy trên lệnh do BỘ MÁY THẬT sinh ra (kịch bản mười mã × 95 phiên của
     `tools/sinh_bang_vang_phien.py`), kể cả vị thế mang sang và cửa sổ cắt giữa lệnh;
  3. gác bảo toàn BỊ ĐỤC: ba cách làm sai đường vốn phải làm gác đỏ;
  4. một tài khoản trùng cấu hình với đường thật phải cho thước 2 bằng 0 (phương án không thể hơn chính nó).
"""
from __future__ import annotations

import ast
import re
import sqlite3
import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.append(str(GOC / "tools"))

import do_rong as dr  # noqa: E402
import duyet_repo  # noqa: E402
import paper_runner as pr  # noqa: E402
import paper_trading as pt  # noqa: E402
import phuong_an_bong as pab  # noqa: E402
import san_dau as sd  # noqa: E402
import sinh_bang_vang_phien as S  # noqa: E402
from test_san_dau import (_cfg, _chay_that, _khung_vni, _lenh, _nap_cli,  # noqa: E402
                          _NguonKichBan, _sach_cache_phan_tich)

assert _sach_cache_phan_tich  # fixture autouse nhập từ test_san_dau, giữ trong module này


@pytest.fixture(scope="module")
def gia():
    return S.dung_gia()


# ── 1. số viết tay ────────────────────────────────────────────────────────────────────────────
def _khung_tay(dong, hau_to="") -> tuple:
    ngay = [f"2026-10-{d:02d}{hau_to}" for d in range(1, len(dong) + 1)]
    kh = pd.DataFrame({"time": ngay, "open": dong, "high": dong, "low": dong, "close": dong, "volume": 1.0})
    return sd._chuan_hoa_gia({"AAA": kh})["AAA"], [d[:10] for d in ngay]


def _lenh_tay(**kw) -> dict:
    t = dict(symbol="AAA", signal_date="2026-10-01", entry_date="2026-10-02", entry_price=50500.0,
             exit_date="2026-10-05", exit_price=51800.0, exit_reason="STOP_LOSS", stop_loss=1.0,
             take_profit=1.0, size_pct=5.0, entry_score=65, status="CLOSED")
    t.update(kw)
    return t


CLOSE_TAY = [50000.0, 51000.0, 50500.0, 52500.0, 52000.0, 53000.0]   # ngày 01..06
#: w = 0,05; (đóng − đầu) / 50500 × 100 × w; phí 0,46 × w ở phiên ra. Số tính tay, xem lệnh ở BƯỚC 242.
DONG_GOP_TAY = {"2026-10-02": 0.04950495049504951, "2026-10-03": -0.04950495049504951,
                "2026-10-04": 0.19801980198019803, "2026-10-05": -0.0923069306930693}


@pytest.mark.parametrize("don_vi, nhan", [(1.0, "VND"), (1000.0, "nghin dong")])
def test_dong_gop_lenh_ra_dung_so_tinh_tay__ca_hai_don_vi_gia(don_vi, nhan):
    moc, _ = _khung_tay([c / don_vi for c in CLOSE_TAY])
    dg = sd.dong_gop_lenh(_lenh_tay(), moc, "2026-10-01", "2026-10-06")
    assert dg == pytest.approx(DONG_GOP_TAY, abs=1e-12), nhan
    # THU GỌN: tổng = w × (ra − vào) / vào − w × phí
    assert sum(dg.values()) == pytest.approx(0.05 * (51800.0 - 50500.0) / 50500.0 * 100.0 - 0.05 * 0.46)


def test_dong_gop_lenh_chi_tra_phien_trong_cua_so_va_phi_o_phien_RA():
    moc, _ = _khung_tay(CLOSE_TAY)
    dg = sd.dong_gop_lenh(_lenh_tay(), moc, "2026-10-03", "2026-10-04")
    assert list(dg) == ["2026-10-03", "2026-10-04"]
    # ra SAU cửa sổ: không trừ phí
    dg2 = sd.dong_gop_lenh(_lenh_tay(), moc, "2026-10-01", "2026-10-04")
    assert sum(dg2.values()) == pytest.approx(0.05 * (52500.0 - 50500.0) / 50500.0 * 100.0)
    # lệnh ra TRƯỚC cửa sổ: rỗng
    assert sd.dong_gop_lenh(_lenh_tay(), moc, "2026-10-06", "2026-10-06") == {}


def test_dong_gop_lenh_vao_va_ra_CUNG_phien_va_lenh_khong_co_dong_gop():
    moc, _ = _khung_tay(CLOSE_TAY)
    cung = _lenh_tay(entry_date="2026-10-03", exit_date="2026-10-03", entry_price=50600.0, exit_price=50400.0)
    dg = sd.dong_gop_lenh(cung, moc, "2026-10-01", "2026-10-06")
    assert dg == pytest.approx({"2026-10-03": 0.05 * (50400.0 - 50600.0) / 50600.0 * 100.0 - 0.05 * 0.46})
    for tt in ("PENDING", "HUY"):
        assert sd.dong_gop_lenh(_lenh_tay(status=tt, entry_date=None, entry_price=None), moc,
                                "2026-10-01", "2026-10-06") == {}
    # CLOSING: vẫn giữ, KHÔNG xét exit_date (đó là ngày TÍN HIỆU ra) và không trừ phí
    cl = sd.dong_gop_lenh(_lenh_tay(status="CLOSING", exit_price=None), moc, "2026-10-01", "2026-10-06")
    assert list(cl)[-1] == "2026-10-06" and cl["2026-10-06"] == pytest.approx(0.05 * 1000.0 / 50500.0 * 100.0)


def test_dong_gop_lenh_doc_ngay_ca_khi_cot_time_mang_hau_to_gio():
    moc, _ = _khung_tay(CLOSE_TAY, hau_to=" 07:00:00")
    assert sd.dong_gop_lenh(_lenh_tay(entry_date="2026-10-02 00:00:00", exit_date="2026-10-05 00:00:00"),
                            moc, "2026-10-01", "2026-10-06") == pytest.approx(DONG_GOP_TAY, abs=1e-12)


def test_chuoi_tai_khoan_cong_cac_lenh_va_dem_e_la_cam_ket_size_pct():
    kh = _khung_tay(CLOSE_TAY)[0]
    gia_tay = {"AAA": kh[0]}
    lenh = [_lenh_tay(), _lenh_tay(entry_date="2026-10-03", entry_price=50500.0, size_pct=10.0,
                                   exit_date=None, exit_price=None, status="OPEN")]
    phien = ["2026-10-01", "2026-10-02", "2026-10-03", "2026-10-04", "2026-10-05", "2026-10-06"]
    ch = sd.chuoi_tai_khoan(lenh, gia_tay, phien)
    assert ch.e == pytest.approx({"2026-10-01": 0.0, "2026-10-02": 0.05, "2026-10-03": 0.15, "2026-10-04": 0.15,
                                  "2026-10-05": 0.15, "2026-10-06": 0.10})
    mot = sd.dong_gop_lenh(lenh[1], kh, phien[0], phien[-1])
    assert ch.r["2026-10-03"] == pytest.approx(DONG_GOP_TAY["2026-10-03"] + mot["2026-10-03"])
    assert ch.r["2026-10-01"] == 0.0
    # lọc theo nhãn: chỉ lệnh thứ hai
    ch2 = sd.chuoi_tai_khoan(lenh, gia_tay, phien, loc=lambda t: t["status"] == "OPEN")
    assert ch2.e["2026-10-02"] == 0.0 and ch2.e["2026-10-03"] == pytest.approx(0.10)
    # lệnh của mã không có giá: bị bỏ khỏi chuỗi VÀ được ĐẾM
    ch3 = sd.chuoi_tai_khoan([_lenh_tay(symbol="ZZZ")], gia_tay, phien)
    assert ch3.thieu_gia == [("ZZZ", "2026-10-01")] and sum(ch3.e.values()) == 0.0


def test_thuoc_1_so_tay__x_va_cot_tho_va_phien_khong_giu():
    d = ["d1", "d2", "d3", "d4"]
    r = {"d1": 1.0, "d2": -0.5, "d3": 0.0, "d4": 0.2}
    e = {"d1": 0.1, "d2": 0.1, "d3": 0.0, "d4": 0.05}
    ro = {"d1": 0.5, "d2": -1.0, "d3": 0.3, "d4": 0.4}
    t = sd.thuoc_1(r, e, ro, d)
    # x = r − e×rổ = 0,95 · −0,40 · 0 · 0,18
    assert t["x_cong_don"] == pytest.approx(0.73)
    assert t["x_tb_giu"] == pytest.approx((0.95 - 0.40 + 0.18) / 3)       # chỉ ba phiên CÓ GIỮ
    assert (t["n_phien"], t["n_giu"], t["n_khong_giu"]) == (4, 3, 1)
    # thô = r − rổ = 0,5 · 0,5 · −0,3 · −0,2 trên MỌI phiên
    assert t["tho_cong_don"] == pytest.approx(0.5) and t["tho_tb"] == pytest.approx(0.125)
    # phiên không có rổ bị bỏ khỏi cả hai
    t2 = sd.thuoc_1(r, e, {k: v for k, v in ro.items() if k != "d1"}, d)
    assert t2["n_phien"] == 3 and t2["x_cong_don"] == pytest.approx(-0.22)
    # không phiên giữ nào: trung bình None, không chia cho 0
    assert sd.thuoc_1(r, {k: 0.0 for k in e}, ro, d)["x_tb_giu"] is None


def test_thuoc_2_so_tay_va_chi_tren_cua_so_chung():
    pa = {"d1": 1.0, "d2": 0.5, "d3": -0.5}
    that = {"d1": 0.4, "d2": 0.9, "d4": 7.0}
    t = sd.thuoc_2(pa, that, ["d1", "d2", "d3", "d4"])        # d3 thiếu ở đường thật, d4 thiếu ở phương án
    assert t["n_phien"] == 2 and t["cong_don"] == pytest.approx(0.2) and t["tb"] == pytest.approx(0.1)
    assert sd.thuoc_2(pa, that, ["d1"])["tb"] == pytest.approx(0.6)       # cửa sổ chung thu hẹp
    assert sd.thuoc_2(pa, that, [])["tb"] is None


def test_sut_giam_toi_da_va_dem_lenh():
    r = {"a": 1.0, "b": -0.5, "c": -0.7, "d": 2.0, "e": -0.1}
    assert sd.sut_giam_toi_da(r, list(r)) == pytest.approx(1.2)           # đỉnh 1,0 → đáy −0,2
    assert sd.sut_giam_toi_da({"a": -0.3, "b": -0.2}, ["a", "b"]) == pytest.approx(0.5)   # đỉnh khởi đầu 0
    assert sd.sut_giam_toi_da({}, []) == 0.0
    ds = [{"status": s} for s in ("CLOSED", "CLOSED", "OPEN", "CLOSING", "PENDING", "HUY")]
    assert sd.dem_lenh(ds) == {"dong": 2, "mo": 2, "cho": 1, "huy": 1}
    assert sd.dem_theo_nhan([{"signal_date": "2026-08-27"}, {"signal_date": "2026-09-01"},
                             {"signal_date": "2026-11-01"}], "2026-10-29") == {
        sd.NHAN_MO_PHONG: 1, sd.NHAN_DA_NHIN: 1, sd.NHAN_CHUA_NHIN: 1}


# ── 2. rổ ─────────────────────────────────────────────────────────────────────────────────────
def test_ro_bang_build_benchmark_cho_tung_cap_phien_lien_nhau(gia):
    phien = S.PHIEN[30:70]
    ro, thieu = sd.loi_nhuan_ro(gia, phien)
    assert thieu == [] and len(ro) == len(phien)
    for truoc, d in zip(S.PHIEN[29:69], phien):
        gia_tri = pr.build_benchmark([types.SimpleNamespace(status="CLOSED", entry_date=truoc, exit_date=d)],
                                     gia)[(truoc, d)]
        assert ro[d] == pytest.approx(gia_tri, abs=1e-9), d
    assert len(set(round(v, 6) for v in ro.values())) > 20, "rổ gần hằng số: phép so không canh gì"


def test_ro_chi_tinh_ma_du_nen_hai_phien_lien_va_phien_dau_chuoi_khong_dung_duoc():
    def kh(close, ngay):
        return pd.DataFrame({"time": ngay, "open": close, "high": close, "low": close, "close": close,
                             "volume": 1.0})
    ngay = ["2026-10-01", "2026-10-02", "2026-10-03"]
    gia_tay = {"A": kh([100.0, 110.0, 99.0], ngay),                              # +10%, −10%
               "B": kh([200.0, 200.0, 220.0], ngay),                             # 0%, +10%
               "C": kh([50.0, 60.0], ["2026-10-01", "2026-10-03"])}              # thiếu 10-02: không vào phiên 02, 03
    ro, thieu = sd.loi_nhuan_ro(gia_tay, ngay)
    assert thieu == ["2026-10-01"]                                              # không có phiên trước
    assert ro["2026-10-02"] == pytest.approx(5.0)                               # (10 + 0) / 2, không có C
    assert ro["2026-10-03"] == pytest.approx(0.0)                               # (−10 + 10) / 2; C thiếu nến 02
    assert sd.loi_nhuan_ro(gia_tay, ["2030-01-01"])[1] == ["2030-01-01"]
    # giá phiên trước bằng 0 (nến hỏng): mã ấy bị bỏ, KHÔNG chia cho 0 — cùng điều kiện `a > 0` của build_benchmark
    co_so_khong = dict(gia_tay, D=kh([0.0, 5.0, 6.0], ngay))
    ro2, _ = sd.loi_nhuan_ro(co_so_khong, ngay)
    assert ro2["2026-10-02"] == pytest.approx(5.0)
    assert ro2["2026-10-03"] == pytest.approx((-10.0 + 10.0 + 20.0) / 3)


def test_phien_cua_so_gom_ca_hai_dau_va_chi_phien_co_nen():
    def kh(ngay):
        return pd.DataFrame({"time": ngay, "open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0, "volume": 1.0})
    gia_tay = {"A": kh(["2026-10-01", "2026-10-02", "2026-10-05"]), "B": kh(["2026-10-02 07:00:00", "2026-10-06"])}
    assert sd.phien_cua_so(gia_tay, "2026-10-02", "2026-10-05") == ["2026-10-02", "2026-10-05"]
    assert sd.phien_cua_so(gia_tay, "2026-10-01", "2026-10-06") == ["2026-10-01", "2026-10-02", "2026-10-05", "2026-10-06"]
    assert sd.phien_cua_so(gia_tay, "2026-10-03", "2026-10-04") == []


# ── 3. gác bảo toàn ───────────────────────────────────────────────────────────────────────────
def _phat(gia):
    so, qd = _chay_that(_cfg(cong_vni_bat=False), gia)
    thuc = _lenh(so)
    so.db.close()
    return thuc, qd


def test_bao_toan_xanh_tren_lenh_do_BO_MAY_THAT_sinh_ra_ca_vi_the_mang_sang_va_cua_so_cat_giua_lenh(gia):
    cfg = _cfg(cong_vni_bat=False)
    thuc, qd = _phat(gia)
    for ten, bd, kt in (("toan ky", S.PHIEN[0], S.PHIEN[-1]), ("cat cuoi", S.PHIEN[0], S.PHIEN[60]),
                        ("bat dau giua", S.PHIEN[30], S.PHIEN[-1]), ("cua so hep", S.PHIEN[40], S.PHIEN[55])):
        mang = sd.vi_the_mang_sang(thuc, bd) if bd != S.PHIEN[0] else []
        tk = sd.phat_lai(cfg, qd, gia, _NguonKichBan(), ngay_bat_dau=bd, ngay_ket_thuc=kt, vi_the_mang_sang=mang)
        try:
            kq = sd.kiem_bao_toan(tk.lenh(), gia, bd, kt)
            if ten == "bat dau giua":
                assert tk.dem["mang_sang"] >= 1, "không có vị thế mang sang: gác không canh ca ấy"
        finally:
            tk.dong()
        assert kq["vi_pham"] == [], (ten, kq["vi_pham"][:3])
        assert kq["da_kiem"] >= 3, (ten, kq["da_kiem"])
        if ten == "toan ky":
            assert kq["dong_trong_cua_so"] >= 5, "ít lệnh đóng trọn cửa sổ: nhánh net_return_pct trống"


def _phat_thuoc_ky(gia):
    cfg = _cfg(cong_vni_bat=False)
    thuc, qd = _phat(gia)
    tk = sd.phat_lai(cfg, qd, gia, _NguonKichBan(), ngay_bat_dau=S.PHIEN[0])
    return tk, S.PHIEN[0], S.PHIEN[-1]


def test_bao_toan_BI_DUC__ba_cach_lam_sai_duong_von_deu_lam_gac_do(gia, monkeypatch):
    tk, bd, kt = _phat_thuoc_ky(gia)
    try:
        lenh = tk.lenh()
        goc = sd.dong_gop_lenh
        assert sd.kiem_bao_toan(lenh, gia, bd, kt)["vi_pham"] == []

        # (1) quên phí khứ hồi ở phiên ra — chỉ đường `net_return_pct` độc lập bắt được (cả hai phía đọc
        #     cùng ROUND_TRIP_COST_PCT khi nó bị đổi)
        import paper_metrics
        monkeypatch.setattr(paper_metrics, "ROUND_TRIP_COST_PCT", 0.0)
        kq = sd.kiem_bao_toan(lenh, gia, bd, kt)
        monkeypatch.undo()
        assert any(v["loai"] == "net_return_pct" for v in kq["vi_pham"]), "quên phí không bị net_return_pct bắt"

        # (2) công thức của đặc tả đọc TRẦN: lợi nhuận đơn mỗi phiên w × (đóng / đóng trước − 1) — tổng KHÔNG
        #     thu gọn về lợi nhuận đơn cả kỳ
        def theo_ti_le(lenh_, moc, b, k):
            out = goc(lenh_, moc, b, k)
            ngay, dong = sd._dong_cua_vnd(moc)
            w = float(lenh_["size_pct"]) / 100.0
            for i, d in enumerate(ngay):
                if d in out and d != sd.ngay10(lenh_["entry_date"]) and d != sd.ngay10(lenh_["exit_date"] or "") and i:
                    out[d] = w * (dong[i] / dong[i - 1] - 1.0) * 100.0
            return out
        monkeypatch.setattr(sd, "dong_gop_lenh", theo_ti_le)
        kq = sd.kiem_bao_toan(lenh, gia, bd, kt)
        monkeypatch.undo()
        assert kq["vi_pham"], "công thức tỉ lệ đơn mỗi phiên phải bị gác bảo toàn bắt"

        # (3) phiên khớp vào tính từ ĐÓNG CỬA HÔM TRƯỚC thay vì giá vào
        def sai_phien_vao(lenh_, moc, b, k):
            out = goc(lenh_, moc, b, k)
            vao = sd.ngay10(lenh_["entry_date"])
            if vao in out:
                out[vao] *= 1.5
            return out
        monkeypatch.setattr(sd, "dong_gop_lenh", sai_phien_vao)
        assert sd.kiem_bao_toan(lenh, gia, bd, kt)["vi_pham"]
        monkeypatch.undo()
        assert sd.kiem_bao_toan(lenh, gia, bd, kt)["vi_pham"] == [], "hoàn trả sau đục"
    finally:
        tk.dong()


def test_bao_toan_bat_lenh_thieu_nen_ngay_vao_va_thieu_gia(gia):
    tk, bd, kt = _phat_thuoc_ky(gia)
    try:
        lenh = tk.lenh()
        ma = lenh[0]["symbol"]
        # bỏ nến NGÀY VÀO của một lệnh: đoạn vào–đóng cửa mất → đường vốn thiếu, gác phải đỏ
        vao = sd.ngay10(lenh[0]["entry_date"])
        khuyet = dict(gia)
        khuyet[ma] = gia[ma][gia[ma]["time"] != vao]
        kq = sd.kiem_bao_toan([lenh[0]], khuyet, bd, kt)
        assert kq["vi_pham"], "thiếu nến ngày vào mà gác vẫn xanh"
        # mã không có chuỗi giá nào
        kq2 = sd.kiem_bao_toan([lenh[0]], {k: v for k, v in gia.items() if k != ma}, bd, kt)
        assert [v["loai"] for v in kq2["vi_pham"]] == ["thieu_gia"]
    finally:
        tk.dong()


# ── 4. nguồn độ rộng ──────────────────────────────────────────────────────────────────────────
def _gia_tong_hop(n_ma=25, den="2026-08-12", so_ngay=165, hau_to=""):
    rng = np.random.default_rng(7)
    ngay = pd.bdate_range(end=den, periods=so_ngay)
    chung = 0.012 * np.sin(0.3 * np.arange(len(ngay)))
    ra = {}
    for i in range(n_ma):
        close = 20000.0 * np.cumprod(1.0 + chung + rng.normal(0.0, 0.01, len(ngay)))
        ra[f"M{i:02d}"] = pd.DataFrame({"time": [d.strftime("%Y-%m-%d") + hau_to for d in ngay], "close": close})
    return ra


def test_nguon_do_rong_bang_ham_goc_o_ngay_con_trong_cache_va_THIEU_o_ngay_cache_chua_toi():
    gia_t = _gia_tong_hop()
    bang_co = sd.co_tu_gia(gia_t)
    nguon = sd.NguonDoRong(bang_co)
    ngay = list(pd.bdate_range(end="2026-08-12", periods=165).strftime("%Y-%m-%d"))
    trong = ngay[80:140]
    gt = [nguon.do_rong(d) for d in trong]
    assert all(g is not None for g in gt) and nguon.ngay_thieu_rong == set()
    assert gt == [dr.do_rong(bang_co, pd.Timestamp(d)) for d in trong], "phải là CHÍNH hàm gốc ở ngày còn trong cache"
    assert min(gt) < 0.5 < max(gt), "độ rộng tổng hợp không cắt 0,50: cổng không canh gì"
    # cache DỪNG ở 12/08: ngày sau đó hàm gốc LẶNG LẼ dùng độ rộng cũ, nguồn tiêm được phải báo THIẾU
    sau = "2026-08-17"
    assert dr.do_rong(bang_co, pd.Timestamp(sau)) is not None, "hàm gốc phải trả độ rộng cũ (bẫy của đặc tả)"
    assert nguon.thieu(sau) and nguon.do_rong(sau) is None and nguon.ngay_thieu_rong == {sau}
    assert nguon.phien_thieu([ngay[-1], sau, "2026-08-18"]) == [sau, "2026-08-18"]
    assert not nguon.thieu(ngay[-1]), "ngày CUỐI của cache vẫn có độ rộng"


def test_nguon_do_rong_thieu_khi_it_hon_N_TOI_THIEU_ma_va_khi_chua_du_50_dong():
    ft = _gia_tong_hop(n_ma=dr.N_TOI_THIEU - 1)
    nguon = sd.NguonDoRong(sd.co_tu_gia(ft))
    assert nguon.thieu("2026-08-10") and nguon.do_rong("2026-08-10") is None
    du = sd.NguonDoRong(sd.co_tu_gia(_gia_tong_hop(n_ma=dr.N_TOI_THIEU)))
    assert not du.thieu("2026-08-10")
    # 30 dòng đầu chưa đủ MA50: mọi mã chưa đủ dữ liệu → THIẾU (N(t) < 20), không phải "độ rộng 0"
    ngay_dau = pd.bdate_range(end="2026-08-12", periods=165)[10].strftime("%Y-%m-%d")
    assert du.thieu(ngay_dau) and du.do_rong(ngay_dau) is None


def test_nguon_do_rong_giong_BangDoRong_doc_tu_thu_muc_cache(tmp_path):
    """`BangDoRong` là cái mà đường thật dùng: cùng thư mục tệp, cùng giá trị — kể cả cột `time` mang hậu tố
    giờ và dòng trùng ngày."""
    gia_t = _gia_tong_hop(hau_to=" 07:00:00")
    for ma, df in gia_t.items():
        d = pd.concat([df, df.iloc[[60]]]).sample(frac=1.0, random_state=3)   # dòng trùng ngày, thứ tự xáo
        d.to_csv(tmp_path / f"{ma}.csv", index=False)
    pd.DataFrame({"time": ["2026-08-12"], "close": [1.0]}).to_csv(tmp_path / "VNINDEX.csv", index=False)
    that = dr.BangDoRong(tmp_path)
    nguon = sd.NguonDoRong(sd.co_tu_gia(dict(gia_t, VNINDEX=pd.DataFrame({"time": ["2026-08-12"], "close": [1.0]}))))
    assert sorted(that.bang_co) == sorted(nguon.bang_co) and "VNINDEX" not in nguon.bang_co
    ngay = list(pd.bdate_range(end="2026-08-12", periods=165).strftime("%Y-%m-%d"))
    for d in ngay[70:]:
        assert nguon.do_rong(d) == that.do_rong(d), d
    assert sd.NguonDoRong(that.bang_co).do_rong(ngay[100]) == that.do_rong(ngay[100])


def test_nguon_do_rong_vni_chi_khi_cau_hinh_con_cong_vni():
    nguon = sd.NguonDoRong(sd.co_tu_gia(_gia_tong_hop()))
    with pytest.raises(RuntimeError):
        nguon.vni_tren_ma50("2026-08-10")
    khung = pd.DataFrame({"time": ["2026-08-10"], "close": [1.0]})
    vni = sd.NguonVni(khung)
    assert sd.NguonDoRong(nguon.bang_co, vni=vni).vni_tren_ma50("2026-08-10") is True


def test_nguon_vni_thieu_khong_ghi_gi_va_nhat_quan_voi_vni_tren_ma50(gia):
    vni = _khung_vni(gia).iloc[:-30]
    nguon = sd.NguonVni(vni)
    cuoi = vni["time"].iloc[-1]
    assert not nguon.thieu(cuoi) and nguon.thieu("2999-01-01") and nguon.thieu("1999-01-01")
    assert nguon.ngay_thieu == set(), "thieu() chỉ ĐỌC, không ghi"
    assert sd.NguonVni(None).thieu("2026-10-01")


# ── 5. cấu hình từ sổ, và những gì bị từ chối ─────────────────────────────────────────────────
def test_phat_lai_chi_nhan_cong_do_rong_khi_nguon_tu_khai_co_do_rong(gia):
    cho = {"FPT": gia["FPT"]}
    cfg = _cfg(do_rong_nguong=0.5, cong_vni_bat=False)
    for nguon in (_NguonKichBan(), sd.NguonVni(None), None):
        with pytest.raises(NotImplementedError):
            sd.phat_lai(cfg, [], cho, nguon)
    tk = sd.phat_lai(cfg, [], cho, sd.NguonDoRong(sd.co_tu_gia(_gia_tong_hop())))
    tk.dong()
    # mọi cấu hình CHƯA có đầu vào vẫn bị từ chối, kể cả khi nguồn có độ rộng
    ok = sd.NguonDoRong(sd.co_tu_gia(_gia_tong_hop()))
    for kw, loi in ((dict(luat_vao="KE_HOACH_B6"), NotImplementedError),
                    (dict(loc_imom_phan_vi=0.2), ValueError), (dict(chot_sut_giam_nguong=0.15), ValueError)):
        with pytest.raises(loi):
            sd.phat_lai(_cfg(do_rong_nguong=0.5, cong_vni_bat=False, **kw), [], cho, ok)


def test_cau_hinh_tu_phuong_an_ghi_de_dung_cac_co_cua_so_that():
    import json
    so = json.loads((GOC / "docs" / "phuong-an-bong.json").read_text(encoding="utf-8"))["phuong_an"]
    co_so = _cfg()
    c1 = sd.cau_hinh_tu_phuong_an(co_so, so["PB-001"])
    c2 = sd.cau_hinh_tu_phuong_an(co_so, so["PB-002"])
    assert c1 == _cfg(nghi_sau_lo_ngay=7)
    assert c2 == _cfg(cong_vni_bat=False, do_rong_nguong=0.5), "PB-002 là MỘT cặp cờ: tắt VN-INDEX VÀ bật độ rộng"
    assert (c2.cong_vni_bat, c2.do_rong_nguong) == (False, 0.5)
    for xau in ({"bo_co": {"khong_co": 1}}, {"bo_co": {"loc_imom_phan_vi": 0.2}}, {"bo_co": {}},
                {"bo_co": {"do_rong_nguong": "nua"}}, {}):
        with pytest.raises(ValueError):
            sd.cau_hinh_tu_phuong_an(co_so, xau)


def test_bo_co_cua_so_that_la_tap_con_cua_truong_CauHinhVao_va_kieu_dung():
    """G8 (đặc tả mục 11): khoá `bo_co` ⊆ trường `CauHinhVao`, đúng kiểu."""
    import dataclasses
    import json
    truong = {f.name for f in dataclasses.fields(pt.CauHinhVao)}
    so = json.loads((GOC / "docs" / "phuong-an-bong.json").read_text(encoding="utf-8"))["phuong_an"]
    for ma, d in so.items():
        assert set(d["bo_co"]) <= truong, ma
        assert pab.vi_pham_bo_co(d["bo_co"]) == [], ma
    assert pab.kieu_co().keys() == truong
    assert pab.vi_pham_bo_co({"cong_vni_bat": 1}) and pab.vi_pham_bo_co({"nghi_sau_lo_ngay": True})
    assert pab.vi_pham_bo_co({"do_rong_nguong": 1}) == [] and pab.vi_pham_bo_co({"do_rong_nguong": 0.5}) == []


# ── 6. PB-002 phát lại = đường thật (Tầng A của cặp cờ mới) ────────────────────────────────────
class _NguonRongKichBan:
    """Độ rộng của kịch bản (CÙNG hàm đã thay vào `do_rong.do_rong_mac_dinh` của đường thật)."""
    co_do_rong = True

    def vni_tren_ma50(self, ngay):
        raise AssertionError("PB-002 tắt cổng VN-INDEX: không được hỏi")

    def do_rong(self, ngay):
        return _do_rong_kich_ban(ngay)


def _do_rong_kich_ban(ngay):
    n = str(ngay)[:10]
    return None if n in S._DO_RONG_THIEU else (0.30 if n in S._DO_RONG_THAP else 0.70)


def test_TANG_A_phuong_an_do_rong_phat_lai_ra_DUNG_cac_lenh_cua_duong_that(gia, monkeypatch):
    cfg = _cfg(cong_vni_bat=False, do_rong_nguong=0.5)
    monkeypatch.setattr(dr, "do_rong_mac_dinh", _do_rong_kich_ban)
    so, qd = _chay_that(cfg, gia)
    thuc = _lenh(so)
    so.db.close()
    chan = [r for r in qd if str(r["skip_reason"]).startswith(pt.LY_DO_DO_RONG)]
    assert chan and any(r["score"] >= 62 for r in chan), "cổng độ rộng không chặn tín hiệu đủ điểm nào"
    assert not [r for r in qd if str(r["skip_reason"]).startswith("VN-INDEX")], "cổng VN-INDEX phải tắt"
    tk = sd.phat_lai(cfg, qd, gia, _NguonRongKichBan(), ngay_bat_dau=S.PHIEN[0])
    try:
        assert sd.so_sanh_lenh(thuc, tk.lenh()) == []
        assert len(thuc) >= 5 and tk.dem["thieu_diem"] == 0
    finally:
        tk.dong()


def test_TANG_A_phuong_an_nghi_sau_lo_va_phuong_an_do_rong_khac_duong_that_o_dung_cho_ho_doi(gia):
    """Phương án KHÁC đường thật: nếu hai tài khoản ra cùng lệnh thì cờ không có tác dụng và gác trống."""
    so, qd = _chay_that(_cfg(), gia, vni_df=_khung_vni(gia))
    so.db.close()
    cfg_that = _cfg()
    vni = _khung_vni(gia)
    tk0 = sd.phat_lai(cfg_that, qd, gia, sd.NguonVni(vni), ngay_bat_dau=S.PHIEN[0])
    tk1 = sd.phat_lai(_cfg(nghi_sau_lo_ngay=7), qd, gia, sd.NguonVni(vni), ngay_bat_dau=S.PHIEN[0])
    try:
        assert sd.so_sanh_lenh(tk0.lenh(), tk1.lenh()), "nghỉ 7 ngày không đổi lệnh nào: kịch bản không canh luật nghỉ"
    finally:
        tk0.dong()
        tk1.dong()


# ── 7. bảng sân đấu: một hàng mỗi tài khoản ───────────────────────────────────────────────────
def _dung(gia, monkeypatch, *, thieu_cuoi=5, them=None):
    cli = _nap_cli()
    monkeypatch.setattr(sd, "NGAY_TIEN_VE_TRUOC", S.PHIEN[0])          # kịch bản nằm trước 28/08/2026
    vni = _khung_vni(gia)
    so, qd = _chay_that(_cfg(), gia, vni_df=vni)
    lenh = _lenh(so)
    so.db.close()
    bang_co = sd.co_tu_gia(_gia_tong_hop(den=S.PHIEN[-1 - thieu_cuoi]))
    khai = S.PHIEN[48]
    pa = {"PB-001": {"lop": "tham_do", "bo_co": {"nghi_sau_lo_ngay": 7}, "khai_ngay": khai, "commit": None,
                     "mo_ta": "x", "ly_do": "y"},
          "PB-002": {"lop": "tham_do", "bo_co": {"cong_vni_bat": False, "do_rong_nguong": 0.5},
                     "khai_ngay": khai, "commit": None, "mo_ta": "x", "ly_do": "y"}}
    pa.update(them or {})
    b = cli.dung_bang(lenh, qd, gia, vni, bang_co, pa, tu_ngay=S.PHIEN[0], cau_hinh=_cfg())
    return cli, b, lenh, qd, pa


@pytest.fixture(scope="module")
def bang_tong_hop(gia):
    mp = pytest.MonkeyPatch()
    try:
        yield _dung(gia, mp, them={"PB-009": {"lop": "tham_do", "bo_co": {"nghi_sau_lo_ngay": 0},
                                              "khai_ngay": S.PHIEN[48], "commit": None, "mo_ta": "x",
                                              "ly_do": "y"}})
    finally:
        mp.undo()


def test_bang_co_mot_hang_moi_tai_khoan_va_gac_bao_toan_xanh_o_moi_hang(bang_tong_hop):
    cli, b, *_ = bang_tong_hop
    assert [h["id"] for h in b["phuong_an"]] == ["PB-001", "PB-002", "PB-009"]
    assert b["phien"][0] == S.PHIEN[0] and b["phien"][-1] == S.PHIEN[-1] and len(b["phien"]) == S.SO_PHIEN
    assert b["that"]["ten"] and b["ro"]["ten"]
    for h in [b["that"], *b["phuong_an"]]:
        assert h["bao_toan"]["vi_pham"] == [], (h["ten"], h["bao_toan"]["vi_pham"][:2])
        assert h["bao_toan"]["da_kiem"] >= 3 and h["thieu_gia"] == []
    assert cli.ma_thoat_bang(b) == cli.MA_BANG_NHAU


def test_bang_phuong_an_TRUNG_cau_hinh_voi_duong_that_cho_thuoc_2_bang_khong(bang_tong_hop):
    """Quy tắc 1 làm máy: một phương án không thể hơn hay kém chính nó."""
    _, b, *_ = bang_tong_hop
    chinh = next(h for h in b["phuong_an"] if h["id"] == "PB-009")
    assert chinh["thuoc2"]["tb"] == pytest.approx(0.0, abs=1e-12) and chinh["thuoc2"]["cong_don"] == pytest.approx(0.0, abs=1e-12)
    assert chinh["cong_don"] == pytest.approx(b["that"]["cong_don"])
    assert chinh["lenh"] == b["that"]["lenh"]
    assert chinh["thuoc1"]["x_cong_don"] == pytest.approx(b["that"]["thuoc1"]["x_cong_don"])
    # hai khối nhãn KHÔNG cộng vào nhau nhưng cộng lại đúng bằng tổng
    k1, k2 = (chinh["khoi"][n] for n in (sd.NHAN_DA_NHIN, sd.NHAN_CHUA_NHIN))
    assert k1["n_lenh"] > 0 and k2["n_lenh"] > 0, "kịch bản phải có lệnh ở CẢ hai khối nhãn"
    assert k1["n_lenh"] + k2["n_lenh"] == sum(chinh["lenh"].values())
    assert k1["cong_don"] + k2["cong_don"] == pytest.approx(chinh["cong_don"])
    assert k1["thuoc2"]["cong_don"] + k2["thuoc2"]["cong_don"] == pytest.approx(0.0, abs=1e-9)


def test_bang_thuoc_2_la_phuong_an_TRU_duong_that__dung_dau_va_khoi_nhan_khop_nhan_cua_lenh(bang_tong_hop):
    _, b, *_ = bang_tong_hop
    that = b["that"]
    for h in b["phuong_an"]:
        ky_vong = sum(h["r"][d] - that["r"][d] for d in h["phien_dung"])
        assert h["thuoc2"]["cong_don"] == pytest.approx(ky_vong), h["id"]
        for nhan in (sd.NHAN_DA_NHIN, sd.NHAN_CHUA_NHIN):
            assert h["khoi"][nhan]["n_lenh"] == h["nhan"].get(nhan, 0), (h["id"], nhan)
        k1, k2 = (h["khoi"][n] for n in (sd.NHAN_DA_NHIN, sd.NHAN_CHUA_NHIN))
        assert k1["cong_don"] + k2["cong_don"] == pytest.approx(h["cong_don"]), h["id"]
        assert k1["thuoc2"]["cong_don"] + k2["thuoc2"]["cong_don"] == pytest.approx(h["thuoc2"]["cong_don"]), h["id"]
    pb1 = next(h for h in b["phuong_an"] if h["id"] == "PB-001")
    pb2 = next(h for h in b["phuong_an"] if h["id"] == "PB-002")
    assert that["chan"]["vni"][0] > 0 and that["chan"]["nghi_sau_lo"] == (0, 0) and that["chan"]["do_rong"] == (0, 0)
    assert pb1["chan"]["nghi_sau_lo"][0] > 0 and pb2["chan"]["do_rong"][0] > 0 and pb2["chan"]["vni"] == (0, 0)
    assert pb1["thuoc2"]["cong_don"] != 0.0, "nghỉ 7 ngày không đổi đường vốn: kịch bản không canh thước 2"


def test_alpha_tung_lenh_la_vs_benchmark_tren_ro_cua_chinh_ma_da_phat_lai(gia):
    import paper_metrics as pm
    so, qd = _chay_that(_cfg(cong_vni_bat=False, buy_threshold=40), gia)
    so.db.close()
    tk = sd.phat_lai(_cfg(cong_vni_bat=False, buy_threshold=40), qd, gia, None, ngay_bat_dau=S.PHIEN[0])
    try:
        a = sd.alpha_tung_lenh(tk, gia)
        dong = [t for t in tk.nhat_ky.all_trades() if t.status == "CLOSED"]
        assert a["n"] == len(dong) >= 10 and a["alpha"] is not None and a["bo_qua"] == 0
        ky_vong = sum(t.net_return_pct() - pr.build_benchmark([t], gia)[(t.entry_date[:10], t.exit_date[:10])]
                      for t in dong) / len(dong)
        assert a["alpha"] == pytest.approx(ky_vong)
        assert pm.vs_benchmark(dong, pr.build_benchmark(dong, gia))["alpha"] == pytest.approx(ky_vong)
    finally:
        tk.dong()
    # dưới 10 lệnh: không có alpha
    tk2 = sd.phat_lai(_cfg(cong_vni_bat=False), qd, gia, None, ngay_bat_dau=S.PHIEN[0], ngay_ket_thuc=S.PHIEN[40])
    try:
        assert sd.alpha_tung_lenh(tk2, gia)["alpha"] is None
    finally:
        tk2.dong()


def test_bang_phuong_an_do_rong_LOAI_dung_cac_phien_thieu_do_rong_va_thuoc_2_chi_tren_cua_so_chung(bang_tong_hop):
    _, b, *_ = bang_tong_hop
    pb2 = next(h for h in b["phuong_an"] if h["id"] == "PB-002")
    pb1 = next(h for h in b["phuong_an"] if h["id"] == "PB-001")
    cuoi = S.PHIEN[-5:]
    assert pb2["rong_loai"] == cuoi, pb2["rong_loai"]
    assert len(pb2["phien_dung"]) == len(b["phien"]) - 5 and not set(cuoi) & set(pb2["phien_dung"])
    assert pb2["thuoc2"]["n_phien"] <= len(b["phien"]) - 5
    assert pb2["rong_thieu"] is not None and pb2["vni_thieu"] is None, "PB-002 tắt cổng VN-INDEX"
    assert pb1["rong_thieu"] is None and pb1["vni_thieu"] is not None and pb1["rong_loai"] == []
    assert b["that"]["rong_thieu"] is None


def test_bang_in_mot_hang_moi_tai_khoan_voi_nhan_va_dong_KTC_den_o_BUOC_243(bang_tong_hop):
    cli, b, *_ = bang_tong_hop
    ra = []
    cli.in_bang(b, ghi=ra.append)
    van = "\n".join(ra)
    for tieu_de in ("[1] DUONG THAT PHAT LAI", "[2] PB-001", "[3] PB-002", "[4] PB-009", "[5] RO DEU"):
        assert tieu_de in van, tieu_de
    assert van.count("BUOC 243") >= 5, "MỖI hàng phải nói KTC và độ phủ đến ở BƯỚC 243"
    assert "THAM DO -- khong bao gio len ban" in van
    assert "DA_NHIN" in van and "CHUA_NHIN" in van and "KHONG cong" in van
    assert "95%" not in van and "KTC" in van
    assert "thuoc 1" in van and "thuoc 2" in van and "tho   (r - ro)" in van
    assert "do phu cong DO RONG" in van and "do phu cong VN-INDEX" in van and "bao toan" in van
    assert "alpha tung lenh" in van and "sut giam toi da" in van


def test_bang_loai_lenh_MO_PHONG_khoi_moi_thong_ke_nhung_van_dem_no(gia, monkeypatch):
    """Tín hiệu trước 28/08 là lượt mô phỏng lịch sử: không vào đường vốn nào, chỉ được ĐẾM trong nhãn."""
    cli = _nap_cli()
    vni = _khung_vni(gia)
    so, qd = _chay_that(_cfg(), gia, vni_df=vni)
    lenh = _lenh(so)
    so.db.close()
    bang_co = sd.co_tu_gia(_gia_tong_hop())
    monkeypatch.setattr(sd, "NGAY_TIEN_VE_TRUOC", S.PHIEN[0])
    h0 = cli.dung_bang(lenh, qd, gia, vni, bang_co, {}, tu_ngay=S.PHIEN[0], cau_hinh=_cfg())["that"]
    monkeypatch.setattr(sd, "NGAY_TIEN_VE_TRUOC", S.PHIEN[40])
    h = cli.dung_bang(lenh, qd, gia, vni, bang_co, {}, tu_ngay=S.PHIEN[0], cau_hinh=_cfg())["that"]
    assert h["nhan"].get(sd.NHAN_MO_PHONG, 0) > 0 and h0["nhan"].get(sd.NHAN_MO_PHONG, 0) == 0
    assert h["cong_don"] != pytest.approx(h0["cong_don"]) and h["thuoc1"]["n_giu"] < h0["thuoc1"]["n_giu"]


def test_bang_ma_thoat_la_1_khi_gac_bao_toan_do_va_vi_pham_duoc_IN(gia, monkeypatch):
    cli = _nap_cli()
    goc = sd.dong_gop_lenh
    monkeypatch.setattr(sd, "dong_gop_lenh", lambda *a, **k: {d: v * 1.01 for d, v in goc(*a, **k).items()})
    monkeypatch.setattr(sd, "NGAY_TIEN_VE_TRUOC", S.PHIEN[0])
    so, qd = _chay_that(_cfg(cong_vni_bat=False), gia)
    lenh = _lenh(so)
    so.db.close()
    pa = {"PB-001": {"lop": "tham_do", "bo_co": {"nghi_sau_lo_ngay": 7}, "khai_ngay": S.PHIEN[48],
                     "commit": None, "mo_ta": "x", "ly_do": "y"}}
    b = cli.dung_bang(lenh, qd, gia, None, {}, pa, tu_ngay=S.PHIEN[0], cau_hinh=_cfg(cong_vni_bat=False))
    ra = []
    cli.in_bang(b, ghi=ra.append)
    assert cli.ma_thoat_bang(b) == cli.MA_KHAC and any("VI PHAM bao toan" in d for d in ra)


def test_dung_cu_bang_chay_dau_cuoi_tren_so_tam_va_sai_so_phuong_an_thi_NO(gia, tmp_path, monkeypatch, capsys):
    import json
    cli = _nap_cli()
    monkeypatch.setattr(sd, "NGAY_TIEN_VE_TRUOC", S.PHIEN[0])
    vni = _khung_vni(gia)
    so, _ = _chay_that(_cfg(), gia, vni_df=vni)
    duong = tmp_path / "so_tam.db"
    dich = sqlite3.connect(duong)
    so.db.backup(dich)
    dich.close()
    so.db.close()
    pa_json = tmp_path / "pa.json"
    pa_json.write_text(json.dumps({"phuong_an": {
        "PB-001": {"lop": "tham_do", "bo_co": {"nghi_sau_lo_ngay": 7}, "khai_ngay": S.PHIEN[48], "commit": None,
                   "mo_ta": "x", "ly_do": "y"}}}), encoding="utf-8")
    monkeypatch.setattr(cli, "doc_gia_cache",
                        lambda ds: dict({m: gia[m] for m in ds if m in gia}, **({"VNINDEX": vni} if "VNINDEX" in ds else {})))
    monkeypatch.setattr(cli, "doc_bang_co_cache", lambda: sd.co_tu_gia(_gia_tong_hop(den=S.PHIEN[-1])))
    cuoi = S.PHIEN[80]
    ma = cli.main(["bang", "--so-tam", str(duong), "--tu-ngay", S.PHIEN[0], "--den-ngay", cuoi,
                   "--so-phuong-an", str(pa_json)])
    ra = capsys.readouterr().out
    assert ma == cli.MA_BANG_NHAU, ra
    assert "[1] DUONG THAT PHAT LAI" in ra and "[2] PB-001" in ra and "[3] RO DEU" in ra
    assert f"{S.PHIEN[0]} .. {cuoi}" in ra and "duong that phat lai vs so THAT" in ra
    # sổ phương án có một dòng không hợp lệ -> NỔ, không in bảng
    pa_json.write_text(json.dumps({"phuong_an": {"UV-001": {}}}), encoding="utf-8")
    with pytest.raises(ValueError):
        cli.main(["bang", "--so-tam", str(duong), "--tu-ngay", S.PHIEN[0], "--so-phuong-an", str(pa_json)])


def test_dung_cu_bang_mac_dinh_va_doc_so_phuong_an_that():
    cli = _nap_cli()
    a = cli.dung_parser().parse_args(["bang"])
    assert a.tu_ngay == sd.NGAY_MO_CONG and a.nguon_gia == "cache" and a.so_phuong_an is None and a.so_tam is None
    pa = cli.doc_so_phuong_an()
    assert set(pa) >= {"PB-001", "PB-002"} and cli.SO_PHUONG_AN == GOC / "docs" / "phuong-an-bong.json"


# ── 8. gác AST cho phần mới (G1–G5, mục 11) ───────────────────────────────────────────────────
def _nguoi_nhap(ten: str) -> set[str]:
    ra = set()
    for p in duyet_repo.duyet(GOC, "*.py"):
        rel = p.relative_to(GOC)
        if rel.parts[0] in {"tests", ".venv", ".git"} or rel.as_posix() == f"{ten}.py":
            continue
        for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if isinstance(n, ast.Import) and any(a.name.split(".")[0] == ten for a in n.names):
                ra.add(rel.as_posix())
            elif isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[0] == ten:
                ra.add(rel.as_posix())
    return ra


def test_G2_phuong_an_bong_chi_duoc_nhap_boi_san_dau_va_dung_cu_cua_no():
    nguoi = _nguoi_nhap("phuong_an_bong")
    assert nguoi == {"san_dau.py", "tools/san_dau.py"}, nguoi


def test_G3_phuong_an_bong_la_module_thuan__chi_stdlib_o_muc_module_khong_dong_ho_khong_git_khong_ghi():
    cay = ast.parse((GOC / "phuong_an_bong.py").read_text(encoding="utf-8"))
    muc_module = set()
    for n in cay.body:
        if isinstance(n, ast.Import):
            muc_module |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            muc_module.add((n.module or "").split(".")[0])
    assert muc_module <= {"__future__", "re", "typing"}, muc_module
    goi = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Call):
            goi.add(n.func.id if isinstance(n.func, ast.Name) else getattr(n.func, "attr", ""))
    assert not (goi & {"open", "run", "Popen", "check_output", "now", "today", "write_text", "read_text",
                       "urlopen", "dump", "load"}), goi
    assert "subprocess" not in {a.name for n in ast.walk(cay) if isinstance(n, ast.Import) for a in n.names}


def test_G4_san_dau_va_dung_cu_khong_goi_sheets_ghi_va_khong_nhap_pab_tu_duong_that():
    for ten in ("san_dau.py", "tools/san_dau.py"):
        goi = set()
        for n in ast.walk(ast.parse((GOC / ten).read_text(encoding="utf-8"))):
            if isinstance(n, ast.Call):
                goi.add(n.func.id if isinstance(n.func, ast.Name) else getattr(n.func, "attr", ""))
        assert not (goi & {"push", "write_all", "append_rows", "to_csv", "to_json"}), ten
    assert not re.search(r"^\s*(?:from|import)\s+(?:san_dau|phuong_an_bong)\b",
                         (GOC / "paper_trading.py").read_text(encoding="utf-8"), re.M)
