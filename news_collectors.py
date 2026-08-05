"""
news_collectors.py
──────────────────────────────────────────────────────────────────────
Đội ngũ Agent thu thập tin tức tài chính trong nước & quốc tế.
Bao gồm tin tức vĩ mô, ngành, doanh nghiệp và cảm xúc thị trường.
──────────────────────────────────────────────────────────────────────
"""
import feedparser
import requests
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from bs4 import BeautifulSoup
import concurrent.futures
import re

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}
FETCH_TIMEOUT = 8

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
               max_items: int = 6) -> list[NewsItem]:
    """Parse một RSS feed và trả về danh sách NewsItem."""
    items: list[NewsItem] = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:max_items]:
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
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            futures = {pool.submit(_fetch_rss, url, src, cat, reg): (url, src)
                       for url, src, cat, reg in self.FEEDS}
            for fut in concurrent.futures.as_completed(futures):
                results.extend(fut.result())
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
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            futures = {pool.submit(_fetch_rss, url, src, cat, reg, 5): (src,)
                       for url, src, cat, reg in self.FEEDS}
            for fut in concurrent.futures.as_completed(futures):
                results.extend(fut.result())
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
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            futures = {pool.submit(_fetch_rss, url, src, cat, reg, 4): (src,)
                       for url, src, cat, reg in self.FEEDS}
            for fut in concurrent.futures.as_completed(futures):
                results.extend(fut.result())
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
        sector_results: dict[str, list[NewsItem]] = {}

        def fetch_sector(sector_name: str, feeds: list) -> tuple:
            items: list[NewsItem] = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as inner:
                futs = {inner.submit(_fetch_rss, url, src, sector_name, reg, 4): src
                        for url, src, reg in feeds}
                for f in concurrent.futures.as_completed(futs):
                    items.extend(f.result())
            return sector_name, items

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            futures = {pool.submit(fetch_sector, sec, feeds): sec
                       for sec, feeds in self.SECTOR_FEEDS.items()}
            for fut in concurrent.futures.as_completed(futures):
                sec_name, sec_items = fut.result()
                sector_results[sec_name] = sec_items

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
        for q in queries:
            url = f"https://news.google.com/rss/search?q={q}&hl=vi&gl=VN&ceid=VN:vi"
            fetched = _fetch_rss(url, "GoogleNews", "corporate", "domestic", 5)
            items.extend(fetched)

        # English Google News
        url_en = f"https://news.google.com/rss/search?q={symbol}+Vietnam+stock&hl=en&gl=VN&ceid=VN:en"
        items.extend(_fetch_rss(url_en, "GoogleNews-EN", "corporate", "international", 4))

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
