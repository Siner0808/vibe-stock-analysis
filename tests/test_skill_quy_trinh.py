"""Skill `quy-trinh-lam-viec` phải nói ĐÚNG về repo, không chỉ nói hay.

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

THU_MUC_SKILL = GOC / ".claude" / "skills"
SKILL = THU_MUC_SKILL / "quy-trinh-lam-viec" / "SKILL.md"
BAY = SKILL.parent / "references" / "bay.md"

# Mọi file tham chiếu đều bị soi như SKILL.md — một trỏ dẫn chết ở đó cũng
# dẫn người đọc đi sai y hệt.
THAM_CHIEU = sorted((SKILL.parent / "references").glob("*.md"))


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


def _git_biet(d: str) -> bool | None:
    """git CÓ BIẾT đường dẫn này không — theo dõi HOẶC cố ý bỏ qua.

    Trả None khi không hỏi được git (bản tải zip): người gọi lùi về kiểm
    sự tồn tại trên đĩa.

    Vì sao không kiểm `Path.exists()`: máy dev có TRẠNG THÁI CHẠY mà CI
    không có. `sl_pattern_memory.json` được SKILL.md nhắc tới chính vì nó
    là thứ CẤM COMMIT — nó gitignore, nên nó tồn tại ở máy và vắng mặt
    trên runner. Bản đầu của gác này kiểm `exists()` và vì thế xanh tại
    máy, đỏ trên CI (31/08/2026). Đúng cùng lớp bất đối xứng với "máy chạy
    3.13, CI chạy 3.11", chỉ khác chỗ nó là trạng thái file chứ không phải
    cú pháp.
    """
    import subprocess

    def _chay(lenh):
        try:
            return subprocess.run(lenh, cwd=GOC, capture_output=True,
                                  text=True, timeout=10)
        except Exception:
            return None

    r = _chay(["git", "ls-files", "--error-unmatch", d])
    if r is None:
        return None
    if r.returncode == 0:
        return True
    r2 = _chay(["git", "check-ignore", "-q", d])
    if r2 is None:
        return None
    return r2.returncode == 0


def test_moi_file_skill_nhac_toi_deu_CO_THAT():
    """Trỏ tới file git KHÔNG BIẾT là hứa một thành phần không có.

    "git không biết" khác "không có trên đĩa": file gitignore thì git biết
    và cố ý bỏ qua — đó là mention hợp lệ. Chỉ tên gõ sai hoặc file đã đổi
    tên mới làm git ngơ ngác.
    """
    thieu = []
    for f in [SKILL] + THAM_CHIEU:
        for d in _duong_dan_nhac_toi(f.read_text(encoding="utf-8")):
            goc_skill = SKILL.parent.relative_to(GOC)
            tuong_doi = [
                d,
                (goc_skill / d).as_posix(),
                # file tham chiếu nhắc tên trần của file anh em cùng thư mục
                (goc_skill / "references" / d).as_posix(),
            ]
            ket = [_git_biet(x) for x in tuong_doi]
            if any(k is True for k in ket):
                continue
            if all(k is None for k in ket):     # không có git -> lùi về đĩa
                if any((GOC / x).exists() for x in tuong_doi):
                    continue
            thieu.append(f"{f.name} -> {d}")
    assert not thieu, "skill trỏ tới file git không biết:\n  " + "\n  ".join(thieu)
    print("PASS  mọi file skill nhắc tới đều được git biết")


def test_moi_TEST_skill_nhac_toi_deu_CO_THAT():
    """Tên test mục ruỗng nhanh nhất — chúng bị đổi tên khi refactor."""
    src = "\n".join(f.read_text(encoding="utf-8")
                    for f in [SKILL] + THAM_CHIEU)
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


CAC_CONG = ("-m pytest tests/", "tools/kiem_cu_phap_311.py",
            "tools/chan_bia_so_lieu.py --quet-repo",
            "tools/kiem_test_chay_rieng.py")


def test_bon_cong_gac_dung_thu_tu_va_dung_ten():
    """Thứ tự là bắt buộc: có test ghi thư mục tạm vào GỐC REPO, nên hai
    tiến trình pytest cùng lúc cho đỏ giả.

    Cổng thứ tư thêm 07/09/2026 (`docs/STATE.md` BƯỚC 34). Danh sách ghim
    ở `CAC_CONG` chứ không viết thẳng trong thân test: để thân test tự
    dựng lại danh sách thì đột biến "bỏ một cổng" sống sót.
    """
    src = SKILL.read_text(encoding="utf-8")
    thu_tu = [src.find(x) for x in CAC_CONG]
    thieu = [c for c, i in zip(CAC_CONG, thu_tu) if i < 0]
    assert not thieu, f"skill thiếu cổng gác: {thieu}"
    assert thu_tu == sorted(thu_tu), (
        f"cổng gác sai thứ tự trong skill: "
        f"{[c for _, c in sorted(zip(thu_tu, CAC_CONG))]}")
    print(f"PASS  {len(CAC_CONG)} cổng gác, đúng thứ tự")


def test_skill_NHAC_hai_quy_tac_dung_dau():
    """Quy tắc 2 thêm 07/09/2026 và nó là quy tắc duy nhất chống được lỗi
    ước lượng — thứ không phép đo nào bắt được, chỉ thói quen bắt được."""
    src = SKILL.read_text(encoding="utf-8").lower()
    # so KHÔNG phân biệt hoa thường: luật là NỘI DUNG, không phải cách viết
    # hoa. Ghim đúng chữ hoa sẽ đỏ vì một câu viết lại cho xuôi tai.
    assert "con số đẹp lên đáng kể" in src, "skill bỏ Quy tắc số 1"
    assert "không có lệnh thì không có số" in src, "skill bỏ Quy tắc số 2"
    print("PASS  skill giữ cả hai quy tắc đứng đầu")


def test_CHI_CO_MOT_skill_quy_trinh():
    """Hai skill cùng tự nhận là quy trình hiện hành = lỗi kinh điển ở đây.

    `docs/STATE.md` BƯỚC 33 và 34 đều là biến thể của "hai chỗ nói về cùng
    một thứ, một chỗ đã hết đúng". Một skill thừa còn tệ hơn, vì nó được
    nạp TỰ ĐỘNG.
    """
    co = sorted(p.name for p in THU_MUC_SKILL.glob("*/SKILL.md"))
    ds = sorted(p.parent.name for p in THU_MUC_SKILL.glob("*/SKILL.md"))
    assert len(co) == 1, f"có {len(co)} skill trong dự án: {ds}"
    assert ds == ["quy-trinh-lam-viec"], ds
    print(f"PASS  đúng một skill: {ds[0]}")


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
