"""Cache trỏ được sang thư mục khác — và KHÔNG đặt thì y hệt trước.

Thêm 11/09/2026 cho ĐO 4. Người dùng chốt: kéo cache về 2018 vào một thư
mục RIÊNG, giữ `backtest/cache/` nguyên vẹn làm **bản neo tái lập** cho
mọi số ĐO 1/2/3 đã công bố.

Lý do không hợp nhất vào cache cũ: nguồn đã đổi hệ số điều chỉnh (đo
11/09/2026: −1,2% trên 1.172/1.217 phiên của VNM). Hợp nhất thì vùng
phải giữ hệ số cũ, vùng trái mang hệ số hôm nay, và chỗ nối là một vết
sẹo mà không phép kiểm nào trong bốn phép đã ký nhìn thấy — lỗi 31.

**Đây là thay đổi DỤNG CỤ, không phải thay đổi số liệu.** Mệnh đề ấy chỉ
đáng tin nếu có phép kiểm đứng sau, nên file này tồn tại.
"""
import importlib
import os
import subprocess
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

PY = sys.executable


def _nap_lai(moi_truong: dict[str, str]) -> Path:
    """Nạp `backtest.data` trong MỘT TIẾN TRÌNH RIÊNG, trả `CACHE_DIR`.

    Phải là tiến trình riêng: biến được đọc lúc **import**, nên
    `importlib.reload` trong cùng tiến trình không chứng minh được điều
    mà `do1_chi_phi_thuc_thi.py` cần — rằng tiến trình CON thấy nó.

    Đó đúng là chỗ một phép kiểm dễ tự lừa: reload trong tiến trình cha
    xanh, mà tiến trình con vẫn đọc cache cũ.
    """
    mt = dict(os.environ)
    mt.pop("VIBE_CACHE_DIR", None)
    mt.update(moi_truong)
    ra = subprocess.run(
        [PY, "-c",
         "import sys; sys.path.insert(0, r'" + str(GOC) + "');"
         "from backtest.data import CACHE_DIR; print(CACHE_DIR)"],
        capture_output=True, text=True, encoding="utf-8", env=mt, cwd=str(GOC))
    assert ra.returncode == 0, ra.stderr
    return Path(ra.stdout.strip())


def test_KHONG_dat_bien_thi_duong_dan_Y_HET_truoc():
    """Điều kiện để câu 'không đổi số nào' là một câu đúng."""
    assert _nap_lai({}) == GOC / "backtest" / "cache"
    print("PASS  không đặt biến -> backtest/cache, y hệt trước")


def test_DAT_bien_thi_tien_trinh_CON_doc_duoc(tmp_path):
    """Tiến trình con phải thấy — đó là cả lý do dùng biến môi trường."""
    d = tmp_path / "cache_khac"
    d.mkdir()
    assert _nap_lai({"VIBE_CACHE_DIR": str(d)}) == d
    print(f"PASS  tiến trình CON đọc được VIBE_CACHE_DIR -> {d.name}")


def test_bien_RONG_thi_quay_ve_mac_dinh():
    """Chuỗi rỗng là 'không đặt', không phải 'đặt vào thư mục rỗng tên'."""
    assert _nap_lai({"VIBE_CACHE_DIR": ""}) == GOC / "backtest" / "cache"
    print("PASS  biến rỗng -> quay về mặc định")


def test_cache_path_DI_THEO_bien(tmp_path):
    """`cache_path()` phải theo, không chỉ `CACHE_DIR` theo.

    Mọi đường đọc cache trong dự án đi qua `cache_path()`; một hằng số
    đổi mà hàm không đổi thì phép trỏ này vô dụng.
    """
    d = tmp_path / "ck"
    d.mkdir()
    mt = dict(os.environ)
    mt["VIBE_CACHE_DIR"] = str(d)
    ra = subprocess.run(
        [PY, "-c",
         "import sys; sys.path.insert(0, r'" + str(GOC) + "');"
         "from backtest.data import cache_path; print(cache_path('FPT'))"],
        capture_output=True, text=True, encoding="utf-8", env=mt, cwd=str(GOC))
    assert ra.returncode == 0, ra.stderr
    assert Path(ra.stdout.strip()) == d / "FPT.csv"
    print("PASS  cache_path() đi theo biến")


def test_module_van_nap_duoc_khi_bien_tro_vao_cho_KHONG_TON_TAI(tmp_path):
    """Trỏ sai chỗ thì phải NẠP ĐƯỢC rồi hỏng ở chỗ đọc, không nổ lúc import.

    Nổ lúc import làm mọi công cụ chết cùng lúc, kể cả công cụ không đụng
    cache — cùng hình dạng với `vnstock_ta` ném `SystemExit` khi import,
    thứ `CLAUDE.md` đã ghi là bẫy.
    """
    d = tmp_path / "khong-he-co"
    assert _nap_lai({"VIBE_CACHE_DIR": str(d)}) == d
    print("PASS  trỏ vào chỗ không tồn tại vẫn nạp được module")
