"""Điều kiện dừng cổng C5 — BẢN 2, đo bằng ALPHA khớp từng lệnh.

VÌ SAO CÓ FILE NÀY
──────────────────
Bản 1 (26/08/2026) đo KỲ VỌNG và hiệu chuẩn để bắt −2,5%/lệnh, trong khi
mức bất lợi đo được ngoài mẫu là alpha −0,927%. Nó cần 11,4 năm để đạt
80% lực phát hiện, chỉ định giá sai lầm loại I, và đếm mù lệnh chưa đóng —
ngày 29/08/2026 sổ có 4 lệnh PENDING mà nó báo "0/60".

Bản 2 khoá ở đây, năm điều:

  1. THIẾU rổ chuẩn thì KHÔNG kết luận. Không được lặng lẽ quay về kỳ
     vọng — đó đúng là lỗi đang sửa.
  2. Biên HẠI: alpha âm tới mức khoảng tin cậy loại được 0 → ĐÓNG.
  3. Biên ĐẢO GÁNH NẶNG: đủ cỡ mẫu nêu trước mà chưa chứng minh được lợi
     thế → ĐÓNG. Đây là chỗ định giá sai lầm loại II.
  4. Lệnh đã cam kết mà chưa đóng phải ĐẾM ĐƯỢC và nói ra.
  5. Ngưỡng phải SUY TỪ lực phát hiện ở mức hiệu ứng thực tế, không phải
     một con số gõ tay.
"""
import ast
import datetime as dt
import random
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import paper_metrics as pm  # noqa: E402
from paper_trading import Trade  # noqa: E402

MOC = dt.datetime(2026, 8, 7, 14, 41).timestamp()


def _ngay(n: int) -> str:
    return (dt.date(2024, 1, 5) + dt.timedelta(days=n)).isoformat()


def _lenh(i: int, trang_thai: str = "CLOSED") -> Trade:
    """Lệnh tiến-về-trước: ghi cách nhau một ngày nên không thành lô."""
    vao, ra = _ngay(i * 3), _ngay(i * 3 + 1)
    return Trade(
        id=i, symbol="FPT", signal_date=vao, entry_date=vao,
        entry_price=100.0, exit_date=(ra if trang_thai == "CLOSED" else None),
        exit_price=(103.0 if trang_thai == "CLOSED" else None),
        exit_reason=("TAKE_PROFIT" if trang_thai == "CLOSED" else None),
        stop_loss=93.0, take_profit=110.0, size_pct=10.0, entry_score=62,
        status=trang_thai, created_at=MOC + 86400 * (i + 1))


def _so(n: int, alpha: float, sd: float = 0.0, seed: int = 7):
    """n lệnh đã đóng + rổ chuẩn sao cho alpha mỗi lệnh ĐÚNG như đặt.

    Dựng rổ từ chính `net_return_pct()` của lệnh: bench = net − alpha. Nhờ
    thế không phải tính lại phí — và không phải tự viết phép tính lợi
    nhuận, thứ mà `NGUYEN-TAC-DO-LUONG.md` cấm.
    """
    rng = random.Random(seed)
    ts = [_lenh(i) for i in range(n)]
    ro = {}
    for t in ts:
        a = alpha + (rng.gauss(0.0, sd) if sd else 0.0)
        ro[(t.entry_date, t.exit_date)] = t.net_return_pct() - a
    return ts, ro


# ── 1. Thiếu rổ chuẩn thì KHÔNG kết luận ─────────────────────────────

def test_thieu_ro_chuan_thi_KHONG_ket_luan():
    ts, _ = _so(300, -5.0)
    kq = pm.dieu_kien_dong_lai(ts, None)
    assert kq["dat"] is False and kq["do_duoc"] is False
    assert "ALPHA" in kq["ly_do"], kq["ly_do"]
    print(f"PASS  thiếu rổ chuẩn -> không kết luận · {kq['ly_do'][:52]}…")


def test_KHONG_duoc_quay_ve_ky_vong():
    """Bản 1 đo kỳ vọng. Gọi lại nó ở đây là quay về đúng lỗi đang sửa."""
    cay = ast.parse((GOC / "paper_metrics.py").read_text(encoding="utf-8"))
    ham = next(n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef)
               and n.name == "dieu_kien_dong_lai")
    goi = {n.func.id for n in ast.walk(ham)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert "expectancy_significant" not in goi, goi
    assert "vs_benchmark" in goi, goi
    print("PASS  chỉ gọi vs_benchmark, không gọi expectancy_significant")


# ── 2. Biên HẠI ──────────────────────────────────────────────────────

def test_chua_du_mau_thi_KHONG_dong_du_lo_nang():
    ts, ro = _so(100, -5.0, sd=2.0)
    kq = pm.dieu_kien_dong_lai(ts, ro)
    assert kq["dat"] is False and kq["do_duoc"] is True
    assert str(pm.N_TOI_THIEU) in kq["ly_do"], kq["ly_do"]
    print(f"PASS  100 lệnh alpha −5% -> chưa đủ mẫu · {kq['ly_do'][:46]}…")


def test_alpha_am_DO_DUOC_thi_DONG():
    ts, ro = _so(200, -3.0, sd=8.0)
    kq = pm.dieu_kien_dong_lai(ts, ro)
    assert kq["dat"] is True, kq
    assert kq["ci"][1] < 0, kq["ci"]
    assert "THUA" in kq["ly_do"], kq["ly_do"]
    print(f"PASS  200 lệnh alpha {kq['alpha']:+.2f}% -> ĐÓNG · KTC {kq['ci']}")


def test_alpha_am_NHE_trong_nhieu_thi_KHONG_dong():
    """Âm thôi chưa đủ — phải âm tới mức khoảng tin cậy loại được 0."""
    ts, ro = _so(200, -0.2, sd=8.0)
    kq = pm.dieu_kien_dong_lai(ts, ro)
    assert kq["dat"] is False, kq
    assert kq["ci"][1] > 0, kq["ci"]
    print(f"PASS  alpha {kq['alpha']:+.2f}% trong nhiễu -> KHÔNG đóng")


# ── 3. Đảo gánh nặng chứng minh tại N_DAY_DU ─────────────────────────

def test_du_co_mau_ma_CHUA_CHUNG_MINH_duoc_thi_DONG():
    """Chỗ bản 1 không có: hệ thống không lợi thế cũng phải dừng."""
    ts, ro = _so(pm.N_DAY_DU + 20, +0.2, sd=8.0)
    kq = pm.dieu_kien_dong_lai(ts, ro)
    assert kq["dat"] is True, kq
    assert "chưa chứng minh" in kq["ly_do"], kq["ly_do"]
    assert kq["ci"][0] < 0 < kq["ci"][1], kq["ci"]
    print(f"PASS  {kq['so_lenh']} lệnh alpha {kq['alpha']:+.2f}% -> ĐÓNG vì "
          f"chưa chứng minh được lợi thế")


def test_du_co_mau_va_CHUNG_MINH_duoc_thi_KHONG_dong():
    ts, ro = _so(pm.N_DAY_DU + 20, +3.0, sd=8.0)
    kq = pm.dieu_kien_dong_lai(ts, ro)
    assert kq["dat"] is False, kq
    assert kq["ci"][0] > 0, kq["ci"]
    assert "VƯỢT" in kq["ly_do"], kq["ly_do"]
    print(f"PASS  alpha {kq['alpha']:+.2f}% có ý nghĩa -> KHÔNG đóng")


def test_truoc_moc_day_du_thi_khong_ap_ganh_nang():
    """Cùng một alpha yếu: trước mốc thì chạy tiếp, sau mốc thì đóng."""
    ts, ro = _so(300, +0.2, sd=8.0)
    assert pm.dieu_kien_dong_lai(ts, ro)["dat"] is False
    ts2, ro2 = _so(pm.N_DAY_DU + 20, +0.2, sd=8.0)
    assert pm.dieu_kien_dong_lai(ts2, ro2)["dat"] is True
    print("PASS  gánh nặng chứng minh chỉ áp TỪ mốc đủ cỡ mẫu")


# ── 4. Lệnh đã cam kết mà chưa đóng ──────────────────────────────────

def test_dem_ca_lenh_DA_CAM_KET_chua_dong():
    """Ngày 29/08/2026 sổ có 4 lệnh PENDING mà bản 1 báo '0/60'."""
    ts, ro = _so(200, -3.0, sd=8.0)
    cho = [_lenh(9000 + i, "PENDING") for i in range(4)]
    kq = pm.dieu_kien_dong_lai(ts + cho, ro)
    assert kq["n_cam_ket"] == 4, kq
    assert "4 lệnh đã cam kết" in kq["ly_do"], kq["ly_do"]
    print(f"PASS  4 lệnh PENDING -> đếm được và nói ra")


def test_lenh_dang_mo_cung_tinh_la_cam_ket():
    ts, ro = _so(200, -3.0, sd=8.0)
    kq = pm.dieu_kien_dong_lai(ts + [_lenh(9100, "OPEN")], ro)
    assert kq["n_cam_ket"] == 1, kq
    print("PASS  lệnh OPEN cũng tính là đã cam kết")


# ── 5. Ngưỡng suy từ lực phát hiện, không gõ tay ─────────────────────

def test_nguong_SUY_TU_luc_phat_hien():
    assert pm.N_DAY_DU == pm.co_mau_cho_luc(), (
        f"N_DAY_DU={pm.N_DAY_DU} nhưng công thức lực phát hiện cho "
        f"{pm.co_mau_cho_luc()} — ngưỡng phải suy ra, không gõ tay")
    print(f"PASS  N_DAY_DU {pm.N_DAY_DU} = co_mau_cho_luc()")


def test_co_mau_lon_hon_khi_hieu_ung_nho_hon():
    """Nếu hàm này là hằng số trá hình thì phép kiểm trên vô nghĩa."""
    assert pm.co_mau_cho_luc(-0.5) > pm.co_mau_cho_luc(-0.927)
    assert pm.co_mau_cho_luc(-2.0) < pm.co_mau_cho_luc(-0.927)
    assert pm.co_mau_cho_luc(luc=0.90) > pm.co_mau_cho_luc(luc=0.80)
    print(f"PASS  hiệu ứng −0,5% cần {pm.co_mau_cho_luc(-0.5)} lệnh, "
          f"−2,0% cần {pm.co_mau_cho_luc(-2.0)}")


def test_bien_HAI_rong_hon_bien_loi_the():
    """Biên hại bị nhìn LIÊN TỤC mỗi lượt quét, nên phải nới rộng hơn."""
    assert pm.Z_BIEN_HAI > pm.Z_LOI_THE
    print(f"PASS  z hại {pm.Z_BIEN_HAI} > z lợi thế {pm.Z_LOI_THE:.3f}")


def test_vs_benchmark_z_mac_dinh_KHONG_doi_ket_qua_cu():
    """Thêm tham số `z` không được đổi một chữ số nào ở chỗ gọi cũ."""
    ts, ro = _so(200, -1.0, sd=8.0)
    a = pm.vs_benchmark(ts, ro)
    b = pm.vs_benchmark(ts, ro, z=1.959964)
    assert a["ci"] == b["ci"], (a["ci"], b["ci"])
    rong = pm.vs_benchmark(ts, ro, z=pm.Z_BIEN_HAI)
    assert rong["ci"][0] < a["ci"][0] and rong["ci"][1] > a["ci"][1]
    print(f"PASS  z mặc định giữ nguyên {a['ci']} · z=2,3 rộng hơn {rong['ci']}")


if __name__ == "__main__":
    for ten, ham in sorted(globals().items()):
        if ten.startswith("test_"):
            ham()
