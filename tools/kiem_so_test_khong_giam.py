"""SỐ TEST KHÔNG ĐƯỢC GIẢM ÂM THẦM.

VÌ SAO CÓ FILE NÀY
──────────────────
Ngày 09/09/2026 một lệnh `cat > tests/test_do_tre_khop.py <<'PYEOF'` đè
mất **40 phép kiểm đã có**. Bốn cổng gác chạy đầy đủ và **cả bốn đều
XANH**. Thứ duy nhất bắt được là một con số đọc bằng mắt: 834 thay vì 874.

Lý do bốn cổng im lặng không phải vì chúng viết dở. Chúng đo thứ **đang
có**: test còn lại xanh không, cú pháp nạp được không, có mẫu bịa số
không, file chạy riêng có xanh không. **Không cổng nào so với thứ ĐÃ
TỪNG có.** Nên xoá mất một phép kiểm, một cái gác, một nhánh mã đều lọt
êm — kể cả trên CI, nơi không ai nhớ hôm qua có bao nhiêu test.

Đây là cổng đầu tiên của dự án đo thứ **BỊ MẤT**.

KHÔNG PHẢI ĐỂ CẤM GIẢM
──────────────────────
Dọn dẹp hợp lệ có làm giảm số test: gộp hai test trùng, xoá một file đã
bị thay thế. Cổng này không cấm điều đó. Nó buộc **nói ra vì sao**, đúng
cơ chế `# bia-ok:` của `chan_bia_so_lieu.py`.

Cách khai một lần giảm hợp lệ:

    python tools/kiem_so_test_khong_giam.py --cap-nhat --ly-do "gop hai
        file test trung, khong mat pham vi nao"

Lý do ấy đi thẳng vào `docs/moc_so_test.json` và nằm trong diff. Ai đọc
lịch sử git sau này thấy con số tụt là thấy luôn lời giải thích cạnh nó.

VÌ SAO ĐÒI KHỚP CHÍNH XÁC, KHÔNG PHẢI ">="
──────────────────────────────────────────
Nếu chỉ đòi `thực_tế >= mốc` thì cái mốc trôi tụt lại phía sau: thêm 26
test mà không cập nhật mốc, rồi xoá mất 26 test — cổng vẫn xanh. Cái lỗ
ấy đúng bằng khoảng cách giữa mốc và thực tế, và nó lớn dần theo thời
gian một cách không ai thấy.

Đòi khớp chính xác nghĩa là mỗi lần số test đổi thì một file nhỏ đổi
theo, và **con số di chuyển hiện ra trong diff**. Đó là cả mục đích.

CÁCH DÙNG

    python tools/kiem_so_test_khong_giam.py            # kiem
    python tools/kiem_so_test_khong_giam.py --cap-nhat # sau khi THEM test
    python tools/kiem_so_test_khong_giam.py --cap-nhat --ly-do "..."
                                                       # khi GIAM

Mã thoát:  0 = số test khớp mốc đã ghi
           1 = LỆCH — giảm mà chưa khai, hoặc tăng mà chưa cập nhật mốc
           2 = CHƯA KIỂM ĐƯỢC (không gọi được pytest, không đọc được mốc)

Trạng thái thứ ba bắt buộc, cùng lý do như `kiem_cu_phap_311.py` và
`kiem_test_chay_rieng.py`: một công cụ không chạy được mà trả 0 thì chính
nó là cổng xanh giả — đúng thứ nó sinh ra để chặn.
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys

GOC = pathlib.Path(__file__).resolve().parent.parent
DUONG_MOC = GOC / "docs" / "moc_so_test.json"

#: `pytest --collect-only -q` kết thúc bằng "N tests collected in 0.63s".
#: Số ít ("1 test collected") cũng phải khớp, nếu không một bộ test chỉ
#: còn một phép kiểm sẽ đọc ra "chưa kiểm được" thay vì "mất gần hết".
_MAU_DEM = re.compile(r"^(\d+)\s+tests?\s+collected", re.M)


def doc_so_test(ket_qua: str) -> int | None:
    """Đọc số test từ đầu ra của `pytest --collect-only -q`.

    Trả `None` khi không thấy — gọi bên ngoài phải đổi nó thành mã thoát
    2, KHÔNG được coi là 0 test.
    """
    khop = _MAU_DEM.search(ket_qua)
    return int(khop.group(1)) if khop else None


def dem_test(goc: pathlib.Path = GOC, giay_toi_da: int = 300) -> int | None:
    """Đếm test THẬT bằng một tiến trình pytest riêng."""
    try:
        kq = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "--collect-only", "-q"],
            cwd=str(goc), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=giay_toi_da)
    except (OSError, subprocess.SubprocessError):
        return None
    return doc_so_test(kq.stdout + kq.stderr)


def doc_moc(duong: pathlib.Path = DUONG_MOC) -> dict | None:
    """Đọc mốc đã ghi. `None` nghĩa là CHƯA KIỂM ĐƯỢC, không phải 0."""
    try:
        d = json.loads(duong.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return d if isinstance(d.get("so_test"), int) else None


def quyet_dinh(thuc_te: int | None, moc: dict | None) -> tuple[int, str]:
    """Hàm THUẦN quyết định mã thoát. Đây là chỗ mọi đột biến phải đục.

    Tách ra khỏi `main()` để phép kiểm gọi thẳng được, không phải dựng
    một cây thư mục giả rồi đoán qua đầu ra.
    """
    if thuc_te is None:
        return 2, "CHUA KIEM DUOC — khong dem duoc test (pytest khong chay?)"
    if moc is None:
        return 2, f"CHUA KIEM DUOC — khong doc duoc {DUONG_MOC.name}"

    ghi = moc["so_test"]
    if thuc_te == ghi:
        return 0, f"OK — {thuc_te} test, khop moc da ghi."
    if thuc_te < ghi:
        return 1, (
            f"CHAN — so test GIAM {ghi} -> {thuc_te} (mat {ghi - thuc_te}).\n"
            f"   Ngay 09/09/2026 mot lenh 'cat >' de mat 40 phep kiem va bon\n"
            f"   cong deu XANH. Neu day la don dep hop le thi khai ra:\n"
            f"   python tools/kiem_so_test_khong_giam.py --cap-nhat"
            f" --ly-do \"<vi sao>\"")
    return 1, (
        f"CHAN — so test TANG {ghi} -> {thuc_te}, moc chua cap nhat.\n"
        f"   Moc troi lai phia sau thi lo hong dung bang khoang cach do.\n"
        f"   python tools/kiem_so_test_khong_giam.py --cap-nhat")


def cap_nhat(thuc_te: int, moc: dict, ly_do: str, ngay: str) -> dict:
    """Trả bản mốc MỚI. Thuần, không ghi đĩa — để kiểm được bằng test."""
    if thuc_te < moc["so_test"] and not ly_do.strip():
        raise ValueError(
            f"so test giam {moc['so_test']} -> {thuc_te} thi BAT BUOC co "
            f"--ly-do. Cam giam khong phai muc dich; noi ra vi sao moi la.")
    d = dict(moc)
    d["so_test"] = thuc_te
    d["cap_nhat_luc"] = ngay
    if thuc_te < moc["so_test"]:
        d["lich_su_giam"] = list(moc.get("lich_su_giam", [])) + [
            {"ngay": ngay, "tu": moc["so_test"], "xuong": thuc_te,
             "ly_do": ly_do.strip()}]
    return d


def main() -> int:
    for luong in (sys.stdout, sys.stderr):
        try:
            luong.reconfigure(encoding="utf-8", line_buffering=True)
        except Exception:
            pass

    ap = argparse.ArgumentParser(description="So test khong duoc giam am tham")
    ap.add_argument("--cap-nhat", action="store_true", dest="cap_nhat",
                    help="ghi so test hien tai vao moc")
    ap.add_argument("--ly-do", default="", dest="ly_do",
                    help="BAT BUOC khi so test giam")
    a = ap.parse_args()

    thuc_te = dem_test()
    moc = doc_moc()

    if a.cap_nhat:
        if thuc_te is None or moc is None:
            print("CHUA KIEM DUOC — khong cap nhat moc khi chua doc duoc so.")
            return 2
        import datetime
        try:
            moi = cap_nhat(thuc_te, moc, a.ly_do,
                           datetime.date.today().isoformat())
        except ValueError as e:
            print(f"TU CHOI — {e}")
            return 1
        DUONG_MOC.write_text(
            json.dumps(moi, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        print(f"Da ghi moc: {moi['so_test']} test.")
        return 0

    ma, loi_nhan = quyet_dinh(thuc_te, moc)
    print(loi_nhan)
    return ma


if __name__ == "__main__":
    sys.exit(main())
