"""Test kho ngoài Google Sheets.

Sổ lệnh là bằng chứng. Một đường sao lưu làm mất, nhân đôi, hay đọc lệch
cột thì tệ hơn không có đường nào — vì nó tạo cảm giác an toàn giả.

Bốn bất biến:
  1. Đẩy rồi kéo về phải ra ĐÚNG sổ cũ (id, seq, kiểu số, giá trị None).
  2. Đẩy hai lần không nhân đôi decision.
  3. pull() từ chối ghi đè sổ đang có dữ liệu.
  4. Lệch cấu trúc cột thì NỔ, không đoán.

Chạy offline:  python3 tests/test_sheets_store.py
Không cần mạng, không cần credential Google.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import market_filter
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
    """Sổ có đủ ba trạng thái: 1 lệnh đóng, 1 lệnh đang mở, 1 lệnh chờ khớp,
    cộng vài quyết định KHÔNG vào lệnh."""
    j = PaperTradingJournal(":memory:")

    # lệnh đã đóng
    j.consider_entry("FPT", "2026-01-05", make_result())
    j.fill_pending("FPT", "2026-01-06", 100.0)
    j.evaluate_open("FPT", "2026-01-20", {"open": 95.0, "high": 96.0,
                                          "low": 88.0, "close": 89.0})
    # lệnh đang mở
    j.consider_entry("ACB", "2026-02-05", make_result())
    j.fill_pending("ACB", "2026-02-06", 21110.0)
    # lệnh chờ khớp — entry_price còn None, đây là chỗ dễ mất kiểu nhất
    j.consider_entry("HPG", "2026-03-05", make_result())
    # quyết định không vào lệnh
    j.consider_entry("VNM", "2026-03-05", make_result(score=40))
    j.consider_entry("SSI", "2026-03-06", make_result(score=30))
    return j


def _anh_chup(j: PaperTradingJournal) -> tuple:
    """Ảnh chụp sổ qua API công khai, để so sánh trước/sau."""
    trades = [(t.id, t.symbol, t.signal_date, t.entry_date, t.entry_price,
               t.exit_date, t.exit_price, t.exit_reason, t.stop_loss,
               t.take_profit, t.size_pct, t.entry_score, t.status)
              for t in j.all_trades()]
    dec = [(d["seq"], d["symbol"], d["signal_date"], d["score"],
            d["acted"], d["data_quality"]) for d in j.decisions()]
    return trades, dec


# ── 1. Vòng đẩy–kéo không mất dữ liệu ────────────────────────────────
def test_day_roi_keo_ve_ra_dung_so_cu():
    goc = so_lenh_mau()
    truoc = _anh_chup(goc)

    sheet = ss.InMemorySheet()
    bao_cao = ss.push(goc.db, sheet)
    assert bao_cao["trades"] == 3, bao_cao
    assert bao_cao["decisions_moi"] == 5, bao_cao

    moi = PaperTradingJournal(":memory:")
    ss.pull(moi.db, sheet)
    sau = _anh_chup(moi)

    assert sau == truoc, (
        f"vòng đẩy-kéo làm đổi dữ liệu\ntrước: {truoc[0][:2]}\nsau  : {sau[0][:2]}")
    print(f"PASS  đẩy-kéo giữ nguyên {len(truoc[0])} lệnh và "
          f"{len(truoc[1])} quyết định")


def test_giu_dung_kieu_so_va_gia_tri_none():
    """Sheets trả về CHUỖI. Kiểu số và None phải dựng lại đúng, nếu không
    `low <= stop_loss` sẽ so chuỗi với số và sổ hỏng âm thầm."""
    goc = so_lenh_mau()
    sheet = ss.InMemorySheet()
    ss.push(goc.db, sheet)
    moi = PaperTradingJournal(":memory:")
    ss.pull(moi.db, sheet)

    cho = [t for t in moi.all_trades() if t.status == Status.PENDING]
    assert len(cho) == 1
    assert cho[0].entry_price is None, (
        f"lệnh chờ khớp phải có entry_price=None, nhận {cho[0].entry_price!r}")

    dong = [t for t in moi.all_trades() if t.status == Status.CLOSED][0]
    assert isinstance(dong.entry_price, float)
    assert isinstance(dong.exit_price, float)
    assert isinstance(dong.entry_score, int)
    assert dong.net_return_pct() is not None
    print(f"PASS  kiểu số dựng lại đúng, lệnh chờ giữ entry_price=None")


def test_giu_nguyen_id_va_seq():
    """Đánh số lại sẽ làm lần đẩy sau nhân đôi dữ liệu."""
    goc = so_lenh_mau()
    id_goc = [t.id for t in goc.all_trades()]
    seq_goc = [d["seq"] for d in goc.decisions()]

    sheet = ss.InMemorySheet()
    ss.push(goc.db, sheet)
    moi = PaperTradingJournal(":memory:")
    ss.pull(moi.db, sheet)

    assert [t.id for t in moi.all_trades()] == id_goc
    assert [d["seq"] for d in moi.decisions()] == seq_goc
    print(f"PASS  id {id_goc} và seq {seq_goc} giữ nguyên")


def test_ghi_tiep_sau_khoi_phuc_khong_dung_id():
    """Sau khi kéo về, lệnh mới phải nhận id chưa dùng."""
    goc = so_lenh_mau()
    sheet = ss.InMemorySheet()
    ss.push(goc.db, sheet)

    moi = PaperTradingJournal(":memory:")
    ss.pull(moi.db, sheet)
    id_cu = {t.id for t in moi.all_trades()}

    moi.consider_entry("MWG", "2026-04-01", make_result())
    id_moi = [t.id for t in moi.all_trades() if t.id not in id_cu]
    assert len(id_moi) == 1, "lệnh mới không được đè lên id cũ"
    assert id_moi[0] > max(id_cu)
    print(f"PASS  lệnh ghi sau khôi phục nhận id {id_moi[0]}, không đụng id cũ")


# ── 2. Đẩy nhiều lần không nhân đôi ──────────────────────────────────
def test_day_hai_lan_khong_nhan_doi():
    goc = so_lenh_mau()
    sheet = ss.InMemorySheet()
    lan1 = ss.push(goc.db, sheet)
    lan2 = ss.push(goc.db, sheet)

    assert lan1["decisions_moi"] == 5
    assert lan2["decisions_moi"] == 0, "đẩy lại không được thêm decision"

    moi = PaperTradingJournal(":memory:")
    ss.pull(moi.db, sheet)
    assert len(moi.decisions()) == 5
    assert len(moi.all_trades()) == 3
    print("PASS  đẩy hai lần -> vẫn 5 quyết định, 3 lệnh (idempotent)")


def test_chi_day_them_quyet_dinh_moi():
    goc = so_lenh_mau()
    sheet = ss.InMemorySheet()
    ss.push(goc.db, sheet)

    goc.consider_entry("GAS", "2026-04-02", make_result(score=35))
    bao_cao = ss.push(goc.db, sheet)
    assert bao_cao["decisions_moi"] == 1, bao_cao
    assert bao_cao["decisions_da_co"] == 5, bao_cao

    moi = PaperTradingJournal(":memory:")
    ss.pull(moi.db, sheet)
    assert [d["symbol"] for d in moi.decisions()][-1] == "GAS"
    print("PASS  chỉ đẩy thêm 1 quyết định mới, không ghi lại 5 cái cũ")


def test_lenh_doi_trang_thai_duoc_cap_nhat():
    """trades soi gương toàn phần: PENDING -> OPEN phải phản ánh lên sheet."""
    goc = so_lenh_mau()
    sheet = ss.InMemorySheet()
    ss.push(goc.db, sheet)

    goc.fill_pending("HPG", "2026-03-06", 27500.0)
    ss.push(goc.db, sheet)

    moi = PaperTradingJournal(":memory:")
    ss.pull(moi.db, sheet)
    hpg = [t for t in moi.all_trades() if t.symbol == "HPG"][0]
    assert hpg.status == Status.OPEN and hpg.entry_price == 27500.0
    assert len(moi.all_trades()) == 3, "không được sinh thêm dòng HPG thứ hai"
    print("PASS  HPG chờ->mở được cập nhật, không sinh dòng trùng")


# ── 2b. Chặn sổ co lại xoá sạch sheet ────────────────────────────────
def test_tu_choi_day_khi_so_local_it_hon_sheet():
    """Kịch bản runner CI: máy sạch không có paper_trades.db -> sổ RỖNG.
    Vì trades ghi đè toàn phần, cú đẩy đầu tiên sẽ xoá trắng lệnh thật
    trên sheet — đúng cơ chế mất 96/113 lệnh ngày 12/08, nhưng tự động và
    lặp lại mỗi lần chạy."""
    goc = so_lenh_mau()
    sheet = ss.InMemorySheet()
    ss.push(goc.db, sheet)
    truoc = sheet.read_rows(ss.TAB_TRADES)

    rong = PaperTradingJournal(":memory:")      # runner sạch
    try:
        ss.push(rong.db, sheet)
        raise AssertionError("phải từ chối đẩy sổ rỗng đè lên sheet có dữ liệu")
    except ss.SheetError as e:
        assert "TỪ CHỐI ĐẨY" in str(e) and "pull()" in str(e)

    assert sheet.read_rows(ss.TAB_TRADES) == truoc, "sheet bị đụng dù đã từ chối"
    print("PASS  sổ rỗng không xoá được 3 lệnh trên sheet")


def test_day_duoc_khi_so_lenh_khong_giam():
    """Không được cản trở đường chạy bình thường: bằng hoặc nhiều hơn thì qua."""
    goc = so_lenh_mau()
    sheet = ss.InMemorySheet()
    ss.push(goc.db, sheet)
    ss.push(goc.db, sheet)                       # bằng -> qua

    goc.consider_entry("MWG", "2026-04-01", make_result())
    bc = ss.push(goc.db, sheet)                  # nhiều hơn -> qua
    assert bc["trades"] == 4
    print("PASS  số lệnh bằng hoặc tăng -> đẩy bình thường")


def test_co_lai_van_duoc_khi_noi_ro():
    goc = so_lenh_mau()
    sheet = ss.InMemorySheet()
    ss.push(goc.db, sheet)
    rong = PaperTradingJournal(":memory:")
    bc = ss.push(rong.db, sheet, cho_phep_co_lai=True)
    assert bc["trades"] == 0
    print("PASS  cho_phep_co_lai=True thì vẫn thay được bằng bản nhỏ hơn")


# ── 3. pull() từ chối ghi đè ─────────────────────────────────────────
def test_pull_tu_choi_ghi_de_so_dang_co_du_lieu():
    """Đây chính là cách 96/113 lệnh thật biến mất ngày 12/08/2026."""
    goc = so_lenh_mau()
    sheet = ss.InMemorySheet()
    ss.push(goc.db, sheet)

    dich = so_lenh_mau()          # sổ đích ĐÃ có dữ liệu
    truoc = _anh_chup(dich)
    try:
        ss.pull(dich.db, sheet)
        raise AssertionError("pull() phải từ chối, nhưng đã ghi đè")
    except ss.SheetError as e:
        assert "từ chối" in str(e)

    assert _anh_chup(dich) == truoc, "sổ đích bị đụng dù pull() đã từ chối"
    print("PASS  pull() từ chối ghi đè sổ đang có dữ liệu, sổ nguyên vẹn")


def test_pull_ghi_de_duoc_khi_noi_ro():
    goc = so_lenh_mau()
    sheet = ss.InMemorySheet()
    ss.push(goc.db, sheet)

    dich = PaperTradingJournal(":memory:")
    dich.consider_entry("XXX", "2026-01-01", make_result())
    ss.pull(dich.db, sheet, allow_overwrite=True)

    assert "XXX" not in {t.symbol for t in dich.all_trades()}
    assert len(dich.all_trades()) == 3
    print("PASS  allow_overwrite=True thì thay toàn bộ như mong đợi")


# ── 4. Lệch cấu trúc cột thì nổ ──────────────────────────────────────
def test_lech_cot_thi_no_chu_khong_doan():
    goc = so_lenh_mau()
    sheet = ss.InMemorySheet()
    ss.push(goc.db, sheet)

    # ai đó chèn thêm một cột trên Google Sheet bằng tay
    rows = sheet.read_rows(ss.TAB_TRADES)
    rows[0].insert(3, "ghi_chu_tay")
    sheet.write_all(ss.TAB_TRADES, rows)

    moi = PaperTradingJournal(":memory:")
    try:
        ss.pull(moi.db, sheet)
        raise AssertionError("lệch cột mà vẫn đọc — phải nổ")
    except ss.SheetSchemaError as e:
        assert "lệch" in str(e)
    print("PASS  lệch cấu trúc cột -> SheetSchemaError, không đoán")


def test_giu_nguyen_null_cot_chu():
    """Ô rỗng mang hai nghĩa tuỳ cột, và cả hai phải về đúng chỗ.

    exit_date/exit_reason NULL (lệnh chưa đóng) phải về NULL.
    skip_reason chuỗi rỗng (lệnh có vào) phải về chuỗi rỗng, KHÔNG thành
    NULL. Chọn bừa một nghĩa cho mọi cột chữ là mất dữ liệu âm thầm."""
    goc = so_lenh_mau()
    sheet = ss.InMemorySheet()
    ss.push(goc.db, sheet)
    moi = PaperTradingJournal(":memory:")
    ss.pull(moi.db, sheet)

    mo = [t for t in moi.all_trades() if t.status == Status.OPEN][0]
    assert mo.exit_reason is None, f"NULL phải giữ NULL, nhận {mo.exit_reason!r}"
    assert mo.exit_date is None
    assert mo.exit_price is None

    cho = [t for t in moi.all_trades() if t.status == Status.PENDING][0]
    assert cho.entry_date is None and cho.entry_price is None

    da_vao = [d for d in moi.decisions() if d["acted"] == 1][0]
    assert da_vao["skip_reason"] == "", (
        f"chuỗi rỗng phải giữ chuỗi rỗng, nhận {da_vao['skip_reason']!r}")
    print("PASS  NULL giữ NULL, chuỗi rỗng giữ chuỗi rỗng — đúng từng cột")


def test_ghi_de_khong_di_qua_trang_thai_rong():
    """Ghi đè bảng trades KHÔNG được có khoảnh khắc bảng rỗng.

    Bản đầu dùng clear() rồi update(): mạng đứt giữa hai lệnh là sổ lệnh
    trên kho ngoài mất sạch. Backend thật nay ghi đè bằng một lệnh gọi
    duy nhất. Test này theo dõi mọi trạng thái trung gian mà backend đi
    qua và bắt lỗi nếu có lúc nào bảng rỗng."""
    class SheetTheoDoi(ss.InMemorySheet):
        def __init__(self):
            super().__init__()
            self.lich_su: list[int] = []

        def write_all(self, tab, rows):
            super().write_all(tab, rows)
            if tab == ss.TAB_TRADES:
                self.lich_su.append(len(self.tabs[tab]))

    goc = so_lenh_mau()
    sheet = SheetTheoDoi()
    ss.push(goc.db, sheet)
    ss.push(goc.db, sheet)          # ghi đè lần hai

    assert all(n > 0 for n in sheet.lich_su), (
        f"có lúc bảng trades rỗng: {sheet.lich_su}")
    moi = PaperTradingJournal(":memory:")
    ss.pull(moi.db, sheet)
    assert len(moi.all_trades()) == 3
    print(f"PASS  ghi đè không đi qua trạng thái rỗng {sheet.lich_su}")


def test_dong_trong_dem_khong_bi_dem_nham():
    """write_all() của backend thật đệm dòng trống để xoá phần dư. Những
    dòng đó không được tính thành bản ghi, và không được kéo về thành lệnh."""
    goc = so_lenh_mau()
    sheet = ss.InMemorySheet()
    ss.push(goc.db, sheet)

    rows = sheet.read_rows(ss.TAB_TRADES)
    so_cot = len(rows[0])
    sheet.write_all(ss.TAB_TRADES, rows + [[""] * so_cot for _ in range(5)])

    tt = ss.trang_thai(sheet)
    assert tt["trades"] == 3, f"dòng trống bị đếm nhầm: {tt}"

    moi = PaperTradingJournal(":memory:")
    bc = ss.pull(moi.db, sheet)
    assert bc["trades"] == 3 and len(moi.all_trades()) == 3
    print("PASS  5 dòng trống đệm -> vẫn đếm 3 lệnh, kéo về 3 lệnh")


# ── 5. Trạng thái kho ngoài ──────────────────────────────────────────
def test_bao_ro_khi_chua_cau_hinh():
    # Truyền mapping tường minh = "đây là toàn bộ cấu hình". Không được âm
    # thầm rơi về st.secrets hay file trên đĩa — nếu rơi, test mô phỏng
    # "chưa cấu hình" sẽ nói chuyện với Google Sheet THẬT mà không ai biết.
    assert ss.open_from_secrets({}) is None

    # ĐỔI HÀNH VI (19/08/2026, Phase 3C). Bản cũ trả None cho cả hai dòng
    # dưới, tức gộp "cấu hình HỎNG" vào "chưa cấu hình". Chính docstring
    # của open_from_secrets đã nói ngược lại: "cấu hình SAI thì phải nổ,
    # vì 'tưởng đã sao lưu mà thật ra không' là trạng thái tệ nhất."
    # Hậu quả của cách cũ: secrets.toml sai cú pháp / thiếu thư viện toml
    # / key rỗng đều in "chưa cấu hình", quét bình thường, quyết định nằm
    # lại local, rồi lần pull() thành công kế tiếp DELETE sạch.
    for hong in ({"GOOGLE_SHEET_KEY": ""}, {"GOOGLE_SHEET_KEY": "x"}):
        try:
            ss.open_from_secrets(hong)
        except ss.SheetError:
            pass
        else:
            raise AssertionError(f"cấu hình hỏng {hong} bị nuốt thành None")

    tt = ss.trang_thai(None)
    assert tt["bat"] is False and "Chưa cấu hình" in tt["ghi_chu"]
    print("PASS  chưa cấu hình -> tắt sạch, nói rõ lý do")


def test_bao_ro_khi_kho_ngoai_loi():
    class SheetHong:
        def read_rows(self, tab): raise RuntimeError("mất mạng")
        def write_all(self, tab, rows): pass
        def append_rows(self, tab, rows): pass

    tt = ss.trang_thai(SheetHong())
    assert tt["bat"] is False and "LỖI" in tt["ghi_chu"]
    print("PASS  kho ngoài lỗi -> báo LỖI, không im lặng báo OK")


def test_sheet_rong_thi_keo_ve_so_rong():
    moi = PaperTradingJournal(":memory:")
    bao_cao = ss.pull(moi.db, ss.InMemorySheet())
    assert bao_cao == {"trades": 0, "decisions": 0}
    assert moi.all_trades() == []
    print("PASS  sheet rỗng -> sổ rỗng, không vỡ")



# ─────────────────────────────────────────────────────────────────────
# Phase 3B — phát hiện dòng bị bỏ sót thay vì mất im lặng
# ─────────────────────────────────────────────────────────────────────
def test_push_no_khi_co_dong_local_khong_co_tren_sheet():
    """Đúng cơ chế đã làm mất 70 dòng ngày 14/08/2026.

    Hai nơi cùng quét. Sheet đi tới seq 9.422 trong khi sổ máy còn ở
    9.142; máy quét xong sinh seq 9.143–9.212, mà push() chỉ đẩy dòng có
    seq > 9.422 — nên 70 quyết định vừa ghi bị BỎ QUA. Không nổ, không
    log, chỉ in "thêm 0 quyết định mới" rồi exit 0. Actions xanh. Lần
    pull() kế tiếp DELETE sạch 70 dòng đó.

    Bước "đối chiếu sổ local với kho ngoài" trong workflow không bắt được
    vì nó chỉ so bảng `trades`.
    """
    sheet = ss.InMemorySheet()

    # Sheet đã có 5 quyết định (seq 1..5)
    goc = so_lenh_mau()
    ss.push(goc.db, sheet)

    # Sổ máy đang ở trạng thái CŨ hơn sheet (seq 1..3), rồi tự sinh thêm
    # seq 4 với nội dung KHÁC dòng seq 4 đang nằm trên sheet.
    may = PaperTradingJournal(":memory:")
    ss.pull(may.db, sheet)
    may.db.execute("DELETE FROM decisions WHERE seq > 3")
    may.db.execute(
        "INSERT INTO decisions (seq, at, symbol, signal_date, score,"
        " recommendation, acted, skip_reason, components, reasons,"
        " data_quality) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (4, 0.0, "ZZZ", "2026-08-14", 61, "MUA", 0, "thu", "{}", "[]", "OK"))
    may.db.commit()

    try:
        ss.push(may.db, sheet)
    except ss.SheetError as e:
        assert "4" in str(e), f"phải nói rõ seq nào bị bỏ sót: {e}"
    else:
        raise AssertionError(
            "push() BỎ QUA dòng local không có trên sheet mà không báo — "
            "đúng cơ chế đã làm mất 70 dòng ngày 14/08")
    print("PASS  push() nổ khi có dòng local không có trên sheet")


def test_push_binh_thuong_van_chay_khi_khong_thieu_dong():
    """Bộ phát hiện không được báo nhầm: đẩy hai lần liên tiếp phải êm."""
    sheet = ss.InMemorySheet()
    goc = so_lenh_mau()
    ss.push(goc.db, sheet)
    bao_cao = ss.push(goc.db, sheet)
    assert bao_cao["decisions_moi"] == 0, bao_cao
    assert bao_cao.get("decisions_bo_sot", 0) == 0, bao_cao
    print("PASS  đẩy lại lần hai không báo nhầm")


# ─────────────────────────────────────────────────────────────────────
# Phase 3C — "chưa cấu hình" KHÁC "cấu hình hỏng"
# ─────────────────────────────────────────────────────────────────────
def test_chua_cau_hinh_thi_tra_none():
    """Không có credential thì tắt sạch — người dùng local không bắt buộc
    phải có Google Cloud."""
    assert ss.open_from_secrets({}) is None
    print("PASS  chưa cấu hình -> None, chạy tiếp bình thường")


def test_cau_hinh_hong_thi_NO_chu_khong_im_lang():
    """Cấu hình SAI phải nổ, không được lẫn với "chưa cấu hình".

    Bản cũ nuốt mọi lỗi bằng `except Exception: pass` và
    `except (KeyError, TypeError): return None`. Hệ quả: secrets.toml sai
    cú pháp, thiếu thư viện `toml` (không có trong requirements.txt), hoặc
    key rỗng — cả ba đều in "Kho ngoài chưa cấu hình", quét bình thường,
    quyết định nằm lại local, rồi lần pull() thành công kế tiếp DELETE
    sạch. Exit code 0, không dòng nào chứa chữ "LỖI".
    """
    for mo_ta, cau_hinh in [
        ("có key nhưng thiếu gcp_service_account",
         {"GOOGLE_SHEET_KEY": "abc123"}),
        ("có gcp_service_account nhưng thiếu key",
         {"gcp_service_account": {"client_email": "x@y.z"}}),
        ("key rỗng", {"GOOGLE_SHEET_KEY": "", "gcp_service_account": {"a": 1}}),
    ]:
        try:
            ss.open_from_secrets(cau_hinh)
        except ss.SheetError:
            continue
        raise AssertionError(
            f"cấu hình hỏng ({mo_ta}) bị nuốt thành 'chưa cấu hình'")
    print("PASS  cấu hình hỏng nổ, không lẫn với chưa cấu hình")


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
