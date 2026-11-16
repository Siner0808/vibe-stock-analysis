"""BƯỚC 279 — sửa danh sách nguồn tin theo quyết định của người dùng 16/11/2026 (không mạng).

Bốn quyết định, mỗi quyết định một điều khoá ở đây (đột biến: STATE BƯỚC 279, mục E):

1. **Đổi một-đổi-một** (*"Thay cả 4 (Recommended)"*): cafef ngan-hang → tai-chinh-ngan-hang · vietstock chung-khoan →
   /144/chung-khoan · vietstock ngan-hang → /757/tai-chinh/ngan-hang · just-style rss.ashx → /feed/.
2. **cafef cong-nghe → kinh-te-so** (*"Dùng kinh-te-so (Recommended)"*).
3. **Bỏ dòng cafef chung-khoan của nhóm ngành chứng khoán, KHÔNG thêm thi-truong-chung-khoan vào nhóm ấy**
   (*"Bỏ dòng trùng (Recommended)"*): địa chỉ thay đã có ở nhóm trong nước, thêm thì một bài bị đếm hai lần.
4. **Xoá nguồn chết hẳn, giữ bốn nguồn chưa rõ** (*"Xoá chết hẳn, giữ 4 nguồn chưa rõ (Recommended)"*): baodautu ·
   agweb · fiercepharma · investing.com (cả hai địa chỉ) còn nguyên.
   **BƯỚC 280 ĐẢO MỘT PHẦN quyết định 4** (người dùng 16/11/2026: *"Bỏ investing.com (Recommended)"*): hai địa chỉ
   investing.com nay phải VẮNG (`BO_280`); ba nguồn còn lại (`MIEN_GIU`) vẫn nguyên. Không danh sách nào khác đổi.

Danh sách "xoá" ở đây suy từ `docs/do-nguon-tin-278/bang_ung_vien.md` (cột ứng viên = "bỏ", trừ bốn nguồn giữ),
không gõ tay hai lần; cộng một dòng ở quyết định 3.
"""
import collections
import pathlib
import re
import sys

import pytest

GOC = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import news_collectors as nc  # noqa: E402

NHOM_NGANH = nc.SectorNewsAgent.SECTOR_FEEDS

# ── (cũ → mới) đúng bốn quyết định đầu của người dùng; nhóm khai và nhãn không đổi ────────────────────────────────
DOI = {
    "https://cafef.vn/ngan-hang.rss": "https://cafef.vn/tai-chinh-ngan-hang.rss",
    "https://vietstock.vn/rss/830/chung-khoan.rss": "https://vietstock.vn/144/chung-khoan.rss",
    "https://vietstock.vn/rss/830/ngan-hang.rss": "https://vietstock.vn/757/tai-chinh/ngan-hang.rss",
    "https://www.just-style.com/rss.ashx": "https://www.just-style.com/feed/",
    "https://cafef.vn/cong-nghe.rss": "https://cafef.vn/kinh-te-so.rss",
}
# nơi mỗi địa chỉ MỚI phải đứng: (nhóm, nguồn hiển thị)
NOI_MOI = {
    "https://cafef.vn/tai-chinh-ngan-hang.rss": [("Domestic", "CafeF"), ("Sector:banking", "CafeF")],
    "https://vietstock.vn/144/chung-khoan.rss": [("Domestic", "Vietstock"), ("Sector:securities_finance", "Vietstock")],
    "https://vietstock.vn/757/tai-chinh/ngan-hang.rss": [("Sector:banking", "Vietstock")],
    "https://www.just-style.com/feed/": [("Sector:textiles_apparel", "JustStyle")],
    "https://cafef.vn/kinh-te-so.rss": [("Sector:technology", "CafeF")],
}
# quyết định 3: dòng của nhóm ngành chứng khoán bị bỏ, địa chỉ thay KHÔNG được vào nhóm ấy
BO_CAFEF_CK = "https://cafef.vn/chung-khoan.rss"
THAY_CAFEF_CK = "https://cafef.vn/thi-truong-chung-khoan.rss"
# quyết định 4: bốn nguồn giữ (tên miền) và nhóm khai của chúng
GIU = {
    "https://baodautu.vn/sitemap/rss": "Domestic",
    "https://www.agweb.com/rss.xml": "Sector:agriculture",
    "https://www.fiercepharma.com/rss/xml": "Sector:healthcare_pharma",
}
MIEN_GIU = ("baodautu.vn", "agweb.com", "fiercepharma.com")
# BƯỚC 280: nguồn người dùng cho BỎ sau khi BƯỚC 279 giữ nó (hai địa chỉ; hết thời gian chờ 16/16 lượt đo 16/11/2026)
BO_280 = ("https://www.investing.com/rss/news.rss", "https://www.investing.com/rss/market_overview.rss")


def _khai():
    """Mọi dòng khai: [(nhóm, url, nguồn hiển thị)] — đọc từ các lớp thật, không chép tay."""
    ds = []
    for ten, agent in (("Domestic", nc.DomesticNewsAgent), ("International", nc.InternationalNewsAgent),
                       ("Macro", nc.MacroDataAgent)):
        ds += [(ten, f[0], f[1]) for f in agent.FEEDS]
    for sec, fs in NHOM_NGANH.items():
        ds += [(f"Sector:{sec}", f[0], f[1]) for f in fs]
    return ds


def _bang_278():
    """Các dòng `| url | nơi khai | lớp | ứng viên/bỏ | ... |` của bảng BƯỚC 278 → [(url, lớp, ứng viên|None)]."""
    md = (GOC / "docs" / "do-nguon-tin-278" / "bang_ung_vien.md").read_text(encoding="utf-8")
    ds = []
    for dong in md.splitlines():
        m = re.match(r"\| `([^`]+)` \| ([^|]+) \| (\S+) \(([^)]*)\) \| (bỏ|`[^`]+`) \|", dong)
        if m:
            ds.append((m.group(1), m.group(3), None if m.group(5) == "bỏ" else m.group(5).strip("`")))
    return ds


def _xoa_theo_bang():
    """Địa chỉ BƯỚC 279 phải xoá: cột "bỏ" của bảng 278 trừ ba nguồn còn giữ và trừ hai địa chỉ BƯỚC 280 bỏ thêm."""
    return [u for u, _, ut in _bang_278() if ut is None and not any(h in u for h in MIEN_GIU) and u not in BO_280]


# ── đọc bảng 278 đúng (máy đo không được rỗng) ───────────────────────────────────────────────────────────────────────
def test_bang_278_doc_ra_dung_so_dong():
    b = _bang_278()
    assert len(b) == 32
    assert sum(1 for _, _, ut in b if ut is None) == 26      # 26 địa chỉ "bỏ" (mục C BƯỚC 278)
    assert {u: ut for u, _, ut in b if ut} == {k: v for k, v in DOI.items() if k != BO_CAFEF_CK} | {BO_CAFEF_CK: THAY_CAFEF_CK}


def test_xoa_theo_bang_la_21_dia_chi_va_khong_co_bon_nguon_giu():
    x = _xoa_theo_bang()
    assert len(x) == 21 and len(set(x)) == 21
    assert not [u for u in x if any(h in u for h in MIEN_GIU)]


# ── 1+2. địa chỉ mới có mặt, đúng nhóm, đúng nhãn ──────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("moi", sorted(NOI_MOI))
def test_dia_chi_moi_dung_o_dung_nhom_va_nhan(moi):
    co = sorted((g, n) for g, u, n in _khai() if u == moi)
    assert co == sorted(NOI_MOI[moi])


@pytest.mark.parametrize("cu", sorted(DOI))
def test_dia_chi_cu_da_bien_mat_o_moi_nhom(cu):
    assert [g for g, u, _ in _khai() if u == cu] == []


def test_nhan_the_loai_va_vung_cua_dong_doi_giu_nguyen():
    """Chỉ ĐỊA CHỈ đổi; nhãn nguồn, thể loại, vùng của dòng khai giữ như cũ."""
    dom = {f[0]: f[1:] for f in nc.DomesticNewsAgent.FEEDS}
    assert dom["https://cafef.vn/tai-chinh-ngan-hang.rss"] == ("CafeF", "banking", "domestic")
    assert dom["https://vietstock.vn/144/chung-khoan.rss"] == ("Vietstock", "stock_market", "domestic")
    nganh = {(sec, f[0]): f[1:] for sec, fs in NHOM_NGANH.items() for f in fs}
    assert nganh[("banking", "https://cafef.vn/tai-chinh-ngan-hang.rss")] == ("CafeF", "domestic")
    assert nganh[("banking", "https://vietstock.vn/757/tai-chinh/ngan-hang.rss")] == ("Vietstock", "domestic")
    assert nganh[("securities_finance", "https://vietstock.vn/144/chung-khoan.rss")] == ("Vietstock", "domestic")
    assert nganh[("technology", "https://cafef.vn/kinh-te-so.rss")] == ("CafeF", "domestic")
    assert nganh[("textiles_apparel", "https://www.just-style.com/feed/")] == ("JustStyle", "international")


# ── 3. quyết định 3: không đếm hai lần thi-truong-chung-khoan ─────────────────────────────────────────────────────────
def test_thi_truong_chung_khoan_chi_o_nhom_trong_nuoc_dung_mot_lan():
    assert [(g, u) for g, u, _ in _khai() if u == THAY_CAFEF_CK] == [("Domestic", THAY_CAFEF_CK)]


def test_nhom_nganh_chung_khoan_chi_con_vietstock_144():
    assert [f[0] for f in NHOM_NGANH["securities_finance"]] == ["https://vietstock.vn/144/chung-khoan.rss"]
    assert BO_CAFEF_CK not in {u for _, u, _ in _khai()}


# ── 4. xoá chết hẳn, giữ bốn nguồn chưa rõ ──────────────────────────────────────────────────────────────────────────
def test_moi_dia_chi_xoa_theo_bang_da_het_o_moi_nhom():
    con = [(g, u) for g, u, _ in _khai() if u in set(_xoa_theo_bang())]
    assert con == []


def test_ten_mien_chet_hang_khong_con_dong_nao():
    """Theo tên miền, không theo địa chỉ đầy đủ: đổi đường dẫn ở cùng máy chủ chết cũng lọt nếu chỉ so địa chỉ."""
    chet = ("reuters.com", "yahoo.com", "ndh.vn", "sbv.gov.vn", "mof.gov.vn", "imf.org", "worldbank.org",
            "batdongsan.com.vn", "steelorbis.com", "simpleflying.com")
    con = [u for _, u, _ in _khai() if any(m in u for m in chet)]
    assert con == []
    assert [u for _, u, _ in _khai() if "vnexpress.net/rss/chung-khoan" in u] == []
    cafef_chet = ("dau-khi", "nong-nghiep", "hang-tieu-dung", "duoc-pham", "giao-thong", "dien-luc", "det-may",
                  "cong-nghe.rss")
    assert [u for _, u, _ in _khai() if "cafef.vn" in u and any(k in u for k in cafef_chet)] == []


@pytest.mark.parametrize("u,nhom", sorted(GIU.items()))
def test_bon_nguon_chua_ro_con_nguyen_o_dung_nhom(u, nhom):
    assert [g for g, x, _ in _khai() if x == u] == [nhom]


def test_hai_dia_chi_investing_com_deu_VANG_buoc_280():
    """BƯỚC 280 đảo quyết định 4 của BƯỚC 279 cho nguồn này: cả HAI địa chỉ phải vắng ở mọi nhóm (bỏ một giữ một là
    chưa đủ), và đó đúng là hai địa chỉ của bảng 278 chưa nằm trong danh sách xoá của BƯỚC 279."""
    assert [(g, u) for g, u, _ in _khai() if "investing.com" in u] == []
    assert sorted(u for u, _, ut in _bang_278() if "investing.com" in u and ut is None) == sorted(BO_280)
    assert not [u for u in _xoa_theo_bang() if "investing" in u]       # bốn quyết định của 279 không đụng nó


# ── không khai lặp ngoài những chỗ đã có từ trước ─────────────────────────────────────────────────────────────────────
# Đây là danh sách có SỐ LẦN, không phải tập hợp: một địa chỉ khai thêm lần nữa ở một nhóm khác thì đỏ.
# Khai ở nhiều nhóm là thiết kế có từ trước (cafef bat-dong-san 3 nhóm; hai tờ báo ngân hàng/chứng khoán vừa ở
# nhóm trong nước vừa ở nhóm ngành; bloomberg · cnbc vừa quốc tế vừa vĩ mô toàn cầu). Điều mới của BƯỚC này là
# KHÔNG thêm lặp mới: thi-truong-chung-khoan vẫn một lần (xem trên), và hai địa chỉ thay thế khai đúng bằng
# số lần của địa chỉ cũ.
TRUNG_DUOC_PHEP = {
    "https://cafef.vn/bat-dong-san.rss": 3,
    "https://cafef.vn/tai-chinh-ngan-hang.rss": 2,
    "https://vietstock.vn/144/chung-khoan.rss": 2,
    "https://feeds.bloomberg.com/markets/news.rss": 2,
    "https://www.cnbc.com/id/100003114/device/rss/rss.html": 2,
}


def test_khai_lap_dung_danh_sach_da_biet_va_khong_them_cai_moi():
    dem = collections.Counter(u for _, u, _ in _khai())
    assert {u: n for u, n in dem.items() if n > 1} == TRUNG_DUOC_PHEP


def test_tong_so_dong_khai_theo_nhom():
    """68 dòng → 43: 25 dòng đã xoá (22 địa chỉ + ba địa chỉ reuters khai hai lần). BƯỚC 280: → 41 (hai địa chỉ
    investing.com của nhóm quốc tế, 10 → 8)."""
    dem = collections.Counter(g.split(":")[0] for g, _, _ in _khai())
    assert dem == {"Domestic": 10, "International": 8, "Macro": 3, "Sector": 20}
    assert sum(dem.values()) == 41           # 43 của BƯỚC 279 trừ hai địa chỉ investing.com của BƯỚC 280


def test_nhom_nganh_hang_khong_logistics_van_con_khoa_voi_danh_sach_rong():
    """Cả hai nguồn của `aviation_logistics` đều chết hẳn nên nhóm hết dòng; khoá ngành vẫn còn (nhãn ngành và
    "n ngành" ở ghi chú gói tin giữ như cũ; không đổi gì ngoài điều người dùng đã chọn)."""
    assert NHOM_NGANH["aviation_logistics"] == []
    assert len(NHOM_NGANH) == 14


# ── hành vi: gói tin vẫn dựng được với danh sách mới (không mạng) ─────────────────────────────────────────────────────
def test_nhom_nganh_rong_van_thu_gom_khong_no(monkeypatch):
    gap = []

    def gia(viec):
        gap.extend(v[1] for v in viec)
        return [[] for _ in viec]
    monkeypatch.setattr(nc, "_gom_song_song", gia)
    kq = nc.SectorNewsAgent().collect()
    assert set(kq) == set(NHOM_NGANH) and kq["aviation_logistics"] == []
    assert len(gap) == 20


# ── thứ tự các dòng còn lại giữ như cũ (chụp đủ danh sách, theo nhóm) ──────────────────────────────────────────────────
def test_thu_tu_cac_dong_con_lai_nhu_truoc_khi_sua():
    """Bản chụp có thứ tự của 43 dòng sau BƯỚC 279: dòng nào còn thì đứng đúng chỗ cũ (không xếp lại, không chèn)."""
    nhom = collections.defaultdict(list)
    for g, u, _ in _khai():
        nhom[g].append(u)
    # aviation_logistics không có dòng nào nên không hiện ở đây
    assert list(nhom) == ["Domestic", "International", "Macro", "Sector:banking", "Sector:real_estate",
                          "Sector:technology", "Sector:steel_materials", "Sector:oil_gas", "Sector:agriculture",
                          "Sector:consumer_retail", "Sector:healthcare_pharma", "Sector:electricity_energy",
                          "Sector:securities_finance", "Sector:textiles_apparel", "Sector:crypto_blockchain",
                          "Sector:global_macro"]
    assert nhom["Domestic"] == [
        "https://vnexpress.net/rss/kinh-doanh.rss", "https://vnexpress.net/rss/doanh-nghiep.rss",
        "https://tuoitre.vn/rss/kinh-doanh.rss", "https://thanhnien.vn/rss/kinh-te.rss",
        "https://baodautu.vn/sitemap/rss", "https://cafef.vn/thi-truong-chung-khoan.rss",
        "https://cafef.vn/bat-dong-san.rss", "https://cafef.vn/tai-chinh-ngan-hang.rss",
        "https://cafef.vn/doanh-nghiep.rss", "https://vietstock.vn/144/chung-khoan.rss"]
    assert nhom["International"] == [
        "https://seekingalpha.com/feed.xml", "https://feeds.bloomberg.com/markets/news.rss",
        "https://feeds.bloomberg.com/economics/news.rss", "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "https://www.cnbc.com/id/10001147/device/rss/rss.html", "https://www.ft.com/?format=rss",
        "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml", "https://feeds.content.dowjones.io/public/rss/mw_marketpulse"]
    assert nhom["Macro"] == [
        "https://cafef.vn/vi-mo-dau-tu.rss", "https://www.federalreserve.gov/feeds/press_monetary.xml",
        "https://www.ecb.europa.eu/rss/press.html"]
    assert nhom["Sector:banking"] == ["https://cafef.vn/tai-chinh-ngan-hang.rss",
                                      "https://vietstock.vn/757/tai-chinh/ngan-hang.rss"]
    assert nhom["Sector:real_estate"] == ["https://cafef.vn/bat-dong-san.rss",
                                          "https://vnexpress.net/rss/bat-dong-san.rss"]
    assert nhom["Sector:technology"] == ["https://cafef.vn/kinh-te-so.rss", "https://techcrunch.com/feed/",
                                         "https://feeds.feedburner.com/venturebeat/SZYF"]
    assert nhom["Sector:steel_materials"] == ["https://cafef.vn/bat-dong-san.rss"]
    assert nhom["Sector:oil_gas"] == ["https://oilprice.com/rss/main"]
    assert nhom["Sector:agriculture"] == ["https://www.agweb.com/rss.xml"]
    assert nhom["Sector:consumer_retail"] == ["https://www.retaildive.com/feeds/news/"]
    assert nhom["Sector:healthcare_pharma"] == ["https://www.fiercepharma.com/rss/xml",
                                                "https://www.biopharmadive.com/feeds/news/"]
    assert nhom["Sector:electricity_energy"] == ["https://www.energymonitor.ai/feed"]
    assert nhom["Sector:securities_finance"] == ["https://vietstock.vn/144/chung-khoan.rss"]
    assert nhom["Sector:textiles_apparel"] == ["https://www.just-style.com/feed/"]
    assert nhom["Sector:crypto_blockchain"] == ["https://feeds.feedburner.com/CoinDesk", "https://cointelegraph.com/rss"]
    assert nhom["Sector:global_macro"] == ["https://feeds.bloomberg.com/markets/news.rss",
                                           "https://www.cnbc.com/id/100003114/device/rss/rss.html"]
    assert list(NHOM_NGANH) == [
        "banking", "real_estate", "technology", "steel_materials", "oil_gas", "agriculture", "consumer_retail",
        "healthcare_pharma", "aviation_logistics", "electricity_energy", "securities_finance", "textiles_apparel",
        "crypto_blockchain", "global_macro"]
