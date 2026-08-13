"""Test lớp gọi gọn google_sheets_sync.

Module này từng tự ghi Sheet bằng lược đồ riêng và bịa số. Test ở đây khoá
lại đúng chỗ đó: vỏ phải ghi CÙNG lược đồ với sheets_store, và tỷ trọng
phải là số thật chứ không phải hằng số 30.

Chạy offline:  python3 tests/test_google_sheets_sync.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import market_filter
import google_sheets_sync as gs
import sheets_store as ss
from paper_trading import PaperTradingJournal, Status

market_filter.is_vni_bullish = lambda _d: True


def make_result(score: int = 70, sl: float = 90.0, tp: float = 120.0,
                entry: float = 100.0) -> dict:
    return {
        "final_score": score,
        "recommendation": "MUA 📈" if score >= 62 else "NẮM GIỮ 👀",
        "data_quality": "OK",
        "score_breakdown": {"trend_score": 70.0, "momentum_score": 65.0},
        "key_reasons": ["Xu hướng tăng"],
        "safety": {"safe_position_size": 10.0},
        "analyses": {"risk": {"recommendations": {
            "entry_price": entry, "stop_loss_price": sl,
            "take_profit_price": tp, "suggested_position_size_pct": 10.0}}},
    }


def so_lenh_mau() -> PaperTradingJournal:
    j = PaperTradingJournal(":memory:")
    j.consider_entry("FPT", "2026-01-05", make_result())
    j.fill_pending("FPT", "2026-01-06", 100.0)
    j.evaluate_open("FPT", "2026-01-20", {"open": 95.0, "high": 96.0,
                                          "low": 88.0, "close": 89.0})
    j.consider_entry("ACB", "2026-02-05", make_result())
    j.fill_pending("ACB", "2026-02-06", 21110.0)
    j.consider_entry("VNM", "2026-02-05", make_result(score=40))
    return j


# ── Chốt chặn: không được tái diễn số bịa ────────────────────────────
def test_ty_trong_la_so_that_khong_phai_hang_so_30():
    """Bản cũ đọc `t.position_size_pct` — trường KHÔNG tồn tại trên Trade
    (tên thật là `size_pct`) nên getattr rơi về mặc định và ghi 30 cho mọi
    lệnh. 30% × số lệnh chồng lấn đúng là phép tính đẻ ra '+636,11%'."""
    goc = so_lenh_mau()
    that = {t.symbol: t.size_pct for t in goc.all_trades()}
    assert 30.0 not in that.values(), "dữ liệu mẫu vô tình trùng 30, đổi mẫu đi"

    sheet = ss.InMemorySheet()
    gs.sync_trades_to_google_sheets(goc, backend=sheet)

    doc_lai = {t.symbol: t.size_pct
               for t in gs.load_trades_from_google_sheets(backend=sheet)}
    assert doc_lai == that, f"tỷ trọng sai\nthật: {that}\nđọc: {doc_lai}"
    print(f"PASS  tỷ trọng giữ số thật {that}, không phải hằng số 30")


def test_vo_ghi_cung_luoc_do_voi_sheets_store():
    """Hai lược đồ khác nhau trên cùng một Sheet là hỏng kho ngoài."""
    goc = so_lenh_mau()
    a, b = ss.InMemorySheet(), ss.InMemorySheet()
    gs.sync_trades_to_google_sheets(goc, backend=a)
    ss.push(goc.db, b)
    assert a.tabs == b.tabs, "vỏ ghi khác ruột — phải giống hệt từng ô"
    assert tuple(a.read_rows(ss.TAB_TRADES)[0]) == ss.TRADE_COLS
    print(f"PASS  vỏ ghi đúng {len(ss.TRADE_COLS)} cột, giống hệt sheets_store")


def test_day_ca_decisions_khong_chi_trades():
    """Chỉ ghi lệnh đã mở thì chính sổ đã có thiên lệch chọn mẫu."""
    goc = so_lenh_mau()
    sheet = ss.InMemorySheet()
    bc = gs.sync_trades_to_google_sheets(goc, backend=sheet)
    assert bc["decisions_moi"] == 3, bc
    assert ss.TAB_DECISIONS in sheet.tabs
    print(f"PASS  đẩy cả {bc['decisions_moi']} quyết định, không riêng lệnh")


def test_goi_theo_kieu_cu_thi_no_chu_khong_bia():
    """Truyền list[Trade] như bản cũ -> báo lỗi rõ ràng, không âm thầm bịa."""
    goc = so_lenh_mau()
    sheet = ss.InMemorySheet()
    try:
        gs.sync_trades_to_google_sheets(goc.all_trades(), backend=sheet)
        raise AssertionError("truyền list mà vẫn chạy — phải nổ")
    except gs.ChuKySaiError as e:
        assert "list[Trade]" in str(e) and "size_pct" in str(e)
    assert sheet.tabs == {}, "đã ghi gì đó lên sheet dù chữ ký sai"
    print("PASS  gọi kiểu cũ -> ChuKySaiError, không ghi gì lên sheet")


# ── Nhận nhiều kiểu nguồn ────────────────────────────────────────────
def test_nhan_journal_connection_va_duong_dan():
    goc = so_lenh_mau()
    a, b = ss.InMemorySheet(), ss.InMemorySheet()
    gs.sync_trades_to_google_sheets(goc, backend=a)
    gs.sync_trades_to_google_sheets(goc.db, backend=b)
    assert a.tabs == b.tabs
    print("PASS  nhận cả journal lẫn connection, kết quả như nhau")


# ── Chưa cấu hình thì tắt sạch ───────────────────────────────────────
def test_chua_cau_hinh_thi_tat_sach():
    import sheets_store
    that = sheets_store.open_from_secrets
    sheets_store.open_from_secrets = lambda *a, **k: None
    try:
        assert gs.is_google_sheets_enabled() is False
        assert gs.sync_trades_to_google_sheets() is None
        assert gs.load_trades_from_google_sheets() == []
        assert gs.restore_journal_from_google_sheets() is None
        assert gs.trang_thai()["bat"] is False
    finally:
        sheets_store.open_from_secrets = that
    print("PASS  chưa cấu hình -> None/[] , không vỡ, không đụng đĩa")


# ── Khôi phục vẫn từ chối ghi đè ─────────────────────────────────────
def test_khoi_phuc_tu_choi_ghi_de_so_dang_co_du_lieu():
    import tempfile
    goc = so_lenh_mau()
    sheet = ss.InMemorySheet()
    gs.sync_trades_to_google_sheets(goc, backend=sheet)

    with tempfile.TemporaryDirectory() as d:
        dich = os.path.join(d, "so.db")
        j = PaperTradingJournal(dich)
        j.consider_entry("XXX", "2026-01-01", make_result())
        truoc = len(j.all_trades())
        j.db.close()

        try:
            gs.restore_journal_from_google_sheets(dich, backend=sheet)
            raise AssertionError("phải từ chối ghi đè")
        except ss.SheetError as e:
            assert "từ chối" in str(e)

        j2 = PaperTradingJournal(dich)
        assert len(j2.all_trades()) == truoc, "sổ đích bị đụng dù đã từ chối"
        j2.db.close()

        bc = gs.restore_journal_from_google_sheets(dich, allow_overwrite=True,
                                                   backend=sheet)
        j3 = PaperTradingJournal(dich)
        assert bc["trades"] == 2 and len(j3.all_trades()) == 2
        assert "XXX" not in {t.symbol for t in j3.all_trades()}
        j3.db.close()
    print("PASS  khôi phục từ chối ghi đè, allow_overwrite=True thì thay")


def test_load_tra_ve_trade_that_khong_phai_dict_tho():
    goc = so_lenh_mau()
    sheet = ss.InMemorySheet()
    gs.sync_trades_to_google_sheets(goc, backend=sheet)
    ds = gs.load_trades_from_google_sheets(backend=sheet)
    assert len(ds) == 2
    dong = [t for t in ds if t.status == Status.CLOSED][0]
    assert dong.net_return_pct() is not None, "phải là Trade dùng được ngay"
    assert dong.exit_reason == "STOP_LOSS"
    print(f"PASS  trả về Trade thật, tính được lợi nhuận "
          f"{dong.net_return_pct():+.2f}%")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
        except Exception as e:
            failed += 1
            print(f"FAIL  {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n===== {len(fns) - failed}/{len(fns)} test PASS =====")
    sys.exit(1 if failed else 0)
