"""Gác cho `lich_giao_dich.py` — lịch phiên công bố trước.

Module này tồn tại để trả lời MỘT câu mà mọi dụng cụ cũ không trả lời
được: nguồn dữ liệu đứng, hay thị trường nghỉ? Nên bộ gác ở đây phải canh
đúng hai thứ, và thứ hai quan trọng hơn thứ nhất:

1. bảng lịch KHỚP dữ liệu thật (nếu không thì mọi phán quyết đều sai);
2. khi bảng KHÔNG phát biểu được thì module nói "chưa biết", chứ không nói
   "ổn". Một cái chuông hết hạn mà báo ổn sẽ biến việc quên cập nhật lịch
   thành nhiều tháng im lặng — đúng kiểu hỏng mà module này sinh ra để
   chấm dứt.
"""
import ast
import datetime as dt
from pathlib import Path

import pytest

import lich_giao_dich as lg

GOC = Path(__file__).resolve().parents[1]


# ── 1. Bảng phải khớp phép đo, không phải khớp bài báo ────────────────

def test_bang_tai_lap_dung_162_phien_da_do():
    """Số phiên bảng dự kiến phải bằng số phiên ĐO ĐƯỢC trên chuỗi thật.

    Đo 02/09/2026 bằng `fetch_one("VNINDEX", "2026-01-01", "2026-09-02")`:
    162 phiên, từ 2026-01-05 tới 2026-08-28, lệch 0 ở CẢ HAI chiều.

    Con số 162 ghim ở đây vì bản chép từ bài báo lần đầu SAI — nó ghi
    02/01/2026 có phiên, cho ra 163. Không có phép đối chiếu này thì bảng
    sai vẫn trông hợp lý hoàn toàn, và cái chuông dựng trên nó sẽ kêu oan
    đúng một ngày mỗi năm.

    ĐẾM TỪ ĐẦU PHẠM VI, KHÔNG TỪ PHIÊN ĐẦU TIÊN. Bản đầu của test này đếm
    `cac_phien("2026-01-04", ...)`; quy ước nửa mở làm cửa sổ bắt đầu ở
    05/01, tức NẰM SAU cả 01/01 lẫn 02/01. Đột biến bỏ 02/01 khỏi bảng —
    tái tạo đúng lỗi đã mắc thật — vẫn cho 162 và test vẫn xanh. Một gác
    ghim đúng con số mà không phủ đúng chỗ dễ sai nhất thì không gác gì cả.
    """
    n = dt.date.fromisoformat(lg.PHU_TU)
    het = dt.date(2026, 8, 28)
    dem = 0
    while n <= het:
        dem += 1 if lg.co_phien(n.isoformat()) else 0
        n += dt.timedelta(days=1)
    assert dem == 162, f"bảng dự kiến {dem} phiên, đo được 162"


def test_phien_dau_tien_cua_nam_la_05_01_khong_phai_02_01():
    """Ghim riêng hai ngày mà cửa sổ đếm ở trên không thể phủ.

    Sở nghỉ cả 01/01 (thứ Năm) và 02/01 (thứ Sáu, hoán đổi sang thứ Bảy
    10/01), giao dịch lại 05/01. Chuỗi VN-INDEX thật bắt đầu đúng ở đó.
    """
    assert lg.co_phien("2026-01-01") is False
    assert lg.co_phien("2026-01-02") is False
    assert lg.co_phien("2026-01-05") is True
    dau = [d for d in lg.cac_phien("2026-01-01", "2026-01-31")][0]
    assert dau == "2026-01-05", dau


def test_moi_ngay_nghi_deu_la_ngay_TRONG_TUAN():
    """Thứ Bảy/Chủ nhật trong `NGAY_NGHI` là dòng thừa đội lốt luật.

    Cuối tuần đã bị `co_phien` loại trước đó. Thêm 22/08 (ngày làm bù, thứ
    Bảy) vào bảng không đổi hành vi nào cả, nhưng người đọc sau sẽ tưởng
    danh sách này là "mọi ngày không giao dịch" và đi tìm những thứ Bảy
    còn thiếu.
    """
    xau = [d for d in lg.NGAY_NGHI
           if dt.date.fromisoformat(d).weekday() >= 5]
    assert not xau, f"ngày cuối tuần nằm trong NGAY_NGHI: {sorted(xau)}"


def test_moi_ngay_nghi_nam_trong_pham_vi_khai_bao():
    ngoai = [d for d in lg.NGAY_NGHI if not (lg.PHU_TU <= d <= lg.PHU_TOI)]
    assert not ngoai, f"ngày nghỉ ngoài [{lg.PHU_TU}; {lg.PHU_TOI}]: {ngoai}"


# ── 2. Ngoài phạm vi phải là "chưa biết", KHÔNG phải "ổn" ─────────────

@pytest.mark.parametrize("ngay", ["2025-12-31", "2027-01-04", "2030-06-11"])
def test_co_phien_tra_None_ngoai_pham_vi(ngay):
    """Không đoán, kể cả khi đoán rất dễ.

    2027-01-04 là thứ Hai giữa mùa, gần chắc có phiên. Trả True cho nó là
    biến bảng công bố thành phỏng đoán — và thứ phỏng đoán bỏ sót đúng là
    ngày nghỉ lễ, tức đúng thứ bảng sinh ra để biết.
    """
    assert lg.co_phien(ngay) is None


def test_chan_doan_HET_HAN_bao_chua_biet_chu_khong_bao_on():
    tt, td = lg.chan_doan("2027-03-01", "2027-03-10")
    assert tt == lg.CHUA_BIET, tt
    assert tt != lg.OK
    assert "CHƯA BIẾT" in td


def test_chan_doan_moc_ngoai_pham_vi_du_nen_trong_pham_vi():
    """Một vế ngoài phạm vi là đủ để không kết luận được."""
    tt, _ = lg.chan_doan("2026-12-30", "2027-01-05")
    assert tt == lg.CHUA_BIET


# ── 3. Đúng tình huống THẬT ngày 02/09/2026 ───────────────────────────

def test_ky_nghi_quoc_khanh_KHONG_bi_bao_la_nguon_dung():
    """Ca đã sinh ra module này. Nến 28/08, hôm nay 02/09 — trễ 3 NGÀY
    LÀM VIỆC nhưng 0 PHIÊN, vì 31/08–02/09 đều nghỉ Quốc khánh.

    Đây là phép thử phân biệt: bộ đếm ngày làm việc cũ báo 3, lịch công bố
    báo 0. Nếu test này đỏ thì cái chuông sẽ kêu suốt mọi kỳ nghỉ lễ, và
    một cái chuông kêu oan mỗi kỳ nghỉ sẽ bị tắt trước khi nó kịp bắt một
    lần hỏng thật.
    """
    tt, td = lg.chan_doan("2026-08-28", "2026-09-02")
    assert tt == lg.OK, td
    assert lg.so_phien_giua("2026-08-28", "2026-09-02") == 0


def test_phien_dau_tien_mo_lai_sau_le_chi_tre_1_phien():
    """Sáng 03/09, trước khi nến hôm đó về: trễ đúng 1 phiên, không phải 4."""
    assert lg.so_phien_giua("2026-08-28", "2026-09-03") == 1
    assert lg.chan_doan("2026-08-28", "2026-09-03")[0] == lg.OK


def test_tet_nguyen_dan_chin_ngay_cung_khong_bao_dong():
    tt, _ = lg.chan_doan("2026-02-13", "2026-02-22")
    assert tt == lg.OK


# ── 4. Nguồn đứng THẬT thì phải kêu ───────────────────────────────────

def test_nguon_dung_giua_mua_thi_KEU():
    """Tháng Sáu, không lễ lạt gì: nến đứng ở 01/06 mà đã tới 05/06."""
    tt, td = lg.chan_doan("2026-06-01", "2026-06-05")
    assert tt == lg.NGUON_DUNG, td
    assert "2026-06-02" in td and "2026-06-04" in td


def test_nguong_dung_o_bien_1_va_2_phien():
    """1 phiên là bình thường (nến hôm nay chưa đóng); 2 phiên là thiếu."""
    assert lg.so_phien_giua("2026-06-01", "2026-06-02") == 1
    assert lg.chan_doan("2026-06-01", "2026-06-02")[0] == lg.OK
    assert lg.so_phien_giua("2026-06-01", "2026-06-03") == 2
    assert lg.chan_doan("2026-06-01", "2026-06-03")[0] == lg.NGUON_DUNG


def test_cuoi_tuan_khong_lam_chuong_keu():
    """Nến thứ Sáu, hôm nay Chủ nhật — 0 phiên trôi qua."""
    assert lg.so_phien_giua("2026-06-05", "2026-06-07") == 0
    assert lg.chan_doan("2026-06-05", "2026-06-07")[0] == lg.OK


# ── 5. Chiều ngược: dữ liệu canh BẢNG ─────────────────────────────────

def test_co_nen_vao_ngay_bang_goi_la_NGHI_thi_bao_BANG_SAI():
    """Nếu Sở mở cửa mà bảng nói nghỉ, lỗi nằm ở bảng.

    Không được lặng lẽ đi tiếp: mọi phán quyết khác của module dựa trên
    bảng, nên bảng sai thì chúng vô giá trị. Đây là lý do `BANG_SAI` là
    một trạng thái riêng chứ không phải một dòng cảnh báo.
    """
    tt, td = lg.chan_doan("2026-09-01", "2026-09-03")
    assert tt == lg.BANG_SAI, tt
    assert "Bảng" in td or "bảng" in td


def test_PHIEN_CUOI_TUAN_lat_duoc_quy_tac_cuoi_tuan(monkeypatch):
    """Ngoại lệ ngược có đường khai, và đường đó THẬT SỰ chạy."""
    assert lg.co_phien("2026-06-06") is False          # thứ Bảy
    monkeypatch.setattr(lg, "PHIEN_CUOI_TUAN", frozenset({"2026-06-06"}))
    assert lg.co_phien("2026-06-06") is True


# ── 6. Gác HÌNH DẠNG, không gác giá trị ───────────────────────────────

def test_chan_doan_SO_SANH_voi_hang_so_nguong():
    """`TRE_BAO_DONG_PHIEN` phải được so trong thân `chan_doan`.

    Kiểm bằng AST chứ không bằng giá trị: một đột biến thay hằng số bằng
    số 2 gõ thẳng cho ra ĐÚNG mọi kết quả hôm nay, và chỉ sai vào ngày ai
    đó chỉnh ngưỡng rồi tưởng mình đã chỉnh. Bài học ba lần mắc ngày
    31/08/2026 — xem CLAUDE.md, mục "Test KIỂM LẠI CHÍNH NÓ".
    """
    cay = ast.parse((GOC / "lich_giao_dich.py").read_text(encoding="utf-8"))
    ham = [n for n in ast.walk(cay)
           if isinstance(n, ast.FunctionDef) and n.name == "chan_doan"]
    assert len(ham) == 1
    ten = {n.id for n in ast.walk(ham[0]) if isinstance(n, ast.Name)}
    assert "TRE_BAO_DONG_PHIEN" in ten, (
        "chan_doan không đọc TRE_BAO_DONG_PHIEN — ngưỡng đã bị gõ thẳng")
    ss = [n for n in ast.walk(ham[0]) if isinstance(n, ast.Compare)]
    assert any(
        isinstance(n.left, ast.Name) and n.left.id == "tre"
        and any(isinstance(c, ast.Name) and c.id == "TRE_BAO_DONG_PHIEN"
                for c in n.comparators)
        for n in ss), "không thấy phép so `tre` với TRE_BAO_DONG_PHIEN"


def test_chan_doan_KHONG_bao_gio_tra_OK_khi_ngoai_pham_vi():
    """Bất biến diễn đạt trực tiếp, quét cả năm 2027.

    Kiểm bằng cách CHẠY hàm trên nhiều mốc chứ không đọc mã: nhánh
    `CHUA_BIET` có thể bị dời xuống dưới phép so ngưỡng và vẫn còn nguyên
    trong file.
    """
    n = dt.date(2027, 1, 1)
    while n < dt.date(2028, 1, 1):
        tt, _ = lg.chan_doan(n.isoformat(), (n + dt.timedelta(days=9)).isoformat())
        assert tt == lg.CHUA_BIET, f"{n} cho {tt}"
        n += dt.timedelta(days=17)


# ── 7. Quy ước nửa mở phải KHỚP market_filter ─────────────────────────

def test_quy_uoc_nua_mo_khop_market_filter():
    """`(sau, toi]` — lệch quy ước với `_tre_phien` là lệch đúng một phiên.

    Hai module đếm cùng một đại lượng ở hai chỗ khác nhau; nếu một bên
    tính cả ngày đầu còn bên kia không, mọi ngưỡng hiệu chuẩn trên bên này
    sẽ lệch một đơn vị khi đọc bằng bên kia.
    """
    import market_filter as mf
    lich = lg.cac_phien("2026-05-31", "2026-06-30")
    assert lg.so_phien_giua("2026-06-01", "2026-06-05") == \
        mf._tre_phien("2026-06-01", "2026-06-05", lich=lich)
    assert lg.so_phien_giua("2026-08-28", "2026-09-02") == \
        mf._tre_phien("2026-08-28", "2026-09-02",
                      lich=lg.cac_phien("2026-08-01", "2026-09-30"))


# ── 8. Chuông đọc lịch: tools/chuong_nguon_dung.py ────────────────────

def _nap_chuong():
    import importlib.util as ilu
    spec = ilu.spec_from_file_location(
        "chuong_nguon_dung_ban_sao", GOC / "tools" / "chuong_nguon_dung.py")
    mod = ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_chuong_KEU_khi_lich_HET_HAN():
    """Lịch hết hạn phải làm đỏ, không được coi là yên.

    Đây là chỗ dễ sai nhất của mọi cái chuông đọc bảng: bảng hết hạn thì
    `chan_doan` trả `CHUA_BIET`, và cách xử lý "tự nhiên" là chỉ kêu khi
    thấy `NGUON_DUNG`. Làm thế thì ngày lịch 2026 hết hiệu lực, chuông sẽ
    im lặng suốt cả năm 2027 trong khi trông vẫn xanh mỗi ngày.
    """
    ch = _nap_chuong()
    assert ch.ma_thoat(lg.CHUA_BIET) == 1
    assert lg.CHUA_BIET in ch.TRANG_THAI_KEU


def test_chuong_phan_loai_DU_moi_trang_thai():
    """Thêm một trạng thái mới mà quên xếp loại thì test đỏ.

    Sổ đăng ký, cùng kiểu với `tests/test_hang_rao_quy_trinh.py`: mọi hằng
    số trạng thái trong `lich_giao_dich` phải hoặc nằm trong danh sách kêu,
    hoặc là `OK`. Không có ô thứ ba để một trạng thái mới rơi vào im lặng.
    """
    ch = _nap_chuong()
    moi = {v for k, v in vars(lg).items()
           if k.isupper() and isinstance(v, str) and v == k}
    assert moi == {lg.OK, lg.NGUON_DUNG, lg.BANG_SAI, lg.CHUA_BIET}, moi
    chua_xep = moi - set(ch.TRANG_THAI_KEU) - {lg.OK}
    assert not chua_xep, f"trạng thái chưa xếp loại: {chua_xep}"
    assert ch.ma_thoat(lg.OK) == 0
    for t in (lg.NGUON_DUNG, lg.BANG_SAI, lg.CHUA_BIET):
        assert ch.ma_thoat(t) == 1, t


def test_chuong_keo_tu_MANG_chu_khong_doc_CACHE():
    """`fetch_one`, KHÔNG `get_vni_df` — và kiểm bằng AST.

    `get_vni_df()` ưu tiên cache trên đĩa. Với backtest đó là đúng (phải
    tất định), nhưng ở đây cache CHÍNH LÀ thứ có thể đang che mất việc
    nguồn đã chết: đo 02/09/2026, cache ở máy dừng ở 20/08 trong khi mạng
    có tới 28/08. Một cái chuông đọc bản sao thì nó canh bản sao.

    Đọc cây cú pháp chứ không `in`: tên `get_vni_df` có mặt trong khối chú
    thích của chính file đó, nên phép kiểm văn bản sẽ nói ngược.
    """
    ch = _nap_chuong()
    cay = ast.parse((GOC / "tools" / "chuong_nguon_dung.py")
                    .read_text(encoding="utf-8"))
    goi = {n.func.attr for n in ast.walk(cay)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert "fetch_one" in goi, "chuông không gọi fetch_one"
    assert "get_vni_df" not in goi, (
        "chuông đang đọc cache qua get_vni_df — nó sẽ canh bản sao")
    assert hasattr(ch, "nen_moi_nhat_tu_mang")
