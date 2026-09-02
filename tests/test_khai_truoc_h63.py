"""Gác cho bản khai trước h=63.

Một bản khai trước chỉ có giá trị nếu nó KHÔNG SỬA ĐƯỢC sau khi thấy kết
quả. Bộ gác này canh đúng chỗ dễ bị nới nhất — và mỗi chỗ đều là một lỗi
dự án đã mắc thật một lần.
"""
import ast
from pathlib import Path

import pytest

import khai_truoc_h63 as kt

GOC = Path(__file__).resolve().parents[1]
NGUON = GOC / "khai_truoc_h63.py"


def _ham(ten: str) -> ast.FunctionDef:
    cay = ast.parse(NGUON.read_text(encoding="utf-8"))
    ra = [n for n in ast.walk(cay)
          if isinstance(n, ast.FunctionDef) and n.name == ten]
    assert len(ra) == 1, f"thấy {len(ra)} hàm {ten}"
    return ra[0]


# ── 1. Điểm thiết kế KHÔNG được là giá trị đã quan sát ────────────────

def test_diem_thiet_ke_SUY_RA_tu_rao_hoa_von():
    """Kiểm HÌNH DẠNG biểu thức, không kiểm giá trị.

    `DIEM_THIET_KE = -0.025` gõ tay cho ra đúng cùng con số hôm nay và chỉ
    sai vào ngày ai đó chỉnh rào rồi tưởng điểm thiết kế đã đi theo. Bài
    học ba lần mắc ngày 31/08/2026 — xem CLAUDE.md, "Test KIỂM LẠI CHÍNH
    NÓ".
    """
    cay = ast.parse(NGUON.read_text(encoding="utf-8"))
    gan = [n for n in cay.body
           if isinstance(n, ast.Assign)
           and any(getattr(t, "id", None) == "DIEM_THIET_KE" for t in n.targets)]
    assert len(gan) == 1
    v = gan[0].value
    assert isinstance(v, ast.UnaryOp) and isinstance(v.op, ast.USub), (
        "DIEM_THIET_KE phải là số ÂM của rào, không phải hằng số gõ tay")
    assert isinstance(v.operand, ast.Name)
    assert v.operand.id == "RAO_HOA_VON_H63", ast.dump(v)


def test_diem_thiet_ke_NHO_HON_hieu_ung_da_quan_sat():
    """Winner's curse: −0,0349 là cực đại của 5 ô, nên nó thổi phồng.

    Neo lực vào nó là tự cho mình phép kiểm dễ. Điểm thiết kế phải là hiệu
    ứng NHỎ NHẤT còn đáng quan tâm — cùng lý lẽ đã dùng cho
    `paper_metrics.MUC_BAT_LOI` ngày 01/09 (lấy cận trên −0,92 chứ không
    lấy ước lượng điểm −1,99).
    """
    assert abs(kt.DIEM_THIET_KE) < abs(kt.RHO_DA_QUAN_SAT)
    assert kt.DIEM_THIET_KE != kt.RHO_DA_QUAN_SAT


@pytest.mark.parametrize("ten", ["sd_null_can", "boi_du_lieu_can",
                                 "nguong_bac_bo", "du_dieu_kien_chay"])
def test_KHONG_phep_tinh_luc_nao_doc_gia_tri_da_quan_sat(ten):
    """`RHO_DA_QUAN_SAT` chỉ để đối chiếu, KHÔNG được vào phép tính lực.

    Đây là đường mà một bản khai trước bị vô hiệu hoá êm nhất: giữ nguyên
    mọi chữ, chỉ lặng lẽ thay điểm thiết kế bằng con số đã nhìn thấy.
    """
    ten_bien = {n.id for n in ast.walk(_ham(ten)) if isinstance(n, ast.Name)}
    assert "RHO_DA_QUAN_SAT" not in ten_bien, (
        f"{ten}() đang đọc giá trị đã quan sát — lực bị neo vào winner's curse")


# ── 2. Hai phía, và không được nới ────────────────────────────────────

def test_hai_phia_va_alpha_5_phan_tram():
    assert kt.HAI_PHIA is True
    assert kt.ALPHA == 0.05
    assert kt.LUC_MUC_TIEU == 0.80


def test_mot_phia_se_LAM_YEU_phep_kiem_dung_nhu_da_khai(monkeypatch):
    """Đổi sang một phía làm cỡ mẫu cần giảm — bằng chứng cho lời khai.

    Test này không cấm một phía; nó ĐO cái giá đã nêu trong docstring, để
    con số 2,94 / 3,73 trong tài liệu không thể trôi mà không ai biết.
    """
    hai = kt.boi_du_lieu_can()
    monkeypatch.setattr(kt, "HAI_PHIA", False)
    mot = kt.boi_du_lieu_can()
    assert mot < hai
    assert round(hai, 2) == 3.73, hai
    assert round(mot, 2) == 2.94, mot


# ── 3. Cổng: phép kiểm này CHƯA được phép chạy ────────────────────────

def test_chua_du_luc_o_co_mau_HIEN_NAY():
    """Trạng thái hôm nay, ghi thành test để nó không âm thầm đổi."""
    duoc, ly_do = kt.du_dieu_kien_chay(kt.NULL_SD_HIEN, kt.RAO_HOA_VON_H63)
    assert duoc is False, ly_do
    assert "CHƯA ĐƯỢC CHẠY" in ly_do
    assert round(kt.luc_tai(kt.DIEM_THIET_KE), 3) == 0.305


def test_du_luc_thi_MO_cong():
    duoc, ly_do = kt.du_dieu_kien_chay(kt.sd_null_can(), kt.RAO_HOA_VON_H63)
    assert duoc is True, ly_do


def test_rao_doi_qua_nhieu_thi_DONG_cong():
    """Rào đổi nghĩa là chi phí hoặc phân phối nhãn đã đổi.

    Khi đó bản khai này nói về một bài toán khác, và dùng lại nó là mượn
    tính chính danh của một bản khai cho một câu hỏi nó chưa từng hỏi.
    """
    duoc, ly_do = kt.du_dieu_kien_chay(kt.sd_null_can(),
                                       kt.RAO_HOA_VON_H63 * 1.5)
    assert duoc is False
    assert "bài toán khác" in ly_do
    duoc2, _ = kt.du_dieu_kien_chay(kt.sd_null_can(),
                                    kt.RAO_HOA_VON_H63 * 1.1)
    assert duoc2 is True, "lệch 10% còn trong trần 20%, không được đóng"


# ── 4. Luật dấu giữ nguyên từ BƯỚC 9 ──────────────────────────────────

def test_rho_DUONG_co_y_nghia_la_BAC_BO_chu_khong_phai_tin_hieu():
    """Đảo chiều là giả thuyết CÓ HƯỚNG. Dương mạnh là động lượng.

    Nếu luật này lỏng ra thành "có ý nghĩa = tìm thấy", phép kiểm biến
    thành phép kiểm hai đuôi cho một giả thuyết một đuôi, và mọi con số
    lực ở trên nói về một phép kiểm khác.
    """
    assert "BÁC BỎ" in kt.phan_xu(+0.05)
    assert "KHÔNG bác bỏ" in kt.phan_xu(0.0)


def test_duoi_rao_hoa_von_KHONG_duoc_goi_la_DAT():
    """Nhánh "dưới rào" chỉ SỐNG ở đúng cỡ mẫu mà cổng mở — kiểm ở đó.

    Ở sd hiện nay (0,0160) ngưỡng bác bỏ là −0,0332, đã nằm NGOÀI rào
    0,025, nên mọi kết quả có ý nghĩa đều tự động trên rào và nhánh này
    không thể chạm tới. Ở sd lúc đủ lực (0,00828) ngưỡng thành −0,0180 và
    khoảng (0,0180 ; 0,025) mở ra: có ý nghĩa thống kê mà không bù nổi chi
    phí.

    Nói cách khác, điều khoản rào hoà vốn hôm nay là chữ chết, và nó sống
    dậy đúng vào ngày phép kiểm được phép đọc. Kiểm nó ở sd hiện nay là
    kiểm một nhánh không bao giờ chạy.
    """
    sd = kt.sd_null_can()
    assert kt.nguong_bac_bo(sd) > -kt.RAO_HOA_VON_H63, (
        "vùng 'có ý nghĩa nhưng dưới rào' phải TỒN TẠI ở cỡ mẫu đủ lực")
    assert "DƯỚI rào" in kt.phan_xu(-0.022, sd)
    assert "ĐẠT" in kt.phan_xu(-0.030, sd)
    # và ở sd hiện nay thì đúng là không chạm tới được
    assert kt.nguong_bac_bo() < -kt.RAO_HOA_VON_H63


def test_gia_tri_da_quan_sat_KHONG_dat_o_nguong_hai_phia_MOT_MINH():
    """−0,0349 vượt ngưỡng hai phía −0,0332 nếu kiểm MỘT MÌNH.

    Ghi lại chính xác vì đây là lý do phải có bản khai này: ô ấy *sẽ* cho
    ra "ĐẠT" nếu ai đó kiểm riêng nó trên đúng dữ liệu cũ. Thứ chặn việc
    đó không phải con số, mà là điều kiện "dữ liệu chưa dùng" cộng cổng
    lực ở mục 3.
    """
    assert kt.RHO_DA_QUAN_SAT < kt.nguong_bac_bo()
    assert round(kt.nguong_bac_bo(), 4) == -0.0332


# ── 5. Đây là BẢN KHAI, không phải thí nghiệm ─────────────────────────

def test_file_khai_truoc_KHONG_doc_du_lieu():
    """Không import pandas/numpy/module thí nghiệm, không đọc file, không mạng.

    Một bản khai trước mà chạm được vào dữ liệu thì không còn ai phân biệt
    được nó viết trước hay viết sau.
    """
    cay = ast.parse(NGUON.read_text(encoding="utf-8"))
    nhap = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            nhap |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            nhap.add((n.module or "").split(".")[0])
    assert nhap <= {"__future__", "statistics"}, f"import lạ: {nhap}"
