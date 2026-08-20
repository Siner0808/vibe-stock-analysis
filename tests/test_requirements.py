"""requirements.txt phải phủ hết thư viện ngoài mà mã ở gốc dự án import.

Vì sao cần test này: GitHub Actions chạy `pip install -r requirements.txt`
rồi `python run_daily.py`. Một thư viện bị import mà không khai báo thì
runner KHÔNG có nó, và lỗi chỉ lộ ra khi phiên quét đã chạy được nửa đường.

Đã xảy ra thật với `toml`: sheets_store.open_from_secrets() import nó để
đọc .streamlit/secrets.toml -- chính đường mà workflow dùng để kéo sổ về
trước khi quét. Thiếu nó thì bước "Kéo sổ lệnh từ Google Sheets" chết ở
MỌI lượt chạy, mà requirements.txt trông vẫn bình thường khi đọc bằng mắt.

Phạm vi: chỉ file .py ở GỐC dự án -- đúng tập file mà workflow chạy.
tests/ và tools/ không nằm trong đường chạy của Actions.
"""
import ast
import pathlib
import sys

GOC = pathlib.Path(__file__).resolve().parent.parent

# Tên module khi import khác tên gói khi cài.
TEN_GOI = {
    "bs4": "beautifulsoup4",
    "google": "google-generativeai",
    "tradingview_ta": "tradingview-ta",
    "yaml": "pyyaml",
    "dateutil": "python-dateutil",
    "sklearn": "scikit-learn",
    "PIL": "pillow",
}


def _da_khai_bao() -> set:
    ten = set()
    for dong in (GOC / "requirements.txt").read_text(encoding="utf-8").splitlines():
        dong = dong.split("#")[0].strip()
        if not dong:
            continue
        for dau in (">=", "==", "<=", "~=", ">", "<", "["):
            dong = dong.split(dau)[0]
        ten.add(dong.strip().lower())
    return ten


def _module_noi_bo() -> set:
    trong = {p.stem for p in GOC.glob("*.py")}
    trong |= {p.name for p in GOC.iterdir() if p.is_dir() and (p / "__init__.py").exists()}
    trong |= {"backtest", "tools", "tests"}
    return trong


def _import_ngoai() -> dict:
    ket = {}
    for f in sorted(GOC.glob("*.py")):
        try:
            cay = ast.parse(f.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for nut in ast.walk(cay):
            if isinstance(nut, ast.Import):
                for a in nut.names:
                    ket.setdefault(a.name.split(".")[0], set()).add(f.name)
            elif isinstance(nut, ast.ImportFrom) and nut.level == 0 and nut.module:
                ket.setdefault(nut.module.split(".")[0], set()).add(f.name)
    return ket


def test_requirements_phu_het_import_o_goc_du_an():
    khai_bao = _da_khai_bao()
    noi_bo = _module_noi_bo()
    thieu = {}
    for mod, files in _import_ngoai().items():
        if mod in sys.stdlib_module_names or mod in noi_bo:
            continue
        if TEN_GOI.get(mod, mod).lower() in khai_bao:
            continue
        thieu[mod] = sorted(files)

    if thieu:
        chi_tiet = "; ".join(
            "%s (import boi %s)" % (m, ", ".join(f)) for m, f in sorted(thieu.items()))
        raise AssertionError(
            "Thu vien duoc import nhung KHONG co trong requirements.txt: "
            + chi_tiet
            + ". GitHub Actions cai theo requirements.txt, nen runner se "
              "thieu no va phien quet chet giua chung.")
    print("PASS  requirements.txt phu het import o goc du an")


if __name__ == "__main__":
    test_requirements_phu_het_import_o_goc_du_an()
