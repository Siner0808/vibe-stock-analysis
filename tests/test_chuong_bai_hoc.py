"""Chuông tiêu chí giai đoạn B — "100% lệnh đóng có bài học trong vòng 1 phiên" (BƯỚC 169).

Ba tầng, mỗi tầng có gác riêng:

  1. `so_bai_hoc.do_phu_bai_hoc` — hàm THUẦN định nghĩa phép đo. Mỗi ca dựng lại một
     tình huống thật của sổ: lệnh mở TRƯỚC nhật ký (không dòng nào, không được đỏ),
     lệnh đóng hôm nay chưa nửa ĐÓNG (trong hạn), lệnh đóng quá một phiên (đỏ), nửa
     ĐÓNG thiếu rổ chuẩn (đỏ), cuối tuần và ngày nghỉ lễ giữa ngày đóng và hôm nay
     (hạn đếm bằng PHIÊN, không bằng ngày lịch).
  2. `tools/chuong_bai_hoc.py` — kéo sổ, in, mã thoát 0 · 1 · 2. Chạy trên đường THẬT:
     `PaperTradingJournal` → `hoan_tat_nhat_ky` → `sheets_store.push` → Sheets giả →
     `keo_so_co_thu_lai` → chuông. Sheets lỗi / chưa cấu hình / lỗi bất ngờ là mã 2.
  3. Dây nối: app và workflow gọi đúng hàm đó (AST, không đọc `in`).

Dữ liệu là dòng GIẢ dựng theo `COT_NHAT_KY` và một sổ `:memory:` — đám mây không đọc
được Sheets thật và `CLAUDE.md` cấm chép số của sổ thật vào tài liệu.
"""
import ast
import datetime as dt
import importlib.util
import re
from pathlib import Path

import pandas as pd
import pytest

import lich_giao_dich
import nhat_ky_vi_sao as nk
import so_bai_hoc as sbh
import sheets_store as ss
from paper_trading import ExitReason, Status, Trade

GOC = Path(__file__).resolve().parent.parent


def _nap_tool():
    spec = importlib.util.spec_from_file_location(
        "chuong_bai_hoc_tool", GOC / "tools" / "chuong_bai_hoc.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


tool = _nap_tool()

MOC = sbh.NGAY_NHAT_KY_BAT_DAU


def _lui(ngay, so_ngay):
    return (dt.date.fromisoformat(ngay) - dt.timedelta(days=so_ngay)).isoformat()


# Lịch tháng 10/2026 dùng ở các ca (đã kiểm ở test dưới): 02/10 thứ Sáu · 03–04/10 cuối
# tuần · 05/10 thứ Hai · 06/10 thứ Ba · 07/10 thứ Tư.
T6, T7, CN = "2026-10-02", "2026-10-03", "2026-10-04"
T2, T3, T4 = "2026-10-05", "2026-10-06", "2026-10-07"


def test_lich_thang_10_dung_nhu_cac_ca_gia_dinh():
    thu = {d: dt.date.fromisoformat(d).weekday() for d in (T6, T7, CN, T2, T3, T4)}
    assert thu == {T6: 4, T7: 5, CN: 6, T2: 0, T3: 1, T4: 2}
    assert all(lich_giao_dich.co_phien(d) for d in (T6, T2, T3, T4))
    assert not lich_giao_dich.co_phien(T7) and not lich_giao_dich.co_phien(CN)


def _lenh(trade_id, vao="2026-09-30", ra="2026-10-01", ma="AAA"):
    return {"trade_id": trade_id, "symbol": ma, "entry_date": vao, "exit_date": ra}


def _dong(trade_id, *, nua_dong=True, ro=0.5, lnr=-2.0, ra="2026-10-01"):
    d = {c: None for c in nk.COT_NHAT_KY}
    d.update(trade_id=trade_id, symbol="AAA", signal_date="2026-09-29",
             entry_date="2026-09-30")
    if nua_dong:
        d.update(exit_date=ra, loi_nhuan_rong_pct=lnr, ro_chuan_pct=ro)
    return d


def _do(lenh, dong_nk, hom_nay, lich=None):
    return sbh.do_phu_bai_hoc(lenh, dong_nk, hom_nay, lich)


def _ids(kq, nhom):
    return [m["trade_id"] for m in kq[nhom]]


# ── 1. phiên kế tiếp theo lịch của dự án ─────────────────────────────────────

def test_phien_ke_tiep_la_thu_Hai_sau_thu_Sau_va_ngay_ke_sau_thu_Ba():
    assert sbh.phien_ke_tiep(T6) == T2
    assert sbh.phien_ke_tiep(T7) == T2
    assert sbh.phien_ke_tiep(T2) == T3


def test_phien_ke_tiep_nhay_qua_ngay_nghi_le_cua_LICH_DU_AN(monkeypatch):
    monkeypatch.setattr(lich_giao_dich, "NGAY_NGHI",
                        lich_giao_dich.NGAY_NGHI | {T2, T3})
    assert sbh.phien_ke_tiep(T6) == T4


def test_phien_ke_tiep_thuc_te_qua_ky_nghi_Quoc_khanh():
    assert sbh.phien_ke_tiep("2026-08-28") == "2026-09-03"


def test_phien_ke_tiep_NGOAI_pham_vi_lich_la_None_khong_doan():
    assert sbh.phien_ke_tiep("2026-12-31") is None
    assert sbh.phien_ke_tiep("2027-03-02") is None


def test_phien_ke_tiep_nhan_ngay_co_gio():
    assert sbh.phien_ke_tiep("2026-10-02 07:00:00") == T2


class _LichGia:
    """Lịch giả đúng hai hàm mà `phien_ke_tiep` được phép hỏi."""

    def __init__(self, phien):
        self.phien = set(phien)

    def trong_pham_vi(self, ngay):
        return "2026-01-01" <= ngay <= "2026-12-31"

    def co_phien(self, ngay):
        return ngay in self.phien


def test_phien_ke_tiep_dung_lich_TIEM_VAO_khong_dung_lich_cung():
    lich = _LichGia({"2026-10-08"})
    assert sbh.phien_ke_tiep("2026-10-01", lich) == "2026-10-08"
    assert sbh.phien_ke_tiep("2026-10-08", lich) is None       # hết lịch trước cuối phạm vi


def test_phien_ke_tiep_KHONG_go_ngay_nghi_hay_so_ngay_cung():
    f = next(n for n in ast.parse((GOC / "so_bai_hoc.py").read_text(encoding="utf-8")).body
             if isinstance(n, ast.FunctionDef) and n.name == "phien_ke_tiep")
    so = [n.value for n in ast.walk(f) if isinstance(n, ast.Constant) and isinstance(n.value, (int, float))
          and not isinstance(n.value, bool)]
    chuoi_ngay = [n.value for n in ast.walk(f) if isinstance(n, ast.Constant)
                  and isinstance(n.value, str) and re.search(r"\d{4}-\d{2}-\d{2}", n.value)]
    assert so == [1], f"chỉ được bước 1 ngày, đang có {so}"
    assert not chuoi_ngay, f"gõ ngày nghỉ lễ trong hàm: {chuoi_ngay}"
    goi = {ast.unparse(c.func) for c in ast.walk(f) if isinstance(c, ast.Call)}
    assert {"lich.trong_pham_vi", "lich.co_phien"} <= goi
    assert not any("weekday" in g for g in goi), "đếm cuối tuần là việc của lịch, không của hàm này"


# ── 2. thế nào là "có bài học" ───────────────────────────────────────────────

def test_ly_do_thieu_bai_hoc_ba_nhanh_va_du():
    assert sbh.ly_do_thieu_bai_hoc(None) == sbh.LY_DO_KHONG_CO_DONG
    assert sbh.ly_do_thieu_bai_hoc(_dong(1, nua_dong=False)) == sbh.LY_DO_CHUA_NUA_DONG
    assert sbh.ly_do_thieu_bai_hoc(_dong(1, ro=None)) == sbh.LY_DO_THIEU_RO_CHUAN
    assert sbh.ly_do_thieu_bai_hoc(_dong(1)) is None


def test_ly_do_thieu_bai_hoc_khong_doi_hoi_gia_sau_nen_nganh_va_cat_lo_sat_khong_thuoc_tieu_chi():
    """Một lệnh thoát bằng cắt lỗ, chưa có chuỗi giá sau thoát, chưa có số ngành: vẫn CÓ bài học."""
    d = _dong(1)
    d.update(exit_reason=ExitReason.STOP_LOSS, entry_price=100.0, exit_price=94.0,
             stop_loss_ban_dau=95.0)
    assert sbh.ly_do_thieu_bai_hoc(d) is None
    b = sbh.lap_bai_hoc(d)
    assert b["cat_lo_sat"]["trang_thai"] == sbh.CLS_CHUA_DU and b["phan"] is not None


@pytest.mark.parametrize("nua_dong", [True, False])
@pytest.mark.parametrize("lnr", [None, -2.0, 0.0, 3.5])
@pytest.mark.parametrize("ro", [None, -1.0, 0.0, 2.0])
def test_co_bai_hoc_KHOP_voi_lap_bai_hoc_tren_luoi(nua_dong, lnr, ro):
    """Tiêu chí đếm "có bài học" bằng cùng điều kiện mà `lap_bai_hoc` dựng được bản ghi
    có phân rã: một công thức, không hai."""
    d = _dong(1, nua_dong=nua_dong, lnr=lnr, ro=ro)
    co = sbh.ly_do_thieu_bai_hoc(d) is None
    if sbh.lenh_da_dong(d):
        assert co == (sbh.lap_bai_hoc(d)["phan"] is not None)
    else:
        assert not co


def test_ly_do_thieu_bai_hoc_goi_phan_ra_khong_chep_cong_thuc():
    f = next(n for n in ast.parse((GOC / "so_bai_hoc.py").read_text(encoding="utf-8")).body
             if isinstance(n, ast.FunctionDef) and n.name == "ly_do_thieu_bai_hoc")
    goi = {ast.unparse(c.func) for c in ast.walk(f) if isinstance(c, ast.Call)}
    assert {"lenh_da_dong", "phan_ra"} <= goi


# ── 3. MỐC nhật ký: gác hằng số ─────────────────────────────────────────────

def test_moc_nhat_ky_la_ngay_luot_quet_dau_tien_cua_BUOC_138():
    """Ngày ấy có trong tiêu đề BƯỚC 138 (bật workflow, lượt quét đầu) — nguồn của hằng số."""
    ngay = dt.date.fromisoformat(MOC).strftime("%d/%m/%Y")
    tieu_de = [d for d in (GOC / "docs" / "STATE.md").read_text(encoding="utf-8").splitlines()
               if d.startswith("## BƯỚC 138 ")]
    assert len(tieu_de) == 1 and f"({ngay})" in tieu_de[0], (ngay, tieu_de)
    gom = [d for d in (GOC / "docs" / "STATE.md").read_text(encoding="utf-8").splitlines()
           if d.startswith("## BƯỚC 134 ")]
    assert len(gom) == 1 and f"({ngay})" in gom[0], "BƯỚC 134 (nối nhật ký) cùng ngày"


def test_moc_nhat_ky_chi_duoc_GO_MOT_LAN_trong_ma():
    """Không ngày nhật ký thứ hai ở so_bai_hoc / chuông / app: gõ ở hai nơi sẽ trôi."""
    for ten in ("so_bai_hoc.py", "tools/chuong_bai_hoc.py", "app.py"):
        cay = ast.parse((GOC / ten).read_text(encoding="utf-8"))
        dem = [n for n in ast.walk(cay) if isinstance(n, ast.Constant) and n.value == MOC]
        assert len(dem) == (1 if ten == "so_bai_hoc.py" else 0), (ten, len(dem))
    cay = ast.parse((GOC / "so_bai_hoc.py").read_text(encoding="utf-8"))
    gan = [n for n in cay.body if isinstance(n, ast.Assign)
           and any(getattr(t, "id", "") == "NGAY_NHAT_KY_BAT_DAU" for t in n.targets)]
    assert len(gan) == 1 and ast.literal_eval(gan[0].value) == MOC


# ── 4. do_phu_bai_hoc: các ca ────────────────────────────────────────────────

def test_LENH_TRUOC_NHAT_KY_khong_dong_nhat_ky_nao_KHONG_do():
    """Dựng lại lỗi "đỏ vĩnh viễn": lệnh mở trước nhật ký không có dòng nào."""
    kq = _do([_lenh(1, vao=_lui(MOC, 1), ra="2026-09-29")], [], T3)
    assert kq["trang_thai"] == sbh.TT_XANH
    assert _ids(kq, "truoc_nhat_ky") == [1] and kq["n_truoc_nhat_ky"] == 1
    assert kq["n_vi_pham"] == 0 and kq["n_tinh"] == 0


def test_BIEN_moc_ngay_vao_dung_bang_moc_thi_TINH():
    kq = _do([_lenh(1, vao=MOC, ra="2026-09-29")], [], T3)
    assert _ids(kq, "vi_pham") == [1] and kq["n_truoc_nhat_ky"] == 0
    kq = _do([_lenh(2, vao=_lui(MOC, 1), ra="2026-09-29")], [], T3)
    assert _ids(kq, "truoc_nhat_ky") == [2]


def test_LENH_DONG_HOM_NAY_chua_nua_DONG_con_TRONG_HAN():
    kq = _do([_lenh(1, ra=T2)], [_dong(1, nua_dong=False)], T2)
    assert _ids(kq, "trong_han") == [1] and kq["trang_thai"] == sbh.TT_XANH
    assert kq["trong_han"][0]["han"] == T3


def test_LENH_DONG_phien_truoc_nua_chua_nua_DONG_la_VI_PHAM():
    kq = _do([_lenh(1, ra=T6)], [_dong(1, nua_dong=False)], T3)
    assert _ids(kq, "vi_pham") == [1] and kq["trang_thai"] == sbh.TT_VI_PHAM
    m = kq["vi_pham"][0]
    assert m["ly_do"] == sbh.LY_DO_CHUA_NUA_DONG and m["han"] == T2 and m["exit_date"] == T6


def test_LENH_khong_co_dong_nhat_ky_qua_han_la_VI_PHAM_kem_ly_do():
    kq = _do([_lenh(1, ra=T6)], [], T3)
    assert kq["vi_pham"][0]["ly_do"] == sbh.LY_DO_KHONG_CO_DONG


def test_CO_nua_DONG_nhung_THIEU_ro_chuan_qua_han_la_VI_PHAM():
    kq = _do([_lenh(1, ra=T6)], [_dong(1, ro=None, ra=T6)], T3)
    assert kq["vi_pham"][0]["ly_do"] == sbh.LY_DO_THIEU_RO_CHUAN


def test_thieu_ro_chuan_nhung_chua_qua_han_thi_TRONG_HAN_khong_do():
    kq = _do([_lenh(1, ra=T6)], [_dong(1, ro=None, ra=T6)], T2)
    assert _ids(kq, "trong_han") == [1] and kq["trang_thai"] == sbh.TT_XANH


def test_LENH_co_bai_hoc_la_CO_du_dong_hom_nay_hay_cach_ca_tuan():
    kq = _do([_lenh(1, ra=T6), _lenh(2, ra="2026-10-01")],
             [_dong(1, ra=T6), _dong(2)], T3)
    assert sorted(_ids(kq, "co")) == [1, 2] and kq["n_vi_pham"] == 0
    assert kq["n_co"] == 2 and kq["n_den_han"] == 2 and kq["trang_thai"] == sbh.TT_XANH


@pytest.mark.parametrize("hom_nay, ket_qua", [
    (T6, "trong_han"), (T7, "trong_han"), (CN, "trong_han"), (T2, "trong_han"),
    (T3, "vi_pham")])
def test_HAN_DEM_BANG_PHIEN_cuoi_tuan_giua_ngay_dong_va_hom_nay_khong_lam_qua_han(hom_nay, ket_qua):
    """Đóng thứ Sáu 02/10: hạn hết thứ Hai 05/10. Đếm bằng ngày lịch thì Chủ nhật (hai
    ngày sau) đã quá hạn — phép đếm sai đơn vị mà `market_filter._tre_phien` từng mắc."""
    kq = _do([_lenh(1, ra=T6)], [_dong(1, nua_dong=False)], hom_nay)
    assert _ids(kq, ket_qua) == [1], (hom_nay, {k: kq[k] for k in ("trong_han", "vi_pham")})


@pytest.mark.parametrize("hom_nay, ket_qua", [(T3, "trong_han"), (T4, "vi_pham")])
def test_BIEN_han_hom_nay_dung_ngay_han_van_con_trong_han(hom_nay, ket_qua):
    """Đóng thứ Hai 05/10: hạn hết thứ Ba 06/10. Thứ Ba còn trong hạn, thứ Tư quá hạn."""
    kq = _do([_lenh(1, ra=T2)], [_dong(1, nua_dong=False)], hom_nay)
    assert _ids(kq, ket_qua) == [1]


@pytest.mark.parametrize("hom_nay, ket_qua", [(T3, "trong_han"), (T4, "vi_pham")])
def test_NGAY_NGHI_LE_giua_ngay_dong_va_hom_nay_day_han_lui_theo_lich(monkeypatch, hom_nay, ket_qua):
    """Thứ Hai 05/10 nghỉ lễ (lịch tiêm vào): đóng thứ Sáu 02/10 thì hạn hết thứ Ba 06/10."""
    monkeypatch.setattr(lich_giao_dich, "NGAY_NGHI", lich_giao_dich.NGAY_NGHI | {T2})
    kq = _do([_lenh(1, ra=T6)], [_dong(1, nua_dong=False)], hom_nay)
    assert _ids(kq, ket_qua) == [1]
    assert (kq["trong_han"] or kq["vi_pham"])[0]["han"] == T3


def test_LICH_KHONG_PHU_toi_han_thi_CHUA_KIEM_DUOC_khong_xanh():
    kq = _do([_lenh(1, ra="2026-12-31")], [_dong(1, nua_dong=False)], "2027-01-06")
    assert _ids(kq, "khong_kiem_duoc") == [1]
    assert kq["trang_thai"] == sbh.TT_CHUA_KIEM_DUOC
    assert "lịch phiên không phủ" in kq["khong_kiem_duoc"][0]["ly_do"]


def test_VI_PHAM_thang_CHUA_KIEM_DUOC_khi_co_ca_hai():
    kq = _do([_lenh(1, ra=T6), _lenh(2, ra="2026-12-31")],
             [_dong(1, nua_dong=False), _dong(2, nua_dong=False)], "2027-01-06")
    assert kq["n_vi_pham"] == 1 and kq["n_khong_kiem_duoc"] == 1
    assert kq["trang_thai"] == sbh.TT_VI_PHAM


@pytest.mark.parametrize("lenh", [
    {"trade_id": 1, "symbol": "AAA", "entry_date": None, "exit_date": T6},
    {"trade_id": 1, "symbol": "AAA", "entry_date": "", "exit_date": T6},
    {"trade_id": 1, "symbol": "AAA", "entry_date": "2026-09-30", "exit_date": None},
])
def test_THIEU_ngay_trong_so_lenh_thi_CHUA_KIEM_DUOC(lenh):
    kq = _do([lenh], [_dong(1, nua_dong=False)], T3)
    assert _ids(kq, "khong_kiem_duoc") == [1] and kq["trang_thai"] == sbh.TT_CHUA_KIEM_DUOC


def test_thieu_ngay_dong_nhung_DA_co_bai_hoc_thi_van_la_CO():
    kq = _do([_lenh(1, ra=None)], [_dong(1)], T3)
    assert _ids(kq, "co") == [1] and kq["trang_thai"] == sbh.TT_XANH


def test_MOI_lenh_roi_vao_DUNG_MOT_nhom():
    lenh = [_lenh(1, vao=_lui(MOC, 3), ra="2026-09-25"), _lenh(2, ra=T6), _lenh(3, ra=T6),
            _lenh(4, ra=T2), _lenh(5, ra=T6), _lenh(6, ra="2026-12-31"),
            {"trade_id": 7, "symbol": "AAA", "entry_date": None, "exit_date": T6}]
    dong_nk = [_dong(2), _dong(3, nua_dong=False), _dong(4, nua_dong=False),
               _dong(6, nua_dong=False), _dong(7, nua_dong=False)]
    kq = _do(lenh, dong_nk, T3)
    nhom = ("co", "trong_han", "vi_pham", "truoc_nhat_ky", "khong_kiem_duoc")
    thay = [i for k in nhom for i in _ids(kq, k)]
    assert sorted(thay) == [1, 2, 3, 4, 5, 6, 7], {k: _ids(kq, k) for k in nhom}
    assert len(thay) == len(set(thay))
    assert (_ids(kq, "co"), _ids(kq, "trong_han"), _ids(kq, "truoc_nhat_ky")) == ([2], [4], [1])
    assert sorted(_ids(kq, "vi_pham")) == [3, 5] and sorted(_ids(kq, "khong_kiem_duoc")) == [6, 7]
    assert kq["n_tinh"] + kq["n_truoc_nhat_ky"] == len(lenh)


def test_dem_khop_danh_sach_va_n_den_han_la_co_cong_vi_pham():
    kq = _do([_lenh(1, ra=T6), _lenh(2, ra=T6), _lenh(3, ra=T2)],
             [_dong(1, ra=T6), _dong(2, nua_dong=False), _dong(3, nua_dong=False)], T3)
    for k, n in (("co", "n_co"), ("trong_han", "n_trong_han"), ("vi_pham", "n_vi_pham"),
                 ("truoc_nhat_ky", "n_truoc_nhat_ky"), ("khong_kiem_duoc", "n_khong_kiem_duoc")):
        assert kq[n] == len(kq[k]), k
    assert kq["n_den_han"] == kq["n_co"] + kq["n_vi_pham"] == 2


def test_rong_la_XANH_va_cau_noi_chua_co_gi_de_do():
    kq = _do([], [], T3)
    assert kq["trang_thai"] == sbh.TT_XANH and kq["n_tinh"] == 0
    assert "chưa có gì để đo" in sbh.cau_tieu_chi_b(kq)


def test_LECH_TRANG_THAI_nhat_ky_co_nua_DONG_ma_trades_khong_noi_CLOSED_chi_de_biet():
    kq = _do([_lenh(1, ra=T6)], [_dong(1, ra=T6), _dong(9, ra=T6)], T3)
    assert kq["lech_trang_thai"] == ["9"] and kq["trang_thai"] == sbh.TT_XANH
    assert 9 not in [m["trade_id"] for k in ("co", "vi_pham", "trong_han") for m in kq[k]]


def test_hom_nay_RONG_thi_no_khong_doan():
    for hom in ("", None):
        with pytest.raises(ValueError):
            _do([_lenh(1)], [], hom)


def test_hom_nay_co_gio_van_so_duoc():
    assert _ids(_do([_lenh(1, ra=T6)], [_dong(1, nua_dong=False)], f"{T2} 16:53:00"), "trong_han") == [1]


def test_TAT_DINH_khong_sua_dau_vao():
    import copy
    lenh = [_lenh(2, ra=T6), _lenh(1, ra=T6)]
    dong_nk = [_dong(1, nua_dong=False)]
    truoc = copy.deepcopy((lenh, dong_nk))
    a, b = _do(lenh, dong_nk, T3), _do(lenh, dong_nk, T3)
    assert a == b and (lenh, dong_nk) == truoc


# ── 5. dựng quần thể lệnh đã đóng ────────────────────────────────────────────

def _trade(i, *, st=Status.CLOSED, created=2_000.0, vao="2026-09-30", ra=T6):
    return Trade(id=i, symbol="AAA", signal_date="2026-09-29", entry_date=vao, entry_price=100.0,
                 exit_date=ra, exit_price=95.0, exit_reason=ExitReason.STOP_LOSS, stop_loss=95.0,
                 take_profit=120.0, size_pct=5.0, entry_score=70, status=st, created_at=created)


def test_lenh_dong_tu_trades_chi_lay_CLOSED_tien_ve_truoc():
    ra = sbh.lenh_dong_tu_trades([
        _trade(1), _trade(2, st=Status.OPEN), _trade(3, st=Status.PENDING),
        _trade(4, st=Status.CLOSING), _trade(5, st=Status.HUY), _trade(6, created=None)])
    assert [r["trade_id"] for r in ra] == [1]
    assert ra[0] == {"trade_id": 1, "symbol": "AAA", "entry_date": "2026-09-30", "exit_date": T6}


def test_lenh_dong_tu_trades_loai_lo_ghi_hang_loat():
    """Một lô ≥ `TOI_THIEU_LENH_LO` lệnh ghi trong vài giây mà tín hiệu trải ≥ 90 ngày là
    một lượt MÔ PHỎNG — không phải lệnh tiến về trước, kể cả khi đã đóng."""
    import paper_metrics
    lo = []
    for i in range(paper_metrics.TOI_THIEU_LENH_LO):
        t = _trade(100 + i, created=5_000.0 + i)
        t.signal_date = (dt.date(2025, 1, 1) + dt.timedelta(days=paper_metrics.TOI_THIEU_NGAY_TRAI * i)
                         ).isoformat()
        lo.append(t)
    assert sbh.lenh_dong_tu_trades(lo + [_trade(1, created=9_000_000.0)]) == [
        {"trade_id": 1, "symbol": "AAA", "entry_date": "2026-09-30", "exit_date": T6}]


def test_lenh_dong_tu_trades_di_qua_lenh_tien_ve_truoc_cua_paper_metrics():
    f = next(n for n in ast.parse((GOC / "so_bai_hoc.py").read_text(encoding="utf-8")).body
             if isinstance(n, ast.FunctionDef) and n.name == "lenh_dong_tu_trades")
    goi = {ast.unparse(c.func) for c in ast.walk(f) if isinstance(c, ast.Call)}
    assert "paper_metrics.lenh_tien_ve_truoc" in goi


def test_lenh_dong_tu_nhat_ky_lay_trang_thai_va_ngay_cua_SO_LENH():
    d_dong = {**_dong(1, nua_dong=False), "trang_thai_lenh": Status.CLOSED,
              "ngay_vao_lenh": "2026-09-30", "ngay_dong_lenh": T6}
    d_mo = {**_dong(2, nua_dong=False), "trang_thai_lenh": Status.OPEN,
            "ngay_vao_lenh": "2026-09-30", "ngay_dong_lenh": None}
    d_thieu = {**_dong(3, nua_dong=False), "trang_thai_lenh": None}
    ra = sbh.lenh_dong_tu_nhat_ky([d_dong, d_mo, d_thieu])
    assert ra == [{"trade_id": 1, "symbol": "AAA", "entry_date": "2026-09-30", "exit_date": T6}]


def test_lenh_dong_tu_nhat_ky_ngay_CUA_SO_LENH_thang_ngay_cua_nhat_ky():
    """Dòng chưa có nửa ĐÓNG: `exit_date` của nhật ký rỗng dù lệnh đã đóng — ngày thật ở
    sổ lệnh. Khoá có mà rỗng thì GIỮ rỗng (không lùi về ngày của nhật ký)."""
    d = {**_dong(1, ra=T6), "trang_thai_lenh": Status.CLOSED,
         "ngay_vao_lenh": None, "ngay_dong_lenh": "2026-10-01"}
    ra = sbh.lenh_dong_tu_nhat_ky([d])
    assert ra[0]["entry_date"] is None and ra[0]["exit_date"] == "2026-10-01"
    d2 = {**_dong(2, ra=T6), "trang_thai_lenh": Status.CLOSED}          # không khoá → lùi về nhật ký
    assert sbh.lenh_dong_tu_nhat_ky([d2])[0]["exit_date"] == T6


# ── 6. câu kết luận ──────────────────────────────────────────────────────────

def test_cau_tieu_chi_b_noi_du_cac_nhom_va_khong_co_so_lai_lo():
    kq = _do([_lenh(1, ra=T6), _lenh(2, ra=T6), _lenh(3, ra=T2), _lenh(4, ra="2026-12-31"),
              _lenh(5, vao=_lui(MOC, 5), ra="2026-09-20")],
             [_dong(1, ra=T6), _dong(2, nua_dong=False), _dong(3, nua_dong=False),
              _dong(4, nua_dong=False)], T3)
    cau = sbh.cau_tieu_chi_b(kq)
    assert cau.startswith("Tiêu chí B: 1/2 lệnh đóng có bài học")
    assert "1 đang trong hạn" in cau and "1 QUÁ HẠN" in cau and "1 chưa kiểm được" in cau
    assert "1 trước nhật ký — không tính" in cau
    assert "\n" not in cau, "MỘT dòng"
    assert "chuong_bai_hoc" not in cau
    assert "chuong_bai_hoc" in sbh.cau_tieu_chi_b(kq, chi_thay_dong_nhat_ky=True)


def test_cau_tieu_chi_b_chi_in_nhom_co_that():
    cau = sbh.cau_tieu_chi_b(_do([_lenh(1, ra=T6)], [_dong(1, ra=T6)], T3))
    assert "QUÁ HẠN" not in cau and "đang trong hạn" not in cau and "chưa kiểm được" not in cau
    assert cau.startswith("Tiêu chí B: 1/1")


# ── 7. sheets_store.doc_nhat_ky: ngày của SỔ LỆNH ─────────────────────────────

@pytest.fixture
def moi_truong(monkeypatch):
    import market_filter
    import paper_trading as pt
    ngay = pd.bdate_range("2026-09-01", "2026-10-30")
    vni = pd.DataFrame({"time": ngay.strftime("%Y-%m-%d"),
                        "close": [1600.0 + i for i in range(len(ngay))],
                        "vni_ma50": [1550.0] * len(ngay)})
    monkeypatch.setattr(market_filter, "is_vni_bullish", lambda *a, **k: True)
    monkeypatch.setattr(market_filter, "get_vni_df", lambda: vni)
    monkeypatch.setattr(pt, "CHO_PHEP_MO_LENH_MOI", True)
    monkeypatch.setattr(pt, "MO_PHONG_TRUOT_GIA", False)
    return dict(zip(vni["time"], vni["close"]))


def _kq():
    return {"final_score": 70, "recommendation": "MUA", "data_quality": "OK",
            "score_breakdown": {"trend_score": 80.0, "volume_score": 70.0},
            "key_reasons": ["xu hướng tăng"],
            "analyses": {"risk": {"recommendations": {"entry_price": 100.0,
                                                      "stop_loss_price": 95.0,
                                                      "take_profit_price": 120.0}}}}


def _vao_dong(j, ma, tin_hieu, khop, ra=None):
    """Mở -> khớp -> (đóng bằng gap xuống dưới cắt lỗ). Trả mã lệnh."""
    tid = j.consider_entry(ma, tin_hieu, _kq())
    j.fill_pending(ma, khop, 100.0)
    if ra:
        j.evaluate_open(ma, ra, {"open": 94, "high": 95, "low": 90, "close": 92})
    return tid


def _so_that(gia_vni):
    """Sổ có đủ ba hạng lệnh như sổ thật sau BƯỚC 134: (1) mở TRƯỚC khi có nhật ký — KHÔNG
    có dòng nào; (2) mở sau, đóng, ĐÃ điền nửa ĐÓNG; (3) mở sau, đóng, CHƯA điền nửa ĐÓNG."""
    from paper_trading import PaperTradingJournal
    j = PaperTradingJournal(":memory:", cho_phep_so_that=True)
    j.ghi_nhat_ky = False                                   # trước BƯỚC 134
    ids = {"truoc": _vao_dong(j, "AAA", "2026-09-22", "2026-09-23", "2026-09-24")}
    j.ghi_nhat_ky = True
    ids["co"] = _vao_dong(j, "BBB", "2026-09-29", "2026-09-30", "2026-10-01")
    j.hoan_tat_nhat_ky(gia_vni)                              # điền nửa ĐÓNG của BBB
    ids["thieu"] = _vao_dong(j, "CCC", "2026-09-29", "2026-09-30", T6)   # đóng SAU lượt điền
    return j, ids


class SheetGhiLai(ss.InMemorySheet):
    def __init__(self):
        super().__init__()
        self.doc, self.ghi = [], []

    def read_rows(self, tab):
        self.doc.append(tab)
        return super().read_rows(tab)

    def write_all(self, tab, rows):
        self.ghi.append(("write_all", tab))
        super().write_all(tab, rows)

    def append_rows(self, tab, rows):
        self.ghi.append(("append_rows", tab))
        super().append_rows(tab, rows)


def test_doc_nhat_ky_dua_ngay_vao_ngay_dong_tu_tab_trades(moi_truong):
    j, ids = _so_that(moi_truong)
    sheet = ss.InMemorySheet()
    ss.push(j.db, sheet)
    dong = {d["trade_id"]: d for d in ss.doc_nhat_ky(sheet)}
    assert ids["truoc"] not in dong, "lệnh trước nhật ký không có dòng"
    thieu = dong[ids["thieu"]]
    assert thieu["exit_date"] is None, "phép kiểm cần nửa ĐÓNG còn rỗng"
    assert thieu["ngay_vao_lenh"] == "2026-09-30" and thieu["ngay_dong_lenh"] == T6
    assert thieu["trang_thai_lenh"] == Status.CLOSED
    assert dong[ids["co"]]["ngay_dong_lenh"] == dong[ids["co"]]["exit_date"] == "2026-10-01"


def test_doc_nhat_ky_lenh_chua_dong_thi_ngay_dong_la_None(moi_truong):
    from paper_trading import PaperTradingJournal
    j = PaperTradingJournal(":memory:", cho_phep_so_that=True)
    j.consider_entry("DDD", "2026-09-29", _kq())
    sheet = ss.InMemorySheet()
    ss.push(j.db, sheet)
    d = ss.doc_nhat_ky(sheet)[0]
    assert d["ngay_vao_lenh"] is None and d["ngay_dong_lenh"] is None
    assert d["trang_thai_lenh"] == Status.PENDING


def test_doc_nhat_ky_van_chi_doc_hai_tab_va_khong_ghi(moi_truong):
    j, _ = _so_that(moi_truong)
    sheet = SheetGhiLai()
    ss.push(j.db, sheet)
    sheet.doc.clear()
    sheet.ghi.clear()
    ss.doc_nhat_ky(sheet)
    assert set(sheet.doc) == {ss.TAB_NHAT_KY, ss.TAB_TRADES} and sheet.ghi == []


# ── 8. chuông qua đường THẬT ─────────────────────────────────────────────────

def _chay(moi_truong, hom_nay, capsys, sheet=None):
    j, ids = _so_that(moi_truong)
    sheet = sheet or SheetGhiLai()
    ss.push(j.db, sheet)
    sheet.doc.clear()
    sheet.ghi.clear()
    ma = tool.main(backend=sheet, hom_nay=hom_nay)
    return ma, capsys.readouterr().out, ids, sheet


def test_CHUONG_qua_han_thi_DO_ma_1_va_chi_dung_dung_lenh_thieu(moi_truong, capsys):
    """CCC đóng thứ Sáu 02/10, nửa ĐÓNG chưa điền; đo thứ Ba 06/10 = quá hạn. AAA (mở trước
    nhật ký, không dòng nào) KHÔNG làm chuông đỏ; BBB (đã nửa ĐÓNG) có bài học."""
    ma, ra, ids, sheet = _chay(moi_truong, T3, capsys)
    assert ma == tool.MA_VI_PHAM, ra
    assert "CCC" in ra and f"#{ids['thieu']}" in ra
    assert "AAA" not in ra and "BBB" not in ra, "chỉ lệnh thiếu bài học mới được nêu tên"
    assert "1/2 lệnh đóng có bài học" in ra
    assert "1 trước nhật ký — không tính" in ra
    assert sbh.LY_DO_CHUA_NUA_DONG in ra
    assert "::error::" in ra


def test_CHUONG_trong_han_thi_XANH_ma_0(moi_truong, capsys):
    ma, ra, ids, _ = _chay(moi_truong, T2, capsys)          # thứ Hai 05/10 = đúng ngày hạn
    assert ma == tool.MA_XANH, ra
    assert "1 đang trong hạn" in ra and "::error::" not in ra
    assert "CCC" in ra, "lệnh đang trong hạn vẫn được liệt kê để biết"


def test_CHUONG_cuoi_tuan_van_xanh(moi_truong, capsys):
    ma, ra, *_ = _chay(moi_truong, CN, capsys)
    assert ma == tool.MA_XANH, ra


def test_CHUONG_hom_nay_ngoai_lich_nhung_han_cua_lenh_trong_lich_van_do_duoc(moi_truong, capsys):
    """Lệnh CCC quá hạn từ lâu và hạn của nó (05/10/2026) NẰM trong lịch: đo được, là vi phạm
    — không phải 'chưa biết'. Chưa biết chỉ khi chính HẠN rơi ngoài lịch (xem ca 31/12)."""
    ma, ra, *_ = _chay(moi_truong, "2027-02-01", capsys)
    assert ma == tool.MA_VI_PHAM, ra


def test_CHUONG_CHI_DOC_khong_ghi_gi_len_Sheets_va_khong_in_lai_lo(moi_truong, capsys):
    ma, ra, ids, sheet = _chay(moi_truong, T3, capsys)
    assert sheet.ghi == [], f"chuông ghi lên Sheets: {sheet.ghi}"
    assert re.search(r"[-+]\d+\.\d+%", ra) is None
    for tu in ("loi_nhuan", "lãi ròng", "Lãi ròng", "alpha", "exit_price"):
        assert tu not in ra, tu


def test_CHUONG_khong_co_lenh_nao_tu_moc_thi_XANH_va_noi_ro(capsys):
    from paper_trading import PaperTradingJournal
    j = PaperTradingJournal(":memory:", cho_phep_so_that=True)
    j.ghi_nhat_ky = False
    j.consider_entry("AAA", "2026-09-22", _kq())
    sheet = ss.InMemorySheet()
    ss.push(j.db, sheet)
    ma = tool.main(backend=sheet, hom_nay=T3)
    ra = capsys.readouterr().out
    assert ma == tool.MA_XANH and "chưa có lệnh đóng nào từ" in ra


def test_CHUONG_SHEETS_LOI_la_ma_2_khong_xanh(monkeypatch, capsys):
    import google_sheets_sync as gs

    def hong(*a, **k):
        raise gs.KeoSoThatBai("mất mạng")
    monkeypatch.setattr(gs, "keo_so_co_thu_lai", hong)
    assert tool.main(hom_nay=T3) == tool.MA_CHUA_KIEM_DUOC
    ra = capsys.readouterr().out
    assert "::error::" in ra and "mất mạng" in ra


def test_CHUONG_KHO_NGOAI_CHUA_CAU_HINH_la_ma_2(monkeypatch, capsys):
    import google_sheets_sync as gs
    monkeypatch.setattr(gs, "keo_so_co_thu_lai", lambda *a, **k: None)
    assert tool.main(hom_nay=T3) == tool.MA_CHUA_KIEM_DUOC
    assert "chưa cấu hình" in capsys.readouterr().out


def test_CHUONG_loi_bat_ngo_la_ma_2_khong_lan_voi_VI_PHAM(moi_truong, monkeypatch, capsys):
    """Ngoại lệ chưa bắt thoát mã 1 theo mặc định của Python — trùng với 'vi phạm'."""
    def no(*a, **k):
        raise KeyError("bất ngờ")
    monkeypatch.setattr(tool, "kiem", no)
    j, _ = _so_that(moi_truong)
    sheet = ss.InMemorySheet()
    ss.push(j.db, sheet)
    assert tool.main(backend=sheet, hom_nay=T3) == tool.MA_CHUA_KIEM_DUOC
    assert "bất ngờ" in capsys.readouterr().out


def test_CHUONG_keo_so_hong_that_qua_backend_cung_la_ma_2(monkeypatch, capsys):
    import functools
    import google_sheets_sync as gs

    class Hong(ss.InMemorySheet):
        def read_rows(self, tab):
            raise RuntimeError("503")
    goc = gs.keo_so_co_thu_lai
    monkeypatch.setattr(gs, "keo_so_co_thu_lai",
                        functools.partial(goc, nghi=lambda s: None, ghi=lambda *a: None))
    assert tool.main(backend=Hong(), hom_nay=T3) == tool.MA_CHUA_KIEM_DUOC
    assert "503" in capsys.readouterr().out


def test_CHUONG_ghi_tom_tat_neu_co_GITHUB_STEP_SUMMARY(moi_truong, monkeypatch, tmp_path, capsys):
    f = tmp_path / "tom_tat.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(f))
    ma, *_ = _chay(moi_truong, T3, capsys)
    txt = f.read_text(encoding="utf-8")
    assert "Chuông bài học" in txt and "🔴" in txt and ma == tool.MA_VI_PHAM


def test_MA_THOAT_la_0_1_2_theo_hop_dong_cua_workflow():
    """Ghim bằng SỐ, không bằng tên hằng: các test khác so `ma == tool.MA_...` nên đổi giá trị
    hằng đổi cả hai vế và không đỏ. Workflow đỏ khi mã ≠ 0; con số là hợp đồng với nó."""
    assert (tool.MA_XANH, tool.MA_VI_PHAM, tool.MA_CHUA_KIEM_DUOC) == (0, 1, 2)
    assert len({tool.MA_XANH, tool.MA_VI_PHAM, tool.MA_CHUA_KIEM_DUOC}) == 3


def _chay_nhu_cli(monkeypatch, sheet, hom_nay):
    """Chạy file như `python tools/chuong_bai_hoc.py`: đi qua khối `__main__` và `sys.exit`.
    Sheets thay bằng bản giả ở tầng `get_backend`; đồng hồ giả để kết quả không trôi theo ngày."""
    import runpy
    import data_quality
    import google_sheets_sync as gs
    monkeypatch.setattr(gs, "get_backend", lambda backend=None: sheet)
    gio = dt.datetime.fromisoformat(f"{hom_nay}T16:53:00")
    monkeypatch.setattr(data_quality, "now_vn", lambda: gio)
    with pytest.raises(SystemExit) as e:
        runpy.run_path(str(GOC / "tools" / "chuong_bai_hoc.py"), run_name="__main__")
    return e.value.code


@pytest.mark.parametrize("hom_nay, ma", [(T2, 0), (T3, 1)])
def test_CHAY_NHU_CLI_thoat_dung_ma_xanh_va_vi_pham(moi_truong, monkeypatch, hom_nay, ma):
    j, _ = _so_that(moi_truong)
    sheet = ss.InMemorySheet()
    ss.push(j.db, sheet)
    assert _chay_nhu_cli(monkeypatch, sheet, hom_nay) == ma


def test_CHAY_NHU_CLI_kho_ngoai_chua_cau_hinh_thoat_2(monkeypatch):
    assert _chay_nhu_cli(monkeypatch, None, T3) == 2


def test_kiem_ma_thoat_theo_trang_thai():
    t = _trade(1)
    ma, dong, kq = tool.kiem([t], [_dong(1, nua_dong=False)], T3)
    assert ma == tool.MA_VI_PHAM and kq["n_vi_pham"] == 1
    ma, *_ = tool.kiem([t], [_dong(1, nua_dong=False)], T2)
    assert ma == tool.MA_XANH
    ma, *_ = tool.kiem([_trade(1, ra="2026-12-31")], [_dong(1, nua_dong=False)], "2027-01-06")
    assert ma == tool.MA_CHUA_KIEM_DUOC


# ── 9. dây nối (AST) ─────────────────────────────────────────────────────────

def _cay(ten):
    return ast.parse((GOC / ten).read_text(encoding="utf-8"))


def _goi_trong(f):
    return [ast.unparse(c.func) for c in ast.walk(f) if isinstance(c, ast.Call)]


def _ham(cay, ten):
    return next(n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == ten)


def test_CHUONG_goi_dung_ham_do_cua_so_bai_hoc_khong_chep_phep_do():
    cay = _cay("tools/chuong_bai_hoc.py")
    goi = _goi_trong(_ham(cay, "kiem"))
    assert goi.count("sbh.do_phu_bai_hoc") == 1 and goi.count("sbh.lenh_dong_tu_trades") == 1
    assert "sbh.cau_tieu_chi_b" in _goi_trong(_ham(cay, "dong_in_ra"))
    tu_tinh = [n for n in ast.walk(_ham(cay, "kiem")) if isinstance(n, ast.BinOp)]
    assert not tu_tinh, "chuông tự tính số thay vì dùng kết quả của hàm đo"
    so = [c for c in ast.walk(cay) if isinstance(c, ast.Constant) and isinstance(c.value, str)
          and re.fullmatch(r"\d{4}-\d{2}-\d{2}", c.value)]
    assert not so, f"chuông gõ ngày: {[c.value for c in so]}"


def test_CHUONG_chi_doc_khong_goi_ham_ghi_len_Sheets_hay_so():
    cay = _cay("tools/chuong_bai_hoc.py")
    goi = set(_goi_trong(cay))
    cam = {"gs.sync_trades_to_google_sheets", "ss.push", "push", "write_all", "append_rows",
           "sync_trades_to_google_sheets", "restore_journal_from_google_sheets"}
    thay = {g for g in goi if g.split(".")[-1] in {c.split(".")[-1] for c in cam}}
    assert not thay, f"chuông gọi hàm ghi: {thay}"
    assert "gs.keo_so_co_thu_lai" in goi, "đường kéo là đường kéo-có-thử-lại đã dùng ở nơi khác"
    # mọi câu lệnh SQL của chuông là SELECT
    for c in ast.walk(cay):
        if isinstance(c, ast.Call) and ast.unparse(c.func).endswith(".execute"):
            sql = ast.unparse(c.args[0]).upper()
            assert "SELECT" in sql and not re.search(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER)\b", sql)


def test_CHUONG_bat_het_ngoai_le_o_main_de_khong_lan_ma_1():
    main = _ham(_cay("tools/chuong_bai_hoc.py"), "main")
    thu = [n for n in ast.walk(main) if isinstance(n, ast.Try)]
    assert thu and any(h.type is not None and ast.unparse(h.type) == "Exception"
                       for t in thu for h in t.handlers)
    tra = [ast.unparse(r.value) for r in ast.walk(main) if isinstance(r, ast.Return)]
    assert "MA_CHUA_KIEM_DUOC" in tra


def test_CHUONG_ep_stdout_utf8():
    cay = _cay("tools/chuong_bai_hoc.py")
    assert any(ast.unparse(c.func) == "sys.stdout.reconfigure"
               for c in ast.walk(_ham(cay, "_ep_stdout_utf8")) if isinstance(c, ast.Call))
    assert "_ep_stdout_utf8" in _goi_trong(_ham(cay, "main"))


def test_APP_in_MOT_dong_tu_cung_ham_do_va_truyen_end_str():
    f = _ham(_cay("app.py"), "_khoi_so_bai_hoc")
    goi = _goi_trong(f)
    assert goi.count("_sbh.do_phu_bai_hoc") == 1 and goi.count("_sbh.lenh_dong_tu_nhat_ky") == 1
    assert goi.count("_sbh.cau_tieu_chi_b") == 1
    c = next(c for c in ast.walk(f) if isinstance(c, ast.Call)
             and ast.unparse(c.func) == "_sbh.do_phu_bai_hoc")
    assert [ast.unparse(a) for a in c.args] == ["_sbh.lenh_dong_tu_nhat_ky(nk)", "nk", "end_str"]
    t = [n for n in ast.walk(f) if isinstance(n, ast.Try) and "do_phu_bai_hoc" in ast.unparse(n)]
    assert t and all(any("st.warning" in ast.unparse(h) for h in n.handlers) for n in t)
    tu_tinh = [n for n in ast.walk(c) if isinstance(n, ast.BinOp)]
    assert not tu_tinh


def test_APP_chay_that_dong_tieu_chi_B_voi_st_gia():
    from test_so_bai_hoc import _St, _chay_app, _loai
    dong = {**_dong(1, nua_dong=False), "trang_thai_lenh": Status.CLOSED,
            "ngay_vao_lenh": "2026-09-30", "ngay_dong_lenh": T6}
    ghi = _chay_app(_St(), [dong])
    chu = [str(g[1][0]) for g in _loai(ghi, "caption")]
    dong_b = [c for c in chu if c.startswith("Tiêu chí B:")]
    assert len(dong_b) == 1, chu
    assert "0/1 lệnh đóng có bài học" in dong_b[0] and "1 QUÁ HẠN" in dong_b[0]
    assert "chuong_bai_hoc" in dong_b[0]


def test_APP_loi_khi_do_tieu_chi_thi_canh_bao_khong_sap(monkeypatch):
    from test_so_bai_hoc import _St, _chay_app, _loai

    def no(*a, **k):
        raise KeyError("x")
    monkeypatch.setattr(sbh, "do_phu_bai_hoc", no)
    ghi = _chay_app(_St(), [{**_dong(1), "trang_thai_lenh": Status.CLOSED}])
    assert "Chưa đo được tiêu chí B" in " ".join(str(g[1][0]) for g in _loai(ghi, "warning"))
    assert _loai(ghi, "dataframe"), "bảng vẫn dựng"


# ── 10. workflow ─────────────────────────────────────────────────────────────

WF = GOC / ".github" / "workflows"
CHUONG = WF / "chuong-bai-hoc.yml"


def _cron(ten):
    m = re.findall(r"^\s*-\s*cron:\s*'(\d+)\s+(\d+)\s+\*\s+\*\s+1-5'\s*$",
                   (WF / ten).read_text(encoding="utf-8"), re.MULTILINE)
    assert len(m) == 1, f"{ten}: {len(m)} dòng cron"
    return int(m[0][0]), int(m[0][1])


def test_workflow_goi_dung_tool_va_chi_doc():
    txt = CHUONG.read_text(encoding="utf-8")
    run = re.findall(r"^\s*run:\s*(python\s+\S+)\s*$", txt, re.MULTILINE)
    assert run == ["python tools/chuong_bai_hoc.py"]
    assert re.search(r"^permissions:\s*\n\s+contents:\s*read\s*$", txt, re.MULTILINE)
    # van-ban-ok: workflow là file YAML, không phải mã Python — tên sự kiện và tên secret chỉ có dạng văn bản để đọc
    assert "workflow_dispatch" in txt and "STREAMLIT_SECRETS_TOML" in txt
    assert "push" not in re.findall(r"^on:\s*\n((?:\s+.*\n)+)", txt, re.MULTILINE)[0]


def test_workflow_cron_lech_khoi_moc_nghen_va_khoi_ba_chuong_kia():
    phut, gio = _cron("chuong-bai-hoc.yml")
    assert phut not in (0, 30)
    moc = gio * 60 + phut
    for kia in ("chuong-bao-quet.yml", "canh-cong-c5.yml", "chuong-nguon-dung.yml"):
        p, g = _cron(kia)
        assert abs(moc - (g * 60 + p)) >= 10, f"cách {kia} dưới 10 phút"


def test_workflow_chu_thich_gio_khop_cron_cua_chinh_no():
    txt = CHUONG.read_text(encoding="utf-8")
    m = re.findall(r"#\s*(\d{2}):(\d{2}) UTC = (\d{2}):(\d{2}) ICT", txt)
    assert len(m) == 1
    gu, pu, gi, pi = map(int, m[0])
    assert (pu, gu) == _cron("chuong-bai-hoc.yml") and (gi, pi) == ((gu + 7) % 24, pu)


def test_workflow_moi_la_THEM_vao_khong_thay_cai_nao_cua_cac_workflow_co_san():
    """Ba chuông cũ và hai workflow quét/kiểm định vẫn còn nguyên tên."""
    assert {p.name for p in WF.glob("*.yml")} >= {
        "chuong-bao-quet.yml", "canh-cong-c5.yml", "chuong-nguon-dung.yml",
        "quet-so-lenh.yml", "kiem-dinh.yml", "chuong-bai-hoc.yml"}


# ── 11. dọn kèm: hạng gói của Cloud / Actions ───────────────────────────────

def test_requirements_cau_cu_ve_Cloud_hang_free_chi_con_khi_DANH_DAU_HET_DUNG():
    """Số/câu cũ được giữ nhưng phải ĐÁNH DẤU (CLAUDE.md): mỗi đoạn chú thích còn nhắc "hạng
    free" hay "báo LỆCH trên cloud ... báo ĐÚNG" phải mang "HẾT ĐÚNG" ngay trong đoạn ấy."""
    txt = (GOC / "requirements.txt").read_text(encoding="utf-8")
    doan = [" ".join(d.split()) for d in re.split(r"\n#\s*\n", txt)]
    cu = [d for d in doan if "hạng free" in d or "báo ĐÚNG" in d or "báo LỆCH trên cloud" in d]
    assert cu, "đoạn nêu lại câu cũ biến mất — nếu cố ý xoá hẳn thì sửa test này"
    for d in cu:
        assert "HẾT ĐÚNG" in d, f"câu cũ để TRẦN: {d[:120]}"
    # van-ban-ok: requirements.txt là tài liệu chú thích, các từ khoá này là NỘI DUNG câu đã sửa chứ không phải định danh mã
    assert "silver" in txt and "KHỚP" in txt and "hạng chưa đọc" in txt
    assert "không có trên PyPI" in txt, "lý do gốc của việc không khai gói tài trợ vẫn đúng"
