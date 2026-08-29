"""Điều kiện dừng phải ĐỔI TRẠNG THÁI, không chỉ thêm một dòng chữ.

VÌ SAO CÓ FILE NÀY
──────────────────
Nguyên nhân nặng nhất của cổng C5 (xem `docs/STATE.md` — "GỐC RỄ CỦA
CỔNG C5") là điều kiện dừng **không có ai thi hành**:
`dieu_kien_dong_lai()` chỉ được gọi bên trong `paper_metrics.report()`,
một hàm nối chuỗi, và khi đạt nó thêm đúng một CÂU VĂN vào một tệp zip
lưu 14 ngày. Kể cả nếu điều kiện có lực phát hiện 100%, nó vẫn không
đóng được cổng.

File này khoá bốn thứ, và thứ tự quan trọng:
  1. đạt điều kiện ⇒ cờ THẬT SỰ đổi giá trị (không phải trả về một chuỗi);
  2. chưa đạt ⇒ KHÔNG đụng vào cờ (một hàng rào hay tự sập thì bị gỡ);
  3. chỗ gọi nằm TRƯỚC vòng quét (sau vòng quét là muộn đúng một phiên);
  4. chuông C5 kêu đúng lúc — và KHÔNG kêu khi cổng đã đóng.
"""
import ast
import datetime as dt
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(GOC / "tools"))

import paper_trading as pt        # noqa: E402
import run_daily as rd            # noqa: E402
from paper_trading import Trade   # noqa: E402
import canh_cong_c5              # noqa: E402

MOC = dt.datetime(2026, 8, 7, 14, 41).timestamp()


def _ngay(n: int) -> str:
    return (dt.date(2024, 1, 5) + dt.timedelta(days=n)).isoformat()


def _lenh(i: int, loi_nhuan: float) -> Trade:
    """Lệnh tiến-về-trước đã đóng: ghi cách nhau một ngày, nên không thành lô."""
    ngay = _ngay(i * 3)
    return Trade(
        id=i, symbol="FPT", signal_date=ngay, entry_date=ngay,
        entry_price=100.0, exit_date=ngay,
        exit_price=100.0 * (1 + loi_nhuan / 100),
        exit_reason="STOP_LOSS", stop_loss=93.0, take_profit=110.0,
        size_pct=10.0, entry_score=62, status="CLOSED",
        created_at=MOC + 86400 * (i + 1))


def _so_lo_nang() -> list[Trade]:
    """80 lệnh −8%/lệnh: KTC loại được số 0 ⇒ điều kiện ĐẠT."""
    return [_lenh(i, -8.0 + (i % 5) * 0.4) for i in range(80)]


def _so_chua_du() -> list[Trade]:
    """30 lệnh, lỗ nặng nhưng chưa đủ mẫu ⇒ điều kiện KHÔNG đạt."""
    return [_lenh(i, -8.0) for i in range(30)]


# ── 1. Đạt điều kiện thì cờ THẬT SỰ đổi ──────────────────────────────

def test_dat_dieu_kien_thi_TAT_co():
    ghi = []
    da_dong, thong_diep = rd.thi_hanh_dieu_kien_dung(_so_lo_nang(), ghi.append)
    assert da_dong is True, thong_diep
    assert ghi == [False], f"cờ được đặt thành {ghi}, phải là [False]"
    assert "ĐÃ ĐẠT" in thong_diep, thong_diep
    print(f"PASS  đạt -> đặt cờ {ghi} · {thong_diep[:48]}…")


def test_co_thuc_su_doi_gia_tri_tren_module():
    """Chứng minh bằng CHẠY, không bằng đọc: cờ thật đổi từ True sang False."""
    cu = pt.CHO_PHEP_MO_LENH_MOI
    try:
        pt.CHO_PHEP_MO_LENH_MOI = True
        rd.thi_hanh_dieu_kien_dung(
            _so_lo_nang(),
            lambda v: setattr(pt, "CHO_PHEP_MO_LENH_MOI", v))
        assert pt.CHO_PHEP_MO_LENH_MOI is False
    finally:
        pt.CHO_PHEP_MO_LENH_MOI = cu
    print("PASS  cờ trên module đổi True -> False khi điều kiện đạt")


# ── 2. Chưa đạt thì KHÔNG đụng vào cờ ────────────────────────────────

def test_chua_du_mau_thi_KHONG_dung_vao_co():
    ghi = []
    da_dong, thong_diep = rd.thi_hanh_dieu_kien_dung(_so_chua_du(), ghi.append)
    assert da_dong is False and ghi == [], f"đã đụng vào cờ: {ghi}"
    print(f"PASS  chưa đủ mẫu -> không đụng cờ · {thong_diep[:48]}…")


def test_dang_lai_thi_KHONG_dung_vao_co():
    ghi = []
    da_dong, _ = rd.thi_hanh_dieu_kien_dung(
        [_lenh(i, +6.0) for i in range(80)], ghi.append)
    assert da_dong is False and ghi == []
    print("PASS  đang lãi -> không đụng cờ")


def test_so_rong_thi_KHONG_dung_vao_co():
    ghi = []
    assert rd.thi_hanh_dieu_kien_dung([], ghi.append)[0] is False
    assert ghi == []
    print("PASS  sổ rỗng -> không đụng cờ")


# ── 3. Chỗ gọi nằm TRƯỚC vòng quét ───────────────────────────────────

def _ham(ten: str) -> ast.FunctionDef:
    cay = ast.parse((GOC / "run_daily.py").read_text(encoding="utf-8"))
    for n in ast.walk(cay):
        if isinstance(n, ast.FunctionDef) and n.name == ten:
            return n
    raise AssertionError(f"không tìm thấy hàm {ten}")


def test_goi_dung_mot_lan_va_TRUOC_vong_quet():
    """Thi hành sau vòng quét là muộn đúng một phiên — phiên không được có."""
    ham = _ham("execute_daily_scan")
    goi = [n for n in ast.walk(ham)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
           and n.func.id == "thi_hanh_dieu_kien_dung"]
    assert len(goi) == 1, f"gọi {len(goi)} lần, phải đúng 1"

    vong = [n for n in ast.walk(ham)
            if isinstance(n, ast.For) and isinstance(n.iter, ast.Call)
            and isinstance(n.iter.func, ast.Name)
            and n.iter.func.id == "enumerate"]
    assert vong, "không tìm thấy vòng quét rổ"
    assert goi[0].lineno < min(v.lineno for v in vong), (
        f"thi hành ở dòng {goi[0].lineno}, vòng quét bắt đầu ở dòng "
        f"{min(v.lineno for v in vong)} — thi hành phải đứng TRƯỚC")
    print(f"PASS  thi hành dòng {goi[0].lineno} < vòng quét dòng "
          f"{min(v.lineno for v in vong)}")


def test_ham_dat_co_that_su_gan_vao_co_C5():
    """Truyền vào một hàm đặt cờ rỗng thì test trên vẫn xanh mà đời vẫn hỏng."""
    ham = _ham("execute_daily_scan")
    goi = [n for n in ast.walk(ham)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
           and n.func.id == "thi_hanh_dieu_kien_dung"][0]
    nguon = ast.dump(goi.args[1])
    assert "setattr" in nguon, nguon
    assert "CHO_PHEP_MO_LENH_MOI" in nguon, nguon
    print("PASS  hàm đặt cờ gán thật vào CHO_PHEP_MO_LENH_MOI")


# ── 4. Chuông C5 kêu đúng lúc ────────────────────────────────────────

def test_chuong_kEU_khi_dat_ma_cong_van_MO():
    ma, td = canh_cong_c5.kiem(_so_lo_nang(), cong_dang_mo=True)
    assert ma == 1 and "VẪN MỞ" in td, td
    print(f"PASS  đạt + cổng mở -> kêu ({ma})")


def test_chuong_IM_khi_dat_nhung_cong_da_DONG():
    """Kêu khi đã đúng trạng thái là dạy người ta bỏ qua chuông."""
    ma, td = canh_cong_c5.kiem(_so_lo_nang(), cong_dang_mo=False)
    assert ma == 0 and "ĐÃ ĐÓNG" in td, td
    print(f"PASS  đạt + cổng đóng -> im ({ma})")


def test_chuong_IM_khi_chua_dat():
    for mo in (True, False):
        ma, td = canh_cong_c5.kiem(_so_chua_du(), cong_dang_mo=mo)
        assert ma == 0, (mo, td)
    print("PASS  chưa đạt -> im, dù cổng mở hay đóng")


if __name__ == "__main__":
    for ten, ham in sorted(globals().items()):
        if ten.startswith("test_"):
            ham()
