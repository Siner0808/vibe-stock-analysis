"""BƯỚC 272 — gác của bộ chỉnh THANG GIÁ lệnh đang mở (`chinh_thang_gia.py`, ĐO 35).

Tiêu chí KÝ TRƯỚC ở `docs/TIEU-CHI-DOC-TRUOC.md` mục `## ĐO 35`. File này giữ phần TỔNG HỢP (dựng tay) của
C5 · C7 · C8 · C9 · C11 và các gác chung; phần trên dữ liệu thật (C1–C4, C6, C9 thật, C11 thật) là
`tools/do35_chinh_thang_gia.py`. Tên test mang khoá tiêu chí (`test_C5_…`) để dụng cụ chọn bằng `-k`.

Số kỳ vọng là SỐ TÍNH TAY viết thẳng (phép tính ở chú thích), không dựng lại công thức của mã.
Khung giá tiêm: nghìn đồng, nhân hệ số cho MỌI nến TRƯỚC ngày giả định ngày giao dịch không hưởng quyền
(đúng cách nguồn điều chỉnh lùi); nến vào của lệnh dựng tay có `open` = giá vào ÷ f_giả.
"""
from __future__ import annotations

import ast
import dataclasses
import hashlib
import json
import pathlib
import re
import sqlite3
import sys

import pandas as pd
import pytest

GOC = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))
sys.path.insert(0, str(GOC))

import chinh_thang_gia as ct  # noqa: E402
import duyet_repo  # noqa: E402
import paper_trading as pt  # noqa: E402
from nhat_ky_vi_sao import COT_NHAT_KY  # noqa: E402
from paper_trading import PaperTradingJournal  # noqa: E402

MA = "XYZ"


# ─────────────────────────── dụng cụ dựng tay ───────────────────────────
def _so():
    return PaperTradingJournal(":memory:")


def _lenh(j, *, id=1, ma=MA, vao="2026-10-01", gia=30000.0, sl=28500.0, tp=36000.0,
          trang_thai="OPEN", size=5.0, ra=None, gia_ra=None, ly_do=None):
    j.db.execute(
        "INSERT INTO trades (id, symbol, signal_date, entry_date, entry_price, exit_date, exit_price,"
        " exit_reason, stop_loss, take_profit, size_pct, status)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (id, ma, vao, vao, gia, ra, gia_ra, ly_do, sl, tp, size, trang_thai))
    j.db.commit()


def _nhat_ky(j, trade_id=1, gia=30000.0, sl=28500.0, boi_canh=None):
    d = {c: None for c in COT_NHAT_KY}
    d.update(trade_id=trade_id, symbol=MA, entry_date="2026-10-01", entry_price=gia,
             stop_loss_ban_dau=sl, rui_ro_pct=(gia - sl) / gia * 100, diem_agent="{}", ly_do="[]",
             boi_canh=boi_canh)
    j.db.execute(f"INSERT INTO nhat_ky ({','.join(COT_NHAT_KY)}) VALUES ({','.join('?' * len(COT_NHAT_KY))})",
                 [d[c] for c in COT_NHAT_KY])
    j.db.commit()


def _khung(nen):
    """nen = [(ngày, mở, cao, thấp, đóng)] nghìn đồng -> DataFrame của một lượt quét."""
    return pd.DataFrame({"time": pd.to_datetime([n[0] for n in nen]),
                         "open": [n[1] for n in nen], "high": [n[2] for n in nen],
                         "low": [n[3] for n in nen], "close": [n[4] for n in nen],
                         "volume": [1_000_000.0] * len(nen)})


def _bam(j, bang="trades"):
    return hashlib.sha256(json.dumps([tuple(r) for r in j.db.execute(f"SELECT * FROM {bang} ORDER BY 1")],
                                     default=str).encode()).hexdigest()


def _chay(j, df, ngay="2026-10-20", san="HOSE", **kw):
    ra = []
    ev = ct.chinh_thang_mot_ma(j, MA, df, ngay, nguon="test", san=san, ghi=ra.append, **kw)
    return ev, ra


def _dong(j, id=1):
    return dict(j.db.execute("SELECT * FROM trades WHERE id=?", (id,)).fetchone())


def _nk(j, id=1):
    r = j.db.execute("SELECT * FROM nhat_ky WHERE trade_id=?", (id,)).fetchone()
    return None if r is None else dict(r)


def _khung_vao(f, gia_vao=30000.0, cao_nhan=1.01):
    """Hai nến: nến vào (mở = giá vào ÷ f, cao = mở × 1,01) và một nến sau."""
    mo = gia_vao / f / 1000.0
    return _khung([("2026-10-01", mo, mo * cao_nhan, mo * 0.99, mo),
                   ("2026-10-02", mo, mo * cao_nhan, mo * 0.99, mo)])


# ───────────────────────── L1–L3: đo f và chia ─────────────────────────
def test_L1_f_do_o_nen_VAO_va_ghi_nguoc_ba_cot_so_tinh_tay():
    # entry 30000, nến vào mở 20,0 nghìn = 20000 -> f = 30000/20000 = 1,5; cao = 20,2 -> 20200;
    # 30000 > 1,02 × 20200 = 20604 nên (b) đúng. Chia: 30000/1,5 = 20000; 28500/1,5 = 19000; 36000/1,5 = 24000.
    j = _so()
    _lenh(j)
    _nhat_ky(j)
    ev, log = _chay(j, _khung([("2026-10-01", 20.0, 20.2, 19.8, 20.0), ("2026-10-02", 20.0, 20.2, 19.8, 20.0)]))
    assert [e["trang_thai"] for e in ev] == [ct.CHINH]
    assert ev[0]["f"] == pytest.approx(1.5, rel=1e-12)
    d = _dong(j)
    assert d["entry_price"] == pytest.approx(20000.0, rel=1e-9)
    assert d["stop_loss"] == pytest.approx(19000.0, rel=1e-9)
    assert d["take_profit"] == pytest.approx(24000.0, rel=1e-9)
    assert d["size_pct"] == 5.0 and d["status"] == "OPEN"
    nk = _nk(j)
    assert nk["entry_price"] == pytest.approx(20000.0, rel=1e-9)
    assert nk["stop_loss_ban_dau"] == pytest.approx(19000.0, rel=1e-9)
    kh = json.loads(nk["boi_canh"])[ct.KHOA_NHAT_KY]
    assert kh == [{"ngay_quet": "2026-10-20", "f": pytest.approx(1.5, rel=1e-12),
                   "ngay_nen_vao": "2026-10-01", "nguon": "test"}]
    assert len(log) == 1 and "f = 1.5000" in log[0] and "#1" in log[0]


def test_L1_do_f_KHONG_phu_thuoc_gia_sau_ngay_vao():
    # Nến sau ngày vào rơi mạnh (đóng 10) không đổi f: chỉ nến VÀO được đo.
    j = _so()
    _lenh(j)
    df = _khung([("2026-10-01", 20.0, 20.2, 19.8, 20.0), ("2026-10-02", 12.0, 12.5, 10.0, 10.0)])
    ev, _ = _chay(j, df)
    assert ev[0]["f"] == pytest.approx(1.5, rel=1e-12)


def test_L2_hai_dieu_kien_deu_can_a_chi_dung_thi_khong_chinh():
    nen = {"2026-10-01": (100.0, 90.0, 110.0)}            # mở, thấp, cao
    assert ct.do_he_so(112.0, "2026-10-01", nen)["trang_thai"] == ct.KHOP_GIUA_PHIEN   # (a) đúng, (b) sai: 112 ≤ 112,2
    assert ct.do_he_so(113.0, "2026-10-01", nen)["trang_thai"] == ct.CHINH             # 113 > 112,2 và > 105
    # (b) đúng mà (a) sai: nến cao 100, mở 100, giá 104 (4% < 5%): không chỉnh
    assert ct.do_he_so(104.0, "2026-10-01", {"2026-10-01": (100.0, 99.0, 101.0)})["trang_thai"] == ct.BINH_THUONG


def test_L2_dung_5_phan_tram_KHONG_kich_hoat_va_chuc_chat():
    assert 1.05 * 100.0 == 105.0                      # phép tính tay: 105,00 đúng bằng ngưỡng dạng nhân
    nen = {"2026-10-01": (100.0, 99.0, 101.0)}
    assert ct.do_he_so(105.0, "2026-10-01", nen)["trang_thai"] == ct.BINH_THUONG
    assert ct.do_he_so(105.01, "2026-10-01", nen)["trang_thai"] == ct.CHINH


def test_L2_hang_so_dung_LAI_cua_nhan_su_kien_quyen_khong_gõ_lai():
    import su_kien_quyen as skq
    assert ct.NGUONG_LECH == skq.NGUONG_LECH == 0.05 and ct.NOI_BIEN == skq.NOI_BIEN == 0.02
    cay = ast.parse((GOC / "chinh_thang_gia.py").read_text(encoding="utf-8"))
    gan = {t.id: n.value for n in ast.walk(cay) if isinstance(n, ast.Assign)
           for t in n.targets if isinstance(t, ast.Name) and t.id in ("NGUONG_LECH", "NOI_BIEN")}
    assert all(isinstance(v, ast.Attribute) and v.value.id == "skq" for v in gan.values()), \
        "NGUONG_LECH / NOI_BIEN phải LẤY từ su_kien_quyen, không gõ lại số"


def test_L2_hinh_dang_so_sanh_dang_nhan_va_so_chat():
    """Gác phép SUY RA: điều kiện (a) và (b) có dạng `gia_vao > (1 + hằng) * <giá nến>` — kiểm HÌNH DẠNG biểu thức."""
    cay = ast.parse((GOC / "chinh_thang_gia.py").read_text(encoding="utf-8"))
    fn = next(n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == "do_he_so")
    dang = set()
    for n in ast.walk(fn):
        if isinstance(n, ast.Compare) and len(n.ops) == 1 and isinstance(n.ops[0], ast.Gt):
            if isinstance(n.left, ast.Name) and n.left.id == "gia_vao" and isinstance(n.comparators[0], ast.BinOp):
                b = n.comparators[0]
                if isinstance(b.op, ast.Mult) and isinstance(b.left, ast.BinOp) and isinstance(b.left.op, ast.Add):
                    dang.add((ast.unparse(b.left), ast.unparse(b.right)))
    assert dang == {("1 + NGUONG_LECH", "mo"), ("1 + NOI_BIEN", "cao")}, dang


# ───────────────────────── L6 ─────────────────────────
def test_L6_khong_co_nen_vao_khong_chinh_va_canh_bao():
    j = _so()
    _lenh(j)
    truoc = _bam(j)
    ev, log = _chay(j, _khung([("2026-10-02", 20.0, 20.2, 19.8, 20.0), ("2026-10-03", 20.0, 20.2, 19.8, 20.0)]))
    assert ev[0]["trang_thai"] == ct.KHONG_DO_DUOC and _bam(j) == truoc
    assert len(log) == 1 and log[0].startswith("##[warning]") and "2026-10-01" in log[0]


def test_L6_gia_nen_khong_phai_so_duong_la_khong_do_duoc():
    j = _so()
    _lenh(j)
    df = _khung([("2026-10-01", 0.0, 20.2, 19.8, 20.0), ("2026-10-02", 20.0, 20.2, 19.8, 20.0)])
    ev, log = _chay(j, df)
    assert ev[0]["trang_thai"] == ct.KHONG_DO_DUOC and len(log) == 1


def test_L6_nguon_cao_hon_so_khong_chinh_va_canh_bao():
    # entry 30000, nến vào mở 40 nghìn = 40000: f = 0,75 < 1/1,05 = 0,9524
    j = _so()
    _lenh(j)
    truoc = _bam(j)
    ev, log = _chay(j, _khung([("2026-10-01", 40.0, 40.4, 39.6, 40.0), ("2026-10-02", 40.0, 40.4, 39.6, 40.0)]))
    assert ev[0]["trang_thai"] == ct.NGUON_CAO_HON and _bam(j) == truoc
    assert len(log) == 1 and "##[warning]" in log[0]


def test_L6_binh_thuong_im_lang_khong_canh_bao():
    j = _so()
    _lenh(j)
    ev, log = _chay(j, _khung_vao(1.0))
    assert ev[0]["trang_thai"] == ct.BINH_THUONG and log == []


def test_L3_chi_OPEN_va_CLOSING_PENDING_va_CLOSED_giu_nguyen():
    j = _so()
    _lenh(j, id=1, trang_thai="OPEN")
    _lenh(j, id=2, trang_thai="CLOSING", ra="2026-10-05", ly_do="SIGNAL_REVERSED")
    _lenh(j, id=3, trang_thai="PENDING")
    _lenh(j, id=4, trang_thai="CLOSED", ra="2026-10-05", gia_ra=21000.0, ly_do="STOP_LOSS")
    cu = {i: _dong(j, i) for i in (3, 4)}
    ev, _ = _chay(j, _khung_vao(1.5))
    assert sorted(e["id"] for e in ev) == [1, 2]
    assert _dong(j, 1)["entry_price"] == pytest.approx(20000.0, rel=1e-9)
    assert _dong(j, 2)["entry_price"] == pytest.approx(20000.0, rel=1e-9)
    assert {i: _dong(j, i) for i in (3, 4)} == cu


def test_L3_lenh_khong_co_dong_nhat_ky_van_chinh_trades():
    j = _so()
    _lenh(j)
    ev, _ = _chay(j, _khung_vao(1.5))
    assert ev[0]["trang_thai"] == ct.CHINH and _nk(j) is None
    assert _dong(j)["stop_loss"] == pytest.approx(19000.0, rel=1e-9)


def test_L3_boi_canh_co_san_duoc_giu_va_lan_chinh_thu_hai_cong_don():
    j = _so()
    _lenh(j)
    _nhat_ky(j, boi_canh=json.dumps({"atr_pct": 2.0, "sharpe": 1.5}))
    _chay(j, _khung_vao(1.25))
    # sau lần 1 giá vào = 24000; nến vào nguồn nay mở 20,0: f = 1,2
    _chay(j, _khung([("2026-10-01", 20.0, 20.2, 19.8, 20.0), ("2026-10-02", 20.0, 20.2, 19.8, 20.0)]), ngay="2026-10-21")
    bc = json.loads(_nk(j)["boi_canh"])
    assert bc["atr_pct"] == 2.0 and bc["sharpe"] == 1.5
    assert [x["ngay_quet"] for x in bc[ct.KHOA_NHAT_KY]] == ["2026-10-20", "2026-10-21"]
    assert [round(x["f"], 9) for x in bc[ct.KHOA_NHAT_KY]] == [1.25, 1.2]


def test_L3_ghi_log_mot_dong_ma_id_f_nen_vao():
    j = _so()
    _lenh(j)
    _, log = _chay(j, _khung_vao(1.5))
    assert len(log) == 1 and MA in log[0] and "#1" in log[0] and "1.5000" in log[0] and "2026-10-01" in log[0]


# ───────────────────────── C5 ─────────────────────────
def _lenh_f(j, f):
    """Lệnh có giá vào = f × 20000, nến vào của nguồn mở ĐÚNG 20,0 nghìn (cao = mở × 1,01): f là hệ số DỰNG,
    nên "1,05 đúng" là đúng từng bit (1,05 × 20000 = 21000,0)."""
    gia = f * 20000.0
    _lenh(j, gia=gia, sl=gia * 0.95, tp=gia * 1.2)
    _nhat_ky(j, gia=gia, sl=gia * 0.95)
    return gia


_KHUNG_MO_20 = [("2026-10-01", 20.0, 20.2, 19.8, 20.0), ("2026-10-02", 20.0, 20.2, 19.8, 20.0)]


@pytest.mark.parametrize("f", [0.951, 0.97, 0.99, 1.00, 1.001, 1.02, 1.03, 1.049, 1.05])
def test_C5_he_so_nho_hoac_dung_nguong_0_dong_doi(f):
    # f = 1,05 ĐÚNG: giá vào = 21000,0 = 1,05 × mở. f = 0,951 < 1/1,05: không chỉnh, chỉ `##[warning]`.
    assert 1.05 * 20000.0 == 21000.0
    j = _so()
    _lenh_f(j, f)
    t0, n0 = _bam(j, "trades"), _bam(j, "nhat_ky")
    ev, _ = _chay(j, _khung(_KHUNG_MO_20))
    assert _bam(j, "trades") == t0 and _bam(j, "nhat_ky") == n0
    assert ev[0]["trang_thai"] == (ct.NGUON_CAO_HON if f == 0.951 else ct.BINH_THUONG)


@pytest.mark.parametrize("f", [1.0501, 1.10, 1.3125, 1.50, 2.00])
def test_C5_he_so_lon_chia_dung_ba_cot_va_nhat_ky(f):
    j = _so()
    gia = _lenh_f(j, f)
    _chay(j, _khung(_KHUNG_MO_20))
    d, nk = _dong(j), _nk(j)
    for cot, cu in (("entry_price", gia), ("stop_loss", gia * 0.95), ("take_profit", gia * 1.2)):
        assert abs(d[cot] / (cu / f) - 1) <= 1e-9, (cot, f)
    assert abs(nk["entry_price"] / (gia / f) - 1) <= 1e-9
    assert abs(nk["stop_loss_ban_dau"] / (gia * 0.95 / f) - 1) <= 1e-9
    assert ct.KHOA_NHAT_KY in json.loads(nk["boi_canh"])
    assert d["entry_price"] == pytest.approx(20000.0, rel=1e-9)          # = mở của nến vào


@pytest.mark.parametrize("gia_khop", [90.0, 93.0, 95.0, 96.0, 100.0, 105.0, 106.0, 112.0])
def test_C5_khop_theo_vung_giua_phien_khong_phai_su_kien_0_dong_doi(gia_khop):
    # Nến vào mở 100, thấp 90, cao 110. 106 > 105 nhưng ≤ 1,02 × 110 = 112,2: không đủ (b); 112 cũng vậy.
    j = _so()
    _lenh(j, gia=gia_khop, sl=gia_khop * 0.95, tp=gia_khop * 1.2)
    _nhat_ky(j, gia=gia_khop, sl=gia_khop * 0.95)
    t0, n0 = _bam(j, "trades"), _bam(j, "nhat_ky")
    # khung ở nghìn đồng: 0,100 ... nhân 1000 -> mở 100, thấp 90, cao 110 (VNĐ)
    df = _khung([("2026-10-01", 0.100, 0.110, 0.090, 0.100), ("2026-10-02", 0.100, 0.110, 0.090, 0.100)])
    ev, log = _chay(j, df)
    assert _bam(j, "trades") == t0 and _bam(j, "nhat_ky") == n0 and ev[0]["trang_thai"] != ct.CHINH, \
        (gia_khop, ev[0]["trang_thai"], log)


def test_C5_gia_khop_113_ngoai_than_nen_cong_2_phan_tram_KICH_HOAT_dung_thiet_ke():
    """113 > 1,02 × 110 = 112,2 và lớn hơn mở 13%: hình dạng MỘT sự kiện. Nhãn *"kích hoạt đúng như thiết kế,
    không phân biệt được với sự kiện thật"* — khớp vùng ngoài thân nến là điều đường thật không làm."""
    j = _so()
    _lenh(j, gia=113.0, sl=107.35, tp=135.6)
    df = _khung([("2026-10-01", 0.100, 0.110, 0.090, 0.100), ("2026-10-02", 0.100, 0.110, 0.090, 0.100)])
    ev, _ = _chay(j, df)
    assert ev[0]["trang_thai"] == ct.CHINH
    assert _dong(j)["entry_price"] == pytest.approx(100.0, rel=1e-9)     # 113 ÷ 1,13


# ───────────────────────── C7 ─────────────────────────
def test_C7a_chay_hai_lan_tren_cung_mot_luot_lan_hai_0_o_doi():
    j = _so()
    _lenh(j)
    _nhat_ky(j)
    df = _khung_vao(1.5)
    _chay(j, df)
    t1, n1 = _bam(j, "trades"), _bam(j, "nhat_ky")
    ev, log = _chay(j, df)
    assert _bam(j, "trades") == t1 and _bam(j, "nhat_ky") == n1
    assert ev[0]["trang_thai"] == ct.BINH_THUONG and log == []


def test_C7b_hai_su_kien_lien_tiep_gia_so_bang_goc_chia_f1_nhan_f2():
    # Gốc: giá vào 30000, cắt lỗ 28500, chốt lời 36000. Lần 1 f1 = 1,25: nến vào mở 30000/1,25 = 24000;
    # sổ -> 24000 · 22800 · 28800. Lần 2 f2 = 1,20: nến vào mở 24000/1,2 = 20000; sổ -> 20000 · 19000 · 24000
    # (= gốc ÷ 1,5: 30000/1,5 = 20000; 28500/1,5 = 19000; 36000/1,5 = 24000).
    j = _so()
    _lenh(j)
    _nhat_ky(j)
    _chay(j, _khung([("2026-10-01", 24.0, 24.24, 23.76, 24.0), ("2026-10-02", 24.0, 24.24, 23.76, 24.0)]))
    d = _dong(j)
    assert (round(d["entry_price"], 6), round(d["stop_loss"], 6), round(d["take_profit"], 6)) == (24000.0, 22800.0, 28800.0)
    _chay(j, _khung([("2026-10-01", 20.0, 20.2, 19.8, 20.0), ("2026-10-02", 20.0, 20.2, 19.8, 20.0)]), ngay="2026-10-21")
    d = _dong(j)
    assert d["entry_price"] == pytest.approx(20000.0, rel=1e-9)
    assert d["stop_loss"] == pytest.approx(19000.0, rel=1e-9)
    assert d["take_profit"] == pytest.approx(24000.0, rel=1e-9)
    nk = _nk(j)
    assert nk["entry_price"] == pytest.approx(20000.0, rel=1e-9)
    assert nk["stop_loss_ban_dau"] == pytest.approx(19000.0, rel=1e-9)


def _nen_lai(nen, he_so, den):
    """Khung nguồn SAU điều chỉnh: mọi nến TRƯỚC `den` chia `he_so` (giá thấp đi); nến từ `den` giữ nguyên."""
    ra = []
    for d, o, h, l, c in nen:
        k = he_so if d < den else 1.0
        ra.append((d, o / k, h / k, l / k, c / k))
    return ra


def test_C7c_lenh_CLOSING_cung_duoc_chinh_va_khop_ra_o_gia_mo_thang_moi_khong_vuot_bien_nen():
    # Lệnh CLOSING (tín hiệu ra 05/10) giá vào 30000. Nguồn đã điều chỉnh ×1,5: nến vào mở 20,0 -> sổ vào 20000.
    # Nến 06/10 (thang mới) mở 20,4 thấp 20,1 cao 20,9: khớp ra ở 20400 -> lợi nhuận gộp 20400/20000 − 1 = +2%,
    # nằm trong [20100/20000 − 1 = +0,5% ; 20900/20000 − 1 = +4,5%].
    j = _so()
    _lenh(j, trang_thai="CLOSING", ra="2026-10-05", ly_do="SIGNAL_REVERSED")
    df = _khung([("2026-10-01", 20.0, 20.2, 19.8, 20.0), ("2026-10-05", 20.3, 20.6, 20.0, 20.3),
                 ("2026-10-06", 20.4, 20.9, 20.1, 20.5)])
    ev, _ = _chay(j, df, ngay="2026-10-06")
    assert ev[0]["trang_thai"] == ct.CHINH
    assert j.fill_closing(MA, "2026-10-06", 20400.0, None) == 1
    d = _dong(j)
    ret = d["exit_price"] / d["entry_price"] - 1
    assert d["exit_price"] == pytest.approx(20400.0) and ret == pytest.approx(0.02, rel=1e-9)
    assert 20100.0 / 20000.0 - 1 <= ret <= 20900.0 / 20000.0 - 1


def test_C7d_khong_chia_hai_lan_trailing_truoc_va_sau_ngay_gia_dinh_so_tinh_tay():
    """Lệnh OPEN vắt qua ngày giả định (f = 1,50, ngày 08/10), quét 5 lượt, trailing nâng giữa các lượt.

    Gốc: vào 30000 (01/10), cắt lỗ 28500, chốt lời 36000. Điểm 70 (không thoát theo tín hiệu).
    L1 (02/10, thang cũ): cao 32000 ≥ 1,05 × 30000 = 31500 và cắt lỗ 28500 < 30000 → về hoà vốn 30000;
        trail 0,93 × 31000 = 28830 < 30000 → cắt lỗ 30000.
    L2 (05/10, thang cũ): thấp 30500 > 30000; 0,93 × 32000 = 29760 < 30000 → giữ 30000.
    L3 (08/10, nguồn ĐÃ điều chỉnh ÷1,5): f = 30000 / 20000 = 1,5 → giá vào 20000 · cắt lỗ 30000/1,5 = 20000 ·
        chốt lời 36000/1,5 = 24000. Nến 08/10 thấp 20800 > 20000; cao 22000 ≥ 21000 nhưng cắt lỗ = giá vào nên không
        hoà vốn; 0,93 × 21500 = 19995 < 20000 → giữ 20000.
    L4 (09/10): 0,93 × 23000 = 21390 > 20000 → cắt lỗ 21390.
    L5 (12/10): 0,93 × 23200 = 21576 > 21390 → cắt lỗ 21576. f ở L4, L5 = 1 → không chia thêm.
    """
    j = _so()
    _lenh(j)
    goc = [("2026-10-01", 30.0, 30.4, 29.6, 30.0), ("2026-10-02", 30.2, 32.0, 29.8, 31.0),
           ("2026-10-05", 31.0, 33.0, 30.5, 32.0), ("2026-10-08", 31.5, 33.0, 31.2, 32.25),
           ("2026-10-09", 22.0, 24.0, 21.8, 23.0), ("2026-10-12", 23.0, 23.5, 22.5, 23.2)]
    moi = {"2026-10-08": (21.0, 22.0, 20.8, 21.5)}                  # nến 08/10 thang mới
    theo_luot = []
    for k, d in enumerate(("2026-10-02", "2026-10-05", "2026-10-08", "2026-10-09", "2026-10-12")):
        nen = [n for n in goc if n[0] <= d]
        if d >= "2026-10-08":                                       # nguồn đã điều chỉnh: nến < 08/10 chia 1,5
            nen = _nen_lai(nen, 1.5, "2026-10-08")
            nen = [(x[0],) + moi[x[0]] if x[0] in moi else x for x in nen]
        df = _khung(nen)
        _chay(j, df, ngay=d)
        r = df.iloc[-1]
        mult = 1000.0
        j.evaluate_open(MA, d, {"open": r["open"] * mult, "high": r["high"] * mult, "low": r["low"] * mult,
                                "close": r["close"] * mult, "volume": 1e6}, current_score=70)
        theo_luot.append(_dong(j))
    sl = [x["stop_loss"] for x in theo_luot]
    assert sl[0] == pytest.approx(30000.0, rel=1e-9) and sl[1] == pytest.approx(30000.0, rel=1e-9)
    assert sl[2] == pytest.approx(20000.0, rel=1e-9)
    assert sl[3] == pytest.approx(21390.0, rel=1e-9)
    assert sl[4] == pytest.approx(21576.0, rel=1e-9)
    cuoi = theo_luot[-1]
    assert cuoi["status"] == "OPEN"
    assert cuoi["entry_price"] == pytest.approx(20000.0, rel=1e-9)         # chia ĐÚNG MỘT lần
    assert cuoi["take_profit"] == pytest.approx(24000.0, rel=1e-9)


def test_C7e_nguyen_tu_loi_giua_hai_cap_nhat_trades_va_nhat_ky_giong_het_truoc_luot(monkeypatch):
    j = _so()
    _lenh(j)
    _nhat_ky(j, boi_canh=json.dumps({"atr_pct": 2.0}))
    t0, n0 = _bam(j, "trades"), _bam(j, "nhat_ky")

    def hong(*a, **k):
        raise RuntimeError("lỗi chèn giữa hai cập nhật")
    monkeypatch.setattr(ct, "_cap_nhat_nhat_ky", hong)
    ev, log = _chay(j, _khung_vao(1.5))
    assert _bam(j, "trades") == t0 and _bam(j, "nhat_ky") == n0
    assert "RuntimeError" in ev[0]["loi"] and len(log) == 1 and log[0].startswith("##[warning]")
    assert not j.db.in_transaction


def test_C7e_boi_canh_khong_phai_json_cung_hoan_tac_ca_hai():
    j = _so()
    _lenh(j)
    _nhat_ky(j, boi_canh="khong phai json")
    t0, n0 = _bam(j, "trades"), _bam(j, "nhat_ky")
    ev, _ = _chay(j, _khung_vao(1.5))
    assert _bam(j, "trades") == t0 and _bam(j, "nhat_ky") == n0 and ev[0]["loi"]


# ───────────────────────── C8 ─────────────────────────
def _cot_real_cua_ddl(ddl: str) -> list[str]:
    ra = []
    for dong in ddl.splitlines():
        for m in re.finditer(r"(\w+)\s+REAL\b", dong):
            ra.append(m.group(1))
    return ra


def _ddl_trades() -> str:
    """Chuỗi DDL của bảng `trades` đọc bằng AST từ `paper_trading.py` (không đọc `in` trên chữ)."""
    cay = ast.parse((GOC / "paper_trading.py").read_text(encoding="utf-8"))
    for n in ast.walk(cay):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and "CREATE TABLE IF NOT EXISTS trades" in n.value:
            dau = n.value.index("CREATE TABLE IF NOT EXISTS trades")
            return n.value[dau:n.value.index(");", dau)]          # CHỈ bảng trades (cùng chuỗi có cả `decisions`)
    raise AssertionError("không thấy DDL bảng trades")


def test_C8_moi_cot_REAL_cua_DDL_trades_da_duoc_bo_chinh_khai():
    cot = _cot_real_cua_ddl(_ddl_trades())
    assert set(cot) >= {"entry_price", "exit_price", "stop_loss", "take_profit"}
    assert ct.cot_gia_chua_khai(cot) == [], ct.cot_gia_chua_khai(cot)


def test_C8_them_mot_cot_gia_moi_vao_DDL_ma_khong_khai_thi_gac_DO():
    mutated = _ddl_trades().replace("take_profit REAL,", "take_profit REAL, gia_moi REAL,")
    assert "gia_moi REAL" in mutated
    assert ct.cot_gia_chua_khai(_cot_real_cua_ddl(mutated)) == ["gia_moi"]


def test_C8_cap_nhat_trades_cham_dung_cac_cot_COT_GIA_CHINH_bang_AST():
    cay = ast.parse((GOC / "chinh_thang_gia.py").read_text(encoding="utf-8"))
    fn = next(n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == "_cap_nhat_trades")
    sql = [n.value for n in ast.walk(fn) if isinstance(n, ast.Constant) and isinstance(n.value, str)
           and n.value.lstrip().startswith("UPDATE trades")]
    assert len(sql) == 1
    dat = set(re.findall(r"(\w+)=\?", sql[0].split("WHERE")[0]))
    assert dat == set(ct.COT_GIA_CHINH)
    assert not (set(ct.COT_GIA_CHINH) & set(ct.COT_GIA_CHI_GHI_LUC_RA))


def test_C8_khong_cham_gi_ngoai_L3_bam_tung_dong_va_danh_sach_cot():
    j = _so()
    _lenh(j, id=1)                                                                 # OPEN, sẽ chỉnh
    _lenh(j, id=2, ma="ABC", trang_thai="CLOSED", ra="2026-10-05", gia_ra=21000.0, ly_do="STOP_LOSS")
    _nhat_ky(j, trade_id=1)
    _nhat_ky(j, trade_id=2)
    j.record_decision(MA, "2026-10-01", {"final_score": 60, "recommendation": "MUA"}, False, "x")
    j.db.execute("INSERT INTO ke_hoach (seq, symbol, signal_date) VALUES (1, 'XYZ', '2026-10-01')")
    j.db.commit()
    cot = {b: [r[1] for r in j.db.execute(f"PRAGMA table_info({b})")] for b in ("trades", "nhat_ky")}
    giu = {"dong2": _dong(j, 2), "nk2": _nk(j, 2),
           "decisions": _bam(j, "decisions"), "ke_hoach": _bam(j, "ke_hoach")}
    _chay(j, _khung_vao(1.5))
    assert _dong(j, 1)["entry_price"] == pytest.approx(20000.0, rel=1e-9)         # có chỉnh thật
    assert {"dong2": _dong(j, 2), "nk2": _nk(j, 2),
            "decisions": _bam(j, "decisions"), "ke_hoach": _bam(j, "ke_hoach")} == giu
    assert {b: [r[1] for r in j.db.execute(f"PRAGMA table_info({b})")] for b in ("trades", "nhat_ky")} == cot


# ───────────────────────── C9 ─────────────────────────
def test_C9_cu_roi_ngoai_bien_do_san_voi_f_chua_vao_khung_dung_MOT_canh_bao_0_o_doi():
    # Nến vào và nến 02/10 cùng thang cao (đóng 100 nghìn... ở đây 30,0); nến 05/10 cao 26,0 thấp 25,0 đóng 25,5.
    # HOSE biên 7%: ngưỡng = 30,0 × 0,93 × 0,98 = 27,342 > cao 26,0 → "chưa điều chỉnh". Nến vào: f = 1 (không chỉnh).
    j = _so()
    _lenh(j)
    _nhat_ky(j)
    t0, n0 = _bam(j, "trades"), _bam(j, "nhat_ky")
    df = _khung([("2026-10-01", 30.0, 30.3, 29.7, 30.0), ("2026-10-02", 30.0, 30.3, 29.7, 30.0),
                 ("2026-10-05", 26.0, 26.0, 25.0, 25.5)])
    ev, log = _chay(j, df, ngay="2026-10-05")
    w = [x for x in log if x.startswith("##[warning]")]
    assert len(w) == 1 and "chưa điều chỉnh" in w[0] and "2026-10-05" in w[0]
    assert _bam(j, "trades") == t0 and _bam(j, "nhat_ky") == n0
    assert ev[0]["trang_thai"] == ct.BINH_THUONG


def test_C9_cu_roi_trong_bien_do_san_khong_bao():
    j = _so()
    _lenh(j)
    df = _khung([("2026-10-01", 30.0, 30.3, 29.7, 30.0), ("2026-10-02", 30.0, 30.3, 29.7, 30.0),
                 ("2026-10-05", 28.5, 28.6, 27.9, 28.0)])   # cao 28,6 ≥ 27,342
    _, log = _chay(j, df, ngay="2026-10-05")
    assert log == []


def test_C9_bien_nguong_do_nen_cao_nhat_chu_khong_phai_thap_va_co_noi_2_phan_tram():
    # Đóng phiên trước 100 (nghìn): ngưỡng HOSE = 100 × 0,93 × 0,98 = 91,14. Cao 92 ≥ 91,14 -> KHÔNG báo (nếu bỏ nới
    # 2% thì ngưỡng 93 và 92 bị báo); cao 91 < 91,14 -> báo. Thấp rất sâu nhưng CAO còn trên ngưỡng -> không báo
    # (cú rơi trong biên độ vẫn có thể chạm thấp 85): điều kiện là CAO, không phải thấp.
    def khung(cao, thap):
        return _khung([("2026-10-01", 100.0, 100.0, 99.0, 100.0), ("2026-10-02", 95.0, cao, thap, 93.0)])
    assert ct.may_do_chua_dieu_chinh(khung(92.0, 85.0), 1.0, "HOSE", "2026-10-02") == []
    assert [d["ngay"] for d in ct.may_do_chua_dieu_chinh(khung(91.0, 85.0), 1.0, "HOSE", "2026-10-02")] == ["2026-10-02"]
    d = ct.may_do_chua_dieu_chinh(khung(91.0, 85.0), 1.0, "HOSE", "2026-10-02")[0]
    assert d["nguong"] == pytest.approx(91.14, rel=1e-12) and d["bien"] == 0.07
    # HNX biên 10%: ngưỡng 100 × 0,90 × 0,98 = 88,2
    assert ct.may_do_chua_dieu_chinh(khung(89.0, 80.0), 1.0, "HNX", "2026-10-02") == []
    assert len(ct.may_do_chua_dieu_chinh(khung(88.0, 80.0), 1.0, "HNX", "2026-10-02")) == 1


def test_C2_nhan_f_la_tham_so_do_do_nhay_chia_cho_f_nhan_nhan_f():
    # f đo = 1,5; × 0,98 = 1,47 -> 30000/1,47 = 20408,163…; × 1,02 = 1,53 -> 30000/1,53 = 19607,843…
    for nhan, ky_vong in ((0.98, 30000.0 / 1.47), (1.02, 30000.0 / 1.53), (1.0, 20000.0)):
        j = _so()
        _lenh(j)
        _chay(j, _khung_vao(1.5), nhan_f=nhan)
        assert _dong(j)["entry_price"] == pytest.approx(ky_vong, rel=1e-12), nhan
    assert 30000.0 / 1.47 == pytest.approx(20408.163265306, rel=1e-9)        # số tính tay


def test_C9_san_khong_ro_thi_khong_do_va_chi_do_nen_cuoi():
    df = _khung([("2026-10-01", 30.0, 30.3, 29.7, 30.0), ("2026-10-02", 20.0, 20.0, 19.0, 19.5),
                 ("2026-10-05", 19.5, 19.6, 19.0, 19.2)])
    assert ct.may_do_chua_dieu_chinh(df, 1000.0, "KHONG_CO", "2026-10-01") == []
    assert [d["ngay"] for d in ct.may_do_chua_dieu_chinh(df, 1000.0, "HOSE", "2026-10-01")] == ["2026-10-02"]
    assert ct.may_do_chua_dieu_chinh(df, 1000.0, "HOSE", "2026-10-05") == []   # chỉ nến cuối: không quét lại nến cũ
    assert ct.may_do_chua_dieu_chinh(df, 1000.0, "HOSE", "2026-10-01", "2026-10-01") == []


# ───────────────────────── C11 ─────────────────────────
def _ra_thang_moi(j, df_vao, tuyen):
    """Dựng lệnh vắt qua ngày giả định (f = 1,5), chỉnh, rồi cho `tuyen(j)` đưa lệnh tới lối ra."""
    _chay(j, df_vao, ngay="2026-10-08")
    return tuyen(j)


def _gioi_han(dfs, vao):
    """[thấp nhỏ nhất × (1 − NOI_BIEN) ÷ vào − 1 ; cao lớn nhất × (1 + NOI_BIEN) ÷ vào − 1] — dạng nhân của `kiem_lenh`."""
    thap = min(float(x) for d in dfs for x in d["low"]) * 1000.0
    cao = max(float(x) for d in dfs for x in d["high"]) * 1000.0
    return thap * 0.98 / vao - 1, cao * 1.02 / vao - 1


def test_C11_chot_loi_cung_ra_o_chot_loi_thang_moi_khong_nhay_thang():
    # Nguồn ÷1,5: nến vào mở 20,0 -> giá vào 20000, chốt lời 24000. Nến 09/10 cao 24,5 ≥ 24000: ra ở 24000, +20%.
    j = _so()
    _lenh(j)
    df = _khung([("2026-10-01", 20.0, 20.2, 19.8, 20.0), ("2026-10-08", 21.0, 22.0, 20.8, 21.5),
                 ("2026-10-09", 23.0, 24.5, 22.8, 24.0)])
    _chay(j, df, ngay="2026-10-09")
    cau = dataclasses.replace(pt.CauHinhVao.tu_module(), chot_loi_cung=True)
    j.evaluate_open(MA, "2026-10-09", {"open": 23000.0, "high": 24500.0, "low": 22800.0, "close": 24000.0,
                                        "volume": 0}, current_score=70, cau_hinh=cau)
    d = _dong(j)
    assert (d["exit_reason"], d["exit_price"]) == ("TAKE_PROFIT", pytest.approx(24000.0, rel=1e-9))
    vao = d["entry_price"]
    lo, hi = _gioi_han([df], vao)
    ret = d["exit_price"] / vao - 1
    assert ret == pytest.approx(0.2, rel=1e-9)
    assert lo <= ret <= hi                                # trong biên đã nới NOI_BIEN
    # đối chứng của chính máy đo: cùng phép với giá vào CHƯA chỉnh (30000) phải VƯỢT biên (−20%)
    ret_cu = d["exit_price"] / 30000.0 - 1
    assert not (lo <= ret_cu <= hi)


def test_C11_SIGNAL_REVERSED_qua_fill_closing_ra_o_gia_mo_thang_moi():
    # Giá vào đã chỉnh 20000; nến 09/10 đóng 19900 < giá vào (không lãi) và điểm 30 < 45 → CLOSING; nến 12/10 mở 19600
    # → khớp 19600 (không trượt: không có nến khớp): ret = 19600/20000 − 1 = −2%. Biên từ ba nến: thấp nhỏ nhất 19300,
    # cao lớn nhất 20300 → [19300×0,98/20000−1 = −5,4% ; 20300×1,02/20000−1 = +3,5%]; giá vào CHƯA chỉnh: −34,7%.
    j = _so()
    _lenh(j)
    df1 = _khung([("2026-10-01", 20.0, 20.2, 19.8, 20.0), ("2026-10-09", 20.2, 20.3, 19.7, 19.9)])
    _chay(j, df1, ngay="2026-10-09")
    j.evaluate_open(MA, "2026-10-09", {"open": 20200.0, "high": 20300.0, "low": 19700.0, "close": 19900.0,
                                        "volume": 0}, current_score=30)
    assert _dong(j)["status"] == "CLOSING"
    assert j.fill_closing(MA, "2026-10-12", 19600.0, None) == 1
    d = _dong(j)
    assert d["exit_reason"] == "SIGNAL_REVERSED" and d["exit_price"] == pytest.approx(19600.0)
    ret = d["exit_price"] / d["entry_price"] - 1
    assert ret == pytest.approx(-0.02, rel=1e-9)
    lo, hi = _gioi_han([df1, _khung([("2026-10-12", 19.6, 19.9, 19.3, 19.5)])], 20000.0)
    assert lo <= ret <= hi
    assert not (lo <= 19600.0 / 30000.0 - 1 <= hi)                       # đối chứng: giá vào CHƯA chỉnh


def test_C11_tran_thoi_gian_MAX_HOLD_ra_o_gia_mo_thang_moi():
    # Vào 05/01/2026 giá 30000; nguồn ÷1,5 (nến vào mở 20,0). Quét 10/04/2026: 95 ngày × 5/7 = 67 ≥ 60 → MAX_HOLD
    # (CLOSING) → khớp nến 13/04 mở 20300: ret = 20300/20000 − 1 = +1,5%.
    j = _so()
    _lenh(j, vao="2026-01-05")
    df = _khung([("2026-01-05", 20.0, 20.2, 19.8, 20.0), ("2026-04-10", 20.4, 20.6, 20.1, 20.5)])
    _chay(j, df, ngay="2026-04-10")
    j.evaluate_open(MA, "2026-04-10", {"open": 20400.0, "high": 20600.0, "low": 20100.0, "close": 20500.0,
                                        "volume": 0}, current_score=70)
    assert _dong(j)["status"] == "CLOSING" and _dong(j)["exit_reason"] == "MAX_HOLD"
    j.fill_closing(MA, "2026-04-13", 20300.0, None)
    d = _dong(j)
    ret = d["exit_price"] / d["entry_price"] - 1
    assert ret == pytest.approx(0.015, rel=1e-9)
    lo, hi = _gioi_han([df], 20000.0)
    assert lo <= ret <= hi


def test_C11_dong_nhat_ky_ra_gia_co_hai_so_cung_thang_nhan_gap_khong_nham():
    """Lệnh ra bình thường ở thang mới: `hau_kiem_may` KHÔNG có nhãn gap/trượt giá (so hai số CÙNG thang)."""
    j = _so()
    _lenh(j)
    _nhat_ky(j)
    _chay(j, _khung([("2026-10-01", 20.0, 20.2, 19.8, 20.0), ("2026-10-09", 20.2, 20.3, 19.7, 19.9)]),
          ngay="2026-10-09")
    nk = _nk(j)
    assert nk["entry_price"] == pytest.approx(20000.0, rel=1e-9)
    assert nk["stop_loss_ban_dau"] == pytest.approx(19000.0, rel=1e-9)
    j.db.execute("UPDATE trades SET status='CLOSED', exit_date='2026-10-12', exit_price=19600.0,"
                 " exit_reason='SIGNAL_REVERSED' WHERE id=1")
    j.db.commit()
    assert j.hoan_tat_nhat_ky(None) == 1
    hk = _nk(j)["hau_kiem_may"]
    assert "gap" not in hk
    # đối chứng: nếu nhật ký KHÔNG được chia (hai số khác thang) thì nhãn gap xuất hiện — máy đo không mù
    j2 = _so()
    _lenh(j2, vao="2026-10-01", gia=20000.0, sl=19000.0, tp=24000.0, trang_thai="CLOSED", ra="2026-10-12",
          gia_ra=19600.0, ly_do="SIGNAL_REVERSED")
    _nhat_ky(j2, gia=30000.0, sl=28500.0)
    j2.hoan_tat_nhat_ky(None)
    assert "gap" in _nk(j2)["hau_kiem_may"]


# ───────────────────────── gác chung ─────────────────────────
def _nhap(cay):
    ra = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            ra |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            ra.add(n.module.split(".")[0])
    return ra


def _ma_nguon():
    bo = {"tests", ".venv", ".git", "node_modules", "__pycache__"}
    return [p for p in duyet_repo.duyet(GOC, "*.py") if not (set(p.relative_to(GOC).parts) & bo)]


def test_gac_chi_dung_cu_nhap_bo_chinh_walkforward_va_loi_giao_dich_KHONG():
    ai = {p.relative_to(GOC).as_posix() for p in _ma_nguon()
          if "chinh_thang_gia" in _nhap(ast.parse(p.read_text(encoding="utf-8")))}
    assert ai == {"tools/do35_chinh_thang_gia.py"}, sorted(ai)    # BƯỚC 272: đường thật TẮT, chỉ dụng cụ đo nhập
    for ten in ("paper_trading.py", "paper_runner.py", "paper_metrics.py", "walkforward.py", "sheets_store.py",
                "google_sheets_sync.py", "master_agent.py", "san_dau.py", "nhat_ky_vi_sao.py"):
        assert "chinh_thang_gia" not in _nhap(ast.parse((GOC / ten).read_text(encoding="utf-8"))), ten
    bt = [p for p in duyet_repo.duyet(GOC / "backtest", "*.py")
          if "chinh_thang_gia" in _nhap(ast.parse(p.read_text(encoding="utf-8")))]
    assert not bt, bt


def test_gac_tham_so_nhan_f_chi_dung_cho_dung_cu_do_khong_den_tay_duong_that():
    for p in _ma_nguon():
        if p.name == "chinh_thang_gia.py":
            continue
        cay = ast.parse(p.read_text(encoding="utf-8"))
        for n in ast.walk(cay):
            if isinstance(n, ast.Call) and getattr(n.func, "attr", getattr(n.func, "id", "")) == "chinh_thang_mot_ma":
                ten = {k.arg for k in n.keywords}
                if "nhan_f" in ten:
                    assert p.as_posix().endswith("tools/do35_chinh_thang_gia.py"), p


def test_gac_ham_chinh_khong_goi_mang_khong_doc_lich_su_kien_khong_import_nen_giao_dich():
    nhap = _nhap(ast.parse((GOC / "chinh_thang_gia.py").read_text(encoding="utf-8")))
    assert not ({"requests", "urllib", "vnstock", "vnstock_data", "gspread", "sheets_store",
                 "google_sheets_sync", "do26_nguong_su_kien_quyen", "nen_su_kien_quyen"} & nhap), nhap


def test_duong_that_TAT_khong_co_nguoi_goi_bo_chinh_trong_duong_quet():
    """ĐO 35 kết cục K0 (BƯỚC 272): bộ chỉnh vào repo nhưng KHÔNG chạy trên đường thật. "Tắt" = không ai gọi
    `chinh_thang_mot_ma` ngoài dụng cụ đo và test; đổi dòng này là bật đường thật, có chủ đích, sau một ĐO kết cục A."""
    goi = set()
    for p in _ma_nguon():
        cay = ast.parse(p.read_text(encoding="utf-8"))
        if any(isinstance(n, ast.Call) and getattr(n.func, "attr", getattr(n.func, "id", "")) == "chinh_thang_mot_ma"
               for n in ast.walk(cay)):
            goi.add(p.relative_to(GOC).as_posix())
    assert goi - {"chinh_thang_gia.py"} == {"tools/do35_chinh_thang_gia.py"}, sorted(goi)
    assert "chinh_thang_gia" not in _nhap(ast.parse((GOC / "run_daily.py").read_text(encoding="utf-8")))
    assert not hasattr(ct, "BAT_TRONG_DUONG_THAT")        # không có cờ chết
