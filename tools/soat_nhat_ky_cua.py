"""Đọc nhật ký cửa Bash — và THỬ một luật ứng viên trên QUẦN THỂ THẬT.

VÌ SAO CÓ FILE NÀY
──────────────────
Ngày 14/09/2026 câu *"nới luật này có bắt nhầm không"* cắn hai lần:

```
loi 49   do ty le bat nham tren 69 DONG LENH TRONG TAI LIEU, roi doc thanh
         "noi la an toan". Sai QUAN THE — luat vua noi chan ngay lenh ke
         tiep, mot doan Python chay bang heredoc.
BUOC 65  noi ba luat nua. Van phai do tren PROXY, vi khong co gi khac.
```

Quần thể đúng là **những lệnh thật sự được gõ**. Cửa Bash thấy hết chúng,
nhưng tới 14/09/2026 nó **không ghi gì** — nên quần thể ấy không tồn tại
dưới dạng đọc được.

Nay `cua_bash_an_toan.ghi_nhat_ky()` ghi mỗi lượt một dòng JSON, ở **cả
ba** ngả `CHO-QUA` · `CHAN` · `THOAT`. Ghi cả ngả CHO-QUA mới là chỗ
quyết định: một nhật ký chỉ có mẫu XẤU thì vẫn không trả lời được câu
*"nới ra thì bắt NHẦM cái gì"*.

GIỚI HẠN, KHAI THẲNG
────────────────────
Nhật ký **bắt đầu từ 14/09/2026**. Mọi lệnh gõ trước đó không có ở đây, và
không dựng lại được. Nên hôm nay nó gần như rỗng; giá trị của nó là **từ
mai trở đi**. Nói ra để không ai đọc một con số nhỏ ở đây thành *"luật này
hiếm khi chặn"*.

Và nó nằm trong TEMP, **ngoài repo** — nội dung là đúng thứ đã gõ vào
Bash, nên nó không bao giờ được commit.

THỬ MỘT LUẬT ỨNG VIÊN
─────────────────────
```
tools/soat_nhat_ky_cua.py --thu-luat pytest-qua-ong --mau "\\bpytest\\b[^|\\n]*\\|"
```

Mẫu ứng viên được **thay vào đúng chỗ luật cũ** rồi chạy qua `kiem()`, nên
nó đi qua **cùng phạm vi đọc** (bản đã bóc · bản giữ nháy · bản thô). So
hai bản trên cùng một lệnh, không dựng lại phép phán ở đây — dựng lại là
đúng bẫy *"test KIỂM LẠI CHÍNH NÓ"*.
"""
import argparse
import json
import re
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(GOC / "tools"))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import cua_bash_an_toan as cb  # noqa: E402


def doc_nhat_ky(duong: Path) -> list[dict]:
    """Mỗi dòng một bản ghi. Dòng hỏng thì BỎ QUA và ĐẾM, không nuốt im."""
    if not duong.exists():
        return []
    ra, hong = [], 0
    for dong in duong.read_text(encoding="utf-8", errors="replace").splitlines():
        if not dong.strip():
            continue
        try:
            ra.append(json.loads(dong))
        except Exception:
            hong += 1
    if hong:
        print(f"⚠️  {hong} dong hong, da bo qua", file=sys.stderr)
    return ra


def thu_mau(ten_luat: str, mau_moi: str, lenh: str) -> list[str]:
    """Tên luật nào khớp `lenh` NẾU `ten_luat` mang mẫu `mau_moi`.

    Thay thẳng vào `LUAT` rồi gọi `kiem()` — để phép thử đi qua ĐÚNG
    phạm vi đọc mà luật ấy khai (`DOC_THO` · `DOC_GIU_NHAY` · `DOC_BOC`
    · mặc định). Dựng lại phép phán ở đây là đúng bẫy *"test KIỂM LẠI
    CHÍNH NÓ"* trong `CLAUDE.md`.
    """
    cu = cb.LUAT
    try:
        cb.LUAT = [(t, re.compile(mau_moi) if t == ten_luat else b, v)
                   for t, b, v in cu]
        return [t for t, _ in cb.kiem(lenh)]
    finally:
        cb.LUAT = cu


def _thong_ke(bg: list[dict]) -> None:
    from collections import Counter

    phan = Counter(b.get("phan", "?") for b in bg)
    print(f"{len(bg)} luot cua duoc goi")
    for k in ("CHO-QUA", "CHAN", "THOAT"):
        print(f"   {k:8s} {phan.get(k, 0):5d}")
    luat = Counter(t for b in bg for t in b.get("luat", []))
    if luat:
        print("\nLUAT nao chan, va bao nhieu lan:")
        for t, n in luat.most_common():
            print(f"   {t:26s} {n}")
    else:
        print("\nchua luat nao chan lan nao")


def _thu(bg: list[dict], ten: str, mau: str) -> int:
    co = {t for t, _, _ in cb.LUAT}
    if ten not in co:
        print(f"CHUA KIEM DUOC — khong co luat ten {ten!r}. Dang co: "
              f"{sorted(co)}", file=sys.stderr)
        return 2
    try:
        re.compile(mau)
    except re.error as e:
        print(f"CHUA KIEM DUOC — mau khong bien dich duoc: {e}",
              file=sys.stderr)
        # bia-ok: 2 KHONG phai mot ket qua do duoc — no la ma "CHUA KIEM
        # DUOC" cua du an, cung quy uoc voi kiem_cu_phap_311.py va
        # vnstock_goi.kiem_goi(). Loi duoc IN RA nguyen van ngay tren,
        # khong bi nuot. Day la phep DOI mot ngoai le thanh trang thai
        # thu ba, khong phai phep thay loi bang mot con so.
        return 2

    them, sot = [], []
    for b in bg:
        lenh = b.get("lenh", "")
        cu = ten in [t for t, _ in cb.kiem(lenh)]
        moi = ten in thu_mau(ten, mau, lenh)
        if moi and not cu:
            them.append(b)
        elif cu and not moi:
            sot.append(b)

    print(f"\nTHU luat {ten!r} voi mau moi tren {len(bg)} lenh THAT:\n")
    print(f"   BAT THEM : {len(them)}")
    for b in them:
        dau = "!! truoc day CHO QUA" if b.get("phan") == "CHO-QUA" else "  "
        print(f"      {dau}  {b.get('lenh', '')[:64]}")
    print(f"   BO SOT   : {len(sot)}")
    for b in sot:
        print(f"          {b.get('lenh', '')[:64]}")

    nham = [b for b in them if b.get("phan") == "CHO-QUA"]
    print(f"\n   {len(nham)} lenh TRUOC DAY CHO QUA nay se bi chan.")
    print("   Do la con so phai nhin — no la ty le bat nham tren quan the THAT.")
    if not bg:
        print("\n   (nhat ky rong — con so 0 o tren KHONG phai '0 bat nham',")
        print("    no la 'chua co du lieu'. Xem GIOI HAN o docstring.)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--thu-luat", help="ten luat muon thu mau moi")
    ap.add_argument("--mau", help="mau ung vien (regex)")
    ts = ap.parse_args()

    duong = cb.duong_nhat_ky()
    bg = doc_nhat_ky(duong)
    print("=" * 64)
    print(f"NHAT KY CUA BASH — {duong}")
    print("=" * 64)
    if not bg:
        print("nhat ky RONG. No bat dau tu 14/09/2026; lenh go truoc do")
        print("khong dung lai duoc. Day KHONG phai 'cua chua bao gio chan'.")

    if ts.thu_luat or ts.mau:
        if not (ts.thu_luat and ts.mau):
            print("CHUA KIEM DUOC — phai co CA --thu-luat lan --mau",
                  file=sys.stderr)
            return 2
        return _thu(bg, ts.thu_luat, ts.mau)

    _thong_ke(bg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
