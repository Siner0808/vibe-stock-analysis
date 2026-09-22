"""Đếm cỡ nhóm TRƯỚC khi ký — lỗi 39.

KẾT QUẢ 22/09/2026, VÀ NÓ NÓI "ĐỪNG XÂY"
    mau RONG  442 cau co mot ten `*.py`
    mau HEP    14 cau kem mot dong tu khang dinh NANG LUC  (3,2%)
Đọc hết 14: chỉ **2** đúng hình dạng lỗi 95, và cả hai là CÙNG MỘT câu
(`financial_collector.py` "đã có sẵn đường lấy dữ liệu"), đã sửa cùng
ngày. 12 câu còn lại là nhiễu — *"đọc được"* dùng nghĩa khác, và khối văn
bản dài của `docs/STATE.md` bị phép cắt câu cắt nhầm.

Nên một gác theo mẫu này sẽ **86% báo nhầm**, và quần thể thật còn lại là
**0**. Đó là lý do ĐO ĐƯỢC để không dựng gác — không phải một linh cảm.

`docs/STATE.md` BƯỚC 115.

Hình dạng lỗi 95: tài liệu nêu tên một module và khẳng định nó CÓ một
năng lực. Câu hỏi đáng hỏi không phải *"dựng gác được không"* mà **"còn
câu nào như thế đang nằm trong tài liệu không"**.

Đo hai mẫu, rộng rồi hẹp — đúng bài BƯỚC 111.
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

GOC = Path(__file__).resolve().parent.parent

TAI_LIEU = ["CLAUDE.md", "MO-XE-KIEN-TRUC.md", "NGUYEN-TAC-DO-LUONG.md",
            "docs/HANDOFF.md", "docs/STATE.md",
            ".claude/skills/quy-trinh-lam-viec/SKILL.md",
            ".claude/skills/quy-trinh-lam-viec/references/loi-da-mac.md",
            ".claude/skills/quy-trinh-lam-viec/references/bay.md"]

#: Mẫu RỘNG: câu nào có một tên `*.py` trong nháy ngược.
RONG = re.compile(r"`[\w./-]+\.py`")

#: Mẫu HẸP: tên `*.py` VÀ một động từ khẳng định NĂNG LỰC ở gần đó.
NANG_LUC = ("đã có sẵn", "có sẵn đường", "cung cấp", "lấy dữ liệu",
            "hỗ trợ", "đọc được", "lấy được", "có đường")


def cau_cua(van: str) -> list[str]:
    """Cắt theo CÂU, gộp dòng trước — ngắt dòng cứng ~76 ký tự là nhiễu
    đã biết (lỗi 88), nên cắt theo dòng sẽ đếm hụt."""
    gon = re.sub(r"\s+", " ", van)
    return re.split(r"(?<=[.!?])\s+", gon)


def main() -> int:
    rong_n = hep = 0
    hep_cau: list[tuple[str, str]] = []
    for ten in TAI_LIEU:
        p = GOC / ten
        if not p.exists():
            print(f"  (thieu) {ten}")
            continue
        for c in cau_cua(p.read_text(encoding="utf-8")):
            if not RONG.search(c):
                continue
            rong_n += 1
            if any(k in c for k in NANG_LUC):
                hep += 1
                hep_cau.append((ten, c.strip()[:190]))

    print(f"mau RONG  — cau co mot ten `*.py`            : {rong_n:>5}")
    print(f"mau HEP   — kem mot dong tu khang dinh NANG LUC: {hep:>5}")
    print()
    if rong_n:
        print(f"ty le hep/rong: {100 * hep / rong_n:.1f}%")
    print()
    print("=" * 70)
    print("MAU HEP — doc TUNG CAU, khong dem roi ket luan")
    print("=" * 70)
    for ten, c in hep_cau:
        print(f"\n[{ten}]")
        print(f"  {c}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
