"""Kiểm mọi file .py của repo có nạp được bằng Python 3.11 không.

VÌ SAO CÓ FILE NÀY
──────────────────
Dự án chạy Python 3.11 (Streamlit Cloud, `.github/workflows/*.yml`), nhưng
máy phát triển có 3.13. Cú pháp mới hơn nạp bình thường ở máy rồi vỡ ở CI.

Đã xảy ra 21/08/2026: một biểu thức điều kiện xuống dòng NGAY TRONG ô thay
thế của f-string — cú pháp đó là PEP 701, chỉ có từ 3.12:

    print(f"x {'A'
           if dieu_kien else 'B'}")

    Python 3.11 -> LỖI dòng 2: unterminated string literal
    Python 3.13 -> nạp được

319 test xanh tại máy, CI đỏ ngay ở bước đầu.

KHÔNG ĐƯA VÀO CI. CI vốn chạy 3.11 nên lỗi kiểu này tự lộ ở đó. Công cụ này
để chạy TRƯỚC KHI PUSH, ở máy 3.13 — nơi duy nhất mà lỗi ẩn được.

    python tools/kiem_cu_phap_311.py

BA KIỂU HỎNG CỦA CHÍNH CÔNG CỤ NÀY — cả ba đều đã xảy ra khi viết nó, và
cả ba đều trông y hệt "đã kiểm, không thấy gì sai":

  1. Tóm nhầm trình thông dịch 3.13.  -> tự kiểm bằng MOI_3_12 trước khi
     chạy: đoạn đó PHẢI bị báo lỗi, không thì dừng.
  2. Bộ lọc thư mục loại sạch, còn 0 file. Repo này nằm dưới
     `.gemini/antigravity/scratch/…` nên lọc "scratch" theo đường TUYỆT ĐỐI
     là khớp mọi file.  -> lọc theo đường TƯƠNG ĐỐI, và 0 file thì dừng.
  3. Bơm mã nguồn qua stdin. `subprocess.run(encoding=…)` chỉ nói cách mã
     hoá phía cha; tiến trình con vẫn giải mã stdin bằng bảng mã mặc định
     của Windows (cp1258) nên chết ngay khi gặp tiếng Việt — 81/84 file
     "lỗi cú pháp" với thông báo RỖNG.  -> con tự đọc file bằng UTF-8, và
     con thoát khác 0 thì coi là CHƯA KIỂM ĐƯỢC chứ không phải sạch.

Ba mã thoát, phân biệt được với nhau:
    0  mọi file nạp được bằng 3.11
    1  có file lỗi cú pháp
    2  CHƯA kiểm được — không phải "sạch"
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import tempfile

# Đoạn này PHẢI hỏng trên 3.11. Nạp được nghĩa là trình thông dịch không
# phải 3.11, và mọi kết luận sau đó vô nghĩa.
MOI_3_12 = "x = 1\nprint(f\"v {'A'\n  if x else 'B'}\")\n"

BO_QUA = {".venv", ".git", "__pycache__", "scratch", "node_modules", "brain"}

DUONG_DOAN = (
    os.environ.get("PYTHON311", ""),
    os.path.expanduser(
        "~/AppData/Roaming/uv/python/"
        "cpython-3.11.15-windows-x86_64-none/python.exe"),
    "python3.11",
)

# Tiến trình con tự đọc file bằng UTF-8 tường minh. In một dòng cho mỗi
# file hỏng, không in gì cho file sạch, và luôn thoát 0 — thoát khác 0
# nghĩa là chính nó hỏng.
_KICH = (
    "import io, sys\n"
    "for d in sys.argv[1:]:\n"
    "    try:\n"
    "        src = io.open(d, encoding='utf-8').read()\n"
    "    except Exception as e:\n"
    "        print(d + '|0|khong doc duoc: ' + type(e).__name__ + ': ' + str(e))\n"
    "        continue\n"
    "    try:\n"
    "        compile(src, d, 'exec')\n"
    "    except SyntaxError as e:\n"
    "        print(d + '|' + str(e.lineno) + '|' + str(e.msg))\n"
)


def _la_311(duong: str) -> bool:
    try:
        r = subprocess.run(
            [duong, "-c", "import sys;print('%d.%d' % sys.version_info[:2])"],
            capture_output=True, text=True, timeout=20, encoding="utf-8")
    except (OSError, subprocess.SubprocessError):
        return False
    return r.returncode == 0 and (r.stdout or "").strip() == "3.11"


def tim_311() -> str | None:
    """Trình thông dịch 3.11 đầu tiên tìm được, hoặc None."""
    for d in DUONG_DOAN:
        if d and _la_311(d):
            return d
    # `py -0p` liệt kê mọi bản cài trên Windows, kể cả bản do uv quản lý.
    try:
        r = subprocess.run(["py", "-0p"], capture_output=True, text=True,
                           timeout=20, encoding="utf-8")
    except (OSError, subprocess.SubprocessError):
        return None
    for dong in (r.stdout or "").splitlines():
        if "3.11" not in dong:
            continue
        phan = dong.split()
        if phan and _la_311(phan[-1]):
            return phan[-1]
    return None


def kiem_bang_311(py: str, duong_dan: list) -> list:
    """Biên dịch từng file bằng `py`. Trả [(đường dẫn, dòng, lý do)].

    MỘT lần gọi tiến trình con cho cả danh sách, không phải một lần mỗi
    file. Ném RuntimeError khi tiến trình con thoát khác 0 — khi đó "không
    có dòng lỗi nào" KHÔNG được đọc thành "sạch".
    """
    if not duong_dan:
        raise RuntimeError("danh sách rỗng — không có gì để kiểm")
    r = subprocess.run([py, "-c", _KICH] + [str(d) for d in duong_dan],
                       capture_output=True, text=True, timeout=300,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(
            f"tiến trình con thoát {r.returncode}. stderr:\n"
            f"{(r.stderr or '').strip()[:800]}")

    ra = []
    for dong in (r.stdout or "").splitlines():
        phan = dong.split("|", 2)
        if len(phan) == 3:
            ra.append((phan[0], phan[1], phan[2]))
    return ra


def cac_file(goc: pathlib.Path) -> list:
    """Mọi .py trong repo, trừ các thư mục ở BO_QUA.

    Lọc theo đường dẫn TƯƠNG ĐỐI so với gốc repo. Lọc theo đường tuyệt đối
    thì "scratch" khớp với mọi file của repo này.
    """
    return [f for f in sorted(goc.rglob("*.py"))
            if not BO_QUA & set(f.relative_to(goc).parts)]


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

    py = tim_311()
    if not py:
        print("⛔ CHƯA KIỂM ĐƯỢC — không tìm thấy Python 3.11 trên máy.")
        print("   Đặt biến môi trường PYTHON311 trỏ tới nó, hoặc cài:")
        print("     uv python install 3.11")
        print("   Không báo xanh: một phép kiểm không chạy thì không phải")
        print("   một phép kiểm đã qua.")
        return 2

    # ── tự kiểm: đoạn 3.12-mới PHẢI bị báo lỗi ──
    fd, thu = tempfile.mkstemp(suffix=".py")
    os.close(fd)
    try:
        pathlib.Path(thu).write_text(MOI_3_12, encoding="utf-8")
        try:
            tu_kiem = kiem_bang_311(py, [thu])
        except (RuntimeError, subprocess.SubprocessError, OSError) as e:
            print(f"⛔ CHƯA KIỂM ĐƯỢC — tự kiểm hỏng: {type(e).__name__}: {e}")
            return 2
    finally:
        if os.path.exists(thu):
            os.remove(thu)

    if not tu_kiem:
        print(f"⛔ CHƯA KIỂM ĐƯỢC — {py} nạp được cú pháp 3.12-mới, nghĩa là")
        print("   nó KHÔNG phải 3.11. Chạy tiếp thì mọi file đều 'xanh' mà")
        print("   chẳng kiểm gì.")
        return 2

    goc = pathlib.Path(__file__).resolve().parent.parent
    ds = cac_file(goc)
    if not ds:
        print(f"⛔ CHƯA KIỂM ĐƯỢC — không có file .py nào dưới {goc}.")
        print("   Bộ lọc BO_QUA nhiều khả năng đang loại nhầm.")
        return 2

    try:
        hong = kiem_bang_311(py, ds)
    except (RuntimeError, subprocess.SubprocessError, OSError) as e:
        print(f"⛔ CHƯA KIỂM ĐƯỢC — {type(e).__name__}: {e}")
        return 2

    print(f"Trình thông dịch: {py}")
    print(f"Đã kiểm {len(ds)} file .py bằng Python 3.11.\n")

    if hong:
        for d, dong, ly_do in hong:
            try:
                ten = pathlib.Path(d).relative_to(goc)
            except ValueError:
                ten = d
            print(f"  ⛔ {ten}:{dong}  —  {ly_do}")
        print(f"\n{len(hong)} file KHÔNG nạp được bằng 3.11. CI sẽ đỏ.")
        return 1

    print("✅ Mọi file nạp được bằng 3.11.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
