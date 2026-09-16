"""Danh sách việc cho lượt SOÁT LẠI QUY TRÌNH — lời khai phủ định còn sống.

VÌ SAO CÓ FILE NÀY
──────────────────
Ngày 16/09/2026 người dùng chốt: soát lại skill và cửa của dự án theo nhịp
**2 ngày**. Đo trước khi nhận, và phép đo đổi cái đích:

    SKILL.md + bang loi co SUA 9 tren 14 ngay gan nhat

Tức việc **cập nhật** đã chạy hằng ngày theo sự kiện — `SKILL.md` Bước 6 lo
việc ấy, mỗi lỗi mới là một dòng mới. Đặt nhịp 2 ngày lên đó là đặt một
nhịp THẤP HƠN nhịp đang có.

Nửa chưa bao giờ có cơ chế là nửa kia: **soát lại thứ ĐÃ CÓ**. Riêng ngày
16/09 hai câu cũ bị bắt gặp do TÌNH CỜ:

    "cua Bash khong ghi nhat ky ... Ghi ra day, CHUA LAM"   (BUOC 65)
        -> nhat ky da co tu 14/09, va tools/soat_nhat_ky_cua.py doc no
    "dac ta noi chay MOT lan / BUOC 49 noi HAI lan -- mot trong hai da cu"
        -> khong cau nao cu; hai ban khai khac nhau ca ba truong, sau ngay

Không công cụ nào chỉ ra chúng. Một lượt "soát lại" không có danh sách thì
nó là một lời hứa — và dự án này đã đo được rằng lời hứa thì trôi.

NÓ CHỌN QUẦN THỂ NÀO, VÀ VÌ SAO HẸP
───────────────────────────────────
Quét thô mọi dòng mang chữ phủ định trên bảy tài liệu: **187 dòng**. Không
ai soát 187 dòng mỗi hai ngày, và một công cụ không dùng nổi thì bị bỏ qua
— đúng cái vòng nó sinh ra để cắt. Ba phép siết, mỗi phép có lý do:

  1. **bỏ dòng bảng** (`| … |`) — bảng lỗi là SỬ LIỆU, lời khai trong đó
     mô tả lúc ấy và phải giữ nguyên.
  2. **bỏ dòng đã mang dấu bác bỏ** (🔴 ⚠️ ~~…~~ "ĐÃ BỊ BÁC") — đã có
     người soát rồi, và quy ước dự án là giữ lại bản cũ kèm dấu.
  3. **phải NÊU TÊN một thành phần** (`` `tools/x.py` ``) — chỉ loại ấy mới
     kiểm lại được bằng máy: có cái tên thì có chỗ để chạy `grep`.

Còn **15 dòng**. Đo 16/09/2026.

`docs/STATE.md` CỐ Ý không nằm trong danh sách: nó là nhật ký chỉ-thêm, lời
khai trong một BƯỚC cũ mô tả ngày ấy và **không phải** thứ cần sửa. Chỗ
chống lại nó là `SKILL.md` Bước 1 điều 2 — *một câu "không làm được" chép
từ ghi chú thì phải ĐO LẠI* — chứ không phải đi vá lịch sử.

NÓ KHÔNG PHÁN — nó chỉ ra CHỖ ĐÁNG NHÌN
───────────────────────────────────────
Giống hệt lời khai về NotebookLM trong `SKILL.md`. Mỗi dòng in ra là một
địa chỉ để mở ra xem, không phải một kết luận rằng câu ấy đã sai.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent

TAI_LIEU = [
    ".claude/skills/quy-trinh-lam-viec/SKILL.md",
    ".claude/skills/quy-trinh-lam-viec/references/loi-da-mac.md",
    ".claude/skills/quy-trinh-lam-viec/references/bay.md",
    ".claude/skills/quy-trinh-lam-viec/references/cong-thuc-chay.md",
    "CLAUDE.md",
    "docs/HANDOFF.md",
    "NGUYEN-TAC-DO-LUONG.md",
]

PHU_DINH = re.compile(
    r"(chưa bao giờ|chưa ai|không ai|chưa có|chưa làm|chưa đo|chưa được"
    r"|chưa kiểm|không tồn tại|không ghi)", re.I)
DA_CO_DAU = ("🔴", "⚠️", "ĐÃ BỊ BÁC", "đã bị thay", "ĐÃ ĐO", "ĐÃ TRUY", "~~")
CO_TEN = re.compile(r"`[A-Za-z_][\w./:-]*`")


RE_BUOC = re.compile(r"^##\s+(BƯỚC\s+(\d+))\s*—")


def buoc_chua_khai(van_state: str, da_khai, moc: int) -> list[str]:
    """`## BƯỚC n` với n >= `moc` mà chưa có tên trong `da_khai`. HÀM THUẦN.

    MỘT bản cài đặt, hai nơi gọi: `tools/cua_mo_phien.py` (bản tin mở
    phiên) và `tests/test_soat_notebooklm.py` (gác). Bản đầu ngày
    16/09/2026 viết hai lần, rồi thêm một gác bắt hai bản khớp nhau — và
    **đục thử cho thấy gác ấy vô dụng**: khi mọi mục đã khai thì cả hai
    vế đều RỖNG, nên hai đột biến vào hook sống sót cả hai. Một phép so
    hai tập rỗng không phân biệt được gì; đó là lỗi 66.

    Bỏ bản thứ hai rẻ hơn và chắc hơn là canh cho hai bản khớp nhau —
    `SKILL.md` Bước 2: *"Suy ra, đừng gõ. Một ngưỡng gõ tay ở hai chỗ sẽ
    trôi ra khỏi nhau."* Điều ấy đúng với mã y như với ngưỡng.

    Neo vào ĐẦU DÒNG và CẤP tiêu đề, không đọc sự XUẤT HIỆN của chữ
    "BƯỚC" — nó nằm hàng chục lần trong văn xuôi của chính `STATE.md`.
    """
    da_khai = set(da_khai)
    ra: list[str] = []
    for d in van_state.splitlines():
        m = RE_BUOC.match(d)
        if m and int(m.group(2)) >= moc:
            ten = re.sub(r"\s+", " ", m.group(1))
            if ten not in da_khai and ten not in ra:
                ra.append(ten)
    return ra


def loi_khai_con_song(goc: Path = GOC) -> list[tuple[str, int, str]]:
    """(file, dòng, nội dung) — mọi lời khai phủ định CÓ NÊU TÊN, chưa đánh dấu."""
    ra: list[tuple[str, int, str]] = []
    for ten in TAI_LIEU:
        p = goc / ten
        if not p.exists():
            continue
        for i, d in enumerate(p.read_text(encoding="utf-8",
                                          errors="replace").splitlines(), 1):
            if not PHU_DINH.search(d):
                continue
            if d.lstrip().startswith("|"):
                continue
            if any(x in d for x in DA_CO_DAU):
                continue
            if not CO_TEN.search(d):
                continue
            ra.append((ten, i, d.strip()))
    return ra


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--im", action="store_true",
                    help="chỉ in con số, dùng khi gọi từ công cụ khác")
    a = ap.parse_args()

    ra = loi_khai_con_song()
    if not a.im:
        print("LỜI KHAI PHỦ ĐỊNH CÒN SỐNG — mở ra xem, đừng tin sẵn\n"
              + "=" * 64)
        f_cu = None
        for f, dong, noi_dung in ra:
            if f != f_cu:
                print(f"\n{f}")
                f_cu = f
            print(f"  {dong:5}  {noi_dung[:150]}")
        print("\n" + "=" * 64)
    print(f"{len(ra)} lời khai · {len(TAI_LIEU)} tài liệu")
    if not a.im:
        print("\nMỗi dòng là một ĐỊA CHỈ để kiểm lại, không phải một phán "
              "quyết rằng nó đã sai.\nGhi kết quả lượt soát vào "
              "docs/soat-dinh-ky.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
