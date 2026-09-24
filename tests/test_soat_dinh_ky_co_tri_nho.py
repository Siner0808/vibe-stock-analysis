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

import soat_loi_khai_cu as s  # noqa: E402
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
#: ─────────────────────────────────────────────────────────────────────
#: MỘT TÊN HÀM `ten()` VẪN LÀ MỘT CÁI TÊN — đo 21/09/2026
#:
#: Phép lọc tự khai là *"lời khai phủ định CÓ NÊU TÊN"*, lý do khai kèm:
#: *"có cái tên thì có chỗ để chạy `grep`"*. Nhưng `CO_TEN` bản đầu không
#: nhận dấu ngoặc, nên `` `_doc()` `` KHÔNG tính là tên — trong khi dự án
#: viết tên hàm đúng kiểu ấy suốt.


def test_TEN_HAM_co_ngoac_VAN_la_ten():
    """Ca thật: `CLAUDE.md` dòng 621, và nó bị bỏ sót suốt 9 ngày.

    Câu ở đó là *"Bản trước trỏ tới một hàm `_doc()` **chưa bao giờ tồn
    tại** trong module này"* — một lời khai phủ định, có nêu tên, chưa
    đánh dấu. Đúng thứ công cụ sinh ra để in. Nó không in, vì `()`.
    """
    assert s.CO_TEN.search("một hàm `_doc()` chưa bao giờ tồn tại")
    assert s.CO_TEN.search("`vnstock_goi.kiem_goi()` phải có ba ô")
    assert s.CO_TEN.search("`paper_metrics.py` chưa ai đọc")   # dạng cũ vẫn chạy
    print("PASS  tên hàm có () vẫn là tên")


def test_CO_TEN_khong_duoc_NHAN_MOI_THU():
    """Chiều ngược lại. Nới một phép lọc là dễ; nới thành vô dụng cũng dễ.

    Lời khai của phép lọc là *"có cái tên thì có chỗ chạy `grep`"* — nên
    một câu KHÔNG có tên phải tiếp tục rơi ra ngoài, nếu không danh sách
    quay lại con số 187 mà ba phép lọc sinh ra để siết.
    """
    assert not s.CO_TEN.search("chuyện ấy trước hôm nay không được ghi ở đâu")
    assert not s.CO_TEN.search("`` rỗng thì không phải tên")
    print("PASS  câu không có tên vẫn rơi ra ngoài")


def test_CONG_CU_phai_TU_NOI_PHAM_VI_cua_no():
    """Một phạm vi chỉ nằm trong docstring là một phạm vi không ai đọc.

    Ngày 21/09/2026 tôi đo được *"công cụ chỉ thấy 1 trên 14 câu lớp
    chưa-ai-ghi"* và suýt dựng cả một lớp gác mới trên con số ấy. Đọc lại
    mã: **12 trong 13 câu lọt qua nằm trong `docs/STATE.md`, thứ công cụ
    CỐ Ý không quét** — và lý do ấy đã viết sẵn ở dòng 40 của chính file.

    Con số ấy không sai; nó chỉ nói về một quần thể khác quần thể tôi
    tưởng. Cùng họ lỗi 73 · 80 · 88. Nên phạm vi phải đi theo BẢN IN, chỗ
    người đọc con số đang nhìn — đúng bài học lỗi 78.
    """
    import io
    import contextlib

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        s.main([])
    dong = buf.getvalue().splitlines()

    # NEO VÀO ĐẦU DÒNG, đừng tìm chữ trong cả bản in: hai chuỗi này CŨNG
    # nằm trong chính quần thể công cụ quét (`CLAUDE.md` có một mục tên
    # "PHẠM VI, đo 15/09/2026"), nên `in ra` xanh cả khi dòng khai đã bị
    # gỡ. Đục thử 21/09/2026 để sống đúng hai phát vì lỗi ấy — lỗi 38.
    dau = [i for i, d in enumerate(dong) if d.startswith("PHẠM VI:")]
    assert len(dau) == 1, (
        f"phai co DUNG MOT dong mo dau bang 'PHẠM VI:', dem duoc {len(dau)}")
    khoi = "\n".join(dong[dau[0]:dau[0] + 3])
    assert "STATE.md" in khoi, "dòng khai phạm vi không gọi tên thứ bị bỏ qua"
    assert "nhật ký" in khoi, "dòng khai phạm vi không nói VÌ SAO bỏ qua"
    print("PASS  công cụ tự nói phạm vi, và nói cả lý do")


def test_PHAM_VI_in_ra_phai_KHOP_voi_ma():
    """Lời khai *"không quét STATE.md"* phải đúng với `TAI_LIEU` thật.

    Gác hình DẠNG, không gác chữ: nếu ai đó thêm `docs/STATE.md` vào danh
    sách thì bản in thành một lời khai sai, và đó đúng là hình dạng
    tài-liệu-lệch-mã mà dự án trả giá nhiều nhất.
    """
    assert not any("STATE.md" in t for t in s.TAI_LIEU), (
        "TAI_LIEU nay CO STATE.md — ban in dang khai nguoc lai")
    print(f"PASS  {len(s.TAI_LIEU)} tài liệu, không có STATE.md, khớp bản in")


def test_HO_KHONG_NHAP_GOI_DUNG_CHAM_la_loi_khai_phu_dinh():
    """Ca THẬT, lượt soát 5 (24/09/2026): `docs/HANDOFF.md` mục 5, nguyên văn
    như nó đứng ở `7a774a2` — trần, chưa dấu. Nó sai từ 22/09 (ĐO 14 nhập
    `vnstock_data`), và công cụ không in nó vì *"không nhập"* nằm ngoài
    danh sách phủ định. Phát đục đầu tiên phải dựng lại đúng ca ấy."""
    that = ("  `~/.vnstock/api_key.json` và `vnii` tự đọc. Repo **không nhập")
    assert s.PHU_DINH.search(that) and s.CO_TEN.search(that)
    for cau in ("`fill_pending` không gọi `_analyze`",
                "loại biểu đồ dự án **không dùng** `mapbox`",
                "`_compute_local_indicators` — hàm thuần, không chạm mạng"):
        assert s.PHU_DINH.search(cau), cau
    print("PASS  ho khong nhap/goi/dung/cham duoc nhan la phu dinh")


def test_HO_MOI_khong_duoc_NHAN_TU_DA_DO_LA_NHIEU():
    """Chiều ngược lại, neo bằng phép đo lượt 5: ba từ này kéo vào 23 dòng,
    phần lớn là luật và văn xuôi. Ai thêm chúng thì phải đo lại, không lặng lẽ."""
    for cau in ("gác phải đọc AST, không đọc `in`",
                "`paper_trading.py` không có, luôn bật",
                "ô thoát `khong_soat_vi` không còn được nhận"):
        assert not s.PHU_DINH.search(cau), cau
    print("PASS  khong doc / khong co / khong con van nam ngoai")
