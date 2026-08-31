"""Skill `quy-trinh-do-luong` phải nói ĐÚNG về repo, không chỉ nói hay.

Một skill là tài liệu, và tài liệu mục ruỗng im lặng: nó trỏ tới file đã
đổi tên, test đã xoá, lệnh không còn chạy — mà không gì kêu. Phiên sau đọc
nó rồi làm theo, và làm sai.

Đây đúng lỗi `Pha C — Wyckoff Spring` và `Fundamental Agent · BCTC Q2`: hai
ô trên giao diện hứa một thành phần không tồn tại, tồn tại nhiều ngày trước
khi ai đó `grep` thử.

File này kiểm mọi thứ skill KHẲNG ĐỊNH là có thật.
"""
import re
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

SKILL = GOC / ".claude" / "skills" / "quy-trinh-do-luong" / "SKILL.md"
BAY = SKILL.parent / "references" / "bay.md"


def test_skill_ton_tai_va_frontmatter_hop_le():
    assert SKILL.exists(), f"không có {SKILL.relative_to(GOC).as_posix()}"
    src = SKILL.read_text(encoding="utf-8")
    assert src.startswith("---\n"), "thiếu frontmatter YAML"
    fm = src.split("---", 2)[1]
    ten = re.search(r"^name:\s*(\S+)", fm, re.M)
    mo_ta = re.search(r"^description:\s*(.+)", fm, re.M)
    assert ten and mo_ta, "frontmatter thiếu name hoặc description"
    assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", ten.group(1)), (
        f"name phải kebab-case: {ten.group(1)!r}")
    assert ten.group(1) == SKILL.parent.name, (
        f"name {ten.group(1)!r} khác tên thư mục {SKILL.parent.name!r}")
    assert "<" not in fm and ">" not in fm, "frontmatter không được có < >"
    assert len(mo_ta.group(1)) > 60, "description quá ngắn để làm điều kiện kích hoạt"
    print(f"PASS  skill {ten.group(1)} · frontmatter hợp lệ")


def _duong_dan_nhac_toi(src: str) -> set:
    """Mọi đường dẫn kiểu `abc/xyz.md` hoặc `abc.py` nằm trong dấu backtick."""
    ra = set()
    for m in re.finditer(r"`([A-Za-z0-9_./-]+\.(?:py|md|json|yml))`", src):
        ra.add(m.group(1))
    return ra


def test_moi_file_skill_nhac_toi_deu_CO_THAT():
    """Trỏ tới file không tồn tại là hứa một thành phần không có."""
    thieu = []
    for f in (SKILL, BAY):
        for d in _duong_dan_nhac_toi(f.read_text(encoding="utf-8")):
            # Bỏ qua đường dẫn tương đối trong chính thư mục skill
            ung_vien = [GOC / d, SKILL.parent / d]
            if not any(u.exists() for u in ung_vien):
                thieu.append(f"{f.name} -> {d}")
    assert not thieu, "skill trỏ tới file không tồn tại:\n  " + "\n  ".join(thieu)
    print("PASS  mọi file skill nhắc tới đều có thật")


def test_moi_TEST_skill_nhac_toi_deu_CO_THAT():
    """Tên test mục ruỗng nhanh nhất — chúng bị đổi tên khi refactor."""
    src = SKILL.read_text(encoding="utf-8") + BAY.read_text(encoding="utf-8")
    thieu = []
    for m in re.finditer(r"`(tests/\w+\.py)::(\w+)`", src):
        f, ham = GOC / m.group(1), m.group(2)
        if not f.exists() or f"def {ham}" not in f.read_text(encoding="utf-8"):
            thieu.append(f"{m.group(1)}::{ham}")
    # Hàm nhắc tới không kèm đường dẫn file
    for ham in ("_ten_da_nhap_va_goi",):
        if ham in src:
            co = any(f"def {ham}" in p.read_text(encoding="utf-8")
                     for p in (GOC / "tests").glob("*.py"))
            if not co:
                thieu.append(ham)
    assert not thieu, "skill trỏ tới test không tồn tại:\n  " + "\n  ".join(thieu)
    print("PASS  mọi test skill nhắc tới đều có thật")


def test_ba_cong_gac_dung_thu_tu_va_dung_ten():
    """Thứ tự là bắt buộc: có test ghi thư mục tạm vào gốc repo, chạy song
    song với `kiem_cu_phap_311` thì gây đỏ giả."""
    src = SKILL.read_text(encoding="utf-8")
    thu_tu = [src.find(x) for x in
              ("-m pytest tests/", "tools/kiem_cu_phap_311.py",
               "tools/chan_bia_so_lieu.py --quet-repo")]
    assert all(i > 0 for i in thu_tu), f"thiếu một cổng gác: {thu_tu}"
    assert thu_tu == sorted(thu_tu), (
        f"ba cổng gác sai thứ tự trong skill: {thu_tu}")
    print("PASS  pytest -> kiem_cu_phap_311 -> chan_bia_so_lieu, đúng thứ tự")


def test_skill_NHAC_ranh_gioi_khong_dat_lenh_that():
    """Ranh giới nặng nhất của dự án. Skill mà bỏ nó thì skill sai."""
    src = SKILL.read_text(encoding="utf-8")
    assert "Không đặt lệnh thật" in src, "skill không nhắc ranh giới đặt lệnh"
    assert "main" in src and "PR" in src, "skill không nhắc luật nhánh/PR"
    print("PASS  skill giữ ranh giới đặt lệnh và luật nhánh")


if __name__ == "__main__":
    for ten, ham in sorted(globals().items()):
        if ten.startswith("test_"):
            ham()
