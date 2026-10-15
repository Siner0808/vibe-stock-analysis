"""BƯỚC 195 (mốc B6 phần 2) — ghi kế hoạch vào lệnh LÚC QUÉT vào tab mới `ke_hoach`.

Người dùng duyệt thiết kế 15/10/2026: tab MỚI (không thêm cột vào tab cũ) · MỌI mã có
điểm ≥ ngưỡng · leader làm · app hiện để sau. Bất biến khoá ở đây:
  1. Kế hoạch tính SAU `run_session` của mã — không chạm khớp lệnh (AST).
  2. Một tín hiệu (mã, ngày nến) ghi MỘT lần; chỉ sổ THẬT ghi.
  3. Tab `ke_hoach`: đẩy CHỈ THÊM theo khoá (mã, ngày); kéo đọc trước mọi DELETE;
     tab vắng ⇒ rỗng; tab lệch tiêu đề ⇒ báo, KHÔNG làm hỏng lượt kéo/đẩy ba tab cũ.
  4. Lỗi lập/ghi kế hoạch KHÔNG BAO GIỜ ném ra lượt quét.
Đột biến: `docs/STATE.md` BƯỚC 195.
"""
from __future__ import annotations

import ast
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import sheets_store as ss  # noqa: E402
import so_ke_hoach as skh  # noqa: E402
from paper_trading import BUY_THRESHOLD, PaperTradingJournal  # noqa: E402


def _so_that():
    return PaperTradingJournal(":memory:", cho_phep_so_that=True)


def _kh(**kw):
    """Một `KeHoachVaoLenh` giả, đủ trường `dong_tu_ke_hoach` đọc."""
    goc = dict(phan_quyet="CHO_VUNG", ly_do=("vì A", "vì B"), ngay="2026-10-14",
               gia_dong=25000.0, atr=800.0, ma20=24000.0, keo_gian_atr=1.25,
               day_xoay_ngay="2026-10-08", day_xoay_gia=23500.0,
               cat_lo_cau_truc=23100.0, rui_ro_pct=7.6, vung=(23950.0, 24300.0),
               so_phien_cho=5, nhan="Đặt chờ")
    goc.update(kw)
    return SimpleNamespace(**goc)


def _dong(ma="AAA", ngay="2026-10-14", **kw):
    return skh.dong_tu_ke_hoach(_kh(ngay=ngay, **kw), ma, 66.0, 62.0, "HOSE",
                                "B6-test", 1_792_000_000.0, ngay or "2026-10-14")


# ───────────────────────── 1. Lược đồ và dựng dòng ─────────────────────────

def test_dong_tu_ke_hoach_doc_dung_truong():
    d = _dong()
    assert d["signal_date"] == "2026-10-14" and d["symbol"] == "AAA"
    assert (d["vung_day"], d["vung_tran"]) == (23950.0, 24300.0)
    assert d["cat_lo"] == 23100.0 and d["phan_quyet"] == "CHO_VUNG"
    assert json.loads(d["ly_do"]) == ["vì A", "vì B"]
    assert set(d) == set(skh.COT_KE_HOACH) - {"seq"}


def test_ke_hoach_khong_lap_duoc_lay_NGAY_NEN_de_khoa_khong_NULL():
    kh = _kh(ngay=None, vung=None, phan_quyet="CHUA_LAP_DUOC", day_xoay_ngay=None)
    d = skh.dong_tu_ke_hoach(kh, "AAA", 66.0, 62.0, "HOSE", "v", 1.0, "2026-10-14")
    assert d["signal_date"] == "2026-10-14"
    assert d["vung_day"] is None and d["day_xoay_ngay"] is None


def test_so_ke_hoach_KHONG_nhap_ham_lap_ke_hoach():
    cay = ast.parse((GOC / "so_ke_hoach.py").read_text(encoding="utf-8"))
    nhap = {(n.module or "") for n in ast.walk(cay) if isinstance(n, ast.ImportFrom)}
    nhap |= {a.name for n in ast.walk(cay) if isinstance(n, ast.Import) for a in n.names}
    assert "ke_hoach_vao_lenh" not in nhap


# ───────────────────────── 2. Sổ: ghi một lần, chỉ sổ thật ─────────────────────────

def test_so_that_ghi_MOT_lan_moi_tin_hieu():
    j = _so_that()
    assert j.ghi_ke_hoach(_dong()) is True
    assert j.ghi_ke_hoach(_dong()) is False                      # cùng (mã, ngày)
    assert j.ghi_ke_hoach(_dong(ngay="2026-10-15")) is True      # ngày khác
    assert j.ghi_ke_hoach(_dong(ma="BBB")) is True                # mã khác
    assert j.db.execute("SELECT COUNT(*) FROM ke_hoach").fetchone()[0] == 3


def test_so_KHONG_that_khong_ghi():
    j = PaperTradingJournal(":memory:")
    assert j.ghi_ke_hoach(_dong()) is False
    assert j.db.execute("SELECT COUNT(*) FROM ke_hoach").fetchone()[0] == 0


def test_ghi_ke_hoach_chi_cham_bang_ke_hoach():
    cay = ast.parse((GOC / "paper_trading.py").read_text(encoding="utf-8"))
    ham = next(n for n in ast.walk(cay)
               if isinstance(n, ast.FunctionDef) and n.name == "ghi_ke_hoach")
    chuoi = " ".join(n.value for n in ast.walk(ham)
                     if isinstance(n, ast.Constant) and isinstance(n.value, str))
    assert "ke_hoach" in chuoi
    for bang in ("trades", "decisions", "nhat_ky"):
        assert bang not in chuoi, bang


# ───────────────────────── 3. Sheets: đẩy chỉ thêm, kéo không làm hỏng ─────────────────────────

def test_day_tao_tab_va_chi_them_dong_moi():
    j, b = _so_that(), ss.InMemorySheet()
    j.ghi_ke_hoach(_dong())
    bc = ss.push(j.db, b)
    assert bc["ke_hoach_moi"] == 1 and bc["ke_hoach_loi"] == ""
    assert b.read_rows(ss.TAB_KE_HOACH)[0] == list(ss.KE_HOACH_COLS)
    assert ss.push(j.db, b)["ke_hoach_moi"] == 0                  # đẩy lại: 0
    j.ghi_ke_hoach(_dong(ma="BBB"))
    assert ss.push(j.db, b)["ke_hoach_moi"] == 1
    assert len(b.read_rows(ss.TAB_KE_HOACH)) == 3


def test_dong_seq_NHO_chua_len_sheet_van_duoc_day():
    """Khoá là (mã, ngày), không phải mốc seq (bài học 14/08 của `decisions`)."""
    j, b = _so_that(), ss.InMemorySheet()
    j.ghi_ke_hoach(_dong(ma="AAA"))
    j.ghi_ke_hoach(_dong(ma="BBB"))
    ss.push(j.db, b)
    hang = b.read_rows(ss.TAB_KE_HOACH)
    b.write_all(ss.TAB_KE_HOACH, [hang[0], hang[2]])             # mất dòng seq 1 (AAA)
    assert ss.push(j.db, b)["ke_hoach_moi"] == 1
    ma = {r[ss.KE_HOACH_COLS.index("symbol")] for r in b.read_rows(ss.TAB_KE_HOACH)[1:]}
    assert ma == {"AAA", "BBB"}


def test_day_keo_mot_vong_khong_mat_gi_ke_ca_NULL():
    j, b = _so_that(), ss.InMemorySheet()
    j.ghi_ke_hoach(_dong())
    kh_rong = _kh(ngay=None, vung=None, phan_quyet="CHUA_LAP_DUOC",
                  day_xoay_ngay=None, day_xoay_gia=None, cat_lo_cau_truc=None)
    j.ghi_ke_hoach(skh.dong_tu_ke_hoach(kh_rong, "CCC", 63.0, 62.0, "UPCOM", "v",
                                        1.0, "2026-10-14"))
    ss.push(j.db, b)
    moi = _so_that()
    bc = ss.pull(moi.db, b)
    assert bc["ke_hoach"] == 2 and bc["ke_hoach_loi"] == ""
    cot = ", ".join(ss.KE_HOACH_COLS)
    assert (j.db.execute(f"SELECT {cot} FROM ke_hoach ORDER BY seq").fetchall()
            == moi.db.execute(f"SELECT {cot} FROM ke_hoach ORDER BY seq").fetchall())
    assert moi.db.execute("SELECT day_xoay_ngay FROM ke_hoach WHERE symbol='CCC'"
                          ).fetchone()[0] is None


def test_keo_khi_tab_VANG_cho_bang_rong_va_KHONG_tao_tab():
    b = ss.InMemorySheet()
    j = _so_that()
    bc = ss.pull(j.db, b)
    assert bc["ke_hoach"] == 0 and ss.TAB_KE_HOACH not in b.tabs


def test_keo_lai_KHONG_nhan_doi():
    j, b = _so_that(), ss.InMemorySheet()
    j.ghi_ke_hoach(_dong())
    ss.push(j.db, b)
    ss.pull(j.db, b, allow_overwrite=True)
    ss.pull(j.db, b, allow_overwrite=True)
    assert j.db.execute("SELECT COUNT(*) FROM ke_hoach").fetchone()[0] == 1


def test_tab_LECH_tieu_de_KHONG_lam_hong_keo_va_day_ba_tab_cu():
    j, b = _so_that(), ss.InMemorySheet()
    j.ghi_ke_hoach(_dong())
    b.write_all(ss.TAB_KE_HOACH, [["seq", "cot_la"], ["1", "x"]])
    bc = ss.push(j.db, b)
    assert bc["ke_hoach_loi"] and bc["ke_hoach_moi"] == 0
    assert b.read_rows(ss.TAB_TRADES)[0] == list(ss.TRADE_COLS)   # ba tab cũ đã đẩy
    moi = _so_that()
    bc2 = ss.pull(moi.db, b)
    assert bc2["ke_hoach_loi"] and bc2["ke_hoach"] == 0
    assert bc2["trades"] == 0                                       # lượt kéo đi trọn


# ───────────────────────── 4. run_daily: ghi sau run_session, không bao giờ ném ─────────────────────────

def _nen(n=40):
    ngay = [datetime(2026, 8, 3) + timedelta(days=i) for i in range(n * 2)]
    ngay = [d for d in ngay if d.weekday() < 5][:n]
    gia = [20.0 + 0.1 * i for i in range(n)]
    return pd.DataFrame({"time": [d.strftime("%Y-%m-%d") for d in ngay],
                         "open": gia, "high": [g + 0.4 for g in gia],
                         "low": [g - 0.6 for g in gia], "close": [g + 0.1 for g in gia],
                         "volume": [1_000_000.0] * n}), ngay[-1]


def test_ghi_cho_ma_DU_diem_ke_ca_DUNG_nguong_va_bo_ma_duoi_nguong():
    import run_daily as rd
    df, cuoi = _nen()
    bay_gio = cuoi.replace(hour=17)
    j = _so_that()
    assert rd.ghi_ke_hoach_tin_hieu(j, "AAA", df, BUY_THRESHOLD - 0.5, "HOSE", bay_gio,
                                    "2026-09-25")[0] == "duoi_nguong"
    assert rd.ghi_ke_hoach_tin_hieu(j, "AAA", df, None, "HOSE", bay_gio,
                                    "2026-09-25")[0] == "duoi_nguong"
    kq = rd.ghi_ke_hoach_tin_hieu(j, "AAA", df, float(BUY_THRESHOLD), "HOSE", bay_gio,
                                  "2026-09-25")
    assert kq[0] == "moi" and kq[1]
    assert rd.ghi_ke_hoach_tin_hieu(j, "AAA", df, 70.0, "HOSE", bay_gio,
                                    "2026-09-25")[0] == "trung"
    hang = j.db.execute("SELECT symbol, diem, nguong, phien_ban FROM ke_hoach").fetchall()
    assert len(hang) == 1 and hang[0][1] == float(BUY_THRESHOLD)
    import ke_hoach_vao_lenh as khvl
    assert hang[0][3] == khvl.PHIEN_BAN


def test_loi_khi_ghi_KHONG_nem_ra_luot_quet():
    import run_daily as rd
    df, cuoi = _nen()

    class SoHong:
        def ghi_ke_hoach(self, dong):
            raise RuntimeError("sổ hỏng giả")

    kq = rd.ghi_ke_hoach_tin_hieu(SoHong(), "AAA", df, 70.0, "HOSE",
                                  cuoi.replace(hour=17), "2026-09-25")
    assert kq[0] == "loi" and "sổ hỏng giả" in kq[1]


def _ham(cay, ten):
    return next(n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == ten)


def test_ast_ghi_ke_hoach_dung_SAU_run_session_trong_vong_quet():
    cay = ast.parse((GOC / "run_daily.py").read_text(encoding="utf-8"))
    ham = _ham(cay, "execute_daily_scan")
    dong = {}
    for n in ast.walk(ham):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
            dong.setdefault(n.func.id, []).append(n.lineno)
    assert len(dong["ghi_ke_hoach_tin_hieu"]) == 1 and len(dong["run_session"]) == 1
    assert dong["ghi_ke_hoach_tin_hieu"][0] > dong["run_session"][0]


def test_ast_ham_ghi_chi_goi_ghi_ke_hoach_tren_so_lenh():
    cay = ast.parse((GOC / "run_daily.py").read_text(encoding="utf-8"))
    ham = _ham(cay, "ghi_ke_hoach_tin_hieu")
    goi_so = {n.func.attr for n in ast.walk(ham)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
              and isinstance(n.func.value, ast.Name) and n.func.value.id == "journal"}
    assert goi_so == {"ghi_ke_hoach"}
