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

# ══ Rác sau đột biến — lỗi 76 ══════════════════════════════════════════
# `dot_bien` hoàn trả file nó VÁ, từng byte. Nhưng một đột biến có thể làm
# mã chạy GHI RA CHỖ KHÁC. Ngày 17/09/2026 phát *"đệm nằm trong cây repo"*
# đổi `ho_so.duong_dan_dem()` thành `GOC / TEN_DEM`; lượt pytest dưới đột
# biến ấy ghi một file đệm 32 KB vào gốc repo, và `git add -A` ngay sau đó
# quét nó vào commit. Cái gác của chính phép đệm kiểm ĐƯỜNG DẪN TRONG MÃ
# nên nó xanh — nó không biết gì về một file đã nằm sẵn trên đĩa.

import pytest  # noqa: E402


def _bai_de_rac(tmp_path: Path, ten_rac: str) -> tuple[Path, list[str]]:
    """Một bài thử mà lượt chạy GHI một file vào gốc repo."""
    muc_tieu = tmp_path / "muc_tieu_rac.py"
    muc_tieu.write_text("DE_RAC = 0\n", encoding="utf-8")
    rac = vat.GOC / ten_rac
    lenh = ["-c", f"import pathlib; "
                  f"pathlib.Path({str(rac)!r}).write_text('rac', "
                  f"encoding='utf-8')"]
    return muc_tieu, lenh


def test_DUC_THU_DE_LAI_FILE_o_GOC_REPO_thi_NO(tmp_path):
    """Ca thật của lỗi 76, dựng lại nguyên văn."""
    ten_rac = "vibe-rac-thu-nghiem.tmp"
    muc_tieu, lenh = _bai_de_rac(tmp_path, ten_rac)
    rac = vat.GOC / ten_rac
    try:
        with pytest.raises(vat.RacSauDotBien) as e:
            vat.dot_bien(muc_tieu, "DE_RAC = 0", "DE_RAC = 1", lenh)
        assert ten_rac in str(e.value), "loi khong GOI TEN muc moi"
        assert rac.exists(), (
            "gac KHONG duoc tu xoa — CLAUDE.md cam xoa file o goc repo "
            "ma chua hoi, va mot cong cu tu don se don nham")
    finally:
        rac.unlink(missing_ok=True)


def test_FILE_BI_VA_VAN_duoc_HOAN_TRA_khi_no_vi_RAC(tmp_path):
    """Phép canh rác không được NUỐT phép hoàn trả.

    Trong `finally`, `p.write_bytes(goc)` đứng TRƯỚC `kiem_khong_de_rac`.
    Đưa phép canh rác lên trên nó thì một lượt để rác sẽ nổ trước khi kịp
    hoàn trả, và file bị vá **ở lại dạng đột biến** — đúng thứ `dot_bien`
    sinh ra để không bao giờ xảy ra.
    """
    ten_rac = "vibe-rac-thu-nghiem-2.tmp"
    muc_tieu, lenh = _bai_de_rac(tmp_path, ten_rac)
    goc = muc_tieu.read_bytes()
    rac = vat.GOC / ten_rac
    try:
        with pytest.raises(vat.RacSauDotBien):
            vat.dot_bien(muc_tieu, "DE_RAC = 0", "DE_RAC = 1", lenh)
        assert muc_tieu.read_bytes() == goc, (
            "file bi va KHONG tro ve nguyen trang khi lo rac no")
    finally:
        rac.unlink(missing_ok=True)


def test_LUOT_DUC_THU_SACH_thi_KHONG_no(tmp_path):
    """Vế còn lại của cặp: một lượt sạch phải đi qua êm.

    Thiếu vế này thì một `kiem_khong_de_rac` nổ với MỌI đầu vào vẫn xanh
    ở phép kiểm trên — đúng lỗi 31 dịch sang chỗ khác.
    """
    muc_tieu, lenh = _bai_thu(tmp_path)
    da_giet = vat.dot_bien(muc_tieu, "GIA_TRI = 1", "GIA_TRI = 2", lenh)
    assert da_giet is True


def test_MUC_GOC_REPO_doc_duoc_va_KHONG_rong():
    """Một `_muc_goc_repo()` trả rỗng làm phép trừ luôn rỗng — gác câm."""
    muc = vat._muc_goc_repo()
    assert len(muc) > 20, f"goc repo chi thay {len(muc)} muc — doc hong?"
    assert "tools" in muc and "tests" in muc
