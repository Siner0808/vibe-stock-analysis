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
import pathlib
import re
import sys

GOC = pathlib.Path(__file__).resolve().parent.parent

# Dấu ngăn lệnh THẬT. `|` cố ý KHÔNG có mặt: `pytest ... | tail` là MỘT
# hình dạng cần nhìn trọn vẹn, tách nó ra là giết mất luật canh nó.
_NGAN_DOI = ("&&", "||")
_NGAN_DON = ";&\n"


def _nuot_than_heredoc(lenh: str, i: int, cho: list[str]) -> int:
    """Nhảy qua thân của mọi heredoc đang chờ. Trả vị trí sau thân cuối."""
    while cho:
        ket = cho.pop(0)
        while i < len(lenh):
            j = lenh.find("\n", i)
            dong = lenh[i:] if j < 0 else lenh[i:j]
            het = len(lenh) if j < 0 else j + 1
            i = het
            if dong.strip() == ket:
                break
    return i


def boc_va_tach(lenh: str) -> list[str]:
    """Bóc NỘI DUNG chuỗi nháy và THÂN heredoc, rồi tách thành lệnh con.

    VÌ SAO CÓ HÀM NÀY
    ──────────────────
    `CLAUDE.md` ghi từ 22/08/2026: *"Gác phải đọc AST, không đọc `in`"* —
    viết cho test Python, và **chưa bao giờ áp cho chính cửa này**. Ba
    luật ở đây quét cả chuỗi lệnh bằng `[^\\n]*`, nên chúng khớp **sự
    xuất hiện** của một chữ, không khớp **vai trò** của nó.

    Đếm được trong hai ngày 10–11/09/2026: **8 lần chặn NHẦM / 3 lần
    chặn ĐÚNG**. Cán cân lật, và mọi lần nhầm đều cùng một gốc:

      • `git push -u origin nhanh && git branch -a | grep main`
        -> `main` là đối số của `grep`, không phải đích của `git push`
      • `gh pr create --body "... rm paper_trades.db ..."`
        -> văn bản MÔ TẢ một lệnh xấu, không phải lệnh xấu
      • `cat > /c/Users/.../Temp/x.py <<'EOF'`
        -> ghi ra TEMP, không phải ghi đè file nguồn trong repo

    Shell không có AST sẵn dùng, nên đây là mức tương đương gần nhất:
    biết trạng thái nháy, biết thân heredoc, biết dấu ngăn lệnh.

    Thân heredoc bị bóc ở CẢ hai dạng — có và không trích dẫn. Khác với
    `kiem_cu_phap_311.doan_nhung()`, vốn chỉ nhận dạng CÓ trích dẫn vì
    nó đi KIỂM phần thân; ở đây ta đi VỨT phần thân, nên dạng nào cũng
    phải vứt.
    """
    ra: list[str] = []
    hien: list[str] = []
    cho: list[str] = []
    i, n = 0, len(lenh)
    nhay: str | None = None

    def chot() -> None:
        s = "".join(hien).strip()
        if s:
            ra.append(s)
        hien.clear()

    while i < n:
        c = lenh[i]

        if nhay is not None:
            if c == "\\" and nhay == '"' and i + 1 < n:
                hien.append("  ")
                i += 2
                continue
            hien.append(c if c == nhay else " ")
            if c == nhay:
                nhay = None
            i += 1
            continue

        if c in "'\"":
            nhay = c
            hien.append(c)
            i += 1
            continue

        if c == "\n" and cho:
            chot()
            i = _nuot_than_heredoc(lenh, i + 1, cho)
            continue

        if lenh.startswith("<<", i) and not lenh.startswith("<<<", i):
            k = i + 2
            if k < n and lenh[k] == "-":
                k += 1
            while k < n and lenh[k] in " \t":
                k += 1
            q = lenh[k] if k < n and lenh[k] in "'\"" else ""
            k += len(q)
            m = re.match(r"[A-Za-z0-9_.-]+", lenh[k:])
            if m:
                cho.append(m.group(0))
                k += len(m.group(0))
                if q and k < n and lenh[k] == q:
                    k += 1
            hien.append(" " * (k - i))
            i = k
            continue

        if lenh.startswith(_NGAN_DOI, i):
            chot()
            i += 2
            continue
        if c in _NGAN_DON:
            chot()
            i += 1
            continue

        hien.append(c)
        i += 1

    chot()
    return ra


def _duong_trong_repo(duong: str) -> bool:
    """Đường dẫn này có nằm TRONG repo không?

    Git Bash trả đường tuyệt đối dạng `/c/Users/...`; `pathlib` trên
    Windows đọc nó là TƯƠNG ĐỐI (không có ổ đĩa) nên sẽ kết luận ngược.
    Quy nó về `C:/Users/...` trước khi hỏi.

    Đường TƯƠNG ĐỐI thì coi như trong repo — lệnh chạy với cwd ở repo là
    trường hợp thường, và là trường hợp nguy hiểm.
    """
    duong = duong.strip("'\"")
    m = re.match(r"^/([A-Za-z])/(.*)$", duong)
    if m:
        duong = f"{m.group(1).upper()}:/{m.group(2)}"
    p = pathlib.Path(duong)
    if not (p.is_absolute() or duong.startswith("/")):
        return True
    try:
        p.resolve().relative_to(GOC)
        return True
    except (ValueError, OSError):
        return False

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
        re.compile(r"(?:cat|tee)\s[^|;&]*>\s*(\S+\.(?:py|md|ya?ml|json|toml))"
                   r"[\s\S]*<<"),
        "Ghi đè file nguồn bằng heredoc. Hai cái hại, và cái thứ hai nặng "
        "hơn: backtick cùng `$` bị shell nội suy trước khi nội dung tới "
        "đĩa (04–05/09/2026), và `cat >` ghi ĐÈ TRỌN file — một lệnh như "
        "vậy đã xoá mất 40 phép kiểm đang có ngày 09/09/2026, trong khi "
        "cả bốn cổng lúc đó đều XANH.\n"
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
        # `[^|]*` cu cho phep CA `>` lan `;` nam giua, nen
        # `pytest ... > log; grep ... | head` bi khop du cai ong khong
        # he gan vao pytest. Ngay 10/09/2026 luat nay chan NHAM 5 lan va
        # chan DUNG 3 lan — can can lat, nen siet lai pham vi thay vi
        # noi muc do. Nay doi ong phai THUOC CUNG mot lenh voi pytest:
        # khong `>` (da chuyen huong thi ong khong o tren stdout cua no)
        # va khong dau ngan lenh `;` `&` hay xuong dong.
        #
        # GIOI HAN AY DA DONG (11/09/2026). Ban 10/09 ghi: "CON LOT, va
        # biet truoc: VAN BAN nhac toi hinh dang ay — trong `echo`,
        # trong than heredoc cua mot commit, trong `--body` cua mot PR —
        # van bi khop. Sua duoc bang cach boc than heredoc va chuoi nhay
        # ra truoc khi so, nhung do la viec RIENG."
        #
        # Viec RIENG ay chinh la `boc_va_tach()` o dau file. Luat nay nay
        # doc ban DA BOC, nen van ban nhac toi hinh dang xau khong con bi
        # khop. Bieu thuc ben duoi KHONG doi — cai doi la thu no doc.
        re.compile(r"\bpytest\b[^|;&\n>]*\|\s*(?:tail|head)\b"),
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
        "`docs/HANDOFF.md` mục 7: nhánh -> PR -> merge.\n"
        "  LÝ DO THẬT: `.github/workflows/kiem-dinh.yml` chạy trên CẢ "
        "`push` lẫn `pull_request`, nên đẩy thẳng thì CI chạy SAU khi mã "
        "đã nằm trên `main` — một cái cổng đặt sau cánh cửa. Đi qua PR "
        "thì nó chạy TRƯỚC.\n"
        "  Hai lý do CŨ của luật này đều đã bị ĐO và BÁC ngày 08/09/2026: "
        "`main` KHÔNG có branch protection (API trả 404 Branch not "
        "protected), và `gh` CÓ cài (2.100.0, đã đăng nhập). Chúng sống "
        "trong chính thông báo này tới 11/09/2026.",
    ),
    (
        "backtick-trong-python-c",
        re.compile(r'\bpython[^\s]*\s+-c\s+"[^"]*`'),
        "Dấu ` bên trong `python -c \"...\"`. Bash nội suy nó TRƯỚC khi "
        "Python thấy chuỗi, nên một khối mã markdown bị thay bằng KẾT QUẢ "
        "chạy lệnh — thường là rỗng, và im lặng.\n"
        "  Đã xảy ra 08/09/2026 — một khối mã ba dòng biến mất khỏi "
        "`references/loi-da-mac.md`; chỉ lộ ra khi đọc lại file.\n"
        "  Cách đúng: viết một file .py rồi chạy nó, hoặc dùng nháy ĐƠN "
        "(bash không nội suy trong nháy đơn).",
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

# Ba luật này phải đọc chuỗi lệnh THÔ, không đọc bản đã bóc — và mỗi
# luật có một lý do riêng, không luật nào là ngoại lệ cho tiện:
#
#   hai-heredoc             hai dấu mở heredoc nằm ở hai lệnh con khác
#                           nhau vẫn là cùng một lỗi; tách ra là mù.
#   heredoc-ghi-file-repo   dấu mở `<<` và đích `>` cách nhau qua một
#                           dòng mới, tức qua một dấu ngăn.
#   backtick-trong-python-c backtick NẰM TRONG nháy kép chính là chủ đề
#                           của luật. Bóc nội dung nháy là xoá mất nó.
DOC_THO = frozenset({
    "hai-heredoc", "heredoc-ghi-file-repo", "backtick-trong-python-c",
})

# Luật chỉ phán khi ĐIỀU KIỆN THÊM cũng đúng. Khác với biểu thức: biểu
# thức nhận ra HÌNH DẠNG, điều kiện thêm trả lời một câu hỏi biểu thức
# không hỏi được.
DIEU_KIEN_THEM = {
    # Tên luật nói "file-repo" từ ngày nó ra đời, nhưng biểu thức chưa
    # bao giờ nhìn đường dẫn. Ngày 11/09/2026 nó chặn một lệnh ghi ra
    # `AppData/Local/Temp` — lần chặn nhầm thứ tư của cùng hình dạng.
    "heredoc-ghi-file-repo": lambda lenh, m: _duong_trong_repo(m.group(1)),
}


def kiem(lenh: str) -> list[tuple[str, str]]:
    """PHÉP PHÁN. Trả danh sách (tên luật, giải thích) bị vi phạm.

    Tách riêng khỏi `main()` có chủ đích: để phần tự chứng minh đi qua
    đúng hàm này chứ không đi qua hàm đọc stdin. Đã mắc lỗi ngược lại
    nhiều lần trong hai ngày 04–05/09/2026.

    Từ 11/09/2026 phép phán đọc HAI văn bản khác nhau, và việc chọn đọc
    bản nào là một quyết định của từng luật — xem `DOC_THO`.
    """
    if RE_THOAT.search(lenh):
        return []

    con = boc_va_tach(lenh)
    pham: list[tuple[str, str]] = []
    for ten, bt, vi_sao in LUAT:
        doi = [lenh] if ten in DOC_THO else con
        for doan in doi:
            m = bt.search(doan)
            if not m:
                continue
            them = DIEU_KIEN_THEM.get(ten)
            if them and not them(doan, m):
                continue
            pham.append((ten, vi_sao))
            break
    return pham


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
