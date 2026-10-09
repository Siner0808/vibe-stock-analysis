"""Gác của `so_bai_hoc.py` — sổ bài học, nhãn nguyên nhân (BƯỚC 167, mốc B3).

Sổ này CHỈ HIỆN: tính lúc xem từ các dòng nhật ký đã có, không ghi đi đâu,
không đổi lược đồ Sheets. Sáu điều đáng canh, mỗi điều một lỗi có hình dạng
ấy đã từng cắn dự án:

1. Hằng đẳng thức: tổng các phần = lãi ròng (nếu không, bảng nguyên nhân kể
   một câu chuyện không cộng lại thành kết quả).
2. Phí KHÔNG được nằm trong "riêng mã/tín hiệu": lệnh hoà vốn giá mà mất đúng
   phí không được gọi là tín hiệu sai.
3. Gap dùng đúng điều kiện của `hau_kiem_may` — MỘT công thức, đọc bằng AST.
4. Thiếu giá/rổ/ngành thì NÓI "chưa đủ dữ liệu", không đoán.
5. Ngưỡng "chưa đủ lệnh" SUY RA từ `paper_metrics.N_TOI_THIEU`, không gõ số.
6. Lược đồ `COT_NHAT_KY` không đổi một ký tự: `sheets_store` nổ khi lệch cột,
   và lượt quét thật trên Actions sẽ hỏng.
"""
import ast
import copy
import json
from pathlib import Path

import pandas as pd
import pytest

import data_quality
import nhat_ky_vi_sao as nk
import paper_metrics
import so_bai_hoc as sbh
from paper_trading import ExitReason, Status, Trade
from vn100_symbols import SECTOR_WATCHLIST

GOC = Path(__file__).resolve().parent.parent
PHI = paper_metrics.ROUND_TRIP_COST_PCT


def _dong(**thay):
    """Dòng nhật ký GIẢ đã đóng, dựng theo `COT_NHAT_KY` (không phải số của sổ thật)."""
    d = {c: None for c in nk.COT_NHAT_KY}
    d.update(
        trade_id=1, symbol="ACB", signal_date="2026-09-01", entry_date="2026-09-02",
        entry_price=100.0, stop_loss_ban_dau=95.0, rui_ro_pct=5.0, entry_score=65,
        diem_agent=json.dumps({"trend_score": 80.0, "volume_score": 60.0}),
        exit_date="2026-09-10", exit_price=90.0, exit_reason=ExitReason.STOP_LOSS,
        loi_nhuan_rong_pct=-10.46, ro_chuan_pct=1.0, alpha_pct=-11.46,
        trang_thai_lenh=Status.CLOSED)
    d.update(thay)
    return d


def _chuoi(ngay_gia):
    return {n: g for n, g in ngay_gia}


# Ngân hàng: ACB cùng ngành với STB VCB LPB BID CTG TCB HDB SHB MBB.
GIA_NGANH = {
    "STB": _chuoi([("2026-09-02", 100.0), ("2026-09-10", 98.0)]),     # −2%
    "VCB": _chuoi([("2026-09-02", 200.0), ("2026-09-10", 192.0)]),    # −4%
    "TCB": _chuoi([("2026-09-02", 50.0)]),                            # thiếu đầu ra
}


# ── 1. hằng đẳng thức ────────────────────────────────────────────────────

LUOI = [(l, r, n) for l in (-12.0, -3.0, -0.46, 0.0, 0.3, 4.0, 15.0)
        for r in (-5.0, 0.0, 2.5)
        for n in (None, -7.0, -1.0, 0.0, 3.0)]


@pytest.mark.parametrize("lnr, ro, nganh", LUOI)
def test_TONG_cac_phan_bang_loi_nhuan_rong(lnr, ro, nganh):
    p = sbh.phan_ra(lnr, ro, nganh)
    tong = sum(v for v in p.values() if v is not None)
    assert tong == pytest.approx(lnr, abs=1e-9)


def test_phan_ra_gia_tri_tay():
    # lãi ròng −3, thị trường −1, ngành −2,5 → ngành hơn/kém thị trường −1,5
    p = sbh.phan_ra(-3.0, -1.0, -2.5)
    assert p["thi_truong"] == -1.0
    assert p["nganh"] == pytest.approx(-1.5)
    assert p["chi_phi"] == pytest.approx(-PHI)
    assert p["rieng_ma"] == pytest.approx(-3.0 + PHI + 2.5)


def test_thieu_ngang_thi_nganh_nam_TRONG_rieng_ma():
    p = sbh.phan_ra(-3.0, -1.0, None)
    assert p["nganh"] is None
    assert p["rieng_ma"] == pytest.approx(-3.0 + PHI + 1.0)


@pytest.mark.parametrize("lnr, ro", [(None, 1.0), (1.0, None), (None, None)])
def test_THIEU_loi_nhuan_hoac_ro_chuan_thi_KHONG_phan_ra(lnr, ro):
    assert sbh.phan_ra(lnr, ro, 2.0) is None


def test_chi_phi_SUY_RA_tu_paper_metrics_khong_go_tay():
    cay = ast.parse((GOC / "so_bai_hoc.py").read_text(encoding="utf-8"))
    ham = next(n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == "phan_ra")
    thuoc = [n for n in ast.walk(ham)
             if isinstance(n, ast.Attribute) and n.attr == "ROUND_TRIP_COST_PCT"
             and getattr(n.value, "id", "") == "paper_metrics"]
    assert thuoc, "phan_ra phải đọc paper_metrics.ROUND_TRIP_COST_PCT"
    so = [n.value for n in ast.walk(ham) if isinstance(n, ast.Constant)
          and isinstance(n.value, float) and n.value not in (0.0, 100.0)]
    assert not so, f"phan_ra gõ tay số thực {so} — phải suy ra"


def test_chi_phi_khop_phi_THAT_cua_Trade():
    """Phần chi phí phải đúng bằng khoảng cách giữa lãi gộp và lãi ròng của Trade."""
    t = Trade(id=1, symbol="ACB", signal_date="2026-09-01", entry_date="2026-09-02",
              entry_price=100.0, exit_date="2026-09-10", exit_price=100.0,
              exit_reason=ExitReason.SIGNAL_REVERSED, stop_loss=95.0,
              take_profit=115.0, size_pct=20.0, entry_score=65, status=Status.CLOSED)
    assert t.gross_return_pct() - t.net_return_pct() == pytest.approx(PHI)


# ── 2. nguyên nhân chính ─────────────────────────────────────────────────

def test_LENH_THUA_nguyen_nhan_la_phan_AM_NHAT():
    p = {"thi_truong": -1.0, "nganh": -4.0, "rieng_ma": -2.0, "chi_phi": -0.46}
    assert sbh.nguyen_nhan_chinh(sbh.KET_QUA_THUA, p) == "nganh"


def test_LENH_THANG_nguyen_nhan_la_phan_DUONG_NHAT():
    p = {"thi_truong": 1.0, "nganh": 4.0, "rieng_ma": 2.0, "chi_phi": -0.46}
    assert sbh.nguyen_nhan_chinh(sbh.KET_QUA_THANG, p) == "nganh"


def test_THANG_va_THUA_chon_dau_ngc_nhau_tren_CUNG_mot_bo_phan():
    """Một bộ phần có cả phần rất dương lẫn rất âm: thắng lấy dương, thua lấy âm."""
    p = {"thi_truong": 9.0, "nganh": 0.5, "rieng_ma": -8.0, "chi_phi": -0.46}
    assert sbh.nguyen_nhan_chinh(sbh.KET_QUA_THANG, p) == "thi_truong"
    assert sbh.nguyen_nhan_chinh(sbh.KET_QUA_THUA, p) == "rieng_ma"


def test_HOA_va_khong_phan_ra_thi_khong_co_nguyen_nhan():
    p = {"thi_truong": 1.0, "nganh": None, "rieng_ma": -1.0, "chi_phi": 0.0}
    assert sbh.nguyen_nhan_chinh(sbh.KET_QUA_HOA, p) is None
    assert sbh.nguyen_nhan_chinh(sbh.KET_QUA_THUA, None) is None


def test_phan_None_bi_bo_qua_khi_chon():
    p = {"thi_truong": -1.0, "nganh": None, "rieng_ma": -2.0, "chi_phi": -0.46}
    assert sbh.nguyen_nhan_chinh(sbh.KET_QUA_THUA, p) == "rieng_ma"


def test_phan_None_KHONG_BAO_GIO_la_nguyen_nhan_ke_ca_khi_doi_thanh_0():
    """Với bộ phần nhất quán (tổng = lãi ròng) thay None bằng 0 không đổi kết quả
    — đột biến ấy từng SỐNG SÓT vì tương đương. Hợp đồng của hàm là chọn trong
    các phần ĐÃ CÓ, nên kiểm thẳng bằng bộ phần mà mọi phần có số đều dương
    (thua) hoặc đều âm (thắng): một None bị coi là 0 sẽ lọt vào."""
    p = {"thi_truong": 2.0, "nganh": None, "rieng_ma": 1.0, "chi_phi": 3.0}
    assert sbh.nguyen_nhan_chinh(sbh.KET_QUA_THUA, p) == "rieng_ma"
    p = {"thi_truong": -2.0, "nganh": None, "rieng_ma": -1.0, "chi_phi": -3.0}
    assert sbh.nguyen_nhan_chinh(sbh.KET_QUA_THANG, p) == "rieng_ma"


def test_HOA_giua_hai_phan_lay_phan_DUNG_TRUOC_trong_PHAN_tat_dinh():
    p = {"thi_truong": -2.0, "nganh": -2.0, "rieng_ma": -2.0, "chi_phi": -2.0}
    assert sbh.nguyen_nhan_chinh(sbh.KET_QUA_THUA, p) == sbh.PHAN[0]
    p = {"thi_truong": 2.0, "nganh": 2.0, "rieng_ma": 2.0, "chi_phi": -2.0}
    assert sbh.nguyen_nhan_chinh(sbh.KET_QUA_THANG, p) == sbh.PHAN[0]


def test_LENH_HOA_VON_GIA_mat_dung_PHI_la_CHI_PHI_khong_phai_tin_hieu_sai():
    """Lỗi sửa đổi 4 phần sinh ra để bắt: để phí nằm trong "riêng mã" thì lệnh
    giá vào = giá ra, thị trường đứng yên, mất đúng phí, bị gọi là tín hiệu sai."""
    b = sbh.lap_bai_hoc(_dong(loi_nhuan_rong_pct=-PHI, ro_chuan_pct=0.0,
                              exit_reason=ExitReason.MAX_HOLD, exit_price=100.0),
                        loi_nhuan_nganh_pct=0.0)
    assert b["ket_qua"] == sbh.KET_QUA_THUA
    assert b["nguyen_nhan"] == "chi_phi"
    assert b["cach_goi"] is None
    assert b["phan"]["rieng_ma"] == pytest.approx(0.0)


def test_TIN_HIEU_SAI_chi_la_cach_GOI_khi_rieng_ma_gay_lenh_thua():
    b = sbh.lap_bai_hoc(_dong(loi_nhuan_rong_pct=-10.46, ro_chuan_pct=1.0),
                        loi_nhuan_nganh_pct=1.0)
    assert b["nguyen_nhan"] == "rieng_ma"
    assert b["cach_goi"] and "tín hiệu sai" in b["cach_goi"]
    assert "bất biến 5" in b["cach_goi"]
    assert "tin_hieu_sai" not in sbh.PHAN     # không phải một nhãn riêng đo được


def test_lenh_THANG_nguyen_nhan_rieng_ma_KHONG_goi_la_tin_hieu_sai():
    b = sbh.lap_bai_hoc(_dong(loi_nhuan_rong_pct=8.0, ro_chuan_pct=0.0, exit_price=108.0,
                              exit_reason=ExitReason.TAKE_PROFIT),
                        loi_nhuan_nganh_pct=0.5)
    assert b["ket_qua"] == sbh.KET_QUA_THANG
    assert b["nguyen_nhan"] == "rieng_ma"
    assert b["cach_goi"] is None


def test_nhan_hien_cua_nguyen_nhan():
    thua = sbh.lap_bai_hoc(_dong(), loi_nhuan_nganh_pct=1.0)
    assert sbh.nhan_nguyen_nhan(thua) == "Riêng mã/tín hiệu (gọi: tín hiệu sai?)"
    hoa = sbh.lap_bai_hoc(_dong(loi_nhuan_rong_pct=0.0))
    assert sbh.nhan_nguyen_nhan(hoa) == "— (hoà)"
    chua = sbh.lap_bai_hoc(_dong(ro_chuan_pct=None))
    assert sbh.nhan_nguyen_nhan(chua) == "— (chưa phân rã được)"


# ── 3. gap: ĐÚNG điều kiện của hau_kiem_may ──────────────────────────────

def _ast_ham(file, ten):
    cay = ast.parse((GOC / file).read_text(encoding="utf-8"))
    return next(n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == ten)


def _goi(nut):
    return {getattr(c.func, "attr", getattr(c.func, "id", "")) for c in ast.walk(nut)
            if isinstance(c, ast.Call)}


def test_GAP_goi_dung_ham_cua_hau_kiem_may_khong_chep_cong_thuc():
    cay = ast.parse((GOC / "so_bai_hoc.py").read_text(encoding="utf-8"))
    nhap = [n for n in ast.walk(cay) if isinstance(n, ast.ImportFrom)
            and n.module == "nhat_ky_vi_sao"
            and "thoat_duoi_cat_lo" in {a.name for a in n.names}]
    assert nhap, "so_bai_hoc phải NHẬP thoat_duoi_cat_lo từ nhat_ky_vi_sao"
    lap = _ast_ham("so_bai_hoc.py", "lap_bai_hoc")
    assert "thoat_duoi_cat_lo" in _goi(lap)
    # công thức thứ hai sẽ là một phép so thứ tự giá thoát với cắt lỗ
    so_thu_tu = [n for n in ast.walk(lap) if isinstance(n, ast.Compare)
                 and any(isinstance(o, (ast.Lt, ast.LtE, ast.Gt, ast.GtE)) for o in n.ops)]
    assert not so_thu_tu, "lap_bai_hoc tự so thứ tự — phải gọi thoat_duoi_cat_lo"
    # và hau_kiem_may cũng gọi CHÍNH hàm ấy, nên hai nơi không thể trôi ra khỏi nhau
    assert "thoat_duoi_cat_lo" in _goi(_ast_ham("nhat_ky_vi_sao.py", "hau_kiem_may"))


@pytest.mark.parametrize("sl, gia_ra", [
    (95.0, 90.0), (95.0, 94.99), (95.0, 95.0), (95.0, 95.01), (95.0, 120.0)])
@pytest.mark.parametrize("ly_do", [ExitReason.STOP_LOSS, ExitReason.MAX_HOLD,
                                   ExitReason.SIGNAL_REVERSED])
def test_GAP_khop_nhan_THOAT_DUOI_cua_hau_kiem_may(sl, gia_ra, ly_do):
    nhan = nk.hau_kiem_may(sl_ban_dau=sl, exit_price=gia_ra, exit_reason=ly_do,
                           loi_nhuan_rong_pct=-3.0, R=-1.0, alpha=-2.0, diem={})
    co_nhan_gap = any(n.startswith("thoát DƯỚI cắt lỗ ban đầu") for n in nhan)
    b = sbh.lap_bai_hoc(_dong(stop_loss_ban_dau=sl, exit_price=gia_ra, exit_reason=ly_do))
    assert b["gap"] is co_nhan_gap


def test_gap_dung_bang_cat_lo_KHONG_phai_gap():
    assert sbh.lap_bai_hoc(_dong(stop_loss_ban_dau=95.0, exit_price=95.0))["gap"] is False


def test_thieu_cat_lo_hoac_gia_thoat_thi_gap_la_None_va_NOI_ra():
    for kw in ({"stop_loss_ban_dau": None}, {"exit_price": None}):
        b = sbh.lap_bai_hoc(_dong(**kw))
        assert b["gap"] is None
        assert any("gap" in t for t in b["thieu"])


# ── 4. cắt lỗ sát ────────────────────────────────────────────────────────

N = sbh.N_PHIEN_SAU_THOAT


def _sau(*gia):
    return list(gia)


def test_CAT_LO_SAT_co_khi_gia_quay_lai_gia_vao_trong_cua_so():
    r = sbh.cat_lo_sat(ExitReason.STOP_LOSS, 100.0, _sau(91, 95, 100, 90, 90))
    assert r["trang_thai"] == sbh.CLS_CO and r["gia_cao_nhat"] == 100


def test_CAT_LO_SAT_bien_BANG_gia_vao_la_CO():
    assert sbh.cat_lo_sat(ExitReason.STOP_LOSS, 100.0, [100.0] * N)["trang_thai"] == sbh.CLS_CO
    assert sbh.cat_lo_sat(ExitReason.STOP_LOSS, 100.0, [99.99] * N)["trang_thai"] == sbh.CLS_KHONG


def test_CAT_LO_SAT_khong_khi_cua_so_DAY_ma_khong_cham_gia_vao():
    r = sbh.cat_lo_sat(ExitReason.STOP_LOSS, 100.0, [90.0] * N)
    assert r["trang_thai"] == sbh.CLS_KHONG


def test_CAT_LO_SAT_chi_nhin_dung_N_phien_phien_thu_N_cong_1_khong_tinh():
    r = sbh.cat_lo_sat(ExitReason.STOP_LOSS, 100.0, [90.0] * N + [130.0])
    assert r["trang_thai"] == sbh.CLS_KHONG


def test_CAT_LO_SAT_phien_thu_N_van_tinh():
    r = sbh.cat_lo_sat(ExitReason.STOP_LOSS, 100.0, [90.0] * (N - 1) + [100.0])
    assert r["trang_thai"] == sbh.CLS_CO


def test_CAT_LO_SAT_cua_so_CHUA_KHEP_ma_chua_cham_thi_CHUA_DU_khong_phai_KHONG():
    r = sbh.cat_lo_sat(ExitReason.STOP_LOSS, 100.0, [90.0] * (N - 1))
    assert r["trang_thai"] == sbh.CLS_CHUA_DU


def test_CAT_LO_SAT_cua_so_chua_khep_nhung_da_cham_thi_van_CO():
    assert sbh.cat_lo_sat(ExitReason.STOP_LOSS, 100.0, [101.0])["trang_thai"] == sbh.CLS_CO


@pytest.mark.parametrize("sau", [None, []])
def test_CAT_LO_SAT_khong_co_chuoi_gia_thi_CHUA_DU_khong_doan(sau):
    assert sbh.cat_lo_sat(ExitReason.STOP_LOSS, 100.0, sau)["trang_thai"] == sbh.CLS_CHUA_DU


def test_CAT_LO_SAT_thieu_gia_vao_thi_CHUA_DU():
    assert sbh.cat_lo_sat(ExitReason.STOP_LOSS, None, [120.0] * N)["trang_thai"] == sbh.CLS_CHUA_DU


@pytest.mark.parametrize("ly_do", [ExitReason.TAKE_PROFIT, ExitReason.SIGNAL_REVERSED,
                                   ExitReason.MAX_HOLD, ExitReason.HET_DU_LIEU, None])
def test_CAT_LO_SAT_chi_ap_dung_cho_lenh_thoat_bang_CAT_LO(ly_do):
    r = sbh.cat_lo_sat(ly_do, 100.0, [130.0] * N)
    assert r["trang_thai"] == sbh.CLS_KHONG_AP_DUNG


def test_N_PHIEN_SAU_THOAT_la_MOT_hang_so_va_moi_cho_deu_doc_no(monkeypatch):
    monkeypatch.setattr(sbh, "N_PHIEN_SAU_THOAT", 2)
    assert sbh.cat_lo_sat(ExitReason.STOP_LOSS, 100.0, [90.0, 90.0, 130.0])["trang_thai"] == sbh.CLS_KHONG
    chuoi = _chuoi([(f"2026-09-{d:02d}", 90.0 + d) for d in range(11, 20)])
    assert len(sbh.gia_sau_thoat(chuoi, "2026-09-10")) == 2


def test_gia_sau_thoat_LOAI_ngay_ra_va_sap_theo_ngay():
    chuoi = _chuoi([("2026-09-12", 3.0), ("2026-09-10", 1.0), ("2026-09-11", 2.0),
                    ("2026-09-15", 4.0), ("2026-09-09", 0.5)])
    assert sbh.gia_sau_thoat(chuoi, "2026-09-10") == [2.0, 3.0, 4.0]
    assert sbh.gia_sau_thoat(chuoi, "2026-09-10 00:00:00") == [2.0, 3.0, 4.0]
    assert sbh.gia_sau_thoat(None, "2026-09-10") is None
    assert sbh.gia_sau_thoat({}, "2026-09-10") is None
    assert sbh.gia_sau_thoat(chuoi, None) is None


def test_lap_bai_hoc_cat_lo_sat_qua_chuoi_gia_sau_thoat():
    b = sbh.lap_bai_hoc(_dong(), gia_dong_sau_thoat=[91.0, 101.0])
    assert b["cat_lo_sat"]["trang_thai"] == sbh.CLS_CO
    b = sbh.lap_bai_hoc(_dong())
    assert b["cat_lo_sat"]["trang_thai"] == sbh.CLS_CHUA_DU
    assert any("cắt lỗ sát" in t for t in b["thieu"])


# ── 5. ngành ─────────────────────────────────────────────────────────────

def test_nganh_suy_tu_SECTOR_WATCHLIST_khong_bang_thu_hai():
    cay = ast.parse((GOC / "so_bai_hoc.py").read_text(encoding="utf-8"))
    nhap = [n for n in ast.walk(cay) if isinstance(n, ast.ImportFrom)
            and n.module == "vn100_symbols"
            and "SECTOR_WATCHLIST" in {a.name for a in n.names}]
    assert nhap
    for n in ast.walk(cay):          # không có từ điển mã -> ngành gõ tay
        if isinstance(n, ast.Dict):
            khoa = [k.value for k in n.keys if isinstance(k, ast.Constant)]
            assert not (set(khoa) & set(SECTOR_WATCHLIST["Ngân hàng"])), "bảng ngành thứ hai"


def test_nganh_cua_mot_nganh_nhieu_nganh_va_khong_co():
    assert sbh.nganh_cua("ACB") == ("Ngân hàng", None)
    ten, ly_do = sbh.nganh_cua("PLX")        # có ở HAI ngành trong rổ
    assert ten is None and "2 ngành" in ly_do
    ten, ly_do = sbh.nganh_cua("XYZ")
    assert ten is None and "không thuộc ngành nào" in ly_do


def test_ma_cung_nganh_khong_gom_chinh_no_va_PLX_khong_co():
    assert "ACB" not in sbh.ma_cung_nganh("ACB") and "VCB" in sbh.ma_cung_nganh("ACB")
    assert sbh.ma_cung_nganh("PLX") == []
    assert sbh.ma_cung_nganh("FPT") == []        # ngành chỉ có một mã


def test_loi_nhuan_nganh_la_TB_cac_ma_cung_nganh_dong_cua_vao_toi_dong_cua_ra():
    r = sbh.loi_nhuan_nganh("ACB", "2026-09-02 00:00:00", "2026-09-10", GIA_NGANH)
    # STB −2% và VCB −4%; TCB thiếu giá ngày ra nên bị LOẠI
    assert r["gia_tri"] == pytest.approx(-3.0)
    assert r["n_ma"] == 2 and r["nganh"] == "Ngân hàng" and r["ly_do"] is None


def test_loi_nhuan_nganh_khong_gom_chinh_ma():
    gia = dict(GIA_NGANH)
    gia["ACB"] = _chuoi([("2026-09-02", 100.0), ("2026-09-10", 200.0)])   # +100%
    assert sbh.loi_nhuan_nganh("ACB", "2026-09-02", "2026-09-10", gia)["gia_tri"] == pytest.approx(-3.0)


@pytest.mark.parametrize("ma, gia, mau_ly_do", [
    ("PLX", GIA_NGANH, "2 ngành"),
    ("XYZ", GIA_NGANH, "không thuộc ngành nào"),
    ("ACB", None, "chưa có giá"),
    ("ACB", {}, "chưa có giá"),
    ("ACB", {"HPG": _chuoi([("2026-09-02", 1.0), ("2026-09-10", 2.0)])}, "không mã cùng ngành"),
    ("FPT", GIA_NGANH, "không mã cùng ngành"),
])
def test_loi_nhuan_nganh_THIEU_thi_None_kem_LY_DO(ma, gia, mau_ly_do):
    r = sbh.loi_nhuan_nganh(ma, "2026-09-02", "2026-09-10", gia)
    assert r["gia_tri"] is None and r["n_ma"] == 0
    assert mau_ly_do in r["ly_do"]


def test_loi_nhuan_nganh_thieu_ngay():
    r = sbh.loi_nhuan_nganh("ACB", None, "2026-09-10", GIA_NGANH)
    assert r["gia_tri"] is None and "ngày" in r["ly_do"]


def test_bai_hoc_dung_ngành_khi_co_gia_va_neu_ly_do_khi_thieu():
    ban = sbh.bai_hoc_cho_so([_dong()], GIA_NGANH)["bai_hoc"][0]
    assert ban["co_nganh"] and ban["nganh"] == "Ngân hàng" and ban["n_ma_nganh"] == 2
    assert ban["phan"]["nganh"] == pytest.approx(-3.0 - 1.0)          # −3% ngành − 1% thị trường
    khong = sbh.bai_hoc_cho_so([_dong(symbol="PLX")], GIA_NGANH)["bai_hoc"][0]
    assert not khong["co_nganh"] and khong["phan"]["nganh"] is None
    assert any("2 ngành" in t for t in khong["thieu"])


def test_chuoi_dong_cua_nhan_he_so_va_bo_phien_khong_gia():
    df = pd.DataFrame({"time": ["2026-09-01 00:00:00", "2026-09-02", "2026-09-03"],
                       "close": [10.5, float("nan"), 11.0]})
    assert sbh.chuoi_dong_cua(df, 1000.0) == {"2026-09-01": 10500.0, "2026-09-03": 11000.0}
    assert sbh.chuoi_dong_cua(None, 1000.0) == {}
    assert sbh.chuoi_dong_cua(df.iloc[0:0], 1000.0) == {}


# ── 6. thiếu thì NÓI, không đoán ─────────────────────────────────────────

def test_THIEU_ro_chuan_thi_khong_phan_ra_va_noi_ro():
    b = sbh.lap_bai_hoc(_dong(ro_chuan_pct=None, alpha_pct=None), loi_nhuan_nganh_pct=1.0)
    assert b["phan"] is None and b["nguyen_nhan"] is None and not b["co_nganh"]
    assert any("chưa có rổ chuẩn" in t for t in b["thieu"])


def test_THIEU_nganh_thi_noi_ro_va_van_phan_ra_duoc():
    b = sbh.lap_bai_hoc(_dong(), ly_do_thieu_nganh="lý do X")
    assert b["phan"] is not None and b["phan"]["nganh"] is None
    assert "lý do X" in b["thieu"]


def test_lap_bai_hoc_TU_CHOI_dong_chua_co_nua_DONG():
    for kw in ({"exit_date": None}, {"loi_nhuan_rong_pct": None}):
        with pytest.raises(ValueError, match="chưa có nửa ĐÓNG"):
            sbh.lap_bai_hoc(_dong(**kw))


def test_ket_qua_lenh_ba_nhanh():
    assert sbh.ket_qua_lenh(0.01) == sbh.KET_QUA_THANG
    assert sbh.ket_qua_lenh(-0.01) == sbh.KET_QUA_THUA
    assert sbh.ket_qua_lenh(0.0) == sbh.KET_QUA_HOA


# ── 7. tất định, không đụng đầu vào ─────────────────────────────────────

def test_TAT_DINH_cung_dau_vao_cung_ket_qua_va_khong_sua_dau_vao():
    nk_rows = [_dong(trade_id=3), _dong(trade_id=2, loi_nhuan_rong_pct=6.0, ro_chuan_pct=1.0,
                                        exit_reason=ExitReason.TAKE_PROFIT, exit_price=106.0),
               _dong(trade_id=1, exit_date=None, loi_nhuan_rong_pct=None)]
    truoc = copy.deepcopy(nk_rows)
    a = sbh.bai_hoc_cho_so(nk_rows, GIA_NGANH)
    b = sbh.bai_hoc_cho_so(nk_rows, GIA_NGANH)
    assert a == b
    assert nk_rows == truoc
    gia_truoc = copy.deepcopy(GIA_NGANH)
    sbh.bai_hoc_cho_so(nk_rows, GIA_NGANH)
    assert GIA_NGANH == gia_truoc


# ── 8. tổng hợp nhiều lệnh ──────────────────────────────────────────────

def _lo(ro, nganh_ret, trade_id=1, lnr=-6.0, ly_do=ExitReason.SIGNAL_REVERSED, gia_ra=94.0):
    return sbh.lap_bai_hoc(
        _dong(trade_id=trade_id, loi_nhuan_rong_pct=lnr, ro_chuan_pct=ro,
              exit_reason=ly_do, exit_price=gia_ra), loi_nhuan_nganh_pct=nganh_ret)


def test_tong_hop_dem_nguyen_nhan_tach_THANG_THUA():
    cac = [_lo(-5.0, -5.5, 1),                       # thua, thị trường −5 là âm nhất
           _lo(0.0, 0.0, 2),                         # thua, riêng mã âm nhất
           _lo(1.0, 1.2, 3, lnr=9.0),                # thắng, riêng mã dương nhất
           _lo(8.0, 8.0, 4, lnr=8.0 - PHI),          # thắng nhờ thị trường
           _lo(0.0, 0.0, 5, lnr=0.0)]                # hoà
    th = sbh.tong_hop(cac)
    assert (th["n"], th["n_thang"], th["n_thua"], th["n_hoa"]) == (5, 2, 2, 1)
    thua, thang = th["nguyen_nhan"][sbh.KET_QUA_THUA], th["nguyen_nhan"][sbh.KET_QUA_THANG]
    assert thua == {"thi_truong": 1, "nganh": 0, "rieng_ma": 1, "chi_phi": 0}
    assert thang == {"thi_truong": 1, "nganh": 0, "rieng_ma": 1, "chi_phi": 0}
    assert th["n_khong_phan_ra"] == 0


def test_tong_hop_dem_lenh_khong_phan_ra_va_bo_qua_hoa():
    cac = [sbh.lap_bai_hoc(_dong(ro_chuan_pct=None)),
           sbh.lap_bai_hoc(_dong(loi_nhuan_rong_pct=0.0, ro_chuan_pct=None))]
    th = sbh.tong_hop(cac)
    assert th["n_khong_phan_ra"] == 1                # lệnh hoà không đếm vào đây
    assert th["tb_phan"]["thi_truong"] is None


def test_tong_hop_trung_binh_dong_gop_va_KTC():
    cac = [_lo(r, r, i + 1, lnr=l) for i, (r, l) in enumerate(
        [(-2.0, -4.0), (0.0, -3.0), (2.0, -1.0), (4.0, 1.0)])]
    th = sbh.tong_hop(cac)
    tt = th["tb_phan"]["thi_truong"]
    assert tt["tb"] == pytest.approx(1.0) and tt["n"] == 4
    lo, cao = tt["ktc"]
    sd = (sum((x - 1.0) ** 2 for x in (-2.0, 0.0, 2.0, 4.0)) / 3) ** 0.5
    nua = paper_metrics.Z_LOI_THE * sd / 4 ** 0.5
    assert (lo, cao) == (pytest.approx(1.0 - nua), pytest.approx(1.0 + nua))
    # ba phần tách được cộng lại đúng lãi ròng trung bình
    tong = sum(th["tb_phan"][k]["tb"] for k in ("thi_truong", "nganh", "rieng_ma", "chi_phi"))
    assert tong == pytest.approx(sum(b["loi_nhuan_rong_pct"] for b in cac) / 4)
    assert th["tb_phan"]["chi_phi"]["tb"] == pytest.approx(-PHI)


def test_tong_hop_mot_lenh_khong_co_KTC():
    th = sbh.tong_hop([_lo(1.0, 1.0)])
    assert th["tb_phan"]["thi_truong"]["ktc"] is None and th["tb_phan"]["thi_truong"]["n"] == 1


def test_tong_hop_rieng_ma_chi_lay_lenh_CO_nganh_con_nganh_va_rieng_lay_tat_ca():
    co = _lo(0.0, 2.0, 1, lnr=-1.0)                  # có ngành
    khong = sbh.lap_bai_hoc(_dong(trade_id=2, loi_nhuan_rong_pct=-1.0, ro_chuan_pct=0.0))
    th = sbh.tong_hop([co, khong])
    assert th["n_co_nganh"] == 1
    assert th["tb_phan"]["nganh"]["n"] == 1 and th["tb_phan"]["rieng_ma"]["n"] == 1
    assert th["tb_phan"]["nganh_va_rieng_ma"]["n"] == 2
    # ngành + riêng mã = lãi ròng + phí − thị trường, dù có tách được ngành hay không
    for b in (co, khong):
        p = b["phan"]
        assert sbh._nganh_va_rieng_ma(p) == pytest.approx(b["loi_nhuan_rong_pct"] + PHI - p["thi_truong"])


def test_tong_hop_tb_lenh_THUA_chi_gom_lenh_thua():
    th = sbh.tong_hop([_lo(1.0, 1.0, 1, lnr=-4.0), _lo(2.0, 2.0, 2, lnr=5.0)])
    assert th["tb_phan_thua"]["thi_truong"]["n"] == 1
    assert th["tb_phan_thua"]["thi_truong"]["tb"] == pytest.approx(1.0)
    assert th["tb_phan"]["thi_truong"]["n"] == 2


def test_dem_gap_va_cat_lo_sat_trong_tong_hop():
    a = sbh.lap_bai_hoc(_dong(trade_id=1, exit_price=90.0), gia_dong_sau_thoat=[101.0])
    b = sbh.lap_bai_hoc(_dong(trade_id=2, exit_price=96.0), gia_dong_sau_thoat=[90.0] * N)
    c = sbh.lap_bai_hoc(_dong(trade_id=3, stop_loss_ban_dau=None))      # gap không xét được
    d = sbh.lap_bai_hoc(_dong(trade_id=4, exit_reason=ExitReason.TAKE_PROFIT, exit_price=120.0,
                              loi_nhuan_rong_pct=19.0))
    th = sbh.tong_hop([a, b, c, d])
    assert (th["n_gap"], th["n_gap_xet"]) == (1, 3)
    assert (th["n_cat_lo_sat"], th["n_cat_lo_sat_xet"]) == (1, 2)    # c: chưa đủ, d: không áp dụng


# ── 9. ngưỡng "chưa đủ lệnh" suy ra, không gõ ────────────────────────────

def test_N_TOI_THIEU_TONG_HOP_SUY_RA_tu_paper_metrics_hinh_dang_AST():
    cay = ast.parse((GOC / "so_bai_hoc.py").read_text(encoding="utf-8"))
    gan = [n for n in cay.body if isinstance(n, ast.Assign)
           and any(getattr(t, "id", "") == "N_TOI_THIEU_TONG_HOP" for t in n.targets)]
    assert len(gan) == 1
    v = gan[0].value
    assert isinstance(v, ast.Attribute) and v.attr == "N_TOI_THIEU"
    assert getattr(v.value, "id", "") == "paper_metrics"
    assert sbh.N_TOI_THIEU_TONG_HOP == paper_metrics.N_TOI_THIEU


def test_DUOI_nguong_co_cau_luu_y_chua_du_lenh_de_ket_luan(monkeypatch):
    th = sbh.tong_hop([_lo(1.0, 1.0)])
    assert not th["du_lenh"]
    assert "chưa đủ lệnh để kết luận" in th["cau_luu_y"]
    assert "một vài lệnh không phải bằng chứng" in th["cau_luu_y"]
    assert str(sbh.N_TOI_THIEU_TONG_HOP) in th["cau_luu_y"]


def test_DUNG_nguong_thi_het_cau_luu_y_va_nguong_chay_theo_hang_so(monkeypatch):
    monkeypatch.setattr(sbh, "N_TOI_THIEU_TONG_HOP", 3)
    cac = [_lo(1.0, 1.0, i) for i in range(1, 4)]
    assert sbh.tong_hop(cac[:2])["cau_luu_y"] is not None
    th = sbh.tong_hop(cac)
    assert th["du_lenh"] and th["cau_luu_y"] is None


def test_tong_hop_khong_xep_hang_agent():
    nguon = (GOC / "so_bai_hoc.py").read_text(encoding="utf-8")
    cay = ast.parse(nguon)
    khong_doc = {n.value for n in ast.walk(cay) if isinstance(n, ast.Constant)
                 and isinstance(n.value, str)}
    assert "diem_agent" not in khong_doc, "sổ bài học không đọc điểm agent để xếp hạng"
    th = sbh.tong_hop([_lo(1.0, 1.0)])
    assert not any("agent" in str(k) for k in th)


# ── 10. toàn bộ sổ ───────────────────────────────────────────────────────

def test_so_RONG_van_chay():
    bh = sbh.bai_hoc_cho_so([])
    assert bh["bai_hoc"] == [] and bh["n_dong_cho_nua_dong"] == 0
    th = bh["tong_hop"]
    assert th["n"] == 0 and th["cau_luu_y"] and not th["du_lenh"]
    assert all(h["TB mọi lệnh"] is None for h in sbh.bang_dong_gop(th))
    assert [h["Lệnh THUA"] for h in sbh.bang_nguyen_nhan(th)] == [0, 0, 0, 0]


def test_lenh_sổ_DA_DONG_ma_nhat_ky_chua_dien_nua_DONG_duoc_DEM_rieng():
    chua = _dong(trade_id=5, exit_date=None, loi_nhuan_rong_pct=None, ro_chuan_pct=None,
                 trang_thai_lenh=Status.CLOSED)
    mo = _dong(trade_id=6, exit_date=None, loi_nhuan_rong_pct=None, trang_thai_lenh=Status.OPEN)
    cho = _dong(trade_id=7, exit_date=None, loi_nhuan_rong_pct=None, trang_thai_lenh=Status.PENDING)
    bh = sbh.bai_hoc_cho_so([chua, mo, cho, _dong(trade_id=8)])
    assert bh["n_dong_cho_nua_dong"] == 1
    assert [b["trade_id"] for b in bh["bai_hoc"]] == [8]


def test_ma_can_gia_va_tu_ngay():
    rows = [_dong(symbol="ACB", entry_date="2026-09-05"),
            _dong(symbol="FPT", entry_date="2026-08-20 00:00:00"),
            _dong(symbol="XYZ", exit_date=None, loi_nhuan_rong_pct=None, entry_date="2020-01-01")]
    ma = sbh.ma_can_gia(rows)
    assert "ACB" in ma and "FPT" in ma and "VCB" in ma and "XYZ" not in ma
    assert ma == sorted(set(ma))
    assert sbh.tu_ngay_can_gia(rows) == "2026-08-20"
    assert sbh.tu_ngay_can_gia([]) is None


def test_dong_bang_so_THO_va_cot_day_du():
    b = sbh.bai_hoc_cho_so([_dong()], GIA_NGANH)["bai_hoc"][0]
    h = sbh.dong_bang(b)
    assert h["Mã"] == "ACB" and h["Ra"] == "2026-09-10" and h["Kết quả"] == sbh.KET_QUA_THUA
    assert h["Lãi ròng %"] == -10.46
    assert h["Thị trường %"] == 1.0 and h["Ngành %"] == pytest.approx(-4.0)
    assert h["Chi phí %"] == pytest.approx(-PHI)
    assert h["Gap"] == "có" and h["Cắt lỗ sát"] == sbh.NHAN_CAT_LO_SAT[sbh.CLS_CHUA_DU]
    chua = sbh.dong_bang(sbh.lap_bai_hoc(_dong(ro_chuan_pct=None)))
    assert chua["Thị trường %"] is None and chua["Còn thiếu"]


def test_moi_trang_thai_cat_lo_sat_co_nhan():
    cls = {v for k, v in vars(sbh).items() if k.startswith("CLS_")}
    assert cls == set(sbh.NHAN_CAT_LO_SAT)


# ── 11. đúng là CHỈ HIỆN: lược đồ đứng yên, module thuần ───────────────

#: Chép NGUYÊN VĂN từ `origin/main` ngày 09/10/2026 (`git show origin/main:nhat_ky_vi_sao.py`).
#: Đổi một ký tự là đổi lược đồ tab Sheets `nhat_ky`: `sheets_store` NỔ khi lệch
#: cột và lượt quét thật trên Actions hỏng. Muốn đổi thì sửa cả ở đây, có chủ đích.
COT_NHAT_KY_O_MAIN = (
    "trade_id", "symbol", "signal_date", "entry_date", "entry_price",
    "stop_loss_ban_dau", "rui_ro_pct", "entry_score", "diem_agent", "ly_do",
    "boi_canh",
    "exit_date", "exit_price", "exit_reason", "loi_nhuan_rong_pct",
    "ket_qua_R", "ro_chuan_pct", "alpha_pct", "hau_kiem_may", "hau_kiem_loi",
)


def test_COT_NHAT_KY_KHONG_DOI_so_voi_main():
    assert nk.COT_NHAT_KY == COT_NHAT_KY_O_MAIN
    assert len(nk.COT_NHAT_KY) == 20


def test_so_bai_hoc_khong_them_cot_hay_bang_nao():
    nguon = (GOC / "so_bai_hoc.py").read_text(encoding="utf-8")
    cay = ast.parse(nguon)
    for n in ast.walk(cay):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            assert "CREATE TABLE" not in n.value.upper() and "ALTER TABLE" not in n.value.upper()
    nhap = {a.name.split(".")[0] for n in ast.walk(cay) if isinstance(n, ast.Import) for a in n.names}
    nhap |= {n.module.split(".")[0] for n in ast.walk(cay) if isinstance(n, ast.ImportFrom)}
    cam = {"sqlite3", "requests", "gspread", "streamlit", "google_sheets_sync", "sheets_store",
           "market_filter", "data_collectors", "backtest", "run_daily", "vnstock", "vnstock_data",
           "anthropic", "urllib", "socket"}
    assert not nhap & cam, f"so_bai_hoc phải THUẦN, đang nhập {nhap & cam}"


def test_so_bai_hoc_khong_goi_ham_ghi_hay_mang():
    cay = ast.parse((GOC / "so_bai_hoc.py").read_text(encoding="utf-8"))
    goi = {getattr(c.func, "attr", getattr(c.func, "id", "")) for c in ast.walk(cay)
           if isinstance(c, ast.Call)}
    assert not goi & {"open", "write_text", "write_bytes", "write", "to_csv", "execute",
                      "commit", "post", "urlopen", "push", "pull"}


def test_hau_kiem_may_GIU_NGUYEN_nhan_da_ghi_trong_so():
    """Tách `thoat_duoi_cat_lo` không được đổi một ký tự của nhãn đã ghi vào sổ."""
    nhan = nk.hau_kiem_may(sl_ban_dau=100.0, exit_price=96.0, exit_reason=ExitReason.STOP_LOSS,
                           loi_nhuan_rong_pct=-4.46, R=-1.2, alpha=-3.0,
                           diem={"trend_score": 80.0, "volume_score": 60.0})
    assert nhan == [
        "THUA", "thua rổ -3.00 điểm",
        "thoát DƯỚI cắt lỗ ban đầu 4.00% — gap/trượt giá "
        "(bất biến 3: gap qua SL khớp ở giá mở cửa)",
        "lỗ -1.20R — vượt mức rủi ro dự kiến 1R",
        "agent cao nhất lúc vào: trend 80 · thấp nhất: volume 60"]
    nhan = nk.hau_kiem_may(sl_ban_dau=95.0, exit_price=100.0, exit_reason=ExitReason.STOP_LOSS,
                           loi_nhuan_rong_pct=4.0, R=0.8, alpha=None, diem={})
    assert nhan == ["THẮNG", "chưa có rổ chuẩn cho cặp ngày này — không nói được vượt hay thua rổ",
                    "thoát bằng cắt lỗ ĐÃ NÂNG (trailing) — cao hơn cắt lỗ ban đầu"]


# ── 12. app: chỉ HIỆN, giá có đệm, lỗi không làm sập tab ────────────────

_APP = (GOC / "app.py").read_text(encoding="utf-8")
_CAY_APP = ast.parse(_APP)


def _ham_app(ten):
    for n in _CAY_APP.body:
        if isinstance(n, ast.FunctionDef) and n.name == ten:
            return n
    raise AssertionError(f"app.py không có hàm {ten}")


def _co_cache_data(f):
    return any("cache_data" in ast.unparse(d) for d in f.decorator_list)


def _hang_so_app(ten):
    """Giá trị literal của hằng số mức module trong app.py (không gõ lại số ở test)."""
    for n in _CAY_APP.body:
        if isinstance(n, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == ten for t in n.targets):
            return ast.literal_eval(n.value)
    raise AssertionError(f"app.py không có hằng số {ten}")


#: Mốc đầu cửa sổ phân tích của app, dựng đúng như app dựng (`end_date - timedelta(
#: days=NGAY_LICH_SU_PHAN_TICH)`) từ cùng hằng số, với `end_str` của `_chay_app`.
_END_STR_TEST = "2026-10-09"
_MOC_PHAN_TICH = (pd.Timestamp(_END_STR_TEST)
                  - pd.Timedelta(days=_hang_so_app("NGAY_LICH_SU_PHAN_TICH"))).strftime("%Y-%m-%d")


def test_app_gia_tai_qua_MOT_ham_CO_DEM_va_khong_goi_load_trong_vong_lap_lenh():
    f = _ham_app("_gia_cho_so_bai_hoc")
    assert _co_cache_data(f), "tải giá cho sổ bài học phải có @st.cache_data"
    cho_goi = [n for n in ast.walk(_CAY_APP) if isinstance(n, ast.Call)
               and getattr(n.func, "id", "") == "load_stock_data"]
    trong_ham = [n for n in ast.walk(f) if isinstance(n, ast.Call)
                 and getattr(n.func, "id", "") == "load_stock_data"]
    assert len(trong_ham) == 1 and len(cho_goi) == 2   # 1 của phân tích mã + 1 trong hàm có đệm
    for ten in ("_khoi_so_bai_hoc", "_bang_bai_hoc", "_bang_dong_gop"):
        assert "load_stock_data" not in {getattr(c.func, "id", "") for c in ast.walk(_ham_app(ten))
                                         if isinstance(c, ast.Call)}, ten


def test_app_khoi_chi_goi_gia_sau_khi_nguoi_dung_bam_nut():
    f = _ham_app("_khoi_so_bai_hoc")
    goi = [n for n in ast.walk(f) if isinstance(n, ast.Call)
           and getattr(n.func, "id", "") == "_gia_cho_so_bai_hoc"]
    assert len(goi) == 1
    nut = [n.lineno for n in ast.walk(f) if isinstance(n, ast.Call)
           and ast.unparse(n.func) == "st.button"]
    assert nut and min(nut) < goi[0].lineno, "tải giá phải đứng SAU nút bấm"
    co_khoa = [n for n in ast.walk(f) if isinstance(n, ast.Constant)
               and n.value == "bai_hoc_co_gia"]
    assert co_khoa, "cờ đã-bấm-nút phải nằm trong session_state"


def test_app_dung_try_cho_ca_tai_gia_lan_dung_bang():
    f = _ham_app("_khoi_so_bai_hoc")
    thu = [n for n in ast.walk(f) if isinstance(n, ast.Try)]
    bao = [ast.unparse(t) for t in thu]
    assert any("_gia_cho_so_bai_hoc" in b for b in bao)
    assert any("bai_hoc_cho_so" in b for b in bao)
    for t in thu:
        assert t.handlers and any("st.warning" in ast.unparse(h) for h in t.handlers)


def test_app_bang_khong_tu_tinh_so_va_di_qua_ham_thuan():
    for ten, qua in (("_bang_bai_hoc", "dong_bang"), ("_bang_dong_gop", "bang_dong_gop")):
        f = _ham_app(ten)
        assert qua in {getattr(c.func, "attr", getattr(c.func, "id", ""))
                       for c in ast.walk(f) if isinstance(c, ast.Call)}, ten
        tinh = [n for n in ast.walk(f) if isinstance(n, ast.BinOp)
                and isinstance(n.op, (ast.Sub, ast.Div, ast.Mult, ast.Add))]
        assert not tinh, f"{ten} tự tính số"


def test_app_goi_khoi_trong_tab_lich_su_voi_nhat_ky_da_doc_san():
    goi = [n for n in ast.walk(_CAY_APP) if isinstance(n, ast.Call)
           and getattr(n.func, "id", "") == "_khoi_so_bai_hoc"]
    assert len(goi) == 1
    assert [ast.unparse(a) for a in goi[0].args] == ["_nk", "_nk_loi"]
    doc = [n for n in ast.walk(_CAY_APP) if isinstance(n, ast.Call)
           and getattr(n.func, "id", "") == "_doc_nhat_ky"]
    assert len(doc) == 1, "đọc Sheets lần hai"


# ── chạy THẬT các hàm hiện của app với một `st` giả ─────────────────────

class _St:
    """`st` giả: ghi lại mọi lệnh hiện để kiểm; không cần Streamlit chạy."""

    def __init__(self, bam_nut=False):
        self.bam_nut = bam_nut
        self.session_state = {}
        self.ghi = []

    def cache_data(self, *a, **k):
        return lambda f: f

    def _ghi(self, loai):
        return lambda *a, **k: self.ghi.append((loai, a, k))

    def __getattr__(self, ten):
        if ten in ("markdown", "caption", "info", "warning", "dataframe"):
            return self._ghi(ten)
        raise AttributeError(ten)

    def button(self, *a, **k):
        return self.bam_nut

    def spinner(self, *a, **k):
        return _Ctx()

    def columns(self, n):
        return [_Ctx() for _ in range(n)]


class _Ctx:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _chay_app(st, nk_rows, nk_loi=None, gia_ham=None, loi_gia=None):
    """Nạp các hàm sổ bài học TỪ app.py thật vào một không gian tên có `st` giả."""
    ten = ("_so", "_mau_dau", "_gia_cho_so_bai_hoc", "_bang_bai_hoc", "_bang_dong_gop",
           "_khoi_so_bai_hoc")
    mod = ast.Module(body=[_ham_app(t) for t in ten], type_ignores=[])
    ns = {"st": st, "pd": pd, "end_str": _END_STR_TEST, "price_multiplier": lambda d: 1.0,
          "start_str_phan_tich": _MOC_PHAN_TICH,
          "load_stock_data": lambda *a, **k: (None, "FAILED", [])}
    if gia_ham is not None:
        ns["load_stock_data"] = gia_ham
    exec(compile(ast.fix_missing_locations(mod), "app.py", "exec"), ns)
    if loi_gia is not None:
        def hong(*a, **k):
            raise loi_gia
        ns["_gia_cho_so_bai_hoc"] = hong
    ns["_khoi_so_bai_hoc"](nk_rows, nk_loi)
    return st.ghi


def _loai(ghi, loai):
    return [g for g in ghi if g[0] == loai]


@pytest.mark.parametrize("nk_rows, nk_loi", [
    (None, None), ([], None), ([_dong()], "Lỗi: không đọc được"), (None, "Lỗi")])
def test_app_NHAT_KY_rong_chua_cau_hinh_hoac_loi_thi_hien_THONG_BAO_khong_sap(nk_rows, nk_loi):
    ghi = _chay_app(_St(), nk_rows, nk_loi)
    assert _loai(ghi, "info"), "phải có thông báo thay cho bảng"
    assert not _loai(ghi, "dataframe")


def test_app_co_dong_nhat_ky_thi_dung_bang_va_noi_chua_tai_gia():
    ghi = _chay_app(_St(), [_dong(), _dong(trade_id=2, exit_date=None, loi_nhuan_rong_pct=None,
                                           trang_thai_lenh=Status.CLOSED)])
    bang = [g[1][0] for g in _loai(ghi, "dataframe")]
    assert len(bang) == 3                                  # bài học · nguyên nhân · đóng góp
    chu = " ".join(str(g[1][0]) for g in _loai(ghi, "caption"))
    assert "Chưa tải giá" in chu
    assert "chưa điền nửa ĐÓNG" in chu
    assert "chưa đủ lệnh để kết luận" in " ".join(str(g[1][0]) for g in _loai(ghi, "warning"))


def test_app_bam_nut_thi_goi_gia_CO_DEM_MOT_lan_va_ngành_hien_ra():
    goi = []

    def tai(ma, vao, ra, san):
        goi.append(ma)
        df = pd.DataFrame({"time": ["2026-09-02", "2026-09-10"],
                           "close": [100.0, 96.0]})
        return df, "OK", []

    ghi = _chay_app(_St(bam_nut=True), [_dong(), _dong(trade_id=2, symbol="VCB")], gia_ham=tai)
    assert sorted(goi) == sorted(set(goi)), "mỗi mã một lần"
    assert "STB" in goi and "ACB" in goi
    hang = _loai(ghi, "dataframe")[0][1][0].data
    assert (hang["Ngành"] != "—").any()


def test_app_tai_gia_HONG_thi_canh_bao_va_van_dung_bang():
    ghi = _chay_app(_St(bam_nut=True), [_dong()], loi_gia=RuntimeError("mất mạng"))
    assert "mất mạng" in " ".join(str(g[1][0]) for g in _loai(ghi, "warning"))
    assert len(_loai(ghi, "dataframe")) == 3


def test_app_ma_khong_tai_duoc_thi_noi_ten_ma():
    ghi = _chay_app(_St(bam_nut=True), [_dong()],
                    gia_ham=lambda *a, **k: (None, "FAILED", []))
    assert "Không tải được giá" in " ".join(str(g[1][0]) for g in _loai(ghi, "caption"))


def test_app_dung_bang_that_loi_thi_canh_bao_khong_sap(monkeypatch):
    def no(*a, **k):
        raise KeyError("x")
    monkeypatch.setattr(sbh, "bai_hoc_cho_so", no)
    ghi = _chay_app(_St(), [_dong()])
    assert "Chưa dựng được sổ bài học" in " ".join(str(g[1][0]) for g in _loai(ghi, "warning"))


def test_app_chua_co_lenh_nao_dong_thi_noi_ro_khong_ve_bang_rong():
    ghi = _chay_app(_St(), [_dong(exit_date=None, loi_nhuan_rong_pct=None,
                                  trang_thai_lenh=Status.OPEN)])
    assert not _loai(ghi, "dataframe")
    assert "Chưa có lệnh đóng nào có bài học" in " ".join(str(g[1][0]) for g in _loai(ghi, "info"))


# ── 13. đi qua đường THẬT: sổ lệnh -> nhật ký -> Sheets (giả) -> sổ bài học ─

def test_DUONG_THAT_dong_nhat_ky_doc_tu_Sheets_chay_duoc_qua_so_bai_hoc(monkeypatch):
    """Kiểu dữ liệu đọc ngược từ Sheets (số, ngày, ô rỗng) phải đi qua module thuần
    mà không cần dòng giả — hình dạng ấy là thứ app thật sẽ đưa vào."""
    import market_filter
    import paper_trading as pt
    import sheets_store as ss
    from paper_trading import PaperTradingJournal

    ngay = pd.bdate_range("2026-07-01", "2026-09-30")
    vni = pd.DataFrame({"time": ngay.strftime("%Y-%m-%d"),
                        "close": [1600.0 + i for i in range(len(ngay))],
                        "vni_ma50": [1550.0] * len(ngay)})
    monkeypatch.setattr(market_filter, "is_vni_bullish", lambda *a, **k: True)
    monkeypatch.setattr(market_filter, "get_vni_df", lambda: vni)
    monkeypatch.setattr(pt, "CHO_PHEP_MO_LENH_MOI", True)
    monkeypatch.setattr(pt, "MO_PHONG_TRUOT_GIA", False)
    kq = {"final_score": 70, "recommendation": "MUA", "data_quality": "OK",
          "score_breakdown": {"trend_score": 80.0, "volume_score": 70.0},
          "key_reasons": ["xu hướng tăng"],
          "analyses": {"risk": {"recommendations": {"entry_price": 100.0,
                                                    "stop_loss_price": 95.0,
                                                    "take_profit_price": 120.0}}}}
    j = PaperTradingJournal(":memory:", cho_phep_so_that=True)
    j.consider_entry("FPT", "2026-09-01", kq)
    j.fill_pending("FPT", "2026-09-03", 100.0)
    j.evaluate_open("FPT", "2026-09-04", {"open": 94, "high": 95, "low": 90, "close": 92})
    j.consider_entry("HPG", "2026-09-01", kq)
    j.fill_pending("HPG", "2026-09-03", 100.0)               # còn mở
    j.hoan_tat_nhat_ky(dict(zip(vni["time"], vni["close"])))
    sheet = ss.InMemorySheet()
    ss.push(j.db, sheet)
    dong = ss.doc_nhat_ky(sheet)
    bh = sbh.bai_hoc_cho_so(dong)
    assert [b["symbol"] for b in bh["bai_hoc"]] == ["FPT"]
    b = bh["bai_hoc"][0]
    assert b["ket_qua"] == sbh.KET_QUA_THUA and b["gap"] is True       # gap xuống 94 < SL 95
    tong = sum(v for v in b["phan"].values() if v is not None)
    assert tong == pytest.approx(b["loi_nhuan_rong_pct"], abs=1e-9)
    fpt = next(d for d in dong if d["symbol"] == "FPT")
    assert b["phan"]["thi_truong"] == fpt["ro_chuan_pct"]               # số nhật ký, không tính lại
    assert b["loi_nhuan_rong_pct"] == fpt["loi_nhuan_rong_pct"]
    assert bh["tong_hop"]["cau_luu_y"]


# ── 14. BƯỚC 168: cửa sổ giá đi qua CỔNG KIỂM ĐỊNH dữ liệu THẬT ─────────────
#
# Lỗi 140: BƯỚC 167 chỉ chạy với giá GIẢ (mỗi mã hai ngày), không ca nào đi qua
# `data_quality.validate_ohlcv`; trên máy thật mọi mã bị chặn `TOO_SHORT` vì cửa
# sổ xin giá bắt đầu đúng ở ngày vào sớm nhất của sổ còn non (vài phiên).

def _tai_qua_cong_kiem_dinh(ma, tu, den, san):
    """Bộ tải giả đúng hình `load_stock_data`: dựng bảng OHLCV MỌI phiên làm việc
    trong [tu, den] rồi cho CHÍNH `data_quality.validate_ohlcv` phán — bị chặn thì
    trả FAILED như `VNStockCollectorAgent.collect`. Không ngưỡng nào gõ ở đây."""
    ngay = pd.bdate_range(tu, den)
    gia = [100.0 + 0.1 * i for i in range(len(ngay))]
    df = pd.DataFrame({"time": ngay.strftime("%Y-%m-%d"), "open": gia, "high": gia,
                       "low": gia, "close": gia, "volume": [1_000_000] * len(ngay)})
    rep = data_quality.validate_ohlcv(df, symbol=ma, exchange=san, as_of=den)
    if rep.blocked:
        return None, "FAILED", []
    return df, "OK", []


#: Sổ còn non: lệnh vào cách ngày hôm nay (`_END_STR_TEST`) khoảng 10 phiên.
_SO_NON = [_dong(entry_date="2026-09-25", exit_date="2026-10-02")]


def test_LOI_THAT_cua_so_tu_ngay_vao_cua_so_non_BI_cong_kiem_dinh_chan():
    """Dựng lại lỗi: xin giá từ `tu_ngay_can_gia` thì mọi mã FAILED. Nếu test này
    xanh khi bộ tải giả KHÔNG chặn nữa thì các test dưới chứng minh được gì cũng vô nghĩa."""
    tu = sbh.tu_ngay_can_gia(_SO_NON)
    assert len(pd.bdate_range(tu, _END_STR_TEST)) < data_quality.SO_PHIEN_TOI_THIEU
    for ma in sbh.ma_can_gia(_SO_NON):
        _d, tt, _ = _tai_qua_cong_kiem_dinh(ma, tu, _END_STR_TEST, "HOSE")
        assert tt == "FAILED", ma


def test_cua_so_phan_tich_cua_app_DU_DAI_cho_cong_kiem_dinh():
    assert len(pd.bdate_range(_MOC_PHAN_TICH, _END_STR_TEST)) >= data_quality.SO_PHIEN_TOI_THIEU


def test_tu_ngay_tai_gia_lay_moc_SOM_HON_cua_hai_mốc():
    can = sbh.tu_ngay_can_gia(_SO_NON)
    assert sbh.tu_ngay_tai_gia(_SO_NON, _MOC_PHAN_TICH) == _MOC_PHAN_TICH < can
    xa = [_dong(entry_date="2020-01-02")]                  # vào TRƯỚC mốc phân tích
    assert sbh.tu_ngay_tai_gia(xa, _MOC_PHAN_TICH) == "2020-01-02"
    assert sbh.tu_ngay_tai_gia(_SO_NON, "2026-09-25 00:00:00") == "2026-09-25"
    assert sbh.tu_ngay_tai_gia(_SO_NON, None) == can       # thiếu mốc thứ hai: như cũ
    assert sbh.tu_ngay_tai_gia(_SO_NON, "") == can


def test_tu_ngay_tai_gia_khong_co_lenh_dong_thi_None():
    chua = [_dong(exit_date=None, loi_nhuan_rong_pct=None, trang_thai_lenh=Status.OPEN)]
    assert sbh.tu_ngay_tai_gia(chua, _MOC_PHAN_TICH) is None
    assert sbh.tu_ngay_tai_gia([], _MOC_PHAN_TICH) is None


def test_app_BAM_NUT_voi_so_non_van_co_gia_qua_cong_kiem_dinh_THAT():
    """Ca thật của lỗi 140: bấm nút trên sổ còn non, bộ tải đi qua cổng kiểm định."""
    ghi = _chay_app(_St(bam_nut=True), _SO_NON, gia_ham=_tai_qua_cong_kiem_dinh)
    chu = " ".join(str(g[1][0]) for g in _loai(ghi, "caption"))
    assert "Không tải được giá" not in chu, chu
    hang = _loai(ghi, "dataframe")[0][1][0].data
    assert (hang["Ngành"] != "—").any()


def test_app_truyen_MOC_CUA_SO_PHAN_TICH_vao_phep_tinh_moc_dau():
    """AST, không đọc `in`: `_khoi_so_bai_hoc` lấy mốc đầu qua `tu_ngay_tai_gia`
    với đúng tên `start_str_phan_tich`, và không còn xin giá từ `tu_ngay_can_gia`."""
    f = _ham_app("_khoi_so_bai_hoc")
    goi = [n for n in ast.walk(f) if isinstance(n, ast.Call)
           and getattr(n.func, "attr", "") == "tu_ngay_tai_gia"]
    assert len(goi) == 1 and [ast.unparse(a) for a in goi[0].args][1:] == ["start_str_phan_tich"]
    assert "tu_ngay_can_gia" not in {getattr(c.func, "attr", getattr(c.func, "id", ""))
                                     for c in ast.walk(f) if isinstance(c, ast.Call)}


def test_ngay_lich_su_phan_tich_la_nguon_cua_start_str_phan_tich():
    gan = next(n for n in _CAY_APP.body if isinstance(n, ast.Assign)
               and any(getattr(t, "id", "") == "start_str_phan_tich" for t in n.targets))
    assert "NGAY_LICH_SU_PHAN_TICH" in {x.id for x in ast.walk(gan.value) if isinstance(x, ast.Name)}


# ── ngưỡng của cổng kiểm định: MỘT hằng số, đường quét thật không đổi hành vi ──

def _bang_n_phien(n):
    ngay = pd.bdate_range("2026-01-05", periods=n)
    gia = [100.0 + 0.1 * i for i in range(n)]
    return (pd.DataFrame({"time": ngay.strftime("%Y-%m-%d"), "open": gia, "high": gia, "low": gia,
                          "close": gia, "volume": [1_000_000] * n}),
            ngay[-1].strftime("%Y-%m-%d"))


def test_cong_kiem_dinh_chan_DUNG_duoi_SO_PHIEN_TOI_THIEU():
    n = data_quality.SO_PHIEN_TOI_THIEU
    df, den = _bang_n_phien(n - 1)
    rep = data_quality.validate_ohlcv(df, as_of=den)
    assert rep.blocked and [i.code for i in rep.blockers] == ["TOO_SHORT"]
    df, den = _bang_n_phien(n)
    assert "TOO_SHORT" not in [i.code for i in data_quality.validate_ohlcv(df, as_of=den).issues]


def test_cong_kiem_dinh_so_rows_voi_HANG_SO_co_ten_khong_voi_so_tran():
    """AST: phép so `rep.rows < …` trong `validate_ohlcv` dùng tên `SO_PHIEN_TOI_THIEU`."""
    cay = ast.parse((GOC / "data_quality.py").read_text(encoding="utf-8"))
    f = next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == "validate_ohlcv")
    so = [c for c in ast.walk(f) if isinstance(c, ast.Compare)
          and ast.unparse(c.left) == "rep.rows" and isinstance(c.ops[0], ast.Lt)
          and not (isinstance(c.comparators[0], ast.BinOp))]
    assert len(so) == 1 and ast.unparse(so[0].comparators[0]) == "SO_PHIEN_TOI_THIEU"
