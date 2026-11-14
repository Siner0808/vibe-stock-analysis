"""BƯỚC 278 — gác hàm phân loại một lượt tải nguồn tin (`tools/phan_loai_nguon_tin.py`).

Không mạng, không đồng hồ: mọi lượt tải là `QuanSat` giả, dựng theo MƯỜI ca thật đã thăm dò ngày 14/11/2026
(`vibe_logs_tim_repo_tang_toc/bao_cao_t2_t3.md`, bảng "Headline finding") cộng các ca biên. Mỗi test gọi tên lớp
chờ đợi; đột biến của từng gác ở STATE BƯỚC 278, mục *Đột biến*.
"""
import ast
import pathlib
import sys

import pytest

GOC = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))

import phan_loai_nguon_tin as pl  # noqa: E402
from phan_loai_nguon_tin import QuanSat, phan_loai  # noqa: E402

XML = '<?xml version="1.0" encoding="utf-8"?><rss version="2.0"><channel>'
HTML = "<!DOCTYPE html><html><head><title>x</title>"


def _q(**k):
    co = dict(url="https://m.vn/rss/a.rss", status=200, url_cuoi="https://m.vn/rss/a.rss",
              content_type="application/rss+xml", n_byte=5000, dau_than=XML, n_bai=10, phien_ban="rss20")
    co.update(k)
    return QuanSat(**co)


# ── mười ca thật ────────────────────────────────────────────────────────────
def test_ca_ok_vnexpress():
    assert phan_loai(_q()) == "ok"


def test_ca_vnexpress_chung_khoan_chuyen_sang_html():
    q = _q(url="https://vnexpress.net/rss/chung-khoan.rss", url_cuoi="https://vnexpress.net/chung-khoan",
           chuyen_huong=(302,), content_type="text/html; charset=utf-8", n_byte=266207, dau_than=HTML,
           n_bai=0, bozo=1, bozo_loi="SAXParseException", phien_ban="")
    assert phan_loai(q) == "moved_to_html"


def test_ca_cafef_ngan_hang_404():
    assert phan_loai(_q(status=404, content_type="text/html", n_byte=3863, dau_than=HTML, n_bai=0)) == "dead_url"


def test_ca_vietstock_html_khong_phai_feed():
    q = _q(content_type="text/html", n_byte=341000, dau_than=HTML, n_bai=0, bozo=1, phien_ban="")
    assert phan_loai(q) == "html_not_feed"


def test_ca_vietstock_python_requests_403():
    assert phan_loai(_q(status=403, content_type="text/html", n_byte=146, dau_than="<html>403", n_bai=0)) == "blocked"


def test_ca_baodautu_sitemap():
    q = _q(content_type="text/xml", n_byte=1243, dau_than='<?xml version="1.0"?><sitemapindex xmlns="x">',
           n_bai=0, bozo=1, bozo_loi="NonXMLContentType", phien_ban="")
    assert phan_loai(q) == "xml_not_feed"


def test_ca_reuters_may_chu_chet():
    q = QuanSat(url="https://feeds.reuters.com/x", chuoi_loi=("ConnectionError", "RequestException", "OSError"),
                thong_diep_loi="Max retries exceeded ... NameResolutionError")
    assert phan_loai(q) == "dead_host"


# ── thứ tự: lỗi truyền tải đứng trước mọi thứ khác ──────────────────────────
def test_loi_truyen_tai_thang_ca_khi_con_status_va_bai():
    q = _q(chuoi_loi=("ConnectionError",), status=404, n_bai=5)
    assert phan_loai(q) == "dead_host"


def test_ssl_la_dead_host():
    assert phan_loai(QuanSat(url="u", chuoi_loi=("SSLError", "ConnectionError"))) == "dead_host"


def test_ssl_rieng_le_van_la_dead_host():
    """Chỉ tên `SSLError` (không kèm ConnectionError) cũng đủ: gác từng tên trong `TEN_LOI_MANG`."""
    # Danh sách gõ TAY ở đây, KHÔNG lặp `pl.TEN_LOI_MANG`: lặp chính tập đang bị đục thì đột biến bỏ một tên sống sót
    # (đo ở lượt đột biến đầu BƯỚC 278: bốn phát sống).
    for ten in ("ConnectionError", "SSLError", "NameResolutionError", "gaierror", "ConnectError"):
        assert phan_loai(QuanSat(url="u", chuoi_loi=(ten,))) == "dead_host", ten


def test_het_han_ket_noi_la_timeout_du_cung_la_ConnectionError():
    """`ConnectTimeout` kế thừa cả `Timeout` lẫn `ConnectionError`: timeout phải thắng."""
    q = QuanSat(url="u", chuoi_loi=("ConnectTimeout", "ConnectionError", "Timeout"))
    assert phan_loai(q) == "timeout"


def test_timeout_cua_san_xuat_la_timeout():
    """`news_collectors._tai_noi_dung` nổ `TimeoutError` khi vượt tổng hạn."""
    assert phan_loai(QuanSat(url="u", chuoi_loi=("TimeoutError", "OSError"))) == "timeout"


def test_doc_het_han_khi_tai_luong_la_timeout_du_ten_lop_noi_ConnectionError():
    """`requests.iter_content` đổi `ReadTimeoutError` thành `ConnectionError`; thông điệp mới nói thật."""
    q = QuanSat(url="u", chuoi_loi=("ConnectionError",), thong_diep_loi="HTTPSConnectionPool: Read timed out.")
    assert phan_loai(q) == "timeout"


def test_loi_la_la_loi_khac():
    assert phan_loai(QuanSat(url="u", chuoi_loi=("ValueError",), thong_diep_loi="nguồn quá 5000000 byte")) == "loi_khac"


def test_khong_co_status_khong_co_loi_la_loi_khac():
    assert phan_loai(QuanSat(url="u")) == "loi_khac"


@pytest.mark.parametrize("ma", [404, 410])
def test_dead_url_ca_404_va_410(ma):
    assert phan_loai(_q(status=ma)) == "dead_url"


@pytest.mark.parametrize("ma", [401, 403, 429])
def test_blocked_theo_ma(ma):
    assert phan_loai(_q(status=ma)) == "blocked"


def test_blocked_theo_cf_mitigated_du_status_la_200():
    assert phan_loai(_q(cf_chan=True)) == "blocked"


def test_blocked_thang_server_error():
    """Có `cf-mitigated` ở mã 503 (Cloudflare chặn): vẫn là chặn, không phải lỗi tạm."""
    assert phan_loai(_q(status=503, cf_chan=True)) == "blocked"


@pytest.mark.parametrize("ma", [500, 502, 503, 504])
def test_server_error(ma):
    assert phan_loai(_q(status=ma)) == "server_error"


def test_server_error_la_tu_500_chu_khong_tu_501():
    assert phan_loai(_q(status=500)) == "server_error"


@pytest.mark.parametrize("ma", [400, 405, 451, 199, 304, 301, 300])
def test_ma_khac_la_loi_khac(ma):
    assert phan_loai(_q(status=ma)) == "loi_khac"


def test_ma_2xx_khac_200_van_di_tiep():
    assert phan_loai(_q(status=206)) == "ok"
    assert phan_loai(_q(status=299)) == "ok"


def test_than_rong_la_empty_body_ke_ca_khi_content_type_html():
    assert phan_loai(_q(n_byte=0, dau_than="", n_bai=0, content_type="text/html")) == "empty_body"


# ── moved_to_html vs html_not_feed ─────────────────────────────────────────
def test_html_khong_chuyen_huong_la_html_not_feed():
    assert phan_loai(_q(content_type="text/html", dau_than=HTML, n_bai=0)) == "html_not_feed"


def test_chuyen_huong_http_sang_https_cung_duong_khong_phai_moved():
    q = _q(url="http://m.vn/rss/a.rss", url_cuoi="https://m.vn/rss/a.rss", chuyen_huong=(301,),
           content_type="text/html", dau_than=HTML, n_bai=0)
    assert phan_loai(q) == "html_not_feed"


def test_dau_gach_cuoi_khong_tinh_la_duong_khac():
    q = _q(url="https://m.vn/rss/a", url_cuoi="https://m.vn/rss/a/", chuyen_huong=(301,),
           content_type="text/html", dau_than=HTML, n_bai=0)
    assert phan_loai(q) == "html_not_feed"


def test_duong_khac_nhung_khong_chuyen_huong_khong_phai_moved():
    """Không có bước chuyển hướng nào thì `url_cuoi` khác chỉ là dữ liệu bẩn: không gọi là moved."""
    q = _q(url_cuoi="https://m.vn/trang-khac", content_type="text/html", dau_than=HTML, n_bai=0)
    assert phan_loai(q) == "html_not_feed"


def test_chuyen_huong_cung_duong_tu_noi_dung_la_feed_van_ok():
    q = _q(chuyen_huong=(301,), url_cuoi="https://www.m.vn/x/y")
    assert phan_loai(q) == "ok"


def test_html_nhan_bang_dau_than_du_content_type_noi_xml():
    q = _q(content_type="application/xml", dau_than="\ufeff  \n<HTML><body>", n_bai=0)
    assert phan_loai(q) == "html_not_feed"


def test_html_nhan_dau_than_doctype_viet_hoa():
    assert phan_loai(_q(content_type="", dau_than="<!DOCTYPE HTML PUBLIC", n_bai=0)) == "html_not_feed"


def test_content_type_html_nhung_co_bai_la_ok():
    """Máy chủ khai sai nhãn mà thân là RSS: app vẫn nhận bài, nên lớp là ok."""
    assert phan_loai(_q(content_type="text/html", n_bai=7)) == "ok"


def test_content_type_html_viet_hoa_van_nhan():
    assert phan_loai(_q(content_type="Text/HTML; charset=x", dau_than=XML, n_bai=0, phien_ban="rss20")) == "html_not_feed"


# ── xml_not_feed / parse_error / empty_feed / ok ──────────────────────────
@pytest.mark.parametrize("goc", ["urlset", "sitemapindex"])
def test_sitemap_la_xml_not_feed_chi_nho_dau_hieu_than(goc):
    """`phien_ban=None` (chưa đo) và bozo=0: chỉ còn dấu hiệu sitemap trong thân để nhận ra."""
    q = _q(dau_than=f'<?xml version="1.0"?><{goc} xmlns="x">', n_bai=0, phien_ban=None)
    assert phan_loai(q) == "xml_not_feed"


def test_sitemap_urlset_la_xml_not_feed():
    q = _q(dau_than='<?xml version="1.0"?><urlset xmlns="x">', n_bai=0, phien_ban="")
    assert phan_loai(q) == "xml_not_feed"


def test_xml_hop_le_nhung_khong_nhan_ra_dinh_dang_la_xml_not_feed():
    q = _q(dau_than='<?xml version="1.0"?><data><a/></data>', n_bai=0, bozo=0, phien_ban="")
    assert phan_loai(q) == "xml_not_feed"


def test_phien_ban_khong_biet_khong_bi_suy_ra_xml_not_feed():
    """`phien_ban=None` = chưa đo, không phải "không nhận ra": rơi xuống empty_feed."""
    q = _q(n_bai=0, phien_ban=None)
    assert phan_loai(q) == "empty_feed"


def test_bozo_khong_bai_la_parse_error():
    q = _q(dau_than="<rss><channel><item>", n_bai=0, bozo=1, bozo_loi="SAXParseException", phien_ban="rss20")
    assert phan_loai(q) == "parse_error"


def test_bozo_khong_dinh_dang_la_parse_error_khong_phai_xml_not_feed():
    """Bozo=1 và không nhận ra định dạng: hỏng phân tích (HTML cụt, XML gãy), không phải XML lành lặn."""
    q = _q(dau_than="<foo", n_bai=0, bozo=1, phien_ban="")
    assert phan_loai(q) == "parse_error"


def test_feed_rong_hop_le_la_empty_feed():
    assert phan_loai(_q(n_bai=0, bozo=0, phien_ban="rss20")) == "empty_feed"


def test_bozo_co_bai_van_la_ok():
    assert phan_loai(_q(bozo=1, bozo_loi="CharacterEncodingOverride", n_bai=3)) == "ok"


def test_mot_bai_la_du_de_ok():
    assert phan_loai(_q(n_bai=1)) == "ok"


# ── hợp đồng chung ─────────────────────────────────────────────────────────
def test_moi_quan_sat_ra_dung_mot_lop_trong_LOP():
    ca = [_q(), _q(status=404), _q(status=403), _q(status=500), _q(n_byte=0), _q(n_bai=0),
          QuanSat(url="u"), QuanSat(url="u", chuoi_loi=("ConnectionError",))]
    for q in ca:
        assert phan_loai(q) in pl.LOP


def test_LOP_khong_trung_va_du_chin_lop_giao_cong_bon_lop_them():
    assert len(set(pl.LOP)) == len(pl.LOP) == 13
    giao = ("dead_host", "dead_url", "blocked", "moved_to_html", "html_not_feed", "xml_not_feed",
            "parse_error", "empty_feed", "ok")
    assert [x for x in pl.LOP if x in giao] == list(giao), "thứ tự chín lớp giao phải giữ nguyên"


def test_moi_lop_trong_LOP_co_mot_ca_tra_ve_no():
    """Máy đo hẹp hơn thứ nó đo: một lớp không bao giờ được trả thì bảng đếm lớp ấy luôn 0."""
    ca = [_q(), _q(status=404), _q(status=403), _q(status=500), _q(n_byte=0), _q(n_bai=0, phien_ban="rss20"),
          QuanSat(url="u"), QuanSat(url="u", chuoi_loi=("ConnectionError",)),
          QuanSat(url="u", chuoi_loi=("ReadTimeout",)),
          _q(content_type="text/html", dau_than=HTML, n_bai=0),
          _q(url_cuoi="https://m.vn/x", chuyen_huong=(302,), content_type="text/html", dau_than=HTML, n_bai=0),
          _q(dau_than="<sitemapindex>", n_bai=0, phien_ban=""),
          _q(n_bai=0, bozo=1, dau_than="<rss", phien_ban="rss20")]
    assert {phan_loai(q) for q in ca} == set(pl.LOP)


def test_ham_thuan_khong_nhap_mang_hay_dong_ho():
    """Gác bằng AST: mô-đun không nhập requests/feedparser/socket/time/datetime/random."""
    cay = ast.parse((GOC / "tools" / "phan_loai_nguon_tin.py").read_text(encoding="utf-8"))
    nhap = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            nhap |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            nhap.add((n.module or "").split(".")[0])
    assert not nhap & {"requests", "feedparser", "socket", "time", "datetime", "random", "urllib3", "httpx"}


def test_san_xuat_khong_nhap_ham_phan_loai():
    """Chẩn đoán thì KHÔNG nằm trên đường tin thật (BƯỚC 278 không đổi gói tin)."""
    for ten in ("news_collectors.py", "app.py", "master_agent.py", "run_daily.py", "data_collectors.py"):
        p = GOC / ten
        if not p.exists():
            continue
        cay = ast.parse(p.read_text(encoding="utf-8"))
        nhap = set()
        for n in ast.walk(cay):
            if isinstance(n, ast.Import):
                nhap |= {a.name for a in n.names}
            elif isinstance(n, ast.ImportFrom):
                nhap.add(n.module or "")
        assert not {x for x in nhap if "phan_loai_nguon_tin" in x or "chan_doan_nguon_tin" in x}, ten
