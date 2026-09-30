"""Đo token của một phiên Claude Code — từ transcript `.jsonl`, không suy.

Vì sao có: hạn mức 5 giờ chạm nhanh, và câu hỏi "code sinh ra nhiều" tưởng
là nguyên nhân. Đo (BƯỚC 145, 30/09/2026) cho thấy thứ đốt hạn mức là
**kích thước ngữ cảnh × số lượt gọi API**: mỗi lượt gọi công cụ gửi lại toàn
bộ ngữ cảnh (~465k token ở hai phiên dự án), 98,5–98,7% token xử lý là ĐỌC LẠI
cache, còn output chưa tới 1%.

Hai chế độ:

    tools/do_token_phien.py <phien.jsonl> [...]   thống kê từng phiên
    tools/do_token_phien.py --tai-lieu            kích cỡ tài liệu nạp tự động

Transcript nằm ở ``~/.claude/projects/<thư mục dự án>/<id phiên>.jsonl``.

Ba điều phải biết khi đọc số:

1. Mỗi khối trả lời được ghi nhiều dòng (một dòng mỗi khối nội dung) với CÙNG
   ``message.id`` và CÙNG ``usage``. Cộng theo dòng là đếm lặp 2–3 lần; số
   đầu tiên đo được (1.244 lượt) thực ra là 517 lượt. Nên gộp theo id.
2. "Ghi lại cả cache" = một lượt có ``cache_creation_input_tokens`` vượt
   ``NGUONG_GHI_LAI``. Xảy ra khi phiên nghỉ quá lâu (cache hết hạn) hoặc khi
   tiền tố ngữ cảnh đổi (ví dụ CLAUDE.md đổi trên đĩa).
3. ``TOKEN_MOI_KY_TU`` là ƯỚC LƯỢNG: hiệu chuẩn hai lần từ mục "Memory files"
   của ``get_usage`` (116.978 ký tự ra 39.004 token; 15.666 ký tự ra 5.223).
   Không có bộ đếm token chính thức trên máy này.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path
from statistics import median

GOC = Path(__file__).resolve().parent.parent

#: Một lượt ghi cache vượt ngưỡng này được coi là ghi lại CẢ cache.
NGUONG_GHI_LAI = 200_000

#: Ký tự trên mỗi token của văn bản dự án (tiếng Việt lẫn mã). ƯỚC LƯỢNG.
KY_TU_MOI_TOKEN = 3.0

#: Tài liệu nạp tự động vào ngữ cảnh (tương đối theo gốc repo, hoặc ``~/``).
TAI_LIEU_NAP = (
    "CLAUDE.md",
    ".claude/skills/quy-trinh-lam-viec/SKILL.md",
    "docs/HANDOFF.md",
    "~/.claude/rules/vibe-preview.md",
    "~/.claude/projects/C--Users-cuong/memory/MEMORY.md",
)


def tong_hop(dong: list[str]) -> dict:
    """Thống kê từ các dòng ``.jsonl``. Hàm thuần: không đọc đĩa.

    Gộp theo ``message.id`` (dòng sau đè dòng trước). Dòng hỏng hoặc không có
    ``usage`` bị bỏ qua và được đếm vào ``dong_bo_qua`` để không im lặng.
    """
    theo_id: dict[str, tuple[str, dict]] = {}
    bo_qua = 0
    for i, d in enumerate(dong):
        try:
            o = json.loads(d)
        except ValueError:
            bo_qua += 1
            continue
        m = o.get("message")
        u = m.get("usage") if isinstance(m, dict) else None
        if not u:
            continue
        khoa = m.get("id") or o.get("requestId") or o.get("uuid") or f"dong{i}"
        theo_id[khoa] = ((o.get("timestamp") or "")[:10], u)

    ngu_canh: list[int] = []
    ghi_lai: list[int] = []
    ngay: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    tong = dict.fromkeys(("luot", "ngu_canh", "doc_cache", "ghi_cache", "output"), 0)
    for ng, u in theo_id.values():
        doc = u.get("cache_read_input_tokens", 0)
        ghi = u.get("cache_creation_input_tokens", 0)
        vao = u.get("input_tokens", 0)
        ra = u.get("output_tokens", 0)
        nc = doc + ghi + vao
        ngu_canh.append(nc)
        if ghi > NGUONG_GHI_LAI:
            ghi_lai.append(ghi)
        for ten, v in (("luot", 1), ("ngu_canh", nc), ("doc_cache", doc),
                       ("ghi_cache", ghi), ("output", ra)):
            tong[ten] += v
            ngay[ng][ten] += v
    return {
        **tong,
        "trung_vi_ngu_canh": int(median(ngu_canh)) if ngu_canh else 0,
        "ghi_lai_ca_cache": len(ghi_lai),
        "token_ghi_lai": sum(ghi_lai),
        "theo_ngay": {k: dict(v) for k, v in sorted(ngay.items())},
        "dong_bo_qua": bo_qua,
    }


def uoc_token(so_ky_tu: int) -> int:
    return round(so_ky_tu / KY_TU_MOI_TOKEN)


def kich_co_tai_lieu() -> list[tuple[str, int | None]]:
    """[(tên, số ký tự)] — ``None`` nếu file không có."""
    ra: list[tuple[str, int | None]] = []
    for ten in TAI_LIEU_NAP:
        p = Path(ten).expanduser() if ten.startswith("~") else GOC / ten
        ra.append((ten, len(p.read_text(encoding="utf-8")) if p.exists() else None))
    return ra


def _in_phien(duong: Path) -> None:
    r = tong_hop(duong.read_text(encoding="utf-8").splitlines())
    print(f"== {duong.name[:8]}  {r['luot']:,} lượt API (đã gộp theo id)  "
          f"bỏ qua {r['dong_bo_qua']} dòng hỏng")
    if not r["luot"]:
        print("   KHÔNG có dòng usage nào — đọc nhầm file, hay khác định dạng?")
        return
    doc = r["doc_cache"] * 100 / r["ngu_canh"]
    print(f"   ngữ cảnh xử lý {r['ngu_canh']:,}  (đọc lại cache {r['doc_cache']:,} = "
          f"{doc:.1f}%)  ghi cache {r['ghi_cache']:,}  output {r['output']:,}")
    print(f"   trung vị ngữ cảnh mỗi lượt {r['trung_vi_ngu_canh']:,}  "
          f"ghi lại cả cache {r['ghi_lai_ca_cache']} lần = {r['token_ghi_lai']:,}")
    for ng, v in r["theo_ngay"].items():
        print(f"     {ng or '?':10s} {v['luot']:>5,} lượt  {v['ngu_canh']:>13,} ngữ cảnh"
              f"  {v['ghi_cache']:>10,} ghi cache")


def main(tham_so: list[str]) -> int:
    if tham_so == ["--tai-lieu"]:
        for ten, n in kich_co_tai_lieu():
            print(f"{ten:60s} " + ("THIẾU" if n is None
                                    else f"{n:>8,} ký tự  ~{uoc_token(n):>6,} token (ước)"))
        return 0
    if not tham_so or any(t.startswith("-") for t in tham_so):
        print(__doc__.splitlines()[0])
        return 2
    for t in tham_so:
        _in_phien(Path(t))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
