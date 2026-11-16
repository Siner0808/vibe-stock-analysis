"""BƯỚC 281 — thêm hai nguồn Báo Xây dựng vào nhóm ngành `aviation_logistics` (không mạng).

Quyết định của người dùng 16/11/2026: *"Thêm 1 và 2 (Recommended)"* (hai địa chỉ baoxaydung.vn; chữ câu hỏi là của
LEADER, ở `docs/STATE.md` BƯỚC 281). Bốn điều khoá, mỗi điều có đột biến ở STATE BƯỚC 281:

1. **Đúng hai địa chỉ, đúng nhóm, đúng nhãn và vùng, mỗi địa chỉ MỘT dòng** (không lọt sang nhóm khác, không khai lặp:
   khai lặp ở hai nhóm làm một bài bị đếm hai lần).
2. **Hành vi**: với bản giả của `_doc_feed` (không mạng), nhóm `aviation_logistics` nhận tối đa 4 bài MỖI nguồn
   (`max_items` của `SectorNewsAgent.collect`), gắn `category = "aviation_logistics"`, nguồn `BaoXayDung`, vùng
   `domestic`; không bài nào lọt sang nhóm khác, và `total_articles` của gói tin cộng đúng chúng.
3. **Điểm KHÔNG đổi**: tin của nhóm ngành này chỉ hiện ở phần tin tức. `news_sentiment_agent` chỉ lấy bốn nhóm
   (`global_macro`, `securities_finance`, `banking`, `macro`) vào điểm tổng; `master_agent` giữ `news_norm` chỉ để
   hiển thị. Gác đọc cả hành vi (cùng điểm khi nhóm có bài và khi nhóm rỗng) lẫn danh sách bốn nhóm bằng AST.
4. **Đường quét không nhập `news_collectors`** (AST) — thêm nguồn tin không đụng điểm cuối của sổ ảo.
"""
import ast
import pathlib
import types

import pytest

import news_collectors as nc
from news_sentiment_agent import NewsSentimentAgent

GOC = pathlib.Path(__file__).resolve().parent.parent

HANG_KHONG = "https://baoxaydung.vn/rss/giao-thong/hang-khong.rss"
HANG_HAI = "https://baoxaydung.vn/rss/giao-thong/hang-hai.rss"
HAI_DIA_CHI = [HANG_KHONG, HANG_HAI]
NHOM = "aviation_logistics"


@pytest.fixture(autouse=True)
def _sach_bo_nho():
    nc.xoa_bo_nho_tin()
    yield
    nc.xoa_bo_nho_tin()


def _moi_dong_khai():
    """[(nhóm, url, nguồn, vùng)] của MỌI dòng khai trong `news_collectors`, đọc từ các lớp thật."""
    ds = []
    for ten, agent in (("Domestic", nc.DomesticNewsAgent), ("International", nc.InternationalNewsAgent),
                       ("Macro", nc.MacroDataAgent)):
        ds += [(ten, u, n, v) for u, n, _the_loai, v in agent.FEEDS]
    for sec, fs in nc.SectorNewsAgent.SECTOR_FEEDS.items():
        ds += [(f"Sector:{sec}", u, n, v) for u, n, v in fs]
    return ds


# ── 1. đúng hai địa chỉ, đúng nhóm, nhãn, vùng; mỗi cái một dòng ─────────────────────────────────────────────────────
def test_nhom_hang_khong_logistics_co_dung_hai_dia_chi_theo_thu_tu():
    assert nc.SectorNewsAgent.SECTOR_FEEDS[NHOM] == [(HANG_KHONG, "BaoXayDung", "domestic"),
                                                      (HANG_HAI, "BaoXayDung", "domestic")]


@pytest.mark.parametrize("url", HAI_DIA_CHI)
def test_moi_dia_chi_chi_mot_dong_va_chi_o_nhom_hang_khong(url):
    co = [(g, n, v) for g, u, n, v in _moi_dong_khai() if u == url]
    assert co == [(f"Sector:{NHOM}", "BaoXayDung", "domestic")]


def test_khong_dia_chi_baoxaydung_nao_khac_o_bat_ky_nhom_nao():
    """Theo TÊN MIỀN: thêm một mục thứ ba (đường sắt, đường thuỷ ...) khi người dùng chỉ chọn hai là sai phạm vi."""
    assert sorted(u for _, u, _, _ in _moi_dong_khai() if "baoxaydung.vn" in u) == sorted(HAI_DIA_CHI)


def test_nhom_nganh_con_14_khoa_va_nhan_nganh_con_nguyen():
    from news_sentiment_agent import SECTOR_LABEL
    assert len(nc.SectorNewsAgent.SECTOR_FEEDS) == 14
    assert SECTOR_LABEL[NHOM] == "✈️ Hàng không & Logistics"


# ── 2. hành vi (bản giả của `_doc_feed`, không mạng) ─────────────────────────────────────────────────────────────────
def _entry(i: int, tien_to: str):
    return types.SimpleNamespace(title=f"{tien_to} bài {i}", summary=f"tóm tắt {tien_to} {i}",
                                 published=f"Mon, 16 Nov 2026 0{i}:00:00 +07", link=f"https://baoxaydung.vn/{tien_to}-{i}.htm")


def _doc_feed_gia(monkeypatch):
    """`_doc_feed` giả: hai địa chỉ baoxaydung trả 6 bài; mọi địa chỉ khác trả rỗng (để biết bài nào lọt đi đâu)."""
    da_goi = []

    def gia(url, dung_bo_nho=True):
        da_goi.append(url)
        if url == HANG_KHONG:
            return [_entry(i, "hk") for i in range(6)]
        if url == HANG_HAI:
            return [_entry(i, "hh") for i in range(6)]
        return []
    monkeypatch.setattr(nc, "_doc_feed", gia)
    return da_goi


def test_nhom_hang_khong_nhan_toi_da_bon_bai_moi_nguon_va_dung_nhan(monkeypatch):
    da_goi = _doc_feed_gia(monkeypatch)
    kq = nc.SectorNewsAgent().collect()
    bai = kq[NHOM]
    assert len(bai) == 8                                  # 2 nguồn × max_items 4 (không phải 6)
    assert [b.title for b in bai] == [f"hk bài {i}" for i in range(4)] + [f"hh bài {i}" for i in range(4)]
    assert {b.category for b in bai} == {NHOM}
    assert {b.source for b in bai} == {"BaoXayDung"}
    assert {b.region for b in bai} == {"domestic"}
    assert all(b.url.startswith("https://baoxaydung.vn/") for b in bai)
    assert HANG_KHONG in da_goi and HANG_HAI in da_goi


def test_khong_bai_nao_lot_sang_nhom_khac(monkeypatch):
    _doc_feed_gia(monkeypatch)
    kq = nc.SectorNewsAgent().collect()
    assert {k: len(v) for k, v in kq.items() if k != NHOM} == {k: 0 for k in nc.SectorNewsAgent.SECTOR_FEEDS if k != NHOM}


def test_goi_tin_cong_dung_tam_bai_cua_nhom_vao_total_articles(monkeypatch):
    """`total_articles` = trong nước + quốc tế + vĩ mô + MỌI nhóm ngành (`news_collectors.py`, `collect_and_handoff`).
    Chỉ hai nguồn này trả bài thì tổng đúng 8 và gói tin `OK`."""
    _doc_feed_gia(monkeypatch)
    goi = nc.NewsOrchestrator("ACV").collect_and_handoff()
    assert len(goi.sector_news[NHOM]) == 8
    assert goi.domestic_news == [] and goi.international_news == [] and goi.macro_news == []
    assert goi.total_articles == 8
    assert goi.status == "OK"


# ── 3. điểm KHÔNG đổi ───────────────────────────────────────────────────────────────────────────────────────────────
def _tin(tieu_de, huong, nhom=NHOM):
    return nc.NewsItem(title=tieu_de, summary="", source="BaoXayDung", category=nhom, region="domestic",
                       published="", url="https://baoxaydung.vn/x.htm", sentiment_hint=huong)


def _goi(co_hang_khong: bool):
    bai_hk = [_tin(f"hk dương {i}", "POSITIVE") for i in range(8)] if co_hang_khong else []
    return nc.NewsPacket(symbol="ACV", sector_news={NHOM: bai_hk, "banking": [], "global_macro": []},
                         total_articles=len(bai_hk))


def test_diem_tong_va_diem_agent_khong_doi_khi_nhom_hang_khong_co_bai():
    """Tám bài TÍCH CỰC trong nhóm hàng không không nhích `sentiment_score` hay `score` nào; chỉ phần hiển thị
    (`sector_sentiment`, `total_articles`) đổi."""
    co = NewsSentimentAgent().analyze(_goi(True))
    khong = NewsSentimentAgent().analyze(_goi(False))
    assert co["sentiment_score"] == khong["sentiment_score"]
    assert co["score"] == khong["score"]
    assert co["overall_sentiment"] == khong["overall_sentiment"]
    assert co["breakdown"] == khong["breakdown"]
    # chỉ phần hiển thị đổi — và đổi THẬT (máy đo này CÓ khả năng thấy một thay đổi)
    assert co["sector_sentiment"][NHOM]["total"] == 8 and khong["sector_sentiment"][NHOM]["total"] == 0
    assert co["sector_sentiment"][NHOM]["positive"] == 8
    assert co["total_articles"] == 8 and khong["total_articles"] == 0
    assert len(co["top_positive"]) == 5 and khong["top_positive"] == []


def test_phep_do_diem_co_kha_nang_thay_nhom_khac():
    """Trước khi tin kết quả ÂM (SKILL, Bước 3 điều 4): cùng bài TÍCH CỰC đặt vào nhóm `banking` PHẢI làm điểm nhích."""
    bai = [_tin(f"nh dương {i}", "POSITIVE", "banking") for i in range(8)]
    goi = nc.NewsPacket(symbol="ACV", sector_news={"banking": bai}, total_articles=8)
    rong = nc.NewsPacket(symbol="ACV", sector_news={"banking": []}, total_articles=0)
    assert NewsSentimentAgent().analyze(goi)["sentiment_score"] > NewsSentimentAgent().analyze(rong)["sentiment_score"]


def test_chi_bon_nhom_vao_diem_tong_va_khong_co_hang_khong():
    """AST của `news_sentiment_agent.analyze`: vòng `for key in [...]` là danh sách chữ đúng bốn nhóm."""
    cay = ast.parse((GOC / "news_sentiment_agent.py").read_text(encoding="utf-8"))
    danh_sach = []
    for n in ast.walk(cay):
        if isinstance(n, ast.For) and isinstance(n.target, ast.Name) and n.target.id == "key" \
                and isinstance(n.iter, ast.List):
            danh_sach.append([e.value for e in n.iter.elts if isinstance(e, ast.Constant)])
    assert danh_sach == [["global_macro", "securities_finance", "banking", "macro"]]


# ── 4. đường quét không nhập news_collectors ────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("tep", ["run_daily.py", "paper_runner.py", "paper_trading.py", "san_dau.py"])
def test_duong_quet_khong_nhap_news_collectors(tep):
    cay = ast.parse((GOC / tep).read_text(encoding="utf-8"))
    nhap = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            nhap |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            nhap.add(n.module.split(".")[0])
    assert "news_collectors" not in nhap and "news_sentiment_agent" not in nhap
