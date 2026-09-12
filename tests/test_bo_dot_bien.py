"""`va_an_toan.dot_bien_bo` phải trả PHÁT SỐNG SÓT, không trả phát bị giết.

VÌ SAO CÓ FILE NÀY
──────────────────
Lỗi 37 (12/09/2026): `dot_bien` trả `True` khi đột biến **bị giết**. Một
script gọi nó đọc ngược đúng quy ước ấy và in ra **"0/10 đỏ"** cho một bộ
thật ra **10/10 đỏ**. Không ngoại lệ, không cảnh báo.

`dot_bien_bo` gom quy ước ấy về một chỗ. Nhưng gom về một chỗ chỉ có giá trị
nếu **chính chỗ ấy được kiểm theo CẢ HAI chiều** — một hàm trả danh sách rỗng
cho mọi đầu vào sẽ báo "đủ đỏ" mãi mãi, tức đúng lỗi 31 dịch sang chỗ khác.

Nên hai phép kiểm dưới đây phải đi thành cặp: một đột biến PHẢI chết, một đột
biến PHẢI sống, và hàm phải phân biệt được hai cái.
"""
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))

import va_an_toan as vat  # noqa: E402


def _bai_thu(tmp_path: Path) -> tuple[Path, list[str]]:
    """Một file bé và một lệnh phán về nó. Không đụng gì trong repo."""
    muc_tieu = tmp_path / "muc_tieu.py"
    muc_tieu.write_text("GIA_TRI = 1\n", encoding="utf-8")
    lenh = ["-c", f"import sys; sys.path.insert(0, {str(tmp_path)!r}); "
                  "import muc_tieu; "
                  "sys.exit(0 if muc_tieu.GIA_TRI == 1 else 1)"]
    return muc_tieu, lenh


def test_DOT_BIEN_BI_GIET_khong_nam_trong_danh_sach_tra_ve(tmp_path):
    muc_tieu, lenh = _bai_thu(tmp_path)
    song = vat.dot_bien_bo(muc_tieu,
                           [("doi gia tri", "GIA_TRI = 1", "GIA_TRI = 2")],
                           lenh, in_ra=False)
    assert song == [], f"dot bien BI GIET ma van bao song: {song}"
    print("PASS  dot bien bi giet -> danh sach rong")


def test_DOT_BIEN_SONG_SOT_PHAI_co_ten_trong_danh_sach(tmp_path):
    """Chiều thứ hai. Thiếu nó thì `return []` qua được phép kiểm trên."""
    muc_tieu, lenh = _bai_thu(tmp_path)
    song = vat.dot_bien_bo(muc_tieu,
                           [("chi them chu thich",
                             "GIA_TRI = 1", "GIA_TRI = 1  # khong doi gi")],
                           lenh, in_ra=False)
    assert song == ["chi them chu thich"], (
        f"dot bien SONG SOT ma khong duoc goi ten: {song}")
    print("PASS  dot bien song sot -> co ten trong danh sach")


def test_MOT_BO_TRON_hai_kieu_thi_CHI_ke_ten_phat_song(tmp_path):
    """Phép kiểm thật sự: hàm phải PHÂN BIỆT, không phải luôn rỗng hay luôn đủ."""
    muc_tieu, lenh = _bai_thu(tmp_path)
    song = vat.dot_bien_bo(
        muc_tieu,
        [("chet", "GIA_TRI = 1", "GIA_TRI = 99"),
         ("song", "GIA_TRI = 1", "GIA_TRI = 1  # vo hai")],
        lenh, in_ra=False)
    assert song == ["song"], f"phan biet sai: {song}"
    print(f"PASS  bo tron hai kieu -> chi ke ten phat song: {song}")


def test_HOAN_TRA_nguyen_trang_sau_ca_bo(tmp_path):
    """Mỗi phát phải trả file về đúng từng byte — kể cả phát sống sót."""
    muc_tieu, lenh = _bai_thu(tmp_path)
    goc = muc_tieu.read_bytes()
    vat.dot_bien_bo(
        muc_tieu,
        [("chet", "GIA_TRI = 1", "GIA_TRI = 5"),
         ("song", "GIA_TRI = 1", "GIA_TRI = 1  # vo hai")],
        lenh, in_ra=False)
    assert muc_tieu.read_bytes() == goc, "file khong tro ve nguyen trang"
    print("PASS  file tro ve dung tung byte sau ca bo")
