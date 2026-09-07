"""Không gác nào được RẼ NHÁNH theo một cờ mà file test khác gán đè.

VÌ SAO CÓ FILE NÀY
──────────────────
Ngày 05/09/2026 một gác vừa viết xong đọc `getattr(paper_trading,
"CHO_PHEP_MO_LENH_MOI")` — tức giá trị **lúc chạy**. Nó **xanh khi chạy
một mình và ĐỎ trong bộ đầy đủ**, vì ba file test gán cờ ấy ở mức module
và pytest nạp mọi module lúc collect. May là nó đỏ: chiều ngược lại cho
một gác **không bao giờ kêu**, và nó sẽ được ghi vào nhật ký là "7/7 đỏ".

Ngày 07/09/2026 soát cả `tests/` bằng máy thì thấy chuyện đó đã xảy ra
sẵn ở một chỗ khác — `test_tran_von_cam_ket.py::
test_cong_MO_thi_ba_thu_bao_ve_phai_CO_MAT` mở đầu bằng

    if not pt.CHO_PHEP_MO_LENH_MOI:
        print("SKIP  cổng đang đóng")
        return

Đo được, cùng một test, khác mỗi danh sách file truyền cho pytest:

    chay mot minh                      -> re nhanh SKIP
    chay sau test_paper_trading.py     -> in "PASS  cong MO ..."

Cổng thật đang **ĐÓNG**. Nhánh thứ hai khẳng định điều ngược lại và vẫn
xanh. Nguy hiểm không nằm ở chỗ nó sai hôm nay, mà ở chỗ **điều kiện
kích hoạt của gác do file test khác quyết định, không do thứ nó canh.**
Dọn ba dòng gán kia đi — một việc đúng đắn — là gác lặng lẽ ngủ.

HỢP ĐỒNG
────────
Tập "tên bị rò" được SUY RA, không gõ tay: mọi tên `<module>.<TÊN>` bị
gán ở **mức module** trong bất kỳ file `tests/*.py` nào. Hôm nay tập ấy
có đúng một phần tử. Thêm một chỗ rò mới thì luật tự nới theo.

Rò rồi thì cấm **rẽ nhánh** theo nó (`if` / biểu thức ba ngôi). KHÔNG
cấm **khẳng định** nó — `assert pt.CHO_PHEP_MO_LENH_MOI is False` là
chính phép kiểm, không phải cái cổng quyết định có kiểm hay không.

GIỚI HẠN, nói ra chứ không giấu
───────────────────────────────
Gán ra biến trung gian rồi rẽ theo biến đó (`x = not pt.CO; if x:`) thì
máy này không thấy. Nó bắt hình dạng trực tiếp, là hình dạng đã xảy ra
thật hai lần. Nới rộng hơn sẽ phải suy luận luồng dữ liệu, và một gác
hay kêu oan thì sớm muộn bị tắt.
"""
import ast
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
THU_MUC_TEST = GOC / "tests"


def _mods_da_nhap(cay: ast.Module) -> set[str]:
    """Tên cục bộ của mọi module được import trong file."""
    ra = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            for a in n.names:
                ra.add(a.asname or a.name.split(".")[0])
    return ra


def _la_hang_so(ten: str) -> bool:
    return ten.isupper() and ten.replace("_", "").isalnum()


def _ten_ro_ri_tu_nguon(cac_src) -> set[str]:
    """TÊN bị gán `<mod>.<TÊN> = ...` ở MỨC MODULE — tức không hoàn tra.

    Hàm THUẦN, nhận danh sách mã nguồn, để tự chứng minh được mà không
    phải dựng file thật.
    """
    ra: set[str] = set()
    for src in cac_src:
        cay = ast.parse(src)
        mods = _mods_da_nhap(cay)
        for cau in cay.body:                      # CHỈ thân module
            if not isinstance(cau, ast.Assign):
                continue
            for t in cau.targets:
                if (isinstance(t, ast.Attribute)
                        and isinstance(t.value, ast.Name)
                        and t.value.id in mods
                        and _la_hang_so(t.attr)):
                    ra.add(t.attr)
    return ra


def _cac_file_test() -> list[Path]:
    """Danh sách file test — MỘT nguồn duy nhất cho cả trích lẫn quét.

    Hai bên đi hai đường thì một cái glob sai chỉ làm nửa phép kiểm câm,
    và nửa câm đó xanh.
    """
    return sorted(THU_MUC_TEST.glob("test_*.py"))


def _ten_ro_ri() -> set[str]:
    return _ten_ro_ri_tu_nguon(
        f.read_text(encoding="utf-8") for f in _cac_file_test())


def _cho_re_nhanh(src: str, ro_ri: set[str]) -> list[tuple[int, str]]:
    """PHÉP PHÁN. Mọi chỗ RẼ NHÁNH theo một tên trong `ro_ri`.

    Tách thành hàm riêng CÓ CHỦ ĐÍCH: để phép phán này nằm thẳng trong
    thân test thì phần tự chứng minh sẽ đi qua bộ TRÍCH chứ không đi qua
    bộ PHÁN, và đột biến vào chính chỗ phán sẽ sống sót. Đã mắc đúng lỗi
    đó ngày 05/09/2026.
    """
    ra: list[tuple[int, str]] = []
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.If):
            dk = n.test
        elif isinstance(n, ast.IfExp):
            dk = n.test
        else:
            continue
        for x in ast.walk(dk):
            if (isinstance(x, ast.Attribute)
                    and isinstance(x.ctx, ast.Load)
                    and x.attr in ro_ri):
                ra.append((n.lineno, x.attr))
    return ra


# ───────────────────────── phép quét thật ─────────────────────────

def test_may_quet_thuc_su_NHIN_THAY_file():
    """Glob hỏng thì cả hai phép dưới đây xanh vì không có gì để soi.

    Không neo con số — bộ test lớn dần mỗi ngày, và neo số là đúng lỗi
    `docs/HANDOFF.md` bản 19/08 mắc phải. Chỉ chặn số 0.
    """
    ds = _cac_file_test()
    assert ds, f"không thấy file test nào trong {THU_MUC_TEST}"
    assert Path(__file__).resolve() in {f.resolve() for f in ds}, (
        "máy quét không nhìn thấy chính nó — glob sai đuôi hoặc sai thư mục")
    print(f"PASS  máy quét nhìn thấy {len(ds)} file, gồm chính nó")


def test_khong_file_test_nao_re_nhanh_theo_co_bi_ro_ri():
    ro_ri = _ten_ro_ri()
    pham = []
    for f in _cac_file_test():
        for dong, ten in _cho_re_nhanh(f.read_text(encoding="utf-8"), ro_ri):
            pham.append(f"{f.name}:{dong} rẽ nhánh theo {ten}")
    assert not pham, (
        "gác rẽ nhánh theo giá trị LÚC CHẠY của một cờ mà file test khác "
        "gán đè — kết quả phụ thuộc thứ tự collect:\n  " + "\n  ".join(pham)
        + "\n\nĐọc từ NGUỒN bằng AST, như `tests/test_c5_noi_that.py::"
          "test_cong_C5_dang_DONG_trong_ma_nguon`.")
    print(f"PASS  {len(_cac_file_test())} file test · "
          f"tập tên bị rò {sorted(ro_ri)} · 0 chỗ rẽ nhánh")


# ────────────────── máy đo tự chứng minh nó bắt được ──────────────────

_XAU = [
    ("if trực tiếp",
     "import paper_trading as pt\n"
     "def test_x():\n"
     "    if not pt.CO_AN_TOAN:\n        return\n    assert 1\n"),
    ("if lồng trong biểu thức and",
     "import paper_trading as pt\n"
     "def test_x():\n"
     "    if pt.CO_AN_TOAN and 1:\n        assert 1\n"),
    ("biểu thức ba ngôi",
     "import paper_trading as pt\n"
     "def test_x():\n"
     "    v = 1 if pt.CO_AN_TOAN else 2\n    assert v\n"),
    ("getattr rồi so sánh trong if",
     "import paper_trading as pt\n"
     "def test_x():\n"
     "    if pt.CO_AN_TOAN is True:\n        assert 1\n"),
    ("if ở mức module",
     "import paper_trading as pt\n"
     "if pt.CO_AN_TOAN:\n    X = 1\n"),
]

_TOT = [
    ("khẳng định thẳng — chính phép kiểm",
     "import paper_trading as pt\n"
     "def test_x():\n    assert pt.CO_AN_TOAN is False\n"),
    ("đọc từ nguồn qua hàm riêng",
     "import paper_trading as pt\n"
     "def _tu_nguon():\n    return False\n"
     "def test_x():\n    if not _tu_nguon():\n        return\n    assert 1\n"),
    ("rẽ nhánh theo cờ KHÁC, không bị rò",
     "import paper_trading as pt\n"
     "def test_x():\n    if pt.CO_KHONG_RO_RI:\n        assert 1\n"),
    ("gán cờ, không rẽ nhánh theo nó",
     "import paper_trading as pt\n"
     "def test_x():\n    pt.CO_AN_TOAN = True\n    assert 1\n"),
]


def test_MAY_DO_tu_chung_minh_no_bat_duoc():
    """5 mẫu đã biết là xấu, 4 mẫu đã biết là tốt, cùng một cửa."""
    ro_ri = {"CO_AN_TOAN"}
    for ten, src in _XAU:
        assert _cho_re_nhanh(src, ro_ri), f"BỎ SÓT mẫu xấu: {ten}"
    for ten, src in _TOT:
        assert not _cho_re_nhanh(src, ro_ri), f"KÊU OAN mẫu tốt: {ten}"
    print(f"PASS  máy đo bắt {len(_XAU)}/{len(_XAU)} xấu, "
          f"tha {len(_TOT)}/{len(_TOT)} tốt")


def test_BO_TRICH_tu_chung_minh_no_phan_biet_duoc_muc_module():
    """Bộ trích phải phân biệt gán MỨC MODULE với gán TRONG HÀM.

    Gán trong hàm có thể được hoàn tra bằng `try/finally` — và
    `test_thi_hanh_dieu_kien_dung.py` làm đúng như vậy. Chỉ gán ở mức
    module mới chắc chắn không bao giờ hoàn tra.
    """
    muc_module = ("import paper_trading as pt\n"
                  "pt.CO_AN_TOAN = True\n")
    trong_ham = ("import paper_trading as pt\n"
                 "def test_x():\n    pt.CO_AN_TOAN = True\n")
    khong_hang_so = ("import paper_trading as pt\n"
                     "pt.duong_dan = 'x'\n")
    khong_phai_module = ("class A: pass\n"
                         "a = A()\n"
                         "a.CO_AN_TOAN = True\n")

    assert _ten_ro_ri_tu_nguon([muc_module]) == {"CO_AN_TOAN"}
    assert _ten_ro_ri_tu_nguon([trong_ham]) == set(), "gán trong hàm bị tính"
    assert _ten_ro_ri_tu_nguon([khong_hang_so]) == set()
    assert _ten_ro_ri_tu_nguon([khong_phai_module]) == set()
    print("PASS  bộ trích phân biệt mức module / trong hàm / không hằng số")


def test_tap_ro_ri_hom_nay_dung_nhu_da_do():
    """Neo lại phép đo 07/09/2026 để thấy khi nó đổi.

    KHÔNG khẳng định tập này phải khác rỗng: dọn hết chỗ rò là việc
    ĐÚNG, và một gác đỏ khi người ta sửa đúng thì sẽ bị tắt. Chỉ in ra,
    và chỉ chặn cái đã biết chắc.
    """
    ro_ri = _ten_ro_ri()
    assert isinstance(ro_ri, set)
    print(f"PASS  tập tên bị rò hiện tại: {sorted(ro_ri) or '(rỗng)'}")


if __name__ == "__main__":
    for ten, ham in sorted(globals().items()):
        if ten.startswith("test_"):
            ham()
