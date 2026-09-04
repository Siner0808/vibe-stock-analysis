"""Gác: hằng số của cổng an toàn đổi thì TÀI LIỆU phải đổi theo.

Ngày 04/09/2026 tìm ra `CLAUDE.md` chứa **hai điều kiện dừng khác nhau**,
cả hai đều tự giới thiệu là hiện hành:

    dòng 478   ">=60 lệnh ... cận trên KTC của KỲ VỌNG < 0"   <- BẢN 1
    dòng 935   "596 lệnh cho 80% lực phát hiện ở -0,927%"     <- BẢN 2, số CŨ
    mã thật    N_TOI_THIEU=113 · N_DAY_DU=451 · MUC_BAT_LOI=-0,920

`7644b8e` (01/09) neo lại hai hằng số và ĐÃ ghi đúng ở `docs/STATE.md`
BƯỚC 10 — chỉ `CLAUDE.md` không được cập nhật. Nó sống được năm ngày vì
**không gác nào đối chiếu con số trong tài liệu với hằng số trong mã**.

QUY ƯỚC CỦA GÁC NÀY
───────────────────
Nó KHÔNG cấm số cũ có mặt. Dự án cố ý giữ số cũ kèm ghi chú, và xoá chúng
là xoá lịch sử đo lường. Nó chỉ đòi **giá trị HIỆN TẠI phải có mặt**.

Hệ quả đúng như mong muốn: đổi một hằng số trong mã mà không đụng tài liệu
thì giá trị mới không có trong tài liệu → đỏ. Giữ số cũ bên cạnh thì vẫn
xanh.

Cùng hình dạng với `tests/test_lich_cron_chuong.py`, nơi chú thích phải
khớp cron của chính file đó — và cũng là loại gác VĂN BẢN hợp lệ, vì thứ
được canh ở đây đúng là văn bản.

GIỚI HẠN — NÊU RA, KHÔNG GIẢ VỜ MẠNH HƠN THỰC TẾ
────────────────────────────────────────────────
Hợp đồng là: **giá trị hiện tại phải xuất hiện ở ÍT NHẤT MỘT chỗ có gọi
tên hằng số.** Không phải "mọi chỗ đều đúng".

Đòi mọi chỗ đúng thì mâu thuẫn với chính quy ước của dự án: bảng
`| N_DAY_DU | 596 | **451** |` cố ý để số cũ nằm ngay cạnh tên. Một gác
cấm điều đó sẽ ép người ta xoá lịch sử đo lường.

Hệ quả phải biết: nếu tài liệu nói về cùng một hằng số ở HAI chỗ và chỉ
một chỗ được cập nhật, gác này **vẫn xanh**. Đột biến trả bảng về 596
sống sót đúng vì lý do đó — đã thử, đã ghi lại, và đó là đánh đổi có chủ
đích chứ không phải sơ sót.

Thứ nó bắt chắc chắn: **đổi hằng số trong mã mà không đụng tài liệu.**
Đó là đúng lỗi đã xảy ra ngày 01/09 và sống tới 04/09.
"""
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import paper_metrics as pm  # noqa: E402

TAI_LIEU = GOC / "CLAUDE.md"

#: Số ký tự tối thiểu của tài liệu. Một file rỗng làm mọi phép `in` sai
#: theo hướng ĐỎ nên không nguy hiểm, nhưng một file đọc hụt thì có —
#: và một máy quét không nói ra nó đọc được bao nhiêu là máy quét có thể
#: đang đọc 0 byte.
SAN_KY_TU = 20_000


def _cach_viet(ten: str, gia_tri) -> list[str]:
    """Các cách con số này có thể được viết trong văn bản tiếng Việt.

    Dấu thập phân là DẤU PHẨY, và một số thực có thể viết 2 hoặc 3 chữ số
    sau dấu. Dấu âm bị bỏ qua có chủ đích: `−0,920` và `-0,920` và
    `0,920%` đều là cùng một con số đang được nói tới, còn việc phân biệt
    ba ký tự gạch ngang khác nhau của Unicode thì chỉ tạo ra đỏ giả.
    """
    if isinstance(gia_tri, int) or float(gia_tri).is_integer():
        return [str(int(gia_tri))]
    v = abs(float(gia_tri))
    return [f"{v:.{n}f}".replace(".", ",") for n in (2, 3, 4)]


#: Hằng số điều khiển CỔNG C5 — thứ quyết định khi nào dừng mở lệnh mới.
#: Đây là lý do bộ gác này tồn tại: một con số sai ở đây không phải lỗi
#: chữ nghĩa, nó là một quy tắc an toàn sai.
HANG_SO = ("N_DAY_DU", "N_TOI_THIEU", "MUC_BAT_LOI")


def _doc() -> str:
    src = TAI_LIEU.read_text(encoding="utf-8")
    assert len(src) >= SAN_KY_TU, (
        f"{TAI_LIEU.name} chỉ đọc được {len(src)} ký tự (sàn {SAN_KY_TU}) "
        f"— gác này đang canh một file rỗng hoặc đọc hụt")
    return src


#: Bao nhiêu ký tự quanh TÊN hằng số thì còn tính là "nói về nó".
#:
#: Hỏi "con số này có ở đâu đó trong file không" là câu hỏi QUÁ YẾU với
#: một tài liệu 60 KB: đột biến trả bảng `N_DAY_DU` về 596 vẫn XANH, vì
#: số 451 còn nằm trong một khối mã ở mục khác. Phải hỏi kề TÊN.
BAN_KINH = 400


def _co_gia_tri_ke_ten(src: str, ten: str, cach: list[str]) -> bool:
    """Có chỗ nào nhắc `ten` mà con số đúng nằm trong bán kính không."""
    i = src.find(ten)
    while i != -1:
        quanh = src[max(0, i - BAN_KINH): i + BAN_KINH]
        if any(c in quanh for c in cach):
            return True
        i = src.find(ten, i + 1)
    return False


@pytest.mark.parametrize("ten", HANG_SO)
def test_gia_tri_HIEN_TAI_phai_co_KE_TEN_hang_so(ten):
    """Đổi hằng số trong mã mà không đụng tài liệu → đỏ.

    "Kề tên" chứ không phải "có mặt đâu đó" — xem `BAN_KINH`.
    """
    gia_tri = getattr(pm, ten)
    src = _doc()
    assert ten in src, (
        f"{TAI_LIEU.name} không nhắc `{ten}` lần nào — nếu hằng số này đã "
        f"hết vai trò thì gỡ khỏi HANG_SO CÓ CHỦ ĐÍCH, kèm lý do")
    cach = _cach_viet(ten, gia_tri)
    assert _co_gia_tri_ke_ten(src, ten, cach), (
        f"`paper_metrics.{ten}` = {gia_tri} nhưng {TAI_LIEU.name} không "
        f"viết con số đó ở CHỖ NÀO nhắc tên hằng số (đã thử: {cach}, "
        f"bán kính {BAN_KINH} ký tự). Đây là hằng số của CỔNG C5. Cập "
        f"nhật tài liệu — và theo quy ước dự án thì ĐÁNH DẤU tại chỗ, "
        f"đừng xoá số cũ.")


def test_HANG_SO_va_SAN_KY_TU_khong_duoc_thu_hep_am_tham():
    """Hai cách vô hiệu hoá gác này mà không sửa một dòng logic nào.

    Rút `HANG_SO` xuống còn một tên thì hai hằng số kia mất gác; hạ
    `SAN_KY_TU` xuống 0 thì gác chấp nhận đọc một file rỗng. Cùng hình
    dạng với `SAN_SO_FILE = 0` sống sót đột biến ngày 03/09/2026.
    """
    assert set(HANG_SO) == {"N_DAY_DU", "N_TOI_THIEU", "MUC_BAT_LOI"}, (
        "bộ hằng số của cổng C5 đã đổi — sửa danh sách này CÓ CHỦ ĐÍCH, "
        "kèm lý do, chứ đừng rút gọn cho test xanh")
    assert SAN_KY_TU == 20_000
    assert BAN_KINH == 400

def test_khong_con_dieu_kien_dung_BAN_1_ma_khong_danh_dau():
    """Bản 1 đo KỲ VỌNG với ngưỡng gõ tay 60; bản 2 đo ALPHA.

    Bản 1 được giữ lại có chủ đích để đối chiếu, nhưng nó PHẢI đi kèm dấu
    hiệu cho biết đã bị thay. Không có dấu ấy thì người đọc gặp hai quy
    tắc an toàn mâu thuẫn và không biết theo cái nào — đúng tình trạng
    ngày 04/09/2026.
    """
    src = _doc()
    if "≥60 lệnh tiến-về-trước" not in src:
        pytest.skip("đoạn bản 1 đã được gỡ hẳn — không còn gì để canh")
    i = src.index("≥60 lệnh tiến-về-trước")
    sau = src[i:i + 1600]
    assert "BẢN 1" in sau, (
        "CLAUDE.md vẫn nêu điều kiện dừng '≥60 lệnh / kỳ vọng' mà không "
        "có dấu hiệu nào cho biết đó là BẢN 1 đã bị thay từ 29/08/2026. "
        "Cùng file mô tả bản 2 ở chỗ khác — hai quy tắc an toàn cùng tự "
        "giới thiệu là hiện hành.")


def test_MAY_DO_tu_chung_minh_no_bat_duoc():
    """Không có test này thì gác trên xanh cả khi nó không kiểm gì.

    Mã thật hiện KHỚP tài liệu, nên một máy dò hỏng trả về đúng cùng câu
    trả lời với một máy dò tốt — đúng đột biến đã sống sót ngày
    03/09/2026 và 04/09/2026. Cách duy nhất tách hai trường hợp là bắt nó
    làm việc trên một giá trị đã biết là KHÔNG có trong tài liệu.
    """
    src = _doc()

    # ĐI QUA `_co_gia_tri_ke_ten`, không đi vòng qua nó. Bản đầu của test
    # này dùng `any(c in src ...)` trực tiếp, nên đột biến biến hàm dò
    # thành `return True` VẪN XANH — lần thứ ba trong một ngày mắc đúng
    # kiểu ấy.
    assert not _co_gia_tri_ke_ten(src, "N_DAY_DU",
                                  _cach_viet("BIA", 987654321)), (
        "máy dò báo N_DAY_DU kề một con số bịa — nó đang trả True cho mọi "
        "thứ, tức không kiểm gì cả")
    assert not _co_gia_tri_ke_ten(src, "TEN_HANG_SO_KHONG_TON_TAI",
                                  _cach_viet("x", pm.N_DAY_DU)), (
        "máy dò tìm thấy một tên hằng số không tồn tại trong tài liệu")
    assert _co_gia_tri_ke_ten(src, "N_DAY_DU",
                              _cach_viet("N_DAY_DU", pm.N_DAY_DU)), (
        "máy dò không thấy cả trường hợp ĐANG ĐÚNG — nó đang hỏng")


def test_cach_viet_hieu_dung_dau_phay_thap_phan():
    """Số thực tiếng Việt dùng DẤU PHẨY. Hiểu sai là đỏ giả hàng loạt."""
    assert "0,92" in _cach_viet("x", -0.92)
    assert "0,920" in _cach_viet("x", -0.92)
    assert _cach_viet("x", 451) == ["451"]
    assert _cach_viet("x", 451.0) == ["451"]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print("Chạy bằng: pytest tests/test_tai_lieu_khop_hang_so.py -q")
