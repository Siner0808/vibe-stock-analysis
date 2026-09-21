"""Đối chiếu một TRÍCH DẪN với tài liệu dự án — sau khi bỏ nhiễu Markdown.

VÌ SAO CÓ FILE NÀY
──────────────────
Ngày 18/09/2026 (BƯỚC 108) dự án ký một luật: *"`grep` ra 0 dòng CHƯA đủ
để kết tội sổ tay bịa — phải grep lại một chuỗi con đặc trưng, bỏ dấu
nhấn, trước khi kết luận."* Luật ấy đúng chiều và **hẹp hơn thứ nó đo**.

Ngày 21/09/2026 lượt soát định kỳ thứ ba đối chiếu **15 trích dẫn** sổ tay
vừa đưa ra. Ba lượt, ba phép đối chiếu khác nhau, ba con số khác hẳn:

    luot 1  grep TUNG DONG, giu nguyen dau nhan   ->   8 khop · 4 nghi BIA
    luot 2  bo dau nhan, noi lien dong            ->  11 khop · 3 nghi BIA
    luot 3  bo THEM dau trich dan `> `            ->  14 khop · 1 BIA that

**Phép đối chiếu của lượt 1 sẽ vu cho sổ tay bịa 4 trên 15.** Ba lớp nhiễu,
mỗi lớp một mình đủ làm một trích dẫn THẬT trả về 0 dòng:

    lop 1  dau nhan Markdown  `**dam**`  `` `ma` ``  `_nghieng_`
    lop 2  NGAT DONG CUNG ~76 ky tu — mot cau dai nam tren 2-3 dong
    lop 3  dau TRICH DAN `> ` dau moi dong trong khoi blockquote

Lớp 1 đo được ngày 18/09; lớp 2 và 3 chỉ lộ ra khi có một quần thể 15 câu
để đếm. Đúng họ lỗi 61: **máy đo hẹp hơn thứ nó đo, và nó không nổ — nó
chỉ in ra một con số nghe hợp lý.**

GIỚI HẠN, khai thẳng
────────────────────
Nó trả lời đúng MỘT câu: *chuỗi này có nằm trong tài liệu dự án không.*

- Nó **không** biết câu ấy còn ĐÚNG hay không. Một câu đã bị bác vẫn nằm
  nguyên trong file kèm dấu 🔴 — đó là quy ước giữ-sử-liệu của dự án.
- Nó **không** thay được việc đọc bối cảnh. `SKILL.md` mục *"Luồng thông
  tin thứ hai"*: mọi phát hiện phải tự kiểm lại bằng lệnh RỒI đọc quanh nó.
- Nó chỉ quét **tài liệu**, không quét mã.
"""
import re
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
SKILL = GOC / ".claude" / "skills" / "quy-trinh-lam-viec"

#: Bảy tài liệu — cùng quần thể `tools/soat_loi_khai_cu.py` quét, cộng ba
#: file skill. Suy từ đường dẫn, không gõ nội dung.
TAI_LIEU = (
    GOC / "CLAUDE.md",
    GOC / "NGUYEN-TAC-DO-LUONG.md",
    GOC / "MO-XE-KIEN-TRUC.md",
    GOC / "docs" / "STATE.md",
    GOC / "docs" / "HANDOFF.md",
    GOC / "docs" / "TIEU-CHI-DOC-TRUOC.md",
    SKILL / "SKILL.md",
    SKILL / "references" / "loi-da-mac.md",
    SKILL / "references" / "bay.md",
    SKILL / "references" / "cong-thuc-chay.md",
)

#: Số ký tự tối thiểu của một trích dẫn đáng đối chiếu. Dưới mức này thì
#: một chuỗi bất kỳ khớp ở đâu đó, và phép đối chiếu hết nói lên điều gì.
DAI_TOI_THIEU = 15


def chuan_hoa(van: str) -> str:
    """Bỏ ba lớp nhiễu Markdown rồi gộp khoảng trắng. HÀM THUẦN.

    Thứ tự bắt buộc: dấu trích dẫn TRƯỚC (nó neo vào đầu dòng, nên phải
    xử lý khi còn thấy được đầu dòng), rồi dấu nhấn, rồi mới gộp xuống
    dòng. Gộp trước thì lớp 3 không còn đầu dòng để neo.

    KHÔNG đụng tới chữ và dấu tiếng Việt — nếu bỏ dấu thì hai câu khác
    nghĩa sẽ khớp nhau, và phép đối chiếu thành vô nghĩa.
    """
    van = re.sub(r"(?m)^[ \t]*>[ \t]?", " ", van)      # lớp 3
    van = re.sub(r"[*`_~]", "", van)                   # lớp 1
    return re.sub(r"\s+", " ", van).strip()            # lớp 2


def ban_da_chuan(duong=TAI_LIEU) -> dict[str, str]:
    """{tên file: toàn văn ĐÃ chuẩn hoá}. File không có thì bỏ qua, im lặng.

    Im lặng vì quần thể co lại là chuyện bình thường (một file đổi tên);
    `phan_dinh()` mới là chỗ phân biệt *không tìm thấy* với *chưa kiểm được*.
    """
    ra: dict[str, str] = {}
    for f in duong:
        try:
            ra[f.name] = chuan_hoa(f.read_text(encoding="utf-8"))
        except OSError:
            continue
    return ra


def tim(trich: str, ban: dict[str, str]) -> list[str]:
    """Tên các tài liệu chứa trích dẫn này. HÀM THUẦN."""
    c = chuan_hoa(trich)
    return [t for t, v in ban.items() if c and c in v]


def tien_to_dai_nhat(trich: str, ban: dict[str, str]) -> tuple[int, str]:
    """(số ký tự của tiền tố dài nhất còn khớp, tên file). HÀM THUẦN.

    Đây là chỗ phân biệt hai thứ mà một phép so nhị phân gộp làm một:

        tien to = 0            ->  BIA han: khong mot mau nao co that
        0 < tien to < do dai   ->  trich DUNG mot doan roi che them
    """
    c = chuan_hoa(trich)
    for n in range(len(c), 0, -1):
        for t, v in ban.items():
            if c[:n] in v:
                return n, t
    return 0, ""


def phan_dinh(trich: str, ban: dict[str, str] | None = None) -> tuple[int, str]:
    """(mã thoát, câu phán). BA ô, cùng quy ước `vnstock_goi.kiem_goi`.

        0  KHỚP            — có thật, nguyên văn, sau khi bỏ nhiễu
        1  LỆCH            — không có; kèm độ dài tiền tố còn khớp
        2  CHƯA KIỂM ĐƯỢC  — trích quá ngắn, hoặc không đọc được tài liệu nào
    """
    ban = ban_da_chuan() if ban is None else ban
    if not ban:
        return 2, "CHƯA KIỂM ĐƯỢC — không đọc được tài liệu nào"
    c = chuan_hoa(trich)
    if len(c) < DAI_TOI_THIEU:
        return 2, (f"CHƯA KIỂM ĐƯỢC — trích dẫn còn {len(c)} ký tự sau khi "
                   f"chuẩn hoá, dưới mức {DAI_TOI_THIEU}")
    thay = tim(trich, ban)
    if thay:
        return 0, "KHỚP — " + " · ".join(thay)
    n, t = tien_to_dai_nhat(trich, ban)
    if n == 0:
        return 1, "LỆCH — không mẩu nào của câu này có trong tài liệu dự án"
    return 1, (f"LỆCH — khớp {n}/{len(c)} ký tự đầu (ở {t}), rồi rẽ khỏi "
               f"nguyên bản. Đọc tiếp từ đó để biết nó chế thêm gì.")


def main(tham_so: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    tham_so = sys.argv[1:] if tham_so is None else tham_so
    if not tham_so:
        print("Dùng: doi_chieu_trich_dan.py \"<trích dẫn cần đối chiếu>\"")
        print(__doc__.split("GIỚI HẠN")[0].strip())
        return 2
    ban = ban_da_chuan()
    ma, cau = phan_dinh(" ".join(tham_so), ban)
    print(f"{len(ban)} tài liệu · {sum(len(v) for v in ban.values())} ký tự")
    print(cau)
    return ma


if __name__ == "__main__":
    raise SystemExit(main())
