"""Phép đối chiếu trích dẫn phải bỏ ĐỦ BA lớp nhiễu — thiếu một lớp là vu oan.

VÌ SAO CÓ FILE NÀY
──────────────────
Luật ký 18/09/2026 (BƯỚC 108): *"`grep` ra 0 dòng CHƯA đủ để kết tội bịa —
grep lại một chuỗi con đặc trưng, bỏ dấu nhấn."* Đúng chiều, **hẹp hơn thứ
nó đo**.

Ngày 21/09/2026, đối chiếu 15 trích dẫn sổ tay vừa đưa ra:

    luot 1  grep TUNG DONG, giu dau nhan    ->   8 khop · 4 nghi BIA
    luot 3  bo du BA lop                    ->  14 khop ·  1 BIA that

Ba lớp, mỗi lớp một mình đủ làm một câu THẬT trả về 0 dòng: dấu nhấn
Markdown · ngắt dòng cứng ~76 ký tự · dấu trích dẫn `> ` đầu dòng.

Mọi mẫu dưới đây là **ca thật đã cắn**, không phải mẫu dựng cho đẹp.
"""
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))

import doi_chieu_trich_dan as d  # noqa: E402

#: Ca thật lớp 1 — sổ tay dẫn câu này ngày 18/09/2026, `grep` ra 0 dòng,
#: và nó KHÔNG bịa: nguyên bản chỉ khác ở hai cặp sao.
LOP1_TAI_LIEU = "**Không:** nó chỉ đọc VĂN BẢN. Chỗ 3 và 6 phải mở mã."
LOP1_SO_TAY = "Không: nó chỉ đọc VĂN BẢN."

#: Ca thật lớp 2 + lớp 3 — câu nằm trong một khối blockquote của `SKILL.md`,
#: ngắt dòng cứng giữa câu, nên mỗi dòng mang thêm `> `.
LOP23_TAI_LIEU = (
    "> Gác: `tests/test_do_phai_khai_da_tra.py`. Nó **không** biết lời khai\n"
    "> có đúng không; nó chặn đúng một thứ — **một phép đo đã ký mà không ai\n"
    "> nói được đã tra trùng hay chưa**. Hai lỗi sinh ra nó: lỗi 41.\n"
)
LOP23_SO_TAY = ("nó chặn đúng một thứ — một phép đo đã ký mà không ai nói "
                "được đã tra trùng hay chưa.")

#: Ca BỊA THẬT, và là ca duy nhất trong 15: sổ tay dựng một tiêu đề khác
#: hẳn cho BƯỚC 106. Nguyên bản: "## BƯỚC 106 — ĐO 13: `urllib3` 1.26.20
#: → 2.8.0, dữ liệu KHÔNG đổi một ô (18/09/2026)".
BIA = ("## BƯỚC 106 — NÂNG urllib3 2.8.0, VÀ Ô ĐỐI CHỨNG KHÔNG CÓ TRONG "
       "BA LẦN NÂNG TRƯỚC (18/09/2026)")


def test_LOP_1_dau_nhan_Markdown_khong_duoc_lam_lech():
    """`**đậm**`, `` `mã` ``, `_nghiêng_` nằm GIỮA câu — ca 18/09/2026."""
    ban = {"x.md": d.chuan_hoa(LOP1_TAI_LIEU)}
    assert d.tim(LOP1_SO_TAY, ban) == ["x.md"]
    print("PASS  lớp 1 — dấu nhấn Markdown")


def test_LOP_2_ngat_dong_cung_khong_duoc_lam_lech():
    """Một câu dài nằm trên 2-3 dòng thì `grep` từng dòng KHÔNG BAO GIỜ khớp."""
    tai_lieu = "nó chặn đúng một thứ — một phép đo đã ký\nmà không ai nói được."
    ban = {"x.md": d.chuan_hoa(tai_lieu)}
    assert d.tim("một phép đo đã ký mà không ai nói được.", ban) == ["x.md"]
    print("PASS  lớp 2 — ngắt dòng cứng")


def test_LOP_3_dau_trich_dan_dau_dong_khong_duoc_lam_lech():
    """Lớp này chỉ lộ ra ở lượt đối chiếu THỨ BA, 21/09/2026.

    Lượt hai đã bỏ dấu nhấn và nối liền dòng, vẫn trượt — vì khi nối liền,
    mỗi dòng trong khối blockquote mang theo một `> ` vào GIỮA câu.
    """
    ban = {"SKILL.md": d.chuan_hoa(LOP23_TAI_LIEU)}
    assert d.tim(LOP23_SO_TAY, ban) == ["SKILL.md"]
    print("PASS  lớp 3 — dấu trích dẫn `> `")


def test_THIEU_MOT_LOP_la_du_de_VU_OAN():
    """Chiều ngược lại: chứng minh từng lớp THẬT SỰ cần, không phải trang trí.

    Nếu thiếu lớp 3 thì đúng câu ở trên trả về RỖNG — và một danh sách rỗng
    là thứ ngày 21/09 suýt bị đọc thành *"sổ tay bịa"*.
    """
    import re
    thieu_lop3 = re.sub(r"\s+", " ",
                        re.sub(r"[*`_~]", "", LOP23_TAI_LIEU)).strip()
    assert d.chuan_hoa(LOP23_SO_TAY) not in thieu_lop3, (
        "bo lop 3 ma van khop — mau nay khong con chung minh duoc gi")
    print("PASS  thiếu một lớp là đủ để một câu THẬT trả về rỗng")


def test_KHONG_duoc_bo_dau_tieng_Viet():
    """Chuẩn hoá quá tay thì hai câu KHÁC NGHĨA khớp nhau, và gác thành mù."""
    ban = {"x.md": d.chuan_hoa("vốn đỉnh đúng 100%")}
    assert d.tim("von dinh dung 100%", ban) == []
    assert d.chuan_hoa("BƯỚC 106 — đúng") == "BƯỚC 106 — đúng"
    print("PASS  dấu tiếng Việt giữ nguyên")


def test_CA_BIA_THAT_phai_LECH_va_phai_noi_ra_LECH_TU_DAU():
    """Ca bịa duy nhất trong 15, và phép đối chiếu phải chỉ được CHỖ rẽ.

    Một chữ "LỆCH" trần không dùng được: người đọc vẫn phải tự đi tìm xem
    nó bịa hẳn hay trích đúng một đoạn rồi chế thêm. `tien_to_dai_nhat`
    trả lời đúng câu đó.
    """
    ban = d.ban_da_chuan()
    ma, cau = d.phan_dinh(BIA, ban)
    assert ma == 1, cau
    n, ten = d.tien_to_dai_nhat(BIA, ban)
    assert 0 < n < len(d.chuan_hoa(BIA)), (
        f"tien to {n} — ca nay trich DUNG mot doan roi che them, "
        f"khong phai bia han")
    print(f"PASS  ca bịa: khớp {n} ký tự đầu ở {ten} rồi rẽ")


def test_CA_THAT_trong_TAI_LIEU_THAT_phai_KHOP():
    """Đối chứng dương trên quần thể THẬT — không có nó thì mọi 'LỆCH' vô nghĩa.

    Chạy trên chính `SKILL.md` đang ở trong repo: câu này vừa bị ngắt dòng
    vừa nằm trong blockquote vừa có `**`, tức đủ cả ba lớp trong một câu.
    """
    ma, cau = d.phan_dinh(LOP23_SO_TAY)
    assert ma == 0, cau
    print(f"PASS  đối chứng dương trên tài liệu thật — {cau}")


def test_BA_O_chu_khong_phai_HAI():
    """`CHƯA KIỂM ĐƯỢC` phải tách khỏi `LỆCH` — cùng quy ước năm cổng gác.

    Gộp hai ô ấy là đúng lỗi 66: một câu trả lời ÂM từ một mẫu không có
    khả năng cho câu dương thì nói về MẪU, không nói về giả thuyết.
    """
    ban = d.ban_da_chuan()
    assert d.phan_dinh("ngắn quá", ban)[0] == 2
    assert d.phan_dinh(LOP23_SO_TAY, {})[0] == 2
    assert d.phan_dinh(BIA, ban)[0] == 1
    assert d.phan_dinh(LOP23_SO_TAY, ban)[0] == 0
    print("PASS  ba ô: 0 khớp · 1 lệch · 2 chưa kiểm được")


def test_QUAN_THE_tai_lieu_deu_CO_THAT():
    """Một cái tên trỏ vào hư không làm quần thể co lại trong im lặng.

    Đây đúng hình dạng lỗi 73 và 80: gác không yếu, nó ngắm một quần thể
    hẹp hơn quần thể thật, và không gì kêu.
    """
    thieu = [str(f) for f in d.TAI_LIEU if not f.exists()]
    assert not thieu, f"tai lieu khai ma khong co that: {thieu}"
    assert len(d.ban_da_chuan()) == len(d.TAI_LIEU)
    print(f"PASS  {len(d.TAI_LIEU)} tài liệu đều có thật")


@pytest.mark.parametrize("cau", [
    "một câu hoàn toàn bịa đặt không nằm trong tài liệu nào của dự án này",
    "the quick brown fox jumps over the lazy dog and keeps running",
])
def test_CAU_KHONG_CO_THAT_thi_phai_LECH(cau):
    """Chiều ngược lại của mọi phép kiểm trên: nó có nói KHÔNG được không.

    Không có phép kiểm này thì một `chuan_hoa()` trả về chuỗi rỗng sẽ làm
    MỌI câu khớp, và cả file test vẫn xanh.
    """
    assert d.phan_dinh(cau)[0] == 1
    print("PASS  câu không có thật thì LỆCH")
