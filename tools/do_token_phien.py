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
import bisect
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

GOC = Path(__file__).resolve().parent.parent

#: Một lượt ghi cache vượt ngưỡng này được coi là ghi lại CẢ cache.
NGUONG_GHI_LAI = 200_000

#: Ký tự trên mỗi token của văn bản dự án (tiếng Việt lẫn mã). ƯỚC LƯỢNG.
KY_TU_MOI_TOKEN = 3.0

#: Một khối ảnh trong ``tool_result`` quy đổi sang chừng này ký tự. ƯỚC LƯỢNG:
#: ảnh không đếm theo độ dài base64 mà theo kích thước ảnh.
KY_TU_MOI_ANH = 1500

#: Loại đính kèm KHÔNG vào ngữ cảnh của mô hình. Suy ra, chưa có tài liệu
#: chính thức: cộng ``prompt_snapshot`` vào thì phần "Messages" ước ra 353k
#: token, vượt 316k mà ``get_usage`` báo; bỏ nó thì ra 287k, gần hơn nhiều.
LOAI_TRU = frozenset({"att:prompt_snapshot"})

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


def _do_dai_ket_qua(noi_dung) -> int:
    if isinstance(noi_dung, str):
        return len(noi_dung)
    if not isinstance(noi_dung, list):
        return 0
    return sum(len(x.get("text", "")) if x.get("type") == "text" else KY_TU_MOI_ANH
               for x in noi_dung if isinstance(x, dict))


def _muc_cua_dong(o: dict, ten_cong_cu: dict) -> list[tuple[str, int]]:
    """[(nhãn nguồn, số ký tự)] mà MỘT dòng transcript đưa vào ngữ cảnh."""
    ra: list[tuple[str, int]] = []
    kieu = o.get("type")
    if kieu == "attachment":
        a = o.get("attachment") or {}
        ra.append(("att:" + str(a.get("type")), len(json.dumps(a, ensure_ascii=False))))
        return ra
    m = o.get("message")
    c = m.get("content") if isinstance(m, dict) else None
    if isinstance(c, str):
        ra.append((f"{kieu}:text", len(c)))
    elif isinstance(c, list):
        for b in c:
            if not isinstance(b, dict):
                continue
            loai = b.get("type")
            if loai == "tool_use":
                ten_cong_cu[b.get("id")] = b.get("name", "?")
                ra.append(("tool_use_input", len(json.dumps(b.get("input"), ensure_ascii=False))))
            elif loai == "tool_result":
                ten = ten_cong_cu.get(b.get("tool_use_id"), "?")
                if ten.startswith("mcp__"):
                    ten = ten.split("__")[-1]
                ra.append(("result:" + ten, _do_dai_ket_qua(b.get("content"))))
            elif loai == "text":
                ra.append((f"{kieu}:text", len(b.get("text", ""))))
    return ra


def xep_hang(dong: list[str]) -> dict:
    """Xếp hạng nguồn ngữ cảnh theo **token-lượt** = ký tự/3 × số lượt API còn lại.

    Một thứ nhỏ nhưng vào sớm tốn hơn một thứ lớn vào muộn, vì nó bị gửi lại ở
    MỌI lượt gọi sau đó. Reset ở mỗi lần compact: nội dung trước đó không còn
    trong ngữ cảnh. Hàm thuần. ``tong`` là ước lượng (3,0 ký tự/token).
    """
    hang = [json.loads(d) for d in dong if d.strip().startswith("{")]
    moc = [i for i, o in enumerate(hang)
           if o.get("isCompactSummary")
           or (o.get("type") == "system" and o.get("subtype") == "compact_boundary")]
    gioi = [0] + moc + [len(hang)]
    chi_phi: Counter = Counter()
    luot = 0
    for dau, cuoi in zip(gioi, gioi[1:]):
        doan = hang[dau:cuoi]
        da_thay: set = set()
        vi_tri: list[int] = []
        for i, o in enumerate(doan):
            m = o.get("message")
            if isinstance(m, dict) and m.get("usage"):
                khoa = m.get("id") or o.get("uuid") or f"dong{i}"
                if khoa not in da_thay:
                    da_thay.add(khoa)
                    vi_tri.append(i)
        n = len(vi_tri)
        luot += n
        ten_cong_cu: dict = {}
        for i, o in enumerate(doan):
            con_lai = n - bisect.bisect_right(vi_tri, i)
            for nhan, so_ky_tu in _muc_cua_dong(o, ten_cong_cu):
                if con_lai > 0 and nhan not in LOAI_TRU:
                    chi_phi[nhan] += so_ky_tu / KY_TU_MOI_TOKEN * con_lai
    return {"luot": luot, "tong": sum(chi_phi.values()), "theo_nguon": dict(chi_phi)}


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


def _in_xep_hang(duong: list[Path]) -> None:
    r: dict = {"luot": 0, "tong": 0.0, "theo_nguon": Counter()}
    for p in duong:             # MỖI file một lượt: đoạn compact không được nối qua file
        x = xep_hang(p.read_text(encoding="utf-8").splitlines())
        r["luot"] += x["luot"]
        r["tong"] += x["tong"]
        r["theo_nguon"].update(x["theo_nguon"])
    print(f"{r['luot']:,} lượt API · {r['tong'] / 1e6:,.1f}M token-lượt nội dung (ước)")
    for nhan, v in sorted(r["theo_nguon"].items(), key=lambda x: -x[1])[:16]:
        print(f"  {nhan:36s} {v / 1e6:8.1f}M  {v * 100 / r['tong']:5.1f}%")


def main(tham_so: list[str]) -> int:
    if tham_so[:1] == ["--xep-hang"] and len(tham_so) > 1:
        _in_xep_hang([Path(t) for t in tham_so[1:]])
        return 0
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
