"""Cửa chặn cho tool Bash — chặn đúng những hình dạng lệnh ĐÃ CẮN THẬT.

Chạy như `PreToolUse` hook, matcher `Bash`. Đọc JSON từ stdin.
Mã thoát 2 = CHẶN, stderr trả lại cho agent.

VÌ SAO CÓ FILE NÀY
──────────────────
Rà lại phiên 07/09/2026: 11 lỗi quy trình. Phần lớn không phải lỗi suy
nghĩ — chúng là **hình dạng lệnh shell** lặp đi lặp lại:

  • hai heredoc trong một lệnh -> bash gộp chúng, chỉ áp NỬA số thay đổi,
    và không báo lỗi. Đã xảy ra: cảnh báo "here-document delimited by
    end-of-file" trôi qua, hai trong ba phép thay không được áp, rồi ngồi
    tìm xem vì sao neo trượt.
  • `pytest ... | tail` chạy nền -> `tail` đệm hết output tới lúc đóng
    ống. Đếm được **ít nhất 10 lượt** gọi công cụ chỉ để hỏi "xong chưa"
    và nhận về màn hình trống.
  • `python` hệ thống thay cho `.venv` -> không có numpy/pandas.

NGUYÊN TẮC (thừa từ `cua_doc_bat_buoc.py`)
──────────────────────────────────────────
1. **Hẹp có chủ đích.** Mỗi luật phải chỉ được ra một sự cố thật. Cửa
   chặn quá rộng sẽ bị tắt, mà cửa bị tắt thì bằng không có.
2. **Hỏng thì KHÔNG chặn.** Nó bảo vệ quy trình, không bảo vệ số liệu.
3. **Thông báo phải nói CÁCH LÀM ĐÚNG**, không chỉ nói "không được".
"""
import json
import re
import sys

# (tên, biểu thức, lời giải thích + cách làm đúng)
#
# MỖI LUẬT PHẢI KHAI NGUỒN, và chỉ có hai nguồn hợp lệ:
#
#   • một SỰ CỐ THẬT, kèm ngày dd/mm/yyyy tra được trong `docs/STATE.md`
#   • một QUY ƯỚC DỰ ÁN đã viết ra, đánh dấu `CHƯA CÓ SỰ CỐ` kèm tên file
#
# Trộn hai thứ đó là bịa. Bản đầu của file này có 8 luật, và
# `tests/test_cua_quy_trinh.py::test_moi_luat_deu_khai_NGUON` bắt ngay 4
# luật viết như thể chúng đến từ sự cố trong khi chúng chỉ là quy ước.
# Gác bắt được chính tác giả của nó, ở lượt chạy đầu tiên.
LUAT = [
    (
        "hai-heredoc",
        re.compile(r"<<-?\s*['\"]?\w+['\"]?[\s\S]*<<-?\s*['\"]?\w+"),
        "Hai heredoc trong MỘT lệnh. Bash gộp chúng: lệnh thứ hai nuốt "
        "phần thân của lệnh thứ nhất, chỉ một nửa số thay đổi được áp, "
        "và bạn chỉ thấy một cảnh báo mờ nhạt.\n"
        "  Đã xảy ra 07/09/2026 — mất một vòng đi tìm vì sao neo trượt.\n"
        "  Cách đúng: tách thành hai lệnh, hoặc viết một file .py rồi chạy.",
    ),
    (
        "heredoc-ghi-file-repo",
        re.compile(r"(?:cat|tee)\s[^|;&]*>\s*\S+\.(?:py|md|ya?ml|json|toml)"
                   r"[\s\S]*<<"),
        "Ghi đè file nguồn bằng heredoc. Backtick và `$` bị shell nội suy "
        "trước khi nội dung tới đĩa, nên thứ ghi ra không phải thứ bạn "
        "viết. Đã xảy ra hai lần (04–05/09/2026).\n"
        "  Cách đúng: dùng tool Write/Edit, hoặc `tools/va_an_toan.thay()`.",
    ),
    (
        "sed-i-file-repo",
        re.compile(r"\bsed\s+(?:-\w+\s+)*-i\b"),
        "`sed -i` trên file repo. CHƯA CÓ SỰ CỐ nào ghi ngày trong repo — "
        "đây là QUY ƯỚC, chép từ `CLAUDE.md` (\"vá lớn thì viết một file "
        ".py rồi chạy\"). Rủi ro thật: bản mingw xử lý ký tự không phải "
        "ASCII không chắc chắn, mà tài liệu và test ở đây toàn tiếng Việt "
        "có dấu.\n"
        "  Cách đúng: `tools/va_an_toan.thay()` (chế độ văn bản, neo phải "
        "khớp đúng một lần).",
    ),
    (
        "pytest-qua-ong",
        re.compile(r"\bpytest\b[^|]*\|\s*(?:tail|head)\b"),
        "`pytest ... | tail` — `tail` đệm toàn bộ output tới khi ống đóng. "
        "Với một lượt chạy nền thì bạn không đọc được gì cho tới lúc nó "
        "xong, và sẽ ngồi hỏi 'xong chưa'. Đếm được ít nhất 10 lượt như "
        "vậy ngày 07/09/2026.\n"
        "  Cách đúng: `... -q > /tmp/kq.log 2>&1` rồi đọc file log.",
    ),
    (
        "python-he-thong",
        re.compile(r"(?:^|[;&|]\s*)(?:python|python3)\s+(?!-c\b)"),
        "`python` hệ thống không có numpy/pandas của dự án. CHƯA CÓ SỰ CỐ "
        "ghi ngày — QUY ƯỚC, chép từ `docs/HANDOFF.md` mục 1.\n"
        "  Cách đúng: `./.venv/Scripts/python.exe`.",
    ),
    (
        "push-thang-main",
        re.compile(r"\bgit\s+push\b[^\n]*\bmain\b(?![\w/-])"),
        "Đẩy thẳng lên `main`. CHƯA CÓ SỰ CỐ ghi ngày — QUY ƯỚC, chép từ "
        "`docs/HANDOFF.md` mục 7: nhánh -> PR -> NGƯỜI DÙNG merge. Nhánh "
        "này có branch protection, và `gh` không cài trên máy này.",
    ),
    (
        "xoa-nhieu-nhanh",
        re.compile(r"\bgit\s+push\b[^\n]*--delete\s+\S+\s+\S"),
        "Xoá nhiều nhánh từ xa trong một lệnh. CHƯA CÓ SỰ CỐ ghi ngày — "
        "quan sát về môi trường: lệnh dạng này bị chặn ở đây. Mỗi lần một "
        "nhánh.",
    ),
    (
        "xoa-db-goc-repo",
        re.compile(r"\brm\b[^\n]*\s\S*\.db\b"),
        "Xoá file `.db`. Đó là DỮ LIỆU ĐO của người dùng, và một lần mất "
        "sổ lệnh đã xảy ra rồi (12/08/2026: 96/113 lệnh thật biến mất).\n"
        "  Phải hỏi người dùng trước.",
    ),
]

# Cho phép thoát cửa khi có chủ đích, kèm LÝ DO — cùng lối `# bia-ok:`
# của `chan_bia_so_lieu.py`. Rỗng thì không tính.
RE_THOAT = re.compile(r"#\s*cua-ok:\s*\S+")


def kiem(lenh: str) -> list[tuple[str, str]]:
    """PHÉP PHÁN. Trả danh sách (tên luật, giải thích) bị vi phạm.

    Tách riêng khỏi `main()` có chủ đích: để phần tự chứng minh đi qua
    đúng hàm này chứ không đi qua hàm đọc stdin. Đã mắc lỗi ngược lại
    nhiều lần trong hai ngày 04–05/09/2026.
    """
    if RE_THOAT.search(lenh):
        return []
    return [(ten, vi_sao) for ten, bt, vi_sao in LUAT if bt.search(lenh)]


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

    if str(d.get("tool_name") or "") != "Bash":
        return 0
    lenh = str((d.get("tool_input") or {}).get("command") or "")
    if not lenh:
        return 0

    pham = kiem(lenh)
    if not pham:
        return 0

    print("CHẶN: hình dạng lệnh này đã gây lỗi thật trong dự án.\n",
          file=sys.stderr)
    for ten, vi_sao in pham:
        print(f"  [{ten}]\n  {vi_sao}\n", file=sys.stderr)
    print("Cố ý muốn chạy? Thêm `# cua-ok: <lý do>` vào lệnh. "
          "Lý do rỗng không tính.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
