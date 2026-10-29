"""Gác cho `CauHinhVao`, `NguonThiTruong` và `paper_runner.buoc_phien` (BƯỚC 239, Lát 1 của C1).

Lát 1 là tái cấu trúc KHÔNG đổi hành vi: bằng chứng chính là bảng vàng
(`tests/test_bang_vang_phien.py`, sinh bằng mã TRƯỚC khi sửa). File này thêm ba lớp gác mà bảng
vàng không tự có:

  1. Đường `cau_hinh`: cờ đi qua `CauHinhVao` khi module giữ MẶC ĐỊNH — nếu còn một chỗ trong bộ
     máy đọc cờ module trần thì kịch bản cờ không mặc định cho ra bảng khác.
  2. AST: cờ chỉ được đọc ở `CauHinhVao.tu_module()`; `run_session` là vỏ mỏng; thứ tự bốn bước
     nằm ở MỘT chỗ (`buoc_phien`) và đúng thứ tự.
  3. Nguồn thị trường tiêm được (`nguon`) thật sự thay cache toàn cục, và bỏ trống thì vẫn đi
     đường cũ (kể cả để `CacheQuaHanError` đi ra ngoài).
"""
from __future__ import annotations

import ast
import dataclasses
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
# `tools` ở CUỐI đường tìm: `tools/cham_xac_nhan.py` cùng tên với module gốc, đứng trước là
# làm test nạp sau (test_keo_bang_gia) nhập nhầm dụng cụ thay vì module.
sys.path.append(str(GOC / "tools"))

import market_filter  # noqa: E402
import paper_runner as pr  # noqa: E402
import paper_trading as pt  # noqa: E402
import sinh_bang_vang_phien as S  # noqa: E402

BANG = json.loads((Path(__file__).resolve().parent / "du_lieu" / "bang_vang_phien.json")
                  .read_text(encoding="utf-8"))
TEN = sorted(BANG["kich_ban"])

#: Mười hai cờ mà `CauHinhVao` gom (khớp `sinh_bang_vang_phien.CO`).
CO = list(S.CO)


@pytest.fixture(scope="module")
def gia():
    return S.dung_gia()


def _cfg(**kw) -> pt.CauHinhVao:
    """Cấu hình dựng TƯỜNG MINH (không đọc biến module — test khác có thể đã đặt cờ)."""
    co = dict(cho_phep_mo_lenh_moi=True, buy_threshold=62, tran_von_cam_ket_pct=100.0,
              cong_vni_bat=True, do_rong_nguong=0, nghi_sau_lo_ngay=0, loc_imom_phan_vi=0,
              chot_sut_giam_nguong=0, chot_sut_giam_phien=20, exit_signal_threshold=45,
              max_hold_sessions=60, chot_loi_cung=False)
    co.update(kw)
    return pt.CauHinhVao(**co)


# ── 1. đường cau_hinh khớp bảng vàng ────────────────────────────────

@pytest.mark.parametrize("ten", TEN)
def test_duong_CAU_HINH_khop_bang_vang(ten, gia):
    """Module giữ mặc định; cờ chỉ đi qua `run_session(cau_hinh=...)`."""
    kq = S.chay_kich_ban(ten, "cau_hinh", gia)
    ky_vong = BANG["kich_ban"][ten]
    for khoa in ("lenh", "quyet_dinh_khac_diem_thap", "buoc", "so_quyet_dinh", "bam_quyet_dinh"):
        assert kq[khoa] == ky_vong[khoa], f"{ten}/{khoa} lệch bảng vàng"


def test_tu_module_doc_DUNG_co_voi_gia_tri_phan_biet(monkeypatch):
    """Mỗi trường nhận ĐÚNG cờ cùng tên (giá trị phân biệt từng cờ, nên đổi chéo hai cờ → đỏ)."""
    mau = {"CHO_PHEP_MO_LENH_MOI": False, "BUY_THRESHOLD": 71.5, "TRAN_VON_CAM_KET_PCT": 83.5,
           "CONG_VNI_BAT": False, "DO_RONG_NGUONG": 0.37, "NGHI_SAU_LO_NGAY": 11,
           "LOC_IMOM_PHAN_VI": 0.13, "CHOT_SUT_GIAM_NGUONG": 0.29, "CHOT_SUT_GIAM_PHIEN": 17,
           "EXIT_SIGNAL_THRESHOLD": 33.5, "MAX_HOLD_SESSIONS": 41, "CHOT_LOI_CUNG": True}
    assert sorted(mau) == sorted(CO)
    for k, v in mau.items():
        monkeypatch.setattr(pt, k, v)
    cau = pt.CauHinhVao.tu_module()
    for k, v in mau.items():
        assert getattr(cau, k.lower()) == v, k
    assert cau.luat_vao == "MO_CUA_SAU"
    assert {f.name for f in dataclasses.fields(cau)} == {k.lower() for k in CO} | {"luat_vao"}


def test_CauHinhVao_bat_bien_va_luat_vao_hop_le():
    c = _cfg()
    with pytest.raises(dataclasses.FrozenInstanceError):
        c.buy_threshold = 1  # type: ignore[misc]
    assert _cfg(luat_vao="KE_HOACH_B6").luat_vao == "KE_HOACH_B6"
    with pytest.raises(ValueError):
        _cfg(luat_vao="KHAC")


def test_buy_threshold_TUONG_MINH_thang_cau_hinh_va_cau_hinh_thang_module(monkeypatch):
    monkeypatch.setattr(market_filter, "is_vni_bullish", lambda *a, **k: True)
    kq = {"final_score": 60, "recommendation": "MUA", "data_quality": "OK",
          "score_breakdown": {}, "key_reasons": [],
          "analyses": {"risk": {"recommendations": {
              "entry_price": 30_000.0, "stop_loss_price": 28_500.0, "take_profit_price": 36_000.0}}}}

    def thu(cau, **kw):
        so = pt.PaperTradingJournal(":memory:")
        try:
            return so.consider_entry("FPT", "2026-09-03", kq, cau_hinh=cau, **kw)
        finally:
            so.db.close()
    assert thu(_cfg(buy_threshold=62)) is None
    assert thu(_cfg(buy_threshold=55)) is not None, "cau_hinh.buy_threshold không được dùng"
    assert thu(_cfg(buy_threshold=62), buy_threshold=55.0) is not None, "tham số tường minh phải thắng"
    assert thu(_cfg(buy_threshold=55), buy_threshold=70.0) is None, "tham số tường minh phải thắng"
    monkeypatch.setattr(pt, "BUY_THRESHOLD", 50)         # module nói 50, cấu hình nói 62
    assert thu(_cfg(buy_threshold=62)) is None, "đọc cờ module dù đã có cau_hinh"


def test_fill_pending_luat_khop_chua_co_thi_NO_khong_bo_qua_lang_le():
    so = pt.PaperTradingJournal(":memory:")
    try:
        with pytest.raises(NotImplementedError):
            so.fill_pending("FPT", "2026-09-04", 30_000.0, None, luat_khop=object())
        assert so.fill_pending("FPT", "2026-09-04", 30_000.0, None) == 0
    finally:
        so.db.close()


# ── 2. nguồn thị trường tiêm được ────────────────────────────────────

class _Nguon:
    def __init__(self, vni=True, dr=0.7):
        self.vni, self.dr, self.goi = vni, dr, []

    def vni_tren_ma50(self, ngay):
        self.goi.append(("vni", ngay))
        return self.vni

    def do_rong(self, ngay):
        self.goi.append(("dr", ngay))
        return self.dr


def _kq(diem=70):
    return {"final_score": diem, "recommendation": "MUA", "data_quality": "OK",
            "score_breakdown": {}, "key_reasons": [],
            "analyses": {"risk": {"recommendations": {
                "entry_price": 30_000.0, "stop_loss_price": 28_500.0, "take_profit_price": 36_000.0}}}}


@pytest.fixture
def so(monkeypatch):
    def _cam(*a, **k):
        raise AssertionError("đã có nguồn tiêm mà vẫn đọc cache toàn cục")
    import do_rong
    monkeypatch.setattr(market_filter, "is_vni_bullish", _cam)
    monkeypatch.setattr(do_rong, "do_rong_mac_dinh", _cam)
    j = pt.PaperTradingJournal(":memory:")
    yield j
    j.db.close()


def _ly_do(j):
    return j.db.execute("SELECT skip_reason FROM decisions ORDER BY seq DESC LIMIT 1").fetchone()[0]


def test_nguon_VNI_tiem_duoc_thay_cache_toan_cuc(so):
    nguon = _Nguon(vni=False)
    assert so.consider_entry("FPT", "2026-09-03 00:00:00", _kq(), cau_hinh=_cfg(), nguon=nguon) is None
    assert _ly_do(so) == pt.LY_DO_VNI and nguon.goi == [("vni", "2026-09-03 00:00:00")]
    nguon = _Nguon(vni=True)
    assert so.consider_entry("FPT", "2026-09-03", _kq(), cau_hinh=_cfg(), nguon=nguon) is not None


def test_nguon_do_rong_tiem_duoc_va_ngay_thieu_do_rong_van_la_khong_chan(so):
    cau = _cfg(do_rong_nguong=0.5)
    nguon = _Nguon(dr=0.3)
    assert so.consider_entry("FPT", "2026-09-03", _kq(), cau_hinh=cau, nguon=nguon) is None
    assert _ly_do(so).startswith(pt.LY_DO_DO_RONG) and "0.300 < 0.5" in _ly_do(so)
    assert ("dr", "2026-09-03") in nguon.goi
    # Hành vi NGUỒN giữ nguyên (độ rộng thiếu thì không chặn): chính sân đấu phải tự đếm ngày thiếu.
    assert so.consider_entry("HPG", "2026-09-03", _kq(), cau_hinh=cau, nguon=_Nguon(dr=None)) is not None


def test_cong_TAT_thi_nguon_khong_bi_hoi(so):
    nguon = _Nguon(vni=False, dr=0.0)
    assert so.consider_entry("FPT", "2026-09-03", _kq(), nguon=nguon,
                             cau_hinh=_cfg(cong_vni_bat=False, do_rong_nguong=0)) is not None
    assert nguon.goi == [], f"cổng tắt mà vẫn hỏi nguồn: {nguon.goi}"


def test_khong_nguon_thi_di_duong_cu_va_CacheQuaHanError_di_ra_ngoai(monkeypatch):
    goi = []

    def _vni(ngay, *a, **k):
        goi.append(ngay)
        raise market_filter.CacheQuaHanError("cache cũ")
    monkeypatch.setattr(market_filter, "is_vni_bullish", _vni)
    j = pt.PaperTradingJournal(":memory:")
    try:
        with pytest.raises(market_filter.CacheQuaHanError):
            j.consider_entry("FPT", "2026-09-03", _kq(), cau_hinh=_cfg())
    finally:
        j.db.close()
    assert goi == ["2026-09-03"]


def _ls_nen():
    ls = pd.DataFrame({"time": ["2026-09-02", "2026-09-03"], "open": [30.0, 30.0],
                       "high": [30.5, 30.5], "low": [29.5, 29.5], "close": [30.0, 30.0],
                       "volume": [3e6, 3e6]})
    return ls, {"open": 30.0, "high": 30.5, "low": 29.5, "close": 30.0, "volume": 3e6}


def test_buoc_phien_truyen_nguon_xuong_consider_entry(so):
    """Dây `buoc_phien` → `consider_entry(nguon=...)`: thiếu thì sân đấu hỏi cache toàn cục."""
    ls, nen = _ls_nen()
    nguon = _Nguon(vni=False)
    pr.buoc_phien(so, "FPT", ls, nen, "2026-09-03", "HOSE", _cfg(), lambda: _kq(), nguon=nguon)
    assert _ly_do(so) == pt.LY_DO_VNI and nguon.goi == [("vni", "2026-09-03")]


@pytest.mark.parametrize("chot_cung", [True, False])
def test_phien_chi_khop_dung_CAU_HINH_khong_doc_co_module(chot_cung, monkeypatch):
    """Phiên chỉ-khớp: `chot_loi_cung` của cấu hình quyết định có chốt lời hay không, bất kể
    biến module nói gì (module đặt NGƯỢC lại)."""
    monkeypatch.setattr(pt, "CHOT_LOI_CUNG", not chot_cung)
    so = pt.PaperTradingJournal(":memory:")
    try:
        so.db.execute(
            "INSERT INTO trades (symbol, exchange, signal_date, entry_date, entry_price, stop_loss,"
            " take_profit, size_pct, entry_score, status) VALUES"
            " ('FPT','HOSE','2026-08-31','2026-09-01',30000.0,28000.0,30400.0,10.0,70,'OPEN')")
        so.db.commit()
        ls, nen = _ls_nen()
        nen["high"] = 31.0                                   # chạm TP 30.400, không chạm SL
        pr.buoc_phien(so, "FPT", ls, nen, "2026-09-03", "HOSE", _cfg(chot_loi_cung=chot_cung),
                      lambda: pytest.fail("phiên chỉ-khớp không được chấm"), chi_khop=True)
        t = so.all_trades()[0]
        assert (t.status == pt.Status.CLOSED) == chot_cung, (t.status, chot_cung)
        if chot_cung:
            assert t.exit_reason == pt.ExitReason.TAKE_PROFIT
    finally:
        so.db.close()


# ── 3. buoc_phien giữ thứ tự bốn bước ───────────────────────────────

class _SoGia:
    """Sổ giả chỉ GHI LẠI thứ tự gọi bốn bước (và không làm gì khác)."""
    ghi_nhat_ky = False

    def __init__(self, dang_giu=False, dong_sau_xet=False):
        self.dang_giu, self.dong_sau_xet, self.lan = dang_giu, dong_sau_xet, []
        self.ngay_vao = None

    def fill_pending(self, *a, **k):
        self.lan.append("fill_pending")
        return 0

    def fill_closing(self, *a, **k):
        self.lan.append("fill_closing")
        return 0

    def open_position(self, ma):
        return object() if self.dang_giu else None

    def evaluate_open(self, *a, **k):
        self.lan.append("evaluate_open")
        if self.dong_sau_xet:
            self.dang_giu = False
        return []

    def xet_lenh_dat_san(self, *a, **k):
        self.lan.append("xet_lenh_dat_san")
        return []

    def consider_entry(self, *a, **k):
        self.lan.append("consider_entry")
        self.ngay_vao = a[1]
        return None


def _chay(so, chi_khop=False):
    ls = pd.DataFrame({"time": ["2026-09-02", "2026-09-03"], "open": [30.0, 30.0],
                       "high": [30.5, 30.5], "low": [29.5, 29.5], "close": [30.0, 30.0],
                       "volume": [3e6, 3e6]})
    nen = {"open": 30.0, "high": 30.5, "low": 29.5, "close": 30.0, "volume": 3e6}
    cham = []
    kq = pr.buoc_phien(so, "FPT", ls, nen, "2026-09-03", "HOSE", _cfg(),
                       lambda: cham.append(1) or _kq(), chi_khop=chi_khop)
    return kq, len(cham)


def test_buoc_phien_THU_TU_bon_buoc():
    so = _SoGia(dang_giu=False)
    _chay(so)
    assert so.lan == ["fill_pending", "fill_closing", "consider_entry"]
    so = _SoGia(dang_giu=True)
    _chay(so)
    assert so.lan == ["fill_pending", "fill_closing", "evaluate_open"]
    so = _SoGia(dang_giu=True, dong_sau_xet=True)
    _chay(so)
    assert so.lan == ["fill_pending", "fill_closing", "evaluate_open", "consider_entry"]


def test_buoc_phien_chuan_hoa_ngay_ve_10_ky_tu():
    """Đường thật truyền `str(row["time"])` 19 ký tự; sổ và rổ chuẩn so NGÀY (ma_giao_dich-05/-06)."""
    so = _SoGia()
    ls, nen = _ls_nen()
    pr.buoc_phien(so, "FPT", ls, nen, "2026-09-03 07:00:00", "HOSE", _cfg(), lambda: _kq())
    assert so.ngay_vao == "2026-09-03"


def test_buoc_phien_chi_khop_khong_cham_diem_va_final_score_None():
    so = _SoGia(dang_giu=True)
    kq, so_lan_cham = _chay(so, chi_khop=True)
    assert so.lan == ["fill_pending", "fill_closing", "xet_lenh_dat_san"]
    assert so_lan_cham == 0, "phiên chỉ-khớp phải KHÔNG chấm điểm"
    assert kq["final_score"] is None


def test_buoc_phien_cham_diem_LUOI_va_mot_lan_khi_khong_dong():
    so = _SoGia(dang_giu=True)
    assert _chay(so)[1] == 1                                  # chấm một lần cho evaluate_open
    so = _SoGia(dang_giu=False)
    assert _chay(so)[1] == 1                                  # chấm một lần cho consider_entry
    so = _SoGia(dang_giu=True, dong_sau_xet=True)
    assert _chay(so)[1] == 1, "đã có result thì không chấm lại"


# ── 4. AST ──────────────────────────────────────────────────────────

def _cay(ten: str) -> ast.Module:
    return ast.parse((GOC / ten).read_text(encoding="utf-8"))


def _cha(cay):
    return {id(c): n for n in ast.walk(cay) for c in ast.iter_child_nodes(n)}


def _doc_co_tran(cay) -> list[tuple[str, int, str]]:
    """Mọi chỗ ĐỌC (Load) tên một trong mười hai cờ, kèm hàm/phép gán bao quanh."""
    cha = _cha(cay)
    ra = []
    for n in ast.walk(cay):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id in CO:
            bao, p = [], cha.get(id(n))
            while p is not None:
                if isinstance(p, ast.FunctionDef):
                    bao.append(p.name)
                elif isinstance(p, ast.Assign) and isinstance(cha.get(id(p)), ast.Module):
                    bao.append("=" + ",".join(t.id for t in p.targets if isinstance(t, ast.Name)))
                p = cha.get(id(p))
            ra.append((n.id, n.lineno, "/".join(bao)))
    return ra


def test_CO_chi_duoc_doc_o_tu_module_va_phep_suy_CO_MUC_TIEU():
    doc = _doc_co_tran(_cay("paper_trading.py"))
    la = [(t, d, b) for t, d, b in doc if b != "tu_module" and b != "=CO_MUC_TIEU_PCT"]
    assert not la, f"cờ module bị đọc ngoài CauHinhVao.tu_module(): {la}"
    ten = {t for t, _, b in doc if b == "tu_module"}
    assert ten == set(CO), f"tu_module() không đọc đủ mười hai cờ: thiếu {set(CO) - ten}"


def test_PaperTradingJournal_khong_ham_nao_doc_ten_co_tran():
    cay = _cay("paper_trading.py")
    lop = next(n for n in cay.body if isinstance(n, ast.ClassDef) and n.name == "PaperTradingJournal")
    doc = [(n.id, n.lineno) for n in ast.walk(lop)
           if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id in CO]
    assert not doc, f"hàm trong PaperTradingJournal đọc cờ module trần: {doc}"


def test_hai_cong_phu_nhan_nguong_qua_tham_so():
    cay = _cay("paper_trading.py")
    ham = {n.name: n for n in cay.body if isinstance(n, ast.FunctionDef)}
    assert [a.arg for a in ham["do_rong_bi_chan"].args.args] == ["signal_date", "nguong", "nguon"]
    assert [a.arg for a in ham["phan_vi_imom_bi_loc"].args.args] == ["symbol", "signal_date", "phan_vi"]


def test_run_session_la_VO_MONG_goi_buoc_phien_va_khong_tu_goi_so():
    ham = next(n for n in ast.walk(_cay("paper_runner.py"))
               if isinstance(n, ast.FunctionDef) and n.name == "run_session")
    goi = [n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", "?")
           for n in ast.walk(ham) if isinstance(n, ast.Call)]
    assert goi.count("buoc_phien") == 1, goi
    cam = {"fill_pending", "fill_closing", "evaluate_open", "consider_entry", "xet_lenh_dat_san",
           "open_position", "record_decision"}
    assert not cam & set(goi), f"run_session tự gọi sổ: {cam & set(goi)}"
    assert not [n for n in ast.walk(ham) if isinstance(n, ast.If)
                and isinstance(n.test, ast.Name) and n.test.id == "chi_khop"], (
        "run_session còn rẽ nhánh chi_khop — thứ tự bốn bước phải ở MỘT chỗ")


def test_MOT_CHO_giu_thu_tu_bon_buoc_trong_paper_runner():
    cay = _cay("paper_runner.py")
    bp = next(n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == "buoc_phien")
    dong = {}
    for n in ast.walk(bp):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
            dong.setdefault(n.func.attr, []).append(n.lineno)
    for ten in ("fill_pending", "fill_closing", "xet_lenh_dat_san", "evaluate_open", "consider_entry"):
        assert len(dong.get(ten, [])) == 1, f"buoc_phien gọi {ten} {len(dong.get(ten, []))} lần"
    assert (dong["fill_pending"][0] < dong["fill_closing"][0] < dong["xet_lenh_dat_san"][0]
            < dong["evaluate_open"][0] < dong["consider_entry"][0]), dong
    # Không hàm nào khác của paper_runner tự gọi bốn bước (hai bản sao là hai thứ tự).
    tong = {}
    for n in ast.walk(cay):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in (
                "fill_pending", "fill_closing", "evaluate_open", "consider_entry"):
            tong[n.func.attr] = tong.get(n.func.attr, 0) + 1
    assert tong == {"fill_pending": 1, "fill_closing": 1, "evaluate_open": 1, "consider_entry": 1}, tong


def test_paper_trading_khong_nhap_san_dau():
    """Gác G2 của đặc tả C1 cho phần đã có mặt ở Lát 1: đường thật không nhập module sân đấu."""
    for ten in ("paper_trading.py", "paper_runner.py"):
        for n in ast.walk(_cay(ten)):
            if isinstance(n, ast.Import):
                assert not [a for a in n.names if a.name.split(".")[0] == "san_dau"], ten
            if isinstance(n, ast.ImportFrom):
                assert (n.module or "").split(".")[0] != "san_dau", ten
