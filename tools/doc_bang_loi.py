"""Đọc bảng lỗi thành SỐ — lớp nào đã đóng, phát hiện nhanh lên hay chậm đi.

    ./.venv/Scripts/python.exe tools/doc_bang_loi.py

VÌ SAO CÓ FILE NÀY
──────────────────
`references/loi-da-mac.md` hỏi *"máy chặn được không"* và **không** hỏi
hai điều quyết định: lỗi thuộc **LỚP** nào, và nó **SỐNG BAO LÂU** trước
khi bị bắt.

Thiếu hai thứ đó thì câu hỏi *"quy trình có khoẻ lên không"* phải dựng
lại phân tích từ đầu mỗi lần — đúng lỗi **"không có lệnh thì không có
số"**, lần này áp lên chính bảng lỗi.

Bảng ở lại nguyên vẹn cho NGƯỜI đọc; phần máy đọc nằm ở
`docs/loi-phan-lop.json`. Tách ra có chủ đích: sửa 34 dòng markdown là
đúng loại thao tác đã sinh ra lỗi 1–3.

CÁCH ĐỌC KẾT QUẢ
────────────────
**Số lỗi mỗi ngày KHÔNG phải thước.** Nó tăng khi ta đào kỹ hơn. Hai
thước thật:

  1. lop nao con SINH RA loi moi, lop nao da im
  2. TUOI THO — mot loi song bao lau truoc khi bi bat

Tuổi thọ giảm nghĩa là lưới dày lên, kể cả khi số lỗi không giảm.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

GOC = pathlib.Path(__file__).resolve().parent.parent
BANG = GOC / ".claude" / "skills" / "quy-trinh-lam-viec" / "references" / "loi-da-mac.md"
PHAN_LOP = GOC / "docs" / "loi-phan-lop.json"

RE_DONG = re.compile(r"^\|\s*(\d+)\s*\|(.*)$")


def tach_cot(dong: str) -> list[str]:
    """Tách một dòng bảng markdown, TÔN TRỌNG dấu `\\|` đã thoát.

    Tách thô bằng `split("|")` cắt nhầm ngay giữa `pytest \\| tail` — hai
    dòng của bảng này viết như vậy. Hậu quả không phải một ô lệch: nó
    đẩy MỌI cột sau đó sang một bậc, nên cột "máy chặn?" bị đọc thành
    cột khác và con số tổng sai đúng hai đơn vị.

    Đây là lỗi 30 ở một chỗ mới: đọc SỰ XUẤT HIỆN của ký tự `|` thay vì
    vai trò NGĂN CỘT của nó.
    """
    ra, hien, i = [], [], 0
    while i < len(dong):
        c = dong[i]
        if c == "\\" and i + 1 < len(dong) and dong[i + 1] == "|":
            hien.append("|")
            i += 2
            continue
        if c == "|":
            ra.append("".join(hien).strip())
            hien = []
            i += 1
            continue
        hien.append(c)
        i += 1
    ra.append("".join(hien).strip())
    return ra


def doc_bang(duong: pathlib.Path = BANG) -> dict[str, dict]:
    """{số hiệu: {mo_ta, may_chan}} từ bảng markdown. Hàm THUẦN trên file."""
    ra: dict[str, dict] = {}
    for dong in duong.read_text(encoding="utf-8").splitlines():
        m = RE_DONG.match(dong)
        if not m:
            continue
        cot = tach_cot(m.group(2))
        if len(cot) < 3:
            continue
        ra[m.group(1)] = {"mo_ta": cot[0], "may_chan": cot[2]}
    return ra


def doc_phan_lop(duong: pathlib.Path = PHAN_LOP) -> dict:
    return json.loads(duong.read_text(encoding="utf-8"))


# ─────────────── dòng khai tổng, và vì sao phải kiểm nó ───────────────
#
# Cuối bảng có một câu dạng "Hai mươi mốt trên ba mươi tư máy chặn được."
# Câu ấy được viết bằng CHỮ, nên không máy nào từng đối chiếu nó với
# bảng — và nó đã trôi.
#
# Đo 11/09/2026 bằng cách dựng lại từng bản trong git:
#
#   d019f9f  07/09  "Tam tren muoi ba"        that 8/13   dung
#   910dcf7  08/09  "Tam tren muoi bon"       that 7/14   LECH tu day
#   955fc6b  10/09  "Muoi ba tren hai muoi bon" that 12/24
#   HEAD     11/09  "Hai muoi hai tren ba muoi tu" that 21/34
#
# Lệch đúng +1 suốt ba ngày, vì con số được CỘNG DỒN mỗi lần thêm một
# dòng thay vì ĐẾM LẠI. Đó là lỗi 35, và nó ở đúng lớp `chua-do`.
_DON_VI = {
    "không": 0, "một": 1, "hai": 2, "ba": 3, "bốn": 4, "năm": 5,
    "sáu": 6, "bảy": 7, "tám": 8, "chín": 9,
    # biến thể chỉ xuất hiện SAU hàng chục
    "mốt": 1, "tư": 4, "lăm": 5,
}


def so_tu_chu(cum: str) -> int | None:
    """Đổi số viết bằng chữ tiếng Việt (0–99) sang số. Trả None nếu không đọc được.

    Có `mốt`/`tư`/`lăm` vì tiếng Việt đổi dạng đơn vị sau hàng chục:
    hai mươi **mốt**, ba mươi **tư**, hai mươi **lăm**.
    """
    t = cum.lower().split()
    if not t or len(t) > 3:
        return None
    if t[0] == "mười":                       # 10..19
        if len(t) == 1:
            return 10
        if len(t) > 2:                       # "mười ba bốn" là rác
            return None
        d = _DON_VI.get(t[1])
        return None if d is None else 10 + d
    chuc = _DON_VI.get(t[0])
    if chuc is None:
        return None
    if len(t) == 1:
        return chuc
    if t[1] != "mươi":                       # 0..9 rồi tới chữ khác
        return None
    if len(t) == 2:
        return chuc * 10
    d = _DON_VI.get(t[2])
    return None if d is None else chuc * 10 + d


RE_KHAI = re.compile(r"\*\*([^*]+?)\s+trên\s+([^*]+?)\s+máy chặn được")


def doc_dong_khai(duong: pathlib.Path = BANG) -> tuple[int, int] | None:
    """(số máy chặn được, tổng) mà BẢNG TỰ KHAI. None nếu không đọc được."""
    m = RE_KHAI.search(duong.read_text(encoding="utf-8"))
    if not m:
        return None
    a, b = so_tu_chu(m.group(1)), so_tu_chu(m.group(2))
    return None if a is None or b is None else (a, b)


def doi_chieu(bang: dict, phan_lop: dict) -> tuple[list[str], list[str]]:
    """(số hiệu thiếu phân lớp, số hiệu phân lớp thừa). Hàm THUẦN."""
    co = set(phan_lop.get("loi", {}))
    thieu = sorted(set(bang) - co, key=int)
    thua = sorted(co - set(bang), key=int)
    return thieu, thua


def quyet_dinh(chan: int, tong: int,
               khai: tuple[int, int] | None) -> tuple[int, str]:
    """PHÉP PHÁN về dòng tự khai. Trả (mã thoát, thông báo). Hàm THUẦN.

    Tách khỏi `main()` vì đục thử 11/09/2026: gỡ phép đối chiếu ra khỏi
    `main()` mà mọi phép kiểm vẫn XANH — chúng gọi thẳng
    `doc_dong_khai()`, không đi qua mã thoát. Một phép kiểm không đi qua
    đường mà người dùng thật đi là một phép kiểm mù.

    Ba trạng thái, cùng lối `kiem_so_test_khong_giam.quyet_dinh`:
    0 khớp · 1 lệch · 2 chưa kiểm được.
    """
    if khai is None:
        return 2, "CHƯA KIỂM ĐƯỢC — không đọc được dòng tự khai ở cuối bảng"
    if khai == (chan, tong):
        return 0, f"khớp dòng tự khai ở cuối bảng ({chan}/{tong})"
    return 1, (f"BẢNG TỰ KHAI {khai[0]}/{khai[1]} — ĐẾM ĐƯỢC {chan}/{tong}\n"
               f"  Sửa dòng khai ở cuối bảng. Đừng cộng dồn — ĐẾM LẠI.")


def _vach(n: int, tran: int = 28) -> str:
    return "█" * min(n, tran)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if not BANG.exists() or not PHAN_LOP.exists():
        print("CHUA KIEM DUOC — thieu bang loi hoac file phan lop.",
              file=sys.stderr)
        return 2

    bang = doc_bang()
    pl = doc_phan_lop()
    loi = pl["loi"]
    ten_lop = pl["_lop"]

    thieu, thua = doi_chieu(bang, pl)
    if thieu or thua:
        if thieu:
            print(f"CHAN: {len(thieu)} lỗi trong bảng chưa có phân lớp: "
                  f"{thieu}", file=sys.stderr)
        if thua:
            print(f"CHAN: {len(thua)} mục phân lớp không có dòng bảng nào: "
                  f"{thua}", file=sys.stderr)
        print("Sửa `docs/loi-phan-lop.json` cho khớp bảng rồi chạy lại.",
              file=sys.stderr)
        return 1

    print(f"{len(bang)} lỗi · phân lớp đầy đủ\n")

    # ── theo LỚP ───────────────────────────────────────────────
    print("LỚP — lớp nào còn sinh ra lỗi mới")
    print("─" * 64)
    theo_lop: dict[str, list[str]] = {k: [] for k in ten_lop}
    for so, v in loi.items():
        theo_lop.setdefault(v["lop"], []).append(so)
    for lop in sorted(theo_lop, key=lambda k: -len(theo_lop[k])):
        ds = sorted(theo_lop[lop], key=int)
        moi_nhat = max(int(x) for x in ds)
        print(f"  {lop:10s} {len(ds):3d}  {_vach(len(ds))}")
        print(f"  {'':10s}      lỗi mới nhất của lớp: #{moi_nhat}")
    print()

    # ── TUỔI THỌ ───────────────────────────────────────────────
    print("TUỔI THỌ — một lỗi sống bao lâu trước khi bị bắt")
    print("─" * 64)
    do_duoc = {s: v["song_ngay"] for s, v in loi.items()
               if v.get("song_ngay") is not None}
    chua = [s for s, v in loi.items() if v.get("song_ngay") is None]
    cung_phien = [s for s, n in do_duoc.items() if n == 0]
    qua_ngay = {s: n for s, n in do_duoc.items() if n > 0}

    print(f"  bắt CÙNG PHIÊN        : {len(cung_phien):3d}/{len(do_duoc)}")
    print(f"  sống qua ≥1 ngày      : {len(qua_ngay):3d}")
    if qua_ngay:
        lau = sorted(qua_ngay.items(), key=lambda kv: -kv[1])
        print(f"  lâu nhất              : "
              + " · ".join(f"#{s} {n}d" for s, n in lau[:5]))
    if chua:
        print(f"  CHƯA ĐO               : {len(chua)} (#{', #'.join(chua)})")
    print()

    # ── nguồn của con số ───────────────────────────────────────
    ma_thoat_la = 0
    print("NGUỒN của tuổi thọ — con số nào có lệnh đứng sau")
    print("─" * 64)
    theo_nguon: dict[str, int] = {}
    for v in loi.values():
        theo_nguon[v["nguon"]] = theo_nguon.get(v["nguon"], 0) + 1
    la = sorted(set(theo_nguon) - set(pl["_nguon_tuoi"]))
    for ng in sorted(theo_nguon, key=lambda k: -theo_nguon[k]):
        # Mot gia tri ngoai tu vung tung lam ham nay no KeyError giua chung
        # bang (12/09/2026). Gac `test_bang_loi_do_duoc` VAN bat duoc, nhung
        # nguoi chay dung cu chi thay mot traceback. Noi ra ten no.
        mo_ta = pl["_nguon_tuoi"].get(ng, "⚠️ NGOAI TU VUNG `_nguon_tuoi`")
        print(f"  {ng:14s} {theo_nguon[ng]:3d}   {mo_ta}")
    if la:
        print()
        print(f"  ⚠️ {len(la)} nguồn NGOÀI từ vựng: {', '.join(la)}")
        print("     Thêm vào `_nguon_tuoi`, hoặc sửa dòng phân lớp.")
        # Thoát 0 ở đây là một cổng xanh GIẢ: dữ liệu không nhất quán
        # mà công cụ vẫn nói "xong". Gác `test_bang_loi_do_duoc` có bắt,
        # nhưng người chạy tay thì chỉ thấy một dòng cảnh báo trôi qua.
        ma_thoat_la = 1
    print()

    # ── máy chặn được ──────────────────────────────────────────
    chan = sum(1 for v in bang.values() if v["may_chan"].startswith("✅"))
    print(f"MÁY CHẶN ĐƯỢC: {chan}/{len(bang)}")

    ma, loi_nhan = quyet_dinh(chan, len(bang), doc_dong_khai())
    if ma == 0:
        print(f"  ✅ {loi_nhan}")
    else:
        print(f"  {'❌' if ma == 1 else '⚠'} {loi_nhan}", file=sys.stderr)

    print()
    print("Số lỗi mỗi ngày KHÔNG phải thước — nó tăng khi ta đào kỹ hơn.")
    print("Hai thước thật: lớp nào đã im, và tuổi thọ có ngắn lại không.")
    # Một nguồn ngoài từ vựng cũng là dữ liệu không nhất quán, và công cụ
    # KHÔNG được nói "xong" trên nó — đó đúng là hình dạng cổng xanh giả.
    return ma or ma_thoat_la


if __name__ == "__main__":
    sys.exit(main())
