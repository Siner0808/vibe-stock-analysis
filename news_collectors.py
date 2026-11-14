"""
news_collectors.py
──────────────────────────────────────────────────────────────────────
Đội ngũ Agent thu thập tin tức tài chính trong nước & quốc tế.
Bao gồm tin tức vĩ mô, ngành, doanh nghiệp và cảm xúc thị trường.
──────────────────────────────────────────────────────────────────────
"""
import feedparser
import requests
import threading
import time
from urllib.parse import quote_plus, urljoin
from dataclasses import dataclass, field
from bs4 import BeautifulSoup
import concurrent.futures

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}
FETCH_TIMEOUT = 8

# ── BƯỚC 275: tải RSS có giới hạn thời gian THẬT + bộ nhớ dùng chung ─────────
#: Tổng giây tối đa cho MỘT nguồn (kết nối + tải). Chặn kiểu treo "nhỏ giọt": mỗi lần chờ
#: socket đều ngắn nhưng cộng lại không có đáy. Trần xấu nhất của một nguồn ≈ HAN_MOT_NGUON +
#: HAN_DOC giây (lần đọc cuối cùng có thể đang chờ). Treo ở bước tra DNS thì `requests` không
#: cắt được — nhóm vẫn thoát ở HAN_NHOM, luồng treo bị bỏ lại chạy nền.
HAN_MOT_NGUON = FETCH_TIMEOUT
HAN_KET_NOI = 3.05
HAN_DOC = 5
HAN_NHOM = HAN_MOT_NGUON + HAN_DOC + 2   # nhóm nguồn đợi tối đa, rồi bỏ những nguồn chưa về
TRAN_BYTE_MOT_NGUON = 5_000_000
#: Bộ nhớ dùng chung cho nguồn KHÔNG phụ thuộc mã (trong nước, quốc tế, vĩ mô, ngành): 20 phút
#: khi tải được bài, 5 phút khi hỏng hay rỗng (không tải lại nguồn chết ở mỗi lượt phân tích).
#: Đây là lựa chọn của phiên làm BƯỚC 275, chờ người dùng xác nhận (STATE BƯỚC 275, mục câu hỏi).
TTL_BO_NHO_TIN = 20 * 60
TTL_BO_NHO_LOI = 5 * 60
# Cùng dấu hiệu mà `feedparser.parse(url)` tự gửi, để máy chủ trả cùng thứ như trước.
_HEADERS_RSS = {
    "User-Agent": feedparser.USER_AGENT,
    "Accept": ("application/atom+xml,application/rdf+xml,application/rss+xml,"
               "application/x-netcdf,application/xml;q=0.9,text/xml;q=0.2,*/*;q=0.1"),
    "A-IM": "feed",
}
_BO_NHO_TIN: dict[str, tuple[float, list | None]] = {}
_KHOA_CHUNG = threading.Lock()
_KHOA_URL: dict[str, threading.Lock] = {}


def xoa_bo_nho_tin() -> None:
    """Xoá bộ nhớ nguồn tin (dụng cụ đo và nút làm mới)."""
    with _KHOA_CHUNG:
        _BO_NHO_TIN.clear()


def _tai_noi_dung(url: str) -> tuple[bytes, dict]:
    """Tải thô một nguồn RSS, có TỔNG hạn `HAN_MOT_NGUON`. Trả (byte, tiêu đề phản hồi viết thường)."""
    bat_dau = time.monotonic()
    with requests.get(url, headers=_HEADERS_RSS, timeout=(HAN_KET_NOI, HAN_DOC), stream=True) as r:
        dem = bytearray()
        for khuc in r.iter_content(16384):
            dem += khuc
            if time.monotonic() - bat_dau > HAN_MOT_NGUON:
                raise TimeoutError(f"nguồn quá {HAN_MOT_NGUON}s: {url}")
            if len(dem) > TRAN_BYTE_MOT_NGUON:
                raise ValueError(f"nguồn quá {TRAN_BYTE_MOT_NGUON} byte: {url}")
        tieu_de = {k.lower(): v for k, v in r.headers.items()}
        # `feedparser.parse(url)` lấy nền tương đối từ địa chỉ CUỐI sau chuyển hướng; đưa nó vào đây.
        tieu_de["content-location"] = urljoin(r.url, tieu_de.get("content-location", ""))
        return bytes(dem), tieu_de


def _tai_va_phan_tich(url: str) -> list:
    noi_dung, tieu_de = _tai_noi_dung(url)
    return list(feedparser.parse(noi_dung, response_headers=tieu_de).entries)


def _khoa_cua(url: str) -> threading.Lock:
    with _KHOA_CHUNG:
        return _KHOA_URL.setdefault(url, threading.Lock())


def _doc_feed(url: str, dung_bo_nho: bool = True) -> list:
    """Các `entry` của một nguồn RSS. Hỏng hay quá hạn thì `[]` (như bản cũ nuốt lỗi).

    `dung_bo_nho=False` cho nguồn phụ thuộc mã (Google News theo mã): luôn tải mới. Còn lại dùng
    chung giữa các mã và các phiên; hai luồng cùng cần một địa chỉ thì MỘT tải, luồng kia đợi.
    """
    if not dung_bo_nho:
        try:
            return _tai_va_phan_tich(url)
        except Exception:
            return []
    with _khoa_cua(url):
        muc = _BO_NHO_TIN.get(url)
        if muc is not None:
            ttl = TTL_BO_NHO_TIN if muc[1] else TTL_BO_NHO_LOI
            if time.monotonic() - muc[0] < ttl:
                return muc[1] or []
        try:
            entries = _tai_va_phan_tich(url)
        except Exception:
            entries = []
        _BO_NHO_TIN[url] = (time.monotonic(), entries)
        return entries


def _gom_song_song(viec: list, han: float = HAN_NHOM) -> list:
    """Chạy song song `[(hàm, *đối số), ...]`; trả kết quả THEO THỨ TỰ KHAI, `None` cho việc hỏng
    hoặc chưa xong sau `han` giây. KHÔNG chờ luồng chưa xong (`shutdown(wait=False)`): bản cũ dùng
    `with ThreadPoolExecutor`, nên một nguồn treo giữ cả lượt phân tích."""
    if not viec:
        return []
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=len(viec))
    try:
        fs = [pool.submit(*v) for v in viec]
        xong, _ = concurrent.futures.wait(fs, timeout=han)
        return [f.result() if f in xong and f.exception() is None else None for f in fs]
    finally:
        pool.shutdown(wait=False, cancel_futures=True)

# ─────────────────────────────────────────────────────────────────────
# DATA CONTRACT
# ─────────────────────────────────────────────────────────────────────
@dataclass
class NewsItem:
    title: str
    summary: str
    source: str
    category: str        # VD: macro / banking / real_estate / tech / ...
    region: str          # domestic / international
    published: str = ""
    url: str = ""
    sentiment_hint: str = "NEUTRAL"   # POSITIVE / NEGATIVE / NEUTRAL

@dataclass
class NewsPacket:
    """Gói tin tức chuẩn hoá chuyển sang Analysis Layer"""
    symbol: str
    timestamp: str = field(default_factory=lambda: __import__('data_quality').now_vn().isoformat())
    domestic_news: list[NewsItem]      = field(default_factory=list)
    international_news: list[NewsItem] = field(default_factory=list)
    macro_news: list[NewsItem]         = field(default_factory=list)
    sector_news: dict[str, list[NewsItem]] = field(default_factory=dict)
    total_articles: int = 0
    # bia-ok: cung ho voi data_collectors.MarketDataPacket.data_quality —
    # goi tin tuc mac dinh tu nhan la lay day du. Thuoc Phase 2C. Chua sua
    # vi chua ai do duoc bao nhieu phien that su thieu tin.
    status: str = "OK"   # OK / PARTIAL / FAILED
    notes: list[str]  = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────
# UTILITIES
# ─────────────────────────────────────────────────────────────────────
POS_KEYWORDS = [
    "tăng", "tăng trưởng", "lợi nhuận cao", "phục hồi", "kỷ lục", "tích cực",
    "thuận lợi", "vượt kỳ vọng", "bứt phá", "dẫn đầu", "mạnh", "FDI tăng",
    "surplus", "growth", "surge", "rally", "beat", "record", "bullish",
    "recovery", "positive", "upgrade", "outperform", "strong", "expand"
]
NEG_KEYWORDS = [
    "giảm", "thua lỗ", "sụt giảm", "rủi ro", "khủng hoảng", "suy thoái", "lạm phát",
    "thất nghiệp", "âm", "yếu", "cảnh báo", "nợ xấu", "tăng lãi suất", "bán tháo",
    "fall", "drop", "crash", "recession", "inflation", "default", "loss", "risk",
    "downgrade", "underperform", "weak", "decline", "bearish", "sell-off"
]

def _sentiment(text: str) -> str:
    t = text.lower()
    pos = sum(1 for k in POS_KEYWORDS if k in t)
    neg = sum(1 for k in NEG_KEYWORDS if k in t)
    if pos > neg + 1:   return "POSITIVE"
    if neg > pos + 1:   return "NEGATIVE"
    return "NEUTRAL"

def _fetch_rss(url: str, source: str, category: str, region: str,
               max_items: int = 6, dung_bo_nho: bool = True) -> list[NewsItem]:
    """Parse một RSS feed và trả về danh sách NewsItem.

    BƯỚC 275: tải qua `_doc_feed` (hạn thời gian thật, bộ nhớ dùng chung). Cách dựng `NewsItem`
    từ `entry` KHÔNG đổi so với bản dùng `feedparser.parse(url)` trực tiếp.
    """
    items: list[NewsItem] = []
    try:
        entries = _doc_feed(url, dung_bo_nho)
        for entry in entries[:max_items]:
            title   = getattr(entry, "title", "") or ""
            summary = getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
            summary = BeautifulSoup(summary, "html.parser").get_text(" ", strip=True)[:300]
            pub     = getattr(entry, "published", "") or getattr(entry, "updated", "") or ""
            link    = getattr(entry, "link", "") or ""
            combined = title + " " + summary
            items.append(NewsItem(
                title=title, summary=summary, source=source,
                category=category, region=region,
                published=pub, url=link,
                sentiment_hint=_sentiment(combined)
            ))
    except Exception as e:
        pass
    return items


# ─────────────────────────────────────────────────────────────────────
# LAYER 1a: DOMESTIC NEWS AGENT  (Tin tức trong nước)
# ─────────────────────────────────────────────────────────────────────
class DomesticNewsAgent:
    """Thu thập tin tức kinh tế-tài chính trong nước từ RSS các báo lớn."""
    NAME = "Domestic News Agent 🇻🇳"

    FEEDS = [
        # VnExpress
        ("https://vnexpress.net/rss/kinh-doanh.rss",         "VnExpress", "macro",       "domestic"),
        ("https://vnexpress.net/rss/doanh-nghiep.rss",        "VnExpress", "corporate",   "domestic"),
        ("https://vnexpress.net/rss/chung-khoan.rss",         "VnExpress", "stock_market","domestic"),
        # Tuổi Trẻ
        ("https://tuoitre.vn/rss/kinh-doanh.rss",             "TuoiTre",   "macro",       "domestic"),
        # Thanh Niên
        ("https://thanhnien.vn/rss/kinh-te.rss",              "ThanhNien", "macro",       "domestic"),
        # Báo Đầu Tư
        ("https://baodautu.vn/sitemap/rss",                   "BaoDauTu",  "investment",  "domestic"),
        # CafeF
        ("https://cafef.vn/thi-truong-chung-khoan.rss",       "CafeF",     "stock_market","domestic"),
        ("https://cafef.vn/bat-dong-san.rss",                 "CafeF",     "real_estate", "domestic"),
        ("https://cafef.vn/ngan-hang.rss",                    "CafeF",     "banking",     "domestic"),
        ("https://cafef.vn/doanh-nghiep.rss",                 "CafeF",     "corporate",   "domestic"),
        # Vietstock
        ("https://vietstock.vn/rss/830/chung-khoan.rss",      "Vietstock", "stock_market","domestic"),
        # NDH Money
        ("https://ndh.vn/thi-truong/chung-khoan.rss",         "NDHMoney",  "stock_market","domestic"),
    ]

    def collect(self) -> list[NewsItem]:
        results: list[NewsItem] = []
        for kq in _gom_song_song([(_fetch_rss, url, src, cat, reg)
                                  for url, src, cat, reg in self.FEEDS]):
            results.extend(kq or [])
        return results


# ─────────────────────────────────────────────────────────────────────
# LAYER 1b: INTERNATIONAL NEWS AGENT  (Tin tức quốc tế)
# ─────────────────────────────────────────────────────────────────────
class InternationalNewsAgent:
    """Thu thập tin tức tài chính & kinh tế quốc tế từ RSS các hãng lớn."""
    NAME = "International News Agent 🌏"

    FEEDS = [
        # Reuters
        ("https://feeds.reuters.com/reuters/businessNews",          "Reuters",       "macro",       "international"),
        ("https://feeds.reuters.com/reuters/companyNews",           "Reuters",       "corporate",   "international"),
        # Seeking Alpha
        ("https://seekingalpha.com/feed.xml",                       "SeekingAlpha",  "stock_market","international"),
        # Bloomberg (open RSS)
        ("https://feeds.bloomberg.com/markets/news.rss",            "Bloomberg",     "macro",       "international"),
        ("https://feeds.bloomberg.com/economics/news.rss",          "Bloomberg",     "macro",       "international"),
        # Yahoo Finance
        ("https://finance.yahoo.com/news/rss/",                     "YahooFinance",  "macro",       "international"),
        # CNBC
        ("https://www.cnbc.com/id/100003114/device/rss/rss.html",   "CNBC",          "macro",       "international"),
        ("https://www.cnbc.com/id/10001147/device/rss/rss.html",    "CNBC",          "stock_market","international"),
        # Investing.com
        ("https://www.investing.com/rss/news.rss",                  "Investing.com", "macro",       "international"),
        ("https://www.investing.com/rss/market_overview.rss",       "Investing.com", "stock_market","international"),
        # FT
        ("https://www.ft.com/?format=rss",                          "FinancialTimes","macro",       "international"),
        # WSJ
        ("https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml",        "WSJ",           "macro",       "international"),
        # MarketWatch
        ("https://feeds.content.dowjones.io/public/rss/mw_marketpulse", "MarketWatch","stock_market","international"),
    ]

    def collect(self) -> list[NewsItem]:
        results: list[NewsItem] = []
        for kq in _gom_song_song([(_fetch_rss, url, src, cat, reg, 5)
                                  for url, src, cat, reg in self.FEEDS]):
            results.extend(kq or [])
        return results


# ─────────────────────────────────────────────────────────────────────
# LAYER 1c: MACRO DATA AGENT  (Dữ liệu vĩ mô VN & toàn cầu)
# ─────────────────────────────────────────────────────────────────────
class MacroDataAgent:
    """Thu thập tin tức và dữ liệu kinh tế vĩ mô: lãi suất, CPI, GDP, FED."""
    NAME = "Macro Data Agent 📊"

    FEEDS = [
        ("https://www.sbv.gov.vn/webcenter/rss?_afrLoop=0&lang=vi&catId=559", "NHNN Vietnam", "interest_rate", "domestic"),
        ("https://mof.gov.vn/webcenter/rss?catId=439&lang=vi",                  "Bo Tai Chinh",  "policy",        "domestic"),
        ("https://cafef.vn/vi-mo-dau-tu.rss",                                   "CafeF Macro",   "macro",         "domestic"),
        ("https://feeds.reuters.com/reuters/economicNews",                       "Reuters Macro", "macro",         "international"),
        ("https://www.federalreserve.gov/feeds/press_monetary.xml",             "US FED",        "interest_rate", "international"),
        ("https://www.ecb.europa.eu/rss/press.html",                            "ECB",           "interest_rate", "international"),
        ("https://www.imf.org/en/News/rss?type=pressRelease",                   "IMF",           "macro",         "international"),
        ("https://www.worldbank.org/en/news/rss",                               "WorldBank",     "macro",         "international"),
    ]

    def collect(self) -> list[NewsItem]:
        results: list[NewsItem] = []
        for kq in _gom_song_song([(_fetch_rss, url, src, cat, reg, 4)
                                  for url, src, cat, reg in self.FEEDS]):
            results.extend(kq or [])
        return results


# ─────────────────────────────────────────────────────────────────────
# LAYER 1d: SECTOR NEWS AGENT  (Tin tức theo ngành chuyên sâu)
# ─────────────────────────────────────────────────────────────────────
class SectorNewsAgent:
    """Thu thập tin tức chuyên sâu theo ngành: ngân hàng, BĐS, công nghệ,
       thép, dệt may, dầu khí, nông sản, y tế, hàng không, tiêu dùng..."""
    NAME = "Sector News Agent 🏭"

    SECTOR_FEEDS = {
        "banking": [
            ("https://cafef.vn/ngan-hang.rss",         "CafeF",    "domestic"),
            ("https://vietstock.vn/rss/830/ngan-hang.rss","Vietstock","domestic"),
            ("https://feeds.reuters.com/reuters/financialServicesAndRealEstateNews", "Reuters", "international"),
        ],
        "real_estate": [
            ("https://cafef.vn/bat-dong-san.rss",      "CafeF",    "domestic"),
            ("https://batdongsan.com.vn/tin-tuc-nha-dat.rss", "BDS.com.vn", "domestic"),
            ("https://vnexpress.net/rss/bat-dong-san.rss","VnExpress","domestic"),
        ],
        "technology": [
            ("https://cafef.vn/cong-nghe.rss",         "CafeF",    "domestic"),
            ("https://techcrunch.com/feed/",            "TechCrunch","international"),
            ("https://feeds.feedburner.com/venturebeat/SZYF","VentureBeat","international"),
        ],
        "steel_materials": [
            ("https://cafef.vn/bat-dong-san.rss",      "CafeF",    "domestic"),
            ("https://www.steelorbis.com/rss/news",    "SteelOrbis","international"),
        ],
        "oil_gas": [
            ("https://cafef.vn/dau-khi.rss",           "CafeF",    "domestic"),
            ("https://oilprice.com/rss/main",          "OilPrice", "international"),
            ("https://feeds.reuters.com/reuters/companyNews", "Reuters","international"),
        ],
        "agriculture": [
            ("https://cafef.vn/nong-nghiep.rss",       "CafeF",    "domestic"),
            ("https://www.agweb.com/rss.xml",          "AgWeb",    "international"),
        ],
        "consumer_retail": [
            ("https://cafef.vn/hang-tieu-dung.rss",    "CafeF",    "domestic"),
            ("https://www.retaildive.com/feeds/news/", "RetailDive","international"),
        ],
        "healthcare_pharma": [
            ("https://cafef.vn/duoc-pham.rss",         "CafeF",    "domestic"),
            ("https://www.fiercepharma.com/rss/xml",   "FiercePharma","international"),
            ("https://www.biopharmadive.com/feeds/news/","BiopharmaDive","international"),
        ],
        "aviation_logistics": [
            ("https://cafef.vn/giao-thong.rss",        "CafeF",    "domestic"),
            ("https://simpleflying.com/feed/",         "SimpleFlying","international"),
        ],
        "electricity_energy": [
            ("https://cafef.vn/dien-luc.rss",          "CafeF",    "domestic"),
            ("https://www.energymonitor.ai/feed",      "EnergyMonitor","international"),
        ],
        "securities_finance": [
            ("https://cafef.vn/chung-khoan.rss",       "CafeF",    "domestic"),
            ("https://vietstock.vn/rss/830/chung-khoan.rss","Vietstock","domestic"),
            ("https://feeds.reuters.com/reuters/businessNews","Reuters","international"),
        ],
        "textiles_apparel": [
            ("https://cafef.vn/det-may.rss",           "CafeF",    "domestic"),
            ("https://www.just-style.com/rss.ashx",    "JustStyle", "international"),
        ],
        "crypto_blockchain": [
            ("https://feeds.feedburner.com/CoinDesk",  "CoinDesk", "international"),
            ("https://cointelegraph.com/rss",           "CoinTelegraph","international"),
        ],
        "global_macro": [
            ("https://feeds.reuters.com/reuters/economicNews",    "Reuters","international"),
            ("https://feeds.bloomberg.com/markets/news.rss",      "Bloomberg","international"),
            ("https://www.cnbc.com/id/100003114/device/rss/rss.html","CNBC","international"),
        ],
    }

    def collect(self, symbol: str = "") -> dict[str, list[NewsItem]]:
        """Thu thập tin tức tất cả ngành song song."""
        sector_results: dict[str, list[NewsItem]] = {sec: [] for sec in self.SECTOR_FEEDS}

        # BƯỚC 275: MỘT bể phẳng cho mọi nguồn của mọi ngành (bản cũ: bể 8 ngành × bể 3 nguồn lồng
        # nhau, mỗi tầng `with` đợi tới cùng). Cùng một địa chỉ ở nhiều ngành chỉ tải một lần.
        viec, chu = [], []
        for sec, feeds in self.SECTOR_FEEDS.items():
            for url, src, reg in feeds:
                viec.append((_fetch_rss, url, src, sec, reg, 4))
                chu.append(sec)
        for sec, kq in zip(chu, _gom_song_song(viec)):
            sector_results[sec].extend(kq or [])
        return sector_results


# ─────────────────────────────────────────────────────────────────────
# LAYER 1e: COMPANY-SPECIFIC NEWS AGENT  (Tin tức theo mã CK)
# ─────────────────────────────────────────────────────────────────────
class CompanyNewsAgent:
    """Tìm tin tức liên quan đến mã cổ phiếu cụ thể từ Google News RSS."""
    NAME = "Company-Specific News Agent 🏢"

    def collect(self, symbol: str) -> list[NewsItem]:
        items: list[NewsItem] = []
        queries = [
            f"{symbol} cổ phiếu lợi nhuận",
            f"{symbol} chứng khoán",
        ]
        # BƯỚC 275: ba địa chỉ theo MÃ, tải song song và KHÔNG qua bộ nhớ dùng chung (`dung_bo_nho=False`);
        # thứ tự kết quả vẫn là hai bản tiếng Việt rồi bản tiếng Anh như trước.
        url_en = f"https://news.google.com/rss/search?q={symbol}+Vietnam+stock&hl=en&gl=VN&ceid=VN:en"
        # BƯỚC 277: câu hỏi tiếng Việt được mã hoá phần trăm (`quote_plus`) nên địa chỉ hợp lệ với mọi
        # thư viện HTTP — bản trước BƯỚC 275 (urllib) nổ InvalidURL vì khoảng trắng nên hai câu này chưa
        # bao giờ trả bài.
        viec = [(_fetch_rss, f"https://news.google.com/rss/search?q={quote_plus(q)}&hl=vi&gl=VN&ceid=VN:vi",
                 "GoogleNews", "corporate", "domestic", 5, False) for q in queries]
        viec.append((_fetch_rss, url_en, "GoogleNews-EN", "corporate", "international", 4, False))
        for kq in _gom_song_song(viec):
            items.extend(kq or [])

        return items


# ─────────────────────────────────────────────────────────────────────
# NEWS ORCHESTRATOR  (Điều phối toàn đội thu thập tin tức)
# ─────────────────────────────────────────────────────────────────────
class NewsOrchestrator:
    """
    Điều phối đội ngũ News Agents, thu thập song song,
    đóng gói thành NewsPacket chuẩn hoá để bàn giao cho Analysis Layer.
    """
    def __init__(self, symbol: str):
        self.symbol = symbol.upper()
        self.domestic_agent   = DomesticNewsAgent()
        self.intl_agent       = InternationalNewsAgent()
        self.macro_agent      = MacroDataAgent()
        self.sector_agent     = SectorNewsAgent()
        self.company_agent    = CompanyNewsAgent()

    def collect_and_handoff(self) -> NewsPacket:
        packet = NewsPacket(symbol=self.symbol)

        # Chạy song song tất cả agents
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
            f_dom     = pool.submit(self.domestic_agent.collect)
            f_intl    = pool.submit(self.intl_agent.collect)
            f_macro   = pool.submit(self.macro_agent.collect)
            f_sector  = pool.submit(self.sector_agent.collect, self.symbol)
            f_company = pool.submit(self.company_agent.collect, self.symbol)

            try:
                packet.domestic_news      = f_dom.result(timeout=20)
                packet.notes.append(f"[Domestic] {len(packet.domestic_news)} bài viết")
            except Exception as e:
                packet.notes.append(f"[Domestic] Lỗi: {e}")

            try:
                packet.international_news = f_intl.result(timeout=20)
                packet.notes.append(f"[International] {len(packet.international_news)} bài viết")
            except Exception as e:
                packet.notes.append(f"[International] Lỗi: {e}")

            try:
                packet.macro_news         = f_macro.result(timeout=20)
                packet.notes.append(f"[Macro] {len(packet.macro_news)} bài viết")
            except Exception as e:
                packet.notes.append(f"[Macro] Lỗi: {e}")

            try:
                packet.sector_news        = f_sector.result(timeout=30)
                total_sector = sum(len(v) for v in packet.sector_news.values())
                packet.notes.append(f"[Sectors] {total_sector} bài viết / {len(packet.sector_news)} ngành")
            except Exception as e:
                packet.notes.append(f"[Sectors] Lỗi: {e}")

            # Company news merged vào domestic
            try:
                company_items = f_company.result(timeout=15)
                packet.domestic_news.extend(company_items)
                packet.notes.append(f"[Company-{self.symbol}] {len(company_items)} bài viết")
            except Exception as e:
                packet.notes.append(f"[Company] Lỗi: {e}")

        packet.total_articles = (
            len(packet.domestic_news) +
            len(packet.international_news) +
            len(packet.macro_news) +
            sum(len(v) for v in packet.sector_news.values())
        )
        packet.status = "OK" if packet.total_articles > 0 else "FAILED"
        return packet
