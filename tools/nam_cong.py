"""Năm cổng gác CHẠY CÙNG LÚC — một lệnh thay cho năm lệnh tuần tự (BƯỚC 201).

VÌ SAO CÓ FILE NÀY
──────────────────
Đo 15–16/10/2026 trên máy 16 nhân: năm cổng tuần tự mất 12½–27½ phút, gần hết
ở cổng 1 (cả bộ pytest, một tiến trình) và cổng 4 (158 file, mỗi file một tiến
trình, lần lượt) — cả hai chạy trên MỘT nhân. Ba cổng còn lại cộng lại ~10 giây.

Luật cũ "tuần tự, KHÔNG song song" có lý do thật: một test đặt file tạm ở gốc
repo, và test quét repo ở tiến trình khác đọc đúng lúc nó bị xoá — đỏ giả. Nguồn
ấy đã dọn (file tạm của test chỉ ở `.tam_test/`, `tools/duyet_repo.py` luật 3),
nên năm cổng chạy cùng lúc được, và cổng 4 tự chạy nhiều file một lúc.

Năm cổng KHÔNG đổi: cùng năm công cụ CI chạy (`.github/workflows/kiem-dinh.yml`,
gác ở `tests/test_nam_cong.py`), cổng 1 vẫn là cả bộ trong MỘT tiến trình, cổng 4
vẫn mỗi file một tiến trình. Chỉ đổi lúc bắt đầu.

CÁCH DÙNG
    ./.venv/Scripts/python.exe tools/nam_cong.py [--thu-muc-log <dir>] [--tuan-tu]

In một dòng `congN=<mã thoát>` cho mỗi cổng (cùng dạng bản tuần tự), thời gian
của từng cổng và của cả lượt. Log đầy đủ ở `<dir>/congN.log`.
Mã thoát: 0 cả năm cổng thoát 0 · 1 có cổng khác 0 — đọc mã của cổng ấy theo
bảng `references/cong-thuc-chay.md` (mã 2 là CHƯA KIỂM ĐƯỢC, không phải sạch).
"""
from __future__ import annotations

import argparse
import os
import pathlib
import subprocess
import sys
import tempfile
import time

GOC = pathlib.Path(__file__).resolve().parent.parent

#: (số, tên, đối số sau `python`) — đúng năm cổng CI chạy, đúng lệnh trong SKILL.md.
CONG: list[tuple[int, str, list[str]]] = [
    (1, "pytest cả bộ", ["-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"]),
    (2, "cú pháp 3.11", ["tools/kiem_cu_phap_311.py"]),
    (3, "quét bịa số liệu", ["tools/chan_bia_so_lieu.py", "--quet-repo"]),
    (4, "từng file một mình", ["tools/kiem_test_chay_rieng.py", "--im"]),
    (5, "số test không giảm", ["tools/kiem_so_test_khong_giam.py"]),
]


def chay(cong=None, thu_muc_log: pathlib.Path | None = None, tuan_tu: bool = False,
         python: str | None = None, cwd: pathlib.Path | None = None) -> list[dict]:
    """Chạy các cổng, CÙNG LÚC trừ khi `tuan_tu`. Trả [{so, ten, ma, giay, log}].

    Mọi cổng được khởi động TRƯỚC khi chờ cổng nào (gác: `tests/test_nam_cong.py`).
    """
    cong = CONG if cong is None else cong
    thu_muc_log = pathlib.Path(thu_muc_log or tempfile.mkdtemp(prefix="nam_cong_"))
    thu_muc_log.mkdir(parents=True, exist_ok=True)
    python = python or sys.executable
    cwd = cwd or GOC
    moi_truong = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")

    def bat_dau(so, doi_so):
        log = thu_muc_log / f"cong{so}.log"
        tep = open(log, "w", encoding="utf-8")
        p = subprocess.Popen([python, *doi_so], cwd=str(cwd), stdout=tep,
                             stderr=subprocess.STDOUT, env=moi_truong)
        return p, tep, log, time.time()

    ra = []
    if tuan_tu:
        for so, ten, doi_so in cong:
            p, tep, log, t0 = bat_dau(so, doi_so)
            ma = p.wait()
            tep.close()
            ra.append({"so": so, "ten": ten, "ma": ma, "giay": time.time() - t0, "log": log})
        return ra

    dang_chay = [(so, ten, *bat_dau(so, doi_so)) for so, ten, doi_so in cong]
    # Hỏi trạng thái cả nhóm thay vì `wait()` theo thứ tự: chờ lần lượt thì cổng
    # xong sớm bị ghi thời gian của cổng chậm nhất đứng trước nó (đo 16/10: cả năm
    # cổng cùng ghi 383 s).
    xong: dict[int, tuple[int, float]] = {}
    while len(xong) < len(dang_chay):
        for so, ten, p, tep, log, t0 in dang_chay:
            if so not in xong and p.poll() is not None:
                xong[so] = (p.returncode, time.time() - t0)
                tep.close()
        if len(xong) < len(dang_chay):
            time.sleep(0.2)
    for so, ten, p, tep, log, t0 in dang_chay:
        ma, giay = xong[so]
        ra.append({"so": so, "ten": ten, "ma": ma, "giay": giay, "log": log})
    return ra


def _dong_cuoi(log: pathlib.Path) -> str:
    """Dòng tóm tắt cuối có nghĩa của một log (bỏ dòng trống và dòng gạch)."""
    try:
        dong = log.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    co_nghia = [d.strip() for d in dong if d.strip() and not set(d.strip()) <= set("-=_ ")]
    return co_nghia[-1][:140] if co_nghia else ""


def main(argv: list[str] | None = None) -> int:
    for luong in (sys.stdout, sys.stderr):
        try:
            luong.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="Năm cổng gác chạy cùng lúc (BƯỚC 201)")
    ap.add_argument("--thu-muc-log", type=pathlib.Path, default=None,
                    help="nơi ghi congN.log (mặc định một thư mục tạm mới)")
    ap.add_argument("--tuan-tu", action="store_true",
                    help="chạy từng cổng một như bản cũ (đường lui)")
    a = ap.parse_args(argv)

    t0 = time.time()
    print(f"Năm cổng {'TUẦN TỰ' if a.tuan_tu else 'CÙNG LÚC'} · bắt đầu {time.strftime('%H:%M:%S')}",
          flush=True)
    kq = chay(thu_muc_log=a.thu_muc_log, tuan_tu=a.tuan_tu)
    for c in kq:
        print(f"cong{c['so']}={c['ma']}  {c['giay']:6.0f}s  {c['ten']:20s} {_dong_cuoi(c['log'])}")
    print(f"xong {time.strftime('%H:%M:%S')} · cả lượt {time.time() - t0:.0f}s · "
          f"log: {kq[0]['log'].parent if kq else '-'}")
    hong = [c for c in kq if c["ma"] != 0]
    if hong:
        print(f"⛔ {len(hong)} cổng không xanh: " + ", ".join(f"cổng {c['so']} (mã {c['ma']})" for c in hong))
        return 1
    print("✅ Cả năm cổng thoát 0.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
