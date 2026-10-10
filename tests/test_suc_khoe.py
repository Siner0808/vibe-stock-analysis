"""Gác BẢNG SỨC KHOẺ HỆ THỐNG — `suc_khoe.py`, `tools/suc_khoe.py`, tab «🩺 Sức khoẻ» (BƯỚC 177, B4).

Bốn tầng:

  1. DANH MỤC khớp công cụ thật: tệp/hàm TỒN TẠI (AST), mỗi câu `bang_chung` có THẬT
     trong file công cụ và phủ đúng các mã thoát của bảng, mỗi dấu hiệu là câu CÓ THẬT
     (ba dấu của chuông nguồn đứng sinh từ hằng của `lich_giao_dich`, nên so với hằng),
     VANG chỉ có khi công cụ tự khai.
  2. ÁNH XẠ mã thoát -> trạng thái bằng subprocess GIẢ (monkeypatch): 0/1/2/lạ/hết giờ/
     ngoại lệ. Luật cứng: CHUA_KIEM_DUOC KHÔNG BAO GIỜ thành XANH — kiểm trên MỌI phép
     × MỌI mã thoát. Cộng đối chứng THẬT: đầu ra mà chính công cụ sinh ra (chạy `main`
     của chúng với mạng/sổ giả) đi qua phép phán và ra đúng trạng thái.
  3. CHỈ ĐỌC + TUẦN TỰ: môi trường tiến trình con, tệp không đổi sau một lượt chạy thật,
     không có `ThreadPool`/`concurrent`, `kiem_lan_luot` đúng hình dạng.
  4. DÂY NỐI: không đường giao dịch/chấm điểm/dữ liệu nào nhập `suc_khoe`; app chạy kiểm
     CHỈ trong nhánh của nút bấm.
"""
import ast
import importlib.util
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from urllib.error import URLError

import pytest

GOC = Path(__file__).resolve().parent.parent
# `tools/` có file cùng tên module gốc `suc_khoe.py` (như `ban_tin`): các test khác
# đặt `tools/` lên ĐẦU sys.path, nên GOC phải được đặt lên trước khi nhập.
sys.path.insert(0, str(GOC))

import lich_giao_dich as lg  # noqa: E402
import suc_khoe as sk  # noqa: E402

assert Path(sk.__file__).resolve() == GOC / "suc_khoe.py", (
    f"nhập nhầm {sk.__file__}: đó là CLI trong tools/, không phải module gốc")

TEN_CAN_CO = {"chuong_bao_quet", "chuong_nguon_dung", "canh_cong_c5", "chuong_bai_hoc",
              "so_ban_goi", "kiem_goi", "market_status", "kiem_cua_song",
              "kiem_duong_ngoai_repo", "soat_tuan"}


def _nap_tool(ten):
    spec = importlib.util.spec_from_file_location(f"{ten}_tool", GOC / "tools" / f"{ten}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _cay(duong):
    return ast.parse((GOC / duong).read_text(encoding="utf-8"))


def _ten_nhap(cay):
    """Tên module gốc mà một cây AST nhập (Import / ImportFrom)."""
    ra = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            ra |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            ra.add(n.module.split(".")[0])
    return ra


def _phep_tep():
    return [p for p in sk.DANH_MUC if p.tep is not None]


def _gia(ma, dau_ra=""):
    """Một `subprocess.run` giả trả mã thoát + đầu ra cho trước."""
    def run(*a, **kw):
        return SimpleNamespace(returncode=ma, stdout=dau_ra, stderr="")
    return run


@pytest.fixture
def khong_dieu_kien(monkeypatch):
    """Mọi điều kiện tiên quyết đạt — để thử ánh xạ mã thoát trên máy bất kỳ."""
    for ten in list(sk.DIEU_KIEN):
        monkeypatch.setitem(sk.DIEU_KIEN, ten, lambda: None)


# ─── 1. DANH MỤC khớp công cụ thật ───────────────────────────────────

def test_danh_muc_du_muoi_phep_theo_de_bai_va_ten_khong_trung():
    ten = [p.ten for p in sk.DANH_MUC]
    assert len(ten) == len(set(ten)), "tên phép trùng"
    assert set(ten) == TEN_CAN_CO, set(ten) ^ TEN_CAN_CO
    assert set(sk.THEO_TEN) == set(ten)


def test_moi_phep_la_tep_hoac_ham_ton_tai_that_doc_bang_AST():
    for p in sk.DANH_MUC:
        if p.tep is not None:
            assert (GOC / p.tep).is_file(), p.tep
            assert p.tep.startswith("tools/")
        else:
            mod, ham = p.ham
            cay = _cay(f"{mod}.py")
            ten_ham = {n.name for n in cay.body if isinstance(n, ast.FunctionDef)}
            assert ham in ten_ham, f"{mod}.{ham} không phải hàm mức module"


def test_phep_phai_co_dung_mot_cach_chay_va_trang_thai_hop_le():
    with pytest.raises(ValueError, match="ĐÚNG MỘT"):
        sk.PhepKiem(ten="x", mo_ta="x")
    with pytest.raises(ValueError, match="ĐÚNG MỘT"):
        sk.PhepKiem(ten="x", mo_ta="x", tep="tools/a.py", ham=("m", "f"))
    with pytest.raises(ValueError, match="trạng thái lạ"):
        sk.PhepKiem(ten="x", mo_ta="x", tep="tools/a.py", ma_thoat=((0, "XANH_LA"),))
    with pytest.raises(ValueError, match="điều kiện lạ"):
        sk.PhepKiem(ten="x", mo_ta="x", tep="tools/a.py", dieu_kien=("khong_co",))


def test_bang_chung_la_chu_CO_THAT_trong_file_cong_cu_va_phu_dung_cac_ma_thoat():
    for p in sk.DANH_MUC:
        file_ct = p.tep if p.tep is not None else f"{p.ham[0]}.py"
        van = (GOC / file_ct).read_text(encoding="utf-8")
        assert p.bang_chung, f"{p.ten}: chưa trích chữ nào của công cụ"
        for nhan, cau in p.bang_chung:
            assert cau in van, f"{p.ten}: câu trích không có trong {file_ct}: {cau!r}"
        if p.tep is not None:
            ma_duoc_trich = {nhan for nhan, _ in p.bang_chung}
            ma_trong_bang = {m for m, _ in p.ma_thoat}
            assert ma_trong_bang <= ma_duoc_trich, (
                f"{p.ten}: mã {ma_trong_bang - ma_duoc_trich} có trong bảng mà chưa trích")


def test_dau_hieu_la_cau_CO_THAT_cua_cong_cu():
    # Ba dấu của chuông nguồn đứng là `f"[{trang_thai}] ..."` nên không có nguyên văn
    # trong file: so với hằng của `lich_giao_dich`, đúng chỗ chúng sinh ra.
    sinh_ra = {"[NGUON_DUNG]": f"[{lg.NGUON_DUNG}]", "[BANG_SAI]": f"[{lg.BANG_SAI}]",
               "[CHUA_BIET]": f"[{lg.CHUA_BIET}]"}
    for p in sk.DANH_MUC:
        if p.tep is None:
            continue
        van = (GOC / p.tep).read_text(encoding="utf-8")
        for _, chuoi, _ in p.dau_hieu:
            if chuoi in sinh_ra:
                assert chuoi == sinh_ra[chuoi]
                assert "f\"[{trang_thai}] {thong_diep}\"" in van
            else:
                assert chuoi in van, f"{p.ten}: dấu hiệu không có trong công cụ: {chuoi!r}"


def test_VANG_chi_co_khi_cong_cu_tu_khai_canh_bao():
    co_vang = [p for p in sk.DANH_MUC
               if any(t == sk.VANG for _, t in p.ma_thoat)
               or any(t == sk.VANG for _, _, t in p.dau_hieu)]
    assert {p.ten for p in co_vang} == {"so_ban_goi", "soat_tuan"}
    for p in co_vang:
        assert p.chung_vang, p.ten
        assert p.chung_vang in (GOC / p.tep).read_text(encoding="utf-8"), p.ten
    with pytest.raises(ValueError, match="chung_vang"):
        sk.PhepKiem(ten="x", mo_ta="x", tep="tools/a.py", ma_thoat=((1, sk.VANG),))


def test_cac_ma_thoat_cua_bang_khop_cau_cua_cong_cu_da_doc():
    """Từng mã đã đọc, từng nhãn: bảng KHÔNG được khai khác chữ của công cụ."""
    bang = {p.ten: dict(p.ma_thoat) for p in _phep_tep()}
    assert bang["chuong_bai_hoc"] == {0: sk.XANH, 1: sk.DO, 2: sk.CHUA_KIEM_DUOC}
    assert bang["kiem_cua_song"] == {0: sk.XANH, 1: sk.DO, 2: sk.CHUA_KIEM_DUOC}
    assert bang["kiem_duong_ngoai_repo"] == {0: sk.XANH, 1: sk.DO, 2: sk.CHUA_KIEM_DUOC}
    assert bang["so_ban_goi"] == {0: sk.XANH, 1: sk.VANG, 2: sk.CHUA_KIEM_DUOC}
    assert bang["soat_tuan"] == {0: sk.XANH, 2: sk.CHUA_KIEM_DUOC}
    for ten in ("chuong_bao_quet", "chuong_nguon_dung", "canh_cong_c5"):
        assert bang[ten] == {0: sk.XANH, 1: sk.DO}, ten
        assert sk.THEO_TEN[ten].ma_can_dau_hieu == (1,), ten
    # Chuông bài học tự khai ba hằng MA_* — bảng phải bằng chúng.
    t = _nap_tool("chuong_bai_hoc")
    assert (t.MA_XANH, t.MA_VI_PHAM, t.MA_CHUA_KIEM_DUOC) == (0, 1, 2)


# ─── 2. ÁNH XẠ mã thoát -> trạng thái (subprocess giả) ───────────────

@pytest.mark.parametrize("phep", _phep_tep(), ids=lambda p: p.ten)
def test_moi_ma_thoat_trong_bang_ra_dung_trang_thai_khi_dau_ra_trung(
        phep, monkeypatch, khong_dieu_kien):
    monkeypatch.setattr(sk.subprocess, "run", _gia(0, "mọi thứ bình thường"))
    for ma, mong in phep.ma_thoat:
        if ma in phep.ma_can_dau_hieu:
            continue                                    # mã mơ hồ: xem test riêng
        monkeypatch.setattr(sk.subprocess, "run", _gia(ma, "dòng trung tính"))
        kq = sk.kiem_mot(phep)
        assert kq.trang_thai == mong, (phep.ten, ma, kq)


@pytest.mark.parametrize("phep", _phep_tep(), ids=lambda p: p.ten)
def test_CHUA_KIEM_DUOC_khong_bao_gio_thanh_XANH_tren_moi_ma_thoat(
        phep, monkeypatch, khong_dieu_kien):
    """XANH chỉ ra khi bảng của công cụ khai XANH cho mã ấy; mọi mã khác thì KHÔNG."""
    bang = dict(phep.ma_thoat)
    for ma in (-15, -9, -1, 0, 1, 2, 3, 4, 7, 99, 126, 127, 255):
        for dau_ra in ("", "xanh xanh", "Traceback (most recent call last)\nboom"):
            monkeypatch.setattr(sk.subprocess, "run", _gia(ma, dau_ra))
            kq = sk.kiem_mot(phep)
            if kq.trang_thai == sk.XANH:
                assert bang.get(ma) == sk.XANH, (phep.ten, ma, dau_ra)
                assert ma == 0 or sk.DAU_NO not in dau_ra   # mã 0 là lời công cụ tự khai


@pytest.mark.parametrize("phep", _phep_tep(), ids=lambda p: p.ten)
def test_ma_la_la_CHUA_KIEM_DUOC_kem_ly_do(phep, monkeypatch, khong_dieu_kien):
    la = next(m for m in (5, 6, 8, 9) if m not in dict(phep.ma_thoat))
    monkeypatch.setattr(sk.subprocess, "run", _gia(la, "ok ok"))
    kq = sk.kiem_mot(phep)
    assert kq.trang_thai == sk.CHUA_KIEM_DUOC
    assert "lạ" in kq.ly_do and str(la) in kq.ly_do


@pytest.mark.parametrize("phep", _phep_tep(), ids=lambda p: p.ten)
def test_het_gio_va_ngoai_le_la_CHUA_KIEM_DUOC_khong_ném(phep, monkeypatch, khong_dieu_kien):
    def het_gio(*a, **kw):
        raise subprocess.TimeoutExpired(cmd="x", timeout=kw["timeout"])

    monkeypatch.setattr(sk.subprocess, "run", het_gio)
    kq = sk.kiem_mot(phep)
    assert kq.trang_thai == sk.CHUA_KIEM_DUOC and "hết giờ" in kq.ly_do
    assert str(phep.timeout_giay) in kq.ly_do

    for loi in (FileNotFoundError("gh"), PermissionError("x"), OSError("disk"),
                RuntimeError("bất ngờ")):
        def hong(*a, _l=loi, **kw):
            raise _l
        monkeypatch.setattr(sk.subprocess, "run", hong)
        kq = sk.kiem_mot(phep)
        assert kq.trang_thai == sk.CHUA_KIEM_DUOC, (phep.ten, loi)
        assert type(loi).__name__ in kq.ly_do


@pytest.mark.parametrize("phep", _phep_tep(), ids=lambda p: p.ten)
def test_traceback_voi_ma_khac_0_la_CHUA_KIEM_DUOC_ke_ca_khi_ma_1_nghe_nhu_DO(
        phep, monkeypatch, khong_dieu_kien):
    """Ngoại lệ chưa bắt của Python thoát 1 — lẫn với "đã kêu". Không được thành DO."""
    ra = ("Traceback (most recent call last):\n  File \"x.py\", line 1\n"
          "ModuleNotFoundError: No module named 'vnstock'")
    # Cố tình kèm CẢ dấu hiệu DO của công cụ: Traceback vẫn thắng.
    dau_do = [c for _, c, t in phep.dau_hieu if t == sk.DO]
    for ma in (1, 2):
        monkeypatch.setattr(sk.subprocess, "run", _gia(ma, ra + "\n" + " ".join(dau_do)))
        kq = sk.kiem_mot(phep)
        assert kq.trang_thai == sk.CHUA_KIEM_DUOC, (phep.ten, ma, kq)
        assert "ngoại lệ" in kq.ly_do


@pytest.mark.parametrize("ten", ["chuong_bao_quet", "chuong_nguon_dung", "canh_cong_c5"])
def test_ma_1_cua_ba_chuong_chi_la_DO_khi_dau_ra_mang_cau_bao_kêu(
        ten, monkeypatch, khong_dieu_kien):
    phep = sk.THEO_TEN[ten]
    monkeypatch.setattr(sk.subprocess, "run", _gia(1, "đầu ra chẳng liên quan"))
    kq = sk.kiem_mot(phep)
    assert kq.trang_thai == sk.CHUA_KIEM_DUOC and "gộp nhiều chuyện" in kq.ly_do
    for _, chuoi, tt in phep.dau_hieu:
        monkeypatch.setattr(sk.subprocess, "run", _gia(1, f"a\n::error::{chuoi} ...\nb"))
        assert sk.kiem_mot(phep).trang_thai == tt, (ten, chuoi)


def test_DO_thang_CHUA_khi_dau_ra_mang_ca_hai_dau_hieu_cua_canh_cong_c5(
        monkeypatch, khong_dieu_kien):
    phep = sk.THEO_TEN["canh_cong_c5"]
    ra = "CHUÔNG C5 KHÔNG ĐO ĐƯỢC — x\nCỔNG C5 RÒ RỈ: 2 quyết định"
    monkeypatch.setattr(sk.subprocess, "run", _gia(1, ra))
    assert sk.kiem_mot(phep).trang_thai == sk.DO


def test_soat_tuan_VANG_chi_khi_dau_ra_co_warning_va_ma_0(monkeypatch, khong_dieu_kien):
    phep = sk.THEO_TEN["soat_tuan"]
    monkeypatch.setattr(sk.subprocess, "run", _gia(0, "### Soát tuần\nxong"))
    assert sk.kiem_mot(phep).trang_thai == sk.XANH
    monkeypatch.setattr(sk.subprocess, "run",
                        _gia(0, "### Soát tuần\n::warning title=Soát tuần — quá nhịp::x"))
    assert sk.kiem_mot(phep).trang_thai == sk.VANG
    # có warning mà mã 2 (máy hỏng) thì KHÔNG được vàng
    monkeypatch.setattr(sk.subprocess, "run", _gia(2, "::warning title=x::y"))
    assert sk.kiem_mot(phep).trang_thai == sk.CHUA_KIEM_DUOC


def test_so_ban_goi_ma_1_la_VANG_khong_phai_DO(monkeypatch, khong_dieu_kien):
    monkeypatch.setattr(sk.subprocess, "run", _gia(1, "CÓ chạm chỗ quyết định."))
    assert sk.kiem_mot(sk.THEO_TEN["so_ban_goi"]).trang_thai == sk.VANG


def test_stdout_none_hoac_bytes_khong_lam_no_va_khong_ra_XANH_tu_dau_ra_hong(
        monkeypatch, khong_dieu_kien):
    phep = sk.THEO_TEN["chuong_bai_hoc"]
    for rac in (None, b"bytes", 123):
        monkeypatch.setattr(sk.subprocess, "run",
                            lambda *a, _r=rac, **kw: SimpleNamespace(returncode=1, stdout=_r))
        assert sk.kiem_mot(phep).trang_thai == sk.DO       # mã 1 của chuông bài học = vi phạm
    monkeypatch.setattr(sk.subprocess, "run",
                        lambda *a, **kw: SimpleNamespace(returncode=None, stdout="x"))
    assert sk.kiem_mot(phep).trang_thai == sk.CHUA_KIEM_DUOC


# ─── điều kiện tiên quyết ────────────────────────────────────────────

def test_dieu_kien_khong_dat_la_CHUA_KIEM_DUOC_va_khong_chay_tien_trinh(monkeypatch):
    def cam(*a, **kw):
        raise AssertionError("không được chạy tiến trình khi điều kiện chưa đạt")

    monkeypatch.setattr(sk.subprocess, "run", cam)
    monkeypatch.setitem(sk.DIEU_KIEN, "may_phat_trien", lambda: "ở Cloud, không phải máy")
    for ten in ("kiem_cua_song", "kiem_duong_ngoai_repo"):
        kq = sk.kiem_mot(sk.THEO_TEN[ten])
        assert kq.trang_thai == sk.CHUA_KIEM_DUOC and "ở Cloud" in kq.ly_do
        assert kq.chi_tiet == (kq.ly_do,), "lý do phải HIỆN, không ẩn"
    monkeypatch.setitem(sk.DIEU_KIEN, "gh", lambda: "không có gh")
    assert sk.kiem_mot(sk.THEO_TEN["so_ban_goi"]).ly_do == "không có gh"
    monkeypatch.setitem(sk.DIEU_KIEN, "cache_vnindex", lambda: "chưa có cache")
    for ten in ("canh_cong_c5", "market_status"):
        assert sk.kiem_mot(sk.THEO_TEN[ten]).ly_do == "chưa có cache"


def test_dieu_kien_may_phat_trien_doc_venv_va_bien_ep(monkeypatch, tmp_path):
    monkeypatch.setattr(sk, "GOC", tmp_path)
    monkeypatch.delenv(sk.BIEN_MAY, raising=False)
    assert sk.dk_may_phat_trien() and "máy phát triển" in sk.dk_may_phat_trien()
    (tmp_path / ".venv").mkdir()
    assert sk.dk_may_phat_trien() is None
    monkeypatch.setenv(sk.BIEN_MAY, "0")
    assert "bỏ qua" in sk.dk_may_phat_trien()
    (tmp_path / ".venv").rmdir()
    monkeypatch.setenv(sk.BIEN_MAY, "1")
    assert sk.dk_may_phat_trien() is None


def test_dieu_kien_gh_theo_PATH(monkeypatch):
    monkeypatch.setattr(sk.shutil, "which", lambda ten: None)
    assert "gh" in sk.dk_co_gh()
    monkeypatch.setattr(sk.shutil, "which", lambda ten: "/usr/bin/gh")
    assert sk.dk_co_gh() is None


def test_dieu_kien_cache_vnindex_khong_co_thi_tu_choi_khong_di_ghi(monkeypatch):
    from backtest import data as btd
    monkeypatch.setattr(btd, "load", lambda ten: None)
    assert "GHI" in sk.dk_cache_vnindex()
    import pandas as pd
    monkeypatch.setattr(btd, "load", lambda ten: pd.DataFrame({"time": []}))
    assert "GHI" in sk.dk_cache_vnindex()
    monkeypatch.setattr(btd, "load", lambda ten: pd.DataFrame({"time": ["2026-10-09"]}))
    assert sk.dk_cache_vnindex() is None

    def no(ten):
        raise OSError("hỏng")
    monkeypatch.setattr(btd, "load", no)
    assert "OSError" in sk.dk_cache_vnindex()


# ─── hàm Python: kiem_goi, status ────────────────────────────────────

def test_danh_gia_kiem_goi_ba_nhan_cua_chinh_vnstock_goi():
    import vnstock_goi as vg
    assert sk.danh_gia_kiem_goi(vg.TrangThaiGoi(tinh_trang=vg.KHOP))[0] == sk.XANH
    assert sk.danh_gia_kiem_goi(vg.TrangThaiGoi(tinh_trang=vg.LECH))[0] == sk.DO
    tt, ly = sk.danh_gia_kiem_goi(vg.TrangThaiGoi(tinh_trang=vg.CHUA_KIEM_DUOC,
                                                  ly_do="mất mạng"))
    assert tt == sk.CHUA_KIEM_DUOC and ly == "mất mạng"
    for la in (SimpleNamespace(tinh_trang="LẠ"), SimpleNamespace(), None, "KHỚP"):
        assert sk.danh_gia_kiem_goi(la)[0] == sk.CHUA_KIEM_DUOC, la


def test_danh_gia_status_active_quá_hạn_va_khong_do_duoc():
    assert sk.danh_gia_status({"active": True, "note": "ok", "rows": 9})[0] == sk.XANH
    tt, ly = sk.danh_gia_status({"active": False, "ngay_cuoi": "2026-09-01",
                                 "tuoi_phien": 20, "note": "QUÁ HẠN"})
    assert tt == sk.DO and "quá hạn" in ly
    assert sk.danh_gia_status({"active": False, "rows": 0, "note": "KHÔNG có dữ liệu"})[0] \
        == sk.CHUA_KIEM_DUOC
    assert sk.danh_gia_status({"active": False, "note": "chưa nạp"})[0] == sk.CHUA_KIEM_DUOC
    for rac in (None, [], "active", {}, {"active": "True"}, {"active": 1}):
        assert sk.danh_gia_status(rac)[0] == sk.CHUA_KIEM_DUOC, rac


def test_ham_kiem_goi_chay_qua_kiem_mot_va_loi_thanh_CHUA(monkeypatch):
    import vnstock_goi as vg
    phep = sk.THEO_TEN["kiem_goi"]
    goi = []

    def gia(*, dung_cache):
        goi.append(dung_cache)
        return vg.TrangThaiGoi(tinh_trang=vg.KHOP, hang_may_chu="silver", hang_cuc_bo="silver")

    monkeypatch.setattr(vg, "kiem_goi", gia)
    kq = sk.kiem_mot(phep)
    assert kq.trang_thai == sk.XANH and goi == [False], "phải bỏ bộ nhớ đệm 30 phút"
    assert kq.chi_tiet and "silver" in kq.chi_tiet[0]

    def no(**kw):
        raise ConnectionError("rớt mạng")
    monkeypatch.setattr(vg, "kiem_goi", no)
    kq = sk.kiem_mot(phep)
    assert kq.trang_thai == sk.CHUA_KIEM_DUOC and "ConnectionError" in kq.ly_do


def test_market_status_xoa_bo_nho_dem_truoc_khi_hoi_de_doc_lai_cache_tren_dia(
        monkeypatch, khong_dieu_kien):
    """`get_vni_df` là lru_cache: không xoá thì bấm nút lần hai trả lại bản nạp CŨ."""
    import market_filter as mf
    nhat_ky = []
    gia = SimpleNamespace(cache_clear=lambda: nhat_ky.append("xoa"))
    monkeypatch.setattr(mf, "get_vni_df", gia)
    monkeypatch.setattr(mf, "status", lambda: nhat_ky.append("hoi") or {"active": True})
    assert sk.kiem_mot(sk.THEO_TEN["market_status"]).trang_thai == sk.XANH
    assert nhat_ky == ["xoa", "hoi"]


def test_ham_market_status_qua_kiem_mot(monkeypatch, khong_dieu_kien):
    import market_filter as mf
    phep = sk.THEO_TEN["market_status"]
    monkeypatch.setattr(mf, "status", lambda: {"active": True, "note": "VN-INDEX ok"})
    assert sk.kiem_mot(phep).trang_thai == sk.XANH
    monkeypatch.setattr(mf, "status", lambda: {"active": False, "ngay_cuoi": "2026-08-01",
                                               "note": "VN-INDEX QUÁ HẠN"})
    kq = sk.kiem_mot(phep)
    assert kq.trang_thai == sk.DO and kq.chi_tiet == ("VN-INDEX QUÁ HẠN",)

    def no():
        raise ValueError("hỏng")
    monkeypatch.setattr(mf, "status", no)
    assert sk.kiem_mot(phep).trang_thai == sk.CHUA_KIEM_DUOC


# ─── ĐỐI CHỨNG THẬT: đầu ra do CHÍNH công cụ sinh ra ─────────────────

def _chay_main(mod, capsys, *a, **kw):
    ma = mod.main(*a, **kw)
    return ma, capsys.readouterr().out


def _phan(ten, ma, ra):
    return sk.danh_gia_ma_thoat(sk.THEO_TEN[ten], ma, ra)[0]


def test_THAT_chuong_bao_quet_ba_nhanh_dau_ra_di_qua_phep_phan(monkeypatch, capsys):
    import datetime as dt
    t = _nap_tool("chuong_bao_quet")
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    def hong(*a, **kw):
        raise URLError("không có mạng")
    monkeypatch.setattr(t, "_tai_cac_luot", hong)
    ma, ra = _chay_main(t, capsys)
    assert ma == 1 and _phan("chuong_bao_quet", ma, ra) == sk.CHUA_KIEM_DUOC

    monkeypatch.setattr(t, "_tai_cac_luot", lambda *a, **kw: [])
    ma, ra = _chay_main(t, capsys)
    assert ma == 1 and _phan("chuong_bao_quet", ma, ra) == sk.DO

    hom_nay = dt.datetime.now(dt.timezone.utc).date()
    luot = [{"conclusion": "success", "created_at": f"{n}T03:00:00Z"}
            for n in t.cac_ngay_lam_viec(hom_nay)]
    monkeypatch.setattr(t, "_tai_cac_luot", lambda *a, **kw: luot)
    ma, ra = _chay_main(t, capsys)
    assert ma == 0 and _phan("chuong_bao_quet", ma, ra) == sk.XANH


def test_THAT_chuong_nguon_dung_cac_trang_thai_cua_lich_di_qua_phep_phan(monkeypatch, capsys):
    t = _nap_tool("chuong_nguon_dung")
    monkeypatch.setattr(t, "nen_moi_nhat_tu_mang", lambda: "2026-10-09")
    mong = {lg.OK: sk.XANH, lg.NGUON_DUNG: sk.DO, lg.BANG_SAI: sk.DO,
            lg.CHUA_BIET: sk.CHUA_KIEM_DUOC}
    for tt, ket in mong.items():
        monkeypatch.setattr(t.lg, "chan_doan", lambda nen, hom, _t=tt: (_t, f"thông điệp {_t}"))
        ma, ra = _chay_main(t, capsys)
        assert _phan("chuong_nguon_dung", ma, ra) == ket, (tt, ma, ra)


def test_THAT_chuong_nguon_dung_keo_hong_hoac_rong_la_CHUA(monkeypatch, capsys):
    import market_filter as mf
    t = _nap_tool("chuong_nguon_dung")

    def hong(*a, **kw):
        raise OSError("DNS")
    monkeypatch.setattr(mf._btd, "fetch_one", hong)
    ma, ra = _chay_main(t, capsys)
    assert ma == 1 and _phan("chuong_nguon_dung", ma, ra) == sk.CHUA_KIEM_DUOC
    monkeypatch.setattr(mf._btd, "fetch_one", lambda *a, **kw: None)
    ma, ra = _chay_main(t, capsys)
    assert ma == 1 and _phan("chuong_nguon_dung", ma, ra) == sk.CHUA_KIEM_DUOC


def test_THAT_canh_cong_c5_thong_diep_that_di_qua_phep_phan(monkeypatch, capsys, tmp_path):
    import google_sheets_sync as gs
    import paper_metrics
    import paper_trading as pt
    t = _nap_tool("canh_cong_c5")
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    monkeypatch.setattr(t, "ro_chuan", lambda trades: None)

    # (a) kho ngoài chưa cấu hình
    monkeypatch.setattr(gs, "keo_so_co_thu_lai", lambda *a, **kw: None)
    ma, ra = _chay_main(t, capsys)
    assert ma == 1 and _phan("canh_cong_c5", ma, ra) == sk.CHUA_KIEM_DUOC
    # (b) kéo hỏng
    def hong(*a, **kw):
        raise gs.KeoSoThatBai("hết lần")
    monkeypatch.setattr(gs, "keo_so_co_thu_lai", hong)
    ma, ra = _chay_main(t, capsys)
    assert ma == 1 and _phan("canh_cong_c5", ma, ra) == sk.CHUA_KIEM_DUOC
    # kéo được: sổ rỗng trong DB tạm
    monkeypatch.setattr(gs, "keo_so_co_thu_lai",
                        lambda *a, **kw: {"trades": 0, "decisions": 0})
    # (c) không đo được
    monkeypatch.setattr(paper_metrics, "dieu_kien_dong_lai",
                        lambda *a, **kw: {"do_duoc": False, "ly_do": "thiếu lệnh"})
    ma, ra = _chay_main(t, capsys)
    assert ma == 1 and _phan("canh_cong_c5", ma, ra) == sk.CHUA_KIEM_DUOC
    # (d) điều kiện đạt mà cổng còn mở
    monkeypatch.setattr(pt, "CHO_PHEP_MO_LENH_MOI", True)
    monkeypatch.setattr(paper_metrics, "dieu_kien_dong_lai",
                        lambda *a, **kw: {"do_duoc": True, "dat": True, "ly_do": "alpha < 0"})
    ma, ra = _chay_main(t, capsys)
    assert ma == 1 and _phan("canh_cong_c5", ma, ra) == sk.DO
    # (e) điều kiện chưa đạt, cổng mở: yên
    monkeypatch.setattr(paper_metrics, "dieu_kien_dong_lai",
                        lambda *a, **kw: {"do_duoc": True, "dat": False, "ly_do": "chưa đủ mẫu"})
    ma, ra = _chay_main(t, capsys)
    assert ma == 0 and _phan("canh_cong_c5", ma, ra) == sk.XANH


def test_THAT_canh_cong_c5_cau_ro_ri_cua_kiem_ro_ri_mang_dau_hieu():
    t = _nap_tool("canh_cong_c5")
    ma, cau = t.kiem_ro_ri([{"acted": 1, "at": 5.0, "symbol": "AAA"}], False, 1.0, "2026-10-01")
    assert ma == 1
    assert _phan("canh_cong_c5", ma, f"::error::{cau}") == sk.DO


def test_THAT_chuong_bai_hoc_ba_ma_thoat_cua_chinh_no(monkeypatch, capsys):
    t = _nap_tool("chuong_bai_hoc")
    monkeypatch.setattr(t, "doc_so", lambda *a, **kw: (None, [], []))
    ma, ra = _chay_main(t, capsys, hom_nay="2026-10-09")
    assert ma == 2 and _phan("chuong_bai_hoc", ma, ra) == sk.CHUA_KIEM_DUOC

    def no(*a, **kw):
        raise RuntimeError("bất ngờ")
    monkeypatch.setattr(t, "doc_so", no)
    ma, ra = _chay_main(t, capsys, hom_nay="2026-10-09")
    assert ma == 2 and "Traceback" not in ra       # chính nó bắt hết -> mã 2, không phải nổ
    assert _phan("chuong_bai_hoc", ma, ra) == sk.CHUA_KIEM_DUOC

    monkeypatch.setattr(t, "doc_so", lambda *a, **kw: ({"trades": 0}, [], []))
    ma, ra = _chay_main(t, capsys, hom_nay="2026-10-09")
    assert ma == 0 and _phan("chuong_bai_hoc", ma, ra) == sk.XANH


def test_THAT_kiem_cua_song_khong_doc_duoc_la_ma_2_va_CHUA(monkeypatch, capsys):
    t = _nap_tool("kiem_cua_song")
    monkeypatch.setattr(t, "_doc", lambda duong: None)
    monkeypatch.setattr(sys, "argv", ["kiem_cua_song.py"])
    ma, ra = _chay_main(t, capsys)
    assert ma == 2 and _phan("kiem_cua_song", ma, ra) == sk.CHUA_KIEM_DUOC
    khai = {"hooks": {"Stop": [{"matcher": "", "hooks": [
        {"type": "command", "command": 'python "x/tools/a.py"'}]}]}}
    monkeypatch.setattr(t, "_doc", lambda duong: khai if "cua-du-an" in str(duong) else {})
    ma, ra = _chay_main(t, capsys)
    assert ma == 1 and _phan("kiem_cua_song", ma, ra) == sk.DO
    monkeypatch.setattr(t, "_doc", lambda duong: khai)
    ma, ra = _chay_main(t, capsys)
    assert ma == 0 and _phan("kiem_cua_song", ma, ra) == sk.XANH


def test_THAT_soat_tuan_canh_bao_that_mang_dau_hieu_VANG():
    t = _nap_tool("soat_tuan")
    kq = {"chua_mo": [("f.md", 1, "câu", None)], "so_loi_khai": 3, "tre_ngay": 1,
          "qua_han": False, "nhip": 7, "ngay_cuoi": None, "so_luot": 1, "thieu_so": []}
    dong = t.canh_bao(kq)
    assert dong, "ca dựng phải sinh ít nhất một ::warning"
    ra = "\n".join(dong)
    assert _phan("soat_tuan", 0, ra) == sk.VANG
    assert _phan("soat_tuan", 0, "soat-tuan: 0 loi khai") == sk.XANH


def test_THAT_so_ban_goi_cac_ma_thoat_cua_so_sanh_va_main(monkeypatch, capsys):
    t = _nap_tool("so_ban_goi")
    monkeypatch.setattr(t, "ban_local", lambda: {"pandas": "2.0", "streamlit": "1.0"})
    monkeypatch.setattr(t, "luot_ci_gan_nhat", lambda: None)
    monkeypatch.setattr(sys, "argv", ["so_ban_goi.py"])
    ma, ra = _chay_main(t, capsys)
    assert ma == 2 and _phan("so_ban_goi", ma, ra) == sk.CHUA_KIEM_DUOC
    monkeypatch.setattr(t, "luot_ci_gan_nhat", lambda: ("1", "hôm nay"))
    monkeypatch.setattr(t, "goi_repo_nhap", lambda: frozenset())
    monkeypatch.setattr(t, "ban_ci", lambda i: {"pandas": "2.0", "streamlit": "1.0"})
    ma, ra = _chay_main(t, capsys)
    assert ma == 0 and _phan("so_ban_goi", ma, ra) == sk.XANH
    monkeypatch.setattr(t, "ban_ci", lambda i: {"pandas": "2.1", "streamlit": "1.0"})
    ma, ra = _chay_main(t, capsys)
    assert ma == 1 and _phan("so_ban_goi", ma, ra) == sk.VANG


def test_THAT_kiem_duong_ngoai_repo_phan_dinh_ba_ma():
    t = _nap_tool("kiem_duong_ngoai_repo")
    assert t.phan_dinh({"co": [], "chet": [], "su_lieu": []}) == 2
    assert t.phan_dinh({"co": [1], "chet": [1], "su_lieu": []}) == 1
    assert t.phan_dinh({"co": [1], "chet": [], "su_lieu": []}) == 0


# ─── tổng hợp, chọn, tuần tự ─────────────────────────────────────────

def _kq(tt):
    return sk.KetQua(ten="x", trang_thai=tt, chi_tiet=(), lenh_tai_lap="", thoi_gian_giay=0.0)


def test_ma_thoat_tong_do_thang_chua_thang_xanh_va_rong_la_2():
    X, V, D, C = (_kq(t) for t in (sk.XANH, sk.VANG, sk.DO, sk.CHUA_KIEM_DUOC))
    assert sk.ma_thoat_tong([X, X]) == 0
    assert sk.ma_thoat_tong([X, V]) == 0
    assert sk.ma_thoat_tong([X, C]) == 2
    assert sk.ma_thoat_tong([X, D]) == 1
    assert sk.ma_thoat_tong([C, D, V, X]) == 1
    assert sk.ma_thoat_tong([]) == 2


def test_kiem_tat_ca_chon_ten_sai_hoac_rong_la_loi_chu_khong_ra_bang_xanh():
    with pytest.raises(ValueError, match="không có trong danh mục"):
        sk.kiem_tat_ca(["khong_co_phep_nay"])
    with pytest.raises(ValueError, match="rỗng"):
        sk.kiem_tat_ca([])


def test_kiem_tat_ca_theo_thu_tu_danh_muc_va_chon_loc(monkeypatch):
    goi = []
    monkeypatch.setattr(sk, "kiem_mot", lambda p: (goi.append(p.ten), _kq(sk.XANH))[1])
    sk.kiem_tat_ca()
    assert goi == [p.ten for p in sk.DANH_MUC]
    goi.clear()
    sk.kiem_tat_ca(["soat_tuan", "chuong_bao_quet"])
    assert goi == ["chuong_bao_quet", "soat_tuan"], "thứ tự theo danh mục, không theo `chon`"


def test_kiem_tat_ca_chay_TUAN_TU_khong_co_hai_phep_cung_luc(monkeypatch):
    dang_chay = []
    chong_lan = []

    def gia(p):
        dang_chay.append(p.ten)
        chong_lan.append(len(dang_chay))
        dang_chay.pop()
        return _kq(sk.XANH)

    monkeypatch.setattr(sk, "kiem_mot", gia)
    sk.kiem_tat_ca()
    assert chong_lan == [1] * len(sk.DANH_MUC)


def test_kiem_mot_khong_bao_gio_nem_ke_ca_khi_ham_chay_hong(monkeypatch):
    def hong(*a, **kw):
        raise KeyError("lạ")
    monkeypatch.setitem(sk._CHAY_HAM, "kiem_goi", hong)
    kq = sk.kiem_mot(sk.THEO_TEN["kiem_goi"])
    assert kq.trang_thai == sk.CHUA_KIEM_DUOC and "KeyError" in kq.ly_do


def test_trang_thai_la_khong_thanh_CHUA_o_hang_rao_cuoi(monkeypatch):
    monkeypatch.setitem(sk._CHAY_HAM, "kiem_goi", lambda: ("TIM", "", ()))
    kq = sk.kiem_mot(sk.THEO_TEN["kiem_goi"])
    assert kq.trang_thai == sk.CHUA_KIEM_DUOC and "TIM" in kq.ly_do


def test_rut_gon_toi_da_3_dong_dau_va_cuoi_bo_dong_rong():
    assert sk.rut_gon("") == ()
    assert sk.rut_gon("a\n\n b \nc") == ("a", "b", "c")
    assert sk.rut_gon("1\n2\n3\n4\n5\n6") == ("1", "2", "6")
    assert len(sk.rut_gon("x" * 1000)[0]) == sk.DO_DAI_DONG
    assert all(len(d) <= sk.DO_DAI_DONG for d in sk.rut_gon("\n".join("y" * 999 for _ in range(9))))
    # dòng CUỐI giữ lại: với ngoại lệ chưa bắt đó là dòng nêu tên lỗi
    assert sk.rut_gon("Traceback\n  File x\n  File y\nValueError: hỏng")[-1] == "ValueError: hỏng"


def test_dong_hien_thi_khong_loc_bot_dong_nao_ke_ca_CHUA():
    ds = [_kq(t) for t in sk.TRANG_THAI]
    ds = [sk.KetQua(ten=f"p{i}", trang_thai=k.trang_thai, chi_tiet=("a",),
                    lenh_tai_lap="python x", thoi_gian_giay=0.1, ly_do="vì sao")
          for i, k in enumerate(ds)]
    dong = sk.dong_hien_thi(ds)
    assert [d["ten"] for d in dong] == ["p0", "p1", "p2", "p3"]
    assert [d["trang_thai"] for d in dong] == list(sk.TRANG_THAI)
    assert dong[3]["ly_do"] == "vì sao" and dong[3]["lenh_tai_lap"] == "python x"


# ─── 3. CHỈ ĐỌC ───────────────────────────────────────────────────────

def test_tien_trinh_con_bi_go_GITHUB_STEP_SUMMARY_va_khong_ghi_bytecode(monkeypatch, khong_dieu_kien):
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", "/tmp/khong-duoc-ghi-vao-day")
    thay = {}

    def bat(lenh, **kw):
        thay["lenh"], thay["kw"] = lenh, kw
        return SimpleNamespace(returncode=0, stdout="ok")

    monkeypatch.setattr(sk.subprocess, "run", bat)
    phep = sk.THEO_TEN["chuong_nguon_dung"]
    sk.kiem_mot(phep)
    env = thay["kw"]["env"]
    assert "GITHUB_STEP_SUMMARY" not in env
    assert env["PYTHONDONTWRITEBYTECODE"] == "1"
    assert env["PYTHONIOENCODING"] == "utf-8"
    assert thay["lenh"][0] == sys.executable
    assert thay["lenh"][1] == str(GOC / "tools" / "chuong_nguon_dung.py")
    assert thay["kw"]["cwd"] == str(GOC)
    assert thay["kw"]["timeout"] == phep.timeout_giay
    assert thay["kw"]["stdin"] == subprocess.DEVNULL
    assert thay["kw"]["stderr"] == subprocess.STDOUT
    assert os.environ["GITHUB_STEP_SUMMARY"] == "/tmp/khong-duoc-ghi-vao-day", \
        "không được sửa môi trường của tiến trình cha"


def test_khong_phep_nao_truyen_doi_so_ghi():
    ghi = {"--tom-tat", "--cap-nhat", "--ghi", "--allow-overwrite", "--day", "--push"}
    for p in _phep_tep():
        assert not (set(p.doi_so) & ghi), (p.ten, p.doi_so)
    assert sk.THEO_TEN["soat_tuan"].doi_so == (), "soat_tuan chỉ được chạy KHÔNG --tom-tat"


def _duyet(goc, mau):
    """`tools/duyet_repo.duyet`: duyệt đệ quy KHÔNG đi vào worktree lồng (BƯỚC 147)."""
    spec = importlib.util.spec_from_file_location("duyet_repo_cho_suc_khoe",
                                                  GOC / "tools" / "duyet_repo.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.duyet(goc, mau)


def _anh_chup():
    ra = {}
    for p in _duyet(GOC, "*"):
        phan = p.relative_to(GOC).parts
        if ".git" in phan or ".pytest_cache" in phan or ".venv" in phan:
            continue
        try:
            if not p.is_file():
                continue
            s = p.stat()
        except OSError:
            continue
        ra[p.relative_to(GOC).as_posix()] = (s.st_size, s.st_mtime_ns)
    return ra


def test_THAT_mot_luot_chay_thuc_cua_phep_offline_khong_doi_tep_nao_trong_repo(monkeypatch):
    """Chạy tiến trình thật (soat_tuan: chỉ đọc tài liệu) và so ảnh chụp cả cây repo."""
    monkeypatch.delenv("PYTHONDONTWRITEBYTECODE", raising=False)
    truoc = _anh_chup()
    assert "suc_khoe.py" in truoc and len(truoc) > 100, "ảnh chụp rỗng thì mọi so sánh đều xanh"
    kq = sk.kiem_mot(sk.THEO_TEN["soat_tuan"])
    sau = _anh_chup()
    assert kq.trang_thai in (sk.XANH, sk.VANG), kq
    moi = sorted(set(sau) - set(truoc))
    doi = sorted(k for k in truoc if k in sau and truoc[k] != sau[k])
    mat = sorted(set(truoc) - set(sau))
    assert not (moi or doi or mat), (moi, doi, mat)


# ─── 4. DÂY NỐI và AST ────────────────────────────────────────────────

def test_suc_khoe_chi_dung_thu_vien_chuan_o_muc_module_va_khong_co_song_song():
    cay = _cay("suc_khoe.py")
    top = set()
    for n in cay.body:
        if isinstance(n, ast.Import):
            top |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            top.add(n.module.split(".")[0])
    assert top <= {"__future__", "os", "shutil", "subprocess", "sys", "time",
                   "dataclasses", "pathlib", "typing"}, top
    cam_nhap = {"threading", "concurrent", "multiprocessing", "asyncio", "_thread", "gevent"}
    assert not (_ten_nhap(cay) & cam_nhap), _ten_nhap(cay) & cam_nhap
    # ... và không gọi/nhắc tên nào của hồ chứa luồng
    ten_cam = {"ThreadPool", "ThreadPoolExecutor", "ProcessPoolExecutor", "Pool",
               "Thread", "Process", "map_async", "apply_async", "submit", "gather"}
    ten_co = ({n.id for n in ast.walk(cay) if isinstance(n, ast.Name)}
              | {n.attr for n in ast.walk(cay) if isinstance(n, ast.Attribute)})
    assert not (ten_co & ten_cam), ten_co & ten_cam


def test_kiem_lan_luot_va_kiem_tat_ca_dung_hinh_dang_tuan_tu():
    cay = _cay("suc_khoe.py")
    ham = {n.name: n for n in cay.body if isinstance(n, ast.FunctionDef)}
    ll = ast.unparse(ham["kiem_lan_luot"].body[-1])
    assert ll == "for phep in _chon_phep(chon):\n    yield kiem_mot(phep)", ll
    ta = ast.unparse(ham["kiem_tat_ca"].body[-1])
    assert ta == "return list(kiem_lan_luot(chon))", ta


def test_hang_rao_cuoi_cua_kiem_mot_dat_CHUA_khi_trang_thai_ngoai_bon_nhan():
    cay = _cay("suc_khoe.py")
    km = next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == "kiem_mot")
    # (không unparse f-string: 3.11 và 3.12+ in dấu nháy khác nhau)
    rao = [n for n in ast.walk(km) if isinstance(n, ast.If)
           and ast.unparse(n.test) == "tt not in TRANG_THAI"]
    assert len(rao) == 1
    gan = rao[0].body[0]
    assert isinstance(gan, ast.Assign) and isinstance(gan.value, ast.Tuple)
    assert ast.unparse(gan.targets[0]) == "(tt, ly_do)" or ast.unparse(gan.targets[0]) == "tt, ly_do"
    assert ast.unparse(gan.value.elts[0]) == "CHUA_KIEM_DUOC"


def test_danh_gia_ma_thoat_thu_tu_cung_traceback_roi_dau_hieu_roi_mo_ho_roi_bang():
    cay = _cay("suc_khoe.py")
    f = next(n for n in cay.body if isinstance(n, ast.FunctionDef)
             and n.name == "danh_gia_ma_thoat")
    s = [x for x in f.body if not isinstance(x, ast.Expr)]
    assert isinstance(s[0], ast.If) and ast.unparse(s[0].test) == "ma != 0 and DAU_NO in dau_ra"
    assert isinstance(s[1], ast.For) and ast.unparse(s[1].iter) == "phep.dau_hieu"
    assert isinstance(s[2], ast.If) and ast.unparse(s[2].test) == "ma in phep.ma_can_dau_hieu"
    assert isinstance(s[3], ast.Assign) and ast.unparse(s[3].value) == "dict(phep.ma_thoat)"
    assert isinstance(s[4], ast.If) and ast.unparse(s[4].test) == "ma not in bang"


def _tep_py_ngoai_tests():
    for p in _duyet(GOC, "*.py"):
        r = p.relative_to(GOC)
        if (".venv" in r.parts or "tests" in r.parts or ".git" in r.parts
                or "worktrees" in r.parts):
            continue
        yield r


def test_chi_app_va_cong_cu_dong_lenh_nhap_suc_khoe():
    nguoi_nhap = set()
    for r in _tep_py_ngoai_tests():
        try:
            cay = ast.parse((GOC / r).read_text(encoding="utf-8"))
        except (SyntaxError, OSError):
            continue
        if "suc_khoe" in _ten_nhap(cay):
            nguoi_nhap.add(r.as_posix())
    assert nguoi_nhap == {"app.py", "tools/suc_khoe.py"}, nguoi_nhap


@pytest.mark.parametrize("duong", ["run_daily.py", "paper_trading.py", "master_agent.py",
                                   "paper_runner.py", "paper_metrics.py", "data_quality.py",
                                   "market_filter.py", "vnstock_goi.py"])
def test_duong_giao_dich_cham_diem_du_lieu_khong_nhap_suc_khoe(duong):
    assert "suc_khoe" not in _ten_nhap(_cay(duong))


def test_backtest_khong_nhap_suc_khoe():
    for p in _duyet(GOC / "backtest", "*.py"):
        assert "suc_khoe" not in _ten_nhap(ast.parse(p.read_text(encoding="utf-8"))), p


def test_CLI_in_theo_ma_thoat_va_dung_sai_lenh_la_3(monkeypatch, capsys):
    spec = importlib.util.spec_from_file_location("suc_khoe_cli", GOC / "tools" / "suc_khoe.py")
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    assert cli.suc_khoe is sk, "CLI phải nhập module gốc, không phải chính nó"

    ds = [sk.KetQua("a", sk.XANH, ("ổn",), "python a", 0.5),
          sk.KetQua("b", sk.CHUA_KIEM_DUOC, ("vì sao",), "python b", 0.1, "vì sao")]
    ma = cli.main(["--chi", "a,b"], kiem=lambda chon: ds)
    ra = capsys.readouterr().out
    assert ma == 2
    assert "a" in ra and "XANH" in ra and "CHUA KIEM DUOC" in ra
    assert "$ python b" in ra and "| vì sao" in ra
    assert cli.main([], kiem=lambda chon: ds[:1]) == 0
    capsys.readouterr()
    assert cli.main([], kiem=lambda chon: [sk.KetQua("c", sk.DO, (), "python c", 0.0)]) == 1
    capsys.readouterr()
    ma = cli.main(["--chi", "khong_co"])
    assert ma == cli.MA_SAI_LENH == 3
    assert "không có trong danh mục" in capsys.readouterr().err
    cli.main(["--ds"])
    ra = capsys.readouterr().out
    assert all(p.ten in ra for p in sk.DANH_MUC)


def test_CLI_goi_dung_ham_tuan_tu_cua_module_va_ep_utf8():
    van = (GOC / "tools" / "suc_khoe.py").read_text(encoding="utf-8")
    assert 'reconfigure(encoding="utf-8"' in van
    cay = ast.parse(van)
    goi = {ast.unparse(n.func) for n in ast.walk(cay) if isinstance(n, ast.Call)}
    assert "suc_khoe.kiem_tat_ca" in {ast.unparse(n) for n in ast.walk(cay)
                                      if isinstance(n, ast.Attribute)}
    assert not any("Thread" in g or "Pool" in g or "concurrent" in g for g in goi)


# ─── app ──────────────────────────────────────────────────────────────

def _app_cay():
    return _cay("app.py")


def test_app_co_tab_Suc_khoe_dung_ten_va_moi_nhan_mot_bien():
    cay = _app_cay()
    tabs = next(n for n in ast.walk(cay) if isinstance(n, ast.Assign)
                and isinstance(n.value, ast.Call) and ast.unparse(n.value.func) == "st.tabs")
    ten_bien = [e.id for e in tabs.targets[0].elts]
    nhan = [ast.unparse(e) for e in tabs.value.args[0].elts]
    assert len(ten_bien) == len(nhan)
    assert ten_bien.index("t_suc_khoe") == [i for i, s in enumerate(nhan) if "Sức khoẻ" in s][0]
    assert "'🩺 Sức khoẻ'" in nhan


def _khoi_suc_khoe():
    return next(n for n in ast.walk(_app_cay()) if isinstance(n, ast.With)
                and any(isinstance(i.context_expr, ast.Name) and i.context_expr.id == "t_suc_khoe"
                        for i in n.items))


def test_app_CHI_chay_kiem_trong_nhanh_cua_nut_bam_khong_chay_luc_tai_trang():
    khoi = _khoi_suc_khoe()
    # mọi lời gọi hàm CHẠY của suc_khoe phải nằm trong thân một `if st.button(...)`
    chay = {"kiem_lan_luot", "kiem_tat_ca", "kiem_mot"}
    trong_nut = set()
    for n in ast.walk(khoi):
        if isinstance(n, ast.If) and isinstance(n.test, ast.Call) \
                and ast.unparse(n.test.func) == "st.button":
            for con in ast.walk(n):
                trong_nut.add(id(con))
    tim_thay = []
    for n in ast.walk(khoi):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                and n.func.attr in chay:
            tim_thay.append(n)
            assert id(n) in trong_nut, f"{ast.unparse(n)} chạy ngoài nhánh nút bấm"
    assert tim_thay, "tab phải gọi suc_khoe.kiem_lan_luot trong nhánh nút bấm"
    # và ngoài khối này, app không gọi hàm chạy nào
    cay = _app_cay()
    ngoai = [n for n in ast.walk(cay) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Attribute) and n.func.attr in chay
             and ast.unparse(n.func.value) in ("_sk", "suc_khoe")]
    assert len(ngoai) == len(tim_thay)


def test_app_hien_moi_ket_qua_qua_dong_hien_thi_va_thoi_diem_chay():
    khoi = ast.unparse(_khoi_suc_khoe())
    assert "_sk.dong_hien_thi(_sk_kq)" in khoi
    assert "suc_khoe_luc" in khoi and "st.session_state" in khoi
    assert "_html.escape" in khoi, "văn bản của công cụ phải thoát HTML trước khi vào markdown"
    for nhan in ("XANH", "VÀNG", "ĐỎ", "CHƯA KIỂM ĐƯỢC"):
        assert nhan in khoi
    van = (GOC / "app.py").read_text(encoding="utf-8")
    assert "Chạy kiểm" in van


def test_app_vong_hien_thi_di_qua_MOI_dong_khong_loc_va_thoat_HTML_moi_chuoi_cua_cong_cu():
    khoi = _khoi_suc_khoe()
    vong = [n for n in ast.walk(khoi) if isinstance(n, ast.For)
            and ast.unparse(n.iter) == "_sk.dong_hien_thi(_sk_kq)"]
    assert len(vong) == 1, "vòng hiển thị phải duyệt NGUYÊN `dong_hien_thi(_sk_kq)`, không lọc"
    thoat = [ast.unparse(c.args[0]) for c in ast.walk(khoi) if isinstance(c, ast.Call)
             and ast.unparse(c.func) == "_html.escape"]
    for can in ("_d", "_r['ten']", "_sk.THEO_TEN[_r['ten']].mo_ta", "_r['lenh_tai_lap']"):
        assert can in thoat, f"chuỗi {can} vào HTML mà không thoát: {thoat}"
