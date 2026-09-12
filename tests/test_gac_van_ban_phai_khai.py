"""Khẳng định một MÃ NGUỒN chứa một ĐỊNH DANH thì phải KHAI vì sao dùng văn bản.

VÌ SAO CÓ FILE NÀY
──────────────────
`CLAUDE.md` có hẳn một mục tên **"Gác phải đọc AST, không đọc `in`"**. Hình
dạng nó cảnh báo đã cắn dự án **ba lần**:

    22/08/2026  "chi_so_moi_nhat" in src   — hai gac, ca hai van xanh sau
                                             khi loi goi bi xoa han, vi ten
                                             con nam trong khoi chu thich
    12/09/2026  "conclusion" not in ma     — do ngay luot chay dau, vi chinh
                                             docstring giai thich *vi sao
                                             khong doc chu ay* chua chu ay
                                             (loi 38)

Mục ấy được đọc trong cùng phiên mắc lỗi 38. **Tài liệu hoá một cái bẫy
không phải cơ chế chặn nó.** File này là cơ chế.

PHẠM VI HẸP CÓ CHỦ ĐÍCH — ĐÃ ĐẾM TRƯỚC KHI KÝ
─────────────────────────────────────────────
Đếm ngày 12/09/2026 trên `tests/`:

    407 cho  `<chuoi> in <ten>`          <- qua dong, phan lon HOP LE
      7 cho  `<DINH DANH> in <bien doc tu .read_text()>`

Bốn trong bảy chỗ ấy là văn-bản-thật (một thông báo lỗi, một file YAML, một
quy ước về tên đã chết trong tài liệu). Nên gác này **không cấm** — nó buộc
**nói ra**, đúng cơ chế `# bia-ok:` và `khong_soat_vi`.

Bài học lỗi 39 áp ở đây: **đếm cỡ nhóm trước khi ký.** Một gác chặn cả 407
chỗ sẽ là quan liêu; một gác chặn 7 chỗ thì trả giá được.
"""
import ast
import re
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
TESTS = GOC / "tests"
KHAI = re.compile(r"#\s*van-ban-ok:\s*(\S.*)$")
DINH_DANH = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*$")
DAI_TOI_THIEU = 20

sys.path.insert(0, str(GOC))


def bien_doc_tu_file(cay: ast.AST) -> set[str]:
    """Tên biến được gán từ một lời gọi `.read_text()` / `.read_bytes()`."""
    ra: set[str] = set()
    for n in ast.walk(cay):
        if not isinstance(n, (ast.Assign, ast.AnnAssign)):
            continue
        gt = n.value
        if not (isinstance(gt, ast.Call) and isinstance(gt.func, ast.Attribute)):
            continue
        if gt.func.attr not in ("read_text", "read_bytes"):
            continue
        dich = n.targets if isinstance(n, ast.Assign) else [n.target]
        ra.update(t.id for t in dich if isinstance(t, ast.Name))
    return ra


def cho_can_khai(duong: Path) -> list[tuple[int, str]]:
    """Mọi `<định danh> in/not in <biến đọc từ file>` trong một file test.

    Trả `(dòng, chuỗi)`. Đọc bằng AST — một gác về việc đọc-bằng-AST mà tự
    nó đọc bằng `in` thì đã tự bác mình.
    """
    try:
        cay = ast.parse(duong.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    bien = bien_doc_tu_file(cay)
    if not bien:
        return []
    ra = []
    for n in ast.walk(cay):
        if not isinstance(n, ast.Compare) or len(n.ops) != 1:
            continue
        if not isinstance(n.ops[0], (ast.In, ast.NotIn)):
            continue
        trai, phai = n.left, n.comparators[0]
        if not (isinstance(trai, ast.Constant) and isinstance(trai.value, str)):
            continue
        if not (isinstance(phai, ast.Name) and phai.id in bien):
            continue
        if not DINH_DANH.match(trai.value):
            continue
        ra.append((n.lineno, trai.value))
    return ra


def da_khai(dong_van: list[str], so_dong: int) -> str | None:
    """Lời khai trên CHÍNH dòng đó, hoặc trên dòng ngay trên nó.

    Hai chỗ thôi — cho phép khai ở bất cứ đâu trong hàm thì một lời khai cũ
    sẽ âm thầm che một phép kiểm mới thêm vào cùng hàm.
    """
    for i in (so_dong - 1, so_dong - 2):
        if 0 <= i < len(dong_van):
            m = KHAI.search(dong_van[i])
            if m:
                return m.group(1).strip()
    return None


def ly_do_hop_le(ly_do: str | None) -> bool:
    """Một lời khai có đủ tư cách là lời khai không.

    Tách thành hàm thuần CÓ CHỦ ĐÍCH. Để phép phán nằm thẳng trong test thì
    nó đọc `DAI_TOI_THIEU` từ chính module, và đột biến hằng số ấy làm mù
    **cả hai vế** — đục thử 12/09/2026 và phát ấy SỐNG SÓT thật. Cùng hình
    dạng lỗi 34: gác chỉ chạy trên đầu vào sạch thì mọi phép nới đều lọt.
    """
    MO_HO = {"ok", "can thiet", "cần thiết", "dung", "đúng",
             "hop le", "hợp lệ", "yaml", "markdown", "van ban"}
    if ly_do is None:
        return False
    ly_do = ly_do.strip()
    return len(ly_do) >= DAI_TOI_THIEU and ly_do.lower() not in MO_HO


def test_LY_DO_HOP_LE_phan_dung_ca_HAI_CHIEU():
    """Thử bằng mẫu DỰNG TAY, không bằng file thật.

    Chiều PHẢI-QUA và chiều PHẢI-CHẶN, cả hai. Một gác chỉ thấy đầu vào
    sạch không thể bị giết bởi đột biến nới lỏng.
    """
    PHAI_QUA = [
        "kiem-dinh.yml la YAML — AST cua Python khong doc duoc no",
        "quy uoc du an — TEN DA CHET khong duoc co mat trong tai lieu",
    ]
    PHAI_CHAN = [
        None, "", "   ", "ok", "yaml", "hop le", "dung",
        "van ban", "markdown", "ngan qua",
    ]
    for x in PHAI_QUA:
        assert ly_do_hop_le(x), f"ly do that bi chan: {x!r}"
    for x in PHAI_CHAN:
        assert not ly_do_hop_le(x), f"ly do rong/mo ho duoc cho qua: {x!r}"
    print(f"PASS  {len(PHAI_QUA)} qua · {len(PHAI_CHAN)} chan")


def test_NGUONG_DAI_khong_duoc_noi_am_tham():
    """Ngưỡng là một QUYẾT ĐỊNH. Đổi nó phải là một hành vi có chủ đích.

    Neo bằng một SỐ VIẾT THẲNG ở đây, không đọc lại hằng số — đọc lại thì
    đột biến hằng số làm mù cả hai vế, đúng phát đã sống sót.
    """
    assert DAI_TOI_THIEU >= 20, (
        f"DAI_TOI_THIEU = {DAI_TOI_THIEU}, duoi 20. Noi nguong nay lam moi "
        f"loi khai mot chu deu hop le, tuc gac thanh trang tri (loi 31).")
    assert not ly_do_hop_le("a" * 19), "19 ky tu khong duoc coi la mot ly do"
    assert ly_do_hop_le("a" * 40), "40 ky tu phai duoc chap nhan"
    print(f"PASS  nguong {DAI_TOI_THIEU} ky tu, neo bang so viet thang")


def test_MOI_khang_dinh_ve_MA_NGUON_deu_phai_KHAI_ly_do():
    """Thiếu `# van-ban-ok:` → đỏ. Đó là toàn bộ việc của gác này."""
    thieu = []
    for f in sorted(TESTS.glob("*.py")):
        dong_van = f.read_text(encoding="utf-8").splitlines()
        for so_dong, chuoi in cho_can_khai(f):
            if da_khai(dong_van, so_dong) is None:
                thieu.append(f"{f.name}:{so_dong}  \"{chuoi}\"")
    assert not thieu, (
        "Cac cho sau khang dinh mot MA NGUON chua mot DINH DANH bang phep so "
        "VAN BAN, ma khong khai vi sao:\n  " + "\n  ".join(thieu) +
        "\n\nHoac doc bang AST, hoac them `# van-ban-ok: <ly do>` tren chinh "
        "dong do. Xem CLAUDE.md muc 'Gac phai doc AST, khong doc `in`'.")
    print("PASS  moi khang dinh ve ma nguon deu co loi khai")


def test_LY_DO_KHONG_duoc_rong_hay_chung_chung():
    """`# van-ban-ok:` rỗng bị từ chối — cùng cơ chế `# bia-ok:`.

    Một ô thoát không đòi lý do thật thì gác này thành trang trí (lỗi 31).
    """
    xau = []
    for f in sorted(TESTS.glob("*.py")):
        dong_van = f.read_text(encoding="utf-8").splitlines()
        for so_dong, _ in cho_can_khai(f):
            ly_do = da_khai(dong_van, so_dong)
            if ly_do is not None and not ly_do_hop_le(ly_do):
                xau.append(f"{f.name}:{so_dong}  {ly_do!r}")
    assert not xau, (
        f"Ly do phai dai it nhat {DAI_TOI_THIEU} ky tu va khong chung chung:\n"
        "  " + "\n  ".join(xau))
    print("PASS  moi loi khai deu cu the")


def test_GAC_NAY_bat_dung_hinh_dang_da_can_that():
    """Dựng lại nguyên văn lỗi 38 và hai gác hỏng ngày 22/08/2026.

    Phép kiểm quan trọng nhất của file này: gác có bắt được đúng thứ nó
    sinh ra để bắt không. Mẫu dựng tay, không đọc file thật.
    """
    import tempfile

    BAT = [
        # loi 38 (12/09/2026) — nguyen van
        'ma = duong.read_text(encoding="utf-8")\n'
        'assert "conclusion" not in ma\n',
        # hai gac hong 22/08/2026
        'src = p.read_text()\n'
        'assert "chi_so_moi_nhat" in src\n',
        # ten co dau cham cung tinh
        'src = p.read_text()\n'
        'assert "sheets_store._COLS" not in src\n',
    ]
    BO_QUA = [
        # khong phai DINH DANH -> van ban that, khong dinh gi toi
        'src = p.read_text()\nassert "Không đặt lệnh thật" in src\n',
        # ve phai khong den tu file
        'ds = ["a", "b"]\nassert "a" in ds\n',
        # da khai -> khong tinh la thieu (kiem o phep kiem tren)
        'src = p.read_text()\n'
        'assert "x_y" in src  # van-ban-ok: day la mot ly do that su dai\n',
    ]
    with tempfile.TemporaryDirectory() as t:
        for i, mau in enumerate(BAT):
            f = Path(t) / f"t{i}.py"
            f.write_text(mau, encoding="utf-8")
            assert cho_can_khai(f), f"KHONG bat duoc mau phai bat:\n{mau}"
        for i, mau in enumerate(BO_QUA[:2]):
            f = Path(t) / f"b{i}.py"
            f.write_text(mau, encoding="utf-8")
            assert not cho_can_khai(f), f"bat NHAM mau khong duoc bat:\n{mau}"
        # mau thu ba CO bi bat, nhung da khai nen khong bi coi la thieu
        f = Path(t) / "b2.py"
        f.write_text(BO_QUA[2], encoding="utf-8")
        cho = cho_can_khai(f)
        assert cho, "mau da-khai van phai duoc NHAN DIEN"
        dv = BO_QUA[2].splitlines()
        assert da_khai(dv, cho[0][0]) is not None, "khong doc duoc loi khai"
    print(f"PASS  bat {len(BAT)}/{len(BAT)} mau da can that, "
          f"bo qua {len(BO_QUA)-1}/{len(BO_QUA)-1} mau hop le")


def test_LOI_KHAI_chi_tinh_tren_dong_do_hoac_dong_NGAY_TREN():
    """Khai ở xa thì một lời khai cũ sẽ che một phép kiểm mới cùng hàm."""
    dv = ["# van-ban-ok: mot ly do that su du dai de duoc chap nhan",
          "assert 1", "assert 2", "assert 3"]
    assert da_khai(dv, 2) is not None, "dong ngay tren phai tinh"
    assert da_khai(dv, 3) is None, "cach hai dong thi KHONG duoc tinh"
    assert da_khai(dv, 4) is None
    print("PASS  loi khai chi phu dung mot dong phia tren")
