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


def _moi_truong_rieng(thu_muc) -> dict:
    """Môi trường có TEMP trỏ sang thư mục riêng của test.

    Cửa Bash ghi nhật ký vào TEMP từ 14/09/2026, và nhật ký ấy là QUẦN
    THỂ để đo tỷ lệ bắt nhầm khi nới một luật. Một test bơm payload XẤU
    vào đó làm lệch đúng phép đo ấy.
    """
    import os

    return dict(os.environ, TMP=str(thu_muc), TEMP=str(thu_muc),
                TMPDIR=str(thu_muc))


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
    ("heredoc nap Python, than co DAU CHEO NHAN DOI (loi 56, lan 5)",
     "./.venv/Scripts/python.exe - <<'PY'\nmoi = 'a\\\\n> b'\nPY\n",
     "heredoc-python-co-escape"),
    ("pytest qua ong tail",
     "./.venv/Scripts/python.exe -m pytest tests/ -q | tail -5",
     "pytest-qua-ong"),
    ("python he thong", "python tools/kiem_cu_phap_311.py", "python-he-thong"),
    ("push thang main", "git push origin main", "push-thang-main"),
    ("xoa .db", "rm paper_trades.db", "xoa-db-goc-repo"),
    ("backtick trong python -c",
     './.venv/Scripts/python.exe -c "s = ```bash"',
     "backtick-trong-nhay-kep"),
    # Hien than THU HAI cua cung co che, cat that ngay 14/09/2026 o mot
    # cong cu khac han. Luat cu (chi canh `python -c`) KHONG bat duoc.
    ("backtick trong doi so cua mot lenh khac",
     './.venv/Scripts/python.exe tools/x.py --ly-do "dung `nguoi-thay` day"',
     "backtick-trong-nhay-kep"),
    ("backtick trong -m cua git commit",
     'git commit -m "sua `foo` thanh `bar`"',
     "backtick-trong-nhay-kep"),
    # Duong dan TUYET DOI nhung nam TRONG repo — van la ghi de file nguon.
    ("heredoc ghi de file repo bang duong tuyet doi",
     f"cat > {GOC.as_posix()}/tools/x.py <<'EOF'\nx\nEOF\n",
     "heredoc-ghi-file-repo"),
    # BON HINH DANG do duoc ngay 14/09/2026 la LOT, khi ra soat ca 8
    # luat xem luat nao canh HEP HON co che no neu. Xem BUOC 65.
    ("pytest qua ong SAU khi da co 2>&1 — hinh dang pho bien nhat",
     "./.venv/Scripts/python.exe -m pytest tests/ -q 2>&1 | tail -20",
     "pytest-qua-ong"),
    ("sed dang DAI --in-place, cung cong cu cung co che",
     "sed --in-place 's/a/b/' CLAUDE.md", "sed-i-file-repo"),
    ("python3.11 — van la python he thong",
     "python3.11 tools/kiem_cu_phap_311.py", "python-he-thong"),
    ("py launcher cua Windows",
     "py -3.11 tools/kiem_cu_phap_311.py", "python-he-thong"),
    # Hai heredoc o HAI LENH CON khac nhau van la cung mot loi.
    ("hai heredoc qua mot dau ngan",
     "bash - <<'A'\nx\nA\n&& bash - <<'B'\ny\nB\n",
     "hai-heredoc"),

    # ── NHOM 1 cua chin hinh dang con de ngo o BUOC 65, dong 17/09/2026.
    #    Ca bay deu do duoc la LOT ngay 14/09/2026, truoc khi co luat.
    ("ghi de file .py bang mot lenh KHONG phai heredoc",
     "echo 'x = 1' > tools/moi.py", "ghi-de-file-nguon"),
    ("ghi de file .md tu dau ra cua mot lenh khac",
     "./.venv/Scripts/python.exe tools/sinh.py > docs/STATE.md",
     "ghi-de-file-nguon"),
    ("ghi de mot workflow yml",
     "printf 'on: push' > .github/workflows/x.yml", "ghi-de-file-nguon"),
    # `xoa-db-goc-repo` chi canh `rm`, nen duong nay di lot.
    ("cat cut mot file .db bang `>`",
     "sqlite3 x .dump > paper_trades.db", "ghi-de-db"),
    ("perl -i — cung co che voi sed -i, khac cong cu",
     "perl -i -pe 's/a/b/' CLAUDE.md", "va-tai-cho-khac-sed"),
    ("perl -i.bak — dang co duoi sao luu",
     "perl -i.bak -pe 's/a/b/' CLAUDE.md", "va-tai-cho-khac-sed"),
    ("ruby -i", "ruby -i -pe 'x' CLAUDE.md", "va-tai-cho-khac-sed"),
]

# Moi dong duoi day la mot lan CHAN NHAM da do duoc, hoac mot loi khai da
# bi BAC bang phep do. Chung khong phai gia dinh — xem BUOC 51.
TOT = [
    # Luat `heredoc-python-co-escape` CO Y hep. Hai dong duoi day la
    # ranh gioi cua no, do 17/09/2026 truoc khi bat.
    ("heredoc nap Python nhung than KHONG co escape",
     "./.venv/Scripts/python.exe - <<'PY'\nprint(1)\nPY\n"),
    ("heredoc co dau cheo NHAN DOI nhung KHONG nap Python",
     "cat <<'EOF' > /tmp/x\na\\\\nb\nEOF\n"),
    # Dau cheo DON song sot DUNG qua duong heredoc — do 17/09/2026.
    # Chan no la chan mot thu khong hong.
    ("heredoc nap Python, than co DAU CHEO DON",
     "./.venv/Scripts/python.exe - <<'PY'\ns = 'a\\nb'\nprint(s)\nPY\n"),
    # Ba dong duoi day la BAT NHAM do duoc ngay 14/09/2026, ngay luot dau
    # tien sau khi noi luat backtick. Chung la ly do co pham vi thu tu
    # `DOC_GIU_NHAY` va mau doi mot CAP nhay dong lai.
    ("nhay DON — dung cach sua, phai con dung duoc",
     "./.venv/Scripts/python.exe tools/x.py --ly-do 'dung `a` day'"),
    ("backtick trong nhay DON, sau mot cap nhay KEP da dong",
     "git commit -m \"ok\" --author 'a`b'"),
    # Trong nhay kep, bash chi cho `\\` giu nghia dac biet truoc $ ` \" \\
    # va xuong dong. Nen `\\`` la mot backtick VAN BAN, khong noi suy gi.
    ("backtick DA THOAT trong nhay kep — bash khong noi suy",
     "echo \"gia tri \\`a\\` o day\""),
    ("than heredoc CO trich dan: bash KHONG noi suy nen backtick vo hai",
     "./.venv/Scripts/python.exe - <<'PYEOF'\n"
     "RONG = re.compile(r\"[^x]*`\")\n"
     "print(\"gia tri `a` o day\")\n"
     "PYEOF\n"),
    # Do 14/09/2026: NOI luat pytest ra MOI ong se bat nham hai ca
    # duoi day, nen luat chi noi toi `tail|head`. Giu chung o day de
    # phep noi ay khong lang le xay ra sau nay.
    # BAT NHAM do duoc tren NHAT KY CUA ngay 14/09/2026, ngay sau khi
    # lop phu dinh duoc noi ra sang `2>&1`. Xem loi 54.
    ("ten luat `pytest-qua-ong` la mot DINH DANH, khong phai lenh pytest",
     "./.venv/Scripts/python.exe tools/soat_nhat_ky_cua.py "
     "--thu-luat pytest-qua-ong 2>&1 | tail -12"),
    ("pytest --collect-only qua ong wc — ma thoat khong quan trong",
     "./.venv/Scripts/python.exe -m pytest --collect-only -q | wc -l"),
    ("ong THUOC mot lenh KHAC, sau dau `;`",
     "./.venv/Scripts/python.exe -m pytest tests/ -q > log 2>&1; "
     "grep FAIL log | head -3"),
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

    # ── Do 17/09/2026, TRUOC khi bat ba luat moi: day la nhung hinh dang
    #    ma mot ban rong hon se bat nham. Ca chin deu la thao tac THAT
    #    dung hang ngay trong repo nay.
    ("ghi log — `>` vao file .log, khong phai file nguon",
     "./.venv/Scripts/python.exe -m pytest tests/ -q > /tmp/kq.log 2>&1"),
    ("ghi /dev/null", "cat x > /dev/null"),
    # `>>` NOI THEM, khong cat cut. Hai dau khac nhau, hai co che khac nhau.
    ("NOI THEM vao mot file .md", "echo 'them' >> docs/ghi-chu.md"),
    # Dang heredoc da co luat RIENG (`heredoc-ghi-file-repo`), va luat ay
    # tha duong NGOAI repo. Hai luat cung phan mot hinh dang la hai thong
    # bao va hai cho de troi ra khoi nhau.
    ("ghi file .py NGOAI repo, khong qua heredoc",
     "echo x > /c/Users/x/AppData/Local/Temp/y.py"),
    ("perl KHONG co -i — khong va tai cho",
     "perl -pe 's/a/b/' CLAUDE.md"),
    # Do mot ban sao so lenh ra TEMP de soi la thao tac AN TOAN, va la
    # duong di vong da dung ngay 12/09/2026. Luat `ghi-de-db` chi phan
    # khi dich nam TRONG repo.
    ("ghi mot file .db RA NGOAI repo",
     "sqlite3 paper_trades.db .dump > "
     "/c/Users/x/AppData/Local/Temp/ban-sao.db"),
    ("van ban NHAC toi mot lenh ghi de",
     "git commit -m 'dung chay echo x > tools/a.py nua'"),
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


def test_MOI_HINH_DANG_XAU_thuoc_ve_DUNG_MOT_LUAT():
    """Một hình dạng, một luật. Hai luật cùng phán là hai chỗ để trôi.

    VÌ SAO CÓ PHÉP KIỂM NÀY (17/09/2026). Luật `ghi-de-file-nguon` cố ý
    **nhường** dạng heredoc cho `heredoc-ghi-file-repo` — hai cơ chế
    giống nhau nhưng cách sửa khác nhau, và hai thông báo cho một hình
    dạng thì người đọc phải tự chọn tin cái nào. Đột biến gỡ phép nhường
    ấy **sống sót** ở lượt đầu: mọi mẫu vẫn bị chặn *bởi ít nhất* luật
    đã khai, nên không phép kiểm nào đỏ.

    Thứ phép kiểm cũ hỏi là *"có bị luật ĐÚNG chặn không"*. Thứ nó KHÔNG
    hỏi là *"có bị luật nào KHÁC chặn cùng lúc không"*.

    Đo 17/09/2026 trước khi khai thành luật: **0 trên 23** mẫu xấu bị
    nhiều hơn một luật phán. Nên đây là một tính chất ĐANG CÓ, không
    phải một mong muốn.
    """
    nhieu = []
    for ten, lenh, mong_doi in XAU:
        bat = sorted({t for t, _ in cb.kiem(lenh)})
        if len(bat) != 1:
            nhieu.append(f"{ten}: đợi [{mong_doi}], bị {bat} phán")
    assert not nhieu, (
        "có hình dạng bị NHIỀU luật cùng phán:\n  "
        + "\n  ".join(nhieu)
        + "\nMột hình dạng phải thuộc về đúng một luật — nếu không, "
          "người bị chặn nhận hai thông báo và hai cách sửa.")
    print(f"PASS  {len(XAU)} hình dạng xấu, mỗi cái đúng MỘT luật")


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


def test_hook_bash_tra_2_khi_CHAN_va_0_khi_KHONG(tmp_path):
    """Chạy hook thật qua stdin — hàm `kiem()` đúng chưa đủ, hook phải nối."""
    import json

    def _chay(d):
        # CACH LY TEMP. Tu 14/09/2026 cua ghi nhat ky vao TEMP, va nhat
        # ky ay la QUAN THE de do ty le bat nham khi noi mot luat. Mot
        # test bom payload XAU vao do lam lech dung phep do ay — cung
        # hinh dang loi 49, lan nay o chieu nguoc lai: khong phai do sai
        # quan the, ma la LAM BAN quan the.
        #
        # Do duoc: 11 dong `git push origin main` trong nhat ky, khong
        # dong nao do nguoi go.
        return subprocess.run(
            [PY, str(GOC / "tools" / "cua_bash_an_toan.py")],
            input=json.dumps(d), capture_output=True, text=True,
            encoding="utf-8", env=_moi_truong_rieng(tmp_path)).returncode

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
        encoding="utf-8", env=_moi_truong_rieng(tmp_path)).returncode == 0
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


def test_DAU_VA_cua_CHUYEN_HUONG_khong_phai_dau_ngan_lenh():
    """`&` trong `2>&1` KHÔNG tách lệnh — nếu tách, năm luật hoá mù.

    Máy tách là nền dùng chung. Tới 14/09/2026 nó cắt

        pytest ... -q 2>&1 | tail -20
    thành
        'pytest ... -q 2>'   và   '1 | tail -20'

    Cái ống rơi sang đoạn không còn chữ `pytest` nào, nên
    `pytest-qua-ong` mù với chính hình dạng phổ biến nhất của thứ nó
    sinh ra để bắt — và tôi gõ đúng hình dạng ấy nhiều lần trong một
    ngày mà không lần nào bị chặn.
    """
    mot_doan = [
        "./.venv/Scripts/python.exe -m pytest tests/ -q 2>&1 | tail -20",
        "./.venv/Scripts/python.exe x.py &> out.txt",
        "./.venv/Scripts/python.exe x.py >&2",
    ]
    for l in mot_doan:
        assert len(cb.boc_va_tach(l)) == 1, (
            f"`&` cua chuyen huong bi coi la dau ngan lenh:\n"
            f"  {l!r}\n  -> {cb.boc_va_tach(l)}")

    # Nhung `&` THAT SU la dau ngan thi van phai tach.
    assert len(cb.boc_va_tach("cmd1 & cmd2")) == 2
    assert len(cb.boc_va_tach("a; b")) == 2
    print("PASS  `&` cua chuyen huong khong tach, `&` chay nen thi co")


# ══ CHUỖI `khong_soat_vi` — lỗi 86 ═════════════════════════════════════
#
# Bản tin mở phiên phải NÓI RA khi nhiều lượt liên tiếp đều bỏ soát chéo.
# Nó không chặn gì; nó chỉ làm một hình dạng vô hình thành nhìn thấy được.
#
# Gác hiển nhiên hơn — *cấm lặp lý do* — đã được ĐO và BÁC (18/09/2026):
# sáu lời khai của lỗi 86 giống nhau trung bình **0,131**, còn THẤP HƠN
# mức trung bình của mọi cặp khác trong sổ (0,099 nền, cao nhất 0,653 ở
# một cặp KHÔNG liên quan). Chúng không bị chép — mỗi lượt một lý do thật
# sự khác, và chính điều đó làm chúng vô hình. Đừng dựng lại gác ấy.


def _so_gia(*the):
    """Sổ dựng tay: `the` là dãy 'k' (khong_soat_vi) hoặc 'p' (phat_hien)."""
    return {f"M{i}": ({"khong_soat_vi": f"ly do rieng so {i}"} if t == "k"
                      else {"phat_hien": [{"noi_dung": "x"}]})
            for i, t in enumerate(the)}


def test_CHUOI_dem_tu_CUOI_SO_va_dut_o_mot_luot_HOI_THAT():
    assert mp.chuoi_khong_soat(_so_gia("k", "k", "k")) == ["M0", "M1", "M2"]
    assert mp.chuoi_khong_soat(_so_gia("k", "k", "p")) == [], (
        "mot luot HOI THAT o CUOI phai cat chuoi ve 0")
    assert mp.chuoi_khong_soat(_so_gia("p", "k", "k")) == ["M1", "M2"], (
        "chi dem tu CUOI tro len, khong dem ca so")
    assert mp.chuoi_khong_soat({}) == []


def test_CHUOI_dem_theo_THU_TU_GHI_chu_khong_theo_NGAY():
    """Nhiều mục cùng một ngày; thứ tự GHI mới là thứ tự người ta đi qua."""
    so = {"A": {"khong_soat_vi": "x", "ngay": "2026-09-18"},
          "B": {"phat_hien": [{"noi_dung": "y"}], "ngay": "2026-09-01"},
          "C": {"khong_soat_vi": "z", "ngay": "2026-09-18"}}
    assert mp.chuoi_khong_soat(so) == ["C"], (
        "sap theo ngay se gop A va C lai — phai theo thu tu ghi")


def test_CHUOI_bo_qua_khoa_KHONG_phai_muc(     ):
    """Sổ có khoá `_ghi_chu`, `_moc_buoc`… là chuỗi, không phải mục."""
    so = {"M0": {"khong_soat_vi": "x"}, "_ghi_chu": "day khong phai muc",
          "M1": {"khong_soat_vi": "y"}}
    assert mp.chuoi_khong_soat(so) == ["M0", "M1"]


def test_BAN_TIN_KEU_khi_chuoi_dat_nguong_va_IM_khi_chua(monkeypatch):
    """Cả hai chiều. Một gác chỉ thấy đầu vào sạch thì không giết được
    đột biến nới lỏng."""
    monkeypatch.setattr(mp, "chuoi_khong_soat",
                        lambda *a, **k: ["M1", "M2", "M3"])
    assert "LIÊN TIẾP" in mp.ban_tin(), "dat nguong ma ban tin IM"
    monkeypatch.setattr(mp, "chuoi_khong_soat", lambda *a, **k: ["M1", "M2"])
    assert "LIÊN TIẾP" not in mp.ban_tin(), "duoi nguong ma van keu"


def test_BAN_TIN_neu_TEN_muc_chu_khong_chi_dem():
    """Một con số trơ trọi là thứ lỗi 78 đã cấm — phải gọi tên."""
    import unittest.mock as m
    with m.patch.object(mp, "chuoi_khong_soat",
                        lambda *a, **k: ["BƯỚC 104", "ĐO 13", "BƯỚC 106"]):
        t = mp.ban_tin()
    assert "BƯỚC 106" in t and "ĐO 13" in t, t


def test_NGUONG_la_mot_QUYET_DINH_khong_duoc_noi_am_tham():
    """Neo bằng số viết THẲNG — đọc lại hằng số thì đột biến vào hằng số
    làm mù cả hai vế, đúng phát đã sống sót ở `kiem_so_test`."""
    assert mp.NGUONG_CHUOI_BO_SOAT <= 3, (
        f"nguong = {mp.NGUONG_CHUOI_BO_SOAT}, noi rong hon 3 thi chuoi sau "
        f"muc cua loi 86 van lot qua o nhung lan dau")
    assert mp.NGUONG_CHUOI_BO_SOAT >= 2, "duoi 2 thi moi luot bo soat deu keu"


def test_DUNG_LAI_CA_THAT_loi_86_ban_tin_PHAI_keu():
    """Ca thật, đọc từ chính sổ: bỏ mục cuối đi là đúng trạng thái lúc lỗi
    86 xảy ra. Đây là phép kiểm duy nhất ở đây chạy trên quần thể THẬT."""
    import json
    so = json.loads((GOC / "docs" / "soat-notebooklm.json")
                    .read_text(encoding="utf-8"))["soat"]
    ten = [k for k, v in so.items() if isinstance(v, dict)]
    luc_hong = {k: v for k, v in so.items() if k != ten[-1]}
    c = mp.chuoi_khong_soat(luc_hong)
    assert len(c) >= mp.NGUONG_CHUOI_BO_SOAT, (
        f"chuoi luc loi 86 xay ra chi {len(c)} — ban tin se IM dung luc "
        f"can keu: {c}")
    assert "BƯỚC 106" in c, c
