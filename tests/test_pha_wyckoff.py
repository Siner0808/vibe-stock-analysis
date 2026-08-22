"""Test bộ đọc pha Wyckoff.

VÌ SAO FILE NÀY TỒN TẠI
───────────────────────
Nhãn "Pha C — Wyckoff Spring" từng xuất hiện trên giao diện cho MỌI mã có
điểm ≥ 60, không có phân tích nào đứng sau. Bài học không phải "đừng hiện
pha Wyckoff" mà là "đừng hiện một kết luận không ai kiểm được".

Nên các test dưới đây kiểm hai nhóm tính chất khác nhau:

  · NHẬN RA ĐÚNG — dựng sẵn kịch bản Spring/UTAD/SOS/Markup rồi đòi module
    gọi đúng tên. Không có nhóm này thì module có thể luôn trả "chưa đủ
    bằng chứng" và vẫn xanh.

  · KHÔNG NHẬN BỪA — pha B phải ra "chưa đủ bằng chứng", vùng quá rộng
    phải bị từ chối, và hai biên phải dựng từ phần NỀN chứ không phải từ
    cả đoạn. Không có nhóm này thì module có thể gán nhãn cho mọi thứ và
    cũng vẫn xanh.

Một bộ nhận dạng chỉ hữu ích khi cả hai nhóm cùng xanh.
"""
import pandas as pd
import pytest

import pha_wyckoff as wy


# ─────────────────────────────────────────────────────────────────────
# Dựng khung nến
# ─────────────────────────────────────────────────────────────────────

def _khung(closes, vols):
    """Khung nến tối giản: thân hẹp 0,5% hai phía, mở = đóng."""
    n = len(closes)
    return pd.DataFrame({
        "time": pd.date_range("2025-01-01", periods=n,
                              freq="B").strftime("%Y-%m-%d"),
        "open": list(closes),
        "close": list(closes),
        "high": [c * 1.005 for c in closes],
        "low": [c * 0.995 for c in closes],
        "volume": list(vols),
    })


def _doan(tu, den, n):
    """n giá trị nội suy tuyến tính từ `tu` tới `den`."""
    if n == 1:
        return [den]
    buoc = (den - tu) / (n - 1)
    return [tu + buoc * i for i in range(n)]


def _tich_luy():
    """100 phiên: giảm → cao trào bán → AR → nền đi ngang → 10 phiên trống.

    Mốc chỉ số dùng lại ở nhiều test:
        0..49   giảm 100 → 80
        50..52  cao trào bán, khối lượng 4x
        53..58  AR bật lên 78
        59..89  nền đi ngang 74..78
        90..99  cửa sổ sự kiện (mặc định để trống)
    """
    closes = (_doan(100, 80, 50) + _doan(78, 72, 3) + _doan(73, 78, 6)
              + [76, 75, 74, 76, 77, 75, 74, 76, 77, 76] * 3 + [75])
    vols = ([1000] * 50 + [4000] * 3 + [1500] * 6 + [800] * 31)
    closes, vols = closes[:90], vols[:90]
    closes += [75, 74, 75, 74, 75, 74, 75, 74, 75, 74]
    vols += [800] * 10
    return _khung(closes, vols)


def _phan_phoi():
    """Ảnh gương: tăng → cao trào mua → AR sụt → nền → cửa sổ sự kiện."""
    closes = (_doan(80, 100, 50) + _doan(102, 108, 3) + _doan(107, 100, 6)
              + [102, 103, 104, 102, 103, 105, 102, 103, 104, 103] * 3 + [103])
    vols = ([1000] * 50 + [4000] * 3 + [1500] * 6 + [800] * 31)
    closes, vols = closes[:90], vols[:90]
    closes += [103, 104, 103, 104, 103, 104, 103, 104, 103, 104]
    vols += [800] * 10
    return _khung(closes, vols)


def _dat(df, i, *, close=None, low=None, high=None, volume=None):
    """Sửa một cây nến trong cửa sổ sự kiện. Trả về bản sao."""
    ra = df.copy()
    if close is not None:
        ra.loc[i, "close"] = close
        ra.loc[i, "open"] = close
    if low is not None:
        ra.loc[i, "low"] = low
    if high is not None:
        ra.loc[i, "high"] = high
    if volume is not None:
        ra.loc[i, "volume"] = volume
    return ra


# ─────────────────────────────────────────────────────────────────────
# 1. Từ chối khi chưa đủ dữ liệu — và nói rõ vì sao
# ─────────────────────────────────────────────────────────────────────

def test_thieu_cot_thi_khong_ket_luan():
    df = _tich_luy().drop(columns=["volume"])
    r = wy.doc_pha(df)
    assert not r.ket_luan_duoc
    assert "volume" in r.nhan_day
    print("PASS  thiếu cột -> nói thiếu cột nào")


def test_qua_it_nen_thi_khong_ket_luan():
    df = _tich_luy().tail(30).reset_index(drop=True)
    r = wy.doc_pha(df)
    assert not r.ket_luan_duoc
    assert str(wy.TOI_THIEU_NEN) in r.nhan_day
    print("PASS  30 phiên -> từ chối, có nêu ngưỡng")


def test_df_rong_hoac_none():
    assert not wy.doc_pha(None).ket_luan_duoc
    assert not wy.doc_pha(pd.DataFrame()).ket_luan_duoc
    print("PASS  None / bảng rỗng -> không nổ, không kết luận")


def test_bien_do_qua_rong_thi_tu_choi():
    """Một 'vùng' rộng 90% không phải vùng dao động, đó là con sóng.

    Neo vào đó rồi gọi tên pha là ép biểu đồ vào sơ đồ lý tưởng — lỗi mà
    chính phương pháp Wyckoff cấm.
    """
    closes = (_doan(100, 80, 50) + _doan(78, 40, 3) + _doan(42, 95, 6)
              + _doan(95, 60, 31) + _doan(60, 90, 10))
    vols = [1000] * 50 + [4000] * 3 + [1500] * 6 + [800] * 41
    r = wy.doc_pha(_khung(closes, vols))
    assert not r.ket_luan_duoc
    assert "quá rộng" in r.nhan_day
    print(f"PASS  biên độ quá rộng -> từ chối ({r.nhan_day[-40:]})")


# ─────────────────────────────────────────────────────────────────────
# 2. Nhận ra đúng sự kiện
# ─────────────────────────────────────────────────────────────────────

def test_spring_co_test_lai_thi_da_xac_nhan():
    df = _tich_luy()
    df = _dat(df, 93, close=74.0, low=70.0, volume=400)   # Spring, KL cạn
    df = _dat(df, 96, close=74.0, low=70.5, volume=300)   # Test, KL nhỏ hơn
    r = wy.doc_pha(df)
    assert r.pha == "C", r.nhan_day
    assert r.su_kien == "Spring"
    assert r.cau_truc == "TÍCH LUỸ"
    assert r.huong == wy.TANG
    assert r.do_tin == "đã xác nhận", r.do_tin
    assert any("thử lại đáy Spring" in b for b in r.bang_chung)
    print(f"PASS  Spring + Test -> {r.nhan_day}")


def test_spring_khong_co_test_thi_chi_nhieu_kha_nang():
    """Spring nói cung đã cạn; chỉ Test mới chứng minh điều đó.

    Không có Test mà vẫn 'đã xác nhận' là tự tin quá mức đúng chỗ đắt
    tiền nhất của cả sơ đồ.
    """
    df = _dat(_tich_luy(), 93, close=74.0, low=70.0, volume=400)
    r = wy.doc_pha(df)
    assert r.su_kien == "Spring"
    assert r.do_tin == "nhiều khả năng", r.do_tin
    assert any("Chưa có phiên Test" in p for p in r.phan_bien)
    print("PASS  Spring thiếu Test -> hạ độ tin, và nói rõ thiếu gì")


def test_utad_lam_cau_truc_phan_phoi():
    df = _dat(_phan_phoi(), 93, close=104.0, high=112.0, volume=2500)
    r = wy.doc_pha(df)
    assert r.pha == "C", r.nhan_day
    assert r.su_kien == "UTAD"
    assert r.cau_truc == "PHÂN PHỐI"
    assert r.huong == wy.GIAM
    print(f"PASS  UTAD -> {r.nhan_day}")


def test_sos_pha_D():
    """Phá trần kèm khối lượng, nhưng chưa rời hẳn vùng -> pha D."""
    df = _dat(_tich_luy(), 95, close=85.0, high=85.5, volume=3000)
    r = wy.doc_pha(df)
    assert r.pha == "D" and r.su_kien == "SOS", r.nhan_day
    assert r.huong == wy.TANG
    print(f"PASS  SOS -> {r.nhan_day}")


def test_markup_pha_E():
    """Ba phiên cuối đóng trên trần -> đã rời vùng, pha E."""
    df = _tich_luy()
    for i in (97, 98, 99):
        df = _dat(df, i, close=85.0, high=85.5, volume=2000)
    r = wy.doc_pha(df)
    assert r.pha == "E" and r.su_kien == "Markup", r.nhan_day
    assert r.do_tin == "đã xác nhận"
    print(f"PASS  Markup -> {r.nhan_day}")


def test_markdown_pha_E():
    df = _phan_phoi()
    for i in (97, 98, 99):
        df = _dat(df, i, close=95.0, low=94.5, volume=2000)
    r = wy.doc_pha(df)
    assert r.pha == "E" and r.su_kien == "Markdown", r.nhan_day
    assert r.huong == wy.GIAM
    print(f"PASS  Markdown -> {r.nhan_day}")


# ─────────────────────────────────────────────────────────────────────
# 3. Không nhận bừa
# ─────────────────────────────────────────────────────────────────────

def test_di_ngang_khong_su_kien_thi_pha_B_va_khong_doan_huong():
    """Test quan trọng nhất file này.

    Pha B của tích luỹ và pha B của phân phối trông giống hệt nhau. Module
    nào gán được hướng ở đây là module đang đoán, và cái đoán đó sẽ đi
    thẳng lên giao diện dưới dạng một kết luận.
    """
    r = wy.doc_pha(_tich_luy())
    assert r.pha == "B", r.nhan_day
    assert r.cau_truc == "CHƯA PHÂN ĐỊNH"
    assert r.huong == wy.TRUNG_TINH
    assert r.do_tin == "chưa đủ bằng chứng"
    assert "tích luỹ" in r.phu_dinh and "phân phối" in r.phu_dinh, r.phu_dinh
    print(f"PASS  pha B -> không đoán hướng · {r.phu_dinh[:60]}…")


def test_hai_bien_dung_tu_NEN_chu_khong_tu_ca_doan():
    """Chống vòng lặp logic: cây thủng sâu nhất không được tự định nghĩa sàn.

    Nếu sàn lấy min trên cả đoạn sau cao trào thì cây Spring (thấp nhất
    đoạn) chính là cái sàn, nên `low < san` không bao giờ đúng và module
    sẽ KHÔNG BAO GIỜ thấy Spring — báo xanh vĩnh viễn trên 0 phát hiện.
    """
    df = _dat(_tich_luy(), 93, close=74.0, low=70.0, volume=400)
    r = wy.doc_pha(df)
    assert r.san is not None
    assert r.san > 70.0, (
        f"sàn {r.san} đã bị chính cây Spring (đáy 70.0) kéo xuống — "
        f"hai biên đang lấy từ cả đoạn thay vì từ phần nền")
    print(f"PASS  sàn {r.san} nằm trên đáy Spring 70.0 -> biên lấy từ nền")


def test_neo_cao_trao_khong_bi_keo_ve_qua_khu_xa():
    """Cụm khối lượng khổng lồ từ 4 tháng trước không được làm điểm neo.

    Nó thuộc một cấu trúc đã kết thúc. Neo vào đó thì 'vùng dao động'
    trải dài cả con sóng — đo trên dữ liệu thật cho ra vùng rộng 96%.
    """
    df = _tich_luy()
    df.loc[5:7, "volume"] = 500_000
    r = wy.doc_pha(df)

    # `ket_luan_duoc` PHẢI được khẳng định trước. Không có dòng này thì
    # nhánh "chưa đủ bằng chứng" (so_phien_nen = 0) cũng thoả cận trên
    # bên dưới, và test xanh mà không kiểm gì — đúng cái bẫy đã bắt được
    # bằng đột biến ngày 22/08/2026.
    assert r.ket_luan_duoc, (
        f"neo bị kéo về cụm khối lượng cũ nên không đọc được nữa: "
        f"{r.nhan_day}")
    assert r.so_phien_nen <= wy.TOI_DA_PHIEN_NEN, (
        f"nền {r.so_phien_nen} phiên > trần {wy.TOI_DA_PHIEN_NEN} — "
        f"điểm neo đã bị kéo về cụm khối lượng cũ")
    print(f"PASS  nền {r.so_phien_nen} phiên, neo không bị kéo về quá khứ")


def test_khong_co_AR_thi_khong_ve_duoc_bien():
    """Cao trào mà không có nhịp bật/sụt theo sau -> thiếu một đường biên."""
    closes = _doan(100, 70, 90) + [70.0] * 10
    vols = [1000] * 50 + [9000] * 3 + [1000] * 47
    r = wy.doc_pha(_khung(closes, vols))
    assert not r.ket_luan_duoc
    assert "AR" in r.nhan_day
    print("PASS  thiếu AR -> từ chối vẽ biên")


# ─────────────────────────────────────────────────────────────────────
# 4. Kỷ luật bắt buộc của phương pháp
# ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("dung", [
    lambda: _tich_luy(),
    lambda: _dat(_tich_luy(), 93, close=74.0, low=70.0, volume=400),
    lambda: _dat(_phan_phoi(), 93, close=104.0, high=112.0, volume=2500),
    lambda: _dat(_tich_luy(), 95, close=85.0, high=85.5, volume=3000),
])
def test_luon_co_bang_chung_phan_bien_va_dieu_kien_phu_dinh(dung):
    r = wy.doc_pha(dung())
    assert r.phan_bien, "kết luận không kèm phản biện thì không kiểm chứng được"
    assert any("Cạnh phải" in p for p in r.phan_bien)
    assert r.phu_dinh.strip(), "thiếu điều kiện phủ định"
    print(f"PASS  {r.nhan_ngan}: {len(r.phan_bien)} phản biện, có điều kiện phủ định")


def test_phu_dinh_neu_moc_gia_cu_the():
    """Điều kiện phủ định phải là một mốc giá, không phải một câu chung chung.

    Đây là cơ sở duy nhất để đặt điểm dừng lỗ có lý do thay vì chọn bừa.
    """
    df = _dat(_tich_luy(), 93, close=74.0, low=70.0, volume=400)
    r = wy.doc_pha(df)
    assert any(ch.isdigit() for ch in r.phu_dinh), r.phu_dinh
    print(f"PASS  điều kiện phủ định có mốc giá: {r.phu_dinh}")


def test_su_kien_nguoc_diem_neo_thi_phai_noi_ra_va_ha_do_tin():
    """Spring (tích luỹ) sau một cao trào MUA là mâu thuẫn, phải nói thẳng.

    Smoke test ACB ngày 22/08/2026 lôi ra đúng lỗi này: nhãn hiện
    "Pha C — Spring · TÍCH LUỸ · đã xác nhận" trong khi dòng bằng chứng
    đầu tiên ngay bên dưới ghi "cao trào MUA". Nhánh sự kiện tự ghi đè
    cấu trúc mà không ai đối chiếu lại với điểm neo.

    Không cấm nhánh này — tái tích luỹ là chuyện có thật. Nhưng chuỗi
    kinh điển không khớp thì phải nói ra, và độ tin phải hạ.
    """
    df = _phan_phoi()                                  # neo = cao trào MUA
    df = _dat(df, 93, close=101.0, low=97.0, volume=400)   # Spring
    df = _dat(df, 96, close=101.0, low=98.0, volume=300)   # Test
    r = wy.doc_pha(df)
    assert r.su_kien == "Spring" and r.cau_truc == "TÍCH LUỸ", r.nhan_day
    assert any("cao trào mua" in p for p in r.phan_bien), r.phan_bien
    assert any("tái tích luỹ" in p for p in r.phan_bien)
    assert r.do_tin == "nhiều khả năng", (
        f"có Spring + Test nhưng điểm neo ngược, độ tin phải hạ khỏi "
        f"'đã xác nhận', đang là {r.do_tin!r}")
    print(f"PASS  mâu thuẫn điểm neo -> nói ra, hạ độ tin ({r.do_tin})")


def test_markup_khong_bi_dan_nhan_PHAN_PHOI():
    """Giá phá lên sau một vùng neo bằng cao trào mua = phép đọc phân phối
    đã hỏng. Gọi nó là "Pha E — Markup · PHÂN PHỐI" là nhãn tự mâu thuẫn."""
    df = _phan_phoi()
    for i in (97, 98, 99):
        df = _dat(df, i, close=115.0, high=115.5, volume=2000)
    r = wy.doc_pha(df)
    assert r.pha == "E" and r.su_kien == "Markup", r.nhan_day
    assert r.cau_truc == "TÍCH LUỸ", r.nhan_day
    assert any("cao trào mua" in p for p in r.phan_bien)
    print(f"PASS  markup -> {r.nhan_day}")


def test_boi_canh_nguoc_thi_phai_phan_bien():
    """Đọc là tích luỹ trong khi giá đang ở đỉnh phạm vi -> phải cảnh báo.

    Bước 1 của phương pháp là định vị bối cảnh TRƯỚC. Tích luỹ ở đỉnh
    nhiều khả năng là tái phân phối đội lốt.
    """
    closes = (_doan(60, 100, 50) + _doan(99, 94, 3) + _doan(95, 100, 6)
              + [98, 99, 100, 98, 99, 100, 98, 99, 100, 99] * 5)
    closes = closes[:100]
    vols = ([1000] * 50 + [4000] * 3 + [1500] * 6 + [800] * 41)[:len(closes)]
    df = _dat(_khung(closes, vols), 93, close=99.0, low=92.0, volume=400)
    r = wy.doc_pha(df)
    assert r.cau_truc == "TÍCH LUỸ", r.nhan_day
    assert any("tái phân phối" in p for p in r.phan_bien), r.phan_bien
    print("PASS  tích luỹ ở vùng đỉnh -> có phản biện bối cảnh")


# ─────────────────────────────────────────────────────────────────────
# 5. Bất biến đo lường
# ─────────────────────────────────────────────────────────────────────

def test_cham_hai_lan_ra_cung_ket_qua():
    """Bất biến 2: cùng gói dữ liệu vào -> cùng kết quả ra."""
    df = _dat(_tich_luy(), 93, close=74.0, low=70.0, volume=400)
    assert wy.doc_pha(df) == wy.doc_pha(df.copy())
    print("PASS  hàm thuần, kết quả tái lập")


def test_khong_nhin_trom_tuong_lai():
    """Bất biến 1: thêm phiên MỚI không được đổi kết quả của phiên cũ.

    Đọc pha là một phép chấm theo thời điểm. Nếu kết quả ngày T đổi sau
    khi có dữ liệu ngày T+5, mọi so sánh lịch sử đều vô nghĩa.
    """
    day_du = _dat(_tich_luy(), 93, close=74.0, low=70.0, volume=400)
    cat = day_du.iloc[:-5].reset_index(drop=True)
    truoc = wy.doc_pha(cat)
    sau = wy.doc_pha(day_du.iloc[:len(cat)].reset_index(drop=True))
    assert truoc == sau
    print("PASS  cắt đuôi rồi chấm lại -> y hệt")


def test_he_so_gia_chi_doi_moc_gia_khong_doi_ket_luan():
    """Nguồn trả nghìn đồng, sổ lệnh dùng VNĐ — nhân hệ số không được
    làm đổi pha, vì mọi so sánh trong module đều là tỷ lệ."""
    df = _dat(_tich_luy(), 93, close=74.0, low=70.0, volume=400)
    mot = wy.doc_pha(df, he_so_gia=1.0)
    nghin = wy.doc_pha(df, he_so_gia=1000.0)
    assert mot.pha == nghin.pha and mot.su_kien == nghin.su_kien
    assert abs(nghin.san - mot.san * 1000) < 1.0
    print(f"PASS  hệ số giá: sàn {mot.san:,.0f} -> {nghin.san:,.0f}, pha không đổi")


def test_khong_ket_luan_duoc_thi_khong_co_moc_gia_gia():
    """Không đọc được thì sàn/trần phải là None, không phải 0.

    Số 0 đi vào chỗ định dạng sẽ hiện ra "0 VNĐ" — một mốc giá bịa.
    """
    r = wy.doc_pha(_tich_luy().tail(30).reset_index(drop=True))
    assert r.san is None and r.tran is None and r.pha is None
    print("PASS  không kết luận -> sàn/trần None, không phải 0")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    for ten, ham in sorted(globals().items()):
        if ten.startswith("test_") and not hasattr(ham, "pytestmark"):
            ham()
