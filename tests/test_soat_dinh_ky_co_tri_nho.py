"""Một lượt SOÁT ĐỊNH KỲ phải để lại dấu vết trong chính bản in của công cụ.

VÌ SAO CÓ FILE NÀY
──────────────────
`tools/soat_loi_khai_cu.py` bản đầu kết bằng *"ghi kết quả lượt soát vào
`docs/soat-dinh-ky.json`"* rồi **không bao giờ đọc file ấy**. Một ống một
chiều: nó đòi một bản ghi mà chính nó không dùng được.

Đo 18/09/2026 — dựng lại cây 7 tài liệu của hai commit trong thư mục tạm
rồi gọi chính `loi_khai_con_song(goc)`:

    16/09 (441b2d4)   15 loi khai
    18/09 (4861040)   16 loi khai
    ra khoi danh sach : 0 dong

Lượt soát 16/09 phán xử hai dòng và đánh dấu một dòng **đúng quy ước dự
án** — giữ câu gốc, thêm ô ⚠️ NGAY DƯỚI — trong khi `DA_CO_DAU` đọc TỪNG
DÒNG. Phạm vi phép lọc hẹp hơn đơn vị của quy ước: cùng họ lỗi 73 và 80.

BA ĐIỀU GÁC NÀY CANH, và chỉ ba
───────────────────────────────
1. `xep()` **không được bỏ dòng nào** — chiều hỏng nguy hiểm là giấu một
   lời khai còn sống, không phải hiện thừa một dòng đã soát.
2. `da_soat()` khoá bằng **nguyên văn dòng**, không bằng số dòng. Hai mục
   lượt 16/09 đã trôi 1706→1873 và 1740→1907 chỉ trong hai ngày.
3. Cơ chế có **người dùng thật**: hai dòng ấy phải hiện ra là đã soát
   trong lượt chạy trên repo THẬT, không phải trên đồ giả.

NÓ KHÔNG canh gì
────────────────
Nó **không** kiểm `dong` có trỏ vào một dòng đang sống hay không. Một câu
được sửa chữ sau lượt soát là việc ĐÚNG và thường xuyên, nên phép kiểm ấy
sinh đỏ giả. Và chiều hỏng của một `dong` ghi sai là chiều AN TOÀN: dòng
ấy hiện như chưa ai mở, tức được mở lại. Công cụ **nói ra** những `dong`
không còn khớp (`so_tro_vao_hu_khong`) — thông tin, không phải cổng.

Nó cũng **không** kiểm phán quyết có trung thực không. Một gác canh chính
lời khai của người khai là một gác rỗng — lỗi 81.
"""
import json
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
SO_DINH_KY = GOC / "docs" / "soat-dinh-ky.json"

sys.path.insert(0, str(GOC / "tools"))

from soat_loi_khai_cu import (  # noqa: E402
    da_soat, loi_khai_con_song, so_tro_vao_hu_khong, xep,
)


def _so() -> dict:
    return json.loads(SO_DINH_KY.read_text(encoding="utf-8"))


# ── 1. chiều hỏng nguy hiểm: giấu một lời khai còn sống ─────────────────

def test_XEP_khong_duoc_BO_dong_nao():
    """Xoá dòng đã soát khỏi danh sách là dựng lại đúng cái im lặng mà nhịp
    soát sinh ra để phá. Một câu phán "THẬT, vẫn đúng" hôm nay vẫn cũ được
    ngày mai."""
    ra = [("a.md", 1, "cau mot"), ("a.md", 9, "cau hai"), ("b.md", 3, "ba")]
    bang = {"cau hai": ("2026-09-16", "THẬT — vẫn đúng")}
    assert len(xep(ra, bang)) == len(ra)
    assert {x[2] for x in xep(ra, bang)} == {n for _, _, n in ra}


def test_XEP_dua_CHUA_AI_MO_len_truoc():
    ra = [("a.md", 1, "da soat"), ("a.md", 2, "chua ai mo")]
    bang = {"da soat": ("2026-09-16", "THẬT")}
    kq = xep(ra, bang)
    assert [x[2] for x in kq] == ["chua ai mo", "da soat"]
    assert kq[0][3] is None and kq[1][3] == ("2026-09-16", "THẬT")


def test_XEP_giu_nguyen_thu_tu_trong_tung_nhom():
    ra = [("a.md", 1, "m1"), ("a.md", 2, "d1"), ("a.md", 3, "m2"),
          ("a.md", 4, "d2")]
    bang = {"d1": ("2026-09-16", "THẬT"), "d2": ("2026-09-16", "SAI")}
    assert [x[2] for x in xep(ra, bang)] == ["m1", "m2", "d1", "d2"]


# ── 2. khoá là NGUYÊN VĂN DÒNG, không phải số dòng ──────────────────────

def test_DA_SOAT_khoa_bang_NGUYEN_VAN_DONG_khong_phai_SO_DONG():
    """Dựng lại đúng ca thật: cùng một câu, số dòng đã trôi.

    Sổ ghi lời khai lúc nó ở dòng 1706; hôm nay nó ở dòng 1873. Khoá bằng
    số dòng thì bảng tra không khớp gì cả — và lượt soát 16/09 biến mất.
    """
    cau = "**Chưa đo:** `tv_recommendation` KHÔNG tái lập"
    so = {"lan_soat": [{"ngay": "2026-09-16", "phat_hien": [
        {"dong": cau, "phan_quyet": "SAI — lời khai vẫn ĐÚNG"}]}]}
    bang = da_soat(so)
    assert cau in bang, "khoa phai la nguyen van dong"
    assert not any(isinstance(k, int) or k.isdigit() for k in bang)
    ra = [("CLAUDE.md", 1706, cau), ("CLAUDE.md", 1873, cau)]
    assert all(x[3] is not None for x in xep(ra, bang)), (
        "so dong doi ma cau khong doi thi phan quyet cu VAN phai theo")


def test_DA_SOAT_cau_DOI_CHU_thi_hien_lai_nhu_chua_ai_mo():
    """Hành vi ĐÚNG, không phải thiếu sót: câu đã khác thì phán quyết cũ
    không còn nói về nó nữa."""
    so = {"lan_soat": [{"ngay": "2026-09-16", "phat_hien": [
        {"dong": "cau goc", "phan_quyet": "THẬT"}]}]}
    assert xep([("a.md", 1, "cau goc da sua")], da_soat(so))[0][3] is None


# ── 3. chiều hỏng AN TOÀN ───────────────────────────────────────────────

def test_DA_SOAT_bo_qua_phat_hien_THIEU_DONG():
    """Thiếu `dong` → dòng hiện như chưa ai mở → lượt sau mở lại nó.

    Chiều nguy hiểm là ngược lại — đánh dấu "đã soát" cho dòng chưa ai
    soát — và khoá nguyên văn không tạo ra được chiều ấy.
    """
    so = {"lan_soat": [{"ngay": "2026-09-18", "phat_hien": [
        {"noi_dung": "co mo, nhung khong ghi dong", "phan_quyet": "THẬT"},
        {"dong": "   ", "phan_quyet": "THẬT"}]}]}
    assert da_soat(so) == {}


def test_DA_SOAT_luot_GAN_NHAT_thang():
    so = {"lan_soat": [
        {"ngay": "2026-09-18", "phat_hien": [{"dong": "x", "phan_quyet": "SAI"}]},
        {"ngay": "2026-09-16", "phat_hien": [{"dong": "x", "phan_quyet": "THẬT"}]}]}
    assert da_soat(so)["x"] == ("2026-09-18", "SAI")


def test_SO_TRO_VAO_HU_KHONG_goi_ten_dong_khong_con_khop():
    bang = {"con song": ("2026-09-16", "THẬT"), "da mat": ("2026-09-16", "SAI")}
    assert so_tro_vao_hu_khong(bang, [("a.md", 1, "con song")]) == ["da mat"]


# ── 4. cơ chế có NGƯỜI DÙNG THẬT, đo trên repo thật ─────────────────────

def test_HAI_DONG_luot_16_09_hien_ra_la_DA_SOAT_tren_repo_THAT():
    """Đo trên quần thể thật, không trên đồ giả.

    Đây là phép kiểm duy nhất trong file này chạy trên repo. Không có nó,
    cả bốn nhóm trên vẫn xanh trong khi `docs/soat-dinh-ky.json` không có
    lấy một khoá `dong` nào — tức cơ chế không có người dùng, và một cơ chế
    không ai dùng thì không có cách nào biết nó hỏng.
    """
    bang = da_soat(_so())
    assert bang, "so khong co lay mot khoa `dong` nao — co che khong ai dung"
    ra = loi_khai_con_song()
    kem = xep(ra, bang)
    da = [x for x in kem if x[3] is not None]
    assert da, "khong dong song nao duoc danh dau — khoa `dong` khong khop gi"
    assert len(da) < len(ra), (
        "moi dong deu 'da soat' — danh sach mat het nghia tien do")
    for f, _, _, dau in da:
        assert dau[0] and dau[1], f"{f}: thieu ngay hoac phan quyet"


def test_MOI_KHOA_DONG_trong_so_la_chuoi_khong_rong():
    for luot in _so()["lan_soat"]:
        for i, pd in enumerate(luot.get("phat_hien", [])):
            if "dong" not in pd:
                continue
            d = pd["dong"]
            dau = f"{luot['ngay']}[{i}]"
            assert isinstance(d, str) and d.strip(), f"{dau}: `dong` rong"
            assert d == d.strip(), f"{dau}: `dong` con khoang trang hai dau"
