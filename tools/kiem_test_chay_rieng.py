"""Mỗi file test phải XANH KHI CHẠY MỘT MÌNH.

VÌ SAO CÓ FILE NÀY
──────────────────
Một file test xanh trong bộ đầy đủ nhưng đỏ khi chạy riêng nghĩa là nó
mượn trạng thái của file khác. Nó không kiểm thứ nó nói nó kiểm — nó kiểm
thứ đó CỘNG một điều kiện không ai khai và không ai giữ.

Ba lần trong ba ngày, cùng một gốc, ba hình dạng khác nhau:

  05/09  gác mới đọc cờ an toàn LÚC CHẠY
         -> xanh một mình, ĐỎ trong bộ.  Chỉ tình cờ đỏ đúng chiều.

  07/09  `test_tran_von_cam_ket.py` RẼ NHÁNH theo cờ ấy
         -> một mình thì SKIP, trong bộ thì khẳng định "cổng MỞ"
            trong khi cổng thật đang ĐÓNG.

  07/09  `test_trade_review.py` ÂM THẦM PHỤ THUỘC cờ ấy
         -> cả 7 test đỏ khi chạy một mình, xanh trong bộ, vì
            `consider_entry()` chỉ mở lệnh khi cờ bật.

Hai cái đầu bắt được bằng AST (`tests/test_gac_khong_phu_thuoc_thu_tu.py`).
Cái thứ ba thì KHÔNG: không có tên cờ nào xuất hiện trong file đó cả. Chỉ
CHẠY THẬT mới thấy. Đó là lý do phải có công cụ này bên cạnh gác AST, chứ
không thay cho nó.

CÁCH DÙNG

    python tools/kiem_test_chay_rieng.py

Mã thoát:  0 = mọi file xanh khi chạy riêng
           1 = có file đỏ khi chạy riêng
           2 = CHƯA KIỂM ĐƯỢC (không gọi được pytest, không thấy file nào)

Trạng thái thứ ba là bắt buộc, cùng lý do như `kiem_cu_phap_311.py`: một
công cụ không chạy được mà trả 0 thì chính nó là cổng xanh giả — đúng thứ
nó sinh ra để chặn.

KHÔNG CHẠY SONG SONG. Vài test ghi thư mục tạm vào gốc repo; hai tiến
trình pytest cùng lúc cho đỏ giả. Xem CLAUDE.md, mục "Dọn code chết".
"""
import argparse
import pathlib
import subprocess
import sys
import tempfile
import time

GOC = pathlib.Path(__file__).resolve().parent.parent
THU_MUC_TEST = GOC / "tests"


def chay_mot_file(duong: pathlib.Path, thu_muc_lam_viec: pathlib.Path,
                  giay_toi_da: int = 300) -> tuple[bool, str]:
    """Chạy MỘT file test trong tiến trình riêng. Trả (xanh, tóm tắt)."""
    try:
        kq = subprocess.run(
            [sys.executable, "-m", "pytest", str(duong), "-q", "--tb=line"],
            cwd=str(thu_muc_lam_viec), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=giay_toi_da)
    except FileNotFoundError as e:
        raise RuntimeError(f"không gọi được pytest: {e}") from e
    except subprocess.TimeoutExpired:
        return False, f"quá {giay_toi_da}s"

    ra = (kq.stdout or "") + (kq.stderr or "")
    dong = [d for d in ra.strip().splitlines()
            if "passed" in d or "failed" in d or "error" in d
            or "no tests ran" in d]
    return kq.returncode == 0, (dong[-1] if dong else ra.strip()[-160:])


def tu_kiem() -> None:
    """Tự chứng minh công cụ phân biệt được XANH với ĐỎ, trước khi tin nó.

    Cùng lý do như `kiem_cu_phap_311.py` tự kiểm bằng một đoạn 3.12-mới:
    nếu `chay_mot_file()` hỏng theo kiểu luôn trả True thì mọi lượt quét
    sau đó đều báo sạch, và báo cáo ấy trông y hệt lúc mọi thứ đều tốt.
    """
    with tempfile.TemporaryDirectory() as d:
        tmp = pathlib.Path(d)
        (tmp / "test_chac_chan_xanh.py").write_text(
            "def test_a():\n    assert 1 == 1\n", encoding="utf-8")
        (tmp / "test_chac_chan_do.py").write_text(
            "def test_b():\n    assert 1 == 2\n", encoding="utf-8")

        xanh, _ = chay_mot_file(tmp / "test_chac_chan_xanh.py", tmp)
        do, _ = chay_mot_file(tmp / "test_chac_chan_do.py", tmp)

    if not xanh:
        raise RuntimeError("tự kiểm hỏng: file chắc chắn XANH lại báo đỏ")
    if do:
        raise RuntimeError("tự kiểm hỏng: file chắc chắn ĐỎ lại báo xanh")


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--im", action="store_true",
                    help="chỉ in file đỏ, không in từng dòng")
    ap.add_argument("file", nargs="*",
                    help="chỉ kiểm những file này; bỏ trống thì kiểm cả "
                         "tests/. CI gọi KHÔNG có đối số.")
    tuy_chon = ap.parse_args(argv)

    try:
        tu_kiem()
    except RuntimeError as e:
        print(f"⚠️  CHƯA KIỂM ĐƯỢC — {e}")
        return 2

    ds = ([pathlib.Path(x) for x in tuy_chon.file] if tuy_chon.file
          else sorted(THU_MUC_TEST.glob("test_*.py")))
    if not ds:
        print(f"⚠️  CHƯA KIỂM ĐƯỢC — không thấy file test nào trong "
              f"{THU_MUC_TEST}")
        return 2

    print(f"Chạy riêng từng file trong {THU_MUC_TEST.relative_to(GOC)} "
          f"— {len(ds)} file.")
    print("Song song sẽ cho đỏ giả (test ghi thư mục tạm vào gốc repo), "
          "nên chạy tuần tự.")
    print()

    hong: list[tuple[str, str]] = []
    t0 = time.time()
    for i, f in enumerate(ds, 1):
        xanh, tom = chay_mot_file(f, GOC)
        if not xanh:
            hong.append((f.name, tom))
        if not tuy_chon.im:
            print(f"  {'ok' if xanh else '⛔'}  [{i:2d}/{len(ds)}] "
                  f"{f.name:52s} {tom}")

    # In cả số file: một số 0 ở đây phải NHÌN THẤY được, nếu không thì một
    # cái glob hỏng sẽ báo xanh y như khi mọi thứ đều sạch.
    print()
    print(f"Đã chạy riêng {len(ds)} file trong {time.time() - t0:.0f}s.")
    print()

    if hong:
        for ten, tom in hong:
            print(f"  ⛔ {ten}  —  {tom}")
        print()
        print(f"{len(hong)} file ĐỎ khi chạy một mình. Chúng mượn trạng thái "
              f"của file khác,")
        print("nên đang kiểm thứ chúng nói CỘNG một điều kiện không ai khai.")
        print("Ghim điều kiện ấy TẠI CHỖ, có hoàn tra — đừng gán ở mức module.")
        return 1

    print("✅ Mọi file test xanh khi chạy một mình.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
