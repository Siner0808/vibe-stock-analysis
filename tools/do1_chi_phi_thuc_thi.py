"""ĐO 1 — bảng "CHI PHÍ THỰC THI" ở cấu hình hiện hành. Bốn lượt.

Tiêu chí đọc đã khai và đã ký TRƯỚC lượt chạy đầu tiên:
`docs/TIEU-CHI-DOC-TRUOC.md`, mục "ĐO 1". Đừng đọc alpha trước khi đọc
file đó — bảng ba kết cục ở trong ấy là thứ quyết định con số này có
được dùng hay không.

BỐN LƯỢT
────────
    #   MO_PHONG_TRUOT_GIA   chế độ
    1   True (mặc định)      theo mã (mặc định)
    2   True (mặc định)      theo ngày
    3   False                theo mã
    4   False                theo ngày

`stride` và `min_history` giữ NGUYÊN mặc định (2 và 60) ở cả bốn lượt.
Đổi chúng là đổi câu hỏi — đó là ĐO 2, một phép đo khác.

VÌ SAO MỖI LƯỢT LÀ MỘT TIẾN TRÌNH RIÊNG
───────────────────────────────────────
Bốn lượt chạy trong cùng một tiến trình sẽ dùng chung trạng thái module:
bộ nhớ hậu nghiệm đã nạp, cache phân tích, và chính cờ `MO_PHONG_TRUOT_GIA`.
Rò một trong ba thứ đó là bất biến 2 (tái lập) bị phá mà không ai thấy —
bảng bốn dòng vẫn in ra đẹp đẽ và không so được với nhau.

Nên tiến trình cha chỉ xếp lịch; mỗi lượt là một `subprocess` gọi lại
chính file này với `--mot-luot N`.

VÌ SAO LƯỢT 1–2 *KIỂM* CỜ CHỨ KHÔNG *ĐẶT* CỜ
────────────────────────────────────────────
Lượt 1–2 phải đo đúng cấu hình đang chạy thật. Nếu mặc định trong
`paper_trading.py` đổi mà kịch bản này cứ đặt lại `True`, nó sẽ tiếp tục
báo cáo một cấu hình không còn tồn tại. Nên ở đây nó *khẳng định* — sai
thì nổ, không lặng lẽ sửa.

Lượt 3–4 thì đặt cờ trong tiến trình, KHÔNG sửa mã nguồn: công tắc ở
`paper_trading.py:329` không có biến môi trường ghi đè, và sửa nguồn giữa
một bảng bốn dòng là đúng thứ làm hỏng phép so.

CHẠY
────
    ./.venv/Scripts/python.exe tools/do1_chi_phi_thuc_thi.py --thu-muc-log <đường dẫn>
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent

#: {số lượt: (mô phỏng trượt giá, chạy theo ngày)}
LUOT = {
    1: (True, False),
    2: (True, True),
    3: (False, False),
    4: (False, True),
}


def _ten_luot(n: int) -> str:
    truot, theo_ngay = LUOT[n]
    return (f"luot{n}_truotgia-{'BAT' if truot else 'TAT'}"
            f"_{'theo-ngay' if theo_ngay else 'theo-ma'}")


def chay_mot_luot(n: int, symbols: str | None = None) -> int:
    """Chạy đúng một lượt TRONG tiến trình này. Trả mã thoát của walkforward.

    `symbols` CHỈ dùng để chạy thử đường ống (hai mã, vài phút) trước khi
    giao cả rổ cho bốn lượt thật. Bảng của ĐO 1 chạy KHÔNG truyền tham số
    này — đổi rổ mã là đổi câu hỏi.
    """
    truot, theo_ngay = LUOT[n]

    sys.path.insert(0, str(GOC))
    import paper_trading

    if truot:
        # Lượt 1-2 đo cấu hình ĐANG CHẠY. Khẳng định, không đặt.
        if paper_trading.MO_PHONG_TRUOT_GIA is not True:
            print(
                f"DỪNG: lượt {n} phải đo cấu hình mặc định, mà "
                f"paper_trading.MO_PHONG_TRUOT_GIA đang là "
                f"{paper_trading.MO_PHONG_TRUOT_GIA!r}, không phải True.\n"
                f"Mặc định trong mã nguồn đã đổi kể từ khi bảng này được "
                f"thiết kế. Sửa docs/TIEU-CHI-DOC-TRUOC.md trước, rồi chạy "
                f"lại — đừng để kịch bản này lặng lẽ đặt lại cờ.",
                file=sys.stderr)
            return 2
    else:
        paper_trading.MO_PHONG_TRUOT_GIA = False

    import walkforward

    sys.argv = ["walkforward.py"]
    if theo_ngay:
        sys.argv.append("--theo-ngay")
    if symbols:
        sys.argv += ["--symbols", symbols]

    print("=" * 72)
    print(f"ĐO 1 · LƯỢT {n}/4 — {_ten_luot(n)}")
    print(f"  MO_PHONG_TRUOT_GIA = {paper_trading.MO_PHONG_TRUOT_GIA}")
    print(f"  chế độ             = {'theo ngày' if theo_ngay else 'theo mã'}")
    print(f"  stride / min_history = mặc định (không truyền)")
    print(f"  rổ mã              = {symbols or 'CẢ RỔ (mặc định)'}")
    print("=" * 72)
    return walkforward.main()


def xep_lich(thu_muc_log: Path, symbols: str | None = None) -> int:
    """Chạy lần lượt bốn lượt, mỗi lượt một tiến trình. Trả 0 nếu cả bốn xong."""
    thu_muc_log.mkdir(parents=True, exist_ok=True)
    tong_hong = 0
    bang = []

    for n in sorted(LUOT):
        log = thu_muc_log / f"do1_{_ten_luot(n)}.log"
        t0 = time.time()
        bat_dau = time.strftime("%H:%M:%S")
        print(f"[{bat_dau}] lượt {n}/4 bắt đầu → {log.name}", flush=True)

        lenh = [sys.executable, str(Path(__file__).resolve()),
                "--mot-luot", str(n)]
        if symbols:
            lenh += ["--symbols", symbols]
        with open(log, "w", encoding="utf-8") as f:
            r = subprocess.run(
                lenh, cwd=str(GOC), stdout=f, stderr=subprocess.STDOUT,
            )

        giay = time.time() - t0
        ket_thuc = time.strftime("%H:%M:%S")
        if r.returncode != 0:
            tong_hong += 1
        bang.append((n, bat_dau, ket_thuc, giay, r.returncode))
        print(f"[{ket_thuc}] lượt {n}/4 xong — mã thoát {r.returncode}"
              f" — {giay / 60:.1f} phút", flush=True)

    print()
    print("=" * 72)
    print("THỜI GIAN CHẠY THẬT — bắt buộc báo cáo KÈM mọi con số alpha")
    print("=" * 72)
    print(f"{'lượt':<6}{'bắt đầu':<11}{'kết thúc':<11}{'phút':>8}  mã thoát")
    for n, b, k, giay, ma in bang:
        print(f"{n:<6}{b:<11}{k:<11}{giay / 60:>8.1f}  {ma}")
    tong = sum(x[3] for x in bang)
    print(f"{'tổng':<6}{'':<11}{'':<11}{tong / 60:>8.1f}")
    print()
    if tong_hong:
        print(f"⛔ {tong_hong}/4 lượt có mã thoát khác 0. Bảng KHÔNG đọc được:")
        print("   một lượt chết giữa chừng vẫn để lại log trông như đầy đủ.")
        return 1
    print("Cả bốn lượt mã thoát 0. Log nằm ở:", thu_muc_log)
    print("Đọc alpha SAU KHI đọc docs/TIEU-CHI-DOC-TRUOC.md mục ĐO 1.")
    return 0


def main() -> int:
    for luong in (sys.stdout, sys.stderr):
        try:
            luong.reconfigure(encoding="utf-8", line_buffering=True)
        except Exception:
            pass

    ap = argparse.ArgumentParser(description="ĐO 1 — bốn lượt chi phí thực thi")
    ap.add_argument("--mot-luot", type=int, choices=sorted(LUOT),
                    dest="mot_luot",
                    help="chạy đúng một lượt trong tiến trình này "
                         "(tiến trình cha dùng, đừng gọi tay trừ khi đo lại)")
    ap.add_argument("--thu-muc-log", dest="thu_muc_log",
                    help="nơi ghi bốn file log; mặc định <TEMP>/do1")
    ap.add_argument("--symbols",
                    help="CHỈ để chạy thử đường ống. Bảng ĐO 1 chạy KHÔNG "
                         "truyền tham số này — đổi rổ mã là đổi câu hỏi.")
    a = ap.parse_args()

    if a.mot_luot:
        return chay_mot_luot(a.mot_luot, a.symbols)

    if a.thu_muc_log:
        thu_muc = Path(a.thu_muc_log)
    else:
        import tempfile
        thu_muc = Path(tempfile.gettempdir()) / "do1"
    return xep_lich(thu_muc, a.symbols)


if __name__ == "__main__":
    sys.exit(main())
