"""Cửa chặn: một lượt ghi KHÔNG được để lại file rỗng.

Chạy như `PostToolUse` hook, matcher `Write|Edit`. Đọc JSON từ stdin.
Mã thoát 2 = báo lại cho agent.

VÌ SAO CÓ FILE NÀY
──────────────────
05/09/2026: `Path.write_text(..., newline=<không hợp lệ>)` làm
`do_tre_khop.py` còn **0 byte**. Hàm mở file để ghi — tức CẮT CỤT — rồi
mới kiểm đối số. Cả file biến mất, và không có gì kêu; chỉ tới lượt chạy
test sau đó mới lộ.

Hẹp có chủ đích. Đây là điều kiện KHÔNG BAO GIỜ đúng: một lượt sửa mã
nguồn không có lý do gì để lại file rỗng. Nên nó không kêu oan bao giờ,
và một cửa không kêu oan là cửa không bị tắt.

MỘT THỨ CỐ Ý KHÔNG KIỂM — và đây là kết quả của phép đo, không phải lười
─────────────────────────────────────────────────────────────────────────
Bản đầu định chặn cả **xuống dòng trộn lẫn**, vì nó nghe như dấu hiệu của
một lượt vá byte hỏng. Đo trước khi viết (07/09/2026):

    trong INDEX (thứ thật sự được commit) : 412/412 file text là LF thuần
    trong working copy                    : 370 CRLF · 41 LF · 1 trộn lẫn
    core.autocrlf = true, không .gitattributes

Git quy đổi cả hai chiều, nên quy ước xuống dòng của bản trên đĩa không
ảnh hưởng tới thứ được commit. Và file trộn lẫn duy nhất —
`ui_prototype.html`, 913 LF + 1 CRLF — vô hại và có sẵn từ trước. Một gác
như thế sẽ ĐỎ ngay ngày đầu vì một chuyện không phải lỗi, và
`docs/STATE.md` BƯỚC 31 đã ghi: **một gác hay kêu oan thì sớm muộn bị
tắt, mà gác bị tắt thì bằng không có.**
"""
import json
import pathlib
import sys

DUOI_CAN_CANH = {".py", ".md", ".yml", ".yaml", ".json", ".toml", ".html",
                 ".css", ".js", ".txt", ".cfg", ".ini"}


def rong_bat_thuong(duong) -> bool:
    """PHÉP PHÁN. File thuộc loại cần canh và đang rỗng.

    Tách riêng để phần tự chứng minh đi qua đúng chỗ phán.
    """
    p = pathlib.Path(duong)
    if p.suffix.lower() not in DUOI_CAN_CANH:
        return False
    try:
        return p.is_file() and p.stat().st_size == 0
    except OSError:
        return False


def main() -> int:
    for luong in (sys.stdout, sys.stderr):
        try:
            luong.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    try:
        d = json.load(sys.stdin)
    except Exception:
        return 0                          # hỏng thì nhường đường

    if str(d.get("tool_name") or "") not in ("Write", "Edit", "NotebookEdit"):
        return 0
    tho = (d.get("tool_input") or {}).get("file_path")
    if not tho or not rong_bat_thuong(tho):
        return 0

    ten = pathlib.Path(str(tho)).name
    print(
        f"CHẶN: `{ten}` còn 0 byte sau lượt ghi vừa rồi.\n"
        f"\n"
        f"Một lượt sửa mã nguồn không có lý do gì để lại file rỗng. Ngày\n"
        f"05/09/2026 `do_tre_khop.py` mất sạch đúng như vậy — hàm ghi mở\n"
        f"file để CẮT CỤT rồi mới kiểm đối số, và không có gì kêu cho tới\n"
        f"lượt chạy test sau đó.\n"
        f"\n"
        f"Khôi phục NGAY:  git checkout -- <đường dẫn>\n"
        f"Rồi vá lại bằng `tools/va_an_toan.thay()`.",
        file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
