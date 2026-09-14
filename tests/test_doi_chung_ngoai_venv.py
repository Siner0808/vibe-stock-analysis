"""Mã chạy bằng MỘT TRÌNH THÔNG DỊCH KHÁC phải được KHAI, không được lách.

VÌ SAO CÓ FILE NÀY
──────────────────
`tests/test_requirements.py` đòi mọi import trong `tools/*.py` phải có
trong `requirements.txt`, vì ba workflow đều chạy mã ở đó. Nhưng nó quét
`(GOC / "tools").glob("*.py")` — **không đệ quy**. Nên một file đặt ở
`tools/<thu-muc-con>/` **thoát khỏi gác ấy**.

Ngày 14/09/2026 tôi tự đi qua đúng cái lỗ đó: ĐO 8 cần `vectorbt`, mà
`vectorbt` không được vào `requirements.txt` (giấy phép Commons Clause,
repo công khai; và cài vào `.venv` chính sẽ nâng pandas 2.3.3 → 3.0.5).
Đặt file ở `tools/doi_chung/` là **đúng chỗ về ngữ nghĩa** — nó chạy bằng
trình thông dịch khác — nhưng nếu chỉ đặt rồi thôi thì tôi đã lặng lẽ làm
yếu một cái gác.

Nên: **không cấm, buộc nói ra.** Mọi `.py` nằm sâu trong `tools/` phải có
tên trong `NGOAI_VENV` kèm lý do thật. Một file mới lặng lẽ xuất hiện ở
đó sẽ làm test này đỏ.

Cùng cơ chế `# bia-ok:` · `# lenh-xau-ok:` · `khong_soat_vi`.
"""
import ast
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

DAI_TOI_THIEU = 60

#: Mã KHÔNG chạy bằng `.venv` của dự án. Khoá là đường tương đối trong
#: repo; giá trị là lý do — phải nói được VÌ SAO nó không thể sống trong
#: môi trường chung, chứ không phải "cho tiện".
NGOAI_VENV: dict[str, str] = {
    "tools/doi_chung/ve_vectorbt.py":
        "Ve doi chung cua DO 8. Import `vectorbt`, thu KHONG duoc vao "
        "requirements.txt vi hai ly do doc duoc: giay phep Apache-2.0 with "
        "Commons Clause (GitHub tra NOASSERTION, khong phai nguon mo OSI) "
        "tren mot repo CONG KHAI; va do 14/09/2026 cho thay cai no vao .venv "
        "chinh se nang pandas 2.3.3 -> 3.0.5 cung numpy 2.2.6 -> 2.5.3, tuc "
        "doi so cua ca du an. No chay trong mot venv RIENG, goi qua tien "
        "trinh con, va khong mot file nao cua repo import no.",
}

#: Gói chỉ được phép xuất hiện trong mã NGOÀI venv. Có tên ở đây thì
#: `requirements.txt` KHÔNG được khai nó.
GOI_NGOAI_VENV = ("vectorbt",)


def _ly_do_hop_le(s: str) -> bool:
    """Hàm THUẦN. Ngưỡng ghim bằng literal, không đọc từ module này."""
    return len(" ".join(s.split()).strip()) >= 60


def _py_sau_trong_tools() -> list[str]:
    """Mọi `.py` nằm SÂU trong `tools/` — tức thứ `glob("*.py")` không thấy."""
    ra = []
    for f in sorted((GOC / "tools").rglob("*.py")):
        if f.parent == GOC / "tools" or "__pycache__" in f.parts:
            continue
        ra.append(f.relative_to(GOC).as_posix())
    return ra


def test_MOI_py_sau_trong_tools_deu_duoc_KHAI():
    """Phép kiểm chính. Thêm một file vào `tools/<con>/` mà không khai → đỏ."""
    tren_dia = set(_py_sau_trong_tools())
    da_khai = set(NGOAI_VENV)
    chua_khai = sorted(tren_dia - da_khai)
    khai_thua = sorted(da_khai - tren_dia)

    assert not chua_khai, (
        f"file .py nam sau trong tools/ ma KHONG duoc khai: {chua_khai}\n"
        f"`tests/test_requirements.py` quet `tools/*.py` KHONG de quy, nen "
        f"cho nay thoat khoi gac ay. Them mot dong vao NGOAI_VENV kem ly do, "
        f"hoac chuyen file len thang `tools/`.")
    assert not khai_thua, (
        f"khai mot file khong ton tai: {khai_thua}")
    print(f"PASS  {len(tren_dia)} file ngoai venv, ca {len(tren_dia)} deu khai")


def test_MOI_LY_DO_deu_that():
    """Một danh sách miễn trừ không có lý do là một danh sách trôi."""
    hong = {k: v for k, v in NGOAI_VENV.items() if not _ly_do_hop_le(v)}
    assert not hong, (
        f"ly do qua ngan hoac chung chung (>= {DAI_TOI_THIEU} ky tu): "
        f"{sorted(hong)}")
    print(f"PASS  {len(NGOAI_VENV)} ly do deu dat nguong {DAI_TOI_THIEU}")


def test_GOI_ngoai_venv_KHONG_nam_trong_requirements():
    """CI chạy `pip install -r requirements.txt`. Khai nó ở đó là hỏng CI."""
    txt = (GOC / "requirements.txt").read_text(encoding="utf-8").lower()
    dong = [d.split("#")[0].strip() for d in txt.splitlines()]
    ten = {d.split("==")[0].split(">=")[0].split("[")[0].strip()
           for d in dong if d.strip()}
    lot = sorted(g for g in GOI_NGOAI_VENV if g in ten)
    assert not lot, (
        f"requirements.txt khai goi chi dung ngoai venv: {lot}. "
        f"CI va Streamlit Cloud se cai no — dieu ma NGOAI_VENV noi la "
        f"KHONG duoc lam.")
    print(f"PASS  {len(GOI_NGOAI_VENV)} goi ngoai venv khong lot vao requirements")


def test_KHONG_file_nao_cua_repo_IMPORT_ma_ngoai_venv():
    """Nó chạy bằng trình thông dịch khác. Import nó là nhập một gói không có.

    Đọc bằng AST, không bằng `in`: tên module ấy còn nằm trong docstring
    của chính dụng cụ dẫn, giải thích vì sao KHÔNG import nó (lỗi 38).
    """
    ten_mo_dun = {Path(k).stem for k in NGOAI_VENV}
    pham = []
    for f in sorted(GOC.rglob("*.py")):
        if any(p in f.parts for p in (".venv", "__pycache__", "scratch")):
            continue
        if f.relative_to(GOC).as_posix() in NGOAI_VENV:
            continue
        try:
            cay = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for n in ast.walk(cay):
            if isinstance(n, ast.Import):
                goc = {a.name.split(".")[0] for a in n.names}
            elif isinstance(n, ast.ImportFrom):
                goc = {(n.module or "").split(".")[0]}
            else:
                continue
            trung = goc & (ten_mo_dun | set(GOI_NGOAI_VENV))
            if trung:
                pham.append(f"{f.relative_to(GOC).as_posix()}: {sorted(trung)}")
    assert not pham, (
        "file cua repo IMPORT ma chay ngoai venv:\n  " + "\n  ".join(pham))
    print("PASS  khong file nao cua repo import ma ngoai venv")


def test_DUNG_CU_DAN_khong_chet_khi_THIEU_venv_doi_chung():
    """Thiếu vế đối chứng phải là CHƯA KIỂM ĐƯỢC, không phải "sạch".

    Cùng ba trạng thái với `kiem_cu_phap_311.py` và `vnstock_goi.kiem_goi()`:
    mã thoát 2 nghĩa là chưa kiểm được. Một dụng cụ đo trả 0 khi vế kia
    vắng mặt là đúng thứ nó sinh ra để bắt.
    """
    import subprocess

    r = subprocess.run(
        [sys.executable, str(GOC / "tools" / "do8_doi_chung_duong_von.py"),
         "--python-venv", str(GOC / "khong-ton-tai" / "python.exe")],
        capture_output=True, text=True, encoding="utf-8", cwd=str(GOC))
    assert r.returncode == 2, (
        f"thieu venv doi chung ma ma thoat la {r.returncode}, phai la 2 "
        f"(CHUA KIEM DUOC)")
    assert "CHUA KIEM DUOC" in (r.stderr or ""), \
        "khong noi ro day la trang thai chua-kiem-duoc"
    print("PASS  thieu venv doi chung -> ma thoat 2, khong phai 'sach'")
