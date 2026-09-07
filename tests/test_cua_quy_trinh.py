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
import va_an_toan as va  # noqa: E402

PY = str(GOC / ".venv" / "Scripts" / "python.exe")


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

XAU = [
    ("hai heredoc", "python - <<'A'\nx\nA\npython - <<'B'\ny\nB\n"),
    ("heredoc ghi de file .py", "cat > tools/x.py <<'EOF'\nx\nEOF\n"),
    ("sed -i", "sed -i 's/a/b/' CLAUDE.md"),
    ("pytest qua ong tail", "./.venv/Scripts/python.exe -m pytest tests/ -q | tail -5"),
    ("python he thong", "python tools/kiem_cu_phap_311.py"),
    ("push thang main", "git push origin main"),
    ("xoa hai nhanh", "git push origin --delete a b"),
    ("xoa .db", "rm paper_trades.db"),
]

TOT = [
    ("mot heredoc", "./.venv/Scripts/python.exe - <<'EOF'\nprint(1)\nEOF\n"),
    ("pytest ghi ra log", "./.venv/Scripts/python.exe -m pytest tests/ -q > kq.log 2>&1"),
    ("venv python", "./.venv/Scripts/python.exe tools/kiem_cu_phap_311.py"),
    ("python -c ngan", "python -c \"print(1)\""),
    ("push len nhanh", "git push -u origin tinh/viec-moi"),
    ("xoa mot nhanh", "git push origin --delete tinh/viec-cu"),
    ("git log binh thuong", "git log --oneline -5"),
    ("doc file .db, khong xoa", "ls -la paper_trades.db"),
    ("main la ten thu muc, khong phai nhanh", "git push origin tinh/main-menu"),
]


def test_MAY_DO_bash_tu_chung_minh_no_bat_duoc():
    """8 mẫu đã biết là xấu, 9 mẫu đã biết là tốt, cùng một cửa."""
    for ten, lenh in XAU:
        assert cb.kiem(lenh), f"BỎ SÓT mẫu xấu: {ten}\n  {lenh!r}"
    for ten, lenh in TOT:
        assert not cb.kiem(lenh), (
            f"KÊU OAN mẫu tốt: {ten}\n  {lenh!r}\n  -> {cb.kiem(lenh)}")
    print(f"PASS  cửa Bash bắt {len(XAU)}/{len(XAU)} xấu, "
          f"tha {len(TOT)}/{len(TOT)} tốt")


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
    khong_chi_file = [
        ten for ten, _, vi_sao in cb.LUAT
        if "CHƯA CÓ SỰ CỐ" in vi_sao
        and not re.search(r"(CLAUDE\.md|HANDOFF\.md|NGUYEN-TAC|môi trường)",
                          vi_sao)]
    assert not khong_chi_file, (
        f"luật quy ước không chỉ ra quy ước nằm ở đâu: {khong_chi_file}")

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

    d = json.loads((GOC / ".claude" / "settings.json").read_text(
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
    print("PASS  cửa Bash nối PreToolUse/Bash · cửa ghi nối PostToolUse/Write|Edit")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print("Chạy bằng: pytest tests/test_cua_quy_trinh.py -q")
