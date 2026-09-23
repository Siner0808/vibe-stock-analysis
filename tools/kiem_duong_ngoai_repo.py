"""Đường dẫn NGOÀI repo mà tài liệu sống nêu tên — cái nào còn, cái nào mất.

VÌ SAO CÓ FILE NÀY
──────────────────
Lượt SOÁT QUY TRÌNH thứ tư (23/09/2026) mở `tools/soat_loi_khai_cu.py` và
đọc chính lời khai phạm vi của nó:

    "loi khai phu dinh CO NEU TEN trong bay tai lieu song"

Ba chữ trong câu ấy là ba bức tường, và **loại lọt qua cả ba** thì không
công cụ nào của dự án nhìn thấy:

    PHU DINH     -> mot cau KHANG DINH ("hien duoc cat o <duong dan>")
    NEU TEN      -> ten no neu la mot DUONG DAN, khong phai module trong repo
    trong REPO   -> duong dan nam o thu muc nha nguoi dung

Đo ngày ấy trên bảy tài liệu: **12 đường dẫn ngoài repo được nêu tên, 2
trỏ vào chỗ trống**. Một trong hai nằm ở `SKILL.md`, ở thì hiện tại, và nó
là chỗ DUY NHẤT của skill giải thích vì sao vòng tròn "phải đọc skill mới
biết đi tìm skill" bị cắt.

VÌ SAO LÀ CÔNG CỤ ĐỌC, KHÔNG PHẢI MỘT CỔNG
──────────────────────────────────────────
Không phải vì ngại dựng gác. Vì dự án **đã quyết** điều này rồi, ở dòng
lỗi 14 của `references/loi-da-mac.md`:

    "co y KHONG dung test canh file rules toan cuc: no nam ngoai repo,
     o duong dan Windows, nen mot test nhu the se do tren CI Linux"

Một cổng luôn đỏ trên CI là một cổng bị tắt, và **một cái gác bị tắt thì
bằng không** (`docs/STATE.md` BƯỚC 31). Nên thứ dựng được ở đây là thứ
`tools/kiem_cua_song.py` đã làm cho sáu cửa: **đọc trạng thái, đừng suy ra
nó**. Nó chạy ở **0 workflow**, đúng như `kiem_cua_song.py`.

NÓ PHÂN BIỆT HAI THỨ KHÁC HẲN NHAU
──────────────────────────────────
Một đường dẫn không tồn tại KHÔNG tự động là một lỗi. Quy ước dự án
(`docs/HANDOFF.md` mục 4) cho phép giữ lại thứ đã chết **kèm dấu** — nó là
sử liệu. Nên:

    khong ton tai + CO cua thoat tuong minh  ->  SU LIEU
    khong ton tai + KHONG co                 ->  CON TRO CHET

Chỉ loại thứ hai làm mã thoát khác 0.

BẢN ĐẦU ĐOÁN CÁI DẤU, VÀ ĐO RA LÀ 0/3 ĐÚNG (cùng ngày)
──────────────────────────────────────────────────────
Bản đầu nhận mọi dấu `🔴 ⚠️ ~~ "không còn" "đã xoá"` xuất hiện **bất kỳ
đâu trên dòng**. Chạy thật, in dữ liệu thô ra dưới con số, và cả hai dòng
nó xếp "sử liệu" đều xếp SAI:

    loi-da-mac.md:45   dau ⚠️ o do la GIA TRI mot o bang ("may chan
                       duoc: mot phan") — no khong noi gi ve duong dan
    CLAUDE.md:87       chu "bi xoa" noi ve SAU FILE KHAC; chinh
                       `~/AGENTS.md` duoc khai la "bi cat", tuc CON SONG

Hai lần trượt, hai cơ chế khác nhau, cùng một gốc: **một dấu ở đâu đó
trên dòng không phải một lời khai về thứ đang xét**. Và cả hai đều trượt
về phía IM LẶNG — đúng chiều nguy hiểm.

Nên phép đoán bị gỡ hẳn. Thay bằng **cửa thoát tường minh**, đúng cơ chế
`# bia-ok: <lý do>` của `tools/chan_bia_so_lieu.py`: muốn giữ một đường đã
chết thì phải NÓI RA, kèm lý do.

    <!-- duong-da-chet: <ly do> -->

Rỗng thì không được nhận. Mục đích không phải cấm giữ — mà là buộc nói ra
vì sao cái tên này được phép trỏ vào hư không.

ĐỐI CHỨNG DƯƠNG NẰM TRONG CHÍNH NÓ
──────────────────────────────────
Nếu **không đường nào** trong quần thể tồn tại thì thứ hỏng gần như chắc
chắn là phép đo, không phải tài liệu — sai thư mục nhà, sai hệ điều hành,
chạy trong hộp cát. Khi ấy nó trả **2 (CHƯA KIỂM ĐƯỢC)** chứ không trả
"12 con trỏ chết". Lỗi 61: một máy đo sai thì chỉ in ra một con số.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from soat_loi_khai_cu import TAI_LIEU  # noqa: E402  quan the DUNG CHUNG

GOC = Path(__file__).resolve().parent.parent

#: Một đường dẫn viết theo lối `~/...`. Lớp ký tự cố ý KHÔNG chứa dấu
#: nháy ngược và dấu cách, nên nó dừng đúng ở biên của đoạn mã inline.
DUONG = re.compile(r"~/[A-Za-z0-9._/@-]+")

#: Cửa thoát TƯỜNG MINH, và phải kèm lý do khác rỗng. Không có danh sách
#: dấu nào để đoán — xem khối "BẢN ĐẦU ĐOÁN CÁI DẤU" ở đầu file: phép
#: đoán ấy đo ra 0/3 đúng, và cả hai lần trượt đều trượt về phía im lặng.
CUA_THOAT = re.compile(r"<!--\s*duong-da-chet:\s*(\S[^>]*?)\s*-->")


def _bo_dau_cau(s: str) -> str:
    """Cắt dấu câu dính ở đuôi. `/` giữ lại — nó phân biệt thư mục."""
    while s and s[-1] in ".,;:":
        s = s[:-1]
    return s


def thu_thap(goc: Path = GOC) -> list[tuple[str, int, str, str]]:
    """Mọi đường dẫn `~/...` trong tài liệu sống.

    Trả về `(tai_lieu, so_dong, duong_dan, nguyen_van_dong)`. Một dòng nêu
    hai đường thì ra hai bản ghi — đếm theo LẦN NÊU, không theo dòng.
    """
    ra: list[tuple[str, int, str, str]] = []
    for ten in TAI_LIEU:
        p = goc / ten
        if not p.exists():
            continue
        for i, dong in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            for m in DUONG.finditer(dong):
                d = _bo_dau_cau(m.group(0))
                if d != "~/":
                    ra.append((ten, i, d, dong))
    return ra


def phan_loai(ban_ghi: list[tuple[str, int, str, str]],
              nha: Path) -> dict[str, list]:
    """Chia ba rổ: `co` · `su_lieu` · `chet`.

    `su_lieu` là đường không còn nhưng dòng nêu nó mang **cửa thoát tường
    minh kèm lý do** — quy ước `docs/HANDOFF.md` mục 4 cho phép giữ, và
    giữ thì phải nói ra.
    """
    ket: dict[str, list] = {"co": [], "su_lieu": [], "chet": []}
    for ten, so_dong, duong, dong in ban_ghi:
        that = nha / duong[2:]
        if that.exists():
            ket["co"].append((ten, so_dong, duong))
        elif CUA_THOAT.search(dong):
            ket["su_lieu"].append((ten, so_dong, duong))
        else:
            ket["chet"].append((ten, so_dong, duong))
    return ket


def phan_dinh(ket: dict[str, list]) -> int:
    """0 sạch · 1 có con trỏ chết · 2 CHƯA KIỂM ĐƯỢC.

    Mã 2 khi **không đường nào tồn tại** — kể cả lúc quần thể rỗng, vì
    rỗng thì cũng không đường nào tồn tại. Đó là đối chứng dương: một thư
    mục nhà đọc được thì ít nhất một trong các đường dự án nêu phải còn.
    Không còn cái nào thì thứ hỏng là **phép đo**, không phải tài liệu.

    Bản đầu viết hai nhánh — `tong == 0` rồi `not ket["co"]` — và lượt
    đục thử lôi ra rằng nhánh đầu là **NO-OP**: rỗng thì nhánh sau đã
    bắt. Một phát đột biến sống sót vì đục vào chỗ không đổi hành vi thì
    nói về PHÉP ĐỤC, không nói về gác (`SKILL.md` Bước 3). Nên nhánh
    thừa bị gỡ, chứ không phải gác bị đem đi sửa.
    """
    if not ket["co"]:
        return 2
    return 1 if ket["chet"] else 0


def bao_cao(ket: dict[str, list], ma: int) -> str:
    d: list[str] = []
    d.append("ĐƯỜNG DẪN NGOÀI REPO mà tài liệu sống nêu tên")
    d.append("=" * 62)
    d.append("")
    if ma == 2:
        d.append("CHƯA KIỂM ĐƯỢC — không đường nào trong quần thể tồn tại,")
        d.append("hoặc quần thể rỗng. Thứ hỏng nhiều khả năng là phép đo:")
        d.append("sai thư mục nhà, khác hệ điều hành, hoặc chạy trong hộp")
        d.append("cát. KHÔNG đọc đây thành 'tài liệu sai'.")
        return "\n".join(d)

    for nhan, tieu_de in (
            ("chet", "CON TRỎ CHẾT — nêu tên, không có cửa thoát"),
            ("su_lieu", "SỬ LIỆU — không còn, NHƯNG đã khai lý do"),
            ("co", "CÒN")):
        d.append(f"--- {tieu_de} ---")
        if not ket[nhan]:
            d.append("    (không có)")
        for ten, so_dong, duong in ket[nhan]:
            d.append(f"    {ten}:{so_dong}")
            d.append(f"        {duong}")
        d.append("")

    d.append("=" * 62)
    d.append(f"{len(ket['chet'])} chết · {len(ket['su_lieu'])} sử liệu · "
             f"{len(ket['co'])} còn")
    d.append("")
    d.append("ĐÂY KHÔNG PHẢI MỘT CỔNG, và cố ý không phải. Đường dẫn ngoài")
    d.append("repo nằm ở thư mục nhà của MÁY NÀY; CI chạy trên máy khác và")
    d.append("khác hệ điều hành, nên một cổng canh chúng sẽ đỏ mọi lượt —")
    d.append("đúng lý do lỗi 14 đã nêu khi cố ý KHÔNG dựng nó.")
    d.append("")
    d.append("Một đường CHẾT sửa bằng một trong hai cách, không có cách ba:")
    d.append("  1. trỏ lại đúng chỗ nó đã chuyển tới")
    d.append("  2. giữ câu như SỬ LIỆU, kèm cửa thoát NÊU LÝ DO:")
    d.append("         <!-- duong-da-chet: <ly do> -->")
    return "\n".join(d)


def main() -> int:
    for luong in (sys.stdout, sys.stderr):
        try:
            luong.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(
        description="Duong dan ngoai repo: cai nao con, cai nao mat")
    ap.add_argument("--nha", default=None,
                    help="thu muc nha de doi chieu (mac dinh: Path.home())")
    a = ap.parse_args()

    nha = Path(a.nha) if a.nha else Path.home()
    ket = phan_loai(thu_thap(), nha)
    ma = phan_dinh(ket)
    print(bao_cao(ket, ma))
    return ma


if __name__ == "__main__":
    sys.exit(main())
