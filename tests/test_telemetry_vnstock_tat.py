"""Telemetry `vnstock` TẮT ở mọi nơi chạy trực tiếp (Q11, BƯỚC 172).

VÌ SAO CÓ FILE NÀY
──────────────────
Máy người dùng tắt telemetry từ 18/09/2026 (`vnai.telemetry_status()` →
`enabled: False`), nhưng Streamlit Cloud và GitHub Actions vẫn gửi tên hàm
và thời gian chạy lên `hq.vnstocks.com/analytics` (nhật ký Cloud 09/10/2026).
Người dùng chọn "Tắt bằng mã ở cả hai" (Q11). Biến `VNSTOCK_TELEMETRY=off`
chỉ chặn việc GỬI số đo; tải dữ liệu và kiểm hạng gói là đường khác.

Hai cách gài, hai gác:
  1. `app.py` và `run_daily.py`: `os.environ.setdefault("VNSTOCK_TELEMETRY",
     "off")` phải đứng TRƯỚC import đầu tiên của module dự án hoặc của
     `vnstock`/`vnai` — các gói ấy đọc biến lúc nạp. `setdefault` (không gán
     đè) để biến đặt tường minh bên ngoài vẫn thắng.
  2. Workflow: MỌI job có bước `pip install -r requirements.txt` đặt
     `env: VNSTOCK_TELEMETRY: "off"` ở cấp JOB (một `env:` ở cấp bước không
     phủ các đoạn `python - <<'PY'` nhúng ở bước khác). Quần thể SUY từ chính
     các tệp workflow, không gõ danh sách tên.

Giá trị phải là chuỗi CÓ NGOẶC KÉP: YAML 1.1 đọc `off` trần thành `False`
(boolean), và biến môi trường khi ấy là "False" — không phải "off".

Workflow đọc bằng tay theo thụt lề, KHÔNG dùng PyYAML: runner của
`kiem-dinh.yml` chỉ cài `requirements.txt` + pytest, không có PyYAML
(bài học ở `tests/test_cua_so_du_lieu_quet.py::_timeout_phut`).
"""
import ast
import re
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
BIEN = "VNSTOCK_TELEMETRY"
TEP_MA = ["app.py", "run_daily.py"]


def _goc_module_cua_du_an() -> set[str]:
    """Tên module nằm ở gốc repo (tệp .py hoặc gói), suy từ đĩa."""
    ten = {p.stem for p in GOC.glob("*.py")}
    ten |= {p.name for p in GOC.iterdir()
            if p.is_dir() and (p / "__init__.py").exists()}
    return ten


def _la_dich(ten_goc: str, du_an: set[str]) -> bool:
    """Import này có thể kéo `vnstock`/`vnai` (trực tiếp hoặc qua mã dự án)."""
    return (ten_goc in du_an or ten_goc.startswith("vnstock")
            or ten_goc.startswith("vnai"))


def _import_dau_tien(cay: ast.AST, du_an: set[str]) -> tuple[int, str]:
    """(số dòng, tên) của import SỚM NHẤT — kể cả import lồng trong hàm."""
    ung = []
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            ten = [a.name.split(".")[0] for a in n.names]
        elif isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
            ten = [n.module.split(".")[0]]
        else:
            continue
        ung += [(n.lineno, t) for t in ten if _la_dich(t, du_an)]
    assert ung, "không thấy import nào của module dự án — tệp đã đổi hình dạng?"
    return min(ung)


def _dong_gai_bien(cay: ast.AST) -> list[int]:
    """Số dòng các lời gọi `os.environ.setdefault("VNSTOCK_TELEMETRY","off")`
    ở MỨC MODULE (một lời gọi lồng trong hàm chưa chạy lúc nạp)."""
    ra = []
    for n in cay.body:
        if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)):
            continue
        c = n.value
        f = c.func
        if not (isinstance(f, ast.Attribute) and f.attr == "setdefault"
                and isinstance(f.value, ast.Attribute)
                and f.value.attr == "environ"
                and isinstance(f.value.value, ast.Name)
                and f.value.value.id == "os"):
            continue
        a = c.args
        if (len(a) == 2 and all(isinstance(x, ast.Constant) for x in a)
                and a[0].value == BIEN and a[1].value == "off"):
            ra.append(n.lineno)
    return ra


def test_ma_dat_bien_TRUOC_import_dau_tien():
    du_an = _goc_module_cua_du_an()
    assert "paper_trading" in du_an and "master_agent" in du_an, (
        "quần thể module dự án suy từ đĩa rỗng/sai — gác sẽ mù")
    for tep in TEP_MA:
        cay = ast.parse((GOC / tep).read_text(encoding="utf-8"))
        dong = _dong_gai_bien(cay)
        assert len(dong) == 1, (
            f"{tep}: cần ĐÚNG một lời gọi os.environ.setdefault("
            f"\"{BIEN}\", \"off\") ở mức module, thấy {len(dong)}. Không dùng "
            f"phép gán đè: biến đặt tường minh bên ngoài phải thắng (Q11).")
        dong_nhap, ten = _import_dau_tien(cay, du_an)
        assert dong[0] < dong_nhap, (
            f"{tep}:{dong[0]} đặt {BIEN} SAU import `{ten}` (dòng "
            f"{dong_nhap}) — vnstock/vnai đọc biến lúc nạp nên đặt muộn là "
            f"không có tác dụng.")
    print("PASS  app.py và run_daily.py đặt VNSTOCK_TELEMETRY=off trước import đầu")


# ── Workflow ────────────────────────────────────────────────────────

def _dong_hieu_luc(tep: Path) -> list[str]:
    """Các dòng không phải chú thích/trống (giữ nguyên thụt lề)."""
    return [d.rstrip("\n") for d in tep.read_text(encoding="utf-8").splitlines()
            if d.strip() and not d.strip().startswith("#")]


def _tach_job(dong: list[str]) -> dict[str, list[str]]:
    """{tên job: các dòng của job} — job là khoá thụt lề đúng 2 dưới `jobs:`."""
    jobs: dict[str, list[str]] = {}
    trong_jobs = False
    hien = None
    for d in dong:
        if re.match(r"^jobs:\s*$", d):
            trong_jobs = True
            continue
        if not trong_jobs:
            continue
        if re.match(r"^\S", d):       # khoá cấp 0 mới = hết `jobs:`
            break
        m = re.match(r"^  ([\w-]+):\s*$", d)
        if m:
            hien = m.group(1)
            jobs[hien] = []
        elif hien is not None:
            jobs[hien].append(d)
    return jobs


def _env_cap_job(dong_job: list[str]) -> dict[str, str]:
    """`env:` thụt lề đúng 4 của job → {khoá: giá trị THÔ (còn ngoặc kép)}."""
    env: dict[str, str] = {}
    trong = False
    for d in dong_job:
        if re.match(r"^    env:\s*$", d):
            trong = True
            continue
        if trong:
            m = re.match(r"^      ([A-Za-z_][\w]*):\s*(.*?)\s*$", d)
            if m:
                env[m.group(1)] = m.group(2)
            elif re.match(r"^\s{0,4}\S", d):   # ra khỏi khối env
                trong = False
    return env


def _cai_requirements(dong_job: list[str]) -> bool:
    return any(re.search(r"pip\s+install\s+(-\S+\s+)*-r\s+requirements\.txt", d)
               for d in dong_job)


def _quan_the() -> list[tuple[str, str, list[str]]]:
    ra = []
    for tep in sorted((GOC / ".github" / "workflows").glob("*.yml")):
        for ten, dong in _tach_job(_dong_hieu_luc(tep)).items():
            if _cai_requirements(dong):
                ra.append((tep.name, ten, dong))
    return ra


def test_quan_the_workflow_cai_requirements_khong_rong():
    """Gác quần thể: rỗng thì mọi vòng `for` bên dưới xanh vì chẳng kiểm gì."""
    qt = _quan_the()
    assert len(qt) >= 1, "không job nào cài requirements.txt — bộ đọc YAML hỏng?"
    assert any(t == "quet-so-lenh.yml" for t, _, _ in qt), (
        "job quét sổ lệnh phải nằm trong quần thể — nó chạy vnstock thật")


def test_moi_job_cai_requirements_tat_telemetry_o_cap_job():
    thieu = []
    for tep, job, dong in _quan_the():
        gia_tri = _env_cap_job(dong).get(BIEN)
        if gia_tri not in ('"off"', "'off'"):
            thieu.append(f"{tep} · job {job}: {BIEN} = {gia_tri!r}")
    assert not thieu, (
        "job cài requirements.txt mà không đặt `env: " + BIEN + ': "off"` '
        "(chuỗi CÓ ngoặc kép) ở cấp job:\n  " + "\n  ".join(thieu))
    print("PASS  mọi job cài requirements.txt đặt VNSTOCK_TELEMETRY=\"off\" ở cấp job")


def test_khong_buoc_nao_bat_lai_telemetry():
    """Một `env:` cấp bước đặt giá trị khác `off` sẽ bật lại cho riêng bước ấy."""
    bat = []
    for tep in sorted((GOC / ".github" / "workflows").glob("*.yml")):
        for d in _dong_hieu_luc(tep):
            m = re.search(rf"{BIEN}\s*:\s*(\S+)", d)
            if m and m.group(1).strip("\"'") != "off":
                bat.append(f"{tep.name}: {d.strip()}")
    assert not bat, "workflow bật lại telemetry:\n  " + "\n  ".join(bat)
