"""Cổng 2 phải chia danh sách file thành LÔ, không nhồi cả repo vào một dòng lệnh.

VÌ SAO CÓ FILE NÀY
──────────────────
`tools/kiem_cu_phap_311.py` gọi trình thông dịch 3.11 MỘT lần với mọi đường
dẫn tuyệt đối trên dòng lệnh. Windows cắt dòng lệnh ở 32.767 ký tự
(`CreateProcess`); vượt là `FileNotFoundError: [WinError 206] The filename
or extension is too long`, và cổng thoát 2 — CHƯA KIỂM ĐƯỢC.

Đo 30/09/2026 (BƯỚC 147): repo có worktree lồng → 458 file, dòng lệnh
47.102 ký tự → cổng 2 thoát 2. KHÔNG có worktree lồng → 229 file, 20.106 ký
tự, tức đã dùng 61% trần — và số file `.py` tăng từ 46 (10/08) lên 229
(30/09). Nên lỗi này tới được mà không cần worktree lồng; worktree lồng chỉ
làm nó tới sớm. Linux (CI) có trần ~2 MB nên chỉ máy Windows gặp.
"""
from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent

_spec = importlib.util.spec_from_file_location(
    "_kiem_cu_phap_311_lo", GOC / "tools" / "kiem_cu_phap_311.py")
k = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(k)

#: Trần dòng lệnh của `CreateProcess`, kể cả ký tự kết thúc.
TRAN_WINDOWS = 32_767


def test_CHIA_LO_giu_thu_tu_KHONG_mat_KHONG_lap_va_khong_lo_nao_vuot_tran():
    ds = [f"C:/rat/dai/{'x' * 80}/f{i}.py" for i in range(600)]
    lo = k.chia_lo(ds, 5_000)
    assert len(lo) > 1, "600 duong dai ~100 ky tu phai ra NHIEU lo"
    assert [d for l in lo for d in l] == ds, "mat, lap hoac dao thu tu file"
    for l in lo:
        assert len(subprocess.list2cmdline(l)) <= 5_000


def test_CHIA_LO_duong_co_DAU_CACH_van_duoi_tran():
    """`list2cmdline` bọc đường có dấu cách trong nháy kép — hai ký tự thêm
    mà một phép đếm `len(str(d)) + 1` bỏ sót."""
    ds = [f"C:/Program Files/{'y' * 40} z/f{i}.py" for i in range(300)]
    for l in k.chia_lo(ds, 3_000):
        assert len(subprocess.list2cmdline(l)) <= 3_000


def test_CHIA_LO_file_DAI_HON_tran_van_co_lo_rieng_chu_khong_bi_bo():
    ds = ["a" * 100, "b.py", "c.py"]
    assert k.chia_lo(ds, 50) == [["a" * 100], ["b.py", "c.py"]]


def test_CHIA_LO_rong_la_rong():
    assert k.chia_lo([], 100) == []


def test_TRAN_MAC_DINH_giu_ca_dong_lenh_duoi_tran_WINDOWS():
    """Trần mặc định chỉ tính phần DANH SÁCH FILE; phần đầu (đường dẫn
    trình thông dịch + đoạn `_KICH`) phải vừa chỗ còn lại, kể cả khi trình
    thông dịch nằm ở một đường dài 260 ký tự."""
    py = "C:/" + "p" * 250 + "/python.exe"
    ds = [f"C:/{'d' * 200}/f{i}.py" for i in range(1_000)]
    for l in k.chia_lo(ds):
        assert len(subprocess.list2cmdline([py, "-c", k._KICH] + l)) < TRAN_WINDOWS


def test_KIEM_BANG_311_qua_TRAN_WINDOWS_van_kiem_va_bat_file_hong_o_LO_CUOI(tmp_path):
    """Dựng lại NGUYÊN VĂN điều kiện của lỗi thật: tổng dòng lệnh vượt
    32.767 ký tự. Bản một-lần-gọi nổ `WinError 206` ở đây (trên Windows).

    File hỏng đặt CUỐI danh sách: một bản chia lô quên lô cuối vẫn không nổ,
    nhưng trả rỗng — đúng hình dạng 'không thấy gì sai'."""
    py = k.tim_311()
    if not py:
        pytest.skip("khong co Python 3.11 tren may — cong 2 cung thoat 2")
    tm = tmp_path / ("d" * 120)
    tm.mkdir()
    ds = []
    for i in range(350):
        p = tm / f"f{i:03d}.py"
        p.write_text("x = 1\n", encoding="utf-8")
        ds.append(p)
    hong = tm / "zz_hong.py"
    hong.write_text(k.MOI_3_12, encoding="utf-8")
    ds.append(hong)
    assert len(subprocess.list2cmdline([str(d) for d in ds])) > TRAN_WINDOWS, (
        "ca thu khong vuot tran — no khong tai hien duoc loi")
    kq = k.kiem_bang_311(py, ds)
    assert [Path(d).name for d, _, _ in kq] == ["zz_hong.py"]
