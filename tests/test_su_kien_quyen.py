"""Phát hiện SỰ KIỆN QUYỀN rơi trong lúc giữ lệnh ảo (BƯỚC 176, mốc D2) — CHỈ GẮN NHÃN.

Lỗi gốc (do leader đo 10/10/2026, dữ liệu thật): lệnh ảo HDB #122 vào 28/09 giá
27.950, đóng 09/10 `STOP_LOSS` −23,18%; nguồn giá HÔM NAY cho giá mở ngày 28/09 chỉ
≈ 21.460 — nguồn đã điều chỉnh LÙI cả lịch sử sau một sự kiện quyền, còn sổ lưu giá
CHƯA điều chỉnh lúc khớp. Giá rơi cơ học ở ngày không hưởng quyền chạm cắt lỗ: lỗ GIẢ.

Ba lớp gác:
  1. `su_kien_quyen.kiem_lenh` — SỐ TÍNH TAY trên nến giả (đáp số bằng SỐ, phép tính
     ở chú thích) cho sáu ca của đề bài + hai biên + ca dựng lại ĐÚNG hình dạng HDB.
  2. `dung_nen` · `pham_vi_tai` · `soi_so` · `tom_tat` — số tính tay.
  3. AST — module nằm NGOÀI đường đo (không ai trên đường giao dịch/đo nhập nó),
     thuần (không ghi, không mạng, không đồng hồ); CLI chỉ đọc; app chỉ tải giá khi
     bấm nút và in câu cố định.

Đột biến (bộ ở thân PR / `docs/STATE.md` BƯỚC 176): `>` thay `>=` ở ngưỡng · bỏ phép
so f_ra < f_vào · lệnh mở coi như đóng · bỏ nới biên.
"""
from __future__ import annotations

import ast
import dataclasses
import pathlib
import sys
from types import SimpleNamespace

import pytest

GOC = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))
sys.path.insert(0, str(GOC))

import duyet_repo  # noqa: E402
import quyet_dinh_cho as qdc  # noqa: E402
import su_kien_quyen as skq  # noqa: E402

V, R = "2026-09-28", "2026-10-09"


def _lenh(gia_vao, gia_ra=None, ngay_vao=V, ngay_ra=R):
    return {"entry_date": ngay_vao, "entry_price": gia_vao,
            "exit_date": ngay_ra, "exit_price": gia_ra}


def _nen(mo_vao, thap_ra=None, cao_ra=None):
    """Nến ngày vào (mở, thấp, cao) và, nếu có, nến ngày ra."""
    n = {V: (mo_vao, mo_vao * 0.98, mo_vao * 1.02)}
    if thap_ra is not None:
        n[R] = (thap_ra, thap_ra, cao_ra)
    return n


# ─────────────────────────────────────────────────────────────────────
# 1. Sáu ca của đề bài. Hệ số f_vào = giá vào sổ ÷ giá MỞ nguồn ngày vào;
#    f_ra = giá ra sổ ÷ trung điểm (thấp+cao)/2 nguồn ngày ra;
#    giá ra quy về cơ sở nguồn = giá ra ÷ f_vào, so với [thấp·0,98 ; cao·1,02].
# ─────────────────────────────────────────────────────────────────────

def test_a_khong_su_kien_la_SACH():
    # vào 20.000 / mở nguồn 20.000 -> f_vào = 1,0 (lệch 0% <= 5%) -> SẠCH ngay.
    # ra 21.000, nến ra [20.500 ; 21.500] trung điểm 21.000 -> f_ra = 1,0.
    kq = skq.kiem_lenh(_lenh(20000, 21000), _nen(20000, 20500, 21500), True)
    assert kq.trang_thai == skq.SACH
    assert kq.he_so_vao == pytest.approx(1.0)
    assert kq.he_so_ra == pytest.approx(1.0)


def test_b_su_kien_SAU_khi_dong_la_SACH():
    # vào 27.950 / mở nguồn (đã điều chỉnh) 21.500 -> f_vào = 1,3.
    # ra 26.000 (cơ sở sổ). 26.000 ÷ 1,3 = 20.000 nằm trong [19.500 ; 20.500]
    # -> hai đầu cùng cơ sở: SẠCH. f_ra = 26.000 ÷ 20.000 = 1,3.
    kq = skq.kiem_lenh(_lenh(27950, 26000), _nen(21500, 19500, 20500), True)
    assert kq.trang_thai == skq.SACH
    assert kq.he_so_vao == pytest.approx(1.3)
    assert kq.he_so_ra == pytest.approx(1.3)


def test_b2_SACH_nho_noi_bien_2_phan_tram():
    # như (b) nhưng nến ra [19.000 ; 19.800]: 20.000 > 19.800 (ngoài biên thô),
    # 19.800 × 1,02 = 20.196 >= 20.000 -> VẪN SẠCH nhờ nới biên.
    kq = skq.kiem_lenh(_lenh(27950, 26000), _nen(21500, 19000, 19800), True)
    assert kq.trang_thai == skq.SACH


def test_b2b_SACH_nho_noi_bien_phia_THAP():
    # nến ra [20.100 ; 21.000]: 20.000 < 20.100 (ngoài biên thô phía thấp),
    # 20.100 × 0,98 = 19.698 <= 20.000 -> VẪN SẠCH nhờ nới biên phía thấp.
    kq = skq.kiem_lenh(_lenh(27950, 26000), _nen(21500, 20100, 21000), True)
    assert kq.trang_thai == skq.SACH


def test_b3_ngoai_ca_bien_da_noi_thi_khong_SACH():
    # nến ra [19.000 ; 19.500]: 19.500 × 1,02 = 19.890 < 20.000 -> ngoài biên.
    # f_ra = 26.000 ÷ 19.250 = 1,3506 >= f_vào 1,3 -> LECH_KHAC.
    kq = skq.kiem_lenh(_lenh(27950, 26000), _nen(21500, 19000, 19500), True)
    assert kq.trang_thai == skq.LECH_KHAC


def test_c_su_kien_GIUA_vao_va_ra_dung_hinh_HDB():
    # f_vào = 27.950 ÷ 21.500 = 1,3. Ra 21.000, nến ra [20.800 ; 22.000] trung
    # điểm 21.400: 21.000 ÷ 1,3 = 16.154 < 20.800 × 0,98 = 20.384 -> ngoài biên.
    # f_ra = 21.000 ÷ 21.400 = 0,9813 < 1,3 -> SỰ KIỆN TRONG LÚC GIỮ.
    kq = skq.kiem_lenh(_lenh(27950, 21000), _nen(21500, 20800, 22000), True)
    assert kq.trang_thai == skq.SU_KIEN_TRONG_LUC_GIU
    assert kq.he_so_vao == pytest.approx(1.3)
    assert kq.he_so_ra == pytest.approx(21000 / 21400)
    assert "GIỮA" in kq.ly_do


def test_d_gia_ra_tren_bien_va_f_ra_lon_hon_f_vao_la_LECH_KHAC():
    # f_vào = 25.000 ÷ 20.000 = 1,25. Ra 30.000, nến ra [20.000 ; 22.000] trung
    # điểm 21.000: 30.000 ÷ 1,25 = 24.000 > 22.000 × 1,02 = 22.440 -> ngoài biên.
    # f_ra = 30.000 ÷ 21.000 = 1,4286 >= 1,25 -> LỆCH KHÁC (f TĂNG, kiểu SSI #100).
    kq = skq.kiem_lenh(_lenh(25000, 30000), _nen(20000, 20000, 22000), True)
    assert kq.trang_thai == skq.LECH_KHAC
    assert kq.he_so_vao == pytest.approx(1.25)
    assert kq.he_so_ra == pytest.approx(30000 / 21000)
    assert "BƯỚC 123" in kq.ly_do and "chưa kiểm" in kq.ly_do


def test_e_lenh_CON_MO_co_f_khac_1_la_SU_KIEN():
    # vào 27.950 / mở 21.500 -> f_vào = 1,3 > 5%; lệnh còn mở -> SỰ KIỆN, không có f_ra.
    kq = skq.kiem_lenh(_lenh(27950, None, ngay_ra=None), _nen(21500), False)
    assert kq.trang_thai == skq.SU_KIEN_TRONG_LUC_GIU
    assert kq.he_so_vao == pytest.approx(1.3)
    assert kq.he_so_ra is None
    assert "CÒN MỞ" in kq.ly_do


def test_e2_lenh_mo_co_ca_du_lieu_ra_van_la_lenh_mo():
    # CLOSING mang sẵn exit_date/exit_price nhưng CHƯA đóng: phải đi nhánh MỞ
    # (nến ngày ra thậm chí không có) chứ không đòi nến ra.
    kq = skq.kiem_lenh(_lenh(27950, 21000), _nen(21500), False)
    assert kq.trang_thai == skq.SU_KIEN_TRONG_LUC_GIU
    assert kq.he_so_ra is None


def test_e3_lenh_mo_f_bang_1_la_SACH():
    kq = skq.kiem_lenh(_lenh(21500, None, ngay_ra=None), _nen(21500), False)
    assert kq.trang_thai == skq.SACH


def test_f_thieu_nen_ngay_vao():
    kq = skq.kiem_lenh(_lenh(27950, 26000), {R: (20000, 19500, 20500)}, True)
    assert kq.trang_thai == skq.KHONG_KIEM_DUOC
    assert kq.he_so_vao is None and "ngày vào" in kq.ly_do


def test_f_thieu_nen_ngay_ra_cua_lenh_dong():
    kq = skq.kiem_lenh(_lenh(27950, 26000), _nen(21500), True)
    assert kq.trang_thai == skq.KHONG_KIEM_DUOC
    assert kq.he_so_vao == pytest.approx(1.3) and "ngày ra" in kq.ly_do


@pytest.mark.parametrize("lenh", [
    _lenh(None, 26000), _lenh(0, 26000), _lenh(27950, None), _lenh(27950, 26000, ngay_ra=None),
    _lenh(27950, 26000, ngay_vao=None), _lenh(float("nan"), 26000)])
def test_f_thieu_gia_hoac_ngay_la_KHONG_KIEM_DUOC(lenh):
    assert skq.kiem_lenh(lenh, _nen(21500, 19500, 20500), True).trang_thai == skq.KHONG_KIEM_DUOC


def test_f_nen_co_o_khong_hop_le_la_KHONG_KIEM_DUOC():
    # giá mở 0 (hoặc thiếu) thì không chia được: không đoán.
    for nen_xau in ({V: (0, 1, 2)}, {V: (21500, None, 22000)}, {V: (21500, 21000)}):
        kq = skq.kiem_lenh(_lenh(27950, None, ngay_ra=None), nen_xau, False)
        assert kq.trang_thai == skq.KHONG_KIEM_DUOC, nen_xau


def test_lenh_mo_khong_can_nen_ngay_ra():
    kq = skq.kiem_lenh(_lenh(21500, None, ngay_ra=None), {V: (21500, 21000, 22000)}, False)
    assert kq.trang_thai == skq.SACH


def test_ngay_co_hau_to_gio_van_khop():
    nen = {V: (21500.0, 21000.0, 22000.0)}
    kq = skq.kiem_lenh(_lenh(27950, None, ngay_vao=V + " 00:00:00", ngay_ra=None), nen, False)
    assert kq.trang_thai == skq.SU_KIEN_TRONG_LUC_GIU


# ── hai biên của ngưỡng 5% (viết dạng nhân để 1050/1000 không trôi) ─────────

def test_bien_5_phan_tram_dung_bang_la_SACH():
    # lệnh mở: vào 1.050 / mở 1.000 -> lệch ĐÚNG 5% (1.050 − 1.000 = 50 = 0,05 × 1.000)
    # -> không vượt ngưỡng -> SẠCH. (Viết |1.05 − 1| > 0,05 trong dấu phẩy động
    # cho True oan vì 1,05 − 1 = 0,05000000000000004.)
    assert skq.kiem_lenh(_lenh(1050, None, ngay_ra=None), {V: (1000, 990, 1010)},
                         False).trang_thai == skq.SACH


def test_bien_5_phan_tram_vuot_mot_dong_la_SU_KIEN():
    assert skq.kiem_lenh(_lenh(1051, None, ngay_ra=None), {V: (1000, 990, 1010)},
                         False).trang_thai == skq.SU_KIEN_TRONG_LUC_GIU


def test_lech_phia_nguon_cao_hon_so_van_gan_nhan_nhung_noi_ro_chieu():
    # vào 1.000 / mở nguồn 1.250 -> f = 0,8: lệch 20% nhưng nguồn CAO hơn sổ, không
    # phải dạng sự kiện quyền. Theo đề bài vẫn là SỰ KIỆN (lệnh mở, |f − 1| > 5%).
    kq = skq.kiem_lenh(_lenh(1000, None, ngay_ra=None), {V: (1250, 1200, 1300)}, False)
    assert kq.trang_thai == skq.SU_KIEN_TRONG_LUC_GIU
    assert kq.he_so_vao == pytest.approx(0.8)
    assert "không phải dạng sự kiện quyền" in kq.ly_do


def test_hang_so_dung_gia_tri_de_xuat():
    assert skq.NGUONG_LECH == 0.05 and skq.NOI_BIEN == 0.02


def test_ket_qua_dong_bang_va_ham_thuan():
    kq = skq.kiem_lenh(_lenh(27950, 21000), _nen(21500, 20800, 22000), True)
    with pytest.raises(dataclasses.FrozenInstanceError):
        kq.trang_thai = skq.SACH                                  # type: ignore[misc]
    lenh, nen = _lenh(27950, 21000), _nen(21500, 20800, 22000)
    bao = (dict(lenh), dict(nen))
    assert skq.kiem_lenh(lenh, nen, True) == skq.kiem_lenh(lenh, nen, True)
    assert (lenh, nen) == bao


# ─────────────────────────────────────────────────────────────────────
# 2. dung_nen · pham_vi_tai · soi_so · tom_tat
# ─────────────────────────────────────────────────────────────────────

def test_dung_nen_nhan_he_so_bo_o_xau_va_giu_dong_cuoi():
    nan = float("nan")
    nen = skq.dung_nen(
        ["2026-09-28 00:00:00", "2026-09-29", "2026-09-30", "2026-09-28"],
        [21.46, nan, 22.0, 21.5], [21.2, 21.0, 0, 21.3], [21.9, 22.5, 22.4, 21.8],
        1000.0)
    # 29/09 có mở NaN -> bỏ; 30/09 có thấp 0 -> bỏ; 28/09 trùng -> giữ dòng cuối
    # (21,5 · 21,3 · 21,8) × 1.000.
    assert list(nen) == ["2026-09-28"]
    assert nen["2026-09-28"] == pytest.approx((21500, 21300, 21800))


def _t(id, ma, vao, gia_vao, ra=None, gia_ra=None):
    return SimpleNamespace(id=id, symbol=ma, entry_date=vao, entry_price=gia_vao,
                           exit_date=ra, exit_price=gia_ra)


def test_pham_vi_tai_ma_duy_nhat_va_lui_10_ngay():
    mo = [_t(1, "HDB", "2026-09-28", 27950), _t(2, "BID", None, None)]    # BID chưa khớp
    dong = [_t(3, "BID", "2026-09-14", 40000, "2026-09-20", 41000),
            _t(4, "HDB", "2026-09-30", 100, "2026-10-05", 101)]
    ma, tu = skq.pham_vi_tai(mo, dong)
    # vào sớm nhất 14/09; lùi 10 ngày lịch -> 04/09. BID có lệnh đã khớp nên vào danh sách.
    assert ma == ["BID", "HDB"]
    assert tu == "2026-09-04"
    assert skq.pham_vi_tai([_t(1, "HDB", None, None)], []) == ([], None)
    assert skq.pham_vi_tai([], []) == ([], None)


def test_soi_so_va_tom_tat_so_tinh_tay():
    mo = [_t(10, "HDB", V, 27950, "2026-10-09", 21000),      # CÒN MỞ (CLOSING): f 1,3 -> SỰ KIỆN
          _t(11, "XYZ", V, 5000)]                              # mã không có nến -> KHÔNG KIỂM ĐƯỢC
    dong = [_t(2, "AAA", V, 20000, R, 21000),                # sạch (a)
            _t(5, "BBB", V, 25000, R, 30000),                # lệch khác (d)
            _t(7, "CCC", V, 27950, R, 21000)]                # sự kiện (c)
    nen = {"HDB": {V: (21500.0, 21000.0, 22000.0)},
           "AAA": {V: (20000.0, 19600.0, 20400.0), R: (20500.0, 20500.0, 21500.0)},
           "BBB": {V: (20000.0, 19600.0, 20400.0), R: (20000.0, 20000.0, 22000.0)},
           "CCC": {V: (21500.0, 21000.0, 22000.0), R: (20800.0, 20800.0, 22000.0)}}
    dong_soi = skq.soi_so(mo, dong, nen)
    assert [d.id for d in dong_soi] == [2, 5, 7, 10, 11]                 # sắp theo id
    nhan = {d.id: d.ket_qua.trang_thai for d in dong_soi}
    assert nhan == {2: skq.SACH, 5: skq.LECH_KHAC, 7: skq.SU_KIEN_TRONG_LUC_GIU,
                    10: skq.SU_KIEN_TRONG_LUC_GIU, 11: skq.KHONG_KIEM_DUOC}
    assert skq.tom_tat(dong_soi) == {skq.SACH: 1, skq.SU_KIEN_TRONG_LUC_GIU: 2,
                                     skq.LECH_KHAC: 1, skq.KHONG_KIEM_DUOC: 1}
    by = {d.id: d for d in dong_soi}
    assert by[10].da_dong is False and by[10].ngay_ra == ""              # CLOSING: chưa ra
    assert by[7].da_dong is True and by[7].ngay_ra == R
    assert skq.tom_tat([]) == {skq.SACH: 0, skq.SU_KIEN_TRONG_LUC_GIU: 0,
                               skq.LECH_KHAC: 0, skq.KHONG_KIEM_DUOC: 0}


# ─────────────────────────────────────────────────────────────────────
# 3. AST
# ─────────────────────────────────────────────────────────────────────
TEN_GHI = {"push", "write_all", "append_rows", "pull", "record_trade", "update_trade",
           "record_decision", "commit", "executemany", "executescript", "execute",
           "open", "write_text", "write_bytes", "unlink", "to_csv", "mkdir",
           "now", "today", "now_vn", "utcnow", "read_csv", "urlopen", "request",
           "sleep"}


def _cay(duong):
    return ast.parse((GOC / duong).read_text(encoding="utf-8"))


def _nhap_va_goi(cay):
    nhap, goi = set(), set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            nhap |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            nhap.add((n.module or "").split(".")[0])
        elif isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name):
                goi.add(f.id)
            elif isinstance(f, ast.Attribute):
                goi.add(f.attr)
    return nhap, goi


def _file_ma_nguon():
    bo = {"tests", ".venv", ".git", "node_modules", "__pycache__"}
    return [p for p in duyet_repo.duyet(GOC, "*.py")
            if not (set(p.relative_to(GOC).parts) & bo)]


def test_CHI_app_va_CLI_duoc_nhap_su_kien_quyen():
    ai = set()
    for p in _file_ma_nguon():
        nhap, _ = _nhap_va_goi(ast.parse(p.read_text(encoding="utf-8")))
        if "su_kien_quyen" in nhap:
            ai.add(p.relative_to(GOC).as_posix())
    assert ai == {"app.py", "tools/soi_su_kien_quyen.py"}, (
        f"su_kien_quyen CHỈ GẮN NHÃN, không vào đường đo; đang có: {sorted(ai)}")


@pytest.mark.parametrize("ten", [
    "run_daily.py", "paper_trading.py", "paper_runner.py", "paper_metrics.py",
    "master_agent.py", "analysis_agents.py", "debate_agents.py", "walkforward.py",
    "sheets_store.py", "google_sheets_sync.py", "ke_hoach_vao_lenh.py",
    "so_lenh_app.py", "so_bai_hoc.py", "ban_tin.py"])
def test_duong_do_va_giao_dich_KHONG_nhap_su_kien_quyen(ten):
    duong = GOC / ten
    assert duong.exists(), ten
    assert "su_kien_quyen" not in _nhap_va_goi(_cay(ten))[0], ten


def test_backtest_KHONG_nhap_su_kien_quyen():
    ai = [p for p in duyet_repo.duyet(GOC / "backtest", "*.py")
          if "su_kien_quyen" in _nhap_va_goi(ast.parse(p.read_text(encoding="utf-8")))[0]]
    assert not ai, ai


def test_module_thuan_chi_nhap_thu_trung_tinh_va_khong_ghi_khong_mang_khong_dong_ho():
    nhap, goi = _nhap_va_goi(_cay("su_kien_quyen.py"))
    assert nhap <= {"__future__", "dataclasses", "typing", "datetime"}, nhap
    assert not (TEN_GHI & goi), sorted(TEN_GHI & goi)


def test_CLI_chi_doc_qua_duong_keo_an_toan_va_khong_goi_ham_ghi():
    cay = _cay("tools/soi_su_kien_quyen.py")
    nhap, goi = _nhap_va_goi(cay)
    ghi = (TEN_GHI - {"today"}) | {"all_trades_ghi"}
    assert not (ghi & goi), sorted(ghi & goi)
    # đường kéo mặc định là `doc_so_that.keo_ve_so_tam` (tham chiếu, không gọi thẳng,
    # để test tiêm được sổ giả); không tự chế đường kéo khác
    tham_chieu = {(n.value.id, n.attr) for n in ast.walk(cay)
                  if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)}
    assert ("doc_so_that", "keo_ve_so_tam") in tham_chieu, "phải kéo sổ qua đường an toàn có sẵn"
    assert "soi_so" in goi
    assert not ({"sqlite3", "gspread", "sheets_store", "google_sheets_sync"} & nhap)


def _ham(cay, ten):
    cac = [n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == ten]
    assert len(cac) == 1, f"{ten}: {len(cac)} định nghĩa"
    return cac[0]


def test_APP_chi_tai_gia_khi_bam_nut_va_trong_tab_lich_su():
    cay = _cay("app.py")
    khoi = _ham(cay, "_khoi_su_kien_quyen")
    # (1) có đúng một nút bấm với khoá riêng, và lệnh tải giá nằm TRONG hàm khối
    nut = [n for n in ast.walk(khoi) if isinstance(n, ast.Call)
           and isinstance(n.func, ast.Attribute) and n.func.attr == "button"]
    assert len(nut) == 1
    assert any(k.arg == "key" and ast.literal_eval(k.value) == "su_kien_quyen_tai_gia"
               for k in nut[0].keywords)
    # (2) hàm tải giá chỉ được gọi từ hàm khối (không ở mức module, không trong vòng khác)
    goi = [n for n in ast.walk(cay) if isinstance(n, ast.Call)
           and isinstance(n.func, ast.Name) and n.func.id == "_nen_cho_su_kien_quyen"]
    trong = {id(n) for n in ast.walk(khoi)}
    assert len(goi) == 1 and id(goi[0]) in trong
    # (3) lời gọi tải giá đứng SAU chốt `st.session_state.get("su_kien_quyen_co_gia")`
    chot = [n for n in ast.walk(khoi) if isinstance(n, ast.Constant)
            and n.value == "su_kien_quyen_co_gia"]
    assert chot and min(c.lineno for c in chot) < goi[0].lineno
    # (4) khối được gọi đúng một chỗ, bên trong `with t_hist:`
    cac_goi = [n for n in ast.walk(cay) if isinstance(n, ast.Call)
               and isinstance(n.func, ast.Name) and n.func.id == "_khoi_su_kien_quyen"]
    assert len(cac_goi) == 1
    with_hist = [n for n in ast.walk(cay) if isinstance(n, ast.With)
                 and any(isinstance(i.context_expr, ast.Name) and i.context_expr.id == "t_hist"
                         for i in n.items)]
    assert len(with_hist) == 1
    assert id(cac_goi[0]) in {id(x) for x in ast.walk(with_hist[0])}


def test_APP_soi_so_nhan_dung_hai_nhom_cua_so_lenh_app():
    cay = _cay("app.py")
    goi = [n for n in ast.walk(_ham(cay, "_khoi_su_kien_quyen")) if isinstance(n, ast.Call)
           and isinstance(n.func, ast.Attribute) and n.func.attr == "soi_so"]
    assert len(goi) == 1
    assert [ast.unparse(a) for a in goi[0].args] == [
        "_so_lenh.vi_the_mo", "_so_lenh.lenh_dong", "_nen"]


def test_APP_khoi_khong_goi_ham_ghi_va_khong_mo_so_ma_nguon():
    khoi = _ham(_cay("app.py"), "_khoi_su_kien_quyen")
    nhap, goi = _nhap_va_goi(khoi)
    assert not ((TEN_GHI | {"PaperTradingJournal", "all_trades"}) & goi)
    ten = {n.id for n in ast.walk(khoi) if isinstance(n, ast.Name)}
    assert "PaperTradingJournal" not in ten


CAU_CO_DINH = ("Lệnh có sự kiện quyền trong lúc giữ mang lãi/lỗ GIẢ (giá sổ chưa điều "
               "chỉnh). Người dùng đã chốt loại các lệnh này khỏi điều kiện dừng — việc "
               "đó là một bước riêng, CHƯA áp dụng.")


def test_APP_in_cau_co_dinh_nguyen_van():
    cay = _cay("app.py")
    chuoi = [n.value for n in ast.walk(_ham(cay, "_khoi_su_kien_quyen"))
             if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    assert CAU_CO_DINH in chuoi


# ─────────────────────────────────────────────────────────────────────
# 4. Hàng đợi quyết định (Q14)
# ─────────────────────────────────────────────────────────────────────

def test_Q14_da_quyet_voi_cau_tra_loi_NGUYEN_VAN_va_viec_con_lai():
    muc = {m.ma: m for m in qdc.doc_muc(qdc.TEP.read_text(encoding="utf-8"))}
    m = muc["Q14"]
    assert m.trang_thai == qdc.DA_QUYET
    gop = "\n".join(m.truong.values())
    assert '*"Đánh dấu + loại khỏi điều kiện dừng (Recommended)"*' in gop
    assert "10/10/2026" in m.truong_nhan(qdc.NHAN_TRA_LOI)
    assert "NotebookLM" in gop and "HDB" in m.tieu_de
    assert qdc.loi_so(list(muc.values())) == []


# ─────────────────────────────────────────────────────────────────────
# 5. CLI chạy được từ đầu đến cuối với sổ giả và nến giả (không mạng)
# ─────────────────────────────────────────────────────────────────────
import pandas as pd  # noqa: E402

import paper_trading as pt  # noqa: E402
import soi_su_kien_quyen as cli  # noqa: E402
from paper_trading import Status  # noqa: E402


def _trade(id, ma, tt, vao, gia_vao, ra=None, gia_ra=None):
    return pt.Trade(id=id, symbol=ma, signal_date="2026-09-25", entry_date=vao,
                    entry_price=gia_vao, exit_date=ra, exit_price=gia_ra,
                    exit_reason=None, stop_loss=1.0, take_profit=2.0, size_pct=10.0,
                    entry_score=70, status=tt)


class _SoGia:
    def __init__(self, trades):
        self._t = trades

    def all_trades(self):
        return list(self._t)


def _bang(mo, thap, cao):
    """Bảng OHLCV nghìn đồng (như vnstock) cho hai ngày."""
    return pd.DataFrame({"time": [V, R], "open": [mo[0] / 1000, mo[1] / 1000],
                         "low": [thap[0] / 1000, thap[1] / 1000],
                         "high": [cao[0] / 1000, cao[1] / 1000],
                         "close": [mo[0] / 1000, mo[1] / 1000]})


def _tai_gia(goi):
    bang = {"HDB": _bang((21500, 20800), (21000, 20800), (22000, 22000)),   # (c): f_vào 1,3
            "AAA": _bang((20000, 20500), (19600, 20500), (20400, 21500))}   # (a): sạch

    def tai(ma, tu, den):
        goi.append((ma, tu, den))
        if ma not in bang:
            return "FAILED", None, 1.0
        return "OK", bang[ma], 1000.0
    return tai


def test_CLI_chay_tron_ve_ma_thoat_1_khi_co_su_kien_va_tai_moi_ma_mot_lan(capsys):
    so = _SoGia([_trade(1, "HDB", Status.CLOSED, V, 27950, R, 21000),
                 _trade(2, "AAA", Status.CLOSED, V, 20000, R, 21000),
                 _trade(3, "HDB", Status.OPEN, V, 27950),
                 _trade(4, "ZZZ", Status.OPEN, V, 5000),            # tải hỏng -> KHÔNG KIỂM ĐƯỢC
                 _trade(5, "AAA", Status.PENDING, None, None),      # chưa khớp
                 _trade(6, "AAA", Status.HUY, None, None)])         # không phải giao dịch
    goi: list = []
    ma_thoat = cli.main(keo=lambda: (so, {}), tai=_tai_gia(goi), hom_nay=R)
    ra = capsys.readouterr().out
    assert ma_thoat == 1
    assert sorted(m for m, _, _ in goi) == ["AAA", "HDB", "ZZZ"]       # mỗi mã MỘT lần
    assert {tu for _, tu, _ in goi} == {"2026-09-18"}                  # 28/09 − 10 ngày
    assert "LỆNH KHÔNG SẠCH: 4/5" in ra                                # 5 lệnh xét (bỏ HUY): sạch = #2
    assert "TRONG ĐÓ LỆNH CÒN MỞ: 3" in ra                             # #3 sự kiện, #4 và #5 không kiểm được
    gon = " ".join(ra.split())
    assert "SACH 1 SU_KIEN_TRONG_LUC_GIU 2 LECH_KHAC 0 KHONG_KIEM_DUOC 2" in gon
    assert "Không tải được nến: ZZZ" in ra
    assert "CHƯA áp dụng" in ra


def test_CLI_ma_thoat_0_khi_khong_co_su_kien(capsys):
    so = _SoGia([_trade(2, "AAA", Status.CLOSED, V, 20000, R, 21000)])
    assert cli.main(keo=lambda: (so, {}), tai=_tai_gia([]), hom_nay=R) == 0
    capsys.readouterr()


def test_CLI_ma_thoat_2_khi_khong_doc_duoc_so(capsys):
    assert cli.main(keo=lambda: None, tai=_tai_gia([]), hom_nay=R) == 2
    assert "CHUA DOC DUOC SO" in capsys.readouterr().err
