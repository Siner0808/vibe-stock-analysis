"""Gác của BƯỚC 136 — hai lỗi ở đường khớp lệnh VÀO, đã sửa theo lựa chọn
của người dùng 28/09/2026.

LỖI 1 — biên độ HOSE ±7% áp cho MỌI mã. `_khop_that` gọi `dat_lenh` với biên
mặc định, mà rổ có 4 mã HNX (PVS · HUT · SHS · MBS) và 3 mã UPCoM (OIL · MSR ·
ACV) — đo 28/09/2026, khớp nhau ở hai nguồn VCI và KBS. Người dùng chọn: KHÔNG
kiểm biên độ sàn với giá MỞ CỬA, vì đó là giá sở đã khớp thật; chỉ giữ một chốt
dữ liệu ở biên rộng nhất của mọi sàn (`BIEN_DO_KIEM_GIA_MO`, suy từ
`data_quality.EXCHANGE_LIMITS`).

LỖI 2 — lệnh không khớp được bị XOÁ, nên `trades` CO LẠI. `sheets_store.push`
từ chối đẩy khi local ít lệnh hơn sheet; lượt ấy không mở lệnh mới thì đẩy
hỏng, lượt sau kéo lệnh chờ về và khớp nó TRỄ một phiên, ở một giá khác. Lỗi 2
không cần lỗi 1: thanh khoản không đủ một lô cũng đi đúng đường ấy. Người dùng
chọn: ĐÓNG ở trạng thái `HUY` kèm `LY_DO_TU_CHOI_LENH`, không xoá — `trades`
chỉ thêm, chốt co-lại của push() giữ nguyên.

Các phép kiểm tái hiện ở đây được viết TRƯỚC khi sửa, dưới dấu
`xfail(strict=True)`, và đã chạy ra đỏ đúng lý do: *"khop=0, còn 0 lệnh"* và
*"push() từ chối … KHỚP TRỄ ở 2026-09-07"*. Phép sửa làm chúng XPASS, strict
làm đỏ, và dấu được gỡ — đúng như thiết kế của dấu ấy.
"""
import ast
from pathlib import Path

import pandas as pd
import pytest

import data_quality
import market_filter
import paper_metrics
import paper_trading as pt
import sheets_store as ss
import vong_doi_lenh
from paper_trading import LY_DO_TU_CHOI_LENH, PaperTradingJournal, Status

GOC = Path(__file__).resolve().parent.parent

TIN_HIEU = "2026-09-03"      # phiên có tín hiệu (thứ Năm)
PHIEN_KHOP = "2026-09-04"    # T+1 — phiên khớp ĐÚNG
PHIEN_SAU = "2026-09-07"     # phiên kế tiếp (thứ Hai) — khớp ở đây là TRỄ

THAM_CHIEU = 30_000.0        # đóng cửa phiên tín hiệu, VNĐ

_ngay = pd.bdate_range("2026-07-01", "2026-09-30")
VNI = pd.DataFrame({
    "time": _ngay.strftime("%Y-%m-%d"),
    "close": [1600.0 + i for i in range(len(_ngay))],
    "vni_ma50": [1550.0] * len(_ngay),
})


def _kq() -> dict:
    return {
        "final_score": 70, "recommendation": "MUA", "data_quality": "OK",
        "score_breakdown": {}, "key_reasons": [],
        "analyses": {"risk": {"recommendations": {
            "entry_price": THAM_CHIEU, "stop_loss_price": 28_500.0,
            "take_profit_price": 36_000.0}}},
    }


def _nen(gia_mo: float, tham_chieu: float, khoi_luong: float = 3_000_000.0):
    return {"high": gia_mo * 1.01, "low": gia_mo * 0.99,
            "volume": khoi_luong, "tham_chieu": tham_chieu}


@pytest.fixture
def moi_truong(monkeypatch):
    monkeypatch.setattr(market_filter, "is_vni_bullish", lambda *a, **k: True)
    monkeypatch.setattr(market_filter, "get_vni_df", lambda: VNI)
    monkeypatch.setattr(pt, "CHO_PHEP_MO_LENH_MOI", True)
    monkeypatch.setattr(pt, "MO_PHONG_TRUOT_GIA", True)


def _mo_lenh_cho(so, ma, san="HOSE", ngay=TIN_HIEU) -> int:
    tid = so.consider_entry(ma, ngay, _kq(), exchange=san, buy_threshold=50.0)
    if tid is None:
        pytest.fail(f"TIỀN ĐỀ gãy: consider_entry({ma}) không mở lệnh chờ — "
                    f"phép kiểm dưới đây không đo được gì")
    return tid


def _mot_lenh_HUY(so, ma="PVS") -> int:
    """Một lệnh chờ bị chốt dữ liệu chặn: mở cửa +16%, vượt biên rộng nhất."""
    tid = _mo_lenh_cho(so, ma)
    gia = round(THAM_CHIEU * 1.16, -2)
    so.fill_pending(ma, PHIEN_KHOP, gia, _nen(gia, THAM_CHIEU))
    return tid


# ─────────────────────────────────────────────────────────────────────
# LỖI 1 — mở cửa HỢP LỆ theo biên độ của sàn thì phải KHỚP
# ─────────────────────────────────────────────────────────────────────
#
# Ca −9% đứng đầu vì nó là quần thể ĐO ĐƯỢC: trên sổ ngoài mẫu lượt 4 của
# ĐO 18 (trượt giá TẮT nên không ai kiểm biên độ), 7/582 lệnh khớp ở phiên
# mở cửa lệch > 7% — cả 7 là mã HNX, cả 7 là GAP GIẢM −7,1…−10%. Ca +7,04%
# của mã HOSE là hình dạng làm tròn của cache: 23 phiên như vậy trong rổ.

@pytest.mark.parametrize("ma, san, lech", [
    ("PVS", "HNX", -0.09),      # mở sàn gần −10%: hình dạng đo được ở ĐO 18
    ("PVS", "HNX", +0.08),      # ca người dùng nêu: +8%, trong ±10% của HNX
    ("OIL", "UPCOM", +0.13),    # UPCoM ±15%
    ("PDR", "HOSE", +0.0704),   # trần HOSE làm tròn trong cache (PDR 2025-04-10)
])
def test_mo_cua_da_KHOP_THAT_thi_lenh_phai_KHOP(moi_truong, ma, san, lech):
    so = PaperTradingJournal(":memory:")
    _mo_lenh_cho(so, ma, san)
    gia_mo = THAM_CHIEU * (1 + lech)

    khop = so.fill_pending(ma, PHIEN_KHOP, gia_mo, _nen(gia_mo, THAM_CHIEU))

    lenh = so.all_trades()
    assert khop == 1 and len(lenh) == 1 and lenh[0].status == Status.OPEN, (
        f"{ma} ({san}) mở cửa {gia_mo:,.0f} = {lech:+.2%} so với tham chiếu "
        f"{THAM_CHIEU:,.0f} — một giá sở ĐÃ khớp thật. Sổ ghi khop={khop}, "
        f"trạng thái {[t.status for t in lenh]}: lệnh bị kiểm bằng biên độ "
        f"±{vong_doi_lenh.BIEN_DO:.0%} của HOSE.")
    assert str(lenh[0].entry_date)[:10] == PHIEN_KHOP


def test_chot_du_lieu_VUOT_bien_rong_nhat_thi_KHONG_mo_vi_the(moi_truong):
    """+16%: không sàn nào khớp được — lỗi dữ liệu hoặc sự kiện doanh nghiệp
    chưa điều chỉnh giá (MBB · SSI 10/08/2026). Chốt vẫn phải chặn."""
    so = PaperTradingJournal(":memory:")
    _mot_lenh_HUY(so)
    lenh = so.all_trades()
    assert [t.status for t in lenh] == [Status.HUY]
    assert lenh[0].entry_price is None and lenh[0].exit_price is None


def test_bien_kiem_gia_mo_SUY_RA_tu_bang_bien_do_cua_san():
    """AST, không so giá trị: một bản sao gõ tay 0.15 cho đúng số hôm nay và
    sai vào ngày bảng biên độ đổi. Và `_khop_that` phải TRUYỀN nó cho
    `dat_lenh` — thiếu `bien_do=` là quay về ±7% mặc định, tức lỗi 1."""
    cay = ast.parse((GOC / "paper_trading.py").read_text(encoding="utf-8"))
    gan = [n.value for n in cay.body if isinstance(n, ast.Assign)
           and any(getattr(t, "id", "") == "BIEN_DO_KIEM_GIA_MO" for t in n.targets)]
    assert len(gan) == 1, "BIEN_DO_KIEM_GIA_MO phải được gán đúng một lần ở mức module"
    v = gan[0]
    assert (isinstance(v, ast.Call) and getattr(v.func, "id", "") == "max"
            and isinstance(v.args[0], ast.Call)
            and getattr(v.args[0].func, "attr", "") == "values"
            and getattr(v.args[0].func.value, "id", "") == "EXCHANGE_LIMITS"), (
        "BIEN_DO_KIEM_GIA_MO phải là max(EXCHANGE_LIMITS.values()), không gõ tay")
    assert pt.BIEN_DO_KIEM_GIA_MO == max(data_quality.EXCHANGE_LIMITS.values())

    ham = next(n for n in ast.walk(cay)
               if isinstance(n, ast.FunctionDef) and n.name == "_khop_that")
    goi = [n for n in ast.walk(ham) if isinstance(n, ast.Call)
           and getattr(n.func, "id", "") == "dat_lenh"]
    assert len(goi) == 1
    kw = {k.arg: k.value for k in goi[0].keywords}
    assert getattr(kw.get("bien_do"), "id", "") == "BIEN_DO_KIEM_GIA_MO", (
        "_khop_that phải gọi dat_lenh(..., bien_do=BIEN_DO_KIEM_GIA_MO)")


# ─────────────────────────────────────────────────────────────────────
# LỖI 2 — sổ co lại -> push() từ chối -> lượt sau khớp TRỄ một phiên
# ─────────────────────────────────────────────────────────────────────
#
# Mỗi lượt quét là một runner SẠCH: kéo sổ từ Sheets, xử lý, đẩy lên
# (`run_daily`). Ba runner dưới đây là ba lượt quét. `run_daily` bắt lỗi của
# push(), in "🚨 ĐẨY KHO NGOÀI THẤT BẠI" rồi đi tiếp — nên ở đây cũng bắt.
#
# Tiền đề: lượt ở phiên khớp KHÔNG mở lệnh mới nào. Có một lệnh mới thì số
# dòng bằng nhau, push() đi qua và chuỗi không xảy ra — nên lỗi này xuất hiện
# thất thường, đúng loại khó thấy.

@pytest.mark.parametrize("tac_nhan", ["bien_do_HNX", "thanh_khoan_duoi_mot_lo"])
def test_lenh_bi_TU_CHOI_khong_duoc_lam_so_CO_LAI_roi_KHOP_TRE(moi_truong, tac_nhan):
    sheet = ss.InMemorySheet()

    # Lượt 1 — phiên tín hiệu: mở lệnh chờ, đẩy lên.
    r1 = PaperTradingJournal(":memory:", cho_phep_so_that=True)
    _mo_lenh_cho(r1, "PVS", "HNX")
    ss.push(r1.db, sheet)

    # Lượt 2 — phiên khớp T+1.
    r2 = PaperTradingJournal(":memory:", cho_phep_so_that=True)
    ss.pull(r2.db, sheet)
    if tac_nhan == "bien_do_HNX":
        gia_1 = 32_400.0                                  # +8%, hợp lệ ở HNX
        nen_1 = _nen(gia_1, THAM_CHIEU)
    else:
        gia_1 = 30_300.0                                  # +1%, trong mọi biên độ
        nen_1 = _nen(gia_1, THAM_CHIEU, khoi_luong=500.0)  # 10% × 500 < một lô
    r2.fill_pending("PVS", PHIEN_KHOP, gia_1, nen_1)
    try:
        ss.push(r2.db, sheet)
        tu_choi = None
    except ss.SheetError as e:
        tu_choi = str(e).splitlines()[0]

    # Lượt 3 — phiên sau: runner sạch kéo sổ về, khớp như thường lệ.
    r3 = PaperTradingJournal(":memory:", cho_phep_so_that=True)
    ss.pull(r3.db, sheet)
    gia_2 = 31_000.0
    r3.fill_pending("PVS", PHIEN_SAU, gia_2, _nen(gia_2, gia_1))

    tre = [t for t in r3.all_trades()
           if str(t.signal_date)[:10] == TIN_HIEU
           and str(t.entry_date or "")[:10] == PHIEN_SAU]
    loi = []
    if tu_choi:
        loi.append(f"lượt {PHIEN_KHOP}: push() từ chối — {tu_choi}")
    if tre:
        loi.append(f"lượt {PHIEN_SAU}: lệnh tín hiệu {TIN_HIEU} sống lại từ "
                   f"Sheets và KHỚP TRỄ ở {PHIEN_SAU}, giá {tre[0].entry_price:,.0f} "
                   f"— vi phạm T+1 (bất biến 1)")
    assert not loi, "\n".join(loi)


def test_lenh_HUY_ghi_ngay_va_ly_do_va_KHONG_co_gia(moi_truong):
    so = PaperTradingJournal(":memory:")
    _mot_lenh_HUY(so)
    t = so.all_trades()[0]
    assert t.status == Status.HUY
    assert t.exit_reason == LY_DO_TU_CHOI_LENH
    assert str(t.exit_date)[:10] == PHIEN_KHOP
    assert t.entry_date is None and t.entry_price is None


def test_lenh_HUY_KHONG_chan_mo_lai_cung_ma_va_KHONG_chiem_von(moi_truong):
    """HUY không phải vị thế: nó không được giữ chỗ của mã, không được ăn vào
    trần vốn. Nếu có, một lệnh chưa bao giờ tồn tại sẽ đổi tập lệnh sau nó."""
    so = PaperTradingJournal(":memory:")
    _mot_lenh_HUY(so, "PVS")
    assert so.open_position("PVS") is None
    tid = so.consider_entry("PVS", PHIEN_KHOP, _kq(), exchange="HNX",
                            buy_threshold=50.0)
    assert tid is not None, "lệnh HUY đang chặn mã PVS mở lại"

    # Trần vốn: dựng đủ lệnh HUY để TỔNG cỡ của chúng vượt trần. Nếu trần
    # đếm HUY thì lệnh mới cuối cùng bị từ chối. Đi qua CHÍNH câu truy vấn
    # của `consider_entry`, không tự cộng lại — tự cộng là kiểm công thức
    # của test (CLAUDE.md, mục "Test KIỂM LẠI CHÍNH NÓ").
    so2 = PaperTradingJournal(":memory:")
    ma_huy = ["HUT", "SHS", "MBS", "OIL", "MSR", "ACV", "BSR", "VTP",
              "HHP", "PVD", "PVT", "GEX", "VSC", "HSG", "NKG", "HPG"]
    tong = 0.0
    for ma in ma_huy:
        _mot_lenh_HUY(so2, ma)
        tong += so2.db.execute("SELECT size_pct FROM trades WHERE symbol=?",
                               (ma,)).fetchone()[0]
        if tong > pt.TRAN_VON_CAM_KET_PCT:
            break
    assert tong > pt.TRAN_VON_CAM_KET_PCT, "TIỀN ĐỀ: chưa đủ lệnh HUY để chạm trần"
    moi = so2.consider_entry("FPT", PHIEN_KHOP, _kq(), buy_threshold=50.0)
    assert moi is not None, (f"{tong:.1f}% lệnh HUY đang ăn vào trần vốn "
                             f"{pt.TRAN_VON_CAM_KET_PCT}%")


def test_lenh_HUY_KHONG_vao_phep_do(moi_truong):
    """Một lệnh không khớp không phải một giao dịch lãi/lỗ 0%. Cạnh nó là một
    lệnh ĐÃ ĐÓNG thật, để phép đếm có thứ để đếm — sổ chỉ có HUY thì
    `compute` trả None và phép kiểm không phân biệt được gì."""
    so = PaperTradingJournal(":memory:")
    _mo_lenh_cho(so, "FPT")
    so.fill_pending("FPT", PHIEN_KHOP, THAM_CHIEU, _nen(THAM_CHIEU, THAM_CHIEU))
    so.evaluate_open("FPT", PHIEN_SAU, {"open": 29_000.0, "high": 29_100.0,
                                        "low": 28_000.0, "close": 28_200.0,
                                        "volume": 3_000_000.0})
    _mot_lenh_HUY(so, "PVS")
    lenh = so.all_trades()
    assert sorted(t.status for t in lenh) == [Status.CLOSED, Status.HUY], (
        "TIỀN ĐỀ: cần đúng một lệnh ĐÃ ĐÓNG và một lệnh HUY")
    assert paper_metrics.compute(lenh).n_trades == 1
