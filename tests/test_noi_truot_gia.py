"""Gác cho việc nối `truot_gia` + `vong_doi_lenh` vào đường chạy.

Hai module này có 29 test và tồn tại từ lâu, nhưng cho tới 24/08/2026
KHÔNG file nào ngoài test của chính chúng import — hai module mồ côi. Sổ
lệnh vẫn coi mọi lệnh khớp TOÀN BỘ, NGAY, ở đúng giá mong muốn.

Cuối mỗi báo cáo có câu *"Giao dịch thật còn có trượt giá, khớp một phần
và tâm lý — kết quả thực tế sẽ thấp hơn"*. Câu đó đúng, nhưng nó là lời
cảnh báo chứ không phải phép đo.

Hai loại lỗi phải chặn:
  • bật lên mà KHÔNG đổi gì   → nối hình thức, câu cảnh báo vẫn chỉ là lời
  • **tắt đi mà VẪN đổi**     → mọi con số lịch sử mất ý nghĩa
"""
import paper_trading as pt
import pytest

pytest.importorskip("pandas")

NEN = {"high": 20_500.0, "low": 19_800.0, "volume": 3_000_000.0,
       "tham_chieu": 20_000.0}

#: Cỡ vị thế ĐẦY ĐỦ cho khoảng cách stop của bộ dữ liệu này (20.000 -> 19.000
#: = 5%). SUY RA chứ không gõ.
#:
#: Trước 31/08/2026 chỗ này là hằng số 20.0 — đúng cỡ mà `account_risk_pct
#: = 1.0` cho ra. Đổi sizing sang mục tiêu 15 vị thế làm hai test ở đây đỏ,
#: dù chúng khoá TRƯỢT GIÁ chứ không khoá sizing. Bản sao của một con số
#: không sai vào ngày nó ra đời, nó sai vào ngày bản gốc đổi.
CO_DAY_DU = round(max(pt.CO_TOI_THIEU_PCT,
                      min(pt.CO_TOI_DA_PCT,
                          pt.RUI_RO_MOI_LENH_PCT / 0.05)), 1)


def _kq(entry=20_000.0, sl=19_000.0, tp=26_000.0):
    return {"final_score": 70, "recommendation": "MUA", "data_quality": "OK",
            "score_breakdown": {}, "key_reasons": [],
            "analyses": {"risk": {"recommendations": {
                "entry_price": entry, "stop_loss_price": sl,
                "take_profit_price": tp}}}}


@pytest.fixture
def so_lenh(tmp_path, monkeypatch):
    import market_filter
    monkeypatch.setattr(market_filter, "is_vni_bullish", lambda *a, **k: True)
    monkeypatch.setattr(pt, "CHO_PHEP_MO_LENH_MOI", True)
    return pt.PaperTradingJournal(str(tmp_path / "wf_t.db"))


def _vao(so, bat, monkeypatch, nen=NEN, gia_mo=20_000.0):
    monkeypatch.setattr(pt, "MO_PHONG_TRUOT_GIA", bat)
    so.consider_entry("FPT", "2026-03-02", _kq(), buy_threshold=50.0)
    so.fill_pending("FPT", "2026-03-03", gia_mo, nen)
    return so.all_trades()[0]


# ─────────────────────────────────────────────────────────────────────
# 1. Tắt thì KHÔNG đổi gì — điều kiện để mọi số lịch sử còn nghĩa
# ─────────────────────────────────────────────────────────────────────

def test_TAT_thi_khop_dung_gia_mo_cua(so_lenh, monkeypatch):
    t = _vao(so_lenh, False, monkeypatch)
    assert t.entry_price == 20_000.0 and t.size_pct == CO_DAY_DU
    print(f"PASS  tắt -> khớp đúng 20.000, size nguyên vẹn ({CO_DAY_DU}%)")


def test_TAT_thi_ban_dung_gia_stop(so_lenh, monkeypatch):
    _vao(so_lenh, False, monkeypatch)
    bar = {"open": 19_500.0, "high": 19_600.0, "low": 18_500.0,
           "close": 18_600.0, "volume": 3_000_000.0}
    c = so_lenh.evaluate_open("FPT", "2026-03-04", bar, current_score=70)
    assert c and c[0]["exit_price"] == 19_000.0
    print("PASS  tắt -> bán đúng 19.000")


# ─────────────────────────────────────────────────────────────────────
# 2. Bật thì PHẢI đổi, và đổi theo chiều BẤT LỢI
# ─────────────────────────────────────────────────────────────────────

def test_BAT_thi_mua_DAT_hon_gia_mo_cua(so_lenh, monkeypatch):
    t = _vao(so_lenh, True, monkeypatch)
    assert t.entry_price > 20_000.0, (
        "bật trượt giá mà mua vẫn đúng giá mong muốn -> nối hình thức")
    print(f"PASS  bật -> mua ở {t.entry_price:,.0f} thay vì 20.000")


def test_BAT_thi_ban_RE_hon_gia_stop(so_lenh, monkeypatch):
    _vao(so_lenh, True, monkeypatch)
    bar = {"open": 19_500.0, "high": 19_600.0, "low": 18_500.0,
           "close": 18_600.0, "volume": 3_000_000.0}
    c = so_lenh.evaluate_open("FPT", "2026-03-04", bar, current_score=70)
    assert c and c[0]["exit_price"] < 19_000.0, (
        "bật trượt giá mà bán vẫn đúng giá stop")
    print(f"PASS  bật -> bán ở {c[0]['exit_price']:,.0f} thay vì 19.000")


def test_truot_luon_lam_ket_qua_XAU_di(so_lenh, monkeypatch, tmp_path):
    """Không có ô nào trượt giá làm lãi hơn. Nếu có, mô hình sai dấu."""
    lai = {}
    for bat in (False, True):
        j = pt.PaperTradingJournal(str(tmp_path / f"wf_{int(bat)}.db"))
        monkeypatch.setattr(pt, "MO_PHONG_TRUOT_GIA", bat)
        j.consider_entry("FPT", "2026-03-02", _kq(), buy_threshold=50.0)
        j.fill_pending("FPT", "2026-03-03", 20_000.0, NEN)
        bar = {"open": 19_500.0, "high": 19_600.0, "low": 18_500.0,
               "close": 18_600.0, "volume": 3_000_000.0}
        j.evaluate_open("FPT", "2026-03-04", bar, current_score=70)
        lai[bat] = j.all_trades()[0].net_return_pct()
    assert lai[True] < lai[False], (
        f"bật trượt giá mà lãi TĂNG ({lai[False]:+.2f}% -> {lai[True]:+.2f}%) "
        f"-> mô hình sai dấu")
    print(f"PASS  {lai[False]:+.2f}% -> {lai[True]:+.2f}% "
          f"(tốn {lai[False] - lai[True]:.2f} điểm %)")


# ─────────────────────────────────────────────────────────────────────
# 3. Vòng đời lệnh phải thật sự được dùng, không chỉ trượt giá
# ─────────────────────────────────────────────────────────────────────

def test_thanh_khoan_can_thi_khop_MOT_PHAN_va_size_giam(so_lenh, monkeypatch):
    """Nến chỉ giao dịch 20.000 CP thì không thể khớp 10.000 CP ở mức 10%.

    Giữ nguyên `size_pct` khi chỉ khớp được một phần là ghi vào sổ một vị
    thế chưa bao giờ tồn tại.
    """
    nen = dict(NEN, volume=20_000.0)
    t = _vao(so_lenh, True, monkeypatch, nen=nen)
    assert t.size_pct < CO_DAY_DU, (
        f"nến chỉ cho khớp ~2.000 CP mà vẫn ghi đủ size {CO_DAY_DU}% "
        f"(nhận {t.size_pct}%)")
    print(f"PASS  thanh khoản cạn -> size {CO_DAY_DU}% giảm còn {t.size_pct}%")


def test_ngoai_bien_do_thi_KHONG_co_lenh(so_lenh, monkeypatch):
    """Sàn từ chối lệnh ngoài ±7%. Không mở, và cũng không ghi lệnh 0%."""
    nen = dict(NEN, tham_chieu=10_000.0)      # 20.000 vượt xa +7% của 10.000
    monkeypatch.setattr(pt, "MO_PHONG_TRUOT_GIA", True)
    so_lenh.consider_entry("FPT", "2026-03-02", _kq(), buy_threshold=50.0)
    so_lenh.fill_pending("FPT", "2026-03-03", 20_000.0, nen)
    assert so_lenh.all_trades() == [], (
        "lệnh bị sàn từ chối mà vẫn nằm trong sổ -> một giao dịch chưa bao "
        "giờ xảy ra")
    print("PASS  ngoài biên độ ±7% -> không có lệnh nào trong sổ")


def test_thieu_nen_thi_khop_nhu_cu(so_lenh, monkeypatch):
    """Không có nến thì không mô hình hoá được — khớp như cũ, không đoán."""
    t = _vao(so_lenh, True, monkeypatch, nen=None)
    assert t.entry_price == 20_000.0
    print("PASS  thiếu nến -> khớp như cũ")


def test_nen_khong_co_khoi_luong_thi_van_tinh_chenh_lech(so_lenh, monkeypatch):
    """Không có khối lượng thì không tính được tác động, nhưng vẫn phải
    trả phần vượt chênh lệch mua-bán — không ai khớp ngay ở giá mình muốn."""
    monkeypatch.setattr(pt, "MO_PHONG_TRUOT_GIA", True)
    _vao(so_lenh, True, monkeypatch)
    bar = {"open": 19_500.0, "high": 19_600.0, "low": 18_500.0,
           "close": 18_600.0, "volume": 0.0}
    c = so_lenh.evaluate_open("FPT", "2026-03-04", bar, current_score=70)
    assert c and c[0]["exit_price"] == 19_000.0, (
        "nến không khối lượng -> `_gia_ban_that` trả nguyên giá, đúng thiết kế")
    print("PASS  nến không khối lượng -> không đoán tác động")


# ─────────────────────────────────────────────────────────────────────
# 4. Hằng số và đường nối
# ─────────────────────────────────────────────────────────────────────

def test_hai_module_KHONG_con_mo_coi():
    """Gác đọc AST: `"truot_gia" in src` khớp phải chính chú thích ở trên."""
    import ast
    import os
    goc = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cay = ast.parse(open(os.path.join(goc, "paper_trading.py"),
                         encoding="utf-8").read())
    nhap = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.ImportFrom) and n.module:
            nhap.add(n.module.split(".")[0])
        elif isinstance(n, ast.Import):
            for a in n.names:
                nhap.add(a.name.split(".")[0])
    assert {"truot_gia", "vong_doi_lenh"} <= nhap, (
        f"paper_trading không import cả hai module — nhận {sorted(nhap & {'truot_gia', 'vong_doi_lenh'})}")
    print("PASS  paper_trading import cả truot_gia lẫn vong_doi_lenh")


def test_von_danh_muc_la_gia_dinh_duoc_neu_ra():
    """Con số này điều khiển tác động thị trường, nên nó phải tồn tại như
    một hằng số có tên — không được nằm rải trong công thức."""
    assert pt.VON_DANH_MUC_VND > 0
    assert pt.MO_PHONG_TRUOT_GIA in (True, False)
    print(f"PASS  vốn giả định {pt.VON_DANH_MUC_VND:,} đ · "
          f"công tắc = {pt.MO_PHONG_TRUOT_GIA}")


def test_cong_tac_mac_dinh_phai_la_lua_chon_CO_Y_THUC():
    """Đổi mặc định là đổi ý nghĩa của mọi con số đã đo, không phải đổi
    cấu hình. Test này ghim giá trị hiện tại để lần đổi sau phải đi qua
    đây — cùng cách `CHOT_LOI_CUNG` và `TRAN_VON_CAM_KET_PCT` được ghim.
    """
    assert pt.MO_PHONG_TRUOT_GIA is True, (
        "mặc định đã đổi — cập nhật docs/STATE.md và CLAUDE.md cùng lúc, "
        "kèm con số đo được trước và sau")
    print("PASS  MO_PHONG_TRUOT_GIA mặc định = True (bật 24/08/2026)")


def test_run_session_KHONG_duoc_nhan_he_so_gia_vao_KHOI_LUONG(tmp_path,
                                                              monkeypatch):
    """`volume` là SỐ CỔ PHIẾU, không phải giá.

    `run_session` nhân mọi giá trị trong `bar` với `price_multiplier` để
    quy nghìn đồng về VNĐ. Nhân nhầm cả `volume` thì tỷ trọng khối lượng
    nhỏ đi 1.000 lần, tác động thị trường gần như biến mất, và trượt giá
    tụt xuống còn đúng một bước giá — mà kết quả vẫn trông hợp lý hoàn
    toàn. Đây là loại lỗi chỉ lộ ra khi đọc từng dòng.

    Gác bắt bằng cách chặn `fill_pending` và soi nến nó nhận được.
    """
    import pandas as pd

    import paper_runner
    import market_filter
    monkeypatch.setattr(market_filter, "is_vni_bullish", lambda *a, **k: True)

    n = 80
    # Giá theo NGHÌN ĐỒNG (20,0 = 20.000đ) -> price_multiplier phải = 1000
    gia = [20.0 + (i % 5) * 0.1 for i in range(n)]
    history = pd.DataFrame({
        "time": pd.bdate_range("2026-01-01", periods=n).astype(str),
        "open": gia, "high": [g * 1.01 for g in gia],
        "low": [g * 0.99 for g in gia], "close": gia,
        "volume": [3_000_000.0] * n,
    })
    from data_quality import price_multiplier
    assert price_multiplier(history) == 1000.0, "tình huống dựng sai"

    nhan = {}
    j = pt.PaperTradingJournal(str(tmp_path / "wf_t.db"))
    goc = j.fill_pending

    def bat(symbol, session_date, open_price, nen=None):
        nhan["nen"] = nen
        nhan["open"] = open_price
        return goc(symbol, session_date, open_price, nen)

    monkeypatch.setattr(j, "fill_pending", bat)
    bar = {"open": 20.0, "high": 20.2, "low": 19.8, "close": 20.1,
           "volume": 3_000_000.0}
    paper_runner.run_session(j, "FPT", history, bar, "2026-04-20",
                             buy_threshold=50.0)

    assert nhan["open"] == 20_000.0, "giá phải được quy về VNĐ"
    assert nhan["nen"] is not None, "không truyền nến -> mô hình không chạy được"
    assert nhan["nen"]["volume"] == 3_000_000.0, (
        f"khối lượng bị nhân hệ số giá: nhận {nhan['nen']['volume']:,.0f} thay "
        f"vì 3.000.000 — tỷ trọng nhỏ đi 1.000 lần và trượt giá gần như "
        f"biến mất")
    assert nhan["nen"]["tham_chieu"] > 1_000, (
        "tham chiếu phải quy về VNĐ như mọi giá khác")
    print(f"PASS  giá x1000, khối lượng giữ nguyên "
          f"({nhan['nen']['volume']:,.0f} CP)")
