"""BƯỚC 191 — lỗi 177: máy quét lời khai phủ định phải thấy câu trải NHIỀU DÒNG
và câu nằm trong một ô ĐÃ MANG DẤU.

Ca thật: `NGUYEN-TAC-DO-LUONG.md`, ô ⚠️ của lượt soát 2 (18/09/2026), viết bản
báo cáo +636,11% *"không tìm thấy ở đâu"* — sai (tệp nằm ngoài repo, trong
`brain/` của Antigravity) và sống 26 ngày. `tools/soat_loi_khai_cu.py` không bao
giờ đưa nó ra: cụm phủ định ở dòng 207, tên tệp ở dòng 206, công cụ quét từng
dòng; cụm *"không tìm thấy"* không thuộc `PHU_DINH`; và dòng mang ⚠️ bị bỏ.
Đo 14/10/2026: chỉ khi vá cả ba thì ca ấy mới hiện ra.
"""
from __future__ import annotations

import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))

import soat_loi_khai_cu as s  # noqa: E402

#: Nguyên văn `NGUYEN-TAC-DO-LUONG.md` dòng 203–207 (không đổi từ 18/09/2026).
CA_177 = [
    "> ⚠️ **Thư mục ấy NAY KHÔNG CÒN — soát định kỳ 18/09/2026.** Vế phủ định",
    "> vẫn đúng và còn đúng mạnh hơn: `git log --all -- brain` trả về **rỗng**,",
    "> tức git chưa bao giờ theo dõi nó. Nhưng `brain/` cũng không còn ở gốc",
    "> repo, và bản báo cáo `20loop_custom71_18m_optimization_report.md` mà",
    "> đoạn trên dẫn thì không tìm thấy ở đâu.",
]


def _goc_gia(tmp_path: Path, ten: str, dong: list[str]) -> Path:
    p = tmp_path / ten
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(dong) + "\n", encoding="utf-8")
    return tmp_path


def _dong(ra, ten):
    return [(i, nd) for f, i, nd in ra if f == ten]


def test_CA_THAT_loi_177_nguyen_van_hien_ra(tmp_path):
    """Phát đầu tiên: dựng lại nguyên văn câu sai — nó phải có trong danh sách,
    ở dòng mang cụm phủ định (dòng 5 của đoạn), khoá là nguyên văn dòng ấy."""
    goc = _goc_gia(tmp_path, "NGUYEN-TAC-DO-LUONG.md", CA_177)
    ra = _dong(s.loi_khai_con_song(goc), "NGUYEN-TAC-DO-LUONG.md")
    assert (5, CA_177[4].strip()) in ra, ra


def test_CA_THAT_loi_177_tren_repo_THAT():
    """Trên quần thể thật, không trên đồ giả: câu sai vẫn đứng (chữ cũ giữ làm
    sử liệu, BƯỚC 190) nên máy phải đưa nó ra."""
    ra = [nd for f, _, nd in s.loi_khai_con_song()
          if f == "NGUYEN-TAC-DO-LUONG.md"]
    assert "> đoạn trên dẫn thì không tìm thấy ở đâu." in ra


def test_KHONG_TIM_THAY_la_phu_dinh():
    assert s.PHU_DINH.search("bản báo cáo thì không tìm thấy ở đâu")


def test_dong_MANG_DAU_khong_con_bi_bo(tmp_path):
    """Một dấu ⚠️ là lời khai MỚI của một lượt soát — nó sai được như mọi lời khai."""
    d = "⚠️ ĐÃ ĐO: `tools/x.py` không gọi `chay()` nữa."
    goc = _goc_gia(tmp_path, "CLAUDE.md", [d])
    assert (1, d) in _dong(s.loi_khai_con_song(goc), "CLAUDE.md")


def test_dong_MANG_DAU_o_BAN_LUU_cung_khong_bi_bo(tmp_path):
    """Bản lưu chỉ quét theo DÒNG, nên ở đó phép lọc dấu cũ là chỗ duy nhất có
    thể nuốt dòng (đục BƯỚC 191: ở tài liệu sống phép quét theo câu che nó)."""
    luu = s.TAI_LIEU_LUU[0]
    d = "🔴 HẾT ĐÚNG: `tools/x.py` không gọi `chay()` nữa."
    goc = _goc_gia(tmp_path, luu, [d])
    assert (1, d) in _dong(s.loi_khai_con_song(goc), luu)


def test_so_dong_la_dong_cua_CUM_PHU_DINH(tmp_path):
    """Tên ở dòng 1, cụm phủ định ở dòng 3: khoá là dòng 3, không phải đầu đoạn."""
    dong = ["Hàm `tinh_diem()` trong", "`tools/a.py` thì", "không ai gọi cả."]
    goc = _goc_gia(tmp_path, "CLAUDE.md", dong)
    assert _dong(s.loi_khai_con_song(goc), "CLAUDE.md") == [(3, "không ai gọi cả.")]


def test_HAI_CAU_rieng_khong_bi_ghep(tmp_path):
    dong = ["`tools/a.py` chạy tốt.", "Không ai gọi nó từ lâu."]
    goc = _goc_gia(tmp_path, "CLAUDE.md", dong)
    assert _dong(s.loi_khai_con_song(goc), "CLAUDE.md") == []


def test_DONG_TRONG_cua_blockquote_cat_doan(tmp_path):
    """`>` đứng một mình là ranh giới đoạn trong blockquote."""
    dong = ["> Tên `tools/a.py`", ">", "> không ai gọi."]
    goc = _goc_gia(tmp_path, "CLAUDE.md", dong)
    assert _dong(s.loi_khai_con_song(goc), "CLAUDE.md") == []


def test_RAO_MA_cat_doan_va_khong_quet_ben_trong(tmp_path):
    """Trong rào là MÃ: hai dòng lệnh không ghép thành một câu (đục BƯỚC 191:
    bản đầu dùng `# …` bên trong rào, và nhánh "tiêu đề" cắt thay nhánh rào)."""
    dong = ["Lệnh:", "```", "python `tools/a.py`", "echo không ai gọi", "```",
            "xong rồi chưa ai", "biết."]
    goc = _goc_gia(tmp_path, "CLAUDE.md", dong)
    assert _dong(s.loi_khai_con_song(goc), "CLAUDE.md") == []


def test_BANG_va_TIEU_DE_cat_doan(tmp_path):
    dong = ["| `tools/a.py` | x |", "không ai gọi.", "",
            "## `tools/b.py`", "không ai gọi."]
    goc = _goc_gia(tmp_path, "CLAUDE.md", dong)
    assert _dong(s.loi_khai_con_song(goc), "CLAUDE.md") == []


def test_BAN_LUU_chi_quet_theo_DONG(tmp_path):
    """Hai bản nguyên văn không bao giờ sửa: câu nhiều dòng ở đó không vào
    danh sách (đo 14/10: thêm 21 lời khai không ai sửa được). Cùng nội dung ở
    một tài liệu sống thì vào."""
    luu = s.TAI_LIEU_LUU[0]
    assert luu.startswith("docs/lich-su/")
    dong = ["Hàm `tinh_diem()`", "không ai gọi."]
    goc = _goc_gia(tmp_path, luu, dong)
    _goc_gia(tmp_path, "CLAUDE.md", dong)
    ra = s.loi_khai_con_song(goc)
    assert _dong(ra, luu) == []
    assert _dong(ra, "CLAUDE.md") == [(2, "không ai gọi.")]


def test_mot_dong_chi_vao_MOT_lan(tmp_path):
    """Dòng tự đủ hai vế VÀ nằm trong một câu nhiều dòng: không lặp."""
    dong = ["Trước đây", "`tools/a.py` không gọi `chay()` nữa."]
    goc = _goc_gia(tmp_path, "CLAUDE.md", dong)
    ra = _dong(s.loi_khai_con_song(goc), "CLAUDE.md")
    assert ra == [(2, dong[1])], ra


def test_BAN_IN_gan_nhan_CO_DAU(capsys):
    """`DA_CO_DAU` không còn lọc; nó gắn nhãn để người soát biết dòng nằm trong
    một ô đã đánh dấu. Quần thể thật có dòng như vậy (vd. 🔴 ở HANDOFF)."""
    assert any(any(x in nd for x in s.DA_CO_DAU)
               for _, _, nd in s.loi_khai_con_song())
    s.main([])
    assert "[có dấu] " in capsys.readouterr().out
