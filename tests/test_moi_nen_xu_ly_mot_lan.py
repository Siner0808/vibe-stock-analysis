"""Đường quét THẬT xử lý MỖI (mã, nến đã đóng) đúng MỘT lần — BƯỚC 241, lỗi 196.

SỰ CỐ (BƯỚC 240 tái lập, BƯỚC 241 đo): Actions quét 2–3 lần mỗi ngày và mỗi lượt sau giờ đóng cửa
xử lý CÙNG MỘT nến đã đóng. `evaluate_open` không lặp lại được: lượt 1 nâng cắt lỗ lên 0,93 × giá đóng
cửa của nến, lượt 2 xét đáy của CHÍNH nến ấy với cắt lỗ mới và cắt lệnh. Lệnh MSR (#119, 01/10/2026)
vào 54.100, nến 01/10 mở 55.600 · cao 60.000 · thấp 54.300 · đóng 58.600: lượt 1 nâng cắt lỗ 54.498,
đáy 54.300 nằm GIỮA cắt lỗ cũ và cắt lỗ mới — lượt 2 cắt lệnh ở 54.400. Trái bất biến 3
(`NGUYEN-TAC-DO-LUONG.md`: cắt lỗ dời chỉ có hiệu lực từ phiên sau).

Cái sửa: `run_daily` hỏi `PaperTradingJournal.nen_da_xu_ly` trước `run_session` và bỏ qua mã đã có dòng
quyết định của nến ấy. `paper_runner.buoc_phien` KHÔNG đổi (walk-forward và bộ phát lại của sân đấu đã
xử lý mỗi nến một lần).
"""
import ast
import sys
from pathlib import Path

import pandas as pd
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import market_filter  # noqa: E402
import paper_runner as pr  # noqa: E402
import paper_trading as pt  # noqa: E402
import run_daily as rd  # noqa: E402
from paper_trading import PaperTradingJournal, Status  # noqa: E402

TIN_HIEU = "2026-09-24"
PHIEN_KHOP = "2026-09-25"
NEN_D = "2026-10-01"           # nến "MSR": nâng cắt lỗ, đáy nằm giữa cắt lỗ cũ và mới
NEN_D1 = "2026-10-02"
GIA_VAO = 30_000.0
KHOI_LUONG = 3_000_000.0


def _kq(diem: int = 70, gia: float = GIA_VAO, chat_luong: str = "OK") -> dict:
    return {"final_score": diem, "recommendation": "MUA", "data_quality": chat_luong,
            "score_breakdown": {}, "key_reasons": [],
            "analyses": {"risk": {"recommendations": {
                "entry_price": gia, "stop_loss_price": gia * 0.95,
                "take_profit_price": gia * 1.5}}}}


class _Cham:
    """Điểm của phiên do test đặt; đếm số lần bị hỏi (lượt bị bỏ qua không được hỏi)."""

    def __init__(self):
        self.kq = _kq()
        self.hoi = 0
        self.no = False

    def __call__(self, *a, **k):
        self.hoi += 1
        if self.no:
            raise RuntimeError("nguồn hỏng giữa lượt")
        return self.kq


@pytest.fixture
def cham(monkeypatch):
    c = _Cham()
    monkeypatch.setattr(market_filter, "is_vni_bullish", lambda *a, **k: True)
    monkeypatch.setattr(market_filter, "get_vni_df", lambda: None)
    monkeypatch.setattr(pt, "CHO_PHEP_MO_LENH_MOI", True)
    monkeypatch.setattr(pt, "MO_PHONG_TRUOT_GIA", False)
    monkeypatch.setattr(pr, "_analyze", c)
    return c


def _so_that() -> PaperTradingJournal:
    return PaperTradingJournal(":memory:", cho_phep_so_that=True)


def _nen(ngay: str, mo: float, cao: float, thap: float, dong: float):
    """(lịch sử, nến thô) theo NGHÌN ĐỒNG như cache; các phiên trước đứng ở GIA_VAO."""
    ngay_cu = pd.bdate_range("2026-06-01", ngay).strftime("%Y-%m-%d")
    n = len(ngay_cu) - 1
    g = GIA_VAO / 1000.0
    df = pd.DataFrame({"time": list(ngay_cu), "open": [g] * n + [mo], "high": [g] * n + [cao],
                       "low": [g] * n + [thap], "close": [g] * n + [dong],
                       "volume": [KHOI_LUONG] * (n + 1)})
    return df, {"open": mo, "high": cao, "low": thap, "close": dong, "volume": KHOI_LUONG}


def _luot_cu(so, ngay, nen):
    """Lượt quét theo ĐÚNG hành vi cũ: chạy `run_session` mỗi lần được hỏi."""
    df, bar = nen
    return pr.run_session(so, "FPT", df, bar, ngay + " 07:00:00", "HOSE", 62.0)


def _luot_that(so, ngay, nen):
    """Một lượt của vòng quét THẬT — CÙNG ba dòng với `run_daily.execute_daily_scan` (AST ở cuối
    file canh rằng vòng quét có đúng hình dạng này)."""
    df, bar = nen
    s = rd.tra_nen_da_xu_ly(so, "FPT", ngay + " 07:00:00")
    if s is None:
        s = pr.run_session(so, "FPT", df, bar, ngay + " 07:00:00", "HOSE", 62.0)
    return s


def _vi_the_mo(so):
    """Một lệnh OPEN: tín hiệu 24/09, khớp 25/09 ở giá mở cửa, cắt lỗ đầu 28.500 (0,95 × giá vào)."""
    tid = so.consider_entry("FPT", TIN_HIEU, _kq(), exchange="HOSE", buy_threshold=62.0)
    assert tid is not None, "TIỀN ĐỀ gãy: consider_entry không mở lệnh chờ"
    so.fill_pending("FPT", PHIEN_KHOP, GIA_VAO, {"high": GIA_VAO + 500, "low": GIA_VAO - 500,
                                                 "volume": KHOI_LUONG, "tham_chieu": GIA_VAO})
    t = so.all_trades()[0]
    assert t.status == Status.OPEN and float(t.stop_loss) == pytest.approx(28_500.0)
    return t


# Nến "MSR": đóng 36.000 → cắt lỗ mới 0,93 × 36.000 = 33.480; đáy 33.000 nằm giữa 28.500 và 33.480
NEN_MSR = (34.0, 36.5, 33.0, 36.0)


def _anh_chup(so):
    """Toàn bộ trạng thái sổ mà một lượt quét có thể đổi: lệnh, quyết định, nhật ký."""
    return {"trades": [dict(r) for r in so.db.execute("SELECT * FROM trades ORDER BY id")],
            "decisions": [dict(r) for r in so.db.execute("SELECT * FROM decisions ORDER BY seq")],
            "nhat_ky": [dict(r) for r in so.db.execute("SELECT * FROM nhat_ky ORDER BY trade_id")]}


# ───────────────────────────────────────────────────────────────────────
# 1. Ca MSR: quét hai lần một nến
# ───────────────────────────────────────────────────────────────────────

def test_CA_MSR_quet_hai_lan_mot_nen_giu_so_GIONG_HET_quet_mot_lan(cham):
    so = _so_that()
    _vi_the_mo(so)
    nen = _nen(NEN_D, *NEN_MSR)
    s1 = _luot_that(so, NEN_D, nen)
    sau_1 = _anh_chup(so)
    t = so.all_trades()[0]
    assert t.status == Status.OPEN and float(t.stop_loss) == pytest.approx(33_480.0), (
        "TIỀN ĐỀ gãy: lượt 1 phải nâng cắt lỗ lên 0,93 × đóng cửa mà chưa cắt lệnh")
    assert s1["closed"] == 0 and not s1.get("da_xu_ly")
    hoi_sau_1 = cham.hoi

    s2 = _luot_that(so, NEN_D, nen)
    s3 = _luot_that(so, NEN_D, nen)
    assert _anh_chup(so) == sau_1, "quét lại cùng một nến làm sổ đổi: lỗi 196"
    assert s2["da_xu_ly"] and s3["da_xu_ly"]
    assert (s2["closed"], s2["opened"], s2["filled_in"], s2["filled_out"]) == (0, 0, 0, 0)
    assert s2["final_score"] == 70.0
    assert cham.hoi == hoi_sau_1, "lượt bỏ qua không được chấm điểm lại"


def test_ĐOI_CHUNG_hanh_vi_cu_quet_hai_lan_cat_lenh_NGAY_nen_da_nang_stop(cham):
    """Kiểm CHÍNH kịch bản: `run_session` chạy hai lần thì lệnh bị cắt ở nến nâng stop, và còn mở lại một
    lệnh chờ trên CÙNG nến. Nếu kịch bản này không tái lập được lỗi thì ca MSR ở trên canh cái không có."""
    so = _so_that()
    _vi_the_mo(so)
    nen = _nen(NEN_D, *NEN_MSR)
    _luot_cu(so, NEN_D, nen)
    assert so.all_trades()[0].status == Status.OPEN
    _luot_cu(so, NEN_D, nen)
    t = so.all_trades()[0]
    assert t.status == Status.CLOSED and t.exit_reason == pt.ExitReason.STOP_LOSS
    assert str(t.exit_date)[:10] == NEN_D, "cắt lỗ vừa nâng đã cắt chính nến nâng nó"
    # hệ quả dây chuyền: mã hết vị thế nên lượt 2 còn xét VÀO LỆNH trên cùng nến
    cung_nen = [x for x in so.all_trades() if str(x.signal_date)[:10] == NEN_D]
    assert len(cung_nen) == 1 and cung_nen[0].status == Status.PENDING


def test_cat_lo_da_nang_chi_co_hieu_luc_tu_PHIEN_SAU(cham):
    """Bất biến 3 sau khi sửa: nến kế tiếp có đáy chạm cắt lỗ đã nâng thì lệnh đóng Ở NẾN ĐÓ, không sớm hơn."""
    so = _so_that()
    _vi_the_mo(so)
    _luot_that(so, NEN_D, _nen(NEN_D, *NEN_MSR))
    _luot_that(so, NEN_D, _nen(NEN_D, *NEN_MSR))
    assert so.all_trades()[0].status == Status.OPEN
    _luot_that(so, NEN_D1, _nen(NEN_D1, 35.0, 35.5, 33.3, 34.0))     # đáy 33.300 ≤ cắt lỗ 33.480
    t = so.all_trades()[0]
    assert t.status == Status.CLOSED and t.exit_reason == pt.ExitReason.STOP_LOSS
    assert str(t.exit_date)[:10] == NEN_D1


# ───────────────────────────────────────────────────────────────────────
# 2. Dấu "đã xử lý" có mặt ở MỌI đường của lượt quét
# ───────────────────────────────────────────────────────────────────────

def _kich_ban_vao_lenh(so, cham, monkeypatch):
    cham.kq = _kq(70)
    return _nen(NEN_D, 30.0, 30.4, 29.8, 30.2)


def _kich_ban_bi_cong_chan(so, cham, monkeypatch):
    monkeypatch.setattr(market_filter, "is_vni_bullish", lambda *a, **k: False)
    cham.kq = _kq(75)
    return _nen(NEN_D, 30.0, 30.4, 29.8, 30.2)


def _kich_ban_diem_duoi_nguong(so, cham, monkeypatch):
    cham.kq = _kq(40)
    return _nen(NEN_D, 30.0, 30.4, 29.8, 30.2)


def _kich_ban_chat_luong_chan(so, cham, monkeypatch):
    cham.kq = _kq(75, chat_luong="BLOCK")
    return _nen(NEN_D, 30.0, 30.4, 29.8, 30.2)


def _kich_ban_o_C5_dong(so, cham, monkeypatch):
    monkeypatch.setattr(pt, "CHO_PHEP_MO_LENH_MOI", False)
    cham.kq = _kq(75)
    return _nen(NEN_D, 30.0, 30.4, 29.8, 30.2)


def _kich_ban_tran_von(so, cham, monkeypatch):
    monkeypatch.setattr(pt, "TRAN_VON_CAM_KET_PCT", 1.0)
    cham.kq = _kq(75)
    return _nen(NEN_D, 30.0, 30.4, 29.8, 30.2)


def _kich_ban_dang_giu(so, cham, monkeypatch):
    _vi_the_mo(so)
    return _nen(NEN_D, *NEN_MSR)


def _kich_ban_giu_roi_cat_lo_roi_xet_vao(so, cham, monkeypatch):
    _vi_the_mo(so)
    return _nen(NEN_D, 20.0, 20.5, 19.0, 19.5)       # gap dưới cắt lỗ: đóng ngay, rồi xét vào lại


def _kich_ban_thieu_sl_tp(so, cham, monkeypatch):
    cham.kq = _kq(75)
    cham.kq["analyses"]["risk"]["recommendations"] = {}
    return _nen(NEN_D, 30.0, 30.4, 29.8, 30.2)


KICH_BAN = [_kich_ban_vao_lenh, _kich_ban_bi_cong_chan, _kich_ban_diem_duoi_nguong,
            _kich_ban_chat_luong_chan, _kich_ban_o_C5_dong, _kich_ban_tran_von,
            _kich_ban_dang_giu, _kich_ban_giu_roi_cat_lo_roi_xet_vao, _kich_ban_thieu_sl_tp]


@pytest.mark.parametrize("kich_ban", KICH_BAN, ids=lambda f: f.__name__.replace("_kich_ban_", ""))
def test_MOI_duong_cua_luot_quet_de_lai_dau_da_xu_ly_va_luot_hai_khong_doi_gi(kich_ban, cham, monkeypatch):
    """Mã chưa giữ (vào lệnh · bị cổng chặn · dưới ngưỡng · chất lượng · ô C5 · trần vốn · thiếu SL/TP) và mã
    đang giữ (kể cả giữ rồi cắt lỗ rồi xét vào lại): luot 1 ghi dấu, luot 2 bỏ qua và sổ giống hệt."""
    so = _so_that()
    nen = kich_ban(so, cham, monkeypatch)
    assert so.nen_da_xu_ly("FPT", NEN_D) is None, "TIỀN ĐỀ: trước lượt 1 nến chưa có dấu"
    _luot_that(so, NEN_D, nen)
    assert so.nen_da_xu_ly("FPT", NEN_D) is not None, (
        f"{kich_ban.__name__}: lượt 1 không để lại dòng quyết định — lượt sau sẽ xử lý lại nến")
    sau_1 = _anh_chup(so)
    s2 = _luot_that(so, NEN_D, nen)
    assert s2["da_xu_ly"] and _anh_chup(so) == sau_1


def test_luot_NO_giua_chung_khong_de_dau_va_luot_sau_xu_ly_BU(cham):
    so = _so_that()
    nen = _nen(NEN_D, 30.0, 30.4, 29.8, 30.2)
    cham.no = True
    with pytest.raises(RuntimeError):
        _luot_that(so, NEN_D, nen)
    assert so.nen_da_xu_ly("FPT", NEN_D) is None
    cham.no = False
    s = _luot_that(so, NEN_D, nen)
    assert not s.get("da_xu_ly") and s["opened"] == 1


def test_nen_khac_ngay_hoac_ma_khac_KHONG_bi_bo_qua(cham):
    so = _so_that()
    _luot_that(so, NEN_D, _nen(NEN_D, 30.0, 30.4, 29.8, 30.2))
    assert so.nen_da_xu_ly("FPT", NEN_D1) is None
    assert so.nen_da_xu_ly("HPG", NEN_D) is None
    assert rd.tra_nen_da_xu_ly(so, "HPG", NEN_D + " 07:00:00") is None


@pytest.mark.parametrize("hau_to", ["", " 07:00:00", " 00:00:00"])
def test_dau_nhan_ca_dong_quyet_dinh_cu_mang_gio(hau_to, cham):
    """Sổ cũ lưu `signal_date` cả giờ (HANDOFF mục 3, ràng buộc 1): so 10 ký tự, không so chuỗi."""
    so = _so_that()
    so.record_decision("FPT", NEN_D + hau_to, _kq(60), False, "x")
    cu = so.nen_da_xu_ly("FPT", NEN_D + " 07:00:00")
    assert cu is not None and cu["score"] == 60


def test_dau_tra_ve_diem_cua_dong_SAU_CUNG(cham):
    so = _so_that()
    so.record_decision("FPT", NEN_D, _kq(55), False, "lượt 1")
    so.record_decision("FPT", NEN_D, _kq(66), False, "lượt 2")
    assert so.nen_da_xu_ly("FPT", NEN_D)["score"] == 66


def test_so_KHONG_phai_so_that_khong_co_dau(cham):
    """Sổ không ghi nhật ký không ghi dòng cho mã đang giữ, nên không có dấu đáng tin: luôn None."""
    so = PaperTradingJournal(":memory:")
    so.record_decision("FPT", NEN_D, _kq(60), False, "x")
    assert so.nen_da_xu_ly("FPT", NEN_D) is None


def test_ket_qua_bo_qua_CUNG_KHUON_run_session(cham):
    so = _so_that()
    nen = _nen(NEN_D, 30.0, 30.4, 29.8, 30.2)
    that = _luot_that(so, NEN_D, nen)
    qua = _luot_that(so, NEN_D, nen)
    assert set(that) <= set(qua), (set(that) - set(qua), "khuôn kết quả lệch: run_daily đọc s['…'] sẽ nổ")


# ───────────────────────────────────────────────────────────────────────
# 3. Hình dạng của mã
# ───────────────────────────────────────────────────────────────────────

def _ham(file: str, ten: str):
    cay = ast.parse((GOC / file).read_text(encoding="utf-8"))
    return next(n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == ten)


def _goi(n, ten):
    return (isinstance(n, ast.Call)
            and getattr(n.func, "id", getattr(n.func, "attr", None)) == ten)


def _vong_quet_co_dau_bo_qua(ham) -> bool:
    """`s = tra_nen_da_xu_ly(...)` rồi `if s is None:` mà `run_session` NẰM TRONG thân nhánh ấy."""
    for kh in ast.walk(ham):
        if not isinstance(kh, ast.If):
            continue
        t = kh.test
        if not (isinstance(t, ast.Compare) and isinstance(t.left, ast.Name) and t.left.id == "s"
                and isinstance(t.ops[0], ast.Is) and isinstance(t.comparators[0], ast.Constant)
                and t.comparators[0].value is None):
            continue
        trong_than = any(_goi(n, "run_session") for b in kh.body for n in ast.walk(b))
        trong_else = any(_goi(n, "run_session") for b in kh.orelse for n in ast.walk(b))
        if trong_than and not trong_else:
            return True
    return False


def test_AST_vong_quet_THAT_hoi_dau_da_xu_ly_truoc_khi_goi_run_session():
    ham = _ham("run_daily.py", "execute_daily_scan")
    goi_tra = [n for n in ast.walk(ham) if isinstance(n, ast.Assign) and _goi(n.value, "tra_nen_da_xu_ly")
               and [getattr(t, "id", None) for t in n.targets] == ["s"]]
    assert len(goi_tra) == 1, "vòng quét thật phải gán `s = tra_nen_da_xu_ly(...)` đúng một lần"
    run = [n for n in ast.walk(ham) if _goi(n, "run_session")]
    assert len(run) == 1 and run[0].lineno > goi_tra[0].lineno
    assert _vong_quet_co_dau_bo_qua(ham), "run_session phải nằm trong `if s is None:` (chỉ chạy khi nến CHƯA xử lý)"


def test_AST_gac_tu_kiem_mau_xau_va_mau_tot():
    tot = ("def f():\n s = tra_nen_da_xu_ly(1)\n if s is None:\n  s = run_session(1)\n else:\n  n = 1\n")
    xau_khong_if = "def f():\n s = tra_nen_da_xu_ly(1)\n s = run_session(1)\n"
    xau_trong_else = "def f():\n s = tra_nen_da_xu_ly(1)\n if s is None:\n  n = 1\n else:\n  s = run_session(1)\n"
    xau_ca_hai = ("def f():\n s = tra_nen_da_xu_ly(1)\n if s is None:\n  s = run_session(1)\n"
                  " else:\n  s = run_session(2)\n")
    f = lambda src: _vong_quet_co_dau_bo_qua(ast.parse(src).body[0])  # noqa: E731
    assert f(tot) and not f(xau_khong_if) and not f(xau_trong_else) and not f(xau_ca_hai)


def test_AST_paper_runner_KHONG_dung_dau_da_xu_ly_ngu_nghia_buoc_phien_giu_nguyen():
    """Walk-forward và bộ phát lại của C1 đi qua `buoc_phien`/`run_session`: chúng đã xử lý mỗi nến đúng
    một lần, và sổ của chúng KHÔNG ghi dòng cho mã đang giữ nên dấu sẽ sai nếu bị dùng ở đó."""
    for file in ("paper_runner.py", "san_dau.py", "walkforward.py"):
        cay = ast.parse((GOC / file).read_text(encoding="utf-8"))
        goi = [n for n in ast.walk(cay) if _goi(n, "nen_da_xu_ly") or _goi(n, "tra_nen_da_xu_ly")]
        assert goi == [], f"{file} dùng dấu đã-xử-lý: đổi ngữ nghĩa của đường đo"


def test_nen_da_xu_ly_la_HAM_DOC_khong_ghi():
    ham = _ham("paper_trading.py", "nen_da_xu_ly")
    cam = {"record_decision", "commit", "executescript"}
    goi = {getattr(n.func, "attr", getattr(n.func, "id", None)) for n in ast.walk(ham) if isinstance(n, ast.Call)}
    assert not (goi & cam)
    sql = [n.value for n in ast.walk(ham) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    assert not any(s.lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE")) for s in sql)


def test_cac_chuong_KHONG_doc_bang_quyet_dinh_nen_bo_qua_luot_quet_khong_gay_bao_dong_gia():
    """Chuông quét (workflow `success`), chuông nguồn đứng (chuỗi giá + lịch), chuông bài học (nhật ký),
    bảng sức khoẻ: không cái nào đếm dòng `decisions` của một lượt. Chuông C5 chỉ đọc `acted = 1`, mà dấu
    bỏ qua không bao giờ xoá hay thêm một dòng vào lệnh."""
    for f in ("tools/chuong_bao_quet.py", "tools/chuong_nguon_dung.py", "tools/chuong_bai_hoc.py",
              "suc_khoe.py"):
        cay = ast.parse((GOC / f).read_text(encoding="utf-8"))
        chuoi = [n.value for n in ast.walk(cay) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
        ten = {n.id for n in ast.walk(cay) if isinstance(n, ast.Name)} |               {n.attr for n in ast.walk(cay) if isinstance(n, ast.Attribute)}
        assert not [s for s in chuoi if "decisions" in s], f
        assert not [t for t in ten if "quyet_dinh" in t or t == "decisions"], f
    c5 = (GOC / "tools" / "canh_cong_c5.py").read_text(encoding="utf-8")
    assert 'int(q.get("acted") or 0) == 1' in c5
