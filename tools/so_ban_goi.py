"""CI đang chạy bản nào, máy này đang chạy bản nào — đọc, đừng suy.

VÌ SAO CÓ FILE NÀY (17/09/2026, lỗi 79)
──────────────────────────────────────
`CLAUDE.md` có một bảng tên *"Bất đối xứng local / CI — VĨNH VIỄN, và là
chủ ý"*, và nó kết bằng một câu khai ĐỦ:

    "Bat doi xung CHI nam o BCTC va han muc; lich su gia thi khong."

Câu ấy **thiếu một vế**, và vế thiếu là vế đổi thường xuyên nhất:
**SỐ HIỆU BẢN THƯ VIỆN**.

`requirements.txt` khai bằng **SÀN** (`vnstock>=4.0.6`, `vnai>=2.5.7`), nên
mỗi lượt CI `pip install` lấy bản **MỚI NHẤT trên PyPI**. Máy local thì cài
một lần rồi đứng yên. Hai nơi trôi ra khỏi nhau mà không ai thấy — vì chưa
có lệnh nào hỏi.

Đo ngày 17/09/2026, và nó đảo ngược cách đọc hai phép nâng gần nhất:

```
luot CI 2026-09-16T01:26:10Z   vnstock-4.0.8   vnai-2.6.0
may local cung luc             vnstock 4.0.7   vnai 2.5.9
PR #130 "nang vnai 2.6.0" merge  2026-09-16T07:55:03Z
```

CI đã chạy `vnai` 2.6.0 **trước sáu tiếng rưỡi**. Và `vnstock` 4.0.8 phát
hành 15/09, nên **mọi cổng xanh từ hôm ấy đều xanh trên 4.0.8** — trong khi
`docs/STATE.md` BƯỚC 87 viết *"mọi con số hiện hành đã đo trên 4.0.7"* như
một lý do để chưa nâng.

Câu ấy đúng về **các lượt ĐO**, và sai về **các lượt CỔNG**. Nên phép nâng
local chưa bao giờ là *"đi trước"* — nó là **đuổi theo thứ cổng đã chạy**.

CÁI NÀY KHÔNG PHẢI MỘT CỔNG
───────────────────────────
Nó cần mạng và cần `gh` đã đăng nhập, nên nó không chạy được trên CI —
cùng hạng với `tools/doc_so_that.py`. Nó là **máy đo gọi bằng tay**, và
giá trị của nó là biến một câu suy đoán thành một lệnh.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")

#: Chỉ các gói CÔNG KHAI. Bốn gói tài trợ không có trên PyPI công khai và
#: CI không cài chúng — xem `requirements.txt`.
CONG_KHAI = ("vnstock", "vnai", "vnstock_ezchart", "pandas", "numpy",
             "streamlit", "tradingview-ta")

RE_GOI = re.compile(r"\b([a-zA-Z][\w.\-]*)-(\d+\.\d+[\w.]*)\b")

KHOP = "KHOP"
LECH = "LECH"
CHUA_KIEM = "CHUA KIEM DUOC"

#: Nhãn cho một gói không xuất hiện trong nhật ký CI. KHÔNG được coi là
#: "khớp": không thấy khác với thấy-và-giống.
KHONG_THAY = "không thấy trong nhật ký"


def ban_local() -> dict[str, str]:
    import importlib.metadata as md
    ra = {}
    for g in CONG_KHAI:
        try:
            ra[g] = md.version(g)
        except Exception:                      # bia-ok: goi khong co thi khai VANG
            ra[g] = "VẮNG"
    return ra


def _chuan(ten: str) -> str:
    return ten.replace("-", "_").lower()


def luot_ci_gan_nhat() -> tuple[str, str] | None:
    """(id, thời điểm) của lượt `kiem-dinh` gần nhất. None nếu không hỏi được."""
    ra = subprocess.run(
        ["gh", "run", "list", "--workflow=kiem-dinh.yml", "--limit=1",
         "--json", "databaseId,createdAt"],
        capture_output=True, text=True, encoding="utf-8", cwd=str(GOC))
    if ra.returncode != 0:
        return None
    try:
        d = json.loads(ra.stdout)[0]
    except (json.JSONDecodeError, IndexError, KeyError):
        return None
    return str(d["databaseId"]), d["createdAt"]


def ban_ci(luot_id: str) -> dict[str, str] | None:
    """Bản CI THẬT SỰ cài, đọc từ dòng `Successfully installed` của nhật ký.

    Đọc NHẬT KÝ chứ không hỏi PyPI: câu hỏi là *"CI đã chạy bản nào"*, và
    chỉ nhật ký trả lời được câu ấy. Hỏi PyPI trả lời một câu khác —
    *"bản mới nhất hôm nay là gì"* — và hai câu ấy lệch nhau đúng bằng
    khoảng từ lượt chạy tới bây giờ.
    """
    ra = subprocess.run(["gh", "run", "view", luot_id, "--log"],
                        capture_output=True, text=True, encoding="utf-8",
                        errors="replace", cwd=str(GOC))
    if ra.returncode != 0:
        return None
    thay: dict[str, str] = {}
    for dong in ra.stdout.splitlines():
        if "Successfully installed" not in dong:
            continue
        for ten, ban in RE_GOI.findall(dong):
            c = _chuan(ten)
            if c in {_chuan(g) for g in CONG_KHAI}:
                thay[c] = ban
    return thay or None


def so_sanh(loc: dict[str, str],
              ci: dict[str, str] | None) -> tuple[str, list[tuple]]:
    """PHÉP PHÁN, tách riêng để đục thử được KHÔNG CẦN MẠNG.

    BA trạng thái, không phải hai — cùng quy ước với `vnstock_goi.kiem_goi`
    và `lich_giao_dich.chan_doan`. Ô thứ ba bắt buộc: không đọc được nhật
    ký CI mà im lặng thì câu ấy bị đọc thành *"hai nơi giống nhau"*, và đó
    đúng là kết luận sai đã sống hai ngày (lỗi 79).
    """
    if not ci:
        return CHUA_KIEM, []
    lech = []
    for g in CONG_KHAI:
        ban = ci.get(_chuan(g))
        if ban is None:
            continue                      # không thấy — không phán
        if loc.get(g) != ban:
            lech.append((g, loc.get(g), ban))
    return (LECH if lech else KHOP), lech


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--luot", help="id lượt CI cụ thể; mặc định lấy gần nhất")
    a = ap.parse_args()

    loc = ban_local()
    print("MÁY NÀY")
    for g, v in loc.items():
        print(f"  {g:18s} {v}")

    if a.luot:
        luot_id, luc = a.luot, "(chỉ định tay)"
    else:
        tim = luot_ci_gan_nhat()
        if tim is None:
            print("\nCHƯA KIỂM ĐƯỢC: không hỏi được `gh`. Đây là ba trạng "
                  "thái, không phải hai — im lặng ở đây sẽ bị đọc thành "
                  "'hai nơi giống nhau'.")
            return 2
        luot_id, luc = tim

    ci = ban_ci(luot_id)
    if ci is None:
        print(f"\nCHƯA KIỂM ĐƯỢC: không đọc được nhật ký lượt {luot_id}.")
        return 2

    ma, lech = so_sanh(loc, ci)
    ten_lech = {g for g, _, _ in lech}
    print(f"\nCI — lượt {luot_id} ({luc})")
    for g in CONG_KHAI:
        ban = ci.get(_chuan(g), KHONG_THAY)
        print(f"  {g:18s} {ban}" + ("   <-- LỆCH" if g in ten_lech else ""))

    print()
    if ma == LECH:
        print(f"LỆCH {len(lech)} gói:")
        for g, a_, b_ in lech:
            print(f"  {g}: máy {a_} · CI {b_}")
        print("\nĐây KHÔNG phải lỗi — `requirements.txt` khai bằng SÀN nên "
              "CI luôn lấy bản mới nhất.\nNhưng nó nghĩa là các CỔNG đang "
              "chạy trên một bản khác bản các phép ĐO đã chạy.")
        return 1
    print("KHỚP — máy này và lượt CI ấy cùng bản trên mọi gói công khai.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
