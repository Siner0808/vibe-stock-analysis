"""Bảng lỗi phải ĐỌC ĐƯỢC THÀNH SỐ, và con số tổng của nó phải do lệnh sinh.

VÌ SAO CÓ FILE NÀY
──────────────────
Bảng lỗi hỏi *"máy chặn được không"* và **không** hỏi hai điều quyết
định: lỗi thuộc **LỚP** nào, và nó **SỐNG BAO LÂU** trước khi bị bắt.

Thiếu hai thứ đó thì câu hỏi *"quy trình có khoẻ lên không"* phải dựng
lại phân tích từ đầu mỗi lần — đúng lỗi **"không có lệnh thì không có
số"**, lần này áp lên chính bảng lỗi.

Và lượt chạy đầu tiên của `tools/doc_bang_loi.py` bắt ngay **lỗi 35**:
dòng tự khai cuối bảng lệch **+1 suốt ba ngày**, vì nó được **cộng dồn**
thay vì **đếm lại**.

HAI CHIỀU, LUÔN LUÔN (bài học lỗi 34)
─────────────────────────────────────
Công cụ này là mã mới, nên mọi phép phán của nó được thử bằng **cả đầu
vào phải-qua lẫn đầu vào phải-chặn**, không chỉ chạy lên file thật. Một
gác chỉ thấy dữ liệu sạch là một gác chưa được thử.
"""
import json
import subprocess
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(GOC / "tools"))

import doc_bang_loi as dbl  # noqa: E402

PY = sys.executable


# ───────────────── phép phán tự chứng minh, HAI CHIỀU ─────────────────

def test_MAY_DO_doc_so_viet_bang_CHU_tieng_Viet():
    """Không đọc được chữ thì không đối chiếu được dòng tự khai.

    `mốt`, `tư`, `lăm` có mặt vì tiếng Việt đổi dạng đơn vị sau hàng
    chục — hai mươi **mốt**, ba mươi **tư**, hai mươi **lăm**. Bỏ sót
    chúng thì phép kiểm im đúng lúc con số đang trôi.
    """
    DUNG = {
        "không": 0, "bảy": 7, "mười": 10, "mười ba": 13, "mười lăm": 15,
        "mười chín": 19, "hai mươi": 20, "hai mươi mốt": 21,
        "hai mươi hai": 22, "hai mươi tư": 24, "hai mươi lăm": 25,
        "ba mươi mốt": 31, "ba mươi tư": 34, "ba mươi lăm": 35,
    }
    for chu, so in DUNG.items():
        assert dbl.so_tu_chu(chu) == so, f"{chu!r} phải ra {so}"

    # KHONG doc duoc thi phai tra None, dung im lang tra mot so sai
    for chu in ("", "linh tinh", "mươi", "hai mươi bảy tám chín", "ba mươi xyz"):
        assert dbl.so_tu_chu(chu) is None, f"{chu!r} phải trả None"
    print(f"PASS  đọc đúng {len(DUNG)} dạng số chữ, trả None cho 5 dạng hỏng")


def test_MAY_DO_tach_cot_TON_TRONG_dau_ong_da_thoat():
    """Lượt chạy đầu của công cụ ra 19/34 thay vì 21/34 vì đúng chỗ này.

    Hai dòng của bảng viết `` `pytest \\| tail` `` với dấu ống ĐÃ THOÁT.
    Tách thô bằng `split("|")` cắt nhầm giữa ô mô tả và đẩy MỌI cột sau
    sang một bậc — nên cột "máy chặn?" bị đọc thành cột khác.

    Lỗi 30 ở một chỗ mới: đọc SỰ XUẤT HIỆN của `|` thay vì vai trò NGĂN
    CỘT của nó.
    """
    # nguyen van hinh dang da cat nham
    cot = dbl.tach_cot(r" 7 | `pytest \| tail` chạy nền | tự nhận ra muộn | ✅ | x ")
    assert cot[3] == "✅", f"cột 'máy chặn?' đọc sai: {cot}"
    assert r"pytest | tail" in cot[1], f"dấu ống thoát bị mất: {cot}"

    # dong binh thuong van dung
    cot = dbl.tach_cot(" 1 | mô tả | bắt bởi | ⚠️ một phần | cách chặn ")
    assert cot[3] == "⚠️ một phần", cot
    print("PASS  tách cột tôn trọng `\\|`, không đẩy lệch cột nào")


def test_MAY_DO_quyet_dinh_ba_trang_thai_va_di_qua_MA_THOAT():
    """Đục thử 11/09/2026: gỡ phép đối chiếu khỏi `main()` mà mọi phép
    kiểm vẫn XANH — chúng gọi thẳng `doc_dong_khai()`, không đi qua mã
    thoát. Một phép kiểm không đi qua đường người dùng thật đi là mù.

    Nên phần phán được tách thành hàm thuần, và thử ở CẢ BA trạng thái.
    """
    assert dbl.quyet_dinh(21, 34, (21, 34))[0] == 0, "khớp phải trả 0"
    assert dbl.quyet_dinh(21, 34, (22, 34))[0] == 1, "lệch số chặn phải trả 1"
    assert dbl.quyet_dinh(21, 34, (21, 35))[0] == 1, "lệch tổng phải trả 1"
    assert dbl.quyet_dinh(21, 34, None)[0] == 2, "không đọc được phải trả 2"

    # thong bao phai NOI RA hai con so, khong chi noi "lech"
    _, tin = dbl.quyet_dinh(21, 34, (22, 34))
    assert "22/34" in tin and "21/34" in tin, f"thông báo thiếu số: {tin!r}"
    print("PASS  quyết định ba trạng thái · thông báo nêu cả hai con số")


def test_MAY_DO_doi_chieu_bat_duoc_THIEU_va_THUA():
    """Phân lớp phải phủ đúng tập dòng bảng — không thiếu, không thừa."""
    bang = {"1": {}, "2": {}, "3": {}}
    assert dbl.doi_chieu(bang, {"loi": {"1": {}, "2": {}, "3": {}}}) == ([], [])
    assert dbl.doi_chieu(bang, {"loi": {"1": {}, "2": {}}}) == (["3"], [])
    assert dbl.doi_chieu(bang, {"loi": {"1": {}, "2": {}, "3": {}, "9": {}}}) \
        == ([], ["9"])
    print("PASS  đối chiếu bắt được cả THIẾU lẫn THỪA")


# ───────────────────── áp lên dữ liệu THẬT ─────────────────────

def test_moi_dong_bang_deu_co_PHAN_LOP_hop_le():
    bang = dbl.doc_bang()
    pl = dbl.doc_phan_lop()
    thieu, thua = dbl.doi_chieu(bang, pl)
    assert not thieu, (
        f"{len(thieu)} lỗi trong bảng chưa có phân lớp: {thieu}\n"
        f"Thêm vào `docs/loi-phan-lop.json`.")
    assert not thua, f"phân lớp thừa, không có dòng bảng nào: {thua}"

    lop_hop_le = set(pl["_lop"])
    nguon_hop_le = set(pl["_nguon_tuoi"])
    for so, v in pl["loi"].items():
        assert v["lop"] in lop_hop_le, f"lỗi {so}: lớp {v['lop']!r} lạ"
        assert v["nguon"] in nguon_hop_le, f"lỗi {so}: nguồn {v['nguon']!r} lạ"
        if v["nguon"] == "chua-do":
            assert v["song_ngay"] is None, (
                f"lỗi {so}: nguồn 'chua-do' mà vẫn có con số tuổi thọ — "
                f"đó là đoán, không phải đo")
        else:
            assert isinstance(v["song_ngay"], int) and v["song_ngay"] >= 0, (
                f"lỗi {so}: tuổi thọ phải là số ngày ≥ 0 hoặc khai 'chua-do'")
    print(f"PASS  {len(bang)} dòng · phân lớp đủ, lớp và nguồn đều hợp lệ")


def test_DONG_TU_KHAI_cuoi_bang_khop_so_DEM_DUOC():
    """Lỗi 35: con số ấy từng được CỘNG DỒN thay vì ĐẾM LẠI, lệch 3 ngày."""
    bang = dbl.doc_bang()
    chan = sum(1 for v in bang.values() if v["may_chan"].startswith("✅"))
    khai = dbl.doc_dong_khai()
    assert khai is not None, (
        "không đọc được dòng tự khai ở cuối bảng — nó phải có dạng "
        "'**<chữ> trên <chữ> máy chặn được**'")
    assert khai == (chan, len(bang)), (
        f"bảng TỰ KHAI {khai[0]}/{khai[1]} nhưng ĐẾM ĐƯỢC "
        f"{chan}/{len(bang)}.\nĐừng cộng dồn — chạy "
        f"`tools/doc_bang_loi.py` rồi chép con số nó in ra.")
    print(f"PASS  dòng tự khai {khai[0]}/{khai[1]} khớp số đếm được")


def test_cong_cu_CHAY_DUOC_va_thoat_0():
    """Một công cụ không chạy được cũng là một cổng xanh giả."""
    r = subprocess.run([PY, str(GOC / "tools" / "doc_bang_loi.py")],
                       capture_output=True, text=True, encoding="utf-8",
                       cwd=str(GOC))
    assert r.returncode == 0, f"mã thoát {r.returncode}\n{r.stderr}"
    for phai_co in ("LỚP", "TUỔI THỌ", "NGUỒN", "MÁY CHẶN ĐƯỢC"):
        assert phai_co in r.stdout, f"thiếu mục {phai_co!r} trong báo cáo"
    print("PASS  công cụ chạy được, thoát 0, in đủ bốn mục")


def test_JSON_phan_lop_doc_duoc_va_co_GIAI_THICH_tung_lop():
    """Một mã lớp không có lời giải thích là một nhãn, không phải một lớp."""
    pl = json.loads((GOC / "docs" / "loi-phan-lop.json")
                    .read_text(encoding="utf-8"))
    assert pl["_lop"], "thiếu bảng giải thích lớp"
    for ten, mo_ta in pl["_lop"].items():
        assert len(mo_ta) > 40, f"lớp {ten!r} giải thích quá ngắn để dùng"
    for ten, mo_ta in pl["_nguon_tuoi"].items():
        assert len(mo_ta) > 15, f"nguồn {ten!r} giải thích quá ngắn"
    print(f"PASS  {len(pl['_lop'])} lớp · {len(pl['_nguon_tuoi'])} nguồn, "
          f"mỗi cái đều có giải thích")
