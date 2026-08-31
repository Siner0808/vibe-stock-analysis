"""Test chuông báo ngày không có lượt quét nào.

Chuông báo sai còn tệ hơn không có chuông: kêu oan vài lần là người ta
thôi nghe, rồi lần kêu thật cũng bị bỏ qua. Nên bốn thứ phải đúng:

  1. Ngày cuối tuần KHÔNG bị coi là ngày trống — cron quét chỉ chạy T2–T6.
  2. Ngày trước khi workflow tồn tại KHÔNG bị soát.
  3. Chỉ lượt `conclusion == "success"` được tính. Lượt đỏ, lượt bị huỷ,
     lượt đang chạy đều không phải bằng chứng đã quét.
  4. Soát nhiều ngày chứ không chỉ hôm nay — vì chính chuông cũng chạy
     bằng cron GitHub và cũng bị rơi nhịp.

Chạy offline, không gọi mạng.
"""
import datetime as dt
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))

import chuong_bao_quet as cb


def _luot(ngay: str, ket_qua: str = "success", gio: str = "08:30") -> dict:
    return {"created_at": f"{ngay}T{gio}:00Z", "conclusion": ket_qua}


# ─────────────────────────────────────────────────────────────────────
# 1. Chọn ngày để soát
# ─────────────────────────────────────────────────────────────────────

def test_bo_qua_cuoi_tuan():
    # 2026-08-24 là thứ Hai. Ba ngày làm việc gần nhất phải nhảy qua
    # T7 22/08 và CN 23/08 để lấy T5 20/08 và T6 21/08.
    ra = cb.cac_ngay_lam_viec(dt.date(2026, 8, 24), so_ngay=3)
    assert ra == ["2026-08-20", "2026-08-21", "2026-08-24"], ra
    print("PASS  cuối tuần không bị soát")


def test_khong_soat_truoc_khi_workflow_ton_tai():
    ra = cb.cac_ngay_lam_viec(dt.date(2026, 8, 14), so_ngay=5,
                              tu_ngay="2026-08-13")
    assert ra == ["2026-08-13", "2026-08-14"], ra
    print("PASS  không soát ngược quá mốc workflow ra đời")


def test_so_ngay_khong_hop_le_thi_no():
    for xau in (0, -3):
        try:
            cb.cac_ngay_lam_viec(dt.date(2026, 8, 21), so_ngay=xau)
        except ValueError:
            pass
        else:
            raise AssertionError(f"so_ngay={xau} được nhận")
    print("PASS  so_ngay < 1 bị từ chối")


# ─────────────────────────────────────────────────────────────────────
# 2. Chỉ lượt THÀNH CÔNG mới được tính
# ─────────────────────────────────────────────────────────────────────

def test_chi_dem_luot_thanh_cong():
    runs = [
        _luot("2026-08-20", "success"),
        _luot("2026-08-20", "failure"),
        _luot("2026-08-20", "cancelled"),
        _luot("2026-08-20", None),          # đang chạy
        _luot("2026-08-19", "success"),
        _luot("2026-08-19", "success"),
    ]
    assert cb.dem_luot_thanh_cong(runs) == {"2026-08-20": 1, "2026-08-19": 2}
    print("PASS  chỉ lượt success được tính là đã quét")


def test_ngay_chi_co_luot_do_bi_coi_la_trong():
    """Ngày có 6 lượt nhưng đỏ hết vẫn là ngày không được quét."""
    runs = [_luot("2026-08-20", "failure") for _ in range(6)]
    kq = cb.kiem_tra(runs, dt.date(2026, 8, 20), so_ngay=1)
    assert kq["ngay_trong"] == ["2026-08-20"], kq
    print("PASS  ngày toàn lượt đỏ -> báo trống, không nhầm là đã quét")


# ─────────────────────────────────────────────────────────────────────
# 3. Kết luận
# ─────────────────────────────────────────────────────────────────────

def test_moi_ngay_deu_co_quet_thi_im_lang():
    runs = [_luot(n) for n in ("2026-08-19", "2026-08-20", "2026-08-21")]
    kq = cb.kiem_tra(runs, dt.date(2026, 8, 21), so_ngay=3)
    assert kq["ngay_trong"] == [], kq
    assert kq["chi_tiet"] == {"2026-08-19": 1, "2026-08-20": 1,
                              "2026-08-21": 1}, kq["chi_tiet"]
    print("PASS  đủ cả ba ngày -> không kêu")


def test_bat_duoc_ngay_trong_o_giua():
    """Ngày trống KHÔNG phải hôm nay — đây là lý do soát nhiều ngày.

    Nếu chuông chỉ soát hôm nay thì nhịp chuông của 20/08 bị rơi là ngày
    đó im lặng vĩnh viễn.
    """
    runs = [_luot("2026-08-19"), _luot("2026-08-21")]
    kq = cb.kiem_tra(runs, dt.date(2026, 8, 21), so_ngay=3)
    assert kq["ngay_trong"] == ["2026-08-20"], kq
    print("PASS  bắt được ngày trống ở giữa, không chỉ hôm nay")


def test_khong_co_luot_nao_thi_bao_het_khoang_soat():
    kq = cb.kiem_tra([], dt.date(2026, 8, 21), so_ngay=3)
    assert kq["ngay_trong"] == ["2026-08-19", "2026-08-20", "2026-08-21"], kq
    print("PASS  không có lượt nào -> báo cả ba ngày")


# ─────────────────────────────────────────────────────────────────────
# 4. Workflow phải thật sự gọi công cụ này
# ─────────────────────────────────────────────────────────────────────

def test_workflow_goi_dung_cong_cu():
    goc = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    p = os.path.join(goc, ".github", "workflows", "chuong-bao-quet.yml")
    assert os.path.exists(p), "chưa có workflow chuông báo"
    s = io.open(p, encoding="utf-8").read()
    assert "tools/chuong_bao_quet.py" in s, "workflow không gọi công cụ"
    assert "actions: read" in s, (
        "thiếu quyền actions:read — không đọc được danh sách lượt chạy")
    print("PASS  workflow gọi đúng công cụ và có đủ quyền")


if __name__ == "__main__":
    for ten, ham in sorted(list(globals().items())):
        if ten.startswith("test_"):
            ham()
    print("\nTẤT CẢ ĐỀU QUA")
