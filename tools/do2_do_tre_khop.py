"""ĐO 2 — độ trễ khớp T+2 so với T+1. Bốn lượt.

Tiêu chí đọc đã khai và đã KÝ trước dòng mã đầu tiên của ĐO 2:
`docs/TIEU-CHI-DOC-TRUOC.md`, mục "ĐO 2 — điều khoản bổ sung", commit
`6959f09`. Đừng đọc alpha trước khi đọc file đó.

BỐN LƯỢT

    #   chế độ      ngưỡng GHIM   do_tre_khop   vai trò
    1   theo mã     62            None          đối chứng (= hôm nay)
    2   theo mã     62            1             T+1
    3   theo ngày   50            None          đối chứng (= hôm nay)
    4   theo ngày   50            1             T+1

VÌ SAO NGƯỠNG GHIM BẰNG TAY, KHÔNG ĐỂ LUẬT TỰ CHỌN

Bài học lỗi 21, mắc ngày 09/09/2026 ở chính ĐO 1. Bảng ĐO 1 thiết kế như
một phép so 2×2 với `stride` và `min_history` ghim nguyên — trông như đã
ghim hết. Chạy xong mới thấy **ngưỡng không được ghim**: nó do luật đã
khai trước tự chọn trên in-sample, và luật ấy ra 62 cho chế độ theo mã,
50 cho chế độ theo ngày. Nên một nửa số phép so trong bảng khác nhau ở
CẢ chế độ LẪN ngưỡng, và không quy được cho vế nào.

**"Được chọn tự động theo luật khai trước" KHÔNG đồng nghĩa với "được
ghim".** Một luật chọn tham số là một cái trục nữa, và nó ẩn kỹ hơn một
tham số gõ tay vì nó *trông* như kỷ luật.

Ghim ở đúng giá trị ĐO 1 đã chọn, nên hai lượt đối chứng phải cho lại
đúng con số ĐO 1 — đó là phép kiểm dụng cụ, miễn phí.

HỆ QUẢ: bỏ luôn vòng dò 7 ngưỡng trên IS, nên mỗi lượt còn MỘT mô phỏng
thay vì tám. Đây là hệ quả của việc ghim, không phải một tối ưu được
chọn thêm — ghi ra để không ai đọc nhầm rằng phép đo đã bị cắt bớt.

VÌ SAO MỖI LƯỢT MỘT TIẾN TRÌNH RIÊNG — y như ĐO 1

Bốn lượt chung một tiến trình dùng chung bộ nhớ hậu nghiệm đã nạp và
cache phân tích. Rò một trong hai là bất biến 2 bị phá mà không ai thấy:
bảng bốn dòng vẫn in ra đẹp đẽ và không so được với nhau.

CHẠY

    ./.venv/Scripts/python.exe tools/do2_do_tre_khop.py --thu-muc-log <đường dẫn>
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent

#: {số lượt: (chạy theo ngày, độ trễ khớp, ngưỡng GHIM)}
LUOT = {
    1: (False, None, 62.0),
    2: (False, 1, 62.0),
    3: (True, None, 50.0),
    4: (True, 1, 50.0),
}

MIN_HISTORY = 60
STRIDE = 2
CHE_DO_HOC = "co_san"


def _ten_luot(n: int) -> str:
    theo_ngay, do_tre, nguong = LUOT[n]
    return (f"luot{n}_{'theo-ngay' if theo_ngay else 'theo-ma'}"
            f"_nguong{nguong:g}"
            f"_dotre-{'hom-nay' if do_tre is None else do_tre}")


def _nap_vung_oos(min_history: int) -> dict:
    """Vùng OOS của cả rổ. Cắt y hệt `walkforward.chay()`."""
    sys.path.insert(0, str(GOC))
    from backtest.data import load_all
    from vn100_symbols import CUSTOM_WATCHLIST_SYMBOLS
    from walkforward import chia_vung, nap_moc_sach

    moc = nap_moc_sach()
    vung = {}
    for sym, df in load_all(CUSTOM_WATCHLIST_SYMBOLS).items():
        if sym not in moc:
            continue
        oos, _ = chia_vung(df, moc[sym])
        if len(oos) > min_history:
            vung[sym] = oos.reset_index(drop=True)
    return vung


def chay_mot_luot(n: int) -> int:
    """Chạy đúng một lượt TRONG tiến trình này."""
    import os

    theo_ngay, do_tre, nguong = LUOT[n]
    sys.path.insert(0, str(GOC))
    import walkforward as wf

    # `co_san` cần cờ này bật; `walkforward.chay()` cũng đặt đúng như vậy.
    # Hai nguồn sự thật lệch nhau thì sớm muộn có chỗ đọc nhầm nguồn.
    os.environ["POST_MORTEM_ENABLED"] = "1"

    print("=" * 72)
    print(f"ĐO 2 · LƯỢT {n}/4 — {_ten_luot(n)}")
    print(f"  chế độ        = {'theo ngày' if theo_ngay else 'theo mã'}")
    print(f"  ngưỡng GHIM   = {nguong:g}   (không dò trên IS — lỗi 21)")
    print(f"  do_tre_khop   = {do_tre!r}"
          f"   ({'= stride, tức đúng hôm nay' if do_tre is None else 'T+1'})")
    print(f"  stride        = {STRIDE}   min_history = {MIN_HISTORY}")
    print(f"  che_do_hoc    = {CHE_DO_HOC}")
    print("=" * 72)

    vung_oos = _nap_vung_oos(MIN_HISTORY)
    print(f"mã có vùng OOS: {len(vung_oos)}")

    o = wf._mo_phong(vung_oos, nguong, f"do2_{n}.db",
                     stride=STRIDE, min_history=MIN_HISTORY,
                     che_do_hoc=CHE_DO_HOC, duong_bo_nho=None,
                     theo_ngay=theo_ngay, do_tre_khop=do_tre)
    if not o.get("so_lenh"):
        print("⛔ không lệnh nào — không có gì để đo.")
        return 1

    o.pop("_lenh", None)
    for dong in wf.dong_bao_cao_oos(o):
        print(dong)
    return 0


def xep_lich(thu_muc_log: Path) -> int:
    thu_muc_log.mkdir(parents=True, exist_ok=True)
    bang, hong = [], 0
    for n in sorted(LUOT):
        log = thu_muc_log / f"do2_{_ten_luot(n)}.log"
        t0 = time.time()
        bat_dau = time.strftime("%H:%M:%S")
        print(f"[{bat_dau}] lượt {n}/4 bắt đầu → {log.name}", flush=True)
        with open(log, "w", encoding="utf-8") as f:
            r = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()),
                 "--mot-luot", str(n)],
                cwd=str(GOC), stdout=f, stderr=subprocess.STDOUT)
        giay = time.time() - t0
        ket_thuc = time.strftime("%H:%M:%S")
        hong += 1 if r.returncode else 0
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
    print(f"{'tổng':<6}{'':<11}{'':<11}{sum(x[3] for x in bang) / 60:>8.1f}")
    print()
    if hong:
        print(f"⛔ {hong}/4 lượt mã thoát khác 0. Bảng KHÔNG đọc được.")
        return 1
    print("Cả bốn lượt mã thoát 0. Log:", thu_muc_log)
    print("Đọc theo docs/TIEU-CHI-DOC-TRUOC.md mục ĐO 2 — và kiểm hai lượt")
    print("đối chứng (1 và 3) có ra lại đúng con số ĐO 1 không.")
    return 0


def main() -> int:
    for luong in (sys.stdout, sys.stderr):
        try:
            luong.reconfigure(encoding="utf-8", line_buffering=True)
        except Exception:
            pass

    ap = argparse.ArgumentParser(description="ĐO 2 — bốn lượt độ trễ khớp")
    ap.add_argument("--mot-luot", type=int, choices=sorted(LUOT),
                    dest="mot_luot",
                    help="chạy đúng một lượt trong tiến trình này")
    ap.add_argument("--thu-muc-log", dest="thu_muc_log",
                    help="nơi ghi bốn file log; mặc định <TEMP>/do2")
    a = ap.parse_args()

    if a.mot_luot:
        return chay_mot_luot(a.mot_luot)
    if a.thu_muc_log:
        thu_muc = Path(a.thu_muc_log)
    else:
        import tempfile
        thu_muc = Path(tempfile.gettempdir()) / "do2"
    return xep_lich(thu_muc)


if __name__ == "__main__":
    sys.exit(main())
