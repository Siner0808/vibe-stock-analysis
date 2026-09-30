"""Gác của BƯỚC 143 — bảng sàn trong repo và đường dây nối nó vào bước giá.

Người dùng chọn phương án A (29/09/2026): bảng chụp 71 mã có ngày + nguồn,
kèm dụng cụ so lại với `Listing`; KHÔNG tra mạng lúc quét; KHÔNG sửa tay dòng
trên Google Sheets. Bước giá tra theo MÃ, không theo cột `exchange` của lệnh
(cột ấy ghi `HOSE` cho cả 125 dòng cũ).

Các phép kiểm hành vi (giá vào/ra nằm trên lưới 100đ) ở
`tests/test_buoc_gia_theo_san.py`. File này canh BỐN thứ khác:

1. bảng phủ ĐÚNG rổ — một mã rổ vắng bảng sẽ rơi im lặng về HOSE;
2. ba bảng sàn dùng CHUNG một bộ tên (`BUOC_GIA` · `EXCHANGE_LIMITS` ·
   `SAN_HOP_LE`) — `UPCOM` viết `UPCoM` ở một nơi là mã ấy nhận thang HOSE;
3. đường dây thật sự được nối, đọc bằng AST (`in src` mù trước chú thích);
4. đổi `exchange` chỉ đổi cảnh báo `PRICE_JUMP`, không đổi được một quyết định.
"""
import ast
from pathlib import Path

import pandas as pd
import pytest

import data_quality
import market_filter
import paper_trading as pt
import san_giao_dich as sg
import truot_gia
from paper_trading import PaperTradingJournal
from vn100_symbols import CUSTOM_WATCHLIST_SYMBOLS

GOC = Path(__file__).resolve().parent.parent


def _cay(ten: str) -> ast.Module:
    return ast.parse((GOC / ten).read_text(encoding="utf-8"))


def _ham(cay: ast.Module, ten: str) -> ast.FunctionDef:
    r = [n for n in ast.walk(cay)
         if isinstance(n, ast.FunctionDef) and n.name == ten]
    assert len(r) == 1, f"tiền đề gãy: {ten} xuất hiện {len(r)} lần"
    return r[0]


def _la_san_cua(node: ast.AST, doi_so: str | None = None) -> bool:
    """`node` là lời gọi `san_cua(<doi_so>)` (đúng tên, đúng đối số)."""
    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id == "san_cua" and len(node.args) == 1):
        return False
    a = node.args[0]
    return doi_so is None or (isinstance(a, ast.Name) and a.id == doi_so)


# ─────────────────────────────────────────────────────────────────────
# 1 · bảng phủ đúng rổ
# ─────────────────────────────────────────────────────────────────────

def test_bang_phu_DUNG_ro_khong_thieu_khong_thua():
    ro = set(CUSTOM_WATCHLIST_SYMBOLS)
    bang = set(sg.BANG_SAN)
    assert ro == bang, (
        f"bảng sàn lệch rổ. Thiếu trong bảng: {sorted(ro - bang)} · thừa: "
        f"{sorted(bang - ro)}. Chạy `tools/kiem_san_giao_dich.py` rồi cập nhật "
        f"`BANG_SAN` và `NGAY_CHUP`. Mã vắng bảng rơi IM LẶNG về HOSE.")


def test_moi_san_trong_bang_la_san_hop_le():
    xau = {m: s for m, s in sg.BANG_SAN.items() if s not in sg.SAN_HOP_LE}
    assert not xau, f"sàn ngoài {sg.SAN_HOP_LE}: {xau}"


def test_GHIM_bay_ma_khac_HOSE_dung_nhu_da_do_29_09():
    """Ảnh chụp 29/09/2026, hai nguồn khớp. Đổi khi rổ hay sàn đổi — có chủ đích."""
    hnx = sorted(m for m, s in sg.BANG_SAN.items() if s == "HNX")
    upc = sorted(m for m, s in sg.BANG_SAN.items() if s == "UPCOM")
    assert hnx == ["HUT", "MBS", "PVS", "SHS"]
    assert upc == ["ACV", "MSR", "OIL"]
    assert sum(1 for s in sg.BANG_SAN.values() if s == "HOSE") == 64


# ─────────────────────────────────────────────────────────────────────
# 2 · ba bảng sàn, một bộ tên
# ─────────────────────────────────────────────────────────────────────

def test_ba_bang_san_dung_CHUNG_mot_bo_ten():
    a, b, c = set(truot_gia.BUOC_GIA), set(data_quality.EXCHANGE_LIMITS), set(sg.SAN_HOP_LE)
    assert a == b == c, (
        f"BUOC_GIA {sorted(a)} · EXCHANGE_LIMITS {sorted(b)} · SAN_HOP_LE "
        f"{sorted(c)}: tên sàn phải giống hệt — lệch một chữ hoa là một mã "
        f"nhận nhầm thang.")


def test_san_cua_moi_ma_trong_bang_la_khoa_cua_BUOC_GIA():
    for ma in sg.BANG_SAN:
        assert sg.san_cua(ma) in truot_gia.BUOC_GIA, ma


# ─────────────────────────────────────────────────────────────────────
# chuẩn hoá nhãn · tra sàn · nhãn lạ nổ
# ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("tho, ra", [
    ("HSX", "HOSE"), ("HOSE", "HOSE"), (" hnx ", "HNX"), ("UPCOM", "UPCOM"),
    ("UPCoM", "UPCOM"),
    ("DELISTED", None), ("BOND", None), ("XHNF", None), ("NAN", None),
    (None, None), ("", None),
])
def test_chuan_hoa_nhan_nhan_la_cho_None_khong_roi_ve_HOSE(tho, ra):
    assert sg.chuan_hoa_nhan(tho) == ra


def test_san_cua_tra_dung_va_ma_ngoai_bang_ve_HOSE_con_tra_san_noi_ra():
    assert sg.san_cua("pvs") == "HNX" and sg.san_cua("MSR") == "UPCOM"
    assert sg.san_cua("ACB") == "HOSE"
    assert sg.san_cua("ZZZ") == "HOSE", "ngoài bảng: hành vi cũ"
    assert sg.tra_san("ZZZ") is None, "tra_san phải cho người gọi phân biệt được"
    assert sg.tra_san("ACB") == "HOSE"


def test_buoc_gia_nhan_la_NO_khong_ve_HOSE_im_lang():
    for nhan in ("HSX", "DELISTED", "", "XHNF"):
        with pytest.raises(ValueError):
            truot_gia.buoc_gia(20_000, nhan)
    # nhãn hợp lệ, mọi kiểu chữ, vẫn chạy
    assert truot_gia.buoc_gia(20_000, "hnx") == 100
    assert truot_gia.buoc_gia(20_000, "UPCoM") == 100
    assert truot_gia.buoc_gia(20_000, "HOSE") == 50


# ─────────────────────────────────────────────────────────────────────
# 3 · đường dây, đọc bằng AST
# ─────────────────────────────────────────────────────────────────────

def test_khop_that_TRUYEN_san_cua_ma_cho_dat_lenh():
    ham = _ham(_cay("paper_trading.py"), "_khop_that")
    lan = [c for c in ast.walk(ham) if isinstance(c, ast.Call)
           and getattr(c.func, "id", None) == "dat_lenh"]
    assert len(lan) == 1
    kw = {k.arg: k.value for k in lan[0].keywords}
    assert "san" in kw and _la_san_cua(kw["san"], "symbol"), (
        "_khop_that phải gọi dat_lenh(..., san=san_cua(symbol), ...)")


def test_gia_ban_that_nhan_symbol_va_TRUYEN_san_cua_ma_cho_truot_gia():
    ham = _ham(_cay("paper_trading.py"), "_gia_ban_that")
    ten_doi_so = [a.arg for a in ham.args.args]
    assert ten_doi_so == ["self", "gia", "size_pct", "bar", "symbol"], ten_doi_so
    lan = [c for c in ast.walk(ham) if isinstance(c, ast.Call)
           and getattr(c.func, "id", None) == "truot_gia"]
    assert len(lan) == 1 and len(lan[0].args) == 5
    assert _la_san_cua(lan[0].args[4], "symbol"), (
        "_gia_ban_that phải gọi truot_gia(g, BAN, bar, so_cp, san_cua(symbol))")


def test_moi_noi_goi_gia_ban_that_deu_truyen_symbol():
    cay = _cay("paper_trading.py")
    lan = [c for c in ast.walk(cay) if isinstance(c, ast.Call)
           and isinstance(c.func, ast.Attribute) and c.func.attr == "_gia_ban_that"]
    assert len(lan) == 2, f"tiền đề gãy: {len(lan)} nơi gọi (evaluate_open, fill_closing)"
    for c in lan:
        cuoi = c.args[3] if len(c.args) >= 4 else None
        assert isinstance(cuoi, ast.Name) and cuoi.id == "symbol", (
            f"dòng {c.lineno}: _gia_ban_that phải nhận `symbol` làm đối số thứ tư")


def test_run_daily_truyen_san_cua_cho_run_session_va_collect():
    cay = _cay("run_daily.py")
    rs = [c for c in ast.walk(cay) if isinstance(c, ast.Call)
          and getattr(c.func, "id", None) == "run_session"]
    assert rs, "tiền đề gãy: run_daily không còn gọi run_session"
    for c in rs:
        assert _la_san_cua(c.args[5], "sym"), (
            "run_session(..., <sàn>, ...) phải nhận san_cua(sym), không phải hằng")
    co = [c for c in ast.walk(cay) if isinstance(c, ast.Call)
          and getattr(c.func, "attr", None) == "collect"
          and any(k.arg == "exchange" for k in c.keywords)]
    assert co, "tiền đề gãy: run_daily không còn gọi collector.collect(exchange=...)"
    for c in co:
        kw = next(k.value for k in c.keywords if k.arg == "exchange")
        assert _la_san_cua(kw, "sym"), "collect(exchange=) phải là san_cua(sym)"


# ─────────────────────────────────────────────────────────────────────
# 4 · đổi `exchange` chỉ đổi cảnh báo, không đổi quyết định
# ─────────────────────────────────────────────────────────────────────

def _lich_su_co_mot_bien_dong(bien: float) -> pd.DataFrame:
    """40 phiên phẳng 20.000đ, một phiên nhảy `bien` rồi giữ nguyên."""
    ngay = pd.bdate_range(end="2026-09-04", periods=40)
    gia = [20_000.0] * 20 + [20_000.0 * (1 + bien)] * 20
    return pd.DataFrame({"time": ngay.strftime("%Y-%m-%d"), "open": gia,
                         "high": gia, "low": gia, "close": gia,
                         "volume": [1_000_000.0] * 40})


def test_doi_san_chi_doi_canh_bao_PRICE_JUMP_va_do_la_WARN():
    lich_su = _lich_su_co_mot_bien_dong(0.12)     # 12%: vượt 10,5% HOSE, không vượt 15% HNX
    ma = {s: {i.code for i in data_quality.validate_ohlcv(
        lich_su, "X", s, as_of="2026-09-04").issues} for s in ("HOSE", "HNX", "UPCOM")}
    assert "PRICE_JUMP" in ma["HOSE"], "tiền đề gãy: biến động 12% phải bị HOSE báo"
    assert "PRICE_JUMP" not in ma["HNX"] and "PRICE_JUMP" not in ma["UPCOM"]
    assert ma["HOSE"] ^ ma["HNX"] == {"PRICE_JUMP"}, (
        f"đổi sàn đổi thêm thứ khác ngoài PRICE_JUMP: {ma['HOSE'] ^ ma['HNX']}")
    rep = data_quality.validate_ohlcv(lich_su, "X", "HOSE", as_of="2026-09-04")
    sev = {i.code: i.severity for i in rep.issues}
    assert sev["PRICE_JUMP"] == data_quality.Severity.WARN


_ngay = pd.bdate_range("2026-07-01", "2026-09-30")
_VNI = pd.DataFrame({"time": _ngay.strftime("%Y-%m-%d"),
                     "close": [1600.0 + i for i in range(len(_ngay))],
                     "vni_ma50": [1550.0] * len(_ngay)})


@pytest.mark.parametrize("chat_luong", ["OK", "WARN"])
def test_WARN_va_OK_deu_MO_lenh_nen_nhan_chat_luong_khong_doi_quyet_dinh(
        monkeypatch, chat_luong):
    monkeypatch.setattr(market_filter, "is_vni_bullish", lambda *a, **k: True)
    monkeypatch.setattr(market_filter, "get_vni_df", lambda: _VNI)
    monkeypatch.setattr(pt, "CHO_PHEP_MO_LENH_MOI", True)
    assert "OK" in pt.MUC_CHAT_LUONG_DUNG_DUOC and "WARN" in pt.MUC_CHAT_LUONG_DUNG_DUOC
    so = PaperTradingJournal(":memory:")
    kq = {"final_score": 70, "recommendation": "MUA", "data_quality": chat_luong,
          "score_breakdown": {}, "key_reasons": [],
          "analyses": {"risk": {"recommendations": {
              "entry_price": 30_000.0, "stop_loss_price": 28_500.0,
              "take_profit_price": 36_000.0}}}}
    assert so.consider_entry("PVS", "2026-09-03", kq, exchange="HNX",
                             buy_threshold=50.0) is not None, (
        f"data_quality={chat_luong} không được chặn lệnh")

# ─────────────────────────────────────────────────────────────────────
# công cụ so lại với Listing — phần THUẦN, chạy offline
# ─────────────────────────────────────────────────────────────────────

import sys  # noqa: E402

sys.path.insert(0, str(GOC / "tools"))
import kiem_san_giao_dich as ks  # noqa: E402


def _nguon(vci: dict, kbs: dict) -> dict:
    return {"vci": vci, "kbs": kbs}


def test_so_sanh_khop_thi_ba_danh_sach_deu_rong():
    bang = {"PVS": "HNX", "ACB": "HOSE"}
    kq = ks.so_sanh(bang, _nguon({"PVS": "HNX", "ACB": "HSX"},
                                 {"PVS": "HNX", "ACB": "HOSE"}))
    assert kq == {"lech": [], "bat_dong": [], "khong_xac_dinh": []}, (
        "HSX của VCI và HOSE của KBS là MỘT sàn — không được báo lệch")


def test_so_sanh_bat_MA_LECH_khi_ma_chuyen_san():
    kq = ks.so_sanh({"PVS": "HNX"}, _nguon({"PVS": "HSX"}, {"PVS": "HOSE"}))
    assert [m for m, *_ in kq["lech"]] == ["PVS"]
    assert kq["bat_dong"] == [] and kq["khong_xac_dinh"] == []


def test_so_sanh_bat_HAI_NGUON_BAT_DONG_du_bang_khop_mot_ben():
    kq = ks.so_sanh({"MSR": "UPCOM"}, _nguon({"MSR": "UPCOM"}, {"MSR": "HNX"}))
    assert [m for m, _ in kq["bat_dong"]] == ["MSR"]
    assert [m for m, *_ in kq["lech"]] == ["MSR"], "lệch với KBS nên cũng hiện ở lech"


@pytest.mark.parametrize("vci, kbs", [
    ({"AAA": "DELISTED"}, {"AAA": "HOSE"}),     # nhãn lạ ở một nguồn
    ({}, {"AAA": "HOSE"}),                      # mã vắng ở một nguồn
    ({"AAA": "HOSE"}, {"AAA": None}),           # nhãn rỗng
])
def test_so_sanh_ma_khong_xac_dinh_duoc_thi_KHONG_bao_khop(vci, kbs):
    kq = ks.so_sanh({"AAA": "HOSE"}, _nguon(vci, kbs))
    assert [m for m, _ in kq["khong_xac_dinh"]] == ["AAA"]
    assert kq["lech"] == [] and kq["bat_dong"] == []


def test_cong_cu_thoat_2_khi_khong_tai_duoc_nguon(monkeypatch, capsys):
    def hong():
        raise ConnectionError("mất mạng")
    monkeypatch.setattr(ks, "_tai_nguon", hong)
    assert ks.main() == 2
    assert "CHƯA KIỂM ĐƯỢC" in capsys.readouterr().out


def test_cong_cu_thoat_1_khi_bang_lech_va_0_khi_khop(monkeypatch, capsys):
    khop = {n: {m: ("HSX" if s == "HOSE" and n == "vci" else s)
                for m, s in sg.BANG_SAN.items()} for n in ("vci", "kbs")}
    monkeypatch.setattr(ks, "_tai_nguon", lambda: khop)
    assert ks.main() == 0
    lech = {n: dict(d) for n, d in khop.items()}
    lech["kbs"]["PVS"] = "HOSE"
    monkeypatch.setattr(ks, "_tai_nguon", lambda: lech)
    assert ks.main() == 1
    assert "PVS" in capsys.readouterr().out


@pytest.mark.parametrize("bien_doi", [
    ("vci", "PVS", "DELISTED"),      # nhãn lạ: không xác định được sàn
    ("kbs", "OIL", None),            # nhãn rỗng
])
def test_cong_cu_thoat_1_khi_co_ma_KHONG_XAC_DINH_duoc_sang(monkeypatch, capsys, bien_doi):
    nguon_, ma, nhan = bien_doi
    khop = {n: dict(sg.BANG_SAN) for n in ("vci", "kbs")}
    khop[nguon_][ma] = nhan
    monkeypatch.setattr(ks, "_tai_nguon", lambda: khop)
    assert ks.main() == 1, "mã không xác định được sàn KHÔNG được báo khớp"
    assert ma in capsys.readouterr().out
