"""BƯỚC 275, lát 1 — tin tức nhanh hơn mà KHÔNG đổi một bài báo hay một điểm.

Bốn điều khoá ở đây (mỗi điều có phép đột biến ở STATE BƯỚC 275, mục D):

1. **Cùng gói tin → cùng bài, cùng điểm.** `tests/du_lieu/tin_rss_vang.json` do MÃ CŨ
   (`feedparser.parse(url)` trực tiếp, commit dbd38af) sinh ra từ mẫu `tin_rss_mau.json`; mã mới tải
   qua `requests` (giả bằng bản mẫu, không mạng) phải ra đúng từng `NewsItem` và đúng đầu ra của
   `NewsSentimentAgent`.
2. **Bộ nhớ chung chỉ cho nguồn KHÔNG theo mã**, có hạn, hỏng thì hạn ngắn hơn, hai luồng cùng một
   địa chỉ chỉ tải một lần.
3. **Hạn thời gian thật**: nguồn nhỏ giọt bị cắt ở `HAN_MOT_NGUON`; một nguồn treo không giữ nhóm.
4. **Đường quét không chạm**: AST — `run_daily`, `paper_runner`, `san_dau`, backtest không nhập
   `news_collectors` và không gọi `collect_and_handoff` / các hàm `load_*_from_google_sheets`.
"""
import ast
import dataclasses
import json
import pathlib
import threading
import time
import types

import pytest

import news_collectors as nc
from news_sentiment_agent import NewsSentimentAgent

GOC = pathlib.Path(__file__).resolve().parent.parent
DU_LIEU = pathlib.Path(__file__).resolve().parent / "du_lieu"


class _PhanHoi:
    """Thay `requests.Response` đủ dùng cho `_tai_noi_dung`."""

    def __init__(self, noi_dung: bytes, url: str, khuc=16384, moi_khuc=None):
        self._nd, self.url, self._khuc, self._moi_khuc = noi_dung, url, khuc, moi_khuc
        self.headers = {"Content-Type": "application/rss+xml; charset=utf-8"}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def iter_content(self, n):
        for i in range(0, len(self._nd), self._khuc):
            if self._moi_khuc:
                self._moi_khuc()
            yield self._nd[i:i + self._khuc]


@pytest.fixture(autouse=True)
def _sach_bo_nho():
    nc.xoa_bo_nho_tin()
    yield
    nc.xoa_bo_nho_tin()


@pytest.fixture
def mau():
    return json.loads((DU_LIEU / "tin_rss_mau.json").read_text(encoding="utf-8"))


@pytest.fixture
def vang():
    return json.loads((DU_LIEU / "tin_rss_vang.json").read_text(encoding="utf-8"))


def _gia_mang(monkeypatch, mau, dem=None, **kw):
    def get(url, **k):
        if dem is not None:
            dem.append(url)
        return _PhanHoi(mau["mau"][url].encode("utf-8"), url, **kw)
    monkeypatch.setattr(nc.requests, "get", get)


# ── 1. cùng gói tin → cùng bài, cùng điểm ────────────────────────────────────
def test_tung_nguon_ra_dung_tung_NewsItem_cua_ma_cu(monkeypatch, mau, vang):
    _gia_mang(monkeypatch, mau)
    assert set(vang["tung_nguon"]) == {"|".join(map(str, v)) for v in mau["viec"]}
    for url, src, cat, reg, mx in mau["viec"]:
        ra = [dataclasses.asdict(i) for i in nc._fetch_rss(url, src, cat, reg, mx)]
        assert ra == vang["tung_nguon"][f"{url}|{src}|{cat}|{reg}|{mx}"], url


def test_cung_goi_tin_cung_dau_ra_NewsSentimentAgent(monkeypatch, mau, vang):
    """Điểm là hàm của gói tin: dựng gói từ mã MỚI trên mẫu, so với đầu ra mã CŨ đã ghi."""
    _gia_mang(monkeypatch, mau)
    ks = [f"{u}|{s}|{c}|{r}|{m}" for u, s, c, r, m in mau["viec"]]
    tu = lambda i: nc._fetch_rss(*mau["viec"][i])
    goi = nc.NewsPacket(symbol="TST", timestamp="2026-11-13T10:00:00+07:00")
    goi.domestic_news = tu(0) + tu(3) + tu(4)
    goi.international_news = tu(1)
    goi.macro_news = tu(0)[:2]
    goi.sector_news = {"banking": tu(2), "global_macro": tu(1)}
    goi.total_articles = (len(goi.domestic_news) + len(goi.international_news) + len(goi.macro_news)
                          + sum(len(v) for v in goi.sector_news.values()))
    goi.status = "OK"
    dau_ra = json.loads(json.dumps(NewsSentimentAgent().analyze(goi), default=str, ensure_ascii=False))
    assert dau_ra == vang["dau_ra_sentiment"]
    assert len(ks) == 5 and goi.total_articles > 10


def test_thu_tu_ket_qua_theo_thu_tu_khai_khong_theo_thu_tu_ve(monkeypatch, mau):
    """Bản cũ `extend` theo `as_completed` (thứ tự về); nay theo thứ tự khai — nguồn về trễ nhất
    vẫn đứng đúng chỗ của nó."""
    vao = []
    def ham(i, ngu):
        time.sleep(ngu)
        vao.append(i)
        return [i]
    kq = nc._gom_song_song([(ham, 0, 0.3), (ham, 1, 0.0), (ham, 2, 0.1)], han=5)
    assert kq == [[0], [1], [2]] and vao[0] == 1


def test_bang_ma_trong_tieu_de_phan_hoi_van_duoc_dung(monkeypatch):
    """Mẫu không khai mã trong XML, chỉ khai ở tiêu đề `Content-Type`: `feedparser.parse(url)` cũ đọc
    tiêu đề đó; tải byte rồi `parse(byte)` phải truyền nó theo (`response_headers`), không thì "Ł" thành "£"."""
    xml = ('<?xml version="1.0"?><rss version="2.0"><channel><item><title>Łódź</title>'
           '<link>https://m.vn/1</link></item></channel></rss>').encode("iso-8859-2")
    class P(_PhanHoi):
        def __init__(s, *a, **k):
            super().__init__(*a, **k)
            s.headers = {"Content-Type": "application/rss+xml; charset=iso-8859-2"}
    monkeypatch.setattr(nc.requests, "get", lambda url, **k: P(xml, url))
    kq = nc._fetch_rss("https://m.vn/x.rss", "M", "macro", "domestic")
    assert [i.title for i in kq] == ["Łódź"]


def test_cac_agent_gom_dung_nhan_nhom_va_so_bai(monkeypatch, mau):
    """Đi qua cả `collect()` của bốn agent và `collect_and_handoff`: nhãn ngành, nguồn, vùng, hạn
    `max_items` mỗi agent (6/5/4/4) và việc cùng một địa chỉ ở nhiều ngành chỉ tải một lần."""
    dem = []
    u_vn, u_en, u_vn2, u_rong, u_rac = [v[0] for v in mau["viec"]]
    def get(url, **k):
        dem.append(url)
        return _PhanHoi(mau["mau"].get(url, mau["mau"][u_rong]).encode("utf-8"), url)
    monkeypatch.setattr(nc.requests, "get", get)
    monkeypatch.setattr(nc.DomesticNewsAgent, "FEEDS", [(u_vn, "VN", "macro", "domestic"), (u_vn2, "VN2", "corporate", "domestic")])
    monkeypatch.setattr(nc.InternationalNewsAgent, "FEEDS", [(u_en, "EN", "macro", "international")])
    monkeypatch.setattr(nc.MacroDataAgent, "FEEDS", [(u_vn, "VNM", "policy", "domestic")])
    monkeypatch.setattr(nc.SectorNewsAgent, "SECTOR_FEEDS",
                        {"banking": [(u_vn, "VN", "domestic"), (u_en, "EN", "international")],
                         "oil_gas": [(u_vn, "VN", "domestic")], "crypto_blockchain": [(u_rac, "R", "domestic")]})
    p = nc.NewsOrchestrator("hpg").collect_and_handoff()
    assert p.symbol == "HPG"
    assert [(i.source, i.category) for i in p.domestic_news][:1] == [("VN", "macro")]
    assert len(p.domestic_news) == 6 + 6          # VN (6) + VN2 (6); Google News không có trong mẫu -> 0
    assert len(p.international_news) == 3
    assert len(p.macro_news) == 4 and {i.category for i in p.macro_news} == {"policy"}
    assert {k: len(v) for k, v in p.sector_news.items()} == {"banking": 4 + 3, "oil_gas": 4, "crypto_blockchain": 0}
    assert {i.category for i in p.sector_news["banking"]} == {"banking"}
    assert p.total_articles == 12 + 3 + 4 + 7 + 4 and p.status == "OK"
    assert dem.count(u_vn) == 1                    # 4 chỗ dùng, MỘT lần tải


# ── 2. bộ nhớ chung ──────────────────────────────────────────────────────────
def test_lan_hai_trong_han_khong_goi_mang(monkeypatch, mau):
    dem = []
    _gia_mang(monkeypatch, mau, dem)
    u = mau["viec"][0][0]
    a = nc._fetch_rss(*mau["viec"][0])
    b = nc._fetch_rss(*mau["viec"][0])
    assert len(dem) == 1 and a == b and len(a) == 6


def test_cung_dia_chi_khac_nhan_dung_chung_mot_lan_tai(monkeypatch, mau):
    dem = []
    _gia_mang(monkeypatch, mau, dem)
    u = mau["viec"][0][0]
    a = nc._fetch_rss(u, "A", "macro", "domestic", 6)
    b = nc._fetch_rss(u, "B", "banking", "domestic", 2)
    assert len(dem) == 1
    assert [i.source for i in a] == ["A"] * 6 and [i.source for i in b] == ["B"] * 2
    assert [i.category for i in b] == ["banking"] * 2


def test_het_han_thi_tai_lai(monkeypatch, mau):
    dem, gio = [], [1000.0]
    monkeypatch.setattr(nc, "time", types.SimpleNamespace(monotonic=lambda: gio[0]))
    _gia_mang(monkeypatch, mau, dem)
    u = mau["viec"][0]
    nc._fetch_rss(*u)
    gio[0] += nc.TTL_BO_NHO_TIN - 1
    nc._fetch_rss(*u)
    assert len(dem) == 1
    gio[0] += 2
    nc._fetch_rss(*u)
    assert len(dem) == 2


def test_nguon_hong_hoac_rong_giu_ngan_hon_nguon_tot(monkeypatch, mau):
    assert nc.TTL_BO_NHO_LOI < nc.TTL_BO_NHO_TIN
    dem, gio = [], [1000.0]
    monkeypatch.setattr(nc, "time", types.SimpleNamespace(monotonic=lambda: gio[0]))
    _gia_mang(monkeypatch, mau, dem)
    rong = mau["viec"][3]
    assert nc._fetch_rss(*rong) == []
    gio[0] += nc.TTL_BO_NHO_LOI - 1
    nc._fetch_rss(*rong)
    assert len(dem) == 1
    gio[0] += 2
    nc._fetch_rss(*rong)
    assert len(dem) == 2


def test_nguon_theo_ma_khong_vao_bo_nho_chung(monkeypatch, mau):
    dem = []
    _gia_mang(monkeypatch, mau, dem)
    u = mau["viec"][0]
    nc._fetch_rss(*u, dung_bo_nho=False)
    nc._fetch_rss(*u, dung_bo_nho=False)
    assert len(dem) == 2 and not nc._BO_NHO_TIN


def test_tin_cong_ty_goi_dung_bo_nho_tat(monkeypatch):
    """`CompanyNewsAgent` phải truyền `dung_bo_nho=False` cho CẢ ba địa chỉ theo mã (AST)."""
    cay = ast.parse((GOC / "news_collectors.py").read_text(encoding="utf-8"))
    lop = next(n for n in cay.body if isinstance(n, ast.ClassDef) and n.name == "CompanyNewsAgent")
    cac_viec = [n for n in ast.walk(lop) if isinstance(n, (ast.Tuple, ast.List)) and n.elts
                and isinstance(n.elts[0], ast.Name) and n.elts[0].id == "_fetch_rss"]
    assert len(cac_viec) >= 1
    for t in cac_viec:
        assert isinstance(t.elts[-1], ast.Constant) and t.elts[-1].value is False


def test_hai_luong_cung_dia_chi_chi_tai_mot_lan(monkeypatch, mau):
    dem = []
    cho = threading.Event()

    def get(url, **k):
        dem.append(url)
        cho.wait(0.3)
        return _PhanHoi(mau["mau"][url].encode("utf-8"), url)

    monkeypatch.setattr(nc.requests, "get", get)
    u = mau["viec"][0]
    kq = nc._gom_song_song([(nc._fetch_rss, *u), (nc._fetch_rss, *u), (nc._fetch_rss, *u)], han=5)
    assert len(dem) == 1 and kq[0] == kq[1] == kq[2] and len(kq[0]) == 6


def test_phat_hanh_giu_nguyen_ket_qua_cu_cho_dia_chi_con_khoang_trang_va_ECB(monkeypatch, mau):
    """Hai chỗ mã MỚI sẽ tải được mà mã CŨ luôn trả 0 bài (STATE BƯỚC 275 mục B). Giữ 0 bài cho
    tới khi người dùng quyết định, và đừng gọi mạng vô ích."""
    dem = []
    _gia_mang(monkeypatch, mau, dem)
    ecb = next(iter(nc.NGUON_GIU_KET_QUA_CU))
    assert ecb == "https://www.ecb.europa.eu/rss/press.html"
    assert nc._fetch_rss(ecb, "ECB", "interest_rate", "international", 4) == []
    goc = "https://news.google.com/rss/search?q=HPG cổ phiếu lợi nhuận&hl=vi&gl=VN&ceid=VN:vi"
    assert nc._fetch_rss(goc, "GoogleNews", "corporate", "domestic", 5, False) == []
    assert dem == []


# ── 3. hạn thời gian thật ────────────────────────────────────────────────────
def test_nguon_nho_giot_bi_cat_o_han_mot_nguon(monkeypatch, mau):
    """Mỗi khúc về đều 'kịp' (không socket nào quá hạn) nhưng cộng lại quá `HAN_MOT_NGUON`."""
    gio = [0.0]
    monkeypatch.setattr(nc, "time", types.SimpleNamespace(monotonic=lambda: gio[0]))
    def get(url, **k):
        assert k["timeout"] == (nc.HAN_KET_NOI, nc.HAN_DOC) and k["stream"] is True
        return _PhanHoi(b"x" * 100_000, url, khuc=1000, moi_khuc=lambda: gio.__setitem__(0, gio[0] + 0.5))
    monkeypatch.setattr(nc.requests, "get", get)
    with pytest.raises(TimeoutError):
        nc._tai_noi_dung("https://cham.vn/rss")
    assert gio[0] <= nc.HAN_MOT_NGUON + 0.5 + 1e-9
    assert nc._fetch_rss("https://cham.vn/rss", "C", "macro", "domestic") == []


def test_nguon_qua_to_bi_cat(monkeypatch):
    monkeypatch.setattr(nc, "TRAN_BYTE_MOT_NGUON", 1000)
    monkeypatch.setattr(nc.requests, "get", lambda url, **k: _PhanHoi(b"x" * 5000, url, khuc=500))
    with pytest.raises(ValueError):
        nc._tai_noi_dung("https://to.vn/rss")


def test_mot_nguon_treo_khong_giu_ca_nhom():
    """Bản cũ: `with ThreadPoolExecutor` đợi tới cùng (mof.gov.vn: 63 giây một lượt). Nay nhóm thoát
    ở `han` và nguồn tốt vẫn có kết quả."""
    cho = threading.Event()
    t0 = time.perf_counter()
    kq = nc._gom_song_song([(lambda: [1],), (cho.wait, 6.0), (lambda: [3],)], han=0.4)
    dt = time.perf_counter() - t0
    cho.set()
    assert dt < 3.0, dt
    assert kq[0] == [1] and kq[2] == [3] and kq[1] is None


def test_viec_nem_loi_thanh_None_khong_lam_hong_nhom():
    def hong():
        raise RuntimeError("x")
    assert nc._gom_song_song([(hong,), (lambda: 7,)], han=5) == [None, 7]


def test_han_nhom_lon_hon_tran_xau_nhat_cua_mot_nguon():
    assert nc.HAN_NHOM > nc.HAN_MOT_NGUON + nc.HAN_DOC


# ── 4. đường quét không chạm ────────────────────────────────────────────────
DUONG_QUET = ["run_daily.py", "paper_runner.py", "san_dau.py", "paper_trading.py", "sheets_store.py"]
TEN_CAM = {"NewsOrchestrator", "collect_and_handoff", "load_nhat_ky_from_google_sheets",
           "load_so_ban_tin_from_google_sheets", "load_ke_hoach_from_google_sheets"}


def _file_duong_quet():
    ra = [GOC / f for f in DUONG_QUET]
    ra += sorted((GOC / "backtest").glob("*.py"))
    return [p for p in ra if p.exists()]


def test_duong_quet_khong_nhap_tin_tuc_va_khong_goi_loader_sheets_cua_app():
    assert len(_file_duong_quet()) >= 5
    for p in _file_duong_quet():
        cay = ast.parse(p.read_text(encoding="utf-8"))
        for n in ast.walk(cay):
            if isinstance(n, ast.ImportFrom) and n.module in ("news_collectors", "news_sentiment_agent"):
                pytest.fail(f"{p.name}:{n.lineno} nhập {n.module}")
            if isinstance(n, ast.Import) and any(a.name in ("news_collectors", "news_sentiment_agent") for a in n.names):
                pytest.fail(f"{p.name}:{n.lineno} nhập news_collectors")
            if isinstance(n, ast.Call):
                f = n.func
                ten = f.id if isinstance(f, ast.Name) else getattr(f, "attr", None)
                assert ten not in TEN_CAM, f"{p.name}:{n.lineno} gọi {ten}"


def test_DataOrchestrator_trong_duong_quet_khong_gom_tin():
    """`paper_runner` và `san_dau` dựng `DataOrchestrator` chỉ để `_compute_local_indicators`; không
    bao giờ gọi `collect_and_handoff` (test trên) — và gói tin của chúng mang `news_packet=None`."""
    for f in ("paper_runner.py", "san_dau.py"):
        cay = ast.parse((GOC / f).read_text(encoding="utf-8"))
        goi = {getattr(n.func, "attr", getattr(n.func, "id", None)) for n in ast.walk(cay) if isinstance(n, ast.Call)}
        assert "collect_and_handoff" not in goi
        assert "_compute_local_indicators" in goi
