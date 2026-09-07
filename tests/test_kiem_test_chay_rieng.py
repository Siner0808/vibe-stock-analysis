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
