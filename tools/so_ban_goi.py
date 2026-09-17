"""CI đang chạy bản nào, máy này đang chạy bản nào — đọc, đừng suy.

VÌ SAO CÓ FILE NÀY (17/09/2026, lỗi 79)
──────────────────────────────────────
`CLAUDE.md` có một bảng tên *"Bất đối xứng local / CI — VĨNH VIỄN, và là
chủ ý"*, và nó kết bằng một câu khai ĐỦ:

    "Bat doi xung CHI nam o BCTC va han muc; lich su gia thi khong."

Câu ấy **thiếu một vế**, và vế thiếu là vế đổi thường xuyên nhất:
**SỐ HIỆU BẢN THƯ VIỆN**.

`requirements.txt` khai bằng **SÀN** (`vnstock>=4.0.6`, `vnai>=2.5.7`) —
và `streamlit` thì không có cả sàn. Nên mỗi lượt CI `pip install` lấy bản
**MỚI NHẤT trên PyPI**, còn máy local cài một lần rồi đứng yên.

VÀ BẢN ĐẦU CỦA CHÍNH FILE NÀY MẮC LẠI ĐÚNG HÌNH DẠNG ẤY (lỗi 80)
────────────────────────────────────────────────────────────────
Bản 17/09 sáng khai một hằng số `CONG_KHAI` gồm **bảy tên gõ tay**, rồi
chỉ so bảy tên ấy. Chiều 17/09 đo lại trên **toàn bộ** quần thể:

    92 goi co o CA HAI noi   ->   LECH 32
    bay ten go tay bat duoc  ->   1   (streamlit)
    lot qua                  ->   31  (co urllib3 1.26.20 / 2.8.0,
                                       plotly 6.9.0 / 7.1.0)

Con số *"còn đúng một vế lệch"* mà `docs/STATE.md` BƯỚC 94 viết là một
câu về **cửa sổ của dụng cụ**, bị đọc thành một câu về **thế giới**. Cùng
họ với lỗi 73: cái gác không yếu, nó ngắm một quần thể khác quần thể thật.

QUẦN THỂ SUY RA · MỨC ĐỘ GÕ TAY — HAI VIỆC KHÁC NHAU
─────────────────────────────────────────────────────
Phép sửa **không** phải gõ thêm tên. Quần thể nay là **giao của hai bên
đọc được**, nên thêm một gói vào `requirements.txt` thì nó tự vào tầm.

Hai danh sách dưới đây vẫn gõ tay, và đó là chủ ý: chúng quyết định
**cái gì ồn ào**, không quyết định **cái gì được nhìn thấy**. Mọi lệch
đều in ra đủ tên và đủ hai số hiệu. Trộn hai việc ấy chính là lỗi 80;
nén một danh sách thành một con số tổng chính là lỗi 78.

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

#: Gõ tay, và chỉ quyết định MỨC ĐỘ. Gói trên đường dữ liệu: lệch ở đây
#: nghĩa là cổng đang chấm bằng một bộ số khác bộ số các phép ĐO đã chạy.
HANG_SO = ("vnstock", "vnai", "vnstock_ezchart", "pandas", "numpy",
           "tradingview-ta")

#: Gõ tay, và chỉ quyết định MỨC ĐỘ. Gói dựng thứ người dùng NHÌN THẤY —
#: Streamlit Cloud cài cùng đường với CI, nên bản của CI là bản phục vụ.
HANG_GIAO_DIEN = ("streamlit", "plotly", "altair", "matplotlib")

SO = "QUYET DINH SO"
GIAO_DIEN = "NGUOI DUNG THAY"
KHAC = "con lai"

RE_GOI = re.compile(r"\b([a-zA-Z][\w.\-]*)-(\d+\.\d+[\w.]*)\b")

KHOP = "KHOP"
LECH = "LECH"
CHUA_KIEM = "CHUA KIEM DUOC"


def _chuan(ten: str) -> str:
    """Quy tên gói về MỘT dạng — PEP 503, cộng dấu chấm."""
    return re.sub(r"[-_.]+", "_", ten).lower()


_HANG_SO = frozenset(_chuan(g) for g in HANG_SO)
_HANG_GIAO_DIEN = frozenset(_chuan(g) for g in HANG_GIAO_DIEN)


def hang_cua(ten: str) -> str:
    c = _chuan(ten)
    if c in _HANG_SO:
        return SO
    if c in _HANG_GIAO_DIEN:
        return GIAO_DIEN
    return KHAC


def ban_local() -> dict[str, str]:
    """MỌI gói đang cài ở máy này — quần thể suy ra, không gõ tay."""
    import importlib.metadata as md
    ra: dict[str, str] = {}
    for d in md.distributions():
        ten = d.metadata["Name"]
        if ten:
            ra[_chuan(ten)] = d.version
    return ra


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


def doc_nhat_ky(van: str) -> dict[str, str]:
    """MỌI gói trên dòng `Successfully installed` — tách ra để đục thử được."""
    thay: dict[str, str] = {}
    for dong in van.splitlines():
        if "Successfully installed" not in dong:
            continue
        phan = dong.split("Successfully installed", 1)[1]
        for ten, ban in RE_GOI.findall(phan):
            thay[_chuan(ten)] = ban
    return thay


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
    return doc_nhat_ky(ra.stdout) or None


def so_sanh(loc: dict[str, str],
            ci: dict[str, str] | None) -> tuple[str, list[tuple[str, str, str, str]]]:
    """PHÉP PHÁN, tách riêng để đục thử được KHÔNG CẦN MẠNG.

    Quần thể là **giao** của hai bên: một gói chỉ có ở một nơi thì không
    so được, và *không thấy* khác *thấy và khác*.

    BA trạng thái, không phải hai — cùng quy ước với `vnstock_goi.kiem_goi`
    và `lich_giao_dich.chan_doan`. Ô thứ ba bắt buộc: không đọc được nhật
    ký CI mà im lặng thì câu ấy bị đọc thành *"hai nơi giống nhau"*, và đó
    đúng là kết luận sai đã sống mười bảy ngày (lỗi 79).

    Mỗi dòng lệch mang **hạng** của nó. Hạng KHÔNG lọc dòng nào ra khỏi
    danh sách — nó chỉ nói dòng ấy có chạm chỗ quyết định không (lỗi 80).
    """
    if not ci:
        return CHUA_KIEM, []
    lech = []
    for g in sorted(set(loc) & set(ci)):
        if loc[g] != ci[g]:
            lech.append((g, loc[g], ci[g], hang_cua(g)))
    return (LECH if lech else KHOP), lech


def cham_cho_quyet_dinh(lech: list[tuple[str, str, str, str]]) -> bool:
    """Câu hỏi THỨ HAI, hỏi sau khi đã biết có lệch hay không.

    Trộn nó vào câu hỏi thứ nhất là cách bản đầu của file này để lọt 31
    gói: một dòng không thuộc hạng nào đã bị loại khỏi cả phép đếm.
    """
    return any(h in (SO, GIAO_DIEN) for _, _, _, h in lech)


def _in_nhom(lech: list[tuple[str, str, str, str]], hang: str) -> None:
    nhom = [d for d in lech if d[3] == hang]
    print(f"\n  {hang}  ({len(nhom)})")
    if not nhom:
        print("      (khong co)")
        return
    for g, a, b, _ in nhom:
        print(f"      {g:<26} máy {a:<12} CI {b}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--luot", help="id lượt CI cụ thể; mặc định lấy gần nhất")
    a = ap.parse_args()

    loc = ban_local()
    print(f"MÁY NÀY — {len(loc)} gói đang cài")

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

    print(f"CI — lượt {luot_id} ({luc}) — {len(ci)} gói lượt ấy cài")
    chi_ci = sorted(set(ci) - set(loc))
    print(f"\nso được {len(set(loc) & set(ci))} gói (giao của hai bên)"
          f"  ·  chỉ ở CI: {len(chi_ci)}  ·  chỉ ở máy: {len(set(loc) - set(ci))}")
    if chi_ci:
        print(f"      chỉ ở CI: {' '.join(chi_ci)}")

    ma, lech = so_sanh(loc, ci)
    if ma == KHOP:
        print("\nKHỚP — hai nơi cùng bản trên mọi gói so được.")
        return 0

    print(f"\nLỆCH {len(lech)} / {len(set(loc) & set(ci))} gói")
    for hang in (SO, GIAO_DIEN, KHAC):
        _in_nhom(lech, hang)

    print("\nĐây KHÔNG phải lỗi — `requirements.txt` khai bằng SÀN (và "
          "`streamlit` không có\ncả sàn), nên CI luôn lấy bản mới nhất. "
          "Nó nghĩa là các CỔNG đang chạy trên\nmột bộ bản khác bộ bản các "
          "phép ĐO đã chạy.")
    if cham_cho_quyet_dinh(lech):
        print("\nCÓ chạm chỗ quyết định.")
        return 1
    print("\nKHÔNG chạm chỗ quyết định — lệch nằm ngoài đường dữ liệu và "
          "ngoài thứ người dùng nhìn thấy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
