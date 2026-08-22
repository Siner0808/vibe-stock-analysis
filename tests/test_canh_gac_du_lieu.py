"""Test canh gác đường dữ liệu nội phiên.

VÌ SAO CÓ FILE NÀY
──────────────────
`quet()` chỉ gọi hàm tải nến khi CÓ vị thế đang mở. Lượt chạy 22/08/2026
có 113 lệnh nhưng cả 113 đều đã đóng, nên vòng lặp không chạy lần nào và
`intraday_data.tai()` chưa từng được thực thi trên runner. Bước cảnh báo
in ra "không vị thế nào chạm SL/TP" — câu đó ĐÚNG mà chứng minh được rất
ít: nó chỉ nói `vi_the_dang_mo()` chạy được.

Canh gác lấp đúng chỗ trống đó. Nhưng một cái canh gác kêu oan còn tệ hơn
không có, nên phần lớn test dưới đây kiểm chiều KHÔNG ĐƯỢC KÊU:

  · nhịp 09:00 chạy trước nến đầu tiên  -> hôm nay 0 nến là BÌNH THƯỜNG
  · có vị thế đang mở                   -> KHÔNG canh gác, khỏi gọi thừa

Và một bất biến giữ nguyên: canh gác KHÔNG đổi trạng thái sổ lệnh.

Chạy offline: hàm tải nến bị thay bằng hàm giả.
"""
import os
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta, timezone

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import canh_bao_noi_phien as cb

VN = timezone(timedelta(hours=7))
HOM_NAY = "2026-08-21"
BAY_GIO = datetime(2026, 8, 21, 14, 0, tzinfo=VN)


def _nen(dau: str, so: int, gia: float = 22_000.0) -> pd.DataFrame:
    """`so` nến 30 phút bắt đầu từ `dau`, giá quanh `gia` (VNĐ)."""
    t0 = pd.Timestamp(dau)
    return pd.DataFrame({
        "time": [t0 + pd.Timedelta(minutes=30 * i) for i in range(so)],
        "open": [gia] * so,
        "high": [gia * 1.01] * so,
        "low": [gia * 0.99] * so,
        "close": [gia] * so,
        "volume": [100_000] * so,
    })


def _nem(loi):
    """Hàm tải nến luôn ném — viết tường minh cho dễ đọc."""
    def tai(ma, tu, den):
        raise loi
    return tai


def _so(lenh: list) -> str:
    """Sổ lệnh tạm chỉ có bảng trades."""
    fd, p = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    c = sqlite3.connect(p)
    c.execute("CREATE TABLE trades (symbol TEXT, entry_date TEXT, "
              "entry_price REAL, stop_loss REAL, take_profit REAL, "
              "status TEXT)")
    for t in lenh:
        c.execute("INSERT INTO trades VALUES (?,?,?,?,?,?)",
                  (t["symbol"], "2026-08-01", 22_000.0, t["stop_loss"],
                   t["take_profit"], t.get("status", "OPEN")))
    c.commit()
    c.close()
    return p


def _doc(p) -> list:
    """Đọc trạng thái sổ. ĐÓNG kết nối — Windows khoá file đang mở, và
    `_don()` sẽ ném PermissionError che mất lỗi thật."""
    c = sqlite3.connect(p)
    try:
        return c.execute("SELECT symbol, status FROM trades").fetchall()
    finally:
        c.close()


def _don(p):
    if p and os.path.exists(p):
        os.remove(p)


# ─────────────────────────────────────────────────────────────────────
# 1. Nguồn hỏng -> nói ra là hỏng
# ─────────────────────────────────────────────────────────────────────

def test_nguon_nem_thi_bao_hong_chu_khong_nem_theo():
    """Canh gác hỏng KHÔNG được kéo cả bước cảnh báo chết theo."""
    g = cb.canh_gac(HOM_NAY, _nem(RuntimeError("khoa API het han")))
    assert not g.song, "nguồn ném mà vẫn báo sống"
    assert not g.dat
    assert "RuntimeError" in g.loi, f"không nêu loại lỗi: {g.loi}"
    assert "khoa API het han" in g.loi, f"không nêu nội dung lỗi: {g.loi}"
    print("PASS  nguồn ném -> báo hỏng, không ném theo")


def test_nguon_tra_rong_ca_khoang_la_hong():
    """Rỗng cả 10 ngày thì không phải 'chưa tới giờ' — đó là hỏng."""
    g = cb.canh_gac(HOM_NAY, lambda ma, tu, den: _nen(HOM_NAY, 0))
    assert not g.song, "rỗng cả khoảng mà vẫn báo sống"
    assert "rỗng" in g.loi, f"không nói rõ vì sao: {g.loi}"
    assert "2026-08-11" in g.loi and "2026-08-21" in g.loi, (
        f"không nêu khoảng đã hỏi: {g.loi}")
    print("PASS  rỗng cả khoảng -> hỏng, có nêu khoảng đã hỏi")


def test_nguon_tra_None_la_hong():
    g = cb.canh_gac(HOM_NAY, lambda ma, tu, den: None)
    assert not g.song and not g.dat
    print("PASS  nguồn trả None -> hỏng")


# ─────────────────────────────────────────────────────────────────────
# 2. KHÔNG ĐƯỢC KÊU OAN
# ─────────────────────────────────────────────────────────────────────

def test_chua_co_nen_hom_nay_van_la_DAT():
    """Nhịp 09:00 chạy TRƯỚC khi nến 30 phút đầu tiên kịp đóng.

    Đây là test quan trọng nhất file này. Nếu canh gác chỉ hỏi riêng hôm
    nay thì nó sẽ kêu hỏng vào nhịp đầu MỖI phiên — 1 báo động giả mỗi
    ngày, và vài ngày là người ta thôi đọc nó.
    """
    tuan_truoc = _nen("2026-08-20 09:00", 9)     # chỉ có nến HÔM QUA
    g = cb.canh_gac(HOM_NAY, lambda ma, tu, den: tuan_truoc)

    assert g.song, "có nến tuần trước mà vẫn báo nguồn chết"
    assert g.dat, f"chưa có nến hôm nay bị coi là hỏng: {g.dong_log()}"
    assert g.so_nen_hom_nay == 0, f"đếm nhầm nến hôm nay: {g.so_nen_hom_nay}"
    assert g.so_nen_tong == 9
    print("PASS  chưa có nến hôm nay vẫn ĐẠT — không kêu oan lúc 09:00")


def test_co_nen_hom_nay_thi_dem_dung():
    d = pd.concat([_nen("2026-08-20 09:00", 9), _nen("2026-08-21 09:00", 4)],
                  ignore_index=True)
    g = cb.canh_gac(HOM_NAY, lambda ma, tu, den: d)
    assert g.dat
    assert g.so_nen_tong == 13
    assert g.so_nen_hom_nay == 4, (
        f"nến hôm nay = {g.so_nen_hom_nay}, đáng lẽ 4 — lọc theo ngày sai")
    print("PASS  đếm đúng 4 nến hôm nay trong 13 nến")


# ─────────────────────────────────────────────────────────────────────
# 3. Cái bẫy đơn vị — sổ rỗng thì không có mốc nào để so
# ─────────────────────────────────────────────────────────────────────

def test_gia_theo_nghin_dong_bi_bat():
    """22,2 thay vì 22.200 — chính cái bẫy ở NGUYEN-TAC-DO-LUONG.md.

    Lệch bậc này làm `low <= stop_loss` đúng với MỌI vị thế, tức báo động
    giả toàn bộ. `_kiem_don_vi()` bắt được nó nhưng cần một mốc SL/TP để
    so; sổ rỗng thì không có mốc nào, nên canh gác so với hằng số.
    """
    g = cb.canh_gac(HOM_NAY, lambda ma, tu, den: _nen(HOM_NAY, 9, gia=22.2))

    assert g.song, "nguồn trả được dữ liệu thì vẫn là sống"
    assert not g.dat, "giá nghìn đồng mà vẫn báo ĐẠT"
    assert "nghìn đồng" in g.loi, f"không chỉ ra nghi ngờ gì: {g.loi}"
    print("PASS  giá nghìn đồng -> sống nhưng KHÔNG đạt")


def test_gia_VND_binh_thuong_thi_dat():
    g = cb.canh_gac(HOM_NAY,
                    lambda ma, tu, den: _nen(HOM_NAY, 9, gia=22_000.0))
    assert g.dat and g.loi is None
    assert abs(g.gia_giua - 22_000.0) < 1e-6
    print("PASS  giá VNĐ bình thường -> đạt")


# ─────────────────────────────────────────────────────────────────────
# 4. Hỏi đúng khoảng, đúng mã
# ─────────────────────────────────────────────────────────────────────

def test_hoi_dung_khoang_va_dung_thu_tu_tham_so():
    goi = []

    def ghi(ma, tu, den):
        goi.append((ma, tu, den))
        return _nen(HOM_NAY, 9)

    cb.canh_gac(HOM_NAY, ghi, ma="VNM", so_ngay=10)
    assert goi == [("VNM", "2026-08-11", "2026-08-21")], f"gọi sai: {goi}"
    print("PASS  hỏi đúng mã và đúng khoảng 10 ngày")


def test_ma_mac_dinh_la_von_hoa_lon():
    """Mã canh gác phải có giá VNĐ cao hơn hẳn ngưỡng, nếu không
    `_kiem_thang_gia` sẽ báo động giả cho chính mã canh gác."""
    assert cb.MA_CANH_GAC == "ACB"
    assert cb.NGUONG_VND == 1_000.0
    print(f"PASS  mã mặc định {cb.MA_CANH_GAC}, "
          f"ngưỡng {cb.NGUONG_VND:,.0f} VNĐ")


# ─────────────────────────────────────────────────────────────────────
# 5. quet_va_canh_gac — điều kiện phải phủ ĐÚNG chỗ trống
# ─────────────────────────────────────────────────────────────────────

def test_so_rong_thi_CO_canh_gac():
    p = _so([])
    try:
        r = cb.quet_va_canh_gac(p, HOM_NAY, BAY_GIO,
                                lambda s, n: _nen(HOM_NAY, 9),
                                lambda m, t, d: _nen(HOM_NAY, 9))
        assert r["so_vi_the"] == 0
        assert r["canh_gac"] is not None, "sổ rỗng mà không canh gác"
        assert r["canh_gac"].dat
    finally:
        _don(p)
    print("PASS  sổ rỗng -> có canh gác")


def test_co_vi_the_thi_KHONG_goi_canh_gac():
    """Chiều ngược lại. Thiếu test này thì một bản 'canh gác luôn luôn'
    cũng xanh — mà bản đó tốn thêm một lần gọi mạng mỗi nhịp trong khi
    các lần nạp thật đã chứng minh đường dữ liệu rồi."""
    p = _so([{"symbol": "ACB", "stop_loss": 20_000.0,
              "take_profit": 25_000.0}])
    goi = []

    def khoang(ma, tu, den):
        goi.append(ma)
        return _nen(HOM_NAY, 9)

    try:
        r = cb.quet_va_canh_gac(p, HOM_NAY, BAY_GIO,
                                lambda s, n: _nen(HOM_NAY, 9), khoang)
        assert r["so_vi_the"] == 1
        assert r["canh_gac"] is None, "có vị thế mà vẫn canh gác"
        assert goi == [], f"gọi mạng thừa {len(goi)} lần: {goi}"
    finally:
        _don(p)
    print("PASS  có vị thế -> không canh gác, không gọi mạng thừa")


def test_canh_gac_khong_dong_vao_so_lenh():
    """Bất biến của cả module: BÁO, KHÔNG ĐỘNG VÀO SỔ."""
    p = _so([{"symbol": "ACB", "stop_loss": 20_000.0,
              "take_profit": 25_000.0, "status": "CLOSED"}])
    try:
        truoc = _doc(p)
        cb.quet_va_canh_gac(p, HOM_NAY, BAY_GIO,
                            lambda s, n: _nen(HOM_NAY, 9),
                            lambda m, t, d: _nen(HOM_NAY, 9))
        sau = _doc(p)
        assert truoc == sau, f"sổ lệnh bị đổi: {truoc} -> {sau}"
    finally:
        _don(p)
    print("PASS  canh gác không đổi trạng thái lệnh nào")


def test_quet_va_canh_gac_giu_nguyen_khoa_cu():
    """Bọc thêm không được làm mất thứ `quet()` vẫn trả về."""
    p = _so([])
    try:
        r = cb.quet_va_canh_gac(p, HOM_NAY, BAY_GIO,
                                lambda s, n: _nen(HOM_NAY, 9),
                                lambda m, t, d: _nen(HOM_NAY, 9))
        for k in ("so_vi_the", "canh_bao", "loi"):
            assert k in r, f"mất khoá {k!r} của quet()"
    finally:
        _don(p)
    print("PASS  giữ nguyên mọi khoá của quet()")


# ─────────────────────────────────────────────────────────────────────
# 6. Dòng log phải đọc được mà không cần mở mã
# ─────────────────────────────────────────────────────────────────────

def test_dong_log_ba_trang_thai_deu_noi_ra_van_de():
    hong = cb.canh_gac(HOM_NAY, _nem(IOError("mat mang")))
    lech = cb.canh_gac(HOM_NAY, lambda m, t, d: _nen(HOM_NAY, 9, gia=22.2))
    tot = cb.canh_gac(HOM_NAY, lambda m, t, d: _nen(HOM_NAY, 9))

    assert "HỎNG" in hong.dong_log(), hong.dong_log()
    assert "bất thường" in lech.dong_log(), lech.dong_log()
    assert "sống" in tot.dong_log(), tot.dong_log()
    assert "22,000" in tot.dong_log(), tot.dong_log()
    for g in (hong, lech, tot):
        print(f"      {g.dong_log()}")
    print("PASS  ba trạng thái đều có dòng log tự giải thích")


if __name__ == "__main__":
    for ten, ham in sorted(list(globals().items())):
        if ten.startswith("test_"):
            ham()
    print("\nTẤT CẢ ĐỀU QUA")
