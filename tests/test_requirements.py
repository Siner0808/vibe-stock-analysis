"""requirements.txt phải phủ hết thư viện ngoài mà mã ở gốc dự án import.

Vì sao cần test này: GitHub Actions chạy `pip install -r requirements.txt`
rồi `python run_daily.py`. Một thư viện bị import mà không khai báo thì
runner KHÔNG có nó, và lỗi chỉ lộ ra khi phiên quét đã chạy được nửa đường.

Đã xảy ra thật với `toml`: sheets_store.open_from_secrets() import nó để
đọc .streamlit/secrets.toml -- chính đường mà workflow dùng để kéo sổ về
trước khi quét. Thiếu nó thì bước "Kéo sổ lệnh từ Google Sheets" chết ở
MỌI lượt chạy, mà requirements.txt trông vẫn bình thường khi đọc bằng mắt.

Phạm vi: HAI phép kiểm.
  • `..._o_goc_du_an`      -- file .py ở gốc, thứ `run_daily.py` kéo theo.
  • `..._o_tests_va_tools` -- tests/ và tools/, vì chúng CŨNG chạy trên
    Actions: `kiem-dinh.yml` chạy `pytest tests/` và
    `tools/chan_bia_so_lieu.py`, `chuong-bao-quet.yml` chạy
    `tools/chuong_bao_quet.py`, `canh-cong-c5.yml` chạy
    `tools/canh_cong_c5.py`.

Bản đầu của file này ghi "tests/ và tools/ không nằm trong đường chạy của
Actions" và chỉ soát ở gốc. Tiền đề đó sai, và nó cho qua một lỗi thật
ngày 29/08/2026: một test import `yaml`, xanh ở máy (streamlit kéo theo
PyYAML) và đỏ trên runner sạch, chặn merge PR.
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
        # Hai truong hop rat khac nhau, thong bao phai noi dung cai nao:
        #  - module CO THE nap duoc -> that su la thu vien ngoai chua khai bao
        #  - module KHONG nap duoc  -> import HONG, khong lien quan requirements
        import importlib.util
        chua_khai, hong = [], []
        for m, files in sorted(thieu.items()):
            mo_ta = "%s (import boi %s)" % (m, ", ".join(files))
            try:
                co = importlib.util.find_spec(m) is not None
            except Exception:
                co = False
            (chua_khai if co else hong).append(mo_ta)

        loi = []
        if chua_khai:
            loi.append(
                "Thu vien ngoai duoc import nhung KHONG co trong "
                "requirements.txt: " + "; ".join(chua_khai)
                + ". GitHub Actions cai theo requirements.txt, nen runner se "
                  "thieu no va phien quet chet giua chung.")
        if hong:
            loi.append(
                "IMPORT HONG — module khong ton tai o dau ca: "
                + "; ".join(hong)
                + ". Day khong phai van de requirements: file do khong nap "
                  "duoc trong bat ky moi truong nao.")
        raise AssertionError(" | ".join(loi))
    print("PASS  requirements.txt phu het import o goc du an")


if __name__ == "__main__":
    test_requirements_phu_het_import_o_goc_du_an()


# ─────────────────────────────────────────────────────────────────────
# Gói tài trợ vnstock — KHÔNG được lọt vào requirements.txt
# ─────────────────────────────────────────────────────────────────────

GOI_TAI_TRO = ("vnstock_data", "vnstock-data", "vnstock_ta", "vnstock-ta",
               "vnstock_news", "vnstock-news", "vnstock_pipeline",
               "vnstock-pipeline", "vnii")


#: `kiem-dinh.yml` chạy `pip install -r requirements.txt` RỒI `pip install
#: pytest`. Đó là ngoại lệ DUY NHẤT được cài thêm.
NGOAI_LE_CI = {"pytest"}


def _import_cua_file(duong_dan) -> set:
    """Tên module cấp cao nhất mà MỘT file import."""
    try:
        cay = ast.parse(duong_dan.read_text(encoding="utf-8"))
    except SyntaxError:
        return set()
    ra = set()
    for nut in ast.walk(cay):
        if isinstance(nut, ast.Import):
            ra |= {a.name.split(".")[0] for a in nut.names}
        elif isinstance(nut, ast.ImportFrom) and nut.level == 0 and nut.module:
            ra.add(nut.module.split(".")[0])
    return ra


def _goc():
    import pathlib
    return pathlib.Path(GOC)


#: Thư mục mà gác cấm-import-mức-module soi. Rút ra khỏi thân hàm ngày
#: 22/09/2026 để chính QUẦN THỂ trở thành thứ khoá được — một gác mở rộng
#: quần thể mà không ai canh quần thể ấy thì nó thu lại được mà không đỏ,
#: đúng hình dạng lỗi 73 · 80 · 90.
THU_MUC_CAM_MUC_MODULE = (".", "tools", "tests")


def tap_file_cam_muc_module() -> list:
    """Mọi `.py` trong `THU_MUC_CAM_MUC_MODULE`, đã sắp xếp."""
    goc_p = _goc()
    ra: list = []
    for tm in THU_MUC_CAM_MUC_MODULE:
        ra += sorted((goc_p / tm).glob("*.py")) if tm != "." else sorted(goc_p.glob("*.py"))
    return ra


def _import_muc_module(duong_dan) -> set:
    """Tên module cấp cao nhất mà một file import **Ở MỨC MODULE**.

    Khác `_import_cua_file` đúng một chỗ, và chỗ ấy quyết định: nó duyệt
    `cay.body` chứ không `ast.walk`, nên một import nằm trong thân hàm
    KHÔNG tính. Đó là ranh giới thật của CI — `pip install` không có gói
    tài trợ, nhưng một import trong hàm không bao giờ chạy trên runner.
    """
    try:
        cay = ast.parse(duong_dan.read_text(encoding="utf-8"))
    except SyntaxError:
        return set()
    ra = set()
    for nut in cay.body:
        if isinstance(nut, ast.Import):
            ra |= {a.name.split(".")[0] for a in nut.names}
        elif isinstance(nut, ast.ImportFrom) and nut.level == 0 and nut.module:
            ra.add(nut.module.split(".")[0])
    return ra


def _module_noi_bo_mo_rong() -> set:
    """Stem của mọi .py trong dự án: gốc + tests/ + tools/.

    Dựng TRÊN NỀN `_module_noi_bo()` (đã gồm gói `backtest/` và các thư
    mục có `__init__.py`) rồi thêm stem của tests/ và tools/. Không sửa
    hàm kia: nới nó ra có thể che một phụ thuộc thật ở đường chạy sản
    xuất chỉ vì trùng tên với một file trong tests/.
    """
    ten = _module_noi_bo()
    for thu_muc in ("tests", "tools"):
        ten |= {p.stem for p in (GOC / thu_muc).glob("*.py")}
    return ten


def test_requirements_phu_het_import_o_tests_va_tools():
    """tests/ và tools/ CŨNG nằm trên đường chạy của Actions.

    Bản đầu của file này ghi "tests/ và tools/ không nằm trong đường chạy
    của Actions". Tiền đề đó SAI, và nó đã cho qua một lỗi thật ngày
    29/08/2026: `tests/test_cua_so_du_lieu_quet.py` import `yaml`, xanh ở
    máy (streamlit kéo theo PyYAML) và đỏ trên runner sạch, chặn merge PR.

    Ba workflow đều chạy mã trong hai thư mục này:
      • `kiem-dinh.yml`      -> `pytest tests/` và `tools/chan_bia_so_lieu.py`
      • `chuong-bao-quet.yml` -> `tools/chuong_bao_quet.py`
      • `canh-cong-c5.yml`    -> `tools/canh_cong_c5.py`
    """
    khai_bao = _da_khai_bao() | NGOAI_LE_CI
    noi_bo = _module_noi_bo_mo_rong()
    tai_tro = {g.replace("-", "_") for g in GOI_TAI_TRO}
    thieu: dict = {}
    for thu_muc in ("tests", "tools"):
        for f in sorted((GOC / thu_muc).glob("*.py")):
            o_muc_module = _import_muc_module(f)
            for m in _import_cua_file(f):
                if m in noi_bo or m in sys.stdlib_module_names:
                    continue
                # Goi tai tro KHONG duoc phep nam trong requirements.txt —
                # khai o do la hong ca CI lan Streamlit Cloud ngay buoc cai
                # (`test_goi_tai_tro_khong_nam_trong_requirements`). Nen mot
                # dung cu can chung chi con MOT duong hop le: import trong
                # than ham. Cho ay duoc mien o day, va bi cam o muc module
                # boi `test_khong_import_goi_tai_tro_o_muc_module` — gac ay
                # tu 22/09/2026 quet ca tools/ va tests/, dung de cai lo nay
                # co day.
                if m.replace("-", "_") in tai_tro and m not in o_muc_module:
                    continue
                goi = TEN_GOI.get(m, m).lower()
                if goi not in khai_bao:
                    thieu.setdefault(goi, set()).add(f"{thu_muc}/{f.name}")
    assert not thieu, (
        "import thư viện KHÔNG khai báo trong requirements.txt: "
        + " · ".join(f"{g} ({', '.join(sorted(fs))})"
                     for g, fs in sorted(thieu.items())))
    print("PASS  tests/ và tools/ không import gì ngoài requirements + pytest")


def test_goi_tai_tro_khong_nam_trong_requirements():
    """Bốn gói tài trợ + vnii không có trên PyPI công khai.

    GitHub Actions và Streamlit Cloud đều chạy `pip install -r
    requirements.txt`. Khai báo chúng ở đó thì cả hai hỏng NGAY Ở BƯỚC CÀI
    — sớm và ồn ào, nhưng hỏng toàn bộ, kể cả những phần không dùng tới
    dữ liệu tài trợ.

    Chúng được cài ở máy local qua API có xác thực bằng khoá. Sự bất đối
    xứng đó là CỐ Ý, và `vnstock_goi.kiem_goi()` báo LỆCH trên cloud chính
    là báo đúng.
    """
    khai_bao = _da_khai_bao()
    lot = [g for g in GOI_TAI_TRO if g.lower() in khai_bao]
    assert not lot, (
        f"requirements.txt khai báo gói không có trên PyPI công khai: {lot}. "
        f"CI và Streamlit Cloud sẽ hỏng ở bước `pip install`.")
    print("PASS  không gói tài trợ nào lọt vào requirements.txt")


def test_QUAN_THE_cua_gac_cam_muc_module_phai_phu_CA_BA_thu_muc():
    """Khoá chính cái quần thể, không chỉ khoá phán quyết của nó.

    Ngoại lệ ở `test_requirements_phu_het_import_o_tests_va_tools` cho gói
    tài trợ đi qua khi nó nằm TRONG HÀM. Thứ duy nhất giữ cho ngoại lệ ấy
    không thành một cái lỗ là gác mức-module — và gác ấy chỉ đóng được lỗ
    nếu nó thật sự nhìn `tools/` và `tests/`. Thu quần thể về `.` là mở lỗ
    mà không một phép kiểm nào khác đỏ.
    """
    assert set(THU_MUC_CAM_MUC_MODULE) >= {".", "tools", "tests"}, (
        f"quần thể bị thu lại: {THU_MUC_CAM_MUC_MODULE}. Ngoại lệ gói tài trợ "
        f"ở gác phủ requirements dựa vào việc gác này nhìn CẢ tools/ và tests/.")

    tap = tap_file_cam_muc_module()
    ten = {p.name for p in tap}
    goc_p = _goc()
    for tm in ("tools", "tests"):
        co_that = {p.name for p in (goc_p / tm).glob("*.py")}
        assert co_that, f"{tm}/ không có file .py nào — mẫu rỗng, phép kiểm vô nghĩa"
        thieu = co_that - ten
        assert not thieu, f"{tm}/ có file ngoài tầm gác: {sorted(thieu)[:5]}"
    print(f"PASS  quan the phu {len(tap)} file o {len(THU_MUC_CAM_MUC_MODULE)} thu muc")


def test_khong_import_goi_tai_tro_o_muc_module():
    """Không file nào được `import vnstock_data` ở mức module.

    Gốc dự án là đúng tập file mà GitHub Actions chạy. Một import ở mức
    module sẽ làm `run_daily.py` chết ngay dòng đầu trên runner — nơi
    không có gói tài trợ và sẽ không bao giờ có.

    Muốn dùng thì import BÊN TRONG hàm, bọc try/except, và có đường lui.

    **Quần thể mở rộng sang `tools/` và `tests/` ngày 22/09/2026**, cùng
    ngày `tools/do14_kha_thi_khoi_ngoai.py` trở thành file ĐẦU TIÊN của
    repo chạm tới một gói tài trợ. Đếm trước khi sửa: cả ba thư mục có
    **0** import ở mức module và **1** import trong hàm, nên phép mở rộng
    này không đổi một phán quyết nào hôm nay — nó đóng trước cái lỗ mà
    ngoại lệ vừa mở ở `test_requirements_phu_het_import_o_tests_va_tools`
    sẽ để lại. Hai gác ấy nay là một cặp: cái kia miễn cho import TRONG
    HÀM, cái này cấm ở MỨC MODULE.
    """
    import ast

    xau = []
    goc_p = _goc()
    tap = tap_file_cam_muc_module()
    for f in tap:
        try:
            cay = ast.parse(f.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for nut in cay.body:                       # CHỈ mức module
            ten = []
            if isinstance(nut, ast.Import):
                ten = [a.name.split(".")[0] for a in nut.names]
            elif isinstance(nut, ast.ImportFrom) and nut.module:
                ten = [nut.module.split(".")[0]]
            for t in ten:
                if t.replace("-", "_") in {g.replace("-", "_")
                                           for g in GOI_TAI_TRO}:
                    xau.append(f"{f.relative_to(goc_p)}:{nut.lineno} -> {t}")
    assert not xau, (
        "import gói tài trợ ở mức module (CI không có chúng):\n  "
        + "\n  ".join(xau))
    print(f"PASS  {len(tap)} file o goc + tools/ + tests/, khong file nao "
          f"import goi tai tro o muc module")
