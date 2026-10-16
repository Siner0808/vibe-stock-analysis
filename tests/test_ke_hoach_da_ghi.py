"""Gác BƯỚC 198 — app HIỆN kế hoạch vào lệnh ĐÃ GHI (tab `ke_hoach`), CHỈ ĐỌC.

Ba vế:
1. `sheets_store.doc_ke_hoach` đọc đúng kiểu, mới nhất đứng đầu, tiêu đề lệch thì nổ,
   và chỉ gọi `read_rows`.
2. `so_ke_hoach` dựng dòng hiện mà không tính lại gì, không điền 0, đọc giờ ghi theo
   giờ VN (Streamlit Cloud chạy UTC), nối lệnh sổ ảo theo (mã, ngày 10 ký tự).
3. App đọc qua một hàm có bộ nhớ đệm, và khối hiện KHÔNG lập lại kế hoạch nào: lập
   lại kế hoạch của tín hiệu cũ là lập trên một chuỗi giá KHÁC chuỗi agent đã thấy
   (ĐO 24: `close` lệch ở 21,6% nến chung; ĐO 26: nguồn điều chỉnh lùi).
"""
from __future__ import annotations

import ast
import pathlib
import sys
from types import SimpleNamespace

import pytest

GOC = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import google_sheets_sync as gss  # noqa: E402
import sheets_store as ss  # noqa: E402
import so_ke_hoach as skh  # noqa: E402
from paper_trading import PaperTradingJournal  # noqa: E402

TEN_GHI = {"push", "write_all", "append_rows", "pull", "record_trade", "update_trade",
           "record_decision", "commit", "executemany", "executescript", "ghi_ke_hoach",
           "open", "write_text", "write_bytes", "unlink", "to_csv", "mkdir",
           "sync_trades_to_google_sheets", "restore_journal_from_google_sheets",
           "keo_so_co_thu_lai"}

#: 15/10/2026 07:10:00 UTC — lượt quét Actions đầu tiên chạy mã BƯỚC 195.
AT_0710_UTC = 1792048200.0


def _kh(**kw):
    """Một `KeHoachVaoLenh` giả, đủ trường `dong_tu_ke_hoach` đọc."""
    goc = dict(phan_quyet="CHO_VUNG", ly_do=("vì A", "vì B"), ngay="2026-10-14",
               gia_dong=25000.0, atr=800.0, ma20=24000.0, keo_gian_atr=1.25,
               day_xoay_ngay="2026-10-08", day_xoay_gia=23500.0,
               cat_lo_cau_truc=23100.0, rui_ro_pct=7.6, vung=(23950.0, 24300.0),
               so_phien_cho=5, nhan="Đặt chờ")
    goc.update(kw)
    return SimpleNamespace(**goc)


def _dong(ma, ngay, luc=AT_0710_UTC, **kw):
    return skh.dong_tu_ke_hoach(_kh(ngay=ngay, **kw), ma, 66.0, 62.0, "HOSE",
                                "B6-test", luc, ngay)


def _sheet_co(*dong):
    """Đi qua đường THẬT: sổ SQLite -> `push` -> ô chuỗi của sheet giả."""
    j = PaperTradingJournal(":memory:", cho_phep_so_that=True)
    for d in dong:
        assert j.ghi_ke_hoach(d)
    b = ss.InMemorySheet()
    ss.push(j.db, b)
    return b


def _cay(duong):
    return ast.parse((GOC / duong).read_text(encoding="utf-8"))


def _goi(nut):
    ra = set()
    for n in ast.walk(nut):
        if isinstance(n, ast.Call):
            f = n.func
            ra.add(f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else "")
    return ra


def _ham(cay, ten):
    return next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == ten)


# ───────────────────────── 1. Đọc tab ─────────────────────────

def test_doc_ke_hoach_tab_VANG_hay_chi_co_tieu_de_la_danh_sach_rong():
    assert ss.doc_ke_hoach(ss.InMemorySheet()) == []
    b = ss.InMemorySheet()
    b.write_all(ss.TAB_KE_HOACH, [list(ss.KE_HOACH_COLS)])
    assert ss.doc_ke_hoach(b) == []


def test_doc_ke_hoach_doi_dung_kieu_va_MOI_NHAT_dung_dau():
    b = _sheet_co(_dong("AAA", "2026-10-14"), _dong("BBB", "2026-10-15"),
                  _dong("CCC", "2026-10-14"))
    ds = ss.doc_ke_hoach(b)
    # ngày nến giảm dần; cùng ngày thì dòng ghi SAU (seq lớn) đứng trước
    assert [d["symbol"] for d in ds] == ["BBB", "CCC", "AAA"]
    d = ds[0]
    assert isinstance(d["seq"], int) and isinstance(d["so_phien_cho"], int)
    assert d["diem"] == 66.0 and d["vung_day"] == 23950.0 and d["cat_lo"] == 23100.0
    assert d["at"] == AT_0710_UTC


def test_doc_ke_hoach_tieu_de_LECH_thi_NO():
    b = _sheet_co(_dong("AAA", "2026-10-14"))
    hang = b.read_rows(ss.TAB_KE_HOACH)
    hang[0] = ["score" if c == "diem" else c for c in hang[0]]
    b.write_all(ss.TAB_KE_HOACH, hang)
    with pytest.raises(ss.SheetSchemaError):
        ss.doc_ke_hoach(b)


def test_doc_ke_hoach_CHI_doc():
    ham = _ham(_cay("sheets_store.py"), "doc_ke_hoach")
    goi = _goi(ham)
    assert "_doc_tab" in goi
    assert not (TEN_GHI & goi), sorted(TEN_GHI & goi)


def test_load_ke_hoach_None_khi_CHUA_cau_hinh_va_danh_sach_khi_co(monkeypatch):
    monkeypatch.setattr(gss._ss, "open_from_secrets", lambda: None)
    assert gss.load_ke_hoach_from_google_sheets() is None
    b = _sheet_co(_dong("AAA", "2026-10-14"))
    assert [d["symbol"] for d in gss.load_ke_hoach_from_google_sheets(b)] == ["AAA"]
    assert gss.load_ke_hoach_from_google_sheets(ss.InMemorySheet()) == []


# ───────────────────────── 2. Dựng dòng hiện ─────────────────────────

def test_dong_hien_thi_giu_SO_DA_GHI_va_o_thieu_KHONG_thanh_0():
    b = _sheet_co(_dong("AAA", "2026-10-14"),
                  _dong("MMM", "2026-10-14", phan_quyet="MUA_NGAY", vung=None,
                        so_phien_cho=None))
    theo_ma = {d["symbol"]: d for d in ss.doc_ke_hoach(b)}
    h = skh.dong_hien_thi(theo_ma["AAA"])
    assert h["Vùng chờ"] == (23950.0, 24300.0)
    assert (h["Cắt lỗ cấu trúc"], h["Rủi ro %"], h["Kéo giãn ATR"], h["Giá đóng"]) == \
        (23100.0, 7.6, 1.25, 25000.0)
    assert h["Hiệu lực (phiên)"] == 5 and h["Phán quyết"] == "CHO_VUNG"
    assert h["Lý do"] == ["vì A", "vì B"] and h["Sổ ảo"] is None
    m = skh.dong_hien_thi(theo_ma["MMM"])
    assert m["Vùng chờ"] is None and m["Hiệu lực (phiên)"] is None
    assert m["Phán quyết"] == "MUA_NGAY"


def test_vung_chi_hien_khi_CO_CA_HAI_bien():
    d = {"vung_day": 23950.0, "vung_tran": None}
    assert skh.dong_hien_thi(d)["Vùng chờ"] is None
    d = {"vung_day": None, "vung_tran": 24300.0}
    assert skh.dong_hien_thi(d)["Vùng chờ"] is None


def test_GHI_LUC_theo_GIO_VN_khong_theo_mui_gio_may():
    """Phát đầu: lượt quét 07:10 UTC phải hiện 14:10 — Cloud chạy UTC sẽ in 07:10."""
    assert skh.dong_hien_thi({"at": AT_0710_UTC})["Ghi lúc"] == "15/10 14:10"
    assert skh.dong_hien_thi({"at": None})["Ghi lúc"] is None
    assert skh.dong_hien_thi({})["Ghi lúc"] is None


def test_GHI_LUC_doi_gio_bang_mui_GIO_VN_doc_tu_NGUON():
    """Máy này chạy giờ VN nên `fromtimestamp(at)` THIẾU múi giờ vẫn ra 14:10 ở đây
    và chỉ lệch trên máy UTC (CI, Streamlit Cloud). Phép kiểm giá trị ở trên không
    bắt được điều đó ở máy; đọc HÌNH DẠNG lời gọi từ nguồn thì bắt được ở mọi máy."""
    from datetime import timedelta, timezone
    assert skh.GIO_VN == timezone(timedelta(hours=7))
    ham = _ham(_cay("so_ke_hoach.py"), "dong_hien_thi")
    goi = [n for n in ast.walk(ham) if isinstance(n, ast.Call)
           and isinstance(n.func, ast.Attribute) and n.func.attr == "fromtimestamp"]
    assert goi, "dong_hien_thi phải đổi `at` bằng fromtimestamp"
    for n in goi:
        mui = n.args[1] if len(n.args) > 1 else next(
            (k.value for k in n.keywords if k.arg == "tz"), None)
        assert isinstance(mui, ast.Name) and mui.id == "GIO_VN", ast.unparse(n)


def test_ly_do_doc_JSON_va_o_HONG_tra_NGUYEN_chu():
    assert skh.ly_do_tu_o('["a", "b"]') == ["a", "b"]
    assert skh.ly_do_tu_o("") == [] and skh.ly_do_tu_o(None) == []
    assert skh.ly_do_tu_o("không phải json") == ["không phải json"]
    assert skh.ly_do_tu_o('{"x": 1}') == ['{"x": 1}']


def _lenh(id_, ma, ngay, st="OPEN"):
    return SimpleNamespace(id=id_, symbol=ma, signal_date=ngay, status=st)


def test_noi_lenh_khop_theo_10_KY_TU_ngay_va_giu_id_LON_nhat():
    lenh = [_lenh(5, "AAA", "2026-10-14", "OPEN"),
            _lenh(1, "AAA", "2026-10-14 00:00:00", "CLOSED"),
            _lenh(3, "BBB", "2026-10-15T00:00:00", "PENDING"),
            _lenh(7, "CCC", None), _lenh(8, "DDD", "")]
    noi = skh.noi_lenh(lenh)
    assert set(noi) == {("AAA", "2026-10-14"), ("BBB", "2026-10-15")}
    assert noi[("AAA", "2026-10-14")].id == 5
    assert noi[skh.khoa_tin_hieu("BBB", "2026-10-15 00:00:00")].id == 3
    h = skh.dong_hien_thi({"symbol": "AAA"}, noi[("AAA", "2026-10-14")])
    assert h["Sổ ảo"] == "#5 OPEN"


def _qd(seq, ma, ngay, acted=0, ly_do="VN-INDEX nằm dưới MA50"):
    return {"seq": seq, "symbol": ma, "signal_date": ngay, "acted": acted,
            "skip_reason": ly_do}


def test_noi_quyet_dinh_khop_10_KY_TU_va_giu_seq_LON_nhat():
    noi = skh.noi_quyet_dinh([_qd(20200, "HHP", "2026-10-14", ly_do="lượt sau"),
                              _qd(20129, "HHP", "2026-10-14 00:00:00", ly_do="lượt đầu"),
                              _qd(5, "XXX", None), _qd(6, "YYY", "")])
    assert set(noi) == {("HHP", "2026-10-14")}
    assert noi[("HHP", "2026-10-14")]["skip_reason"] == "lượt sau"


def test_cot_SO_AO_lenh_truoc_roi_LY_DO_khong_mo_roi_moi_den_gach():
    lenh, qd = _lenh(5, "AAA", "2026-10-14"), _qd(9, "AAA", "2026-10-14")
    assert skh.o_so_ao(lenh, qd) == "#5 OPEN"            # có lệnh thì lệnh thắng
    assert skh.o_so_ao(None, qd) == "không mở — VN-INDEX nằm dưới MA50"
    assert skh.o_so_ao(None, _qd(9, "AAA", "2026-10-14", ly_do="")) is None
    assert skh.o_so_ao(None, _qd(9, "AAA", "2026-10-14", ly_do=None)) is None
    assert skh.o_so_ao() is None
    h = skh.dong_hien_thi({"symbol": "AAA"}, None, qd)
    assert h["Sổ ảo"] == "không mở — VN-INDEX nằm dưới MA50"


def test_noi_lenh_id_LON_thang_ca_khi_dung_TRUOC():
    noi = skh.noi_lenh([_lenh(1, "AAA", "2026-10-14"), _lenh(9, "AAA", "2026-10-14"),
                        _lenh(4, "AAA", "2026-10-14")])
    assert noi[("AAA", "2026-10-14")].id == 9


# ───────────────────────── 3. App ─────────────────────────

def test_app_doc_ke_hoach_qua_ham_CO_DEM_va_chi_doc():
    cay = _cay("app.py")
    ham = _ham(cay, "_doc_ke_hoach")
    assert any("st.cache_data" in ast.unparse(d) for d in ham.decorator_list), \
        "đọc Sheets mỗi lượt vẽ là hết hạn mức"
    goi = _goi(ham)
    assert "load_ke_hoach_from_google_sheets" in goi
    assert not (TEN_GHI & goi), sorted(TEN_GHI & goi)


def test_khoi_hien_KHONG_lap_lai_ke_hoach_va_chi_doc():
    cay = _cay("app.py")
    khoi = _ham(cay, "_khoi_ke_hoach_da_ghi")
    goi = _goi(khoi)
    assert {"_doc_ke_hoach", "dong_hien_thi", "noi_lenh", "noi_quyet_dinh",
            "_doc_so_ban_tin"} <= goi
    assert "lap_ke_hoach" not in goi, "bảng này là bản GHI tại ngày nến, không tính lại"
    # cột "Sổ ảo" cần CẢ lệnh lẫn quyết định: thiếu đối số thứ ba thì lý do không mở mất
    goi_dht = [n for n in ast.walk(khoi) if isinstance(n, ast.Call)
               and isinstance(n.func, ast.Attribute) and n.func.attr == "dong_hien_thi"]
    assert goi_dht and all(len(n.args) == 3 for n in goi_dht), \
        [ast.unparse(n) for n in goi_dht]
    assert not (TEN_GHI & goi), sorted(TEN_GHI & goi)
    nhac = {n.id for n in ast.walk(khoi) if isinstance(n, ast.Name)} \
        | {n.attr for n in ast.walk(khoi) if isinstance(n, ast.Attribute)}
    assert not ({"PaperTradingJournal", "all_trades", "DB_PATH"} & nhac)


def test_tab_Lich_su_giao_dich_GOI_khoi_ke_hoach_da_ghi():
    cay = _cay("app.py")
    khoi = next(n for n in cay.body if isinstance(n, ast.With)
                and any(isinstance(i.context_expr, ast.Name) and i.context_expr.id == "t_hist"
                        for i in n.items))
    assert "_khoi_ke_hoach_da_ghi" in _goi(khoi)
