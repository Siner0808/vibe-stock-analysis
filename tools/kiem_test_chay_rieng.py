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

CHẠY SONG SONG (BƯỚC 201). Mỗi file VẪN chạy một mình trong tiến trình
riêng; song song chỉ là nhiều file cùng lúc — mặc định ba phần tư số nhân
(`SO_TIEN_TRINH_MAC_DINH`), `--tuan-tu` để chạy từng file một. Bản cũ
chạy tuần tự vì đỏ giả: `tests/test_chan_bia_so_lieu.py` đặt `tmpXXXX/thu.py`
ở GỐC repo, và test quét repo ở tiến trình khác đọc đúng lúc nó bị xoá
(`FileNotFoundError`; đo 16/10/2026: 3/158 file mỗi vòng). Đã dọn tận gốc:
file tạm của test chỉ được nằm dưới `.tam_test/`, nơi `duyet_repo.duyet`
bỏ qua — 0/158 đỏ ở hai vòng 8 tiến trình sau khi sửa.
"""
import argparse
import os
import pathlib
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor

GOC = pathlib.Path(__file__).resolve().parent.parent
THU_MUC_TEST = GOC / "tests"

#: Số file chạy cùng lúc (BƯỚC 201): ba phần tư số nhân, chừa chỗ cho cổng 1
#: chạy cùng lúc ở `tools/nam_cong.py`. Máy 16 nhân → 12; runner CI 4 nhân → 3.
SO_TIEN_TRINH_MAC_DINH = max(1, (os.cpu_count() or 1) * 3 // 4)


def chay_mot_file(duong: pathlib.Path, thu_muc_lam_viec: pathlib.Path,
                  giay_toi_da: int = 300) -> tuple[bool, str]:
    """Chạy MỘT file test trong tiến trình riêng. Trả (xanh, tóm tắt)."""
    try:
        kq = subprocess.run(
            [sys.executable, "-m", "pytest", str(duong), "-q", "--tb=line",
             "-p", "no:cacheprovider"],   # nhiều tiến trình: không tranh .pytest_cache
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


def chay_nhieu_file(ds: list[pathlib.Path], thu_muc_lam_viec: pathlib.Path,
                    so_tien_trinh: int) -> list[tuple[pathlib.Path, bool, str]]:
    """[(file, xanh, tóm tắt)] ĐÚNG thứ tự `ds`; tối đa `so_tien_trinh` file chạy cùng lúc.

    Gọi `chay_mot_file` qua tên của module lúc chạy (không giữ tham chiếu), nên
    test thay nó bằng `monkeypatch` vẫn thay được đường song song."""
    n = max(1, min(int(so_tien_trinh), len(ds) or 1))
    with ThreadPoolExecutor(max_workers=n) as ex:
        kq = list(ex.map(lambda f: chay_mot_file(f, thu_muc_lam_viec), ds))
    return [(f, xanh, tom) for f, (xanh, tom) in zip(ds, kq)]


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

        # Đi qua ĐÚNG đường song song mà lượt thật dùng.
        (_, xanh, _), (_, do, _) = chay_nhieu_file(
            [tmp / "test_chac_chan_xanh.py", tmp / "test_chac_chan_do.py"], tmp, 2)

    if not xanh:
        raise RuntimeError("tự kiểm hỏng: file chắc chắn XANH lại báo đỏ")
    if do:
        raise RuntimeError("tự kiểm hỏng: file chắc chắn ĐỎ lại báo xanh")


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--im", action="store_true",
                    help="chỉ in file đỏ, không in từng dòng")
    ap.add_argument("--so-tien-trinh", type=int, default=SO_TIEN_TRINH_MAC_DINH,
                    help="số file chạy cùng lúc (mặc định %(default)s = ba phần tư số nhân)")
    ap.add_argument("--tuan-tu", action="store_true",
                    help="chạy từng file một (đường lui; bằng --so-tien-trinh 1)")
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
    so_tien_trinh = 1 if tuy_chon.tuan_tu else max(1, tuy_chon.so_tien_trinh)
    print(f"{so_tien_trinh} file chạy cùng lúc, mỗi file một tiến trình riêng "
          f"(BƯỚC 201; --tuan-tu để chạy từng file một).")
    print()

    hong: list[tuple[str, str]] = []
    t0 = time.time()
    for i, (f, xanh, tom) in enumerate(chay_nhieu_file(ds, GOC, so_tien_trinh), 1):
        if not xanh:
            hong.append((f.name, tom))
        if not tuy_chon.im:
            print(f"  {'ok' if xanh else '⛔'}  [{i:2d}/{len(ds)}] "
                  f"{f.name:52s} {tom}")

    # In cả số file: một số 0 ở đây phải NHÌN THẤY được, nếu không thì một
    # cái glob hỏng sẽ báo xanh y như khi mọi thứ đều sạch.
    print()
    print(f"Đã chạy riêng {len(ds)} file trong {time.time() - t0:.0f}s "
          f"({so_tien_trinh} cùng lúc).")
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
