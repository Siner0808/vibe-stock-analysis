"""BƯỚC 278 — gác công cụ chẩn đoán nguồn tin (`tools/chan_doan_nguon_tin.py`). Không có test nào dùng mạng.

Điều khoá: (1) danh sách nguồn ĐỌC từ mã, khớp với AST của `news_collectors.py` và công cụ không gõ lại URL;
(2) `tai_mot` tải đúng như sản xuất (tiêu đề, hạn) và ghi lại mã trạng thái + chuỗi chuyển hướng; (3) mỗi địa chỉ
chỉ tải một lần, thử thêm User-Agent trình duyệt CHỈ cho `blocked`/`dead_url`; (4) đánh dấu trùng; (5) mã sản xuất
không đổi (`news_collectors.py` không nhập công cụ; việc `git diff` rỗng nằm ở STATE).
"""
import ast
import pathlib
import sys

import pytest

GOC = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))
sys.path.insert(0, str(GOC))

import chan_doan_nguon_tin as cd  # noqa: E402
import news_collectors as nc  # noqa: E402
from phan_loai_nguon_tin import QuanSat  # noqa: E402

RSS = (b'<?xml version="1.0"?><rss version="2.0"><channel><item><title>a</title><link>https://m.vn/1</link>'
       b'</item><item><title>b</title><link>https://m.vn/2</link></item></channel></rss>')


class _Lich:
    def __init__(self, status=200, than=RSS, url=None, history=(), headers=None, nem=None):
        self.status_code, self._than, self.url = status, than, url
        self.history = [type("H", (), {"status_code": s})() for s in history]
        self.headers = headers or {"Content-Type": "application/rss+xml"}
        self._nem = nem

    def __enter__(self):
        if self._nem:
            raise self._nem
        return self

    def __exit__(self, *a):
        return False

    def iter_content(self, n):
        yield self._than


def _gia(monkeypatch, ra):
    """`ra(url, headers, timeout)` -> _Lich; ghi lại mọi lời gọi."""
    goi = []

    def get(url, **k):
        goi.append((url, k))
        p = ra(url, k)
        if p.url is None:
            p.url = url
        return p
    monkeypatch.setattr(cd.requests, "get", get)
    return goi


# ── 1. danh sách đọc từ mã ──────────────────────────────────────────────────
def _tu_ast_dem_nguon():
    """Đếm nguồn khai trong `news_collectors.py` bằng AST, độc lập với việc nhập mô-đun."""
    cay = ast.parse((GOC / "news_collectors.py").read_text(encoding="utf-8"))
    tong = 0
    for cls in (n for n in cay.body if isinstance(n, ast.ClassDef)):
        for st in cls.body:
            tgt = st.targets[0] if isinstance(st, ast.Assign) else getattr(st, "target", None)
            ten = getattr(tgt, "id", None)
            if ten == "FEEDS" and isinstance(st.value, ast.List):
                tong += len(st.value.elts)
            elif ten == "SECTOR_FEEDS" and isinstance(st.value, ast.Dict):
                tong += sum(len(v.elts) for v in st.value.values)
    return tong


def test_so_nguon_doc_ra_bang_so_khai_trong_ma_theo_AST():
    n = cd.doc_danh_sach_nguon()
    assert len(n) == _tu_ast_dem_nguon() > 0
    assert {d["nhom"] for d in n} == {"Domestic", "International", "Macro", "Sector"}


def test_moi_url_doc_ra_nam_trong_mot_agent():
    """Không URL nào do công cụ bịa: mỗi cái có thật trong một danh sách của `news_collectors`."""
    co = {f[0] for a in (nc.DomesticNewsAgent, nc.InternationalNewsAgent, nc.MacroDataAgent) for f in a.FEEDS}
    co |= {f[0] for fs in nc.SectorNewsAgent.SECTOR_FEEDS.values() for f in fs}
    assert {d["url"] for d in cd.doc_danh_sach_nguon()} == co


def test_doc_danh_sach_dung_khi_mã_nguon_doi(monkeypatch):
    """Đổi danh sách trong mã thì công cụ đổi theo (không chép tay)."""
    monkeypatch.setattr(nc.MacroDataAgent, "FEEDS", [("https://x.vn/a.rss", "X", "macro", "domestic")])
    assert [d for d in cd.doc_danh_sach_nguon() if d["nhom"] == "Macro"] == [
        {"nhom": "Macro", "url": "https://x.vn/a.rss", "nguon": "X", "the_loai": "macro"}]


def test_cong_cu_khong_go_lai_URL_nao():
    """Không hằng chuỗi nào chứa `://` trong công cụ (trừ chuỗi đơn "http"/"https" làm tên lược đồ)."""
    cay = ast.parse((GOC / "tools" / "chan_doan_nguon_tin.py").read_text(encoding="utf-8"))
    xau = [n.value for n in ast.walk(cay) if isinstance(n, ast.Constant) and isinstance(n.value, str)
           and "://" in n.value]
    assert xau == []


@pytest.mark.parametrize("ma", ["HPG", "VCB"])
def test_dia_chi_google_news_bat_tu_ma_va_khong_goi_mang(monkeypatch, ma):
    def cam(*a, **k):
        raise AssertionError("không được gọi mạng")
    monkeypatch.setattr(cd.requests, "get", cam)
    monkeypatch.setattr(nc.requests, "get", cam)
    u = cd.dia_chi_google_news(ma)
    assert len(u) == 3 and all("news.google.com" in x and ma in x for x in u)
    assert not any(c.isspace() for x in u for c in x)
    assert nc._gom_song_song.__name__ == "_gom_song_song", "phải trả lại hàm gốc sau khi bắt"


def test_bat_dia_chi_google_news_khoi_phuc_ham_goc_ca_khi_collect_no(monkeypatch):
    goc = nc._gom_song_song
    monkeypatch.setattr(nc.CompanyNewsAgent, "collect", lambda self, s: (_ for _ in ()).throw(RuntimeError("x")))
    with pytest.raises(RuntimeError):
        cd.dia_chi_google_news("HPG")
    assert nc._gom_song_song is goc


# ── 2. tai_mot ──────────────────────────────────────────────────────────────
def test_tai_mot_dung_tieu_de_va_han_cua_san_xuat(monkeypatch):
    goi = _gia(monkeypatch, lambda u, k: _Lich())
    cd.tai_mot("https://m.vn/a.rss")
    (_, k), = goi
    assert k["headers"] is nc._HEADERS_RSS and k["stream"] is True
    assert k["timeout"] == (nc.HAN_KET_NOI, nc.HAN_DOC)


def test_tai_mot_ghi_status_chuyen_huong_va_bai(monkeypatch):
    _gia(monkeypatch, lambda u, k: _Lich(url="https://m.vn/final.rss", history=(301, 302)))
    q, them = cd.tai_mot("https://m.vn/a.rss")
    assert (q.status, q.url_cuoi, q.chuyen_huong, q.n_bai, q.n_byte) == (200, "https://m.vn/final.rss", (301, 302), 2, len(RSS))
    assert q.phien_ban == "rss20" and q.bozo == 0 and them["loi"] == ""


def test_tai_mot_404_van_phan_tich_than_nhu_san_xuat(monkeypatch):
    """Sản xuất không kiểm status; công cụ ghi status 404 và vẫn đếm bài như sản xuất sẽ thấy."""
    _gia(monkeypatch, lambda u, k: _Lich(status=404, than=RSS))
    q, _ = cd.tai_mot("https://m.vn/a.rss")
    assert q.status == 404 and q.n_bai == 2


def test_tai_mot_loi_ket_noi_thanh_chuoi_MRO(monkeypatch):
    class ConnectionError_(Exception):
        pass
    ConnectionError_.__name__ = "ConnectionError"
    _gia(monkeypatch, lambda u, k: _Lich(nem=ConnectionError_("Max retries exceeded")))
    q, them = cd.tai_mot("https://m.vn/a.rss")
    assert "ConnectionError" in q.chuoi_loi and "Exception" not in q.chuoi_loi and them["loi"] == "ConnectionError"
    assert q.status is None and "Max retries" in them["thong_diep_loi"]


def test_tai_mot_qua_tran_byte_la_loi_khac(monkeypatch):
    monkeypatch.setattr(nc, "TRAN_BYTE_MOT_NGUON", 10)
    _gia(monkeypatch, lambda u, k: _Lich())
    q, _ = cd.tai_mot("https://m.vn/a.rss")
    assert q.chuoi_loi == ("ValueError",)


def test_tai_mot_cf_mitigated_va_dau_than(monkeypatch):
    _gia(monkeypatch, lambda u, k: _Lich(status=403, than=b"<html>chan", headers={"Content-Type": "text/html", "cf-mitigated": "challenge"}))
    q, _ = cd.tai_mot("https://m.vn/a.rss")
    assert q.cf_chan is True and q.dau_than == "<html>chan"


def test_tai_mot_dung_headers_trinh_duyet_khi_duoc_dua(monkeypatch):
    goi = _gia(monkeypatch, lambda u, k: _Lich())
    cd.tai_mot("https://m.vn/a.rss", nc.HEADERS)
    assert goi[0][1]["headers"] is nc.HEADERS


# ── 3. chạy hết ─────────────────────────────────────────────────────────────
def _nguon(*urls):
    return [{"nhom": "T", "url": u, "nguon": "S", "the_loai": "c"} for u in urls]


def test_moi_dia_chi_tai_dung_mot_lan_ke_ca_khai_lap(monkeypatch):
    goi = _gia(monkeypatch, lambda u, k: _Lich())
    dong = cd.chay_het(_nguon("https://m.vn/a.rss", "https://m.vn/b.rss", "https://m.vn/a.rss"), nghi=0)
    assert [g[0] for g in goi] == ["https://m.vn/a.rss", "https://m.vn/b.rss"]
    assert len(dong) == 3 and [d["so_lan_khai"] for d in dong] == [2, 1, 2]


def test_chi_blocked_va_dead_url_duoc_thu_them_ua_trinh_duyet(monkeypatch):
    def ra(u, k):
        if u.endswith("chan.rss"):
            return _Lich(status=403, than=b"x") if k["headers"] is nc._HEADERS_RSS else _Lich()
        if u.endswith("chet.rss"):
            return _Lich(status=404, than=b"x")
        if u.endswith("rong.rss"):
            return _Lich(than=b'<?xml version="1.0"?><rss version="2.0"><channel></channel></rss>')
        return _Lich()
    goi = _gia(monkeypatch, ra)
    dong = cd.chay_het(_nguon("https://m.vn/ok.rss", "https://m.vn/chan.rss", "https://m.vn/chet.rss",
                              "https://m.vn/rong.rss"), nghi=0)
    theo = {d["url"].rsplit("/", 1)[1]: d for d in dong}
    assert {k: v["lop"] for k, v in theo.items()} == {"ok.rss": "ok", "chan.rss": "blocked",
                                                       "chet.rss": "dead_url", "rong.rss": "empty_feed"}
    assert theo["chan.rss"]["lop_ua_trinh_duyet"] == "ok" and theo["chan.rss"]["n_bai_ua_trinh_duyet"] == 2
    assert theo["chet.rss"]["lop_ua_trinh_duyet"] == "dead_url"
    assert theo["ok.rss"]["lop_ua_trinh_duyet"] == "" and theo["rong.rss"]["lop_ua_trinh_duyet"] == ""
    them = [g for g in goi if g[1]["headers"] is nc.HEADERS]
    assert sorted(g[0].rsplit("/", 1)[1] for g in them) == ["chan.rss", "chet.rss"], "chỉ hai nguồn được thử thêm"
    assert len(goi) == 6


def test_khong_thu_ua_khi_tat(monkeypatch):
    goi = _gia(monkeypatch, lambda u, k: _Lich(status=404, than=b"x"))
    cd.chay_het(_nguon("https://m.vn/a.rss"), nghi=0, thu_ua=False)
    assert len(goi) == 1


# ── 4. đánh dấu trùng & đếm ─────────────────────────────────────────────────
def test_trung_dia_chi_cuoi_giua_hai_dia_chi_khai_khac_nhau(monkeypatch):
    _gia(monkeypatch, lambda u, k: _Lich(url="https://m.vn/chung.rss") if "a.rss" in u or "b.rss" in u else _Lich())
    dong = cd.chay_het(_nguon("https://m.vn/a.rss", "https://m.vn/b.rss", "https://m.vn/c.rss"), nghi=0)
    assert [d["khoa_trung"] for d in dong] == ["https://m.vn/chung.rss"] * 2 + [""]


def test_khai_lap_cung_mot_url_khong_tu_thanh_trung_cuoi(monkeypatch):
    """Một địa chỉ khai hai lần là `so_lan_khai` = 2, KHÔNG phải hai địa chỉ khác nhau cùng đích."""
    _gia(monkeypatch, lambda u, k: _Lich())
    dong = cd.chay_het(_nguon("https://m.vn/a.rss", "https://m.vn/a.rss"), nghi=0)
    assert [d["khoa_trung"] for d in dong] == ["", ""] and dong[0]["so_lan_khai"] == 2


def test_trung_chi_tinh_khi_tai_duoc_2xx(monkeypatch):
    """Hai địa chỉ cùng chuyển về một trang 404 không phải là "trùng feed"."""
    _gia(monkeypatch, lambda u, k: _Lich(status=404, url="https://m.vn/loi"))
    dong = cd.chay_het(_nguon("https://m.vn/a.rss", "https://m.vn/b.rss"), nghi=0, thu_ua=False)
    assert [d["khoa_trung"] for d in dong] == ["", ""]


def test_dem_lop_theo_khai_va_theo_duy_nhat():
    dong = [{"url": "a", "lop": "ok"}, {"url": "a", "lop": "ok"}, {"url": "b", "lop": "dead_url"}]
    theo_khai, duy_nhat = cd.dem_lop(dong)
    assert dict(theo_khai) == {"ok": 2, "dead_url": 1} and dict(duy_nhat) == {"ok": 1, "dead_url": 1}


def test_viet_bang_ghi_csv_va_dem_lop_du_cot_va_dung_thu_muc(tmp_path, monkeypatch):
    _gia(monkeypatch, lambda u, k: _Lich())
    dong = cd.chay_het(_nguon("https://m.vn/a.rss", "https://m.vn/a.rss"), nghi=0)
    cd.viet_bang(dong, tmp_path / "ra")
    csv_ = (tmp_path / "ra" / "bang_tung_nguon.csv").read_text(encoding="utf-8").splitlines()
    assert csv_[0].split(",") == cd.COT and len(csv_) == 3
    md = (tmp_path / "ra" / "bang_tung_nguon_dem_lop.md").read_text(encoding="utf-8")
    assert "| ok | 2 | 1 |" in md and "| **tổng** | 2 | 1 |" in md
    assert sorted(p.name for p in tmp_path.rglob("*") if p.is_file()) == [
        "bang_tung_nguon.csv", "bang_tung_nguon_dem_lop.md"]


# ── 5. liên kết RSS trên trang mục ──────────────────────────────────────────
def test_tim_lien_ket_rss_noi_goc_bo_trung_giu_thu_tu():
    html = ('<a href="/rss/a.rss">A</a><a href="b.rss?x=1">B</a><a href="https://o.vn/c.xml">C</a>'
            '<a href="/rss/a.rss">dup</a><a href="/trang.html">no</a><a href="mailto:x@y.rss">m</a>')
    assert cd.tim_lien_ket_rss(html, "https://m.vn/rss/index") == [
        "https://m.vn/rss/a.rss", "https://m.vn/rss/b.rss", "https://o.vn/c.xml"]


# ── 6. phạm vi: sản xuất không đổi ──────────────────────────────────────────
def test_san_xuat_khong_nhap_cong_cu_chan_doan():
    for ten in ("news_collectors.py", "app.py", "master_agent.py", "data_collectors.py", "run_daily.py"):
        p = GOC / ten
        if not p.exists():
            continue
        cay = ast.parse(p.read_text(encoding="utf-8"))
        for n in ast.walk(cay):
            ten_mo = ([a.name for a in n.names] if isinstance(n, ast.Import)
                      else [n.module or ""] if isinstance(n, ast.ImportFrom) else [])
            assert not [m for m in ten_mo if "chan_doan_nguon_tin" in m or "phan_loai_nguon_tin" in m], ten
