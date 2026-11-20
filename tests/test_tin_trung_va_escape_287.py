"""BƯỚC 287 — hai lỗi nhỏ của sản phẩm: tin trùng trong gói tin, và lời tranh luận dán thô vào HTML.

1. TIN TRÙNG. Đo thật 20/11/2026 (`vibe_logs_287/do_a_truoc.log`, 6 mã × 200 bài, mạng thật): Google News trả cùng
   một bài cho hai câu hỏi theo mã, nên `collect_and_handoff` đưa bài ấy vào gói hai lần (0–3 bài mỗi mã); mọi
   cặp trùng cùng tiêu đề, cùng đường dẫn, cùng nguồn; không cặp nào cùng tiêu đề khác đường dẫn. Luật bỏ trùng:
   `news_collectors.khoa_trung` (cùng đường dẫn; không có đường dẫn thì cùng tiêu đề đã chuẩn hoá và cùng nguồn),
   chỉ so TRONG MỘT nhóm. Cùng một bài ở nhóm "trong nước" và nhóm ngành (24–27 bài mỗi mã, vì một địa chỉ RSS
   được gắn cho nhiều ngành) KHÔNG bị gộp — mỗi nhóm được chấm điểm riêng, và gộp là đổi cách chấm.
2. ESCAPE. Ô Bull/Bear của app dán `statement` vào HTML (`unsafe_allow_html`). Đo cùng ngày
   (`do_b_truoc.log`): chữ ngoài (tiêu đề tin) KHÔNG tới được phát biểu — tranh luận chỉ đọc sáu trường nhãn đóng
   và số — nhưng 40/560 phát biểu đã mang `&` (chuỗi viết cứng "macro & ngành"), và đường dán là thô.

Không test nào dùng mạng.
"""
import ast
import hashlib
import html
import pathlib
import sys
from html.parser import HTMLParser

import pytest

GOC = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))
sys.path.insert(0, str(GOC))

import news_collectors as nc  # noqa: E402
from news_collectors import NewsItem  # noqa: E402

APP = GOC / "app.py"


# ── dựng ──────────────────────────────────────────────────────────────────
def _tin(tieu_de="T", url="", nguon="S"):
    return NewsItem(title=tieu_de, summary="", source=nguon, category="c", region="domestic", url=url)


def _rss(bai):
    muc = "".join(f"<item><title>{t}</title><link>{u}</link><description>mô tả</description></item>" for t, u in bai)
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


def _gia_mang(monkeypatch):
    """Mạng giả. Mỗi nguồn thường trả bài RIÊNG (đường dẫn theo địa chỉ), bài đầu lặp lại một lần; ba địa chỉ Google News theo mã trả bài A
    ở CẢ BA (đúng hình dạng thật: cùng tiêu đề, cùng đường dẫn), kèm B ở câu 1 và C ở câu 2."""
    def get(url, **k):
        if "news.google.com" in url:
            if "ceid=VN:en" in url:
                bai = [("Tin A", "https://gn/A")]
            elif "nhu%E1%BA%ADn" in url:   # câu 1: "<mã> cổ phiếu lợi nhuận"
                bai = [("Tin A", "https://gn/A"), ("Tin B", "https://gn/B")]
            else:
                bai = [("Tin A", "https://gn/A"), ("Tin C", "https://gn/C")]
        else:
            ma = hashlib.sha1(url.encode()).hexdigest()[:6]
            bai = [(f"Tin {ma} {i}", f"https://m.vn/{ma}/{i}") for i in range(3)]
            bai.append(bai[0])   # bài đầu lặp lại ngay trong nguồn: MỌI nhóm (trong nước, quốc tế, vĩ mô, từng ngành) có bản trùng
        return _PhanHoi(_rss(bai), url)
    monkeypatch.setattr(nc.requests, "get", get)


# ── 1. luật bỏ trùng (hàm thuần) ───────────────────────────────────────────
def test_1a_cung_duong_dan_la_trung_giu_bai_dau_va_thu_tu():
    a, b, c = _tin("a", "https://x/1"), _tin("b", "https://x/2"), _tin("a khác chữ", " https://x/1 ")
    kq, bo = nc.bo_tin_trung([a, b, c])
    assert kq == [a, b] and bo == 1 and kq[0] is a


def test_1b_khong_duong_dan_thi_cung_tieu_de_chuan_hoa_va_cung_nguon_la_trung():
    a = _tin("Giá  Vàng HÔM NAY", "", "CafeF")
    b = _tin("giá vàng hôm nay ", "", "CafeF")
    kq, bo = nc.bo_tin_trung([a, b])
    assert kq == [a] and bo == 1


def test_1c_cung_tieu_de_khac_nguon_khong_duong_dan_khong_trung():
    kq, bo = nc.bo_tin_trung([_tin("Giá vàng", "", "CafeF"), _tin("Giá vàng", "", "VnExpress")])
    assert len(kq) == 2 and bo == 0


def test_1d_cung_tieu_de_khac_duong_dan_khong_trung_hai_bai_bao_khac_nhau():
    kq, bo = nc.bo_tin_trung([_tin("Cổ phiếu VCB", "https://x/1", "S"), _tin("Cổ phiếu VCB", "https://x/2", "S")])
    assert len(kq) == 2 and bo == 0


def test_1e_bai_khong_tieu_de_khong_duong_dan_giu_het_khong_doan():
    kq, bo = nc.bo_tin_trung([_tin("", "", "S"), _tin("", "", "S"), _tin("  ", "", "S")])
    assert len(kq) == 3 and bo == 0


def test_1f_khong_sua_danh_sach_dau_vao():
    vao = [_tin("a", "u"), _tin("a", "u")]
    nc.bo_tin_trung(vao)
    assert len(vao) == 2


# ── 2. collect_and_handoff trên mạng giả có tin trùng ────────────────────────
def _lien_ket(ds):
    return [i.url for i in ds]


def test_2a_goi_tin_khong_con_bai_trung_trong_mot_nhom_va_dem_theo_so_con_lai(monkeypatch):
    _gia_mang(monkeypatch)
    p = nc.NewsOrchestrator("VCB").collect_and_handoff()
    nhom = [p.domestic_news, p.international_news, p.macro_news, *p.sector_news.values()]
    for ds in nhom:
        assert len(_lien_ket(ds)) == len(set(_lien_ket(ds))), "còn hai bài cùng đường dẫn trong một nhóm"
    gn = [i for i in p.domestic_news if i.source.startswith("GoogleNews")]
    assert sorted(i.title for i in gn) == ["Tin A", "Tin B", "Tin C"], "A xuất hiện ở cả ba câu hỏi, chỉ giữ một"
    assert p.total_articles == sum(len(ds) for ds in nhom), "tổng phải đếm SAU khi bỏ trùng"
    assert any(n.startswith("[Trùng]") and "bỏ 0 bài" not in n for n in p.notes), p.notes


def test_2b_cung_mot_bai_o_hai_nhom_khac_nhau_van_o_ca_hai_khong_doi_cach_cham_diem(monkeypatch):
    _gia_mang(monkeypatch)
    p = nc.NewsOrchestrator("VCB").collect_and_handoff()
    dom = set(_lien_ket(p.domestic_news))
    chung = [sec for sec, ds in p.sector_news.items() if dom & set(_lien_ket(ds))]
    assert chung, "bài của nguồn trong nước phải còn ở nhóm ngành chung địa chỉ RSS (gộp chéo nhóm là đổi cách chấm)"


def test_2c_khong_co_tin_trung_thi_khong_them_ghi_chu(monkeypatch):
    def get(url, **k):
        ma = hashlib.sha1(url.encode()).hexdigest()[:6]
        return _PhanHoi(_rss([(f"Tin {ma} {i}", f"https://m.vn/{ma}/{i}") for i in range(2)]), url)
    monkeypatch.setattr(nc.requests, "get", get)
    p = nc.NewsOrchestrator("VCB").collect_and_handoff()
    assert not any(n.startswith("[Trùng]") for n in p.notes)


# ── 3. escape ở ô tranh luận của app ────────────────────────────────────────
class _Thu(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.the, self.chu = [], []

    def handle_starttag(self, tag, attrs):
        self.the.append(tag)

    def handle_data(self, d):
        self.chu.append(d)


def _gan(cay, ten):
    kq = [n for n in ast.walk(cay) if isinstance(n, ast.Assign)
          and any(isinstance(t, ast.Name) and t.id == ten for t in n.targets)]
    assert len(kq) == 1
    return kq[0]


def _dung_o(rounds):
    """Chạy ĐÚNG biểu thức `o_vong_tranh_luan` của app.py (biên dịch từ cây AST)."""
    cay = ast.parse(APP.read_text(encoding="utf-8"))
    phe = eval(compile(ast.Expression(_gan(cay, "_PHE_TRANH_LUAN").value), "app.py", "eval"), {})
    env = {"rounds": rounds, "_PHE_TRANH_LUAN": phe, "symbol": "FPT", "_chua": "X", "_html": html}
    return eval(compile(ast.Expression(_gan(cay, "o_vong_tranh_luan").value), "app.py", "eval"), env)


NHIEM = '<b>BOOM</b> & "so" <script>x()</script> A&B'


def test_3a_phat_bieu_chua_the_hien_ra_la_CHU_khong_thanh_the():
    html_ra = _dung_o([[{"stance": "BULL", "statement": NHIEM}, {"stance": "BEAR", "statement": "<i>y</i>"}]])
    p = _Thu()
    p.feed(html_ra)
    assert set(p.the) == {"div", "span"}, f"phát biểu sinh thẻ lạ: {sorted(set(p.the))}"
    chu = "".join(p.chu)
    assert NHIEM in chu and "<i>y</i>" in chu, "chữ phải hiện nguyên văn như văn bản"
    assert "<script>" not in html_ra and "<b>BOOM" not in html_ra


def test_3b_dau_va_don_cua_chuoi_viet_cung_cung_duoc_thoat_ma_van_hien_dung_chu():
    cau = "📰 Dòng tin tức đang tích cực (POSITIVE 📰🟢) — macro & ngành hỗ trợ tâm lý mua."
    html_ra = _dung_o([[{"stance": "BULL", "statement": cau}]])
    assert "macro &amp; ngành" in html_ra
    p = _Thu()
    p.feed(html_ra)
    assert cau in "".join(p.chu)


def test_3c_thieu_phat_bieu_hoac_None_thi_o_rong_khong_in_None():
    html_ra = _dung_o([[{"stance": "BULL"}, {"stance": "BEAR", "statement": None}]])
    assert "None" not in html_ra


def test_3d_ham_thoat_la_html_escape_cua_app_nhung_vao_o_phat_bieu_bang_AST():
    """Hình dạng: trong khuôn ô, giá trị lấy từ `arg` đi qua một lời gọi `<tên>.escape(...)` của module `html`."""
    cay = ast.parse(APP.read_text(encoding="utf-8"))
    khuon = _gan(cay, "o_vong_tranh_luan").value.values[0].args[0].elt
    gia_tri = [v.value for v in khuon.values if isinstance(v, ast.FormattedValue)
               and any(isinstance(x, ast.Constant) and x.value == "statement" for x in ast.walk(v.value))]
    assert len(gia_tri) == 1, "khuôn ô phải có đúng một chỗ dán `statement`"
    g = gia_tri[0]
    assert isinstance(g, ast.Call) and isinstance(g.func, ast.Attribute) and g.func.attr == "escape"
    nhap = {(a.asname or a.name) for n in ast.walk(cay) if isinstance(n, ast.Import) for a in n.names if a.name == "html"}
    assert isinstance(g.func.value, ast.Name) and g.func.value.id in nhap, "`escape` phải là của module `html`"
