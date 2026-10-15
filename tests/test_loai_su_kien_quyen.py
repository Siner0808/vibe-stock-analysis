"""BƯỚC 182 (Q14, mốc D2) — LOẠI lệnh có sự kiện quyền trong lúc giữ khỏi mẫu của điều kiện dừng.

Người dùng chốt 10/10/2026 (`docs/QUYET-DINH-CHO.md` Q14): *"Đánh dấu + loại khỏi
điều kiện dừng (Recommended)"*. BƯỚC 176 đánh dấu; bài này loại. Ca gốc: lệnh HDB #122
vào 28/09 giá 27.950, đóng 09/10 `STOP_LOSS` −23,18% — lỗ GIẢ vì sổ lưu giá chưa điều
chỉnh còn nguồn điều chỉnh LÙI sau sự kiện quyền.

Năm điểm thiết kế mà file này khoá:
  1. Loại theo NHÃN CỦA MÁY (`SU_KIEN_TRONG_LUC_GIU`), không theo lãi/lỗ; `KHONG_KIEM_DUOC`
     · `LECH_KHAC` · `SACH` ở lại; không tải được nến ⇒ ở lại.
  2. Không đổi ngưỡng nào (`N_TOI_THIEU` · `N_DAY_DU` · `Z_*` · `MUC_BAT_LOI`).
  3. `dieu_kien_dong_lai(trades, benchmark, loai_tru=None)` thuần; `None` = bản cũ; kết quả
     trả thêm `n_loai` · `id_loai` và `ly_do` nói ra số lệnh bị loại; loại TRƯỚC `vs_benchmark`.
  4. Người gọi tính tập loại ở MỘT chỗ (`nen_su_kien_quyen.tap_loai`); `run_daily` và
     `tools/canh_cong_c5.py` cùng gọi; tải hỏng ⇒ không loại gì + `::warning::`.
  5. Chiều thiên lệch (loại lệnh lỗ giả chỉ làm alpha ĐẸP LÊN) nằm trong docstring.

Số TÍNH TAY ở chú thích từng ca. Đột biến (bộ ở `docs/STATE.md` BƯỚC 182): loại cả
`KHONG_KIEM_DUOC` · loại cả `LECH_KHAC` · loại SAU `vs_benchmark` · `ly_do` không nêu
số lệnh loại · tải hỏng ⇒ loại hết · đổi `N_TOI_THIEU`; phát đầu: dựng lại ca HDB.
"""
from __future__ import annotations

import ast
import datetime as dt
import sys
from pathlib import Path

import pandas as pd
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))
sys.path.insert(0, str(GOC))

import canh_cong_c5  # noqa: E402
import duyet_repo  # noqa: E402
import nen_su_kien_quyen as nsk  # noqa: E402
import paper_metrics as pm  # noqa: E402
import run_daily as rd  # noqa: E402
import soi_su_kien_quyen as cli  # noqa: E402
import su_kien_quyen as skq  # noqa: E402
from paper_trading import Trade  # noqa: E402

MOC = dt.datetime(2026, 8, 7, 14, 41).timestamp()
V, R = "2026-09-28", "2026-10-09"


def _ngay(n: int) -> str:
    return (dt.date(2024, 1, 5) + dt.timedelta(days=n)).isoformat()


def _lenh(i: int, gia_vao: float = 100.0, gia_ra: float = 103.0,
          trang_thai: str = "CLOSED", ma: str = "FPT",
          tien_ve_truoc: bool = True) -> Trade:
    """Lệnh tiến-về-trước: ghi cách nhau một ngày nên không thành lô.

    `tien_ve_truoc=False` bỏ `created_at` -> `lenh_tien_ve_truoc` loại nó khỏi mẫu."""
    vao, ra = _ngay(i * 3), _ngay(i * 3 + 1)
    dong = trang_thai == "CLOSED"
    return Trade(
        id=i, symbol=ma, signal_date=vao, entry_date=vao, entry_price=gia_vao,
        exit_date=ra if dong else None, exit_price=gia_ra if dong else None,
        exit_reason="STOP_LOSS" if dong else None, stop_loss=93.0,
        take_profit=110.0, size_pct=10.0, entry_score=62, status=trang_thai,
        created_at=(MOC + 86400 * (i + 1)) if tien_ve_truoc else None)


# ─────────────────────────────────────────────────────────────────────
# 1. Số TÍNH TAY: ca HDB trong mẫu 113 lệnh
#
# 113 lệnh sạch, vào 100 ra 103: lãi gộp 3,00%, phí vòng 0,46% -> net 2,54%.
# Chuẩn đặt bằng SỐ: lệnh chẵn bench 1,54 -> alpha +1,00; lệnh lẻ bench 3,54 -> −1,00.
# ids 0..112: 57 chẵn, 56 lẻ -> alpha trung bình = (57 − 56) / 113 = 1/113 = +0,0088496.
# Lệnh HDB (#9000): vào 27.950 ra 21.470: gộp = −6.480 / 27.950 = −23,18426%; net =
# −23,18426 − 0,46 = −23,64426%; chuẩn 0,00 -> alpha −23,64426.
#   KHÔNG loại: n = 114, alpha = (1 − 23,64426) / 114 = −22,64426 / 114 = −0,198634
#   CÓ loại   : n = 113, alpha = 1 / 113 = +0,008850
# ─────────────────────────────────────────────────────────────────────
ID_HDB = 9000


def _so_ca_hdb():
    ts, ro = [], {}
    for i in range(113):
        t = _lenh(i)
        ts.append(t)
        ro[(t.entry_date, t.exit_date)] = 1.54 if i % 2 == 0 else 3.54
    hdb = _lenh(ID_HDB, 27950.0, 21470.0, ma="HDB")
    ts.append(hdb)
    ro[(hdb.entry_date, hdb.exit_date)] = 0.0
    return ts, ro


def test_a_loai_lenh_dang_HDB_n_giam_dung_1_alpha_dung_so_tinh_tay():
    ts, ro = _so_ca_hdb()
    cu = pm.dieu_kien_dong_lai(ts, ro)
    assert cu["so_lenh"] == 114
    assert cu["alpha"] == pytest.approx(-0.198634, abs=1e-6)
    assert cu["n_loai"] == 0 and cu["id_loai"] == []
    assert "LOẠI" not in cu["ly_do"]

    moi = pm.dieu_kien_dong_lai(ts, ro, {ID_HDB: "sự kiện quyền"})
    assert moi["so_lenh"] == 113                           # giảm ĐÚNG 1
    assert moi["alpha"] == pytest.approx(1 / 113, abs=1e-9)  # 0,0088496
    assert moi["n_loai"] == 1 and moi["id_loai"] == [ID_HDB]
    assert f"#{ID_HDB}" in moi["ly_do"]
    assert "1 lệnh LOẠI vì sự kiện quyền trong lúc giữ" in moi["ly_do"]
    # tập, danh sách hay ánh xạ đều là "tập id": cùng kết quả
    assert pm.dieu_kien_dong_lai(ts, ro, {ID_HDB}) == moi
    assert pm.dieu_kien_dong_lai(ts, ro, [ID_HDB]) == moi


def test_a2_dung_o_N_TOI_THIEU_lenh_bi_loai_KHONG_duoc_dem_vao_mau():
    """113 lệnh đã đóng, 1 bị loại: n = 112 < N_TOI_THIEU = 113 -> chưa đủ để kết luận.

    Không loại: n = 113 chạm ngưỡng nên được đánh giá; alpha mỗi lệnh −3,00 đồng nhất
    -> khoảng tin cậy suy biến ở −3, cận trên < 0 -> ĐÓNG. Loại 1 lệnh: 112 < 113."""
    ts = [_lenh(i, 100.0, 92.0 + (i % 5) * 0.4) for i in range(113)]
    ro = {(t.entry_date, t.exit_date): t.net_return_pct() + 3.0 for t in ts}
    khong = pm.dieu_kien_dong_lai(ts, ro)
    assert khong["so_lenh"] == 113 and khong["dat"] is True
    co = pm.dieu_kien_dong_lai(ts, ro, {7})
    assert co["so_lenh"] == 112 and co["dat"] is False
    assert "mới 112/113" in co["ly_do"] and "#7" in co["ly_do"]
    assert co["n_loai"] == 1 and co["id_loai"] == [7]


def test_a3_ly_do_ke_ca_hai_lenh_bi_loai_theo_thu_tu_id():
    ts, ro = _so_ca_hdb()
    kq = pm.dieu_kien_dong_lai(ts, ro, {ID_HDB, 5})
    assert kq["id_loai"] == [5, ID_HDB] and kq["n_loai"] == 2
    assert "2 lệnh LOẠI vì sự kiện quyền trong lúc giữ: #5, #9000" in kq["ly_do"]


def test_a4_thieu_ro_chuan_ly_do_van_noi_ra_lenh_bi_loai():
    ts, _ = _so_ca_hdb()
    kq = pm.dieu_kien_dong_lai(ts, None, {ID_HDB})
    assert kq["do_duoc"] is False and kq["n_loai"] == 1
    assert "#9000" in kq["ly_do"] and "ALPHA" in kq["ly_do"]


# ── (d) loai_tru rỗng / None = bản cũ, so cả dict ────────────────────

def test_d_loai_tru_None_rong_hoac_khong_trung_lenh_nao_cho_ra_CUNG_MOT_ket_qua():
    ts, ro = _so_ca_hdb()
    goc = pm.dieu_kien_dong_lai(ts, ro)
    for ngoai in (None, {}, set(), [], {123456: "id không có trong sổ"}):
        assert pm.dieu_kien_dong_lai(ts, ro, ngoai) == goc, ngoai
    # và bằng đúng thứ `vs_benchmark` cho trên toàn bộ nhóm đã đóng (khung cũ)
    b = pm.vs_benchmark(ts, ro, z=pm.Z_BIEN_HAI)
    assert goc["so_lenh"] == b["n"] and goc["alpha"] == b["alpha"]
    assert goc["ci"] == b["ci"]
    # khoá chính bản cũ còn nguyên; chỉ THÊM n_loai/id_loai
    assert {"so_lenh", "n_cam_ket", "alpha", "ci", "bo_qua", "do_duoc", "dat",
            "ly_do"} <= set(goc)
    assert set(goc) - {"so_lenh", "n_cam_ket", "alpha", "ci", "bo_qua", "do_duoc",
                       "dat", "ly_do"} == {"n_loai", "id_loai"}


# ── (f) id ngoài nhóm tiến-về-trước đã đóng không ảnh hưởng ──────────

def test_f_id_cua_lenh_mo_lenh_mo_phong_va_id_la_khong_anh_huong():
    ts, ro = _so_ca_hdb()
    mo = _lenh(8001, trang_thai="OPEN", ma="HDB")
    mo_phong = _lenh(8002, 27950.0, 21470.0, ma="HDB", tien_ve_truoc=False)
    tat_ca = ts + [mo, mo_phong]
    ro[(mo_phong.entry_date, mo_phong.exit_date)] = 0.0
    goc = pm.dieu_kien_dong_lai(tat_ca, ro)
    # lệnh mô phỏng không có created_at -> không thuộc nhóm tiến-về-trước; lệnh mở thì
    # chưa đóng: gọi tên chúng trong loai_tru không đổi một chữ số nào.
    kq = pm.dieu_kien_dong_lai(tat_ca, ro, {8001, 8002, 424242})
    assert kq == goc
    assert kq["n_loai"] == 0 and kq["id_loai"] == []
    assert kq["n_cam_ket"] == 1                      # lệnh mở vẫn được đếm là cam kết


# ─────────────────────────────────────────────────────────────────────
# 2. Đi hết đường: nến giả -> nhãn máy -> tập loại -> điều kiện dừng
# ─────────────────────────────────────────────────────────────────────

def _bang(mo, thap, cao):
    """Bảng OHLCV NGHÌN đồng (như vnstock) cho hai ngày V và R."""
    return pd.DataFrame({"time": [V, R], "open": [mo[0] / 1000, mo[1] / 1000],
                         "low": [thap[0] / 1000, thap[1] / 1000],
                         "high": [cao[0] / 1000, cao[1] / 1000],
                         "close": [mo[0] / 1000, mo[1] / 1000]})


BANG = {
    "HDB": _bang((21500, 20800), (21000, 20800), (22000, 22000)),   # (c) f_vào 1,3 · SỰ KIỆN
    "AAA": _bang((20000, 20500), (19600, 20500), (20400, 21500)),   # (a) SẠCH
    "BBB": _bang((20000, 20000), (19600, 20000), (20400, 22000)),   # (d) LỆCH KHÁC
}


def _tai_gia(goi):
    def tai(ma, tu, den):
        goi.append((ma, tu, den))
        if ma not in BANG:
            return "FAILED", None, 1.0                  # ZZZ: tải hỏng
        return "OK", BANG[ma], 1000.0
    return tai


def _l(id, ma, gia_vao, gia_ra, trang_thai="CLOSED", tien_ve_truoc=True):
    dong = trang_thai in ("CLOSED", "CLOSING")        # CLOSING mang sẵn giá/ngày ra nhưng CHƯA đóng
    return Trade(
        id=id, symbol=ma, signal_date="2026-09-25", entry_date=V,
        entry_price=gia_vao, exit_date=R if dong else None,
        exit_price=gia_ra if dong else None,
        exit_reason="STOP_LOSS" if dong else None, stop_loss=1.0, take_profit=2.0,
        size_pct=10.0, entry_score=70, status=trang_thai,
        created_at=(1.8e9 + 86400 * id) if tien_ve_truoc else None)


def _so_giay():
    return [_l(1, "HDB", 27950, 21000),                         # nhãn SU_KIEN -> LOẠI
            _l(2, "AAA", 20000, 21000),                         # nhãn SACH
            _l(3, "BBB", 25000, 30000),                         # nhãn LECH_KHAC
            _l(4, "ZZZ", 5000, 5200),                           # tải hỏng -> KHONG_KIEM_DUOC
            _l(5, "HDB", 27950, None, "OPEN"),                  # còn MỞ: không bao giờ loại
            _l(7, "HDB", 27950, 21000, "CLOSING"),              # đang đóng, đã có giá ra: vẫn là MỞ
            _l(6, "HDB", 27950, 21000, tien_ve_truoc=False)]    # mô phỏng: ngoài nhóm


def test_b_c_tap_loai_chi_co_nhan_SU_KIEN_con_KHONG_KIEM_DUOC_va_LECH_KHAC_o_lai():
    goi: list = []
    kq = nsk.tap_loai(_so_giay(), hom_nay=R, tai=_tai_gia(goi))
    assert list(kq.loai) == [1]                                   # chỉ HDB #1
    assert "GIỮA" in kq.loai[1]
    assert kq.n_xet == 4                                          # #1 #2 #3 #4
    assert kq.thieu == ("ZZZ",)
    assert kq.loi == ""
    assert len(kq.canh_bao) == 1 and "ZZZ" in kq.canh_bao[0]
    assert "ở lại mẫu" in kq.canh_bao[0]
    # mỗi mã MỘT lần; mã của lệnh mở/mô phỏng không tải thêm; ngày bắt đầu = 28/09 − 10
    assert sorted(m for m, _, _ in goi) == ["AAA", "BBB", "HDB", "ZZZ"]
    assert {(tu, den) for _, tu, den in goi} == {("2026-09-18", R)}


def test_b_c_dieu_kien_dung_dem_dung_lenh_o_lai():
    ts = _so_giay()
    ro = {(V, R): 0.0}
    ket = nsk.tap_loai(ts, hom_nay=R, tai=_tai_gia([]))
    cu = pm.dieu_kien_dong_lai(ts, ro)
    moi = pm.dieu_kien_dong_lai(ts, ro, ket.loai)
    assert cu["so_lenh"] == 4                                     # #1 #2 #3 #4
    assert moi["so_lenh"] == 3 and moi["id_loai"] == [1]          # #2 SẠCH #3 LỆCH #4 KHÔNG KIỂM
    assert moi["n_cam_ket"] == 2                                  # #5 OPEN và #7 CLOSING: còn mở


def test_e_tai_hong_ca_luot_KHONG_loai_gi_va_canh_bao():
    """`pham_vi_tai` nổ giữa chừng: tập loại rỗng, có cảnh báo, hàm KHÔNG ném lỗi."""
    def no(*a, **k):
        raise RuntimeError("hết mạng")
    cu = skq.pham_vi_tai
    skq.pham_vi_tai = no
    try:
        kq = nsk.tap_loai(_so_giay(), hom_nay=R, tai=_tai_gia([]))
    finally:
        skq.pham_vi_tai = cu
    assert kq.loai == {} and "RuntimeError" in kq.loi
    assert len(kq.canh_bao) == 1 and "MẪU ĐẦY ĐỦ" in kq.canh_bao[0]


def test_e2_tai_tung_ma_hong_het_cung_KHONG_loai_gi():
    def hong(ma, tu, den):
        raise ConnectionError("rớt mạng")
    kq = nsk.tap_loai(_so_giay(), hom_nay=R, tai=hong)
    assert kq.loai == {}
    assert sorted(kq.thieu) == ["AAA", "BBB", "HDB", "ZZZ"]
    assert "4/4 mã" in kq.canh_bao[0]


def test_khong_co_lenh_tien_ve_truoc_da_dong_thi_KHONG_tai_gi():
    goi: list = []
    ts = [_l(5, "HDB", 27950, None, "OPEN"),
          _l(6, "HDB", 27950, 21000, tien_ve_truoc=False)]
    kq = nsk.tap_loai(ts, hom_nay=R, tai=_tai_gia(goi))
    assert kq.loai == {} and goi == [] and kq.canh_bao == () and kq.n_xet == 0
    assert nsk.tap_loai([], hom_nay=R, tai=_tai_gia(goi)).loai == {}


# ── (e) ở mức run_daily: cờ vẫn được đặt đúng như bản cũ cho cùng đầu vào ──

def _so_lo_nang():
    ts = [_lenh(i, 100.0, 100.0 * (1 + (-8.0 + (i % 5) * 0.4) / 100))
          for i in range(200)]
    return ts, {(t.entry_date, t.exit_date): t.net_return_pct() + 3.0 for t in ts}


def test_e3_run_daily_tai_hong_co_van_duoc_dat_nhu_ban_cu(capsys):
    ts, ro = _so_lo_nang()

    def hong(ma, tu, den):
        raise ConnectionError("rớt mạng")
    loai = rd.tinh_loai_tru_c5(ts, tai=hong, hom_nay=R)
    ra = capsys.readouterr().out
    assert loai == {}
    assert "::warning::" in ra and "FPT" in ra and "::error::" not in ra
    ghi_moi, ghi_cu = [], []
    moi = rd.thi_hanh_dieu_kien_dung(ts, ghi_moi.append, ro, loai)
    cu = rd.thi_hanh_dieu_kien_dung(ts, ghi_cu.append, ro)
    assert moi == cu and moi[0] is True
    assert ghi_moi == ghi_cu == [False]


def test_e4_run_daily_ghi_tom_tat_khi_co_GITHUB_STEP_SUMMARY(tmp_path, monkeypatch, capsys):
    f = tmp_path / "tom_tat.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(f))
    rd.tinh_loai_tru_c5(_so_giay(), tai=_tai_gia([]), hom_nay=R)
    capsys.readouterr()
    assert "ZZZ" in f.read_text(encoding="utf-8")


def test_e5_run_daily_in_dong_tom_tat_loai(capsys):
    loai = rd.tinh_loai_tru_c5(_so_giay(), tai=_tai_gia([]), hom_nay=R)
    ra = capsys.readouterr().out
    assert list(loai) == [1]
    assert "soi 4 lệnh tiến-về-trước đã đóng, LOẠI 1 khỏi điều kiện dừng: #1" in ra


def test_run_daily_truyen_loai_tru_cho_dieu_kien_dong_lai():
    ts, ro = _so_ca_hdb()
    ghi: list = []
    da_dong, td = rd.thi_hanh_dieu_kien_dung(ts, ghi.append, ro, {ID_HDB: "x"})
    assert da_dong is False and ghi == []                         # alpha ≈ 0: chưa đạt, không đụng cờ
    assert f"#{ID_HDB}" in td and "1 lệnh LOẠI" in td             # ly_do nói ra lệnh bị loại


# ── báo cáo phiên nói CÙNG điều kiện với chỗ thi hành ────────────────

def test_report_in_dong_cong_C5_voi_cung_tap_loai():
    """`report()` in "Cổng C5: …" mỗi phiên; nếu nó không biết tập loại thì báo cáo nói
    một đằng (113+1 lệnh) còn điều kiện dừng làm một nẻo (113 lệnh)."""
    ts, ro = _so_ca_hdb()
    co = pm.report(ts, benchmark=ro, loai_tru={ID_HDB: "x"})
    khong = pm.report(ts, benchmark=ro)
    dong_co = [d for d in co.splitlines() if d.startswith("Cổng C5")]
    dong_khong = [d for d in khong.splitlines() if d.startswith("Cổng C5")]
    assert len(dong_co) == len(dong_khong) == 1
    assert "1 lệnh LOẠI vì sự kiện quyền trong lúc giữ: #9000" in dong_co[0]
    assert "LOẠI" not in dong_khong[0]


# ── chuông C5 ────────────────────────────────────────────────────────

def test_chuong_kiem_truyen_loai_tru_va_noi_ra_trong_thong_diep():
    ts, ro = _so_ca_hdb()
    ma, td = canh_cong_c5.kiem(ts, True, ro, {ID_HDB: "x"})
    assert ma == 0 and f"#{ID_HDB}" in td and "1 lệnh LOẠI" in td
    ma0, td0 = canh_cong_c5.kiem(ts, True, ro)
    assert "LOẠI" not in td0


# ── CLI và điều kiện dừng nói CÙNG một danh sách ─────────────────────

class _SoGia:
    def __init__(self, trades):
        self._t = trades

    def all_trades(self):
        return list(self._t)


def test_CLI_in_dung_danh_sach_ma_dieu_kien_dung_loai(capsys):
    ts = _so_giay()
    ma_thoat = cli.main(keo=lambda: (_SoGia(ts), {}), tai=_tai_gia([]), hom_nay=R)
    ra = capsys.readouterr().out
    ket = nsk.tap_loai(ts, hom_nay=R, tai=_tai_gia([]))
    assert ma_thoat == 1
    gon = " ".join(ra.split())
    assert "ĐIỀU KIỆN DỪNG LOẠI KHỎI MẪU (tiến-về-trước, đã đóng, SU_KIEN_TRONG_LUC_GIU): 1 lệnh: #1" in gon
    assert sorted(ket.loai) == [1]


# ─────────────────────────────────────────────────────────────────────
# 3. Ngưỡng KHÔNG đổi (điểm thiết kế 2)
# ─────────────────────────────────────────────────────────────────────

def test_nguong_va_z_giu_nguyen_gia_tri_va_cach_suy_ra():
    assert (pm.N_TOI_THIEU, pm.N_DAY_DU, pm.Z_BIEN_HAI, pm.Z_LOI_THE,
            pm.MUC_BAT_LOI) == (113, 451, 2.30, 1.959964, -0.920)
    cay = ast.parse((GOC / "paper_metrics.py").read_text(encoding="utf-8"))
    gan = {t.id: ast.unparse(n.value) for n in ast.walk(cay)
           if isinstance(n, ast.Assign) for t in n.targets if isinstance(t, ast.Name)}
    assert gan["N_TOI_THIEU"] == "round(N_DAY_DU / 4)"            # vẫn SUY RA
    assert gan["N_DAY_DU"] == "451"                               # khớp co_mau_cho_luc (gác cũ)


# ─────────────────────────────────────────────────────────────────────
# 4. AST: hình dạng của phép loại và của dây nối
# ─────────────────────────────────────────────────────────────────────

def _cay(duong):
    return ast.parse((GOC / duong).read_text(encoding="utf-8"))


def _ham(cay, ten):
    cac = [n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == ten]
    assert len(cac) == 1, f"{ten}: {len(cac)} định nghĩa"
    return cac[0]


def _ten_goi(n):
    f = n.func
    return f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None


def test_ast_loai_xay_ra_TRUOC_vs_benchmark_va_vs_benchmark_chi_nhan_nhom_da_loai():
    ham = _ham(_cay("paper_metrics.py"), "dieu_kien_dong_lai")
    vs = [n for n in ast.walk(ham) if isinstance(n, ast.Call) and _ten_goi(n) == "vs_benchmark"]
    assert len(vs) == 2                                            # biên hại + biên lợi thế
    assert all(ast.unparse(c.args[0]) == "dong" for c in vs), [ast.unparse(c) for c in vs]
    gan = [n for n in ast.walk(ham) if isinstance(n, ast.Assign)
           and any(isinstance(t, ast.Name) and t.id == "dong" for t in n.targets)]
    assert len(gan) == 1 and isinstance(gan[0].value, ast.ListComp)
    nguon = ast.unparse(gan[0].value)
    assert nguon == "[t for t in dong_het if t.id not in loai]", nguon
    assert gan[0].lineno < min(c.lineno for c in vs)
    het = [n for n in ast.walk(ham) if isinstance(n, ast.Assign)
           and any(isinstance(t, ast.Name) and t.id == "dong_het" for t in n.targets)]
    assert len(het) == 1
    assert ast.unparse(het[0].value) == "[t for t in tien if t.status == 'CLOSED']"


def test_ast_loai_chi_nhan_nhan_SU_KIEN_TRONG_LUC_GIU_va_chi_trong_nhom_da_dong():
    ham = _ham(_cay("su_kien_quyen.py"), "id_su_kien_trong_luc_giu")
    tra = [n for n in ast.walk(ham) if isinstance(n, ast.Return)]
    assert len(tra) == 1
    nguon = ast.unparse(tra[0])                 # chỉ câu lệnh, không tính docstring
    assert "d.ket_qua.trang_thai == SU_KIEN_TRONG_LUC_GIU" in nguon
    for ten in ("KHONG_KIEM_DUOC", "LECH_KHAC", "SACH"):
        assert ten not in nguon, ten
    # lệnh mở không có đường vào: tham số `vi_the_mo` của soi_so là `()`
    goi = [n for n in ast.walk(ham) if isinstance(n, ast.Call) and _ten_goi(n) == "soi_so"]
    assert len(goi) == 1 and ast.unparse(goi[0].args[0]) == "()"


def test_ast_tap_loai_tai_hong_tra_tap_rong_khong_phai_tap_day_du():
    ham = _ham(_cay("nen_su_kien_quyen.py"), "tap_loai")
    xu = [h for n in ast.walk(ham) if isinstance(n, ast.Try) for h in n.handlers]
    assert len(xu) == 1
    tra = [n for n in ast.walk(xu[0]) if isinstance(n, ast.Return)]
    assert len(tra) == 1 and ast.unparse(tra[0].value).startswith("KetQuaLoai({},"), (
        "nhánh lỗi phải trả tập loại RỖNG")


def test_ast_run_daily_tinh_loai_truoc_thi_hanh_va_chuyen_cho_ca_thi_hanh_lan_report():
    ham = _ham(_cay("run_daily.py"), "execute_daily_scan")
    tinh = [n for n in ast.walk(ham) if isinstance(n, ast.Call)
            and _ten_goi(n) == "tinh_loai_tru_c5"]
    thi = [n for n in ast.walk(ham) if isinstance(n, ast.Call)
           and _ten_goi(n) == "thi_hanh_dieu_kien_dung"]
    rep = [n for n in ast.walk(ham) if isinstance(n, ast.Call) and _ten_goi(n) == "report"]
    assert len(tinh) == len(thi) == len(rep) == 1
    assert tinh[0].lineno < thi[0].lineno
    assert ast.unparse(thi[0].args[3]) == "_loai_c5"
    assert any(k.arg == "loai_tru" and ast.unparse(k.value) == "_loai_c5"
               for k in rep[0].keywords)
    gan = [n for n in ast.walk(ham) if isinstance(n, ast.Assign)
           and ast.unparse(n.targets[0]) == "_loai_c5"]
    assert len(gan) == 1 and ast.unparse(gan[0].value) == "tinh_loai_tru_c5(_so_truoc_quet)"


def test_ast_run_daily_canh_bao_di_bang_warning_khong_doi_ma_thoat():
    ham = _ham(_cay("run_daily.py"), "tinh_loai_tru_c5")
    chuoi = [n.value for n in ast.walk(ham) if isinstance(n, ast.Constant)
             and isinstance(n.value, str)]
    mau = [s for n in ast.walk(ham) if isinstance(n, ast.JoinedStr)
           for s in [c.value for c in n.values if isinstance(c, ast.Constant)]]
    assert any(s.startswith("::warning::") for s in mau)
    assert not any("::error::" in s for s in chuoi + mau)
    assert not [n for n in ast.walk(ham) if isinstance(n, ast.Call)
                and _ten_goi(n) in {"exit", "_exit"}]
    assert not [n for n in ast.walk(ham) if isinstance(n, ast.Raise)]


def test_ast_chuong_c5_goi_tap_loai_va_chuyen_loai_cho_kiem():
    cay = _cay("tools/canh_cong_c5.py")
    main = _ham(cay, "main")
    tap = [n for n in ast.walk(main) if isinstance(n, ast.Call) and _ten_goi(n) == "tap_loai"]
    kiem = [n for n in ast.walk(main) if isinstance(n, ast.Call) and _ten_goi(n) == "kiem"]
    assert len(tap) == 1 and len(kiem) == 1
    assert tap[0].lineno < kiem[0].lineno
    assert [ast.unparse(a) for a in kiem[0].args] == [
        "trades", "pt.CHO_PHEP_MO_LENH_MOI", "ro_chuan(trades)", "loai.loai"]
    # cảnh báo đi bằng ::warning:: (chuông chỉ đỏ vì điều kiện, không vì tải hỏng)
    mau = [c.value for n in ast.walk(main) if isinstance(n, ast.JoinedStr)
           for c in n.values if isinstance(c, ast.Constant)]
    assert any(s.startswith("::warning::") for s in mau)
    ham_kiem = _ham(cay, "kiem")
    dk = [n for n in ast.walk(ham_kiem) if isinstance(n, ast.Call)
          and _ten_goi(n) == "dieu_kien_dong_lai"]
    assert len(dk) == 1 and [ast.unparse(a) for a in dk[0].args] == [
        "trades", "benchmark", "loai_tru"]


def test_ast_thi_hanh_truyen_loai_tru_cho_dieu_kien_dong_lai():
    ham = _ham(_cay("run_daily.py"), "thi_hanh_dieu_kien_dung")
    dk = [n for n in ast.walk(ham) if isinstance(n, ast.Call)
          and _ten_goi(n) == "dieu_kien_dong_lai"]
    assert len(dk) == 1 and [ast.unparse(a) for a in dk[0].args] == [
        "trades", "benchmark", "loai_tru"]


def _nhap(cay):
    ra = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            ra |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            ra.add((n.module or "").split(".")[0])
    return ra


def _ma_nguon():
    bo = {"tests", ".venv", ".git", "node_modules", "__pycache__"}
    return [p for p in duyet_repo.duyet(GOC, "*.py")
            if not (set(p.relative_to(GOC).parts) & bo)]


def test_ast_chi_ba_noi_duoc_nhap_duong_noi_va_duong_do_khong_bao_gio():
    ai = {p.relative_to(GOC).as_posix() for p in _ma_nguon()
          if "nen_su_kien_quyen" in _nhap(ast.parse(p.read_text(encoding="utf-8")))}
    # BƯỚC 192: dụng cụ ĐO 26 (chỉ đọc) gọi `tai_nen` và `tap_loai` để đo ĐÚNG đường của
    # điều kiện dừng (đối chứng (iii) của bản ký); gác ghi riêng ở test_do26_*.
    assert ai == {"run_daily.py", "tools/canh_cong_c5.py", "tools/soi_su_kien_quyen.py",
                  "tools/do26_nguong_su_kien_quyen.py",
                  "tools/do27_su_kien_quyen_chieu_tien.py"}, sorted(ai)   # BƯỚC 194: ĐO 27
    for ten in ("paper_trading.py", "paper_runner.py", "paper_metrics.py", "master_agent.py",
                "analysis_agents.py", "debate_agents.py", "walkforward.py", "sheets_store.py",
                "google_sheets_sync.py", "ke_hoach_vao_lenh.py", "so_lenh_app.py",
                "so_bai_hoc.py", "ban_tin.py"):
        nhap = _nhap(_cay(ten))
        assert not ({"nen_su_kien_quyen", "su_kien_quyen"} & nhap), ten
    bt = [p for p in duyet_repo.duyet(GOC / "backtest", "*.py")
          if {"nen_su_kien_quyen", "su_kien_quyen"} & _nhap(ast.parse(p.read_text(encoding="utf-8")))]
    assert not bt, bt


def test_ast_duong_noi_khong_goi_ham_ghi():
    ghi = {"push", "write_all", "append_rows", "pull", "record_trade", "update_trade",
           "record_decision", "commit", "executemany", "executescript", "execute",
           "open", "write_text", "write_bytes", "unlink", "to_csv", "mkdir"}
    goi = {_ten_goi(n) for n in ast.walk(_cay("nen_su_kien_quyen.py")) if isinstance(n, ast.Call)}
    assert not (ghi & goi), sorted(ghi & goi)
    assert not ({"sqlite3", "gspread", "sheets_store", "google_sheets_sync",
                 "paper_trading"} & _nhap(_cay("nen_su_kien_quyen.py")))


# ─────────────────────────────────────────────────────────────────────
# 5. Q14 trong hàng đợi quyết định: phần LOẠI đã làm ở BƯỚC 182
# ─────────────────────────────────────────────────────────────────────

def test_Q14_ghi_phan_LOAI_da_lam_o_BUOC_182():
    import quyet_dinh_cho as qdc
    muc = {m.ma: m for m in qdc.doc_muc(qdc.TEP.read_text(encoding="utf-8"))}
    q14 = muc["Q14"]
    gop = "\n".join(q14.truong.values())
    assert "BƯỚC 182" in gop and "nen_su_kien_quyen" in gop
    assert "CHƯA làm" not in gop
    assert qdc.loi_so(list(muc.values())) == []
