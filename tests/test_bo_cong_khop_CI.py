"""Danh sách cổng trong TÀI LIỆU phải khớp danh sách CI thật sự chạy.

VÌ SAO CÓ FILE NÀY
──────────────────
Cổng thứ năm — `tools/kiem_so_test_khong_giam.py` — ra đời **10/09/2026**.
Tới **14/09/2026**, bốn ngày sau, đếm được:

```
CI chay 5 cong
ten `kiem_so_test_khong_giam` xuat hien trong tai lieu chi dan:
    CLAUDE.md                 0 lan
    docs/HANDOFF.md           0 lan
    README.md                 0 lan
    references/cong-thuc-chay.md   0 lan
    SKILL.md                  3 lan   <- duy nhat
```

Và bốn chỗ vẫn viết **"bốn cổng"**, trong đó có *điều kiện tự merge* ở
`SKILL.md` Bước 5 và tiêu đề công thức chạy.

Đúng hình dạng lệch dự án đã trả giá nhiều lần: `N_DAY_DU` ghi 596 khi mã
là 451, cờ C5 ghi `True` khi mã là `False`. **Một con số đếm-thứ-có-thật
viết bằng tay ở nhiều chỗ sẽ trôi ra khỏi nhau.**

NGUỒN SỰ THẬT LÀ CI, KHÔNG PHẢI TÀI LIỆU
────────────────────────────────────────
`.github/workflows/kiem-dinh.yml` là thứ **thật sự chạy** trên mỗi PR.
Gác này suy danh sách cổng từ đó, rồi đòi mọi khối lệnh trong tài liệu
mà đã đặt tên **từ hai cổng trở lên** phải đặt tên **đủ**.

Ngưỡng hai là có chủ đích: một khối nhắc *một* cổng là đang nói về cổng
ấy, không phải đang liệt kê bộ cổng. Nới xuống một sẽ bắt nhầm mọi câu
nhắc tên; đó là điều gác này **không** làm.
"""
import re
import subprocess
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
CI_YML = GOC / ".github" / "workflows" / "kiem-dinh.yml"

sys.path.insert(0, str(GOC))

DAU = "# cong-thieu-ok:"
DAI_TOI_THIEU = 24
TOI_THIEU_DE_LA_DANH_SACH = 2

_KHOI = re.compile(r"```(?:bash|sh|shell)\n(.*?)```", re.S)
_CONG_CU = re.compile(r"tools/([a-z_0-9]+)\.py")
# `pytest tests/ ...` la ca bo test. `pytest tests/test_x.py` thi khong —
# do la mot file rieng, khong phai cong 1.
_PYTEST_CA_BO = re.compile(r"pytest\s+tests/(?:\s|$)", re.M)


def ly_do_hop_le(ly_do: str) -> bool:
    """Hàm THUẦN. Cửa thoát phải mang một lý do thật, như `# bia-ok:`."""
    return len(" ".join(ly_do.split()).strip()) >= DAI_TOI_THIEU


def bo_cong_trong(van_ban: str) -> set[str]:
    """Tên các cổng mà một đoạn văn bản đặt ra. Hàm THUẦN."""
    ra = set(_CONG_CU.findall(van_ban))
    if _PYTEST_CA_BO.search(van_ban):
        ra.add("pytest")
    return ra


def bo_cong_CI(yml: str) -> set[str]:
    """Cổng mà CI thật sự chạy — suy từ workflow, không gõ tay."""
    return bo_cong_trong(yml)


def khoi_lenh(noi_dung: str) -> list[tuple[int, str]]:
    """Mọi khối ```bash kèm số dòng bắt đầu. Hàm THUẦN."""
    return [(noi_dung[:m.start()].count("\n") + 1, m.group(1))
            for m in _KHOI.finditer(noi_dung)]


def _file_md() -> list[str]:
    ra = subprocess.run(["git", "ls-files", "*.md"], cwd=str(GOC),
                        capture_output=True, text=True)
    assert ra.returncode == 0, f"git ls-files that bai: {ra.stderr}"
    return [d for d in ra.stdout.split("\n") if d.strip()]


def _thieu_trong_khoi(khoi: str, cong_ci: set[str]) -> list[str]:
    """Cổng bị thiếu, hoặc rỗng nếu khối này không phải một danh sách."""
    co = bo_cong_trong(khoi) & cong_ci
    if len(co) < TOI_THIEU_DE_LA_DANH_SACH:
        return []
    if DAU in khoi:
        ly_do = khoi.split(DAU, 1)[1].split("\n", 1)[0]
        if ly_do_hop_le(ly_do):
            return []
    return sorted(cong_ci - co)


def test_CI_chay_dung_nam_cong_va_ca_nam_deu_TON_TAI():
    """Neo phép đo vào thứ chạy thật, và chứng minh từng cổng có mặt."""
    cong = bo_cong_CI(CI_YML.read_text(encoding="utf-8"))
    assert "pytest" in cong, "CI phai chay ca bo test"
    for ten in sorted(cong - {"pytest"}):
        assert (GOC / "tools" / f"{ten}.py").exists(), \
            f"kiem-dinh.yml goi tools/{ten}.py nhung file do khong ton tai"
    assert len(cong) >= 5, (
        f"CI dang chay {len(cong)} cong: {sorted(cong)}. "
        f"Neu that su bot cong thi sua ca tai lieu trong CUNG mot PR.")


def test_MOI_KHOI_dat_ten_TU_HAI_CONG_thi_phai_dat_ten_DU():
    """Phép kiểm chính. Thêm một cổng vào CI mà quên tài liệu → đỏ."""
    cong_ci = bo_cong_CI(CI_YML.read_text(encoding="utf-8"))
    hong = []
    for d in _file_md():
        noi_dung = (GOC / d).read_text(encoding="utf-8", errors="replace")
        for so, khoi in khoi_lenh(noi_dung):
            thieu = _thieu_trong_khoi(khoi, cong_ci)
            if thieu:
                hong.append(f"  {d}:{so} — thieu {', '.join(thieu)}")
    assert not hong, (
        "Khoi lenh liet ke cong nhung KHONG du:\n" + "\n".join(hong) +
        f"\n\nCI dang chay: {sorted(cong_ci)}\n"
        f"Co y liet ke thieu thi ghi `{DAU} <ly do>` trong chinh khoi do.")


def test_PHEP_THU_bat_dung_NGUYEN_VAN_cai_da_lech():
    """Dựng lại **nguyên văn** khối `cong-thuc-chay.md` trước 14/09/2026.

    Câu hỏi duy nhất đáng hỏi về một gác mới: nó bắt được đúng thứ nó
    sinh ra để bắt không. Mẫu dựng tay, không đọc file thật (lỗi 34).
    """
    cong_ci = {"pytest", "kiem_cu_phap_311", "chan_bia_so_lieu",
               "kiem_test_chay_rieng", "kiem_so_test_khong_giam"}
    lech = (
        "./.venv/Scripts/python.exe -m pytest tests/ -q > /tmp/g1.log 2>&1\n"
        "./.venv/Scripts/python.exe tools/kiem_cu_phap_311.py\n"
        "./.venv/Scripts/python.exe tools/chan_bia_so_lieu.py --quet-repo\n"
        "./.venv/Scripts/python.exe tools/kiem_test_chay_rieng.py --im\n")
    assert _thieu_trong_khoi(lech, cong_ci) == ["kiem_so_test_khong_giam"]

    du = lech + "./.venv/Scripts/python.exe tools/kiem_so_test_khong_giam.py\n"
    assert _thieu_trong_khoi(du, cong_ci) == []


def test_KHOI_chi_nhac_MOT_cong_thi_KHONG_phai_danh_sach():
    """Bắt nhầm còn hại hơn bỏ sót — nó dạy người ta tắt gác đi.

    Đây là **giới hạn đã khai trước** của gác này, không phải sơ sót:
    nó chỉ canh khối đang LIỆT KÊ bộ cổng.
    """
    cong_ci = {"pytest", "kiem_cu_phap_311", "chan_bia_so_lieu",
               "kiem_test_chay_rieng", "kiem_so_test_khong_giam"}
    assert _thieu_trong_khoi(
        "./.venv/Scripts/python.exe tools/kiem_cu_phap_311.py\n", cong_ci) == []
    assert _thieu_trong_khoi("streamlit run app.py\n", cong_ci) == []
    # mot file test rieng KHONG phai cong 1
    assert _thieu_trong_khoi(
        "./.venv/Scripts/python.exe -m pytest tests/test_skill_quy_trinh.py -q\n"
        "./.venv/Scripts/python.exe tools/kiem_cu_phap_311.py\n", cong_ci) == []


def test_CUA_THOAT_can_mot_LY_DO_THAT():
    """Không cấm, buộc nói ra — cùng cơ chế `# bia-ok:` và `# van-ban-ok:`.

    `DAI_TOI_THIEU` ghim bằng một SỐ VIẾT THẲNG. Đọc hằng số từ chính
    module đang thử làm mù cả hai vế; lỗi ấy mắc ở BƯỚC 58 rồi mắc LẠI ở
    BƯỚC 60 chưa đầy một giờ sau.
    """
    assert DAI_TOI_THIEU == 24
    assert not ly_do_hop_le("")
    assert not ly_do_hop_le("x" * 23)
    assert ly_do_hop_le("x" * 24)

    cong_ci = {"pytest", "kiem_cu_phap_311", "chan_bia_so_lieu",
               "kiem_test_chay_rieng", "kiem_so_test_khong_giam"}
    thieu = ("./.venv/Scripts/python.exe -m pytest tests/ -q\n"
             "./.venv/Scripts/python.exe tools/kiem_cu_phap_311.py\n")
    assert _thieu_trong_khoi(thieu, cong_ci)
    assert _thieu_trong_khoi(f"{DAU}\n" + thieu, cong_ci), "dau RONG phai bi tu choi"
    assert _thieu_trong_khoi(f"{DAU} ok\n" + thieu, cong_ci), "ly do ngan phai bi tu choi"
    assert _thieu_trong_khoi(
        f"{DAU} chi minh hoa hai cong dau, khong phai bo day du\n" + thieu,
        cong_ci) == []


def test_khoi_lenh_va_bo_cong_trong_la_ham_THUAN():
    """Tách phần đọc khỏi phần phán để thử được bằng mẫu dựng tay."""
    md = ("van xuoi\n\n```bash\ntools/kiem_cu_phap_311.py\n```\n\n"
          "```python\ntools/chan_bia_so_lieu.py\n```\n")
    khoi = khoi_lenh(md)
    assert len(khoi) == 1, "khoi ```python KHONG phai lenh shell"
    assert khoi[0][0] == 3
    assert bo_cong_trong(khoi[0][1]) == {"kiem_cu_phap_311"}
    assert bo_cong_trong("pytest tests/ -q") == {"pytest"}
    assert bo_cong_trong("pytest tests/test_x.py") == set()
