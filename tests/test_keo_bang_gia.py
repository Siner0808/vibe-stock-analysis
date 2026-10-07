"""Gác BỘ KÉO bảng giá một lượt — BƯỚC 162 (`keo_bang_gia.py`, `tools/keo_bang_gia.py`).

Bộ kéo ra đúng định dạng `cham_xac_nhan.dinh_dang_bang_gia`. Mọi dữ liệu ở đây là GIẢ và
hàm kéo là HÀM GIẢ truyền vào tham số `lay` — không có mạng, không `vnstock`, không đọc
dữ liệu thật. Chạy thật là việc trên MÁY người dùng.

Bốn điều gác chính (mỗi điều chặn một cách bảng giá tự khen mình):
1. `SYNTHETIC` / `FAILED` KHÔNG BAO GIỜ vào bảng — kể cả khi chúng mang một DataFrame đầy đủ
   dòng (đúng như đường lui của `VNStockCollectorAgent.collect`).
2. MỘT `keo_luc` cho cả bảng, `nguon` mỗi mã; mã kéo hỏng thì BÁO TÊN, không điền, và không
   có văn bản bảng nào ra khi còn một mã hỏng.
3. Kéo sau khi nến cuối đã đóng (`data_quality.nen_cuoi_dang_do`).
4. Giãn nhịp gọi (hạn mức 60/phút ở hạng free): nghỉ GIỮA các lời gọi.
"""
import ast
import datetime
import importlib.util
import json
import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(GOC / "tests"))

import cham_bong as cb  # noqa: E402
import cham_xac_nhan as cx  # noqa: E402
import data_quality as dq  # noqa: E402
import keo_bang_gia as kg  # noqa: E402
from test_cham_xac_nhan import KEO, _so_uv, _spec, dung  # noqa: E402

VN = dq.VN_TZ


def _bang(W=30, M=6):
    """(ngày × mã, lịch, mã) — bảng giá giả đã qua `cham_xac_nhan` một lần."""
    _, bg, cal, ma = dung(W=W, M=M)
    return bg["gia"], cal, ma


def _gio(ngay, gio="16:00"):
    h, m = map(int, gio.split(":"))
    d = datetime.date.fromisoformat(ngay)
    return datetime.datetime(d.year, d.month, d.day, h, m, tzinfo=VN)


def _df(s: pd.Series, thoi="chuoi"):
    t = list(s.index) if thoi == "chuoi" else list(pd.to_datetime(s.index))
    return pd.DataFrame({"time": t, "open": s.values, "high": s.values, "low": s.values,
                         "close": s.values, "volume": 1000})


class Gia:
    """Hàm kéo GIẢ + nhật ký: ghi lại từng lời gọi, từng lần nghỉ, mỗi lần hỏi đồng hồ."""

    def __init__(self, gia, nguon="vci", loi=None, sua=None, thoi="chuoi"):
        self.gia, self.nguon, self.loi, self.sua, self.thoi = gia, nguon, loi or {}, sua or {}, thoi
        self.su_kien = []

    def lay(self, ma, tu, den):
        self.su_kien.append(("lay", ma, tu, den))
        if ma in self.loi:
            raise self.loi[ma]
        if ma in self.sua:
            return self.sua[ma](self.gia[ma].dropna())
        nguon = self.nguon[ma] if isinstance(self.nguon, dict) else self.nguon
        return {"status": "OK", "df": _df(self.gia[ma].dropna(), self.thoi), "source": nguon,
                "note": "gia"}

    def ngu(self, giay):
        self.su_kien.append(("ngu", giay))


def _keo(gia, cal, ma, g=None, gio=None, nghi=0.0, **kw):
    g = g or Gia(gia)
    gio = gio or _gio(cal[-1])
    kq = kg.keo(ma, cal[0], cal[-1], lay=g.lay, nghi_giay=nghi, bay_gio=lambda: gio, ngu=g.ngu, **kw)
    return kq, g


# ── 1. đúng định dạng, đi qua máy chấm ───────────────────────────────────

def test_KEO_ra_DUNG_dinh_dang_va_vong_di_vong_ve_giu_nguyen_tung_o():
    gia, cal, ma = _bang()
    nguon = {m: ("kbs" if i % 2 else "vci") for i, m in enumerate(ma)}
    kq, _ = _keo(gia, cal, ma, g=Gia(gia, nguon=nguon))
    assert kq["hong"] == {} and kq["cuoi"] == cal[-1]
    assert kq["van_ban"] == cx.dinh_dang_bang_gia(gia, kq["keo_luc"], nguon)
    bg = cx.phan_tich_bang_gia(kq["van_ban"])
    pd.testing.assert_frame_equal(bg["gia"], gia)
    assert bg["nguon"] == nguon and bg["keo_luc"] == kq["keo_luc"]
    dong = kq["van_ban"].splitlines()
    assert dong[0] == "symbol,date,close,nguon,keo_luc"
    assert {d.split(",")[4] for d in dong[1:]} == {kq["keo_luc"]}      # MỘT keo_luc
    assert {(d.split(",")[0], d.split(",")[3]) for d in dong[1:]} == set(nguon.items())


def test_KEO_nhan_time_la_chuoi_hoac_Timestamp_va_moc_gio_trong_cot_time():
    gia, cal, ma = _bang(W=20, M=3)
    for thoi in ("chuoi", "timestamp"):
        kq, _ = _keo(gia, cal, ma, g=Gia(gia, thoi=thoi))
        pd.testing.assert_frame_equal(cx.phan_tich_bang_gia(kq["van_ban"])["gia"], gia)

    def co_gio(s):
        d = _df(s)
        d["time"] = [t + " 00:00:00" for t in d["time"]]
        return {"status": "OK", "df": d, "source": "vci"}
    kq, _ = _keo(gia, cal, ma, g=Gia(gia, sua={m: co_gio for m in ma}))
    pd.testing.assert_frame_equal(cx.phan_tich_bang_gia(kq["van_ban"])["gia"], gia)


def test_KEO_thu_tu_cot_theo_danh_sach_dau_vao_va_ma_viet_thuong_trung_lap_duoc_gop():
    gia, cal, ma = _bang(W=20, M=4)
    kq, g = _keo(gia, cal, [ma[2].lower(), ma[0], ma[2], ma[1], ma[3]])
    assert list(kq["gia"].columns) == [ma[2], ma[0], ma[1], ma[3]]
    assert [e[1] for e in g.su_kien if e[0] == "lay"] == [ma[2], ma[0], ma[1], ma[3]]   # mỗi mã MỘT lời gọi


def test_KEO_noi_voi_may_cham_cham_chay_duoc_va_cho_CUNG_ket_qua_voi_bang_goc(monkeypatch):
    """Tích hợp: văn bản của bộ kéo vào `cham_xac_nhan.cham` ra đúng thứ bảng gốc cho."""
    monkeypatch.setattr(cb, "MOC_DOC", 70)
    rows, bg, cal, ma = dung(W=70, M=45, gamma=0.012)
    g = Gia(bg["gia"])
    kq = kg.keo(ma, cal[0], bg["gia"].index[-1], lay=g.lay, nghi_giay=0.0, ngu=g.ngu,
                bay_gio=lambda: _gio("2027-03-01"))
    bg2 = cx.phan_tich_bang_gia(kq["van_ban"])
    uv = _so_uv(cal[0], _spec(volume_score=1.0))
    a = cx.cham(rows, uv, bg, so=100)["chi_tiet"]["UV-T"]
    b = cx.cham(rows, uv, bg2, so=100)["chi_tiet"]["UV-T"]
    assert b["trang_thai"] == "QUA"
    assert (a["delta"], a["p"], a["z"]) == (b["delta"], b["p"], b["z"])


# ── 2. MỘT keo_luc, lấy ở lời gọi đầu ────────────────────────────────────

def test_KEO_hoi_dong_ho_DUNG_MOT_lan_va_keo_luc_la_gio_cua_loi_goi_dau_theo_gio_VN():
    gia, cal, ma = _bang(W=20, M=3)
    gio = iter([_gio(cal[-1], "16:00"), _gio(cal[-1], "17:00"), _gio(cal[-1], "18:00")])
    g = Gia(gia)
    kq = kg.keo(ma, cal[0], cal[-1], lay=g.lay, nghi_giay=0.0, bay_gio=lambda: next(gio), ngu=g.ngu)
    assert kq["keo_luc"] == f"{cal[-1]}T16:00:00+07:00"
    assert next(gio) == _gio(cal[-1], "17:00")                 # lần hỏi thứ hai KHÔNG xảy ra
    assert {d.split(",")[4] for d in kq["van_ban"].splitlines()[1:]} == {kq["keo_luc"]}


def test_KEO_gio_UTC_duoc_doi_ve_gio_VN_va_gio_khong_co_mui_BI_TU_CHOI():
    gia, cal, ma = _bang(W=20, M=3)
    utc = datetime.datetime.fromisoformat(f"{cal[-1]}T09:00:00+00:00")        # 16:00 giờ VN
    kq, _ = _keo(gia, cal, ma, gio=utc)
    assert kq["keo_luc"] == f"{cal[-1]}T16:00:00+07:00"
    with pytest.raises(kg.KeoLoi, match="mui gio"):
        _keo(gia, cal, ma, gio=datetime.datetime.fromisoformat(f"{cal[-1]}T16:00:00"))


# ── 3. SYNTHETIC / FAILED không bao giờ vào bảng ─────────────────────────

def _synthetic(ma, tu, den):
    """Đúng dạng kết quả đường lui của `VNStockCollectorAgent.collect`: ĐỦ dòng, status SYNTHETIC."""
    import data_collectors
    df = data_collectors.VNStockCollectorAgent()._generate_fallback_df(ma, tu, den)
    return {"status": "SYNTHETIC", "df": df,
            "note": "⚠️ KHÔNG kết nối được nguồn thật — đang dùng dữ liệu MÔ PHỎNG NGẪU NHIÊN"}


def test_SYNTHETIC_mang_DataFrame_day_du_van_BI_TU_CHOI_va_goi_ten_ma():
    gia, cal, ma = _bang(W=25, M=5)
    x = ma[2]
    g = Gia(gia, sua={x: lambda s: _synthetic(x, cal[0], cal[-1])})
    assert len(_synthetic(x, cal[0], cal[-1])["df"]) > 10        # đường lui có dữ liệu thật sự
    kq, _ = _keo(gia, cal, ma, g=g)
    assert list(kq["hong"]) == [x] and "SYNTHETIC" in kq["hong"][x]
    assert kq["van_ban"] is None and x not in kq["gia"].columns and x not in kq["nguon"]
    assert set(kq["gia"].columns) == set(ma) - {x}              # mã khác nguyên vẹn, không ai thay chỗ


def test_FAILED_va_status_la_va_nguon_ngoai_ho_va_bang_rong_deu_BI_TU_CHOI():
    gia, cal, ma = _bang(W=25, M=8)
    cac = {
        ma[0]: lambda s: {"status": "FAILED", "df": None, "note": "x", "source": ""},
        ma[1]: lambda s: {"status": "PARTIAL", "df": _df(s), "source": "vci"},
        ma[2]: lambda s: {"status": "OK", "df": _df(s), "source": "tcbs"},
        ma[3]: lambda s: {"status": "OK", "df": _df(s)},                       # thiếu `source`
        ma[4]: lambda s: {"status": "OK", "df": _df(s.iloc[:0]), "source": "vci"},
        ma[5]: lambda s: {"status": "OK", "df": None, "source": "vci"},
        ma[6]: lambda s: "khong phai dict",
        ma[7]: lambda s: {"status": "SYNTHETIC", "df": _df(s), "source": "vci"},  # có cả `source` hợp lệ
    }
    kq, _ = _keo(gia, cal, ma, g=Gia(gia, sua=cac))
    assert set(kq["hong"]) == set(ma[:8]) and kq["van_ban"] is None
    assert "FAILED" in kq["hong"][ma[0]] and "PARTIAL" in kq["hong"][ma[1]]
    assert "tcbs" in kq["hong"][ma[2]] and "None" in kq["hong"][ma[3]]
    assert "SYNTHETIC" in kq["hong"][ma[7]]
    assert "bang rong" in kq["hong"][ma[4]] and "bang rong" in kq["hong"][ma[5]]
    assert "khong phai dict" in kq["hong"][ma[6]]
    assert kq["gia"].empty


def test_KHONG_con_hong_thi_moi_co_van_ban_va_bang_bo_mot_ma_KHONG_duoc_ghi_ra():
    gia, cal, ma = _bang(W=25, M=5)
    kq, _ = _keo(gia, cal, ma, g=Gia(gia, loi={ma[4]: RuntimeError("mat mang")}))
    assert kq["van_ban"] is None and "RuntimeError: mat mang" in kq["hong"][ma[4]]
    assert len(kq["gia"].columns) == 4                           # có gia để chẩn đoán, KHÔNG có văn bản
    kq, _ = _keo(gia, cal, ma)
    assert kq["hong"] == {} and kq["van_ban"] is not None


def test_thieu_goi_ImportError_DUNG_CA_LUOT_ngay_sau_loi_goi_dau():
    gia, cal, ma = _bang(W=20, M=5)
    g = Gia(gia, loi={m: ImportError("No module named 'vnstock'") for m in ma})
    with pytest.raises(kg.KeoLoi, match="vnstock"):
        _keo(gia, cal, ma, g=g)
    assert [e for e in g.su_kien if e[0] == "lay"] == [("lay", ma[0], cal[0], cal[-1])]


# ── 4. giãn nhịp ─────────────────────────────────────────────────────────

def test_NHIP_nghi_GIUA_cac_loi_goi_khong_nghi_truoc_loi_goi_dau():
    gia, cal, ma = _bang(W=20, M=4)
    g = Gia(gia)
    kq, _ = _keo(gia, cal, ma, g=g, nghi=1.7)
    assert g.su_kien == [("lay", ma[0], cal[0], cal[-1]), ("ngu", 1.7),
                         ("lay", ma[1], cal[0], cal[-1]), ("ngu", 1.7),
                         ("lay", ma[2], cal[0], cal[-1]), ("ngu", 1.7),
                         ("lay", ma[3], cal[0], cal[-1])]
    g1 = Gia(gia)
    _keo(gia, cal, ma[:1], g=g1, nghi=1.7)
    assert g1.su_kien == [("lay", ma[0], cal[0], cal[-1])]       # một mã: không nghỉ


def test_NHIP_mac_dinh_2_giay_va_con_so_am_BI_TU_CHOI_va_hong_van_nghi():
    assert kg.NGHI_GIAY == 2.0
    gia, cal, ma = _bang(W=20, M=3)
    with pytest.raises(kg.KeoLoi, match="nghi_giay"):
        _keo(gia, cal, ma, nghi=-1)
    g = Gia(gia, loi={ma[0]: RuntimeError("x")})                 # mã hỏng vẫn tốn một lời gọi → vẫn nghỉ sau
    _keo(gia, cal, ma, g=g, nghi=kg.NGHI_GIAY)
    assert [e for e in g.su_kien if e[0] == "ngu"] == [("ngu", 2.0), ("ngu", 2.0)]


# ── 5. nến cuối đã đóng ──────────────────────────────────────────────────

@pytest.mark.parametrize("gio, ok", [("14:00", False), ("15:29", False), ("15:30", True),
                                     ("23:59", True)])
def test_NEN_DO_keo_truoc_15h30_gio_VN_cua_ngay_nen_cuoi_BI_TU_CHOI(gio, ok):
    gia, cal, ma = _bang(W=20, M=3)
    if ok:
        kq, _ = _keo(gia, cal, ma, gio=_gio(cal[-1], gio))
        assert kq["van_ban"] is not None
    else:
        with pytest.raises(kg.KeoLoi, match="DO"):
            _keo(gia, cal, ma, gio=_gio(cal[-1], gio))


def test_NEN_DO_theo_gio_VN_khong_theo_gio_UTC_va_nen_cuoi_o_ngay_sau_gio_keo_BI_TU_CHOI():
    gia, cal, ma = _bang(W=20, M=3)
    sau = datetime.datetime.fromisoformat(f"{cal[-1]}T08:29:00+00:00")        # 15:29 VN
    with pytest.raises(kg.KeoLoi, match="DO"):
        _keo(gia, cal, ma, gio=sau)
    ok = datetime.datetime.fromisoformat(f"{cal[-1]}T08:30:00+00:00")         # 15:30 VN
    assert _keo(gia, cal, ma, gio=ok)[0]["van_ban"] is not None
    truoc = _gio((datetime.date.fromisoformat(cal[-1]) - datetime.timedelta(days=1)).isoformat())
    with pytest.raises(kg.KeoLoi, match="DO"):                                 # giá từ tương lai
        _keo(gia, cal, ma, gio=truoc)


# ── 6. mã hỏng cụ thể: gọi tên, không điền ───────────────────────────────

def test_LECH_nen_cuoi_goi_ten_ma_tre_va_ma_di_truoc_nhung_khong_vu_oan_ma_con_lai():
    gia, cal, ma = _bang(W=25, M=6)
    tre = Gia(gia, sua={ma[1]: lambda s: {"status": "OK", "df": _df(s.iloc[:-1]), "source": "vci"}})
    kq, _ = _keo(gia, cal, ma, g=tre)
    assert list(kq["hong"]) == [ma[1]] and "nen cuoi" in kq["hong"][ma[1]]
    # hoà phiếu (hai mã, hai ngày cuối khác nhau): nến cuối chung là ngày MUỘN hơn
    hai = Gia(gia, sua={ma[1]: lambda s: {"status": "OK", "df": _df(s.iloc[:-1]), "source": "vci"}})
    kq2, _ = _keo(gia, cal, ma[:2], g=hai)
    assert kq2["cuoi"] == cal[-1] and list(kq2["hong"]) == [ma[1]]
    # một mã có nến SAU nến cuối chung: chính nó bị gọi tên; năm mã kia không bị vu
    dai = gia.copy()
    dai.loc["2099-01-01", ma[3]] = 1.0
    g = Gia(dai)
    kq = kg.keo(ma, cal[0], "2099-12-31", lay=g.lay, nghi_giay=0.0, ngu=g.ngu,
                bay_gio=lambda: _gio("2099-12-31"))
    assert list(kq["hong"]) == [ma[3]] and kq["cuoi"] == cal[-1]
    assert "2099-01-01" in kq["hong"][ma[3]] and kq["van_ban"] is None


def test_CA_BANG_cung_thieu_mot_phien_thi_KHONG_ma_nao_hong_nhung_lich_cong_bo_bat_duoc():
    """Mọi mã cùng thiếu một phiên: không mã nào lệch so với lịch chung của bảng, chỉ
    `kiem_lich` (so với lịch công bố trước) thấy — nhãn sẽ trượt một phiên mà không ai báo."""
    gia, cal, ma = _bang(W=25, M=4)
    thieu = gia.drop(index=cal[7])
    with pytest.raises(cx.BangGiaLoi, match=cal[7]):
        _keo(thieu, cal, ma)


def test_THIEU_phien_giua_chung_goi_ten_ma_va_phien_khong_dien():
    gia, cal, ma = _bang(W=25, M=5)
    thieu = Gia(gia, sua={ma[2]: lambda s: {"status": "OK", "df": _df(s.drop(index=cal[7])),
                                            "source": "kbs"}})
    kq, _ = _keo(gia, cal, ma, g=thieu)
    assert list(kq["hong"]) == [ma[2]]
    assert "thieu 1 phien" in kq["hong"][ma[2]] and cal[7] in kq["hong"][ma[2]]
    assert kq["van_ban"] is None
    assert np.isnan(kq["gia"].at[cal[7], ma[2]])                 # chỗ thiếu vẫn là NaN, không ai điền


@pytest.mark.parametrize("gia_xau", [0.0, -3.5, float("nan"), float("inf")])
def test_GIA_khong_phai_so_duong_huu_han_goi_ten_ma_va_ngay(gia_xau):
    gia, cal, ma = _bang(W=25, M=4)

    def hong(s):
        s = s.copy()
        s.iloc[5] = gia_xau
        return {"status": "OK", "df": _df(s), "source": "vci"}
    kq, _ = _keo(gia, cal, ma, g=Gia(gia, sua={ma[1]: hong}))
    assert list(kq["hong"]) == [ma[1]] and cal[5] in kq["hong"][ma[1]]
    assert "khong phai so duong huu han" in kq["hong"][ma[1]]


def test_GIA_chuoi_khong_doc_duoc_va_ngay_khong_doc_duoc_va_ngay_trung_BI_TU_CHOI():
    gia, cal, ma = _bang(W=25, M=4)

    def chu(s):
        d = _df(s)
        d["close"] = d["close"].astype(object)
        d.loc[3, "close"] = "abc"
        return {"status": "OK", "df": d, "source": "vci"}

    def ngay_xau(s):
        d = _df(s)
        d.loc[2, "time"] = "khong phai ngay"
        return {"status": "OK", "df": d, "source": "vci"}

    def trung(s):
        d = _df(s)
        return {"status": "OK", "df": pd.concat([d, d.iloc[[4]]], ignore_index=True), "source": "vci"}

    def thieu_cot(s):
        return {"status": "OK", "df": _df(s).drop(columns=["close"]), "source": "vci"}
    cac = dict(zip(ma, (chu, ngay_xau, trung, thieu_cot)))
    kq, _ = _keo(gia, cal, ma, g=Gia(gia, sua=cac))
    assert set(kq["hong"]) == set(ma)
    assert "khong phai so duong huu han" in kq["hong"][ma[0]] and cal[3] in kq["hong"][ma[0]]
    assert "`time`" in kq["hong"][ma[1]]
    assert "trung" in kq["hong"][ma[2]] and cal[4] in kq["hong"][ma[2]]
    assert "thieu cot" in kq["hong"][ma[3]]


def test_NEN_ngoai_khoang_tu_den_bi_bo_khong_vao_bang():
    gia, cal, ma = _bang(W=25, M=3)
    kq = kg.keo(ma, cal[3], cal[-1], lay=Gia(gia).lay, nghi_giay=0.0, ngu=lambda s: None,
                bay_gio=lambda: _gio(cal[-1]))
    assert kq["gia"].index[0] == cal[3] and kq["gia"].index[-1] == cal[-1]
    assert kq["hong"] == {}


def test_MA_chi_co_nen_ngoai_khoang_tu_den_la_hong_khong_phai_chuoi_rong_im_lang():
    gia, cal, ma = _bang(W=25, M=3)
    cu = Gia(gia, sua={ma[0]: lambda s: {"status": "OK", "df": _df(s.iloc[:3]), "source": "vci"}})
    kq = kg.keo(ma, cal[5], cal[-1], lay=cu.lay, nghi_giay=0.0, ngu=lambda s: None,
                bay_gio=lambda: _gio(cal[-1]))
    assert list(kq["hong"]) == [ma[0]] and "khong co nen nao" in kq["hong"][ma[0]]
    assert kq["van_ban"] is None


# ── 7. tham số ───────────────────────────────────────────────────────────

@pytest.mark.parametrize("ma", [[], ["A,B"], ["A B"], [""], ["abc-d"], ["TOOLONGMA123"]])
def test_THAM_SO_danh_sach_ma_khong_hop_le_BI_TU_CHOI_truoc_khi_goi_gi(ma):
    g = Gia(pd.DataFrame())
    with pytest.raises(kg.KeoLoi):
        kg.keo(ma, "2026-10-05", "2026-10-30", lay=g.lay, bay_gio=lambda: _gio("2026-10-30"),
               ngu=g.ngu)
    assert g.su_kien == []


def test_THAM_SO_tu_bang_den_la_hop_le_mot_phien():
    gia, cal, ma = _bang(W=20, M=3)
    g = Gia(gia)
    kq = kg.keo(ma, cal[4], cal[4], lay=g.lay, nghi_giay=0.0, bay_gio=lambda: _gio("2027-03-01"),
                ngu=g.ngu)
    assert kq["hong"] == {} and list(kq["gia"].index) == [cal[4]]


@pytest.mark.parametrize("tu, den", [("05/10/2026", "2026-10-30"), ("2026-10-05", "30-10"),
                                     ("2026-02-30", "2026-10-30"), ("2026-10-30", "2026-10-05")])
def test_THAM_SO_ngay_sai_khuon_hoac_dao_nguoc_BI_TU_CHOI(tu, den):
    g = Gia(pd.DataFrame())
    with pytest.raises(ValueError):
        kg.keo(["AAA"], tu, den, lay=g.lay, bay_gio=lambda: _gio("2026-10-30"), ngu=g.ngu)
    assert g.su_kien == []


# ── 8. gác AST: không điền, không mạng ở mức module ──────────────────────

def _cay(f):
    return ast.parse((GOC / f).read_text(encoding="utf-8"))


def _goc_nhap(cay, trong=None):
    ra = set()
    for n in ast.walk(trong or cay):
        if isinstance(n, ast.Import):
            ra |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            ra.add((n.module or "").split(".")[0])
    return ra


def test_GAC_AST_keo_bang_gia_khong_dien_gia_khong_ghi_file_khong_nhap_mang_o_muc_module():
    cay = _cay("keo_bang_gia.py")
    goi = {getattr(n.func, "attr", getattr(n.func, "id", "")) for n in ast.walk(cay)
           if isinstance(n, ast.Call)}
    assert not goi & {"fillna", "ffill", "bfill", "pad", "backfill", "interpolate", "replace",
                      "write_text", "write_bytes", "to_csv", "to_json", "open", "mkdir",
                      "unlink", "rename", "touch"}, sorted(goi)
    kw = {k.arg for n in ast.walk(cay) if isinstance(n, ast.Call) for k in n.keywords}
    assert not kw & {"fill_value", "method", "limit"}, kw
    muc_module = set()
    for n in cay.body:                                           # CHỈ câu lệnh ở mức module
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            muc_module |= _goc_nhap(n)
    assert not muc_module & {"vnstock", "vnstock_data", "vnai", "data_collectors", "requests",
                             "urllib", "urllib3", "http", "socket", "gspread", "sheets_store",
                             "google_sheets_sync", "httpx", "aiohttp"}, sorted(muc_module)
    toan = _goc_nhap(cay)
    assert "vnstock" not in toan and "vnstock_data" not in toan and "vnai" not in toan


def test_GAC_AST_data_collectors_chi_duoc_nhap_BEN_TRONG_lay_mac_dinh():
    cay = _cay("keo_bang_gia.py")
    ham = [n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == "lay_mac_dinh"]
    assert len(ham) == 1 and "data_collectors" in _goc_nhap(cay, ham[0])
    ngoai = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.FunctionDef) and n.name != "lay_mac_dinh":
            ngoai |= _goc_nhap(n)
    assert "data_collectors" not in ngoai


def test_lay_mac_dinh_uy_thac_collect_voi_san_theo_MA_tu_bang_chup(monkeypatch):
    goi = []

    class Gia_(object):
        def collect(self, ma, tu, den, exchange="HOSE"):
            goi.append((ma, tu, den, exchange))
            return {"status": "OK", "df": "dau-vao-nguyen-ven", "source": "vci"}
    monkeypatch.setitem(sys.modules, "data_collectors",
                        types.SimpleNamespace(VNStockCollectorAgent=Gia_))
    for ma, san in (("HUT", "HNX"), ("ACV", "UPCOM"), ("FPT", "HOSE"), ("ZZZ", "HOSE")):
        kq = kg.lay_mac_dinh(ma, "2026-10-05", "2026-10-30")
        assert kq == {"status": "OK", "df": "dau-vao-nguyen-ven", "source": "vci"}
        assert goi[-1] == (ma, "2026-10-05", "2026-10-30", san)


# ── 9. CLI ───────────────────────────────────────────────────────────────

def _cli():
    spec = importlib.util.spec_from_file_location("keo_bang_gia_cli", GOC / "tools" / "keo_bang_gia.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _chay(args, g, gio):
    return _cli().main(args, lay=g.lay, bay_gio=lambda: gio, ngu=g.ngu)


def test_CLI_ghi_dung_van_ban_cua_bo_keo_va_in_tom_tat(tmp_path, capsys):
    gia, cal, ma = _bang(W=25, M=4)
    ra = tmp_path / "bg.csv"
    g = Gia(gia)
    kq, _ = _keo(gia, cal, ma)
    code = _chay(["--ma", ",".join(ma), "--tu", cal[0], "--den", cal[-1], "--ra", str(ra),
                  "--nghi-giay", "0"], g, _gio(cal[-1]))
    assert code == 0
    assert ra.read_text(encoding="utf-8") == kq["van_ban"]
    assert [e for e in g.su_kien if e[0] == "ngu"] == [("ngu", 0.0)] * (len(ma) - 1)
    out = capsys.readouterr().out
    assert "da ghi" in out and f"{len(ma)} ma" in out and kq["keo_luc"] in out
    pd.testing.assert_frame_equal(cx.doc_bang_gia(ra)["gia"], gia)


def test_CLI_con_mot_ma_hong_thi_KHONG_ghi_file_va_in_TEN_ma_hong_ma_thoat_1(tmp_path, capsys):
    gia, cal, ma = _bang(W=25, M=5)
    ra = tmp_path / "bg.csv"
    g = Gia(gia, sua={ma[3]: lambda s: _synthetic(ma[3], cal[0], cal[-1])}, loi={ma[1]: OSError("rot mang")})
    code = _chay(["--ma", ",".join(ma), "--tu", cal[0], "--den", cal[-1], "--ra", str(ra),
                  "--nghi-giay", "0"], g, _gio(cal[-1]))
    out = capsys.readouterr().out
    assert code == 1 and not ra.exists() and out.startswith("TU CHOI")
    assert f"{ma[3]}:" in out and "SYNTHETIC" in out and f"{ma[1]}:" in out and "rot mang" in out
    assert not [m for m in ma if m not in (ma[1], ma[3]) and f"  {m}:" in out]    # mã tốt không bị gọi tên


def test_CLI_tep_ra_da_ton_tai_thi_TU_CHOI_khong_ghi_de_khong_ghi_noi_va_khong_keo_gi(tmp_path, capsys):
    gia, cal, ma = _bang(W=20, M=3)
    ra = tmp_path / "bg.csv"
    ra.write_text("cu\n", encoding="utf-8")
    g = Gia(gia)
    code = _chay(["--ma", ",".join(ma), "--tu", cal[0], "--den", cal[-1], "--ra", str(ra)], g,
                 _gio(cal[-1]))
    assert code == 1 and ra.read_text(encoding="utf-8") == "cu\n"
    assert g.su_kien == [] and "da ton tai" in capsys.readouterr().out


def test_CLI_thieu_goi_thi_TU_CHOI_ma_thoat_1_khong_ghi_file(tmp_path, capsys):
    gia, cal, ma = _bang(W=20, M=3)
    ra = tmp_path / "bg.csv"
    g = Gia(gia, loi={m: ImportError("No module named 'vnstock'") for m in ma})
    code = _chay(["--ma", ",".join(ma), "--tu", cal[0], "--den", cal[-1], "--ra", str(ra)], g,
                 _gio(cal[-1]))
    assert code == 1 and not ra.exists() and "vnstock" in capsys.readouterr().out


def test_CLI_nen_cuoi_con_do_thi_TU_CHOI_ma_thoat_1(tmp_path, capsys):
    gia, cal, ma = _bang(W=20, M=3)
    ra = tmp_path / "bg.csv"
    code = _chay(["--ma", ",".join(ma), "--tu", cal[0], "--den", cal[-1], "--ra", str(ra),
                  "--nghi-giay", "0"], Gia(gia), _gio(cal[-1], "14:00"))
    assert code == 1 and not ra.exists() and "DO" in capsys.readouterr().out


def test_CLI_ma_va_quyet_dinh_loai_tru_nhau_va_phai_co_ra(tmp_path):
    cli = _cli()
    for args in ([], ["--ma", "AAA"], ["--ma", "AAA", "--quyet-dinh", "x.json", "--ra", "y.csv"],
                 ["--ra", "y.csv"]):
        with pytest.raises(SystemExit) as e:
            cli.main(args)
        assert e.value.code == 2, args


def test_CLI_quyet_dinh_lay_moi_ma_va_tu_mac_dinh_la_du_lieu_cham_som_nhat_cua_so(tmp_path):
    gia, cal, ma = _bang(W=25, M=4)
    rows = [{"symbol": m, "signal_date": cal[0], "score": 1.0, "components": "{}"} for m in ma]
    rows += [{"symbol": ma[0], "signal_date": cal[1], "score": 1.0, "components": "{}"}]
    (tmp_path / "qd.json").write_text(json.dumps(rows), encoding="utf-8")
    uv = {"ung_vien": {"UV-A": {"khai_ngay": "2026-10-05", "mo_ta": "m", "ly_do": "l",
                                "qua_sang": None, "spec": {"loai": "trong_so",
                                                           "trong_so": {"volume_score": 1.0}}},
                       "UV-B": {"khai_ngay": "2026-11-02", "mo_ta": "m", "ly_do": "l",
                                "qua_sang": None, "spec": {"loai": "trong_so",
                                                           "trong_so": {"volume_score": 1.0}}}}}
    (tmp_path / "uv.json").write_text(json.dumps(uv), encoding="utf-8")
    g = Gia(gia)
    code = _chay(["--quyet-dinh", str(tmp_path / "qd.json"), "--ung-vien", str(tmp_path / "uv.json"),
                  "--den", cal[-1], "--ra", str(tmp_path / "bg.csv"), "--nghi-giay", "0"], g,
                 _gio(cal[-1]))
    goi = [e for e in g.su_kien if e[0] == "lay"]
    assert code == 0 and [e[1] for e in goi] == sorted(ma)       # mỗi mã MỘT lần, thứ tự chữ cái
    assert {e[2] for e in goi} == {cx.tu_ngay_doc("2026-10-05")}  # sớm nhất trong sổ, theo biên đã ký
    assert {e[3] for e in goi} == {cal[-1]}


def test_CLI_den_mac_dinh_la_hom_nay_gio_VN(tmp_path, monkeypatch):
    gia, cal, ma = _bang(W=20, M=3)
    monkeypatch.setattr(dq, "now_vn", lambda: _gio(cal[-1], "16:30"))
    g = Gia(gia)
    code = _cli().main(["--ma", ",".join(ma), "--tu", cal[0], "--ra", str(tmp_path / "bg.csv"),
                        "--nghi-giay", "0"], lay=g.lay, ngu=g.ngu)
    assert code == 0 and {e[3] for e in g.su_kien if e[0] == "lay"} == {cal[-1]}
    assert f"{cal[-1]}T16:30:00+07:00" in (tmp_path / "bg.csv").read_text(encoding="utf-8")


def test_CLI_khong_khai_nghi_giay_thi_dung_mac_dinh_NGHI_GIAY(tmp_path):
    gia, cal, ma = _bang(W=20, M=3)
    g = Gia(gia)
    assert _chay(["--ma", ",".join(ma), "--tu", cal[0], "--den", cal[-1],
                  "--ra", str(tmp_path / "bg.csv")], g, _gio(cal[-1])) == 0
    assert [e for e in g.su_kien if e[0] == "ngu"] == [("ngu", kg.NGHI_GIAY)] * 2


def test_CLI_ma_khong_hop_le_BI_TU_CHOI_ma_thoat_1(tmp_path, capsys):
    gia, cal, ma = _bang(W=20, M=3)
    g = Gia(gia)
    code = _chay(["--ma", "AAA,b;c", "--tu", cal[0], "--den", cal[-1], "--ra", str(tmp_path / "x.csv")],
                 g, _gio(cal[-1]))
    assert code == 1 and "ma khong hop le" in capsys.readouterr().out and g.su_kien == []


def test_CLI_mo_tep_ra_o_che_do_TAO_MOI_va_chi_nhap_module_thuan_AST():
    cay = _cay("tools/keo_bang_gia.py")
    mo = [n for n in ast.walk(cay) if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "open"]
    assert len(mo) == 1 and isinstance(mo[0].args[0], ast.Constant) and mo[0].args[0].value == "x"
    goc = _goc_nhap(cay)
    assert goc >= {"cham_bong", "cham_xac_nhan", "keo_bang_gia", "data_quality"}
    assert not goc & {"vnstock", "vnstock_data", "vnai", "requests", "gspread", "sheets_store",
                      "google_sheets_sync", "app", "streamlit", "data_collectors"}, goc
    ghi = {n.func.attr for n in ast.walk(cay)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert not ghi & {"write_text", "write_bytes", "to_csv", "to_json", "push", "mkdir", "unlink"}
