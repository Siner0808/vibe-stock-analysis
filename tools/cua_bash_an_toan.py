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
import tempfile
from datetime import datetime

GOC = pathlib.Path(__file__).resolve().parent.parent

# Dấu ngăn lệnh THẬT. `|` cố ý KHÔNG có mặt: `pytest ... | tail` là MỘT
# hình dạng cần nhìn trọn vẹn, tách nó ra là giết mất luật canh nó.
_NGAN_DOI = ("&&", "||")
_NGAN_DON = ";&\n"


def _la_chuyen_huong(lenh: str, i: int) -> bool:
    """Dấu `&` ở vị trí `i` có thuộc một dấu CHUYỂN HƯỚNG không?

    `&` là dấu ngăn lệnh trong bash — **trừ khi** nó là một phần của
    `2>&1`, `>&2`, `<&0` hay `&>file`. Máy tách không biết phân biệt ấy
    cho tới 14/09/2026, nên nó cắt

        pytest ... -q 2>&1 | tail -20
    thành
        'pytest ... -q 2>'   và   '1 | tail -20'

    Cái ống rơi sang đoạn thứ hai, nơi không còn chữ `pytest` nào — nên
    `pytest-qua-ong` **mù với chính hình dạng phổ biến nhất** của thứ nó
    sinh ra để bắt. Tôi gõ đúng hình dạng ấy nhiều lần trong ngày và
    không lần nào bị chặn.

    Máy tách là nền dùng chung của **năm** luật, nên chỗ sai này không
    phải của riêng một luật.
    """
    if lenh[i] != "&":
        return False
    if i + 1 < len(lenh) and lenh[i + 1] == ">":       # `&>` hoac `&>>`
        return True
    j = i - 1
    while j >= 0 and lenh[j] in " \t":
        j -= 1
    return j >= 0 and lenh[j] in "><"                  # `2>&1`, `>&2`, `<&0`


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


def boc(lenh: str) -> str:
    """Như `boc_va_tach()` nhưng KHÔNG tách — trả lại một chuỗi.

    Dùng cho luật cần nhìn **trọn** câu lệnh mà vẫn phải mù với dữ liệu:
    `hai-heredoc` (hai dấu mở ở hai lệnh con vẫn là cùng một lỗi) và
    `heredoc-ghi-file-repo` (dấu `<<` và đích `>` cách nhau qua một dòng
    mới, tức qua một dấu ngăn).

    **Dấu MỞ heredoc được giữ lại; chỉ THÂN bị bóc.** Phân biệt ấy là cả
    vấn đề: dấu mở là CẤU TRÚC, thân là DỮ LIỆU. Bản đầu 11/09/2026 bóc
    cả hai, và `hai-heredoc` hoá mù với chính ca nó sinh ra để bắt.
    """
    return "\n".join(_quet(lenh, tach=False))


def boc_than_heredoc(lenh: str) -> str:
    """Bóc THÂN heredoc, GIỮ nguyên nội dung chuỗi nháy.

    PHẠM VI THỨ TƯ, thêm 14/09/2026, và nó có vì hai phạm vi kia đều
    KHÔNG cho đúng thứ `backtick-trong-nhay-kep` cần:

      • `boc()` bóc cả nội dung nháy — mà nội dung nháy CHÍNH LÀ chủ đề
        của luật ấy. Bóc đi là xoá mất thứ đang đi tìm.
      • bản THÔ giữ nguyên mọi thứ, kể cả **thân heredoc**. Mà một thân
        heredoc CÓ TRÍCH DẪN (`<<'EOF'`) thì bash **không nội suy**, nên
        backtick nằm trong đó vô hại.

    Lượt nới luật ngày 14/09/2026 dùng bản THÔ, và nó chặn ngay một lệnh
    hợp lệ của chính tôi: một đoạn Python trong `<<'PYEOF'` có chuỗi
    `\'"[^"]*`\'`. Đó là **bắt nhầm**, và nó lộ ra rằng phép đo trước khi
    nới đã đo sai QUẦN THỂ — 69 dòng lệnh trong tài liệu, chứ không phải
    những hình dạng thật sự được gõ, mà hình dạng gõ nhiều nhất là
    heredoc chạy Python.

    GIỚI HẠN, khai thẳng: hàm này bóc thân heredoc ở **cả hai dạng**, có
    và không trích dẫn. Một thân heredoc KHÔNG trích dẫn thì bash CÓ nội
    suy, nên backtick ở đó vẫn nguy hiểm và luật sẽ **không** thấy. Đó là
    cùng lựa chọn `kiem_cu_phap_311.doan_nhung()` đã khai từ 22/08/2026 —
    dạng không trích dẫn thì thứ trên đĩa không phải thứ chạy thật.
    """
    return "\n".join(_quet(lenh, tach=False, giu_nhay=True))


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
    return _quet(lenh, tach=True)


def _quet(lenh: str, tach: bool, giu_nhay: bool = False) -> list[str]:
    """Máy quét dùng chung cho ba hàm bóc.

    `tach=False` thì dấu ngăn lệnh KHÔNG chốt đoạn — chúng ở lại như ký
    tự thường, nên chuỗi trả về vẫn là một câu lệnh liền mạch.

    `giu_nhay=True` thì nội dung chuỗi nháy được GIỮ nguyên thay vì thay
    bằng dấu cách. Dùng cho luật mà nội dung nháy chính là chủ đề.
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
                # Ky tu DA THOAT khong bao gio la mot dau noi suy: trong
                # nhay kep, bash chi cho `\` giu nghia dac biet truoc
                # $ ` " \ va xuong dong — nen `\`` la mot backtick VAN
                # BAN. Trung hoa no o CA hai pham vi, ke ca `giu_nhay`:
                # giu lai la bat nham dung cai bash khong lam.
                hien.append("  ")
                i += 2
                continue
            hien.append(c if (giu_nhay or c == nhay) else " ")
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
            if tach:
                chot()
            else:
                hien.append(" ")
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
            # GIU dau mo — no la CAU TRUC. Chi THAN bi boc, o nhanh tren.
            hien.append(lenh[i:k])
            i = k
            continue

        if lenh.startswith(_NGAN_DOI, i):
            if tach:
                chot()
            else:
                hien.append("  ")
            i += 2
            continue
        if c in _NGAN_DON and not _la_chuyen_huong(lenh, i):
            if tach:
                chot()
            else:
                hien.append(" ")
            i += 1
            continue

        hien.append(c)
        i += 1

    chot()
    return ra


def _chuan_duong(duong: str) -> str:
    """Về một dạng chuỗi duy nhất: gạch chéo xuôi, `/c/…` -> `c:/…`."""
    d = duong.strip().strip("'\"").replace("\\", "/")
    m = re.match(r"^/([A-Za-z])/(.*)$", d)          # Git Bash -> Windows
    if m:
        d = f"{m.group(1)}:/{m.group(2)}"
    return d.rstrip("/")


def _duong_trong_repo(duong: str) -> bool:
    """Đường dẫn này có nằm TRONG repo không?

    So bằng CHUỖI, **không** hỏi `pathlib` của hệ điều hành đang chạy.

    Bản đầu (11/09/2026) hỏi `pathlib`, và CI bắt được ngay trong lượt
    đầu tiên: nó quy `/c/Users/…` của Git Bash về `C:/Users/…` rồi hỏi
    `Path.is_absolute()`. Trên Windows đúng; trên Linux thì `C:/Users/…`
    **không** có dấu `/` đầu nên bị đọc là TƯƠNG ĐỐI, rơi vào nhánh
    "coi như trong repo", và cửa chặn nhầm đúng cái mẫu nó vừa được sửa
    để tha. Năm cổng tại máy đều xanh.

    Bài học: **đừng quy một đường dẫn về quy ước của HĐH này rồi hỏi HĐH
    kia.** Phép kiểm phải độc lập với nơi nó chạy — cùng lý do
    `tests/test_cua_song.py` MÔ PHỎNG môi trường CI thay vì phụ thuộc nó.

    Đường TƯƠNG ĐỐI thì coi như trong repo — lệnh chạy với cwd ở repo là
    trường hợp thường, và là trường hợp nguy hiểm.
    """
    d = _chuan_duong(duong)
    tuyet_doi = d.startswith("/") or re.match(r"^[A-Za-z]:/", d)
    if not tuyet_doi:
        return True
    goc = _chuan_duong(str(GOC))
    return (d + "/").lower().startswith((goc + "/").lower())

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
        # `--in-place` la dang DAI cua `-i`, cung co che. Ban cu
        # `-\w+` khong khop `--in-place` vi `\w` khong an dau `-`.
        re.compile(r"\bsed\s+(?:-[-\w]+\s+)*(?:-i\b|--in-place\b)"),
        "`sed -i` trên file repo. CHƯA CÓ SỰ CỐ nào ghi ngày trong repo — "
        "đây là QUY ƯỚC, chép từ `CLAUDE.md` (\"vá lớn thì viết một file "
        ".py rồi chạy\"). Rủi ro thật: bản mingw xử lý ký tự không phải "
        "ASCII không chắc chắn, mà tài liệu và test ở đây toàn tiếng Việt "
        "có dấu.\n"
        "  Nới 14/09/2026: bản cũ bỏ sót dạng dài `--in-place`, cùng công "
        "cụ và cùng cơ chế. `perl -i` thì KHÔNG nới — đó là công cụ "
        "khác, và không có luật nào cho nó; xem BƯỚC 65.\n"
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
        # 14/09/2026 — lop phu dinh siet lai con dung mot ky tu.
        # `;` va `&` o do la THUA: may tach da cat dau ngan THAT roi.
        # `>` la ve them ngay 10/09 de tranh khop
        # `pytest ... > log; grep ... | head`, nhung dau `;` moi la thu
        # tach ca ay, va viec tach da do `boc_va_tach()` lam tu 11/09.
        # Ve `>` o lai sau khi ly do cua no da mat, va no lam luat MU
        # voi `pytest ... 2>&1 | tail` — hinh dang pho bien nhat.
        # `(?!-)`: `\b` da chan `pytest_cache` (gach duoi la ky tu tu),
        # nhung KHONG chan `pytest-qua-ong` — chinh TEN cua luat nay. Sau
        # khi lop phu dinh duoc noi ra sang `2>&1` (14/09/2026), mot lenh
        # nhu `--thu-luat pytest-qua-ong ... 2>&1 | tail` bi chan NHAM.
        # Do la bat nham THAT, do duoc tren nhat ky cua, cung ngay.
        re.compile(r"\bpytest\b(?!-)[^|\n]*\|\s*(?:tail|head)\b"),
        "`pytest ... | tail` — `tail` đệm toàn bộ output tới khi ống đóng. "
        "Với một lượt chạy nền thì bạn không đọc được gì cho tới lúc nó "
        "xong, và sẽ ngồi hỏi 'xong chưa'. Đếm được ít nhất 10 lượt như "
        "vậy ngày 07/09/2026.\n"
        "  Mặt thứ HAI, im lặng hơn: mã thoát của một ống là mã thoát của "
        "lệnh CUỐI, tức `tail`, tức luôn 0 — nên `&&` sau đó đi tiếp dù "
        "pytest đỏ.\n"
        "  Nới 14/09/2026: bản cũ mù với `pytest … 2>&1 | tail` vì lớp "
        "phủ định loại cả `>` lẫn `&`, mà `2>&1` có cả hai. Đo trước khi "
        "nới: 0 bắt nhầm trên 20 lệnh `TOT` và 69 dòng lệnh tài liệu.\n"
        "  Cách đúng: `... -q > /tmp/kq.log 2>&1` rồi đọc file log.",
    ),
    (
        "python-he-thong",
        # 14/09/2026: them `python3.11`, `python3.13` va `py` (bo
        # phong cua Windows). Ca ba deu la python HE THONG, cung co che.
        re.compile(r"(?:^|[;&|]\s*)(?:python3?(?:\.\d+)?|py)\s+(?!-c\b)"),
        "`python` hệ thống không có numpy/pandas của dự án. CHƯA CÓ SỰ CỐ "
        "ghi ngày — QUY ƯỚC, chép từ `docs/HANDOFF.md` mục 1.\n"
        "  Nới 14/09/2026: bản cũ bỏ sót `python3.11` và `py` — cùng là "
        "python hệ thống. Đo trước khi nới: 0 bắt nhầm trên 20 lệnh "
        "`TOT` và 69 dòng lệnh tài liệu.\n"
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
        "backtick-trong-nhay-kep",
        # Doi mot CAP nhay dong lai: `"..."` co backtick o giua. Mau
        # long hon (`"[^"]*` + backtick) khop ca tu dau nhay DONG cua mot
        # cap truoc do, nen `git commit -m "ok" --author \'a`b\'` bi bat
        # nham du backtick nam trong nhay DON.
        re.compile(r'"[^"]*`[^"]*"'),
        "Dấu ` bên trong một chuỗi NHÁY KÉP. Bash nội suy nó TRƯỚC khi "
        "lệnh nhận được chuỗi, nên phần trong backtick bị thay bằng KẾT "
        "QUẢ chạy nó như một lệnh — thường là rỗng, và im lặng.\n"
        "  Đã xảy ra HAI LẦN, ở hai chỗ khác nhau:\n"
        "    08/09/2026 — `python -c \"…`…\"`: một khối mã ba dòng biến "
        "mất khỏi `references/loi-da-mac.md`, chỉ lộ ra khi đọc lại file.\n"
        "    14/09/2026 — `--ly-do \"…`nguoi-thay`…\"` của một công cụ "
        "khác hẳn: bash báo `nguoi-thay: command not found` và lý do khai "
        "vào mốc số test bị nuốt mất một khúc.\n"
        "  Luật cũ tên `backtick-trong-python-c` và chỉ canh `python -c`, "
        "tức HẸP HƠN cơ chế nó canh — bash nội suy trong nháy kép của MỌI "
        "lệnh. Nới ngày 14/09/2026; đo trước khi nới: 69 dòng lệnh trong "
        "tài liệu repo, **0 dòng** dính luật rộng.\n"
        "  Cách đúng: dùng nháy ĐƠN (bash không nội suy trong nháy đơn), "
        "hoặc viết một file rồi truyền qua `-F`/`--body-file`.",
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

# BA PHẠM VI, và mỗi luật khai nó đọc bản nào. Không luật nào là ngoại
# lệ "cho tiện" — mỗi lựa chọn dưới đây có một lý do đọc được.
#
#   mặc định   bản đã BÓC, TÁCH thành lệnh con
#   DOC_BOC    bản đã BÓC, KHÔNG tách — cần nhìn trọn câu lệnh
#   DOC_THO    bản THÔ — nội dung nháy chính là chủ đề của luật
#
#   hai-heredoc             hai dấu mở ở hai lệnh con khác nhau vẫn là
#                           cùng một lỗi, nên không tách. Nhưng phải BÓC:
#                           một dấu `<<` nằm TRONG thân heredoc là VĂN
#                           BẢN, không phải dấu mở thứ hai.
#   heredoc-ghi-file-repo   dấu mở `<<` và đích `>` cách nhau qua một
#                           dòng mới, tức qua một dấu ngăn.
#   DOC_GIU_NHAY bản đã bóc THÂN heredoc, GIỮ nội dung nháy
#
#   backtick-trong-nhay-kep backtick NẰM TRONG nháy kép chính là chủ đề
#                           của luật, nên không bóc nội dung nháy.
#                           Nhưng thân heredoc CÓ trích dẫn thì bash
#                           không nội suy, nên phải bóc — nếu không,
#                           mọi đoạn Python chạy bằng heredoc đều bị
#                           chặn nhầm. Đo được 14/09/2026, ngay lượt
#                           đầu tiên sau khi nới luật.
#
# Hai luật đầu từng nằm ở DOC_THO, và ngày 11/09/2026 `hai-heredoc` chặn
# nhầm một lệnh `git commit -F -` có thân heredoc *nhắc tới* `<<'EOF'`.
# Lần chặn nhầm thứ CHÍN, và nó xảy ra trong chính lượt sửa tám lần kia.
DOC_BOC = frozenset({"hai-heredoc", "heredoc-ghi-file-repo"})
DOC_THO = frozenset()

# Bóc THÂN heredoc nhưng GIỮ nội dung nháy — xem `boc_than_heredoc()`.
DOC_GIU_NHAY = frozenset({"backtick-trong-nhay-kep"})

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
        if ten in DOC_THO:
            doi = [lenh]
        elif ten in DOC_GIU_NHAY:
            doi = [boc_than_heredoc(lenh)]
        elif ten in DOC_BOC:
            doi = [boc(lenh)]
        else:
            doi = con
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


#: Nhật ký nằm trong TEMP, NGOÀI repo — nó không bao giờ được commit.
#: Nội dung là đúng thứ đã gõ vào Bash, nên nó có thể chứa bất cứ gì người
#: gõ đưa vào. Đó là lý do nó ở TEMP và chỉ ở TEMP.
TEN_NHAT_KY = "vibe_cua_bash_chay.log"


def duong_nhat_ky() -> pathlib.Path:
    return pathlib.Path(tempfile.gettempdir()) / TEN_NHAT_KY


def ghi_nhat_ky(lenh: str, pham: list, thoat: bool) -> None:
    """Ghi MỘT dòng JSON cho mỗi lượt cửa được gọi.

    VÌ SAO CÓ HÀM NÀY
    ─────────────────
    `cua_doc_bat_buoc.py` ghi nhật ký từ 09/09/2026, và nhờ đó câu *"cửa
    ấy có chạy không"* trả lời được bằng một lượt đọc file. Cửa Bash thì
    **không ghi gì**, nên hai câu dưới đây tới 14/09/2026 vẫn chỉ đoán
    được:

      • cửa này đã chặn bao nhiêu lần, và chặn cái gì
      • nới một luật ra thì nó bắt NHẦM bao nhiêu

    Câu thứ hai cắn thật trong ngày ấy. Lỗi 49: tôi đo tỷ lệ bắt nhầm
    trên **69 dòng lệnh trong tài liệu** rồi đọc thành *"nới là an
    toàn"* — sai QUẦN THỂ, và luật vừa nới chặn ngay lệnh kế tiếp. Rồi
    BƯỚC 65 nới ba luật nữa, vẫn phải đo trên proxy vì không có gì khác.

    Nhật ký này biến quần thể ấy thành **quần thể thật**:
    `tools/soat_nhat_ky_cua.py` chạy một mẫu ỨNG VIÊN lên đúng những
    lệnh đã gõ, và nói ra nó sẽ bắt thêm/bắt nhầm những gì.

    **Ghi hỏng thì NHƯỜNG ĐƯỜNG.** Một cửa an toàn không được chết vì
    cái nhật ký của nó — nhật ký là thứ phụ, phép phán mới là việc chính.
    """
    try:
        ban_ghi = {
            "luc": datetime.now().isoformat(timespec="seconds"),
            "phan": "THOAT" if thoat else ("CHAN" if pham else "CHO-QUA"),
            "luat": [t for t, _ in pham],
            "lenh": lenh,
        }
        with open(duong_nhat_ky(), "a", encoding="utf-8") as f:
            f.write(json.dumps(ban_ghi, ensure_ascii=False) + "\n")
    except Exception:
        pass


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

    # Ghi o CA BA nga. Chi ghi nga CHAN thi nhat ky chi co mau xau,
    # va cau hoi 'noi luat co bat NHAM khong' van khong tra loi duoc —
    # dung cai lo da sinh ra loi 49.
    thoat = bool(RE_THOAT.search(lenh))
    pham = kiem(lenh)
    ghi_nhat_ky(lenh, pham, thoat)
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
