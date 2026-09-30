"""Mã ĐANG GIỮ cũng phải có dòng quyết định — BƯỚC 146 (P3b chấm bóng).

`run_session` chỉ gọi `consider_entry` khi mã KHÔNG có vị thế, và chỉ
`consider_entry` ghi `decisions`. Nên mỗi phiên, bảng quyết định thiếu đúng
những mã điểm cao nhất — mã đang giữ — và phép chấm bóng (`cham_bong.py`) đo
IC trên một lát cắt đã bị cổng mua lọc.

Ba điều phải giữ cùng lúc:
  1. sổ THẬT: mã đang giữ có đúng MỘT dòng, `acted = 0`, lý do dùng chung;
  2. sổ KHÔNG cờ (walkforward, backtest): không dòng nào — không phép đo nào đổi;
  3. vị thế đóng NGAY trong phiên: `consider_entry` đã ghi, không ghi đôi.
"""
import ast
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import pandas as pd
import pytest

import cham_bong
import paper_runner as pr
import paper_trading as pt

DIEM = 71
PHIEN = "2026-08-20"


def _chuoi(n: int = 80) -> pd.DataFrame:
    ngay = pd.bdate_range(end=PHIEN, periods=n).strftime("%Y-%m-%d")
    return pd.DataFrame({
        "time": ngay, "open": [10.0] * n, "high": [10.4] * n,
        "low": [9.7] * n, "close": [10.1] * n, "volume": [1_000_000] * n})


def _kq() -> dict:
    return {"final_score": DIEM, "recommendation": "GIỮ", "data_quality": "OK",
            "score_breakdown": {k: 60.0 for k in cham_bong.THANH_PHAN},
            "key_reasons": [], "analyses": {"risk": {"recommendations": {}}}}


@pytest.fixture
def so(monkeypatch, tmp_path):
    monkeypatch.setattr(pr, "_analyze", lambda *a, **k: _kq())
    import market_filter
    monkeypatch.setattr(market_filter, "is_vni_bullish", lambda _d: True)
    mo = []

    def _mo(that: bool, sl: float = 9_000.0):
        j = pt.PaperTradingJournal(str(tmp_path / f"s{len(mo)}.db"),
                                   cho_phep_so_that=that)
        j.db.execute(
            "INSERT INTO trades (symbol, exchange, signal_date, entry_date,"
            " entry_price, stop_loss, take_profit, size_pct, entry_score,"
            " entry_recommendation, components, reasons, status, created_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("AAA", "HOSE", "2026-08-18", "2026-08-19", 10_000.0, sl,
             12_000.0, 10.0, 70, "MUA", "{}", "[]", pt.Status.OPEN, 0.0))
        j.db.commit()
        mo.append(j)
        return j

    yield _mo
    for j in mo:
        j.db.close()


def _chay(j, low: float = 9.7) -> dict:
    bar = {"open": 10.0, "high": 10.4, "low": low, "close": 10.1}
    return pr.run_session(j, "AAA", _chuoi(), bar, PHIEN)


def test_SO_THAT_ma_dang_giu_co_DUNG_MOT_dong_quyet_dinh(so):
    j = so(True)
    stats = _chay(j)
    assert j.open_position("AAA") is not None, "dung cu hong: vi the da dong"
    dong = j.decisions()
    assert len(dong) == 1, f"can dung 1 dong, co {len(dong)}"
    d = dong[0]
    assert (d["symbol"], d["signal_date"], d["score"], d["acted"]) == (
        "AAA", PHIEN, DIEM, 0), d
    assert d["skip_reason"] == pt.LY_DO_DANG_GIU
    assert stats["final_score"] == DIEM
    # Dòng ấy phải ĐỌC ĐƯỢC bởi bảng chấm bóng, không bị bỏ vì thiếu thành phần.
    b = cham_bong.doc_quyet_dinh(dong, "2026-08-01")
    assert list(b["symbol"]) == ["AAA"] and b.attrs["bo"] == 0
    print("PASS  so that: ma dang giu -> 1 dong acted=0, cham bong doc duoc")


def test_SO_KHONG_CO_walkforward_khong_ghi_dong_nao(so):
    j = so(False)
    _chay(j)
    assert j.open_position("AAA") is not None
    assert j.decisions() == [], (
        "so khong co (walkforward/backtest) da ghi them dong -> phep do doi")
    print("PASS  so khong co: 0 dong, walkforward khong doi")


def test_vi_the_DONG_ngay_trong_phien_KHONG_ghi_doi(so):
    j = so(True)
    _chay(j, low=8.5)                    # thủng SL 9.000 -> đóng trong phiên
    assert j.open_position("AAA") is None, "dung cu hong: vi the chua dong"
    dong = j.decisions()
    assert len(dong) == 1, f"ghi doi: {[d['skip_reason'] for d in dong]}"
    assert dong[0]["skip_reason"] != pt.LY_DO_DANG_GIU, (
        "vi the da dong ma dong quyet dinh van noi 'dang giu'")
    print(f"PASS  dong trong phien: 1 dong tu consider_entry "
          f"({dong[0]['skip_reason'][:30]!r})")


def test_LY_DO_DANG_GIU_la_MOT_hang_khong_go_lai_o_noi_goi():
    """Suy ra, đừng gõ: chuỗi lý do xuất hiện ĐÚNG MỘT LẦN, ở chính hằng ấy."""
    thay = []
    for ten in ("paper_trading.py", "paper_runner.py"):
        cay = ast.parse((GOC / ten).read_text(encoding="utf-8"))
        cha = {id(c): n for n in ast.walk(cay) for c in ast.iter_child_nodes(n)}
        for n in ast.walk(cay):
            if (isinstance(n, ast.Constant) and isinstance(n.value, str)
                    and pt.LY_DO_DANG_GIU in n.value):
                p = cha.get(id(n))
                gan = (isinstance(p, ast.Assign)
                       and [t.id for t in p.targets] == ["LY_DO_DANG_GIU"])
                thay.append((ten, n.lineno, gan))
    assert len(thay) == 1 and thay[0][0] == "paper_trading.py" and thay[0][2], thay
    print(f"PASS  chuoi ly do chi o hang LY_DO_DANG_GIU: {thay}")
