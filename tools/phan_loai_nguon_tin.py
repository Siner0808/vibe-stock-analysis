"""BƯỚC 278 — hàm PHÂN LOẠI một lượt tải nguồn tin (RSS) thành đúng MỘT lớp. CHỈ ĐỂ CHẨN ĐOÁN.

Hàm thuần: không mạng, không đồng hồ, không đọc file. Đầu vào là một `QuanSat` (kết quả của MỘT lượt tải,
do `tools/chan_doan_nguon_tin.py` dựng); đầu ra là một chuỗi trong `LOP`. KHÔNG nằm trên đường tin thật:
`news_collectors.py`, `app.py` và gói tin không nhập file này (gác: `tests/test_phan_loai_nguon_tin_278.py`).

Thứ tự lớp mượn từ miniflux (Apache-2.0), `internal/reader/fetcher/response_handler.go` (`LocalizedError`):
lỗi truyền tải → trạng thái HTTP → thân rỗng → phân tích. Báo cáo của phiên tìm repo
(`vibe_logs_tim_repo_tang_toc/bao_cao_t2_t3.md`, mục T2) đọc dòng mã ấy; phiên này KHÔNG đọc lại mã miniflux.
Thứ tự người dùng/leader giao: dead_host, dead_url, blocked, moved_to_html, html_not_feed, xml_not_feed,
parse_error, empty_feed, ok.

SAI LỆCH so với thứ tự giao (mỗi chỗ một lý do):
- Thêm `timeout`: quá hạn là lỗi TẠM, không phải máy chủ chết; miniflux cũng tách nó khỏi mã trạng thái.
- Thêm `server_error` (HTTP ≥ 500): lỗi tạm của máy chủ, không phải URL chết.
- Thêm `empty_body` (thân 0 byte, HTTP 2xx), xét TRƯỚC các phép đoán nội dung: không có byte nào thì không có
  gì để đoán là HTML hay XML (miniflux cũng xét thân rỗng trước khi phân tích).
- Thêm `loi_khac`: lỗi truyền tải chưa biết tên (vượt hạn byte, chuyển hướng vòng…) hoặc mã HTTP không thuộc lớp nào.
  Không để nó rơi vào `dead_host` — gán sai nhãn là cách làm bảng nói dối.
- Lỗi TLS gộp vào `dead_host` (như miniflux gộp TLS/mạng/hết hạn vào một nhánh "thân rỗng"): không bắt tay được
  = không có kết nối an toàn tới máy chủ. Ngoại lệ: lỗi nào mang chữ "timed out" ở thông điệp là `timeout`
  (`requests.iter_content` đổi `ReadTimeoutError` thành `ConnectionError`, nên TÊN lớp một mình nói dối).
- Công thức "403 và thân < ~1.000 byte" của báo cáo T2 bị gộp: mọi 403 đã là `blocked`.
- Chuyển hướng sang trang HTML (`moved_to_html`) và trang HTML (`html_not_feed`) chỉ tính khi feedparser tìm
  được 0 bài NẾU chỉ có Content-Type nói HTML (máy chủ khai sai nhãn mà thân là RSS thì vẫn là `ok`).
- `ok` kể cả khi `bozo` = 1 mà có bài (cờ ấy là cảnh báo, không phải hỏng); bảng chẩn đoán in cột `bozo` riêng.
"""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

LOP = (
    "dead_host", "timeout", "dead_url", "blocked", "server_error", "empty_body",
    "moved_to_html", "html_not_feed", "xml_not_feed", "parse_error", "empty_feed", "ok", "loi_khac",
)

#: Số byte đầu của thân dùng để đoán HTML/sitemap (đủ qua khai báo `<?xml …?>` và vài thẻ gốc).
SO_BYTE_DAU = 512
DAU_HIEU_HTML = ("<!doctype html", "<html")
DAU_HIEU_SITEMAP = ("<sitemapindex", "<urlset")
MA_CHAN = (401, 403, 429)
#: Tên lớp ngoại lệ (đứng trong MRO) báo "không nối được máy chủ": mạng, tra DNS, từ chối kết nối, TLS.
TEN_LOI_MANG = frozenset({"ConnectionError", "SSLError", "NameResolutionError", "gaierror", "ConnectError"})


@dataclass(frozen=True)
class QuanSat:
    """Một lượt tải. `chuoi_loi` là TÊN mọi lớp trong MRO của ngoại lệ (rỗng nếu không có), để hàm thuần
    không phải nhập `requests`."""
    url: str
    chuoi_loi: tuple = ()
    thong_diep_loi: str = ""
    status: int | None = None
    url_cuoi: str = ""
    chuyen_huong: tuple = ()        # mã trạng thái của từng bước chuyển hướng (r.history)
    content_type: str = ""
    n_byte: int = 0
    dau_than: str = ""              # SO_BYTE_DAU byte đầu, đã giải mã (errors="replace")
    bozo: int = 0
    bozo_loi: str = ""
    n_bai: int = 0
    phien_ban: str | None = None    # feedparser `version` ("" = không nhận ra định dạng; None = không biết)
    cf_chan: bool = False           # tiêu đề `cf-mitigated` có mặt


def _duong(url: str) -> str:
    return urlparse(url).path.rstrip("/")


def _la_html(q: QuanSat) -> bool:
    dau = q.dau_than.lstrip("\ufeff \t\r\n").lower()
    if dau.startswith(DAU_HIEU_HTML):
        return True
    return q.content_type.lower().startswith("text/html") and q.n_bai == 0


def phan_loai(q: QuanSat) -> str:
    """Trả đúng một lớp trong `LOP`; câu đầu khớp thắng (thứ tự là hợp đồng, xem docstring module)."""
    if q.chuoi_loi:
        if any("timeout" in t.lower() for t in q.chuoi_loi) or "timed out" in q.thong_diep_loi.lower():
            return "timeout"
        if TEN_LOI_MANG & set(q.chuoi_loi):
            return "dead_host"
        return "loi_khac"
    s = q.status
    if s is None:
        return "loi_khac"
    if s in (404, 410):
        return "dead_url"
    if s in MA_CHAN or q.cf_chan:
        return "blocked"
    if s >= 500:
        return "server_error"
    if s < 200 or s >= 300:
        return "loi_khac"
    if q.n_byte == 0:
        return "empty_body"
    html = _la_html(q)
    if html and q.chuyen_huong and _duong(q.url_cuoi or q.url) != _duong(q.url):
        return "moved_to_html"
    if html:
        return "html_not_feed"
    dau = q.dau_than.lower()
    if q.n_bai == 0 and (any(m in dau for m in DAU_HIEU_SITEMAP)
                         or (q.phien_ban == "" and not q.bozo)):
        return "xml_not_feed"
    if q.n_bai == 0 and q.bozo:
        return "parse_error"
    if q.n_bai == 0:
        return "empty_feed"
    return "ok"
