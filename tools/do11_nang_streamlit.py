"""Đọc bảng ĐO 11 — `streamlit` 1.60.0 → 1.64.0 có chạy được ở máy này không.

VÌ SAO CÓ FILE NÀY
──────────────────
BƯỚC 94 đo ra vế lệch cuối cùng giữa máy local và CI: `streamlit` máy
1.60.0, CI 1.64.0. `requirements.txt` khai gói này **không có sàn** — trần
trụi một dòng — nên Streamlit Cloud lấy bản mới nhất ở mỗi lượt deploy.
Tức **bản đang phục vụ người dùng là bản của CI**, không phải bản đang
chạy ở đây.

Quy tắc số 2 của dự án: *không có lệnh thì không có số*. File này là cái
lệnh ấy, và nó chạy HAI LƯỢT — trước khi nâng và sau khi nâng.

BẢNG ĐỌC nằm ở `docs/TIEU-CHI-DOC-TRUOC.md` mục ĐO 11, khai **trước** khi
con số so sánh đầu tiên tồn tại. File này không được mang bảng đọc thứ hai.

    A mot ten BIEN MAT                      ->  KHONG NANG
    B mot tu khoa bi CHOI THEM              ->  KHONG NANG
    C mot module dang nap duoc ma NAP NO    ->  KHONG NANG
    D may chu dang dung duoc ma KHONG DUNG  ->  KHONG NANG
      bon o GIONG hoac TOT LEN              ->  NANG DUOC
      khong chay duoc mot luot nao          ->  CHUA KET LUAN DUOC

VÌ SAO B SẮC HƠN A
──────────────────
Cách một thư viện giao diện phế truất thường là **giữ tên, bỏ tham số**.
Một phép kiểm chỉ hỏi `hasattr` sẽ xanh suốt qua đúng loại hỏng ấy. B hỏi
`inspect.signature` xem từ khoá repo đang truyền có còn được nhận không.

BA TRẠNG THÁI Ở MỌI Ô, KHÔNG PHẢI HAI
─────────────────────────────────────
`AttributeError` khi tra một tên nghĩa là tên MẤT. Một lỗi khác — chẳng
hạn `st.session_state` đòi ngữ cảnh chạy — nghĩa là **chưa kiểm được**, và
nó không được nhập chung với "mất". Đúng lỗi 66: một kết quả âm từ một mẫu
không thể cho kết quả dương thì nói về MẪU, không nói về giả thuyết.
"""
import argparse
import ast
import inspect
import json
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.stdout.reconfigure(encoding="utf-8")

#: Ký trong `docs/TIEU-CHI-DOC-TRUOC.md` ĐO 11.
MODUN_NAP = ("chatbot_agent", "sheets_store", "vnstock_auth")
GIAY_CHO_MAY_CHU = 90.0
BO_QUA = {".venv", "scratch", "node_modules", ".git", "backtest"}

CO = "CO"
THIEU = "THIEU"
CHUA_KIEM = "CHUA KIEM"

NANG_DUOC = "NANG DUOC"
KHONG_NANG = "KHONG NANG"
CHUA_KET_LUAN = "CHUA KET LUAN DUOC"

TEN_ANH = "vibe_do11_streamlit.json"


def duong_anh() -> Path:
    return Path(tempfile.gettempdir()) / TEN_ANH


# ── phần ĐỌC REPO: thuần, không chạm streamlit ──────────────────────────
def _trong_repo(p: Path) -> bool:
    """Lọc theo đường TƯƠNG ĐỐI với gốc repo.

    Lọc theo đường tuyệt đối đã cắn hai lần (16/09 và 17/09/2026): repo
    nằm dưới một thư mục tên `scratch`, nên `"scratch" in p.parts` đúng
    với MỌI file và lượt quét ra 0.
    """
    return not any(x in p.relative_to(GOC).parts for x in BO_QUA)


def _bi_danh(cay: ast.AST) -> str | None:
    """`import streamlit as st` -> "st". Không có thì None."""
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name == "streamlit":
                    return a.asname or "streamlit"
    return None


def _chuoi(n: ast.AST, bi: str) -> list[str] | None:
    """`st.sidebar.markdown` -> ["sidebar", "markdown"]; ngoài `st` -> None."""
    phan: list[str] = []
    while isinstance(n, ast.Attribute):
        phan.append(n.attr)
        n = n.value
    if isinstance(n, ast.Name) and n.id == bi and phan:
        return list(reversed(phan))
    return None


def be_mat(goc: Path = GOC) -> tuple[dict[str, list[str]], dict[str, list[str]], int]:
    """Quét repo bằng AST. Trả (tên -> file, tên -> từ khoá, số file quét).

    Tên là đường có chấm tính từ `st`, ví dụ `sidebar.markdown`.
    """
    ten: dict[str, set[str]] = {}
    khoa: dict[str, set[str]] = {}
    quet = 0
    for p in sorted(goc.rglob("*.py")):
        if not _trong_repo(p):
            continue
        quet += 1
        try:
            cay = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        bi = _bi_danh(cay)
        if bi is None:
            continue
        for n in ast.walk(cay):
            if isinstance(n, ast.Attribute):
                c = _chuoi(n, bi)
                if c:
                    ten.setdefault(".".join(c), set()).add(p.name)
            if isinstance(n, ast.Call):
                c = _chuoi(n.func, bi)
                if not c:
                    continue
                for kw in n.keywords:
                    khoa.setdefault(".".join(c), set()).add(
                        kw.arg if kw.arg else "**")
    return ({k: sorted(v) for k, v in ten.items()},
            {k: sorted(v) for k, v in khoa.items()},
            quet)


# ── phần CHẠM streamlit ─────────────────────────────────────────────────
def _tra(st, duong: str):
    """Đi theo đường có chấm. Trả (trạng thái, đối tượng hoặc lý do)."""
    o = st
    for phan in duong.split("."):
        try:
            o = getattr(o, phan)
        except AttributeError:
            return THIEU, f"khong co .{phan}"
        except Exception as e:                # bia-ok: khong tra duoc, khong doan
            return CHUA_KIEM, f"{type(e).__name__}: {e}"
    return CO, o


def do_ten(ten: dict) -> dict:
    import streamlit as st
    ra = {}
    for duong in sorted(ten):
        tt, _ = _tra(st, duong)
        ra[duong] = tt
    return ra


def do_khoa(khoa: dict) -> dict:
    """Mỗi (tên, từ khoá) -> NHAN / CHOI / CHUA KIEM."""
    import streamlit as st
    ra = {}
    for duong in sorted(khoa):
        tt, o = _tra(st, duong)
        if tt != CO:
            for k in khoa[duong]:
                ra[f"{duong}({k})"] = CHUA_KIEM
            continue
        if not callable(o):
            for k in khoa[duong]:
                ra[f"{duong}({k})"] = CHUA_KIEM
            continue
        try:
            sig = inspect.signature(o)
        except (ValueError, TypeError) as e:  # bia-ok: khong doc duoc chu ky
            for k in khoa[duong]:
                ra[f"{duong}({k})"] = CHUA_KIEM
            del e
            continue
        co_var = any(t.kind is inspect.Parameter.VAR_KEYWORD
                     for t in sig.parameters.values())
        for k in khoa[duong]:
            if k == "**":
                ra[f"{duong}({k})"] = CHUA_KIEM
            elif co_var or k in sig.parameters:
                ra[f"{duong}({k})"] = "NHAN"
            else:
                ra[f"{duong}({k})"] = "CHOI"
    return ra


def do_nap() -> dict:
    """Nạp từng module trong một TIẾN TRÌNH RIÊNG — nạp chung thì một
    module hỏng sẽ giết cả lượt đo."""
    ra = {}
    for m in MODUN_NAP:
        kq = subprocess.run(
            [sys.executable, "-c", f"import {m}"],
            cwd=str(GOC), capture_output=True, text=True, timeout=180)
        ra[m] = {
            "ma": kq.returncode,
            "loi": (kq.stderr or "").strip().splitlines()[-1:] or [""],
        }
    return ra


def _cong_trong() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    cong = s.getsockname()[1]
    s.close()
    return cong


def do_may_chu() -> dict:
    """Dựng `streamlit run app.py` headless rồi hỏi `/_stcore/health`."""
    cong = _cong_trong()
    p = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py",
         "--server.headless", "true", "--server.port", str(cong),
         "--server.address", "127.0.0.1",
         "--browser.gatherUsageStats", "false"],
        cwd=str(GOC), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace")
    url = f"http://127.0.0.1:{cong}/_stcore/health"
    het = time.monotonic() + GIAY_CHO_MAY_CHU
    ra = {"cong": cong, "suc_khoe": None, "giay": None, "chet_som": False}
    try:
        while time.monotonic() < het:
            if p.poll() is not None:
                ra["chet_som"] = True
                break
            try:
                with urllib.request.urlopen(url, timeout=2) as r:
                    ra["suc_khoe"] = r.read().decode("utf-8", "replace").strip()
                    ra["giay"] = round(GIAY_CHO_MAY_CHU - (het - time.monotonic()), 1)
                    break
            except (urllib.error.URLError, OSError):
                time.sleep(1.0)
    finally:
        p.terminate()
        try:
            out = p.communicate(timeout=20)[0] or ""
        except subprocess.TimeoutExpired:
            p.kill()
            out = p.communicate()[0] or ""
    ra["traceback"] = "Traceback (most recent call last)" in out
    ra["nhat_ky_cuoi"] = out.strip().splitlines()[-4:]
    return ra


def chup() -> dict:
    import streamlit as st
    ten, khoa, quet = be_mat()
    assert quet > 100, f"quet chi {quet} file — may do hep hon thu no do"
    return {
        "ban": st.__version__,
        "quet_file": quet,
        "A": do_ten(ten),
        "B": do_khoa(khoa),
        "C": do_nap(),
        "D": do_may_chu(),
    }


# ── phần PHÁN: thuần, đục thử được không cần streamlit ──────────────────
def phan_xu(truoc: dict | None, sau: dict | None) -> tuple[str, list[str]]:
    """So hai lượt chụp. Trả (phán quyết, danh sách lý do)."""
    if not truoc or not sau:
        return CHUA_KET_LUAN, ["thiếu một trong hai lượt chụp"]

    xau: list[str] = []

    # A — tên đang CÓ mà thành THIẾU
    for k, v in truoc["A"].items():
        if v == CO and sau["A"].get(k) == THIEU:
            xau.append(f"A: st.{k} biến mất")

    # B — từ khoá đang NHẬN mà thành CHỐI
    for k, v in truoc["B"].items():
        if v == "NHAN" and sau["B"].get(k) == "CHOI":
            xau.append(f"B: st.{k} bị chối")

    # C — module đang nạp được mà nạp nổ
    for m, v in truoc["C"].items():
        if v["ma"] == 0 and sau["C"].get(m, {}).get("ma") != 0:
            xau.append(f"C: {m} nạp nổ")

    # D — máy chủ đang dựng được mà không dựng
    dt, ds = truoc["D"], sau["D"]
    if dt.get("suc_khoe") == "ok" and ds.get("suc_khoe") != "ok":
        xau.append("D: máy chủ không dựng được")
    if not dt.get("traceback") and ds.get("traceback"):
        xau.append("D: nhật ký máy chủ có traceback")

    if xau:
        return KHONG_NANG, xau
    if sau["D"].get("suc_khoe") != "ok" and truoc["D"].get("suc_khoe") != "ok":
        return CHUA_KET_LUAN, ["cả hai lượt đều không dựng được máy chủ"]
    return NANG_DUOC, []


def _dem(d: dict, gia_tri: str) -> int:
    return sum(1 for v in d.values() if v == gia_tri)


def _in_luot(nhan: str, a: dict) -> None:
    print(f"  {nhan:<6} streamlit {a['ban']}  ·  quét {a['quet_file']} file")
    print(f"         A  {_dem(a['A'], CO)} có · {_dem(a['A'], THIEU)} thiếu"
          f" · {_dem(a['A'], CHUA_KIEM)} chưa kiểm")
    print(f"         B  {_dem(a['B'], 'NHAN')} nhận · {_dem(a['B'], 'CHOI')} chối"
          f" · {_dem(a['B'], CHUA_KIEM)} chưa kiểm")
    xanh = sum(1 for v in a["C"].values() if v["ma"] == 0)
    print(f"         C  {xanh}/{len(a['C'])} module nạp được")
    d = a["D"]
    print(f"         D  /_stcore/health = {d.get('suc_khoe')!r}"
          f" sau {d.get('giay')}s · traceback={d.get('traceback')}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--luot", choices=("truoc", "sau"),
                    help="chụp một lượt và ghi vào ảnh")
    ap.add_argument("--so", action="store_true", help="so hai lượt đã chụp")
    ns = ap.parse_args()

    anh = duong_anh()
    kho = json.loads(anh.read_text(encoding="utf-8")) if anh.exists() else {}

    if ns.luot:
        kho[ns.luot] = chup()
        anh.write_text(json.dumps(kho, ensure_ascii=False, indent=2),
                       encoding="utf-8")
        print(f"ĐO 11 — lượt {ns.luot}")
        _in_luot(ns.luot, kho[ns.luot])
        print(f"\nảnh: {anh}")
        return 0

    if not ns.so:
        ap.print_help()
        return 2

    print("ĐO 11 — streamlit, so hai lượt\n")
    for nhan in ("truoc", "sau"):
        if nhan in kho:
            _in_luot(nhan, kho[nhan])
        else:
            print(f"  {nhan:<6} (chưa chụp)")
    tt, ly_do = phan_xu(kho.get("truoc"), kho.get("sau"))
    print(f"\nPHAN QUYET: {tt}")
    for d in ly_do:
        print(f"  - {d}")
    return {NANG_DUOC: 0, KHONG_NANG: 1, CHUA_KET_LUAN: 2}[tt]


if __name__ == "__main__":
    raise SystemExit(main())
