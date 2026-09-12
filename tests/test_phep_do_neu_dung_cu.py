"""Mỗi phép đo đã ký phải NÊU lệnh đọc nó — hoặc nói ra vì sao không có.

VÌ SAO CÓ FILE NÀY
──────────────────
**Quy tắc số 2: không có lệnh thì không có số.**

Đếm ngày 12/09/2026 trên `docs/TIEU-CHI-DOC-TRUOC.md`: **2/9** mục ĐO nêu
tên một dụng cụ nằm trong repo. Bảy mục còn lại không nêu gì, và trong đó:

- ĐO 1 · 2 · 3 · 4 **có** dụng cụ thật, chỉ là tên nó nằm ở `CLAUDE.md`
  chứ không nằm cạnh tiêu chí — người đọc tiêu chí không thấy.
- ĐO 5 · 5b **không có** dụng cụ trong repo. Bản chạy nằm ở thư mục tạm và
  DB đầu vào đã bị xoá cùng worktree, nên những con số của chúng **không
  tái lập được**. Chuyện ấy trước gác này không được ghi ở đâu cả.

ĐO 6 lọt qua đúng cùng cách, và nó chỉ bị bắt vì **tình cờ** đi rà lại
(BƯỚC 59). Một khuyết tật chỉ bị bắt bằng tình cờ là một khuyết tật sẽ tái
diễn.

Gác này **không ép phải có dụng cụ** — nó ép phải **nói ra**, đúng cơ chế
`# bia-ok:`, `khong_soat_vi` và `# van-ban-ok:`.
"""
import re
import subprocess
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
TIEU_CHI = GOC / "docs" / "TIEU-CHI-DOC-TRUOC.md"

RE_MUC = re.compile(r"^##\s+(ĐO\s+\d+[a-z]?)\s*—", re.M)
# KHÔNG hạn chế ở `tools/`: `walkforward.py` ở gốc repo cũng là một
# lệnh đọc hợp lệ, và chính nó sinh ra hai DB của ĐO 6. Việc phán để
# GIT BIẾT làm — một cái tên viết trần mà git không biết vẫn bị chặn.
RE_DUNG_CU = re.compile(r"`([A-Za-z0-9_./-]+\.py)`")
RE_KHONG_CO = re.compile(r"\*\*Không có dụng cụ vì:\*\*\s*(\S[^\n]*)")
DAI_TOI_THIEU = 30

sys.path.insert(0, str(GOC))


def _git_biet() -> set[str]:
    """Tập file GIT biết — không phải tập file có trên đĩa.

    Một file chưa `git add` thì người khác `clone` về sẽ không có nó, nên
    nêu tên nó trong tiêu chí là một lời hứa về thành phần không tồn tại.
    Cùng luật với `tests/test_skill_quy_trinh.py`.
    """
    r = subprocess.run(["git", "ls-files"], cwd=str(GOC),
                       capture_output=True, text=True)
    return set(r.stdout.split())


def cac_muc(van: str) -> list[tuple[str, str]]:
    """`(tên mục, thân mục)` cho mỗi tiêu đề `## ĐO n —`.

    Cắt theo TIÊU ĐỀ, không theo chữ "ĐO" xuất hiện ở đâu đó trong văn
    xuôi — chữ ấy nằm đầy trong chính file này. Lỗi 30/35/36/38.
    """
    vt = [(m.start(), re.sub(r"\s+", " ", m.group(1)))
          for m in RE_MUC.finditer(van)]
    if not vt:
        return []
    bien = [v[0] for v in vt] + [len(van)]
    return [(vt[i][1], van[bien[i]:bien[i + 1]]) for i in range(len(vt))]


def khai_cua_muc(than: str, git_biet: set[str]) -> tuple[str, str]:
    """(loại, nội dung) — `dung_cu` · `khong_co` · `thieu`.

    Hàm THUẦN trên văn bản một mục, để thử được bằng mẫu dựng tay thay vì
    bằng file thật.
    """
    for duong in RE_DUNG_CU.findall(than):
        if duong in git_biet:
            return "dung_cu", duong
    m = RE_KHONG_CO.search(than)
    if m:
        return "khong_co", m.group(1).strip()
    return "thieu", ""


def ly_do_hop_le(ly_do: str) -> bool:
    """Một lời khai không-có-dụng-cụ có đủ tư cách là lời khai không.

    Tách thành hàm thuần vì lý do đã trả giá HAI LẦN trong một ngày: để
    phép phán nằm thẳng trong test thì nó đọc `DAI_TOI_THIEU` từ chính
    module, và đột biến hằng số ấy làm mù **cả hai vế**. Lần thứ nhất ở
    `tests/test_gac_van_ban_phai_khai.py` (BƯỚC 58); lần thứ hai ở chính
    file này, viết sau đó chưa tới một giờ.
    """
    MO_HO = {"chua lam", "chưa làm", "khong can", "không cần", "sau", "n/a",
             "bo qua", "bỏ qua", "sau nay", "sau này"}
    ly_do = (ly_do or "").strip()
    return len(ly_do) >= DAI_TOI_THIEU and ly_do.lower().strip(" .") not in MO_HO


def test_LY_DO_HOP_LE_phan_dung_ca_HAI_CHIEU():
    """Mẫu dựng tay, cả chiều phải-qua lẫn chiều phải-chặn."""
    PHAI_QUA = [
        "ban doc chay mot lan roi nam lai o thu muc tam, DB da bi go",
        "phep do nay khong chay duoc — nhom chung rong theo cau tao",
    ]
    PHAI_CHAN = ["", "   ", "chua lam", "khong can", "sau", "bo qua", "ngan"]
    for x in PHAI_QUA:
        assert ly_do_hop_le(x), f"ly do that bi chan: {x!r}"
    for x in PHAI_CHAN:
        assert not ly_do_hop_le(x), f"ly do rong/mo ho duoc cho qua: {x!r}"
    print(f"PASS  {len(PHAI_QUA)} qua · {len(PHAI_CHAN)} chan")


def test_NGUONG_DAI_khong_duoc_noi_am_tham():
    """Neo bằng một SỐ VIẾT THẲNG — đọc lại hằng số thì đột biến làm mù."""
    assert DAI_TOI_THIEU >= 30, (
        f"DAI_TOI_THIEU = {DAI_TOI_THIEU}, duoi 30. Noi nguong nay lam moi "
        f"loi khai mot chu deu hop le, tuc gac thanh trang tri (loi 31).")
    assert not ly_do_hop_le("a" * 29), "29 ky tu khong duoc coi la mot ly do"
    assert ly_do_hop_le("a" * 60), "60 ky tu phai duoc chap nhan"
    print(f"PASS  nguong {DAI_TOI_THIEU} ky tu, neo bang so viet thang")


def test_MOI_MUC_DO_deu_NEU_lenh_doc_no_hoac_noi_ra_vi_sao_khong():
    """Thiếu cả hai → đỏ. Đó là toàn bộ việc của gác này."""
    git_biet = _git_biet()
    thieu = [ten for ten, than in cac_muc(TIEU_CHI.read_text(encoding="utf-8"))
             if khai_cua_muc(than, git_biet)[0] == "thieu"]
    assert not thieu, (
        f"Cac muc sau khong neu lenh doc chung, cung khong noi ra vi sao: "
        f"{thieu}\n\nQuy tac so 2: khong co lenh thi khong co so. Hoac neu "
        f"mot duong `tools/....py` GIT BIET, hoac viet mot dong\n"
        f"  **Khong co dung cu vi:** <ly do>")
    print("PASS  moi muc DO deu neu lenh doc hoac ly do khong co")


def test_LY_DO_khong_co_dung_cu_phai_CU_THE():
    """`Không có dụng cụ vì: chưa làm` bị từ chối — cùng cơ chế `# bia-ok:`."""
    xau = []
    for ten, than in cac_muc(TIEU_CHI.read_text(encoding="utf-8")):
        loai, noi_dung = khai_cua_muc(than, _git_biet())
        if loai == "khong_co" and not ly_do_hop_le(noi_dung):
            xau.append(f"{ten}: {noi_dung!r}")
    assert not xau, (
        f"Ly do phai dai it nhat {DAI_TOI_THIEU} ky tu va khong chung chung:\n"
        "  " + "\n  ".join(xau))
    print("PASS  moi ly do khong-co-dung-cu deu cu the")


def test_DUONG_DUNG_CU_phai_la_duong_GIT_BIET():
    """Một đường git không biết là lời hứa về thành phần không tồn tại.

    Thử bằng mẫu dựng tay CẢ HAI CHIỀU — một gác chỉ thấy đầu vào sạch thì
    mọi phép nới đều lọt (lỗi 34).
    """
    biet = {"tools/co_that.py"}
    assert khai_cua_muc("Dụng cụ: `tools/co_that.py`", biet)[0] == "dung_cu"
    assert khai_cua_muc("Dụng cụ: `tools/bia_ra.py`", biet)[0] == "thieu"
    assert khai_cua_muc("Dụng cụ: `do6.py`", biet)[0] == "thieu", (
        "ten file viet TRAN, thieu tien to thu muc — khong duoc nhan")
    # mot duong o GOC repo van hop le neu GIT BIET no — han che o
    # `tools/` la tuy tien, va `walkforward.py` cung sinh ra so that
    assert khai_cua_muc("Dụng cụ: `walkforward.py`",
                        biet | {"walkforward.py"})[0] == "dung_cu"
    assert khai_cua_muc("chua noi gi", biet)[0] == "thieu"
    assert khai_cua_muc(
        "**Không có dụng cụ vì:** mot ly do that su du dai de duoc nhan",
        biet)[0] == "khong_co"
    print("PASS  chi duong GIT BIET moi duoc nhan, ca hai chieu")


def test_CAT_MUC_theo_TIEU_DE_chu_khong_theo_chu_xuat_hien():
    """Chữ "ĐO 5" nằm đầy trong văn xuôi; chỉ `## ĐO 5 —` mới mở một mục."""
    mau = ("# Dau\nVan xuoi nhac ĐO 5 va ĐO 6 nhieu lan.\n"
           "## ĐO 7 — mot muc that\nThan muc lai nhac ĐO 7.\n"
           "### ĐO 8 — tieu de CAP BA\n"
           "## ĐO 9 — mot muc nua\nThan.\n")
    ten = [t for t, _ in cac_muc(mau)]
    assert ten == ["ĐO 7", "ĐO 9"], ten
    # than muc DO 7 phai chua ca tieu de cap ba, khong duoc cat som
    than7 = dict(cac_muc(mau))["ĐO 7"]
    assert "CAP BA" in than7, "cat nham o tieu de cap ba"
    print("PASS  chi tieu de cap hai moi mo mot muc")


def test_MOI_MUC_chi_duoc_nhan_MOT_khai():
    """Nêu dụng cụ VÀ khai không-có cùng lúc là nói nước đôi."""
    biet = {"tools/co_that.py"}
    ca_hai = ("Dụng cụ: `tools/co_that.py`\n"
              "**Không có dụng cụ vì:** mot ly do that su du dai de duoc nhan")
    loai, _ = khai_cua_muc(ca_hai, biet)
    assert loai == "dung_cu", (
        "khai ca hai the thi phai uu tien DUNG CU co that — mot muc vua co "
        "dung cu vua noi khong co la mot mau thuan, va duong dung la sua "
        "tieu chi chu khong phai de gac tu chon")
    print("PASS  co dung cu that thi loi khai 'khong co' khong che duoc no")
