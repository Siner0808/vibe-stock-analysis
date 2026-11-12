"""BƯỚC 267 — `nguon_gia_cong_khai`: đường lấy giá NGÀY công khai thay `vnstock`. TOÀN BỘ OFFLINE.

Phản hồi THẬT của các điểm cuối (cửa sổ nhỏ, ghi 11/11/2026) nằm ở `tests/du_lieu/nguon_gia_267.json`;
test không chạm mạng (gác thứ ba của `tests/conftest.py` làm ĐỎ mọi test gọi mạng giá thật).

Bảy nhóm:
  1. khung trả về đúng dạng vnstock 4.0.9 (cột, kiểu, không múi giờ) với MỌI nguồn
  2. thứ tự nguồn là quyết định đo được (iBoard KHÔNG đứng trong chuỗi cổ phiếu) và MỘT chuỗi = MỘT nguồn
  3. lỗi thật đã gặp: nến trùng ngày (Entrade), mốc trùng (iBoard), nến sai lẻ (VNDirect)
  4. kiểm lành mạnh nổ TO, không sửa không lấp
  5. mạng: User-Agent thật, timeout 30 giây, thử lại 2 lần có lùi, nghỉ giữa hai lần gọi, 406 của VNDirect
  6. nến của ngày đang giao dịch bị `nen_cuoi_dang_do` coi là CHƯA ĐÓNG
  7. nối dây: `collect` · `fetch_one` · các chỗ không có nguồn · không module sản xuất nào sập khi vắng vnstock
"""
import ast
import copy
import datetime as dt
import json
import re
import sys
from pathlib import Path

import pandas as pd
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import nguon_gia_cong_khai as ngk  # noqa: E402
from data_quality import GIO_NEN_DA_DONG, VN_TZ, nen_cuoi_dang_do, SO_PHIEN_TOI_THIEU  # noqa: E402

FIX = json.loads((Path(__file__).resolve().parent / "du_lieu" / "nguon_gia_267.json").read_text(encoding="utf-8"))["muc"]
HOST = {"entrade": "services.entrade.com.vn", "vndirect": "dchart-api.vndirect.com.vn",
        "vps": "histdatafeed.vps.com.vn", "iboard": "iboard-api.ssi.com.vn"}
NGUON = {n.ten: n for n in (ngk.NGUON_ENTRADE, ngk.NGUON_VNDIRECT, ngk.NGUON_VPS, ngk.NGUON_IBOARD)}


@pytest.fixture(autouse=True)
def _dong_ho_goi_mang_ve_0():
    """`_lan_goi_cuoi` là trạng thái module (nghỉ giữa hai lần gọi): đặt lại trước và sau mỗi test."""
    ngk._lan_goi_cuoi[0] = 0.0
    yield
    ngk._lan_goi_cuoi[0] = 0.0


def _pr(ten):
    return copy.deepcopy(FIX[ten]["phan_hoi"])


def _http_gia(theo_host):
    """Mạng giả: {tên nguồn: phản hồi | Exception | hàm(url)}; ghi mọi lần gọi vào `.goi`."""
    goi = []

    def http(url, accept="*/*"):
        goi.append((url, accept))
        for ten, host in HOST.items():
            if host in url:
                if ten not in theo_host:
                    raise AssertionError(f"test không giả nguồn {ten}: {url}")
                v = theo_host[ten]
                if isinstance(v, Exception):
                    raise v
                if callable(v):
                    return v(url)
                return copy.deepcopy(v)
        raise AssertionError(f"host lạ: {url}")

    http.goi = goi
    return http


def _lay(ma, tu, den, theo_host, **kw):
    kw.setdefault("toi_thieu", 1)
    return ngk.lay_ohlcv(ma, tu, den, http=_http_gia(theo_host), ngu=lambda s: None,
                         dong_ho=lambda: 0.0, **kw)


def _chuoi_tong_hop(n=30, ket_thuc="2026-11-10", **ghi_de):
    """Chuỗi TỔNG HỢP (không phải số thật) cho test logic cần ≥ 20 phiên. Phản hồi dạng VNDirect."""
    ngay = pd.bdate_range(end=ket_thuc, periods=n)
    t = [int(d.replace(tzinfo=dt.timezone.utc).timestamp()) for d in ngay]
    c = [round(20.0 + 0.1 * i, 2) for i in range(n)]
    ra = {"t": t, "o": [x - 0.05 for x in c], "h": [x + 0.2 for x in c], "l": [x - 0.2 for x in c],
          "c": c, "v": [1_000_000 + 1000 * i for i in range(n)], "s": "ok"}
    ra.update(ghi_de)
    return ra


# ── 1. khung đúng dạng ─────────────────────────────────────────────────

@pytest.mark.parametrize("ten", ["entrade", "vndirect", "vps", "iboard"])
def test_khung_co_phieu_dung_dang_vnstock_409(ten):
    m = FIX[f"fpt_{ten}"]
    df = ngk.dung_khung(NGUON[ten].doc(m["phan_hoi"]), dt.date(2026, 11, 3), dt.date(2026, 11, 10))
    assert list(df.columns) == list(ngk.COT) == ["time", "open", "high", "low", "close", "volume"]
    assert str(df["time"].dtype) == "datetime64[ns]", df["time"].dtype      # không múi giờ, đơn vị ns
    assert df["time"].dt.tz is None
    assert (df["time"] == df["time"].dt.normalize()).all()                  # ngày, không có giờ
    assert [str(df[c].dtype) for c in ("open", "high", "low", "close")] == ["float64"] * 4
    assert str(df["volume"].dtype) == "int64"
    assert df["time"].is_monotonic_increasing and not df["time"].duplicated().any()
    print(f"PASS  {ten}: khung đúng dạng, {len(df)} phiên")


def test_bon_nguon_cung_gia_dong_cua_FPT_nhung_ngay_chung():
    """Cùng một mã, cùng ngày: đóng cửa phải GIỐNG HỆT ở cả bốn nguồn (đơn vị nghìn đồng)."""
    khung = {}
    for ten in NGUON:
        m = FIX[f"fpt_{ten}"]
        df = ngk.dung_khung(NGUON[ten].doc(m["phan_hoi"]), dt.date(2026, 11, 3), dt.date(2026, 11, 10))
        khung[ten] = df.set_index("time")["close"]
    chung = set.intersection(*(set(s.index) for s in khung.values()))
    assert len(chung) >= 4, chung
    for ngay in sorted(chung):
        gia = {t: float(s.loc[ngay]) for t, s in khung.items()}
        assert len(set(gia.values())) == 1, (ngay, gia)
    assert float(khung["vndirect"].loc["2026-11-10"]) == 50.9       # đơn vị nghìn đồng, như VCI


def test_ngay_phien_la_ngay_gio_VN_cho_moi_cach_dat_moc():
    """Nguồn đặt mốc nến ở 00:00 UTC (iBoard/VPS), 02:00 UTC = 09:00 ICT (Entrade) hoặc 17:00 UTC hôm
    trước = 00:00 ICT (kiểu TradingView): cả ba là CÙNG một ngày phiên theo giờ VN."""
    nam = [dt.datetime(2026, 11, 10, 0, 0, tzinfo=dt.timezone.utc), dt.datetime(2026, 11, 10, 2, 0, tzinfo=dt.timezone.utc),
           dt.datetime(2026, 11, 9, 17, 0, tzinfo=dt.timezone.utc)]
    for gio in nam:
        ra = {"t": [int(gio.timestamp())], "o": [1.0], "h": [1.0], "l": [1.0], "c": [1.0], "v": [1]}
        df = ngk.dung_khung(ngk._doc_phang(ra), dt.date(2026, 11, 1), dt.date(2026, 11, 30))
        assert str(df["time"].iloc[0].date()) == "2026-11-10", gio


def test_cat_cua_so_hai_dau_tinh_ca_hai_dau():
    df = ngk.dung_khung(ngk._doc_phang(_pr("fpt_vndirect")), dt.date(2026, 11, 5), dt.date(2026, 11, 9))
    assert [str(x.date()) for x in df["time"]] == ["2026-11-05", "2026-11-06", "2026-11-09"]


def test_lay_ohlcv_xin_rong_mot_ngay_hai_dau_roi_cat_chinh_xac():
    http = _http_gia({"vndirect": _pr("fpt_vndirect")})
    r = ngk.lay_ohlcv("FPT", "2026-11-05", "2026-11-09", toi_thieu=1, chuoi=[ngk.NGUON_VNDIRECT],
                      http=http, ngu=lambda s: None, dong_ho=lambda: 0.0)
    url = http.goi[0][0]
    ts_tu = int(dt.datetime(2026, 11, 5, tzinfo=dt.timezone.utc).timestamp())
    ts_den = int(dt.datetime(2026, 11, 9, tzinfo=dt.timezone.utc).timestamp())
    assert f"from={ts_tu - 86400}" in url and f"to={ts_den + 86400}" in url, url
    assert [str(x.date()) for x in r.df["time"]] == ["2026-11-05", "2026-11-06", "2026-11-09"]


# ── 2. thứ tự nguồn và MỘT chuỗi = MỘT nguồn ────────────────────────────

def test_thu_tu_nguon_la_QUYET_DINH_DO_DUOC():
    assert [n.ten for n in ngk.CHUOI_CO_PHIEU] == ["entrade", "vndirect", "vps"]
    assert [n.ten for n in ngk.CHUOI_CHI_SO] == ["vndirect", "iboard", "vps"]
    # iBoard sai giá ở mã UPCoM (BƯỚC 267): không được vào chuỗi cổ phiếu. Entrade thiếu phiên ở chỉ số.
    assert "iboard" not in ngk.ten_cac_nguon("FPT") and "entrade" not in ngk.ten_cac_nguon("VNINDEX")
    assert ngk.loai_ma("vnindex") == "chi_so" and ngk.loai_ma("FPT") == "co_phieu"
    assert ngk.chuoi_nguon("VNINDEX") is ngk.CHUOI_CHI_SO and ngk.chuoi_nguon("SHS") is ngk.CHUOI_CO_PHIEU


def test_nguon_dau_phuc_vu_duoc_thi_khong_hoi_nguon_sau():
    r = _lay("FPT", "2026-11-03", "2026-11-10", {"entrade": _pr("fpt_entrade"), "vndirect": _pr("fpt_vndirect")})
    assert r.nguon == "entrade" and r.da_thu == [] and r.df.attrs["nguon"] == "entrade"


def test_mot_chuoi_luon_tu_MOT_nguon_khong_va_nua_nua():
    """Entrade hỏng thì CẢ chuỗi lấy từ VNDirect: không có dòng nào của Entrade trong kết quả."""
    http = _http_gia({"entrade": ngk._LoiTam("HTTP 503"), "vndirect": _pr("fpt_vndirect")})
    r = ngk.lay_ohlcv("FPT", "2026-11-03", "2026-11-10", toi_thieu=1, http=http, ngu=lambda s: None,
                      dong_ho=lambda: 0.0)
    assert r.nguon == "vndirect" and [t for t, _ in r.da_thu] == ["entrade"]
    assert "sau 3 lần thử" in r.da_thu[0][1] and "HTTP 503" in r.da_thu[0][1]
    ref = ngk.dung_khung(ngk._doc_phang(_pr("fpt_vndirect")), dt.date(2026, 11, 3), dt.date(2026, 11, 10))
    pd.testing.assert_frame_equal(r.df, ref)
    # Entrade được thử đủ 3 lần, rồi VNDirect đúng 1 lần, không nguồn nào khác
    ten_goi = [next(t for t, h in HOST.items() if h in u) for u, _ in http.goi]
    assert ten_goi == ["entrade"] * 3 + ["vndirect"], ten_goi


def test_het_nguon_thi_NO_va_ke_tung_ly_do():
    with pytest.raises(ngk.NguonGiaHetNguon) as e:
        _lay("FPT", "2026-11-03", "2026-11-10", {"entrade": ngk._LoiTam("timeout"),
                                                 "vndirect": {"s": "no_data"}, "vps": {"s": "error"}})
    msg = str(e.value)
    assert [t for t, _ in e.value.da_thu] == ["entrade", "vndirect", "vps"]
    assert "0 phiên" in msg and "s='error'" in msg and "timeout" in msg and "FPT" in msg


def test_chi_so_di_VNDirect_truoc_roi_iBoard_roi_VPS():
    r = _lay("VNINDEX", "2026-11-03", "2026-11-10", {"vndirect": ngk._LoiTam("x"), "iboard": _pr("vnindex_iboard"),
                                                     "vps": _pr("vnindex_vps")})
    assert r.nguon == "iboard" and [t for t, _ in r.da_thu] == ["vndirect"]
    assert float(r.df["close"].iloc[-1]) == 1743.07          # điểm, không đổi đơn vị
    r2 = _lay("VNINDEX", "2026-11-03", "2026-11-10", {"vndirect": _pr("vnindex_vndirect")})
    assert r2.nguon == "vndirect"


def test_kiem_them_tu_choi_thi_bo_CA_chuoi_va_thu_nguon_ke():
    """`kiem_them` là chỗ `collect` nối `validate_ohlcv`: nguồn trả dữ liệu hỏng bị bỏ cả chuỗi."""
    thay = []

    def tu_choi_entrade(df):
        thay.append(len(df))
        return "kiểm định chặn" if len(thay) == 1 else None

    r = _lay("FPT", "2026-11-03", "2026-11-10", {"entrade": _pr("fpt_entrade"), "vndirect": _pr("fpt_vndirect")},
             kiem_them=tu_choi_entrade)
    assert r.nguon == "vndirect" and r.da_thu == [("entrade", "kiểm định chặn")]
    assert len(thay) == 2


# ── 3. lỗi thật đã gặp (phản hồi THẬT) ──────────────────────────────────

def test_Entrade_nen_trung_ngay_BCM_bi_loai_to():
    """Entrade 27/12/2022 BCM: hai nến CÙNG NGÀY (09:00 và 07:00 ICT, khối lượng 9.100 và 85.400)."""
    with pytest.raises(ngk.NguonGiaHetNguon) as e:
        _lay("BCM", "2022-12-23", "2022-12-30", {"entrade": _pr("bcm_entrade_nen_trung")}, chuoi=[ngk.NGUON_ENTRADE])
    assert "cùng một ngày phiên" in str(e.value)


def test_iBoard_chi_so_moc_trung_bi_loai_to():
    with pytest.raises(ngk.NguonGiaHetNguon) as e:
        _lay("VNINDEX", "2022-08-22", "2022-08-26", {"iboard": _pr("vnindex_iboard_moc_trung")},
             chuoi=[ngk.NGUON_IBOARD])
    assert "không tăng ngặt" in str(e.value)


def test_VNDirect_nen_sai_le_VNM_khong_bi_bat_va_khop_VPS_o_cac_ngay_con_lai():
    """GHI NHẬN MỘT KHIẾM KHUYẾT ĐÃ ĐO, không phải một gác: VNDirect có nến VNM 13/05/2025 đóng
    48,23 trong khi VPS 49,999 (kiểm lành mạnh theo chuỗi KHÔNG thấy một nến sai riêng lẻ). Test này
    khoá hiện trạng để ai đổi thứ tự nguồn hay thêm kiểm chéo phải đọc dòng này."""
    vnd = ngk.dung_khung(ngk._doc_phang(_pr("vnm_vndirect_nen_sai")), dt.date(2025, 5, 12), dt.date(2025, 5, 15))
    vps = ngk.dung_khung(ngk._doc_phang(_pr("vnm_vps_doi_chieu")), dt.date(2025, 5, 12), dt.date(2025, 5, 15))
    gia_vnd = vnd.set_index("time")["close"]
    gia_vps = vps.set_index("time")["close"]
    assert abs(gia_vnd.loc["2025-05-13"] / gia_vps.loc["2025-05-13"] - 1) > 0.03
    for ngay in ("2025-05-14", "2025-05-15"):
        assert abs(gia_vnd.loc[ngay] / gia_vps.loc[ngay] - 1) < 0.001


# ── 4. kiểm lành mạnh ──────────────────────────────────────────────────

def _khung_loi(**ghi_de):
    return ngk.dung_khung(ngk._doc_phang(_chuoi_tong_hop(**ghi_de)), dt.date(2025, 1, 1), dt.date(2026, 12, 31))


def _chuoi_theo_url(url):
    """Chuỗi TỔNG HỢP phủ đúng [from, to] của URL (test không phụ thuộc ngày chạy)."""
    import re
    tu, den = (int(x) for x in re.search(r"from=(\d+)&to=(\d+)", url).groups())
    ngay = pd.bdate_range(dt.datetime.fromtimestamp(tu, dt.timezone.utc).date(),
                          dt.datetime.fromtimestamp(den, dt.timezone.utc).date())
    t = [int(d.replace(tzinfo=dt.timezone.utc).timestamp()) for d in ngay]
    c = [round(20.0 + 0.1 * i, 2) for i in range(len(t))]
    return {"t": t, "o": c, "h": [x + 0.2 for x in c], "l": [x - 0.2 for x in c], "c": c,
            "v": [1_000_000] * len(t), "s": "ok"}


@pytest.fixture
def ngay_co_dinh(monkeypatch):
    """Đóng băng 'hôm nay' của kiểm định độ cũ: 17:00 ICT 11/11/2026 (sau giờ đóng nến)."""
    import data_quality
    monkeypatch.setattr(data_quality, "today_vn",
                        lambda: dt.datetime(2026, 11, 11, tzinfo=data_quality.VN_TZ))


@pytest.mark.parametrize("ghi_de, cum", [
    ({"c": [20.0] * 29 + [0.0]}, "'close' ≤ 0"),
    ({"o": [20.0] * 29 + [-1.0]}, "'open' ≤ 0"),
    ({"c": [20.0] * 29 + [None]}, "'close' thiếu"),
    ({"v": [100] * 29 + [-5]}, "khối lượng âm"),
    ({"v": [100] * 29 + [None]}, "'volume' thiếu"),
    ({"o": [20.0] * 29}, "khác độ dài"),
    ({"t": [1_767_000_000 + 86400 * i for i in range(29, -1, -1)]}, "không tăng ngặt"),
    ({"t": [1_767_000_000] * 30}, "không tăng ngặt"),
    ({"t": [1_767_000_000 + 86400 * (i // 2) for i in range(30)]}, "không tăng ngặt"),
    ({"t": []}, "0 phiên"),
])
def test_khung_loi_NO_cho_tung_kieu_hong(ghi_de, cum):
    if ghi_de.get("t") == []:
        ghi_de = {"t": [], "o": [], "h": [], "l": [], "c": [], "v": []}
    with pytest.raises(ngk.NguonGiaLoi) as e:
        _khung_loi(**ghi_de)
    assert cum in str(e.value), str(e.value)


def test_thieu_mang_trong_phan_hoi_NO():
    ra = _chuoi_tong_hop()
    del ra["v"]
    with pytest.raises(ngk.NguonGiaLoi, match="thiếu mảng 'v'"):
        ngk._doc_phang(ra)
    with pytest.raises(ngk.NguonGiaLoi, match="code=ERROR"):
        ngk._doc_iboard({"code": "ERROR", "data": {}})
    with pytest.raises(ngk.NguonGiaLoi):
        ngk._doc_phang([1, 2])


def test_so_phien_toi_thieu_la_so_cua_data_quality_va_bi_ep():
    assert ngk.TOI_THIEU_PHIEN == SO_PHIEN_TOI_THIEU
    with pytest.raises(ngk.NguonGiaHetNguon) as e:
        ngk.lay_ohlcv("XYZ", "2026-01-01", "2026-12-31",
                      http=_http_gia({k: _chuoi_tong_hop(19) for k in HOST}), ngu=lambda s: None, dong_ho=lambda: 0.0)
    assert "chỉ 19 phiên < tối thiểu 20" in str(e.value)
    r = ngk.lay_ohlcv("XYZ", "2026-01-01", "2026-12-31", http=_http_gia({"entrade": _chuoi_tong_hop(20)}),
                      ngu=lambda s: None, dong_ho=lambda: 0.0)
    assert len(r.df) == 20


def test_khong_sua_khong_lap_so():
    """Nguồn đưa gì thì ra nấy: giá trị trong khung bằng mảng thô, không làm tròn, không nội suy."""
    ra = _chuoi_tong_hop()
    ra["c"][7] = 21.337
    df = ngk.dung_khung(ngk._doc_phang(ra), dt.date(2026, 1, 1), dt.date(2026, 12, 31))
    assert df["close"].tolist() == ra["c"] and df["volume"].tolist() == ra["v"] and len(df) == 30


# ── 5. mạng ─────────────────────────────────────────────────────────────

def test_user_agent_la_ten_du_an_khong_phai_trinh_duyet():
    ua = ngk.USER_AGENT
    assert ua.startswith("vibe-preview/") and "Siner0808/vibe-stock-analysis" in ua
    for cam in ("Mozilla", "Chrome", "Safari", "AppleWebKit", "Gecko"):
        assert cam not in ua, cam
    ua.encode("ascii")                                  # tiêu đề HTTP: ASCII thuần


class _Tra:
    def __init__(self, ma, ndung=None, loi_json=False):
        self.status_code, self._n, self._l = ma, ndung, loi_json

    def json(self):
        if self._l:
            raise ValueError("không phải JSON")
        return self._n


def _vao_requests(monkeypatch, tra):
    import requests
    ghi = {}

    def get(url, **kw):
        ghi["url"] = url
        ghi.update(kw)
        if isinstance(tra, Exception):
            raise tra
        return tra

    monkeypatch.setattr(requests, "get", get)
    return ghi


def _http_json_that():
    cay = ast.parse((GOC / "nguon_gia_cong_khai.py").read_text(encoding="utf-8"))
    ham = next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == "_http_json")
    ns = {"USER_AGENT": ngk.USER_AGENT, "TIMEOUT_GIAY": ngk.TIMEOUT_GIAY,
          "NguonGiaLoi": ngk.NguonGiaLoi, "_LoiTam": ngk._LoiTam}
    exec(compile(ast.Module([ham], []), "nguon_gia_cong_khai", "exec"), ns)
    return ns["_http_json"]


def test_http_json_gui_UA_that_timeout_30_va_Accept(monkeypatch):
    ghi = _vao_requests(monkeypatch, _Tra(200, {"a": 1}))
    assert _http_json_that()("https://x/y", "*/*") == {"a": 1}
    assert ghi["timeout"] == 30 == ngk.TIMEOUT_GIAY
    assert ghi["headers"] == {"User-Agent": ngk.USER_AGENT, "Accept": "*/*"}


@pytest.mark.parametrize("ma, loai", [(429, ngk._LoiTam), (500, ngk._LoiTam), (503, ngk._LoiTam),
                                      (406, ngk.NguonGiaLoi), (404, ngk.NguonGiaLoi), (403, ngk.NguonGiaLoi)])
def test_http_json_phan_loai_ma_trang_thai(monkeypatch, ma, loai):
    _vao_requests(monkeypatch, _Tra(ma))
    with pytest.raises(ngk.NguonGiaLoi) as e:
        _http_json_that()("https://x")
    assert type(e.value) is loai, (ma, type(e.value))


def test_http_json_loi_mang_la_tam_thoi_va_JSON_hong_la_loi_thang(monkeypatch):
    import requests
    _vao_requests(monkeypatch, requests.exceptions.ConnectTimeout("hết giờ"))
    with pytest.raises(ngk._LoiTam, match="ConnectTimeout"):
        _http_json_that()("https://x")
    _vao_requests(monkeypatch, _Tra(200, loi_json=True))
    with pytest.raises(ngk.NguonGiaLoi, match="không phải JSON") as e:
        _http_json_that()("https://x")
    assert type(e.value) is ngk.NguonGiaLoi


def test_thu_lai_2_lan_co_lui_roi_thanh_cong():
    ngu, lan = [], {"n": 0}

    def http(url, accept="*/*"):
        lan["n"] += 1
        if lan["n"] < 3:
            raise ngk._LoiTam("HTTP 502")
        return {"ok": 1}

    ngk._lan_goi_cuoi[0] = 0.0
    kq = ngk._goi_co_thu_lai("u", "*/*", http, ngu.append, lambda: 100.0, 0.0)
    assert kq == {"ok": 1} and lan["n"] == 3 == ngk.SO_LAN_THU
    assert ngu == list(ngk.LUI_GIAY) == [2.0, 5.0]


def test_thu_lai_het_lan_thi_loi_va_loi_vinh_vien_KHONG_thu_lai():
    lan = {"n": 0}

    def tam(url, accept="*/*"):
        lan["n"] += 1
        raise ngk._LoiTam("HTTP 500")

    ngu = []
    with pytest.raises(ngk.NguonGiaLoi, match="HTTP 500 sau 3 lần thử"):
        ngk._goi_co_thu_lai("u", "*/*", tam, ngu.append, lambda: 0.0, 0.0)
    assert lan["n"] == 3
    assert ngu == [2.0, 5.0], ngu          # không nghỉ thêm SAU lần thất bại cuối trước khi báo lỗi
    lan["n"] = 0

    def vinh_vien(url, accept="*/*"):
        lan["n"] += 1
        raise ngk.NguonGiaLoi("HTTP 406")

    with pytest.raises(ngk.NguonGiaLoi, match="HTTP 406"):
        ngk._goi_co_thu_lai("u", "*/*", vinh_vien, lambda s: None, lambda: 0.0, 0.0)
    assert lan["n"] == 1


def test_nghi_giua_hai_lan_goi_mang():
    """Hai lần gọi sát nhau thì lần sau phải nghỉ phần còn thiếu của `nghi`; đủ rồi thì không nghỉ."""
    ngu = []
    ngk._lan_goi_cuoi[0] = 100.0
    ngk._goi_co_thu_lai("u", "*/*", lambda u, a: {}, ngu.append, lambda: 100.1, 0.3)
    assert ngu == [pytest.approx(0.2)]
    ngu.clear()
    ngk._lan_goi_cuoi[0] = 50.0
    ngk._goi_co_thu_lai("u", "*/*", lambda u, a: {}, ngu.append, lambda: 100.0, 0.3)
    assert ngu == []
    assert ngk.NGHI_GIUA_LAN_GOI_GIAY > 0 and ngk.TIMEOUT_GIAY == 30


def test_VNDirect_xin_Accept_sao_khong_phai_application_json():
    """Đo 11/11/2026: VNDirect trả HTTP 406 nếu `Accept: application/json`."""
    assert ngk.NGUON_VNDIRECT.accept == "*/*"
    http = _http_gia({"vndirect": _pr("fpt_vndirect")})
    ngk.lay_ohlcv("FPT", "2026-11-03", "2026-11-10", toi_thieu=1, chuoi=[ngk.NGUON_VNDIRECT], http=http,
                  ngu=lambda s: None, dong_ho=lambda: 0.0)
    assert http.goi[0][1] == "*/*"
    assert all(n.accept == "*/*" for n in ngk.CHUOI_CO_PHIEU + ngk.CHUOI_CHI_SO)


def test_url_tung_nguon_dung_dang_da_do():
    u = {t: n.url("co_phieu", "FPT", 100, 200) for t, n in NGUON.items()}
    assert u["iboard"] == ("https://iboard-api.ssi.com.vn/statistics/charts/history"
                           "?symbol=FPT&resolution=1D&from=100&to=200")
    assert u["entrade"] == ("https://services.entrade.com.vn/chart-api/v2/ohlcs/stock"
                            "?symbol=FPT&resolution=1D&from=100&to=200")
    assert u["vndirect"] == ("https://dchart-api.vndirect.com.vn/dchart/history"
                             "?symbol=FPT&resolution=D&from=100&to=200")
    assert u["vps"] == ("https://histdatafeed.vps.com.vn/tradingview/history"
                        "?symbol=FPT&resolution=D&from=100&to=200")
    assert "ohlcs/index" in ngk.NGUON_ENTRADE.url("chi_so", "VNINDEX", 1, 2)


# ── 6. nến của ngày đang giao dịch ──────────────────────────────────────

def _chuoi_co_nen_hom_nay():
    """Phản hồi VNDirect THẬT (FPT) cộng THÊM một nến ngày 11/11/2026 TỔNG HỢP, mô phỏng nến dở
    mà iBoard/VNDirect trả giữa phiên."""
    ra = _pr("fpt_vndirect")
    ra["t"].append(int(dt.datetime(2026, 11, 11, tzinfo=dt.timezone.utc).timestamp()))
    for k, v in zip("ochlv", (50.9, 51.0, 51.1, 50.8, 651_400)):
        ra[k].append(v)
    return ra


def test_nen_hom_nay_do_dang_do_den_15h30_roi_moi_dong():
    r = _lay("FPT", "2026-11-03", "2026-11-11", {"entrade": ngk._LoiTam("x"), "vndirect": _chuoi_co_nen_hom_nay()})
    assert str(r.df["time"].iloc[-1].date()) == "2026-11-11"     # module KHÔNG tự cắt nến cuối
    cuoi = r.df["time"].iloc[-1]
    sang = dt.datetime(2026, 11, 11, 9, 50, tzinfo=VN_TZ)
    sat = dt.datetime(2026, 11, 11, GIO_NEN_DA_DONG[0], GIO_NEN_DA_DONG[1] - 1, tzinfo=VN_TZ)
    dung = dt.datetime(2026, 11, 11, GIO_NEN_DA_DONG[0], GIO_NEN_DA_DONG[1], tzinfo=VN_TZ)
    toi = dt.datetime(2026, 11, 11, 17, 5, tzinfo=VN_TZ)
    assert nen_cuoi_dang_do(cuoi, sang) and nen_cuoi_dang_do(cuoi, sat)
    assert not nen_cuoi_dang_do(cuoi, dung) and not nen_cuoi_dang_do(cuoi, toi)
    # Hôm qua luôn đã đóng; nến 'tương lai' luôn dở
    assert not nen_cuoi_dang_do(r.df["time"].iloc[-2], sang)
    assert nen_cuoi_dang_do(cuoi, dt.datetime(2026, 11, 10, 20, 0, tzinfo=VN_TZ))


def test_bo_nen_dang_do_cua_backtest_cat_dung_nen_hom_nay_trong_phien():
    from backtest.data import bo_nen_dang_do
    r = _lay("FPT", "2026-11-03", "2026-11-11", {"entrade": ngk._LoiTam("x"), "vndirect": _chuoi_co_nen_hom_nay()})
    trong_phien = bo_nen_dang_do(r.df, dt.datetime(2026, 11, 11, 10, 0, tzinfo=VN_TZ))
    assert str(trong_phien["time"].iloc[-1].date()) == "2026-11-10" and len(trong_phien) == len(r.df) - 1
    sau_dong_cua = bo_nen_dang_do(r.df, dt.datetime(2026, 11, 11, 16, 0, tzinfo=VN_TZ))
    assert len(sau_dong_cua) == len(r.df)


# ── 7. nối dây ──────────────────────────────────────────────────────────

def test_collect_OK_tra_ten_nguon_va_khung_dung_dang(monkeypatch, ngay_co_dinh):
    import data_collectors as dc
    http = _http_gia({"entrade": _chuoi_tong_hop(60)})
    monkeypatch.setattr(ngk, "_http_json", http)
    monkeypatch.setattr(ngk, "NGHI_GIUA_LAN_GOI_GIAY", 0.0)
    r = dc.VNStockCollectorAgent().collect("FPT", "2026-01-01", "2026-12-31", exchange="HOSE")
    assert r["status"] == "OK" and r["source"] == "entrade" and "ENTRADE" in r["note"]
    assert len(r["df"]) == 60 and str(r["df"]["time"].dtype) == "datetime64[ns]"
    assert list(r["df"].columns) == list(ngk.COT) and r["quality"] is not None


def test_cua_so_vci_cu_la_so_ngay_lam_viec_cong_mot_va_xin_lui_dau_cua_so():
    """Luật đếm của `vnstock` 4.0.9/VCI (quote.py L234-262): countBack = len(bdate_range(start,end)) + 1."""
    start_rong, n = ngk.cua_so_vci_cu("2023-11-12", "2026-11-11")
    assert n == len(pd.bdate_range("2023-11-12", "2026-11-11")) + 1 == 784
    assert start_rong == "2023-06-25"                     # 30 + ceil(1095 / 10) = 140 ngày lùi
    assert start_rong < "2023-11-12"
    assert ngk.cua_so_vci_cu("2026-11-02", "2026-11-11")[1] == 8 + 1 and ngk.cua_so_vci_cu("2026-11-11", "2026-11-01")[1] == 0


def test_collect_GIU_cua_so_784_cua_VCI_cu_khong_phai_746_cua_start(monkeypatch, ngay_co_dinh):
    """KHOÁ hành vi cố ý (BƯỚC 267): `collect` trả 784 nến CUỐI, đầu cửa sổ nằm TRƯỚC `start` như VCI cũ
    (FPT 785 nến từ 2023-09-19 so với 746 nến từ 2023-11-13 khi tôn trọng `start`). "Sửa" về tôn trọng
    `start` đổi điểm 184/1.420 cặp và 2 quyết định qua ngưỡng 62 — test này phải ĐỎ khi ai đó làm vậy."""
    import data_collectors as dc
    monkeypatch.setattr(ngk, "_http_json", _http_gia({"entrade": _chuoi_theo_url}))
    monkeypatch.setattr(ngk, "NGHI_GIUA_LAN_GOI_GIAY", 0.0)
    r = dc.VNStockCollectorAgent().collect("FPT", "2023-11-12", "2026-11-11")
    assert r["status"] == "OK" and len(r["df"]) == 784, len(r["df"])
    assert r["df"]["time"].iloc[0] < pd.Timestamp("2023-11-12"), r["df"]["time"].iloc[0]
    assert str(r["df"]["time"].iloc[-1].date()) == "2026-11-11"
    assert r["df"]["time"].is_monotonic_increasing and str(r["df"]["time"].dtype) == "datetime64[ns]"


def test_collect_cua_so_ngan_va_ma_moi_niem_yet(monkeypatch, ngay_co_dinh):
    import data_collectors as dc
    monkeypatch.setattr(ngk, "_http_json", _http_gia({"entrade": _chuoi_theo_url}))
    monkeypatch.setattr(ngk, "NGHI_GIUA_LAN_GOI_GIAY", 0.0)
    r = dc.VNStockCollectorAgent().collect("FPT", "2026-10-01", "2026-11-11")
    assert len(r["df"]) == len(pd.bdate_range("2026-10-01", "2026-11-11")) + 1
    # mã niêm yết muộn: nguồn chỉ có 60 phiên thì trả 60, không bịa thêm
    monkeypatch.setattr(ngk, "_http_json", _http_gia({"entrade": _chuoi_tong_hop(60)}))
    r = dc.VNStockCollectorAgent().collect("GEL", "2023-11-12", "2026-11-11")
    assert len(r["df"]) == 60


def test_collect_nguon_dau_bi_kiem_dinh_chan_thi_nguon_ke_duoc_dung(monkeypatch, ngay_co_dinh):
    import data_collectors as dc
    hong = _chuoi_tong_hop(60)
    hong["h"] = [x - 1.0 for x in hong["c"]]                 # cao < thấp -> `validate_ohlcv` BLOCK
    monkeypatch.setattr(ngk, "_http_json", _http_gia({"entrade": hong, "vndirect": _chuoi_tong_hop(60)}))
    monkeypatch.setattr(ngk, "NGHI_GIUA_LAN_GOI_GIAY", 0.0)
    r = dc.VNStockCollectorAgent().collect("FPT", "2026-01-01", "2026-12-31")
    assert r["status"] == "OK" and r["source"] == "vndirect"
    assert "đã bỏ: entrade" in r["note"]


def test_collect_het_nguon_la_SYNTHETIC_co_ly_do_khong_bao_gio_OK(monkeypatch):
    import data_collectors as dc
    monkeypatch.setattr(ngk, "_http_json", _http_gia({k: ngk._LoiTam("HTTP 500") for k in HOST}))
    monkeypatch.setattr(ngk, "NGHI_GIUA_LAN_GOI_GIAY", 0.0)
    monkeypatch.setattr(ngk.time, "sleep", lambda s: None)
    r = dc.VNStockCollectorAgent().collect("FPT", "2026-01-01", "2026-12-31")
    assert r["status"] == "SYNTHETIC" and "MÔ PHỎNG NGẪU NHIÊN" in r["note"]
    assert "entrade" in r["note"] and "vndirect" in r["note"] and "vps" in r["note"]


def test_collect_khong_can_vnstock(monkeypatch, ngay_co_dinh):
    """Vắng `vnstock` (CI, Cloud): `collect` vẫn chạy, không nạp gói ấy."""
    import data_collectors as dc
    monkeypatch.setitem(sys.modules, "vnstock", None)         # `import vnstock` -> ImportError
    monkeypatch.setattr(ngk, "_http_json", _http_gia({"entrade": _chuoi_tong_hop(40)}))
    monkeypatch.setattr(ngk, "NGHI_GIUA_LAN_GOI_GIAY", 0.0)
    assert dc.VNStockCollectorAgent().collect("FPT", "2026-01-01", "2026-12-31")["status"] == "OK"


def test_fetch_one_mac_dinh_la_chuoi_co_phieu_hay_chi_so_va_gan_ten_nguon(monkeypatch):
    from backtest import data as bt
    assert bt.NGUON_MAC_DINH_CO_PHIEU == ("entrade", "vndirect", "vps")
    assert bt.NGUON_MAC_DINH_CHI_SO == ("vndirect", "iboard", "vps")
    http = _http_gia({"entrade": _chuoi_tong_hop(30), "vndirect": _chuoi_tong_hop(30)})
    monkeypatch.setattr(ngk, "_http_json", http)
    monkeypatch.setattr(ngk, "NGHI_GIUA_LAN_GOI_GIAY", 0.0)
    df = bt.fetch_one("FPT", "2026-01-01", "2026-12-31", pause=0.0)
    assert df.attrs["nguon"] == "entrade" and len(df) == 30
    df = bt.fetch_one("VNINDEX", "2026-01-01", "2026-12-31", pause=0.0)
    assert df.attrs["nguon"] == "vndirect"


def test_fetch_one_ghim_nguon_la_loi_thang_khong_roi_sang_nguon_khac(monkeypatch):
    from backtest import data as bt
    http = _http_gia({"vps": ngk._LoiTam("HTTP 500"), "vndirect": _chuoi_tong_hop(30)})
    monkeypatch.setattr(ngk, "_http_json", http)
    monkeypatch.setattr(ngk, "NGHI_GIUA_LAN_GOI_GIAY", 0.0)
    monkeypatch.setattr(ngk.time, "sleep", lambda s: None)
    assert bt.fetch_one("FPT", "2026-01-01", "2026-12-31", nguon="vps", pause=0.0) is None
    assert {next(t for t, h in HOST.items() if h in u) for u, _ in http.goi} == {"vps"}
    with pytest.raises(ValueError, match="kbs"):
        bt.fetch_one("FPT", "2026-01-01", "2026-12-31", nguon="kbs")
    df = bt.fetch_one("FPT", "2026-01-01", "2026-12-31", nguon=("vps", "vndirect"), pause=0.0)
    assert df.attrs["nguon"] == "vndirect"


def test_chi_so_moi_nhat_di_qua_chuoi_chi_so_ke_ca_cua_so_ngan(monkeypatch):
    """Ô VN-Index topbar chỉ xin ~36 ngày lịch: số phiên tối thiểu phải theo cửa sổ, không cứng 20."""
    import market_filter as mf
    http = _http_gia({"vndirect": _chuoi_theo_url})
    monkeypatch.setattr(ngk, "_http_json", http)
    monkeypatch.setattr(ngk, "NGHI_GIUA_LAN_GOI_GIAY", 0.0)
    r = mf.chi_so_moi_nhat()
    assert r["loi"] is None and r["nguon"] == "mạng" and r["dong_cua"] is not None and r["phan_tram"] is not None
    assert len(http.goi) == 1


def test_ma_la_vao_URL_nen_chi_nhan_chu_hoa_va_so():
    http = _http_gia({"entrade": _chuoi_tong_hop(30)})
    for xau in ("FPT&x=1", "FPT/../x", "", "A" * 13, "FP T", "FPT?"):
        with pytest.raises(ValueError, match="mã không hợp lệ"):
            ngk.lay_ohlcv(xau, "2026-01-01", "2026-12-31", http=http, ngu=lambda s: None, dong_ho=lambda: 0.0)
    assert http.goi == []
    assert ngk.lay_ohlcv(" fpt ", "2026-01-01", "2026-12-31", http=http, ngu=lambda s: None,
                         dong_ho=lambda: 0.0).df["time"].size == 30


def test_toi_thieu_mac_dinh_theo_cua_so():
    f = ngk.toi_thieu_mac_dinh
    assert f(dt.date(2023, 11, 1), dt.date(2026, 11, 11)) == 20 == ngk.TOI_THIEU_PHIEN   # cửa sổ quét
    assert f(dt.date(2026, 10, 6), dt.date(2026, 11, 11)) == 13                         # topbar: 26 ngày làm việc // 2
    assert f(dt.date(2026, 11, 9), dt.date(2026, 11, 10)) == 2                          # ít nhất 2
    assert f(dt.date(2026, 11, 11), dt.date(2026, 11, 1)) == 2


# ── chỗ KHÔNG có nguồn: nói thẳng "không có nguồn", không số thay thế, không sập ──

def test_khong_co_nguon_cau_chu_chung():
    c = ngk.ly_do_khong_co_nguon("bảng giá")
    assert c.startswith("không có nguồn: bảng giá") and "10/11/2026" in c and "BƯỚC 265" in c


def test_vnstock_vang_nhan_ra_ca_khi_bi_chan(monkeypatch):
    monkeypatch.setitem(sys.modules, "vnstock", None)
    assert ngk.vnstock_vang() is True


def test_bang_gia_vang_vnstock_la_khong_co_nguon_va_khong_suy_tran(monkeypatch):
    import mau_bang_gia as mbg
    monkeypatch.setitem(sys.modules, "vnstock", None)
    r = mbg.doc_bang_gia("SSI")
    assert r["loi"].startswith("không có nguồn")
    assert r["tran"] is None and r["san"] is None and r["tham_chieu"] is None
    # đường lui: không có bảng giá thì NĂM màu tụt xuống BA màu
    m = mbg.mau_cho_phien(21000.0, 20500.0, "2026-11-10", r)
    assert m.ma == mbg.TANG and not m.biet_bien_do and m.tran is None


def test_nen_noi_phien_vang_vnstock_nem_IntradayError_khong_co_nguon(monkeypatch):
    import intraday_data as idd
    monkeypatch.setitem(sys.modules, "vnstock", None)
    monkeypatch.setitem(sys.modules, "vnstock.api", None)
    monkeypatch.setitem(sys.modules, "vnstock.api.quote", None)
    with pytest.raises(idd.IntradayError, match="không có nguồn"):
        idd.tai("ZZZ1", "2026-01-01", "2026-01-31", "30m", dung_cache=False)


def test_bctc_va_khoi_ngoai_vang_vnstock_noi_khong_co_nguon(monkeypatch):
    import financial_collector as fc
    monkeypatch.setitem(sys.modules, "vnstock", None)
    monkeypatch.setitem(sys.modules, "vnstock.api", None)
    monkeypatch.setitem(sys.modules, "vnstock.api.financial", None)
    c = fc.FinancialDataCollector()
    bt = c.get_financial_statements("ZZ267A")
    kn = c.get_foreign_trading_history("ZZ267A")
    assert bt["available"] is False and "không có nguồn" in bt["note"]
    assert kn["available"] is False and "không có nguồn" in kn["note"]
    dg = c._fetch_ratio("ZZ267A")
    assert dg[0] is None and dg[1].startswith("không có nguồn")


def test_co_ban_vang_vnstock_la_khong_co_du_lieu_noi_khong_co_nguon(monkeypatch):
    import fundamental_agent as fa
    monkeypatch.setitem(sys.modules, "vnstock", None)
    monkeypatch.setitem(sys.modules, "vnstock.api", None)
    monkeypatch.setitem(sys.modules, "vnstock.api.financial", None)
    r = fa.doc_chi_so("ZZ267B")
    assert r.co_du_lieu is False and r.ly_do.startswith("không có nguồn")
    # hàm tiêm vào trả None thì giữ câu cũ: câu mới CHỈ cho đường thật
    assert fa.doc_chi_so("ZZ267C", tai_bang=lambda m: None).ly_do.startswith("không lấy được bảng chỉ số")


def test_gac_cam_mang_gia_that_do_conftest():
    """Gác thứ ba của `tests/conftest.py`: gọi `_http_json` thật trong test thì nổ (và ghi vi phạm)."""
    import conftest as cf
    import inspect
    nid = [k for k in cf._VI_PHAM_MANG_GIA] + []
    with pytest.raises(AssertionError, match="gọi MẠNG giá thật"):
        ngk._http_json("https://services.entrade.com.vn/x")
    # gỡ vi phạm vừa cố ý gây, nếu không `pytest_runtest_call` làm đỏ chính test này
    for k in list(cf._VI_PHAM_MANG_GIA):
        if k not in nid:
            cf._VI_PHAM_MANG_GIA.pop(k)
    assert "gac_khong_cham_mang_gia_that" in inspect.getsource(cf)


# ── không module SẢN XUẤT nào sập khi vắng vnstock (AST) ─────────────────

_DUONG_VAO = ("app.py", "run_daily.py")


#: Gói của hãng `vnstock` (đã bị gỡ 10/11/2026). KHÔNG dùng tiền tố `vnstock`: `vnstock_goi` và
#: `vnstock_auth` là module của repo.
GOI_HANG = frozenset({"vnstock", "vnstock_data", "vnstock_ta", "vnstock_news", "vnstock_pipeline",
                      "vnstock_ezchart", "vnai", "vnii"})


def _nhap_vnstock(cay):
    """[(nút Import, [tổ tiên])] của mọi nhập gói của hãng (`GOI_HANG`) trong cây."""
    ra = []

    def duyet(nut, tt):
        for con in ast.iter_child_nodes(nut):
            if isinstance(con, ast.Import) and any(a.name.split(".")[0] in GOI_HANG for a in con.names):
                ra.append((con, tt + [nut]))
            elif isinstance(con, ast.ImportFrom) and (con.module or "").split(".")[0] in GOI_HANG:
                ra.append((con, tt + [nut]))
            duyet(con, tt + [nut])

    duyet(cay, [])
    return ra


def _bat_duoc_import_error(try_nut) -> bool:
    for h in try_nut.handlers:
        if h.type is None:
            return True
        ten = [h.type] if not isinstance(h.type, ast.Tuple) else list(h.type.elts)
        if any(isinstance(t, ast.Name) and t.id in ("Exception", "BaseException", "ImportError",
                                                    "ModuleNotFoundError") for t in ten):
            return True
    return False


def _co_try_che(nut, tt) -> bool:
    for i, a in enumerate(tt):
        if isinstance(a, ast.Try) and _bat_duoc_import_error(a):
            tiep = tt[i + 1] if i + 1 < len(tt) else nut
            if tiep in a.body:                     # nằm trong THÂN try, không phải trong handler/finally
                return True
    return False


def _file_nhap(cay):
    """Module của repo mà cây này nhập (mọi độ sâu): {'ten'} với ten.py ở gốc hoặc thư mục gói."""
    ra = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            ra |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
            ra.add(n.module.split(".")[0])
            ra |= {f"{n.module.split('.')[0]}/{a.name}" for a in n.names}
    return ra


def _module_san_xuat():
    """Mọi module repo mà `app.py`/`run_daily.py` nhập tới (bắc cầu, mọi độ sâu), trừ `tools/` và `tests/`."""
    thay, cho = {}, list(_DUONG_VAO)
    while cho:
        p = cho.pop()
        if p in thay:
            continue
        f = GOC / p
        if not f.exists():
            continue
        thay[p] = ast.parse(f.read_text(encoding="utf-8"))
        for ten in _file_nhap(thay[p]):
            for ung in (f"{ten}.py", f"{ten}/__init__.py", f"{ten.replace('/', '/')}.py"):
                if (GOC / ung).exists() and not ung.startswith(("tools/", "tests/")):
                    cho.append(ung)
    return thay


def test_AST_moi_nhap_vnstock_o_duong_san_xuat_nam_trong_try_bat_ImportError():
    cac = _module_san_xuat()
    assert {"app.py", "run_daily.py", "data_collectors.py", "backtest/data.py", "mau_bang_gia.py",
            "fundamental_agent.py", "intraday_data.py"} <= set(cac), sorted(cac)
    thieu, tong = [], 0
    for ten, cay in sorted(cac.items()):
        for nut, tt in _nhap_vnstock(cay):
            tong += 1
            if not _co_try_che(nut, tt):
                thieu.append(f"{ten}:{nut.lineno}")
    assert tong >= 6, f"chỉ thấy {tong} chỗ nhập gói của hãng — bộ duyệt hỏng?"
    assert not thieu, ("nhập vnstock KHÔNG bọc try bắt ImportError ở đường sản xuất — Cloud/Actions "
                       f"(vắng vnstock) sẽ sập: {thieu}")


def test_AST_duong_gia_khong_nhap_vnstock_nua():
    """`fetch_one` và `collect` — đường giá của quét + app — KHÔNG được nhập `vnstock` lại (BƯỚC 267)."""
    for tep in ("backtest/data.py", "data_collectors.py", "nguon_gia_cong_khai.py", "market_filter.py"):
        cay = ast.parse((GOC / tep).read_text(encoding="utf-8"))
        assert not _nhap_vnstock(cay), f"{tep} lại nhập vnstock: {[(n.lineno) for n, _ in _nhap_vnstock(cay)]}"


def test_AST_nguon_gia_cong_khai_khong_doc_dia_khong_doc_khoa():
    """Luật 5 của module: không đọc/ghi đĩa, không đọc khoá, không dùng vnstock."""
    cay = ast.parse((GOC / "nguon_gia_cong_khai.py").read_text(encoding="utf-8"))
    ten_cam = {"open", "environ", "getenv", "to_csv", "read_csv", "write_text", "read_text", "secrets",
               "st", "streamlit", "toml", "vnstock", "vnai", "os", "pathlib", "Path"}
    thay = sorted({n.id for n in ast.walk(cay) if isinstance(n, ast.Name) and n.id in ten_cam}
                  | {n.attr for n in ast.walk(cay) if isinstance(n, ast.Attribute) and n.attr in ten_cam})
    nhap = sorted({a.name.split(".")[0] for n in ast.walk(cay) if isinstance(n, ast.Import) for a in n.names}
                  | {(n.module or "").split(".")[0] for n in ast.walk(cay) if isinstance(n, ast.ImportFrom)})
    assert not thay, thay
    assert set(nhap) <= {"__future__", "re", "time", "dataclasses", "datetime", "typing", "pandas", "importlib",
                         "requests"}, nhap


def _chuoi_trong_app() -> list[str]:
    """MỌI hằng chuỗi của app.py (kể cả phần chữ của f-string và HTML), đọc bằng AST — không đọc chú thích `#`."""
    cay = ast.parse((GOC / "app.py").read_text(encoding="utf-8"))
    return [n.value for n in ast.walk(cay) if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def test_AST_chu_tren_app_khong_noi_gia_ngay_den_tu_vnstock():
    """BƯỚC 269: caption tab Pipeline v2 từng ghi "giá vnstock → chấm điểm" và chân trang "VNStock + TradingView"
    tới 12/11/2026 — hết đúng từ BƯỚC 267. Caption phải gọi đúng chuỗi nguồn LẤY TỪ `CHUOI_CO_PHIEU`."""
    cac = _chuoi_trong_app()
    assert len(cac) > 200, f"chỉ thấy {len(cac)} hằng chuỗi — bộ duyệt hỏng?"
    cam = (r"giá\s+vnstock", r"vnstock\s*\+\s*tradingview", r"vnstock\s+và\s+tradingview")
    dinh = [(p, s[:70]) for s in cac for p in cam if re.search(p, s, re.IGNORECASE)]
    assert not dinh, f"app.py lại nói giá ngày đến từ vnstock: {dinh}"
    ten_hien = {"entrade": "Entrade", "vndirect": "VNDirect", "vps": "VPS"}
    chuoi = " → ".join(ten_hien[n.ten] for n in ngk.CHUOI_CO_PHIEU)
    assert any(f"giá ngày công khai ({chuoi})" in s for s in cac), \
        f"caption Pipeline v2 không gọi đúng chuỗi nguồn thật ({chuoi})"
