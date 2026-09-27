"""Sổ lệnh TRUNG THỰC — bảy phát hiện CAO của audit 25/09/2026 trên đường
giao dịch ảo (`docs/STATE.md` BƯỚC 121, sửa ở BƯỚC 123).

Mỗi test dựng lại NGUYÊN VĂN kịch bản audit đã dùng để chứng minh lỗi
(`sim_phien.py`, `sim_ngay.py` trong scratchpad của phiên audit), rồi đòi
hành vi đúng. Chung một chiều: mọi lỗi ở đây đều làm sổ trông ĐẸP hơn thật
— thoát sớm ở giá có trước tín hiệu, bán không trượt giá, cắt lỗ ở mức SL dù
giá đã gap qua, và điều kiện dừng không bao giờ đếm được lệnh nào.
"""
import ast
import datetime as dt
import os
import sys
from pathlib import Path

import pandas as pd

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
os.environ.pop("POST_MORTEM_ENABLED", None)

import paper_metrics as pm  # noqa: E402
import paper_trading as pt  # noqa: E402
from data_quality import GIO_NEN_DA_DONG, nen_cuoi_dang_do  # noqa: E402
from paper_trading import ExitReason, Status  # noqa: E402


class _TatTruotGia:
    """Ghim `MO_PHONG_TRUOT_GIA` TẠI CHỖ, có hoàn trả — không gán ở mức module."""

    def __init__(self, bat: bool):
        self.bat = bat

    def __enter__(self):
        self.cu = pt.MO_PHONG_TRUOT_GIA
        pt.MO_PHONG_TRUOT_GIA = self.bat

    def __exit__(self, *a):
        pt.MO_PHONG_TRUOT_GIA = self.cu


def _so_co_lenh_mo(entry_date="2026-09-03", gia=10000.0, sl=9500.0):
    j = pt.PaperTradingJournal(":memory:")
    j.db.execute(
        "INSERT INTO trades (symbol, exchange, signal_date, entry_date, entry_price,"
        " stop_loss, take_profit, size_pct, entry_score, status, created_at)"
        " VALUES ('HUT','HOSE','2026-09-02',?,?,?,?,6.7,65,'OPEN',0)",
        (entry_date, gia, sl, gia * 1.2))
    j.db.commit()
    return j


def _mot_lenh(j):
    return dict(j.db.execute(
        "SELECT entry_date, exit_date, exit_price, exit_reason, status, stop_loss"
        " FROM trades").fetchone())


# ─────────────────────────────────────────────────────────────────────
# ma_giao_dich-01 · lệnh thoát khớp NGAY trong phiên ra tín hiệu
# ─────────────────────────────────────────────────────────────────────
def test_lenh_thoat_KHONG_khop_trong_CUNG_phien_ra_tin_hieu():
    """CA 1 của audit, nguyên văn: hai lượt quét trong CÙNG phiên 04/09.

    `run_session` gọi `fill_closing` TRƯỚC `evaluate_open`. Lượt trưa đặt
    CLOSING; bản cũ để lượt tối cùng phiên khớp ngay ở giá mở cửa 04/09 —
    một mức giá có TRƯỚC khi tín hiệu thoát ra đời. Cả 3/3 lệnh
    tiến-về-trước đã đóng trên sổ thật (HUT, TCB, NAF) mang hình dạng này.
    """
    with _TatTruotGia(False):
        j = _so_co_lenh_mo()
        assert j.fill_closing("HUT", "2026-09-04", 9900.0) == 0
        kq = j.evaluate_open("HUT", "2026-09-04",
                             {"open": 9900, "high": 9950, "low": 9600,
                              "close": 9700}, current_score=30)
        assert kq and kq[0]["reason"] == ExitReason.SIGNAL_REVERSED
        assert _mot_lenh(j)["exit_date"] == "2026-09-04", (
            "lệnh CLOSING phải mang NGÀY TÍN HIỆU THOÁT")

        assert j.fill_closing("HUT", "2026-09-04", 9900.0) == 0, (
            "lệnh thoát khớp NGAY trong phiên ra tín hiệu — giá mở cửa ấy có "
            "trước tín hiệu (audit ma_giao_dich-01)")
        assert _mot_lenh(j)["status"] == Status.CLOSING

        assert j.fill_closing("HUT", "2026-09-07", 9800.0) == 1
        r = _mot_lenh(j)
        assert (r["status"], r["exit_date"], r["exit_price"]) == (
            Status.CLOSED, "2026-09-07", 9800.0), r
    print("PASS  lệnh thoát chờ phiên SAU tín hiệu, khớp ở giá mở cửa phiên ấy")


def test_lenh_CLOSING_doi_cu_khong_mang_ngay_van_khop():
    """Lệnh CLOSING ghi trước BƯỚC 123 không có ngày tín hiệu. Không có dữ
    kiện để chặn thì khớp như cũ — đừng để nó kẹt vĩnh viễn."""
    with _TatTruotGia(False):
        j = _so_co_lenh_mo()
        j.db.execute("UPDATE trades SET status=?, exit_reason=?",
                     (Status.CLOSING, ExitReason.SIGNAL_REVERSED))
        j.db.commit()
        assert j.fill_closing("HUT", "2026-09-04", 9900.0) == 1
    print("PASS  CLOSING đời cũ (exit_date rỗng) vẫn khớp")


# ─────────────────────────────────────────────────────────────────────
# ma_giao_dich-07 · lệnh thoát theo tín hiệu được bán MIỄN PHÍ trượt giá
# ─────────────────────────────────────────────────────────────────────
_NEN_MONG = {"high": 10000.0, "low": 9800.0, "volume": 20000.0,
             "tham_chieu": 9900.0}


def _khop_closing(bat_truot):
    with _TatTruotGia(bat_truot):
        j = _so_co_lenh_mo()
        j.db.execute("UPDATE trades SET status=?, exit_reason=?, exit_date=?",
                     (Status.CLOSING, ExitReason.SIGNAL_REVERSED, "2026-09-04"))
        j.db.commit()
        assert j.fill_closing("HUT", "2026-09-07", 9900.0, _NEN_MONG) == 1
        return _mot_lenh(j)["exit_price"]


def test_lenh_thoat_theo_tin_hieu_CHIU_truot_gia_ban():
    tat, bat = _khop_closing(False), _khop_closing(True)
    assert tat == 9900.0, f"tắt trượt giá thì khớp đúng giá mở cửa, nhận {tat}"
    assert bat < 9900.0, (
        f"bật trượt giá mà lệnh thoát theo tín hiệu vẫn bán ở {bat} — miễn phí "
        f"trượt giá bán (audit ma_giao_dich-07)")
    print(f"PASS  bán khi thoát theo tín hiệu: tắt {tat:,.0f} · bật {bat:,.0f}")


def test_run_session_TRUYEN_nen_cho_fill_closing():
    """Đọc AST: hàm có tham số `nen` mà không ai truyền thì trượt giá bán
    vẫn không bao giờ chạy — đúng hình dạng "dây chưa cắm"."""
    cay = ast.parse((GOC / "paper_runner.py").read_text(encoding="utf-8"))
    ham = next(n for n in ast.walk(cay)
               if isinstance(n, ast.FunctionDef) and n.name == "run_session")
    goi = [n for n in ast.walk(ham) if isinstance(n, ast.Call)
           and isinstance(n.func, ast.Attribute) and n.func.attr == "fill_closing"]
    assert len(goi) == 1, f"run_session gọi fill_closing {len(goi)} lần"
    so_doi = len(goi[0].args) + len(goi[0].keywords)
    assert so_doi >= 4, "run_session không truyền nến cho fill_closing"
    print("PASS  run_session truyền nến khớp cho fill_closing")


# ─────────────────────────────────────────────────────────────────────
# ma_giao_dich-03 · gap xuống dưới SL vẫn ghi đúng giá SL
# ─────────────────────────────────────────────────────────────────────
def test_gap_xuong_DUOI_SL_thoat_o_gia_MO_CUA():
    """CA 3 của audit, nguyên văn: mở cửa 9.000 < SL 9.500."""
    with _TatTruotGia(False):
        j = _so_co_lenh_mo()
        kq = j.evaluate_open("HUT", "2026-09-04",
                             {"open": 9000, "high": 9100, "low": 8900,
                              "close": 9000}, current_score=70)
    assert kq and kq[0]["reason"] == ExitReason.STOP_LOSS
    assert kq[0]["exit_price"] == 9000.0, (
        f"gap dưới SL mà vẫn ghi giá {kq[0]['exit_price']} — giả định có lợi "
        f"(audit ma_giao_dich-03)")
    print("PASS  gap dưới SL -> thoát ở giá mở cửa 9.000, không phải SL 9.500")


def test_cham_SL_trong_phien_van_thoat_o_SL():
    """Đối chứng: mở cửa TRÊN SL rồi chạm SL trong phiên -> khớp ở SL."""
    with _TatTruotGia(False):
        j = _so_co_lenh_mo()
        kq = j.evaluate_open("HUT", "2026-09-04",
                             {"open": 9900, "high": 9950, "low": 9400,
                              "close": 9600}, current_score=70)
    assert kq[0]["exit_price"] == 9500.0
    print("PASS  chạm SL trong phiên -> thoát ở SL")


# ─────────────────────────────────────────────────────────────────────
# ma_giao_dich-06 · hậu tố giờ khác nhau làm khớp NGAY trong phiên tín hiệu
# ─────────────────────────────────────────────────────────────────────
def test_lenh_cho_KHONG_khop_trong_phien_tin_hieu_du_hau_to_gio_khac():
    """`sim_ngay.py` phần A, nguyên văn."""
    j = pt.PaperTradingJournal(":memory:")
    j.db.execute(
        "INSERT INTO trades (symbol, signal_date, stop_loss, take_profit, size_pct,"
        " entry_score, status, created_at)"
        " VALUES ('NAF','2026-09-03 00:00:00',9000,12000,6.7,65,'PENDING',0)")
    j.db.commit()
    with _TatTruotGia(False):
        assert j.fill_pending("NAF", "2026-09-03 07:00:00", 10000.0) == 0, (
            "lệnh chờ khớp NGAY trong phiên tín hiệu vì hậu tố giờ khác "
            "nhau (audit ma_giao_dich-06)")
        assert j.fill_pending("NAF", "2026-09-04", 10000.0) == 1
    print("PASS  cùng NGÀY, khác hậu tố giờ -> không khớp")


def test_KHONG_cham_lenh_trong_phien_vao_du_hau_to_gio_khac():
    with _TatTruotGia(False):
        j = _so_co_lenh_mo(entry_date="2026-09-03 00:00:00")
        kq = j.evaluate_open("HUT", "2026-09-03 07:00:00",
                             {"open": 9000, "high": 9100, "low": 8900,
                              "close": 9000}, current_score=30)
    assert kq == [], f"lệnh bị chấm ngay trong phiên vào: {kq}"
    print("PASS  không chấm lệnh ngay trong phiên vào, dù hậu tố giờ khác")


def test_run_session_ghi_so_bang_NGAY_10_ky_tu():
    """Nguồn gốc của cả họ lỗi ngày: `run_daily` truyền `str(row["time"])`
    19 ký tự. `run_session` chuẩn hoá ở cửa vào; nhánh `chi_khop` không gọi
    chuỗi agent nên đo được thuần phần ghi sổ."""
    from paper_runner import run_session

    j = pt.PaperTradingJournal(":memory:")
    j.db.execute(
        "INSERT INTO trades (symbol, signal_date, stop_loss, take_profit, size_pct,"
        " entry_score, status, created_at)"
        " VALUES ('NAF','2026-09-03',9000,12000,6.7,65,'PENDING',0)")
    j.db.commit()
    lich_su = pd.DataFrame({
        "time": ["2026-09-03 07:00:00", "2026-09-04 07:00:00"],
        "open": [10000.0, 10100.0], "high": [10200.0, 10300.0],
        "low": [9900.0, 10000.0], "close": [10100.0, 10200.0],
        "volume": [1e6, 1e6]})
    with _TatTruotGia(False):
        run_session(j, "NAF", lich_su,
                    {"open": 10100.0, "high": 10300.0, "low": 10000.0,
                     "close": 10200.0, "volume": 1e6},
                    "2026-09-04 07:00:00", chi_khop=True)
    r = _mot_lenh(j)
    assert r["status"] == Status.OPEN and r["entry_date"] == "2026-09-04", r
    print("PASS  run_session ghi ngày 10 ký tự vào sổ")


# ─────────────────────────────────────────────────────────────────────
# ma_giao_dich-05 · điều kiện dừng đếm 0 lệnh vì ngày 19 ký tự
# ─────────────────────────────────────────────────────────────────────
def _so_130_lenh(dai: bool):
    ts, gia = [], {}
    d0 = dt.date(2026, 9, 1)
    for i in range(130):
        vao = d0 + dt.timedelta(days=2 * i)
        ra = vao + dt.timedelta(days=1)
        f = (lambda d: d.isoformat() + (" 00:00:00" if dai else ""))
        gia[vao.isoformat()] = 1000.0
        gia[ra.isoformat()] = 1000.0 + (i % 7)
        ts.append(pt.Trade(
            id=i + 1, symbol="X", signal_date=f(vao), entry_date=f(vao),
            entry_price=100.0, exit_date=f(ra), exit_price=100.0 - (i % 5),
            exit_reason="SIGNAL_REVERSED", stop_loss=90.0, take_profit=120.0,
            size_pct=6.7, entry_score=65, status="CLOSED",
            created_at=1_790_000_000.0 + 3600 * i))
    return ts, gia


def test_dieu_kien_dung_DEM_DUOC_lenh_ngay_19_ky_tu():
    """`sim_ngay.py` phần B, nguyên văn: 130 lệnh giống hệt, chỉ khác định
    dạng ngày. Bản cũ: 10 ký tự đếm 130, 19 ký tự đếm 0 và bỏ 130."""
    kq = {}
    for dai in (False, True):
        ts, gia = _so_130_lenh(dai)
        dk = pm.dieu_kien_dong_lai(ts, pm.ro_chuan_tu_chuoi_gia(ts, gia))
        kq[dai] = (dk["so_lenh"], dk["bo_qua"])
    assert kq[True] == kq[False] == (130, 0), (
        f"10 ký tự {kq[False]} · 19 ký tự {kq[True]} — điều kiện dừng mù với "
        f"sổ thật (audit ma_giao_dich-05)")
    print("PASS  điều kiện dừng đếm 130/130 lệnh ở cả hai định dạng ngày")


def test_vs_benchmark_KHOP_ro_co_hau_to_gio():
    """Phía kia của cùng phép so: rổ dựng từ cache có hậu tố ` 07:00:00`."""
    ts, _ = _so_130_lenh(False)
    ro = {(t.entry_date + " 07:00:00", t.exit_date + " 07:00:00"): 1.0 for t in ts}
    r = pm.vs_benchmark(ts, ro)
    assert (r["n"], r["bo_qua"]) == (130, 0), r
    print("PASS  rổ có hậu tố giờ khớp đủ 130 lệnh ngày sạch")


def test_build_benchmark_KHOP_cache_co_hau_to_gio():
    """Rổ chuẩn của walkforward dựng từ `df["time"]` thô, mà 40/125 file
    cache mang hậu tố ` 07:00:00`. Sổ ghi ngày 10 ký tự từ BƯỚC 123, nên nếu
    rổ không chuẩn hoá thì mọi lệnh của các mã ấy rơi vào `bo_qua` — một
    phép đo walk-forward âm thầm bỏ mẫu."""
    from paper_runner import build_benchmark

    ngay = ["2026-09-01", "2026-09-02", "2026-09-03"]
    ds = {"A": pd.DataFrame({"time": [d + " 07:00:00" for d in ngay],
                             "close": [100.0, 110.0, 121.0]}),
          "B": pd.DataFrame({"time": ngay, "close": [50.0, 50.0, 55.0]})}
    t = pt.Trade(id=1, symbol="A", signal_date="2026-08-31",
                 entry_date="2026-09-01", entry_price=100.0,
                 exit_date="2026-09-03", exit_price=121.0,
                 exit_reason="SIGNAL_REVERSED", stop_loss=90.0,
                 take_profit=130.0, size_pct=6.7, entry_score=65,
                 status="CLOSED", created_at=0.0)
    ro = build_benchmark([t], ds)
    assert ro == {("2026-09-01", "2026-09-03"): (21.0 + 10.0) / 2}, (
        f"rổ không khớp cache có hậu tố giờ: {ro}")
    print("PASS  rổ chuẩn walkforward gộp được cả hai định dạng ngày")


# ─────────────────────────────────────────────────────────────────────
# ma_giao_dich-02 · state_loi_hua-09 · sổ chỉ ghi trên nến ĐÃ ĐÓNG
# ─────────────────────────────────────────────────────────────────────
_VN = dt.timezone(dt.timedelta(hours=7))


def _luc(h, m, ngay=dt.date(2026, 9, 28)):
    return dt.datetime(ngay.year, ngay.month, ngay.day, h, m, tzinfo=_VN)


def test_nen_cuoi_dang_do_PHAN_DUNG_quanh_gio_chot():
    h, m = GIO_NEN_DA_DONG
    assert nen_cuoi_dang_do("2026-09-28 07:00:00", _luc(10, 0)) is True
    assert nen_cuoi_dang_do("2026-09-28", _luc(h, m) - dt.timedelta(minutes=1)) is True
    assert nen_cuoi_dang_do("2026-09-28", _luc(h, m)) is False
    assert nen_cuoi_dang_do("2026-09-25", _luc(10, 0)) is False, (
        "nến của phiên TRƯỚC luôn là nến đã đóng")
    assert nen_cuoi_dang_do("2026-09-29", _luc(20, 0)) is True, (
        "nến mang ngày TƯƠNG LAI thì không tin")
    print(f"PASS  nến hôm nay dở tới {h:02d}:{m:02d}, nến hôm trước luôn đóng")


def test_run_daily_BO_nen_do_TRUOC_khi_ghi_so():
    """Đọc AST của `execute_daily_scan`: phải có một nhánh gọi
    `nen_cuoi_dang_do` và bỏ nến cuối (`df = df.iloc[:-1]`), đứng TRƯỚC lời
    gọi `run_session`. Kiểm HÌNH DẠNG, không kiểm giá trị — hàm quét cần
    mạng nên không chạy được trong test."""
    cay = ast.parse((GOC / "run_daily.py").read_text(encoding="utf-8"))
    ham = next(n for n in ast.walk(cay)
               if isinstance(n, ast.FunctionDef) and n.name == "execute_daily_scan")

    def _goi(n, ten):
        return (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                and n.func.id == ten)

    chan = [n for n in ast.walk(ham) if isinstance(n, ast.If)
            and any(_goi(c, "nen_cuoi_dang_do") for c in ast.walk(n.test))]
    assert chan, "execute_daily_scan không hỏi nen_cuoi_dang_do"
    bo = [s for n in chan for s in n.body if isinstance(s, ast.Assign)
          and ast.unparse(s) == "df = df.iloc[:-1]"]
    assert bo, "nhánh nến dở không bỏ nến cuối"
    run = [n for n in ast.walk(ham) if _goi(n, "run_session")]
    assert run and min(n.lineno for n in chan) < min(n.lineno for n in run), (
        "chốt nến dở phải đứng TRƯỚC run_session")
    print("PASS  run_daily bỏ nến dở trước khi ghi sổ")
