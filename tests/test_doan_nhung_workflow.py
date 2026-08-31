"""Test bộ trích đoạn python nhúng trong workflow YAML.

VÌ SAO CÓ FILE NÀY
──────────────────
Bước "Cảnh báo chạm SL/TP trong phiên" có hơn 70 dòng python nằm trong một
heredoc của YAML. Đoạn đó chạy trên runner y hệt một file .py, nhưng:

  · `rglob("*.py")` không thấy nó — nó không có đuôi .py
  · không test nào import nó — nó không phải module
  · máy chạy 3.13, CI chạy 3.11 — khoảng cách đó đã làm CI đỏ một lần rồi

`tools/kiem_cu_phap_311.doan_nhung()` lấp chỗ mù đó. Nhưng chính nó cũng có
thể hỏng lặng lẽ: trích ra 0 đoạn thì mọi thứ vẫn "✅ sạch". Đó đúng là
kiểu hỏng đã xảy ra với bộ lọc BO_QUA — báo xanh trên 0 file.

Nên test cuối cùng ở đây kiểm trên FILE THẬT, không phải file giả.
"""
import importlib.util
import os
import pathlib
import sys

import pytest

GOC = pathlib.Path(__file__).resolve().parent.parent

_spec = importlib.util.spec_from_file_location(
    "kiem_cu_phap_311", GOC / "tools" / "kiem_cu_phap_311.py")
kiem = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kiem)


def _wf(tmp_path, ten: str, noi_dung: str) -> pathlib.Path:
    """Dựng một cây .github/workflows giả có đúng một file."""
    d = tmp_path / ".github" / "workflows"
    d.mkdir(parents=True, exist_ok=True)
    (d / ten).write_text(noi_dung, encoding="utf-8")
    return tmp_path


# ─────────────────────────────────────────────────────────────────────
# 1. Trích đúng
# ─────────────────────────────────────────────────────────────────────

def test_trich_duoc_va_dedent_dung(tmp_path):
    goc = _wf(tmp_path, "a.yml", "\n".join([
        "jobs:",
        "  x:",
        "    steps:",
        "      - run: |",
        "          python - <<'PYA' || true",
        "          def f():",
        "              return 1",
        "          PYA",
        "",
    ]))
    ra = kiem.doan_nhung(goc)
    assert len(ra) == 1, f"trích được {len(ra)} đoạn, cần 1"
    nhan, ma = ra[0]
    assert nhan == "a.yml:5 (PYA)", nhan
    assert ma == "def f():\n    return 1\n", repr(ma)
    print(f"PASS  trích đúng, dedent đúng — {nhan}")


def test_nhieu_heredoc_trong_mot_file(tmp_path):
    goc = _wf(tmp_path, "b.yml", "\n".join([
        "      - run: |",
        "          python - <<'M1'",
        "          a = 1",
        "          M1",
        "      - run: |",
        "          python - <<'M2'",
        "          b = 2",
        "          M2",
        "",
    ]))
    ra = kiem.doan_nhung(goc)
    assert [n for n, _ in ra] == ["b.yml:2 (M1)", "b.yml:6 (M2)"], ra
    print("PASS  trích hết mọi heredoc trong cùng một file")


# ─────────────────────────────────────────────────────────────────────
# 2. Không được im lặng bỏ qua
# ─────────────────────────────────────────────────────────────────────

def test_heredoc_khong_dong_thi_NO(tmp_path):
    """Bỏ qua lặng lẽ thì một YAML hỏng cũng cho '✅ sạch'."""
    goc = _wf(tmp_path, "c.yml", "\n".join([
        "      - run: |",
        "          python - <<'MO'",
        "          a = 1",
        "",
    ]))
    with pytest.raises(RuntimeError) as e:
        kiem.doan_nhung(goc)
    assert "MO" in str(e.value) and "c.yml:2" in str(e.value), str(e.value)
    print("PASS  heredoc không đóng -> nổ, không im")


def test_heredoc_khong_trich_dan_thi_BO_QUA(tmp_path):
    """`<<PY` (không nháy) để shell nội suy trước khi python thấy, nên nội
    dung trên đĩa KHÔNG phải thứ chạy thật. Kiểm nó là kiểm nhầm."""
    goc = _wf(tmp_path, "d.yml", "\n".join([
        "      - run: |",
        "          python - <<PY",
        "          a = 1",
        "          PY",
        "",
    ]))
    assert kiem.doan_nhung(goc) == []
    print("PASS  heredoc không trích dẫn -> bỏ qua có chủ đích")


def test_khong_co_thu_muc_workflows_thi_tra_rong(tmp_path):
    assert kiem.doan_nhung(tmp_path) == []
    print("PASS  không có .github/workflows -> rỗng, không nổ")


# ─────────────────────────────────────────────────────────────────────
# 3. Trên FILE THẬT — chống báo xanh trên 0 đoạn
# ─────────────────────────────────────────────────────────────────────

def test_workflow_that_phai_trich_ra_duoc_doan_canh_bao():
    """Test quan trọng nhất file này.

    Một bộ trích trả rỗng vẫn cho "✅ Mọi file nạp được bằng 3.11" — y hệt
    khi mọi thứ đều sạch. Chỉ có cách neo vào nội dung THẬT mới phân biệt
    được hai trạng thái đó.
    """
    ra = kiem.doan_nhung(GOC)
    assert ra, "không trích được đoạn nhúng nào từ workflow thật"

    canh_bao = [ma for nhan, ma in ra
                if "quet-so-lenh.yml" in nhan and "canh_bao_noi_phien" in ma]
    assert canh_bao, (
        f"không thấy đoạn của bước cảnh báo nội phiên trong "
        f"{[n for n, _ in ra]}")

    ma = canh_bao[0]
    assert "quet_va_canh_gac" in ma, "bước cảnh báo không gọi canh gác"
    assert "tai_khoang" in ma, "thiếu hàm tải theo khoảng ngày"
    print(f"PASS  workflow thật: {len(ra)} đoạn, bước cảnh báo có canh gác")


def test_moi_doan_nhung_that_deu_la_python_hop_le():
    """Cú pháp 3.11 do `tools/kiem_cu_phap_311.py` lo; ở đây chỉ chặn lỗi
    thô — dedent sai hay cắt nhầm dòng thì compile() nổ ngay."""
    for nhan, ma in kiem.doan_nhung(GOC):
        try:
            compile(ma, nhan, "exec")
        except SyntaxError as e:
            raise AssertionError(f"{nhan} không phải python hợp lệ: {e}")
    print("PASS  mọi đoạn nhúng đều compile được")


if __name__ == "__main__":
    for ten, ham in sorted(list(globals().items())):
        if ten.startswith("test_") and "tmp_path" not in ham.__code__.co_varnames:
            ham()
    print("\n(các test cần tmp_path chỉ chạy dưới pytest)")
