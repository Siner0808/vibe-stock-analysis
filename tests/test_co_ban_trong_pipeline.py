"""Agent Cơ Bản nối vào Master — hai tính chất trái ngược phải cùng đúng.

  · **Nối THẬT**: `analyses["fundamental"]` phải có mặt, và khi bật trọng
    số lên thì điểm phải dịch. Không có nhóm này thì đoạn nối có thể là mã
    chết mà vẫn xanh.

  · **Chưa tham gia chấm**: với trọng số 0 mặc định, điểm cuối phải KHÔNG
    ĐỔI dù báo cáo tài chính đẹp hay xấu. Không có nhóm này thì 113 lệnh
    trong sổ và mọi kết quả walk-forward đã đo lặng lẽ mất hiệu lực.

Và một tính chất thứ ba, quan trọng hơn cả hai: **backtest không được
chạm vào dữ liệu cơ bản.** Bảng chỉ số theo năm là trạng thái HIỆN TẠI,
không kèm ngày công bố. Chấm phiên năm 2022 bằng số liệu 2025 là nhìn
trộm tương lai ở dạng thô nhất.
"""
import numpy as np
import pandas as pd
import pytest

import fundamental_agent as fa
import master_agent as ma
from data_collectors import MarketDataPacket
from master_agent import MasterConsensusAgent


def _goi(n=140):
    close = 50_000 * np.power(1.002, np.arange(n))
    return MarketDataPacket(
        symbol="TST", exchange="HOSE",
        ohlcv_df=pd.DataFrame({
            "time": pd.bdate_range("2026-01-01", periods=n).strftime("%Y-%m-%d"),
            "open": close * 0.998, "high": close * 1.006,
            "low": close * 0.994, "close": close,
            "volume": np.full(n, 2_000_000)}))


def _bang(nam=2025, **dong):
    return pd.DataFrame({"item_id": list(dong),
                         str(nam): [dong[k] for k in dong]})


def _dep():
    return _bang(roe=40.0, roa=20.0, pe_ratio=5.0, pb_ratio=0.8,
                 net_margin=40.0, debt_to_equity=5.0, interest_coverage=80.0,
                 **{"profit_after_tax_for_shareholders_of_the_parent"
                    "_company": 90.0})


def _xau():
    return _bang(roe=-30.0, roa=-15.0, pe_ratio=-4.0, pb_ratio=8.0,
                 net_margin=-25.0, debt_to_equity=700.0,
                 interest_coverage=0.4,
                 **{"profit_after_tax_for_shareholders_of_the_parent"
                    "_company": -70.0})


def _master(bang, doc_co_ban=True):
    m = MasterConsensusAgent(doc_co_ban=doc_co_ban)
    m.fundamental_agent = fa.FundamentalAgent(tai_bang=lambda _: bang)
    return m


# ─────────────────────────────────────────────────────────────────────
# 1. Đã nối thật
# ─────────────────────────────────────────────────────────────────────

def test_ket_qua_co_khoa_fundamental():
    kq = _master(_dep()).run(_goi())
    assert "fundamental" in kq["analyses"]
    assert kq["analyses"]["fundamental"]["available"] is True
    assert kq["score_breakdown"]["fundamental_score"] is not None
    print(f"PASS  có analyses['fundamental'], điểm cơ bản "
          f"{kq['score_breakdown']['fundamental_score']}")


def test_key_reasons_neu_ket_qua_co_ban():
    kq = _master(_dep()).run(_goi())
    assert any("Cơ bản" in r for r in kq["key_reasons"]), kq["key_reasons"]
    print("PASS  luận điểm tổng hợp có nhắc tầng cơ bản")


def test_bat_trong_so_len_thi_diem_PHAI_dich():
    """Chống mã chết: nếu số hạng cơ bản không thật sự nằm trong công thức
    thì bật trọng số lên cũng chẳng đổi gì, và test 'trọng số 0 không đổi
    điểm' bên dưới sẽ xanh vì lý do sai."""
    goc = ma.TRONG_SO_CO_BAN
    try:
        ma.TRONG_SO_CO_BAN = 0.5
        dep = _master(_dep()).run(_goi())["pre_debate_score"]
        xau = _master(_xau()).run(_goi())["pre_debate_score"]
    finally:
        ma.TRONG_SO_CO_BAN = goc
    assert dep > xau, f"bật trọng số mà điểm không dịch: {dep} vs {xau}"
    print(f"PASS  trọng số 0,5 -> điểm dịch {xau} … {dep}")


# ─────────────────────────────────────────────────────────────────────
# 2. Nhưng chưa tham gia chấm
# ─────────────────────────────────────────────────────────────────────

def test_trong_so_mac_dinh_bang_0():
    assert ma.TRONG_SO_CO_BAN == 0.0, (
        "Đổi hằng số này là đổi MỌI con số lịch sử của sổ lệnh. Nó chỉ được "
        "khác 0 sau khi có phép đo, không phải sau khi có cảm giác.")
    print("PASS  TRONG_SO_CO_BAN = 0")


def test_bao_cao_dep_hay_xau_deu_khong_doi_diem():
    """Test then chốt: 113 lệnh trong sổ được chấm khi chưa có agent này."""
    dep = _master(_dep()).run(_goi())
    xau = _master(_xau()).run(_goi())
    khong = _master(None).run(_goi())
    assert dep["final_score"] == xau["final_score"] == khong["final_score"]
    assert dep["pre_debate_score"] == xau["pre_debate_score"]
    assert dep["analyses"]["fundamental"]["diem"] != \
        xau["analyses"]["fundamental"]["diem"], "hai kịch bản phải khác nhau"
    print(f"PASS  điểm cơ bản {dep['analyses']['fundamental']['diem']} vs "
          f"{xau['analyses']['fundamental']['diem']}, điểm cuối cùng bằng nhau "
          f"({dep['final_score']})")


def test_dong_gop_ghi_ra_bang_0_de_doc_duoc():
    """Con số 0 phải HIỆN RA. Một ảnh hưởng ẩn là một ảnh hưởng không ai kiểm."""
    kq = _master(_dep()).run(_goi())
    assert kq["score_breakdown"]["fundamental_adjustment"] == 0.0
    print("PASS  fundamental_adjustment = 0.0, ghi rõ trong score_breakdown")


# ─────────────────────────────────────────────────────────────────────
# 3. Backtest và sổ lệnh giấy KHÔNG được chạm dữ liệu cơ bản
# ─────────────────────────────────────────────────────────────────────

def test_mac_dinh_TAT_va_khong_goi_nguon():
    """`MasterConsensusAgent()` rỗng là thứ backtest và paper_runner dùng."""
    m = MasterConsensusAgent()
    assert m.doc_co_ban is False

    goi_may_lan = []
    m.fundamental_agent = fa.FundamentalAgent(
        tai_bang=lambda ma_ck: goi_may_lan.append(ma_ck))
    kq = m.run(_goi())
    assert goi_may_lan == [], (
        f"đường backtest đã gọi nguồn dữ liệu cơ bản {len(goi_may_lan)} lần — "
        f"số liệu năm hiện tại đang chảy vào các phiên quá khứ")
    assert kq["analyses"]["fundamental"]["available"] is False
    assert kq["analyses"]["fundamental"]["diem"] is None
    print("PASS  mặc định tắt, không gọi nguồn lần nào")


def test_run_full_analysis_bat_doc_co_ban():
    """Đường phân tích một mã tại hiện tại thì phải BẬT.

    Đọc từ mã nguồn: gọi thật sẽ kéo theo mạng và cả pipeline tin tức.
    """
    import ast
    import inspect

    cay = ast.parse(inspect.getsource(ma.run_full_analysis))
    bat = [n for n in ast.walk(cay)
           if isinstance(n, ast.keyword) and n.arg == "doc_co_ban"]
    assert bat and getattr(bat[0].value, "value", None) is True, (
        "run_full_analysis() không truyền doc_co_ban=True")
    print("PASS  run_full_analysis dựng master với doc_co_ban=True")


def test_loi_o_tang_co_ban_khong_lam_hong_luot_cham():
    """Mất mạng ở tầng cơ bản không được kéo đổ cả phân tích kỹ thuật."""
    def _no(_):
        raise RuntimeError("nguồn sập")

    m = MasterConsensusAgent(doc_co_ban=True)
    m.fundamental_agent = fa.FundamentalAgent(tai_bang=_no)
    kq = m.run(_goi())
    assert kq["final_score"] > 0
    assert kq["analyses"]["fundamental"]["available"] is False
    assert any("lỗi" in s.lower() for s in
               kq["analyses"]["fundamental"]["signals"])
    print("PASS  nguồn sập -> vẫn chấm xong, và nói rõ tầng nào hỏng")


def test_du_lieu_hong_thi_score_breakdown_van_du_khoa():
    """Nhánh 'không phán quyết' cũng phải có đủ khoá, nếu không người đọc
    `score_breakdown` sẽ vấp KeyError đúng lúc dữ liệu đang hỏng."""
    goi = MarketDataPacket(symbol="TST", exchange="HOSE",
                           data_quality="FAILED")
    bd = MasterConsensusAgent().run(goi)["score_breakdown"]
    assert "fundamental_score" in bd and "fundamental_adjustment" in bd
    print("PASS  nhánh dữ liệu hỏng vẫn đủ khoá cơ bản")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    for ten, ham in sorted(globals().items()):
        if ten.startswith("test_"):
            ham()
