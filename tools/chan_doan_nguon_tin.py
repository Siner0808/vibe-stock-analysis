"""BƯỚC 278 — CHẨN ĐOÁN vì sao nhiều nguồn tin trả 0 bài. CHỈ ĐỌC trên mã sản xuất; KHÔNG sửa gói tin.

Đọc danh sách nguồn TỪ MÃ (`news_collectors`: `FEEDS` của ba agent, `SECTOR_FEEDS`, và địa chỉ Google News theo
mã bắt bằng cách chặn `_gom_song_song` — không gõ lại URL nào, gác bằng AST trong
`tests/test_chan_doan_nguon_tin_278.py`), tải MỖI địa chỉ ĐÚNG MỘT LẦN với User-Agent, tiêu đề và hạn thời gian của
sản xuất (`_HEADERS_RSS`, `HAN_KET_NOI`, `HAN_DOC`, `HAN_MOT_NGUON`, `TRAN_BYTE_MOT_NGUON`) rồi phân lớp bằng
`phan_loai_nguon_tin.phan_loai`. Nguồn lớp `blocked` hoặc `dead_url` được thử THÊM một lần với User-Agent trình
duyệt (`news_collectors.HEADERS`); cột ấy là CHẨN ĐOÁN, không phải điều app làm.

    ./.venv/Scripts/python.exe tools/chan_doan_nguon_tin.py chay --ghi-thu-muc <thư mục> [--ma VCB FPT HPG]
    ./.venv/Scripts/python.exe tools/chan_doan_nguon_tin.py thu <url> [<url> ...]      (ứng viên thay thế; chỉ đếm khi ≥ 1 bài)
    ./.venv/Scripts/python.exe tools/chan_doan_nguon_tin.py chi-muc <url trang mục RSS>   (liệt kê liên kết .rss/.xml)

Dùng MẠNG (chỉ ba lệnh trên, chỉ khi bạn chạy). Đo từ MỘT địa chỉ IP nhà vào MỘT ngày: IP của Actions và Cloud
chưa đo, chặn theo IP trung tâm dữ liệu có thể có và CHƯA đo. Không ghi file nào ngoài thư mục `--ghi-thu-muc`.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
import time
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin, urlparse

import feedparser
import requests

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(GOC / "tools"))

import news_collectors as nc  # noqa: E402
from phan_loai_nguon_tin import LOP, SO_BYTE_DAU, QuanSat, phan_loai  # noqa: E402

MA_MAC_DINH = ("VCB", "FPT", "HPG")
NGHI_GIUA_HAI_LAN = 0.3          # giây; tải tuần tự, nhẹ tay với máy chủ
LOP_THU_THEM_UA = ("blocked", "dead_url")
COT = ["nhom", "nguon", "the_loai", "url", "lop", "status", "url_cuoi", "chuyen_huong", "content_type",
       "n_byte", "bozo", "bozo_loi", "n_bai", "phien_ban", "thoi_gian_s", "loi", "thong_diep_loi",
       "lop_ua_trinh_duyet", "n_bai_ua_trinh_duyet", "khoa_trung", "so_lan_khai"]


# ── đọc danh sách nguồn TỪ MÃ ───────────────────────────────────────────────
def doc_danh_sach_nguon() -> list[dict]:
    """Mọi nguồn cố định đã khai trong `news_collectors`, theo thứ tự khai (kể cả địa chỉ khai lặp)."""
    ra = []
    for tag, agent in (("Domestic", nc.DomesticNewsAgent), ("International", nc.InternationalNewsAgent)):
        for url, nguon, the_loai, _vung in agent.FEEDS:
            ra.append({"nhom": tag, "url": url, "nguon": nguon, "the_loai": the_loai})
    for url, nguon, the_loai, _vung in nc.MacroDataAgent.FEEDS:
        ra.append({"nhom": "Macro", "url": url, "nguon": nguon, "the_loai": the_loai})
    for nganh, feeds in nc.SectorNewsAgent.SECTOR_FEEDS.items():
        for url, nguon, _vung in feeds:
            ra.append({"nhom": "Sector", "url": url, "nguon": nguon, "the_loai": nganh})
    return ra


def dia_chi_google_news(ma: str) -> list[str]:
    """Ba địa chỉ Google News của một mã, bắt từ `CompanyNewsAgent.collect` (KHÔNG mạng, không gõ lại URL)."""
    bat: list[str] = []
    cu = nc._gom_song_song

    def gia(viec, han=None):
        bat.extend(v[1] for v in viec)
        return [None] * len(viec)

    nc._gom_song_song = gia
    try:
        nc.CompanyNewsAgent().collect(ma)
    finally:
        nc._gom_song_song = cu
    return bat


# ── tải một địa chỉ đúng như sản xuất ───────────────────────────────────────
def tai_mot(url: str, headers: dict | None = None) -> tuple[QuanSat, dict]:
    """Tải MỘT lần và trả (QuanSat, thêm). Cùng cách `news_collectors._tai_noi_dung` tải: cùng tiêu đề, hạn kết
    nối/đọc, trần thời gian và trần byte, rồi `feedparser.parse(byte, response_headers=…)`. Khác: GHI LẠI mã
    trạng thái và chuỗi chuyển hướng (sản xuất bỏ cả hai)."""
    h = nc._HEADERS_RSS if headers is None else headers
    bat_dau = time.monotonic()
    them: dict = {"thoi_gian_s": 0.0, "loi": "", "thong_diep_loi": ""}
    try:
        with requests.get(url, headers=h, timeout=(nc.HAN_KET_NOI, nc.HAN_DOC), stream=True) as r:
            dem = bytearray()
            for khuc in r.iter_content(16384):
                dem += khuc
                if time.monotonic() - bat_dau > nc.HAN_MOT_NGUON:
                    raise TimeoutError(f"nguồn quá {nc.HAN_MOT_NGUON}s: {url}")
                if len(dem) > nc.TRAN_BYTE_MOT_NGUON:
                    raise ValueError(f"nguồn quá {nc.TRAN_BYTE_MOT_NGUON} byte: {url}")
            tieu_de = {k.lower(): v for k, v in r.headers.items()}
            status, url_cuoi = r.status_code, r.url
            chuyen = tuple(x.status_code for x in r.history)
        tieu_de["content-location"] = urljoin(url_cuoi, tieu_de.get("content-location", ""))
        than = bytes(dem)
        d = feedparser.parse(than, response_headers=tieu_de)
        bozo = int(bool(d.get("bozo")))
        q = QuanSat(
            url=url, status=status, url_cuoi=url_cuoi, chuyen_huong=chuyen,
            content_type=tieu_de.get("content-type", ""), n_byte=len(than),
            dau_than=than[:SO_BYTE_DAU].decode("utf-8", errors="replace"),
            bozo=bozo, bozo_loi=type(d.bozo_exception).__name__ if bozo else "",
            n_bai=len(d.entries), phien_ban=d.get("version", ""),
            cf_chan="cf-mitigated" in tieu_de)
    except Exception as e:
        mro = tuple(c.__name__ for c in type(e).__mro__ if c not in (object, BaseException, Exception))
        q = QuanSat(url=url, chuoi_loi=mro or (type(e).__name__,), thong_diep_loi=str(e)[:300])
        them["loi"] = type(e).__name__
        them["thong_diep_loi"] = str(e)[:200]
    them["thoi_gian_s"] = round(time.monotonic() - bat_dau, 2)
    return q, them


def _dong(nguon: dict, q: QuanSat, them: dict) -> dict:
    return {
        **nguon, "lop": phan_loai(q), "status": q.status if q.status is not None else "",
        "url_cuoi": q.url_cuoi, "chuyen_huong": "/".join(map(str, q.chuyen_huong)),
        "content_type": q.content_type, "n_byte": q.n_byte, "bozo": q.bozo, "bozo_loi": q.bozo_loi,
        "n_bai": q.n_bai, "phien_ban": "" if q.phien_ban is None else q.phien_ban,
        "thoi_gian_s": them["thoi_gian_s"], "loi": them["loi"], "thong_diep_loi": them["thong_diep_loi"],
        "lop_ua_trinh_duyet": "", "n_bai_ua_trinh_duyet": "", "khoa_trung": "", "so_lan_khai": 1,
    }


def danh_dau_trung(dong: list[dict]) -> None:
    """Điền `so_lan_khai` (cùng địa chỉ khai nhiều lần) và `khoa_trung` (các địa chỉ KHÁC NHAU cùng một địa
    chỉ cuối khi tải được 2xx; nhóm 1 phần tử thì để trống)."""
    dem = Counter(d["url"] for d in dong)
    for d in dong:
        d["so_lan_khai"] = dem[d["url"]]
    nhom: dict[str, set] = {}
    for d in dong:
        if d["status"] != "" and 200 <= int(d["status"]) < 300 and d["url_cuoi"]:
            nhom.setdefault(d["url_cuoi"], set()).add(d["url"])
    for d in dong:
        if d["url_cuoi"] in nhom and len(nhom[d["url_cuoi"]]) > 1:
            d["khoa_trung"] = d["url_cuoi"]


def chay_het(nguon: list[dict], tai=tai_mot, nghi: float = NGHI_GIUA_HAI_LAN, thu_ua: bool = True) -> list[dict]:
    """Mỗi ĐỊA CHỈ KHÁC NHAU tải một lần; địa chỉ khai lặp dùng lại kết quả (cùng QuanSat, cùng thời gian)."""
    da: dict[str, tuple[QuanSat, dict]] = {}
    dong = []
    for n in nguon:
        if n["url"] not in da:
            if da and nghi:
                time.sleep(nghi)
            da[n["url"]] = tai(n["url"])
        q, them = da[n["url"]]
        d = _dong(n, q, them)
        dong.append(d)
    if thu_ua:
        thu: dict[str, tuple[str, int]] = {}
        for d in dong:
            if d["lop"] in LOP_THU_THEM_UA and d["url"] not in thu:
                if nghi:
                    time.sleep(nghi)
                q2, _ = tai(d["url"], nc.HEADERS)
                thu[d["url"]] = (phan_loai(q2), q2.n_bai)
        for d in dong:
            if d["url"] in thu:
                d["lop_ua_trinh_duyet"], d["n_bai_ua_trinh_duyet"] = thu[d["url"]]
    danh_dau_trung(dong)
    return dong


def dem_lop(dong: list[dict]) -> tuple[Counter, Counter]:
    """(đếm theo địa chỉ KHAI — gồm khai lặp, đếm theo địa chỉ DUY NHẤT)."""
    theo_khai = Counter(d["lop"] for d in dong)
    duy_nhat = {}
    for d in dong:
        duy_nhat.setdefault(d["url"], d["lop"])
    return theo_khai, Counter(duy_nhat.values())


def viet_bang(dong: list[dict], thu_muc: Path, ten: str = "bang_tung_nguon") -> None:
    thu_muc.mkdir(parents=True, exist_ok=True)
    with open(thu_muc / f"{ten}.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COT)
        w.writeheader()
        w.writerows(dong)
    theo_khai, duy_nhat = dem_lop(dong)
    dong_md = ["| lớp | số lần khai | số địa chỉ duy nhất |", "|---|---:|---:|"]
    for lop in LOP:
        dong_md.append(f"| {lop} | {theo_khai.get(lop, 0)} | {duy_nhat.get(lop, 0)} |")
    dong_md.append(f"| **tổng** | {len(dong)} | {len({d['url'] for d in dong})} |")
    (thu_muc / f"{ten}_dem_lop.md").write_text("\n".join(dong_md) + "\n", encoding="utf-8")


# ── tìm liên kết RSS trên trang mục ─────────────────────────────────────────
LIEN_KET_RSS = re.compile(r"""href\s*=\s*["']([^"'#>\s]+?\.(?:rss|xml))(?:\?[^"'#>\s]*)?["']""", re.I)


def tim_lien_ket_rss(html: str, goc: str) -> list[str]:
    """Liên kết `.rss`/`.xml` trong `href`, đã nối với địa chỉ trang, bỏ trùng, giữ thứ tự."""
    ra, thay = [], set()
    for m in LIEN_KET_RSS.finditer(html):
        u = urljoin(goc, m.group(1))
        if u not in thay and urlparse(u).scheme in ("http", "https"):
            thay.add(u)
            ra.append(u)
    return ra


def _main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sp = ap.add_subparsers(dest="lenh", required=True)
    c = sp.add_parser("chay")
    c.add_argument("--ghi-thu-muc", required=True)
    c.add_argument("--ma", nargs="+", default=list(MA_MAC_DINH))
    c.add_argument("--khong-thu-ua", action="store_true")
    t = sp.add_parser("thu")
    t.add_argument("url", nargs="+")
    m = sp.add_parser("chi-muc")
    m.add_argument("url")
    a = ap.parse_args()

    if a.lenh == "chay":
        nguon = doc_danh_sach_nguon()
        for ma in a.ma:
            nguon += [{"nhom": f"GoogleNews:{ma}", "url": u, "nguon": "GoogleNews", "the_loai": "corporate"}
                      for u in dia_chi_google_news(ma)]
        dong = chay_het(nguon, thu_ua=not a.khong_thu_ua)
        viet_bang(dong, Path(a.ghi_thu_muc))
        theo_khai, duy_nhat = dem_lop(dong)
        for d in dong:
            print(f"{d['lop']:<14} {d['status']!s:>3} bài={d['n_bai']:<3} {d['nhom'][:14]:<14} {d['url']}")
        print("\nTheo địa chỉ khai:", dict(theo_khai), "tổng", len(dong))
        print("Theo địa chỉ duy nhất:", dict(duy_nhat), "tổng", len({d['url'] for d in dong}))
        return 0
    if a.lenh == "thu":
        for u in a.url:
            q, them = tai_mot(u)
            print(f"{phan_loai(q):<14} {q.status!s:>4} bài={q.n_bai:<3} byte={q.n_byte:<7} "
                  f"cuối={q.url_cuoi or '-'} {them['loi']} {u}")
            print("      đầu thân:", " ".join(q.dau_than[:160].split()) or "-", "| bozo:", q.bozo_loi or "-")
            time.sleep(NGHI_GIUA_HAI_LAN)
        return 0
    r = requests.get(a.url, headers=nc._HEADERS_RSS, timeout=(nc.HAN_KET_NOI, nc.HAN_DOC + 5))
    print(f"trang mục: {r.status_code} {r.url} ({len(r.content)} byte)")
    for u in tim_lien_ket_rss(r.text, r.url):
        print(u)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
