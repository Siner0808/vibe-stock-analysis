"""Chạy bảng kiểm `kiem_de_xuat` trên MỘT phiếu ứng viên và IN kết quả — BƯỚC 305.

    ./.venv/Scripts/python.exe tools/kiem_phieu_de_xuat.py <phieu.json> [--so docs/ung-vien.json]

Phiếu là một file JSON (khuôn ở docstring của `kiem_de_xuat.py`). Công cụ CHỈ ĐỌC hai file và CHỈ IN:
không ghi sổ, không ghi file, không chặn ai, không mở khoá ứng viên nào (đặc tả mục 3). Kết quả dán vào mô
tả PR của ứng viên; KHÔNG lưu file phiếu vào repo (khuyến nghị 1 của đặc tả, người dùng duyệt 25/11/2026).
Chạy được cho cả đề xuất TAY của leader (khuyến nghị 3).

Mã thoát: 0 PASS · 1 REVISE · 3 REJECT · 2 chưa kiểm được (file thiếu, JSON hỏng, phiếu hỏng).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _luong in (sys.stdout, sys.stderr):
    try:
        _luong.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import kiem_de_xuat as K  # noqa: E402

SO_MAC_DINH = GOC / "docs" / "ung-vien.json"
MA_THOAT = {K.PASS: 0, K.REVISE: 1, K.REJECT: 3}


def _doc_json(duong: Path):
    return json.loads(Path(duong).read_text(encoding="utf-8"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("phieu", help="file JSON của phiếu ứng viên")
    ap.add_argument("--so", default=str(SO_MAC_DINH), help="sổ ứng viên (mặc định docs/ung-vien.json)")
    a = ap.parse_args(argv)
    try:
        kq = K.kiem_phieu(_doc_json(a.phieu), _doc_json(a.so))
    except (OSError, ValueError) as e:                  # json.JSONDecodeError là ValueError
        print(f"CHUA KIEM DUOC: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    for m in kq["muc"]:
        print(f"{m['stt']}. {m['ten']:<17} {m['ket_qua']:<6} {m['ly_do']}")
        print(f"   số liệu thô: {json.dumps(m['do'], ensure_ascii=False)}")
    print(f"KET LUAN: {kq['ket_luan']}")
    print("(Bảng kiểm chỉ in: không chặn, không ghi sổ, không mở khoá ứng viên; người dùng vẫn duyệt một chạm.)")
    return MA_THOAT[kq["ket_luan"]]


if __name__ == "__main__":
    sys.exit(main())
