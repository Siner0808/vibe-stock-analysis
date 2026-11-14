"""BƯỚC 277 — ba nguồn tin từng bị ghim 0 bài được vào gói tin.

Người dùng 13/11/2026: *"đồng ý cả 3 đề xuất"* (đề xuất 2 của leader: cho ECB và hai câu Google News
tiếng Việt theo mã vào gói tin, có so gói tin trước/sau). Ba điều khoá ở đây (mỗi điều có đột biến ở
STATE BƯỚC 277, mục D; không có test nào dùng mạng):

1. **ECB đi qua `_doc_feed` như mọi nguồn khác** — không còn bảng giữ kết quả cũ.
2. **Mọi địa chỉ Google News theo mã không có khoảng trắng hay ký tự ngoài ASCII và giải mã lại ra đúng
   câu hỏi** — bắt bằng `requests.get` giả. `_tai_noi_dung` cũng không còn từ chối địa chỉ có khoảng trắng.
3. **Gói tin tức không tới được đường sổ ảo** — bằng AST: mọi nơi gọi `NewsOrchestrator` /
   `collect_and_handoff` / `run_full_analysis` nằm đúng ba chỗ khai ở đây, đường quét không nhập `app`
   hay `top_stocks_screener` (hai chỗ gốc), và `top_stocks_screener` truyền `collect_news=False`.
"""
import ast
import pathlib
import sys
from urllib.parse import parse_qs, urlparse

import pytest

GOC = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))
sys.path.insert(0, str(GOC))

import duyet_repo  # noqa: E402
import news_collectors as nc  # noqa: E402

ECB = "https://www.ecb.europa.eu/rss/press.html"

def _rss(n=3):
    muc = "".join(f'<item><title>Tin {i} tăng trưởng</title><link>https://m.vn/{i}</link>'
                  f'<description>mô tả {i}</description></item>' for i in range(n))
    return f'<?xml version="1.0"?><rss version="2.0"><channel>{muc}</channel></rss>'.encode("utf-8")


class _PhanHoi:
    def __init__(self, noi_dung, url):
        self._nd, self.url = noi_dung, url
        self.headers = {"Content-Type": "application/rss+xml; charset=utf-8"}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def iter_content(self, n):
        yield self._nd


@pytest.fixture(autouse=True)
def _sach_bo_nho():
    nc.xoa_bo_nho_tin()
    yield
    nc.xoa_bo_nho_tin()


def _gia_mang(monkeypatch, so_bai=3):
    dem = []

    def get(url, **k):
        dem.append(url)
        return _PhanHoi(_rss(so_bai), url)
    monkeypatch.setattr(nc.requests, "get", get)
    return dem


# ── 1. ECB như mọi nguồn khác ────────────────────────────────────────────────
def test_ECB_di_qua_doc_feed_va_ra_bai(monkeypatch):
    dem = _gia_mang(monkeypatch, 3)
    kq = nc._fetch_rss(ECB, "ECB", "interest_rate", "international", 4)
    assert dem == [ECB], "ECB phải được tải thật một lần"
    assert [i.source for i in kq] == ["ECB"] * 3 and {i.category for i in kq} == {"interest_rate"}
    assert {i.region for i in kq} == {"international"}


def test_doc_feed_tra_dung_entry_cua_ECB_va_vao_bo_nho_chung(monkeypatch):
    dem = _gia_mang(monkeypatch, 3)
    assert len(nc._doc_feed(ECB)) == 3
    assert len(nc._doc_feed(ECB)) == 3 and dem == [ECB]
    assert ECB in nc._BO_NHO_TIN, "ECB là nguồn không theo mã: phải dùng chung bộ nhớ như nguồn khác"


def test_agent_vi_mo_gom_ECB_cung_cac_nguon_khac(monkeypatch):
    dem = _gia_mang(monkeypatch, 5)
    monkeypatch.setattr(nc.MacroDataAgent, "FEEDS", [
        ("https://cafef.vn/vi-mo-dau-tu.rss", "CafeF Macro", "macro", "domestic"),
        (ECB, "ECB", "interest_rate", "international")])
    kq = nc.MacroDataAgent().collect()
    assert ECB in dem
    # hạn mỗi nguồn của agent vĩ mô là 4 bài; ECB không được ngoại lệ
    assert [i.source for i in kq] == ["CafeF Macro"] * 4 + ["ECB"] * 4


def test_agent_vi_mo_that_van_khai_ECB():
    """Danh sách nguồn KHÔNG đổi ở BƯỚC 277: ECB vẫn nằm trong `MacroDataAgent.FEEDS`."""
    assert (ECB, "ECB", "interest_rate", "international") in nc.MacroDataAgent.FEEDS


def test_khong_con_bang_giu_ket_qua_cu():
    """Không còn tên `NGUON_GIU_KET_QUA_CU` ở mức module (gác bằng AST, không đọc chuỗi)."""
    cay = ast.parse((GOC / "news_collectors.py").read_text(encoding="utf-8"))
    ten = {t.id for n in cay.body if isinstance(n, (ast.Assign, ast.AnnAssign))
           for t in (n.targets if isinstance(n, ast.Assign) else [n.target]) if isinstance(t, ast.Name)}
    assert "NGUON_GIU_KET_QUA_CU" not in ten and not hasattr(nc, "NGUON_GIU_KET_QUA_CU")


# ── 2. Google News theo mã: địa chỉ hợp lệ, giải mã ra đúng câu hỏi ──────────
def _dia_chi_cua_ma(monkeypatch, ma):
    dem = _gia_mang(monkeypatch, 2)
    kq = nc.CompanyNewsAgent().collect(ma)
    return dem, kq


@pytest.mark.parametrize("ma", ["HPG", "SHS", "VCB", "PVS", "A&B"])
def test_moi_dia_chi_google_news_khong_khoang_trang_va_giai_ma_ra_dung_cau_hoi(monkeypatch, ma):
    dem, _ = _dia_chi_cua_ma(monkeypatch, ma)
    assert len(dem) == 3
    for u in dem:
        assert not any(c.isspace() for c in u), u
        assert u.isascii(), u
    cau_vi = [parse_qs(urlparse(u).query)["q"][0] for u in dem if "hl=vi" in u]
    assert cau_vi == [f"{ma} cổ phiếu lợi nhuận", f"{ma} chứng khoán"]
    for u in dem:
        q = parse_qs(urlparse(u).query)
        assert q["hl"] in (["vi"], ["en"]) and q["gl"] == ["VN"] and q["ceid"] in (["VN:vi"], ["VN:en"])
    en = [u for u in dem if "hl=en" in u]
    assert len(en) == 1
    if ma.isalnum():   # địa chỉ tiếng Anh KHÔNG đổi ở BƯỚC 277 (mã thật chỉ có chữ và số)
        assert en[0] == f"https://news.google.com/rss/search?q={ma}+Vietnam+stock&hl=en&gl=VN&ceid=VN:en"


def test_hai_cau_tieng_viet_ra_bai_cung_vung_va_nhan_nhu_cu(monkeypatch):
    """Trước BƯỚC 277 hai câu này luôn 0 bài; nay mỗi câu ra bài, đúng nhãn/vùng/hạn 5 bài."""
    _gia_mang(monkeypatch, 8)
    kq = nc.CompanyNewsAgent().collect("HPG")
    vi = [i for i in kq if i.source == "GoogleNews"]
    en = [i for i in kq if i.source == "GoogleNews-EN"]
    assert len(vi) == 5 + 5 and len(en) == 4
    assert {(i.category, i.region) for i in vi} == {("corporate", "domestic")}
    assert {(i.category, i.region) for i in en} == {("corporate", "international")}


def test_tai_noi_dung_khong_tu_choi_dia_chi_co_khoang_trang(monkeypatch):
    """Bản BƯỚC 275 nổ `ValueError` ở đây để giữ kết quả cũ; nay địa chỉ đi tới `requests` như mọi địa chỉ."""
    dem = _gia_mang(monkeypatch, 2)
    u = "https://m.vn/rss?q=a b"
    nd, _ = nc._tai_noi_dung(u)
    assert nd and dem == [u]
    assert len(nc._fetch_rss(u, "M", "macro", "domestic", 6, False)) == 2


def test_cong_ty_van_khong_vao_bo_nho_chung(monkeypatch):
    _gia_mang(monkeypatch, 2)
    nc.CompanyNewsAgent().collect("HPG")
    assert not nc._BO_NHO_TIN


# ── 3. Phạm vi: gói tin tức không tới đường sổ ảo ────────────────────────────
BO_QUA = {"tests", ".venv", ".tam_test", "__pycache__", "node_modules", "cache", "scratch", "docs"}
TEN_TIN = {"collect_and_handoff", "run_full_analysis", "NewsOrchestrator"}
#: Bốn chỗ gọi duy nhất trong mã nguồn (không tính tests/): (file, hàm bao, tên gọi).
CHO_GOI_KHAI = {
    ("app.py", "<mức module>", "run_full_analysis"),
    ("data_collectors.py", "DataOrchestrator.collect_and_handoff", "NewsOrchestrator"),
    ("master_agent.py", "run_full_analysis", "collect_and_handoff"),
    ("top_stocks_screener.py", "analyze_single_ticker", "run_full_analysis"),
}
DUONG_QUET = ["run_daily", "paper_trading", "paper_runner", "san_dau", "sheets_store"]


def _file_ma_nguon():
    # Duyệt đệ quy PHẢI qua `duyet_repo.duyet` (không `os.walk`): nó bỏ worktree lồng, `.tam_test/` và
    # tệp tạm của test (gác `tests/test_duyet_repo.py`).
    for p in duyet_repo.duyet(GOC, "*.py"):
        phan = p.relative_to(GOC).parts
        if not (set(phan[:-1]) & BO_QUA) and not any(x.startswith(".") for x in phan[:-1]):
            yield p


def _ten_goi(n):
    f = n.func
    return f.id if isinstance(f, ast.Name) else getattr(f, "attr", None)


def _bao_ham(cay):
    ra = {}

    def di(n, ngu):
        for c in ast.iter_child_nodes(n):
            ten = ngu
            if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                ten = (ngu + "." if ngu else "") + c.name
            ra[c] = ten or "<mức module>"
            di(c, ten)
    di(cay, "")
    return ra


@pytest.fixture(scope="module")
def cac_cay():
    return {p: ast.parse(p.read_text(encoding="utf-8")) for p in _file_ma_nguon()}


def _mo_dun_nhap(cay):
    ra = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            ra |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
            ra.add(n.module.split(".")[0])
            ra |= {f"{n.module}.{a.name}".split(".")[0] for a in n.names}
    return ra


def test_chi_ba_cho_goi_gom_tin_va_dung_cho_da_khai(cac_cay):
    thay = []   # danh sách, không phải tập hợp: thêm MỘT lời gọi thứ hai cùng hàm cũng phải đỏ
    for p, cay in cac_cay.items():
        cha = _bao_ham(cay)
        for n in ast.walk(cay):
            if isinstance(n, ast.Call) and _ten_goi(n) in TEN_TIN:
                thay.append((p.relative_to(GOC).as_posix(), cha[n], _ten_goi(n)))
    assert sorted(thay) == sorted(CHO_GOI_KHAI)


def test_cho_goi_run_full_analysis_la_app_hoac_collect_news_False(cac_cay):
    """Ngoài `app.py` (người đọc rồi tự quyết), mọi nơi gọi `run_full_analysis` phải truyền
    `collect_news=False` bằng hằng số."""
    so_goi = 0
    for p, cay in cac_cay.items():
        ten = p.relative_to(GOC).as_posix()
        for n in ast.walk(cay):
            if isinstance(n, ast.Call) and _ten_goi(n) == "run_full_analysis":
                so_goi += 1
                if ten == "app.py":
                    continue
                kw = {k.arg: k.value for k in n.keywords}
                assert isinstance(kw.get("collect_news"), ast.Constant) and kw["collect_news"].value is False, \
                    f"{ten}:{n.lineno}"
    assert so_goi == 2


def test_duong_quet_khong_nhap_hai_goc_cua_chuoi_tin(cac_cay):
    """Bao đóng nhập (mọi mức, kể cả nhập trong hàm) của đường quét/sổ ảo/backtest không chứa `app` hay
    `top_stocks_screener` — hai file duy nhất gọi `run_full_analysis`."""
    ten_file = {p.stem: p for p in cac_cay if p.parent == GOC}
    mo_dau = set(DUONG_QUET)
    for p, cay in cac_cay.items():
        if p.parent == GOC / "backtest":
            mo_dau |= _mo_dun_nhap(cay)
    thay, hang = set(), list(mo_dau)
    while hang:
        t = hang.pop()
        if t in thay or t not in ten_file:
            continue
        thay.add(t)
        hang += _mo_dun_nhap(cac_cay[ten_file[t]])
    assert {"run_daily", "paper_trading", "paper_runner"} <= thay, "bao đóng rỗng: máy đo hỏng"
    assert not ({"app", "top_stocks_screener"} & thay), sorted({"app", "top_stocks_screener"} & thay)


def test_may_do_bao_dong_nhap_thay_mot_duong_that(cac_cay):
    """Máy đo phải thấy được một nhập có thật: `run_daily` nhập `paper_runner` ở mức module."""
    assert "paper_runner" in _mo_dun_nhap(cac_cay[GOC / "run_daily.py"])
    cay = ast.parse("def f():\n    import top_stocks_screener\n")
    assert "top_stocks_screener" in _mo_dun_nhap(cay)
