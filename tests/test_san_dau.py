"""Gác cho `san_dau.py` và `tools/san_dau.py` (BƯỚC 240, Lát 2 của C1; `docs/thiet-ke-c1-san-dau.md`).

Gác ĐẦU TIÊN của cách A là PHÉP THỬ TƯƠNG ĐƯƠNG: phát lại cấu hình của đường thật phải ra ĐÚNG các lệnh
mà đường thật ra. Hai tầng (đặc tả mục 6):

  • TẦNG A (file này, chạy ở CI, offline, dữ liệu tổng hợp): chạy kịch bản mười mã × 95 phiên của
    `tools/sinh_bang_vang_phien.py` bằng `paper_runner.run_session` (đường thật; sổ ghi nhật ký như sổ
    thật nên phiên đang giữ lệnh cũng có dòng quyết định), lấy bảng `decisions` nó ghi ra, rồi phát lại
    bằng `san_dau.phat_lai`. Điểm trong kịch bản viết tay; phần rủi ro đi qua `RiskManagementAgent` THẬT
    trên gói dữ liệu THẬT của `paper_runner._analyze` — nên việc dựng lại phần rủi ro bằng `dung_lai_rui_ro`
    được chứng minh, không được giả định. Bảng `trades` hai bên bằng nhau TỪNG Ô.
  • TẦNG B: `tools/san_dau.py tuong-duong`, chạy tay trên sổ THẬT (STATE BƯỚC 240); ở đây chỉ gác phần
    tính của nó bằng kịch bản tổng hợp.

Cộng gác AST G1–G5 của đặc tả mục 11 cho phần có mặt.
"""
from __future__ import annotations

import ast
import contextlib
import dataclasses
import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
# `tools` ở CUỐI đường tìm: `tools/cham_xac_nhan.py` cùng tên với module gốc, đứng trước là làm test
# nạp sau (test_keo_bang_gia) nhập nhầm dụng cụ thay vì module (bài học BƯỚC 239).
sys.path.append(str(GOC / "tools"))

import duyet_repo  # noqa: E402
import market_filter  # noqa: E402
import paper_runner as pr  # noqa: E402
import paper_trading as pt  # noqa: E402
import san_dau as sd  # noqa: E402
import sinh_bang_vang_phien as S  # noqa: E402

# Nạp một BẢN SAO RIÊNG của market_filter (khuôn `tests/test_market_filter.py`): `tests/test_sheets_store.py`
# ghim `market_filter.is_vni_bullish` thành `lambda: True` ở MỨC MODULE, lời ghim sống suốt tiến trình, nên chạy
# cả bộ thì "cổng thật" ở đây là cái lambda ấy. Bản sao này luôn là mã thật.
_spec_mf = importlib.util.spec_from_file_location("market_filter_ban_sao_san_dau", GOC / "market_filter.py")
MF = importlib.util.module_from_spec(_spec_mf)
_spec_mf.loader.exec_module(MF)

DUONG_MODULE = GOC / "san_dau.py"
DUONG_CLI = GOC / "tools" / "san_dau.py"


def _nap_cli():
    """Nạp `tools/san_dau.py` theo đường dẫn, dưới tên riêng (tên `san_dau` là của module gốc)."""
    spec = importlib.util.spec_from_file_location("san_dau_cli", DUONG_CLI)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── dựng kịch bản ──────────────────────────────────────────────────────────────────────────────
class _TatHoc:
    enabled = False


def _cfg(**kw) -> pt.CauHinhVao:
    """Cấu hình dựng TƯỜNG MINH (không đọc biến module — test khác có thể đã đặt cờ)."""
    co = dict(cho_phep_mo_lenh_moi=True, buy_threshold=62, tran_von_cam_ket_pct=100.0,
              cong_vni_bat=True, do_rong_nguong=0, nghi_sau_lo_ngay=0, loc_imom_phan_vi=0,
              chot_sut_giam_nguong=0, chot_sut_giam_phien=20, exit_signal_threshold=45,
              max_hold_sessions=60, chot_loi_cung=False)
    co.update(kw)
    return pt.CauHinhVao(**co)


@pytest.fixture(scope="module")
def gia():
    return S.dung_gia()


@pytest.fixture(scope="module", autouse=True)
def _sach_cache_phan_tich():
    """`_ANALYZE_CACHE` khoá theo (mã, độ dài, ngày) chứ không theo kịch bản: dọn trước và sau module."""
    pr._xoa_cache_phan_tich()
    yield
    pr._xoa_cache_phan_tich()


def _khung_vni(gia) -> pd.DataFrame:
    """VN-INDEX tổng hợp đủ dài để có MA50 ở phiên đầu, và cắt MA50 vài lần trong kịch bản."""
    import math
    ngay = [d.strftime("%Y-%m-%d") for d in pd.bdate_range(end=S.PHIEN[-1], periods=S.SO_PHIEN + 70)]
    dong = [1000.0 + 45.0 * math.sin(0.13 * i) + 0.6 * i for i in range(len(ngay))]
    return pd.DataFrame({"time": ngay, "close": [round(x, 2) for x in dong]})


class _NguonKichBan:
    """Nguồn VN-INDEX của kịch bản: ngày trong `_VNI_XAU` thì dưới MA50 — CÙNG hàm đã thay vào đường thật."""

    def vni_tren_ma50(self, ngay):
        return str(ngay)[:10] not in S._VNI_XAU

    def do_rong(self, ngay):
        raise AssertionError("cấu hình mặc định không được hỏi độ rộng")


@contextlib.contextmanager
def _duong_that(gia, vni_df=None):
    """Đường THẬT với chấm điểm thay bằng kịch bản: điểm viết tay, phần rủi ro do `RiskManagementAgent`
    THẬT tính trên gói dữ liệu mà `paper_runner._analyze` dựng (cùng chỉ báo cục bộ). VN-INDEX: hàm
    kịch bản, hay — khi `vni_df` có — chính `market_filter.is_vni_bullish` đọc khung ấy."""
    import analysis_agents
    import master_agent
    import post_mortem_learning

    chi_so = {d: i for i, d in enumerate(S.PHIEN)}

    class _MayChamGia:
        def run(self, goi):
            ma = goi.symbol
            i = chi_so[str(goi.ohlcv_df["time"].iloc[-1])[:10]]
            kq = S.ket_qua_cham(ma, i, gia)
            kq["analyses"] = {"risk": analysis_agents.RiskManagementAgent().analyze(goi)}
            return kq

    khung = None
    if vni_df is not None:
        khung = vni_df.copy()
        khung["time"] = khung["time"].astype(str)
        khung["vni_ma50"] = khung["close"].rolling(MF.MA_WINDOW).mean()
    with contextlib.ExitStack() as st:
        for doi_tuong, ten, moi in [
                (master_agent, "MasterConsensusAgent", _MayChamGia),
                (post_mortem_learning, "get_learning_engine", lambda *a, **k: _TatHoc()),
                (market_filter, "get_vni_df", (lambda: khung)),
                (MF, "get_vni_df", (lambda: khung)),
                (market_filter, "is_vni_bullish",
                 MF.is_vni_bullish if khung is not None
                 else (lambda d, *a, **k: str(d)[:10] not in S._VNI_XAU))]:
            cu = getattr(doi_tuong, ten)
            setattr(doi_tuong, ten, moi)
            st.callback(setattr, doi_tuong, ten, cu)
        yield


def _chay_that(cau_hinh, gia, *, chi_khop_xen_ke=False, vni_df=None):
    """Chạy kịch bản bằng `run_session`; trả (sổ, các dòng `decisions` của sổ)."""
    so = pt.PaperTradingJournal(":memory:", cho_phep_so_that=True)
    with _duong_that(gia, vni_df):
        for i in range(S.SO_PHIEN):
            chi_khop = chi_khop_xen_ke and i % 2 == 1 and i > 0
            for ma in S.MA:
                nen = {k: float(gia[ma][k].iloc[i]) for k in ("open", "high", "low", "close", "volume")}
                pr.run_session(so, ma, gia[ma].iloc[: i + 1], nen, S.PHIEN[i], "HOSE",
                               chi_khop=chi_khop, cau_hinh=cau_hinh)
    return so, so.decisions()


def _lenh(so) -> list[dict]:
    cot = ", ".join(sd.COT_TUONG_DUONG)
    return [dict(r) for r in so.db.execute(f"SELECT {cot} FROM trades ORDER BY id").fetchall()]


@contextlib.contextmanager
def _cam_cache_toan_cuc():
    """Trong lúc phát lại, cổng VN-INDEX và nguồn khung của `market_filter` nổ nếu bị hỏi: bộ phát lại
    chỉ được dùng nguồn TIÊM VÀO, không bao giờ cache toàn cục (cache cũ = ô C1; mạng = không tất định)."""
    def no(*a, **k):
        raise AssertionError("phát lại đã hỏi cache toàn cục của market_filter")
    cu = (market_filter.is_vni_bullish, market_filter.get_vni_df)
    market_filter.is_vni_bullish, market_filter.get_vni_df = no, no
    try:
        yield
    finally:
        market_filter.is_vni_bullish, market_filter.get_vni_df = cu


def _tuong_duong(cau_hinh, gia, nguon, *, chi_khop_xen_ke=False, vni_df=None):
    so, qd = _chay_that(cau_hinh, gia, chi_khop_xen_ke=chi_khop_xen_ke, vni_df=vni_df)
    with _cam_cache_toan_cuc():
        tk = sd.phat_lai(cau_hinh, qd, gia, nguon, ngay_bat_dau=S.PHIEN[0])
    thuc, phat = _lenh(so), tk.lenh()
    so.db.close()
    tk.dong()
    return thuc, phat, tk.dem, qd


CAU_HINH = {
    "mac_dinh": {},
    "nguong_58": dict(buy_threshold=58),
    "tran_von_40": dict(tran_von_cam_ket_pct=40.0),
    "nghi_sau_lo_7": dict(nghi_sau_lo_ngay=7),
    "cong_vni_tat": dict(cong_vni_bat=False),
    "thoat_50_giu_30": dict(exit_signal_threshold=50, max_hold_sessions=30),
    "chot_loi_cung": dict(chot_loi_cung=True),
}


# ── TẦNG A ────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("ten", sorted(CAU_HINH))
def test_TANG_A_phat_lai_ra_DUNG_cac_lenh_cua_duong_that(gia, ten):
    """Phát lại = chạy thật, từng ô của mười hai cột, với 7 cấu hình cờ. Đây là gác ĐẦU TIÊN của cách A."""
    cfg = _cfg(**CAU_HINH[ten])
    thuc, phat, dem, _ = _tuong_duong(cfg, gia, _NguonKichBan())
    khac = sd.so_sanh_lenh(thuc, phat)
    assert not khac, f"{ten}: {len(khac)} khác biệt, đầu tiên: {khac[:3]}"
    assert len(thuc) >= 8, f"{ten}: kịch bản quá ít lệnh ({len(thuc)}) để canh gì"
    assert dem["thieu_diem"] == 0 and dem["thieu_nen"] == 0


def test_TANG_A_kich_ban_CHAM_cac_nhanh_can_canh(gia):
    """Kịch bản không rỗng ở chỗ nó định canh: cắt lỗ, thoát theo điểm, trần giữ lệnh, huỷ vì kịch trần,
    lệnh gap dưới SL, và cổng VN-INDEX chặn ít nhất một tín hiệu đủ điểm."""
    thuc, phat, _, qd = _tuong_duong(_cfg(), gia, _NguonKichBan())
    ly_do = {r["exit_reason"] for r in thuc}
    assert {"STOP_LOSS", "SIGNAL_REVERSED", "MAX_HOLD"} <= ly_do, ly_do
    assert any(r["status"] == "HUY" for r in thuc), "thiếu ca lệnh chờ bị huỷ vì kịch trần"
    assert any(r["status"] == "OPEN" for r in thuc)
    assert any(str(r["skip_reason"]).startswith("VN-INDEX") for r in qd), "cổng VN-INDEX không chặn gì"
    assert sd.so_sanh_lenh(thuc, phat) == []


def test_TANG_A_phien_chi_khop_xen_ke_duoc_phat_lai_dung(gia):
    """Đường thật chạy chỉ-khớp ở phiên lẻ (không chấm, không quyết định): bộ phát lại thấy phiên-mã
    thiếu điểm, chạy chỉ-khớp, ĐẾM — và ra đúng các lệnh ấy."""
    thuc, phat, dem, qd = _tuong_duong(_cfg(), gia, _NguonKichBan(), chi_khop_xen_ke=True)
    assert sd.so_sanh_lenh(thuc, phat) == []
    phien_le = (S.SO_PHIEN - 1) // 2
    assert dem["thieu_diem"] == phien_le * len(S.MA), dem
    assert len(thuc) >= 3


def test_TANG_A_vn_index_THAT_cua_nguon_tiem_duoc_bang_cong_cua_market_filter(gia):
    """`NguonVni` phát lại đúng thứ `is_vni_bullish` THẬT (bản sao `MF` của `market_filter`) quyết định trên
    cùng khung VN-INDEX."""
    vni = _khung_vni(gia)
    thuc, phat, dem, qd = _tuong_duong(_cfg(), gia, sd.NguonVni(vni), vni_df=vni)
    assert sd.so_sanh_lenh(thuc, phat) == []
    bi_chan = [r for r in qd if str(r["skip_reason"]).startswith("VN-INDEX")]
    assert bi_chan, "khung VN-INDEX tổng hợp không chặn tín hiệu nào: gác không canh gì"
    assert any(r["score"] >= 62 for r in bi_chan)


@pytest.mark.parametrize("hau_to", ["", " 07:00:00"], ids=["ngay_tron", "ngay_kem_gio"])
def test_TANG_A_nguon_vni_tiem_duoc_giong_market_filter_tren_moi_ngay(gia, monkeypatch, hau_to):
    """Cả hai dạng cột `time`: cache CSV (`2026-09-30`) và nguồn tải thẳng (`2026-09-30 07:00:00`). Từ BƯỚC
    241 (lỗi 195) cổng thật so NGÀY 10 ký tự nên hai dạng đọc cùng nến; nguồn tiêm được phải giống nó ở
    cả hai dạng."""
    vni = _khung_vni(gia)
    vni["time"] = vni["time"] + hau_to
    khung = vni.copy()
    khung["vni_ma50"] = khung["close"].rolling(MF.MA_WINDOW).mean()
    monkeypatch.setattr(MF, "get_vni_df", lambda: khung)
    nguon = sd.NguonVni(vni)
    ngay = [d for d in S.PHIEN]
    that = [MF.is_vni_bullish(d) for d in ngay]
    assert [nguon.vni_tren_ma50(d) for d in ngay] == that
    assert True in that and False in that, "khung không cắt MA50: phép so trống rỗng"
    assert nguon.ngay_thieu == set()


def test_nguon_vni_hai_dang_cot_time_doc_CUNG_nen(gia):
    """Hai dạng cột `time` cho CÙNG đáp án mọi ngày (BƯỚC 241, lỗi 195). Trước đó dạng kèm giờ nhìn nến hôm
    trước — bản gốc của test này khẳng định đúng điều ngược lại, và đó là lỗi của cổng thật."""
    tron = _khung_vni(gia)
    kem = tron.copy()
    kem["time"] = kem["time"] + " 07:00:00"
    a, b = sd.NguonVni(tron), sd.NguonVni(kem)
    ket = [(a.vni_tren_ma50(d), b.vni_tren_ma50(d)) for d in S.PHIEN]
    assert all(x == y for x, y in ket)
    assert {x for x, _ in ket} == {True, False}, "khung không cắt MA50: phép so trống rỗng"
    # đáp án của ngày d là nến của CHÍNH ngày d, không phải nến liền trước
    d = tron.assign(ma=tron["close"].rolling(50).mean())
    for ngay in S.PHIEN:
        dong = d[d["time"] == ngay].iloc[-1]
        assert b.vni_tren_ma50(ngay) == (float(dong["close"]) >= float(dong["ma"])), ngay


def test_rui_ro_dung_lai_BANG_agent_rui_ro_trong_duong_cham_diem_THAT(gia, monkeypatch):
    """Không thay `MasterConsensusAgent`: gọi `paper_runner._analyze` THẬT trên khung tổng hợp rồi so với
    `dung_lai_rui_ro` — giá vào, cắt lỗ, chốt lời, tỷ lệ cắt lỗ."""
    import post_mortem_learning
    monkeypatch.setattr(post_mortem_learning, "get_learning_engine", lambda *a, **k: _TatHoc())
    # khoá cache KHÔNG chứa kịch bản: kết quả THẬT ở đây không được lọt vào các lượt chạy kịch bản
    dang_co = dict(pr._ANALYZE_CACHE)
    pr._ANALYZE_CACHE.clear()
    so_sanh = 0
    try:
        for ma in ("FPT", "HPG", "SHS"):
            for i in (30, 55, 80, 94):
                ls = gia[ma].iloc[: i + 1]
                that = pr._analyze(ma, ls, "HOSE", S.PHIEN[i])["analyses"]["risk"]["recommendations"]
                assert sd.dung_lai_rui_ro(ma, ls) == that, (ma, i)
                so_sanh += 1
    finally:
        pr._ANALYZE_CACHE.clear()
        pr._ANALYZE_CACHE.update(dang_co)
    assert so_sanh == 12


# ── đột biến của chính bộ phát lại phải đỏ: các phép thử đơn vị ───────────────────────────────
def _qd(ma, ngay, diem, at, seq, chat_luong="OK"):
    return {"seq": seq, "at": at, "symbol": ma, "signal_date": ngay, "score": diem,
            "recommendation": "MUA" if diem >= 62 else "GIỮ", "acted": 0, "skip_reason": "",
            "components": "{}", "reasons": "[]", "data_quality": chat_luong}


def test_chon_quyet_dinh_giu_dong_SAU_CUNG_theo_at_va_seq():
    ds = [_qd("AAA", "2026-10-01", 70, at=10.0, seq=1),
          _qd("AAA", "2026-10-01 00:00:00", 40, at=20.0, seq=2),     # lượt quét sau: thắng, dù ngày 19 ký tự
          _qd("AAA", "2026-10-01", 55, at=20.0, seq=3),               # cùng `at`: `seq` lớn thắng
          _qd("AAA", "2026-10-02", 66, at=5.0, seq=4),
          _qd("BBB", "2026-10-01", 61, at=1.0, seq=5)]
    giu = sd.chon_quyet_dinh(ds)
    assert set(giu) == {("AAA", "2026-10-01"), ("AAA", "2026-10-02"), ("BBB", "2026-10-01")}
    assert giu[("AAA", "2026-10-01")][1]["score"] == 55
    # đảo thứ tự đầu vào không đổi kết quả
    assert sd.chon_quyet_dinh(list(reversed(ds)))[("AAA", "2026-10-01")][1]["score"] == 55
    # thiếu `at` xếp TRƯỚC mọi dòng có `at`
    them = [_qd("CCC", "2026-10-01", 10, at=None, seq=None), _qd("CCC", "2026-10-01", 77, at=0.5, seq=1)]
    assert sd.chon_quyet_dinh(them)[("CCC", "2026-10-01")][1]["score"] == 77


def test_thu_tu_ma_trong_phien_la_at_seq_chu_khong_phai_ten_ma(gia):
    """Trần vốn phụ thuộc thứ tự mở lệnh: đảo thứ tự `at` của hai mã cùng tín hiệu đổi mã nào vào lệnh."""
    d = S.PHIEN[40]
    chung = {"FPT": 80, "VCB": 80}
    nguon = _NguonKichBan()

    def chay(at_fpt, at_vcb, tran):
        qd = [_qd(ma, d, diem, at=at, seq=i) for i, (ma, diem, at)
              in enumerate([("FPT", 80, at_fpt), ("VCB", 80, at_vcb)], 1)]
        tk = sd.phat_lai(_cfg(tran_von_cam_ket_pct=tran), qd, {m: gia[m] for m in chung}, nguon,
                         ngay_bat_dau=d, ngay_ket_thuc=d)
        ra = {r["symbol"]: r["size_pct"] for r in tk.lenh()}
        tk.dong()
        return ra

    co = chay(1.0, 2.0, 100.0)
    assert set(co) == {"FPT", "VCB"}
    tran = max(co.values()) + 0.01           # chỉ chừa chỗ cho MỘT lệnh: lệnh vào TRƯỚC chiếm chỗ
    assert tran < sum(co.values())
    assert list(chay(1.0, 2.0, tran)) == ["FPT"]
    assert list(chay(2.0, 1.0, tran)) == ["VCB"]


def test_quyet_dinh_ngoai_cua_so_duoc_dem_khong_chay(gia):
    d0, d1, d2 = S.PHIEN[40], S.PHIEN[41], S.PHIEN[42]
    qd = [_qd("FPT", d, 90, at=float(i), seq=i) for i, d in enumerate([d0, d1, d2], 1)]
    tk = sd.phat_lai(_cfg(), qd, {"FPT": gia["FPT"]}, _NguonKichBan(), ngay_bat_dau=d1, ngay_ket_thuc=d1)
    assert tk.dem["quyet_dinh_ngoai_cua_so"] == 2 and tk.dem["phien"] == 1 and tk.dem["buoc"] == 1
    assert tk.lenh()[0]["signal_date"] == d1               # chỉ quyết định TRONG cửa sổ được chạy
    assert (tk.ngay_bat_dau, tk.ngay_ket_thuc) == (d1, d1)
    tk.dong()


def test_phien_ma_thieu_nen_duoc_dem_va_bo_qua(gia):
    d = S.PHIEN[40]
    ngan = gia["FPT"].iloc[:40]                       # FPT không có nến ngày d
    qd = [_qd("FPT", d, 90, at=1.0, seq=1), _qd("VCB", d, 90, at=2.0, seq=2)]
    tk = sd.phat_lai(_cfg(), qd, {"FPT": ngan, "VCB": gia["VCB"], "GAS": gia["GAS"]},
                     _NguonKichBan(), ngay_bat_dau=d, ngay_ket_thuc=d)
    assert tk.dem["thieu_nen"] == 1 and tk.ds_thieu_nen == [("FPT", d)]
    assert [r["symbol"] for r in tk.lenh()] == ["VCB"]
    tk.dong()


def test_phien_ma_thieu_diem_chay_chi_khop_va_khong_xet_vao(gia):
    """Mã có nến mà không có quyết định: ĐẾM, không mở lệnh dù điểm của ngày khác cao."""
    d0, d1 = S.PHIEN[40], S.PHIEN[41]
    qd = [_qd("FPT", d0, 90, at=1.0, seq=1)]          # d1: FPT không có quyết định
    tk = sd.phat_lai(_cfg(), qd, {"FPT": gia["FPT"]}, _NguonKichBan(), ngay_bat_dau=d0, ngay_ket_thuc=d1)
    assert tk.dem["thieu_diem"] == 1 and tk.dem["buoc"] == 2 and tk.ds_thieu_diem == [("FPT", d1)]
    assert [r["status"] for r in tk.lenh()] == ["OPEN"]       # d0 đặt lệnh chờ, d1 chỉ khớp
    tk.dong()


def test_phat_lai_TU_CHOI_cau_hinh_ma_lat_2_chua_co_dau_vao(gia):
    nguon = _NguonKichBan()
    cho_qua = [(dict(luat_vao="KE_HOACH_B6"), NotImplementedError),
               (dict(do_rong_nguong=0.5), NotImplementedError),
               (dict(loc_imom_phan_vi=0.2), ValueError),
               (dict(chot_sut_giam_nguong=0.15), ValueError)]
    for kw, loi in cho_qua:
        with pytest.raises(loi):
            sd.phat_lai(_cfg(**kw), [], {"FPT": gia["FPT"]}, nguon)
    with pytest.raises(ValueError):                    # cổng VN-INDEX bật mà không có nguồn
        sd.phat_lai(_cfg(), [], {"FPT": gia["FPT"]}, None)


def test_phat_lai_TU_CHOI_khi_DUNG_MUC_FIBONACCI_bat(gia, monkeypatch):
    monkeypatch.setattr(pt, "DUNG_MUC_FIBONACCI", True)
    with pytest.raises(ValueError):
        sd.phat_lai(_cfg(), [], {"FPT": gia["FPT"]}, _NguonKichBan())


def test_nguon_vni_do_rong_NO_chu_khong_tra_khong_chan():
    nguon = sd.NguonVni(None)
    with pytest.raises(NotImplementedError):
        nguon.do_rong("2026-10-01")


def test_nguon_vni_ghi_ngay_thieu_nhung_van_tra_nhu_nguon_that(gia):
    vni = _khung_vni(gia).iloc[:-30]                   # chuỗi dừng trước phần cuối kịch bản
    nguon = sd.NguonVni(vni)
    cuoi = vni["time"].iloc[-1]
    assert nguon.vni_tren_ma50(cuoi) in (True, False)
    assert nguon.ngay_thieu == set()
    nguon.vni_tren_ma50("2999-01-01")
    nguon.vni_tren_ma50("1999-01-01")                   # trước chuỗi: không có dòng nào
    assert nguon.ngay_thieu == {"2999-01-01", "1999-01-01"}
    assert sd.NguonVni(None).vni_tren_ma50("2026-10-01") is True


def test_vi_the_mang_sang_chon_dung_lenh_va_trang_thai_dau_phien():
    n = "2026-09-28"
    t = lambda **kw: dict(dict(symbol="AAA", exchange="HOSE", signal_date="2026-09-20", entry_date="2026-09-22",
                               entry_price=10.0, exit_date=None, exit_price=None, exit_reason=None,
                               stop_loss=9.0, take_profit=12.0, size_pct=5.0, entry_score=65,
                               status="OPEN"), **kw)
    lenh = [
        t(symbol="OPEN_CU"),                                                        # đang mở -> OPEN
        t(symbol="DONG_SAU", status="CLOSED", exit_date="2026-09-28", exit_price=9.5),  # ra ĐÚNG ngày -> còn sống
        t(symbol="DONG_TRUOC", status="CLOSED", exit_date="2026-09-25", exit_price=9.5),  # đã xong
        t(symbol="HUY_TRUOC", status="HUY", entry_date=None, entry_price=None, exit_date="2026-09-25"),
        t(symbol="CHO_KHOP", signal_date="2026-09-25", entry_date="2026-09-28", entry_price=11.0,
          status="CLOSED", exit_date="2026-10-09", exit_price=10.0, exit_reason="STOP_LOSS"),  # khớp ĐÚNG ngày
        t(symbol="TIN_HIEU_NAY", signal_date="2026-09-28", entry_date="2026-09-29"),         # tín hiệu cùng ngày
        t(symbol="CU_19", signal_date="2026-08-28 00:00:00", entry_date="2026-09-03 00:00:00",
          status="CLOSED", exit_date="2026-10-01", exit_price=9.0),
    ]
    ra = {r["symbol"]: r for r in sd.vi_the_mang_sang(lenh, n)}
    assert set(ra) == {"OPEN_CU", "DONG_SAU", "CHO_KHOP", "CU_19"}
    assert ra["OPEN_CU"]["status"] == "OPEN" and ra["OPEN_CU"]["entry_price"] == 10.0
    assert ra["DONG_SAU"]["status"] == "OPEN" and ra["DONG_SAU"]["exit_price"] is None
    assert ra["CHO_KHOP"]["status"] == "PENDING"
    assert ra["CHO_KHOP"]["entry_date"] is None and ra["CHO_KHOP"]["entry_price"] is None
    assert ra["CHO_KHOP"]["stop_loss"] == 9.0, "cột còn lại chép NGUYÊN VĂN"
    assert ra["CU_19"]["status"] == "OPEN"


def test_vi_the_mang_sang_duoc_gieo_vao_so_phat_lai_va_khop_o_phien_dau(gia):
    d = S.PHIEN[40]
    gia_vao = float(gia["FPT"]["open"].iloc[40]) * 1000.0
    mang = [dict(symbol="FPT", signal_date=S.PHIEN[39], entry_date=None, entry_price=None, exit_date=None,
                 exit_price=None, exit_reason=None, stop_loss=gia_vao * 0.9, take_profit=gia_vao * 1.5,
                 size_pct=5.0, entry_score=70, status="PENDING")]
    qd = [_qd("FPT", d, 50, at=1.0, seq=1)]
    tk = sd.phat_lai(_cfg(), qd, {"FPT": gia["FPT"]}, _NguonKichBan(), ngay_bat_dau=d,
                     ngay_ket_thuc=d, vi_the_mang_sang=mang)
    (lenh,) = tk.lenh()
    assert tk.dem["mang_sang"] == 1
    assert lenh["status"] == "OPEN" and lenh["entry_date"] == d
    assert lenh["symbol"] == "FPT" and lenh["signal_date"] == S.PHIEN[39]
    tk.dong()


def test_nhan_du_lieu_theo_moc():
    assert sd.nhan_du_lieu("2026-08-27") == sd.NHAN_MO_PHONG
    assert sd.nhan_du_lieu("2026-08-28") == sd.NHAN_TIEN_VE_TRUOC          # không có khai_ngay
    assert sd.nhan_du_lieu("2026-08-28 07:00:00", "2026-11-02") == sd.NHAN_DA_NHIN
    assert sd.nhan_du_lieu("2026-11-01", "2026-11-02") == sd.NHAN_DA_NHIN
    assert sd.nhan_du_lieu("2026-11-02", "2026-11-02") == sd.NHAN_CHUA_NHIN
    assert sd.nhan_du_lieu("2026-08-27", "2026-11-02") == sd.NHAN_MO_PHONG


def test_so_sanh_lenh_bat_tung_loai_khac_biet():
    a = dict(symbol="AAA", signal_date="2026-10-01", entry_date="2026-10-02 00:00:00", entry_price=10.0,
             exit_date=None, exit_price=None, exit_reason=None, stop_loss=9.0, take_profit=12.0,
             size_pct=5.0, entry_score=65, status="OPEN")
    b = dict(a, entry_date="2026-10-02")                    # chỉ khác hậu tố giờ: KHÔNG phải khác biệt
    assert sd.so_sanh_lenh([a], [b]) == []
    c = dict(a, entry_price=10.0000001)                     # không dung sai
    (k,) = sd.so_sanh_lenh([a], [c])
    assert (k["loai"], k["cot"]) == ("khac_o", "entry_price")
    d = dict(a, symbol="BBB")
    loai = sorted(x["loai"] for x in sd.so_sanh_lenh([a], [d]))
    assert loai == ["chi_co_o_phat_lai", "chi_co_o_thuc"]
    (t,) = sd.so_sanh_lenh([a, a], [a])
    assert t["loai"] == "lenh_trung_khoa"
    e = dict(a, status="CLOSED")
    assert [x["cot"] for x in sd.so_sanh_lenh([a], [e])] == ["status"]


# ── phần tính của Tầng B (dụng cụ) ────────────────────────────────────────────────────────────
def test_tang_B_tinh_tren_kich_ban_tong_hop_khop_het_va_bat_sua_mot_o(gia):
    cli = _nap_cli()
    # cổng VN-INDEX tắt để phần tính không phụ thuộc cache toàn cục
    cfg = _cfg(cong_vni_bat=False)
    so, qd = _chay_that(cfg, gia)
    lenh = [dict(r) for r in so.db.execute("SELECT * FROM trades ORDER BY id").fetchall()]
    so.db.close()
    assert len(lenh) >= 8
    b = cli.so_tuong_duong(lenh, qd, gia, None, tu_ngay=S.PHIEN[0], cau_hinh=cfg)
    assert b["khac"] == [] and b["khop_tung_o"] == len(lenh) == b["lenh_thuc_trong_cua_so"]
    assert b["dem"]["thieu_diem"] == 0 and cli.ma_thoat(b) == cli.MA_BANG_NHAU
    sai = [dict(r) for r in lenh]
    sai[0]["entry_price"] = float(sai[0]["entry_price"]) + 1.0
    b2 = cli.so_tuong_duong(sai, qd, gia, None, tu_ngay=S.PHIEN[0], cau_hinh=cfg)
    assert [k["cot"] for k in b2["khac"]] == ["entry_price"] and cli.ma_thoat(b2) == cli.MA_KHAC


def test_ma_thoat_cua_dung_cu_dua_tren_tung_dieu_kien():
    cli = _nap_cli()
    tot = {"khac": [], "vni_thieu": [], "dem": {"thieu_diem": 0, "thieu_nen": 0}}
    assert cli.ma_thoat(tot) == cli.MA_BANG_NHAU
    for sua in ({"khac": [{"loai": "khac_o"}]}, {"vni_thieu": ["2026-10-01"]},
                {"dem": {"thieu_diem": 1, "thieu_nen": 0}}, {"dem": {"thieu_diem": 0, "thieu_nen": 1}}):
        assert cli.ma_thoat(dict(tot, **sua)) == cli.MA_KHAC, sua


def test_tang_B_cua_so_loc_theo_ngay_tin_hieu_hai_dau_deu_gom(gia):
    """Lệnh có tín hiệu ĐÚNG ngày bắt đầu và ĐÚNG ngày cuối đều được so; lệnh trước/sau thì không."""
    cli = _nap_cli()
    cfg = _cfg(cong_vni_bat=False)
    so, qd = _chay_that(cfg, gia)
    lenh = [dict(r) for r in so.db.execute("SELECT * FROM trades ORDER BY id").fetchall()]
    so.db.close()
    ngay = sorted({sd.ngay10(t["signal_date"]) for t in lenh})
    dau, cuoi = ngay[1], ngay[-2]
    b = cli.so_tuong_duong(lenh, qd, gia, None, tu_ngay=dau, den_ngay=cuoi, cau_hinh=cfg)
    trong = [t for t in lenh if dau <= sd.ngay10(t["signal_date"]) <= cuoi]
    assert b["lenh_thuc_trong_cua_so"] == len(trong)
    assert any(sd.ngay10(t["signal_date"]) == dau for t in lenh)
    assert any(sd.ngay10(t["signal_date"]) == cuoi for t in lenh)
    assert b["lenh_thuc_sau_ngay_cuoi"] == len([t for t in lenh if sd.ngay10(t["signal_date"]) > cuoi])
    assert b["tu_ngay"] == dau and b["ngay_cuoi"] == cuoi
    # lệnh có tín hiệu TRƯỚC `dau` mà còn sống ở `dau` được chép (mang sang), không tính vào so sánh
    assert len(b["mang_sang"]) == len(sd.vi_the_mang_sang(lenh, dau)) > 0
    assert b["dem"]["mang_sang"] == len(b["mang_sang"]), "vị thế mang sang phải được GIEO vào sổ phát lại"
    # phát lại tìm thấy MỌI lệnh thật có tín hiệu đúng ngày bắt đầu (ngày đầu của cửa sổ phát lại cũng gom)
    thieu = [k for k in b["khac"] if k["loai"] == "chi_co_o_thuc" and k["khoa"][1] == dau]
    assert not thieu, thieu
    assert b["lenh_phat_lai_trong_cua_so"] >= len([t for t in trong if sd.ngay10(t["signal_date"]) == dau])


def test_tang_B_lenh_chua_khop_o_ngay_cuoi_khong_so_SL_va_size(gia):
    """Tín hiệu rơi đúng ngày cuối: phát lại có lệnh PENDING (cỡ lúc ĐẶT) còn sổ thật chỉ giữ cỡ lúc KHỚP và SL
    đã nâng — hai cột ấy không so được; còn lại (mã, ngày tín hiệu, điểm, chốt lời) vẫn so."""
    cli = _nap_cli()
    cfg = _cfg(cong_vni_bat=False)
    so, qd = _chay_that(cfg, gia)
    lenh = [dict(r) for r in so.db.execute("SELECT * FROM trades ORDER BY id").fetchall()]
    so.db.close()
    t = next(r for r in lenh if r["status"] in ("OPEN", "CLOSED") and r["entry_date"]
             and sd.ngay10(r["entry_date"]) > sd.ngay10(r["signal_date"]))
    cuoi = sd.ngay10(t["signal_date"])
    b = cli.so_tuong_duong(lenh, qd, gia, None, tu_ngay=S.PHIEN[0], den_ngay=cuoi, cau_hinh=cfg)
    assert b["khac"] == [], b["khac"][:3]
    khoa = (t["symbol"], cuoi)
    assert {c for k, c in b["cot_khong_so_duoc"] if k == khoa} == {"stop_loss", "size_pct"}


def test_dung_cu_chay_tron_tren_so_tam_va_in_bao_cao(gia, tmp_path, monkeypatch, capsys):
    """Dòng lệnh đầu-cuối trên một DB tạm dựng từ kịch bản: đọc sổ, đọc giá (đã thay), phát lại, in, mã thoát."""
    import sqlite3
    cli = _nap_cli()
    cfg = _cfg(cong_vni_bat=False)
    so, _ = _chay_that(cfg, gia)
    duong = tmp_path / "so_tam.db"
    dich = sqlite3.connect(duong)
    so.db.backup(dich)
    dich.close()
    so.db.close()
    monkeypatch.setattr(pt, "CONG_VNI_BAT", False)      # `tu_module()` đọc cờ lúc gọi
    monkeypatch.setattr(cli, "doc_gia_cache", lambda ds: {m: gia[m] for m in ds if m in gia})
    cuoi = S.PHIEN[70]
    ma = cli.main(["tuong-duong", "--so-tam", str(duong), "--tu-ngay", S.PHIEN[0], "--den-ngay", cuoi])
    ra = capsys.readouterr().out
    assert ma == cli.MA_BANG_NHAU, ra
    assert f"{S.PHIEN[0]} .. {cuoi}" in ra and "Khop TUNG O" in ra and "Khong co dung sai" in ra
    # sổ sai một ô -> khác biệt được IN và mã thoát là 1
    db = sqlite3.connect(duong)
    db.execute("UPDATE trades SET entry_price = entry_price + 1 WHERE id = 1")
    db.commit()
    db.close()
    ma2 = cli.main(["tuong-duong", "--so-tam", str(duong), "--tu-ngay", S.PHIEN[0], "--den-ngay", cuoi])
    ra2 = capsys.readouterr().out
    assert ma2 == cli.MA_KHAC and "KHAC" in ra2 and "entry_price" in ra2, ra2
    # sổ rỗng giá -> không đọc được, mã 2
    monkeypatch.setattr(cli, "doc_gia_cache", lambda ds: {})
    assert cli.main(["tuong-duong", "--so-tam", str(duong)]) == cli.MA_KHONG_DOC_DUOC


def test_dung_cu_mac_dinh_cua_so_la_NGAY_MO_CONG_va_gia_la_cache():
    cli = _nap_cli()
    a = cli.dung_parser().parse_args(["tuong-duong"])
    assert a.tu_ngay == sd.NGAY_MO_CONG and a.nguon_gia == "cache" and a.den_ngay is None and a.so_tam is None
    assert cli.dung_parser().parse_args(["tuong-duong", "--tu-ngay", "2026-09-25"]).tu_ngay == "2026-09-25"


def test_dung_cu_mo_so_tam_CHI_DOC(tmp_path, monkeypatch):
    """`doc_so_tam` mở DB bằng URI `mode=ro`: kể cả khi mã sau này có lỡ tay, SQLite từ chối ghi."""
    import sqlite3
    cli = _nap_cli()
    duong = tmp_path / "so_tam.db"
    db = sqlite3.connect(duong)
    db.execute("CREATE TABLE trades (id INTEGER PRIMARY KEY, symbol TEXT)")
    db.execute("CREATE TABLE decisions (seq INTEGER PRIMARY KEY, symbol TEXT)")
    db.execute("INSERT INTO trades (symbol) VALUES ('AAA')")
    db.execute("INSERT INTO decisions (symbol) VALUES ('AAA')")
    db.commit()
    db.close()
    truoc = duong.read_bytes()
    thay_the = []
    that = sqlite3.connect

    def ghi_nho(*a, **k):
        thay_the.append((a, k))
        return that(*a, **k)

    monkeypatch.setattr(cli.sqlite3, "connect", ghi_nho)
    lenh, qd = cli.doc_so_tam(str(duong))
    assert lenh == [{"id": 1, "symbol": "AAA"}] and qd == [{"seq": 1, "symbol": "AAA"}]
    (a, k), = thay_the
    assert a[0].endswith("?mode=ro") and k.get("uri") is True, thay_the
    assert duong.read_bytes() == truoc
    ro = that(f"file:{duong.as_posix()}?mode=ro", uri=True)
    with pytest.raises(sqlite3.OperationalError):
        ro.execute("INSERT INTO trades (symbol) VALUES ('BBB')")
    ro.close()


def test_tang_B_lenh_thoat_theo_tin_hieu_o_ngay_cuoi_khong_so_status(gia):
    """Đường thật ghi `exit_date` = NGÀY KHỚP RA; nếu tín hiệu thoát rơi đúng ngày cuối thì phát lại đang
    ở CLOSING còn sổ thật chỉ cho thấy ngày khớp sau đó: `status` của lệnh ấy KHÔNG so được (ghi lại)."""
    cli = _nap_cli()
    cfg = _cfg(cong_vni_bat=False)
    so, qd = _chay_that(cfg, gia)
    lenh = [dict(r) for r in so.db.execute("SELECT * FROM trades ORDER BY id").fetchall()]
    so.db.close()
    ung = [t for t in lenh if t["exit_reason"] in ("SIGNAL_REVERSED", "MAX_HOLD") and t["status"] == "CLOSED"]
    assert ung, "kịch bản không có lệnh thoát theo tín hiệu"
    t = ung[0]
    cuoi = S.PHIEN[S.PHIEN.index(t["exit_date"]) - 1]
    b = cli.so_tuong_duong(lenh, qd, gia, None, tu_ngay=S.PHIEN[0], den_ngay=cuoi, cau_hinh=cfg)
    assert b["khac"] == [], b["khac"][:3]
    khoa = (t["symbol"], sd.ngay10(t["signal_date"]))
    assert {c for k, c in b["cot_khong_so_duoc"] if k == khoa} == {"stop_loss", "status", "exit_date",
                                                                    "exit_reason"}, b["cot_khong_so_duoc"]


def test_tang_B_lenh_that_doi_qua_ngay_cuoi_khong_so_cot_da_doi(gia):
    """Sổ chỉ giữ trạng thái CUỐI: lệnh mở tới hết cửa sổ mà sổ thật đã nâng cắt lỗ sau đó thì KHÔNG so
    cắt lỗ (ghi lại trong `cot_khong_so_duoc`), nhưng vẫn so giá vào."""
    cli = _nap_cli()
    cfg = _cfg(cong_vni_bat=False)
    so, qd = _chay_that(cfg, gia)
    lenh = [dict(r) for r in so.db.execute("SELECT * FROM trades ORDER BY id").fetchall()]
    so.db.close()
    cuoi = S.PHIEN[60]
    b = cli.so_tuong_duong(lenh, qd, gia, None, tu_ngay=S.PHIEN[0], den_ngay=cuoi, cau_hinh=cfg)
    assert b["khac"] == [], b["khac"][:3]
    assert b["ngay_cuoi"] == cuoi and b["lenh_thuc_sau_ngay_cuoi"] > 0
    assert any(c == "stop_loss" for _, c in b["cot_khong_so_duoc"]), "không có lệnh nào đang mở qua ngày cuối"


# ── G1–G5: gác AST (đặc tả mục 11) ───────────────────────────────────────────────────────────
TEN_GHI = {"push", "write_all", "append_rows", "ghi_ke_hoach", "record_trade", "update_trade",
           "write_text", "write_bytes", "to_csv", "to_json", "dump"}
CAM_CHAM_DIEM = {"_analyze", "MasterConsensusAgent", "run_full_analysis", "run_session"}
CAM_UNG_VIEN = {"SO_UNG_VIEN", "doc_so_ung_vien", "diem_ung_vien"}


def _cay(duong):
    return ast.parse(duong.read_text(encoding="utf-8"))


def _goi(cay) -> set[str]:
    ra = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name):
                ra.add(f.id)
            elif isinstance(f, ast.Attribute):
                ra.add(f.attr)
    return ra


def _ten_dung(cay) -> set[str]:
    """Mọi tên được DÙNG hay nhập: Name, Attribute, alias của import."""
    ra = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Name):
            ra.add(n.id)
        elif isinstance(n, ast.Attribute):
            ra.add(n.attr)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names:
                ra.add(a.name.split(".")[-1])
                if a.asname:
                    ra.add(a.asname)
    return ra


def _chuoi(cay) -> list[str]:
    return [n.value for n in ast.walk(cay) if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def _mo_ghi(cay) -> list[ast.Call]:
    """Lời gọi `open(...)` ở chế độ ghi/nối/tạo (đối số thứ hai hay `mode=`)."""
    ra = []
    for n in ast.walk(cay):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "open":
            mode = n.args[1] if len(n.args) > 1 else next(
                (k.value for k in n.keywords if k.arg == "mode"), None)
            if isinstance(mode, ast.Constant) and any(c in str(mode.value) for c in "wax+"):
                ra.append(n)
            elif mode is not None and not isinstance(mode, ast.Constant):
                ra.append(n)                               # chế độ không đọc được -> coi là ghi
    return ra


def _so_nhat_ky_sai(cay) -> list[str]:
    """Chỗ dựng `PaperTradingJournal` không truyền ĐÚNG ":memory:" hay đường dưới `gettempdir()`."""
    sai = []
    for n in ast.walk(cay):
        if isinstance(n, ast.Call):
            f = n.func
            ten = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None
            if ten != "PaperTradingJournal":
                continue
            doi = n.args[0] if n.args else next((k.value for k in n.keywords if k.arg == "path"), None)
            if isinstance(doi, ast.Constant) and doi.value == ":memory:":
                continue
            nguon = ast.dump(doi) if doi is not None else ""
            if "gettempdir" in nguon:
                continue
            sai.append(ast.dump(n)[:90])
    return sai


FILE_GAC = [DUONG_MODULE, DUONG_CLI]


@pytest.mark.parametrize("duong", FILE_GAC, ids=lambda p: p.name if p == DUONG_MODULE else "tools/san_dau.py")
def test_G1_khong_ghi(duong):
    cay = _cay(duong)
    assert not (_goi(cay) & TEN_GHI), sorted(_goi(cay) & TEN_GHI)
    assert not _mo_ghi(cay), "mở file ở chế độ ghi"
    assert not _so_nhat_ky_sai(cay), _so_nhat_ky_sai(cay)


def test_G1_mau_xau_va_tot_cua_chinh_phep_do():
    xau = ['gs.push(db, be)', 'df.to_csv("x.csv")', 'p.write_text("x")', 'journal.ghi_ke_hoach(d)',
           'open("f", "w")', 'open("f", mode="a+")', 'open("f", m)', 'PaperTradingJournal("paper_trades.db")',
           'PaperTradingJournal(DB_PATH)', 'json.dump(x, f)']
    tot = ['open("f")', 'open("f", "r")', 'PaperTradingJournal(":memory:")',
           'PaperTradingJournal(os.path.join(tempfile.gettempdir(), "x.db"))', 'x = json.dumps(d)',
           '"""push() chỉ nằm trong chú thích"""\n# push(x)\nx = 1']
    for m in xau:
        c = ast.parse(m)
        assert (_goi(c) & TEN_GHI) or _mo_ghi(c) or _so_nhat_ky_sai(c), f"không bắt được: {m}"
    for m in tot:
        c = ast.parse(m)
        assert not ((_goi(c) & TEN_GHI) or _mo_ghi(c) or _so_nhat_ky_sai(c)), f"bắt nhầm: {m}"


def _importers_cua_san_dau() -> set[str]:
    ra = set()
    for p in duyet_repo.duyet(GOC, "*.py"):
        rel = p.relative_to(GOC)
        if rel.parts[0] in {"tests", ".venv", ".git"} or rel.as_posix() == "san_dau.py":
            continue
        cay = ast.parse(p.read_text(encoding="utf-8"))
        for n in ast.walk(cay):
            if isinstance(n, ast.Import) and any(a.name.split(".")[0] == "san_dau" for a in n.names):
                ra.add(rel.as_posix())
            elif isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[0] == "san_dau":
                ra.add(rel.as_posix())
    return ra


def test_G2_duong_that_KHONG_nhap_san_dau():
    nguoi_nhap = _importers_cua_san_dau()
    assert nguoi_nhap <= {"app.py", "tools/san_dau.py"}, f"chỉ app.py và tools/san_dau.py được nhập: {nguoi_nhap}"
    assert "tools/san_dau.py" in nguoi_nhap
    for ten in ("paper_trading.py", "paper_runner.py", "paper_metrics.py", "run_daily.py", "master_agent.py",
                "analysis_agents.py", "walkforward.py", "sheets_store.py", "cham_bong.py", "hau_kiem_loi.py",
                "ban_tin.py"):
        assert ten not in nguoi_nhap, ten
    assert not [x for x in nguoi_nhap if x.startswith("backtest/")]


def test_G2_phep_do_bat_duoc_mot_importer_la():
    c = ast.parse("import san_dau\nfrom san_dau import phat_lai\n")
    assert any(isinstance(n, ast.Import) for n in ast.walk(c)) and any(
        isinstance(n, ast.ImportFrom) for n in ast.walk(c))


def test_G3_module_thuan_chi_nhap_thu_vien_chuan_va_pandas_o_muc_module():
    cay = _cay(DUONG_MODULE)
    muc_module = set()
    for n in cay.body:
        if isinstance(n, ast.Import):
            muc_module |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            muc_module.add((n.module or "").split(".")[0])
    assert muc_module <= {"__future__", "dataclasses", "json", "typing", "pandas", "numpy"}, muc_module
    # các nhập nặng nằm TRONG hàm
    trong_ham = set()
    for f in ast.walk(cay):
        if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for n in ast.walk(f):
                if isinstance(n, ast.ImportFrom):
                    trong_ham.add((n.module or "").split(".")[0])
                elif isinstance(n, ast.Import):
                    trong_ham |= {a.name.split(".")[0] for a in n.names}
    assert {"paper_trading", "paper_runner", "analysis_agents", "data_collectors"} <= trong_ham
    # không đồng hồ, không mạng
    assert not ({"now", "today", "now_vn", "today_vn", "read_csv", "urlopen", "request", "sleep",
                 "time", "perf_counter", "monotonic"} & _goi(cay)), _goi(cay)
    assert not ({"time", "datetime", "requests", "urllib", "socket", "os", "sys"} & (
        muc_module | trong_ham))


def test_G4_khong_cham_lai_diem():
    for duong in FILE_GAC:
        cay = _cay(duong)
        assert not (_ten_dung(cay) & CAM_CHAM_DIEM), sorted(_ten_dung(cay) & CAM_CHAM_DIEM)
        assert not (set(_chuoi(cay)) & CAM_CHAM_DIEM)
        goc_nhap = {(n.module or "").split(".")[0] for n in ast.walk(cay) if isinstance(n, ast.ImportFrom)}
        assert "master_agent" not in goc_nhap
    # từ analysis_agents chỉ được dựng agent rủi ro
    cay = _cay(DUONG_MODULE)
    tu_agents = {a.name for n in ast.walk(cay) if isinstance(n, ast.ImportFrom)
                 and n.module == "analysis_agents" for a in n.names}
    assert tu_agents == {"RiskManagementAgent"}


def test_G5_UV_001_khong_hien():
    for duong in FILE_GAC:
        cay = _cay(duong)
        chuoi = _chuoi(cay)
        assert not [s for s in chuoi if "UV-" in s or "ung-vien" in s], duong
        assert not (_ten_dung(cay) & (CAM_UNG_VIEN | {"cham_bong"})), duong


def test_G_phep_do_AST_bat_duoc_mau_xau_cua_G3_G4_G5():
    # G4: gọi, nhập hay nhắc tên bằng chuỗi
    for m in ("_analyze(x)", "pr._analyze(x)", "from master_agent import MasterConsensusAgent",
              "x = getattr(m, 'run_session')", "run_full_analysis()"):
        c = ast.parse(m)
        assert (_ten_dung(c) & CAM_CHAM_DIEM) or (set(_chuoi(c)) & CAM_CHAM_DIEM), m
    # G5
    for m in ("x = 'UV-001'", "p = 'docs/ung-vien.json'", "SO_UNG_VIEN", "from cham_bong import doc_so_ung_vien"):
        c = ast.parse(m)
        assert [s for s in _chuoi(c) if 'UV-' in s or 'ung-vien' in s] or (
            _ten_dung(c) & (CAM_UNG_VIEN | {"cham_bong"})), m


def test_dung_cu_nhap_duoc_va_khong_nuot_module_goc():
    """`tools/san_dau.py` nạp dưới tên riêng không làm `import san_dau` trỏ vào nó (bài học BƯỚC 239)."""
    cli = _nap_cli()
    assert cli.sd is sd and sd.__file__ == str(DUONG_MODULE)
    assert Path(sys.modules["san_dau"].__file__).resolve() == DUONG_MODULE
    assert cli.NGAY_BO_MAY_HIEN_HANH > sd.NGAY_MO_CONG
