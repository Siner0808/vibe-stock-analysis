"""Gác cho `paper_metrics.lo_ghi_hang_loat()`.

Vì sao có hàm này. Ngày 23/08/2026 đo `paper_trades.db`: cả 113 lệnh có
`created_at` nằm trong **258 giây** ngày 07/08/2026, trong khi `signal_date`
của chúng trải 2024-01-05 → 2026-06-26. Sổ ấy chưa bao giờ tích luỹ một
lệnh nào từ việc quét tiến về phía trước — nó là kết quả của MỘT lượt mô
phỏng.

Không có gì sai khi một sổ sinh ra như vậy. Sai là đọc nó như bằng chứng
tích luỹ, mà `CLAUDE.md` gọi nó là *"bằng chứng duy nhất chưa bị tối ưu
chạm vào"* nên cách đọc ấy là mặc định.

Hai loại lỗi phải chặn, và loại thứ hai nguy hiểm hơn:
  • bỏ sót lô hàng loạt  → sổ mô phỏng đi qua như sổ thật
  • **báo nhầm sổ thật** → cảnh báo kêu suốt thì không ai đọc nó nữa
"""
import datetime as dt

import paper_metrics as pm
from paper_trading import Trade

MOC = dt.datetime(2026, 8, 7, 14, 41).timestamp()


def _lenh(i: int, ngay: str, ghi_luc: float) -> Trade:
    return Trade(
        id=i, symbol="FPT", signal_date=ngay, entry_date=ngay,
        entry_price=100.0, exit_date=ngay, exit_price=101.0,
        exit_reason="STOP_LOSS", stop_loss=93.0, take_profit=110.0,
        size_pct=10.0, entry_score=62, status="CLOSED", created_at=ghi_luc)


def _ngay(n: int) -> str:
    return (dt.date(2024, 1, 5) + dt.timedelta(days=n)).isoformat()


# ─────────────────────────────────────────────────────────────────────
# 1. Bắt được lô hàng loạt
# ─────────────────────────────────────────────────────────────────────

def test_bat_duoc_lo_113_lenh_trong_258_giay():
    """Đúng hình dạng của `paper_trades.db` ngày 23/08/2026."""
    ts = [_lenh(i, _ngay(i * 8), MOC + i * 2.3) for i in range(113)]
    lo = pm.lo_ghi_hang_loat(ts)
    assert len(lo) == 1
    assert lo[0]["so_lenh"] == 113
    assert lo[0]["ngay_trai"] > 800
    print(f"PASS  bắt được lô {lo[0]['so_lenh']} lệnh / "
          f"{lo[0]['giay']:.0f} giây / trải {lo[0]['ngay_trai']} ngày")


def test_hai_lo_cach_xa_nhau_thi_dem_la_hai():
    ts = ([_lenh(i, _ngay(i * 8), MOC + i) for i in range(30)]
          + [_lenh(100 + i, _ngay(300 + i * 8), MOC + 86400 + i)
             for i in range(30)])
    assert len(pm.lo_ghi_hang_loat(ts)) == 2
    print("PASS  hai lô cách nhau một ngày -> đếm là hai")


# ─────────────────────────────────────────────────────────────────────
# 2. KHÔNG báo nhầm sổ tích luỹ thật
# ─────────────────────────────────────────────────────────────────────

def test_so_tich_luy_that_KHONG_bi_bao():
    """Mỗi lệnh ghi cách nhau một ngày, đúng như quét từng phiên."""
    ts = [_lenh(i, _ngay(i), MOC + i * 86400) for i in range(150)]
    assert pm.lo_ghi_hang_loat(ts) == []
    print("PASS  sổ ghi mỗi ngày một lệnh -> không báo")


def test_mot_phien_ban_ron_KHONG_bi_bao():
    """20 lệnh trong 30 giây là bình thường — nếu CÙNG một ngày tín hiệu.

    Đây là ô dễ báo nhầm nhất: chỉ nhìn `created_at` thì phiên này giống
    hệt một lượt mô phỏng. Thứ phân biệt là `signal_date` không trải.
    """
    ts = [_lenh(i, "2026-03-04", MOC + i * 1.5) for i in range(20)]
    assert pm.lo_ghi_hang_loat(ts) == [], "một phiên bận rộn bị báo nhầm"
    print("PASS  20 lệnh/30 giây cùng một ngày tín hiệu -> không báo")


def test_it_lenh_thi_khong_ket_luan():
    ts = [_lenh(i, _ngay(i * 40), MOC + i) for i in range(5)]
    assert pm.lo_ghi_hang_loat(ts) == []
    print("PASS  5 lệnh -> không đủ để nói gì")


def test_lo_NHO_nam_canh_lo_lon_van_phai_bi_bo_qua():
    """Ngưỡng tối thiểu phải áp cho TỪNG lô, không chỉ cho tổng số lệnh.

    Không có test này thì phép kiểm bên trong vòng lặp là mã chết: lần
    đột biến ngày 23/08/2026 xoá nó đi mà cả bộ test vẫn xanh, vì mọi
    trường hợp ít lệnh đều bị chặn sớm ở lối vào hàm.
    """
    lon = [_lenh(i, _ngay(i * 8), MOC + i) for i in range(30)]
    nho = [_lenh(500 + i, _ngay(400 + i * 100), MOC + 86400 + i)
           for i in range(4)]          # 4 lệnh, tín hiệu trải 300 ngày
    lo = pm.lo_ghi_hang_loat(lon + nho)
    assert len(lo) == 1 and lo[0]["so_lenh"] == 30, (
        f"lô 4 lệnh không được coi là lô hàng loạt (nhận {lo})")
    print("PASS  lô 4 lệnh cạnh lô 30 lệnh -> chỉ báo lô 30")


# ─────────────────────────────────────────────────────────────────────
# 3. Không biết thì phải NÓI là không biết
# ─────────────────────────────────────────────────────────────────────

def test_so_khong_co_dau_thoi_gian_thi_bao_khong_ro():
    """Sổ cũ hơn schema hiện tại thiếu `created_at`.

    Rỗng ở đây nghĩa là "không thấy", KHÔNG phải "đã chứng minh là
    không có" — và `tom_tat_lo_ghi` phải nói ra phần chưa biết.
    """
    ts = [Trade(id=i, symbol="FPT", signal_date=_ngay(i * 8),
                entry_date=None, entry_price=None, exit_date=None,
                exit_price=None, exit_reason=None, stop_loss=0.0,
                take_profit=0.0, size_pct=10.0, entry_score=62,
                status="CLOSED") for i in range(50)]
    tt = pm.tom_tat_lo_ghi(ts)
    assert tt["so_lo"] == 0
    assert tt["so_lenh_khong_ro"] == 50, (
        "im lặng về 50 lệnh không rõ nguồn gốc là nói dối bằng cách bỏ sót")
    print("PASS  thiếu created_at -> báo 50 lệnh không rõ")


def test_tron_lan_thi_dem_dung_ca_hai_phan():
    co = [_lenh(i, _ngay(i * 8), MOC + i) for i in range(40)]
    khong = [Trade(id=900 + i, symbol="ACB", signal_date=_ngay(i),
                   entry_date=None, entry_price=None, exit_date=None,
                   exit_price=None, exit_reason=None, stop_loss=0.0,
                   take_profit=0.0, size_pct=10.0, entry_score=62,
                   status="CLOSED") for i in range(7)]
    tt = pm.tom_tat_lo_ghi(co + khong)
    assert tt["so_lenh_trong_lo"] == 40 and tt["so_lenh_khong_ro"] == 7
    print("PASS  trộn lẫn -> 40 trong lô, 7 không rõ")


# ─────────────────────────────────────────────────────────────────────
# 4. Cảnh báo phải HIỆN trong report()
# ─────────────────────────────────────────────────────────────────────

def test_report_phai_in_canh_bao():
    """Một phép đo không ai nhìn thấy thì không bảo vệ được gì."""
    ts = [_lenh(i, _ngay(i * 8), MOC + i * 2.3) for i in range(113)]
    bao = pm.report(ts)
    assert "KHÔNG PHẢI BẢN GHI TÍCH LUỸ" in bao
    # 112 khoảng × 2,3 giây = 257,6 -> làm tròn "258 giây". Khẳng định
    # đúng con số chứ không phải "có chữ s trong báo cáo" — một gác khớp
    # được với gần như mọi chuỗi thì không gác gì cả.
    assert "258 giây" in bao, bao
    assert "2024-01-05" in bao and "113 lệnh" in bao
    print("PASS  report() in đúng 258 giây và khoảng ngày tín hiệu")


def test_report_so_that_KHONG_in_canh_bao():
    ts = [_lenh(i, _ngay(i), MOC + i * 86400) for i in range(150)]
    assert "KHÔNG PHẢI BẢN GHI TÍCH LUỸ" not in pm.report(ts)
    print("PASS  sổ tích luỹ -> report() im lặng, đúng")
