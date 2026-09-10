"""Cổng thứ năm: số test không được giảm âm thầm.

Bốn cổng cũ đo thứ ĐANG CÓ. Không cổng nào so với thứ ĐÃ TỪNG CÓ — nên
ngày 09/09/2026 một lệnh `cat >` đè mất 40 phép kiểm và cả bốn đều xanh.
File này khoá cái cổng vá lỗ đó.

Phép kiểm ĐẦU TIÊN dựng lại nguyên văn sự cố ấy (834 so với 874), theo
đúng Bước 3 của skill: *"Phát đầu tiên phải là dựng lại nguyên văn lỗi
thật — gác có bắt được đúng thứ nó sinh ra để bắt không."*
"""
import ast
import json
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))

import kiem_so_test_khong_giam as cong  # noqa: E402

MOC_874 = {"so_test": 874, "cap_nhat_luc": "2026-09-10"}


# ══ 1. Sự cố thật ══════════════════════════════════════════════════════

def test_DUNG_LAI_su_co_09_09_834_thay_vi_874_phai_BI_CHAN():
    """Nguyên văn lỗi 23. Nếu phép kiểm này xanh thì cổng vô dụng."""
    ma, loi_nhan = cong.quyet_dinh(834, MOC_874)
    assert ma == 1, "834 so voi moc 874 mà KHONG bi chan"
    assert "GIAM" in loi_nhan and "40" in loi_nhan, (
        f"thong bao khong noi ro mat bao nhieu: {loi_nhan!r}")
    print(f"PASS  834/874 -> ma {ma}, thong bao neu dung so mat")


# ══ 2. Ba nhánh quyết định ═════════════════════════════════════════════

def test_khop_thi_qua():
    ma, _ = cong.quyet_dinh(874, MOC_874)
    assert ma == 0


def test_TANG_ma_chua_cap_nhat_moc_cung_bi_CHAN():
    """Không phải khắt khe thừa — mốc trôi tụt lại thì lỗ hổng đúng bằng
    khoảng cách đó, và nó lớn dần mà không ai thấy."""
    ma, loi_nhan = cong.quyet_dinh(900, MOC_874)
    assert ma == 1, "tang ma khong cap nhat moc lai duoc cho qua"
    assert "TANG" in loi_nhan
    print("PASS  874 -> 900 chua cap nhat moc: bi chan")


@pytest.mark.parametrize("thuc_te,moc,vi_sao", [
    (None, MOC_874, "khong dem duoc test"),
    (874, None, "khong doc duoc moc"),
])
def test_KHONG_DEM_DUOC_tra_2_chu_KHONG_tra_0(thuc_te, moc, vi_sao):
    """Trạng thái thứ ba là bắt buộc. Một công cụ không chạy được mà trả 0
    thì chính nó là cổng xanh giả — đúng thứ nó sinh ra để chặn."""
    ma, loi_nhan = cong.quyet_dinh(thuc_te, moc)
    assert ma == 2, f"{vi_sao}: tra {ma} thay vi 2"
    assert "CHUA KIEM DUOC" in loi_nhan


# ══ 3. Cửa thoát — buộc NÓI RA, không phải cấm ═════════════════════════

def test_GIAM_ma_KHONG_co_ly_do_thi_TU_CHOI():
    with pytest.raises(ValueError) as e:
        cong.cap_nhat(860, MOC_874, "", "2026-09-10")
    assert "ly-do" in str(e.value)


@pytest.mark.parametrize("ly_do", ["", "   ", "\n\t "])
def test_ly_do_RONG_hay_TOAN_KHOANG_TRANG_deu_bi_TU_CHOI(ly_do):
    """`# bia-ok:` rỗng cũng bị từ chối vì đúng lý do này: một cửa thoát
    không đòi nội dung thì nó chỉ là một câu thần chú."""
    with pytest.raises(ValueError):
        cong.cap_nhat(860, MOC_874, ly_do, "2026-09-10")


def test_GIAM_co_ly_do_thi_QUA_va_ly_do_di_vao_LICH_SU():
    moi = cong.cap_nhat(860, MOC_874, "gop hai file test trung", "2026-09-10")
    assert moi["so_test"] == 860
    assert len(moi["lich_su_giam"]) == 1
    g = moi["lich_su_giam"][0]
    assert (g["tu"], g["xuong"]) == (874, 860)
    assert g["ly_do"] == "gop hai file test trung"
    print("PASS  giam co ly do -> ghi vao lich su, nam trong diff")


def test_TANG_thi_KHONG_them_dong_lich_su_giam():
    moi = cong.cap_nhat(900, MOC_874, "", "2026-09-10")
    assert moi["so_test"] == 900
    assert "lich_su_giam" not in moi


def test_cap_nhat_KHONG_lam_hong_lich_su_da_co():
    cu = dict(MOC_874, lich_su_giam=[{"ngay": "2026-01-01", "tu": 9,
                                      "xuong": 8, "ly_do": "cu"}])
    moi = cong.cap_nhat(860, cu, "moi", "2026-09-10")
    assert [g["ly_do"] for g in moi["lich_su_giam"]] == ["cu", "moi"]
    assert cu["lich_su_giam"][0]["ly_do"] == "cu", "da SUA vao ban goc"


# ══ 4. Đọc số — chỗ một lỗi im lặng biến "mất gần hết" thành "sạch" ════

@pytest.mark.parametrize("ra,mong", [
    ("874 tests collected in 0.63s", 874),
    ("1 test collected in 0.10s", 1),          # SỐ ÍT — pytest đổi chữ
    ("no tests ran", None),
    ("", None),
])
def test_doc_so_test(ra, mong):
    assert cong.doc_so_test(ra) is mong or cong.doc_so_test(ra) == mong


def test_KHONG_DOC_DUOC_phai_la_None_chu_khong_phai_0():
    """`0` nghĩa là "đếm được, và bằng 0" — nó sẽ báo mất TOÀN BỘ test.
    `None` nghĩa là "chưa đếm được". Trộn hai thứ là sinh báo động giả."""
    assert cong.doc_so_test("loi gi do") is None


# ══ 5. Mốc trên đĩa phải là số THẬT — chống trôi ═══════════════════════

def test_MOC_TREN_DIA_khop_so_test_THAT():
    """Phép kiểm tự soi. Thêm hay bớt test mà quên cập nhật mốc thì đỏ
    NGAY tại máy, không phải đợi tới CI."""
    moc = cong.doc_moc()
    assert moc is not None, "khong doc duoc docs/moc_so_test.json"
    that = cong.dem_test()
    assert that is not None, "khong dem duoc test that"
    assert moc["so_test"] == that, (
        f"moc ghi {moc['so_test']} nhung dem duoc {that}. Chay:\n"
        f"  ./.venv/Scripts/python.exe tools/kiem_so_test_khong_giam.py"
        f" --cap-nhat")
    print(f"PASS  moc {moc['so_test']} == so test that")


def test_file_moc_la_JSON_hop_le_va_co_du_truong():
    d = json.loads((GOC / "docs/moc_so_test.json").read_text(encoding="utf-8"))
    assert isinstance(d["so_test"], int) and d["so_test"] > 0
    assert d["cap_nhat_luc"]


# ══ 6. Cổng phải được NỐI VÀO CI, không chỉ tồn tại ════════════════════

def test_CI_that_su_goi_cong_nay():
    """Một cổng không ai gọi thì không phải cổng. Lỗi 14 của dự án là
    đúng hình dạng đó: sáu cửa dựng xong, không cửa nào từng chạy."""
    yml = (GOC / ".github/workflows/kiem-dinh.yml").read_text(encoding="utf-8")
    assert "kiem_so_test_khong_giam.py" in yml, (
        "kiem-dinh.yml khong goi cong so test")
    print("PASS  kiem-dinh.yml co goi cong nay")


def test_cong_co_DU_BA_trang_thai_thoat():
    """Đọc bằng AST, không bằng `in`: chính khối chú thích đầu file công
    cụ đã chứa chữ `return 2`."""
    cay = ast.parse((GOC / "tools/kiem_so_test_khong_giam.py")
                    .read_text(encoding="utf-8"))
    h = [n for n in ast.walk(cay)
         if isinstance(n, ast.FunctionDef) and n.name == "quyet_dinh"][0]
    ma_tra = {n.value.elts[0].value for n in ast.walk(h)
              if isinstance(n, ast.Return) and isinstance(n.value, ast.Tuple)}
    assert ma_tra == {0, 1, 2}, f"quyet_dinh chi tra {sorted(ma_tra)}"
    print("PASS  quyet_dinh tra du ca 0, 1 va 2")


if __name__ == "__main__":
    for ten, ham in sorted(globals().items()):
        if ten.startswith("test_") and not hasattr(ham, "pytestmark"):
            ham()
