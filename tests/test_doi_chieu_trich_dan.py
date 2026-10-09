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


def test_QUAN_THE_doi_chieu_PHU_MOI_nguon_cua_so_tay():
    """Dụng cụ đối chiếu trích dẫn của SỔ TAY phải đọc mọi nguồn sổ tay đọc.

    `so_tay.NGUON_MAC_DINH` thêm `references/soat-cheo-notebooklm.md` ở BƯỚC
    130; `TAI_LIEU` ở đây thì không. Ngày 28/09/2026 (BƯỚC 137) sổ tay trích
    hai câu THẬT của file ấy, và dụng cụ báo cả hai là LỆCH — một phép tự kiểm
    vu oan, đúng chiều lỗi 88. Hai danh sách gõ tay của cùng một quần thể thì
    trôi khỏi nhau; gác này bắt chúng phải phủ nhau.
    """
    so_tay = pytest.importorskip("so_tay")
    duong = [f.as_posix() for f in d.TAI_LIEU]
    thieu = [n for n in so_tay.NGUON_MAC_DINH
             if not any(p.endswith("/" + n) for p in duong)]
    assert not thieu, f"nguon so tay ma dung cu doi chieu KHONG doc: {thieu}"


def test_CAU_THAT_cua_nguon_thu_MUOI_MOT_phai_KHOP():
    """Một câu CHỈ có ở nguồn thứ 11, ở mục luật bền (*Không làm*), lột dấu
    nhấn. Hai câu sổ tay trích hôm ấy thì chính BƯỚC 137 viết lại — neo gác
    vào chúng là neo vào thứ sắp biến mất."""
    ma, loi = d.phan_dinh(
        "Không mở Chrome, không dùng claude-in-chrome trừ khi người dùng nói "
        "thẳng.", d.ban_da_chuan())
    assert ma == 0 and "soat-cheo-notebooklm.md" in loi, loi


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


# ── BƯỚC 145: bản NGUYÊN VĂN trước khi rút gọn phải còn nằm trong quần thể ──

def test_QUAN_THE_phu_ca_hai_ban_LUU_TRU():
    """Hai câu dưới CHỈ còn ở bản lưu (đã rút khỏi `CLAUDE.md` / `SKILL.md`).

    Thiếu bản lưu trong `TAI_LIEU` thì trích dẫn từ lịch sử bị báo LỆCH — và
    đó đúng là lỗi 73/80: gác không yếu, nó ngắm quần thể hẹp hơn quần thể thật.
    Kiểm cả hai chiều: câu KHÔNG còn ở bản sống, VÀ được tìm ra ở bản lưu.
    """
    ban = d.ban_da_chuan()
    ca_claude = "tác dụng phụ không ai chọn"
    ca_skill = ("Cái gác không yếu — nó ngắm quần thể khác với quần thể công "
                "việc thật")
    assert d.tim(ca_claude, ban) == ["CLAUDE-md-2026-09-30.md"]
    assert d.tim(ca_skill, ban) == ["SKILL-md-2026-09-30.md"]
    assert d.phan_dinh(ca_claude, ban)[0] == 0
    assert d.phan_dinh(ca_skill, ban)[0] == 0


# ── BƯỚC 166: lộ trình và hàng đợi quyết định phải nằm trong quần thể ───────

CAU_A4_CUA_SO_TAY = "- **A4** — Tách docs/STATE.md theo tháng, giữ một mục lục."


def test_CAU_A4_THAT_cua_so_tay_phai_KHOP_LO_TRINH():
    """Lỗ đo được 09/10/2026: sổ tay trích đúng câu A4 của `docs/LO-TRINH.md`, mà dụng cụ
    đối chiếu báo LỆCH chỉ vì quần thể 13 tài liệu của nó không có tệp ấy."""
    ma, loi = d.phan_dinh(CAU_A4_CUA_SO_TAY, d.ban_da_chuan())
    assert ma == 0 and "LO-TRINH.md" in loi, loi


def test_CAU_A4_van_LECH_khi_quan_the_thieu_LO_TRINH_phat_dau_dung_nguyen_van_loi():
    """Dựng lại NGUYÊN VĂN lỗi: bỏ `LO-TRINH.md` khỏi quần thể thì câu thật bị vu là LỆCH."""
    thieu = [f for f in d.TAI_LIEU if f.name != "LO-TRINH.md"]
    assert len(thieu) == len(d.TAI_LIEU) - 1
    assert d.phan_dinh(CAU_A4_CUA_SO_TAY, d.ban_da_chuan(thieu))[0] == 1


def test_CAU_cua_QUYET_DINH_CHO_phai_KHOP():
    ma, loi = d.phan_dinh("Mục KHÔNG bị xoá; chỉ đổi trạng thái. Mã Q1…Qn liền nhau",
                          d.ban_da_chuan())
    assert ma == 0 and "QUYET-DINH-CHO.md" in loi, loi


def test_NGUON_so_tay_mac_dinh_co_LO_TRINH_va_QUYET_DINH_CHO():
    so_tay = pytest.importorskip("so_tay")
    assert {"LO-TRINH.md", "QUYET-DINH-CHO.md"} <= set(so_tay.NGUON_MAC_DINH)
