"""Gác cho `run_daily.canh_bao_nguon()` — "0 lệnh" phải nói được vì sao.

`execute_daily_scan` bỏ qua một mã bằng `break` khi nguồn dữ liệu trả
`SYNTHETIC` (mất kết nối → `data_collectors` sinh giá bằng `np.random`)
hoặc khi không đủ 20 nến. Trước 24/08/2026 cả hai nhánh đó **im lặng hoàn
toàn**: một ngày mà cả 71 mã mất nguồn cho ra đúng cùng một báo cáo với
một ngày không có tín hiệu nào — "0 lệnh mới".

Cổng C5 đóng thì hai thứ đó như nhau, vì không ngày nào mở lệnh. Cổng mở
rồi (24/08/2026) thì chúng khác hẳn: một bên là thị trường không có cơ
hội, một bên là hệ thống đang mù.

Dữ liệu SYNTHETIC không bao giờ tới được `run_session` — nhánh `break`
chặn trước. Gác này không phải về việc đó; nó về việc **im lặng**.
"""
import run_daily


def test_quet_du_ca_ro_thi_khong_canh_bao():
    assert run_daily.canh_bao_nguon(71, {}, 71) == ""
    print("PASS  quét đủ 71/71 -> im lặng, đúng")


def test_bo_qua_it_ma_thi_bao_nhung_khong_bao_dong():
    ra = run_daily.canh_bao_nguon(60, {"SYNTHETIC": 11}, 71)
    assert "bỏ qua 11 mã" in ra and "SYNTHETIC: 11" in ra
    assert "CHỈ QUÉT ĐƯỢC" not in ra, "11/71 chưa phải mức báo động"
    print(f"PASS  bỏ qua 11 -> báo, không báo động: {ra.strip()}")


def test_mat_nguon_ca_ro_thi_PHAI_BAO_DONG():
    """Đây là ô mà cảnh báo này sinh ra để bắt."""
    ra = run_daily.canh_bao_nguon(0, {"SYNTHETIC": 71}, 71)
    assert "CHỈ QUÉT ĐƯỢC 0/71" in ra
    assert "không kết luận được gì" in ra, (
        "phải nói rõ phiên này KHÔNG kết luận được gì về thị trường — "
        "'0 lệnh' đọc một mình là một câu nói dối bằng cách bỏ sót")
    print("PASS  mất nguồn cả rổ -> báo động")


def test_nguong_bao_dong_la_MOT_NUA_ro():
    assert "CHỈ QUÉT ĐƯỢC" not in run_daily.canh_bao_nguon(36, {"x": 35}, 71)
    assert "CHỈ QUÉT ĐƯỢC" in run_daily.canh_bao_nguon(35, {"x": 36}, 71)
    print("PASS  ranh giới đúng ở một nửa rổ (35/36 trên 71)")


def test_gop_nhieu_ly_do_va_sap_xep_on_dinh():
    """Cùng một tình trạng phải cho cùng một chuỗi, để so sánh giữa các phiên."""
    a = run_daily.canh_bao_nguon(50, {"SYNTHETIC": 15, "thiếu nến": 6}, 71)
    b = run_daily.canh_bao_nguon(50, {"thiếu nến": 6, "SYNTHETIC": 15}, 71)
    assert a == b, "thứ tự dict làm đổi chuỗi -> hai phiên giống nhau đọc khác nhau"
    assert "bỏ qua 21 mã" in a
    print(f"PASS  gộp lý do, thứ tự ổn định: {a.strip()}")


def test_ro_rong_khong_no():
    """Chia cho 0 ở `quet_duoc * 2 < tong_ma` không xảy ra, nhưng phải chắc."""
    assert run_daily.canh_bao_nguon(0, {}, 0) == ""
    print("PASS  rổ rỗng -> chuỗi rỗng, không nổ")
