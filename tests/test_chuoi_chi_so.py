"""Test `chuoi_chi_so` — dữ liệu sạch cho VN30 · VNMidcap · VN100 (BƯỚC 307, Dow phần 2, Lát 1, mốc B7).

VÌ SAO FILE NÀY TỒN TẠI
───────────────────────
Ba chuỗi chỉ số đi qua ba nguồn công khai, và mỗi nguồn có một bẫy riêng (đặc tả `vibe_logs_dow2/DAC-TA-DOW2.md`
mục 2, đo ở `vibe_logs_dow2/BAO-CAO.md`): iBoard trả VNMidcap ở thang ×0,001, VPS trả ngày trùng và `close` = 0,
tên mã khác nhau theo nguồn, `volume` của chỉ số có hàng bằng 0. Một chuỗi làm sạch SAI không nổ: nó cho phần 1
(`cau_truc_gia`) một bảng giá lệch thang, và mọi lật của ĐO 39 đọc từ bảng đó. Nên mỗi quy tắc làm sạch có test riêng,
và test dùng BẢNG GIẢ ba nguồn qua một `http` giả (module không bao giờ tự gọi mạng).

BỨC TƯỜNG ĐO 39: file này chỉ dùng bảng TỔNG HỢP. Không test nào đọc dữ liệu thật của ba chỉ số, không test nào đếm
swing hay lật trên chúng. Dòng dữ kiện in ra chỉ gồm nguồn, số hàng, ngày đầu/cuối và tỷ số hai chuỗi.

Quy tắc dữ liệu BỔ SUNG SAU KHI KÝ ĐO 39 (chỉ đường dự phòng; quyết định của leader 28/11/2026): nguồn có tỷ lệ nến
`high == low == close` > 0,5% bị loại cho chuỗi ấy. Ngưỡng chọn SAU KHI thấy dữ liệu (VNDirect 0/2.311 hàng, iBoard
VNMidcap 94/1.983 = 4,74%); nó là ngưỡng LÀM SẠCH dữ liệu, không phải ngưỡng đo.
"""
from __future__ import annotations

import ast
import inspect
import pathlib
import re
import sys
from datetime import date, datetime

import pandas as pd
import pytest

GOC = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.append(str(GOC / "tools"))

import chuoi_chi_so as CC  # noqa: E402
import nguon_gia_cong_khai as ng  # noqa: E402

NGUON = GOC / "chuoi_chi_so.py"
N = 200
NGAY = list(pd.bdate_range("2017-08-24", periods=N))
DEN = NGAY[-1].date()
SAU_DONG_CUA = datetime(DEN.year, DEN.month, DEN.day, 16, 0)
TRONG_PHIEN = datetime(DEN.year, DEN.month, DEN.day, 10, 0)


def _ngu(giay):
    return None


def _ts(ngay):
    return int(pd.Timestamp(ngay).tz_localize("UTC").timestamp())


def _cot(ngay, dong, *, bien=3.0, vol=1000, mot_gia=(), vol0=()):
    """Mảng (t, o, h, l, c, v) thô như nguồn trả. `mot_gia`: chỉ số hàng có high = low = close."""
    cao = [c + bien for c in dong]
    thap = [c - bien for c in dong]
    for i in mot_gia:
        cao[i] = thap[i] = dong[i]
    v = [0 if i in vol0 else vol for i in range(len(dong))]
    return {"t": [_ts(d) for d in ngay], "o": list(dong), "h": cao, "l": thap, "c": list(dong), "v": v}


def _kho(**ghi_de):
    """Kho bảng giả: khoá (nguồn, mã trên nguồn). iBoard VNMIDCAP ở thang ×0,001 như thật."""
    vn30 = [900.0 + i for i in range(N)]
    vnmid = [1100.0 + i for i in range(N)]
    vn100 = [950.0 + i for i in range(N)]
    kho = {}
    for ns in ("vndirect", "iboard", "vps"):
        kho[(ns, "VN30")] = _cot(NGAY, vn30)
        kho[(ns, "VN100")] = _cot(NGAY, vn100)
    kho[("vndirect", "VNMID")] = _cot(NGAY, vnmid)
    kho[("vps", "VNMID")] = _cot(NGAY, vnmid)
    kho[("iboard", "VNMIDCAP")] = _cot(NGAY, [g / 1000 for g in vnmid], bien=0.003)
    kho.update(ghi_de)
    return kho


def _bo(kho, *khoa):
    return {k: v for k, v in kho.items() if k not in khoa}


def _http(kho, goi=None):
    """`http(url, accept)` giả: nhận ra nguồn qua host, mã qua `symbol=`; mã không có trong kho -> mảng rỗng."""
    def http(url, accept):
        ns = "vndirect" if "vndirect" in url else "iboard" if "iboard" in url else "vps"
        ma = re.search(r"symbol=([A-Za-z0-9]+)", url).group(1)
        if goi is not None:
            goi.append((ns, ma))
        cot = kho.get((ns, ma), {"t": [], "o": [], "h": [], "l": [], "c": [], "v": []})
        return {"code": "SUCCESS", "data": cot} if ns == "iboard" else {"s": "ok", **cot}
    return http


def _lay(kho, goi=None, bay_gio=SAU_DONG_CUA, den=DEN):
    return CC.lay_ba_chuoi(den, bay_gio, http=_http(kho, goi), ngu=_ngu, nghi=0.0)


# ── 0. ĐO 39: hằng số ghim ──────────────────────────────────────────────────────────────────────────────
def test_hang_so_ghim_theo_dac_ta():
    assert CC.TU_NGAY == date(2017, 8, 24)                       # ghim: nguồn sạch dài nhất chung (§2)
    assert CC.CHUOI == ("VN30", "VNMidcap", "VN100")
    assert CC.HE_SO_THANG == {("iboard", "VNMIDCAP"): 1000}
    assert CC.DAI_DO_LON == (0.2, 5.0)
    assert CC.NGUONG_NEN_MOT_GIA == 0.005
    assert CC.HE_SO_GIA == 1.0                                   # quy tắc 6: chỉ số không điều chỉnh quyền
    assert CC.CAC_COT == ("time", "open", "high", "low", "close")


def test_moi_nguon_cua_chuoi_chi_so_deu_co_ma_cho_ca_ba_chuoi():
    """Thêm một nguồn vào `CHUOI_CHI_SO` mà quên khai mã thì nổ ở ĐÂY, không ở lúc chạy."""
    for nguon in ng.CHUOI_CHI_SO:
        for chuoi in CC.CHUOI:
            assert (chuoi, nguon.ten) in CC.MA_THEO_NGUON, (chuoi, nguon.ten)
    assert [n.ten for n in ng.CHUOI_CHI_SO] == ["vndirect", "iboard", "vps"]


# ── 1. đường chính: VNDirect, ba chuỗi, không cột volume ──────────────────────────────────────────────────
def test_ba_chuoi_tu_VNDirect_khong_goi_nguon_du_phong_va_khong_co_cot_volume():
    goi = []
    kq = _lay(_kho(), goi)
    assert set(goi) == {("vndirect", "VN30"), ("vndirect", "VNMID"), ("vndirect", "VN100")}
    assert len(goi) == 3, "mỗi chuỗi một lượt kéo; không kéo nguồn dự phòng khi nguồn đầu dùng được"
    for ten in CC.CHUOI:
        r = kq[ten]
        assert r.nguon == "vndirect" and r.df is not None and r.da_thu == ()
        assert list(r.df.columns) == list(CC.CAC_COT)            # quy tắc 4: KHÔNG cột volume
        assert len(r.df) == N and r.df["time"].iloc[0] == NGAY[0] and r.df["time"].iloc[-1] == NGAY[-1]
        assert r.he_so_gia == 1.0 and not r.lich_su_ngan_hon and not r.bo_nen_cuoi_dang_do
    assert kq["VNMidcap"].ma == "VNMID" and kq["VN30"].ma == "VN30" and kq["VN100"].ma == "VN100"
    assert kq["VN30"].df["close"].iloc[0] == 900.0 and kq["VNMidcap"].df["close"].iloc[0] == 1100.0


# ── 2. quy tắc 3: tên mã khác nhau theo nguồn ────────────────────────────────────────────────────────────
def test_QUY_TAC_3_ten_ma_theo_nguon_iBoard_VNMIDCAP_con_VPS_VNMID():
    goi = []
    kho = _bo(_kho(), ("vndirect", "VNMID"))
    kq = _lay(kho, goi)
    assert ("iboard", "VNMIDCAP") in goi and ("iboard", "VNMID") not in goi
    assert kq["VNMidcap"].nguon == "iboard" and kq["VNMidcap"].ma == "VNMIDCAP"
    goi = []
    kq = _lay(_bo(_kho(), ("vndirect", "VNMID"), ("iboard", "VNMIDCAP")), goi)
    assert ("vps", "VNMID") in goi and ("vps", "VNMIDCAP") not in goi
    assert kq["VNMidcap"].nguon == "vps" and kq["VNMidcap"].ma == "VNMID"


# ── 3. quy tắc 1: thang iBoard ×0,001 và cổng độ lớn ─────────────────────────────────────────────────────
def test_QUY_TAC_1_iBoard_VNMIDCAP_nhan_1000_ra_dung_thang_VNDirect():
    kho = _bo(_kho(), ("vndirect", "VNMID"))
    r = _lay(kho)["VNMidcap"]
    assert r.nguon == "iboard" and r.da_thu[0][0] == "vndirect"
    goc = pd.Series([1100.0 + i for i in range(N)])
    for cot in ("open", "high", "low", "close"):
        assert r.df[cot].to_numpy() == pytest.approx((goc + {"open": 0, "high": 3, "low": -3, "close": 0}[cot]).to_numpy(),
                                                     rel=1e-9)
    # các chuỗi khác của iBoard KHÔNG bị nhân (hệ số khai theo (nguồn, mã), không theo nguồn)
    kho = _bo(_kho(), ("vndirect", "VN30"))
    assert _lay(kho)["VN30"].df["close"].iloc[0] == 900.0


def test_QUY_TAC_1_cong_do_lon_loai_nguon_khi_iBoard_sua_thang():
    """iBoard trả VNMIDCAP đã đúng thang 1.100: nhân 1000 ra 1.100.000, tỷ số với VN30 ≈ 1.222 > 5 ⇒ LOẠI, không nhân nhầm."""
    kho = _bo(_kho(), ("vndirect", "VNMID"))
    kho[("iboard", "VNMIDCAP")] = _cot(NGAY, [1100.0 + i for i in range(N)])
    r = _lay(kho)["VNMidcap"]
    assert r.nguon == "vps"                                        # rơi xuống VPS (sạch trong bảng giả)
    assert [t for t, _ in r.da_thu] == ["vndirect", "iboard"]
    assert "độ lớn" in dict(r.da_thu)["iboard"]
    r = _lay(_bo(kho, ("vps", "VNMID")))["VNMidcap"]
    assert r.df is None and r.nguon is None


def test_QUY_TAC_1_cong_do_lon_chay_voi_moi_nguon_khong_chi_iBoard():
    """Cổng là MỘT cổng cho mọi nguồn: VNDirect trả VNMID nhỏ 1000 lần cũng bị loại."""
    kho = _kho()
    kho[("vndirect", "VNMID")] = _cot(NGAY, [(1100.0 + i) / 1000 for i in range(N)], bien=0.003)
    r = _lay(kho)["VNMidcap"]
    assert r.nguon == "iboard" and "độ lớn" in dict(r.da_thu)["vndirect"]      # iBoard ×1000 vẫn đúng thang


@pytest.mark.parametrize("ty_so,duoc", [(0.2, True), (5.0, True), (1.0, True), (0.19, False), (5.01, False),
                                        (0.15, False), (6.0, False)])
def test_kiem_do_lon_bien_dai_0_2_toi_5_dong_ca_hai_dau(ty_so, duoc):
    """Dải [0,2 ; 5] đóng ở cả hai đầu (đặc tả §2 khoản 1): bắt `0.2`→`0.1`/`0`, `5.0`→`6`/`50`, và `<=`→`<`."""
    a = pd.Series([100.0 * ty_so] * 5, index=NGAY[:5])
    b = pd.Series([100.0] * 5, index=NGAY[:5])
    ly_do = CC.kiem_do_lon(a, b)
    assert (ly_do is None) == duoc, ly_do
    if not duoc:
        assert "độ lớn" in ly_do


def test_kiem_do_lon_dung_TRUNG_VI_khong_phai_trung_binh():
    a = pd.Series([100.0, 100.0, 100.0, 100.0, 100000.0], index=NGAY[:5])
    b = pd.Series([100.0] * 5, index=NGAY[:5])
    assert CC.kiem_do_lon(a, b) is None


def test_kiem_do_lon_khong_ngay_chung_thi_loai():
    ly_do = CC.kiem_do_lon(pd.Series([1.0], index=NGAY[:1]), pd.Series([1.0], index=NGAY[5:6]))
    assert ly_do is not None and "ngày chung" in ly_do


# ── 4. quy tắc 2: VPS ngày trùng và close = 0 ────────────────────────────────────────────────────────────
def _chi_con_vps(vps):
    kho = _bo(_kho(), ("vndirect", "VNMID"), ("iboard", "VNMIDCAP"))
    kho[("vps", "VNMID")] = vps
    return _lay(kho)["VNMidcap"]


def test_QUY_TAC_2_VPS_ngay_trung_thi_loai_ca_chuoi_khong_khu_trung():
    vps = _cot(NGAY, [1100.0 + i for i in range(N)])
    for k in ("t", "o", "h", "l", "c", "v"):
        vps[k] = vps[k][:50] + [vps[k][49]] + vps[k][50:]            # nến 49 xuất hiện HAI lần
    r = _chi_con_vps(vps)
    assert r.df is None and r.nguon is None
    assert [t for t, _ in r.da_thu] == ["vndirect", "iboard", "vps"]


def test_QUY_TAC_2_VPS_close_bang_0_thi_loai_ca_chuoi():
    vps = _cot(NGAY, [1100.0 + i for i in range(N)])
    vps["c"][70] = 0.0
    r = _chi_con_vps(vps)
    assert r.df is None and "close" in dict(r.da_thu)["vps"]


def test_QUY_TAC_2_VPS_sach_thi_dung_duoc():
    r = _chi_con_vps(_cot(NGAY, [1100.0 + i for i in range(N)]))
    assert r.nguon == "vps" and len(r.df) == N


# ── 5. quy tắc 4: không cột volume, kể cả khi nguồn trả volume = 0 ────────────────────────────────────────
def test_QUY_TAC_4_nguon_tra_volume_0_van_khong_con_cot_volume():
    kho = _bo(_kho(), ("vndirect", "VNMID"))
    kho[("iboard", "VNMIDCAP")] = _cot(NGAY, [(1100.0 + i) / 1000 for i in range(N)], bien=0.003, vol0=range(0, 21))
    r = _lay(kho)["VNMidcap"]
    assert r.nguon == "iboard" and "volume" not in r.df.columns and len(r.df) == N
    kho = _kho()
    kho[("vndirect", "VN30")] = _cot(NGAY, [900.0 + i for i in range(N)], vol0=range(0, 21))
    assert "volume" not in _lay(kho)["VN30"].df.columns


# ── 6. nguồn thiếu: nói đủ lý do, không suy từ chuỗi khác ────────────────────────────────────────────────
def test_het_nguon_thi_khong_doc_duoc_va_thong_bao_goi_ten_tung_nguon_va_ly_do():
    kho = _bo(_kho(), ("vndirect", "VNMID"), ("iboard", "VNMIDCAP"), ("vps", "VNMID"))
    kq = _lay(kho)
    r = kq["VNMidcap"]
    assert r.df is None and r.nguon is None and r.ma is None
    msg = r.thong_bao()
    assert msg.startswith("Không đọc được: VNMidcap — đã thử VNDirect (")
    assert "iBoard (" in msg and "VPS (" in msg and "0 phiên" in msg
    assert kq["VN30"].df is not None and kq["VN100"].df is not None      # chuỗi khác không bị kéo theo
    assert kq["VN30"].thong_bao() == ""


def test_khong_doc_duoc_VN30_thi_hai_chuoi_kia_cung_khong_doc_duoc_vi_khong_co_gi_de_kiem_thang():
    kho = _bo(_kho(), ("vndirect", "VN30"), ("iboard", "VN30"), ("vps", "VN30"))
    kq = _lay(kho)
    assert kq["VN30"].df is None
    for ten in ("VNMidcap", "VN100"):
        assert kq[ten].df is None
        assert kq[ten].thong_bao() == f"Không đọc được: {ten} — không đọc được VN30, nên không kiểm được độ lớn"


# ── 7. quy tắc bổ sung (đường dự phòng): nến một giá high = low = close ──────────────────────────────────
def _iboard_mot_gia(so_nen, *, bien_so_nen=N):
    mot = list(range(10, 10 + so_nen))
    return _cot(NGAY[:bien_so_nen], [(1100.0 + i) / 1000 for i in range(bien_so_nen)], bien=0.003, mot_gia=mot)


def _iboard_con_lai(so_nen):
    kho = _bo(_kho(), ("vndirect", "VNMID"), ("vps", "VNMID"))
    kho[("iboard", "VNMIDCAP")] = _iboard_mot_gia(so_nen)
    return _lay(kho)["VNMidcap"]


def test_ty_le_nen_mot_gia_dem_dung_high_bang_low_bang_close():
    df = pd.DataFrame({"high": [5.0, 5.0, 6.0, 7.0, 8.0], "low": [5.0, 4.0, 6.0, 7.0, 6.0],
                       "close": [5.0, 5.0, 6.0, 6.0, 6.0]})
    # hàng 0: h=l=c ✓; hàng 1: h=c, l≠ ✗; hàng 2: ✓; hàng 3: h=l, c khác ✗; hàng 4: l=c, h khác ✗
    assert CC.ty_le_nen_mot_gia(df) == 0.4
    assert CC.ty_le_nen_mot_gia(df.iloc[0:0]) == 0.0


def test_NGUONG_nen_mot_gia_bien_dung_0_5_phan_tram_chi_loai_khi_VUOT():
    """200 hàng: 1 nến một giá = 0,500% ĐÚNG ngưỡng ⇒ giữ; 2 nến = 1,0% ⇒ loại. Bắt `>`→`>=` và bỏ cổng."""
    assert CC.NGUONG_NEN_MOT_GIA == 1 / N
    giu = _iboard_con_lai(1)
    assert giu.nguon == "iboard" and len(giu.df) == N
    bo = _iboard_con_lai(2)
    assert bo.df is None and bo.nguon is None
    assert "high = low = close" in dict(bo.da_thu)["iboard"]


def test_THONG_BAO_goi_ten_ly_do_cua_iBoard_VNMidcap_nen_mot_gia():
    """Ô "Không đọc được" phải nói LÝ DO của iBoard VNMidcap: tỷ lệ nến một giá và ngưỡng."""
    bo = _iboard_con_lai(10)                                               # 10/200 = 5,00%
    msg = bo.thong_bao()
    assert msg.startswith("Không đọc được: VNMidcap — đã thử VNDirect (")
    assert "iBoard (5,00% nến có high = low = close, vượt ngưỡng 0,50%" in msg


def test_nguong_nen_mot_gia_khong_loai_nguon_sach_vndirect():
    kq = _lay(_kho())
    assert all(kq[t].nguon == "vndirect" for t in CC.CHUOI)


# ── 8. cửa sổ, lịch sử ngắn, nến cuối chưa đóng ──────────────────────────────────────────────────────────
def test_cua_so_bat_dau_tu_TU_NGAY_nen_truoc_do_bi_cat():
    ngay = list(pd.bdate_range("2017-06-01", periods=N + 60))
    kho = _kho()
    for ns in ("vndirect",):
        kho[(ns, "VN30")] = _cot(ngay, [900.0 + i for i in range(len(ngay))])
    r = _lay(kho, bay_gio=datetime(2019, 1, 1), den=ngay[-1].date())["VN30"]
    assert r.df["time"].iloc[0] >= pd.Timestamp(CC.TU_NGAY) and r.df["time"].iloc[0] < pd.Timestamp("2017-09-01")
    assert (r.df["time"] >= pd.Timestamp(CC.TU_NGAY)).all()


def test_lich_su_ngan_hon_duoc_gan_nhan_khi_nguon_bat_dau_muon():
    muon = list(pd.bdate_range("2018-12-11", periods=N))
    kho = _bo(_kho(), ("vndirect", "VNMID"))
    kho[("iboard", "VNMIDCAP")] = _cot(muon, [(1100.0 + i) / 1000 for i in range(N)], bien=0.003)
    kho[("vndirect", "VN30")] = _cot(muon, [900.0 + i for i in range(N)])
    kq = _lay(kho, bay_gio=datetime(2020, 1, 1), den=muon[-1].date())
    assert kq["VNMidcap"].lich_su_ngan_hon is True
    assert kq["VN30"].lich_su_ngan_hon is True
    assert _lay(_kho())["VN30"].lich_su_ngan_hon is False


def test_nen_cuoi_dang_do_bi_bo_khi_chua_qua_gio_dong_cua_va_giu_khi_da_dong():
    kq = _lay(_kho(), bay_gio=TRONG_PHIEN)
    for ten in CC.CHUOI:
        r = kq[ten]
        assert r.bo_nen_cuoi_dang_do is True and len(r.df) == N - 1 and r.df["time"].iloc[-1] == NGAY[-2]
    kq = _lay(_kho(), bay_gio=SAU_DONG_CUA)
    for ten in CC.CHUOI:
        assert kq[ten].bo_nen_cuoi_dang_do is False and len(kq[ten].df) == N
    # hôm sau: nến của ngày hôm trước luôn đã đóng
    kq = _lay(_kho(), bay_gio=datetime(DEN.year, DEN.month, DEN.day, 9, 0) + pd.Timedelta(days=1))
    assert len(kq["VN30"].df) == N


# ── 9. căn theo GIAO các ngày, ngày cuối lệch ────────────────────────────────────────────────────────────
def _hai_chuoi_lech():
    """VN30 thiếu ngày 100, VNMidcap thiếu ngày 150; VN30 còn hai phiên cuối mà VNMidcap chưa có."""
    vn30 = [i for i in range(N) if i != 100]
    vnmid = [i for i in range(N - 2) if i != 150]
    kho = _kho()
    kho[("vndirect", "VN30")] = _cot([NGAY[i] for i in vn30], [900.0 + i for i in vn30])
    kho[("vndirect", "VNMID")] = _cot([NGAY[i] for i in vnmid], [1100.0 + i for i in vnmid])
    return _lay(kho), vn30, vnmid


def test_can_theo_GIAO_cac_ngay_khong_phai_HOP():
    kq, vn30, vnmid = _hai_chuoi_lech()
    cap = CC.can_theo_giao(kq["VN30"], kq["VNMidcap"])
    chung = sorted(set(vn30) & set(vnmid))
    assert len(cap.df_a) == len(cap.df_b) == len(chung) == cap.so_hang
    assert list(cap.df_a["time"]) == list(cap.df_b["time"]) == [NGAY[i] for i in chung]
    assert 100 not in [NGAY.index(t) for t in cap.df_a["time"]] and 150 not in [NGAY.index(t) for t in cap.df_b["time"]]
    assert cap.df_a["close"].iloc[0] == 900.0 and cap.df_b["close"].iloc[0] == 1100.0
    assert (cap.chuoi_a, cap.chuoi_b) == ("VN30", "VNMidcap")


def test_ngay_cuoi_lech_doc_toi_ngay_chung_muon_nhat_va_ghi_so_phien_chua_dung():
    kq, vn30, vnmid = _hai_chuoi_lech()
    cap = CC.can_theo_giao(kq["VN30"], kq["VNMidcap"])
    assert cap.ngay_cuoi_chung == NGAY[N - 3].date()
    assert cap.thua == {"VN30": 2, "VNMidcap": 0}
    assert cap.ghi_chu == "VN30 có thêm 2 phiên chưa dùng"
    nguoc = CC.can_theo_giao(kq["VNMidcap"], kq["VN30"])
    assert nguoc.thua == {"VNMidcap": 0, "VN30": 2} and nguoc.ghi_chu == cap.ghi_chu


def test_ngay_cuoi_khop_thi_khong_ghi_chu():
    kq = _lay(_kho())
    cap = CC.can_theo_giao(kq["VN30"], kq["VNMidcap"])
    assert cap.thua == {"VN30": 0, "VNMidcap": 0} and cap.ghi_chu == "" and cap.so_hang == N


def test_can_theo_giao_tu_choi_chuoi_khong_doc_duoc_va_khong_co_ngay_chung():
    kq = _lay(_bo(_kho(), ("vndirect", "VNMID"), ("iboard", "VNMIDCAP"), ("vps", "VNMID")))
    with pytest.raises(ValueError, match="không đọc được"):
        CC.can_theo_giao(kq["VN30"], kq["VNMidcap"])
    a, b = _lay(_kho())["VN30"], _lay(_kho())["VN100"]
    b2 = CC.KetQuaChuoi(**{**b.__dict__, "df": b.df.assign(time=b.df["time"] + pd.Timedelta(days=1000))})
    with pytest.raises(ValueError, match="ngày chung"):
        CC.can_theo_giao(a, b2)


# ── 10. dòng dữ kiện (Xong khi): chỉ dữ kiện, KHÔNG trạng thái ───────────────────────────────────────────
def test_dong_du_kien_in_nguon_so_hang_ngay_dau_cuoi_va_ty_so_hai_chuoi():
    dong = CC.dong_du_kien(_lay(_kho()))
    van = "\n".join(dong)
    for ten, ma in (("VN30", "VN30"), ("VNMidcap", "VNMID"), ("VN100", "VN100")):
        d = next(x for x in dong if x.startswith(ten + ":"))
        assert "vndirect" in d and ma in d and "200 hàng" in d and "2017-08-24" in d and NGAY[-1].strftime("%Y-%m-%d") in d
    # trung vị (1100+i)/(900+i) trên 200 ngày chung = (1199/999 + 1200/1000)/2 = 1,2001
    assert "VNMidcap/VN30: trung vị close 1,2001 trên 200 ngày chung" in dong
    assert "VN100/VN30: trung vị close 1,0500 trên 200 ngày chung" in dong      # (1049/999 + 1050/1000)/2 = 1,050025
    for tu in ("lật", "swing", "đảo chiều", "xác nhận", "thủy triều", "đỉnh", "đáy", "xu hướng", "CHoCH", "BOS"):
        assert tu not in van, tu


def test_dong_du_kien_noi_chuoi_khong_doc_duoc_bang_thong_bao_cua_no():
    kq = _lay(_bo(_kho(), ("vndirect", "VNMID"), ("iboard", "VNMIDCAP"), ("vps", "VNMID")))
    dong = CC.dong_du_kien(kq)
    assert any(d.startswith("Không đọc được: VNMidcap — đã thử VNDirect (") for d in dong)
    assert not any(d.startswith("VNMidcap/") for d in dong)


# ── 11. gác cấu trúc: thuần, `http` truyền vào, không đường tới đếm lật ──────────────────────────────────
def _nhap_va_goi(duong):
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


def test_chi_nhap_thu_trung_tinh_va_khong_nhap_duong_do_swing_hay_cham_diem():
    """BỨC TƯỜNG ĐO 39: mô-đun dữ liệu KHÔNG nhập `cau_truc_gia` (không có đường tới đếm swing/lật) và không nhập đường
    chấm điểm/sổ lệnh."""
    nhap, goi = _nhap_va_goi(NGUON)
    assert nhap <= {"__future__", "dataclasses", "datetime", "pandas", "numpy", "nguon_gia_cong_khai",
                    "data_quality"}, nhap
    for cam in ("cau_truc_gia", "pha_wyckoff", "muc_fibonacci", "paper_trading", "paper_runner", "master_agent",
                "run_daily", "sheets_store", "walkforward", "backtest"):
        assert cam not in nhap, cam
    assert not ({"now", "today", "now_vn", "today_vn", "utcnow", "sleep", "monotonic", "read_csv", "get", "request",
                 "urlopen", "open", "to_csv", "to_json", "write_text", "read_text", "doc_cau_truc"} & goi), goi


def test_http_phai_duoc_truyen_vao_khong_co_gia_tri_mac_dinh_mang():
    for ham in (CC.lay_chuoi, CC.lay_ba_chuoi):
        p = inspect.signature(ham).parameters["http"]
        assert p.default is inspect.Parameter.empty and p.kind is inspect.Parameter.KEYWORD_ONLY, ham.__name__
    with pytest.raises(TypeError):
        CC.lay_ba_chuoi(DEN, SAU_DONG_CUA)


def test_bang_ra_di_qua_phan_1_o_che_do_chi_so_khong_can_cot_volume():
    """Hợp đồng với `cau_truc_gia` (CHỈ trên bảng tổng hợp): bảng ra có `time/high/low/close` và không `volume`."""
    import cau_truc_gia as C
    df = _lay(_kho())["VNMidcap"].df
    nens = C.chuan_bi_nen(df, "HOSE", la_chi_so=True)
    assert len(nens) == N and all(n.khoa_bien is None and not n.khong_giao_dich for n in nens)
