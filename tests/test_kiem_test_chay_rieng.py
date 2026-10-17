"""Gác cho `tools/kiem_test_chay_rieng.py` — dụng cụ đi kiểm cũng hỏng được.

Công cụ ấy in ra "✅ Mọi file test xanh khi chạy một mình". Một câu như thế
là **kết quả sạch**, và `references/bay.md` mục 4 nói thẳng: kết quả "không
có gì" cũng đẹp theo cách riêng của nó — nó cho phép đi tiếp mà vẫn tỏ ra
nghiêm khắc. Nó phải được đối chiếu đúng như một kết quả dương.

Ba đường hỏng, cả ba đều làm công cụ báo SẠCH khi thật ra chưa kiểm gì:

  1. `chay_mot_file()` luôn trả xanh   -> mọi file đều "qua"
  2. glob sai                          -> không có file nào để soi
  3. phán xử bỏ qua danh sách hỏng     -> tìm ra rồi vẫn trả 0

Công cụ tự chặn (1) và (2) bằng `tu_kiem()` và bằng mã thoát 2. File này
chặn cả ba, từ bên ngoài, và chặn (3) — thứ `tu_kiem()` không với tới.
"""
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(GOC / "tools"))

import kiem_test_chay_rieng as k  # noqa: E402

XANH = "def test_a():\n    assert 1 == 1\n"
DO = "def test_b():\n    assert 1 == 2\n"


def _viet(thu_muc: Path, ten: str, noi_dung: str) -> Path:
    """Viết một file test vào `thu_muc`, kèm `pytest.ini` rỗng nếu chưa có (BƯỚC 206).

    `k.main()` chạy pytest LỒNG với cwd = repo. Tệp nằm ở `%TEMP%` mà thư mục không
    có tệp cấu hình thì rootdir là tổ tiên chung của repo và tệp — thư mục NHÀ — và
    pytest đi từ đó xuống `%TEMP%`, nơi mọi tiến trình tạo/xoá thư mục tạm (kể cả
    `tu_kiem()` ngay trước đó): `ERROR ../../../.. - FileNotFoundError` trên một
    `Temp/tmpXXXX` vừa bị xoá. Đo 17/10/2026, chạy cùng cổng 4: 11/116 lượt lồng đỏ;
    có `pytest.ini` thì 0/895. Tệp ấy ghim rootdir vào chính `thu_muc`.
    """
    ini = thu_muc / "pytest.ini"
    if not ini.exists():
        ini.write_text("[pytest]\n", encoding="utf-8")
    f = thu_muc / ten
    f.write_text(noi_dung, encoding="utf-8")
    return f


def test_chay_mot_file_phan_biet_xanh_voi_do(tmp_path):
    """Hàm chạy một file phải phân biệt được hai chiều, không chỉ một."""
    fx = _viet(tmp_path, "test_x.py", XANH)
    fd = _viet(tmp_path, "test_d.py", DO)

    xanh, tom_x = k.chay_mot_file(fx, tmp_path)
    do, tom_d = k.chay_mot_file(fd, tmp_path)

    assert xanh is True, f"file chắc chắn xanh lại báo đỏ: {tom_x}"
    assert do is False, f"file chắc chắn đỏ lại báo xanh: {tom_d}"
    print(f"PASS  xanh->{tom_x} · đỏ->{tom_d}")


def test_main_tra_1_khi_co_file_DO(tmp_path):
    """Đây là phép phán. Đột biến `if hong:` phải chết ở đây."""
    fd = _viet(tmp_path, "test_d.py", DO)
    assert k.main(["--im", str(fd)]) == 1
    print("PASS  có file đỏ -> mã thoát 1")


def test_main_tra_0_khi_moi_file_XANH(tmp_path):
    """Chiều ngược lại: một công cụ luôn trả 1 cũng vô dụng."""
    fx = _viet(tmp_path, "test_x.py", XANH)
    assert k.main(["--im", str(fx)]) == 0
    print("PASS  mọi file xanh -> mã thoát 0")


def test_main_tra_2_khi_DUNG_CU_hong(tmp_path, monkeypatch):
    """`chay_mot_file` luôn trả xanh → phải là CHƯA KIỂM ĐƯỢC, không phải sạch.

    Đây là hình dạng nguy hiểm nhất: công cụ chạy trơn tru, in ra một dấu
    tích, và chưa kiểm gì cả.
    """
    monkeypatch.setattr(k, "chay_mot_file", lambda *a, **kw: (True, "giả"))
    fd = _viet(tmp_path, "test_d.py", DO)
    assert k.main(["--im", str(fd)]) == 2
    print("PASS  dụng cụ luôn báo xanh -> mã thoát 2, KHÔNG phải 0")


def test_main_tra_2_khi_dung_cu_luon_bao_DO(tmp_path, monkeypatch):
    """Chiều kia của cùng phép tự kiểm."""
    monkeypatch.setattr(k, "chay_mot_file", lambda *a, **kw: (False, "giả"))
    assert k.main(["--im"]) == 2
    print("PASS  dụng cụ luôn báo đỏ -> mã thoát 2")


def test_main_tra_2_khi_KHONG_THAY_file_nao(tmp_path, monkeypatch):
    """Glob hỏng thì "không tìm thấy gì" trông y hệt "không có gì sai".

    Không truyền đối số file, để đi đúng nhánh glob.
    """
    monkeypatch.setattr(k, "THU_MUC_TEST", tmp_path)
    assert k.main(["--im"]) == 2
    print("PASS  glob không thấy file nào -> mã thoát 2")


def test_khong_doi_so_thi_soi_dung_thu_muc_tests():
    """Mặc định phải là `tests/` thật, không phải một chỗ nào khác.

    Không neo số lượng file — bộ test lớn dần mỗi ngày. Chỉ neo ĐỊA CHỈ.
    """
    assert k.THU_MUC_TEST == GOC / "tests"
    assert k.THU_MUC_TEST.is_dir()
    assert any(k.THU_MUC_TEST.glob("test_*.py"))
    print(f"PASS  mặc định soi {k.THU_MUC_TEST.relative_to(GOC)}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print("Chạy bằng: pytest tests/test_kiem_test_chay_rieng.py -q")


# ── BƯỚC 201: song song ─────────────────────────────────────────────────

def test_SONG_SONG_giu_dung_thu_tu_va_that_su_chay_cung_luc(tmp_path, monkeypatch):
    """Kết quả trả ĐÚNG thứ tự đầu vào; và có lúc ≥ 2 file chạy cùng lúc."""
    import threading
    import time as _t
    dang, dinh, khoa = [0], [0], threading.Lock()

    def gia(f, cwd):
        with khoa:
            dang[0] += 1
            dinh[0] = max(dinh[0], dang[0])
        _t.sleep(0.15 if f.name.endswith("0.py") else 0.05)
        with khoa:
            dang[0] -= 1
        return (not f.name.startswith("do"), f.name)

    monkeypatch.setattr(k, "chay_mot_file", gia)
    ds = [tmp_path / t for t in ("xanh0.py", "do1.py", "xanh2.py", "do3.py", "xanh4.py")]
    kq = k.chay_nhieu_file(ds, tmp_path, 4)
    assert [(f.name, x) for f, x, _ in kq] == [
        ("xanh0.py", True), ("do1.py", False), ("xanh2.py", True), ("do3.py", False), ("xanh4.py", True)]
    assert dinh[0] >= 2, "không có lúc nào hai file chạy cùng lúc"


def test_TUAN_TU_chi_mot_file_mot_luc(tmp_path, monkeypatch):
    import threading
    import time as _t
    dang, dinh, khoa = [0], [0], threading.Lock()

    def gia(f, cwd):
        with khoa:
            dang[0] += 1
            dinh[0] = max(dinh[0], dang[0])
        _t.sleep(0.03)
        with khoa:
            dang[0] -= 1
        return (True, "")

    monkeypatch.setattr(k, "chay_mot_file", gia)
    fx = tmp_path / "test_x.py"
    fx.write_text("def test_a():\n    assert True\n", encoding="utf-8")
    monkeypatch.setattr(k, "tu_kiem", lambda: None)
    assert k.main(["--im", "--tuan-tu", str(fx), str(fx), str(fx)]) == 0
    assert dinh[0] == 1


def test_MAC_DINH_suy_tu_so_nhan_khong_go_tay():
    """Hình dạng (AST): SO_TIEN_TRINH_MAC_DINH là biểu thức có gọi os.cpu_count()."""
    import ast
    cay = ast.parse(Path(k.__file__).read_text(encoding="utf-8"))
    gan = next(n for n in cay.body if isinstance(n, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id == "SO_TIEN_TRINH_MAC_DINH" for t in n.targets))
    goi = [n for n in ast.walk(gan.value) if isinstance(n, ast.Call)
           and isinstance(n.func, ast.Attribute) and n.func.attr == "cpu_count"]
    assert goi, ast.unparse(gan.value)
    assert k.SO_TIEN_TRINH_MAC_DINH >= 1


def test_MAC_DINH_main_chay_song_song(tmp_path, monkeypatch):
    """Không truyền gì thì main() chạy với SO_TIEN_TRINH_MAC_DINH file cùng lúc."""
    thay = {}
    monkeypatch.setattr(k, "tu_kiem", lambda: None)
    monkeypatch.setattr(k, "SO_TIEN_TRINH_MAC_DINH", 5)
    monkeypatch.setattr(k, "chay_nhieu_file",
                        lambda ds, cwd, n: thay.setdefault("n", n) and [(f, True, "") for f in ds])
    fx = tmp_path / "test_x.py"
    fx.write_text("def test_a():\n    assert True\n", encoding="utf-8")
    # argparse đọc mặc định lúc dựng parser → phải là giá trị LÚC CHẠY của hằng
    assert k.main(["--im", str(fx)]) == 0
    assert thay["n"] == 5


# ── BƯỚC 206: tên test hỏng ─────────────────────────────────────────────
# Sự cố 17/10/2026: cổng 4 (chạy cùng lúc với cổng 1) báo
# `⛔ test_suc_khoe.py — 1 failed, 103 passed`, chạy lại thì xanh — và báo cáo
# không nói test NÀO đỏ, nên không tái hiện được.

HAI = ("def test_xanh_rieng():\n    assert 1 == 1\n\n\n"
       "def test_hong_ten_rieng():\n    assert 1 == 2\n")


def test_FILE_DO_bao_ten_TUNG_test_hong_ngay_duoi_dong_tom_tat(tmp_path):
    f = _viet(tmp_path, "test_hai.py", HAI)
    xanh, tom = k.chay_mot_file(f, tmp_path)
    assert xanh is False
    dong = tom.splitlines()
    assert "1 failed, 1 passed" in dong[0], tom
    hong = [d.strip() for d in dong[1:]]
    assert len(hong) == 1 and hong[0].startswith("FAILED "), tom
    assert "test_hai.py::test_hong_ten_rieng" in hong[0], tom
    assert "test_xanh_rieng" not in tom


def test_TEN_test_hong_van_in_khi_cau_hinh_TAT_muc_tom_tat(tmp_path):
    """`-rfE` tường minh: `addopts = -rN` (tắt mục tóm tắt) không được làm mất tên."""
    (tmp_path / "pytest.ini").write_text("[pytest]\naddopts = -rN\n", encoding="utf-8")
    f = _viet(tmp_path, "test_hai.py", HAI)
    assert "-rN" in (tmp_path / "pytest.ini").read_text(encoding="utf-8"), "_viet đè mất cấu hình"
    xanh, tom = k.chay_mot_file(f, tmp_path)
    assert xanh is False and "test_hai.py::test_hong_ten_rieng" in tom, tom


def test_LOI_NAP_file_bao_ten_qua_dong_ERROR(tmp_path):
    f = _viet(tmp_path, "test_nap_hong.py", "import mo_dun_khong_ton_tai_206\n")
    xanh, tom = k.chay_mot_file(f, tmp_path)
    assert xanh is False
    assert any(d.strip().startswith("ERROR ") and "test_nap_hong.py" in d
               for d in tom.splitlines()[1:]), tom


def test_dong_test_hong_chi_lay_FAILED_ERROR_o_DAU_dong():
    ra = ("..F\n"
          "E   assert 1 == 2\n"
          "C:\\x\\test_a.py:6: RuntimeError: FAILED to ERROR out\n"
          "=========== short test summary info ===========\n"
          "FAILED tests/test_a.py::test_b - assert 1 == 2\n"
          "ERROR tests/test_c.py - ModuleNotFoundError\n"
          "1 failed, 1 error, 2 passed in 0.10s\n")
    assert k.dong_test_hong(ra) == ["FAILED tests/test_a.py::test_b - assert 1 == 2",
                                    "ERROR tests/test_c.py - ModuleNotFoundError"]
    assert k.dong_test_hong("3 passed in 0.10s\n") == []


def test_main_IM_in_ten_test_hong_vao_bao_cao(tmp_path, capsys):
    """Đường cổng 4 thật (`--im`, đi qua `chay_nhieu_file`) phải in tên ra log."""
    f = _viet(tmp_path, "test_hai.py", HAI)
    assert k.main(["--im", str(f)]) == 1
    ra = capsys.readouterr().out
    assert "test_hai.py::test_hong_ten_rieng" in ra, ra


def test_LUOT_LONG_co_rootdir_RIENG_khong_di_tu_thu_muc_NHA(tmp_path):
    """Lượt lồng như `k.main()` gọi (cwd = repo) trên file của `_viet`: rootdir = thư mục tạm.

    Thiếu ghim ấy rootdir là thư mục nhà và lượt lồng chập chờn khi máy chạy nhiều tiến
    trình — đo 17/10/2026: cổng 4 đỏ ở 2/3 chu kỳ năm cổng (`test_main_IM_in_ten…`), cổng 1
    ở 1/3 (`test_main_tra_0_khi_moi_file_XANH`, test có từ trước), một vòng lặp riêng 1/72."""
    import subprocess
    f = _viet(tmp_path, "test_x.py", XANH)
    kq = subprocess.run([sys.executable, "-m", "pytest", str(f), "--co", "-p", "no:cacheprovider"],
                        cwd=str(GOC), capture_output=True, text=True, encoding="utf-8",
                        errors="replace")
    assert f"rootdir: {tmp_path}" in kq.stdout, kq.stdout[-800:]

