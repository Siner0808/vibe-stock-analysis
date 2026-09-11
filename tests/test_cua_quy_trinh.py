"""Gác cho ba công cụ quy trình thêm ngày 07/09/2026.

    tools/va_an_toan.py        -- đường vá duy nhất
    tools/cua_bash_an_toan.py  -- cửa chặn hình dạng lệnh đã cắn thật
    tools/cua_ghi_an_toan.py   -- cửa chặn file rỗng sau lượt ghi

Cả ba sinh ra từ một lượt rà quy trình, không từ một ý hay. Mỗi luật
trong `cua_bash_an_toan.LUAT` phải chỉ được ra một sự cố có ngày; test
cuối file bắt đúng điều đó, vì một cửa chặn tích góp luật "nghe hợp lý"
sẽ phình ra tới lúc kêu oan, rồi bị tắt.

HAI CHIỀU, LUÔN LUÔN. Một cửa chặn mọi thứ cũng vô dụng y như một cửa
không chặn gì — nên mỗi phép kiểm dưới đây có cả mẫu XẤU lẫn mẫu TỐT.
"""
import subprocess
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(GOC / "tools"))

import cua_bash_an_toan as cb  # noqa: E402
import cua_ghi_an_toan as cg  # noqa: E402
import cua_mo_phien as mp  # noqa: E402,F401
import va_an_toan as va  # noqa: E402

# KHONG ghim ".venv/Scripts/python.exe": duong Windows, runner CI la
# Linux. Xem tools/va_an_toan.py.
PY = sys.executable


# ─────────────────────────── va_an_toan ───────────────────────────

def test_va_an_toan_tu_kiem_chay_duoc():
    """`_tu_kiem()` là thứ chứng minh module, nên nó phải thật sự chạy."""
    va._tu_kiem()
    print("PASS  va_an_toan._tu_kiem() qua")


@pytest.mark.parametrize("goc", [b"mot\r\nhai\r\nba\r\n", b"mot\nhai\nba\n"])
def test_neo_viet_bang_LF_khop_ca_hai_quy_uoc(tmp_path, goc):
    """Điểm của cả module: neo viết một kiểu, chạy được trên cả hai file.

    Ngày 07/09/2026 mất 5 lượt vì neo byte không khớp quy ước của file.
    """
    f = tmp_path / "x.py"
    f.write_bytes(goc)
    va.thay(f, "mot\nhai", "MOT\nHAI")
    ra = f.read_bytes()
    assert b"MOT" in ra
    assert ra.count(b"\r\n") == goc.count(b"\r\n"), "quy ước bị đổi"
    # Tên quy ước tính NGOÀI f-string: dấu \ trong ô thay thế của f-string
    # là cú pháp 3.12 (PEP 701). Máy chạy 3.13 nạp được, CI 3.11 đỏ ngay
    # bước đầu — `tools/kiem_cu_phap_311.py` bắt đúng chỗ này 07/09/2026.
    quy_uoc = "CRLF" if goc.count(b"\r\n") else "LF"
    print(f"PASS  neo viết bằng LF khớp file {quy_uoc}")


def test_thay_GIU_NGUYEN_quy_uoc_cu(tmp_path):
    """Giữ quy ước cũ để diff khỏi nở ra — thẩm mỹ, không phải đúng sai."""
    f = tmp_path / "c.py"
    f.write_bytes(b"a\r\nb\r\n")
    va.thay(f, "b", "B")
    assert f.read_bytes() == b"a\r\nB\r\n"

    g = tmp_path / "l.py"
    g.write_bytes(b"a\nb\n")
    va.thay(g, "b", "B")
    assert g.read_bytes() == b"a\nB\n"
    print("PASS  CRLF ở lại CRLF, LF ở lại LF")


def test_neo_mo_ho_thi_NO_va_KHONG_sua_gi(tmp_path):
    """Vá đúng một nửa còn tệ hơn vá trượt hẳn, vì nó chạy được."""
    f = tmp_path / "x.py"
    f.write_bytes(b"x\nx\n")
    with pytest.raises(va.NeoMoHo):
        va.thay(f, "x", "y")
    assert f.read_bytes() == b"x\nx\n", "nổ rồi mà file vẫn bị sửa"

    with pytest.raises(va.NeoMoHo):
        va.thay(f, "khong-co-o-dau", "y")
    print("PASS  neo khớp 2 lần và 0 lần đều nổ, file nguyên vẹn")


def test_dot_bien_HOAN_TRA_du_lenh_no(tmp_path):
    """Hoàn tra phải nằm trong `finally`, không phải sau lời gọi."""
    f = tmp_path / "x.py"
    goc = b"CO = False\n"
    f.write_bytes(goc)
    # lệnh chắc chắn thất bại
    do = va.dot_bien(f, "False", "True", ["-c", "import sys; sys.exit(1)"],
                     mo_ta="thử")
    assert do is True, "lệnh thoát 1 mà không tính là ĐỎ"
    assert f.read_bytes() == goc, "không hoàn tra"
    print("PASS  đột biến hoàn tra đúng từng byte")


def test_kiem_hoan_tra_NO_khi_file_khong_tro_ve(tmp_path):
    """Lưới an toàn phải tự chứng minh được, không chỉ tồn tại.

    Bản đầu để phép kiểm này nằm thẳng trong `finally`, và đột biến
    `if con_lai != goc:` -> `if False:` **SỐNG SÓT** (đục thử 07/09/2026):
    test bên ngoài chỉ khẳng định "file đã trở về", nên nó xanh dù lưới
    bị gỡ. Đây là đúng bẫy "tự chứng minh đi qua hàm TRÍCH thay vì hàm
    PHÁN" — lần thứ ba trong bốn ngày.
    """
    f = tmp_path / "x.py"
    f.write_bytes(b"noi dung that\n")

    va.kiem_hoan_tra(f, b"noi dung that\n")          # khop -> im lang

    with pytest.raises(RuntimeError, match="HOÀN TRA HỎNG"):
        va.kiem_hoan_tra(f, b"mot noi dung khac\n")
    with pytest.raises(RuntimeError, match="HOÀN TRA HỎNG"):
        va.kiem_hoan_tra(f, b"")                     # đúng ca 05/09: rỗng
    print("PASS  kiểm hoàn tra nổ khi lệch, im khi khớp")


def test_dot_bien_THAT_SU_GOI_kiem_hoan_tra_trong_finally():
    """"Hàm X có tồn tại" khác ""nhánh Y có gọi X"" — `bay.md` mục 1.

    Đục thử 07/09/2026: gỡ hẳn lời gọi `kiem_hoan_tra(p, goc)` khỏi
    `dot_bien` mà bộ test vẫn XANH, vì ở đường chạy bình thường việc hoàn
    tra luôn thành công nên lưới an toàn không bao giờ nổ. Phép kiểm giá
    trị mù ở đây; phải kiểm CHỖ NỐI, bằng AST.

    Và phải là trong `finally`: đặt sau lời gọi lệnh thì một test nổ giữa
    chừng sẽ nhảy qua nó, để lại file đã bị đục.
    """
    import ast

    cay = ast.parse((GOC / "tools" / "va_an_toan.py").read_text(
        encoding="utf-8"))
    ham = next(n for n in ast.walk(cay)
               if isinstance(n, ast.FunctionDef) and n.name == "dot_bien")

    trong_finally = [
        c for t in ast.walk(ham) if isinstance(t, ast.Try)
        for n in t.finalbody for c in ast.walk(n)
        if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)
        and c.func.id == "kiem_hoan_tra"]
    assert trong_finally, (
        "`dot_bien` không gọi `kiem_hoan_tra` trong `finally` — lưới an "
        "toàn tồn tại nhưng không nối vào đâu")

    ghi_lai = [c for t in ast.walk(ham) if isinstance(t, ast.Try)
               for n in t.finalbody for c in ast.walk(n)
               if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
               and c.func.attr == "write_bytes"]
    assert ghi_lai, "`finally` không ghi lại nội dung gốc"
    print("PASS  dot_bien gọi kiem_hoan_tra TRONG finally, sau khi ghi lại")


def test_dot_bien_bao_XANH_khi_lenh_thanh_cong(tmp_path):
    """Chiều ngược lại — nếu không có, một đột biến sống sót vẫn báo đỏ."""
    f = tmp_path / "x.py"
    f.write_bytes(b"CO = False\n")
    assert va.dot_bien(f, "False", "True", ["-c", "pass"], mo_ta="thử") is False
    print("PASS  lệnh thoát 0 -> đột biến SỐNG SÓT, báo đúng")


# ──────────────────────── cua_bash_an_toan ────────────────────────

# (mo ta, lenh, TEN LUAT phai bat duoc no)
#
# Cot thu ba them 11/09/2026, va no khong phai trang tri. Ban truoc chi
# hoi "co chan khong", nen mot mau van XANH khi bi chan boi NHAM LUAT.
# Duc thu loi ra dung the: mau `hai-heredoc` (`python - <<'A'...`) van bi
# chan sau khi luat hai-heredoc da hoa mu, vi luat `python-he-thong` bat
# duoc chu `python` o dau dong. Test xanh vi mot ly do khac han.
#
# Cung hinh dang loi 20: kiem mot truong CO MAT thay vi kiem HANH VI.
XAU = [
    ("hai heredoc", "bash - <<'A'\nx\nA\nbash - <<'B'\ny\nB\n",
     "hai-heredoc"),
    ("heredoc ghi de file .py", "cat > tools/x.py <<'EOF'\nx\nEOF\n",
     "heredoc-ghi-file-repo"),
    ("sed -i", "sed -i 's/a/b/' CLAUDE.md", "sed-i-file-repo"),
    ("pytest qua ong tail",
     "./.venv/Scripts/python.exe -m pytest tests/ -q | tail -5",
     "pytest-qua-ong"),
    ("python he thong", "python tools/kiem_cu_phap_311.py", "python-he-thong"),
    ("push thang main", "git push origin main", "push-thang-main"),
    ("xoa .db", "rm paper_trades.db", "xoa-db-goc-repo"),
    ("backtick trong python -c",
     './.venv/Scripts/python.exe -c "s = ```bash"',
     "backtick-trong-python-c"),
    # Duong dan TUYET DOI nhung nam TRONG repo — van la ghi de file nguon.
    ("heredoc ghi de file repo bang duong tuyet doi",
     f"cat > {GOC.as_posix()}/tools/x.py <<'EOF'\nx\nEOF\n",
     "heredoc-ghi-file-repo"),
    # Hai heredoc o HAI LENH CON khac nhau van la cung mot loi.
    ("hai heredoc qua mot dau ngan",
     "bash - <<'A'\nx\nA\n&& bash - <<'B'\ny\nB\n",
     "hai-heredoc"),
]

# Moi dong duoi day la mot lan CHAN NHAM da do duoc, hoac mot loi khai da
# bi BAC bang phep do. Chung khong phai gia dinh — xem BUOC 51.
TOT = [
    ("mot heredoc", "./.venv/Scripts/python.exe - <<'EOF'\nprint(1)\nEOF\n"),
    ("pytest ghi ra log", "./.venv/Scripts/python.exe -m pytest tests/ -q > kq.log 2>&1"),
    ("venv python", "./.venv/Scripts/python.exe tools/kiem_cu_phap_311.py"),
    ("python -c ngan", "python -c \"print(1)\""),
    ("push len nhanh", "git push -u origin tinh/viec-moi"),
    ("git log binh thuong", "git log --oneline -5"),
    ("doc file .db, khong xoa", "ls -la paper_trades.db"),
    ("main la ten thu muc, khong phai nhanh", "git push origin tinh/main-menu"),
    # nhay DON: bash khong noi suy backtick -> an toan, phai duoc tha
    ("backtick trong nhay don",
     "./.venv/Scripts/python.exe -c 'x = `'"),

    # ── nam hinh dang CHAN NHAM, do duoc 10–11/09/2026 ──────────────
    # 11/09: heredoc ghi ra scratchpad trong TEMP. Luat ten la
    # `...-file-repo` nhung bieu thuc chua bao gio nhin duong dan.
    ("heredoc ghi file NGOAI repo",
     "cat > /c/Users/x/AppData/Local/Temp/y.py <<'EOF'\nprint(1)\nEOF\n"),
    # `main` nam o mot LENH CON khac, khong phai dich cua git push.
    ("push nhanh roi grep chu main o lenh sau",
     "git push -u origin gac/viec && git branch -a | grep main"),
    ("push nhanh roi echo chu main",
     "git push -u origin gac/viec; echo 'xong, chua dung main'"),
    # Van ban NHAC TOI hinh dang xau — gioi han da biet cua ban 10/09,
    # nay dong lai bang cach boc noi dung chuoi nhay.
    ("van ban nhac toi pytest qua ong",
     "git commit -m 'dung pytest tests/ -q | tail -5 nua'"),
    ("van ban nhac toi rm .db",
     "gh pr create --body 'dung chay rm paper_trades.db'"),
    # Loi khai cua luat `xoa-nhieu-nhanh` — DO LAI 11/09/2026 tren hai
    # nhanh nem di: chay tron lot, ma thoat 0, xoa duoc ca hai.
    ("xoa hai nhanh trong mot lenh — loi khai da bi BAC",
     "git push origin --delete tam-thu-a tam-thu-b"),

    # Lan chan NHAM thu CHIN, 11/09/2026, va no xay ra trong chinh luot
    # sua tam lan kia: mot commit message NHAC TOI `<<'EOF'` trong than
    # heredoc cua no. Mot dau `<<` trong THAN la VAN BAN, khong phai dau
    # mo thu hai. Nguyen van lenh da bi chan:
    ("commit message nhac toi mot heredoc khac",
     "git commit -q -F - <<'MSGEOF'\n"
     "sua: phep kiem duong dan\n\n"
     "  cat > /c/Users/x/Temp/y.py <<'EOF'\n\n"
     "het\nMSGEOF"),
]


def test_MAY_DO_bash_tu_chung_minh_no_bat_duoc():
    """Mẫu xấu phải bị chặn **bởi ĐÚNG luật**, mẫu tốt phải được tha.

    Vế "đúng luật" thêm 11/09/2026 sau khi đục thử cho thấy một mẫu vẫn
    xanh trong khi luật đang thử đã hoá mù — nó bị một luật KHÁC chặn.
    """
    for ten, lenh, mong_doi in XAU:
        bat = [t for t, _ in cb.kiem(lenh)]
        assert mong_doi in bat, (
            f"BỎ SÓT mẫu xấu: {ten}\n  {lenh!r}\n"
            f"  chờ luật {mong_doi!r}, thực tế bắt bởi {bat}")
    for ten, lenh in TOT:
        assert not cb.kiem(lenh), (
            f"KÊU OAN mẫu tốt: {ten}\n  {lenh!r}\n  -> {cb.kiem(lenh)}")
    print(f"PASS  cửa Bash bắt {len(XAU)}/{len(XAU)} xấu ĐÚNG LUẬT, "
          f"tha {len(TOT)}/{len(TOT)} tốt")


def test_BOC_chuoi_nhay_va_than_heredoc_roi_TACH_lenh_con():
    """Phép phán phải đọc CẤU TRÚC lệnh, không đọc sự xuất hiện của chữ.

    Ba luật của cửa này từng quét cả chuỗi lệnh bằng `[^\\n]*`, nên một
    chữ nằm trong `--body` của PR hay trong đối số của một lệnh KHÁC vẫn
    bị đọc như đối số của `git push`. Đếm được **8 lần chặn nhầm / 3 lần
    chặn đúng** trong hai ngày 10–11/09/2026.

    Đây là phép kiểm đi qua đúng cái hàm đang phán, không qua hàm gọi nó.
    """
    # noi dung trong nhay bi BOC, dau nhay o lai de con thay cau truc
    ra = cb.boc_va_tach("echo 'git push origin main'")
    assert len(ra) == 1
    assert "main" not in ra[0], f"noi dung nhay don chua bi boc: {ra[0]!r}"

    ra = cb.boc_va_tach('gh pr create --body "rm paper_trades.db"')
    assert "paper_trades" not in ra[0], f"nhay kep chua bi boc: {ra[0]!r}"

    # than heredoc bi BOC — ke ca dang KHONG trich dan
    ra = cb.boc_va_tach("cat <<EOF\ngit push origin main\nEOF\necho xong")
    assert not any("main" in c for c in ra), f"than heredoc con sot: {ra}"

    # tach o dau ngan lenh — BA dang, va phai kiem RIENG tung dang.
    #
    # Duc thu 11/09/2026 cho thay vi sao: mot ca `&&` KHONG phan biet duoc
    # nhanh `&&` voi ky tu `&` le, nen dot bien go han nhanh `&&` VAN SONG.
    # `||` thi khong co duong vong nao — `|` co y khong phai dau ngan.
    ra = cb.boc_va_tach("git push -u origin gac/x && git branch -a | grep main")
    assert len(ra) == 2, f"`&&` phai tach lam 2: {ra}"
    assert "main" not in ra[0]

    ra = cb.boc_va_tach("git push -u origin gac/x || git branch -a | grep main")
    assert len(ra) == 2, f"`||` phai tach lam 2: {ra}"
    assert "main" not in ra[0]

    # `;` phai la thu DUY NHAT cuu ca nay — chu `main` de TRAN, khong nam
    # trong nhay, nen phep boc khong giup gi.
    ra = cb.boc_va_tach("git push -u origin gac/x; git branch -a | grep main")
    assert len(ra) == 2, f"`;` phai tach lam 2: {ra}"
    assert "main" not in ra[0]
    assert not cb.kiem("git push -u origin gac/x; git branch -a | grep main")

    # ...NHUNG KHONG tach o dau ong: `pytest ... | tail` la MOT hinh dang,
    # tach no ra la giet mat luat pytest-qua-ong.
    ra = cb.boc_va_tach("pytest tests/ -q | tail -5")
    assert len(ra) == 1, f"khong duoc tach o dau ong: {ra}"

    # dau ngan NAM TRONG nhay thi khong phai dau ngan
    ra = cb.boc_va_tach("echo 'a && b'")
    assert len(ra) == 1, f"`&&` trong nhay bi doc thanh dau ngan: {ra}"

    print("PASS  boc_va_tach: bóc nháy · bóc heredoc · tách lệnh con · "
          "giữ ống · `&&` trong nháy không phải dấu ngăn")


def test_DUONG_TRONG_REPO_doc_giong_nhau_tren_MOI_he_dieu_hanh():
    """Phép kiểm đường dẫn không được phụ thuộc vào HĐH đang chạy nó.

    Bản đầu (11/09/2026) quy `/c/Users/…` của Git Bash về `C:/Users/…`
    rồi hỏi `pathlib.Path.is_absolute()`. Trên Windows đúng. Trên Linux
    `C:/Users/…` **không** có dấu `/` đầu nên bị đọc là TƯƠNG ĐỐI, rơi
    vào nhánh "coi như trong repo", và cửa chặn nhầm đúng cái mẫu nó vừa
    được sửa để tha.

    **Năm cổng tại máy đều xanh; CI đỏ ở lượt đầu tiên.** Cùng hình dạng
    với lỗi 26, và cùng cách vá: MÔ PHỎNG môi trường kia, đừng phụ thuộc
    vào việc tình cờ chạy ở đó.

    Nên phép kiểm này cấp cho hàm cả bốn quy ước đường dẫn, bất kể test
    đang chạy ở đâu.
    """
    NGOAI = [
        "/c/Users/x/AppData/Local/Temp/y.py",   # Git Bash
        "C:/Users/x/AppData/Local/Temp/y.py",   # Windows, gach xuoi
        "C:\\Users\\x\\AppData\\Local\\y.py",   # Windows, gach nguoc
        "/tmp/y.py",                            # POSIX
        "/home/runner/work/khac/khac/y.py",     # runner Linux
    ]
    for d in NGOAI:
        assert not cb._duong_trong_repo(d), f"{d!r} bị coi là TRONG repo"

    TRONG = [
        "tools/x.py",                     # tuong doi -> coi nhu trong repo
        "./docs/STATE.md",
        GOC.as_posix() + "/tools/x.py",   # tuyet doi, dung theo HDH nay
        str(GOC) + "/tools/x.py",
    ]
    for d in TRONG:
        assert cb._duong_trong_repo(d), f"{d!r} bị coi là NGOÀI repo"

    print(f"PASS  _duong_trong_repo: {len(NGOAI)} đường ngoài · "
          f"{len(TRONG)} đường trong, không phụ thuộc HĐH")


def test_KHONG_luat_nao_con_giu_LY_DO_DA_BI_BAC():
    """Lỗi 17 sống ngay trong thông báo của chính cửa.

    `push-thang-main` từng nêu hai lý do, và **cả hai đã bị đo là sai**:

      • "nhánh này có branch protection" — `gh api .../branches/main/
        protection` trả 404 "Branch not protected", đo 08/09/2026
      • "`gh` không cài trên máy này" — có, 2.100.0, đã đăng nhập

    Một cửa nêu lý do sai vẫn chặn đúng, nên không ai phát hiện. Nhưng
    người đọc thông báo ấy sẽ mang lý do sai đi chỗ khác — đúng cách lỗi
    17 lan ra.

    Gác dạng VĂN BẢN là hợp lệ ở đây: `vi_sao` thật sự là văn bản, không
    có cấu trúc nào để đọc bằng AST.

    KHÔNG cấm NHẮC TỚI cụm đã bị bác — cấm KHẲNG ĐỊNH nó. Hai việc khác
    nhau, và `docs/HANDOFF.md` mục 4 đã chọn giữa chúng từ 05/09/2026:
    *"giá trị cũ để trần được ở lại, NHƯNG PHẢI ĐÁNH DẤU"*. Một thông báo
    nói thẳng "lý do này đã bị đo và bác" dạy được nhiều hơn một thông
    báo im lặng xoá nó đi — người đọc sau sẽ không dựng lại nó lần nữa.

    Nên phép kiểm là: cụm bị bác xuất hiện thì trong cùng thông báo phải
    có dấu **BÁC**, đúng quy ước viết hoa dùng khắp `CLAUDE.md`.

    Bản ĐẦU của chính phép kiểm này cấm tuyệt đối, và nó đỏ ngay trên
    thông báo đã sửa ĐÚNG — phép kiểm sai so với chủ đích của nó, không
    phải mã sai. Ghi lại vì đây là cái bẫy hay gặp: sửa mã cho hết đỏ thì
    sẽ xoá mất đúng phần đáng giữ.
    """
    DA_BAC = [
        ("branch protection", "đo 08/09/2026: API trả 404 Branch not protected"),
        ("gh` không cài", "đo 08/09/2026: gh 2.100.0, đã đăng nhập"),
        ("gh không cài", "đo 08/09/2026: gh 2.100.0, đã đăng nhập"),
    ]
    hong = [(ten, cum, vi)
            for ten, _, vi_sao in cb.LUAT
            for cum, vi in DA_BAC
            if cum in vi_sao and "BÁC" not in vi_sao]
    assert not hong, (
        "luật KHẲNG ĐỊNH một lý do đã bị bác (nhắc tới thì được, nhưng "
        "phải kèm dấu `BÁC`):\n"
        + "\n".join(f"  [{t}] giữ {c!r} — {v}" for t, c, v in hong))

    # Chieu con lai: co luat nao THAT SU con nhac toi khong? Neu khong,
    # phep kiem nay dang canh mot cho trong va se im lang mai mai.
    co_nhac = [ten for ten, _, vi_sao in cb.LUAT
               if any(cum in vi_sao for cum, _ in DA_BAC)]
    assert co_nhac, (
        "không luật nào nhắc tới lý do đã bị bác nữa — phép kiểm này "
        "không còn canh gì. Xoá nó, hoặc nói rõ vì sao giữ.")
    print(f"PASS  {len(cb.LUAT)} luật · {len(co_nhac)} luật nhắc lý do đã "
          f"bác, tất cả đều đánh dấu BÁC")


def test_cua_thoat_phai_CO_LY_DO():
    lenh = "sed -i 's/a/b/' CLAUDE.md"
    assert cb.kiem(lenh), "mẫu nền phải bị chặn"
    assert not cb.kiem(lenh + "  # cua-ok: chay tren file ngoai repo")
    assert cb.kiem(lenh + "  # cua-ok:"), "lý do RỖNG mà vẫn cho qua"
    print("PASS  `# cua-ok:` phải kèm lý do")


def test_hook_bash_tra_2_khi_CHAN_va_0_khi_KHONG():
    """Chạy hook thật qua stdin — hàm `kiem()` đúng chưa đủ, hook phải nối."""
    import json

    def _chay(d):
        return subprocess.run(
            [PY, str(GOC / "tools" / "cua_bash_an_toan.py")],
            input=json.dumps(d), capture_output=True, text=True,
            encoding="utf-8").returncode

    assert _chay({"tool_name": "Bash",
                  "tool_input": {"command": "git push origin main"}}) == 2
    assert _chay({"tool_name": "Bash",
                  "tool_input": {"command": "git status"}}) == 0
    # tool khác thì không đụng tới
    assert _chay({"tool_name": "Read",
                  "tool_input": {"command": "git push origin main"}}) == 0
    # stdin hỏng thì NHƯỜNG ĐƯỜNG, không làm kẹt phiên
    assert subprocess.run(
        [PY, str(GOC / "tools" / "cua_bash_an_toan.py")],
        input="khong-phai-json", capture_output=True, text=True,
        encoding="utf-8").returncode == 0
    print("PASS  hook nối đúng: chặn 2 · cho qua 0 · hỏng thì nhường đường")


def test_moi_luat_deu_khai_NGUON():
    """Mỗi luật phải khai nó đến từ đâu. Hai nguồn, và chỉ hai.

        • SỰ CỐ THẬT   -> ngày dd/mm/yyyy, tra được trong docs/STATE.md
        • QUY ƯỚC      -> dấu `CHƯA CÓ SỰ CỐ` + tên file quy ước

    Viết một quy ước như thể nó là sự cố đã đo chính là bịa. Lượt chạy
    ĐẦU TIÊN của phép kiểm này bắt 4/8 luật của chính tác giả nó —
    `sed-i-file-repo`, `python-he-thong`, `push-thang-main`,
    `xoa-nhieu-nhanh` — cả bốn viết bằng giọng "đã xảy ra".

    Không neo SỐ LƯỢNG luật: bộ luật lớn dần mỗi khi có lỗi mới, và neo
    số là đúng lỗi bản `docs/HANDOFF.md` 19/08 mắc phải.
    """
    import re
    thieu = [ten for ten, _, vi_sao in cb.LUAT
             if not re.search(r"\d{2}/\d{2}/\d{4}", vi_sao)
             and "CHƯA CÓ SỰ CỐ" not in vi_sao]
    assert not thieu, (
        f"luật không khai nguồn: {thieu}\n"
        f"Thêm ngày sự cố, hoặc đánh dấu `CHƯA CÓ SỰ CỐ` kèm tên file "
        f"quy ước. Đừng viết quy ước bằng giọng sự cố.")

    quy_uoc = [ten for ten, _, vi_sao in cb.LUAT if "CHƯA CÓ SỰ CỐ" in vi_sao]
    # "môi trường" ĐÃ BỊ GỠ khỏi danh sách được chấp nhận (11/09/2026).
    #
    # Nó từng là một cửa thoát: luật `xoa-nhieu-nhanh` khai nguồn là
    # *"quan sát về môi trường: lệnh dạng này bị chặn ở đây"* — không
    # ngày, không lệnh, không ai tra được. Đo lại 11/09/2026 trên hai
    # nhánh ném đi: `git push origin --delete a b` chạy **trót lọt, mã
    # thoát 0**, xoá được cả hai. Lời khai SAI, và luật đã bị gỡ.
    #
    # Một câu về môi trường là một PHÉP ĐO, không phải một quy ước. Nó
    # phải có ngày để tra lại — đúng Bước 1 điều 2 của skill. Quy ước thì
    # phải nằm trong một file đọc được.
    khong_chi_file = [
        ten for ten, _, vi_sao in cb.LUAT
        if "CHƯA CÓ SỰ CỐ" in vi_sao
        and not re.search(r"(CLAUDE\.md|HANDOFF\.md|NGUYEN-TAC)", vi_sao)]
    assert not khong_chi_file, (
        f"luật quy ước không chỉ ra quy ước nằm ở đâu: {khong_chi_file}\n"
        f"Một câu về 'môi trường' KHÔNG còn được tính — nó là phép đo, "
        f"nên phải kèm ngày và lệnh tra lại được.")

    assert all(len(vi_sao) > 60 for _, _, vi_sao in cb.LUAT), (
        "có luật giải thích quá ngắn để hành động theo")
    print(f"PASS  {len(cb.LUAT)} luật · {len(cb.LUAT) - len(quy_uoc)} từ sự "
          f"cố có ngày · {len(quy_uoc)} từ quy ước, khai rõ")


# ───────────────────────── cua_ghi_an_toan ─────────────────────────

def test_cua_ghi_bat_file_rong_va_THA_file_co_noi_dung(tmp_path):
    rong = tmp_path / "a.py"
    rong.write_bytes(b"")
    co = tmp_path / "b.py"
    co.write_bytes(b"x = 1\n")
    khac_duoi = tmp_path / "c.bin"
    khac_duoi.write_bytes(b"")

    assert cg.rong_bat_thuong(rong) is True
    assert cg.rong_bat_thuong(co) is False
    assert cg.rong_bat_thuong(khac_duoi) is False, "đuôi lạ không phải việc"
    assert cg.rong_bat_thuong(tmp_path / "khong-ton-tai.py") is False
    print("PASS  bắt file rỗng, tha file có nội dung và đuôi lạ")


def test_hook_ghi_tra_2_khi_file_RONG(tmp_path):
    import json

    rong = tmp_path / "a.py"
    rong.write_bytes(b"")
    co = tmp_path / "b.py"
    co.write_bytes(b"x = 1\n")

    def _chay(duong):
        return subprocess.run(
            [PY, str(GOC / "tools" / "cua_ghi_an_toan.py")],
            input=json.dumps({"tool_name": "Write",
                              "tool_input": {"file_path": str(duong)}}),
            capture_output=True, text=True, encoding="utf-8").returncode

    assert _chay(rong) == 2
    assert _chay(co) == 0
    print("PASS  hook ghi: rỗng -> 2, có nội dung -> 0")


# ───────────────── hai cửa mới phải thật sự ĐƯỢC NỐI ─────────────────

# ───────────────────────── cua_mo_phien ─────────────────────────

def test_ban_tin_mo_phien_NEU_TEN_SKILL_doc_tu_dia():
    """Gõ tay tên skill vào lời nhắc là tạo thêm một chỗ lệch nữa."""
    import cua_mo_phien as mp

    ten = mp.ten_skill()
    assert ten == ["quy-trinh-lam-viec"], ten
    assert "quy-trinh-lam-viec" in mp.ban_tin()
    print(f"PASS  lời nhắc đọc tên skill từ đĩa: {ten}")


def test_moc_ngay_LOC_THEO_hom_nay():
    """PHÉP PHÁN. Mốc đã tới hạn thì không còn chặn, mốc tương lai thì có.

    Truyền `hom_nay` cố định nên phép kiểm này không mục ruỗng theo thời
    gian — nó vẫn đúng vào năm 2030.
    """
    import datetime as dt

    import cua_mo_phien as mp

    truoc = mp.moc_ngay_con_chan(dt.date(2026, 9, 7))
    assert [n for n, _ in truoc] == [dt.date(2026, 9, 12),
                                     dt.date(2026, 9, 17)], truoc

    giua = mp.moc_ngay_con_chan(dt.date(2026, 9, 13))
    assert [n for n, _ in giua] == [dt.date(2026, 9, 17)], giua

    sau = mp.moc_ngay_con_chan(dt.date(2026, 12, 31))
    assert sau == [], f"mốc đã qua vẫn còn báo chặn: {sau}"
    print("PASS  lọc đúng theo ngày: 2 -> 1 -> 0")


def test_cua_mo_phien_KHONG_BAO_GIO_hong_phien(tmp_path, monkeypatch):
    """Một hook mở phiên mà làm hỏng phiên thì tệ hơn không có.

    Chỉ vào một thư mục rỗng: không có HANDOFF, không có skill. Phải vẫn
    thoát 0 và vẫn in ra được thứ gì đó.
    """
    import cua_mo_phien as mp

    monkeypatch.setattr(mp, "HANDOFF", tmp_path / "khong-co.md")
    monkeypatch.setattr(mp, "THU_MUC_SKILL", tmp_path / "khong-co")
    assert mp.moc_ngay_con_chan() == []
    assert mp.ten_skill() == []
    assert "không thấy skill" in mp.ban_tin()
    assert mp.main() == 0
    print("PASS  thiếu hết mọi thứ vẫn thoát 0 và vẫn nói ra là thiếu")


def test_mo_phien_NUOT_LOI_du_ban_tin_no(monkeypatch, capsys):
    """Lớp chặn lỗi phải tự chứng minh được, không chỉ tồn tại.

    Đục thử 07/09/2026: gỡ `try/except` quanh `print(ban_tin())` mà bộ
    test vẫn XANH, vì ở đường chạy bình thường không có gì nổ. Cùng bẫy
    với `va_an_toan.kiem_hoan_tra` — lưới an toàn không được kiểm bằng
    đường chạy êm.

    Ép `ban_tin` nổ, rồi đòi `main()` vẫn trả 0. Một hook mở phiên làm
    hỏng phiên thì tệ hơn không có hook.
    """
    def _no():
        raise RuntimeError("giả vờ hỏng")

    monkeypatch.setattr(mp, "ban_tin", _no)
    assert mp.main() == 0, "ban_tin() nổ mà main() không nuốt -> hỏng phiên"
    print("PASS  ban_tin() nổ, main() vẫn trả 0")


def test_hook_mo_phien_thoat_0_khi_chay_that():
    kq = subprocess.run([PY, str(GOC / "tools" / "cua_mo_phien.py")],
                        capture_output=True, text=True, encoding="utf-8")
    assert kq.returncode == 0, kq.stderr[-300:]
    assert "quy-trinh-lam-viec" in (kq.stdout or "")
    print("PASS  chạy thật: thoát 0, có nhắc skill")


def test_hai_cua_moi_duoc_DANG_KY_dung_matcher():
    """Hook tồn tại mà không nối vào đâu thì bằng không có.

    Đột biến "đổi matcher thành NotebookEdit" từng SỐNG SÓT ngày
    31/08/2026 vì test chỉ đọc `command`, bỏ qua `matcher` — xem
    `CLAUDE.md`, bảng "Test KIỂM LẠI CHÍNH NÓ". Nên ở đây kiểm CẢ HAI,
    và kiểm cả SỰ KIỆN (`PreToolUse` khác `PostToolUse`: một cái là cửa,
    cái kia là chuông báo cháy).
    """
    import json
    import re

    # Bản KHAI, không phải nơi đăng ký — xem `docs/STATE.md` BƯỚC 49.
    # Giữ hook ở cả hai nơi làm chúng chạy HAI LẦN khi phiên mở ở repo.
    d = json.loads((GOC / "docs" / "cua-du-an.json").read_text(
        encoding="utf-8"))

    def _tim(su_kien: str, ten_file: str):
        for nhom in d.get("hooks", {}).get(su_kien, []):
            for h in nhom.get("hooks", []):
                if ten_file in str(h.get("command", "")):
                    return nhom.get("matcher", "")
        return None

    m = _tim("PreToolUse", "cua_bash_an_toan.py")
    assert m is not None, "cửa Bash chưa đăng ký ở PreToolUse"
    assert re.search(r"\bBash\b", m), (
        f"cửa Bash đăng ký với matcher {m!r} — nó sẽ không bao giờ chạy")

    m = _tim("PostToolUse", "cua_ghi_an_toan.py")
    assert m is not None, "cửa ghi chưa đăng ký ở PostToolUse"
    assert re.search(r"Write|Edit", m), (
        f"cửa ghi đăng ký với matcher {m!r}")

    assert _tim("PreToolUse", "cua_ghi_an_toan.py") is None, (
        "cửa ghi phải là PostToolUse — nó soi file SAU khi ghi")

    # Cửa mở phiên: SỰ KIỆN mới là thứ quyết định. Đăng ký nó ở PreToolUse
    # thì nó chạy trước MỌI thao tác — nhiễu tới mức bị tắt ngay.
    assert _tim("SessionStart", "cua_mo_phien.py") is not None, (
        "cửa mở phiên chưa đăng ký ở SessionStart — nó sẽ không bao giờ "
        "chạy, và lỗi số 10 (không biết dự án có skill) lặp lại")
    for sk in ("PreToolUse", "PostToolUse", "Stop"):
        assert _tim(sk, "cua_mo_phien.py") is None, (
            f"cửa mở phiên bị đăng ký nhầm ở {sk}")

    print("PASS  Bash→PreToolUse · ghi→PostToolUse · mở phiên→SessionStart")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print("Chạy bằng: pytest tests/test_cua_quy_trinh.py -q")
