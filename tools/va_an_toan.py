"""Đường DUY NHẤT để vá một file trong repo, và để chạy một đột biến.

VÌ SAO CÓ FILE NÀY
──────────────────
Ngày 07/09/2026 rà lại một phiên làm việc: 11 lỗi quy trình, và **5 trong
số đó** đến từ đúng một chỗ — tự viết neo vá theo BYTE.

    neo dùng `\\n`   trên file CRLF   -> "neo khop 0 lan"  (3 lần)
    neo dùng `\\r\\n` trên file LF     -> "neo khop 0 lan"  (1 lần)
    tiếng Việt trong `b"..."`         -> SyntaxError       (1 lần)

Và trước đó, 05/09/2026, `Path.write_text(..., newline=<không hợp lệ>)`
làm `do_tre_khop.py` **rỗng 0 byte**: hàm mở file để ghi (cắt cụt) TRƯỚC
khi kiểm đối số.

Gốc chung: mỗi lượt vá lại tự chế một cách xử lý xuống dòng và mã hoá.

ĐO ĐƯỢC, VÀ NÓ BÁC MỘT LUẬT ĐANG CÓ
───────────────────────────────────
`CLAUDE.md` và skill từng ghi *"repo dùng CRLF"*. Đo 07/09/2026:

    trong INDEX (thứ thật sự được commit) : 412/412 file text là LF thuần
    trong working copy                    : 370 CRLF · 41 LF · 1 trộn lẫn
    core.autocrlf = true, không .gitattributes

Git quy đổi cả hai chiều. **Quy ước xuống dòng của bản trên đĩa không ảnh
hưởng tới thứ được commit.** Luật cũ không chỉ thừa — nó là nguyên nhân
của 5 lỗi kể trên, vì nó đẩy người ta sang thao tác byte.

Luật đúng: **đọc/ghi ở chế độ VĂN BẢN, để Python và git lo xuống dòng.**
Module này giữ nguyên quy ước cũ của từng file chỉ để diff khỏi nở ra —
đó là chuyện thẩm mỹ, không phải chuyện đúng sai.

CÁCH DÙNG

    from va_an_toan import thay, dot_bien

    thay("paper_metrics.py", "N_TOI_THIEU = 113", "N_TOI_THIEU = 120")

    dot_bien("paper_metrics.py", "z=2,30", "z=1,00",
             ["-m", "pytest", "tests/test_dieu_kien_dung_alpha.py", "-q"])
"""
import pathlib
import subprocess
import sys

GOC = pathlib.Path(__file__).resolve().parent.parent
PY_VENV = GOC / ".venv" / "Scripts" / "python.exe"


class NeoMoHo(Exception):
    """Neo khớp 0 lần hoặc nhiều hơn số lần đã khai — DỪNG, không đoán."""


def _quy_uoc(b: bytes) -> str:
    """Quy ước xuống dòng ĐANG CÓ của file: 'crlf', 'lf' hoặc 'tron'."""
    crlf = b.count(b"\r\n")
    lf = b.count(b"\n") - crlf
    if crlf and lf:
        return "tron"
    return "crlf" if crlf else "lf"


def doc(duong) -> str:
    """Đọc thành văn bản, mọi xuống dòng quy về '\\n'.

    Không bao giờ trả về `bytes`. Mọi phép so khớp phía trên đều làm trên
    văn bản đã chuẩn hoá, nên neo viết thế nào cũng khớp — đó chính là
    thứ 5 lỗi ngày 07/09 thiếu.
    """
    b = pathlib.Path(duong).read_bytes()
    return b.decode("utf-8").replace("\r\n", "\n")


def ghi(duong, noi_dung: str) -> None:
    """Ghi lại, GIỮ NGUYÊN quy ước xuống dòng cũ của file.

    Ghi qua file tạm rồi đổi tên: một lỗi giữa chừng không để lại file
    rỗng. Đó là đúng cách `do_tre_khop.py` mất sạch ngày 05/09/2026.
    """
    p = pathlib.Path(duong)
    cu = p.read_bytes() if p.exists() else b""
    qu = _quy_uoc(cu) if cu else "lf"        # file mới: LF, khớp index

    ra = noi_dung.replace("\r\n", "\n")
    if qu == "crlf":
        ra = ra.replace("\n", "\r\n")

    tam = p.with_suffix(p.suffix + ".dang-ghi")
    tam.write_bytes(ra.encode("utf-8"))
    tam.replace(p)


def thay(duong, cu: str, moi: str, *, so_lan: int = 1) -> None:
    """Thay `cu` bằng `moi`. Neo PHẢI khớp đúng `so_lan` lần, không thì nổ.

    Viết neo bằng '\\n' bình thường; hàm này so trên văn bản đã chuẩn hoá.
    """
    s = doc(duong)
    thay_duoc = s.count(cu)
    if thay_duoc != so_lan:
        raise NeoMoHo(
            f"{duong}: neo khớp {thay_duoc} lần, khai {so_lan}.\n"
            f"  neo: {cu[:120]!r}\n"
            f"Neo mơ hồ thì DỪNG, không đoán — một lượt vá đúng nửa còn "
            f"tệ hơn một lượt vá trượt hẳn, vì nó chạy được.")
    ghi(duong, s.replace(cu, moi, so_lan))


def dot_bien(duong, cu: str, moi: str, lenh: list[str],
             *, mo_ta: str = "", mong_doi: str = "DO") -> bool:
    """Đục thử: làm mã SAI đúng cách gác phải bắt, chạy, rồi HOÀN TRA.

    `lenh` là phần sau `python` (ví dụ `["-m", "pytest", "tests/x.py", "-q"]`).
    Trả True khi kết quả đúng `mong_doi` ("DO" = lệnh phải thất bại).

    Ba điều bắt buộc, cả ba đều từ sự cố thật:
      1. hoàn tra trong `finally` — dù test nổ giữa chừng
      2. so khớp TỪNG BYTE sau khi hoàn tra, không tin là đã trả đúng
      3. neo mơ hồ thì không chạy gì cả
    """
    p = pathlib.Path(duong)
    goc = p.read_bytes()
    ten = mo_ta or f"{p.name}: {cu[:40]}"

    s = doc(duong)
    if s.count(cu) != 1:
        raise NeoMoHo(f"{duong}: neo khớp {s.count(cu)} lần, phải đúng 1 "
                      f"({ten})")

    try:
        ghi(duong, s.replace(cu, moi, 1))
        kq = subprocess.run([str(PY_VENV)] + lenh, cwd=str(GOC),
                            capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
        that_bai = kq.returncode != 0
    finally:
        p.write_bytes(goc)
        kiem_hoan_tra(p, goc)

    return that_bai if mong_doi == "DO" else not that_bai


def kiem_hoan_tra(duong, goc: bytes) -> None:
    """Nổ nếu file không trở về ĐÚNG TỪNG BYTE như trước khi đục.

    Tách thành hàm riêng CÓ CHỦ ĐÍCH. Để phép kiểm này nằm thẳng trong
    `finally` thì đột biến `if con_lai != goc:` -> `if False:` **sống
    sót** — đã đục thử 07/09/2026 và nó sống thật. Test bên ngoài chỉ
    khẳng định "file đã trở về", nên nó xanh dù lưới an toàn bị gỡ.

    Có hàm riêng thì `tests/test_cua_quy_trinh.py` gọi thẳng được với một
    nội dung KHÁC và bắt nó phải nổ.
    """
    con_lai = pathlib.Path(duong).read_bytes()
    if con_lai != goc:
        raise RuntimeError(
            f"HOÀN TRA HỎNG: {duong} không trở về nguyên trạng. "
            f"{len(goc)} byte -> {len(con_lai)} byte. Dùng "
            f"`git checkout -- {duong}` NGAY.")


def _tu_kiem() -> None:
    """Chứng minh module tự nó chạy đúng, trước khi ai đó tin nó."""
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        # 1. giữ CRLF
        f = pathlib.Path(d) / "crlf.txt"
        f.write_bytes(b"mot\r\nhai\r\nba\r\n")
        thay(f, "hai", "HAI")
        assert f.read_bytes() == b"mot\r\nHAI\r\nba\r\n", f.read_bytes()

        # 2. giữ LF
        g = pathlib.Path(d) / "lf.txt"
        g.write_bytes(b"mot\nhai\nba\n")
        thay(g, "hai", "HAI")
        assert g.read_bytes() == b"mot\nHAI\nba\n", g.read_bytes()

        # 3. NEO ĐI QUA ĐƯỢC CẢ HAI QUY ƯỚC — đây là điểm của cả module
        h = pathlib.Path(d) / "hai_dong.txt"
        for goc in (b"mot\r\nhai\r\n", b"mot\nhai\n"):
            h.write_bytes(goc)
            thay(h, "mot\nhai", "MOT\nHAI")     # neo viet bang \n
            assert b"MOT" in h.read_bytes(), (goc, h.read_bytes())

        # 4. neo mơ hồ thì nổ, không sửa gì
        k = pathlib.Path(d) / "mo_ho.txt"
        k.write_bytes(b"x\nx\n")
        try:
            thay(k, "x", "y")
        except NeoMoHo:
            pass
        else:
            raise AssertionError("neo khớp 2 lần mà không nổ")
        assert k.read_bytes() == b"x\nx\n", "nổ rồi mà file vẫn bị sửa"

        # 5. tiếng Việt có dấu đi qua nguyên vẹn
        v = pathlib.Path(d) / "viet.txt"
        v.write_text("cổng đang đóng\n", encoding="utf-8")
        thay(v, "đóng", "MỞ")
        assert v.read_text(encoding="utf-8") == "cổng đang MỞ\n"


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    _tu_kiem()
    print("✅ va_an_toan tự kiểm xong: giữ CRLF · giữ LF · neo đi qua cả "
          "hai · neo mơ hồ thì nổ · tiếng Việt nguyên vẹn")
