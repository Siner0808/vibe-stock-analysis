"""Mở phiên: nhắc quy trình và các mốc ngày đang chặn — hook `SessionStart`.

VÌ SAO CÓ FILE NÀY
──────────────────
Ngày 07/09/2026 dự án đã có sẵn một skill quy trình, và tôi làm việc **nửa
buổi** rồi mới biết — hệ thống tự hiện nó ra giữa chừng. Đó là lỗi số 10
trong `references/loi-da-mac.md`.

Vá bằng cách viết "Bước 0: `ls .claude/skills/`" vào chính skill ấy là một
vòng tròn: phải đọc skill mới biết phải đi tìm skill. **Một luật nằm trong
đầu thì không phải luật** — câu đó rút ra từ lỗi số 12 cùng ngày, khi tôi
áp dụng đúng một quy tắc ở một file rồi vi phạm nó ở file kế tiếp sau một
giờ.

File này là cơ chế: harness chạy nó lúc mở phiên, không phụ thuộc ai nhớ.

NGUYÊN TẮC THIẾT KẾ
───────────────────
1. **KHÔNG BAO GIỜ CHẶN.** Luôn thoát 0, nuốt mọi lỗi. Một hook mở phiên
   mà làm hỏng phiên thì tệ hơn không có.
2. **Suy ra, đừng gõ.** Tên skill đọc từ `.claude/skills/`, mốc ngày đọc
   từ `docs/HANDOFF.md`. Gõ tay vào đây là tạo thêm một chỗ lệch nữa —
   đúng thứ cả tuần này đi vá.
3. **Ngắn.** Nhắc nhiều thì thành nhiễu, mà nhiễu thì bị bỏ qua.
"""
import datetime as dt
import pathlib
import re
import sys

GOC = pathlib.Path(__file__).resolve().parent.parent
HANDOFF = GOC / "docs" / "HANDOFF.md"
THU_MUC_SKILL = GOC / ".claude" / "skills"

RE_NGAY = re.compile(r"\*\*(\d{2})/(\d{2})/(\d{4})\*\*")


def ten_skill() -> list[str]:
    """Đọc từ đĩa, không gõ tay — đổi tên skill thì lời nhắc đi theo."""
    try:
        return sorted(p.parent.name for p in THU_MUC_SKILL.glob("*/SKILL.md"))
    except OSError:
        return []


def moc_ngay_con_chan(hom_nay: dt.date | None = None) -> list[tuple[dt.date, str]]:
    """Mốc ngày trong mục "Chờ tới ngày" của HANDOFF mà CHƯA tới hạn.

    PHÉP PHÁN, tách riêng để tự chứng minh được: đưa vào một `hom_nay` cố
    định thì kết quả phải đổi theo, và đó là thứ đột biến sẽ nhắm tới.
    """
    hom_nay = hom_nay or dt.date.today()
    try:
        src = HANDOFF.read_text(encoding="utf-8")
    except OSError:
        return []

    kh = re.search(r"\*\*Chờ tới ngày[^\n]*\*\*\n(.*?)(?=\n\*\*|\n## )",
                   src, re.S)
    if not kh:
        return []

    ra = []
    for dong in re.split(r"\n(?=- )", kh.group(1)):
        m = RE_NGAY.search(dong)
        if not m:
            continue
        try:
            ngay = dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            continue
        if ngay <= hom_nay:
            continue                      # tới hạn rồi thì không còn chặn
        mo_ta = re.sub(r"\s+", " ", dong.split("—", 1)[-1]).strip(" -.")
        ra.append((ngay, mo_ta[:70]))
    return sorted(ra)


def trang_thai_cua() -> str:
    """Một dòng: bao nhiêu cửa đang thật sự chạy được.

    Có mặt vì tới 10/09/2026 không ai ĐỌC được trạng thái này — phải suy
    ra từ `python --version`, một phép thử chỉ đi qua ĐÚNG MỘT trong sáu
    cửa. Ba ngày liền câu "sáu cửa chết" được chép lại trong khi bốn cửa
    vẫn đang chạy. Xem `tools/kiem_cua_song.py`.
    """
    try:
        from kiem_cua_song import bao_cao
        return bao_cao(mot_dong=True)[1]
    except Exception:
        return "CUA: chua kiem duoc (tools/kiem_cua_song.py)"


def ban_tin(hom_nay: dt.date | None = None) -> str:
    hom_nay = hom_nay or dt.date.today()
    d = ["┌─ vibe_preview ─────────────────────────────────────────────"]
    for t in ten_skill():
        d.append(f"│ QUY TRÌNH BẮT BUỘC — gọi skill `{t}` TRƯỚC khi đọc")
        d.append("│ hay sửa file đầu tiên. Nó có: cách vá file (một đường")
        d.append("│ duy nhất), vòng lặp đột biến, năm cổng gác đúng thứ tự.")
    if not ten_skill():
        d.append("│ ⚠️  không thấy skill quy trình nào trong .claude/skills/")

    d.append("│")
    d.append(f"│ {trang_thai_cua()}")

    chan = moc_ngay_con_chan(hom_nay)
    if chan:
        d.append("│")
        d.append("│ CHẶN THEO NGÀY — đừng đọc sớm:")
        for ngay, mo_ta in chan:
            con = (ngay - hom_nay).days
            d.append(f"│   {ngay.strftime('%d/%m/%Y')} (còn {con} ngày) — {mo_ta}")
    d.append("└────────────────────────────────────────────────────────────")
    return "\n".join(d)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    try:
        print(ban_tin())
    except Exception:
        pass                       # mở phiên KHÔNG BAO GIỜ được hỏng vì đây
    return 0


if __name__ == "__main__":
    sys.exit(main())
